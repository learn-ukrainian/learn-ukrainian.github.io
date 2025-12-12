
import os
import re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    
    # Logic: Find "**English Translation:**" and wrap the following content until next section
    # We look for blocks that are NOT yet wrapped (don't start with >)
    
    # Regex explanation:
    # (**English Translation:**)\n   <- Group 1: Header
    # ((?:(?!\n##|\n---|>\s*\[!note\]).)*)  <- Group 2: Content (stop at next header, separator, or if already wrapped)
    # 
    # This is tricky with regex. Better to iterate lines.
    
    lines = content.split('\n')
    new_lines = []
    
    in_translation_block = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Start of Translation Block
        if stripped == "**English Translation:**" or stripped == "**English Translation**:":
            # Check if already wrapped
            if i > 0 and lines[i-1].strip().startswith('>'):
                 # Already wrapped or part of a blockquote
                 new_lines.append(line)
                 i += 1
                 continue
            
            # Start strict wrapping
            new_lines.append("> [!note] English Translation")
            in_translation_block = True
            i += 1
            continue
            
        if in_translation_block:
            # End conditions
            if line.startswith('## ') or line.strip() == '---' or line.strip() == '# Summary' or (line.strip() == '' and i+1 < len(lines) and lines[i+1].startswith('## ')):
                in_translation_block = False
                new_lines.append(line)
                i += 1
                continue
            
            # Wrap content
            if line.strip() == "":
                 new_lines.append(">") # Empty blockquote line
            else:
                 # Convert numbered lists to bullets if inside translation
                 clean_line = line
                 if re.match(r'^\d+\.', clean_line):
                      clean_line = re.sub(r'^\d+\.', '-', clean_line)
                 
                 new_lines.append(f"> {clean_line}")
            i += 1
        else:
            new_lines.append(line)
            i += 1

    new_content = '\n'.join(new_lines)
    
    if new_content != original_content:
        print(f"Fixed: {filepath}")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
    else:
        print(f"No changes: {filepath}")

def main():
    targets = [
        "module-05.md", "module-07.md", "module-08.md", 
        "module-09.md", "module-11.md", "module-12.md", "module-15.md"
    ]
    
    base_dir = "curriculum/l2-uk-en/a1"
    
    for t in targets:
        path = os.path.join(base_dir, t)
        if os.path.exists(path):
            fix_file(path)
        else:
            print(f"File not found: {path}")

if __name__ == "__main__":
    main()
