#!/usr/bin/env python3
"""
Cluster Insights Web UI - Flask Application

A web interface for visualizing GPU cluster status with real-time refresh.
"""

import subprocess
import os
import sys
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import re
from typing import Dict, List, Optional

app = Flask(__name__)

# Configuration
USERNAME = "afkhan"
NODES_FILE = "node_list_gpus.txt"
WORKERS = 20

def parse_report(report_text: str) -> Dict:
    """
    Parse the text report into a structured format.
    """
    nodes = {}
    current_node = None
    current_gpu = None

    lines = report_text.split('\n')
    for line in lines:
        # Node header line
        if line.startswith("Node: "):
            node_name = line.replace("Node: ", "").strip()
            current_node = {
                'name': node_name,
                'status': 'unknown',
                'error': None,
                'gpus': []
            }
            nodes[node_name] = current_node

        elif current_node and line.startswith("Status: "):
            current_node['status'] = line.replace("Status: ", "").strip()

        elif current_node and line.startswith("Error: "):
            current_node['error'] = line.replace("Error: ", "").strip()

        elif current_node and line.startswith("  GPU "):
            # GPU header line
            match = re.match(r'^\s+GPU\s+(\d+)\s+\(([^)]+)\):', line)
            if match:
                gpu_idx = match.group(1)
                gpu_pci = match.group(2)
                current_gpu = {
                    'index': gpu_idx,
                    'pci': gpu_pci,
                    'name': 'Unknown',
                    'memory_used': 0,
                    'memory_total': 0,
                    'memory_percent': 0,
                    'utilization': 0,
                    'temperature': 0,
                    'processes': []
                }
                current_node['gpus'].append(current_gpu)

        elif current_gpu:
            # Parse GPU details
            if line.strip().startswith("Name: "):
                current_gpu['name'] = line.replace("Name: ", "").strip()

            elif line.strip().startswith("Memory: "):
                # Format: "Memory: 74231 MiB / 81920 MiB (90.61%)"
                match = re.search(r'(\d+)\s+MiB\s+/\s+(\d+)\s+MiB\s+\(([0-9.]+)%\)', line)
                if match:
                    current_gpu['memory_used'] = int(match.group(1))
                    current_gpu['memory_total'] = int(match.group(2))
                    current_gpu['memory_percent'] = float(match.group(3))

            elif line.strip().startswith("GPU Utilization: "):
                val = line.replace("GPU Utilization: ", "").replace(" %", "").strip()
                try:
                    current_gpu['utilization'] = int(val)
                except:
                    pass

            elif line.strip().startswith("Temperature: "):
                val = line.replace("Temperature: ", "").replace(" C", "").strip()
                try:
                    current_gpu['temperature'] = int(val)
                except:
                    pass

            elif "Processes" in line and "(" in line:
                # Processes count line
                match = re.search(r'Processes \((\d+)\):', line)
                if match:
                    pass  # Process count, actual processes follow

            elif current_gpu and line.strip().startswith("PID "):
                # Process info line: "PID 532747 - User: jyuan - Memory: 74224 MiB - Time: 16"
                match = re.search(r'PID\s+(\d+)\s+-\s+User:\s+(\S+)\s+-\s+Memory:\s+(\d+)\s+MiB\s+-\s+Time:\s+(\S+)', line)
                if match:
                    proc = {
                        'pid': match.group(1),
                        'user': match.group(2),
                        'memory': int(match.group(3)),
                        'time': match.group(4)
                    }
                    current_gpu['processes'].append(proc)

            elif current_gpu and line.strip().startswith("No processes running"):
                # No processes
                pass

    return nodes


def get_gpu_type(node_name: str) -> str:
    """Extract GPU type from node name (e.g., sws-2a100-01 -> A100)"""
    if 'a100' in node_name.lower():
        return 'A100'
    elif 'h100' in node_name.lower():
        return 'H100'
    elif 'a40' in node_name.lower():
        return 'A40'
    elif 'l40' in node_name.lower():
        return 'L40'
    return 'Unknown'


def group_by_gpu_type(nodes: Dict) -> Dict:
    """Group nodes by GPU type"""
    groups = {}
    for node_name, node_data in sorted(nodes.items()):
        gpu_type = get_gpu_type(node_name)
        if gpu_type not in groups:
            groups[gpu_type] = []
        groups[gpu_type].append(node_data)
    return groups


def run_monitor() -> Dict:
    """Run the GPU monitor and return parsed results"""
    try:
        # Run the monitoring command
        cmd = [
            sys.executable,  # Use current Python
            'gpu_cluster_monitor.py',
            '-u', USERNAME,
            '-f', 'text',
            '-w', str(WORKERS),
            '--nodes-file', NODES_FILE
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=os.path.dirname(os.path.abspath(__file__)) or '.'
        )

        output = result.stdout if result.stdout else result.stderr

        if not output:
            return {'error': 'No output from monitoring command', 'nodes': {}, 'groups': {}}

        nodes = parse_report(output)
        groups = group_by_gpu_type(nodes)

        return {
            'nodes': nodes,
            'groups': groups,
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'error': None
        }

    except subprocess.TimeoutExpired:
        return {'error': 'Monitoring command timed out', 'nodes': {}, 'groups': {}, 'success': False}
    except Exception as e:
        return {'error': str(e), 'nodes': {}, 'groups': {}, 'success': False}


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/refresh')
def refresh():
    """Refresh GPU data"""
    result = run_monitor()
    return jsonify(result)


@app.route('/status')
def status():
    """Get current status summary"""
    result = run_monitor()

    summary = {
        'total_nodes': len(result['nodes']),
        'successful': sum(1 for n in result['nodes'].values() if n['status'] == 'success'),
        'failed': sum(1 for n in result['nodes'].values() if n['status'] != 'success'),
        'total_gpus': sum(len(n['gpus']) for n in result['nodes'].values() if n['status'] == 'success'),
        'occupied_gpus': sum(
            sum(1 for g in n['gpus'] if g['processes'])
            for n in result['nodes'].values() if n['status'] == 'success'
        ),
        'available_gpus': sum(
            sum(1 for g in n['gpus'] if not g['processes'])
            for n in result['nodes'].values() if n['status'] == 'success'
        ),
        'timestamp': result.get('timestamp', '')
    }

    return jsonify(summary)


if __name__ == '__main__':
    print("Starting Cluster Insights Web UI...")
    print("Open http://127.0.0.1:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)