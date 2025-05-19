import kfp
from kfp import client
import os
from pipeline import product_attractiveness_pipeline # <--- ADD THIS IMPORT

def upload_pipeline():
    # Get the Kubeflow endpoint
    host = os.environ.get("KFP_ENDPOINT", "http://localhost:8080") # Use env var or default
    
    # Create client
    client_instance = kfp.Client(host=host) # Renamed to avoid conflict with kfp.client module
    
    # Compile the pipeline
    # This assumes product_attractiveness_pipeline is now imported
    kfp.compiler.Compiler().compile(
        pipeline_func=product_attractiveness_pipeline,
        package_path='product-attractiveness-pipeline.yaml' # This will be created in the CWD
    )
    
    # Upload the pipeline
    pipeline = client_instance.upload_pipeline(
        pipeline_package_path='product-attractiveness-pipeline.yaml',
        pipeline_name='product-attractiveness-pipeline',
        description='Pipeline for product attractiveness classification'
    )
    
    print(f"Pipeline uploaded successfully! Pipeline ID: {pipeline.id}")
    return pipeline.id

if __name__ == '__main__':
    upload_pipeline()