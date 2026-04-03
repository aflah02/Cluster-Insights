# Cluster Insights

A Python tool for monitoring GPU cluster status via SSH. Check GPU usage, memory, temperature, and see which users/processes are using each GPU.

## Two Ways to Run

### 1. CLI (Command Line)

```bash
python gpu_cluster_monitor.py -u your_username -k ~/.ssh/id_rsa --nodes-file node_list_gpus.txt
python gpu_cluster_monitor.py -u your_username -k ~/.ssh/id_rsa --nodes-file node_list_gpus.txt -o report.txt
python gpu_cluster_monitor.py -u your_username -k ~/.ssh/id_rsa --nodes-file node_list_gpus.txt -f json
```

### 2. Web UI

```bash
python web_ui.py
```

Then open **http://127.0.0.1:5000** in your browser.

**Web UI Features:**
- Visual GPU status - green = free, red = occupied
- Groups nodes by GPU type (H100, A100, A40, L40, V100)
- Auto-refresh with configurable intervals (15s, 30s, 1min, 2min)
- Memory usage bars, temperature, utilization per GPU
- Hover over processes to see PID and full command

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Edit these lines in `web_ui.py`:
```python
USERNAME = "your_username"
NODES_FILE = "node_list_gpus.txt"
```

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