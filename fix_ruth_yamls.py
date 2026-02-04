import os
import re

dir_path = 'curriculum/l2-uk-en/plans/ruth/'
files = [f for f in os.listdir(dir_path) if f.endswith('.yaml')]

for f in files:
    path = os.path.join(dir_path, f)
    with open(path, 'r') as stream:
        content = stream.read()
    
    # Fix single quotes inside single quotes in objectives
    # - 'Smotrytsky's' -> - "Smotrytsky's"
    new_content = re.sub(r"- '(.*?)'(?=\n)", r'- "\1"', content)
    
    # Fix "Енеїда" (1798) issue
    new_content = re.sub(r'- "(.*?)" (.*?)(?=\n)', r'- "\1 \2"', new_content)
    
    # Special case for Smotrytsky's inside already double quoted? 
    # Actually the regex above replaces all '- '...' with '- "..."' which handles Smotrytsky's.
    
    if new_content != content:
        with open(path, 'w') as stream:
            stream.write(new_content)
        print(f"Fixed {f}")
