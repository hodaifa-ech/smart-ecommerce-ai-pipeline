import kfp
from kfp import dsl
from kfp.components import func_to_container_op
import time
import os

# Set up the client
client = kfp.Client(host='http://localhost:8081')

@func_to_container_op
def data_scraping():
    return "Data scraping completed"

@func_to_container_op
def data_processing():
    return "Data processing completed"

@func_to_container_op
def ml_training():
    return "ML training completed"

@func_to_container_op
def model_evaluation():
    return "Model evaluation completed"

@func_to_container_op
def deploy_model():
    return "Model deployment completed"

@dsl.pipeline(
    name='Smart E-commerce Pipeline',
    description='Pipeline for e-commerce data processing and ML'
)
def smart_ecommerce_pipeline():
    # Define the pipeline steps
    scraping_task = data_scraping()
    processing_task = data_processing().after(scraping_task)
    training_task = ml_training().after(processing_task)
    evaluation_task = model_evaluation().after(training_task)
    deploy_task = deploy_model().after(evaluation_task)

def upload_and_run_pipeline():
    # Compile the pipeline
    kfp.compiler.Compiler().compile(smart_ecommerce_pipeline, 'smart_ecommerce_pipeline.yaml')
    
    # Upload the pipeline
    pipeline_name = 'Smart E-commerce Pipeline'
    pipeline_version = f'v{int(time.time())}'  # Create unique version
    
    try:
        # Upload pipeline
        pipeline = client.upload_pipeline(
            pipeline_package_path='smart_ecommerce_pipeline.yaml',
            pipeline_name=pipeline_name,
            description='Automated e-commerce pipeline'
        )
        print(f"Pipeline uploaded successfully: {pipeline_name}")
        
        # Create an experiment if it doesn't exist
        experiment_name = 'Smart E-commerce Experiments'
        experiment = client.create_experiment(name=experiment_name)
        
        # Run the pipeline
        run_name = f'Run_{pipeline_version}'
        run = client.run_pipeline(
            experiment_id=experiment.id,
            job_name=run_name,
            pipeline_id=pipeline.id
        )
        print(f"Pipeline run started: {run_name}")
        
        # Monitor the run
        while True:
            run_status = client.get_run(run.id)
            if run_status.status in ['Succeeded', 'Failed', 'Error']:
                print(f"Pipeline run completed with status: {run_status.status}")
                break
            print(f"Pipeline status: {run_status.status}")
            time.sleep(30)  # Check every 30 seconds
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    upload_and_run_pipeline() 