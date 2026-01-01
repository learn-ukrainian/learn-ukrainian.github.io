#!/usr/bin/env python3
"""
Validate Vocabulary YAML
------------------------
Validates vocabulary files against the specific schema.
- Unique lemmas
- Mandatory fields (ipa, translation)
- Valid Enums (POS, Gender)
"""

import argparse
import sys
import yaml
from pathlib import Path

VALID_POS = {'noun', 'verb', 'adj', 'adv', 'pron', 'prep', 'conj', 'part', 'intj', 'num', 'phrase', 'propn', 'other', 'suffix', 'prefix'}
VALID_GENDER = {'m', 'f', 'n', 'pl', '-', ''}

def validate_file(file_path):
    print(f"Validating {file_path.name}...")
    try:
        data = yaml.safe_load(file_path.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"  ❌ YAML Error: {e}")
        return False
        
    errors = []
    lemmas = set()
    
    if 'items' not in data or not isinstance(data['items'], list):
        print("  ❌ Missing 'items' list")
        return False
        
    for i, item in enumerate(data['items']):
        lemma = item.get('lemma')
        if not lemma:
            errors.append(f"Item #{i}: Missing 'lemma'")
            continue
            
        if lemma in lemmas:
            errors.append(f"Duplicate lemma: '{lemma}'")
        lemmas.add(lemma)
        
        # Mandatory Enrichment Check
        if not item.get('ipa'):
            errors.append(f"'{lemma}': Missing IPA")
        if not item.get('translation'):
            errors.append(f"'{lemma}': Missing Translation")
            
        # Enum Checks
        pos = item.get('pos', 'other')
        if pos not in VALID_POS:
            errors.append(f"'{lemma}': Invalid POS '{pos}'")
            
        if pos == 'noun':
            gen = item.get('gender', '')
            if not gen:
                errors.append(f"'{lemma}' (noun): Missing Gender")
            elif gen not in VALID_GENDER:
                errors.append(f"'{lemma}': Invalid Gender '{gen}'")
    
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
        return False
        
    print(f"  ✅ PASS ({len(lemmas)} items)")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+', type=Path)
    args = parser.parse_args()
    
    failed = False
    for f in args.files:
        if not validate_file(f):
            failed = True
            
    if failed:
        sys.exit(1)
