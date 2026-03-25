import re

with open("curriculum/l2-uk-en/a2/vocabulary/being-and-becoming.yaml", "r", encoding="utf-8") as f:
    text = f.read()

# Match lemma: "..." and remove anything that is not Cyrillic, hyphen, apostrophe, or space.
def clean_lemma(match):
    prefix = match.group(1)
    word = match.group(2)
    # keep only ukrainian lowercase/uppercase letters, space, hyphen, apostrophe
    cleaned_word = re.sub(r"[^а-яіїєґА-ЯІЇЄҐ'ʼ\- ]", "", word)
    return f'{prefix}"{cleaned_word}"'

text = re.sub(r'(lemma:\s*)"([^"]+)"', clean_lemma, text)

with open("curriculum/l2-uk-en/a2/vocabulary/being-and-becoming.yaml", "w", encoding="utf-8") as f:
    f.write(text)

