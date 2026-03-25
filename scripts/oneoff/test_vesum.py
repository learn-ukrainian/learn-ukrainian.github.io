import urllib.request
import json

def check(words):
    req = urllib.request.Request(
        "http://127.0.0.1:8766/sse",
        data=json.dumps({"command": "verify_words", "args": {"words": words}}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as r:
            print(f"{words}: {r.read().decode('utf-8')}")
    except Exception as e:
        print(f"Error for {words}: {e}")

check(["ма", "а", "д", "м", "бан", "пинка", "ода"])
