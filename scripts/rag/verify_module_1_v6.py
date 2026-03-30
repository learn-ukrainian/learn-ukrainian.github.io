import sys
from pathlib import Path

# Add scripts/ directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from rag.query import search_dictionary, search_text, verify_words
from rag.source_query import pravopys_lookup, r2u_translate


def run_verification():
    print("=== TASK 1: VESUM Verification ===")
    vocab = ["звук", "літера", "голосний", "приголосний", "привіт", "як справи", "добре", "чудово", "мама", "молоко", "нормально", "тато", "око", "дім", "ніс", "сон"]
    # "як справи" is a phrase, VESUM won't find it directly. Split it.
    single_words = []
    for item in vocab:
        single_words.extend(item.split())

    vesum_results = verify_words(list(set(single_words)))
    confirmed = [w for w, matches in vesum_results.items() if matches]
    not_found = [w for w, matches in vesum_results.items() if not matches]
    print(f"Confirmed: {confirmed}")
    print(f"Not found: {not_found}")

    print("\n=== TASK 2: Textbook Excerpts ===")
    sections = ["Звуки і літери", "Голосні звуки", "Приголосні звуки", "Привіт!"]
    for section in sections:
        print(f"\n--- Section: {section} ---")
        hits = search_text(section, limit=2)
        for hit in hits:
            print(f"[{hit['author']}, Grade {hit['grade']}] {hit['text']}...")

    print("\n=== TASK 3: Grammar Rules ===")
    topics = ["алфавіт", "голосні", "приголосні"]
    for topic in topics:
        res = pravopys_lookup(topic)
        if res:
            print(f"Rule for '{topic}': Правопис §{res['section']} - {res['text'][:300]}...")
        else:
            print(f"Rule for '{topic}': NOT FOUND")

    print("\n=== TASK 4: Calque Warnings ===")
    phrases = ["як справи", "привіт", "добре", "чудово", "нормально"]
    for phrase in phrases:
        # Check r2u for Russian equivalents to see if they are the same
        # Actually r2u_translate takes Russian word.
        # Let's check common Russianisms: "як діла" (calque of "как дела")
        if phrase == "як справи":
            res = r2u_translate("как дела")
            print(f"'{phrase}' vs Russian 'как дела': {res}")

    print("\n=== TASK 5: CEFR Check ===")
    # Check if words are A1
    for word in ["звук", "літера", "голосний", "приголосний", "привіт", "мама"]:
        res = search_dictionary(word, "puls_cefr", limit=1)
        if res:
            print(f"'{word}': {res[0]['text'][:200]}...")
        else:
            print(f"'{word}': NOT FOUND in CEFR")

if __name__ == "__main__":
    run_verification()
