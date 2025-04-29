from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import json
import time
import os

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")  # Set a larger window size
    
    # Initialize the Chrome driver
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def wait_for_element_interactable(driver, element, timeout=10):
    try:
        # Wait for element to be visible
        WebDriverWait(driver, timeout).until(
            EC.visibility_of(element)
        )
        
        # Wait for element to be clickable
        WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.ID, element.get_attribute('id')))
        )
        
        # Scroll element into view
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)  # Small pause after scrolling
        
        return True
    except:
        return False

def scrape_boarddocs():
    # Create results directory if it doesn't exist
    if not os.path.exists('results'):
        os.makedirs('results')
    
    driver = setup_driver()
    try:
        # Navigate to the BoardDocs page
        driver.get("https://go.boarddocs.com/ok/moore/Board.nsf/Public")
        
        # Wait for the page to load
        time.sleep(5)  # Give time for initial page load
        
        # Click on the Policies tab using the href attribute
        policies_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#tab-policies"]'))
        )
        policies_tab.click()
        
        # Wait for policies content to load
        time.sleep(5)  # Increased wait time
        
        # Find all policy links
        policy_links = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[id^="policy-"]'))
        )
        
        print(f"Found {len(policy_links)} policy links")
        
        results = []
        
        for link in policy_links:
            try:
                # Wait for the link to be interactable
                if not wait_for_element_interactable(driver, link):
                    print(f"Skipping unclickable link: {link.text.strip()}")
                    continue
                
                # Use JavaScript click as a fallback
                try:
                    link.click()
                except:
                    driver.execute_script("arguments[0].click();", link)
                
                time.sleep(2)  # Wait for content to load
                
                # Get the policy title
                title = link.text.strip()
                print(f"Processing policy: {title}")
                
                # Wait for and get the policy content
                policy_content = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "wrap-policy-item"))
                )
                
                # Get all text content from the policy item
                content = policy_content.text.strip()
                
                # Get any additional metadata if available
                metadata = {}
                try:
                    # Look for common metadata elements
                    metadata_elements = policy_content.find_elements(By.CSS_SELECTOR, '.policy-meta, .policy-date, .policy-status')
                    for meta in metadata_elements:
                        key = meta.get_attribute('class').replace('policy-', '')
                        metadata[key] = meta.text.strip()
                except:
                    pass
                
                results.append({
                    "title": title,
                    "content": content,
                    "metadata": metadata
                })
                
                print(f"Successfully processed policy: {title}")
                
            except Exception as e:
                print(f"Error processing policy link: {str(e)}")
                continue
        
        # Save results to JSON file
        with open('results/policies.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
            
        print("Scraping completed successfully!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_boarddocs()
