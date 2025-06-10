from kfp import dsl
from kfp.dsl import pipeline
from components.scrape_aliexpress_component import scrape_aliexpress_component
from components.train_classifier_component import train_classifier_component
# from components.scrape_shopify_component import scrape_shopify_component # Can be added similarly

# The pipeline decorator specifies the pipeline's name and root.
# The pipeline root is where Kubeflow will store all the artifacts (outputs)
# of this pipeline. You MUST configure this to a persistent location like a
# cloud storage bucket (GCS, S3) or a mounted PVC.
@pipeline(
    name="E-commerce AI Pipeline",
    description="A pipeline to scrape product data and train an attractiveness model.",
    pipeline_root="gs://your-kubeflow-artifacts-bucket/ecommerce-pipeline" # IMPORTANT: CHANGE THIS
)
def ecommerce_ai_pipeline(
    aliexpress_max_pages: int = 5,
):
    """Defines the workflow of the e-commerce AI pipeline."""

    # 1. Scrape data from AliExpress
    scrape_task = scrape_aliexpress_component(
        max_pages=aliexpress_max_pages
    )
    # Set a display name for clarity in the UI
    scrape_task.set_display_name("Scrape AliExpress Top-Selling")


    # 2. Train the model using the output from the scraping task
    # The output of one task is connected to the input of the next.
    train_task = train_classifier_component(
        input_dataset=scrape_task.outputs['output_data']
    )
    train_task.set_display_name("Train Product Classifier")

    # You could add the Shopify scraper here as a parallel task:
    # shopify_scrape_task = scrape_shopify_component(...)
    # And then perhaps have another component that merges the two datasets.