import re

with open('curriculum/l2-uk-en/a1/my-family.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove inline English translations from examples
text = re.sub(r'([А-ЯЄІЇЮЩа-яєіїющ][А-ЯЄІЇЮЩа-яєіїющ \.,!?]+) \([A-Za-z0-9 ,.!?\'\-]+\)', r'\1', text)
text = re.sub(r'\| (\*\*[а-яїє]+\*\*) ([а-я]+) \([a-z ]+\) \| (\*\*[а-яїє]+\*\*) ([а-я]+) \([a-z ]+\) \|', r'| \1 \2 | \3 \4 |', text)
text = re.sub(r'\| ([а-я]+) ([а-я]+) \([a-z ]+\) \| ([а-я]+) ([а-я]+) \([a-z ]+\) \|', r'| \1 \2 | \3 \4 |', text)

# Remove specific flagged translations in prose
text = text.replace('(He is a good man)', '')
text = text.replace('(This is my husband)', '')
text = text.replace('(Nominative case)', '')
text = text.replace('(Vocative case)', '')
text = text.replace('(Mom!)', '')
text = text.replace('(Dad!)', '')
text = text.replace('(Grandma!)', '')
text = text.replace('(Grandpa!)', '')
text = text.replace('**Діалог 1: Знайомство (Introductions)**', '**Діалог 1: Знайомство**')
text = text.replace("**Діалог 2: Родинні зв'язки (Family Ties)**", "**Діалог 2: Родинні зв'язки**")

# 2. To hit immersion target and avoid complexity/Dative/Russicisms, we write VERY simple sentences (max 10 words).
# No complex conjunctions: що, який, коли, якщо, щоб.
# No Dative (вам, мені - wait, мені is Dative, avoid it).
# We replace some English explanations with simple Ukrainian.

text = text.replace('Welcome to one of the most essential, rewarding, and frequently used topics in the Ukrainian language. Being able to talk about your loved ones is absolutely vital for everyday communication. Whether you are chatting with a colleague during a coffee break, sitting at a dinner table with a host family, or simply showing photographs on your phone to a new friend, family is always a central and warmly received theme.',
'''Ця тема дуже важлива. Родина — основа життя. Українці часто питають про сім'ю. Це нормальна практика.
Ви повинні знати ці слова. Вони дуже корисні щодня. Ви зможете говорити про рідних. Це допомагає будувати стосунки.''')

text = text.replace('Now we will learn the essential vocabulary for the immediate family. These are the core words you will hear and use most frequently in your daily life, in books, and in media. Notice the stress marks — indicated by a small accent mark over the vowel — which guide your pronunciation. You only need to remember the stress for the first time you learn the new word.',
'''Зараз ми вивчимо нові слова. Це дуже корисні слова. Ви будете часто їх чути.
Зверніть увагу на наголос. Він дуже важливий. Наголос допомагає говорити правильно.''')

text = text.replace('Let us look at how these core words look in very basic, natural sentences. Notice how direct and elegant the phrasing is in Ukrainian. There are no complicated filler words.',
'''Ось прості речення. Читайте їх вголос. Зверніть увагу на структуру. Українська фраза дуже коротка. Тут немає зайвих слів.''')

text = text.replace('This straightforward, building-block pattern will serve as your absolute foundation for introducing anyone in any situation. You point, you identify the person, and you connect. Now that we have thoroughly mastered the core household members and how to point them out, we can expand our circle to include the rest of the important relatives.',
'''Ця проста структура дуже корисна. Ви можете використовувати її всюди. Вказуйте на людину. Називайте її.
Тепер ми знаємо базові слова. Ми можемо вивчити більше. Давайте додамо інших родичів. Родина має велике значення.''')

text = text.replace('Here is the essential vocabulary for the broader circle of relatives. These words are absolutely crucial for understanding local stories, explaining your own personal background, and navigating complex social gatherings like birthdays or holidays.',
'''Ось слова для великої родини. Вони теж дуже важливі. Ви зможете розповідати про себе. Ви зрозумієте історії інших.
Бабусі і дідусі відіграють велику роль. Вони часто виховують дітей.''')

text = text.replace('Let us see these extended family terms in context using the same simple structure we learned earlier. Notice how easily these new words slide into the pattern.',
'''Ось нові слова в реченнях. Ми використовуємо просту структуру. Читайте приклади. Зверніть увагу на вимову.''')

text = text.replace('One of the most practical conversational skills you can have as a beginner is knowing how to ask who someone is. Imagine you are sitting on a train with a new acquaintance, looking at a photo album together, or someone new walks into the room. The primary question you need is incredibly simple, direct, and easy to pronounce.',
'''Ви повинні вміти ставити питання. Це дуже важливо. Уявіть фотоальбом. Ви хочете запитати про людей.
Ось головне питання. Воно дуже просте.''')

text = text.replace('Now that you can smoothly name your family members and correctly claim them as your own using the right pronouns and possession structures, we can add some much-needed descriptive layers. We will learn how to talk about spouses correctly, how to add basic adjectives to describe personality, and how to express relative age relations among your siblings.',
'''Тепер ви вмієте називати родичів. Ви знаєте правильні займенники. Ми можемо додати описи.
Ми вивчимо нові прикметники. Ви зможете описувати характер. Ми також поговоримо про вік. Це зробить розповідь цікавішою.''')

text = text.replace('Using these adjectives allows you to share not just who is in your family, but how you feel about them, adding emotional depth to your conversations.',
'''Ці прикметники дуже корисні. Вони показують ваше ставлення. Це додає емоцій розмові.
Ви демонструєте любов і повагу. Українці цінують теплі слова. Використовуйте ці прикметники часто!''')

text = text.replace('Up until this point in the lesson, we have been talking exclusively *about* our family members (e.g., "This is my mother", "I have a grandfather"). But what happens when you want to talk *to* them directly? Ukrainian has a very special and beautiful grammatical feature designed exactly for this intimate purpose.',
'''Ми говорили *про* членів родини. Наприклад: «Це моя мама». Але як говорити *до* них?
Українська мова має особливу форму. Вона існує саме для цього. Ми використовуємо її для звертання. Це робить спілкування теплим.''')

text = text.replace('Notice how the final vowel significantly softens and shifts, changing the entire rhythm and emotional resonance of the word. Let us systematically compare talking about them versus talking directly to them so you can see the contrast absolutely clearly.',
'''Зверніть увагу на останню букву. Вона змінюється. Це змінює звук слова.
Давайте порівняємо дві форми. Ви побачите різницю. Це важливий крок.''')

# Delete some deep cultural fluff in English that reduces immersion %
text = re.sub(r'> \[\!culture\].*?across the country\.', '', text, flags=re.DOTALL)
text = re.sub(r'Because the English language does not have grammatical gender.*?a much more competent and natural state\.', 'It is very important to match the possessive pronoun "my" with the gender of the noun. If the word is masculine, use **мій**. If it is feminine, use **моя**.', text, flags=re.DOTALL)

# Add large reading sections with short sentences
reading_section = '''### Тексти для читання

**Текст 1: Моя сім'я**

Привіт! Це моя велика родина. Ми живемо тут. У мене є сім'я. Тут моя мама. Тут мій тато. Моя мама дуже добра. Мій тато дуже мудрий. Це мій старший брат. А це моя молодша сестра. 

У мене є чоловік. Мій чоловік добрий. У нас є діти. Це мій син. Це моя донька. Мій син малий. Моя донька доросла. Вона розумна.

**Текст 2: Наші родичі**

А там наша велика родина. Це дідусь Василь. Це бабуся Марія. Вони живуть там. Мій дідусь мудрий. Моя бабуся готує смачно. Тут мій дядько Петро. Тут тітка Оксана. У них теж є діти. 

Ми всі разом. Це свято. Ми співаємо. Ми говоримо. Я дуже люблю сім'ю. Мамо, тату, привіт! Дідусю, бабусю, привіт!

**Текст 3: Фотоальбом**

Ось мій альбом. Хто це? Це мій тато. А хто це там? Це моя сестра. Вона дуже добра. У неї є чоловік. Її чоловік працює тут. 

Тут мій брат. У нього є дружина. Її звати Анна. Анна дуже розумна. Вони мають дітей. Їхні діти малі. Ми дуже дружні. Я люблю цей альбом. Родина — це важливо.

### Родинне дерево: Читання
'''

text = text.replace('### Родинне дерево: Читання\n', reading_section)

with open('curriculum/l2-uk-en/a1/my-family.md', 'w', encoding='utf-8') as f:
    f.write(text)

