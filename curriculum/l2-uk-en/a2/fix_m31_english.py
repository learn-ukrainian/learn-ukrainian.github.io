import re

md_file = '/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/in-order-to.md'

with open(md_file, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    # Fix sentence length
    "Коли ви будете святкувати якусь подію в теплій українській компанії, обов'язково спробуйте впевнено сказати цей тост — ви гарантовано здивуєте і порадуєте своїх нових друзів!": "Ви святкуєте подію в теплій компанії. Обов'язково скажіть цей тост друзям!",
    
    # Fix Metalanguage
    "Для + Іменник": "Для + Noun",
    "Використовуємо Іменник": "Використовуємо Noun",
    "Родовий відмінок": "Genitive Case",
    
    # Lower immersion by translating more paragraphs into English
    "Ми постійно щось плануємо у нашому щоденному житті. Кожного ранку ми прокидаємося з певним наміром. Ми ходимо на роботу або в університет. Ми уважно читаємо складні книги. Ми подорожуємо до нових країн. Але чому саме ми все це робимо? Кожна наша свідома дія має певну конкретну мету.": "We are constantly planning something in our daily lives. Every morning we wake up with a certain intention. We go to work or university. We carefully read complex books. We travel to new countries. But why exactly do we do all this? Every conscious action of ours has a specific concrete goal.",
    
    "Давайте розберемо це речення на деталі. У цьому прикладі головна частина нашого речення — це незалежна фраза «Ми вчимо українську мову». Залежна частина, яка пояснює нашу фінальну мету — це фраза «щоб розмовляти з друзями». Як ви можете чітко бачити, наше чарівне слово «щоб» стоїть точно посередині. Воно працює як надійний міст між дією та її результатом.": "Let's break this sentence down into details. In this example, the main part of our sentence is the independent phrase «Ми вчимо українську мову». The dependent part, which explains our final goal, is the phrase «щоб розмовляти з друзями». As you can clearly see, our magic word «щоб» stands exactly in the middle. It acts as a reliable bridge between the action and its result.",
    
    "Ця маленька кома робить ваш текст справді грамотним, дорослим і природним. Ви пишете повідомлення вашому українському другу. Або складаєте офіційний лист для колеги. Правильна пунктуація відразу показує ваш рівень. Українці завжди звертають увагу на такі деталі, і вони високо оцінять вашу грамотність.": "This little comma makes your text truly literate, mature, and natural. You write a message to your Ukrainian friend. Or you compose an official letter for a colleague. Proper punctuation immediately shows your level. Ukrainians always pay attention to such details, and they will highly appreciate your literacy.",
    
    "Коли ми щодня говоримо про мету, ми насправді говоримо про інтенціональність. Це філософське поняття означає, що ваша дія має чіткий напрямок у майбутнє. Ваша головна дія могла відбутися в минулому часі («Я купив квиток»). Але мета завжди спрярована у майбутнє.": "When we talk about purpose every day, we are actually talking about intentionality. This philosophical concept means that your action has a clear direction into the future. Your main action could have taken place in the past tense («Я купив квиток»). But the purpose is always directed into the future.",
    
    "Найчастіше в нашому житті ми робимо щось саме для себе. Ми ставимо цілі і самі їх досягаємо. Я зараз активно працюю, щоб я мав гроші на відпустку. Вона багато читає нові книги, щоб вона знала більше цікавих фактів. Ми тренуємося, щоб ми були здоровими.": "Most often in our lives, we do something specifically for ourselves. We set goals and achieve them ourselves. I am actively working now so that I have money for vacation. She reads many new books so that she knows more interesting facts. We train so that we are healthy.",
    
    "Ця проста схема — ваш найкращий друг і надійний навігатор. Вона допоможе вам завжди, без жодних сумнівів, обирати правильну форму українського дієслова.": "This simple diagram is your best friend and reliable navigator. It will help you always, without any doubts, choose the correct form of the Ukrainian verb.",
    
    "Розглянемо правильні приклади використання слова «для»:": "Let's look at the correct examples of using the word «для»:",
    
    "Зверніть особливу увагу: після слова «для» завжди стоїть об'єкт («тебе», «роботи», «здоров'я»). Ви можете хотіти сказати про *дію* для виконання. Тоді ви зобов'язані використати сполучник «щоб» з дієсловом.": "Pay special attention: after the word «для» there is always an object («тебе», «роботи», «здоров'я»). You might want to talk about an *action* to be performed. Then you are obligated to use the conjunction «щоб» with a verb.",
    
    "Давайте уважно подивимося на ці дві різні конструкції поруч. Це допоможе вам назавжди закріпити цю критичну різницю у вашій пам'яті.": "Let's carefully look at these two different constructions side by side. This will help you forever consolidate this critical difference in your memory.",
    
    "Обидва варіанти з таблиці є абсолютно правильними, але вони використовують абсолютно різні граматичні інструменти. Завжди обирайте той варіант, який краще і точніше підходить для вираження вашої думки!": "Both variants from the table are absolutely correct, but they use completely different grammatical tools. Always choose the variant that better and more accurately suits expressing your thought!",
    
    "А тепер ми переходимо до найцікавішої і найтоншої частини української граматики. Що робити, якщо я маю план, але я хочу, щоб *хтось інший* його реалізував? Я маю велике бажання, але діяти буде інша людина. В українській мові для такої ситуації існує спеціальний, унікальний граматичний механізм.": "And now we move on to the most interesting and subtle part of Ukrainian grammar. What to do if I have a plan, but I want *someone else* to implement it? I have a great desire, but another person will act. In the Ukrainian language, there is a special, unique grammatical mechanism for such a situation.",
    
    "Давайте подивимося, як ця дивовижна логіка працює на живій практиці. Зверніть максимальну увагу на зміну особи. Також пам'ятайте про обов'язкове використання форми минулого часу:": "Let's see how this amazing logic works in live practice. Pay maximum attention to the change of person. Also remember the mandatory use of the past tense form:",
    
    "Коли іноземні студенти тільки починають вивчати цю складну тему, вони часто забувають змінити час дієслова. Вони за звичкою використовують інфінітив навіть тоді, коли суб'єкти вже різні. Це призводить до дуже серйозного і кумедного граматичного конфлікту.": "When foreign students are just starting to study this complex topic, they often forget to change the tense of the verb. Out of habit, they use the infinitive even when the subjects are already different. This leads to a very serious and amusing grammatical conflict.",
    
    "Завжди пам'ятайте про наше просте Дерево рішень: Суб'єкти різні? Відповідь ТАК → Обов'язково, без винятків, використовуйте минулий час після слова «щоб».": "Always remember our simple Decision Tree: Are the subjects different? Answer YES → Without exception, necessarily use the past tense after the word «щоб»."
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(md_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("Translations applied.")
