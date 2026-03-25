import yaml
with open("curriculum/l2-uk-en/a1/activities/vowel-sounds.yaml", "r") as f:
    data = yaml.safe_load(f)

# Change only the non-existent forms in quiz
for act in data:
    if act['type'] == 'quiz':
        for item in act['items']:
            for opt in item['options']:
                if opt['text'] == 'мома': opt['text'] = 'мапа'
                if opt['text'] == 'мума': opt['text'] = 'сума'
                if opt['text'] == 'сик': opt['text'] = 'суп'

# Change image-to-letter 'И' item because 'риба' doesn't start with 'И'
for act in data:
    if act['type'] == 'image-to-letter':
        for item in act['items']:
            if item.get('answer') == 'И':
                item['emoji'] = '🦃'
                item['answer'] = 'І'
                item['note'] = 'індик'
            # Also fix distractors if any
            if 'distractors' in item:
                item['distractors'] = ['А' if d == 'И' else d for d in item['distractors']]

with open("curriculum/l2-uk-en/a1/activities/vowel-sounds-test2.yaml", "w") as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)
