import re

md_file = 'curriculum/l2-uk-en/a1/imperative-and-requests.md'

with open(md_file, 'r') as f:
    content = f.read()

# Fix inline english issues:
content = content.replace("Давайте подивимося", "Подивімося")
content = content.replace("Щоб створити", "Для")
content = content.replace("Дуже важливо розуміти (It is absolutely crucial to understand)", "Дуже важливо розуміти")
content = content.replace("Використання формального закінчення демонструє повагу (Using the formal ending demonstrates respect)", "Використання формального закінчення демонструє повагу")

# More Ukrainian sentences replacing English ones to boost immersion:
replacements = {
    "As a beginner, you do not need to memorize the command forms for every single verb in the entire language immediately. That would be completely overwhelming and unnecessary at this stage of your learning journey.": "Вам не треба запам'ятовувати всі дієслова зараз. Це не обов'язково на цьому етапі.",
    "These are the absolute most common actions (дії) you will need to request or instruct others to do in your daily life, in your language studies, and when traveling.": "Це дуже важливі дії у вашому житті, у навчанні та під час подорожей.",
    "Some of these essential verbs follow the regular and highly predictable patterns that we discussed earlier in the lesson. Others, however, have slightly irregular stems that you will simply need to memorize as unique vocabulary items.": "Деякі з цих дієслів мають правильні форми. Інші дієслова мають неправильні основи. Їх треба просто запам'ятати.",
    "Learning these eight words inside and out will give you a remarkably solid foundation for classroom interactions and basic daily navigation in a Ukrainian-speaking environment.": "Ці вісім слів — ваша гарна база для спілкування.",
    "These first four verbs are incredibly common in a traditional learning environment or a language classroom.": "Ці перші чотири дієслова дуже часті на уроках.",
    "A teacher will frequently use the formal or plural commands to instruct the class during a lesson.": "Вчитель часто дає формальні команди на уроці.",
    "You will hear these constantly as you progress through your studies.": "Ви будете постійно чути ці слова.",
    "While using the formal plural ending (закінчення) is absolutely necessary for basic respect (повага), it is often not quite enough on its own in many social contexts.": "Формальне закінчення є дуже важливим для поваги. Але цього часто мало у багатьох соціальних контекстах.",
    "A direct command, even with the formal ending attached, can sometimes sound too blunt, direct, or even demanding in everyday, casual conversations.": "Пряма команда іноді звучить занадто прямо.",
    "To truly soften a request and make it genuinely polite, you must learn to incorporate the universal marker of politeness into your sentences.": "Для ввічливого прохання треба знати маркер ввічливості.",
    "The phrase for please is your absolute best tool for making polite, acceptable requests.": "Слово «будь ласка» — ваш найкращий інструмент для ввічливого прохання.",
    "You should add this vital phrase to almost every single command you give to a stranger, a service worker, or a casual acquaintance.": "Додавайте це слово до кожної команди.",
    "It instantly and effectively transforms a direct instruction into a courteous and pleasant request that people will be happy to fulfill.": "Це швидко робить вашу команду приємною.",
    "Sometimes, you need to tell someone not to do something right away.": "Іноді вам треба сказати людині не робити щось.",
    "This is grammatically called a prohibition or a negative command (заборона). Forming a negative command is an incredibly straightforward and simple process in Ukrainian.": "Це називається заборона або негативна команда. Робити негативну команду українською дуже просто.",
    "You simply take the standard command form that you have just learned and place the short negative particle (частка) directly in front of it.": "Ви просто берете форму команди і ставите коротку частку «не» перед нею.",
    "You do not need to change the verb ending at all to make it negative.": "Вам не треба міняти закінчення дієслова.",
    "The informal and formal endings remain exactly the same as they were for all positive commands.": "Форми на «ти» і «ви» залишаються такими ж, як і раніше.",
    "One of the great things about this polite phrase is its total flexibility in a sentence structure. You can place it at the beginning, right in the middle, or at the very end of your sentence. The meaning remains exactly the same in all cases. However, placing it immediately after the verb is a very common and natural-sounding pattern that native speakers use all the time.": "Одна з переваг цієї ввічливої фрази — її гнучкість. Ви можете поставити її на початку, всередині або в кінці речення. Значення залишається тим самим. Але ставити її одразу після дієслова — це дуже природно.",
    "If you find yourself in a highly formal situation, you can use another sophisticated pattern. You can use the formal phrase meaning I ask you followed by the dictionary form of the verb you want them to do. This formal pattern is often used in professional customer service environments or official bureaucratic settings. It shows a remarkably high level of respect for the person you are addressing and maintains a highly professional, polite distance.": "У дуже формальній ситуації ви можете використовувати іншу конструкцію. Ви можете сказати формальну фразу «я прошу вас» і потім інфінітив. Ця конструкція часто звучить у професійному сервісі. Це показує велику повагу.",
    "You can effectively use these negative commands in both informal and formal situations whenever necessary. Just remember to always match the verb ending to the person you are currently speaking to, and never forget to include the negative particle right before the verb to change the meaning.": "Ви можете використовувати ці негативні команди у формальних та неформальних ситуаціях. Просто пам'ятайте про правильне закінчення дієслова для кожної людини. Не забувайте ставити частку «не» перед дієсловом.",
    "For now, focus entirely on successfully using the personal negative commands. They are completely perfect for telling close friends, energetic children, or even friendly colleagues to stop doing a specific action immediately.": "Зараз просто фокусуйтеся на особистих негативних командах. Вони ідеальні для близьких друзів, дітей або колег.",
    "Let us briefly review what we have thoroughly covered in this detailed lesson today. You have successfully learned exactly how to form the imperative mood to confidently give commands and clear instructions to different people around you.": "Коротко повторимо наш урок. Ви вивчили, як утворювати наказовий спосіб для команди.",
    "You know precisely how to distinguish between the informal singular forms and the formal plural forms to show appropriate social respect. You have also memorized the eight vitally required verbs that form the core of your vocabulary for making everyday requests.": "Ви знаєте, як розрізняти неформальні і формальні форми. Ви також запам'ятали вісім важливих дієслів для прохань.",
    "Furthermore, you have effectively practiced making your new commands highly polite by adding the universal and flexible word for please. You learned the incredibly simple grammatical rule for creating negative commands by just adding a short particle right before the verb to accurately express a basic prohibition.": "Ви також практикували робити ваші команди ввічливими. Ви вивчили правило для негативних команд — просто додайте коротку частку перед дієсловом.",
    "Keep actively practicing these forms as much as possible. Try giving yourself simple instructions mentally throughout the day using the verbs you have recently learned in this lesson. The more you use these imperative commands, the more natural and fluent they will eventually feel in your actual daily conversations.": "Практикуйте ці форми якомога частіше. Давайте собі прості інструкції протягом дня. Чим більше ви використовуєте ці команди, тим більш природно вони будуть звучати."
}

for eng, ukr in replacements.items():
    content = content.replace(eng, ukr)

# Just to be safe, any residual (For this polite command)
content = content.replace("Для цієї ввічливої команди (For this polite command)", "Для цієї ввічливої команди")

with open(md_file, 'w') as f:
    f.write(content)
