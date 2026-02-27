#!/usr/bin/env python3
"""
Auto-extract Ukrainian vocabulary from module content.

Scans module .md files for Ukrainian words, filters out vocabulary from
prior modules, and creates skeleton YAML entries ready for enrichment.

Usage:
    .venv/bin/python scripts/auto_vocab_extract.py curriculum/l2-uk-en/hist/volodymyr-monomakh.md
    
Output:
    Creates/updates curriculum/l2-uk-en/hist/vocabulary/volodymyr-monomakh.yaml
    with skeleton entries for all new words found in content.
"""

import re
import argparse
import sqlite3
from pathlib import Path
from typing import Set, List, Dict
import yaml

# Configure YAML for Unicode
def setup_yaml():
    yaml.Dumper.ignore_aliases = lambda *args: True
    
setup_yaml()


# =============================================================================
# UKRAINIAN TEXT EXTRACTION
# =============================================================================

def extract_ukrainian_text(md_path: Path) -> str:
    """
    Extract Ukrainian text from markdown content.
    
    Skips:
    - Frontmatter (between --- markers)
    - Code blocks (``` markers)
    - Tables (| markers)
    - English text
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    ukrainian_text = []
    in_frontmatter = False
    in_code_block = False
    
    for line in content.split('\n'):
        stripped = line.strip()
        
        # Toggle frontmatter
        if stripped == '---':
            in_frontmatter = not in_frontmatter
            continue
        
        # Skip frontmatter
        if in_frontmatter:
            continue
        
        # Toggle code blocks
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        
        # Skip code blocks
        if in_code_block:
            continue
        
        # Skip tables
        if stripped.startswith('|'):
            continue
        
        # Skip headers (we want the text in headers too, but not the # symbols)
        if stripped.startswith('#'):
            stripped = re.sub(r'^#+\s*', '', stripped)
        
        # Check if line contains Cyrillic (Ukrainian content)
        if re.search(r'[\u0400-\u04FF]', stripped):
            ukrainian_text.append(stripped)
    
    return '\n'.join(ukrainian_text)


# =============================================================================
# TOKENIZATION & FILTERING
# =============================================================================

def tokenize_ukrainian(text: str) -> Set[str]:
    """
    Extract individual Ukrainian words from text.
    
    Returns a set of unique words (lowercased).
    """
    # Remove punctuation but keep apostrophes and hyphens within words
    # Pattern: match Ukrainian words (Cyrillic + apostrophe/hyphen)
    words = re.findall(r"[а-яіїєґА-ЯІЇЄҐ][а-яіїєґА-ЯІЇЄҐ'ʼ-]*", text)
    
    # Lowercase and deduplicate
    unique_words = {word.lower() for word in words if len(word) > 1}
    
    # Filter out common words that shouldn't be in vocabulary
    # (these are too basic for B2+ level)
    exclude = {
        # Prepositions
        'і', 'в', 'на', 'з', 'у', 'до', 'від', 'за', 'по', 'під', 'над',
        'про', 'для', 'без', 'через', 'після', 'перед', 'між', 'серед',
        # Conjunctions
        'та', 'а', 'але', 'чи', 'або', 'що', 'як', 'бо', 'тому', 'коли',
        'якщо', 'хоча', 'щоб',
        # Pronouns
        'це', 'цей', 'ця', 'ці', 'той', 'та', 'ті', 'він', 'вона', 'воно', 'вони',
        'мій', 'моя', 'моє', 'мої', 'твій', 'твоя', 'твоє', 'твої',
        'наш', 'наша', 'наше', 'наші', 'ваш', 'ваша', 'ваше', 'ваші',
        'його', 'її', 'їх', 'хто', 'що', 'який', 'яка', 'яке', 'які',
        # Common verbs
        'є', 'був', 'була', 'було', 'були', 'буде', 'будуть', 'бути',
        'мати', 'має', 'мав', 'мала', 'мали', 'матиме',
        'може', 'міг', 'могла', 'могли',
        'треба', 'можна', 'потрібно',
        # Particles & adverbs
        'не', 'ні', 'так', 'вже', 'ще', 'дуже', 'тільки', 'також', 'навіть',
        'там', 'тут', 'де', 'коли', 'чому', 'куди', 'звідки'
    }
    
    return unique_words - exclude


# =============================================================================
# PRIOR VOCABULARY LOADING
# =============================================================================

def load_prior_vocabulary(md_path: Path) -> Set[str]:
    """
    Load vocabulary from all prior modules in this level.
    
    For tracks (hist, bio, etc.), loads vocabulary from
    all modules that come before this one in the curriculum.
    """
    level_dir = md_path.parent
    level_name = level_dir.name
    vocab_dir = level_dir / 'vocabulary'
    
    if not vocab_dir.exists():
        return set()
    
    # Get all vocabulary YAML files
    vocab_files = sorted(vocab_dir.glob('*.yaml'))
    
    # For now, load ALL vocabulary from the level
    # TODO: Could be enhanced to only load modules 01-current
    all_vocab = set()
    
    for vocab_file in vocab_files:
        # Skip the current module's vocab file
        if vocab_file.stem == md_path.stem:
            continue
        
        try:
            with open(vocab_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict) and 'lemma' in entry:
                        all_vocab.add(entry['lemma'].lower())
        except Exception as e:
            print(f"Warning: Could not load {vocab_file.name}: {e}")
    
    return all_vocab


def load_db_baseline() -> Set[str]:
    """
    Load vocabulary baseline from the vocabulary database.
    
    Returns all words from A1-B2 core levels.
    """
    db_path = Path("curriculum/l2-uk-en/vocabulary.db")
    
    if not db_path.exists():
        print(f"  Warning: Database not found at {db_path}")
        return set()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all lemmas from core levels
        cursor.execute("""
            SELECT uk FROM lemmas 
            WHERE level IN ('A1', 'A2', 'B1', 'B2')
        """)
        
        words = {row[0].lower() for row in cursor.fetchall()}
        conn.close()
        
        return words
    except Exception as e:
        print(f"  Warning: Could not load DB baseline: {e}")
        return set()


# =============================================================================
# POS DETECTION (Simple Heuristics)
# =============================================================================

def detect_pos(word: str) -> str:
    """
    Detect part of speech using Ukrainian morphology heuristics.

    Returns: 'noun', 'verb', 'adj', or 'adv'
    """
    word = word.lower()

    # Verb forms (infinitive, past tense, participles)
    if word.endswith(('ти', 'тися', 'тись', 'сти', 'чти')):
        return 'verb'
    if word.endswith(('ив', 'ив', 'ала', 'али', 'ало', 'ила', 'или', 'ило')):
        return 'verb'

    # Adverb endings
    if word.endswith(('но', 'льно', 'ньо', 'ом', 'єм', 'ем')):
        return 'adv'

    # Adjective endings (more comprehensive)
    # Full forms: -ий, -а, -е, -і
    # Comparative: -іший, -ший
    # Relational: -ський, -цький, -зький, -ний, -ній
    adj_suffixes = [
        'ний', 'на', 'не', 'ні',  # verbal adjectives
        'тний', 'тна', 'тне',  # quality adjectives
        'ський', 'ська', 'ське', 'ські',  # relational
        'цький', 'цька', 'цьке', 'цькі',
        'зький', 'зька', 'зьке', 'зькі',
        'івський', 'івська', 'івське',
        'овий', 'ова', 'ове', 'ові',
        'евий', 'ева', 'еве', 'еві',
        'іший', 'іша', 'іше', 'іші',  # comparative
        'ший', 'ша', 'ше', 'ші',
        'им', 'ім',  # instrumental forms of adjectives
        'ою', 'ою',  # instrumental feminine
    ]

    for suffix in adj_suffixes:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return 'adj'

    # Default to noun (most common for content words)
    return 'noun'


def detect_gender(word: str) -> str:
    """
    Detect grammatical gender for nouns.
    
    Returns: 'm', 'f', 'n', or None
    """
    word = word.lower()
    
    # Feminine: ends in -а, -я, -іння, -ість
    if word.endswith(('а', 'я', 'іння', 'ість', 'ня')):
        return 'f'
    
    # Neuter: ends in -о, -е, -я (diminutives), -ство
    if word.endswith(('о', 'е', 'ство', 'ття', 'ня')):
        return 'n'
    
    # Masculine: consonant, -ій, -ар, -ор, -ір
    if word.endswith(('ій', 'ар', 'ор', 'ір', 'ець', 'ець')) or word[-1] in 'бвгджзклмнпрстфхцчшщ':
        return 'm'
    
    return None


# =============================================================================
# YAML GENERATION
# =============================================================================

def create_skeleton_entries(words: Set[str]) -> List[Dict]:
    """
    Create skeleton YAML entries for vocabulary words.
    
    Returns list of dictionaries ready for YAML serialization.
    """
    entries = []
    
    for word in sorted(words):
        pos = detect_pos(word)
        entry = {
            'lemma': word,
            'ipa': '',  # Empty - to be filled by enrichment
            'translation': '',  # Empty - to be filled by enrichment
            'pos': pos
        }
        
        # Add gender for nouns
        if pos == 'noun':
            gender = detect_gender(word)
            if gender:
                entry['gender'] = gender
        
        entries.append(entry)
    
    return entries


def update_vocabulary_yaml(md_path: Path, new_entries: List[Dict]):
    """
    Update or create the vocabulary YAML file for this module.
    
    Merges with existing entries if file exists.
    """
    vocab_dir = md_path.parent / 'vocabulary'
    vocab_dir.mkdir(exist_ok=True)
    
    vocab_file = vocab_dir / f"{md_path.stem}.yaml"
    
    # Load existing entries if file exists
    existing_entries = []
    existing_lemmas = set()
    
    if vocab_file.exists():
        with open(vocab_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if isinstance(data, list):
            existing_entries = data
            existing_lemmas = {e['lemma'].lower() for e in data if isinstance(e, dict) and 'lemma' in e}
    
    # Add only new entries
    for entry in new_entries:
        if entry['lemma'].lower() not in existing_lemmas:
            existing_entries.append(entry)
    
    # Write back to file
    with open(vocab_file, 'w', encoding='utf-8') as f:
        yaml.dump(existing_entries, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    return vocab_file, len(new_entries)


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Auto-extract Ukrainian vocabulary from module content'
    )
    parser.add_argument('md_file', type=Path, help='Path to module .md file')
    parser.add_argument('--min-words', type=int, default=2, help='Minimum word length (default: 2)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be extracted without writing files')
    parser.add_argument('--use-db-baseline', action='store_true', help='Use vocabulary.db as baseline for deduplication (for tracks like hist)')
    
    args = parser.parse_args()
    
    if not args.md_file.exists():
        print(f"Error: File not found: {args.md_file}")
        return 1
    
    print(f"Extracting vocabulary from: {args.md_file.name}")
    
    # Step 1: Extract Ukrainian text from markdown
    ukrainian_text = extract_ukrainian_text(args.md_file)
    
    # Step 2: Tokenize into words
    all_words = tokenize_ukrainian(ukrainian_text)
    print(f"  Found {len(all_words)} unique words in content")
    
    # Step 3: Load prior vocabulary
    if args.use_db_baseline:
        db_vocab = load_db_baseline()
        print(f"  DB baseline (A1-B2): {len(db_vocab)} words")
        level_vocab = load_prior_vocabulary(args.md_file)
        print(f"  Level vocabulary: {len(level_vocab)} words")
        prior_vocab = db_vocab | level_vocab
    else:
        prior_vocab = load_prior_vocabulary(args.md_file)
    print(f"  Total prior vocabulary: {len(prior_vocab)} words")
    
    # Step 4: Filter to new words only
    new_words = all_words - prior_vocab
    print(f"  New words: {len(new_words)}")
    
    if not new_words:
        print("  ✓ No new vocabulary to extract (all words already in prior modules)")
        return 0
    
    # Step 5: Create skeleton entries
    skeleton_entries = create_skeleton_entries(new_words)
    
    if args.dry_run:
        print("\n  Dry run - would extract:")
        for entry in skeleton_entries[:10]:
            print(f"    - {entry['lemma']} ({entry['pos']})")
        if len(skeleton_entries) > 10:
            print(f"    ... and {len(skeleton_entries) - 10} more")
        return 0
    
    # Step 6: Update vocabulary YAML
    vocab_file, count = update_vocabulary_yaml(args.md_file, skeleton_entries)
    
    print(f"\n  ✅ Extracted {count} new words to {vocab_file.name}")
    print(f"  💡 Run enrichment next:")
    print(f"     .venv/bin/python scripts/enrich_yaml_vocab.py {vocab_file}")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
