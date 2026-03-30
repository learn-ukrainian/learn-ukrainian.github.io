import sys
from pathlib import Path

# Add scripts/ directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from rag.source_query import pravopys_section


def verify():
    sections = {
        "Я-Ю-Є": 4,
        "Апостроф": 7,
        "М'який знак": 26,
        "Голосні": 1
    }

    for topic, num in sections.items():
        print(f"\n--- {topic} (Section {num}) ---")
        res = pravopys_section(num)
        if res:
            # Print first 300 chars
            text = res['text']
            # Clean HTML if any
            import re
            text = re.sub(r'<[^>]+>', ' ', text)
            print(text[:400].strip() + "...")

if __name__ == "__main__":
    verify()
