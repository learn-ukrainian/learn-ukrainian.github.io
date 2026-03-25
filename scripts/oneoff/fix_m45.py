import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix dative case
text = text.replace('допомогти мені з комп\'ютером?', 'допомогти? Комп\'ютер не працює.')
text = text.replace('допомогти мені?', 'допомогти?')
text = text.replace('допоможе вам.', 'допоможе.')

# Fix metalanguage
text = text.replace('Займенник (Pronoun)', '(Pronoun)')

# Fix robotic structure "This is..."
text = text.replace('This is a circumstantial block.', 'The barrier here is circumstantial.')
text = text.replace('This is a skill block.', 'The barrier here relates to skill.')
text = text.replace('This is a rule block.', 'The barrier here involves a strict rule.')
text = text.replace('This is strictly about the present moment', 'The verb strictly focuses on the present moment')
text = text.replace('This is a raw statement', 'We use this as a raw statement')
text = text.replace('This is an excellent, respectful way', 'Using this structure provides an excellent, respectful way')

# To increase immersion without breaking the structure, I will translate English paragraphs to Ukrainian and keep English in parentheses or just add Ukrainian paragraphs before English ones.
# Actually, the easiest way to increase immersion safely is to add more Ukrainian examples, or translate the English explanations. 
# But let's check how many words we need. 3666 * 0.35 = 1283. We need ~1000 more Ukrainian words. 
