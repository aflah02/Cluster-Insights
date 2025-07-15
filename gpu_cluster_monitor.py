#!/usr/bin/env python3
"""
GPU Cluster Monitoring Tool

This script connects to multiple nodes via SSH, checks GPU status using nvidia-smi,
and generates a detailed report of GPU usage, processes, and users.
"""

import subprocess
import json
import csv
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import paramiko
import xml.etree.ElementTree as ET


class GPUMonitor:
    def __init__(self, username: str, ssh_key_path: Optional[str] = None, 
                 password: Optional[str] = None, timeout: int = 30):
        """
        Initialize the GPU Monitor
        
        Args:
            username: SSH username for connecting to nodes
            ssh_key_path: Path to SSH private key (optional)
            password: SSH password (optional, not recommended for production)
            timeout: SSH connection timeout in seconds
        """
        self.username = username
        self.ssh_key_path = ssh_key_path
        self.password = password
        self.timeout = timeout
        
    def connect_ssh(self, hostname: str) -> Optional[paramiko.SSHClient]:
        """
        Establish SSH connection to a node
        
        Args:
            hostname: The hostname or IP address of the node
            
        Returns:
            SSH client object or None if connection failed
        """
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.ssh_key_path:
                ssh.connect(
                    hostname=hostname,
                    username=self.username,
                    key_filename=self.ssh_key_path,
                    timeout=self.timeout
                )
            elif self.password:
                ssh.connect(
                    hostname=hostname,
                    username=self.username,
                    password=self.password,
                    timeout=self.timeout
                )
            else:
                # Try to use SSH agent or default keys
                ssh.connect(
                    hostname=hostname,
                    username=self.username,
                    timeout=self.timeout
                )
            
            return ssh
        except Exception as e:
            print(f"Failed to connect to {hostname}: {str(e)}")
            return None

    def get_gpu_info(self, ssh_client: paramiko.SSHClient) -> Optional[Dict]:
        """
        Execute nvidia-smi command and parse GPU information
        
        Args:
            ssh_client: Active SSH connection
            
        Returns:
            Dictionary containing GPU information or None if failed
        """
        try:
            # Execute nvidia-smi with XML output for easier parsing
            stdin, stdout, stderr = ssh_client.exec_command(
                'nvidia-smi -q -x', timeout=30
            )
            
            xml_output = stdout.read().decode('utf-8')
            error_output = stderr.read().decode('utf-8')
            
            if error_output and 'nvidia-smi' in error_output.lower():
                return {'error': 'nvidia-smi not found or NVIDIA drivers not installed'}
            
            if not xml_output.strip():
                return {'error': 'No output from nvidia-smi command'}
                
            # Parse XML output
            root = ET.fromstring(xml_output)
            
            gpu_info = {
                'driver_version': root.find('.//driver_version').text if root.find('.//driver_version') is not None else 'Unknown',
                'cuda_version': root.find('.//cuda_version').text if root.find('.//cuda_version') is not None else 'Unknown',
                'gpus': []
            }
            
            # Parse each GPU
            for gpu in root.findall('.//gpu'):
                gpu_data = self._parse_gpu_data(gpu, ssh_client)
                gpu_info['gpus'].append(gpu_data)
                
            return gpu_info
            
        except Exception as e:
            return {'error': f'Failed to get GPU info: {str(e)}'}

    def _parse_gpu_data(self, gpu_element: ET.Element, ssh_client: paramiko.SSHClient) -> Dict:
        """
        Parse individual GPU data from XML element
        
        Args:
            gpu_element: XML element containing GPU information
            ssh_client: Active SSH connection for additional queries
            
        Returns:
            Dictionary containing parsed GPU data
        """
        gpu_data = {}
        
        # Basic GPU information
        gpu_data['id'] = gpu_element.get('id', 'Unknown')
        gpu_data['name'] = self._get_text(gpu_element, './/product_name')
        gpu_data['uuid'] = self._get_text(gpu_element, './/uuid')
        
        # Memory information
        memory_elem = gpu_element.find('.//fb_memory_usage')
        if memory_elem is not None:
            gpu_data['memory_total'] = self._get_text(memory_elem, './/total')
            gpu_data['memory_used'] = self._get_text(memory_elem, './/used')
            gpu_data['memory_free'] = self._get_text(memory_elem, './/free')
            
            # Calculate memory usage percentage
            try:
                total = float(gpu_data['memory_total'].replace(' MiB', ''))
                used = float(gpu_data['memory_used'].replace(' MiB', ''))
                gpu_data['memory_usage_percent'] = round((used / total) * 100, 2)
            except:
                gpu_data['memory_usage_percent'] = 'Unknown'
        
        # Utilization information
        utilization_elem = gpu_element.find('.//utilization')
        if utilization_elem is not None:
            gpu_data['gpu_utilization'] = self._get_text(utilization_elem, './/gpu_util')
            gpu_data['memory_utilization'] = self._get_text(utilization_elem, './/memory_util')
        
        # Temperature
        gpu_data['temperature'] = self._get_text(gpu_element, './/temperature/gpu_temp')
        
        # Power information
        gpu_data['power_draw'] = self._get_text(gpu_element, './/power_readings/power_draw')
        gpu_data['power_limit'] = self._get_text(gpu_element, './/power_readings/power_limit')
        
        # Process information
        gpu_data['processes'] = self._get_gpu_processes(gpu_element, ssh_client)
        
        return gpu_data

    def _get_gpu_processes(self, gpu_element: ET.Element, ssh_client: paramiko.SSHClient) -> List[Dict]:
        """
        Get detailed process information for GPU
        
        Args:
            gpu_element: XML element containing GPU information
            ssh_client: Active SSH connection
            
        Returns:
            List of dictionaries containing process information
        """
        processes = []
        
        # Get processes from nvidia-smi XML
        processes_elem = gpu_element.find('.//processes')
        if processes_elem is not None:
            for process in processes_elem.findall('.//process_info'):
                proc_data = {
                    'pid': self._get_text(process, './/pid'),
                    'type': self._get_text(process, './/type'),
                    'process_name': self._get_text(process, './/process_name'),
                    'used_memory': self._get_text(process, './/used_memory')
                }
                
                # Get additional process details using ps command
                if proc_data['pid'] and proc_data['pid'] != 'Unknown':
                    try:
                        stdin, stdout, stderr = ssh_client.exec_command(
                            f"ps -p {proc_data['pid']} -o pid,ppid,user,start,etime,cmd --no-headers",
                            timeout=10
                        )
                        ps_output = stdout.read().decode('utf-8').strip()
                        
                        if ps_output:
                            parts = ps_output.split(None, 5)
                            if len(parts) >= 6:
                                proc_data['user'] = parts[2]
                                proc_data['start_time'] = parts[3]
                                proc_data['elapsed_time'] = parts[4]
                                proc_data['command'] = parts[5]
                            elif len(parts) >= 3:
                                proc_data['user'] = parts[2]
                    except:
                        pass
                
                processes.append(proc_data)
        
        return processes

    def _get_text(self, element: ET.Element, xpath: str) -> str:
        """
        Safely get text from XML element
        
        Args:
            element: XML element to search in
            xpath: XPath expression
            
        Returns:
            Text content or 'Unknown' if not found
        """
        found = element.find(xpath)
        return found.text if found is not None and found.text else 'Unknown'

    def check_node(self, hostname: str) -> Dict:
        """
        Check GPU status for a single node
        
        Args:
            hostname: The hostname or IP address of the node
            
        Returns:
            Dictionary containing node status and GPU information
        """
        print(f"Checking node: {hostname}")
        
        result = {
            'hostname': hostname,
            'timestamp': datetime.now().isoformat(),
            'status': 'unknown',
            'error': None,
            'gpu_info': None
        }
        
        # Try to establish SSH connection
        ssh_client = self.connect_ssh(hostname)
        if ssh_client is None:
            result['status'] = 'connection_failed'
            result['error'] = 'Failed to establish SSH connection'
            return result
        
        try:
            # Check if nvidia-smi is available and get GPU info
            gpu_info = self.get_gpu_info(ssh_client)
            
            if gpu_info and 'error' in gpu_info:
                result['status'] = 'no_gpu_or_driver'
                result['error'] = gpu_info['error']
            else:
                result['status'] = 'success'
                result['gpu_info'] = gpu_info
                
        except Exception as e:
            result['status'] = 'error'
            result['error'] = f'Error during GPU check: {str(e)}'
        finally:
            ssh_client.close()
        
        return result

    def check_multiple_nodes(self, hostnames: List[str], max_workers: int = 10) -> List[Dict]:
        """
        Check GPU status for multiple nodes concurrently
        
        Args:
            hostnames: List of hostnames or IP addresses
            max_workers: Maximum number of concurrent SSH connections
            
        Returns:
            List of dictionaries containing results for each node
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks
            future_to_hostname = {
                executor.submit(self.check_node, hostname): hostname 
                for hostname in hostnames
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_hostname):
                hostname = future_to_hostname[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        'hostname': hostname,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'error',
                        'error': f'Unexpected error: {str(e)}',
                        'gpu_info': None
                    })
        
        return results

    def generate_report(self, results: List[Dict], output_format: str = 'text') -> str:
        """
        Generate a formatted report from the results
        
        Args:
            results: List of node check results
            output_format: Output format ('text', 'json', 'csv')
            
        Returns:
            Formatted report string
        """
        if output_format == 'json':
            return json.dumps(results, indent=2)
        elif output_format == 'csv':
            return self._generate_csv_report(results)
        else:
            return self._generate_text_report(results)

    def _generate_text_report(self, results: List[Dict]) -> str:
        """Generate a human-readable text report"""
        report = []
        report.append("=" * 80)
        report.append(f"GPU Cluster Monitoring Report")
        report.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        total_nodes = len(results)
        successful_nodes = sum(1 for r in results if r['status'] == 'success')
        failed_nodes = total_nodes - successful_nodes
        
        report.append(f"SUMMARY:")
        report.append(f"  Total nodes checked: {total_nodes}")
        report.append(f"  Successful: {successful_nodes}")
        report.append(f"  Failed: {failed_nodes}")
        report.append("")
        
        # Individual node reports
        for result in results:
            report.append("-" * 60)
            report.append(f"Node: {result['hostname']}")
            report.append(f"Status: {result['status']}")
            report.append(f"Timestamp: {result['timestamp']}")
            
            if result['status'] == 'success' and result['gpu_info']:
                gpu_info = result['gpu_info']
                report.append(f"Driver Version: {gpu_info.get('driver_version', 'Unknown')}")
                report.append(f"CUDA Version: {gpu_info.get('cuda_version', 'Unknown')}")
                report.append("")
                
                for i, gpu in enumerate(gpu_info.get('gpus', [])):
                    report.append(f"  GPU {i} ({gpu.get('id', 'Unknown')}):")
                    report.append(f"    Name: {gpu.get('name', 'Unknown')}")
                    report.append(f"    Memory: {gpu.get('memory_used', 'Unknown')} / {gpu.get('memory_total', 'Unknown')} ({gpu.get('memory_usage_percent', 'Unknown')}%)")
                    report.append(f"    GPU Utilization: {gpu.get('gpu_utilization', 'Unknown')}")
                    report.append(f"    Temperature: {gpu.get('temperature', 'Unknown')}")
                    report.append(f"    Power: {gpu.get('power_draw', 'Unknown')} / {gpu.get('power_limit', 'Unknown')}")
                    
                    processes = gpu.get('processes', [])
                    if processes:
                        report.append(f"    Processes ({len(processes)}):")
                        for proc in processes:
                            user = proc.get('user', 'Unknown')
                            cmd = proc.get('command', proc.get('process_name', 'Unknown'))
                            memory = proc.get('used_memory', 'Unknown')
                            elapsed = proc.get('elapsed_time', 'Unknown')
                            report.append(f"      PID {proc.get('pid', 'Unknown')} - User: {user} - Memory: {memory} - Time: {elapsed}")
                            if len(cmd) > 60:
                                cmd = cmd[:57] + "..."
                            report.append(f"        Command: {cmd}")
                    else:
                        report.append(f"    No processes running")
                    report.append("")
            else:
                report.append(f"Error: {result.get('error', 'Unknown error')}")
            
            report.append("")
        
        return "\n".join(report)

    def _generate_csv_report(self, results: List[Dict]) -> str:
        """Generate a CSV format report"""
        import io
        output = io.StringIO()
        
        fieldnames = [
            'hostname', 'status', 'timestamp', 'error', 'driver_version', 'cuda_version',
            'gpu_id', 'gpu_name', 'memory_used', 'memory_total', 'memory_usage_percent',
            'gpu_utilization', 'temperature', 'power_draw', 'processes_count',
            'process_users', 'process_commands'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            base_row = {
                'hostname': result['hostname'],
                'status': result['status'],
                'timestamp': result['timestamp'],
                'error': result.get('error', '')
            }
            
            if result['status'] == 'success' and result['gpu_info']:
                gpu_info = result['gpu_info']
                base_row.update({
                    'driver_version': gpu_info.get('driver_version', ''),
                    'cuda_version': gpu_info.get('cuda_version', '')
                })
                
                for gpu in gpu_info.get('gpus', []):
                    row = base_row.copy()
                    row.update({
                        'gpu_id': gpu.get('id', ''),
                        'gpu_name': gpu.get('name', ''),
                        'memory_used': gpu.get('memory_used', ''),
                        'memory_total': gpu.get('memory_total', ''),
                        'memory_usage_percent': gpu.get('memory_usage_percent', ''),
                        'gpu_utilization': gpu.get('gpu_utilization', ''),
                        'temperature': gpu.get('temperature', ''),
                        'power_draw': gpu.get('power_draw', ''),
                        'processes_count': len(gpu.get('processes', [])),
                        'process_users': '; '.join([p.get('user', 'Unknown') for p in gpu.get('processes', [])]),
                        'process_commands': '; '.join([p.get('command', p.get('process_name', 'Unknown')) for p in gpu.get('processes', [])])
                    })
                    writer.writerow(row)
            else:
                writer.writerow(base_row)
        
        return output.getvalue()


def load_nodes_from_file(file_path: str) -> List[str]:
    """
    Load node hostnames from a text file (one per line)
    
    Args:
        file_path: Path to the file containing node hostnames
        
    Returns:
        List of node hostnames
    """
    try:
        with open(file_path, 'r') as f:
            nodes = []
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    nodes.append(line)
            return nodes
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{file_path}': {str(e)}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Monitor GPU usage across cluster nodes',
        epilog='''
Examples:
  # Check specific nodes
  python gpu_cluster_monitor.py -u username -k ~/.ssh/id_rsa node1 node2 node3
  
  # Check nodes from file
  python gpu_cluster_monitor.py -u username -k ~/.ssh/id_rsa --nodes-file nodes.txt
  
  # Mix file and command line nodes
  python gpu_cluster_monitor.py -u username -k ~/.ssh/id_rsa --nodes-file nodes.txt node4 node5
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Node specification arguments
    parser.add_argument('nodes', nargs='*', help='List of node hostnames or IP addresses')
    parser.add_argument('--nodes-file', '-n', help='File containing node hostnames (one per line)')
    
    # SSH connection arguments
    parser.add_argument('-u', '--username', required=True, help='SSH username')
    parser.add_argument('-k', '--key', help='Path to SSH private key file')
    parser.add_argument('-p', '--password', help='SSH password (not recommended)')
    parser.add_argument('-t', '--timeout', type=int, default=30, help='SSH connection timeout (seconds)')
    
    # Execution arguments
    parser.add_argument('-w', '--workers', type=int, default=10, help='Maximum concurrent connections')
    
    # Output arguments
    parser.add_argument('-f', '--format', choices=['text', 'json', 'csv'], default='text', help='Output format')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    # Collect nodes from both command line and file
    all_nodes = []
    
    # Add nodes from command line
    if args.nodes:
        all_nodes.extend(args.nodes)
    
    # Add nodes from file
    if args.nodes_file:
        file_nodes = load_nodes_from_file(args.nodes_file)
        all_nodes.extend(file_nodes)
    
    # Validate that we have at least one node
    if not all_nodes:
        parser.error("No nodes specified. Provide nodes via command line or --nodes-file option.")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_nodes = []
    for node in all_nodes:
        if node not in seen:
            seen.add(node)
            unique_nodes.append(node)
    
    # Initialize monitor
    monitor = GPUMonitor(
        username=args.username,
        ssh_key_path=args.key,
        password=args.password,
        timeout=args.timeout
    )
    
    # Check nodes
    print(f"Checking {len(unique_nodes)} nodes...")
    if args.nodes_file:
        print(f"  - {len(load_nodes_from_file(args.nodes_file))} nodes from file: {args.nodes_file}")
    if args.nodes:
        print(f"  - {len(args.nodes)} nodes from command line")
    
    results = monitor.check_multiple_nodes(unique_nodes, max_workers=args.workers)
    
    # Generate report
    report = monitor.generate_report(results, output_format=args.format)
    
    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)


if __name__ == '__main__':
    main()
