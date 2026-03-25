import yaml
with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/meta/hryhoriy-skovoroda.yaml', 'r') as f:
    data = yaml.safe_load(f)
data['id'] = 'hryhoriy-skovoroda'
data['word_target'] = 4000
for item in data.get('content_outline', []):
    item['words'] = 400
with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/meta/hryhoriy-skovoroda.yaml', 'w') as f:
    yaml.dump(data, f, allow_unicode=True)
