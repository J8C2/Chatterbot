import pyodbc

# Azure SQL Server details
server = 'groupd-server.database.windows.net'  #SQL Server name
database = 'group_d_ai_chatbot_server'  #database name
username = ''  #SQL admin username
password = ''  #password
driver = '{ODBC Driver 18 for SQL Server}'  #have this driver installed

# Establish connection
try:
    #Connection to Azure SQL Database
    conn = pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    )
    cursor = conn.cursor()
    print("Connection to Database successful")

    #Create Table if one doesnt exist
    #IF NOT EXISTS uses infor..schema.tables that has metadata to see if anyhting about a faq table exists
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'FAQs')
        CREATE TABLE FAQs (
            id INT IDENTITY(1,1) PRIMARY KEY,
            question NVARCHAR(500) NOT NULL,
            answer TEXT NOT NULL,
            source_url NVARCHAR(255)
        )
    """)
    conn.commit()
    print("FAQs table created")

    #Insert Sample Data if empty
    cursor.execute("SELECT COUNT(*) FROM FAQs")
    count = cursor.fetchone()[0]

    if count == 0:  # Only insert if no records exist. Currently uses no offical records or sites
        cursor.execute("""
            INSERT INTO FAQs (question, answer, source_url)
            VALUES 
            ('What are the school hours?', 'The school operates from 8 AM to 3 PM.', 'https://school.edu/hours'),
            ('How do I apply?', 'You can apply through our website at https://school.edu/apply.', 'https://school.edu/apply')
        """)
        conn.commit()
        print("Sample FAQs inserted")

    #Query Data & Display FAQs
    cursor.execute("SELECT question, answer FROM FAQs")
    faqs = cursor.fetchall()
    # Display FAQs
    print("\n FAQs from Database:")
    for question, answer in faqs:
        print(f"Q: {question}\nA: {answer}\n")

    #Close the connection
    conn.close()

except Exception as e:
    print("Connection failed:", e)