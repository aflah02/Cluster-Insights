#!/usr/bin/env python3
"""
Example usage of Cluster Insights - GPU Monitoring Tool
"""

from gpu_cluster_monitor import GPUMonitor
import json

def main():
    # Example 1: Basic usage with SSH key
    print("=== Example 1: Basic Usage ===")
    
    # Initialize monitor
    monitor = GPUMonitor(
        username="your_username",
        ssh_key_path="~/.ssh/id_rsa",  # Update with your SSH key path
        timeout=30
    )
    
    # List of nodes to check
    nodes = [
        "node1.cluster.local",
        "node2.cluster.local", 
        "192.168.1.100"
    ]
    
    # Check all nodes
    print(f"Checking {len(nodes)} nodes...")
    results = monitor.check_multiple_nodes(nodes, max_workers=5)
    
    # Generate and print text report
    text_report = monitor.generate_report(results, output_format='text')
    print(text_report)
    
    print("\n" + "="*80 + "\n")
    
    # Example 2: JSON output for programmatic processing
    print("=== Example 2: JSON Output ===")
    
    json_report = monitor.generate_report(results, output_format='json')
    data = json.loads(json_report)
    
    # Process the data programmatically
    for node_result in data:
        hostname = node_result['hostname']
        status = node_result['status']
        
        if status == 'success' and node_result['gpu_info']:
            gpu_count = len(node_result['gpu_info']['gpus'])
            total_processes = sum(len(gpu.get('processes', [])) for gpu in node_result['gpu_info']['gpus'])
            print(f"{hostname}: {gpu_count} GPUs, {total_processes} total processes")
            
            # Show users currently using GPUs
            users = set()
            for gpu in node_result['gpu_info']['gpus']:
                for process in gpu.get('processes', []):
                    if process.get('user'):
                        users.add(process['user'])
            
            if users:
                print(f"  Active users: {', '.join(users)}")
            else:
                print(f"  No active GPU processes")
        else:
            print(f"{hostname}: {status} - {node_result.get('error', 'Unknown error')}")
    
    print("\n" + "="*80 + "\n")
    
    # Example 3: Save CSV report
    print("=== Example 3: CSV Output ===")
    
    csv_report = monitor.generate_report(results, output_format='csv')
    
    # Save to file
    with open('gpu_report.csv', 'w') as f:
        f.write(csv_report)
    
    print("CSV report saved to 'gpu_report.csv'")
    
    # Example 4: Check single node with detailed error handling
    print("\n=== Example 4: Single Node Check ===")
    
    single_result = monitor.check_node("test-node.example.com")
    print(f"Node: {single_result['hostname']}")
    print(f"Status: {single_result['status']}")
    
    if single_result['status'] == 'success':
        gpu_info = single_result['gpu_info']
        print(f"Driver: {gpu_info['driver_version']}")
        print(f"CUDA: {gpu_info['cuda_version']}")
        print(f"GPUs found: {len(gpu_info['gpus'])}")
    else:
        print(f"Error: {single_result.get('error', 'Unknown')}")

if __name__ == '__main__':
    main()
