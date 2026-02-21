#!/usr/bin/env python3
"""
Global fix for ASCII quotes in Ukrainian text.

Replaces ASCII double quotes " with Ukrainian angular quotes «» 
in all activity YAML files to prevent JSON parsing errors in MDX.

This addresses the typography rule: Ukrainian content should use «» not "".
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ACTIVITIES_DIRS = [
    PROJECT_ROOT / 'curriculum' / 'l2-uk-en' / level / 'activities'
    for level in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit']
]

def fix_quotes_in_file(file_path: Path) -> int:
    """
    Fix ASCII quotes around Ukrainian text in a YAML file.
    
    Returns number of replacements made.
    """
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    
    # Pattern 1: Quotes around Ukrainian words/phrases (most common)
    # Matches: "слово", "кілька слів", "речення з розділовими знаками, тощо"
    content = re.sub(
        r'"([а-яА-ЯіїєґІЇЄҐ][^"]*?)"',
        r'«\1»',
        content
    )
    
    # Pattern 2: Quotes with apostrophes inside (like "загальнослов'янській")
    # Already handled by pattern 1, but keeping for clarity
    
    # Pattern 3: Quotes with mixed content (Ukrainian + punctuation)
    # Already handled by pattern 1
    
    # Count changes
    changes = content.count('«') - original_content.count('«')
    
    if changes > 0:
        file_path.write_text(content, encoding='utf-8')
    
    return changes


def main():
    print("🔄 Fixing ASCII quotes in all activity files\n")
    
    total_files = 0
    total_changes = 0
    files_changed = 0
    
    for activities_dir in ACTIVITIES_DIRS:
        if not activities_dir.exists():
            continue
        
        level = activities_dir.parent.name
        yaml_files = list(activities_dir.glob('*.yaml'))
        
        level_changes = 0
        level_files_changed = 0
        
        for yaml_file in yaml_files:
            changes = fix_quotes_in_file(yaml_file)
            total_files += 1
            
            if changes > 0:
                total_changes += changes
                files_changed += 1
                level_changes += changes
                level_files_changed += 1
        
        if level_files_changed > 0:
            print(f"  {level.upper()}: {level_files_changed} files, {level_changes} replacements")
    
    print(f"\n✅ Complete!")
    print(f"   Files processed: {total_files}")
    print(f"   Files changed: {files_changed}")
    print(f"   Total replacements: {total_changes}")
    
    if total_changes > 0:
        print(f"\n⚠️  Recommendation: Regenerate all MDX files")
        print(f"   Run: .venv/bin/python scripts/generate_mdx.py l2-uk-en")


if __name__ == '__main__':
    main()
