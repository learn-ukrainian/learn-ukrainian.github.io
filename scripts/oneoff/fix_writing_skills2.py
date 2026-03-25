import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/writing-skills.md', 'r') as f:
    text = f.read()

# 1. Dative 'мові'
text = text.replace('В українській мові цей документ', 'Українською цей документ')

# 2. Dative 'Вам' and 'вам'
text = text.replace('Вам не потрібно знати складні слова.', 'Ви не повинні знати складні слова.')
text = text.replace('Вам треба вивчити три частини.', 'Ви маєте вивчити три частини.')
text = text.replace('вам потрібні матеріали.', 'ви шукаєте матеріали.')

# 3. Subordinate clause ', які в'
text = text.replace('основні поля, які ви побачите в кожній анкеті.', 'основні поля. Ви побачите їх у кожній анкеті.')

# 4. Subordinate clause 'тому що л'
text = text.replace('Але слова різні, тому що люди різні.', 'Але слова різні. Люди різні.')

# 5. Increase immersion
t5_eng = """The standard greeting on a Ukrainian postcard uses a specific and important grammatical construction. You usually say «Привіт з» followed by the name of the city in the Genitive case. This phrase literally translates to "Greetings from..." in English. The preposition «з» is a powerful trigger word that always requires the following noun to take the Genitive case ending. For most masculine cities ending in a consonant, you add an '-а'. For feminine cities ending in '-а', the ending changes to '-и'. Let us look at how the endings of common Ukrainian city names change when placed in this construction."""
t5_ukr = """Стандартне привітання на поштовій листівці має спеціальну граматику. Ви зазвичай пишете «Привіт з» та назву міста. Слово «з» завжди вимагає родового відмінка. Для більшості міст ми додаємо закінчення "-а". Для жіночих міст ми використовуємо закінчення "-и". Розгляньмо, як змінюються назви українських міст. Це дуже просте правило."""
text = text.replace(t5_eng, t5_ukr)

t6_eng = """The gender field on Ukrainian forms has a distinctive structure and often causes confusion for English speakers. In English, you might casually write "male" or "female" as nouns in the gender box. However, Ukrainian formal documents require you to use adjectives to describe your gender. You must write «чоловіча» for masculine or «жіноча» for feminine. Writing the standard noun forms for man or woman is a common beginner mistake. You must remember that you are describing your physical sex («стать»), which is a feminine noun requiring an adjective agreement."""
t6_ukr = """Поле «Стать» в українських анкетах має особливу структуру. Англійською ви пишете іменники "male" або "female". Але українські офіційні документи вимагають прикметників. Ви маєте писати «чоловіча» або «жіноча». Не пишіть слова "чоловік" або "жінка". Ви описуєте стать. Тому потрібен прикметник."""
text = text.replace(t6_eng, t6_ukr)

t7_eng = """On modern forms, your contact information is just as important as your name. You will always be asked for your «телефо́н» (telephone) and «електро́нна по́шта» (email). When dictating your email address to a clerk, you need to know how to pronounce the special symbols. Ukrainians playfully call the @ symbol a «ра́влик» (a little snail) or a «соба́чка» (a little dog). A dot is simply called a «кра́пка»."""
t7_ukr = """Ваші контакти дуже важливі. Вас завжди запитають про «телефон» та «електронну пошту». Ви повинні знати спеціальні символи. Українці називають символ @ «равлик» або «собачка». Крапка — це просто «крапка»."""
text = text.replace(t7_eng, t7_ukr)

# Fix possible remaining issues
text = text.replace('Вам потрібно знати ці слова.', 'Ви повинні знати ці слова.')
text = text.replace('Вам потрібен конве́рт.', 'Ви маєте купити конве́рт.')
text = text.replace('Вам потрібно заповнити анкету.', 'Ви повинні заповнити анкету.')

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/writing-skills.md', 'w') as f:
    f.write(text)

print("Replacement complete.")
