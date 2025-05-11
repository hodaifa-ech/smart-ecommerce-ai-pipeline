#!/bin/bash

# Install required packages
pip3 install -r requirements.txt --break-system-packages

# Set environment variables
export GROQ_API_KEY="your-groq-api-key"

# Run the ML pipeline
while true; do
    echo "Starting ML pipeline at $(date)"
    
    # Compile and run the pipeline
    python3 ml_pipeline.py
    
    # Upload and run the pipeline
    python3 automate_pipeline.py
    
    # Wait for 6 hours before next run
    echo "Waiting for 6 hours before next run..."
    sleep 21600
done 