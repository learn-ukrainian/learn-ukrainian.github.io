import sys
from pathlib import Path

# Add scripts/ directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from rag.source_query import goroh_translate, r2u_translate


def check_calques():
    phrases = [
        "принимать участие", # Russian
        "иметь место", # Russian
        "поделить на слоги" # Russian
    ]

    for p in phrases:
        print(f"\n--- Checking Russian phrase: {p} ---")
        res = r2u_translate(p)
        if res:
            for entry in res[:5]:
                print(f"Translation: {entry['translation']}")

if __name__ == "__main__":
    check_calques()
