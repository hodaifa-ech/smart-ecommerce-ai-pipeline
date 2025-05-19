import kfp
from kfp import client
import os

def run_pipeline(pipeline_id):
    # Get the Kubeflow endpoint
    host = "http://localhost:8080"  # Default Kubeflow pipelines endpoint
    
    # Create client
    client = kfp.Client(host=host)
    
    # Create an experiment
    experiment = client.create_experiment(
        name='product-attractiveness-experiment',
        description='Experiment for product attractiveness classification'
    )
    
    # Run the pipeline
    run = client.run_pipeline(
        experiment_id=experiment.id,
        job_name='product-attractiveness-run',
        pipeline_id=pipeline_id,
        params={
            'input_data': '/app/data/aliexpress_multi_page_firefox.csv',
            'output_data': '/app/data/processed_data.csv',
            'model_output': '/app/models/model.joblib',
            'metrics_output': '/app/metrics/metrics.json'
        }
    )
    
    print(f"Pipeline run started! Run ID: {run.id}")
    return run.id

if __name__ == '__main__':
    # You can get the pipeline_id from the upload_pipeline.py output
    pipeline_id = input("Enter the pipeline ID: ")
    run_pipeline(pipeline_id) 