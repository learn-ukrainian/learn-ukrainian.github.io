import glob
from pathlib import Path

files = sorted(glob.glob("curriculum/l2-uk-en/b2-hist/meta/*.yaml"))

def remove_summary(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    skip = 0
    removed = False
    
    for i, line in enumerate(lines):
        if skip > 0:
            skip -= 1
            continue
            
        if "- section: Підсумок" in line or "- section: 'Підсумок'" in line or '- section: "Підсумок"' in line:
            # Found it. We need to skip this line and subsequent indented lines belonging to it.
            # Usually 'words:' and 'points:'.
            # Let's peek ahead.
            removed = True
            print(f"Removing Підсумок from {Path(file_path).name}")
            
            # Simple heuristic: skip lines until next list item (starting with -) or end of section
            # But we are in a list. Next item starts with "- section:".
            # Or end of 'content_outline'.
            
            # Look ahead to decide how many lines to skip
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                stripped = next_line.strip()
                
                # If next line starts with '-', it's next item. Stop skipping.
                if stripped.startswith("- "):
                    break
                
                # If next line is unindented (start of new root key), stop.
                if next_line and not next_line.startswith(" ") and ":" in next_line:
                    break
                
                # Otherwise, it's a property of this item. Skip it.
                j += 1
            
            skip = j - i - 1 # -1 because loop increments
            continue
            
        new_lines.append(line)
        
    if removed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    else:
        print(f"Підсумок not found in {Path(file_path).name}")

for f in files:
    remove_summary(f)
