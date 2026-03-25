import re

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "r") as f:
    content = f.read()

# Fix the complexity violation
content = content.replace("> **📖 Чита́ння: Студе́нти та майбу́тнє**", "> **📖 Чита́ння: Студе́нти**")
content = content.replace("Університе́ти Украї́ни ма́ють бага́то таланови́тих студе́нтів.", "В Украї́ні є́ бага́то студе́нтів.")

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "w") as f:
    f.write(content)
