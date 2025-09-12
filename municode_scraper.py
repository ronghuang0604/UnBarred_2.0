import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- Configuration ---
download_directory = "/Users/ronghuang/Desktop/210/municode_pdfs"
if not os.path.exists(download_directory):
    os.makedirs(download_directory)

chrome_options = webdriver.ChromeOptions()
prefs = {"download.default_directory": download_directory}
chrome_options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 20)

# --- Get County Links ---
print("Navigating to the main Florida page...")
driver.get("https://library.municode.com/fl")
county_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li a.index-link")))
county_urls = [element.get_attribute('href') for element in county_elements]
print(f"Found {len(county_urls)} county/city links to process.")

# --- Loop Through Each County ---
for url in county_urls:
    print(f"\n--- Processing: {url} ---")
    try:
        driver.get(url)

        all_download_buttons = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button.btn-pdf-download"))
        )        
        visible_buttons = [btn for btn in all_download_buttons if btn.is_displayed()]        
        print(f"  Found {len(visible_buttons)} VISIBLE download button(s) on this page.")

        for i in range(len(visible_buttons)):
            buttons_to_click = [btn for btn in driver.find_elements(By.CSS_SELECTOR, "button.btn-pdf-download") if btn.is_displayed()]
            button_to_click = buttons_to_click[i]
            
            print(f"  -> Clicking visible button #{i+1}...")
            button_to_click.click()

            modal_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.get-pdf-download-btn")))
            modal_button.click()
            print("    Download triggered.")
            
            time.sleep(30) # Wait for the download to finish before trying the next one


    except TimeoutException:
        print(f"  -> No download buttons found on this page. Skipping.")
        continue
    except Exception as e:
        print(f"  -> An error occurred on this page: {e}")
        continue

print("\nAll URLs have been processed.")
driver.quit()