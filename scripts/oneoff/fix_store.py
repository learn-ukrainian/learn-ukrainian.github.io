import re

with open('curriculum/l2-uk-en/a1/at-the-store.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix heading level
content = content.replace('## Підсумок', '# Підсумок')

# Fix 'Нам потрібно' / 'Нам також треба' / 'допомагає вам'
content = content.replace('Нам потрібно знати правильні слова. Нам також треба розуміти питання на касі. Цей урок допомагає вам робити закупи самостійно. Коли ви живете в Україні, ви часто ходите в магазин.', 'Ми маємо знати правильні слова. Ми також маємо розуміти питання на касі. Цей урок допомагає робити закупи самостійно. Ви живете в Україні і часто ходите в магазин.')
content = content.replace('We need to know the right words. We also need to understand questions at the checkout. This lesson helps you do your shopping independently. When you live in Ukraine, you frequently go to the store.', 'We have to know the right words. We also have to understand questions at the checkout. This lesson helps to do your shopping independently. You live in Ukraine and frequently go to the store.')

# Fix 'Коли ми заходимо в супермаркет'
content = content.replace('Коли ми заходимо в супермаркет, ми бачимо різні зони. Це — відділи. Кожен відділ має свою назву. Нам потрібно знати ці назви, щоб знайти продукти. Давайте подивимося на основні відділи супермаркету.', 'Ми заходимо в супермаркет. Ми бачимо різні зони. Це — відділи. Кожен відділ має свою назву. Ми маємо знати ці назви. Вони допомагають знайти продукти. Подивімося на основні відділи супермаркету.')
content = content.replace('When we enter a supermarket, we see different zones. These are the departments. Each department has its own name. We need to know these names to find groceries. Let\'s look at the main departments of a supermarket.', 'We enter a supermarket. We see different zones. These are the departments. Each department has its own name. We must know these names. They help to find groceries. Let\'s look at the main departments of a supermarket.')

# Fix departments list (inline English, robotic structure)
content = content.replace('- **Моло́чний ві́дділ** (Dairy department). Тут ми купуємо молоко, сир та сметану. (Here we buy milk, cheese, and sour cream.)', '- **Моло́чний ві́дділ**. У цьому відділі ми купуємо молоко, сир та сметану. (Here we buy milk, cheese, and sour cream.)')
content = content.replace('- **М\'ясни́й ві́дділ** (Meat department). Тут є свіже м\'ясо та ковбаса. (Here there is fresh meat and sausage.)', '- **М\'ясни́й ві́дділ**. Тут є свіже м\'ясо та ковбаса. (Here there is fresh meat and sausage.)')
content = content.replace('- **Хлі́бний ві́дділ** (Bakery department). Тут ми беремо свіжий хліб. (Here we take fresh bread.)', '- **Хлі́бний ві́дділ**. Там ми беремо свіжий хліб. (There we take fresh bread.)')
content = content.replace('- **Конди́терський ві́дділ** (Confectionery department). Тут ми бачимо цукерки та торти. (Here we see candies and cakes.)', '- **Конди́терський ві́дділ**. У цій зоні лежать цукерки та торти. (In this zone lie candies and cakes.)')
content = content.replace('- **Відділ овочів та фруктів** (Produce department). Тут ми знаходимо свіжі овочі. (Here we find fresh vegetables.)', '- **Відділ овочів та фруктів**. Ми знаходимо там свіжі овочі. (We find fresh vegetables there.)')

# Fix 'Щоб запитати', 'У якому відділі' -> 'В якому відділі'
content = content.replace('Щоб запитати про місце, ми використовуємо місцевий відмінок. Ми питаємо: «У якому відділі?».', 'Ми використовуємо місцевий відмінок для місця. Ми питаємо: «В якому відділі?».')
content = content.replace('To ask about a location, we use the Locative case. We ask: «У якому відділі?» (In which department?).', 'We use the Locative case for a location. We ask: «В якому відділі?» (In which department?).')
content = content.replace('У якому відділі вода?', 'В якому відділі вода?')
content = content.replace('У якому відділі сир?', 'В якому відділі сир?')

# Fix 'Коли ми купуємо товар', 'В українській мові ми'
content = content.replace('Коли ми купуємо товар, ми робимо дію. Цей товар — це об\'єкт нашої дії. В українській мові ми використовуємо знахідний відмінок для об\'єкта. Форма слова змінюється.', 'Ми купуємо товар. Ми робимо дію. Цей товар — це об\'єкт нашої дії. Ми використовуємо знахідний відмінок для об\'єкта. Форма слова змінюється.')
content = content.replace('When we buy a product, we are performing an action. This product is the object of our action. In the Ukrainian language, we use the Accusative case for the direct object. The form of the word changes.', 'We buy a product. We perform an action. This product is the object of our action. We use the Accusative case for the direct object. The form of the word changes.')

# Fix 'Коли ми рухаємося' / 'Нам треба'
content = content.replace('Коли ми рухаємося, ми використовуємо один відмінок. Коли ми стоїмо на місці, ми використовуємо інший відмінок. Нам треба бути уважними.', 'Ми рухаємося і використовуємо один відмінок. Ми стоїмо на місці і використовуємо інший відмінок. Ми маємо бути уважними.')
content = content.replace('When we are moving, we use one case. When we are standing in place, we use another case. We need to be careful.', 'We are moving and we use one case. We are standing in place and we use another case. We have to be careful.')

# Fix 'під впливом'
content = content.replace('Ми маємо використовувати правильні українські слова. Деякі люди роблять помилки під впливом інших мов. Ми вчимося говорити чисто та природно.', 'Ми маємо використовувати правильні українські слова. Деякі люди роблять помилки. Ми вчимося говорити чисто та природно.')

# Fix 'В українській мові слова мають'
content = content.replace('В українській мові слова мають рід.', 'Слова мають рід.')

# Fix 'Incorrect Over-correction'
content = content.replace('Incorrect Over-correction:', 'Типова помилка:')

# Fix 'Коли ми заходимо в супермаркет, нам потрібен кошик'
content = content.replace('Коли ми заходимо в супермаркет, нам потрібен кошик або візок. Ми шукаємо їх біля входу.', 'Ми заходимо в супермаркет. Ми беремо кошик або візок. Ми шукаємо їх біля входу.')
content = content.replace('When we enter the supermarket, we need a basket or a cart. We look for them near the entrance.', 'We enter the supermarket. We take a basket or a cart. We look for them near the entrance.')

# Fix 'Вам потрібно знайти'
content = content.replace('Вам потрібно знайти товари й запитати про їхню ціну.', 'Ви маєте знайти товари й запитати про їхню ціну.')
content = content.replace('You need to find products and ask about their price.', 'You have to find products and ask about their price.')

# Fix 'яка ціна за кілограм' -> 'Яка ціна'
content = content.replace('- **Ви:** Скажіть, будь ласка, яка ціна за кілограм?', '- **Ви:** Яка ціна за кілограм?')
content = content.replace('- **You:** Tell me, please, what is the price per kilogram?', '- **You:** What is the price per kilogram?')

# Fix 'Ви бачите, що є вільна каса'
content = content.replace('Ви бачите, що є вільна каса.', 'Ви бачите вільну касу.')
content = content.replace('You see that there is an open checkout.', 'You see an open checkout.')

# Fix 'Вам також може знадобитися чек' -> 'Ви також можете взяти чек.'
content = content.replace('Вам також може знадобитися чек.', 'Ви також можете взяти чек.')
content = content.replace('You might also need a receipt.', 'You might also take a receipt.')

# Fix 'Мені потрібен цей чек.' -> 'Я забираю цей чек.'
content = content.replace('- **Ви:** Дякую. Чек, будь ласка. Мені потрібен цей чек.', '- **Ви:** Дякую. Чек, будь ласка. Я забираю цей чек.')
content = content.replace('- **You:** Thank you. Receipt, please. I need this receipt.', '- **You:** Thank you. Receipt, please. I am taking this receipt.')

# Fix 'Не бійтеся говорити, навіть якщо ви робите невелику помилку. Українці дуже підтримують іноземців, які намагаються говорити їхньою мовою.'
content = content.replace('Не бійтеся говорити, навіть якщо ви робите невелику помилку. Українці дуже підтримують іноземців, які намагаються говорити їхньою мовою.', 'Не бійтеся говорити. Українці дуже підтримують іноземців. Вони допомагають говорити їхньою мовою.')
content = content.replace('Do not be afraid to speak, even if you make a small mistake. Ukrainians are very supportive of foreigners who try to speak their language.', 'Do not be afraid to speak. Ukrainians are very supportive of foreigners. They help to speak their language.')

with open('curriculum/l2-uk-en/a1/at-the-store.md', 'w', encoding='utf-8') as f:
    f.write(content)
