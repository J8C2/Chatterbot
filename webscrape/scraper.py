import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
from elasticsearch import Elasticsearch

# Connect to Elasticsearch
es = Elasticsearch(["http://localhost:9200"])

# Base URL of the site to scrape
BASE_URL = 'https://www.mooreschools.com'

# Common noise phrases to filter out
NOISE_PHRASES = {
    "Your web browser does not support the <video> tag."
}

# Elasticsearch index name
INDEX_NAME = "school_website_data"


def clean_text(text):
    """Cleans text by removing extra whitespace and filtering out noise phrases."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text if text not in NOISE_PHRASES else ""


def is_internal_link(link):
    """Checks if a link is internal by comparing its domain with the base URL."""
    parsed_base = urlparse(BASE_URL)
    parsed_link = urlparse(link)
    return not parsed_link.netloc or parsed_link.netloc == parsed_base.netloc


def extract_text_content(soup):
    """Extracts all visible text content from the webpage."""
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()  # Remove scripts, styles, and hidden elements
    
    text_lines = [clean_text(text) for text in soup.stripped_strings]
    return list(filter(None, text_lines))  # Remove empty lines


def scrape_page(url):
    """Fetches a webpage, extracts text, and finds internal links."""
    print(f"Scraping: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error accessing {url}: {e}")
        return None, set()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract structured content
    title = clean_text(soup.title.get_text()) if soup.title else ""
    content = extract_text_content(soup)

    # Extract metadata (description, keywords, Open Graph tags)
    meta = {tag.get("name", tag.get("property")): tag.get("content", "")
            for tag in soup.find_all('meta') if tag.get("content")}

    # Extract all internal links
    internal_links = {
        urljoin(BASE_URL, a['href']) for a in soup.find_all("a", href=True)
        if is_internal_link(a['href'])
    }

    return {"url": url, "title": title, "meta": meta, "content": content}, internal_links


def crawl_site(start_url, max_pages=100):
    """Crawls the website and scrapes up to `max_pages` unique pages."""
    visited = set()
    results = {}
    queue = deque([start_url])

    while queue and len(visited) < max_pages:
        current_url = queue.popleft()
        if current_url in visited:
            continue

        visited.add(current_url)
        scraped_data, found_links = scrape_page(current_url)

        if scraped_data:
            results[current_url] = scraped_data
            save_to_elasticsearch(scraped_data)  # Store data in Elasticsearch

        queue.extend(link for link in found_links if link not in visited)

    return results


def save_to_elasticsearch(data):
    """Stores the scraped data in Elasticsearch."""
    es.index(index=INDEX_NAME, document=data)


if __name__ == '__main__':
    # Crawl and scrape the website
    scraped_data = crawl_site(BASE_URL, max_pages=100)

    # Save final JSON output (optional)
    with open("scraped_results.json", "w", encoding="utf-8") as file:
        json.dump(scraped_data, file, indent=4, ensure_ascii=False)

    print("\nWeb scraping completed and data stored in Elasticsearch!")
