#!/bin/bash

# Install required packages
pip3 install -r requirements.txt --break-system-packages
pip3 install -r kubeflow_pipelines/requirements.txt --break-system-packages

# Run the pipeline automation
while true; do
    echo "Starting pipeline automation at $(date)"
    python3 kubeflow_pipelines/automate_pipeline.py
    
    # Wait for 1 hour before next run
    echo "Waiting for 1 hour before next run..."
    sleep 3600
done
