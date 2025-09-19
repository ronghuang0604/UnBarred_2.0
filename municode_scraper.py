import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, InvalidSessionIdException

# --- Configuration ---
download_directory = os.path.abspath("municode_pdfs2")
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
county_names = [el.text for el in county_elements]
county_urls = [element.get_attribute('href') for element in county_elements]
print(f"Found {len(county_urls)} county/city links to process.")
# print(county_urls)
failed_urls = []


# ----------------- FL COUNTIES NOT ON MUNICODE -----------------
# florida_counties = [
#     "Alachua County",
#     "Baker County",
#     "Bay County",
#     "Bradford County",
#     "Brevard County",
#     "Broward County",
#     "Calhoun County",
#     "Charlotte County",
#     "Citrus County",
#     "Clay County",
#     "Collier County",
#     "Columbia County",
#     "DeSoto County",
#     "Dixie County",
#     "Duval County",
#     "Escambia County",
#     "Flagler County",
#     "Franklin County",
#     "Gadsden County",
#     "Gilchrist County",
#     "Glades County",
#     "Gulf County",
#     "Hamilton County",
#     "Hardee County",
#     "Hendry County",
#     "Hernando County",
#     "Highlands County",
#     "Hillsborough County",
#     "Holmes County",
#     "Indian River County",
#     "Jackson County",
#     "Jefferson County",
#     "Lafayette County",
#     "Lake County",
#     "Lee County",
#     "Leon County",
#     "Levy County",
#     "Liberty County",
#     "Madison County",
#     "Manatee County",
#     "Marion County",
#     "Martin County",
#     "Miami-Dade County",
#     "Monroe County",
#     "Nassau County",
#     "Okaloosa County",
#     "Okeechobee County",
#     "Orange County",
#     "Osceola County",
#     "Palm Beach County",
#     "Pasco County",
#     "Pinellas County",
#     "Polk County",
#     "Putnam County",
#     "Santa Rosa County",
#     "Sarasota County",
#     "Seminole County",
#     "St. Johns County",
#     "St. Lucie County",
#     "Sumter County",
#     "Suwannee County",
#     "Taylor County",
#     "Union County",
#     "Volusia County",
#     "Wakulla County",
#     "Walton County",
#     "Washington County"
# ]

# counties_not_on_municode = list(set(florida_counties) - set(county_names))
# print(counties_not_on_municode)
# ----------------- FL COUNTIES NOT ON MUNICODE -----------------


# ----------------- EDGE CASES NOT HANDLED -----------------
edge_cases_not_handled = [
    'https://library.municode.com/fl/fanning_springs', # no download buttons
    'https://library.municode.com/fl/ocoee', # browse then no download button
    'https://library.municode.com/fl/escambia_county',
    'https://library.municode.com/fl/south_daytona', # browse then download button
]
# ----------------- EDGE CASES NOT HANDLED -----------------


# ------------------ RESUME SCRAPING ------------------
def slice_urls(urls, start_url=None, end_url=None):
    """Return sublist of urls between start_url and end_url (inclusive)."""
    start_idx = 0
    end_idx = len(urls)  # default: go to the end
    
    if start_url in urls:
        start_idx = urls.index(start_url)
    if end_url in urls:
        end_idx = urls.index(end_url) + 1  # +1 to include the end
    
    return urls[start_idx:end_idx]

start_url = 'https://library.municode.com/fl/macclenny'
end_url = 'https://library.municode.com/fl/mulberry'
urls_to_process = slice_urls(county_urls, start_url, end_url)
print(f"Resuming processing from {start_url} to {end_url} ({len(urls_to_process)} links in total).")
# --------------------- RESUME SCRAPING ---------------------


# --- Loop Through Each County ---
for url in urls_to_process:
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
            time.sleep(10)
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
    if time.time() - start_time > 900: # 900 seconds timeout
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