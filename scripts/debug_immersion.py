
import re
import sys

def clean_for_immersion(text: str) -> str:
    # Remove ONLY metadata callouts (not engagement boxes)
    text = re.sub(r'^\s*>\s*\[!(answer|options|error|id)\].*$', '', text, flags=re.MULTILINE)
    # Remove Tables
    text = re.sub(r'^\s*\|.*$', '', text, flags=re.MULTILINE)
    # Remove Headers
    text = re.sub(r'^#+.*$', '', text, flags=re.MULTILINE)
    # Remove URLs from markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # Remove callout type markers [!note], [!tip], [!warning], etc.
    text = re.sub(r'\[![a-zA-Z-]+\]', '', text)
    # Remove image syntax ![alt](url)
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
    return text

def debug_immersion(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Manually remove frontmatter first as audit_module does
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if match:
        body = match.group(2)
    else:
        body = content

    clean_text = clean_for_immersion(body)
    
    # Calculate score
    clean_no_space = re.sub(r'\s+', '', clean_text)
    cyrillic = len(re.findall(r'[\u0400-\u04ff]', clean_no_space))
    latin = len(re.findall(r'[a-zA-Z]', clean_no_space))
    total = cyrillic + latin
    score = (cyrillic / total) * 100 if total > 0 else 100
    
    print(f"Immersion Score: {score:.2f}%")
    print(f"Cyrillic: {cyrillic}, Latin: {latin}")
    
    # Find Latin chars contexts
    print("\n--- LATIN CHARS CONTEXT ---")
    lines = clean_text.split('\n')
    for i, line in enumerate(lines):
        if re.search(r'[a-zA-Z]', line):
            # Highlight latin chars
            highlighted = re.sub(r'([a-zA-Z]+)', r'>>\1<<', line)
            print(f"Line {i}: {highlighted.strip()}")

if __name__ == "__main__":
    debug_immersion(sys.argv[1])
