#!/usr/bin/env python3
"""
Vocabulary Enrichment using Ukrainian NLP Tools.

Uses:
- pymorphy2: Lemmatization & POS tagging
- ukrainian-word-stress: Stress marks → IPA conversion

Usage:
    .venv/bin/python scripts/vocab_enrich_nlp.py curriculum/l2-uk-en/b2-hist/vocabulary/trypillian-civilization.yaml

This script:
1. Loads a vocabulary YAML file
2. For each entry:
   - Converts word form to proper lemma (dictionary form)
   - Gets correct POS tag from pymorphy2
   - Adds stress marks using ukrainian-word-stress
   - Converts stressed form to IPA notation
3. Deduplicates entries (multiple word forms → one lemma)
4. Writes back enriched YAML
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml

# Lazy imports for heavy dependencies
_morph = None
_stressifier = None


def get_morph():
    """Lazy load pymorphy3 MorphAnalyzer."""
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
# UKRAINIAN PHONEME TO IPA MAPPING
# =============================================================================

# Ukrainian letters to IPA (simplified, standard pronunciation)
CYRILLIC_TO_IPA = {
    'а': 'a', 'б': 'b', 'в': 'ʋ', 'г': 'ɦ', 'ґ': 'g',
    'д': 'd', 'е': 'ɛ', 'є': 'jɛ', 'ж': 'ʒ', 'з': 'z',
    'и': 'ɪ', 'і': 'i', 'ї': 'ji', 'й': 'j', 'к': 'k',
    'л': 'l', 'м': 'm', 'н': 'n', 'о': 'ɔ', 'п': 'p',
    'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
    'х': 'x', 'ц': 't͡s', 'ч': 't͡ʃ', 'ш': 'ʃ', 'щ': 'ʃt͡ʃ',
    'ь': 'ʲ', 'ю': 'ju', 'я': 'ja', "'": '', 'ʼ': '',
}

# Stress mark (combining acute accent)
STRESS_MARK = '\u0301'


def stressed_to_ipa(stressed_word: str) -> str:
    """
    Convert a stressed Ukrainian word to IPA notation.
    
    Example:
        Input: "культу́ра" (with combining acute accent after у)
        Output: "/kulʲˈtura/"
    """
    if not stressed_word:
        return ''
    
    ipa_chars = []
    stress_placed = False
    prev_char = ''
    
    i = 0
    while i < len(stressed_word):
        char = stressed_word[i].lower()
        
        # Check if next character is stress mark
        is_stressed = (i + 1 < len(stressed_word) and 
                       stressed_word[i + 1] == STRESS_MARK)
        
        # Skip the stress mark itself
        if char == STRESS_MARK:
            i += 1
            continue
        
        # Get IPA for this character
        ipa = CYRILLIC_TO_IPA.get(char, char)
        
        # Place stress mark BEFORE the stressed vowel's syllable
        if is_stressed and not stress_placed:
            ipa_chars.append('ˈ')
            stress_placed = True
        
        ipa_chars.append(ipa)
        prev_char = char
        i += 1
    
    # Wrap in slashes
    result = ''.join(ipa_chars)
    if result:
        return f"/{result}/"
    return ''


# =============================================================================
# POS TAG MAPPING
# =============================================================================

# pymorphy2 POS tags to our simplified tags
POS_MAP = {
    'NOUN': 'noun',
    'ADJF': 'adj',   # full adjective
    'ADJS': 'adj',   # short adjective
    'COMP': 'adj',   # comparative
    'VERB': 'verb',
    'INFN': 'verb',  # infinitive
    'PRTF': 'verb',  # participle (full)
    'PRTS': 'verb',  # participle (short)
    'GRND': 'verb',  # gerund
    'NUMR': 'num',   # numeral
    'ADVB': 'adv',   # adverb
    'NPRO': 'pron',  # pronoun
    'PRED': 'adv',   # predicative
    'PREP': 'prep',  # preposition
    'CONJ': 'conj',  # conjunction
    'PRCL': 'part',  # particle
    'INTJ': 'interj', # interjection
}

# Gender tag mapping
GENDER_MAP = {
    'masc': 'm',
    'femn': 'f',
    'neut': 'n',
}


def analyze_word(word: str) -> Dict:
    """
    Analyze a Ukrainian word using pymorphy2.
    
    Returns:
        {
            'lemma': '...',  # dictionary form
            'pos': '...',    # part of speech
            'gender': '...'  # for nouns only
        }
    """
    morph = get_morph()
    parsed = morph.parse(word)
    
    if not parsed:
        return {'lemma': word, 'pos': 'noun', 'gender': None}
    
    # Take the most likely parse
    best = parsed[0]
    
    result = {
        'lemma': best.normal_form,
        'pos': POS_MAP.get(best.tag.POS, 'noun'),
        'gender': None
    }
    
    # Get gender for nouns
    if best.tag.gender:
        result['gender'] = GENDER_MAP.get(best.tag.gender)
    
    return result


def get_stressed_form(word: str) -> str:
    """
    Get the stressed form of a Ukrainian word.
    
    Returns the word with a combining acute accent on the stressed vowel.
    """
    try:
        stressifier = get_stressifier()
        stressed = stressifier(word)
        return stressed
    except Exception as e:
        print(f"  Warning: Could not stress '{word}': {e}")
        return word


# =============================================================================
# YAML PROCESSING
# =============================================================================

def setup_yaml():
    """Configure YAML for proper Unicode handling."""
    yaml.Dumper.ignore_aliases = lambda *args: True


def enrich_vocabulary(yaml_path: Path, dry_run: bool = False) -> Dict:
    """
    Enrich a vocabulary YAML file with lemmas, POS, and IPA.
    
    Returns statistics about the enrichment.
    """
    stats = {
        'original_count': 0,
        'deduplicated_count': 0,
        'ipa_added': 0,
        'lemmas_corrected': 0,
        'pos_corrected': 0,
    }
    
    # Load existing YAML
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not data or not isinstance(data, list):
        print(f"  Warning: No vocabulary items found in {yaml_path.name}")
        return stats
    
    stats['original_count'] = len(data)
    print(f"  Processing {len(data)} entries...")
    
    # Process and deduplicate
    seen_lemmas: Set[str] = set()
    enriched_entries: List[Dict] = []
    
    for i, entry in enumerate(data):
        if not isinstance(entry, dict) or 'lemma' not in entry:
            continue
        
        original_word = entry['lemma']
        
        # Analyze with pymorphy2
        analysis = analyze_word(original_word)
        true_lemma = analysis['lemma']
        
        # Skip if we've already seen this lemma
        if true_lemma.lower() in seen_lemmas:
            continue
        seen_lemmas.add(true_lemma.lower())
        
        # Track corrections
        if true_lemma != original_word:
            stats['lemmas_corrected'] += 1
        if analysis['pos'] != entry.get('pos'):
            stats['pos_corrected'] += 1
        
        # Get stressed form and IPA
        ipa = entry.get('ipa', '')
        if not ipa:
            stressed = get_stressed_form(true_lemma)
            ipa = stressed_to_ipa(stressed)
            if ipa:
                stats['ipa_added'] += 1
        
        # Build enriched entry
        enriched = {
            'lemma': true_lemma,
            'ipa': ipa,
            'translation': entry.get('translation', ''),
            'pos': analysis['pos'],
        }
        
        # Add gender for nouns
        if analysis['pos'] == 'noun' and analysis['gender']:
            enriched['gender'] = analysis['gender']
        
        enriched_entries.append(enriched)
        
        # Progress indicator
        if (i + 1) % 500 == 0:
            print(f"    Processed {i + 1}/{len(data)} entries...")
    
    stats['deduplicated_count'] = len(enriched_entries)
    
    # Write back if not dry run
    if not dry_run:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(enriched_entries, f, 
                     allow_unicode=True, 
                     default_flow_style=False, 
                     sort_keys=False)
        print(f"  ✅ Wrote {len(enriched_entries)} entries to {yaml_path.name}")
    else:
        print(f"  [DRY RUN] Would write {len(enriched_entries)} entries")
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Enrich Ukrainian vocabulary with lemmas, POS, and IPA using NLP tools'
    )
    parser.add_argument('yaml_file', type=Path, 
                        help='Path to vocabulary YAML file')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without writing files')
    
    args = parser.parse_args()
    
    if not args.yaml_file.exists():
        print(f"Error: File not found: {args.yaml_file}")
        return 1
    
    setup_yaml()
    
    print(f"\n🔧 Enriching vocabulary: {args.yaml_file.name}")
    print("=" * 60)
    
    stats = enrich_vocabulary(args.yaml_file, dry_run=args.dry_run)
    
    print("\n📊 Statistics:")
    print(f"  Original entries:    {stats['original_count']}")
    print(f"  After deduplication: {stats['deduplicated_count']}")
    print(f"  Lemmas corrected:    {stats['lemmas_corrected']}")
    print(f"  POS corrected:       {stats['pos_corrected']}")
    print(f"  IPA added:           {stats['ipa_added']}")
    
    reduction = stats['original_count'] - stats['deduplicated_count']
    if reduction > 0:
        pct = (reduction / stats['original_count']) * 100
        print(f"\n  🎯 Reduced by {reduction} entries ({pct:.1f}% deduplication)")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
