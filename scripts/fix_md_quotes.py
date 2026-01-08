#!/usr/bin/env python3
"""
Global fix for ASCII quotes in Ukrainian text (Markdown files).

Replaces ASCII double quotes " with Ukrainian angular quotes «» 
in all markdown content files.
"""

import re
import sys
from pathlib import Path

def fix_quotes_in_file(file_path: Path) -> int:
    """
    Fix ASCII quotes around Ukrainian text in a Markdown file.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        print(f"⚠️  Skipping binary/encoding error: {file_path}")
        return 0
        
    original_content = content
    
    # Simple strategy: Replace "text" with «text»
    # We want to avoid replacing quotes inside HTML tags like <img src="...">
    # Or frontmatter keys... but we shouldn't have frontmatter ideally.
    
    # Regex to match quotes that contain at least one Cyrillic character
    # This avoids replacing code attributes or English-only quotes unless intended
    # Matches: "Слово" -> «Слово»
    # Negative lookbehind to avoid escaping \"
    
    # Pattern: " (content with at least one cyrillic char) "
    # We use non-greedy matching .*?
    
    new_content = re.sub(
        r'"([^"*?[а-яА-ЯіїєґІЇЄҐ][^"]*?)"',
        r'«\1»',
        content
    )
    
    if new_content != content:
        # Calculate replacements roughly
        replacements = (len(new_content) - len(content)) # length might change? No, " and « are 1 char? No, « is unicode.
        # Just check if changed.
        file_path.write_text(new_content, encoding='utf-8')
        return 1
    
    return 0

def main():
    args = sys.argv[1:]
    
    if args:
        files = [Path(p) for p in args]
    else:
        # Default to B2 directory for now as per task context
        root = Path("curriculum/l2-uk-en/b2")
        files = list(root.glob("*.md"))

    print(f"🔄 Processing {len(files)} files...")
    
    fixed_count = 0
    for f in files:
        if f.is_file() and f.suffix == '.md':
            if fix_quotes_in_file(f):
                print(f"  Fixed: {f.name}")
                fixed_count += 1
                
    print(f"✅ Fixed {fixed_count} files.")

if __name__ == '__main__':
    main()
