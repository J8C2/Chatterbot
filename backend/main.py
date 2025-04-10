from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from openai import OpenAI
import os
import shutil
import logging
from fastapi.middleware.cors import CORSMiddleware

# Load OpenAI API key from environment variable (or replace with your key)
openai_client = OpenAI(api_key = "")

# Initialize FastAPI app
app = FastAPI(debug=True)
logging.basicConfig(level=logging.DEBUG)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use ["http://localhost:3000"] in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],
)

# Connect to Elasticsearch
es = Elasticsearch(["http://localhost:9200"])
INDEX_NAME = "school_website_data"

# Define request model
class QueryRequest(BaseModel):
    query: str

# OpenAI API Key (Replace with your actual key)
#openai_client = OpenAI(api_key = "")

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
def generate_answer(query):
    results = search_query(query)
    contextList = []
    for doc in results:
        text = doc.get("text", "")
        url = doc.get("url", "")
        contextList.append(f"Source: {url}\nContent: {text}\n\n")
    
    context = "".join(contextList)

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an assistant answering questions based on Moore Public Schools policy and information. Use only the provided context. If you cite anything, include the specific link it came from. Please use clear markdown formatting to make your answers as simple and readable as possible, and put all references at the bottom of the response"},
            {"role": "user", "content": f"Query: {query}\n\nContext: \n{context}"}
        ]
    )
    """
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Answer based on the information you can find on any Moore Public school website for Moore public schools in Oklahoma. Include the calendar page"},
            {"role": "user", "content": f"Query: {query}"}
        ]
    )
    """

    return response.choices[0].message.content

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
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {"message": f"File '{file.filename}' uploaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
