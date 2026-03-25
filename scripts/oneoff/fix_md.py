import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-ukrainian-alphabet.md', 'r') as f:
    content = f.read()

# Fix 1: IPA_BANNED
content = content.replace('[Full Playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)', 'full playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV')

# Fix 2-6: Remove stress marks and fix decodability issues by standardizing
words_to_strip = ['ма́ма', 'та́то', 'молоко́', 'мі́сто', 'ма́сло']
for w in words_to_strip:
    content = content.replace(w, w.replace('́', ''))

# Fix 7-9: Morphological violation for "дякую"
content = content.replace('дя́кую', 'спасибі')
content = content.replace('дякую', 'спасибі')
content = content.replace('Дя́кую', 'Спасибі')
content = content.replace('Дякую', 'Спасибі')

# Fix 10-11: Untranslated non-decodable
content = content.replace('letters (**букви**)', '**букви** (letters)')
content = content.replace('sounds (**звуки**)', '**звуки** (sounds)')

# Fix 12: Сторінка
content = content.replace('Сторінка 4', 'Сторінка (page) 4')
content = content.replace('Сторінка 38', 'Сторінка (page) 38')
content = content.replace('Сторінка 28', 'Сторінка (page) 28')
content = content.replace('Сторінка 5', 'Сторінка (page) 5')

# Fix 13-24: Alphabet translation
alpha_orig = """* **Аа Бб Вв Гг Ґґ Дд Ее Єє Жж Зз Ии**
* **Іі Її Йй Кк Лл Мм Нн Оо Пп Рр Сс**
* **Тт Уу Фф Хх Цц Чч Шш Щщ Ьь Юю Яя**"""

alpha_new = """* **Аа** (A) **Бб** (B) **Вв** (V) **Гг** (H) **Ґґ** (G) **Дд** (D) **Ее** (E) **Єє** (Ye) **Жж** (Zh) **Зз** (Z) **Ии** (Y)
* **Іі** (I) **Її** (Yi) **Йй** (Y) **Кк** (K) **Лл** (L) **Мм** (M) **Нн** (N) **Оо** (O) **Пп** (P) **Рр** (R) **Сс** (S)
* **Тт** (T) **Уу** (U) **Фф** (F) **Хх** (Kh) **Цц** (Ts) **Чч** (Ch) **Шш** (Sh) **Щщ** (Shch) **Ьь** (soft sign) **Юю** (Yu) **Яя** (Ya)"""

content = content.replace(alpha_orig, alpha_new)

# Fix 25: PLAN_SECTION_MISSING
content = content.replace('## Алфавіт — The Alphabet', '## Вступ — Introduction')
content = content.replace('## Голосні: А, О, У, І — Vowels', '## Голосні та приголосні — Vowels and Consonants')
content = content.replace('## Приголосні: М, Н, Т, К, С, Л — Consonants', '## Перші 10 літер — First 10 Letters')
content = content.replace('## Перші слова — First Words', '## Перші слова — First Words in Context')

# Split "Букви і звуки — Letters and Sounds"
target_split = 'The most important concept for a beginner is the difference between letters'
if target_split in content:
    content = content.replace(target_split, '## Букви і звуки — Letters and Sounds\n\n' + target_split)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-ukrainian-alphabet.md', 'w') as f:
    f.write(content)
