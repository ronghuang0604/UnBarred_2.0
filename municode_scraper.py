import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, InvalidSessionIdException

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
failed_urls = []

# example_urls = [
#     'https://library.municode.com/fl/cape_coral',
#     'https://library.municode.com/fl/fanning_springs',
#     'https://library.municode.com/fl/apalachicola',
#     'https://library.municode.com/fl/fort_meade'
# ]

# --- Loop Through Each County ---
for url in county_urls:
    print(f"\n--- Processing: {url} ---")
    try:
        driver.get(url)
        all_download_buttons = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button.btn-pdf-download")))
        visible_buttons = [btn for btn in all_download_buttons if btn.is_displayed()]
        num_buttons_to_click = len(visible_buttons)
        print(f"  Found {num_buttons_to_click} VISIBLE download button(s) on this page.")

        for i in range(num_buttons_to_click):
            # Re-find visible buttons to prevent errors caused by the race condition between Selenium and JavaScript rendering
            current_visible_buttons = [btn for btn in driver.find_elements(By.CSS_SELECTOR, "button.btn-pdf-download") if btn.is_displayed()]
            if i >= len(current_visible_buttons):
                print("  -> A button disappeared after a page refresh. Ending loop for this page.")
                break

            button_to_click = current_visible_buttons[i]                
            print(f"  -> Clicking visible button #{i+1}...")
            button_to_click.click()

            # Handle the modal pop-up
            modal_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.get-pdf-download-btn")))
            modal_button.click()
            print("    Download triggered.")    
            time.sleep(30) # Wait for the download to finish
    except (TimeoutException, StaleElementReferenceException):
        print(f"  -> No download buttons found on this page. Skipping.")
        failed_urls.append(url)
        continue
    except InvalidSessionIdException:
        print(f"  -> SESSION DIED. The browser may have crashed. Skipping this URL.")
        failed_urls.append(url)
        break 
    except Exception as e:
        print(f"  -> An unknown error occurred on this page: {e}")
        failed_urls.append(url)
        continue

# --- Wait for the last file to finish downloading ---
print("\n--- All downloads triggered. Waiting for files to complete... ---")
start_time = time.time()
while any(f.endswith('.crdownload') for f in os.listdir(download_directory)):
    if time.time() - start_time > 90: # 90 seconds timeout
        print("!!! Final wait timed out. Some files may not have completed. !!!")
        break
    print("  - Downloads still in progress, checking again in 10 seconds...")
    time.sleep(10)

print("All downloads have finished.")


# --- Write failed urls to a text file ---
if failed_urls:
    print(f"\n--- Encountered {len(failed_urls)} errors. Saving details to failed_urls.txt ---")
    with open("failed_urls.txt", "w") as f:
        for item in failed_urls:
            f.write(f"{item}\n")

print("\nAll URLs have been processed.")
driver.quit()