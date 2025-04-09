import requests
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from openai import OpenAI
import datetime
import re
from collections import deque
from urllib.parse import urljoin, urlparse


# Elasticsearch setup
es = Elasticsearch("http://localhost:9200")
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
# OpenAI API Key (Replace with your actual key)
openai_client = OpenAI(api_key = "")

# Function to generate embeddings using OpenAI
def generate_embedding(text):
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

    for data in data_list:
        print(data["url"])
        try:
            if isinstance(data, dict) and "text" in data:
                embedding = generate_embedding(data["text"])
                document = {
                    "text": data["text"],
                    "text_embedding": embedding,
                    "url": data["url"],
                    "timestamp": datetime.datetime.now(datetime.UTC)
                }
                es.index(index=index_name, body=document)
                print("Stored:", data["url"])
            else:
                print("Skipping invalid data:", data)
        except Exception as e:
            print(f"Error storing data: {data}\nException: {e}")

# Delete existing index and recreate it
def reset_elasticsearch():
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        print(f"Deleted index: {index_name}")

    mapping = {
        "mappings": {
            "properties": {
                "text": {"type": "text"},
                "text_embedding": {"type": "dense_vector", "dims": 1536},
                "url": {"type": "keyword"},
                "timestamp": {"type": "date"}
            }
        }
    }
    es.indices.create(index=index_name, body=mapping)
    print(f"Recreated index: {index_name}")

# Main execution
if __name__ == "__main__":
    reset_elasticsearch()

    scraped_data = scrape_school_website()

    if scraped_data:
        store_data_in_elasticsearch(scraped_data)
