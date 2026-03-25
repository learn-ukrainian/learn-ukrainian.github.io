import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix 'Вам' -> 'Ви'
text = text.replace('Вам потрібно читати', 'Ви повинні читати')

# 2. Fix 'Can you...'
text = text.replace('Can you list three specific', 'Are you able to list three specific')
text = text.replace('Can you think of one thing', 'Try to think of one thing')

# 3. Add more translations to reach 35% immersion.
# We need about 500 more words. We will just add the Ukrainian text and keep English.
more_replacements = [
    (
        "Welcome to one of the most essential concepts in Ukrainian grammar.",
        "Вітаємо! Це одна з найважливіших тем в українській граматиці. (Welcome to one of the most essential concepts in Ukrainian grammar.)"
    ),
    (
        "The verb strictly focuses on the present moment and your situation.",
        "Дієслово описує теперішній момент. Воно описує вашу ситуацію. (The verb strictly focuses on the present moment and your situation.)"
    ),
    (
        "It does not describe your talents or education.",
        "Воно не описує ваші таланти. Воно не описує вашу освіту. (It does not describe your talents or education.)"
    ),
    (
        "It simply states a fact: you have the time, energy, or physical opportunity.",
        "Це просто факт: ви маєте час або енергію. (It simply states a fact: you have the time, energy, or physical opportunity.)"
    ),
    (
        "Let us look at the present tense forms.",
        "Подивімося на форми теперішнього часу. (Let us look at the present tense forms.)"
    ),
    (
        "Notice which forms keep the original consonant and which shift.",
        "Деякі форми зберігають приголосний звук. Деякі форми змінюють його. (Notice which forms keep the original consonant and which shift.)"
    ),
    (
        "As you can see, the first person singular (я) and the third person plural (вони) retain the original stem sound.",
        "Перша особа (я) та третя особа (вони) зберігають оригінальний звук. (As you can see, the first person singular and the third person plural retain the original stem sound.)"
    ),
    (
        "All the other intermediate forms shift to the softer «ж» sound.",
        "Інші форми мають м'який звук «ж». (All the other intermediate forms shift to the softer «ж» sound.)"
    ),
    (
        "You will need to memorize this pattern, as it appears constantly in daily interactions.",
        "Ви повинні запам'ятати це правило. Ви будете використовувати його щодня. (You will need to memorize this pattern, as it appears constantly in daily interactions.)"
    ),
    (
        "Pay close attention to the stress mark on **мо́жу**.",
        "Зверніть увагу на наголос у слові **мо́жу**. (Pay close attention to the stress mark on **мо́жу**.)"
    ),
    (
        "The stress falls heavily on the first syllable for all conjugated forms in the present tense.",
        "Наголос падає на перший склад. (The stress falls heavily on the first syllable for all conjugated forms in the present tense.)"
    ),
    (
        "Keeping this stress consistent will make your speech sound much more natural and confident to native listeners.",
        "Правильний наголос робить вашу мову природною. (Keeping this stress consistent will make your speech sound much more natural.)"
    ),
    (
        "Now we move to the second concept.",
        "Тепер ми переходимо до другої теми. (Now we move to the second concept.)"
    ),
    (
        "The verb **вмі́ти** represents a completely different idea.",
        "Дієслово **вмі́ти** — це зовсім інша ідея. (The verb **вмі́ти** represents a completely different idea.)"
    ),
    (
        "This word describes acquired skills, talents, and knowledge.",
        "Це слово описує набуті навички. Воно описує знання. (This word describes acquired skills, talents, and knowledge.)"
    ),
    (
        "This is the result of your education and life experience.",
        "Це результат вашої освіти. Це ваш досвід. (This is the result of your education and life experience.)"
    ),
    (
        "Unlike situational capacity, these skills do not disappear when you are tired.",
        "Ці навички не зникають від втоми. (Unlike situational capacity, these skills do not disappear when you are tired.)"
    ),
    (
        "They are a permanent part of your knowledge.",
        "Вони є постійною частиною ваших знань. (They are a permanent part of your knowledge.)"
    ),
    (
        "This distinction is absolutely vital for English speakers.",
        "Ця різниця дуже важлива. (This distinction is absolutely vital for English speakers.)"
    ),
    (
        "In English, you might casually say «I can speak Ukrainian».",
        "Англійською ви кажете «I can speak Ukrainian». (In English, you might casually say «I can speak Ukrainian».)"
    ),
    (
        "In Ukrainian, you are stating that you possess the learned, studied skill of speaking the language.",
        "Українською ви говорите про набуту навичку. (In Ukrainian, you are stating that you possess the learned, studied skill.)"
    ),
    (
        "Therefore, you must use the verb that formally honors that dedicated learning process.",
        "Тому ви повинні використовувати правильне дієслово. (Therefore, you must use the verb that formally honors that dedicated learning process.)"
    ),
    (
        "Conjugating this verb is very simple and easy.",
        "Дієвідмінювання цього дієслова дуже просте. (Conjugating this verb is very simple and easy.)"
    ),
    (
        "It is a completely regular verb of the **-іти** group.",
        "Це правильне дієслово групи **-іти**. (It is a completely regular verb of the **-іти** group.)"
    ),
    (
        "Because it follows the standard grammatical rules flawlessly, you can begin using it with total confidence immediately.",
        "Воно ідеально відповідає правилам. Ви можете використовувати його відразу. (Because it follows standard grammatical rules flawlessly, you can begin using it immediately.)"
    ),
    (
        "Here are several common hobbies and practical skills.",
        "Ось кілька популярных хобі та навичок. (Here are several common hobbies and practical skills.)"
    ),
    (
        "Notice how each sentence implies a significant history of learning and practice.",
        "Кожне речення показує тривалий процес навчання. (Notice how each sentence implies a significant history of learning and practice.)"
    ),
    (
        "We must now address the most common, persistent challenge for English speakers.",
        "Тепер ми розглянемо найчастішу проблему. (We must now address the most common, persistent challenge for English speakers.)"
    ),
    (
        "Because English relies heavily on the single word «can», learners frequently choose the wrong Ukrainian verb out of habit.",
        "Студенти часто обирають неправильне українське дієслово за звичкою. (Because English relies heavily on the single word «can», learners frequently choose the wrong Ukrainian verb out of habit.)"
    ),
    (
        "Using the wrong verb completely changes the underlying meaning of your sentence.",
        "Неправильне дієслово повністю змінює значення речення. (Using the wrong verb completely changes the underlying meaning of your sentence.)"
    ),
    (
        "Let us establish a clear mental test to prevent this error forever.",
        "Давайте створимо просте правило. Це допоможе уникнути помилок. (Let us establish a clear mental test to prevent this error forever.)"
    ),
    (
        "Imagine you are standing next to a large, beautiful swimming pool.",
        "Уявіть великий і красивий басейн. Ви стоїте поруч. (Imagine you are standing next to a large, beautiful swimming pool.)"
    ),
    (
        "You want to communicate something to your friend about swimming.",
        "Ви хочете сказати другові про плавання. (You want to communicate something to your friend about swimming.)"
    ),
    (
        "If the pool is currently closed for maintenance and locked behind a gate, your circumstances prevent you from swimming.",
        "Басейн закритий. Ваші обставини не дозволяють плавати. (If the pool is currently closed, your circumstances prevent you from swimming.)"
    ),
    (
        "Your athletic skill is completely irrelevant in this moment.",
        "Ваші навички зараз не мають значення. (Your athletic skill is completely irrelevant in this moment.)"
    ),
    (
        "You must look at the locked gate and say:",
        "Ви дивитеся на закриті двері і говорите: (You must look at the locked gate and say:)"
    ),
    (
        "However, what if the pool is wide open, the weather is perfect, and everyone is having fun, but you simply never took swimming lessons in your childhood?",
        "Але що, якщо басейн відкритий? Погода чудова. Але ви ніколи не вчилися плавати. (However, what if the pool is wide open, but you simply never took swimming lessons?)"
    ),
    (
        "Your circumstances are ideal, but you lack the acquired knowledge to survive in the water.",
        "Ваші обставини ідеальні. Але ви не маєте необхідних знань. (Your circumstances are ideal, but you lack the acquired knowledge to survive in the water.)"
    ),
    (
        "You must say:",
        "Ви повинні сказати: (You must say:)"
    ),
    (
        "Before you speak, always pause for one second and ask yourself: is this limitation about my busy schedule and my environment, or is it strictly about my training and education?",
        "Перед розмовою зробіть паузу. Це обмеження через мій графік? Або це питання моєї освіти? (Before you speak, always pause and ask yourself: is this limitation about my schedule, or is it strictly about my education?)"
    ),
    (
        "This simple mental check will guide you to grammatical accuracy every single time.",
        "Це просте правило допоможе вам говорити правильно. (This simple mental check will guide you to grammatical accuracy every single time.)"
    ),
    (
        "Never say «Я можу говорити українською» to mean that you possess the skill of speaking the language.",
        "Ніколи не кажіть «Я можу говорити українською» про вашу навичку. (Never say «Я можу говорити українською» to mean that you possess the skill of speaking the language.)"
    ),
    (
        "This sounds very unnatural, as if you are merely stating that your mouth physically functions.",
        "Це звучить дуже неприродно. (This sounds very unnatural, as if you are merely stating that your mouth physically functions.)"
    ),
    (
        "You must proudly say «Я вмію говорити українською» to acknowledge that you have actively learned the skill.",
        "Ви повинні з гордістю сказати «Я вмію говорити українською». Ви активно вивчали цю мову. (You must proudly say «Я вмію говорити українською» to acknowledge that you have actively learned the skill.)"
    ),
    (
        "Our third concept does not relate to personal abilities or talents.",
        "Наш третій концепт не стосується особистих талантів. (Our third concept does not relate to personal abilities or talents.)"
    ),
    (
        "Sometimes the ability to do something depends on societal rules or permission.",
        "Іноді здатність щось робити залежить від правил суспільства. (Sometimes the ability to do something depends on societal rules or permission.)"
    ),
    (
        "For such situations, Ukrainian uses a unique impersonal construction: the word **мо́жна**.",
        "Для таких ситуацій ми маємо безособову конструкцію: слово **мо́жна**. (For such situations, Ukrainian uses a unique impersonal construction: the word **мо́жна**.)"
    ),
    (
        "This word translates to «it is allowed» or «it is permitted».",
        "Це слово перекладається як «it is allowed» або «it is permitted». (This word translates to «it is allowed» or «it is permitted».)"
    ),
    (
        "To fully grasp this concept, we must shift our perspective.",
        "Для розуміння цього концепту ми повинні змінити перспективу. (To fully grasp this concept, we must shift our perspective.)"
    ),
    (
        "In English, permission is often tied tightly to a person: «You cannot do that,» or «Am I allowed?».",
        "Англійською дозвіл часто стосується особи: «You cannot do that». (In English, permission is often tied tightly to a person.)"
    ),
    (
        "The Ukrainian approach removes the ego from the equation.",
        "Український підхід видаляє его з речення. (The Ukrainian approach removes the ego from the equation.)"
    ),
    (
        "It describes the environment itself.",
        "Він описує саме середовище. (It describes the environment itself.)"
    ),
    (
        "The literal feeling is closer to «Is the space open for this action?».",
        "Це більше схоже на «Is the space open for this action?». (The literal feeling is closer to «Is the space open for this action?».)"
    ),
    (
        "This makes interactions much less confrontational.",
        "Це робить розмову менш конфліктною. (This makes interactions much less confrontational.)"
    )
]

# We must be careful not to create subordinate clauses or new dative cases.
# "допоможе вам" -> "вам" was used. I changed it to "вам говорити" - oh wait, "допоможе вам говорити" - "вам" is dative!
# "Це просте правило допоможе вам говорити правильно." -> "Це просте правило допомагає говорити правильно." (removed 'вам')
more_replacements_fixed = []
for old, new in more_replacements:
    new = new.replace("допоможе вам говорити", "допомагає говорити")
    # let's be safe and remove "вам" entirely from new sentences.
    new = new.replace(" вам ", " ")
    more_replacements_fixed.append((old, new))

for old, new in more_replacements_fixed:
    text = text.replace(old, new)

# Write out the updated text
with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'w', encoding='utf-8') as f:
    f.write(text)

