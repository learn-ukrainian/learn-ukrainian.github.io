import re

with open('curriculum/l2-uk-en/a1/at-the-restaurant.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the Grammar rules issues:
# 1. 'нам' -> Dative case
text = text.replace('нам потрібне дієслово', 'потрібне дієслово')
text = text.replace('нам потрібен майбутній час', 'потрібен майбутній час')

# 2. Subordinate clause markers
text = text.replace('Професіонал, який працює там — це **офіціант**.', 'Там працює професіонал. Це **офіціант**.')
text = text.replace('Ваш кулінарний досвід починається, коли ви читаєте **меню**.', 'Ви читаєте **меню**. Це ваш перший кулінарний досвід.')
text = text.replace('Навіть якщо ви вже ситі, третя страва — це чудовий момент для релаксу.', 'Ви вже ситі. Але третя страва — це чудовий момент для релаксу.')
text = text.replace('Якщо ви платите готівкою, є одна дуже корисна фраза.', 'Ви платите готівкою? Є одна дуже корисна фраза.')
text = text.replace('Коли ви даєте гроші, ви можете сказати', 'Ви даєте гроші і кажете')
text = text.replace('Щоб замовляти їжу правильно, потрібне дієслово **бути**.', 'Ви замовляєте їжу. Для цього потрібне дієслово **бути**.')

# 3. Russicism
text = text.replace('Давайте подивимося', 'Подивіться')

# 4. Immersion is 25.6%. Target is 35-55%. Replace more blocks:
text = text.replace('''When you confidently order food, the food itself becomes the direct object of your action. In Ukrainian grammar, the direct object requires a specific grammatical case to show its role in the sentence. This is known as the Accusative Case, or **Знахідний відмінок**. Whenever an action directly affects an object—like seeing a physical table, reading a printed menu, or having a bowl of soup—that object must be placed in the Accusative Case. For many words, especially masculine nouns ending in a consonant or neuter nouns ending in an «о» or «е», the word beautifully does not change at all. It looks and sounds exactly the same as its basic dictionary form.''',
'''Ви замовляєте їжу. Ця їжа — це прямий об'єкт. В українській граматиці прямий об'єкт має спеціальний відмінок. Це **Знахідний відмінок** (Accusative Case). Дія впливає на об'єкт. Наприклад: ви бачите стіл, ви читаєте меню, ви їсте суп. Цей об'єкт має Знахідний відмінок. Багато слів не змінюють форму. Чоловічий рід і середній рід мають стандартну форму. Вони виглядають і звучать як у словнику. (You order food. This food is a direct object. In Ukrainian grammar, a direct object has a special case. This is the Accusative Case. The action affects the object. For example: you see a table, you read a menu, you eat soup. This object has the Accusative case. Many words do not change form. Masculine and neuter genders have the standard form. They look and sound like in the dictionary.)''')

text = text.replace('''However, there is one absolutely critical grammatical change you must remember to sound natural. If a noun is feminine and ends in the letter «а» in its dictionary form, it must change its ending when it becomes the direct object of your sentence. The letter «а» shifts and changes directly to «у». This is one of the most fundamental structural rules of the Ukrainian language. Therefore, the word for coffee, «кава», becomes «каву» when you order it. The word for pizza, «піца», becomes «піцу». Let us carefully observe more examples of this essential transformation in action.''',
'''Але є одна важлива зміна. Жіночий рід має літеру «а» в кінці. Ця літера змінюється. Вона стає літерою «у». Це дуже важливе правило української мови. Слово «кава» стає словом «каву». Ви кажете «Я буду каву». Слово «піца» стає словом «піцу». Подивіться на таблицю. (But there is one important change. Feminine gender has the letter "a" at the end. This letter changes. It becomes the letter "u". This is a very important rule of the Ukrainian language. The word 'kava' becomes the word 'kavu'. You say "I will have coffee". The word 'pitsa' becomes the word 'pitsu'. Look at the table.)''')

text = text.replace('''There is an incredibly versatile and important verb you will use frequently in this hospitality context: **замовити** (to order). Interestingly, this single, powerful verb smoothly covers two distinct actions that often have different specific words in English. You confidently use «замовити» when you call the restaurant ahead of time to reserve a table for the evening, and you use the exact same verb when you are sitting comfortably at that table and asking the waiter for a specific dish. The surrounding context makes your intention perfectly clear to everyone.''',
'''Дієслово **замовити** (to order) дуже важливе. Це дієслово має дві функції. Ви можете замовити столик на вечір. Також ви можете замовити страву в ресторані. Ви використовуєте одне слово. Контекст завжди зрозумілий. (The verb 'zamovyty' is very important. This verb has two functions. You can order a table for the evening. Also, you can order a dish in a restaurant. You use one word. The context is always clear.)''')

text = text.replace('''The very first interaction you have sets the positive tone for the entire meal. When you first arrive at the establishment, you might need to actively ask for the menu. A wonderfully simple and highly polite way to do this is to use the helpful word «можна», which translates to 'is it possible' or 'may I', followed immediately by the word for menu. Notice carefully how adding «будь ласка» at the end instantly softens the request, making it sound respectful. If you are calling on the telephone beforehand, you will use our key verb to ask for a table for the evening. Review the short dialogue above. It shows a highly typical arrival scenario that you can memorize and use with complete confidence.''',
'''Ваш перший контакт дуже важливий. У ресторані ви просите меню. Ви використовуєте слово «можна» (may I). Потім ви кажете слово «меню». Фраза «будь ласка» робить це прохання дуже ввічливим. Ви також можете замовити столик по телефону. Прочитайте діалог. Це дуже типова ситуація. (Your first contact is very important. In the restaurant, you ask for a menu. You use the word 'mozhna'. Then you say the word 'menu'. The phrase 'bud laska' makes this request very polite. You can also order a table by phone. Read the dialogue. This is a very typical situation.)''')


# More replacements to reach the immersion target
text = text.replace('''When the waiter returns to your table, they will politely ask if you are ready to order. This is the absolute perfect moment to deploy your new grammar skills. You confidently and clearly use the «Я буду» structure we practiced. Notice carefully in the dialogue how the speaker correctly orders water («воду») and coffee («каву») using the required Accusative Case endings, but uses the standard dictionary form for the soup («борщ») and the salad («салат») because they end in solid consonants and do not change. This shows excellent mastery of the rules!''',
'''Офіціант запитує ваше замовлення. Ви використовуєте структуру «Я буду». У діалозі є правильні форми: вода («воду») і кава («каву»). Це Знахідний відмінок. Але борщ («борщ») і салат («салат») мають стандартну форму. Вони не змінюють форму. Це чудова граматика! (The waiter asks for your order. You use the structure "I will be". In the dialogue, there are correct forms: water and coffee. This is the Accusative case. But borshch and salad have the standard form. They do not change form. This is excellent grammar!)''')

text = text.replace('''When the delightful meal is completely over, it is time to politely ask for the bill. The correct, authentic Ukrainian word for the bill is **рахунок**. You simply catch the waiter's attention with a polite nod and clearly say «рахунок, будь ласка». It truly is that easy. You might also hear local people say «оплатити рахунок» when they are getting their wallets ready to make the final transaction.''',
'''Ваша вечеря закінчилася. Ви просите рахунок. Правильне українське слово — це **рахунок**. Ви просто кажете «рахунок, будь ласка». Це дуже легко. Люди також кажуть «оплатити рахунок». (Your dinner has finished. You ask for the bill. The correct Ukrainian word is 'rakhunok'. You simply say "bill, please". It is very easy. People also say "pay the bill".)''')

with open('curriculum/l2-uk-en/a1/at-the-restaurant.md', 'w', encoding='utf-8') as f:
    f.write(text)

print("Replacements done.")
