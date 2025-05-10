import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup

def scrape_aliexpress_top_selling(
    max_pages=20,
    output_csv="aliexpress_multi_page_firefox.csv",
    inter_page_delay=5,
    headless=True
):
    BASE_URL = "https://fr.aliexpress.com"
    SEARCH_QUERY_BASE_URL = f"{BASE_URL}/w/wholesale-top-selling-items.html"
    PAGE_LOAD_TIMEOUT = 40
    IMPLICIT_WAIT = 10

    options = webdriver.FirefoxOptions()
    if headless:
        options.add_argument("-headless")
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0")

    all_product_data = []
    driver = None

    try:
        print("Initializing Firefox WebDriver...")
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        driver.implicitly_wait(IMPLICIT_WAIT)
        print("Firefox WebDriver initialized.")

        for page_num in range(1, max_pages + 1):
            current_page_url = f"{SEARCH_QUERY_BASE_URL}?page={page_num}"
            print(f"\nProcessing Page {page_num}/{max_pages}: {current_page_url}")
            page_source_current = None

            try:
                driver.get(current_page_url)
                print(f"  Waiting for page to load (10-15s)...")
                time.sleep(10 + (page_num // 5 * 2))

                WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div#card-list"))
                )

                page_source_current = driver.page_source
            except Exception as e_page:
                print(f"  Error on page {page_num}: {e_page}")
                time.sleep(inter_page_delay)
                continue

            if not page_source_current:
                time.sleep(inter_page_delay)
                continue

            soup = BeautifulSoup(page_source_current, 'html.parser')
            container = soup.find('div', id='card-list')
            if not container:
                time.sleep(inter_page_delay)
                continue

            product_cards = container.find_all('div', class_='hm_bu search-item-card-wrapper-gallery', recursive=False)

            for card in product_cards:
                data = {'page_number': page_num}

                link = card.find('a', class_='jr_g')
                data['url'] = (
                    "https:" + link['href'] if link and link.has_attr('href') and link['href'].startswith("//")
                    else BASE_URL + link['href'] if link and link.has_attr('href') and link['href'].startswith("/")
                    else link['href'] if link and link.has_attr('href')
                    else 'N/A'
                )

                name_tag = card.find('h3', class_='jr_kp')
                data['name'] = name_tag.text.strip() if name_tag else 'N/A'

                price_div = card.find('div', class_='jr_kr')
                if price_div:
                    spans = price_div.find_all('span')
                    if len(spans) >= 2:
                        currency = spans[0].text.strip()
                        main = spans[1].text.strip()
                        decimal = f".{spans[3].text.strip()}" if len(spans) == 4 and spans[2].text.strip() == '.' else ''
                        data['price'] = f"{currency} {main}{decimal}"
                    else:
                        data['price'] = price_div.get_text(separator=' ', strip=True).replace(" . ", ".")
                else:
                    data['price'] = 'N/A'

                orig = card.find('div', class_='jr_ks')
                data['original_price'] = orig.text.strip() if orig else 'N/A'

                discount = card.find('span', class_='jr_kt')
                data['discount_percentage'] = discount.text.strip() if discount else 'N/A'

                rating = card.find('span', class_='jr_kf')
                data['rating'] = rating.text.strip() if rating else 'N/A'

                sales = card.find('span', class_='jr_j7')
                data['sales_info'] = sales.text.strip().lstrip('+ ') if sales else 'N/A'

                img = card.find('img', class_='mm_be')
                data['image_url'] = (
                    "https:" + img['src'] if img and img.has_attr('src') and img['src'].startswith("//")
                    else BASE_URL + img['src'] if img and img.has_attr('src') and img['src'].startswith("/")
                    else img['src'] if img and img.has_attr('src')
                    else 'N/A'
                )

                additional_info = []
                for tag in card.select('div.jr_ae > span.jr_ae'):
                    if tag.text.strip(): additional_info.append(tag.text.strip())

                for div in card.find_all('div', class_='jr_k2'):
                    img_mv = div.find('img', class_='ms_mv')
                    span_mu = div.find('span', class_='ms_mu')
                    if img_mv and img_mv.get('title'):
                        additional_info.append(img_mv['title'].strip())
                    elif span_mu:
                        additional_info.append(span_mu.get_text(strip=True))

                data['additional_badges'] = " | ".join(set(additional_info)) if additional_info else "N/A"

                all_product_data.append(data)

            print(f"  Extracted {len(product_cards)} products from page {page_num}")
            if page_num < max_pages:
                time.sleep(inter_page_delay)

    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

    if all_product_data:
        df = pd.DataFrame(all_product_data)
        df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        print(f"\nScraping completed: {len(df)} products saved to {output_csv}")
    else:
        print("No data was scraped.")

# Example usage:
# scrape_aliexpress_top_selling(max_pages=5, output_csv="test.csv")
