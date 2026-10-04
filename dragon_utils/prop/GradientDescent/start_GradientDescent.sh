#!/bin/bash
source /home/motz/CALETana/prop/.venv/bin/activate

# Check for correct argument count
if [ $# -ne 1 ]; then
    echo "No valid arguments given. Argument must be 0 or 1"
    exit 1
fi

# if run_submit_script==1 then run automated submission of several gradient descent runs with submitGD.py
# else run one GD.py descent run with the current configuration in config.yaml
run_submit_script=$1

if [ $run_submit_script -eq 0 ]; then
    echo "Starting single descent run with current configuration"
    python GD.py
elif [ $run_submit_script -eq 1 ]; then
    echo "Starting submission of several descents with different configuration"
    python submitGD.py
else
    echo "Not a valid running mode. Argument must be 0 or 1"
    exit 1
fi
