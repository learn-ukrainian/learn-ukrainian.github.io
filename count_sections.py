import re
import sys

def count_words(text):
    return len(text.split())

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by any header (# or ##)
    sections = re.split(r'\n(#+ .*?)\n', content)
    
    current_header = "Header/Frontmatter"
    results = []
    
    # First part before first header
    results.append((current_header, count_words(sections[0])))
    
    for i in range(1, len(sections), 2):
        header = sections[i]
        body = sections[i+1] if i+1 < len(sections) else ""
        results.append((header, count_words(body)))
        
    for header, count in results:
        print(f"{header}: {count}")

if __name__ == "__main__":
    process_file(sys.argv[1])
