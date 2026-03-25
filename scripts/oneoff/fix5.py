import re

with open("curriculum/l2-uk-en/a1/yesterday-past-tense.md", "r", encoding="utf-8") as f:
    text = f.read()

# Fix the instrumental case issues
text = text.replace("**Я говорив з ним.** (I spoke with him.)", "**Я говорив там.** (I spoke there.)")
text = text.replace("**Я говорила з нею.** (I spoke with her.)", "**Я говорила тут.** (I spoke here.)")

# Translate English paragraphs into Ukrainian to boost immersion
rules = [
    ("The verb «бу́ти» (to be) is one of the most important verbs you will ever learn. In the present tense, we frequently omit it entirely. We simply say «Я тут» (I am here). But in the past tense, it is strictly required to link ideas and describe states of being.",
     "Дієслово «бу́ти» — дуже важливе. (The verb \"to be\" is very important.) У теперішньому часі ми часто не говоримо його. (In the present tense, we often do not say it.) Ми кажемо: «Я тут». (We say: \"I am here\".) Але в минулому часі воно обов'язкове. (But in the past tense it is mandatory.)"),
    
    ("The past tense stem is «бу-».", "Основа: «бу-»."),
    
    ("How do we handle reflexive verbs in the past tense? Examine the verb «диви́тися» (to watch). The process is logical: we first form the regular past tense, and then we attach the reflexive particle at the very end.",
     "Як працюють дієслова на «-ся»? (How do reflexive verbs work?) Дивіться на дієслово «диви́тися». (Look at the verb \"to watch\".) Спочатку робимо звичайний минулий час. (First we make the regular past tense.) Потім додаємо частку. (Then we add the particle.)"),
     
    ("If the past tense ends in a consonant (like the masculine form), we add `-ся`.", "Для чоловічого роду додаємо `-ся`."),
    ("If the past tense ends in a vowel (like the feminine or plural forms), we add `-лася`, `-лося`, or `-лися`.", "Для інших форм додаємо `-лася`, `-лося`, `-лися`."),
    
    ("Here is the core rule for building the past tense. According to standard Ukrainian grammar, the process is wonderfully simple and consistent. We start with the dictionary form of the verb, which is the infinitive.",
     "Ось головне правило. (Here is the core rule.) Процес дуже простий. (The process is very simple.) Ми починаємо з інфінітива. (We start with the infinitive.)"),
     
    ("Take the highly frequent verb «роби́ти» (to do).\nFirst, we remove the final «-ти». This leaves us with the stem: «роби-».\nNext, we add our past tense suffixes. These endings change based on the gender and the number of the subject.",
     "Візьміть дієслово «роби́ти». (Take the verb \"to do\".)\nМи забираємо «-ти». (We remove \"-ти\".) Залишається основа: «роби-». (The stem remains: \"роби-\".)\nПотім додаємо закінчення. (Then we add endings.) Закінчення залежать від роду і числа. (Endings depend on gender and number.)"),
     
    ("See this agreement in action using two highly frequent verbs: «робити» (to do) and «чита́ти» (to read).\nLook carefully at how the ending shifts depending on who is performing the action.",
     "Дивіться на дієслова «роби́ти» і «чита́ти». (Look at the verbs \"to do\" and \"to read\".)\nЗакінчення змінюються. (The endings change.)"),
     
    ("Now apply the exact same logic to reading. We take the stem «чита-» and add the suffixes.",
     "Тепер дієслово «чита́ти». (Now the verb \"to read\".) Ми беремо основу «чита-». (We take the stem \"чита-\".)"),
     
    ("This specific point is where many learners face a significant challenge. When you use the word \"I\" in English, it carries no grammatical gender. A man and a woman both say \"I read.\" However, in Ukrainian, the pronoun «я» (I) takes on the physical gender of the speaker.",
     "В англійській мові слово \"I\" не має роду. (In English, the word \"I\" has no gender.) Чоловік і жінка кажуть: \"I read\". (A man and a woman say: \"I read\".) Але в українській мові займенник «я» має рід. (But in Ukrainian, the pronoun \"я\" has gender.)"),
     
    ("If you are a man, you must use the masculine ending `-в`.", "Якщо ви чоловік, використовуйте закінчення `-в`."),
    ("If you are a woman, you must use the feminine ending `-ла`.", "Якщо ви жінка, використовуйте закінчення `-ла`."),
    
    ("The exact same rule applies when you are asking someone a question using «ти» (you). You must look at the person you are speaking to and choose the ending based on their gender.",
     "Це правило також працює для слова «ти». (This rule also works for the word \"you\".) Вибирайте закінчення правильно. (Choose the ending correctly.)")
]

for old, new in rules:
    text = text.replace(old, new)

with open("curriculum/l2-uk-en/a1/yesterday-past-tense.md", "w", encoding="utf-8") as f:
    f.write(text)