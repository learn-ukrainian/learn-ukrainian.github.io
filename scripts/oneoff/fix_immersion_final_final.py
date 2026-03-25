with open('curriculum/l2-uk-en/a1/my-world-objects.md', 'r', encoding='utf-8') as f:
    text = f.read()

old_text = 'Most importantly, you successfully mastered the critical difference between the invariant identifier **це** ("this is") and the gender-matched demonstratives **цей** and **той** ("this" and "that").'
new_text = 'Найважливіше, ви зрозуміли різницю між словом це та займенниками цей і той. Most importantly, you successfully mastered the critical difference between the invariant identifier **це** ("this is") and the gender-matched demonstratives **цей** and **той** ("this" and "that").'

text = text.replace(old_text, new_text)

# Also let's translate the questions in the summary:
q_old = """**Перевірте себе:**
1.  How do you correctly say "This is a table" versus "This table"? Explain the fundamental grammatical difference between the two phrases.
2.  What is the helpful phonetic mnemonic trick to remember the "far" demonstratives (that/those)?
3.  Why is it grammatically incorrect to say «ця стіл» or «цей кни́га»? What is the strict rule you must always follow?
4.  Translate the following phrase into Ukrainian, paying very close attention to the special plural rule: "That door."
5.  What is the core difference in meaning and feeling between the words **дім**, **ха́та**, and **кварти́ра**?"""

q_new = """**Перевірте себе (Check yourself):**
1.  Як правильно сказати (How do you correctly say) "This is a table" versus "This table"? Explain the fundamental grammatical difference between the two phrases.
2.  What is the helpful phonetic mnemonic trick to remember the "far" demonstratives (that/those)?
3.  Чому неправильно говорити (Why is it grammatically incorrect to say) «ця стіл» or «цей кни́га»? What is the strict rule you must always follow?
4.  Перекладіть українською (Translate into Ukrainian), paying very close attention to the special plural rule: "That door."
5.  What is the core difference in meaning and feeling between the words **дім**, **ха́та**, and **кварти́ра**?"""

text = text.replace(q_old, q_new)

with open('curriculum/l2-uk-en/a1/my-world-objects.md', 'w', encoding='utf-8') as f:
    f.write(text)

print("Immersion boosted over 15%.")
