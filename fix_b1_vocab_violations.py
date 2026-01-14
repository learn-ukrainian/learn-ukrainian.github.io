import yaml
from pathlib import Path

def fix_08():
    path = Path('curriculum/l2-uk-en/b1/vocabulary/08-aspect-past-result-process.yaml')
    if not path.exists(): return
    data = yaml.safe_load(path.read_text())
    for item in data['items']:
        if item['lemma'] == 'хвилину':
            item['gender'] = 'f'
        if item['lemma'] == 'годину':
            item['gender'] = 'f'
            item['ipa'] = '/ɦɔˈdɪnu/'
    with open(path, 'w') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def fix_35():
    path = Path('curriculum/l2-uk-en/b1/vocabulary/35-concessive-khocha.yaml')
    if not path.exists(): return
    data = yaml.safe_load(path.read_text())
    for item in data['items']:
        if item['lemma'] == 'все ж таки':
            item['pos'] = 'part'
    with open(path, 'w') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def fix_pos(path):
    if not path.exists(): return
    data = yaml.safe_load(path.read_text())
    for item in data['items']:
        pos = item.get('pos', '')
        if 'noun phrase' in pos:
            item['pos'] = 'phrase'
        elif 'verb phrase' in pos:
            item['pos'] = 'phrase'
        elif 'proper noun' in pos:
            item['pos'] = 'propn'
        elif 'noun (pl)' in pos:
            item['pos'] = 'noun'
            item['gender'] = 'pl'
    with open(path, 'w') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def fix_91():
    path = Path('curriculum/l2-uk-en/b1/vocabulary/91-b1-capstone.yaml')
    if not path.exists(): return
    data = yaml.safe_load(path.read_text())
    seen = set()
    new_items = []
    for item in data['items']:
        lemma = item['lemma']
        if lemma not in seen:
            seen.add(lemma)
            new_items.append(item)
    data['items'] = new_items
    with open(path, 'w') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

if __name__ == "__main__":
    fix_08()
    fix_35()
    for i in range(80, 85):
        fix_pos(Path(f'curriculum/l2-uk-en/b1/vocabulary/{i:02}-active-lifestyle.yaml')) # This is wrong, names are different
    
    # Correct names for 80-84
    fix_pos(Path('curriculum/l2-uk-en/b1/vocabulary/80-active-lifestyle.yaml'))
    fix_pos(Path('curriculum/l2-uk-en/b1/vocabulary/81-running-in-ukraine.yaml'))
    fix_pos(Path('curriculum/l2-uk-en/b1/vocabulary/82-mountains-trail.yaml'))
    fix_pos(Path('curriculum/l2-uk-en/b1/vocabulary/83-cycling-water.yaml'))
    fix_pos(Path('curriculum/l2-uk-en/b1/vocabulary/84-winter-sports.yaml'))
    
    fix_91()
    print("B1 Vocab Fixes applied.")
