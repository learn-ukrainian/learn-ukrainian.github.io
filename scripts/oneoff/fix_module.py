import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/shopping-and-market.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1 & 2: Дайте, будь ласка, хліб/молоко -> Я беру хліб/молоко
content = content.replace(
    'One of the most useful phrases is **Дайте, будь ласка...** (Give me, please...). You can treat this as a frozen shopping formula.\n- **Дайте, будь ласка, хліб.** (Give me, please, bread.)\n- **Дайте, будь ласка, молоко.** (Give me, please, milk.)',
    'One useful approach is to simply name the item and add please.\n- **Хліб, будь ласка.** (Bread, please.)\n- **Молоко, будь ласка.** (Milk, please.)'
)

# Fix 8 (and text around it): Можна каву -> Я хочу каву
content = content.replace(
    'Sometimes you want to ask "May I...?" or "Can I...?" In this case, use **Можна...?**:\n- **Можна каву, будь ласка?** (May I have a coffee, please?)',
    'Sometimes you want to politely request an item without a verb. In this case, just ask for the item directly:\n- **Каву, будь ласка.** (A coffee, please.)'
)

# Fix 4: Дайте, будь ласка. Скільки коштує?
content = content.replace(
    '> — **Дайте, будь ласка. Скільки коштує?** (Give me, please. How much does it cost?)',
    '> — **Добре. Скільки коштує?** (Good. How much does it cost?)'
)

# Fix 9: сім літрів -> вісім літрів
content = content.replace(
    '- **сім літрів** (seven litres)',
    '- **вісім літрів** (eight litres)'
)

# Fix 5: Дайте, будь ласка, дві пляшки води.
content = content.replace(
    '- **Дайте, будь ласка, дві пляшки води.** (Give me, please, two bottles of water.)',
    '- **Я хочу купити дві пляшки води.** (I want to buy two bottles of water.)'
)

# Fix 6: Дайте, будь ласка, кілограм яблук.
content = content.replace(
    '> — **Дайте, будь ласка, кілограм яблук.** (Give me, please, a kilogram of apples.)',
    '> — **Я хочу купити кілограм яблук.** (I want to buy a kilogram of apples.)'
)

# Fix 7: Give me, please, a bottle of water
content = content.replace(
    '3. How do you say "Give me, please, a bottle of water"?',
    '3. How do you say "I want to buy a bottle of water"?'
)

# Fix 10: Add 1 more callout boxes (> [!tip])
callout = """
> [!cultural-note]
> In Ukraine, you will often be asked if you need a bag (**пакет**). It is very common to bring your own reusable bag to the supermarket!
"""

content = content.replace(
    '## Засоби гігієни (Hygiene Products)',
    callout + '\n## Засоби гігієни (Hygiene Products)'
)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/shopping-and-market.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixes applied.")
