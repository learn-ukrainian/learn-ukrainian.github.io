import os
import re

def fix_yaml_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    modified = False
    
    for line in lines:
        # Match lines like: - "Text" more text OR focus: "Text" more text
        # But NOT if they are already wrapped in single quotes or if it's just a single quoted string
        
        # Pattern 1: list item starting with quote but having trailing text
        list_match = re.match(r'^(\s*-\s*)"([^"]+)"\s*(.+)$', line)
        if list_match:
            prefix, quoted, trailing = list_match.groups()
            new_line = f"{prefix}'\"{quoted}\" {trailing.strip()}'\n"
            new_lines.append(new_line)
            modified = True
            continue
            
        # Pattern 2: key value starting with quote but having trailing text
        key_match = re.match(r'^(\s*\w+:\s*)"([^"]+)"\s*(.+)$', line)
        if key_match:
            prefix, quoted, trailing = key_match.groups()
            new_line = f"{prefix}'\"{quoted}\" {trailing.strip()}'\n"
            new_lines.append(new_line)
            modified = True
            continue
            
        new_lines.append(line)
        
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return False

def main():
    directory = "curriculum/l2-uk-en/c1-bio/meta"
    for filename in os.listdir(directory):
        if filename.endswith(".yaml"):
            path = os.path.join(directory, filename)
            if fix_yaml_file(path):
                print(f"Fixed {filename}")

if __name__ == "__main__":
    main()
