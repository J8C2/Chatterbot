"""
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
import datetime


use_openai = True
try:
    from openai import OpenAI
    # OpenAI API Key (Replace with your actual key)
    openai_client = OpenAI(api_key = "")
    if not openai_client.api_key:
        print("OpenAI API key not provided. Embeddings will not be generated.")
        use_openai = False
except ImportError:
    print("OpenAI package not installed. Embeddings will not be generated.")
    use_openai = False

def generate_embedding(text, max_length=1000):
    if not use_openai:
        return []
    
    # Truncate text if it exceeds max_length
    if len(text) > max_length:
        text = text[:max_length]
    
    response = openai_client.embeddings.create(
        input=[text], model="text-embedding-ada-002"
    )
    return response.data[0].embedding  # Corrected for OpenAI 1.0.0+


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

def scrape_boarddocs_data():
    results = []
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
        
        for link in policy_links:
            try:
                # Wait for the link to be interactable
                if not wait_for_element_interactable(driver, link):
                    continue
                
                # Use JavaScript click as a fallback
                try:
                    link.click()
                except:
                    driver.execute_script("arguments[0].click();", link)
                
                time.sleep(2)  # Wait for content to load
                
                # Get the policy title
                title = link.text.strip()
                
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
                
                text = json.dumps({"title": title, "content": content, "metadata": metadata})
                embedding = generate_embedding(text) if use_openai else []
                results.append({
                    "url": driver.current_url,
                    "text": text,
                    "text_embedding": embedding,
                    "timestamp": datetime.datetime.now(datetime.UTC)
                })
                
            except Exception as e:
                continue
        
    except Exception as e:
        pass
    finally:
        driver.quit()
    return results

if __name__ == "__main__":
    scrape_boarddocs_data()
"""
