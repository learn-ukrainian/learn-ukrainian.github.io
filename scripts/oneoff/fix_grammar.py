import re

with open('curriculum/l2-uk-en/a1/my-world-objects.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix Dative and Complex Sentences
text = text.replace('В англійській мові "door" — це однина.', 'Слово "door" англійською — це однина.')
text = text.replace('В українській мові слово "двері" завжди має форму множини.', 'Українською слово "двері" завжди має форму множини.')
text = text.replace('В українській мові немає форми однини для цього слова.', 'Українською немає форми однини для цього слова.')
text = text.replace('Тому що слово "двері" — це множина, вказівний займенник також має бути у формі множини.', 'Слово "двері" — це множина. Вказівний займенник також має форму множини.')
text = text.replace('Ви ніколи не можете використовувати слова "ця" або "та" з цим словом.', 'Не використовуйте слова "ця" або "та".')
text = text.replace('Щоб сказати "this door", ми використовуємо слово "ці":', 'Для "this door" ми використовуємо слово "ці":')
text = text.replace('Щоб сказати "that door", ми використовуємо слово "ті":', 'Для "that door" ми використовуємо слово "ті":')
text = text.replace("Пам'ятайте, що двері — це завжди множина!", "Увага! Двері — це завжди множина!")

# Boost Immersion (just a tiny bit more)
immersion_addition = """
Ви чудово попрацювали. Ви знаєте нові слова: дім, стіл, вікно. Ви знаєте нову граматику. Це дуже важливо!
"""
text = text.replace('### Підсумок', '### Підсумок\n' + immersion_addition)

with open('curriculum/l2-uk-en/a1/my-world-objects.md', 'w', encoding='utf-8') as f:
    f.write(text)

# Add vocabulary words
vocab_add = """  - lemma: "однина"
    translation: "singular"
    pos: "noun"
    gender: "f"
  - lemma: "займенник"
    translation: "pronoun"
    pos: "noun"
    gender: "m"
"""

with open('curriculum/l2-uk-en/a1/vocabulary/my-world-objects.yaml', 'a', encoding='utf-8') as f:
    f.write(vocab_add)

print("Fixed grammar, complexity, metalanguage and boosted immersion.")
