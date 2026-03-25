import re

file_path = '/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/direction-and-origin.md'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix missing periods in callouts and remove inline English
content = content.replace('> **Обережно: Не плутайте «де» і «куди»**', '> **Обережно: Не плутайте «де» і «куди».**')
content = content.replace('> **Зверніть увагу: Збіг закінчень (Coincidence of endings)**', '> **Зверніть увагу: Збіг закінчень.**')
content = content.replace('> **Культура: У гості (Visiting guests)**', '> **Культура: У гості.**')
content = content.replace('> **Підказка: «До» + професії**', '> **Підказка: «До» та професії.**')
content = content.replace('> **Факт: Правила милозвучності (Rules of Euphony)**', '> **Факт: Правила милозвучності.**')

# Fix table header inline English
content = content.replace('Приклад у реченні (Example in context)', 'Приклад у реченні')
content = content.replace('Називний (Nominative - Що?)', 'Називний (Що?)') # Keep minimal grammar
content = content.replace('Знахідний (Accusative - Куди?)', 'Знахідний (Куди?)')
content = content.replace('Рід (Gender)', 'Рід')

# Reduce English / Add Ukrainian for immersion
content = content.replace(
    'When you are static, resting, or simply existing in a place, you use **де** (where at). However, when you are actively moving toward a destination, you must switch your mindset and use **куди** (where to).',
    'Коли ви не рухаєтесь і просто стоїте, ви використовуєте **де**. Але коли ви активно рухаєтеся до мети, ви завжди використовуєте **куди**.'
)
content = content.replace(
    'This is a fundamental, foundational concept in the Ukrainian language.',
    'Це абсолютно фундаментальний концепт в українській мові.'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixes applied.")
