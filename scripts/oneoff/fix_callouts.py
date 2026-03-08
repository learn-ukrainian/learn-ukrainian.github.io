import re

def fix_callouts(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Find [!tag] that are NOT preceded by > and add >
    # Actually, let's just do a blanket replace for all known tags.
    tags = [
        'note', 'tip', 'warning', 'caution', 'important', 'cultural',
        'history-bite', 'myth-buster', 'quote', 'context', 'analysis',
        'source', 'legacy', 'reflection', 'fact', 'culture', 'military',
        'perspective', 'biography', 'decolonization'
    ]

    for tag in tags:
        # If it's just [!tag] on a line, replace with > [!tag]
        # Make sure not to duplicate > if it's already there.
        text = re.sub(rf'^(?!\>)\s*\[!{tag}\]', f'> [!{tag}]', text, flags=re.MULTILINE)
        
    # Replace decolonization with perspective as it's not in the official list
    text = text.replace('> [!decolonization]', '> [!perspective]')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)

fix_callouts('curriculum/l2-uk-en/hist/oun.md')
