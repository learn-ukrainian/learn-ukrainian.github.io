"""Convert Антоненко-Давидович "Як ми говоримо" HTML to chunked JSONL for RAG.

Input: data/antonenko-davydovych/yak-my-hovorymo.html
Output: data/antonenko-davydovych/yak-my-hovorymo.txt (plain text)
        data/antonenko-davydovych/chunks.jsonl (RAG-ready chunks)

The book is structured as:
- Foreword (ПЕРЕДНЄ СЛОВО)
- Part-of-speech sections (ІМЕННИКИ, ПРИКМЕТНИКИ, ДІЄСЛОВА, etc.)
  - Grammar discussion paragraphs
  - ЗАУВАЖЕННЯ ДО НИЗКИ ... (remarks on specific words)
    - Individual word/phrase entries (short title + discussion paragraphs)
- Thematic sections (БАЖАННЯ ЛІТЕРАТОРА, СПОСТЕРЕЖЕННЯ МИТЦЯ, etc.)
- Afterword (ПІСЛЯСЛОВО)

Each entry discusses how a Ukrainian word/phrase should be used correctly.
"""

import json
from pathlib import Path

from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "antonenko-davydovych"
INPUT_HTML = DATA_DIR / "yak-my-hovorymo.html"
OUTPUT_TXT = DATA_DIR / "yak-my-hovorymo.txt"
OUTPUT_JSONL = DATA_DIR / "chunks.jsonl"

# ALL-CAPS headers that mark major sections
SECTION_HEADERS = {
    "ПЕРЕДНЄ СЛОВО",
    "ІМЕННИКИ",
    "ЗАУВАЖЕННЯ ДО НИЗКИ ІМЕННИКІВ",
    "ПРИКМЕТНИКИ",
    "ЗАУВАЖЕННЯ ДО НИЗКИ ПРИКМЕТНИКІВ",
    "ДІЄСЛОВА",
    "ЗАУВАЖЕННЯ ДО НИЗКИ ДІЄСЛІВ",
    "ДІЄПРИКМЕТНИКИ",
    "ЗАУВАЖЕННЯ ДО НИЗКИ ДІЄПРИКМЕТНИКІВ",
    "ДІЄПРИСЛІВНИКИ",
    "ЗАУВАЖЕННЯ ДО ДЕЯКИХ ДІЄПРИСЛІВНИКІВ",
    "ЧИСЛІВНИКИ",
    "ЗАУВАЖЕННЯ ДО ДЕЯКИХ ЧИСЛІВНИКІВ",
    "ЗАЙМЕННИКИ",
    "ЗАУВАЖЕННЯ ДО ДЕЯКИХ ЗАЙМЕННИКІВ",
    "ПРИСЛІВНИКИ",
    "ЗАУВАЖЕННЯ ДО НИЗКИ ПРИСЛІВНИКІВ",
    "ПРИЙМЕННИКИ",
    "СПОЛУЧНИКИ",
    "ЧАСТКИ",
    "ВИГУКИ",
    "БАЖАННЯ ЛІТЕРАТОРА",
    "СПОСТЕРЕЖЕННЯ МИТЦЯ",
    "ЩОБ ЯСКРАВО Й ТОЧНО",
    "ВАГОВИТІ ДРІБНИЦІ",
    "ПІСЛЯСЛОВО",
}


def is_section_header(text: str) -> bool:
    """Check if a paragraph is a major section header (ALL-CAPS)."""
    return text == text.upper() and text in SECTION_HEADERS


def is_entry_title(text: str, next_text: str | None) -> bool:
    """Heuristic: short paragraph followed by longer content = entry title."""
    if len(text) > 80:
        return False
    if text[0].islower():
        return False
    if text == text.upper():
        return False  # section header, not entry title
    # Must be followed by substantive content
    return bool(next_text and len(next_text) > 80)


def extract_paragraphs(html_path: Path) -> list[str]:
    """Extract all paragraph texts from the content div."""
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    content = soup.find("div", id="content")
    return [p.get_text().strip() for p in content.find_all("p")]


def save_plain_text(paragraphs: list[str], output_path: Path):
    """Save full plain text version."""
    with open(output_path, "w", encoding="utf-8") as f:
        for text in paragraphs:
            if text:
                f.write(text + "\n\n")
    print(f"Saved plain text: {output_path} ({output_path.stat().st_size:,} bytes)")


def chunk_entries(paragraphs: list[str]) -> list[dict]:
    """Split into RAG chunks: one per entry/topic."""
    chunks = []
    current_section = ""
    current_title = ""
    current_text_parts = []

    def flush():
        nonlocal current_title, current_text_parts
        if current_title and current_text_parts:
            full_text = "\n\n".join(current_text_parts)
            # Extract the key word(s) from the title
            word = current_title.rstrip("?").strip()
            chunks.append(
                {
                    "section": current_section,
                    "word": word,
                    "text": full_text,
                }
            )
        current_title = ""
        current_text_parts = []

    # Skip foreword (paragraphs before ІМЕННИКИ)
    start_idx = 0
    for i, text in enumerate(paragraphs):
        if text == "ІМЕННИКИ":
            start_idx = i
            break

    i = start_idx
    while i < len(paragraphs):
        text = paragraphs[i]

        if not text:
            i += 1
            continue

        # Section header
        if is_section_header(text):
            flush()
            current_section = text

            # For sections without sub-entries (grammar discussion),
            # collect all paragraphs until next header or entry title
            if "ЗАУВАЖЕННЯ" not in text and text not in {
                "БАЖАННЯ ЛІТЕРАТОРА",
                "СПОСТЕРЕЖЕННЯ МИТЦЯ",
                "ЩОБ ЯСКРАВО Й ТОЧНО",
                "ВАГОВИТІ ДРІБНИЦІ",
                "ПІСЛЯСЛОВО",
            }:
                # Grammar intro section — collect paragraphs as one chunk
                current_title = text
                i += 1
                while i < len(paragraphs):
                    next_text = paragraphs[i]
                    if not next_text:
                        i += 1
                        continue
                    if is_section_header(next_text):
                        break
                    # Check if this is an entry title (in ЗАУВАЖЕННЯ sections)
                    peek = paragraphs[i + 1] if i + 1 < len(paragraphs) else None
                    if is_entry_title(next_text, peek):
                        break
                    current_text_parts.append(next_text)
                    i += 1
                flush()
                continue
            else:
                i += 1
                continue

        # Entry title detection
        next_text = paragraphs[i + 1] if i + 1 < len(paragraphs) else None
        if is_entry_title(text, next_text):
            flush()
            current_title = text
            i += 1
            continue

        # Content paragraph
        if current_title:
            current_text_parts.append(text)
        else:
            # Orphan paragraph in a thematic section — start a new chunk
            # For sections like ЩОБ ЯСКРАВО Й ТОЧНО, group consecutive paragraphs
            current_title = current_section or text[:60]
            current_text_parts.append(text)

        i += 1

    flush()
    return chunks


def main():
    print(f"Reading {INPUT_HTML}...")
    paragraphs = extract_paragraphs(INPUT_HTML)
    print(f"Found {len(paragraphs)} paragraphs")

    # Save plain text
    save_plain_text(paragraphs, OUTPUT_TXT)

    # Chunk into entries
    chunks = chunk_entries(paragraphs)
    print(f"Created {len(chunks)} chunks")

    # Write JSONL
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks, 1):
            entry = {
                "id": f"ad-{i:03d}",
                "word": chunk["word"],
                "section": chunk["section"],
                "text": chunk["text"],
                "source": "Антоненко-Давидович",
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Written {len(chunks)} entries to {OUTPUT_JSONL}")

    # Stats
    sections = {}
    for c in chunks:
        s = c["section"]
        sections[s] = sections.get(s, 0) + 1

    print("\nChunks per section:")
    for section, count in sections.items():
        print(f"  {section}: {count}")

    # Show samples
    print("\nSample entries:")
    for chunk in chunks[:5]:
        print(f"\n--- {chunk['word']} ({chunk['section']}) ---")
        print(chunk["text"][:200] + "...")


if __name__ == "__main__":
    main()
