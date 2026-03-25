import re

md_file = 'curriculum/l2-uk-en/a1/imperative-and-requests.md'
yaml_file = 'curriculum/l2-uk-en/a1/activities/imperative-and-requests.yaml'

with open(md_file, 'r') as f:
    content = f.read()

content = content.replace(
"- **Будь ласка, допоможіть.** — Please help.",
"- **Будь ласка, скажіть це.** — Please say this."
)

content = content.replace("Наприклад (For example):", "Наприклад:")
content = content.replace("Порівняйте (Compare):", "Порівняйте:")

content = content.replace(
"We will look at how to form these specific commands step by step.",
"Ми розглянемо, як утворювати ці команди (We will look at how to form these specific commands) step by step."
)

content = content.replace(
"Then, you remove the infinitive ending from the end of the word.",
"Потім ви забираєте закінчення інфінітива (Then, you remove the infinitive ending) from the end of the word."
)

content = content.replace(
"Finally, you add the correct imperative ending depending on the consonant or vowel at the end of the verb stem.",
"Нарешті, ви додаєте правильне закінчення (Finally, you add the correct imperative ending) depending on the consonant or vowel at the end of the verb stem."
)

content = content.replace(
"Let us look at the fundamental pattern for forming informal commands.",
"Давайте подивимося на основне правило (Let us look at the fundamental pattern) for forming informal commands."
)

content = content.replace(
"Now, consider the formal or plural form, which is incredibly important for social interactions.",
"Тепер розглянемо формальну або множинну форму (Now, consider the formal or plural form), which is incredibly important for social interactions."
)

content = content.replace(
"To create this polite command, you take the informal command and simply add a specific plural ending to it.",
"Щоб створити цю ввічливу команду (To create this polite command), you take the informal command and simply add a specific plural ending to it."
)

content = content.replace(
"It is absolutely crucial to understand that mixing these forms is a common mistake for language learners when they first begin.",
"Дуже важливо розуміти (It is absolutely crucial to understand) that mixing these forms is a common mistake for language learners when they first begin."
)

content = content.replace(
"Using the formal ending demonstrates respect and significant cultural awareness.",
"Використання формального закінчення демонструє повагу (Using the formal ending demonstrates respect) and significant cultural awareness."
)

with open(md_file, 'w') as f:
    f.write(content)

with open(yaml_file, 'r') as f:
    yaml_content = f.read()

yaml_content = yaml_content.replace('question: Translate "Please give."', 'question: What is the correct translation for "Please give."?')
yaml_content = yaml_content.replace('question: Translate "Do not read."', 'question: What is the correct translation for "Do not read."?')
yaml_content = yaml_content.replace('question: Translate "Wait here, please."', 'question: What is the correct translation for "Wait here, please."?')
yaml_content = yaml_content.replace('question: Translate "Please look."', 'question: What is the correct translation for "Please look."?')
yaml_content = yaml_content.replace('question: Translate "Say this word."', 'question: What is the correct translation for "Say this word."?')
yaml_content = yaml_content.replace('question: Translate "Do not stand here."', 'question: What is the correct translation for "Do not stand here."?')
yaml_content = yaml_content.replace('question: Translate "Listen to this, please."', 'question: What is the correct translation for "Listen to this, please."?')
yaml_content = yaml_content.replace('question: Translate "Go there."', 'question: What is the correct translation for "Go there."?')

with open(yaml_file, 'w') as f:
    f.write(yaml_content)
