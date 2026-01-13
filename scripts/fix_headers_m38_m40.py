
import os

files = [
    'curriculum/l2-uk-en/c1/38-volodymyr-velykii.md',
    'curriculum/l2-uk-en/c1/39-kniaz-yaroslav-mudryi.md',
    'curriculum/l2-uk-en/c1/40-knyazhna-anna-yaroslavna.md'
]

replacements = [
    ('## Біографія', '## Життєпис'),
    ('## Історичний контекст', '## Внесок'),
    ('## Спадщина та сучасне сприйняття', '## Спадщина')
]

for file_path in files:
    if not os.path.exists(file_path):
        continue
        
    with open(file_path, 'r') as f:
        content = f.read()
    
    new_content = content
    for old, new in replacements:
        new_content = new_content.replace(old, new)
        
    # Also Ensure "Потрібно більше практики?" is filled if empty
    # For now just headers
    
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Fixed headers in {file_path}")
