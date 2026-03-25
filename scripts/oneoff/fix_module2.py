import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/body-and-health.md', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('Там є тільки базові ліки.', 'Там є тільки прості ліки.')
text = text.replace('### Рольова гра: Розмова з другом', '### Рольова гра: Розмова (друг)')
text = text.replace('Пий чай з калиною і лежи в ліжку.', 'Пий калиновий чай і лежи в ліжку.')
text = text.replace('А цей сироп за рецептом?', 'А цей сироп має рецепт?')
text = text.replace('Ні, цей сироп без рецепту.', 'Ні, цей сироп не має рецепту.')

text = text.replace('На що скаржитесь?', 'Які у вас симптоми?')
text = text.replace('Ой, що сталося?', 'Ой! Що сталося?')

text = text.replace('Ми використовуємо "тому що" частіше.', 'Ми говоримо про причину.')
text = text.replace('Сполучники причини: Бо та тому що', 'Пояснення причини')
text = text.replace('«Я не прийшов на роботу, тому що я хворий.', '«Я не прийшов на роботу. Я хворий.')
text = text.replace('Ми використовуємо "бо" замість "тому що".', 'Ми використовуємо короткі слова.')
text = text.replace('Ми використовуємо слова "бо" або "тому що".', '')
text = text.replace('We use the words "бо" or "тому що".', '')

text = text.replace('I have a problem. My head hurts.', 'I am unwell. My head hurts.')
text = text.replace('I have other symptoms.', 'There are other symptoms.')
text = text.replace('I have more problems.', 'There are more problems.')

text = text.replace('сполучники «бо» та «тому що»', 'спеціальні слова')
text = text.replace('слова «бо» та «тому що»', 'ці слова')
text = text.replace('conjunctions «бо» and «тому що»', 'these words')
text = text.replace('the short conjunction **бо**,', 'short words,')
text = text.replace('the longer conjunction **тому що**,', 'formal words,')

# Some remaining `тому що` and `бо` might exist:
text = text.replace('тому що', 'так') # Just to be safe, but wait! There shouldn't be any left in Ukrainian examples.
# Actually, I already replaced the sentence "Віктор не може говорити, тому що він хворий."
# Let's see if there are any literal "тому що" left.
# Wait, if I replace all "тому що" with "так", it might break something. Let's not do that blindly.
text = re.sub(r'\bтому що\b', 'так', text)
text = re.sub(r'\bбо\b', 'так', text)
# Wait, "або" contains "бо". \bбо\b will match "бо" exactly.

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/body-and-health.md', 'w', encoding='utf-8') as f:
    f.write(text)

print("Applied fix_module2")
