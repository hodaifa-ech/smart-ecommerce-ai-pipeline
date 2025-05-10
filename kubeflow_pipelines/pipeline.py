import kfp
from kfp import dsl
from kfp.components import func_to_container_op

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

if __name__ == '__main__':
    # Compile the pipeline
    kfp.compiler.Compiler().compile(smart_ecommerce_pipeline, 'smart_ecommerce_pipeline.yaml') 