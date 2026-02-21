#!/usr/bin/env python3
"""
Vocabulary Source Tracer

Traces all Ukrainian words in a module to their sources:
- Markdown prose (with line numbers)
- Activities YAML (with activity type/index)
- Vocabulary YAML (translation status)

Shows which words are untranslated and where they came from.

Usage:
    .venv/bin/python scripts/vocab_trace_sources.py curriculum/l2-uk-en/b1/92-b1-final-exam.md
"""

import argparse
import re
import yaml
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Simple stopwords for filtering
STOPWORDS = {
    'і', 'в', 'на', 'з', 'у', 'до', 'від', 'за', 'по', 'під', 'над',
    'та', 'а', 'але', 'чи', 'або', 'що', 'як', 'бо', 'то', 'це',
    'не', 'ні', 'так', 'є', 'був', 'була', 'було', 'були',
}


def extract_words_from_markdown(md_path: Path) -> Dict[str, List[int]]:
    """Extract Ukrainian words with line numbers from markdown."""
    words = defaultdict(list)

    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_frontmatter = False
    in_code_block = False
    frontmatter_count = 0

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        # Track frontmatter
        if stripped == '---':
            frontmatter_count += 1
            if frontmatter_count <= 2:
                in_frontmatter = not in_frontmatter
            continue

        if in_frontmatter or in_code_block:
            continue

        # Track code blocks
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue

        # Skip tables
        if stripped.startswith('|'):
            continue

        # Extract words from line (including blockquotes)
        text = stripped.lstrip('>')  # Remove blockquote marker
        found_words = re.findall(r"[а-яіїєґА-ЯІЇЄҐ][а-яіїєґА-ЯІЇЄҐ'ʼ-]*", text)

        for word in found_words:
            word_lower = word.lower()
            if len(word_lower) > 1 and word_lower not in STOPWORDS:
                words[word_lower].append(line_num)

    return words


def extract_words_from_activities(activities_path: Path) -> Dict[str, List[str]]:
    """Extract Ukrainian words with activity context from YAML."""
    words = defaultdict(list)

    if not activities_path.exists():
        return words

    with open(activities_path, 'r', encoding='utf-8') as f:
        activities = yaml.safe_load(f)

    if not isinstance(activities, list):
        return words

    for idx, activity in enumerate(activities, 1):
        activity_type = activity.get('type', 'unknown')
        activity_title = activity.get('title', 'untitled')
        context = f"Activity #{idx} ({activity_type}): {activity_title}"

        # Convert activity to string and extract words
        activity_str = yaml.dump(activity, allow_unicode=True)
        found_words = re.findall(r"[а-яіїєґА-ЯІЇЄҐ][а-яіїєґА-ЯІЇЄҐ'ʼ-]*", activity_str)

        for word in found_words:
            word_lower = word.lower()
            if len(word_lower) > 1 and word_lower not in STOPWORDS:
                words[word_lower].append(context)

    return words


def load_vocab_translations(vocab_path: Path) -> Dict[str, str]:
    """Load vocabulary YAML and return word->translation mapping."""
    translations = {}

    if not vocab_path.exists():
        return translations

    with open(vocab_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not data or 'words' not in data:
        return translations

    for entry in data['words']:
        word = entry.get('word', '').lower()
        translation = entry.get('translation', '')
        if word:
            translations[word] = translation

    return translations


def main():
    parser = argparse.ArgumentParser(
        description='Trace vocabulary sources and translation status'
    )
    parser.add_argument('markdown', type=Path,
                        help='Module markdown file')
    parser.add_argument('--show-all', action='store_true',
                        help='Show all words, not just untranslated')

    args = parser.parse_args()

    md_path = args.markdown
    activities_path = md_path.parent / 'activities' / f"{md_path.stem}.yaml"
    vocab_path = md_path.parent / 'vocabulary' / f"{md_path.stem}.yaml"

    print("=" * 80)
    print(f"📊 VOCABULARY SOURCE TRACE: {md_path.name}")
    print("=" * 80)

    # Extract words from all sources
    md_words = extract_words_from_markdown(md_path)
    activity_words = extract_words_from_activities(activities_path)
    vocab_translations = load_vocab_translations(vocab_path)

    # Combine all unique words
    all_words = set(md_words.keys()) | set(activity_words.keys())

    print(f"\n📝 SOURCE STATISTICS:")
    print(f"  Words in markdown:    {len(md_words):,}")
    print(f"  Words in activities:  {len(activity_words):,}")
    print(f"  Words in vocab YAML:  {len(vocab_translations):,}")
    print(f"  Total unique words:   {len(all_words):,}")

    # Analyze translation status
    untranslated = []
    translated = []

    for word in sorted(all_words):
        translation = vocab_translations.get(word, '')
        sources = []

        if word in md_words:
            line_nums = md_words[word][:3]  # First 3 occurrences
            sources.append(f"MD:L{','.join(map(str, line_nums))}")

        if word in activity_words:
            contexts = activity_words[word][:2]  # First 2 contexts
            sources.append(f"YAML:{len(activity_words[word])} times")

        source_str = " | ".join(sources)

        if not translation:
            untranslated.append((word, source_str))
        else:
            translated.append((word, translation, source_str))

    print(f"\n  Translated:     {len(translated):,}")
    print(f"  Untranslated:   {len(untranslated):,}")
    print(f"  Coverage:       {len(translated)/len(all_words)*100:.1f}%")

    # Show untranslated words
    if untranslated:
        print(f"\n🔴 UNTRANSLATED WORDS ({len(untranslated)}):")
        print("-" * 80)
        for word, sources in untranslated[:50]:  # Limit to 50
            print(f"  {word:30} → {sources}")

        if len(untranslated) > 50:
            print(f"\n  ... and {len(untranslated) - 50} more")

    # Show sample of translated words if requested
    if args.show_all and translated:
        print(f"\n✅ SAMPLE TRANSLATED WORDS:")
        print("-" * 80)
        for word, translation, sources in translated[:20]:
            print(f"  {word:20} → {translation:30} | {sources}")

    # Analysis summary
    print(f"\n📈 ANALYSIS:")

    # Words only in markdown
    only_md = set(md_words.keys()) - set(activity_words.keys())
    print(f"  Words ONLY in markdown:     {len(only_md):,}")

    # Words only in activities
    only_activities = set(activity_words.keys()) - set(md_words.keys())
    print(f"  Words ONLY in activities:   {len(only_activities):,}")

    # Words in both
    in_both = set(md_words.keys()) & set(activity_words.keys())
    print(f"  Words in BOTH:              {len(in_both):,}")

    # Words not in vocab YAML
    not_in_vocab = all_words - set(vocab_translations.keys())
    print(f"  Words NOT in vocab YAML:    {len(not_in_vocab):,}")

    if not_in_vocab:
        print(f"\n💡 RECOMMENDATION:")
        print(f"  {len(not_in_vocab)} words are used but not in vocabulary YAML.")
        print(f"  They may be:")
        print(f"    - Already known from previous modules (filtered by delta extraction)")
        print(f"    - Proper nouns or place names")
        print(f"    - Inflected forms not lemmatized to dictionary form")
        print(f"    - Words that need to be added manually")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
