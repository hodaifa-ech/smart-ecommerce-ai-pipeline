#!/bin/bash

# This script compiles the pipeline defined in pipeline.py into a YAML file.
# Make sure you have the Kubeflow SDK installed:
# pip install kfp

# Set the name for the output file
OUTPUT_FILE="ecommerce_pipeline.yaml"

echo "Compiling pipeline.py to ${OUTPUT_FILE}..."

kfp dsl compile \
    --python-function ecommerce_ai_pipeline \
    pipeline.py \
    --output "${OUTPUT_FILE}"

# Check if compilation was successful
if [ $? -eq 0 ]; then
    echo "Pipeline compiled successfully to ${OUTPUT_FILE}"
    echo "You can now upload this file to the Kubeflow Pipelines UI."
else
    echo "Pipeline compilation failed."
fi