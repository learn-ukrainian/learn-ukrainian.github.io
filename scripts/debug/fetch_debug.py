import requests
headers = {'User-Agent': 'Mozilla/5.0'}
resp = requests.get('https://www.ukrainianlessons.com/season1/', headers=headers)
print(resp.text[:3000])
