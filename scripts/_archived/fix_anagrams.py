#!/usr/bin/env python3
"""
Fix anagram letter mismatches in markdown module files.
Reads each anagram activity, extracts the answer, and regenerates correct scrambled letters.
"""

import re
import sys
import random

def scramble_word(word):
    """Scramble a word's letters while keeping spaces and apostrophes intact."""
    # Remove spaces but keep track of them
    clean = word.replace(' ', '')
    # Shuffle the letters
    letters = list(clean)
    random.shuffle(letters)
    # Return space-separated letters
    return ' '.join(letters)

def fix_anagram_in_file(filepath):
    """Fix all anagram activities in a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    modified = False
    in_anagram = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Detect anagram activity header
        if stripped.startswith('## anagram:'):
            in_anagram = True
            i += 1
            continue
        
        # Exit anagram section on next ## header
        if stripped.startswith('## ') and not stripped.startswith('## anagram:'):
            in_anagram = False
            i += 1
            continue
        
        # In anagram section, look for numbered items and their answers
        if in_anagram:
            # Match numbered item like "1. к і т"
            item_match = re.match(r'^(\d+\.)\s+(.+)$', stripped)
            if item_match:
                item_num = item_match.group(1)
                current_scrambled = item_match.group(2)
                leading_spaces = len(line) - len(line.lstrip())
                
                # Look for the answer on next non-empty line
                j = i + 1
                while j < len(lines) and lines[j].strip() == '':
                    j += 1
                
                if j < len(lines):
                    answer_match = re.match(r'^\s*>\s*\[!answer\]\s*(.+)$', lines[j])
                    if answer_match:
                        answer = answer_match.group(1).strip()
                        
                        # Compare letters (ignore case, spaces, apostrophes)
                        scrambled_clean = ''.join(current_scrambled.split()).lower().replace("'", "").replace("'", "")
                        answer_clean = answer.lower().replace(' ', '').replace("'", "").replace("'", "")
                        
                        if sorted(scrambled_clean) != sorted(answer_clean):
                            # Generate correct scrambled version
                            new_scrambled = scramble_word(answer)
                            lines[i] = ' ' * leading_spaces + f"{item_num} {new_scrambled}"
                            modified = True
                            print(f"  Fixed: '{current_scrambled}' -> '{new_scrambled}' (answer: {answer})")
        
        i += 1
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        return True
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fix_anagrams.py <file.md> [file2.md ...]")
        sys.exit(1)
    
    total_fixed = 0
    for filepath in sys.argv[1:]:
        print(f"\nProcessing {filepath}...")
        if fix_anagram_in_file(filepath):
            total_fixed += 1
    
    print(f"\n✅ Fixed anagrams in {total_fixed} files.")

if __name__ == "__main__":
    main()
