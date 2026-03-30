import sys
from pathlib import Path

# Add scripts/ directory to sys.path
PROJECT_ROOT = Path("/Users/krisztiankoos/projects/learn-ukrainian")
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

try:
    from rag.query import search_dictionary
    from rag.source_query import pravopys_lookup
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

print("--- Alphabet ---")
for kw in ["алфавіт", "абетка", "букви", "звуки"]:
    res = pravopys_lookup(kw)
    if res:
        print(f"Keyword '{kw}' -> Section {res.get('section', 'N/A')}")
        print(f"Content: {res['text'][:200]}...")

print("\n--- CEFR ---")
words = ["літера", "привіт", "голосний", "приголосний", "звук", "мама", "тато", "дім", "сон", "ніс", "око", "добре", "чудово", "нормально"]
for w in words:
    res = search_dictionary(w, "puls_cefr", limit=1)
    if res:
        # Assuming the search_dictionary returns list of matches, each with 'text'
        # Which usually contains word(LEVEL, POS)
        print(f"{w}: {res[0]['text'][:100]}...")
    else:
        print(f"{w}: NOT FOUND")
