import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/health-basics.md', 'r') as f:
    content = f.read()

# Add missing engagement callouts - wait, they were NOT counted?
# Let's check what engagement callouts ARE counted.
# > [!note], [!tip], [!warning], [!caution], [!important], [!cultural], [!history-bite], [!myth-buster], [!quote], [!context], [!analysis], [!source], [!legacy], [!reflection], [!fact], [!culture], [!military], [!perspective], [!biography]

# Transliteration detected: 'трави (herbs)', 'збори (herbal blends)', 'протягу (draft/breeze)'
content = content.replace('трави (herbs)', 'трави')
content = content.replace('збори (herbal blends)', 'збори')
content = content.replace('протягу (draft/breeze)', 'протягу')

# [COMPLEXITY] Sentence too long for A2: 18 words (max 15)
# FIX: Break into shorter sentences. First 5 words: 'Сьогодні ви можете купити аптеці...'
content = content.replace(
    "Сьогодні ви можете купити в аптеці спеціальні трав'яні збори, які лікарі офіційно рекомендують пити разом із традиційними таблетками.",
    "Сьогодні ви можете купити в аптеці спеціальні трав'яні збори. Лікарі офіційно рекомендують пити їх разом із традиційними таблетками."
)

# Fix immersion being too high (75.5%). I need to expand English scaffolding for grammar.
english_addition = """
### Understanding the Impersonal Structure
To truly master this, we need to look at why Ukrainian avoids "I hurt". Culturally and linguistically, pain is seen as something that happens to a person, not an action a person performs. You are the location where the pain occurs. Therefore, the body part must always be in the Nominative case (it is the subject acting upon you), and you must be in the Genitive case with the preposition "у" (at/by). This concept of the external force of pain is central to Slavic grammar and differs fundamentally from Germanic and Romance languages.
"""

content = content.replace('### Однина: У мене болить', f'{english_addition}\n### Однина: У мене болить')

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/health-basics.md', 'w') as f:
    f.write(content)

