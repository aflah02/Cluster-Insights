@echo off
REM GPU Cluster Monitor - Quick Run Script
REM Usage: run_monitor.bat [output_file] .\personal_runner.bat report_today.txt 

set USERNAME=afkhan
set NODES_FILE=node_list_gpus.txt
set OUTPUT_FORMAT=text
set WORKERS=20

if "%1"=="" (
    echo Running GPU monitor with output to console...
    python gpu_cluster_monitor.py -u %USERNAME% -f %OUTPUT_FORMAT% -w %WORKERS% --nodes-file %NODES_FILE%
) else (
    echo Running GPU monitor with output to file: %1
    python gpu_cluster_monitor.py -u %USERNAME% -f %OUTPUT_FORMAT% -w %WORKERS% --nodes-file %NODES_FILE% -o %1
)

if %ERRORLEVEL% NEQ 0 (
    echo Error occurred during execution
    pause
)