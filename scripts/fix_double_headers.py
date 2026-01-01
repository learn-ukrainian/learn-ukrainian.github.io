import re
from pathlib import Path

def fix_double_headers():
    modules_dir = Path("/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1")
    modules = sorted(list(modules_dir.glob("*.md")))
    
    # Regex to find the pattern:
    # | Word ... | ... |
    # | --- ... | ... |
    # | Word ... | ... |
    # | --- ... | ... |
    # We want to replace it with just one set.
    
    # The pattern in M04 was:
    # | Word ... | ... |
    # | --- ... | ... |
    # | Word ... | ... |
    # | --- ... | ... |
    
    print(f"Scanning {len(modules)} modules for double headers...")
    
    count_fixed = 0
    
    for mod_file in modules:
        with open(mod_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Define the header block
        header_block = "| Word        | IPA             | English          | POS   | Gender | Note     |\n| ----------- | --------------- | ---------------- | ----- | ------ | -------- |"
        
        # Regex for flexible whitespace
        # Capture the header, then look for a repeat of it immediately or closely following
        
        # Simpler approach: Look for two consecutive occurrences of the word/dash rows
        # We'll split by lines and look for patterns.
        
        lines = content.splitlines()
        new_lines = []
        skip_next = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this line looks like a header start
            if "Word" in line and "IPA" in line and "|" in line:
                # Check next line for separator
                if i + 1 < len(lines) and "---" in lines[i+1]:
                    # Check if lines i+2 and i+3 are ALSO header + separator
                    if i + 2 < len(lines) and "Word" in lines[i+2] and "IPA" in lines[i+2] and "|" in lines[i+2]:
                        if i + 3 < len(lines) and "---" in lines[i+3]:
                            # Found double header!
                            # print(f"Found double header in {mod_file.name} at line {i}")
                            # Append the first one (i, i+1)
                            new_lines.append(lines[i])
                            new_lines.append(lines[i+1])
                            # Skip the duplicate (i+2, i+3)
                            i += 4
                            count_fixed += 1
                            continue
            
            new_lines.append(line)
            i += 1
            
        new_content = "\n".join(new_lines)
        if new_content != content:
            # Add final newline if it was stripped
            if content.endswith("\n") and not new_content.endswith("\n"):
                new_content += "\n"
                
            with open(mod_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Fixed {mod_file.name}")
            
    print(f"Total files fixed: {count_fixed}")

if __name__ == "__main__":
    fix_double_headers()
