import re

with open('curriculum/l2-uk-en/a1/at-the-restaurant.md', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('''Modern Ukrainian cities are highly progressive and very accommodating to various personal dietary preferences. If you are a vegetarian, the absolute essential phrase you need to know is **без м'яса** (without meat). If you have a gluten intolerance or preference, the phrase **без глютену** (gluten-free) is widely understood and instantly recognized by almost all restaurant staff. Adding the preposition «без» (without) requires the following noun to change its grammatical ending slightly, but for now, you can simply learn these two specific phrases as fixed, highly useful vocabulary blocks that will protect your diet.''',
'''Сучасні українські міста дуже прогресивні. Вони мають багато варіантів для різних дієт. Ви вегетаріанець? Дуже важлива фраза — це **без м'яса** (without meat). Ви не їсте глютен? Фраза **без глютену** (gluten-free) дуже популярна. Офіціанти добре знають ці фрази. Слово «без» (without) змінює закінчення слова. Але зараз ви можете просто запам'ятати ці дві фрази. Вони захистять вашу дієту. (Modern Ukrainian cities are very progressive. They have many options for different diets. Are you a vegetarian? A very important phrase is 'bez miasa'. You don't eat gluten? The phrase 'bez hlutenu' is very popular. Waiters know these phrases well. The word 'without' changes the ending of the word. But now you can just remember these two phrases. They will protect your diet.)''')

text = text.replace('''Sometimes the written menu description is simply not enough, and you need more specific details before confidently committing to an order. You might deeply want to know the exact ingredients, especially if you have sensitive allergies. Asking «З чого це?» (What is this made from?) is a fantastic start. If you are highly sensitive to strong spices, asking if something is spicy («гостре») can save you from an uncomfortable surprise. Furthermore, asking the waiter for their personal recommendation is always a wonderful, engaging way to discover excellent local dishes you might have otherwise ignored.''',
'''Іноді тексту в меню недостатньо. Ви хочете знати інгредієнти. Можливо, у вас є алергія. Запитання «Із чого ця страва?» (What is this made from?) — це чудовий старт. Ви не любите гостру їжу? Запитайте «Це гостре?» (Is this spicy?). Також ви можете запитати: «Що ви рекомендуєте?». Це гарний спосіб знайти чудові місцеві страви. (Sometimes the text in the menu is not enough. You want to know the ingredients. Maybe you have an allergy. The question "From what is this dish?" is a great start. You don't like spicy food? Ask "Is this spicy?". Also you can ask: "What do you recommend?". This is a good way to find great local dishes.)''')


with open('curriculum/l2-uk-en/a1/at-the-restaurant.md', 'w', encoding='utf-8') as f:
    f.write(text)

print("Replacements done.")
