
import sys
import re

def bold_terms(file_path, terms):
    with open(file_path, 'r') as f:
        content = f.read()
    
    for term in terms:
        # Avoid double bolding
        pattern = re.compile(f'(?<!\\*\\*)(?<!\\*){re.escape(term)}(?!\\*)(?!\\*\\*)')
        content = pattern.sub(f'**{term}**', content)
        
    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    file_path = sys.argv[1]
    terms = sys.argv[2:]
    bold_terms(file_path, terms)
