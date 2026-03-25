import os

file_path = 'curriculum/l2-uk-en/a1/weather-and-nature.md'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix 'бо' grammar violations by using 'тому' instead
text = text.replace('Ми не гуляємо, бо холодно', 'Холодно, тому ми не гуляємо')
text = text.replace('я беру парасолю, бо йде дощ', 'йде дощ, тому я беру парасолю')
text = text.replace('Ми сидимо вдома, бо сильний вітер', 'Сильний вітер, тому ми сидимо вдома')
text = text.replace('Ми йдемо на річку, бо спекотно', 'Спекотно, тому ми йдемо на річку')
text = text.replace('ми йдемо в ліс, бо тепло і гарно', 'тепло і гарно, тому ми йдемо в ліс')
text = text.replace('ми не беремо куртки, бо спекотно', 'спекотно, тому ми не беремо куртки')
text = text.replace('ми сидимо вдома, бо холодно', 'холодно, тому ми сидимо вдома')

text = text.replace('We are not walking because it is cold', 'It is cold, so we are not walking')
text = text.replace('I am taking an umbrella because it is raining', 'It is raining, so I am taking an umbrella')
text = text.replace('We sit at home because there is a strong wind', 'There is a strong wind, so we sit at home')
text = text.replace('We go to the river because it is hot', 'It is hot, so we go to the river')
text = text.replace('we are going to the forest, because it is warm and nice', 'it is warm and nice, so we are going to the forest')
text = text.replace('we are not taking jackets, because it is hot', 'it is hot, so we are not taking jackets')
text = text.replace('we sit at home, because it is cold', 'it is cold, so we sit at home')

# Fix immersion by removing redundant English translations of full paragraphs
# We keep the Ukrainian paragraphs which already have inline vocab translations.

# Привітання з Карпат
text = text.replace(
    'The Carpathian Mountains are large mountains in Ukraine. The nature here is very beautiful. But the weather here is complex. It changes rapidly. In the morning, the bright sun shines. During the day, heavy rain often falls. In the evening, it can be very cold. We must know the forecast. We always talk about the weather. This is very important.\nWhen you travel or live in Ukraine, understanding the environment is not just small talk. It is a matter of practical daily planning. The Ukrainian language reflects this deep connection to nature. We observe the elements closely, and we talk about them constantly.',
    'When you travel or live in Ukraine, understanding the environment is a matter of practical daily planning. We observe the elements closely, and we talk about them constantly.'
)

# Погода як ключ до спілкування
text = text.replace(
    'Weather is a wonderful topic. We often ask about it. What is the weather like today? This question starts a conversation. We speak with neighbors. We speak with friends. It is easy and pleasant. You can say: today it is warm. Or you say: today it is cold. People agree. The conversation continues. This is very useful for beginners.\nMastering basic weather vocabulary gives you a universal key to interaction. Every Ukrainian experiences the same dramatic shifts in seasons. Sharing a simple observation about the rain or the sunshine instantly connects you with the people around you. It shows you are present in the moment and opens the door for further connection.',
    'Mastering basic weather vocabulary gives you a universal key to interaction. Sharing a simple observation about the rain or the sunshine instantly connects you with the people around you.'
)

# Бабине літо та фольклор
text = text.replace(
    'Autumn in Ukraine is very beautiful. At first, it rains. It is cold and cloudy. But then the sun arrives. It is warm outside again. We call this Indian Summer (**ба́бине лі́то**). This is a wonderful time. People go to the park. They walk in the forest. The leaves have a beautiful color. It is a joyful period before winter. We really love these days.\nThe concept of Indian Summer is deeply embedded in Ukrainian folklore. It literally translates to "women\'s summer". Historically, this brief return of warm weather in late September or early October marked the end of the heavy agricultural harvest. It was a time when women could briefly rest and enjoy the mild sunshine before the harsh winter arrived. It remains a culturally significant season today.',
    'The concept of Indian Summer (**ба́бине лі́то**) is deeply embedded in Ukrainian folklore. Historically, this brief return of warm weather in late September or early October marked the end of the heavy agricultural harvest.'
)

# Зима та зимовий відпочинок
text = text.replace(
    'In winter it is very cold. It often snows. There is a lot of snow in the mountains. People ski. The nights are long and dark. The days are short. We warm ourselves by the fire. Winter is a time of rest. We celebrate holidays at home. We drink hot drinks.\n',
    ''
)

# Весна: Пробудження природи
text = text.replace(
    'In spring, nature wakes up. It becomes warm. The bright sun shines. Green leaves appear on the trees. Birds sing songs. The snow melts quickly. This is a time of new life. People work in the garden. The days become longer. We rejoice in spring. This is a wonderful period.\n',
    ''
)

# Літо: Спека та відпустки
text = text.replace(
    'In summer the days are very long. It is hot outside. We go to the sea. There we swim and sunbathe. We often walk in the evening. We eat fresh fruits. Summer is vacation time. Children do not go to school. Everyone loves summer. This is a warm and bright season.\n',
    ''
)

# Осінь: Врожай та прохолода
text = text.replace(
    'In autumn it often rains. It becomes cool and cloudy. Yellow leaves fall to the ground. We gather a rich harvest. The days become shorter. We prepare for winter. This is a time of calm. The air becomes fresh. We wear warm jackets. Autumn has its own character.\n',
    ''
)

# Природні ландшафти: Ліс
text = text.replace(
    'I really love the forest. It is always quiet in the forest. Tall trees grow there. The air there is very clean and fresh. We gather mushrooms in the autumn. Different animals live there. The forest gives calm. We often walk there with friends. This is the best place for rest.\nExploring natural objects like the forest is an important part of Ukrainian outdoor culture. The forest (**ліс**) provides shelter from the wind and sun. Foraging for mushrooms is a beloved national pastime. Knowing these landscape terms fulfills a key part of the language standards for navigating the environment and participating in local leisure activities.',
    'Exploring natural objects like the forest is an important part of Ukrainian outdoor culture. Foraging for mushrooms is a beloved national pastime.'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
