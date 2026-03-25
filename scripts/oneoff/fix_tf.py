import yaml

with open('curriculum/l2-uk-en/a1/activities/euphony-and-polish.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

for act in data:
    if act.get('type') == 'true-false':
        for item in act['items']:
            item['correct'] = item.pop('is_true')
            item['explanation'] = 'Це правило української мови.'

with open('curriculum/l2-uk-en/a1/activities/euphony-and-polish.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)
