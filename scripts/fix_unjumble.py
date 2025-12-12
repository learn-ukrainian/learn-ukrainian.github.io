#!/usr/bin/env python3
"""
Fix unjumble word mismatches in markdown module files.
Reads each unjumble activity, extracts the answer, and regenerates shuffled word order.
"""

import re
import sys
import random

def shuffle_words(sentence):
    """Shuffle words in a sentence while preserving each word."""
    # Remove punctuation for shuffling, preserve sentence structure
    clean = re.sub(r'[.,!?;:]', '', sentence)
    words = clean.split()
    random.shuffle(words)
    return ' / '.join(words)

def fix_unjumble_in_file(filepath):
    """Fix all unjumble activities in a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    modified = False
    in_unjumble = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Detect unjumble activity header
        if stripped.startswith('## unjumble:'):
            in_unjumble = True
            i += 1
            continue
        
        # Exit unjumble section on next ## header
        if stripped.startswith('## ') and not stripped.startswith('## unjumble:'):
            in_unjumble = False
            i += 1
            continue
        
        # In unjumble section, look for numbered items and their answers
        if in_unjumble:
            # Match numbered item like "1. книгу / читаю / Я"
            item_match = re.match(r'^(\d+\.)\s+(.+)$', stripped)
            if item_match:
                item_num = item_match.group(1)
                current_jumbled = item_match.group(2)
                leading_spaces = len(line) - len(line.lstrip())
                
                # Look for the answer on next non-empty line
                j = i + 1
                while j < len(lines) and lines[j].strip() == '':
                    j += 1
                
                if j < len(lines):
                    answer_match = re.match(r'^\s*>\s*\[!answer\]\s*(.+)$', lines[j])
                    if answer_match:
                        answer = answer_match.group(1).strip()
                        
                        # Parse current jumbled words
                        current_clean = re.sub(r'[.,!?;:]', '', current_jumbled).lower()
                        answer_clean = re.sub(r'[.,!?;:]', '', answer).lower()
                        
                        if '/' in current_jumbled:
                            current_words = set(w.strip() for w in current_clean.split('/'))
                        else:
                            current_words = set(current_clean.split())
                        
                        answer_words = set(answer_clean.split())
                        
                        if current_words != answer_words:
                            # Generate correct shuffled version
                            new_jumbled = shuffle_words(answer)
                            lines[i] = ' ' * leading_spaces + f"{item_num} {new_jumbled}"
                            modified = True
                            print(f"  Fixed: '{current_jumbled}' -> '{new_jumbled}' (answer: {answer})")
        
        i += 1
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        return True
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fix_unjumble.py <file.md> [file2.md ...]")
        sys.exit(1)
    
    total_fixed = 0
    for filepath in sys.argv[1:]:
        print(f"\nProcessing {filepath}...")
        if fix_unjumble_in_file(filepath):
            total_fixed += 1
    
    print(f"\n✅ Fixed unjumble in {total_fixed} files.")

if __name__ == "__main__":
    main()
