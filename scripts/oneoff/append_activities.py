import yaml

with open('curriculum/l2-uk-en/a1/activities/imperative-and-requests.yaml', 'r', encoding='utf-8') as f:
    content = f.read()

new_activities = """
- type: quiz
  title: Negative Commands Quiz
  instruction: Select the correct negative command form.
  items:
  - question: How do you tell a friend not to look?
    explanation: Use 'не' before the informal imperative form.
    options:
    - text: не дивись
      correct: true
    - text: не дивіться
      correct: false
    - text: не дивитися
      correct: false
    - text: не дивлюсь
      correct: false
  - question: How do you formally tell a group not to wait?
    explanation: Use 'не' before the formal imperative form.
    options:
    - text: не чекайте
      correct: true
    - text: не чекай
      correct: false
    - text: не чекати
      correct: false
    - text: чекати не
      correct: false
  - question: Which form is correct for 'Do not read here' (informal)?
    explanation: The negative particle 'не' comes right before the imperative.
    options:
    - text: не читай тут
      correct: true
    - text: читай не тут
      correct: false
    - text: не читати тут
      correct: false
    - text: не читаю тут
      correct: false
  - question: How do you formally ask someone not to stand?
    explanation: Formal imperative with 'не'.
    options:
    - text: не стійте
      correct: true
    - text: не стій
      correct: false
    - text: не стояти
      correct: false
    - text: стійте не
      correct: false
- type: match-up
  title: Polite Requests
  pairs:
  - left: Help, please.
    right: Допоможіть, будь ласка.
  - left: Give this, please.
    right: Дайте це, будь ласка.
  - left: Say this, please.
    right: Скажіть це, будь ласка.
  - left: Please, listen.
    right: Будь ласка, слухай.
  - left: Please show this word.
    right: Покажіть це слово, будь ласка.
  instruction: З'єднайте англійські та українські фрази.
- type: fill-in
  title: Complete the Negative Commands
  items:
  - sentence: ___ іди туди.
    answer: Не
    options:
    - Не
    - Ні
    - Нічого
    - Немає
  - sentence: Не ___! Там машина.
    answer: ідіть
    options:
    - ідіть
    - іти
    - іду
    - іде
  - sentence: Не ___ це, будь ласка.
    answer: пишіть
    options:
    - пишіть
    - писати
    - пишу
    - пишете
  - sentence: Не ___ сюди!
    answer: дивись
    options:
    - дивись
    - дивитися
    - дивлюсь
    - дивляться
  instruction: Оберіть правильне слово для заповнення пропуску.
"""

with open('curriculum/l2-uk-en/a1/activities/imperative-and-requests.yaml', 'a', encoding='utf-8') as f:
    f.write(new_activities)
