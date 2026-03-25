import yaml
import sys

data = """
- type: 'watch-and-repeat'
  title: 'Pronunciation Overview'
  items:
    - video: 'https://www.youtube.com/watch?v=ksXIXj7CXwc'
      letter: 'Alphabet'
      word: 'Абетка'
- type: 'classify'
  title: 'Familiar vs. False Friends'
  instruction: 'Sort these letters into the correct group.'
  categories:
    - label: 'Familiar'
      items: ['А', 'О', 'К', 'М', 'Т', 'Е']
    - label: 'False Friends'
      items: ['В', 'Н', 'Р', 'С', 'У', 'Х']
- type: 'match-up'
  title: 'Match the False Friend'
  instruction: 'Match the Cyrillic false friend letter to its actual sound.'
  pairs:
    - left: 'В'
      right: 'v'
    - left: 'Н'
      right: 'n'
    - left: 'Р'
      right: 'rolled r'
    - left: 'С'
      right: 's'
    - left: 'У'
      right: 'oo'
    - left: 'Х'
      right: 'heavy h'
- type: 'quiz'
  title: 'Vocabulary Check'
  instruction: 'How do you say these words in Ukrainian?'
  items:
    - question: "How do you say 'water'?"
      options:
        - text: 'вода'
          correct: true
        - text: 'рука'
          correct: false
        - text: 'хата'
          correct: false
        - text: 'ніс'
          correct: false
    - question: "How do you say 'hand'?"
      options:
        - text: 'рука'
          correct: true
        - text: 'сон'
          correct: false
        - text: 'книга'
          correct: false
        - text: 'школа'
          correct: false
    - question: "How do you say 'book'?"
      options:
        - text: 'книга'
          correct: true
        - text: 'місто'
          correct: false
        - text: 'зима'
          correct: false
        - text: 'аптека'
          correct: false
    - question: "How do you say 'school'?"
      options:
        - text: 'школа'
          correct: true
        - text: 'банк'
          correct: false
        - text: 'метро'
          correct: false
        - text: 'пошта'
          correct: false
    - question: "How do you say 'city'?"
      options:
        - text: 'місто'
          correct: true
        - text: 'зима'
          correct: false
        - text: 'дім'
          correct: false
        - text: 'зупинка'
          correct: false
    - question: "How do you say 'winter'?"
      options:
        - text: 'зима'
          correct: true
        - text: 'мама'
          correct: false
        - text: 'тато'
          correct: false
        - text: 'кафе'
          correct: false
- type: 'fill-in'
  title: 'Complete the Word'
  instruction: 'Fill in the missing letter to complete the Ukrainian word.'
  items:
    - sentence: 'This is water: _ода'
      answer: 'в'
      options: ['в', 'б', 'д', 'м']
    - sentence: 'This is a hand: _ука'
      answer: 'р'
      options: ['р', 'п', 'с', 'н']
    - sentence: 'This is a traditional house: _ата'
      answer: 'х'
      options: ['х', 'к', 'г', 'ж']
    - sentence: 'This is a book: кни_а'
      answer: 'г'
      options: ['г', 'ґ', 'х', 'д']
    - sentence: 'This is a school: _кола'
      answer: 'ш'
      options: ['ш', 'щ', 'ч', 'ц']
    - sentence: 'This is the metro: ме_ро'
      answer: 'т'
      options: ['т', 'п', 'г', 'н']
- type: 'quiz'
  title: 'Sound Recognition'
  instruction: 'Which letter makes this sound?'
  vesum_exempt: true
  items:
    - question: "Which letter sounds like the 's' in 'pleasure'?"
      options:
        - text: 'Ж'
          correct: true
        - text: 'Ш'
          correct: false
        - text: 'Щ'
          correct: false
        - text: 'З'
          correct: false
    - question: "Which letter sounds like the 'ts' in 'cats'?"
      options:
        - text: 'Ц'
          correct: true
        - text: 'Ч'
          correct: false
        - text: 'С'
          correct: false
        - text: 'Т'
          correct: false
    - question: "Which letter sounds like the 'ch' in 'church'?"
      options:
        - text: 'Ч'
          correct: true
        - text: 'Ш'
          correct: false
        - text: 'Щ'
          correct: false
        - text: 'Ц'
          correct: false
    - question: "Which letter sounds like the 'sh' in 'ship'?"
      options:
        - text: 'Ш'
          correct: true
        - text: 'Ж'
          correct: false
        - text: 'Щ'
          correct: false
        - text: 'С'
          correct: false
    - question: "Which letter sounds like 'sh' and 'ch' said together smoothly?"
      options:
        - text: 'Щ'
          correct: true
        - text: 'Ш'
          correct: false
        - text: 'Ч'
          correct: false
        - text: 'Ж'
          correct: false
    - question: "Which letter makes a hard 'g' sound, like in 'go'?"
      options:
        - text: 'Ґ'
          correct: true
        - text: 'Г'
          correct: false
        - text: 'К'
          correct: false
        - text: 'Х'
          correct: false
"""

try:
    yaml.safe_load(data)
    print("YAML is valid")
except Exception as e:
    print(f"YAML error: {e}")
