#!/usr/bin/env python3
"""
Simple Vocabulary Rebuild Script
- Strict chronological processing.
- Scans MD content, excluding # Vocabulary section.
- Extracts all Cyrillic words.
- M01-M02: Excludes ALL single-letter words (Alphabet phase).
- M03+: Filters single-letter words against a hardcoded whitelist.
- Enforces First Appearance rule.
"""

import argparse
import re
import sqlite3
import stanza
from pathlib import Path

# Config
DB_PATH = Path("curriculum/l2-uk-en/vocabulary.db")
CURRICULUM_PATH = Path("curriculum/l2-uk-en")
SKIP_SECTIONS = {'Vocabulary', 'Словник', 'Activities', 'Вправи'} 

# Valid single-letter words in Ukrainian (for M03+)
VALID_SINGLE_LETTERS = {'а', 'б', 'в', 'ж', 'з', 'і', 'й', 'о', 'у', 'я', 'є'}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # We should NOT drop the table if we are running simply for one level, 
    # but the current architecture implies a full rebuild order A1 -> A2 -> B1
    # For now, if we are rebuilding, we assume we might want to preserve previous levels
    # BUT, to keep it simple and correct, the user flow is delete ALL -> rebuild ALL.
    # If we rebuild A2, we need A1 to be in the DB to know what is "new".
    # So we should probably NOT drop if the table exists, OR we should assume strict sequential run.
    c.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary (
            lemma TEXT PRIMARY KEY,
            first_module TEXT,
            pos TEXT,
            gender TEXT
        )
    """)
    conn.commit()
    return conn

def get_modules(level):
    level_path = CURRICULUM_PATH / level
    if not level_path.exists():
        print(f"Level directory not found: {level_path}")
        return []

    files = sorted(list(level_path.glob("[0-9]*.md")))
    
    # Sort by number: 01-..., 107-...
    try:
        files.sort(key=lambda x: int(x.name.split('-')[0]))
    except:
        pass # Fallback to name sort
        
    return files

def clean_content(text):
    """
    Remove header sections we don't want.
    Remove markdown syntax.
    """
    lines = text.split('\n')
    cleaned_lines = []
    skip_mode = False
    
    for line in lines:
        if line.lstrip().startswith('#'):
            header_title = line.lstrip('#').strip()
            # Check strictly for the excluded headers
            is_excluded = False
            for s in SKIP_SECTIONS:
                if header_title.lower() == s.lower():
                    is_excluded = True
                    break
            
            if is_excluded:
                skip_mode = True
            elif skip_mode:
                # If we hit another header that ISN'T excluded, stop skipping?
                # Actually, typically Vocabulary/Activities are at the end. 
                # Better safe: if we hit a new header, check if it's excluded.
                # If it's NOT excluded, resume? No, usually Vocab is end.
                # But let's assume if we hit a new header, we re-evaluate.
                skip_mode = False 
                # Re-check this new header
                for s in SKIP_SECTIONS:
                    if header_title.lower() == s.lower():
                        is_excluded = True
                        skip_mode = True
                        break
        
        if not skip_mode:
            # Remove Table Headers
            if '| Word |' in line or '| Слово |' in line or '|---' in line:
                continue
            cleaned_lines.append(line)
            
    content = '\n'.join(cleaned_lines)
    
    # Remove YAML frontmatter
    content = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)
    
    # Remove markdown links [text](url) -> text
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
    
    # Remove bold/italic
    content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
    content = re.sub(r'\*([^*]+)\*', r'\1', content)
    
    # Collapse whitespace
    content = re.sub(r'\s+', ' ', content)
    
    return content

def infer_gender(feats):
    if not feats: return '-'
    if 'Gender=Masc' in feats: return 'ч'
    if 'Gender=Fem' in feats: return 'ж'
    if 'Gender=Neut' in feats: return 'с'
    return '-'

def pos_map(upos):
    m = {'NOUN': 'noun', 'VERB': 'verb', 'ADJ': 'adj', 'ADV': 'adv', 'PRON': 'pron', 'PROPN': 'name'}
    return m.get(upos, 'other')

def process_modules(level):
    # Init Stanza
    try:
        nlp = stanza.Pipeline('uk', processors='tokenize,mwt,pos,lemma', verbose=False, use_gpu=False)
    except Exception as e:
        print(f"Error initializing Stanza: {e}")
        # Try downloading if missing? safely
        stanza.download('uk')
        nlp = stanza.Pipeline('uk', processors='tokenize,mwt,pos,lemma', verbose=False, use_gpu=False)
        
    conn = init_db()
    cursor = conn.cursor()
    
    modules = get_modules(level)
    
    # Load existing lemmas to respect global "first appearance" across levels
    cursor.execute("SELECT lemma FROM vocabulary")
    existing_lemmas = {row[0] for row in cursor.fetchall()}
    
    print(f"Loaded {len(existing_lemmas)} existing lemmas from DB.")
    print(f"Processing {len(modules)} modules for level {level}...")
    
    for mod_file in modules:
        mod_id = mod_file.stem
        try:
            mod_num = int(mod_id.split('-')[0])
        except:
            mod_num = 999
            
        print(f"Processing {mod_id}...")
        
        raw_text = mod_file.read_text(encoding='utf-8')
        text = clean_content(raw_text)
        
        doc = nlp(text)
        
        new_words = []
        local_seen = set()
        
        for sent in doc.sentences:
            for word in sent.words:
                lemma = word.lemma
                if not lemma: continue
                lemma = lemma.lower()
                
                # Filter Cyrillic
                if not re.match(r'^[а-яіїєґ\']+$', lemma):
                    continue
                
                # Single Letter Rules
                if len(lemma) == 1:
                    # M01 & M02 (A1 only): Ignore ALL single letters
                    if level == 'a1' and mod_num <= 2:
                        continue
                    # General rule: Only allow valid words
                    if lemma not in VALID_SINGLE_LETTERS:
                        continue
                
                # Check seen globally and locally
                if lemma not in existing_lemmas and lemma not in local_seen:
                    existing_lemmas.add(lemma)
                    local_seen.add(lemma)
                    
                    pos = pos_map(word.upos)
                    gender = infer_gender(word.feats)
                    
                    # Store in DB
                    cursor.execute("INSERT OR IGNORE INTO vocabulary (lemma, first_module, pos, gender) VALUES (?, ?, ?, ?)",
                                   (lemma, mod_id, pos, gender))
                    
                    if cursor.rowcount > 0:
                        new_words.append({
                            'uk': lemma,
                            'pos': pos,
                            'gender': gender
                        })
                    else:
                        # It was already there (race condition or previous run), so we treat it as seen
                        # and DO NOT add it to this module's vocabulary list
                        pass
        
def clean_db_for_modules(conn, module_ids):
    c = conn.cursor()
    if not module_ids: return
    
    placeholders = ','.join(['?'] * len(module_ids))
    # Delete all words that were first introduced in these modules
    # This effectively "forgets" that these modules claimed any words, allowing re-claiming.
    query = f"DELETE FROM vocabulary WHERE first_module IN ({placeholders})"
    c.execute(query, list(module_ids))
    print(f"Cleared {c.rowcount} entries for {len(module_ids)} modules from DB.")
    conn.commit()

def process_modules(level):
    # Init Stanza
    try:
        nlp = stanza.Pipeline('uk', processors='tokenize,mwt,pos,lemma', verbose=False, use_gpu=False)
    except Exception as e:
        print(f"Error initializing Stanza: {e}")
        stanza.download('uk')
        nlp = stanza.Pipeline('uk', processors='tokenize,mwt,pos,lemma', verbose=False, use_gpu=False)
        
    conn = init_db()
    cursor = conn.cursor()
    
    modules = get_modules(level)
    module_ids = [m.stem for m in modules]
    
    # Clean DB for these modules to allow clean rebuild
    clean_db_for_modules(conn, module_ids)
    
    # Load existing lemmas (after cleanup)
    cursor.execute("SELECT lemma FROM vocabulary")
    existing_lemmas = {row[0] for row in cursor.fetchall()}
    
    print(f"Loaded {len(existing_lemmas)} global lemmas (excluding current level).")
    
    for mod_file in modules:
        mod_id = mod_file.stem
        try:
            mod_num = int(mod_id.split('-')[0])
        except:
            mod_num = 999
            
        print(f"Processing {mod_id}...")
        
        raw_text = mod_file.read_text(encoding='utf-8')
        text = clean_content(raw_text)
        
        doc = nlp(text)
        
        new_words = []
        local_seen = set()
        
        for sent in doc.sentences:
            for word in sent.words:
                lemma = word.lemma
                if not lemma: continue
                lemma = lemma.lower()
                
                # Filter Cyrillic
                if not re.match(r'^[а-яіїєґ\']+$', lemma):
                    continue
                
                # Single Letter Rules
                if len(lemma) == 1:
                    if level == 'a1' and mod_num <= 2:
                        continue
                    if lemma not in VALID_SINGLE_LETTERS:
                        continue
                
                # Check seen globally and locally
                if lemma not in existing_lemmas and lemma not in local_seen:
                    existing_lemmas.add(lemma)
                    local_seen.add(lemma)
                    
                    pos = pos_map(word.upos)
                    gender = infer_gender(word.feats)
                    
                    # Store in DB
                    cursor.execute("INSERT OR IGNORE INTO vocabulary (lemma, first_module, pos, gender) VALUES (?, ?, ?, ?)",
                                   (lemma, mod_id, pos, gender))
                    
                    new_words.append({
                        'uk': lemma,
                        'pos': pos,
                        'gender': gender
                    })
        
        if new_words:
            new_words.sort(key=lambda x: x['uk'])
            
            table = ["# Vocabulary", "", "| Word | IPA | English | POS | Gender | Note |", "| --- | --- | --- | --- | --- | --- |"]
            for w in new_words:
                table.append(f"| {w['uk']} |  |  | {w['pos']} | {w['gender']} |  |")
            
            table_str = "\n".join(table)
            
            content = mod_file.read_text(encoding='utf-8')
            
            if '# Vocabulary' in content:
                content = content.split('# Vocabulary')[0].strip()
            elif '# Словник' in content:
                content = content.split('# Словник')[0].strip()
            
            final_content = content.strip() + "\n\n" + table_str + "\n"
            
            vocab_size = len(new_words)
            
            if 'vocab_count:' in final_content:
                final_content = re.sub(r'vocab_count: \d+', f'vocab_count: {vocab_size}', final_content)
            
            mod_file.write_text(final_content, encoding='utf-8')
            print(f"  -> Added {vocab_size} new words.")
        else:
            print(f"  -> No new words found.")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--level', type=str, required=True, help="Level to rebuild (a1, a2, b1, etc)")
    args = parser.parse_args()
    
    process_modules(args.level)
