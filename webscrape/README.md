# Web Scraper and Content Parser

This project is a Python-based web scraper and content parser designed to crawl a website (in this example, [Moore Public Schools](https://www.mooreschools.com)) and extract structured content. The code retrieves key metadata, headers, footers, and main content segments while filtering out repeated or non-informative elements (such as duplicate navigation links or empty sections).

## Table of Contents

- [Overview](#overview)
- [Dependencies and Setup](#dependencies-and-setup)
- [Code Structure and Workflow](#code-structure-and-workflow)
  - [Helper Functions](#helper-functions)
  - [Content Parsing](#content-parsing)
  - [Page Scraping and Link Discovery](#page-scraping-and-link-discovery)
  - [Site Crawling](#site-crawling)
  - [Post-Processing](#post-processing)
  - [Saving Results](#saving-results)
- [Example Output](#example-output)
- [Conclusion](#conclusion)

## Overview

The code performs the following tasks:
1. **Crawls a website**: Starting at the base URL, it uses a breadth-first search (BFS) approach to visit internal pages.
2. **Extracts content**: For each page, it retrieves the HTML, parses the content to obtain the title, metadata, header, main sections, and footer.
3. **Cleans and structures the data**: The code removes noisy or duplicate text (e.g., "Your web browser does not support the \<video\> tag.") and discards sections with empty content.
4. **Removes common elements**: If all pages share identical headers or footers, these are removed from individual outputs.
5. **Saves the results**: Finally, the structured data is written to a JSON file.

## Dependencies and Setup

To run the code, ensure you have Python installed along with the following packages:

- `requests`
- `beautifulsoup4`

You can install these dependencies using:

```bash
pip install requests beautifulsoup4
```

## Code Structure and Workflow

The project is organized into several functions that work together to produce the final JSON output.

### Helper Functions

- **`clean_text(text)`**  
  Cleans input text by collapsing extra whitespace and stripping leading/trailing spaces.

- **`deduplicate_list(lst)`**  
  Removes duplicate entries from a list while preserving the order.

- **`is_internal(link)`**  
  Checks if a given URL is internal relative to the base URL (i.e., belongs to the same domain).

### Content Parsing

- **`parse_html_to_json(html)`**  
  Uses BeautifulSoup to parse the HTML of a page and extracts:
  - **Title**: Retrieved from the `<title>` tag.
  - **Meta Information**: Captures meta tags such as `description`, `keywords`, and any Open Graph properties (e.g., `og:title`, `og:image`).
  - **Header and Footer**: Extracts and cleans text from the first `<header>` and `<footer>` elements. If the cleaned header or footer matches defined noise phrases, they are set to an empty string.
  - **Sections**:  
    - If `<article>` elements exist within the `<main>` tag, each article is processed as a section using its first heading as the section title and paragraphs (`<p>`) as content.
    - Otherwise, the code traverses the `<main>` tag and segments content based on heading tags (`h1`–`h6`).
    - Sections with empty content are filtered out so that only meaningful text is kept.

### Page Scraping and Link Discovery

- **`scrape_page(url)`**  
  Downloads the HTML of the given URL, calls `parse_html_to_json` to structure its content, and then finds all internal links by removing script, style, and noscript tags.

### Site Crawling

- **`crawl_site(start_url, max_pages=50)`**  
  Implements a BFS crawl starting from the base URL. It maintains a queue of URLs to visit and a set of already visited URLs, ensuring that up to a specified maximum number of pages are processed.

### Post-Processing

- **`remove_common_elements(results)`**  
  Compares header and footer content across all pages. If the header (or footer) is identical across every page, that key is removed from each page’s output. This helps reduce redundancy.

### Saving Results

- **`save_to_file(filename, data)`**  
  Writes the final structured JSON data to a file (e.g., `scraped_results.txt`).

## Example Output

An example of the JSON output is stored in the `scraped_results.txt` file. For instance, one entry from the output looks like:

```json
{
    "https://www.mooreschools.com": {
        "title": "Home - Moore Public Schools",
        "meta": {
            "description": "MPS is one of the highest paying districts in the state, always topping Oklahoma's average teacher salary (according to ZipRecruiter 2025).",
            "keywords": "Home, Moore Schools, Moore Public Schools, Highest paying district, Teacher salary, highest, oklahoma",
            "og:url": "https://www.mooreschools.com/",
            "og:description": "MPS is one of the highest paying districts in the state, always topping Oklahoma's average teacher salary (according to ZipRecruiter 2025).",
            "og:image": "https://resources.finalsite.net/images/t_image_size_4/v1694095874/mooreschoolscom/h3kluqmgaqiagqymwjbj/MPSlogo-socialmedia_SEO-graph.png",
            "og:image:width": "1200",
            "og:image:height": "1200",
            "og:title": "Home - Moore Public Schools",
            "og:type": "website"
        },
        "sections": [],
        "header": "Find a School Apple Creek Elementary ...",
        "footer": "Close Search"
    }
}
```

In this example, you can see that:
- The **meta** field includes additional Open Graph tags.
- The **header** and **footer** are non-empty since they differ from common noise.
- The **sections** array is empty if no meaningful article or content sections were extracted, thanks to our filtering logic.

Additional entries in the file follow similar patterns, ensuring that empty sections and duplicate noise are removed.

## Conclusion

This code is designed to generate a clean, structured JSON representation of a website's content that is suitable for further analysis or feeding into an LLM chatbot. The process involves:
- Crawling a site via BFS,
- Parsing and cleaning HTML content,
- Structuring text into logical sections,
- Removing duplicate and empty entries,
- And finally, saving the results to a file for later use.

The included example output in the `scraped_results.txt` file citeturn1file0 illustrates how the data is organized. This approach allows downstream applications to easily parse and utilize the scraped information with minimal noise and maximum clarity.