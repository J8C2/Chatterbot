from elasticsearch import Elasticsearch

es = Elasticsearch(["http://localhost:9200"])
response = es.search(index="school_website_data")
print(response["hits"]["hits"])
