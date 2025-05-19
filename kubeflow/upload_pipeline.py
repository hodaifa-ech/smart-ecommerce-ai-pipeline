import kfp
from kfp import client
import os

def upload_pipeline():
    # Get the Kubeflow endpoint
    host = "http://localhost:8080"  # Default Kubeflow pipelines endpoint
    
    # Create client
    client = kfp.Client(host=host)
    
    # Compile the pipeline
    kfp.compiler.Compiler().compile(
        pipeline_func=product_attractiveness_pipeline,
        package_path='product-attractiveness-pipeline.yaml'
    )
    
    # Upload the pipeline
    pipeline = client.upload_pipeline(
        pipeline_package_path='product-attractiveness-pipeline.yaml',
        pipeline_name='product-attractiveness-pipeline',
        description='Pipeline for product attractiveness classification'
    )
    
    print(f"Pipeline uploaded successfully! Pipeline ID: {pipeline.id}")
    return pipeline.id

if __name__ == '__main__':
    upload_pipeline() 