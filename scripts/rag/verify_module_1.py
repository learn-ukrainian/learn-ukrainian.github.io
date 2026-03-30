import sys
from pathlib import Path

# Add scripts/ directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from rag.query import search_dictionary
from rag.source_query import pravopys_lookup, r2u_translate


def check_pravopys(topic):
    res = pravopys_lookup(topic)
    if res:
        print(f"--- Pravopys: {topic} ---")
        print(res.get('text', 'No text found')[:1000])
        print(f"URL: {res.get('url')}")
    else:
        print(f"--- Pravopys: {topic} NOT FOUND ---")

def check_calque(phrase):
    print(f"--- Calque check: {phrase} ---")
    # Check style guide (Antonenko-Davydovych)
    res = search_dictionary(phrase, "style_guide", limit=2)
    for i, hit in enumerate(res, 1):
        print(f"  [Style Guide {i}] {hit['text'][:500]}...")

    # Check r2u if it's a short phrase
    if len(phrase.split()) <= 3:
        res_r2u = r2u_translate(phrase)
        if res_r2u:
            print(f"  [r2u] {res_r2u}")

def check_cefr(word):
    print(f"--- CEFR check: {word} ---")
    res = search_dictionary(word, "puls_cefr", limit=1)
    if res:
        print(f"  [PULS] {res[0]['text']}")
    else:
        print("  [PULS] Not found")

if __name__ == "__main__":
    print("Verifying Module 1...")

    # Task 3: Grammar rules
    check_pravopys("алфавіт")
    check_pravopys("голосні")
    check_pravopys("приголосні")

    # Task 4: Calques
    check_calque("як справи")
    check_calque("рада тебе бачити")
    check_calque("а у тебе")

    # Task 5: CEFR
    words_to_check = ["мама", "тато", "привіт", "банк", "аптека"]
    for w in words_to_check:
        check_cefr(w)
