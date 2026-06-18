import json
import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DATASET_ROOT = PROJECT_ROOT / "data" / "lexicon-dataset"
DATASET_DIR = DATASET_ROOT / "dataset"

ATTRIBUTION_MD = """# Word Atlas Open Dataset Attribution

This dataset aggregates data from the following sources. The provenance of each field in the dataset is tracked per-entry in the data itself.

- **СУМ-11** (Словник української мови в 11 томах)
- **СУМ-20** (Словник української мови у 20 томах)
- **ЕСУМ** (Етимологічний словник української мови)
- **Горох** (Goroh.pp.ua)
- **kaikki** / **Wiktionary** (English Wiktionary machine-readable extracts) — CC BY-SA 3.0
- **Вікісловник** (Ukrainian Wiktionary) — CC BY-SA
- **Вікіпедія** (Ukrainian Wikipedia) — CC BY-SA
- **Грінченко** (Словарь української мови, 1907-1909) — Public Domain
- **dmklinger** (Dictionary mappings / datasets)
- **ukrainian-word-stress** (Stress marks data)
- **VESUM** (Великий електронний словник української мови)
- **UA-GEC** (Ukrainian Grammatical Error Correction dataset)
- **Learn Ukrainian Project** (Our own derived data, classifications, and course usage)
"""

NOTICE_MD = """# Word Atlas Dataset Notice

All rights to the original definitions, etymologies, and extracted text belong to their respective source creators (e.g., the National Academy of Sciences of Ukraine for СУМ/ЕСУМ, the respective communities for Wikipedia/Wiktionary, etc.).

We claim ownership only over our derived structure, custom classifications, English pedagogical translations, and the specific syllabus-mapping used in the Learn Ukrainian curriculum.

**Takedown Requests:**
If you are the rightsholder of any source material included in this dataset and object to its open publication in this format, please open an issue on our GitHub repository, and we will remove your data upon request.
"""

README_MD = """# Word Atlas Lexicon Dataset

This directory contains the open, sharded dataset of the Word Atlas lexicon.

## Structure

The data is provided in JSONL (JSON Lines) format, sharded by the first letter of the Ukrainian headword (`lemma`), located in the `dataset/` directory.

- `dataset/А.jsonl`, `dataset/Б.jsonl`, etc.
- Each line in the `.jsonl` files is a standalone JSON object representing a single lemma.

## Schema

Each entry represents a single word (lemma) and contains:
- `lemma` (string): The Ukrainian headword.
- `url_slug` (string): Slug used for routing.
- `gloss` (string): English translation/gloss.
- `pos` (string): Part of speech.
- `ipa` (string): International Phonetic Alphabet representation.
- `course_usage` (array): List of course modules where this word is taught.
- Plus any available enriched fields (`etymology`, `definitions`, `paradigm`, `heritage_status`, etc.).

Provenance is tracked per-field where applicable. For full attribution details, see [ATTRIBUTION.md](./ATTRIBUTION.md) and [NOTICE.md](./NOTICE.md).
"""


def main() -> None:
    DATASET_ROOT.mkdir(parents=True, exist_ok=True)
    if DATASET_DIR.exists():
        shutil.rmtree(DATASET_DIR)
    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    (DATASET_ROOT / "ATTRIBUTION.md").write_text(ATTRIBUTION_MD, encoding="utf-8")
    (DATASET_ROOT / "NOTICE.md").write_text(NOTICE_MD, encoding="utf-8")
    (DATASET_ROOT / "README.md").write_text(README_MD, encoding="utf-8")

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    entries = manifest.get("entries", [])

    metadata = {k: v for k, v in manifest.items() if k != "entries"}
    (DATASET_DIR / "_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    # Group entries by first character
    shards: dict[str, list[dict]] = {}
    for entry in entries:
        lemma = entry.get("lemma", "")
        if not lemma:
            continue

        first_char = lemma[0].upper()
        if not first_char.isalpha():
            first_char = "symbol"

        if first_char not in shards:
            shards[first_char] = []
        shards[first_char].append(entry)

    for char, char_entries in shards.items():
        file_path = DATASET_DIR / f"{char}.jsonl"
        with open(file_path, "w", encoding="utf-8") as out_f:
            for entry in char_entries:
                out_f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Exported {len(entries)} entries to {DATASET_DIR.relative_to(PROJECT_ROOT)} across {len(shards)} shards.")


if __name__ == "__main__":
    main()
