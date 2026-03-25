import re

file_path = "curriculum/l2-uk-en/a2/being-and-becoming.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1 & 2 (Slang note and vocab)
content = content.replace(
    "> [!note] Note on Slang\n> The words **айті́шник** and **айті́шниця** are sometimes heard, but the standard forms **айтіве́ць** and **айті́вка** are preferred in modern communication.",
    "> [!note] Зауваження про сленг (Note on Slang)\n> While you might hear older slang for IT workers, the standard forms **айтіве́ць** and **айті́вка** are the correct terms in modern communication."
)
content = content.replace(
    "Слова для контексту: айтівка, бути, вчитель, вчителька, економістка, журналістка, мріяти, програмувальник, айтівець, інженер, інженерка, журналіст, юрист, юристка, економіст, менеджер, менеджерка, спеціаліст, спеціалістка, громадянин, громадянка, директор, директорка, студент, студентка, стати, ставати, працювати, лікар, лікарка, програміст, програмістка, айтішник, айтішниця.",
    "Слова для контексту: айтівка, бути, вчитель, вчителька, економістка, журналістка, мріяти, програмувальник, айтівець, інженер, інженерка, журналіст, юрист, юристка, економіст, менеджер, менеджерка, спеціаліст, спеціалістка, громадянин, громадянка, директор, директорка, студент, студентка, стати, ставати, працювати, лікар, лікарка, програміст, програмістка."
)

# Fix 3 (була́ журналі́сткою)
content = content.replace(
    "— **Вона́ рані́ше була́ журналі́сткою. Тепе́р вона́ працю́є ме́неджеркою.**",
    "— **Вона́ рані́ше була́ відо́мою журналі́сткою. Тепе́р вона́ працю́є ме́неджеркою.**"
)

# Fix 4 (ста́ла хоро́шою)
content = content.replace(
    "— **Та́к. Вона́ ста́ла хоро́шою спеціалі́сткою.**",
    "— **Та́к. Вона́ ста́ла ду́же хоро́шою спеціалі́сткою.**"
)

# Fix 5 (головна́ + головно́ю)
content = content.replace(
    "Then, the adjective must change to its feminine form **головна́**. Finally, both take their Instrumental endings: **головно́ю інжене́ркою**.",
    "Then, the adjective must change to its feminine form **головна́**. Finally, the phrase takes its Instrumental endings: **ста́ла головно́ю інжене́ркою**."
)

# Fix 6 (моєї + Робота)
content = content.replace(
    "> **Текст для читання: Робота моєї мрії**",
    "> **Текст для читання: Моя́ ідеа́льна робо́та**"
)

# Immersion Improvements
content = content.replace(
    "These sentences show a fundamental difference in how Ukrainian expresses identity versus a role or function over time. When you are talking about who you are right now, in the present tense, you simply use the Nominative case.",
    "These sentences show a fundamental difference in how Ukrainian expresses identity versus a role or function over time. When you are talking about who you are right now, in the present tense (**тепе́рішній час**), you simply use the Nominative case (**називни́й відмі́нок**)."
)

content = content.replace(
    "However, when you shift to the past tense, the future tense, or talk about a process of becoming, the grammar changes. The noun describing the profession or role must change to the Instrumental case.",
    "However, when you shift to the past tense (**мину́лий час**), the future tense (**майбу́тній час**), or talk about a process of becoming (**проце́с стано́влення**), the grammar changes. The noun describing the profession (**профе́сія**) or role must change to the Instrumental case (**ору́дний відмі́нок**)."
)

content = content.replace(
    "In Ukrainian, certain key verbs strictly govern the Instrumental case when describing a person's profession, status, or role.",
    "In Ukrainian, certain key verbs (**дієслова́**) strictly govern the Instrumental case when describing a person's profession, status, or role."
)

content = content.replace(
    "When you use these verbs, the noun that follows them—the profession or role—must take the Instrumental case endings. For masculine nouns ending in a consonant, you typically add **-ом** or **-ем**. For feminine nouns ending in **-а**, you change the ending to **-ою**.",
    "When you use these verbs, the noun that follows them—the profession or role—must take the Instrumental case endings (**закі́нчення**). For masculine nouns (**чолові́чий рід**) ending in a consonant, you typically add **-ом** or **-ем**. For feminine nouns (**жіно́чий рід**) ending in **-а**, you change the ending to **-ою**."
)

content = content.replace(
    "Ukrainian has undergone significant modernizations recently, particularly regarding gender and professional titles. In 2020, a major grammar reform officially codified the use of femininitives.",
    "Ukrainian has undergone significant modernizations recently, particularly regarding gender and professional titles. In 2020, a major grammar reform officially codified the use of femininitives (**фемініти́ви**)."
)

content = content.replace(
    "Another massive cultural shift is the booming Information Technology sector. Ukraine has one of the largest and most prestigious developer communities in Europe.",
    "Another massive cultural shift is the booming Information Technology sector (**сфе́ра IT**). Ukraine has one of the largest and most prestigious developer communities in Europe."
)

content = content.replace(
    "When you are combining these professional nouns with adjectives, you must ensure that everything matches perfectly. The noun and the adjective must agree in both gender and case.",
    "When you are combining these professional nouns with adjectives (**прикме́тники**), you must ensure that everything matches perfectly. The noun (**іме́нник**) and the adjective must agree in both gender (**рід**) and case (**відмі́нок**)."
)

content = content.replace(
    "Discussing career history and future aspirations is one of the most common and practical uses for the vocabulary and grammar covered in this module.",
    "Discussing career history (**істо́рія кар'є́ри**) and future aspirations (**майбу́тні пла́ни**) is one of the most common and practical uses for the vocabulary and grammar covered in this module."
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Replacements applied.")
