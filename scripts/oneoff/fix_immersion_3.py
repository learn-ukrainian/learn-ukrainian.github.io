import re

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "r") as f:
    text = f.read()

# Fix the long sentence
text = text.replace(
    "Не використову́йте називни́й відмі́нок після дієслі́в **бу́ти** (у мину́лому чи майбу́тньому ча́сі) або **ста́ти**. Do not use the Nominative case after verbs like **бу́ти** (to be) in the past or future, or **ста́ти** (to become).",
    "Не використову́йте називни́й відмі́нок після «бу́ти» або «ста́ти»!\n> Do not use Nominative after «бу́ти» or «ста́ти»."
)

text = text.replace(
    "> [!tip] Як сказати \"Working as\" (Working \"As\" Someone)\n> Ніко́ли не використову́йте сло́во **як** після дієсло́ва **працюва́ти**. Never use the word **як** after the verb **працюва́ти**. The Instrumental case by itself already contains the meaning of \"as\" or \"in the capacity of.\"",
    "> [!tip] Як сказати \"Working as\"\n> Ніко́ли не використову́йте сло́во **як** після дієсло́ва **працюва́ти**.\n> Never use the word **як** after the verb **працюва́ти**. The Instrumental case by itself already contains the meaning of \"as\"."
)


# Add more text to push past 45%
t7 = """
> **Текст для читання: Моя́ сім'я́ і пла́ни**
> Мій ба́тько — інжене́р, а ма́ма — лі́карка. Вони́ ду́же лю́блять свою́ робо́ту. Мій ста́рший брат — айтіве́ць. Він працю́є в компа́нії. Його́ дружи́на — юри́стка. Я ще студе́нт. Я вчу́ся в університе́ті. Я мрі́ю ста́ти архіте́ктором. Я хо́чу будува́ти нові́ будинки. Моя́ мо́лодша сестра́ ще в шко́лі. Вона́ хо́че бу́ти вчи́телькою. Ми всі ма́ємо рі́зні пла́ни. 

"""

text = text.replace(
    "Understanding this shift is the first major step away from beginner sentence structures.",
    t7 + "Understanding this shift is the first major step away from beginner sentence structures."
)

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "w") as f:
    f.write(text)
