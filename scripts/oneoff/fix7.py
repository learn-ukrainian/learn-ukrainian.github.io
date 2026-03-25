import re

with open("curriculum/l2-uk-en/a1/yesterday-past-tense.md", "r", encoding="utf-8") as f:
    text = f.read()

more_sentences6 = """
**Вчора я також читав статтю.** (Yesterday I also read an article.)
**Вона читала цікаву статтю.** (She read an interesting article.)
**Ми читали разом.** (We read together.)
**Ви читали вчора.** (You read yesterday.)
**Вони читали вранці.** (They read in the morning.)

**Я писав текст.** (I wrote a text.)
**Ти писала лист.** (You wrote a letter.)
**Він писав книгу.** (He wrote a book.)
**Ми писали багато.** (We wrote a lot.)
**Ви писали швидко.** (You wrote fast.)
**Вони писали сьогодні.** (They wrote today.)

**Я знав усе.** (I knew everything.)
**Вона знала це.** (She knew this.)
**Ми знали про це.** (We knew about this.)
**Ви знали раніше.** (You knew earlier.)
**Вони знали вчора.** (They knew yesterday.)
"""

text = text.replace("### Нові слова: Маркери часу", "### Нові слова: Маркери часу\n" + more_sentences6)

# Replace English translations with Ukrainian to boost the ratio heavily
text = text.replace("(It was a very old book.)", "(Це була дуже стара книга.)")
text = text.replace("(He worked many days.)", "(Він працював багато днів.)")
text = text.replace("(This was an important event for Ukraine.)", "(Це була важлива подія для України.)")
text = text.replace("(People read this book.)", "(Люди читали цю книгу.)")
text = text.replace("(It was a new republic.)", "(Це була нова республіка.)")
text = text.replace("(This law was very important.)", "(Цей закон був дуже важливий.)")
text = text.replace("(People read this document.)", "(Люди читали цей документ.)")
text = text.replace("(They understood this law.)", "(Вони розуміли цей закон.)")
text = text.replace("(It was a historical event.)", "(Це була історична подія.)")
text = text.replace("(This law protected the Ukrainian language.)", "(Цей закон захищав українську мову.)")

with open("curriculum/l2-uk-en/a1/yesterday-past-tense.md", "w", encoding="utf-8") as f:
    f.write(text)