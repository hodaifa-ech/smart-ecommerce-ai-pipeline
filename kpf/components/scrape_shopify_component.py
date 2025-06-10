from kfp.dsl import component, Output, Dataset
from typing import List

@component(
    base_image="python:3.9",
    packages_to_install=["pandas==2.2.2", "requests==2.31.0"],
)
def scrape_shopify_component(
    store_domains: List[str],
    output_data: Output[Dataset],
):
    """A Kubeflow component to scrape product data from Shopify stores."""
    import requests
    import json
    import csv
    import time
    import logging
    import os
    from urllib.parse import urlparse, urlunparse
    import pandas as pd

    # --- Your logic from utils/fetch_shopify_product_data.py goes here ---
    # We will wrap the core logic into this function.
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # (Include your helper functions: construct_url, fetch_products, flatten_data)
    # ...
    
    all_flattened_data = []
    for domain in store_domains:
        logging.info(f"--- Processing domain: {domain} ---")
        # url = construct_url(domain)
        # if not url: continue
        # products_data = fetch_products(url)
        # ... your fetching logic ...
        # flattened = flatten_data(products_data, domain)
        # all_flattened_data.extend(flattened)
        time.sleep(2)

    if all_flattened_data:
        df = pd.DataFrame(all_flattened_data)
        # ** KEY CHANGE: Save to the path provided by the Output[Dataset] artifact **
        df.to_csv(output_data.path, index=False, encoding='utf-8-sig')
        print(f"Shopify scraping completed. Saved {len(df)} rows to {output_data.path}")
    else:
        print("No Shopify data was scraped.")
        pd.DataFrame([]).to_csv(output_data.path, index=False)