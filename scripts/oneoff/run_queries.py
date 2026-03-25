import sys
import json
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path("./scripts").resolve()))

async def main():
    try:
        from rag.source_query import wikipedia_extract
        print("=== WIKIPEDIA EXTRACT ===")
        res_wiki = wikipedia_extract("Василь Стус")
        if res_wiki:
            print(f"# {res_wiki['title']}")
            print(f"URL: {res_wiki['url']}")
            print(res_wiki['extract'])
        else:
            print("Not found.")
    except Exception as e:
        print(f"Error wikipedia: {e}")

    try:
        from rag.query import search_literary
        print("\n=== SEARCH LITERARY: моральний імператив ===")
        res_lit1 = search_literary("Василь Стус моральний імператив", limit=5)
        for i, hit in enumerate(res_lit1, 1):
            print(f"--- Result {i} ---")
            print(f"Work: {hit.get('work')}, Author: {hit.get('author')}")
            print(hit.get('text', ''))

        print("\n=== SEARCH LITERARY: Стус Палімпсести ===")
        res_lit2 = search_literary("Стус Палімпсести", limit=5)
        for i, hit in enumerate(res_lit2, 1):
            print(f"--- Result {i} ---")
            print(f"Work: {hit.get('work')}, Author: {hit.get('author')}")
            print(hit.get('text', ''))
    except Exception as e:
        print(f"Error literary: {e}")

asyncio.run(main())
