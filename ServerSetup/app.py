# Code uses streamlit for a quick UI setup to test chatbot functionality
from flask import Flask, request, jsonify, app  # Add jsonify here
import pyodbc
import openai
import streamlit as st
import os
from flask_cors import CORS  # This is for enabling CORS if needed

# Azure SQL Connection details
server = 'groupd-server.database.windows.net'  
database = 'group_d_ai_chatbot_server'  
username = ''  
password = ''  # Need to remove this for security
driver = '{ODBC Driver 18 for SQL Server}'
# Need to remove api key for security as well
openai.api_key = ""

app = Flask(__name__)

# Enable CORS if frontend and backend are on different ports
CORS(app)

# Function to get answer from Azure SQL Database
def get_answer_from_db(question):
    try:
        # This connects to the Azure SQL Database based on inputs above
        conn = pyodbc.connect(
            f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        )
        # Creating a cursor to execute SQL queries, helps to fetch data
        cursor = conn.cursor()
        cursor.execute("SELECT answer FROM FAQs WHERE question LIKE ?", ('%' + question + '%',))
        result = cursor.fetchone()
        conn.close()
        # Return the answer if found, else None
        return result[0] if result else None
    except Exception as e:
        return f"Database error: {e}"

# Function to generate AI response using OpenAI
def get_ai_answer(question):
    try:
        # Setting up OpenAI client and generating a response
        client = openai.OpenAI()
        response = client.chat.completions.create(  
            model="gpt-3.5-turbo",
            messages=[ # Messages to send to the model
                {"role": "system", "content": "You are a helpful school assistant."},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content  # Extracting the AI response
    # Error handling for OpenAI specific errors
    except openai.OpenAIError as e: 
        return f"OpenAI API Error: {e}"

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # Get the message from the frontend (React)
        data = request.get_json()
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({"response": "Please enter a question."})

        # First, check the database for an answer
        db_answer = get_answer_from_db(user_message)

        if db_answer:
            # Return answer from the database
            return jsonify({"response": db_answer})
        else:
            # If no answer in the database, use OpenAI
            ai_answer = get_ai_answer(user_message)
            return jsonify({"response": ai_answer})

    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)

# Streamlit UI
""""
st.title("School Chatbot")
st.write("Ask a question for the school chatbot to answer")

user_input = st.text_input("Enter your question:")

if st.button("Get Answer"):
    if user_input:
        # First, check the database for an answer
        db_answer = get_answer_from_db(user_input)
        # Currently database direct answers are split up from AI generated answers
        if db_answer:
            st.success(f"Answer from Database:\n{db_answer}")
        else:
            st.warning("No exact match found in the database. Using AI instead...")

            # Send question to OpenAI when no match in DB
            ai_answer = get_ai_answer(user_input)
            # Display AI-generated answer or error message if no answer is found
            if ai_answer:
                st.info(f"AI-generated Answer:\n{ai_answer}")
            else:
                st.error("I couldn't find an answer. Please try rewording your question.")
    else: # Extra check for empty input
        st.warning("Please enter a question.")
"""
