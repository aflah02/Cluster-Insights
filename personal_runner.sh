#!/bin/bash
# GPU Cluster Monitor - Quick Run Script
# Usage: ./personal_runner.sh [output_file]

USERNAME=afkhan
NODES_FILE=node_list_gpus.txt
OUTPUT_FORMAT=text
WORKERS=20

if [ -z "$1" ]; then
    echo "Running GPU monitor with output to console..."
    python gpu_cluster_monitor.py -u "$USERNAME" -f "$OUTPUT_FORMAT" -w "$WORKERS" --nodes-file "$NODES_FILE"
else
    echo "Running GPU monitor with output to file: $1"
    python gpu_cluster_monitor.py -u "$USERNAME" -f "$OUTPUT_FORMAT" -w "$WORKERS" --nodes-file "$NODES_FILE" -o "$1"
fi