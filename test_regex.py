import re

file_path = 'curriculum/l2-uk-en/b1/37-adverbial-participles-perfective.md'

with open(file_path, 'r') as f:
    content = f.read()

# find ALL ## mark-the-words sections
pattern = r'## mark-the-words:.*?(?=##|$)'
matches = re.finditer(pattern, content, re.DOTALL)

for i, match in enumerate(matches):
    section_text = match.group(0)
    print(f"\n--- Section {i+1} (length {len(section_text)}) ---")
    print(f"Start: {section_text[:50]}...")
    
    # regex from activities.py
    bold_matches = re.findall(r'\*\*[^*]+\*\*', section_text)
    print(f"All matches: {bold_matches}")
    
    valid_matches = [m for m in bold_matches if not m.strip('*').isdigit()]
    print(f"Valid matches: {len(valid_matches)}")
