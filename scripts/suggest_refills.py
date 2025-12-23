import re
import os
import sqlite3
from pathlib import Path

DB_PATH = "curriculum/l2-uk-en/vocabulary.db"

def get_master_vocab():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT uk FROM lemmas")
    lemmas = {row[0].lower() for row in cursor.fetchall()}
    cursor.execute("SELECT uk FROM expressions")
    exprs = {row[0].lower() for row in cursor.fetchall()}
    conn.close()
    return lemmas.union(exprs)

def suggest_refills(filepath: Path, master_vocab: set):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract all Ukrainian words from content (excluding YAML and Vocab section)
    # Just look at sections before # Vocabulary
    body = content.split('# Vocabulary')[0]
    
    # Find all Cyrillic words
    words = re.findall(r'[А-ЯІЇЄҐа-яіїєґ]{4,}', body) # 4+ chars to avoid small particles
    words = {w.lower() for w in words}
    
    # Filter out words already in DB
    candidates = [w for w in words if w not in master_vocab]
    
    return sorted(candidates)

def analyze_starvation(curriculum_root: str):
    master_vocab = get_master_vocab()
    base_path = Path(curriculum_root)
    
    levels = {
        "a1": 20,
        "a2": 25
    }
    
    for level, target in levels.items():
        print(f"\n=== Starvation Report: {level.upper()} (Target: {target}) ===")
        level_path = base_path / level
        files = sorted(level_path.glob("*.md"))
        
        for f in files:
            if not f.name[0].isdigit(): continue
            
            # Current count
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            
            vocab_section = re.search(r'# Vocabulary\n\n(.*?)(?=\n#|\Z)', content, re.DOTALL)
            if not vocab_section: continue
            
            rows = [line for line in vocab_section.group(1).split('\n') if line.strip().startswith('|') and '---' not in line and 'Word' not in line]
            current_count = len(rows)
            
            if current_count < target:
                gap = target - current_count
                candidates = suggest_refills(f, master_vocab)
                print(f"  {f.name}: {current_count}/{target} (Need {gap})")
                if candidates:
                    print(f"    Suggested from content: {', '.join(candidates[:15])}...")
                else:
                    print(f"    NO CANDIDATES FOUND IN CONTENT.")

if __name__ == "__main__":
    analyze_starvation("curriculum/l2-uk-en")
