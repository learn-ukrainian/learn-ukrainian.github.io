import json

vocab_path = '/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/health-basics.yaml'

with open(vocab_path, 'r') as f:
    lines = f.readlines()

new_yaml = """
  - uk: "однина"
    en: "singular"
    ipa: "ɔd.nɪ.nɑ́"
    pos: "noun"
    gender: "f"
  - uk: "множина"
    en: "plural"
    ipa: "mnɔ.ʒɪ.nɑ́"
    pos: "noun"
    gender: "f"
  - uk: "родовий"
    en: "genitive case"
    ipa: "rɔ.dɔ.vɪ́j"
    pos: "adj"
  - uk: "давальний"
    en: "dative case"
    ipa: "dɑ.vɑ́lʲ.nɪj"
    pos: "adj"
  - uk: "прикметник"
    en: "adjective"
    ipa: "prɪ.kmɛ́t.nɪk"
    pos: "noun"
    gender: "m"
"""

with open(vocab_path, 'a') as f:
    f.write(new_yaml)
