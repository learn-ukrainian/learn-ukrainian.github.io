import os

file_path = 'curriculum/l2-uk-en/a1/weather-and-nature.md'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix grammar violations
text = text.replace('Ліс дає нам спокій.', 'Ліс дає спокій.')
text = text.replace('Море дає нам радість.', 'Море дає радість.')
text = text.replace('Сучасні технології дають нам точний прогноз.', 'Сучасні технології дають точний прогноз.')
text = text.replace('Тепло і холодно — це базові слова.', 'Тепло і холодно — це головні слова.')

# Fix immersion by truncating verbose English
text = text.replace(
    'When you describe environmental conditions or temperature in Ukrainian, you do not use phrases like "the weather is" or the dummy pronoun "it". Instead, the language employs impersonal adverbs. These adverbs stand alone and independently convey the entire meaning of the condition. This structural difference highlights the directness of Ukrainian expressions. You just state the condition as a universal fact.',
    'When you describe environmental conditions in Ukrainian, you do not use phrases like "the weather is" or the dummy pronoun "it". Instead, the language employs impersonal adverbs. You just state the condition as a fact.'
)

text = text.replace(
    'The adverbs **тепло** and **холодно** are your primary tools for describing temperature. Notice that we do not say "It is warm". We just say "Warm". You can add the location, like «на вулиці» (outside), but the core of the sentence remains the single adverb. This simplicity is beautiful, but it requires English speakers to unlearn their habit of always searching for a grammatical subject.',
    'The adverbs **тепло** and **холодно** describe temperature. We do not say "It is warm". We just say "Warm". The core of the sentence remains the single adverb.'
)

text = text.replace(
    'When talking about rain, Ukrainian uses a fascinating idiomatic construction. We use the noun for the weather event (**дощ**) and combine it with the verb of motion «іти» (to walk/to go). Literally, we say "the rain walks". This paints a dynamic, active picture of precipitation. The rain is an active participant moving through the environment.',
    'When talking about rain, Ukrainian uses a motion verb. We combine the noun (**дощ**) with the verb of motion «іти» (to walk/to go). Literally, we say "the rain walks".'
)

text = text.replace(
    'Just like with rain, we use the verb of motion «іти» for snow. The phrase **йде сніг** translates to "it is snowing", but literally means "the snow walks". In Ukraine, snow is a major part of the winter experience, completely transforming both the urban landscape and the natural scenery. Knowing how to describe the falling snow is essential for winter conversations.',
    'Just like with rain, we use the verb of motion «іти» for snow. The phrase **йде сніг** translates to "it is snowing", but literally means "the snow walks".'
)

text = text.replace(
    'In Ukrainian, we have distinct adverbs derived from the names of the seasons to answer the question "when?". Instead of using a preposition like "in the winter", we use a single dedicated temporal adverb. This is a crucial feature of State Standard §3.4. Memorizing these temporal adverbs will immediately elevate your fluency and help you describe time accurately.',
    'In Ukrainian, we have distinct adverbs derived from the names of the seasons to answer the question "when?". Instead of using a preposition like "in the winter", we use a single dedicated temporal adverb.'
)

text = text.replace(
    'The adverb form for "in winter" is **взимку**. Notice the stress falls on the first syllable. When you talk about the winter environment, the combination of **холодно** and **сніг** is essential. The Carpathian mountains become a major destination because of the reliable snow cover. Using the adverb correctly allows you to set the scene for any winter story.',
    'The adverb form for "in winter" is **взимку**. Notice the stress falls on the first syllable. The combination of **холодно** and **сніг** is essential here.'
)

text = text.replace(
    'The adverb form for "in summer" is **влітку**. The warm weather drives people to natural bodies of water. The Black Sea in the south of Ukraine is a classic summer destination. When describing the summer environment, the adverb **спекотно** is used frequently to indicate high temperatures that invite a trip to the beach or a walk in the shade.',
    'The adverb form for "in summer" is **влітку**. When describing the summer environment, the adverb **спекотно** is used frequently to indicate high temperatures.'
)

text = text.replace(
    'The adverb form for "in autumn" is **восени**. Pay close attention to the stress: vóseny. The first syllable is stressed. Autumn brings a dramatic shift in weather, transitioning from the heat of summer to the chill of winter. It is the season most associated with **дощ** and **вітер**, but also with the beautiful cultural tradition of the harvest.',
    'The adverb form for "in autumn" is **восени**. Pay close attention to the stress: vóseny. It is the season most associated with **дощ** and **вітер**.'
)

text = text.replace(
    'The mountains (**гори**) expose you to rapid weather changes. The Carpathian mountain range in western Ukraine is a symbol of natural beauty and resilience. Understanding the weather patterns in the mountains is essential for anyone planning a hike. You must always be prepared for rain, wind, and sudden temperature drops.',
    'The mountains (**гори**) expose you to rapid weather changes. Understanding the weather patterns in the mountains is essential for anyone planning a hike.'
)

text = text.replace(
    'Freshwater bodies like lakes (**озеро**) and rivers (**річка**) are everywhere in Ukraine, providing an escape from the summer heat. Whether you are describing a quiet lake or the vast expanse of the sea, these vocabulary words are essential for planning leisure activities and describing the natural geography around you accurately.',
    'Freshwater bodies like lakes (**озеро**) and rivers (**річка**) provide an escape from the summer heat. These vocabulary words are essential for describing the natural geography.'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
