#!/usr/bin/env python3
"""
Remove Activity Hints (e.g., [Hint: ...]) from curriculum modules.
Restricted to the Activities/Вправи section to avoid accidental deletion in instructional prose.
"""

import re
import sys
import os

def remove_hints(filepath):
    """Remove hint patterns from the Activities section of a markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into parts: frontmatter, pre-activities, and activities
    # Use the same logic as cleaners.py but keep both parts
    activities_pattern = re.compile(r'^#{1,2}\s+(Activities|Вправи|Exercises)', re.MULTILINE | re.IGNORECASE)
    match = activities_pattern.search(content)

    if not match:
        # print(f"  ℹ️ No Activities section found in {os.path.basename(filepath)}")
        return False

    pre_activities = content[:match.start()]
    activities_section = content[match.start():]

    # Pattern 1: [Hint: ...]
    # Pattern 2: (Hint: ...)
    # Pattern 3: Standalone Hint: ... (often at end of line or in square brackets)
    
    modified_activities = activities_section
    
    # Remove [Hint: ...] including the brackets and any leading space
    modified_activities = re.sub(r'\s*\[Hint:.*?\]', '', modified_activities, flags=re.IGNORECASE)
    
    # Remove (Hint: ...) including the parentheses and any leading space
    modified_activities = re.sub(r'\s*\(Hint:.*?(\)|$)', '', modified_activities, flags=re.IGNORECASE)
    
    # Remove stand-alone "Hint: ..." until end of line, but only if preceded by space or bracket
    # This is to avoid matching words that contain "hint" (though rare in UK/EN context)
    modified_activities = re.sub(r'(?<=\s)Hint:.*$', '', modified_activities, flags=re.MULTILINE | re.IGNORECASE)

    if modified_activities != activities_section:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(pre_activities + modified_activities)
        print(f"  ✅ Removed hints from {os.path.basename(filepath)}")
        return True
    
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/fix_hints.py <file.md> [file2.md ...]")
        sys.exit(1)
    
    total_fixed = 0
    for filepath in sys.argv[1:]:
        if os.path.isfile(filepath):
            if remove_hints(filepath):
                total_fixed += 1
    
    if total_fixed > 0:
        print(f"\n✅ Successfully removed hints from {total_fixed} file(s).")
    else:
        print("\nℹ️ No hints found to remove in the specified file(s).")

if __name__ == "__main__":
    main()
