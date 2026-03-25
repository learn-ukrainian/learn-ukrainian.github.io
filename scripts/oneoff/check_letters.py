import re
with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-ukrainian-alphabet.md', 'r') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'ма́ма' in line or 'та́то' in line or 'кіт' in line or 'молоко' in line or 'ма́сло' in line or 'ліс' in line:
        print(f"Line {i+1}: {repr(line)}")
