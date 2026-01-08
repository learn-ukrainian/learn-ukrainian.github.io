import re
from pathlib import Path

def clean_file(path):
    content = path.read_text(encoding='utf-8')
    original = content
    
    # Remove # Activities and its placeholder text
    content = re.sub(r'# Activities\s*\n+\(Вправи знаходяться у YAML файлі\)\s*', '', content)
    
    # Remove # Vocabulary and its placeholder text
    content = re.sub(r'# Vocabulary\s*\n+\(Словник знаходиться у YAML файлі\)\s*', '', content)
    
    # Remove trailing dashes if they were left behind
    content = re.sub(r'\n---\s*$', '', content.strip())
    
    if content != original:
        print(f"Cleaning {path}")
        path.write_text(content + '\n', encoding='utf-8')

root = Path('curriculum/l2-uk-en')
for f in root.glob('**/*.md'):
    clean_file(f)
