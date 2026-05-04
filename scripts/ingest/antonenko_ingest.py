import argparse
import json
import re
import sqlite3


def load_existing_headwords():
    conn = sqlite3.connect("data/sources.db")
    rows = conn.execute("SELECT word FROM style_guide").fetchall()
    conn.close()
    return {row[0].strip() for row in rows}

def clean_and_track_pages(lines):
    cleaned = []
    current_page = 0
    for line in lines:
        line = line.rstrip()

        if line == '\x0c':
            continue

        m = re.match(r'^\s*(\d+)\s*$', line)
        if m:
            current_page = int(m.group(1))
            continue

        if not line:
            continue

        cleaned.append((line, current_page))
    return cleaned

def segment_text(lines_with_pages):
    existing = load_existing_headwords()

    items = []
    current_headword = None
    current_text = []
    current_page = 0

    normalized_existing = {re.sub(r'[?!.]$', '', h).lower() for h in existing}

    i = 0
    while i < len(lines_with_pages):
        line, page = lines_with_pages[i]
        indent = len(line) - len(line.lstrip())

        is_headword = False
        text_strip = line.strip()

        norm_text = re.sub(r'[?!.]$', '', text_strip).lower()
        if norm_text in normalized_existing:
            is_headword = True
        elif indent == 4 and i + 1 < len(lines_with_pages):
            next_line, _ = lines_with_pages[i+1]
            next_indent = len(next_line) - len(next_line.lstrip())

            if next_indent >= 4 and not text_strip.endswith('.') and len(text_strip) < 150:
                is_headword = True

        if is_headword:
            if current_headword is not None:
                items.append({
                    "headword": current_headword,
                    "text": current_text,
                    "page": current_page
                })
            current_headword = text_strip
            current_text = []
            current_page = page
        else:
            if current_headword is not None:
                current_text.append(line)
        i += 1

    if current_headword is not None:
        items.append({
            "headword": current_headword,
            "text": current_text,
            "page": current_page
        })

    return items

def join_paragraphs(lines):
    paragraphs = []
    current_para = ""
    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        if indent >= 4:
            if current_para:
                paragraphs.append(current_para)
            current_para = stripped
        else:
            if current_para.endswith('-'):
                current_para = current_para[:-1] + stripped
            else:
                current_para += " " + stripped if current_para else stripped

    if current_para:
        paragraphs.append(current_para)

    return "\n\n".join(paragraphs)

def main():
    parser = argparse.ArgumentParser(description="Ingest Antonenko-Davydovych PDF text")
    parser.add_argument("--input", required=True, help="Input txt file")
    parser.add_argument("--output", required=True, help="Output jsonl file")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        lines = f.readlines()

    cleaned = clean_and_track_pages(lines)
    items = segment_text(cleaned)

    processed_items = []
    for item in items:
        text = join_paragraphs(item["text"])
        processed_items.append({
            "headword": item["headword"],
            "russianism_pattern": item["headword"],
            "commentary": text,
            "page": item["page"],
            "source_excerpt": text[:100] + "..." if text else ""
        })

    existing = load_existing_headwords()
    found = set()
    for item in processed_items:
        hw_norm = re.sub(r'[?!.]$', '', item['headword']).lower()
        for ex in existing:
            if re.sub(r'[?!.]$', '', ex).lower() == hw_norm:
                found.add(ex)

    print(f"Total items extracted: {len(processed_items)}")
    print(f"Recall against existing subset: {len(found)} / {len(existing)} ({len(found)/len(existing)*100:.1f}%)")

    with open(args.output, "w", encoding="utf-8") as f:
        for item in processed_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
