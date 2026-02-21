
import re

file_path = 'curriculum/l2-uk-en/c1/activities/31-diaspora-ukrainian.yaml'
with open(file_path, 'r') as f:
    content = f.read()

# Replacements for Quiz Prompts
replacements = [
    ('question: Як українська діаспора відреагувала на проголошення Незалежності України у 1991 році\?', 
     'question: Як саме світова українська діаспора відреагувала на історичне проголошення Незалежності України у 1991 році та чи підтримала вона референдум?'),
     
    ('question: Як називається відомий український район у Чикаго \(США\)\?', 
     'question: Як називається відомий історичний український район у місті Чикаго (США), де розташовано багато національних установ, церков та музеїв?')
]

for old, new in replacements:
    content = re.sub(old, new, content)

with open(file_path, 'w') as f:
    f.write(content)
