import re

with open('curriculum/l2-uk-en/a1/body-and-health.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1 & 2
content = content.replace('[Subject]', 'Subject')
content = content.replace('[body part]', 'body part')

# Fix 6
content = content.replace('ме́не', 'мене́')

# Fix 3
content = content.replace('It perfectly captures the concept of being healthy, which in Ukrainian is **здоро́вий** (healthy).', 'It perfectly captures the concept of being healthy.')

# Fix 4 & 5
old_pharmacy = """After seeing the doctor, you will likely need to visit the pharmacy, which is called **апте́ка**. Navigating Ukrainian streets to find one is easy: just look for the illuminated green cross (**зеле́ний хрест**). You might see two types of signs: an **Апте́ка** is a full pharmacy, while an **Апте́чний пункт** is a smaller dispensary kiosk, often located inside a clinic."""

new_pharmacy = """After seeing the doctor, you will likely need to visit the pharmacy. Navigating Ukrainian streets to find one is easy. You might see these signs:
*   **апте́ка** — full pharmacy
*   **зеле́ний хрест** — illuminated green cross
*   **апте́чний пункт** — smaller dispensary kiosk, often located inside a clinic."""

content = content.replace(old_pharmacy, new_pharmacy)

# Fix 7
old_tea = """When you have these symptoms, Ukrainians often turn to home remedies before visiting a clinic. The Ukrainian tradition of **траволікува́ння** (phytotherapy or herbal medicine) is very strong. If you tell a Ukrainian friend «**Мені́ пога́но**», they will immediately suggest drinking tea! The most popular remedies include tea with **мали́на** (raspberry), **кали́на** (viburnum berries), or a large spoonful of **мед** (honey). «**Чай з мали́ною**» is practically the official national cure for a common cold."""

new_tea = """> [!cultural-note]
> When you have these symptoms, Ukrainians often turn to home remedies before visiting a clinic. The Ukrainian tradition of **траволікува́ння** (phytotherapy or herbal medicine) is very strong. If you tell a Ukrainian friend «**Мені́ пога́но**», they will immediately suggest drinking tea! The most popular remedies include tea with **мали́на** (raspberry), **кали́на** (viburnum berries), or a large spoonful of **мед** (honey). «**Чай з мали́ною**» is practically the official national cure for a common cold."""

content = content.replace(old_tea, new_tea)

with open('curriculum/l2-uk-en/a1/body-and-health.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixes applied.")
