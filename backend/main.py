from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os
import logging
from fastapi.middleware.cors import CORSMiddleware

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

# Define request models
class QueryRequest(BaseModel):
    query: str

class FeedbackRequest(BaseModel):
    message_id: int
    feedback: str
    response_text: str 

# OpenAI API Key
openai_client = OpenAI(api_key="")

# Function to generate OpenAI embeddings
def generate_embedding(text):
    response = openai_client.embeddings.create(
        input=[text], model="text-embedding-ada-002"
    )
    return response.data[0].embedding

# Function to perform hybrid search (keyword + vector)
def search_query(query):
    query_embedding = generate_embedding(query)

    # Mock results (unchanged)
    results = [
        {
            "text": "Sample result 1",
            "url": "http://example.com/1",
            "score": 0.95
        },
        {
            "text": "Sample result 2",
            "url": "http://example.com/2",
            "score": 0.90
        }
    ]
    
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
            {"role": "system", "content": "Your job is to respond with the last feedback that you received that has the form of User provided feedback: {request.feedback} on response: {request.response_text}."},
            {"role": "user", "content": f"Query: {query}\n"}
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

# Endpoint to handle feedback
@app.post("/feedback")
async def send_feedback(request: FeedbackRequest):
    """Handles feedback from the frontend and notifies OpenAI."""
    try:
        # Send feedback to OpenAI as a system message
        openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"User provided feedback: {request.feedback} on response: {request.response_text}"
                }
            ]
        )
        return {"status": "feedback received"}
    
    except Exception as e:
        logging.error(f"Error sending feedback to OpenAI: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
