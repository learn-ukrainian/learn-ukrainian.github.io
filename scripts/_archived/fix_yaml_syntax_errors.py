import os
import re
from pathlib import Path

def fix_yaml_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by activity
    parts = re.split(r'\n-\s+', '\n' + content)
    header = parts[0].lstrip()
    activities = parts[1:]
    
    modified = False
    new_activities = []
    
    for act in activities:
        if 'type: mark-the-words' in act:
            # Regex to capture text key and value
            # (\s*text:\s*) (value) (?=\n\s*\w+:|\Z)
            match = re.search(r'(\s*text:\s*)((?:\||>)?.*)(?=\n\s*\w+:|\Z)', act, re.DOTALL)
            
            if match:
                key_part = match.group(1)
                value_part = match.group(2)
                
                # Check if it looks broken (contains | and lines with quotes or varying indentation)
                if '|' in value_part or '>' in value_part:
                    # Try to extract the actual text content
                    # Remove the | or > and newlines/indentation
                    cleaned_val = value_part.replace('|', '').replace('>', '').strip()
                    
                    # Remove leading/trailing quotes if they were wrapped around the block lines
                    if cleaned_val.startswith("'" ) and cleaned_val.endswith("'" ):
                        cleaned_val = cleaned_val[1:-1]
                    
                    # Normalize whitespace (replace newlines with spaces)
                    cleaned_val = re.sub(r'\s+', ' ', cleaned_val)
                    
                    # reconstruct as simple quoted string
                    new_val = f'"{cleaned_val}"'
                    
                    # Use span
                    start, end = match.span(2)
                    # We only replace the value part
                    act = act[:start] + new_val + act[end:]
                    modified = True
        
        new_activities.append(act)

    if modified:
        new_content = header.strip() + '\n- ' + '\n- '.join([a.strip() for a in new_activities])
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content.strip() + '\n')
        return True
    return False

def main():
    base_dir = Path('curriculum/l2-uk-en')
    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit']
    
    total_fixed = 0
    for level in levels:
        act_dir = base_dir / level / 'activities'
        if not act_dir.exists():
            continue
            
        print(f"Scanning Level {level.upper()}...")
        for yaml_file in act_dir.glob('*.yaml'):
            try:
                if fix_yaml_file(yaml_file):
                    print(f"  Fixed syntax: {yaml_file.name}")
                    total_fixed += 1
            except Exception as e:
                print(f"  Error processing {yaml_file.name}: {e}")
                
    print(f"\nTotal files fixed: {total_fixed}")

if __name__ == "__main__":
    main()