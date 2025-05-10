import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService # Specific import for Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager # For Firefox
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- Configuration ---
BASE_URL = "https://www.footlocker.co.uk"
CATEGORY_URL = f"{BASE_URL}/en/category/men/clothing.html"
MAX_PRODUCTS_TO_SCRAPE = 20 # Set a limit for demonstration, set to None for all
PAGE_LOAD_TIMEOUT = 30 # Increased timeout a bit
IMPLICIT_WAIT = 5 # General implicit wait

# --- Helper Function to handle cookie banner ---
def accept_cookies(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "onetrust-banner-sdk"))
        )
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        accept_button.click()
        print("Cookie banner accepted.")
        time.sleep(2)
    except Exception as e:
        print(f"Cookie banner not found or could not be clicked: {e}")

# --- Selenium Setup for Firefox ---
options = webdriver.FirefoxOptions()
options.add_argument("-headless")  # Run in headless mode
options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0")


try:
    driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
    driver.implicitly_wait(IMPLICIT_WAIT) # Set an implicit wait
    print("Firefox WebDriver initialized.")
except Exception as e:
    print(f"Error initializing Firefox WebDriver: {e}")
    exit()

product_links = []
all_product_data = []

try:
    # 1. Navigate to Category Page and Get Product Links
    print(f"Navigating to category page: {CATEGORY_URL}")
    driver.get(CATEGORY_URL)
    time.sleep(3) # Initial wait

    accept_cookies(driver)

    print("Waiting for product list to load...")
    WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "ul.row li.product-container"))
    )
    print("Product list found.")

    # It's generally more robust to get all links first, then iterate
    # because navigating away might make the original elements stale.
    product_list_items = driver.find_elements(By.CSS_SELECTOR, "ul.row li.product-container")
    for item in product_list_items:
        try:
            link_element = item.find_element(By.CSS_SELECTOR, "a.ProductCard-link")
            href = link_element.get_attribute('href')
            if href:
                full_url = urljoin(BASE_URL, href)
                if full_url not in product_links:
                    product_links.append(full_url)
        except Exception as e:
            print(f"Could not find link in a product container: {e}")

    print(f"Found {len(product_links)} unique product links.")

    if MAX_PRODUCTS_TO_SCRAPE and len(product_links) > MAX_PRODUCTS_TO_SCRAPE:
        product_links = product_links[:MAX_PRODUCTS_TO_SCRAPE]
        print(f"Scraping a maximum of {MAX_PRODUCTS_TO_SCRAPE} products.")


    # 2. Scrape Individual Product Pages by navigating to each link
    for i, link_url in enumerate(product_links):
        print(f"\nScraping product {i+1}/{len(product_links)}: {link_url}")
        
        try:
            driver.get(link_url) # Navigate to the product page

            # Wait for essential elements of the product page
            WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "pageTitle"))
            )
            WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProductDetails-form__price div.ProductPrice"))
            )
            # Rating might not always be present
            # WebDriverWait(driver, 5).until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, "div.bv_avgRating_component_container"))
            # )
            print(f"  Page loaded: {link_url}")
            time.sleep(1) # Small delay for JS rendering
        except Exception as e:
            print(f"  Timeout or error loading page {link_url}: {e}")
            all_product_data.append({
                'url': link_url,
                'name': 'Error loading page',
                'price': 'N/A',
                'rating': 'N/A',
                'reviews_count': 'N/A'
            })
            continue # Skip to next product

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        product_data = {'url': link_url}

        # Extract Name
        name_tag_h1 = soup.find("h1", id="pageTitle")
        if name_tag_h1:
            primary_name_tag = name_tag_h1.find("span", class_="ProductName-primary")
            alt_name_tag = name_tag_h1.find("span", class_="ProductName-alt")
            
            name_text = primary_name_tag.text.strip() if primary_name_tag else ''
            alt_text = alt_name_tag.text.strip() if alt_name_tag else ''
            
            product_data['name'] = f"{name_text} ({alt_text})" if alt_text else name_text
            if not product_data['name']:
                product_data['name'] = 'N/A (Name structure not found)'
        else:
            product_data['name'] = 'N/A (pageTitle H1 not found)'


        # Extract Price
        price_container = soup.select_one("div.ProductDetails-form__price div.ProductPrice")
        if price_container:
            price_span = price_container.find("span") # The first span usually has the price
            product_data['price'] = price_span.text.strip() if price_span else 'N/A'
            
            vat_span = price_container.find("span", class_="ProductPrice-taxLabel")
            if vat_span and product_data['price'] != 'N/A': # Add VAT label if price was found
                 product_data['price'] += f" ({vat_span.text.strip()})"
        else:
            product_data['price'] = 'N/A'

        # Extract Rating
        rating_tag = soup.select_one("div.bv_avgRating_component_container.notranslate")
        product_data['rating'] = rating_tag.text.strip() if rating_tag else 'N/A'
        
        # Extract Number of Reviews
        reviews_count_tag = soup.select_one("button.bv_main_container_row_flex div.bv_numReviews_text")
        if not reviews_count_tag: # Fallback selector if the first one doesn't work
            reviews_count_tag = soup.select_one(".ProductDetails-header-V2-metadata .bv_numReviews_text")
        product_data['reviews_count'] = reviews_count_tag.text.strip().replace('(', '').replace(')', '') if reviews_count_tag else 'N/A'

        print(f"    Name: {product_data['name']}")
        print(f"    Price: {product_data['price']}")
        print(f"    Rating: {product_data['rating']}")
        print(f"    Reviews: {product_data['reviews_count']}")
        
        all_product_data.append(product_data)
        time.sleep(1) # Politeness delay

except Exception as e:
    print(f"An error occurred during scraping: {e}")

finally:
    if 'driver' in locals() and driver:
        print("Closing Firefox WebDriver.")
        driver.quit()

# --- Create DataFrame and Save ---
if all_product_data:
    df = pd.DataFrame(all_product_data)
    print("\n--- Scraped Data ---")
    print(df)
    df.to_csv("footlocker_clothing_men_firefox.csv", index=False)
    print("\nData saved to footlocker_clothing_men_firefox.csv")
else:
    print("No data was scraped.")