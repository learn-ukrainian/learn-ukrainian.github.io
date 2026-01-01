import re
import glob
import os
from pathlib import Path

def clean_file(file_path):
    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find Activities section
    # Matches #, ##, ### with optional emoji 🎯
    # Followed by Activities or Вправи
    # Captures everything until:
    # 1. The next # Header (Summary, Vocabulary, Resources)
    # 2. End of file
    
    # We want to remove the Activities block.
    # Note: Sometimes Activities is the LAST section.
    
    # Pattern explanation:
    # ^#{1,3}\s+          : 1-3 hashes
    # (?:🎯\s*)?          : Optional emoji
    # (?:Activities|Вправи) : Title
    # .*?                 : Content (non-greedy)
    # (?=\n^#|\Z)         : Lookahead for next header or EOF
    
    pattern = r'(^#{1,3}\s+(?:🎯\s*)?(?:Activities|Вправи).*?)(?=\n^#|\Z)'
    
    match = re.search(pattern, content, flags=re.DOTALL | re.MULTILINE)
    
    if match:
        # print(f"Found activities in {path.name}")
        # Replace with empty string
        new_content = content[:match.start()] + content[match.end():]
        
        # Clean up extra newlines
        new_content = re.sub(r'\n{3,}', '\n\n', new_content)
        
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Cleaned {path.name}")
    # else:
        # print(f"  (Clean) {path.name}")

def main():
    dirs = ['curriculum/l2-uk-en/a1', 'curriculum/l2-uk-en/a2']
    
    for d in dirs:
        print(f"Scanning {d}...")
        files = sorted(glob.glob(os.path.join(d, '*.md')))
        for f in files:
            clean_file(f)

if __name__ == "__main__":
    main()
