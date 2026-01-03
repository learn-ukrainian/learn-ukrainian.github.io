#!/usr/bin/env python3
"""
Extract metadata from curriculum modules for resource mapping.

This script:
1. Reads all markdown files from curriculum/l2-uk-en/{level}/ folders
2. Extracts metadata: title, level, topics, vocabulary
3. Creates module_metadata.json for automated resource scoring

Usage:
    .venv/bin/python scripts/extract_module_metadata.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List


def extract_frontmatter(content: str) -> Dict[str, str]:
    """Extract YAML frontmatter from markdown."""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}

    frontmatter = {}
    for line in match.group(1).split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            frontmatter[key.strip()] = value.strip().strip('"\'')

    return frontmatter


def extract_h2_topics(content: str) -> List[str]:
    """Extract H2 section headers as topic keywords."""
    # Remove frontmatter
    content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

    # Find all H2 headers (## Title)
    h2_pattern = r'^## (.+)$'
    topics = re.findall(h2_pattern, content, re.MULTILINE)

    # Clean up topics (remove emoji, special chars)
    cleaned = []
    for topic in topics:
        # Remove callout markers like [!observe], [!resources]
        topic = re.sub(r'\[![\w-]+\]', '', topic)
        # Remove emoji and special chars
        topic = re.sub(r'[^\w\s\-]', '', topic)
        topic = topic.strip()
        if topic and topic.lower() not in ['vocabulary', 'словник', 'activities', 'вправи', 'summary', 'підсумок']:
            cleaned.append(topic.lower())

    return cleaned


def extract_vocabulary_words(content: str) -> List[str]:
    """Extract vocabulary words from vocabulary section."""
    # Find vocabulary section (# Vocabulary or # Словник)
    vocab_pattern = r'^# (?:Vocabulary|Словник)\n\n(.*?)(?=\n#|\Z)'
    match = re.search(vocab_pattern, content, re.MULTILINE | re.DOTALL)

    if not match:
        return []

    vocab_section = match.group(1)

    # Extract words from table rows
    # Format: | word | ... | ... |
    words = []
    for line in vocab_section.split('\n'):
        if line.startswith('|') and not line.startswith('|--'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) > 1 and parts[1]:  # First column is word
                word = parts[1].strip()
                # Remove transliteration (text in parentheses)
                word = re.sub(r'\s*\([^)]+\)', '', word)
                # Remove multiple words separated by comma (keep first)
                word = word.split(',')[0].strip()
                if word and not word.lower().startswith('word'):
                    words.append(word.lower())

    return words


def extract_module_metadata(file_path: Path) -> Dict:
    """Extract all metadata from a single module."""
    content = file_path.read_text(encoding='utf-8')

    # Extract frontmatter
    frontmatter = extract_frontmatter(content)

    # Derive level and module_num from file path
    # e.g., curriculum/l2-uk-en/a1/01-the-cyrillic-code-i.md
    parts = file_path.parts
    level = parts[-2].upper()  # a1 -> A1
    filename = file_path.stem  # 01-the-cyrillic-code-i

    # Extract module number from filename
    match = re.match(r'^(\d+)-(.+)$', filename)
    if match:
        module_num = int(match.group(1))
        slug = match.group(2)
    else:
        module_num = 0
        slug = filename

    # Module ID format: {level}-{slug}
    module_id = f"{level.lower()}-{slug}"

    # Extract topics from H2 headers
    topics = extract_h2_topics(content)

    # Extract vocabulary words
    vocabulary = extract_vocabulary_words(content)

    # Get title from frontmatter
    title = frontmatter.get('title', filename.replace('-', ' ').title())

    return {
        "module_id": module_id,
        "level": level,
        "module_num": module_num,
        "title": title,
        "file_path": str(file_path),
        "topics": topics,
        "vocabulary": vocabulary,
        "vocab_count": len(vocabulary)
    }


def extract_all_modules() -> Dict[str, Dict]:
    """Extract metadata from all curriculum modules."""
    curriculum_path = Path('curriculum/l2-uk-en')

    all_metadata = {}
    levels = ['a1', 'a2', 'b1', 'b2']

    for level in levels:
        level_path = curriculum_path / level
        if not level_path.exists():
            print(f"⚠️  Level directory not found: {level_path}")
            continue

        # Find all .md files in level directory (not in subdirectories)
        md_files = sorted(level_path.glob('*.md'))

        for md_file in md_files:
            # Skip audit/review files
            if md_file.stem.endswith('-review'):
                continue

            metadata = extract_module_metadata(md_file)
            module_id = metadata['module_id']
            all_metadata[module_id] = metadata

            print(f"  Extracted: {module_id} - {metadata['title']}")

    return all_metadata


def save_metadata(metadata: Dict[str, Dict], output_path: Path):
    """Save module metadata to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved {len(metadata)} module metadata entries to {output_path}")


def main():
    """Main entry point."""
    output_path = Path('docs/resources/ukrainianlessons/module_metadata.json')

    print("🔍 Extracting module metadata from curriculum...\n")

    metadata = extract_all_modules()
    save_metadata(metadata, output_path)

    # Print summary by level
    print("\n📊 Summary by level:")
    by_level = {}
    for module_id, data in metadata.items():
        level = data['level']
        by_level[level] = by_level.get(level, 0) + 1

    for level in sorted(by_level.keys()):
        print(f"   {level}: {by_level[level]} modules")

    print(f"\n   Total: {len(metadata)} modules")

    # Sample output
    print("\n📝 Sample metadata (first module):")
    first_module = next(iter(metadata.values()))
    print(f"   Module ID: {first_module['module_id']}")
    print(f"   Title: {first_module['title']}")
    print(f"   Topics: {first_module['topics'][:5]}...")
    print(f"   Vocabulary count: {first_module['vocab_count']}")


if __name__ == '__main__':
    main()
