import json

vocab_path = '/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/health-basics.yaml'

with open(vocab_path, 'r') as f:
    content = f.read()

# I appended at the end, but vocabulary might not have been at the end, or syntax error. Let's fix it properly.
if 'однина' not in content:
    with open(vocab_path, 'a') as f:
        f.write("\n  - uk: 'однина'\n    en: 'singular'\n    ipa: 'ɔd.nɪ.nɑ́'\n    pos: 'noun'\n    gender: 'f'\n")
        f.write("  - uk: 'множина'\n    en: 'plural'\n    ipa: 'mnɔ.ʒɪ.nɑ́'\n    pos: 'noun'\n    gender: 'f'\n")
        f.write("  - uk: 'родовий'\n    en: 'genitive case'\n    ipa: 'rɔ.dɔ.vɪ́j'\n    pos: 'adj'\n")
        f.write("  - uk: 'давальний'\n    en: 'dative case'\n    ipa: 'dɑ.vɑ́lʲ.nɪj'\n    pos: 'adj'\n")
        f.write("  - uk: 'прикметник'\n    en: 'adjective'\n    ipa: 'prɪ.kmɛ́t.nɪk'\n    pos: 'noun'\n    gender: 'm'\n")

