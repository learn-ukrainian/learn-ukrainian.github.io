with open('curriculum/l2-uk-en/a2/being-and-becoming.md', 'r', encoding='utf-8') as f:
    text = f.read()

summary_add = """
> **📝 Ключові слова (Key Words)**
> * **кар'єра** — career
> * **робота** — job/work
> * **майбутнє** — future
> * **ціль** — goal
> * **статус** — status
> * **зміна** — change
> * **результат** — result
> * **процес** — process
> * **успіх** — success
"""

text = text.replace('# Підсумок', summary_add + '\n# Підсумок')

with open('curriculum/l2-uk-en/a2/being-and-becoming.md', 'w', encoding='utf-8') as f:
    f.write(text)
