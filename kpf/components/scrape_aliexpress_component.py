from kfp.dsl import component, Output, Dataset

# This decorator defines the component's interface and environment.
# We specify the packages that need to be installed in the container for this component to run.
@component(
    base_image="python:3.9",
    packages_to_install=[
        "pandas==2.2.2",
        "selenium==4.21.0",
        "webdriver-manager==4.0.1",
        "beautifulsoup4==4.12.3",
    ],
)
def scrape_aliexpress_component(
    max_pages: int,
    output_data: Output[Dataset], # Kubeflow provides a path for the output artifact
):
    """
    A Kubeflow component to scrape top-selling products from AliExpress.
    It wraps the original scraping logic.
    """
    import time
    import pandas as pd
    from selenium import webdriver
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.firefox import GeckoDriverManager
    from bs4 import BeautifulSoup

    # --- Your scraping logic from utils/ali_express.py goes here ---
    # The main change is to use the `output_data.path` provided by Kubeflow
    # instead of a hardcoded filename.

    BASE_URL = "https://fr.aliexpress.com"
    SEARCH_QUERY_BASE_URL = f"{BASE_URL}/w/wholesale-top-selling-items.html"
    PAGE_LOAD_TIMEOUT = 40
    IMPLICIT_WAIT = 10
    inter_page_delay = 5
    headless = True # Must be headless to run in a cluster

    options = webdriver.FirefoxOptions()
    if headless:
        options.add_argument("-headless")
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0")

    all_product_data = []
    driver = None

    try:
        print("Initializing Firefox WebDriver for Kubeflow component...")
        # Note: In a real cluster, you might need a more robust way to handle the driver,
        # like connecting to a Selenium Grid, but GeckoDriverManager can work.
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        driver.implicitly_wait(IMPLICIT_WAIT)
        print("Firefox WebDriver initialized.")

        for page_num in range(1, max_pages + 1):
            current_page_url = f"{SEARCH_QUERY_BASE_URL}?page={page_num}"
            print(f"\nProcessing Page {page_num}/{max_pages}: {current_page_url}")
            
            try:
                driver.get(current_page_url)
                time.sleep(10 + (page_num // 5 * 2))
                WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div#card-list"))
                )
                page_source_current = driver.page_source
            except Exception as e_page:
                print(f"  Error on page {page_num}: {e_page}")
                continue

            if not page_source_current:
                continue

            soup = BeautifulSoup(page_source_current, 'html.parser')
            container = soup.find('div', id='card-list')
            if not container:
                continue

            product_cards = container.find_all('div', class_='hm_bu search-item-card-wrapper-gallery', recursive=False)
            
            # (The inner loop for extracting data is omitted for brevity but should be included)
            # ... your data extraction logic for each card ...
            for card in product_cards:
                # Assuming 'data' dict is created here as in your original script
                data = {} # Placeholder for your data extraction logic
                # ...
                all_product_data.append(data)


            print(f"  Extracted {len(product_cards)} products from page {page_num}")
            if page_num < max_pages:
                time.sleep(inter_page_delay)
    
    except Exception as e:
        print(f"Unexpected error in component: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

    if all_product_data:
        df = pd.DataFrame(all_product_data)
        # ** KEY CHANGE: Save to the path provided by the Output[Dataset] artifact **
        df.to_csv(output_data.path, index=False, encoding='utf-8-sig')
        print(f"\nScraping completed: {len(df)} products saved to artifact path: {output_data.path}")
    else:
        print("No data was scraped.")
        # Create an empty file to signify completion
        pd.DataFrame([]).to_csv(output_data.path, index=False)