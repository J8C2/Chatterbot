from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from openai import OpenAI
import os
import shutil
import logging
import fitz
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from openai import OpenAI
import os
import logging
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from docx import Document
from io import BytesIO

# Load OpenAI API key from environment variable (or replace with your key)
#openai_client = OpenAI(api_key = "")

# Initialize FastAPI app
app = FastAPI(debug=True)
logging.basicConfig(level=logging.DEBUG)
# Initialize FastAPI app
app = FastAPI(debug=True)
logging.basicConfig(level=logging.DEBUG)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Use ["http://localhost:3000"] in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
)

# Connect to Elasticsearch
es = Elasticsearch(["http://localhost:9200"])
INDEX_NAME = "school_website_data"

# Define request models
class QueryRequest(BaseModel):
    query: str

class FeedbackRequest(BaseModel):
    query: str
    feedback: str 
    response_text: str 


# OpenAI API Key (Replace with your actual key)
openai_client = OpenAI(api_key = "")

# Function to generate OpenAI embeddings
def generate_embedding(text):
    response = openai_client.embeddings.create(
        input=[text], model="text-embedding-ada-002"
    )
    return response.data[0].embedding


# Function to perform hybrid search (keyword + vector)
def search_query(query):
    query_embedding = generate_embedding(query)

    search_payload = {
        "size": 10,
        "query": {
            "bool": {
                "should": [
                    {"match": {"text": query}},  # Keyword search
                    {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'text_embedding') + 1.0",
                                "params": {"query_vector": query_embedding}
                            }
                        }
                    }
                ]
            }
        }
    }

    response = es.search(index=INDEX_NAME, body=search_payload)
    results = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        results.append({
            "text": source.get("text", ""),
            "url": source.get("url", ""),
            "score": hit["_score"]
        })
    
    return results

# AI chatbot function to generate answers
# AI chatbot function to generate answers
def generate_answer(query, file_content=None):
    # Search Elasticsearch for relevant documents
    es_results = search_query(query)
    context_list = []

    # Add Elasticsearch results to context
    for doc in es_results:
        text = doc.get("text", "")
        url = doc.get("url", "")
        context_list.append(f"Source: {url}\nContent: {text}\n\n")

    # Add file content to context if provided
    if file_content:
        context_list.append(f"File Content:\n{file_content}\n\n")

    context = "".join(context_list)

    # Call OpenAI with the combined context
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an assistant answering questions based on the information you can find on any Moore Public school website for Moore public schools in Oklahoma. The context for this information is provided to you in the context, you should use this and apply more weight to the content of the file content if a user uploaded one (found in file_content at end). Please return your response in clear, well structured and styled markdown, including specific links and references to where you got the information. Do not include a link if it isn't specifically mentioned in the context. For any job-related questions, look for information from links starting with 'https://ap1.erplinq.com/moore_ap/search.php' and try your best to list out specific jobs found in the context."},
            {"role": "user", "content": f"Query: {query}\n\nContext: \n{context}"}
        ]
    )

    return response.choices[0].message.content

# Endpoint to handle queries
@app.post("/ask")
async def ask_question(request: QueryRequest):
    """Handles query requests from the frontend."""
    try:
        ai_response = generate_answer(request.query)
        print("Successful AI")
        
        return {"query": request.query, "response": ai_response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    #appp.post for uploading files and handling them

@app.post("/upload_and_query")
async def upload_and_query(file: UploadFile = File(...), query: str = Form(...)):
    try:
        logging.info(query)
        # Read file into memory
        file_content = await file.read()
        file_stream = BytesIO(file_content)
        # Extract text based on file type
        text_content = ""
        if file.filename.endswith(".txt"):
            text_content = file_content.decode("utf-8")

        elif file.filename.endswith(".pdf"):
            with fitz.open(stream=file_content, filetype="pdf") as doc:
                text_content = "\n".join(page.get_text() for page in doc)

        elif file.filename.endswith(".docx"):
            doc = Document(file_stream)
            text_content = "\n".join(para.text for para in doc.paragraphs)

        else:
            return {"response": f"File '{file.filename}' uploaded, but unsupported type."}

        # Use the modified generate_answer function
        ai_response = generate_answer(query, file_content=text_content)

        return {"query": query, "response": ai_response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to handle feedback
@app.post("/feedback")
async def send_feedback(request: FeedbackRequest):
    """Logs user feedback to separate good/bad files."""
    try:
        # Select log file based on feedback type
        log_file = "./good_feedback.txt" if request.feedback == "good" else "./bad_feedback.txt"
        log_entry = f"Query: {request.query}\nResponse: {request.response_text}\n\n"
        
        # Write to the appropriate log file
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        
        logging.info(f"Feedback logged to {log_file}: {log_entry.strip()}")
        return {"status": "feedback logged"}
        
    except Exception as e:
        logging.error(f"Error logging feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    # try:
    #     # Send feedback to OpenAI as a system message
    #     response = openai_client.chat.completions.create(
    #         model="gpt-4o",
    #         messages=[
    #             {
    #                 "role": "system",
    #                 "content": f"User provided feedback: {request.feedback} on response: {request.response_text}"
    #             }
    #         ]
    #     )
    #     # Log the OpenAI response
    #     response_text = response.choices[0].message.content
    #     logging.info(f"OpenAI feedback response: {response_text}")
    #     return {"status": "feedback received"}
    
    # except Exception as e:
    #     logging.error(f"Error sending feedback to OpenAI: {str(e)}")
    #     raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)