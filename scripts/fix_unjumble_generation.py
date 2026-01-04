#!/usr/bin/env python3
"""Fix unjumble generation to handle both YAML formats.

The YAML activities have TWO formats for unjumble/anagram activities:
1. words: [array] - for unjumble (reorder words into sentence)
2. scrambled: "string" - for anagram (unscramble letters)

The generation code only handles 'scrambled', causing empty jumbled fields
for all word-based unjumble activities (303 affected).

This script patches scripts/generate_mdx.py to handle both formats.
"""

import re
from pathlib import Path


def main():
    script_path = Path('scripts/generate_mdx.py')
    
    if not script_path.exists():
        print(f"❌ {script_path} not found")
        return 1
    
    content = script_path.read_text(encoding='utf-8')
    
    # Find the buggy line
    old_pattern = r'"jumbled":\s*escape_jsx\(item\.get\(\'scrambled\',\s*\'\'\)\),'
    
    if not re.search(old_pattern, content):
        print("❌ Could not find target pattern in generate_mdx.py")
        print("   Expected: \"jumbled\": escape_jsx(item.get('scrambled', '')),")
        return 1
    
    # Replace with version that handles both formats
    new_code = '''# Handle both YAML formats
            # - words: [array] for unjumble (reorder words)
            # - scrambled: "string" for anagram (unscramble letters)
            jumbled = ''
            if 'words' in item:
                jumbled = ' / '.join(item['words'])
            elif 'scrambled' in item:
                jumbled = item['scrambled']
            
            "jumbled": escape_jsx(jumbled),'''
    
    # Replace the line
    fixed_content = re.sub(
        r'(\s+)"jumbled":\s*escape_jsx\(item\.get\(\'scrambled\',\s*\'\'\)\),',
        new_code,
        content,
        count=1
    )
    
    if fixed_content == content:
        print("❌ Replacement failed - content unchanged")
        return 1
    
    # Write back
    script_path.write_text(fixed_content, encoding='utf-8')
    
    print("✅ Fixed scripts/generate_mdx.py")
    print()
    print("Changes made:")
    print("  - Line 355: Now handles 'words' array format")
    print("  - Joins words with ' / ' separator")
    print("  - Falls back to 'scrambled' for anagram activities")
    print()
    print("Affected activities:")
    print("  - 303 unjumble activities (words format)")
    print("  - 2114 anagram activities (scrambled format)")
    print()
    print("Next steps:")
    print("  1. Regenerate MDX: npm run generate l2-uk-en")
    print("  2. Check output: docusaurus/docs/a1/module-26.mdx")
    print("  3. Test rendering: http://localhost:3000/docs/a1/module-26")
    
    return 0


if __name__ == '__main__':
    exit(main())
