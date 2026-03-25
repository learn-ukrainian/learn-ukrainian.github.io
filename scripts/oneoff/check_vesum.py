import json
import urllib.request
import urllib.error

data = json.dumps({
    "jsonrpc": "2.0",
    "method": "verify_words",
    "params": {"words": ["кит", "кіт", "сир", "сір", "лис", "ліс", "бити", "біти", "мило", "міло", "дим", "дім", "син", "сін", "пити", "піти", "риба", "ріба"]},
    "id": 1
}).encode('utf-8')

req = urllib.request.Request("http://127.0.0.1:8766/mcp", data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode())
except urllib.error.URLError as e:
    print(f"Error: {e}")
