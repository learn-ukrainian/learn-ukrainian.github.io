import re

md_file = 'curriculum/l2-uk-en/a1/imperative-and-requests.md'
yaml_file = 'curriculum/l2-uk-en/a1/activities/imperative-and-requests.yaml'

with open(md_file, 'r') as f:
    content = f.read()

content = content.replace(
"""- **Будь ласка, допоможіть.** — Please help.
- **Дайте, будь ласка, час.** — Give time, please.
- **Покажіть, будь ласка.** — Show, please.
- **Чекайте там, будь ласка.** — Wait there, please.
- **Візьміть, будь ласка, це.** — Take this, please.
- **Слухайте, будь ласка, це.** — Listen to this, please.""",
"""Порівняйте (Compare):

- **Будь ласка, допоможіть.** — Please help.
- **Дайте, будь ласка, час.** — Give time, please.
- **Покажіть, будь ласка.** — Show, please.
- **Читайте, будь ласка, текст.** — Read the text, please.
- **Пишіть, будь ласка, тут.** — Write here, please.
- **Слухайте, будь ласка, це.** — Listen to this, please."""
)

content = content.replace(
'When you want to tell someone to do something, you use the imperative mood. This is the grammatical form we use for giving commands, offering instructions, or making direct requests in daily life. In English, we simply use the base form of the verb without any special changes or suffixes.',
'When you want to tell someone to do something, you use the imperative mood (наказовий спосіб). This is the grammatical form we use for giving commands (команди), offering instructions (інструкції), or making direct requests (прохання) in daily life. In English, we simply use the base form of the verb (дієслово) without any special changes or suffixes.'
)

content = content.replace(
'addressing one person informally, or addressing multiple people or someone formally.',
'addressing one person informally (на ти), or addressing multiple people or someone formally (на ви).'
)

content = content.replace(
'a core set of eight essential verbs. These are the absolute most common actions you will need',
'a core set of eight essential verbs (вісім дієслів). These are the absolute most common actions (дії) you will need'
)

content = content.replace(
'While using the formal plural ending is absolutely necessary for basic respect, it is often not quite enough',
'While using the formal plural ending (закінчення) is absolutely necessary for basic respect (повага), it is often not quite enough'
)

content = content.replace(
'This is grammatically called a prohibition or a negative command. Forming a negative command is an incredibly straightforward and simple process in Ukrainian. You simply take the standard command form that you have just learned and place the short negative particle directly in front of it.',
'This is grammatically called a prohibition or a negative command (заборона). Forming a negative command is an incredibly straightforward and simple process in Ukrainian. You simply take the standard command form that you have just learned and place the short negative particle (частка) directly in front of it.'
)

content = content.replace(
'The command form usually ends in a specific letter or vowel that clearly indicates the command is personal and direct.\n\n| Інфінітив',
'The command form usually ends in a specific letter or vowel that clearly indicates the command is personal and direct.\n\nНаприклад (For example):\n\n| Інфінітив'
)

content = content.replace(
'This extra ending acts as a crucial marker of respect or plurality.\n\n- **Читай',
'This extra ending acts as a crucial marker of respect or plurality.\n\nПорівняйте (Compare):\n\n- **Читай'
)

content = content.replace(
'solid foundation for classroom interactions and basic daily navigation in a Ukrainian-speaking environment. \n\n| Ukrainian',
'solid foundation for classroom interactions and basic daily navigation in a Ukrainian-speaking environment. \n\nНаприклад (For example):\n\n| Ukrainian'
)

content = content.replace(
'regular conjugation pattern. \n\n| Ukrainian Sentence',
'regular conjugation pattern. \n\nНаприклад (For example):\n\n| Ukrainian Sentence'
)

content = content.replace(
'request that people will be happy to fulfill.\n\n| Command | Polite Request',
'request that people will be happy to fulfill.\n\nНаприклад (For example):\n\n| Command | Polite Request'
)

content = content.replace(
'telling the person to avoid doing it entirely.\n\n| Positive',
'telling the person to avoid doing it entirely.\n\nПорівняйте (Compare):\n\n| Positive'
)

content = content.replace(
'particle right before the verb to change the meaning.\n\n- **Не чекай там.',
'particle right before the verb to change the meaning.\n\nНаприклад (For example):\n\n- **Не чекай там.'
)

with open(md_file, 'w') as f:
    f.write(content)

yaml_append = """
- type: fill-in
  title: Complete the polite requests
  items:
  - sentence: Скажіть, ___ ласка.
    answer: будь
    options:
    - будь
    - прошу
    - не
    - дай
  - sentence: ___, будь ласка.
    answer: Скажіть
    options:
    - Скажіть
    - Сказати
    - Кажу
    - Каже
  - sentence: ___ це, будь ласка.
    answer: Покажіть
    options:
    - Покажіть
    - Показати
    - Покажу
    - Покаже
  - sentence: Допоможіть, будь ___.
    answer: ласка
    options:
    - ласка
    - ласку
    - ласки
    - будь
  - sentence: ___ тут, будь ласка.
    answer: Чекайте
    options:
    - Чекайте
    - Чекати
    - Чекаю
    - Чекаємо
  - sentence: ___ це слово, будь ласка.
    answer: Пишіть
    options:
    - Пишіть
    - Писати
    - Пишу
    - Пишемо
  - sentence: ___, будь ласка.
    answer: Допоможіть
    options:
    - Допоможіть
    - Допомогти
    - Допомагаю
    - Допомагає
  - sentence: ___ там, будь ласка.
    answer: Стійте
    options:
    - Стійте
    - Стояти
    - Стою
    - Стоїмо
  instruction: Оберіть правильне слово для заповнення пропуску.
- type: unjumble
  title: Put the negative commands in order
  items:
  - words:
    - Не
    - читай
    - це
    answer: Не читай це
  - words:
    - Не
    - дивіться
    - там
    answer: Не дивіться там
  - words:
    - Не
    - пишіть
    - це
    answer: Не пишіть це
  - words:
    - Не
    - стійте
    - тут
    answer: Не стійте тут
  - words:
    - Не
    - ідіть
    - там
    answer: Не ідіть там
  - words:
    - Не
    - слухай
    - це
    answer: Не слухай це
  - words:
    - Не
    - чекайте
    - там
    answer: Не чекайте там
  - words:
    - Не
    - пишіть
    - тут
    answer: Не пишіть тут
  instruction: Розташуйте слова у правильному порядку.
- type: quiz
  title: Choose the correct translation
  items:
  - question: Translate "Please give."
    explanation: Дайте, будь ласка means please give.
    options:
    - text: Дайте, будь ласка
      correct: true
    - text: Скажіть, будь ласка
      correct: false
    - text: Дай
      correct: false
    - text: Дати
      correct: false
  - question: Translate "Do not read."
    explanation: Не читайте is the negative command.
    options:
    - text: Не читайте
      correct: true
    - text: Читайте
      correct: false
    - text: Не писати
      correct: false
    - text: Не пишіть
      correct: false
  - question: Translate "Wait here, please."
    explanation: Чекайте тут, будь ласка means wait here, please.
    options:
    - text: Чекайте тут, будь ласка
      correct: true
    - text: Стійте тут
      correct: false
    - text: Чекайте там
      correct: false
    - text: Ідіть тут
      correct: false
  - question: Translate "Please look."
    explanation: Дивіться, будь ласка means please look.
    options:
    - text: Дивіться, будь ласка
      correct: true
    - text: Слухайте, будь ласка
      correct: false
    - text: Не дивіться
      correct: false
    - text: Дивитися
      correct: false
  - question: Translate "Say this word."
    explanation: Скажіть це слово means say this word.
    options:
    - text: Скажіть це слово
      correct: true
    - text: Пишіть це слово
      correct: false
    - text: Читайте це
      correct: false
    - text: Скажіть там
      correct: false
  - question: Translate "Do not stand here."
    explanation: Не стійте тут means do not stand here.
    options:
    - text: Не стійте тут
      correct: true
    - text: Стійте тут
      correct: false
    - text: Не ідіть там
      correct: false
    - text: Чекайте там
      correct: false
  - question: Translate "Listen to this, please."
    explanation: Слухайте це, будь ласка means listen to this, please.
    options:
    - text: Слухайте це, будь ласка
      correct: true
    - text: Дивіться на це
      correct: false
    - text: Не слухайте
      correct: false
    - text: Слухати
      correct: false
  - question: Translate "Go there."
    explanation: Ідіть там means go there.
    options:
    - text: Ідіть там
      correct: true
    - text: Стійте там
      correct: false
    - text: Ідіть тут
      correct: false
    - text: Не ідіть
      correct: false
  instruction: Оберіть правильний переклад.
"""

with open(yaml_file, 'a') as f:
    f.write(yaml_append)
