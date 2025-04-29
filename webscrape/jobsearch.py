import requests
from bs4 import BeautifulSoup
import time
import json
import os
from urllib.parse import urljoin
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


class JobScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.categories = {}  # Dictionary to store jobs by category
        # Create results directory if it doesn't exist
        if not os.path.exists('results'):
            os.makedirs('results')

    def get_category_links(self):
        """Extract all category links from the main page"""
        response = self.session.get(self.base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all category links that match the pattern
        category_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and href.startswith('job-category-list.php?cid='):
                category_name = link.text.strip()
                category_id = href.split('cid=')[1].split('&')[0] if '&' in href else href.split('cid=')[1]
                category_links.append({
                    'url': urljoin(self.base_url, href),
                    'name': category_name,
                    'id': category_id
                })
        
        return category_links

    def get_job_links_from_category(self, category_url):
        """Extract all job links from a category page"""
        response = self.session.get(category_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        job_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and href.startswith('job-detail-view.php?jid='):
                job_links.append(urljoin(self.base_url, href))
        
        return job_links

    def get_job_details(self, job_url):
        """Extract job details from a job listing page"""
        response = self.session.get(job_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        job_data = {
            'summary': {},
            'contact': {},
            'requirements': '',
            'description': '',
            'application_procedure': '',
            'url': job_url
        }
        
        # Extract summary information
        summary_table = soup.find('td', class_='systemcolorarea1 jdvheading', string='Summary Information:')
        if summary_table:
            summary_table = summary_table.find_parent('table')
            for row in summary_table.find_all('tr')[1:]:  # Skip header row
                cells = row.find_all('td')
                if len(cells) >= 2:
                    key = cells[0].text.strip()
                    value = cells[1].text.strip()
                    job_data['summary'][key] = value
        
        # Extract contact information
        contact_table = soup.find('td', class_='systemcolorarea1 jdvheading', string='Contact Information:')
        if contact_table:
            contact_table = contact_table.find_parent('table')
            contact_info = []
            for row in contact_table.find_all('tr')[1:]:  # Skip header row
                cells = row.find_all('td')
                if cells:
                    contact_info.append(cells[0].text.strip())
            job_data['contact'] = {
                'name': contact_info[0] if len(contact_info) > 0 else '',
                'address': contact_info[1] if len(contact_info) > 1 else '',
                'city_state_zip': contact_info[2] if len(contact_info) > 2 else '',
                'phone': contact_info[3] if len(contact_info) > 3 else '',
                'fax': contact_info[4] if len(contact_info) > 4 else '',
                'email': contact_info[5] if len(contact_info) > 5 else ''
            }
        
        # Extract requirements
        requirements_heading = soup.find('td', class_='systemcolorarea1 jdvheading', string='Requirements')
        if requirements_heading:
            requirements_cell = requirements_heading.find_next('td', class_='systemlightgray editor')
            if requirements_cell:
                job_data['requirements'] = requirements_cell.text.strip()
        
        # Extract description
        description_heading = soup.find('td', class_='systemcolorarea1 jdvheading', string='Description')
        if description_heading:
            description_cell = description_heading.find_next('td', class_='systemlightgray editor')
            if description_cell:
                job_data['description'] = description_cell.text.strip()
        
        # Extract application procedure
        app_proc_heading = soup.find('td', class_='systemcolorarea1 jdvheading', string='Application Procedure')
        if app_proc_heading:
            app_proc_cell = app_proc_heading.find_next('td', class_='systemlightgray editor')
            if app_proc_cell:
                job_data['application_procedure'] = app_proc_cell.text.strip()
        
        return job_data

    def scrape_all_jobs(self):
        """Scrape all jobs from all categories"""
        category_links = self.get_category_links()
        print(f"Found {len(category_links)} categories to process")
        
        for i, category in enumerate(category_links, 1):
            print(f"\nProcessing category {i}/{len(category_links)}: {category['name']}")
            self.categories[category['id']] = {
                'name': category['name'],
                'jobs': []
            }
            
            job_links = self.get_job_links_from_category(category['url'])
            print(f"Found {len(job_links)} jobs in this category")
            
            for j, job_url in enumerate(job_links, 1):
                print(f"Processing job {j}/{len(job_links)}: {job_url}")
                job_data = self.get_job_details(job_url)
                self.categories[category['id']]['jobs'].append(job_data)
                time.sleep(1)  # Be nice to the server
            
            time.sleep(2)  # Additional delay between categories

    def save_to_file(self, filename):
        """Save scraped jobs to a JSON file organized by category"""
        filepath = os.path.join('results', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.categories, f, indent=2, ensure_ascii=False)

def scrape_jobs():
    base_url = "https://ap1.erplinq.com/moore_ap/search.php"
    scraper = JobScraper(base_url)
    scraper.scrape_all_jobs()
    
    # Format data for Elasticsearch
    formatted_data = []
    for category_id, category_data in scraper.categories.items():
        for job in category_data['jobs']:
            text = json.dumps(job)  # Convert the job data to a JSON string
            embedding = generate_embedding(text) if use_openai else []
            formatted_data.append({
                "url": job['url'],
                "text": text,
                "text_embedding": embedding,
                "timestamp": datetime.datetime.now(datetime.UTC)
            })
    return formatted_data

def main():
    base_url = "https://ap1.erplinq.com/moore_ap/search.php"
    scraper = JobScraper(base_url)
    scraper.scrape_all_jobs()
    scraper.save_to_file('job_listings.json')

if __name__ == "__main__":
    main()
