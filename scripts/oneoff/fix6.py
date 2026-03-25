import re

with open("curriculum/l2-uk-en/a1/yesterday-past-tense.md", "r", encoding="utf-8") as f:
    text = f.read()

# Fix pedagogy grammar issues
text = text.replace("В англійській мові слово \"I\" не має роду.", "Англійська не має роду для слова \"I\".")
text = text.replace("Але в українській мові займенник «я» має рід.", "Але українське слово «я» має рід.")
text = text.replace("Якщо ви чоловік, використовуйте закінчення `-в`.", "Ви чоловік? Використовуйте закінчення `-в`.")
text = text.replace("Якщо ви жінка, використовуйте закінчення `-ла`.", "Ви жінка? Використовуйте закінчення `-ла`.")

# Increase immersion
more_sentences5 = """
**Я думав про роботу.** (I thought about work.)
**Вона думала про дім.** (She thought about home.)
**Ми думали про це вчора.** (We thought about this yesterday.)
**Вони думали про нас.** (They thought about us.)
**Я спав дуже довго.** (I slept very long.)
**Ти спала дуже мало.** (You slept very little.)
**Він спав погано.** (He slept poorly.)
**Ми спали добре.** (We slept well.)
**Я дивився новий фільм.** (I watched a new film.)
**Ти дивилася відео.** (You watched a video.)
**Він дивився кіно.** (He watched a movie.)
**Ми дивилися фото.** (We watched photos.)
**Вчора я відпочивав удома.** (Yesterday I rested at home.)
**Вчора вона відпочивала там.** (Yesterday she rested there.)
**Сьогодні ми відпочивали.** (Today we rested.)
"""
text = text.replace("### Дієслова на «-ся»", "### Дієслова на «-ся»\n" + more_sentences5)

# Replace the text
with open("curriculum/l2-uk-en/a1/yesterday-past-tense.md", "w", encoding="utf-8") as f:
    f.write(text)