#!/usr/bin/env python3
"""
Fix resources section placement and formatting in B1 modules.
Ensures:
1. `---` separator before `## Need More Practice?`
2. Resources section with proper header
3. `---` separator before `## Activities` or first activity
"""

import re
from pathlib import Path

def fix_module_resources(filepath: Path) -> bool:
    content = filepath.read_text()
    modified = False
    
    # Find existing resources callout
    resources_match = re.search(r'(\> \[!resources\][^\n]*\n(?:\>[^\n]*\n)*)', content)
    if not resources_match:
        print(f"  No resources found in {filepath.name}")
        return False
    
    resources_block = resources_match.group(1)
    
    # Find first activity (## Activities, ## quiz:, ## match-up:, etc)
    activity_patterns = [
        r'^## Activities\s*$',
        r'^## quiz:',
        r'^## match-up:',
        r'^## fill-in:',
        r'^## true-false:',
        r'^## group-sort:',
        r'^## cloze:',
    ]
    
    first_activity_pos = len(content)
    first_activity_match = None
    
    for pattern in activity_patterns:
        match = re.search(pattern, content, re.MULTILINE)
        if match and match.start() < first_activity_pos:
            first_activity_pos = match.start()
            first_activity_match = match
    
    if not first_activity_match:
        print(f"  No activities found in {filepath.name}")
        return False
    
    # Check if resources are AFTER the first activity
    resources_pos = resources_match.start()
    if resources_pos > first_activity_pos:
        # Need to move resources before activities
        print(f"  Moving resources in {filepath.name}")
        
        # Remove the resources and any surrounding NMP header
        temp_content = content[:resources_match.start()] + content[resources_match.end():]
        temp_content = re.sub(r'\n## Need More Practice\?\s*\n', '\n', temp_content)
        
        # Re-find the first activity position
        for pattern in activity_patterns:
            match = re.search(pattern, temp_content, re.MULTILINE)
            if match:
                first_activity_pos = match.start()
                first_activity_match = match
                break
        
        # Insert the proper section before the activity
        proper_section = f"\n---\n\n## Need More Practice?\n\n{resources_block}\n---\n\n"
        content = temp_content[:first_activity_pos] + proper_section + temp_content[first_activity_pos:]
        modified = True
    else:
        # Resources are in the right place, just check formatting
        # Look for proper header and separators
        before_resources = content[:resources_pos]
        
        # Check for ## Need More Practice? before resources
        if "## Need More Practice?" not in before_resources[-200:]:
            print(f"  Missing header in {filepath.name}")
            # Add the header before resources
            content = content[:resources_pos] + "## Need More Practice?\n\n" + resources_block + "\n" + content[resources_match.end():]
            modified = True
        
        # Check for --- before Need More Practice
        nmp_match = re.search(r'^## Need More Practice\?', content, re.MULTILINE)
        if nmp_match:
            before_nmp = content[max(0, nmp_match.start()-10):nmp_match.start()]
            if "---" not in before_nmp:
                content = content[:nmp_match.start()] + "---\n\n" + content[nmp_match.start():]
                modified = True
    
    if modified:
        filepath.write_text(content)
        return True
    
    return False

def main():
    b1_dir = Path("curriculum/l2-uk-en/b1")
    
    modules = sorted(b1_dir.glob("*.md"))
    fixed = 0
    
    for module in modules:
        if fix_module_resources(module):
            fixed += 1
    
    print(f"\n✅ Fixed: {fixed} modules")

if __name__ == "__main__":
    main()
