#!/usr/bin/env python3
"""
Populate Vocabulary Database (SQLite) from Markdown Modules.

Reads A1-C2 modules, extracts vocabulary tables, and populates:
- lemmas (single words)
- expressions (phrases/idioms)
- module_vocabulary (linkage)
"""

import sqlite3
import re
import os
import sys
import uuid
from pathlib import Path

DB_PATH = "curriculum/l2-uk-en/vocabulary.db"
CURRICULUM_PATH = "curriculum/l2-uk-en"

# Core levels only - exclude tracks (b2-hist, c1-bio, etc.)
CORE_LEVELS = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def determine_type(text, pos):
    """Determine if text is a lemma or expression."""
    text = text.strip()
    if pos and 'phrase' in pos.lower():
        return 'expression'
    if ' ' in text and len(text.split()) > 1:
        # Check for simple compound nouns which might still be lemmas?
        # For now, treat multi-word as expressions unless proven otherwise
        return 'expression'
    return 'lemma'

def extract_vocabulary(filepath: Path):
    """Extract vocabulary items from a module file."""
    items = []
    
    # regex to match module number from filename "01-title.md" or "module-01.md"
    match = re.search(r'(\d+)', filepath.name)
    if not match:
        return items
    module_num = int(match.group(1))
    
    # Determine level from parent directory
    # filepath is like curriculum/l2-uk-en/a1/01-title.md
    level = filepath.parent.name.upper() # 'A1'
    if level not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
        # fallback if file structure is flat
        if module_num <= 34: level = 'A1'
        elif module_num <= 84: level = 'A2' # Adjusted for A2 reset? 
        # Actually user said A2 restarts from 01. So filepath MUST give level.
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find vocabulary section
    # Matches: # Vocabulary OR # Словник ... table ... end
    # Simplified regex to capture the table block
    vocab_match = re.search(
        r'# (?:Vocabulary|Словник)\n\n(.*?)(?=\n#|\Z)', 
        content, 
        re.DOTALL
    )
    
    if not vocab_match:
        return items

    table_block = vocab_match.group(1)
    
    lines = table_block.strip().split('\n')
    header_found = False
    
    for line in lines:
        if not line.strip().startswith('|'):
            continue
        
        parts = [p.strip() for p in line.split('|')]
        # Drop empty start/end from split('|')
        if len(parts) > 2 and parts[0] == '' and parts[-1] == '':
             parts = parts[1:-1]
        elif len(parts) == 0:
            continue
            
        # Check header
        if 'Word' in parts[0] or 'Слово' in parts[0] or '---' in parts[0]:
            continue

        # Data row
        # Schema for A1: | Word | IPA | English | Note | Audio |
        # But some files might vary. We assume:
        # Col 0: Word (UK)
        # Col 1: IPA
        # Col 2: English
        # Col 3: Note
        
        if len(parts) >= 3:
            uk = parts[0]
            ipa = parts[1]
            en = parts[2]
            note = parts[3] if len(parts) > 3 else ''
            
            # Clean up
            uk = uk.strip().replace('`', '') # remove code ticks if any
            
            # Skip if empty
            if not uk or '---' in uk: continue

            item_type = determine_type(uk, '')
            
            items.append({
                'uk': uk,
                'ipa': ipa,
                'en': en,
                'note': note,
                'type': item_type,
                'module': module_num,
                'level': level
            })

    return items

def populate_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    base_path = Path(CURRICULUM_PATH)
    # Recursively find all MD files in a1, a2, etc directories.
    # Exclude 'legacy' and 'gemini' if they are duplicates?
    # User user's strict structure: curriculum/l2-uk-en/a1/*.md
    
    files = list(base_path.glob("**/*.md"))
    # Filter: only core levels, no legacy, filename starts with digit
    files = [f for f in files 
             if "legacy" not in str(f) 
             and f.name[0].isdigit()
             and f.parent.name.lower() in CORE_LEVELS]
    
    print(f"Found {len(files)} module files in core levels ({', '.join(CORE_LEVELS)}).")
    
    # Sort files to process in order (A1 M01 -> C2 ...)
    files.sort(key=lambda x: (x.parent.name, x.name))
    
    count_added = 0
    
    for f in files:
        vocab_items = extract_vocabulary(f)
        for item in vocab_items:
            # Generate ID: v-slug-level-mod
            slug = re.sub(r'[^a-zA-Z0-9]', '-', transliterate(item['uk']))
            uid = f"v-{slug}-{item['level']}-{item['module']}"
            
            # Check if exists to avoid duplicates? 
            # Or always insert ignore?
            # User wants: "first occurrence owns it" behavior?
            # Or just unique constraint on uk?
            
            # DB Schema: 
            # lemmas: id TEXT PRIMARY KEY, uk TEXT UNIQUE NOT NULL
            # expressions: id TEXT PRIMARY KEY, uk TEXT UNIQUE NOT NULL
            
            try:
                if item['type'] == 'lemma':
                    cursor.execute("""
                        INSERT OR IGNORE INTO lemmas (id, uk, ipa, en, notes, level, first_module)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (uid, item['uk'], item['ipa'], item['en'], item['note'], item['level'], item['module']))
                    
                    # If ignored (duplicate), we still need to record that this module USES it?
                    # module_vocabulary (module_num, entry_type, entry_id)
                    # We need the ID of the inserted OR existing item.
                    
                    cursor.execute("SELECT id FROM lemmas WHERE uk = ?", (item['uk'],))
                    res = cursor.fetchone()
                    real_id = res[0]
                    
                    is_new = 1 if real_id == uid else 0 # Simple logic: if IDs match, I inserted it.
                    
                    cursor.execute("""
                        INSERT OR IGNORE INTO module_vocabulary (module_num, entry_type, entry_id, is_new)
                        VALUES (?, 'lemma', ?, ?)
                    """, (item['module'], real_id, is_new))

                else:
                    cursor.execute("""
                        INSERT OR IGNORE INTO expressions (id, uk, ipa, en, notes, level, first_module)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (uid, item['uk'], item['ipa'], item['en'], item['note'], item['level'], item['module']))
                    
                    cursor.execute("SELECT id FROM expressions WHERE uk = ?", (item['uk'],))
                    res = cursor.fetchone()
                    real_id = res[0]
                    
                    is_new = 1 if real_id == uid else 0
                    
                    cursor.execute("""
                        INSERT OR IGNORE INTO module_vocabulary (module_num, entry_type, entry_id, is_new)
                        VALUES (?, 'expression', ?, ?)
                    """, (item['module'], real_id, is_new))
                
                count_added += 1
                
            except Exception as e:
                print(f"Error processing {item['uk']} in {f}: {e}")

    conn.commit()
    print(f"Database populated with {count_added} entries processed.")
    conn.close()

def transliterate(uk):
    # Simple translit for IDs
    mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g', 'д': 'd', 'е': 'e',
        'є': 'ye', 'ж': 'zh', 'з': 'z', 'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'y',
        'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'shch', 'ь': '', 'ю': 'yu', 'я': 'ya'
    }
    res = ""
    for char in uk.lower():
        res += mapping.get(char, char)
    return res

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        sys.exit(1)
    populate_db()
