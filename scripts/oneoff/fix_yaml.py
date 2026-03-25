import yaml
with open("curriculum/l2-uk-en/a1/activities/vowel-sounds.yaml", "r") as f:
    data = yaml.safe_load(f)

for act in data:
    if act['type'] == 'quiz':
        for item in act['items']:
            for opt in item['options']:
                if opt['text'] == 'мома': opt['text'] = 'мапа'
                if opt['text'] == 'мума': opt['text'] = 'сума'
                if opt['text'] == 'сик': opt['text'] = 'суп'

    if act['type'] == 'image-to-letter':
        for item in act['items']:
            if item.get('answer') == 'И' and item.get('note') == 'риба':
                item['emoji'] = '🦃'
                item['answer'] = 'І'
                item['note'] = 'індик'
                item['distractors'] = ['А', 'Е']
            elif 'И' in item.get('distractors', []):
                # Replace 'И' with something else in distractors
                if item['note'] == 'їжак':
                    item['distractors'] = ['І', 'А']
                elif item['note'] == 'село':
                    item['distractors'] = ['О', 'І']

with open("curriculum/l2-uk-en/a1/activities/vowel-sounds.yaml", "w") as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)
