import re

file_path = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/a1-final-exam.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix `вам`
content = content.replace("Ваші базові знання дуже допоможуть вам вивчати ці нові теми.", "Ваші базові знання дуже допоможуть вивчати ці нові теми.")

# Fix `давайте повторимо`
content = content.replace("Давайте повторимо важливі фрази.", "Ми повторимо важливі фрази.")

# Fix `слова і а` (Euphony)
content = content.replace("Вони використовують слова «і», «а» або «але».", "Вони використовують слова «й», «а» або «але».")
content = content.replace("слова «і», «а» або «але»", "слова «й», «а» або «але»")
content = content.replace("words like "і" (and)", "words like "й" (and)")
content = content.replace("«і», «а», and «але»", "«й», «а», and «але»")

# Add more bilingual replacements to hit 35% immersion
rep13 = """The Accusative case is one of the most frequently and widely used grammatical forms in the language. Its primary syntactic function is to indicate the direct object of a transitive action. For example, when you read a book, the book receives the action; thus, it is the direct object. Another fundamentally crucial function of the Accusative case is expressing physical motion towards a specific destination. When you are going somewhere, you must use the Accusative case immediately after the prepositions "в" (into) or "на" (onto)."""
rep13_bil = """Знахідний відмінок — це дуже часта форма в мові. Його головна функція — показувати прямий об'єкт дії. Наприклад, коли ви читаєте книгу, книга отримує дію. Тому це прямий об'єкт. Інша дуже важлива функція Знахідного відмінка — це вираження руху до певного місця. Коли ви йдете кудись, ви маєте використовувати Знахідний відмінок після слів «в» або «на».
*(The Accusative case is one of the most frequently and widely used grammatical forms in the language. Its primary syntactic function is to indicate the direct object of a transitive action. For example, when you read a book, the book receives the action; thus, it is the direct object. Another fundamentally crucial function of the Accusative case is expressing physical motion towards a specific destination. When you are going somewhere, you must use the Accusative case immediately after the prepositions "в" (into) or "на" (onto).)*"""
content = content.replace(rep13, rep13_bil)

rep14 = """While the Accusative case shows dynamic movement and where you are going, the Locative case shows static position and where you currently are. This conceptual distinction is a very common point of confusion for learners. The Locative case meticulously describes a static, unchanging location. It strictly requires the use of prepositions like "в" (in) or "на" (on) to indicate spatial position. You absolutely cannot use the Locative case by itself without an accompanying preposition."""
rep14_bil = """Знахідний відмінок показує рух і куди ви йдете. Місцевий відмінок показує статичну позицію і де ви є зараз. Ця різниця є дуже частою проблемою для студентів. Місцевий відмінок описує статичну позицію. Він вимагає слова «в» або «на» для опису місця. Цей відмінок завжди має прийменник.
*(While the Accusative case shows dynamic movement and where you are going, the Locative case shows static position and where you currently are. This conceptual distinction is a very common point of confusion for learners. The Locative case meticulously describes a static, unchanging location. It strictly requires the use of prepositions like "в" (in) or "на" (on) to indicate spatial position. You absolutely cannot use the Locative case by itself without an accompanying preposition.)*"""
content = content.replace(rep14, rep14_bil)

rep15 = """Creating accurate sentences in Ukrainian is a very straightforward process once you know the basic underlying structure. The standard and most neutral word order is Subject-Verb-Object (SVO), just like in English syntax. However, because the noun cases clearly and unambiguously show who is doing what, you can freely change the word order for stylistic emphasis without changing the core meaning of the sentence. Forming questions correctly is another vital skill."""
rep15_bil = """Створення речень — це дуже простий процес. Стандартний порядок слів — це Суб'єкт-Дієслово-Об'єкт. Однак, відмінки чітко показують, хто робить дію. Тому ви можете вільно змінювати порядок слів. Це не змінює головний сенс речення. Правильне створення питань — це ще одна важлива навичка.
*(Creating accurate sentences in Ukrainian is a very straightforward process once you know the basic underlying structure. The standard and most neutral word order is Subject-Verb-Object (SVO), just like in English syntax. However, because the noun cases clearly and unambiguously show who is doing what, you can freely change the word order for stylistic emphasis without changing the core meaning of the sentence. Forming questions correctly is another vital skill.)*"""
content = content.replace(rep15, rep15_bil)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done part 4.")
