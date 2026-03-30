import sys
from pathlib import Path

# Add scripts/ directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from rag.source_query import e2u_translate, goroh_translate, pravopys_section, r2u_translate


def run_extra():
    print("=== Extra Verification ===")

    print("\n--- Pravopys Section 1 (Vowels) ---")
    res = pravopys_section(1)
    if res:
        print(f"Text: {res['text'][:500]}...")

    print("\n--- English to Ukrainian 'letter' ---")
    res = e2u_translate("letter")
    for entry in res[:3]:
        print(f"{entry['headword']}: {entry['translation']}")

    print("\n--- English to Ukrainian 'hi' ---")
    res = e2u_translate("hi")
    for entry in res[:3]:
        print(f"{entry['headword']}: {entry['translation']}")

    print("\n--- Goroh 'літера' ---")
    res = goroh_translate("літера")
    print(f"Translations: {res}")

    print("\n--- Goroh 'привіт' ---")
    res = goroh_translate("привіт")
    print(f"Translations: {res}")

    print("\n--- R2U 'как дела' ---")
    res = r2u_translate("как дела")
    print(f"Translations: {res}")

if __name__ == "__main__":
    run_extra()
