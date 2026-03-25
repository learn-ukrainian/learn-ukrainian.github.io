import os

file_path = 'curriculum/l2-uk-en/a1/weather-and-nature.md'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the failed 'тому що' replacement
text = text.replace('— Привіт! Ні, ми не їдемо, тому що погана погода.', '— Привіт! Погана погода, тому ми не їдемо.')

# Fix 'тому що' in checking question 4
text = text.replace('Яке коротке та дуже популярне слово ми використовуємо замість "тому що" у розмовній мові?', 'Яке слово ми використовуємо замість "тому" у розмовній мові?')
text = text.replace('Яке коротке та дуже популярне слово використовується замість "тому що" у розмовній мові?', 'Яке слово використовується замість "тому" у розмовній мові?')

# Fix immersion by removing more English
text = text.replace(
    'Before we dive into the deep Ukrainian vocabulary, let us outline how the grammar of weather works. In English, you always need a subject. You say "It is cold" or "It is raining", using the dummy subject "it". Ukrainian grammar operates differently. We use elegant, subjectless impersonal constructions. We simply say "Cold" or use a verb of motion for the rain. We will use English explanations to scaffold this grammatical concept clearly, ensuring you understand the logic before you drill the Ukrainian phrases.',
    ''
)

# And another one just in case
text = text.replace(
    'This second dialogue shows the opposite scenario: canceling plans due to poor conditions. Notice how smoothly the speakers use the impersonal adverbs and the active verb structure for rain. By mastering these conversational patterns, you are well-equipped to handle the daily logistics of life in Ukraine, regardless of what the sky brings.',
    'This second dialogue shows the opposite scenario: canceling plans due to poor conditions. Mastering these conversational patterns helps you handle the daily logistics of life in Ukraine.'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
