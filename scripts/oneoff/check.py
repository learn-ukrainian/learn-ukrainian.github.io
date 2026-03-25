import urllib.request
import json

def verify(words):
    req = urllib.request.Request(
        "http://127.0.0.1:8766/sse", 
        data=json.dumps({"method": "verify_words", "params": {"words": words}}).encode("utf-8"), 
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            print(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Error: {e}")

verify(["студент", "Олег", "Олегу", "Ганна", "Петро", "Іван", "Марія", "мамо", "тату"])
