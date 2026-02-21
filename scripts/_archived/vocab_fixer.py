import re
import os
import sys
from pathlib import Path
from collections import Counter

def cleanup_module(filepath: Path, seen_vocab: set):
    """Remove duplicate vocabulary from a module."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    in_vocab_table = False
    deleted_count = 0
    kept_count = 0
    
    # Regex to detect table row
    table_row_re = re.compile(r'^\s*\|\s*([^|]+)\s*\|')

    for line in lines:
        if line.strip().startswith('# Vocabulary'):
            in_vocab_table = True
            new_lines.append(line)
            continue
        
        if in_vocab_table:
            # Check for end of section (header or theme change)
            if line.strip().startswith('#') and not line.strip().startswith('# Vocabulary'):
                in_vocab_table = False
                new_lines.append(line)
                continue
            
            # Check for table row
            match = table_row_re.search(line)
            if match:
                word = match.group(1).strip().replace('`', '')
                # Skip header/sep
                if 'Word' in word or 'Слово' in word or '---' in word:
                    new_lines.append(line)
                    continue
                
                # Check if Ukrainian word (Cyrillic)
                if re.search(r'[А-ЯІЇЄҐа-яіїєґ]', word):
                    if word in seen_vocab:
                        deleted_count += 1
                        continue # Skip this line
                    else:
                        seen_vocab.add(word)
                        kept_count += 1
                        new_lines.append(line)
                        continue
        
        new_lines.append(line)

    if deleted_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
    return kept_count, deleted_count

def run_cleanup(curriculum_path: str):
    base_path = Path(curriculum_path)
    seen_vocab = set()
    
    # Process A1
    print("\nProcessing A1...")
    a1_path = base_path / "a1"
    a1_files = sorted(a1_path.glob("*.md"))
    for f in a1_files:
        if not f.name[0].isdigit(): continue
        kept, deleted = cleanup_module(f, seen_vocab)
        if deleted > 0:
            print(f"  {f.name}: Kept {kept}, Removed {deleted}")

    # Process A2
    print("\nProcessing A2...")
    a2_path = base_path / "a2"
    a2_files = sorted(a2_path.glob("*.md"))
    for f in a2_files:
        if not f.name[0].isdigit(): continue
        kept, deleted = cleanup_module(f, seen_vocab)
        if deleted > 0:
            print(f"  {f.name}: Kept {kept}, Removed {deleted}")

if __name__ == "__main__":
    run_cleanup("curriculum/l2-uk-en")
    print("\nCleanup Complete.")
