# GPU Cluster Monitor

![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-Apache%202.0-blue)

A Python script that connects to multiple cluster nodes via SSH, checks GPU status using `nvidia-smi`, and generates detailed reports of GPU usage, processes, and users.

## Features

- **Concurrent SSH connections** to multiple nodes for fast monitoring
- **Detailed GPU information** including memory usage, utilization, temperature, and power consumption
- **Process tracking** with user information and command details
- **Multiple output formats** (text, JSON, CSV)
- **Graceful error handling** for nodes that don't respond or don't have GPUs
- **Comprehensive reporting** with summary statistics

## Installation

1. Install Python 3.6 or higher
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```bash
# Check specific nodes with SSH key authentication
python gpu_cluster_monitor.py -u your_username -k ~/.ssh/id_rsa node1 node2 node3

# Check nodes with password authentication (not recommended for production)
python gpu_cluster_monitor.py -u your_username -p your_password node1 node2

# Check nodes from a file
python gpu_cluster_monitor.py -u your_username -k ~/.ssh/id_rsa $(cat nodes.txt)
```

### Advanced Usage

```bash
# Generate JSON output
python gpu_cluster_monitor.py -u username -k ~/.ssh/id_rsa -f json node1 node2

# Generate CSV output and save to file
python gpu_cluster_monitor.py -u username -k ~/.ssh/id_rsa -f csv -o gpu_report.csv node1 node2

# Increase concurrent connections and timeout
python gpu_cluster_monitor.py -u username -k ~/.ssh/id_rsa -w 20 -t 60 node1 node2 node3
```

### Quick Run Scripts

For convenience, platform-specific runner scripts are provided with pre-configured settings:

#### Windows (`run_monitor.bat`)

```batch
# Run with console output
run_monitor.bat

# Run and save output to file
run_monitor.bat gpu_report.csv
```

#### Linux/Mac (`run_monitor.sh`)

```bash
# Run with console output
./run_monitor.sh

# Run and save output to file
./run_monitor.sh gpu_report.csv
```

### Command Line Options

- `-u, --username`: SSH username (required)
- `-k, --key`: Path to SSH private key file
- `-p, --password`: SSH password (not recommended for production)
- `-t, --timeout`: SSH connection timeout in seconds (default: 30)
- `-w, --workers`: Maximum concurrent connections (default: 10)
- `-f, --format`: Output format - text, json, or csv (default: text)
- `-o, --output`: Output file (default: stdout)

## Sample Output

### Text Format
```
================================================================================
GPU Cluster Monitoring Report
Generated at: 2025-07-15 14:30:25
================================================================================

SUMMARY:
  Total nodes checked: 3
  Successful: 2
  Failed: 1

------------------------------------------------------------
Node: gpu-node-01
Status: success
Timestamp: 2025-07-15T14:30:25.123456
Driver Version: 470.82.01
CUDA Version: 11.4

  GPU 0 (GPU-12345678-1234-1234-1234-123456789012):
    Name: NVIDIA GeForce RTX 3090
    Memory: 2048 MiB / 24576 MiB (8.33%)
    GPU Utilization: 85 %
    Temperature: 72 C
    Power: 320.45 W / 350.00 W
    Processes (2):
      PID 1234 - User: alice - Memory: 1024 MiB - Time: 02:30:15
        Command: python train_model.py --batch-size 32
      PID 5678 - User: bob - Memory: 1024 MiB - Time: 01:15:30
        Command: jupyter-lab --ip=0.0.0.0 --port=8888

------------------------------------------------------------
Node: gpu-node-02
Status: connection_failed
Error: Failed to establish SSH connection
```

## Requirements

- Python 3.6+
- paramiko library for SSH connections
- Network access to target nodes
- SSH access to target nodes
- nvidia-smi installed on target nodes (for GPU information)

## Error Handling

The script handles various error conditions gracefully:

- **SSH connection failures**: Reports connection issues without stopping the entire scan
- **Missing nvidia-smi**: Detects when NVIDIA drivers or nvidia-smi are not installed
- **Permission issues**: Reports authentication or permission problems
- **Network timeouts**: Configurable timeout for unresponsive nodes
- **Invalid responses**: Handles malformed or unexpected command outputs

## Security Considerations

- Use SSH key authentication instead of passwords when possible
- Ensure your SSH keys are properly secured
- Consider using SSH agent for key management
- Be cautious when using password authentication in scripts

## Output Formats

### JSON Format
Structured data suitable for programmatic processing and integration with other tools.

### CSV Format
Tabular data suitable for importing into spreadsheets or databases.

### Text Format
Human-readable format with detailed information and summary statistics.

## Troubleshooting

1. **"Permission denied" errors**: Check SSH key permissions and user access
2. **"nvidia-smi not found"**: Ensure NVIDIA drivers are installed on target nodes
3. **Connection timeouts**: Increase timeout value or check network connectivity
4. **"Host key verification failed"**: Add hosts to known_hosts or use StrictHostKeyChecking=no (not recommended for production)

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool.
