import re

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "r") as f:
    text = f.read()

# Fix euphony
text = text.replace("працюва́ти в IT", "працюва́ти у сфе́рі IT")
text = text.replace("в IT.", "у IT.")

# Add one more long text to get over 45%
t6 = """
> **Текст для читання: Моя́ кар'є́ра**
> Мене́ зва́ти Ві́ктор. Мені́ три́дцять ро́ків. Коли́ я бу́в мале́ньким, я хоті́в ста́ти космона́втом. Але по́тім я вирі́с і зрозумі́в, що це ду́же скла́дно. Тому́ я пішо́в вчи́тися в університе́т на юри́ста. Я вчи́вся п'ять ро́ків і ста́в хоро́шим спеціалі́стом. Після університету я працюва́в юри́стом у невели́кій компа́нії. 
> Але че́рез три ро́ки я зрозумі́в, що ця робо́та не для ме́не. Я хоті́в працюва́ти з комп'ю́терами. Тому́ я поча́в вчи́ти програмува́ння. Це було́ неле́гко, але ду́же ціка́во. Тепе́р я айтіве́ць. Я працю́ю програмі́стом і створю́ю нові́ програ́ми. Моя́ робо́та ду́же динамі́чна і суча́сна. Моя́ сім'я́ підтри́мує ме́не. Моя́ дружи́на Катери́на — економі́стка, і вона́ теж ду́же лю́бить свою́ профе́сію.

"""

text = text.replace(
    "Whether you are at a dinner party meeting new friends, or in a formal interview discussing your resume, this grammar pattern will be your constant companion.",
    "Whether you are at a dinner party meeting new friends, or in a formal interview discussing your resume, this grammar pattern will be your constant companion.\n\n" + t6
)

# Translate some English blockquotes to Ukrainian
text = text.replace(
    "> [!warning] The Nominative Trap\n> Do not use the Nominative case after verbs like **бу́ти** (to be) in the past or future, or **ста́ти** (to become).",
    "> [!warning] Ува́га: Називни́й відмі́нок (The Nominative Trap)\n> Не використову́йте називни́й відмі́нок після дієслі́в **бу́ти** (у мину́лому чи майбу́тньому ча́сі) або **ста́ти**. Do not use the Nominative case after verbs like **бу́ти** (to be) in the past or future, or **ста́ти** (to become)."
)

text = text.replace(
    "> [!tip] Working \"As\" Someone\n> Never use the word **як** after the verb **працюва́ти**. The Instrumental case by itself already contains the meaning of \"as\" or \"in the capacity of.\"",
    "> [!tip] Як сказати \"Working as\" (Working \"As\" Someone)\n> Ніко́ли не використову́йте сло́во **як** після дієсло́ва **працюва́ти**. Never use the word **як** after the verb **працюва́ти**. The Instrumental case by itself already contains the meaning of \"as\" or \"in the capacity of.\""
)

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "w") as f:
    f.write(text)
