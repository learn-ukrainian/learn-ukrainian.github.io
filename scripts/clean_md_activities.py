import re
from pathlib import Path

FILES_TO_CLEAN = [
    "curriculum/l2-uk-en/b1/19-motion-starting-returning.md",
    "curriculum/l2-uk-en/b1/48-diminutives-master-class.md",
    "curriculum/l2-uk-en/b1/74-regions-south.md",
    "curriculum/l2-uk-en/b1/78-technology-and-startups.md",
    "curriculum/l2-uk-en/b1/79-sports-in-ukraine.md",
    "curriculum/l2-uk-en/b1/81-ukrainski-sviata-ta-festyvali.md",
    "curriculum/l2-uk-en/b1/86-b1-capstone.md",
]

def clean_file(file_path):
    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find Activities section
    # Matches # Activities/Вправи (level 1-3)
    # Captures everything until the next # Header or End of String
    # We want to remove the match but keep the *next* header if it exists.
    
    # Pattern:
    # (^#{1,3}\s+(?:Activities|Вправи).*?)(?=\n^#|\Z)
    # flags=re.DOTALL | re.MULTILINE
    
    pattern = r'(^#{1,3}\s+(?:Activities|Вправи).*?)(?=\n^#|\Z)'
    
    match = re.search(pattern, content, flags=re.DOTALL | re.MULTILINE)
    
    if match:
        print(f"Found activities in {path.name}")
        # Replace with empty string
        new_content = content[:match.start()] + content[match.end():]
        
        # Clean up extra newlines if any
        new_content = re.sub(r'\n{3,}', '\n\n', new_content)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Cleaned {path.name}")
    else:
        print(f"⚠️ No Activities section found in {path.name} (or pattern mismatch)")

if __name__ == "__main__":
    for f in FILES_TO_CLEAN:
        clean_file(f)
