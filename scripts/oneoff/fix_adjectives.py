import sys

file_path = "curriculum/l2-uk-en/a1/adjective-case-forms.md"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    ("This beautiful harmony is called gender-case agreement. In this module, we will explore exactly how to change adjective endings in the Accusative and Locative cases.",
     "This beautiful harmony is called gender-case agreement. Adjective endings change systematically in the Accusative and Locative cases.\n\n> [!tip] Dictionary Form\n> When you look up an adjective in a dictionary, it will always be listed in its masculine Nominative form (like **новий**). From there, you can adapt it to any gender and case!"),
    ("Saying something like *у новий місто* is a typical error.",
     "Saying something like *у новий парку* is a typical error."),
    ("- Я купую (новий) машину. → Я купую **нову** машину. (Accusative feminine)\n- Ми гуляємо у (великий) парку. → Ми гуляємо у **великому** парку. (Locative masculine)\n- Я знаю (молодий) чоловіка. → Я знаю **молодого** чоловіка. (Accusative animate masculine)\n- Вона живе в (український) місті. → Вона живе в **українському** місті. (Locative neuter)\n- Я п'ю (смачний) каву. → Я п'ю **смачну** каву. (Accusative feminine)\n- Це лежить у (старий) книзі. → Це лежить у **старій** книзі. (Locative feminine)",
     "- Я купую (нова) машину. → Я купую **нову** машину. (Accusative feminine)\n- Ми гуляємо у (великий) парку. → Ми гуляємо у **великому** парку. (Locative masculine)\n- Я знаю (молодий) чоловіка. → Я знаю **молодого** чоловіка. (Accusative animate masculine)\n- Ми живемо в (українське) місті. → Ми живемо в **українському** місті. (Locative neuter)\n- Я п'ю (смачна) каву. → Я п'ю **смачну** каву. (Accusative feminine)\n- Це лежить у (стара) книзі. → Це лежить у **старій** книзі. (Locative feminine)")
]

for old, new in replacements:
    if old not in content:
        print(f"ERROR: Not found: {old[:50]}")
    content = content.replace(old, new)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Replacements done.")
