import urllib.request
import urllib.parse
url = f"https://goroh.pp.ua/%D0%A2%D1%80%D0%B0%D0%BD%D1%81%D0%BA%D1%80%D0%B8%D0%BF%D1%86%D1%96%D1%8F/{urllib.parse.quote('восени')}"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')
if "во́сени" in html:
    print("во́сени is True")
if "восени́" in html:
    print("восени́ is True")
