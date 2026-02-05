import json
import os

slugs = [
    "ivan-vyhovskyi", "bohdan-khmelnytskyy", "petro-mohyla", "sylvestr-kosiv",
    "volodymyr-monomakh", "danylo-apostol", "knyazhna-anna-yaroslavna",
    "pavlo-polubotok", "danylo-halytskyi", "knyahynia-olha", "ivan-puliui",
    "meletii-smotrytskyi", "yuriy-kondratiuk", "yuriy-nemyrych",
    "mykhailo-chernihivskyi", "kost-hordiyenko", "ivan-sirko",
    "hryhoriy-skovoroda", "volodymyr-vernadskyi"
]

results = {}
for slug in slugs:
    path = f"curriculum/l2-uk-en/c1-bio/status/{slug}.json"
    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
            status = data.get("overall", {}).get("status", "unknown")
            results[slug] = status
    else:
        results[slug] = "MISSING"

for slug, status in results.items():
    print(f"{slug}: {status}")