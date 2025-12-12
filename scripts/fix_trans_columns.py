#!/usr/bin/env python3
"""
Remove transliteration columns from vocabulary tables in A2 M21+ modules.
For A2 level, M21+ should have transliteration: none (no transliteration column).
"""

import re
import sys
import os

def remove_trans_column(filepath):
    """Remove transliteration column from tables in the file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get module number from filename
    match = re.search(r'module-(\d+)\.md', filepath)
    if not match:
        return False
    
    module_num = int(match.group(1))
    
    # Only process M21+ for A2
    if module_num < 21:
        return False
    
    lines = content.split('\n')
    modified = False
    
    for i, line in enumerate(lines):
        # Match table lines with transliteration column (4th column typically)
        # Pattern: | Word | IPA | English | Trans |
        # or: | Word | Trans | IPA | English |
        
        # Look for lines with Transliteration header
        if re.match(r'\|\s*(Transliteration|Trans\.?)\s*\|', line, re.IGNORECASE):
            # This is likely a header - skip, but flag for column removal
            pass
        
        # Match table rows - remove 4th column if it looks like transliteration
        # Typically format: | Ukrainian | IPA | English | Trans |
        parts = line.split('|')
        if len(parts) >= 5:  # Has at least 4 columns + borders
            # Check if 4th real column looks like transliteration (Latin text)
            col4 = parts[4].strip() if len(parts) > 4 else ''
            
            # Detect Latin transliteration column
            if col4 and re.match(r'^[a-zA-Zʹ\'\-\s]+$', col4) and not re.match(r'^[\d\s\-]+$', col4):
                # Remove the 4th column
                new_parts = parts[:4] + parts[5:] if len(parts) > 5 else parts[:4] + ['']
                new_line = '|'.join(new_parts)
                if new_line != line:
                    lines[i] = new_line
                    modified = True
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"  ✅ Removed transliteration columns from {os.path.basename(filepath)}")
        return True
    
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fix_trans_columns.py <file.md> [file2.md ...]")
        sys.exit(1)
    
    total_fixed = 0
    for filepath in sys.argv[1:]:
        if remove_trans_column(filepath):
            total_fixed += 1
    
    print(f"\n✅ Fixed transliteration columns in {total_fixed} files.")

if __name__ == "__main__":
    main()
