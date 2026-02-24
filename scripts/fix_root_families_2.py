import re

with open('curriculum/l2-uk-en/a2/root-families-i.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix transliteration
text = text.replace("шаблон (pattern)", "загальний шаблон")

# 2. Expand "Родини ход- та пис-" (Target: 700, Current: 568. Add ~150 words)
expansion_hod_pys = """
**Understanding Context and Metaphorical Uses**
While the primary meaning of the **-ход-** root is physical movement, Ukrainian frequently employs it in metaphorical contexts. This is a common feature of the language, where a word describing a physical action is borrowed to describe abstract concepts. For instance, the word **підхід** literally translates to "approach" (moving toward something from below or closely). However, in professional and academic settings, **підхід** is almost exclusively used to describe a "methodology" or a "strategy" for solving a problem. If a business leader says, "Нам потрібен новий підхід до цієї проблеми," they are not talking about physically walking toward the problem; they are asking for a new strategic methodology. Understanding these metaphorical extensions is crucial for reading Ukrainian news, business documents, and literature. The root remains the same, providing a solid anchor for comprehension, but the prefix shifts the meaning into the realm of abstract thought.
"""
text = text.replace("Завжди звертайте увагу на контекст розмови. Слово **запис** може означати і текстовий конспект, і музичний трек.", "Завжди звертайте увагу на контекст розмови. Слово **запис** може означати і текстовий конспект, і музичний трек.\n\n" + expansion_hod_pys)


# 3. Expand "Родини чит- та бач-" (Target: 700, Current: 556. Add ~150 words)
expansion_chyt_bach = """
**The Concept of "Mutual Seeing"**
The root **-бач-** also serves as the foundation for words expressing mutual agreement, understanding, and interpersonal dynamics. When people share a common vision or perspective, they are metaphorically "seeing" the situation in the same way. The prefix **по-** often adds a layer of completion or mutuality to the action. Thus, when we explore the vocabulary of relationships, the core concept of vision is frequently utilized. This highlights how deeply intertwined sensory perception and cognitive understanding are in the Ukrainian linguistic worldview. 

To further illustrate the flexibility of the **-чит-** root, consider its usage in academic environments. A university lecture is not merely a spoken presentation; it is often referred to as "читання лекції" (the reading of a lecture), emphasizing the formal, structured delivery of information. This usage stems directly from the root's ancient association with honoring and accurately transmitting vital knowledge to an audience.
"""
text = text.replace("Це слово чудово показує, як логічна лінгвістична структура може створювати дуже емоційну та романтичну лексику.", "Це слово чудово показує, як логічна лінгвістична структура може створювати дуже емоційну та романтичну лексику.\n\n" + expansion_chyt_bach)


# 4. Expand "Практичне застосування" (Target: 600, Current: 416. Add ~200 words)
expansion_practical = """
### Creating Your Own Word Networks
One of the most effective strategies for independent language learning is building your own personal word networks. Now that you understand the mechanics of the "Big Four" roots, you can apply this system to any new root you encounter. Create a visual map in your notebook: write a new core root in the center, and draw branches connecting it to all the prefixes you know (в-, ви-, при-, під-, пере-). Try to predict the meaning of each resulting word, and then check a dictionary to confirm your hypothesis. This active, analytical approach is infinitely more powerful than passively trying to memorize long lists of vocabulary.

**The Role of Context in Vocabulary Acquisition**
Always remember that words do not exist in a vacuum. A word's true meaning is often determined by the surrounding sentences and the overall context of the conversation. When you encounter a familiar root with an unfamiliar prefix, do not panic. Read the entire sentence carefully. Look for clues that might indicate direction, completion, or abstract metaphorical usage. For instance, if you see the word **вихідний** in a sentence about days of the week, the prefix **ви-** (out) and the root **-ход-** (motion) logically point to a day when you "go out" from your normal work routine—a weekend or a day off.
"""
text = text.replace("Пам'ятайте ці правила та слухайте носіїв мови. Ваша українська швидко звучатиме впевнено та граматично бездоганно.", "Пам'ятайте ці правила та слухайте носіїв мови. Ваша українська швидко звучатиме впевнено та граматично бездоганно.\n\n" + expansion_practical)

with open('curriculum/l2-uk-en/a2/root-families-i.md', 'w', encoding='utf-8') as f:
    f.write(text)
