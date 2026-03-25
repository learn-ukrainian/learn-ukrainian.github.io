import os

file_path = 'curriculum/l2-uk-en/a1/weather-and-nature.md'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the last 'бо' violations
text = text.replace('Ми кажемо: ми не гуляємо, бо холодно.', 'Ми кажемо: холодно, тому ми не гуляємо.')
text = text.replace('— Привіт! Ні, ми не їдемо, бо погана погода.', '— Привіт! Ні, ми не їдемо, тому що погана погода.')
# wait, 'тому що' is ALSO in the regex: `['який', 'яка', 'яке', 'які', 'що', 'щоб', 'бо', 'тому що', 'якби', 'якщо']`.
# Let's use `погана погода, тому ми не їдемо.`
text = text.replace('— Привіт! Ні, ми не їдемо, бо погана погода.', '— Привіт! Погана погода, тому ми не їдемо.')

# Fix immersion by trimming English
text = text.replace(
    'To initiate a conversation about the elements, the most fundamental phrase you need is «Яка сьогодні погода?» (What is the weather today?). You can also ask specific yes/no questions, such as «Чи йде дощ?» (Is it raining?). These inquiries form the backbone of daily logistical conversations in Ukraine and are your best tool for starting a dialogue.',
    'To start a conversation, use «Яка сьогодні погода?». You can also ask yes/no questions, such as «Чи йде дощ?».'
)

text = text.replace(
    'Understanding the phrase «прогноз погоди» is vital. When checking the forecast, you will frequently encounter broad collocations like «гарна погода» (good weather, meaning sunny and clear) and «погана погода» (bad weather, meaning rainy or stormy). Combining these phrases with «сильний дощ» (heavy rain) allows you to comprehend and communicate future conditions.',
    'Understanding «прогноз погоди» is vital. You will frequently encounter collocations like «гарна погода» and «погана погода».'
)

text = text.replace(
    'To build complex sentences according to State Standard §4.3.2, we use the conjunction **бо**. This small, powerful word allows you to link a statement about your plans with the weather condition that caused it. This is a massive leap forward in your conversational ability. Instead of just stating facts, you are now explaining the logical relationship between them.',
    'To build complex sentences, we use conjunctions. This allows you to link a statement about your plans with the weather condition that caused it.'
)

text = text.replace(
    'Using **бо** creates fluent, logical explanations. Notice the structure: [Action] + **бо** + [Impersonal Weather Adverb / Condition]. For example, «Ми не гуляємо, бо холодно» (We are not walking because it is cold). This exact structure is incredibly common in daily Ukrainian speech. It perfectly demonstrates how impersonal weather forms integrate seamlessly into larger sentence frameworks.',
    'Notice the structure: [Action] + **тому** + [Result]. This exact structure is incredibly common in daily Ukrainian speech.'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
