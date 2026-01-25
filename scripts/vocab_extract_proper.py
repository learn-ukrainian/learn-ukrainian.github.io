#!/usr/bin/env python3
"""
Proper Vocabulary Extraction with NLP Lemmatization.

Extracts vocabulary FROM MARKDOWN SOURCE FILES, properly lemmatizes using
pymorphy3, and creates clean vocabulary YAML files.

This replaces the broken workflow of:
  bad markdown → bad extraction → bad DB → bad YAMLs

New workflow:
  markdown source → pymorphy3 lemmatization → clean YAMLs → clean DB

Usage:
    .venv/bin/python scripts/vocab_extract_proper.py curriculum/l2-uk-en/b2-hist/*.md
    .venv/bin/python scripts/vocab_extract_proper.py curriculum/l2-uk-en/b2-hist/trypillian-civilization.md
"""

import argparse
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Optional
import yaml

# =============================================================================
# LAZY-LOADED NLP TOOLS
# =============================================================================

_morph = None
_stressifier = None


def get_morph():
    """Lazy load pymorphy3 MorphAnalyzer for Ukrainian."""
    global _morph
    if _morph is None:
        from pymorphy3 import MorphAnalyzer
        _morph = MorphAnalyzer(lang='uk')
    return _morph


def get_stressifier():
    """Lazy load ukrainian-word-stress Stressifier."""
    global _stressifier
    if _stressifier is None:
        from ukrainian_word_stress import Stressifier, StressSymbol
        _stressifier = Stressifier(stress_symbol=StressSymbol.CombiningAcuteAccent)
    return _stressifier


# =============================================================================
# CYRILLIC TO IPA MAPPING
# =============================================================================

CYRILLIC_TO_IPA = {
    'а': 'a', 'б': 'b', 'в': 'ʋ', 'г': 'ɦ', 'ґ': 'g',
    'д': 'd', 'е': 'ɛ', 'є': 'jɛ', 'ж': 'ʒ', 'з': 'z',
    'и': 'ɪ', 'і': 'i', 'ї': 'ji', 'й': 'j', 'к': 'k',
    'л': 'l', 'м': 'm', 'н': 'n', 'о': 'ɔ', 'п': 'p',
    'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
    'х': 'x', 'ц': 't͡s', 'ч': 't͡ʃ', 'ш': 'ʃ', 'щ': 'ʃt͡ʃ',
    'ь': 'ʲ', 'ю': 'ju', 'я': 'ja', "'": '', 'ʼ': '',
}

STRESS_MARK = '\u0301'


def stressed_to_ipa(stressed_word: str) -> str:
    """Convert stressed Ukrainian word to IPA notation."""
    if not stressed_word:
        return ''
    
    ipa_chars = []
    stress_placed = False
    i = 0
    
    while i < len(stressed_word):
        char = stressed_word[i].lower()
        is_stressed = (i + 1 < len(stressed_word) and 
                       stressed_word[i + 1] == STRESS_MARK)
        
        if char == STRESS_MARK:
            i += 1
            continue
        
        ipa = CYRILLIC_TO_IPA.get(char, char)
        
        if is_stressed and not stress_placed:
            ipa_chars.append('ˈ')
            stress_placed = True
        
        ipa_chars.append(ipa)
        i += 1
    
    result = ''.join(ipa_chars)
    return f"/{result}/" if result else ''


# =============================================================================
# POS AND GENDER MAPPING
# =============================================================================

POS_MAP = {
    'NOUN': 'noun', 'ADJF': 'adj', 'ADJS': 'adj', 'COMP': 'adj',
    'VERB': 'verb', 'INFN': 'verb', 'PRTF': 'verb', 'PRTS': 'verb', 'GRND': 'verb',
    'NUMR': 'num', 'ADVB': 'adv', 'NPRO': 'pron', 'PRED': 'adv',
    'PREP': 'prep', 'CONJ': 'conj', 'PRCL': 'part', 'INTJ': 'interj',
}

GENDER_MAP = {'masc': 'm', 'femn': 'f', 'neut': 'n'}


# =============================================================================
# STOPWORDS (function words to exclude from vocabulary)
# =============================================================================

STOPWORDS = {
    # Prepositions
    'і', 'в', 'на', 'з', 'у', 'до', 'від', 'за', 'по', 'під', 'над',
    'про', 'для', 'без', 'через', 'після', 'перед', 'між', 'серед', 'при', 'біля',
    # Conjunctions
    'та', 'а', 'але', 'чи', 'або', 'що', 'як', 'бо', 'тому', 'коли',
    'якщо', 'хоча', 'щоб', 'проте', 'однак', 'тож', 'адже', 'оскільки',
    # Pronouns (common)
    'це', 'цей', 'ця', 'ці', 'той', 'ті', 'він', 'вона', 'воно', 'вони',
    'мій', 'моя', 'моє', 'мої', 'твій', 'твоя', 'твоє', 'твої',
    'наш', 'наша', 'наше', 'наші', 'ваш', 'ваша', 'ваше', 'ваші',
    'його', 'її', 'їх', 'їхній', 'свій', 'себе', 'собі',
    'хто', 'який', 'яка', 'яке', 'які', 'котрий', 'чий',
    # Particles & adverbs (very common)
    'не', 'ні', 'так', 'вже', 'ще', 'дуже', 'тільки', 'також', 'навіть',
    'там', 'тут', 'де', 'коли', 'чому', 'куди', 'звідки', 'ось', 'он',
    'теж', 'лише', 'саме', 'майже', 'просто', 'зовсім',
    # Common verbs (auxiliary/modal)
    'бути', 'є', 'був', 'була', 'було', 'були', 'буде', 'будуть',
    'мати', 'має', 'мав', 'мала', 'мали',
    'могти', 'може', 'міг', 'могла', 'могли',
    'хотіти', 'хоче', 'хотів', 'хотіла',
    'треба', 'можна', 'потрібно', 'слід',
    # Numbers (basic)
    'один', 'одна', 'одне', 'два', 'дві', 'три', 'чотири', 'пять',
    # Articles/demonstratives already covered
}


# =============================================================================
# TEXT EXTRACTION FROM MARKDOWN
# =============================================================================

def extract_module_number(md_path: Path) -> int:
    """
    Extract module number from filename or meta sidecar.
    Example: '01-title.md' -> 1
    Example: 'slug.md' -> looks in meta/slug.yaml for 'module' field
    """
    # 1. Try filename prefix
    match = re.match(r'(\d+)', md_path.name)
    if match:
        return int(match.group(1))
    
    # 2. Try meta sidecar
    meta_path = md_path.parent / 'meta' / f"{md_path.stem}.yaml"
    if meta_path.exists():
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for 'module: ...-XX'
                match = re.search(r'module:.*-(\d+)', content)
                if match:
                    return int(match.group(1))
        except:
            pass
            
    return 999  # Fallback


def extract_ukrainian_text(md_path: Path) -> str:
    """
    Extract Ukrainian text from markdown, skipping:
    - Frontmatter (--- ... ---)
    - Code blocks (``` ... ```)
    - Tables (| ... |)
    - YAML callouts (> [!...])
    """
    content = md_path.read_text(encoding='utf-8')
    
    lines = []
    in_frontmatter = False
    in_code_block = False
    frontmatter_count = 0
    
    for line in content.split('\n'):
        stripped = line.strip()
        
        # Toggle frontmatter
        if stripped == '---':
            frontmatter_count += 1
            if frontmatter_count <= 2:
                in_frontmatter = not in_frontmatter
            continue
        
        if in_frontmatter:
            continue
        
        # Toggle code blocks
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        
        if in_code_block:
            continue
        
        # Skip tables
        if stripped.startswith('|'):
            continue
        
        # Skip callout markers but keep text
        if stripped.startswith('> [!'):
            continue
        
        # Skip pure HTML
        if stripped.startswith('<') and stripped.endswith('>'):
            continue
        
        # Remove markdown header markers but keep text
        if stripped.startswith('#'):
            stripped = re.sub(r'^#+\s*', '', stripped)
        
        # Keep if contains Cyrillic
        if re.search(r'[\u0400-\u04FF]', stripped):
            lines.append(stripped)
    
    return '\n'.join(lines)


def get_known_lemmas(db_path: Path) -> Set[str]:
    """Get set of all unique lemmas already in the database."""
    if not db_path.exists():
        return set()
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT uk FROM lemmas")
        lemmas = {row[0] for row in cur.fetchall()}
        conn.close()
        return lemmas
    except Exception as e:
        print(f"  ⚠️  Warning: Could not read database for filtering: {e}")
        return set()


def tokenize_and_lemmatize(text: str, known_lemmas: Optional[Set[str]] = None) -> Dict[str, Dict]:
    """
    Tokenize Ukrainian text and lemmatize each word using pymorphy3.
    
    Returns dict: {lemma: {pos, gender, count}}
    """
    morph = get_morph()
    
    # Extract all Ukrainian word tokens
    words = re.findall(r"[а-яіїєґА-ЯІЇЄҐ][а-яіїєґА-ЯІЇЄҐ'ʼ-]*", text)
    
    lemma_data = {}
    
    for word in words:
        word_lower = word.lower()
        
        # Skip short words and stopwords
        if len(word_lower) <= 1:
            continue
        if word_lower in STOPWORDS:
            continue
        
        # Analyze with pymorphy3
        parsed = morph.parse(word_lower)
        if not parsed:
            continue
        
        best = parsed[0]
        lemma = best.normal_form
        
        # Skip if lemma is a stopword
        if lemma in STOPWORDS:
            continue
        
        # SKIP if already known (Delta Extraction)
        if known_lemmas and lemma in known_lemmas:
            continue
        
        # Get POS
        pos = POS_MAP.get(best.tag.POS, 'noun')
        
        # Get gender for nouns
        gender = None
        if pos == 'noun' and best.tag.gender:
            gender = GENDER_MAP.get(best.tag.gender)
        
        # Update or create entry
        if lemma not in lemma_data:
            lemma_data[lemma] = {
                'pos': pos,
                'gender': gender,
                'count': 0
            }
        lemma_data[lemma]['count'] += 1
    
    return lemma_data


def create_vocabulary_entries(lemma_data: Dict[str, Dict], min_count: int = 1) -> List[Dict]:
    """
    Create vocabulary YAML entries from lemma data.
    
    Filters by minimum occurrence count and adds IPA.
    """
    stressifier = get_stressifier()
    entries = []
    
    for lemma, data in sorted(lemma_data.items()):
        if data['count'] < min_count:
            continue
        
        # Get stressed form and IPA
        try:
            stressed = stressifier(lemma)
            ipa = stressed_to_ipa(stressed)
        except Exception:
            ipa = ''
        
        entry = {
            'lemma': lemma,
            'ipa': ipa,
            'translation': '',  # To be filled manually or by LLM
            'pos': data['pos'],
        }
        
        if data['gender']:
            entry['gender'] = data['gender']
        
        entries.append(entry)
    
    return entries


# =============================================================================
# MAIN
# =============================================================================

def process_module(md_path: Path, output_dir: Optional[Path] = None, 
                   dry_run: bool = False, min_count: int = 1,
                   known_lemmas: Optional[Set[str]] = None) -> Dict:
    """
    Process a single module markdown file.
    
    Returns statistics dict.
    """
    # Try to detect level from path
    level = "UNKNOWN"
    for part in md_path.parts:
        if part.lower() in ['a1', 'a2', 'b1', 'b2', 'b2-hist', 'b2-pro', 'c1', 'c1-bio', 'c1-pro', 'lit']:
            level = part.upper()
            break

    # Output to vocabulary/ subdirectory by default
    if output_dir is None:
        output_dir = md_path.parent / 'vocabulary'
    
    output_path = output_dir / f"{md_path.stem}.yaml"
    
    # Extract and process
    text = extract_ukrainian_text(md_path)
    lemma_data = tokenize_and_lemmatize(text, known_lemmas)
    entries = create_vocabulary_entries(lemma_data, min_count)
    
    # Wrap in standard schema
    data = {
        'module': md_path.stem,
        'level': level,
        'version': '2.0',
        'items': entries
    }
    
    stats = {
        'module': md_path.name,
        'words_found': sum(d['count'] for d in lemma_data.values()),
        'unique_lemmas': len(lemma_data),
        'entries_created': len(entries),
    }
    
    if not dry_run and entries:
        output_dir.mkdir(exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Extract vocabulary from markdown with proper lemmatization'
    )
    parser.add_argument('files', nargs='+', type=Path,
                        help='Markdown files to process')
    parser.add_argument('--min-count', type=int, default=1,
                        help='Minimum word occurrences to include (default: 1)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview without writing files')
    parser.add_argument('--output-dir', type=Path,
                        help='Output directory (default: vocabulary/ subdir)')
    
    args = parser.parse_args()
    
    # Delta extraction check
    db_path = Path("curriculum/l2-uk-en/vocabulary.db")
    known_lemmas = get_known_lemmas(db_path) if db_path.exists() else set()
    
    if known_lemmas:
        print(f"  🔍 Knowledge-Aware: Filtering against {len(known_lemmas):,} known lemmas")
    
    print("=" * 60)
    print("📝 PROPER VOCABULARY EXTRACTION (with pymorphy3)")
    print("=" * 60)
    
    total_words = 0
    total_lemmas = 0
    total_entries = 0
    
    # Sort files numerically to ensure sequential extraction
    files = sorted([f for f in args.files if f.exists() and not f.is_dir()], 
                   key=extract_module_number)
    
    for md_path in files:
        stats = process_module(md_path, args.output_dir, args.dry_run, args.min_count, known_lemmas)
        
        # CUMULATIVE UPDATE: Add newly found entries to known_lemmas for the next file in batch
        if known_lemmas is not None and not args.dry_run:
            # We need to re-extract the lemmas we just saved to YAML to update the set
            # Or better, process_module can return them.
            text = extract_ukrainian_text(md_path)
            current_results = tokenize_and_lemmatize(text, known_lemmas)
            # Add these new ones to the set for the NEXT file
            for lemma in current_results:
                known_lemmas.add(lemma)
        
        total_words += stats['words_found']
        total_lemmas += stats['unique_lemmas']
        total_entries += stats['entries_created']
        
        print(f"  ✓ {stats['module']}: {stats['words_found']} words → {stats['entries_created']} lemmas")
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"  Total words processed: {total_words:,}")
    print(f"  Unique lemmas found:   {total_lemmas:,}")
    print(f"  Entries created:       {total_entries:,}")
    
    if args.dry_run:
        print("\n  [DRY RUN - no files written]")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
