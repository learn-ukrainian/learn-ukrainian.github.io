import sqlite3
import re
import os
from pathlib import Path
from collections import defaultdict

DB_PATH = "curriculum/l2-uk-en/vocabulary.db"

def extract_vocabulary(filepath: Path):
    """Extract vocabulary items from a module file."""
    items = []
    
    match = re.search(r'(\d+)', filepath.name)
    if not match:
        return items
    module_num = int(match.group(1))
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    vocab_match = re.search(
        r'# Vocabulary\n\n(.*?)(?=\n#|\Z)', 
        content, 
        re.DOTALL
    )
    
    if not vocab_match:
        return items

    table_block = vocab_match.group(1)
    
    for line in table_block.strip().split('\n'):
        if not line.strip().startswith('|'):
            continue
        
        parts = [p.strip() for p in line.split('|')]
        if len(parts) > 2 and parts[0] == '' and parts[-1] == '':
             parts = parts[1:-1]
            
        if not parts or 'Word' in parts[0] or '---' in parts[0]:
            continue

        uk = parts[0].strip().replace('`', '')
        if uk and re.search(r'[А-ЯІЇЄҐа-яіїєґ]', uk):
            items.append({'uk': uk})

    return items

def analyze_all():
    # --- A1 Analysis ---
    a1_path = Path("curriculum/l2-uk-en/a1")
    a1_files = sorted(a1_path.glob("*.md"))
    
    a1_first_seen = {} # word -> mod_num
    a1_duplicate_count = 0
    a1_new_count = 0
    a1_stats = defaultdict(lambda: {"repeats": 0, "new_words": 0, "total": 0})
    
    for f in a1_files:
        items = extract_vocabulary(f)
        try:
            mod_num = int(re.search(r'(\d+)', f.name).group(1))
        except: continue
        
        for item in items:
            word = item['uk']
            a1_stats[mod_num]["total"] += 1
            if word in a1_first_seen:
                a1_duplicate_count += 1
                a1_stats[mod_num]["repeats"] += 1
            else:
                a1_first_seen[word] = mod_num
                a1_new_count += 1
                a1_stats[mod_num]["new_words"] += 1

    print("=" * 40)
    print("A1 SELF-DUPLICATION ANALYSIS")
    print("=" * 40)
    print(f"Total A1 entries: {sum(s['total'] for s in a1_stats.values())}")
    print(f"Repeats within A1: {a1_duplicate_count}")
    print(f"Unique words in A1: {a1_new_count}")
    print("\nPer-module stats (A1):")
    print("| Mod | Total | New | Rep |")
    print("|-----|-------|-----|-----|")
    for mod in sorted(a1_stats.keys()):
        s = a1_stats[mod]
        print(f"| {mod:02d} | {s['total']:5d} | {s['new_words']:3d} | {s['repeats']:3d} |")
    
    # --- A2 Analysis ---
    a1_words = set(a1_first_seen.keys())
    
    a2_path = Path("curriculum/l2-uk-en/a2")
    module_files = sorted(a2_path.glob("*.md"))
    
    a2_first_seen = {} # word -> mod_num
    duplicate_count_a1 = 0
    duplicate_count_a2 = 0
    new_words_count = 0
    modules_stats = defaultdict(lambda: {"a1_repeats": 0, "a2_repeats": 0, "new_words": 0, "total": 0})
    
    for f in module_files:
        items = extract_vocabulary(f)
        try:
            mod_num = int(re.search(r'(\d+)', f.name).group(1))
        except: continue
        
        for item in items:
            word = item['uk']
            modules_stats[mod_num]["total"] += 1
            
            if word in a1_words:
                duplicate_count_a1 += 1
                modules_stats[mod_num]["a1_repeats"] += 1
            elif word in a2_first_seen:
                duplicate_count_a2 += 1
                modules_stats[mod_num]["a2_repeats"] += 1
            else:
                a2_first_seen[word] = mod_num
                new_words_count += 1
                modules_stats[mod_num]["new_words"] += 1
            
    print("\n" + "=" * 40)
    print("A2 INHERITANCE ANALYSIS")
    print("=" * 40)
    print(f"Total A2 entries analyzed: {sum(s['total'] for s in modules_stats.values())}")
    print(f"Repeats from A1: {duplicate_count_a1}")
    print(f"Repeats within A2: {duplicate_count_a2}")
    print(f"Unique new words in A2: {new_words_count}")
    print("\nPer-module stats (A2):")
    print("| Mod | Total | New | A1 Rep | A2 Rep |")
    print("|-----|-------|-----|--------|--------|")
    for mod in sorted(modules_stats.keys()):
        s = modules_stats[mod]
        print(f"| {mod:02d} | {s['total']:5d} | {s['new_words']:3d} | {s['a1_repeats']:6d} | {s['a2_repeats']:6d} |")

if __name__ == "__main__":
    analyze_all()
