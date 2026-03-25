import urllib.request
import json
import sys

def check_dict(word):
    req = urllib.request.Request(
        'http://127.0.0.1:8766/search_text',
        data=json.dumps({"query": word}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        response = urllib.request.urlopen(req)
        print(response.read().decode())
    except Exception as e:
        print(f"Error: {e}")

check_dict("гадати")
