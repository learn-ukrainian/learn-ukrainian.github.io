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
    c.execute("DROP TABLE IF EXISTS vocabulary")
    c.execute("""
        CREATE TABLE vocabulary (
            lemma TEXT PRIMARY KEY,
            first_module TEXT,
            pos TEXT,
            gender TEXT
        )
    """)
    conn.commit()
    return conn

def get_modules(limit_count=None):
    # Get A1 modules 01..limit
    a1_path = CURRICULUM_PATH / "a1"
    files = sorted(list(a1_path.glob("[0-9]*.md")))
    
    # Sort by number
    files.sort(key=lambda x: int(x.name.split('-')[0]))
    
    if limit_count:
        files = files[:limit_count]
    
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
            if any(s in header_title for s in SKIP_SECTIONS):
                skip_mode = True
            elif skip_mode:
                 skip_mode = False
        
        if not skip_mode:
            # Remove Table Headers
            if '| Word |' in line or '| Слово |' in line or '|---' in line:
                continue
            cleaned_lines.append(line)
            
    content = '\n'.join(cleaned_lines)
    
    # Remove YAML frontmatter
    content = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)
    
    # Remove markdown links
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
    
    # Remove bold/italic
    content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
    content = re.sub(r'\*([^*]+)\*', r'\1', content)
    
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

def process_modules(limit_count):
    # Init Stanza
    nlp = stanza.Pipeline('uk', processors='tokenize,mwt,pos,lemma', verbose=False, use_gpu=False)
    
    conn = init_db()
    cursor = conn.cursor()
    
    modules = get_modules(limit_count)
    seen_lemmas = set()
    
    for mod_file in modules:
        mod_id = mod_file.stem
        # Extract module number from filename "01-..."
        try:
            mod_num = int(mod_id.split('-')[0])
        except:
            mod_num = 0
            
        print(f"Processing {mod_id} (M{mod_num})...")
        
        raw_text = mod_file.read_text(encoding='utf-8')
        text = clean_content(raw_text)
        
        doc = nlp(text)
        
        new_words = []
        
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
                    # M01 & M02: Ignore ALL single letters (Teaching alphabet)
                    if mod_num <= 2:
                        continue
                    # M03+: Only allow valid words
                    if lemma not in VALID_SINGLE_LETTERS:
                        continue
                
                # Check seen
                if lemma not in seen_lemmas:
                    seen_lemmas.add(lemma)
                    
                    pos = pos_map(word.upos)
                    gender = infer_gender(word.feats)
                    
                    cursor.execute("INSERT INTO vocabulary (lemma, first_module, pos, gender) VALUES (?, ?, ?, ?)",
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
            
            final_content = content + "\n\n" + table_str + "\n"
            
            count = len(new_words)
            if 'vocab_count:' in final_content:
                final_content = re.sub(r'vocab_count: \d+', f'vocab_count: {count}', final_content)
            
            mod_file.write_text(final_content, encoding='utf-8')
            print(f"  -> Added {count} new words.")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit-modules', type=int, default=34)
    args = parser.parse_args()
    
    process_modules(args.limit_modules)
