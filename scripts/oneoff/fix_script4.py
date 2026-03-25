import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-restaurant.md', 'r') as f:
    text = f.read()

# Replace all remaining "It is possible to "
text = text.replace('It is possible to ', 'Guests freely ')
text = text.replace('Guests freely easily ask', 'Guests easily ask')
text = text.replace('Guests freely also directly ask', 'Guests directly ask')
text = text.replace('Guests freely incredibly easily and quickly', 'Guests incredibly easily and quickly')
text = text.replace('Guests freely be simply drinking', 'Guests might be simply drinking')
text = text.replace('Guests freely be slowly sipping', 'Guests might be slowly sipping')
text = text.replace('Guests freely always loudly and proudly', 'Guests loudly and proudly')
text = text.replace('Guests freely obviously also confidently', 'Guests obviously also confidently')

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-restaurant.md', 'w') as f:
    f.write(text)
