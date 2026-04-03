# Cluster Insights

A Python tool that connects to cluster nodes via SSH, checks GPU status using `nvidia-smi`, and reports GPU usage.

## Two Ways to Run

### 1. CLI (Command Line)

```bash
# Check nodes from file
python gpu_cluster_monitor.py -u your_username -k ~/.ssh/id_rsa --nodes-file node_list_gpus.txt

# Save output to file
python gpu_cluster_monitor.py -u your_username -k ~/.ssh/id_rsa --nodes-file node_list_gpus.txt -o report.txt

# JSON output
python gpu_cluster_monitor.py -u your_username -k ~/.ssh/id_rsa --nodes-file node_list_gpus.txt -f json
```

### 2. Web UI

```bash
# Install flask (pip install flask)
python web_ui.py
```

Then open **http://127.0.0.1:5000** in your browser.

Features:
- Visual GPU status (green = free, red = occupied)
- Groups nodes by GPU type (A100, H100, A40, etc.)
- Auto-refresh with configurable intervals
- Memory usage bars, temperature, utilization
- Shows which user/process is using each GPU

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Edit these lines in `web_ui.py` to change defaults:
```python
USERNAME = "your_username"
NODES_FILE = "node_list_gpus.txt"
```

Or create a `.bat` file similar to `personal_runner.bat`.

## Quick Run Scripts

### Windows
```batch
personal_runner.bat report.txt
```

### Linux/Mac
```bash
chmod +x personal_runner.sh
./personal_runner.sh report.txt
```

## Requirements

- Python 3.6+
- paramiko (SSH connections)
- flask (web UI only)
- SSH access to cluster nodes
- nvidia-smi on target nodes