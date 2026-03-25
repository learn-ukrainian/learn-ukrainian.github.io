import yaml
with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/meta/hryhoriy-skovoroda.yaml', 'r') as f:
    data = yaml.safe_load(f)
data['word_target'] = 3900
targets = {
    'Вступ — Український Сократ': 380,
    'Життєпис: I — Формування особистості': 420,
    'Життєпис: II — Європейський досвід та педагогіка': 440,
    'Життєпис: III — Шлях мандрівного філософа': 400,
    'Історичний контекст: Філософія на тлі руїни': 320,
    'Внесок: I — Філософська система': 600,
    'Внесок: II — Літературна спадщина': 400,
    'Останні роки та легенда': 300,
    'Спадщина: Живий символ': 400,
    'Підсумок': 200
}
for item in data.get('content_outline', []):
    item['words'] = targets.get(item['section'], 400)
with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/meta/hryhoriy-skovoroda.yaml', 'w') as f:
    yaml.dump(data, f, allow_unicode=True)
