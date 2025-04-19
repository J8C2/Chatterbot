from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from openai import OpenAI
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from openai import OpenAI
import os
import logging
from fastapi.middleware.cors import CORSMiddleware

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

# Define request model
class QueryRequest(BaseModel):
    query: str

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


@app.post("/ask")
async def ask_question(request: QueryRequest):
    """Handles query requests from the frontend."""
    try:
        ai_response = generate_answer(request.query)
        print("Successful AI")
        
        return {"query": request.query, "response": ai_response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
