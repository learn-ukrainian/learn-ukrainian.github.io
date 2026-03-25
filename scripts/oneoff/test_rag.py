import requests
import json

def search(query):
    url = "http://127.0.0.1:8766/sse"
    payload = {
        "tool": "search_text",
        "query": query
    }
    try:
        response = requests.post(url, json=payload)
        return response.text
    except Exception as e:
        return str(e)

print(search("вимова шся ться"))
