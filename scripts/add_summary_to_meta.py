import yaml
import glob
from pathlib import Path

# Target files: B2-HIST 01-15
files = sorted(glob.glob("curriculum/l2-uk-en/b2-hist/meta/*.yaml"))

def update_outline(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        # Read as lines to preserve comments/order better than full yaml dump
        lines = f.readlines()
    
    content = "".join(lines)
    
    # Simple check if Підсумок is already in the outline
    if "- section: Підсумок" in content or "- section: 'Підсумок'" in content:
        print(f"Skipping {Path(file_path).name} (already has Підсумок)")
        return

    # Load data to find insertion point logic conceptually, 
    # but we will perform text insertion to preserve formatting if possible.
    # Actually, simpler to just load, modify object, and dump with safe settings.
    # But PyYAML often messes up flow style.
    
    # Let's try text processing. 
    # We want to insert 'Підсумок' before 'Потрібно більше практики?' or at end of outline. 
    
    # Find the line with "section: Потрібно більше практики?"
    insert_idx = -1
    for i, line in enumerate(lines):
        if "section: Потрібно більше практики?" in line or "section: 'Потрібно більше практики?'" in line:
            # We want to insert *before* this item.
            # But we need to account for the list item dash.
            insert_idx = i
            break
            
    if insert_idx != -1:
        # Construct the YAML list item
        new_item = "- section: Підсумок\n  words: 150\n  points: []\n"
        lines.insert(insert_idx, new_item)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"Updated {Path(file_path).name}")
    else:
        print(f"Warning: Could not find insertion point in {Path(file_path).name}")

for f in files:
    # Filter for modules 1-15 (rough check or process all)
    # We'll process all found in b2-hist meta to be consistent
    update_outline(f)
