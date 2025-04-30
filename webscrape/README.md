# Web Scraper and Content Parser

This project contains two Python-based web scrapers designed to extract structured content from websites. The scripts are specifically tailored for scraping Moore Public Schools' website and job listings.

## Table of Contents

- [Overview](#overview)
- [Dependencies and Setup](#dependencies-and-setup)
- [Scripts](#scripts)
  - [mooreschool.py](#mooreschoolpy)
  - [jobsearch.py](#jobsearchpy)
- [Example Output](#example-output)

## Overview

The project contains two main scripts:

1. **mooreschool.py**: A general website scraper that crawls the Moore Public Schools website, extracting structured content from various pages.
2. **jobsearch.py**: A specialized scraper for extracting job listings from the Moore Public Schools employment portal.

Both scripts support OpenAI embeddings generation for enhanced text analysis capabilities.

## Dependencies and Setup

To run the scripts, ensure you have Python installed along with the following packages:

```bash
pip install requests beautifulsoup4 openai
```

Optional: For OpenAI embeddings generation, you'll need to set up your OpenAI API key in the scripts.

## Scripts

### mooreschool.py

This script crawls the Moore Public Schools website and extracts structured content. Key features:

- Crawls the site using breadth-first search (BFS)
- Extracts and structures content including:
  - Page titles
  - Meta information
  - Headers and footers
  - Main content sections
- Removes duplicate and non-informative content
- Supports OpenAI embeddings generation
- Saves results in JSON format

Usage:

```bash
python mooreschool.py [--url BASE_URL]
```

### jobsearch.py

This script specifically targets the Moore Public Schools job listings portal. Key features:

- Extracts job listings by category
- For each job, captures:
  - Summary information
  - Contact details
  - Requirements
  - Description
  - Application procedures
- Supports OpenAI embeddings generation
- Saves results in JSON format

Usage:

```bash
python jobsearch.py
```

## Example Output

Both scripts generate structured JSON output. For example, a job listing might look like:

```json
{
  "summary": {
    "Position": "Teacher",
    "Location": "Elementary School",
    "Status": "Full-time"
  },
  "contact": {
    "name": "John Doe",
    "email": "john.doe@mooreschools.com",
    "phone": "123-456-7890"
  },
  "requirements": "Bachelor's degree in Education...",
  "description": "Job description details...",
  "application_procedure": "Application instructions..."
}
```

The website scraper output includes similar structured data for each page crawled, with additional metadata and content sections.
