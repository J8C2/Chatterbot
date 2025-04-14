import requests
from bs4 import BeautifulSoup
import datetime
import re
from collections import deque
from urllib.parse import urljoin, urlparse
import os
import json

# Attempt to import Elasticsearch
use_elasticsearch = True
try:
    from elasticsearch import Elasticsearch
    # Elasticsearch setup - only create connection if available
    es = Elasticsearch("http://localhost:9200", request_timeout=30)
    # Test connection
    try:
        es.info()
        print("Successfully connected to Elasticsearch")
    except Exception as e:
        print(f"Elasticsearch is not available: {e}")
        use_elasticsearch = False
except ImportError:
    print("Elasticsearch package not installed. Will save data to JSON instead.")
    use_elasticsearch = False

# Attempt to import OpenAI
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

index_name = "school_website_data"
BASE_URL = 'https://www.mooreschools.com'
#
# Add logic for Employment, BoardDocs
#
MAIN_SECTIONS = {
    "About Us": f"{BASE_URL}/about-us",
    "Departments": f"{BASE_URL}/departments",
    "Enrollment": f"{BASE_URL}/enrollment",
    "Employment": f"{BASE_URL}/employment",
    "Board of Education": f"{BASE_URL}/school-board",
    "MPS Foundation": f"{BASE_URL}/buildingbridges"
}
NOISE_PHRASES = {
    "Your web browser does not support the <video> tag."
}

# Function to generate embeddings using OpenAI
def generate_embedding(text):
    if not use_openai:
        return []
    
    response = openai_client.embeddings.create(
        input=[text], model="text-embedding-ada-002"
    )
    return response.data[0].embedding  # Corrected for OpenAI 1.0.0+

# Scrape a single page
def scrape_page(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {url}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract content (headings + paragraphs)
    text_data = []
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    for section in soup.find_all(['h1', 'h2', 'h3', 'p']):
        text_data.append(section.get_text(strip=True))

    return {
        "url": url,
        "text": " ".join(text_data)
    }

# Scrape the main sections and one level deep links
def scrape_school_website():
    visited_urls = set()
    all_data = []

    for section, url in MAIN_SECTIONS.items():
        print(f"Scraping section: {section} -> {url}")
        main_page_data = scrape_page(url)
        if main_page_data:
            all_data.append(main_page_data)
            visited_urls.add(url)

        # Find internal links (one level deep)
        response = requests.get(url)
        if response.status_code != 200:
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            full_url = requests.compat.urljoin(BASE_URL, link['href'])  # Convert to absolute URL
            
            if full_url.startswith(BASE_URL) and full_url not in visited_urls:
                print(f"Scraping subpage: {full_url}")
                subpage_data = scrape_page(full_url)
                if subpage_data:
                    all_data.append(subpage_data)
                visited_urls.add(full_url)
    
    return all_data

# Function to store data in Elasticsearch
def store_data_in_elasticsearch(data_list):
    if not data_list:
        return None
    
    if not use_elasticsearch:
        # Save to JSON file instead
        save_to_json(data_list)
        return

    for data in data_list:
        print(data["url"])
        try:
            if isinstance(data, dict) and "text" in data:
                if use_openai:
                    embedding = generate_embedding(data["text"])
                    document = {
                        "text": data["text"],
                        "text_embedding": embedding,
                        "url": data["url"],
                        "timestamp": datetime.datetime.now(datetime.UTC)
                    }
                else:
                    document = {
                        "text": data["text"],
                        "url": data["url"],
                        "timestamp": datetime.datetime.now(datetime.UTC)
                    }
                es.index(index=index_name, body=document)
                print("Stored:", data["url"])
            else:
                print("Skipping invalid data:", data)
        except Exception as e:
            print(f"Error storing data: {data}\nException: {e}")

# Save data to a JSON file
def save_to_json(data_list):
    output_dir = "scraped_data"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/scraped_data_{timestamp}.json"
    
    # Convert datetime objects to strings
    serializable_data = []
    for item in data_list:
        if "timestamp" in item and isinstance(item["timestamp"], datetime.datetime):
            item["timestamp"] = item["timestamp"].isoformat()
        serializable_data.append(item)
    
    with open(filename, 'w') as f:
        json.dump(serializable_data, f, indent=2)
    
    print(f"Data saved to {filename}")
    return filename

# Delete existing index and recreate it
def reset_elasticsearch():
    global use_elasticsearch
    
    if not use_elasticsearch:
        print("Elasticsearch not available. Skipping index reset.")
        return
    
    try:
        if es.indices.exists(index=index_name):
            es.indices.delete(index=index_name)
            print(f"Deleted index: {index_name}")

        mapping = {
            "mappings": {
                "properties": {
                    "text": {"type": "text"},
                    "url": {"type": "keyword"},
                    "timestamp": {"type": "date"}
                }
            }
        }
        
        # Add embedding field only if OpenAI is available
        if use_openai:
            mapping["mappings"]["properties"]["text_embedding"] = {"type": "dense_vector", "dims": 1536}
            
        es.indices.create(index=index_name, body=mapping)
        print(f"Recreated index: {index_name}")
    except Exception as e:
        print(f"Error resetting Elasticsearch: {e}")
        print("Will continue and save data to JSON instead")
        use_elasticsearch = False

# Main execution
if __name__ == "__main__":
    reset_elasticsearch()

    scraped_data = scrape_school_website()

    if scraped_data:
        store_data_in_elasticsearch(scraped_data)
