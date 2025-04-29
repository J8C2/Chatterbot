import json
import re
import requests
import argparse
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque

# Define the default base URL
DEFAULT_BASE_URL = 'https://www.mooreschools.com'

def parse_arguments():
    parser = argparse.ArgumentParser(description='Web scraper for extracting structured data from websites')
    parser.add_argument('--url', type=str, default=DEFAULT_BASE_URL,
                      help=f'Base URL to scrape (default: {DEFAULT_BASE_URL})')
    return parser.parse_args()

# Get the base URL from command line arguments
args = parse_arguments()
base_url = args.url

# Define noise phrases to filter out
NOISE_PHRASES = {
    "Your web browser does not support the <video> tag."
}

REMOVE_PHRASES = {
    "Find a School Apple Creek Elementary Briarwood Elementary Brink Junior High Broadmoore Elementary Bryant Elementary Central Elementary Central Junior High Earlywine Elementary Eastlake Elementary Fairview Elementary Fisher Elementary Heritage Trails Elementary Highland East Jr. High Highland West Jr. High Houchin Elementary Kelley Elementary Kingsgate Elementary Moore High Moore West Jr. High Northmoor Elementary Oakridge Elementary Plaza Towers Elementary Red Oak Elementary Santa Fe Elementary Sky Ranch Elementary Sooner Elementary Southgate Elementary South Lake Elementary Southmoore High School Southridge Jr. High Timber Creek Elementary VISTA Academy Wayland Bonds Elementary Westmoore High School Winding Creek Elementary Open Menu Calendar Open Search Search Clear Search Close Search Find a School Apple Creek Elementary Briarwood Elementary Brink Junior High Broadmoore Elementary Bryant Elementary Central Elementary Central Junior High Earlywine Elementary Eastlake Elementary Fairview Elementary Fisher Elementary Heritage Trails Elementary Highland East Jr. High Highland West Jr. High Houchin Elementary Kelley Elementary Kingsgate Elementary Moore High Moore West Jr. High Northmoor Elementary Oakridge Elementary Plaza Towers Elementary Red Oak Elementary Santa Fe Elementary Sky Ranch Elementary Sooner Elementary Southgate Elementary South Lake Elementary Southmoore High School Southridge Jr. High Timber Creek Elementary VISTA Academy Wayland Bonds Elementary Westmoore High School Winding Creek Elementary Students Parents Staff Our Schools Moore Public Schools is the fourth-largest public school district in Oklahoma. Learn what makes us such a strong community of learners! Elementary Info & Directory Junior High Info & Directory High School Info & Directory VISTA Alternative Programs Individual School Boundary Maps About Us Each day MPS teachers and staff are fulfilling the MPS Vision of Shaping Today's Students Into Tomorrow's Leaders. Learn more about our incredible district! Administrative Team ASC Hours & Info Administrative Service Center Staff Communications Department Community Partners COVID-19 Return to Learn District Boundaries District Privacy Policies Moore Council PTA Moore Love MPS Bond 2021 MPS Logo & Brand Guidelines Project SEARCH Spring Weather Information Winter Weather Information Departments Job Opportunities Visit our Employment page for information and steps to start your career path with MPS! Administration Athletics Child Nutrition Curriculum & Instruction Educational Technology Employment Enrollment Federal Programs Finance Health Services Operations Professional Development Safety & Security Special Services Student Services Technology Enrollment Enrollment Info MPS serves more than 24,500 families at 35 school sites. We're glad you want to be a part of the MPS family! Proof of Residency Residency Affidavits Immunization Information NEW STUDENT Enrollment Pre-K Enrollment 2025-2026 Open Transfers In-District Transfers Find My School Parent Student Portal Support Enrollment Policy Acknowledgements Parent Portal Annual Review Instructions District Boundaries City of Moore - Interactive Map (opens in new window/tab) Employment Human Resources Substitute Teach at MPS Employee Identification Badge Board Policy (opens in new window/tab) TLE Resources Board of Education Board Policies Agendas & Minutes Meeting Dates How to Speak at Meetings District Map MPS Foundation"
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

def detect_repeated_content(content_list):
    """
    Detects and returns a set of content that appears in multiple sections.
    Content is considered repeated if it appears in more than one section and meets length/occurrence thresholds.
    """
    content_counts = {}
    repeated_content = set()
    
    # Count occurrences of each content line
    for content in content_list:
        for line in content:
            # Only consider lines longer than 100 characters to avoid short common phrases
            if len(line) > 100:
                content_counts[line] = content_counts.get(line, 0) + 1
    
    # Identify content that appears in multiple sections
    for line, count in content_counts.items():
        # Consider content repeated if it appears in at least 3 sections
        if count >= 3:
            repeated_content.add(line)
    
    # Also check for partial matches in long content
    long_content = [line for line in content_counts.keys() if len(line) > 500]
    for content in long_content:
        # If this content appears in at least 3 sections, consider it repeated
        if content_counts[content] >= 3:
            repeated_content.add(content)
    
    return repeated_content

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
    # Remove any content that matches REMOVE_PHRASES
    for phrase in REMOVE_PHRASES:
        header = header.replace(phrase, "")
    header = clean_text(header)  # Clean again after removal
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
                    # Remove any content that matches REMOVE_PHRASES from headers
                    for phrase in REMOVE_PHRASES:
                        heading = heading.replace(phrase, "")
                    heading = clean_text(heading)  # Clean again after removal
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
                    # Remove any content that matches REMOVE_PHRASES from headers
                    for phrase in REMOVE_PHRASES:
                        current_section["header"] = current_section["header"].replace(phrase, "")
                    current_section["header"] = clean_text(current_section["header"])  # Clean again after removal
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

    # Detect repeated content across sections
    all_content = [section["content"] for section in sections]
    repeated_content = detect_repeated_content(all_content)

    # Remove repeated content from sections while preserving unique content
    processed_sections = []
    for section in sections:
        # Filter out repeated content
        unique_content = [line for line in section["content"] if line not in repeated_content]
        
        # If the section has unique content or a meaningful header, keep it
        if unique_content or (section["header"] and len(section["header"]) > 10):
            section["content"] = unique_content
            processed_sections.append(section)

    # Build final dictionary omitting empty header/footer keys.
    result = {
        "title": title,
        "meta": meta,
        "sections": processed_sections
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

def sanitize_url_for_filename(url):
    """Convert a URL into a safe filename by removing protocol and replacing invalid characters."""
    # Remove protocol and www
    clean = re.sub(r'^https?://(?:www\.)?', '', url)
    # Replace invalid filename characters with underscores
    clean = re.sub(r'[<>:"/\\|?*]', '_', clean)
    # Remove trailing dots and spaces
    clean = clean.strip('. ')
    return clean

def save_to_file(base_url, data):
    """
    Saves the scraped data as a JSON file in the results directory.
    The filename is based on the sanitized base URL.
    """
    # Create results directory if it doesn't exist
    os.makedirs('results', exist_ok=True)
    
    # Generate filename from base URL
    filename = f"results/{sanitize_url_for_filename(base_url)}.json"
    
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    print(f"\nScraped data has been saved to {filename}")

if __name__ == '__main__':
    # Crawl the site (limiting to a set number of pages if desired)
    scraped_data = crawl_site(base_url, max_pages=50)
    
    # Remove common elements (e.g. identical header/footer across pages)
    processed_data = remove_common_elements(scraped_data)
    
    # Save the processed data to a file
    save_to_file(base_url, processed_data)
