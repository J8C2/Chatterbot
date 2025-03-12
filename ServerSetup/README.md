# ServerSetup Folder

This folder contains the necessary files for setting up and running the server side components of the AI chatbot, including database access and API integration.

## Folder Contents

- **`app.py`** – Streamlit-based chatbot application that queries the database and interacts with OpenAI. Mainly used for testing purposes.
- **`serveraccess.py`** – Handles the connection to the Azure SQL database, ensures the necessary tables exist, and inserts sample data if needed.
- **`scraper.py`** – Web scraping script, reference the webscrape folder for detailed scraper.py information

## Setup

### Dependencies

Ensure you have Python installed, then install the required packages:

pip install streamlit pyodbc openai requests beautifulsoup4

### Configure Database Connection

The following credentials need to be updated accordingly:

```python
server = 'groupd-server.database.windows.net'
database = 'group_d_ai_chatbot_server'
username = 'your_username'
password = 'your_password'
driver = '{ODBC Driver 18 for SQL Server}'
```

### Run the Database Setup

Run **`serveraccess.py`** to create and populate the database:

```sh
python serveraccess.py
```

### Run the Web Scraper (Optional)

If you want to scrape new data into the database, run:

```sh
python scraper.py
```

### Start the Chatbot

Launch the chatbot UI using Streamlit:

```sh
streamlit run app.py
```

## Expected Behavior

- If a user asks a question, `app.py` first checks the database.
- If no match is found, the question is sent to OpenAI for a response.
- The chatbot displays the answer from either the database or OpenAI.

## Notes

- Ensure **Azure SQL Database** allows public access or set firewall rules.
- Modify **`scraper.py`** to scrape additional pages if needed.

---

