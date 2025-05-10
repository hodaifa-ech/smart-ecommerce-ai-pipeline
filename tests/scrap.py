import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import traceback # For detailed error logging

# --- Configuration Constants (can be overridden when calling scrap) ---
DEFAULT_BASE_URL = "https://www.footlocker.co.uk"
DEFAULT_MAX_PRODUCTS_TO_SCRAPE = 20
DEFAULT_PAGE_LOAD_TIMEOUT = 30
DEFAULT_IMPLICIT_WAIT = 5
DEFAULT_CSV_FILENAME = "footlocker_scraped_products.csv"

# --- Helper Function (internal to scraper module) ---
def _accept_cookies(driver):
    try:
        cookie_banner_id = "onetrust-banner-sdk"
        accept_button_id = "onetrust-accept-btn-handler"

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, cookie_banner_id))
        )
        print("Cookie banner found.")
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, accept_button_id))
        )
        accept_button.click()
        print("Cookie banner accepted.")
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.ID, cookie_banner_id))
        )
        print("Cookie banner confirmed dismissed.")
    except Exception as e:
        print(f"Cookie banner not found, could not be clicked, or did not disappear: {e}")

def scrap_products(
    base_url=DEFAULT_BASE_URL,
    max_products_to_scrape=DEFAULT_MAX_PRODUCTS_TO_SCRAPE,
    page_load_timeout=DEFAULT_PAGE_LOAD_TIMEOUT,
    implicit_wait=DEFAULT_IMPLICIT_WAIT,
    save_to_csv=True,
    csv_filename=DEFAULT_CSV_FILENAME
):
    """
    Scrapes product information from the specified category URL on Footlocker.

    Args:
        base_url (str): The base URL of the website.
        max_products_to_scrape (int): Maximum number of products to scrape.
        page_load_timeout (int): Timeout in seconds for page loads.
        implicit_wait (int): Implicit wait time for Selenium.
        save_to_csv (bool): Whether to save the scraped data to a CSV file.
        csv_filename (str): Filename for the CSV if save_to_csv is True.

    Returns:
        list: A list of dictionaries, where each dictionary represents a scraped product.
              Returns an empty list if errors occur or no products are found.
    """
    category_url = f"{base_url}/en/category/men/clothing.html"

    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0")

    driver = None
    all_product_data = []

    try:
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        driver.implicitly_wait(implicit_wait)
        print("Firefox WebDriver initialized for scraping.")
    except Exception as e:
        print(f"Error initializing Firefox WebDriver: {e}")
        return []

    try:
        print(f"Navigating to category page: {category_url}")
        driver.get(category_url)
        _accept_cookies(driver)

        print("Waiting for product list to load...")
        WebDriverWait(driver, page_load_timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.ProductCardListing-grid"))
        )
        print("Product list container found.")

        product_list_items = driver.find_elements(By.CSS_SELECTOR, "ul.ProductCardListing-grid li.ProductCard")
        print(f"Found {len(product_list_items)} potential product items on the page.")

        product_links = []
        for item in product_list_items:
            if max_products_to_scrape is not None and len(product_links) >= max_products_to_scrape:
                break
            try:
                link_element = item.find_element(By.CSS_SELECTOR, "a.ProductCard-link")
                href = link_element.get_attribute('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if full_url not in product_links:
                        product_links.append(full_url)
            except Exception as e:
                print(f"Could not find link in a product container: {e}")

        print(f"Collected {len(product_links)} unique product links to scrape.")

        if not product_links:
            print("No product links found. Exiting scraping process.")
            return []
        
        # Adjust if max_products_to_scrape was hit during link collection or is smaller than collected
        if max_products_to_scrape is not None and len(product_links) > max_products_to_scrape:
            product_links = product_links[:max_products_to_scrape]
            print(f"Limiting scraping to {len(product_links)} products based on MAX_PRODUCTS_TO_SCRAPE.")


        for i, link_url in enumerate(product_links):
            print(f"\nScraping product {i+1}/{len(product_links)}: {link_url}")
            product_data = {'url': link_url, 'name': 'N/A', 'price': 'N/A', 'rating': 'N/A', 'reviews_count': 'N/A'}

            try:
                driver.get(link_url)
                WebDriverWait(driver, page_load_timeout).until(
                    EC.presence_of_element_located((By.ID, "pageTitle"))
                )
                WebDriverWait(driver, page_load_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProductDetails-form__price div.ProductPrice"))
                )
                try:
                    WebDriverWait(driver, 10).until( # Shorter timeout for non-critical elements
                        EC.any_of(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.bv_main_container_row_flex")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.bv_avgRating_component_container")),
                            EC.presence_of_element_located((By.ID, "BVRRContainer"))
                        )
                    )
                except Exception:
                    print(f"  Bazaarvoice elements (ratings/reviews) not explicitly found after wait for {link_url}.")

                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')

                # Extract Name
                name_tag_h1 = soup.find("h1", id="pageTitle")
                if name_tag_h1:
                    primary = name_tag_h1.find("span", class_="ProductName-primary")
                    alt = name_tag_h1.find("span", class_="ProductName-alt")
                    name_parts = [tag.text.strip() for tag in [primary, alt] if tag and tag.text.strip()]
                    product_data['name'] = " ".join(name_parts) if name_parts else 'N/A (Name structure not found)'
                else:
                    product_data['name'] = 'N/A (pageTitle H1 not found)'

                # Extract Price
                price_cont = soup.select_one("div.ProductDetails-form__price div.ProductPrice")
                if price_cont:
                    price_span = price_cont.find("span", class_=lambda x: x and ('ProductPrice-price' in x or 'ProductPrice-finalPrice' in x))
                    if not price_span: price_span = price_cont.find("span") # Fallback
                    product_data['price'] = price_span.text.strip() if price_span else 'N/A'
                    vat_span = price_cont.find("span", class_="ProductPrice-taxLabel")
                    if vat_span and product_data['price'] != 'N/A':
                        product_data['price'] += f" ({vat_span.text.strip()})"
                else:
                    product_data['price'] = 'N/A'

                # Extract Rating
                rating_tag = soup.select_one("div.bv_avgRating_component_container.notranslate")
                product_data['rating'] = rating_tag.text.strip() if rating_tag else 'N/A'
                
                # Extract Number of Reviews
                rev_count_tag = soup.select_one("button.bv_main_container_row_flex div.bv_numReviews_text, .ProductDetails-header-V2-metadata .bv_numReviews_text")
                if rev_count_tag:
                    product_data['reviews_count'] = rev_count_tag.text.strip().replace('(', '').replace(')', '')
                else:
                    rev_label = soup.find("span", class_="bv-rating-label")
                    if rev_label and "review" in rev_label.text.lower():
                        product_data['reviews_count'] = rev_label.text.strip().replace('(', '').replace(')', '')
                    else:
                        product_data['reviews_count'] = 'N/A'
                
                print(f"    Data: Name='{product_data['name']}', Price='{product_data['price']}', Rating='{product_data['rating']}', Reviews='{product_data['reviews_count']}'")

            except Exception as e:
                print(f"  Error processing page {link_url}: {e}")
                if product_data['name'] == 'N/A': product_data['name'] = 'Error processing page'
            
            all_product_data.append(product_data)
            time.sleep(0.3) # Politeness delay

    except Exception as e:
        print(f"An unexpected error occurred during the scraping process: {e}")
        traceback.print_exc()
    finally:
        if driver:
            print("Closing Firefox WebDriver for scraping.")
            driver.quit()

    if save_to_csv and all_product_data:
        df = pd.DataFrame(all_product_data)
        try:
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"\nScraped data saved to {csv_filename}")
        except Exception as e:
            print(f"Error saving data to CSV '{csv_filename}': {e}")
    elif save_to_csv:
        print(f"No data was scraped, so CSV '{csv_filename}' was not created.")

    return all_product_data

if __name__ == '__main__':
    print("--- Testing Scraper Module Independently ---")
    # Example: Scrape 2 products and save to a test CSV
    test_scraped_data = scrap_products(max_products_to_scrape=2, 
                                       save_to_csv=True, 
                                       csv_filename="test_scraper_output.csv")
    if test_scraped_data:
        print(f"\nSuccessfully scraped {len(test_scraped_data)} products during test.")
        for i, item in enumerate(test_scraped_data):
            print(f"  Product {i+1}: {item['name']}")
    else:
        print("\nScraper test completed, but no data was returned.")
    print("--- Scraper Module Test Finished ---")