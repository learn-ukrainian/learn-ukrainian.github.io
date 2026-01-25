#!/usr/bin/env python3
import os
import re
from pathlib import Path

def count_words(text):
    return len(re.findall(r'[а-яіїєґА-ЯІЇЄҐA-Za-z]+', text))

def scan_module(path):
    content = path.read_text(encoding='utf-8')
    
    # Detect Essay section
    essay_pattern = re.compile(r'#+ (Есе|Порівняльний аналіз).*?(?=#+ |$)', re.DOTALL | re.IGNORECASE)
    match = essay_pattern.search(content)
    
    has_essay = bool(match)
    essay_text = match.group(0) if match else ""
    essay_word_count = count_words(essay_text)
    
    # Detect Frontmatter
    has_frontmatter = content.startswith('---')
    
    total_words = count_words(content)
    clean_prose_words = total_words - essay_word_count
    
    return {
        'slug': path.stem,
        'has_essay': has_essay,
        'has_frontmatter': has_frontmatter,
        'total_words': total_words,
        'clean_prose_words': clean_prose_words,
        'shortfall': max(0, 4000 - clean_prose_words)
    }

def main():
    base_dir = Path('curriculum/l2-uk-en/b2-hist')
    modules = sorted([f for f in base_dir.glob('*.md') if f.is_file()])
    
    print(f"{'Module':<35} | {'Essay?':<6} | {'Front?':<6} | {'Prose':<6} | {'Short':<6}")
    print("-" * 75)
    
    rebuild_count = 0
    for m in modules:
        res = scan_module(m)
        essay_str = "YES" if res['has_essay'] else "no"
        front_str = "YES" if res['has_frontmatter'] else "no"
        
        status = ""
        if res['shortfall'] > 0:
            status = "!!"
            rebuild_count += 1
            
        print(f"{res['slug']:<35} | {essay_str:<6} | {front_str:<6} | {res['clean_prose_words']:<6} | {res['shortfall']:<6} {status}")

    print("-" * 75)
    print(f"Total modules: {len(modules)}")
    print(f"Modules needing content expansion (shortfall > 0): {rebuild_count}")

if __name__ == '__main__':
    main()
