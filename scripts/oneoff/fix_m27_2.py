import yaml
import re

# Fix YAML
yaml_file = 'curriculum/l2-uk-en/b1/activities/relative-clauses-de-kudy-zvidky.yaml'
with open(yaml_file, 'r', encoding='utf-8') as f:
    act_data = yaml.safe_load(f)

for i, activity in enumerate(act_data):
    if activity['type'] == 'translate':
        act_data[i] = {
            'type': 'translate',
            'title': 'Перекладіть українською',
            'instruction': 'Оберіть правильний переклад речення українською мовою.',
            'items': [
                {
                    'source': 'This is the old house where I lived.',
                    'options': [
                        {'text': 'Це старий будинок, де я жив.', 'correct': True},
                        {'text': 'Це старий будинок, куди я жив.', 'correct': False}
                    ]
                },
                {
                    'source': 'Show me the road where we need to go.',
                    'options': [
                        {'text': 'Покажи мені дорогу, куди нам потрібно йти.', 'correct': True},
                        {'text': 'Покажи мені дорогу, де нам потрібно йти.', 'correct': False}
                    ]
                },
                {
                    'source': 'The city where he comes from is very beautiful.',
                    'options': [
                        {'text': 'Місто, звідки він походить, дуже гарне.', 'correct': True},
                        {'text': 'Місто, куди він походить, дуже гарне.', 'correct': False}
                    ]
                },
                {
                    'source': 'We will go where you want to go.',
                    'options': [
                        {'text': 'Ми поїдемо туди, куди ти хочеш поїхати.', 'correct': True},
                        {'text': 'Ми поїдемо там, де ти хочеш поїхати.', 'correct': False}
                    ]
                },
                {
                    'source': 'It is good there, where we are not.',
                    'options': [
                        {'text': 'Добре там, де нас немає.', 'correct': True},
                        {'text': 'Добре туди, куди нас немає.', 'correct': False}
                    ]
                },
                {
                    'source': 'He put his keys somewhere in the room.',
                    'options': [
                        {'text': 'Він поклав ключі десь у кімнаті.', 'correct': True},
                        {'text': 'Він поклав ключі кудись у кімнаті.', 'correct': False}
                    ]
                }
            ]
        }

with open(yaml_file, 'w', encoding='utf-8') as f:
    yaml.dump(act_data, f, allow_unicode=True, sort_keys=False, indent=2)

# Fix Markdown
md_file = 'curriculum/l2-uk-en/b1/relative-clauses-de-kudy-zvidky.md'
with open(md_file, 'r', encoding='utf-8') as f:
    md_content = f.read()
    
md_content = md_content.replace("З часом вони обов'язково дозволять", "Із часом вони обов'язково дозволять")

with open(md_file, 'w', encoding='utf-8') as f:
    f.write(md_content)

print("Fixed")
