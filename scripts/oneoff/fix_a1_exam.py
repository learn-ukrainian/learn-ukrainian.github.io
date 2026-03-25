import re

with open('curriculum/l2-uk-en/a1/a1-final-exam.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix Instrumental 'перед іспитом'
text = text.replace('Перевірте себе перед іспитом:', 'Перевірте себе:')

# 2. Fix Participle 'Захоплюючий'
text = text.replace('Захоплюючий перехід до A2', 'Цікавий перехід до A2')

# 3, 4, 5. Fix complex sentences and sentence length
old_complex = """> «Я дуже хочу пити каву, але мій молодший брат хоче пити чай.»
> I really want to drink coffee, but my younger brother wants to drink tea.

> «Цей розумний студент завжди відповідає правильно, бо він багато і часто читає.»
> This smart student always answers correctly because he reads a lot and often.

> «Ми повільно гуляємо в парку, і сьогодні погода просто чудова.»
> We are walking slowly in the park, and today the weather is simply wonderful."""

new_complex = """> «Я дуже хочу пити каву. Мій брат хоче пити чай.»
> I really want to drink coffee. My brother wants to drink tea.

> «Цей студент завжди відповідає правильно. Він дуже багато читає.»
> This student always answers correctly. He reads a lot.

> «Ми гуляємо в парку. Сьогодні погода просто чудова.»
> We are walking in the park. Today the weather is simply wonderful."""

text = text.replace(old_complex, new_complex)

# Fix the English explanation above it that mentions complex sentences and "бо"
old_explanation = """To thoroughly and rigorously assess your advanced reading and listening skills, you must prove your ability to process not just simple sentences, but basic complex sentences. A complex sentence joins two separate, independent ideas using simple coordinating or subordinating conjunctions like **і** (and - addition), **а** (and/but - contrast), **але** (but - contradiction), or **бо / тому що** (because - reason)."""

new_explanation = """To thoroughly and rigorously assess your advanced reading and listening skills, you must prove your ability to process connected simple sentences. We can place simple sentences together to tell a story, explain a contrast, or provide a clear reason."""

text = text.replace(old_explanation, new_explanation)

# Fix question 6 that specifically asks about 'бо'
old_q6 = "6. Describe a highly practical communicative scenario where you would absolutely need to use the conjunction **бо** to build a complex sentence explaining a reason."
new_q6 = "6. Describe a highly practical communicative scenario where you would need to use simple sentences to explain a reason clearly."
text = text.replace(old_q6, new_q6)

# 6. Fix Redundancy 1 (-и- or -ї-)
text = text.replace(
    "The typical present tense endings heavily feature the linking vowel **-и-** (or **-ї-** after vowels).",
    "For this group, the conjugation pattern uses the vowel **-и-** (or **-ї-** following another vowel) to connect the stem and the ending."
)

# 7. Fix Redundancy 2 (Чи новий студент...)
old_q_redundant = """> «Чи новий студент уважно читає велику книгу?» (General Question)
> Is the new student carefully reading a large book?"""
new_q_redundant = """> «Чи ми добре розуміємо цю нову тему?» (General Question)
> Do we understand this new topic well?"""
text = text.replace(old_q_redundant, new_q_redundant)

# 8. Fix Robotic structure (can you...) AND Immersion
# Replace the paragraph completely with a Ukrainian translation to hit both birds with one stone.
old_psych = """Language learning is a marathon, not a sprint. At the A1 beginner level, the ultimate goal is not absolute, flawless grammatical perfection, but rather effective and confident communication. If you accidentally use the wrong case ending but the barista completely understands your coffee order, that is a massive victory. This exam is meticulously designed to highlight what you can actively do, rather than punish you for the complex nuances you are still learning. Your grade, or **оцінка**, is an objective measurement of your functional communication skills. Can you understand a basic train schedule? Can you successfully ask for directions on the street? Can you describe your morning routine? If you can perform these functional tasks **правильно** (correctly) the majority of the time, you have thoroughly achieved the communicative goals of A1."""

new_psych = """Вивчення мови — це марафон, а не спринт. На рівні А1 головна мета — це не абсолютна граматична досконалість, а ефективна та впевнена комунікація. Якщо ви випадково використовуєте неправильне закінчення, але бариста повністю розуміє ваше замовлення, це велика перемога. Цей іспит створений, щоб показати, що ви вже вмієте робити, а не карати за помилки. Ваша **оцінка** — це об'єктивне вимірювання ваших практичних навичок. Ви можете зрозуміти розклад поїздів? Чи легко вам запитати дорогу на вулиці? Ви готові описати свій ранок? Якщо ви робите це **правильно** більшість часу, ви успішно досягли цілей рівня А1."""

text = text.replace(old_psych, new_psych)


# 9. Boost Immersion
# Translate more paragraphs to Ukrainian
old_outro = """You have read and comprehended highly descriptive, authentic texts about the cities of Kyiv and Lviv. You can confidently and accurately conjugate essential communication verbs across both structural classes. You can instantly formulate and properly answer highly practical, daily questions. You are absolutely no longer an absolute beginner. You are a functional, capable, and confident speaker of the Ukrainian language.

Take immense, justified pride in the vast vocabulary repertoire you have systematically built. When you listen to native speakers conversing now, you will consistently pick out familiar words, recognize grammatical structures, and understand the general flow of information. Continue passionately listening to Ukrainian music, reading simple graded cultural texts, and practicing your conversational skills at every opportunity. The Patient Supportive Tutor is incredibly proud of your steadfast dedication and your remarkable success."""

new_outro = """Ви прочитали та зрозуміли автентичні тексти про Київ та Львів. Ви можете впевнено та правильно відмінювати базові дієслова обох класів. Ви можете швидко формулювати та правильно відповідати на практичні щоденні запитання. Ви більше не є абсолютним новачком. Ви — впевнений мовець, який розуміє українську мову.

Пишайтеся своїм великим словниковим запасом. Коли ви слухаєте носіїв мови, ви завжди розпізнаєте знайомі слова, граматичні структури та розумієте загальний зміст. Продовжуйте слухати українську музику, читати прості культурні тексти та практикувати свої навички спілкування за кожної нагоди. Ми дуже пишаємося вашою відданістю та неймовірним успіхом."""

text = text.replace(old_outro, new_outro)


old_summary = """This massive, comprehensive final review module synthesizes the core morphological, syntactic, and highly communicative goals of the entire A1 learning level. You systematically and deeply revisited essential noun cases (Nominative for subjects, Vocative for addressing, Accusative for direct objects, Locative for static position), solidified your robust understanding of Class I and Class II present tense verb conjugations, and rigorously practiced crucial syntactic structures including flexible word order and specific question formation. Through the engaging cultural narratives detailing the unique urban environments of Kyiv and Lviv, you actively applied these abstract grammatical concepts to tangible, real-world contexts involving public transport, regional food, and daily life routines. You are now fully and comprehensively prepared to demonstrate your practical communicative skills in the final overall assessment and transition smoothly and confidently into the deeper grammatical explorations of level A2."""

new_summary = """Цей фінальний модуль повторення об'єднує граматику та словник рівня А1. Ви повторили відмінки: називний, кличний, знахідний, місцевий. Ви закріпили розуміння дієслів першого та другого класу. Ви також практикували синтаксис і формування запитань. Через культурні тексти про Київ та Львів ви використовували ці правила в реальних контекстах: транспорт, їжа та щоденна рутина. Тепер ви повністю готові до фінального тесту і переходу на рівень А2. Ваша праця дає чудові результати. Успіхів на іспиті!"""

text = text.replace(old_summary, new_summary)

# Also let's translate the first two paragraphs to secure a massive immersion boost
old_intro1 = """Welcome to the absolute culmination of your A1 language journey! You have worked incredibly hard, dedicating hours of focus to reach this significant point. To drastically reduce any test anxiety and create a supportive learning environment, the instructions, structural explanations, and strategic advice in this final review will be delivered in English. However, the core reading texts, practical examples, and situational dialogues will be presented entirely in Ukrainian. This balanced approach ensures you understand exactly what is expected of you, while still rigorously proving your immersion capabilities and reading comprehension skills in the target language."""

new_intro1 = """Ласкаво просимо до фінального етапу вашої подорожі рівнем А1! Ви неймовірно багато працювали, приділяючи години уваги, щоб досягти цього важливого моменту. Щоб зменшити хвилювання та створити комфортне середовище, граматичні пояснення залишаться англійською. Але всі тексти для читання, практичні приклади та діалоги будуть повністю українською. Цей підхід гарантує, що ви розумієте завдання, водночас перевіряючи ваші навички читання та розуміння."""

text = text.replace(old_intro1, new_intro1)

old_intro2 = """Ви готові! Чудова робота! Think back to your very first module. You started by deciphering the Cyrillic alphabet, learning how to pronounce entirely new sounds, and struggling to read simple words. Today, you have successfully navigated a complex morphological system, learned how to conjugate essential verbs across different classes, and started using noun cases to build meaningful, communicative sentences. You can now politely greet people, order food in a restaurant, navigate a city using public transport, and confidently talk about your daily routine. This final exam simply confirms what you already know and practice daily. Take a deep breath and acknowledge your success. You have built a strong, functional, and permanent foundation in the Ukrainian language."""

new_intro2 = """Ви готові! Чудова робота! Згадайте свій найперший модуль. Ви починали з вивчення кирилиці, нових звуків та простих слів. Сьогодні ви успішно використовуєте відмінки, відмінюєте дієслова та будуєте змістовні речення. Ви можете ввічливо вітатися, замовляти їжу в ресторані, користуватися транспортом і розповідати про свій день. Цей фінальний іспит просто підтверджує те, що ви вже знаєте і практикуєте щодня. Зробіть глибокий вдих і визнайте свій успіх. Ви побудували міцний і постійний фундамент в українській мові."""

text = text.replace(old_intro2, new_intro2)


with open('curriculum/l2-uk-en/a1/a1-final-exam.md', 'w', encoding='utf-8') as f:
    f.write(text)

print("Done replacements.")
