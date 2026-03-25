import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/body-and-health.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. 'за рецептом'
text = text.replace('ці антибіотики тільки за рецептом', 'ці антибіотики потребують рецепт')

# 2. Robotic structure: 3 sentences start with 'ви просите...'
text = text.replace('Ви просите ліки від кашлю. Ви просите ліки від болю. Ви просите ліки від температури.', 'Ви просите ліки від кашлю. Також ви берете ліки від болю. Або ви купуєте ліки від температури.')

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/body-and-health.md', 'w', encoding='utf-8') as f:
    f.write(text)

print("Applied fix_module3")
