#!/bin/bash
# GPU Cluster Monitor - Quick Run Script for Linux/Mac
# Usage: ./run_monitor.sh [output_file]

# Configuration - modify these variables as needed
USERNAME=""
NODES_FILE="node_list.txt"
OUTPUT_FORMAT="csv"
WORKERS=20

# Make script executable if it isn't already
if [ ! -x "$0" ]; then
    chmod +x "$0"
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH"
    exit 1
fi

# Check if the GPU monitor script exists
if [ ! -f "gpu_cluster_monitor.py" ]; then
    echo "Error: gpu_cluster_monitor.py not found in current directory"
    exit 1
fi

# Check if the nodes file exists
if [ ! -f "$NODES_FILE" ]; then
    echo "Error: Node list file '$NODES_FILE' not found"
    exit 1
fi

# Run the monitor with or without output file
if [ -z "$1" ]; then
    echo "Running GPU monitor with output to console..."
    python3 gpu_cluster_monitor.py -u "$USERNAME" -f "$OUTPUT_FORMAT" -w "$WORKERS" --nodes-file "$NODES_FILE"
else
    echo "Running GPU monitor with output to file: $1"
    python3 gpu_cluster_monitor.py -u "$USERNAME" -f "$OUTPUT_FORMAT" -w "$WORKERS" --nodes-file "$NODES_FILE" -o "$1"
fi

# Check exit status
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Error occurred during execution (exit code: $exit_code)"
    echo "Press any key to continue..."
    read -n 1
fi
