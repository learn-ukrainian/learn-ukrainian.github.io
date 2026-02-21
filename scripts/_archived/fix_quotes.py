import sys
import re

files = sys.argv[1:]

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace "..." with «...»
    # Regex: "([^"]*)" -> «\1»
    new_content = re.sub(r'"([^"]*)"', r'«\1»', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Processed {file_path}")
