import re
import yaml

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/health-basics.md', 'r') as f:
    content = f.read()

# Fix inline english translations
content = content.replace('### Однина: У мене болить (Singular subject)', '### Однина: У мене болить')
content = content.replace('### Множина: У мене болять (Plural subject)', '### Множина: У мене болять')
content = content.replace('**Мені болить...** (It hurts to me).', '**Мені болить...**.')
content = content.replace('### Фізичний біль проти емоційного (Physical vs. Emotional pain)', '### Фізичний біль проти емоційного')
content = content.replace('### Вказівки лікаря (Medical imperatives)', '### Вказівки лікаря')
content = content.replace('### В аптеці (Navigating the pharmacy)', '### В аптеці')
content = content.replace('### Лікарня чи поліклініка? (Hospital vs. Clinic)', '### Лікарня чи поліклініка?')
content = content.replace('**швидка допомога** (ambulance)', '**швидка допомога**')

# Fix Transliteration detected: 'множина (plural)' etc.
content = content.replace('однина (singular)', 'однина')
content = content.replace('множина (plural)', 'множина')
content = content.replace('родовий (genitive case)', 'родовий')
content = content.replace('давальний (dative case)', 'давальний')
content = content.replace('прикметник (adjective)', 'прикметник')
content = content.replace('наказний спосіб (Imperative mood)', 'наказний спосіб')
content = content.replace('наказовий спосіб (Imperative mood)', 'наказовий спосіб')

# The original english replacement I did had bugs with english
content = content.replace('**У мене болить серце.** (My physical heart organ has an ache. I need a cardiologist.)', '**У мене болить серце.**')
content = content.replace('**Мені болить серце за Україну.** (My heart aches for Ukraine. I feel deep sorrow and empathy.)', '**Мені болить серце за Україну.**')

# Engagement fixes
content = content.replace('[!tip]', '[!note]')

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/health-basics.md', 'w') as f:
    f.write(content)

# Fix Metalanguage terms used but not in vocabulary
vocab_path = '/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/health-basics.yaml'
with open(vocab_path, 'r') as f:
    vocab = yaml.safe_load(f)

new_words = [
    {'uk': 'однина', 'en': 'singular', 'ipa': 'ɔd.nɪ.nɑ́', 'pos': 'noun', 'gender': 'f'},
    {'uk': 'множина', 'en': 'plural', 'ipa': 'mnɔ.ʒɪ.nɑ́', 'pos': 'noun', 'gender': 'f'},
    {'uk': 'родовий', 'en': 'genitive', 'ipa': 'rɔ.dɔ.vɪ́j', 'pos': 'adj'},
    {'uk': 'давальний', 'en': 'dative', 'ipa': 'dɑ.vɑ́lʲ.nɪj', 'pos': 'adj'},
    {'uk': 'прикметник', 'en': 'adjective', 'ipa': 'prɪ.kmɛ́t.nɪk', 'pos': 'noun', 'gender': 'm'}
]

# Ensure terms aren't already there
existing_words = [item['uk'] for item in vocab['vocabulary']]
for w in new_words:
    if w['uk'] not in existing_words:
        vocab['vocabulary'].append(w)

with open(vocab_path, 'w') as f:
    yaml.dump(vocab, f, allow_unicode=True, sort_keys=False)

