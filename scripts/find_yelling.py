
import os
import re

def is_yelling(line):
    # Ignore short lines, headers, likely empty lines, or lines with mostly non-letters
    clean_line = line.strip()
    if not clean_line:
        return False
    if clean_line.startswith('#'):
        return False
    if clean_line.startswith('>'): # Ignore blockquotes? Check content maybe.
         # Actually, blockquotes MIGHT be yelling. Let's inspect content.
         pass
    if clean_line.startswith('|') or clean_line.startswith('- ['): # Tables and checkboxes
        return False
    
    # Heuristic: mostly uppercase
    letters = [c for c in clean_line if c.isalpha()]
    if len(letters) < 5: # Ignore short abbreviations
        return False
    
    upper_count = sum(1 for c in letters if c.isupper())
    ratio = upper_count / len(letters)
    
    # If > 70% uppercase, flag it
    return ratio > 0.7

def scan_file(filepath):
    yelling_lines = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if is_yelling(line):
                yelling_lines.append((i + 1, line.strip()))
    return yelling_lines

def main():
    target_dir = os.path.join(os.getcwd(), 'curriculum/l2-uk-en/a1')
    files = sorted([f for f in os.listdir(target_dir) if f.endswith('.md')])
    
    found_any = False
    for filename in files:
        path = os.path.join(target_dir, filename)
        issues = scan_file(path)
        if issues:
            found_any = True
            print(f"File: {filename}")
            for line_num, content in issues:
                print(f"  Line {line_num}: {content}")
            print("-" * 40)

    if not found_any:
        print("No yelling found!")

if __name__ == "__main__":
    main()
