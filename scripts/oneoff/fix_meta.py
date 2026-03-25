import yaml

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/the-ukrainian-alphabet.yaml', 'r') as f:
    data = yaml.safe_load(f)

# The new outline should match the plan and the markdown
new_outline = [
    {
        "title": "Вступ — Introduction",
        "slug": "introduction",
        "words": 150,
        "points": data['content_outline'][0]['points'][:3]
    },
    {
        "title": "Букви і звуки — Letters and Sounds",
        "slug": "letters-and-sounds",
        "words": 200,
        "points": data['content_outline'][0]['points'][3:]
    },
    {
        "title": "Голосні та приголосні — Vowels and Consonants",
        "slug": "vowels-and-consonants",
        "words": 200,
        "points": data['content_outline'][1]['points']
    },
    {
        "title": "Перші 10 літер — First 10 Letters",
        "slug": "first-10-letters",
        "words": 350,
        "points": data['content_outline'][2]['points']
    },
    {
        "title": "Перші слова — First Words in Context",
        "slug": "first-words-in-context",
        "words": 200,
        "points": data['content_outline'][3]['points']
    },
    {
        "title": "Підсумок — Summary",
        "slug": "summary",
        "words": 100,
        "points": data['content_outline'][4]['points']
    }
]

data['content_outline'] = new_outline

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/the-ukrainian-alphabet.yaml', 'w') as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)
