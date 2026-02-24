import yaml

vocab_path = '/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/health-basics.yaml'

with open(vocab_path, 'r') as f:
    content = f.read()

# Replace my wrong keys (uk -> lemma, en -> translation)
content = content.replace('uk: "однина"', 'lemma: "однина"')
content = content.replace('en: "singular"', 'translation: "singular"')
content = content.replace('uk: "множина"', 'lemma: "множина"')
content = content.replace('en: "plural"', 'translation: "plural"')
content = content.replace('uk: "родовий"', 'lemma: "родовий"')
content = content.replace('en: "genitive case"', 'translation: "genitive case"')
content = content.replace('uk: "давальний"', 'lemma: "давальний"')
content = content.replace('en: "dative case"', 'translation: "dative case"')
content = content.replace('uk: "прикметник"', 'lemma: "прикметник"')
content = content.replace('en: "adjective"', 'translation: "adjective"')

# I used 'uk' instead of 'lemma' and 'en' instead of 'translation' with single quotes
content = content.replace("uk: 'однина'", "lemma: 'однина'")
content = content.replace("en: 'singular'", "translation: 'singular'")
content = content.replace("uk: 'множина'", "lemma: 'множина'")
content = content.replace("en: 'plural'", "translation: 'plural'")
content = content.replace("uk: 'родовий'", "lemma: 'родовий'")
content = content.replace("en: 'genitive case'", "translation: 'genitive case'")
content = content.replace("uk: 'давальний'", "lemma: 'давальний'")
content = content.replace("en: 'dative case'", "translation: 'dative case'")
content = content.replace("uk: 'прикметник'", "lemma: 'прикметник'")
content = content.replace("en: 'adjective'", "translation: 'adjective'")

with open(vocab_path, 'w') as f:
    f.write(content)

