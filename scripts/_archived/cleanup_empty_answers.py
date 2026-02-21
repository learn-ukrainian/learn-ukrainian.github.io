import os
import re
from pathlib import Path

def cleanup_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    in_mark_the_words = False
    modified = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check if we are entering a mark-the-words block
        if '- type: mark-the-words' in line:
            in_mark_the_words = True
        elif '- type:' in line:
            in_mark_the_words = False
            
        if in_mark_the_words:
            # Check for answers: [] on one line
            if re.match(r'^\s*answers:\s*\[\]\s*(#.*)?$', line):
                modified = True
                i += 1
                continue
            
            # Check for answers: \n [] (multiline empty list)
            if re.match(r'^\s*answers:\s*$', line):
                # Peek ahead
                if i + 1 < len(lines):
                    next_line = lines[i+1]
                    if re.match(r'^\s*\[\]\s*$', next_line):
                        modified = True
                        i += 2 # Skip both lines
                        continue
                        
        new_lines.append(line)
        i += 1

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return False

def main():
    base_dir = Path('curriculum/l2-uk-en')
    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit']
    
    total_cleaned = 0
    for level in levels:
        act_dir = base_dir / level / 'activities'
        if not act_dir.exists():
            continue
            
        print(f"Cleaning Level {level.upper()}...")
        for yaml_file in act_dir.glob('*.yaml'):
            if cleanup_file(yaml_file):
                print(f"  Cleaned: {yaml_file.name}")
                total_cleaned += 1
                
    print(f"\nTotal files cleaned: {total_cleaned}")

if __name__ == "__main__":
    main()
