#!/usr/bin/env python3
"""
Extract content elements for activity generation.

Usage:
    python3 scripts/extract_for_activities.py <file>
    python3 scripts/extract_for_activities.py curriculum/l2-uk-en/b1/43-*-content.md

Extracts:
- vocabulary: Ukrainian-English pairs from vocabulary table
- sentences: Example sentences from content
- dialogues: A/B dialogue pairs
- paragraphs: Content paragraphs suitable for cloze/comprehension

Outputs JSON to stdout or file.
"""

import sys
import re
import json
from pathlib import Path


def parse_frontmatter(content: str) -> dict:
    """Extract frontmatter from module content."""
    fm = {}
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def extract_body(content: str) -> str:
    """Extract body content (after frontmatter, before activities/vocab)."""
    # Remove frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2]

    # Remove activities section
    for section in ['# Activities', '# Вправи', '## Activities', '## Вправи']:
        match = re.search(rf'^{re.escape(section)}\s*$', content, re.MULTILINE)
        if match:
            content = content[:match.start()]
            break

    # Remove vocabulary section
    for section in ['# Vocabulary', '# Словник', '## Vocabulary', '## Словник']:
        match = re.search(rf'^{re.escape(section)}\s*$', content, re.MULTILINE)
        if match:
            content = content[:match.start()]
            break

    return content.strip()


def extract_vocabulary(content: str) -> list[dict]:
    """Extract vocabulary items from table."""
    vocabulary = []

    # Find vocabulary section
    vocab_match = None
    for header in ['# Vocabulary', '# Словник', '## Vocabulary', '## Словник']:
        match = re.search(rf'^{re.escape(header)}\s*$', content, re.MULTILINE)
        if match:
            vocab_match = match
            break

    if not vocab_match:
        return vocabulary

    vocab_section = content[vocab_match.end():]

    # Find next section to limit scope
    next_section = re.search(r'^#', vocab_section, re.MULTILINE)
    if next_section:
        vocab_section = vocab_section[:next_section.start()]

    # Parse table rows
    # A1/A2 format: | Word | IPA | English | POS | Gender | Note |
    # B1+ format: | Слово | Переклад | Примітки |

    rows = re.findall(r'^\|([^|]+)\|([^|]+)\|([^|]+)', vocab_section, re.MULTILINE)

    for row in rows:
        word = row[0].strip()
        col2 = row[1].strip()
        col3 = row[2].strip()

        # Skip header/separator rows
        if word.startswith('-') or word.lower() in ('word', 'слово', 'ipa', 'вимова'):
            continue

        # Clean markdown formatting
        word = re.sub(r'\*\*([^*]+)\*\*', r'\1', word)
        word = re.sub(r'\*([^*]+)\*', r'\1', word)

        # Determine format
        if re.match(r'^/.*/$', col2):
            # A1/A2 format: col2 is IPA, col3 is English
            vocabulary.append({
                'uk': word,
                'ipa': col2,
                'en': col3,
            })
        else:
            # B1+ format: col2 is translation
            vocabulary.append({
                'uk': word,
                'en': col2,
            })

    return vocabulary


def extract_sentences(content: str) -> list[str]:
    """Extract Ukrainian example sentences."""
    body = extract_body(content)
    sentences = []

    # Bold Ukrainian sentences
    bold_matches = re.findall(r'\*\*([А-ЯІЇЄҐа-яіїєґ][^*]+[.!?])\*\*', body)
    sentences.extend(bold_matches)

    # Italic Ukrainian sentences (sometimes used for examples)
    italic_matches = re.findall(r'\*([А-ЯІЇЄҐа-яіїєґ][^*]+[.!?])\*', body)
    sentences.extend(italic_matches)

    # Bulleted Ukrainian sentences
    bullet_matches = re.findall(r'^[-–—]\s+([А-ЯІЇЄҐа-яіїєґ][^–—\n]+[.!?])', body, re.MULTILINE)
    sentences.extend(bullet_matches)

    # Table cell sentences (from example tables)
    table_matches = re.findall(r'\|\s*([А-ЯІЇЄҐа-яіїєґ][^|]+[.!?])\s*\|', body)
    sentences.extend(table_matches)

    # Deduplicate and filter
    seen = set()
    unique = []
    for s in sentences:
        s = s.strip()
        # Skip short fragments and duplicates
        if len(s) > 10 and s not in seen:
            seen.add(s)
            unique.append(s)

    return unique


def extract_dialogues(content: str) -> list[dict]:
    """Extract dialogue pairs."""
    body = extract_body(content)
    dialogues = []

    # Pattern 1: **А:** ... **Б:** ...
    ab_pattern = r'\*\*([АБВ]):\*\*\s*([^\n*]+)'
    ab_matches = re.findall(ab_pattern, body)

    # Group into pairs
    current_pair = {}
    for speaker, text in ab_matches:
        if speaker == 'А':
            if current_pair.get('a'):
                dialogues.append(current_pair)
            current_pair = {'a': text.strip()}
        elif speaker == 'Б':
            current_pair['b'] = text.strip()
            dialogues.append(current_pair)
            current_pair = {}

    # Pattern 2: **Speaker:** format (e.g., **Пасажир:**)
    speaker_pattern = r'\*\*([А-ЯІЇЄҐа-яіїєґ]+):\*\*\s*([^\n*]+)'
    speaker_matches = re.findall(speaker_pattern, body)

    # Group into pairs (every 2 consecutive speakers form a pair)
    for i in range(0, len(speaker_matches) - 1, 2):
        dialogues.append({
            'a': speaker_matches[i][1].strip(),
            'b': speaker_matches[i + 1][1].strip(),
            'speakers': [speaker_matches[i][0], speaker_matches[i + 1][0]]
        })

    # Pattern 3: А: ... / Б: ... (plain text)
    plain_pattern = r'^([АБВ]):\s*([^\n]+)'
    plain_matches = re.findall(plain_pattern, body, re.MULTILINE)

    current_pair = {}
    for speaker, text in plain_matches:
        if speaker == 'А':
            if current_pair.get('a'):
                dialogues.append(current_pair)
            current_pair = {'a': text.strip()}
        elif speaker == 'Б':
            current_pair['b'] = text.strip()
            dialogues.append(current_pair)
            current_pair = {}

    # Pattern 4: Speaker: text (e.g., Марія: Привіт!)
    name_pattern = r'^([А-ЯІЇЄҐа-яіїєґ]{2,20}):\s+([А-ЯІЇЄҐа-яіїєґ][^\n]+)'
    name_matches = re.findall(name_pattern, body, re.MULTILINE)

    for i in range(0, len(name_matches) - 1, 2):
        dialogues.append({
            'a': name_matches[i][1].strip(),
            'b': name_matches[i + 1][1].strip(),
            'speakers': [name_matches[i][0], name_matches[i + 1][0]]
        })

    # Pattern 5: Em-dash dialogue (— text)
    dash_matches = re.findall(r'^—\s+([^\n]+)', body, re.MULTILINE)
    for i in range(0, len(dash_matches) - 1, 2):
        dialogues.append({
            'a': dash_matches[i].strip(),
            'b': dash_matches[i + 1].strip(),
        })

    # Deduplicate
    seen = set()
    unique = []
    for d in dialogues:
        key = (d.get('a', ''), d.get('b', ''))
        if key not in seen and d.get('a') and d.get('b'):
            seen.add(key)
            unique.append(d)

    return unique


def extract_paragraphs(content: str) -> list[str]:
    """Extract paragraphs suitable for cloze/comprehension activities."""
    body = extract_body(content)
    paragraphs = []

    # Split by double newlines
    blocks = re.split(r'\n\s*\n', body)

    for block in blocks:
        block = block.strip()

        # Skip headers, tables, lists, short content
        if not block:
            continue
        if block.startswith('#'):
            continue
        if block.startswith('|'):
            continue
        if block.startswith('-') or block.startswith('*'):
            continue
        if block.startswith('>'):
            continue
        if len(block) < 100:
            continue

        # Check it's mostly Ukrainian
        ukr_words = len(re.findall(r'[а-яіїєґА-ЯІЇЄҐ]+', block))
        eng_words = len(re.findall(r'[a-zA-Z]+', block))

        if ukr_words > eng_words:
            paragraphs.append(block)

    return paragraphs


def extract_proverbs(content: str) -> list[str]:
    """Extract proverbs and sayings."""
    body = extract_body(content)
    proverbs = []

    # Look for proverb indicators
    patterns = [
        r'«([^»]+)»',  # Quoted
        r'"([А-ЯІЇЄҐа-яіїєґ][^"]+[.!])"',  # Double quoted Ukrainian
        r'\*\*Приказка:\*\*\s*([^\n]+)',  # Labeled proverbs
        r'\*\*Прислів\'я:\*\*\s*([^\n]+)',  # Labeled sayings
    ]

    for pattern in patterns:
        matches = re.findall(pattern, body)
        proverbs.extend(matches)

    # Deduplicate
    return list(set(p.strip() for p in proverbs if len(p) > 10))


def extract_tables(content: str) -> list[dict]:
    """Extract grammar tables for reference."""
    body = extract_body(content)
    tables = []

    # Find table blocks
    table_pattern = r'(\|[^\n]+\|(?:\n\|[^\n]+\|)+)'
    matches = re.findall(table_pattern, body)

    for table_text in matches:
        rows = table_text.strip().split('\n')
        if len(rows) < 2:
            continue

        # Parse header
        header = [c.strip() for c in rows[0].split('|')[1:-1]]

        # Skip separator row
        data_rows = []
        for row in rows[1:]:
            if re.match(r'^[\|\s\-:]+$', row):
                continue
            cells = [c.strip() for c in row.split('|')[1:-1]]
            if cells:
                data_rows.append(cells)

        if header and data_rows:
            tables.append({
                'header': header,
                'rows': data_rows
            })

    return tables


def extract_all(file_path: Path) -> dict:
    """Extract all content elements from a module file."""
    content = file_path.read_text(encoding='utf-8')
    fm = parse_frontmatter(content)

    return {
        'module': fm.get('module', ''),
        'title': fm.get('title', ''),
        'focus': fm.get('focus', ''),
        'vocabulary': extract_vocabulary(content),
        'sentences': extract_sentences(content),
        'dialogues': extract_dialogues(content),
        'paragraphs': extract_paragraphs(content),
        'proverbs': extract_proverbs(content),
        'tables': extract_tables(content),
        'stats': {
            'vocabulary_count': len(extract_vocabulary(content)),
            'sentence_count': len(extract_sentences(content)),
            'dialogue_count': len(extract_dialogues(content)),
            'paragraph_count': len(extract_paragraphs(content)),
            'proverb_count': len(extract_proverbs(content)),
            'table_count': len(extract_tables(content)),
        }
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/extract_for_activities.py <file>")
        print("Example: python3 scripts/extract_for_activities.py curriculum/l2-uk-en/b1/43-content.md")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    # Extract content
    data = extract_all(file_path)

    # Output JSON
    output = sys.argv[2] if len(sys.argv) > 2 else None

    if output:
        Path(output).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"Extracted to: {output}")
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
