import re

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "r", encoding="utf-8") as f:
    text = f.read()

# Replace the stressed vocab list with unstressed one
old_vocab = "**бу́ти, вчи́тель, вчи́телька, дире́ктор, дире́кторка, економі́ст, економі́стка, журналі́ст, журналі́стка, інжене́р, інжене́рка, лі́кар, лі́карка, ме́неджер, ме́неджерка, програмі́ст, програмі́стка, спеціалі́ст, спеціалі́стка, студе́нт, юри́ст, юри́стка, кра́щий.**"
new_vocab = "**бути, вчитель, вчителька, директор, директорка, економіст, економістка, журналіст, журналістка, інженер, інженерка, лікар, лікарка, менеджер, менеджерка, програміст, програмістка, спеціаліст, спеціалістка, студент, юрист, юристка, кращий.**"

text = text.replace(old_vocab, new_vocab)

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "w", encoding="utf-8") as f:
    f.write(text)
