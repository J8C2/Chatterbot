from fastapi import FastAPI, HTTPException, UploadFile, File
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
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],
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
#openai_client = OpenAI(api_key = "")

# Function to generate OpenAI embeddings
def generate_embedding(text):
    # Return a fixed dummy vector instead of making an OpenAI API call
    return [0.01] * 1536  # 1536 is the embedding size for "text-embedding-ada-002"


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
def generate_answer(query):
    return f"### Response Preview\nYou asked: **{query}**\n\nThis is a _dummy_ response using Markdown.\n\n- List item\n- [Link to calendar](https://www.mooreschools.com/Page/2)"


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
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
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
            return {"message": f"File '{file.filename}' uploaded, but unsupported type."}

        # Handeling for readable text content
        if text_content.strip():
            embedding = generate_embedding(text_content)
            doc = {
                "text": text_content,
                "text_embedding": embedding,
                "url": f"uploaded://{file.filename}",  # Upload check for URL to be included at the end
                "source_type": "upload",               # Checking for source type
                "timestamp": datetime.utcnow()
            }
            es.index(index=INDEX_NAME, body=doc)
            return {
                "message": f"File '{file.filename}' uploaded and processed successfully.",
                "filename": file.filename
            }
        else:
            return {"message": f"File '{file.filename}' uploaded but contained no readable text."}

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