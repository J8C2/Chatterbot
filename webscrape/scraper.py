import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque

# Define the base URL
base_url = 'https://www.mooreschools.com'

# Define noise phrases to filter out
NOISE_PHRASES = {
    "Your web browser does not support the <video> tag."
}

def clean_text(text):
    """Clean text by collapsing whitespace and stripping extra spaces."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def deduplicate_list(lst):
    """Return a list with duplicate items removed (preserving order)."""
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

def is_internal(link):
    """
    Determines if the provided link is internal.
    A link is internal if it is relative or its domain matches that of the base URL.
    """
    parsed_base = urlparse(base_url)
    parsed_link = urlparse(link)
    if not parsed_link.netloc:
        return True
    return parsed_link.netloc == parsed_base.netloc

def parse_html_to_json(html):
    """
    Parses HTML and returns a structured dictionary containing:
      - title: The page title.
      - meta: A dictionary with meta tags (description, keywords, and og: properties).
      - header: Cleaned text from the first <header> element (omitted if empty).
      - sections: A list of sections extracted from the <main> tag.
                  Sections with empty content are removed.
      - footer: Cleaned text from the first <footer> element (omitted if empty).
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract Title
    title = clean_text(soup.title.get_text()) if soup.title else ""
    
    # Extract Meta Information (including og: properties)
    meta = {}
    for meta_tag in soup.find_all('meta'):
        if meta_tag.get("name") in ["description", "keywords"]:
            meta[meta_tag.get("name")] = meta_tag.get("content", "")
        if meta_tag.get("property") and meta_tag.get("property").startswith("og:"):
            meta[meta_tag.get("property")] = meta_tag.get("content", "")
    
    # Extract Header Content
    header_tag = soup.find('header')
    header = clean_text(header_tag.get_text(separator="\n", strip=True)) if header_tag else ""
    if header in NOISE_PHRASES:
        header = ""
    
    # Extract Footer Content
    footer_tag = soup.find('footer')
    footer = clean_text(footer_tag.get_text(separator="\n", strip=True)) if footer_tag else ""
    if footer in NOISE_PHRASES:
        footer = ""
    
    # Extract Main Content as Sections
    main_tag = soup.find('main')
    sections = []
    if main_tag:
        # If <article> elements exist, use them for semantic segmentation.
        articles = main_tag.find_all('article')
        if articles:
            for art in articles:
                # Use the first heading found as the section header, or default to "Article"
                heading = None
                for h in art.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    heading = clean_text(h.get_text())
                    break
                if not heading:
                    heading = "Article"
                # Extract paragraphs from the article as content
                content_lines = [clean_text(p.get_text()) for p in art.find_all('p')]
                content_lines = [line for line in content_lines if line and line not in NOISE_PHRASES]
                content_lines = deduplicate_list(content_lines)
                sections.append({"header": heading, "content": content_lines})
        else:
            # Fallback: traverse descendants and segment by headings.
            current_section = {"header": None, "content": []}
            for element in main_tag.descendants:
                if element.name and element.name.lower() in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if current_section["header"] or current_section["content"]:
                        current_section["content"] = deduplicate_list(
                            [clean_text(line) for line in current_section["content"]
                             if clean_text(line) and clean_text(line) not in NOISE_PHRASES]
                        )
                        sections.append(current_section)
                    current_section = {"header": clean_text(element.get_text()), "content": []}
                elif element.name in ['p', 'div']:
                    text = clean_text(element.get_text(separator=" ", strip=True))
                    if text and text not in NOISE_PHRASES:
                        current_section["content"].append(text)
            if current_section["header"] or current_section["content"]:
                current_section["content"] = deduplicate_list(
                    [clean_text(line) for line in current_section["content"]
                     if clean_text(line) and clean_text(line) not in NOISE_PHRASES]
                )
                sections.append(current_section)
    else:
        # Fallback: use the entire body text if no <main> exists.
        body_text = clean_text(soup.body.get_text(separator="\n", strip=True)) if soup.body else ""
        sections = [{"header": None, "content": deduplicate_list(body_text.split("\n"))}]
    
    # Filter out sections with empty content
    sections = [s for s in sections if s["content"]]

    # Build final dictionary omitting empty header/footer keys.
    result = {
        "title": title,
        "meta": meta,
        "sections": sections
    }
    if header:
        result["header"] = header
    if footer:
        result["footer"] = footer
    
    return result

def scrape_page(url):
    """
    Fetches a URL, processes its HTML to return structured data (as JSON),
    and discovers internal links on the page.
    """
    print(f"Scraping: {url}")
    try:
        response = requests.get(url, timeout=10)
    except Exception as e:
        print(f"Error accessing {url}: {e}")
        return None, set()
    
    if response.status_code != 200:
        print(f"Failed to retrieve {url}: Status code {response.status_code}")
        return None, set()
    
    html = response.text
    structured_data = parse_html_to_json(html)
    
    # Remove scripts and styles for link extraction.
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    
    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag['href']
        full_link = urljoin(base_url, href)
        if is_internal(full_link):
            links.add(full_link)
    
    return structured_data, links

def crawl_site(start_url, max_pages=50):
    """
    Crawls the site starting from start_url, visiting up to max_pages,
    and returns a dictionary mapping each URL to its structured JSON data.
    """
    visited = set()
    results = {}
    queue = deque([start_url])
    
    while queue and len(visited) < max_pages:
        current_url = queue.popleft()
        if current_url in visited:
            continue
        visited.add(current_url)
        data, found_links = scrape_page(current_url)
        if data is not None:
            results[current_url] = data
        for link in found_links:
            if link not in visited:
                queue.append(link)
    return results

def remove_common_elements(results):
    """
    Checks if the header and footer content are identical across all pages.
    If so, removes them from each page's data to avoid redundant content.
    """
    if not results:
        return results
    
    headers = [data.get("header", "") for data in results.values()]
    footers = [data.get("footer", "") for data in results.values()]
    
    common_header = headers[0] if all(h == headers[0] for h in headers) else None
    common_footer = footers[0] if all(f == footers[0] for f in footers) else None
    
    new_results = {}
    for url, data in results.items():
        new_data = data.copy()
        if common_header and new_data.get("header", "") == common_header:
            new_data.pop("header", None)
        if common_footer and new_data.get("footer", "") == common_footer:
            new_data.pop("footer", None)
        new_results[url] = new_data
    return new_results

def save_to_file(filename, data):
    """
    Saves the scraped data as a JSON file.
    """
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    print(f"\nScraped data has been saved to {filename}")

if __name__ == '__main__':
    # Crawl the site (limiting to a set number of pages if desired)
    scraped_data = crawl_site(base_url, max_pages=50)
    
    # Remove common elements (e.g. identical header/footer across pages)
    processed_data = remove_common_elements(scraped_data)
    
    # Save the processed data to a text file
    save_to_file("scraped_results.txt", processed_data)
