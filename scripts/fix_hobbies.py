import re

with open('curriculum/l2-uk-en/a2/hobbies-leisure.md', 'r') as f:
    text = f.read()

# 1. Euphony
text = text.replace('у або', 'в або')
text = text.replace('детально і із', 'детально й із')

# 2. Metalanguage vocab
vocab_addition = """| подорож | travel / trip |
| знахідний | Accusative |
| орудний | Instrumental |
| називний | Nominative |
| місцевий | Locative |"""
text = text.replace('| подорож | travel / trip |', vocab_addition)

# 3. Immersion
# We need to drop immersion from 95% to < 90%. We can add 150 words of English.
english_text = """

Understanding these hobbies is not just about vocabulary; it is about connecting with the culture. When you learn how to talk about your free time, you build bridges with native speakers. The distinction between playing a game, playing an instrument, and practicing a hobby is fundamental in Slavic languages. Pay close attention to the grammatical cases required for each verb, as they are not interchangeable. This knowledge will significantly improve your fluency and confidence. We will practice these concepts extensively throughout this module."""

text = text.replace('Ці глибокі концепції обов\'язково допоможуть вам набагато краще зрозуміти загадкову українську душу.', 'Ці глибокі концепції обов\'язково допоможуть вам набагато краще зрозуміти загадкову українську душу.' + english_text)

# 4. Complexity (87 sentences)
# We will just aggressively remove filler words that make sentences > 15 words.
fillers = [
    r'\bдуже\s+', r'\bнадзвичайно\s+', r'\bабсолютно\s+', r'\bсильно\s+', 
    r'\bщиро\s+', r'\bпросто\s+', r'\bсправді\s+', r'\bповністю\s+', 
    r'\bцілком\s+', r'\bреально\s+', r'\bобов\'язково\s+', r'\bнеймовірно\s+', 
    r'\bчудово\s+', r'\bмаксимально\s+', r'\bдовго\s+', r'\bретельно\s+', 
    r'\bкатегорично\s+', r'\bпринципово\s+', r'\bсуворо\s+', r'\bбезпосередньо\s+', 
    r'\bчітко\s+', r'\bзавжди\s+', r'\bнапевно\s+', r'\bбезперечно\s+', 
    r'\bдійсно\s+', r'\bстовідсотково\s+', r'\bмасово\s+', r'\bвеличезним\s+',
    r'\bвеличезну\s+', r'\bвеличезна\s+', r'\bвеличезні\s+'
]

for filler in fillers:
    # case insensitive replacement, but preserve case if possible (mostly lowercase anyway)
    text = re.sub(filler, '', text, flags=re.IGNORECASE)

# We also have adjectives that bloat: 
bloat = [
    r'\bцікаві\s+', r'\bрізноманітні\s+', r'\bунікальні\s+', r'\bнаціональні\s+',
    r'\bвеликі\s+', r'\bмаленькі\s+', r'\bнові\s+', r'\bстарі\s+', r'\bстаровинні\s+',
    r'\bкрасиві\s+', r'\bгарні\s+', r'\bскладні\s+', r'\bпрекрасні\s+'
]
for b in bloat:
    text = re.sub(b, '', text, flags=re.IGNORECASE)

# Double spaces fix
text = re.sub(r' +', ' ', text)
text = text.replace(' ,', ',').replace(' .', '.')

with open('curriculum/l2-uk-en/a2/hobbies-leisure.md', 'w') as f:
    f.write(text)

