from elasticsearch import Elasticsearch
from openai import OpenAI

# Elasticsearch setup
es = Elasticsearch("http://localhost:9200")
index_name = "school_website_data"

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
        "size": 5,
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

    response = es.search(index=index_name, body=search_payload)
    return response["hits"]["hits"]

# AI chatbot function to generate answers
def generate_answer(query):
    results = search_query(query)
    context = "\n".join([doc["_source"]["text"] for doc in results])

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Answer based on school policy data."},
            {"role": "user", "content": f"Query: {query}\nContext: {context}"}
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

# Test the search function
if __name__ == "__main__":
    query = "When are parent teacher conferences"
    answer = generate_answer(query)
    print("AI Response:", answer)
