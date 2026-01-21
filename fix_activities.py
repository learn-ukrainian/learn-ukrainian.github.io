#!/usr/bin/env python3
"""Fix M94 activities 7 and 11 structure."""

import yaml

# Read current activities
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'r') as f:
    activities = yaml.safe_load(f)

# Fix Activity 7 - Convert from ordering task to proper unjumble with words array
# Change from slide ordering to sentence unscrambling for presentation topics
activity_7 = {
    'type': 'unjumble',
    'title': 'Структура презентації - Розташуйте речення',
    'instruction': 'Розташуйте слова в правильному порядку.',
    'items': [
        {
            'words': ['презентації', 'є', 'структура', 'ефективної', 'ключем', 'успіху', 'чітка', 'до'],
            'answer': 'Чітка структура є ключем до успіху ефективної презентації.'
        },
        {
            'words': ['слайд', 'організацію', 'титульний', 'автора', 'містить', 'назву', 'дату', 'та'],
            'answer': 'Титульний слайд містить назву, автора, дату та організацію.'
        },
        {
            'words': ['актуальність', 'теми', 'вступ', 'мету', 'контекст', 'розкриває', 'та'],
            'answer': 'Вступ розкриває актуальність теми, контекст та мету.'
        },
        {
            'words': ['даних', 'основна', 'графіками', 'таблицями', 'частина', 'з', 'підтверджується', 'та'],
            'answer': 'Основна частина підтверджується даних з графіками та таблицями.'
        },
        {
            'words': ['ключові', 'результати', 'висновки', 'дослідження', 'основі', 'формулюють', 'даних', 'на'],
            'answer': 'Результати дослідження формулюють ключові висновки на основі даних.'
        },
        {
            'words': ['рекомендації', 'пропозиції', 'конкретні', 'містять', 'дій', 'щодо'],
            'answer': 'Рекомендації містять конкретні пропозиції щодо дій.'
        },
        {
            'words': ['головних', 'висновки', 'тез', 'підсумовують', 'презентації', 'всі'],
            'answer': 'Висновки підсумовують всі головні тези презентації.'
        },
        {
            'words': ['слайд', 'контактний', 'подальшої', 'для', 'співпраці', 'інформацію', 'містить'],
            'answer': 'Контактний слайд містить інформацію для подальшої співпраці.'
        },
        {
            'words': ['питання', 'аудиторії', 'запрошення', 'до', 'відповіді', 'діалогу', 'та', 'це'],
            'answer': 'Питання та відповіді — це запрошення аудиторії до діалогу.'
        },
        {
            'words': ['візуальні', 'презентації', 'підвищують', 'ефективність', 'елементи'],
            'answer': 'Візуальні елементи підвищують ефективність презентації.'
        },
        {
            'words': ['має', 'логічною', 'бути', 'послідовною', 'презентація', 'та'],
            'answer': 'Презентація має бути логічною та послідовною.'
        },
        {
            'words': ['слайдах', 'багато', 'тексту', 'уникайте', 'на'],
            'answer': 'Уникайте багато тексту на слайдах.'
        },
        {
            'words': ['завжди', 'джерела', 'вказуйте', 'даних'],
            'answer': 'Завжди вказуйте джерела даних.'
        }
    ]
}

activities[6] = activity_7

# Fix Activity 11 - Add blanks count
# Count the {option|option|...} patterns in the text
text = activities[10]['text']
blanks_count = text.count('{')

activities[10]['blanks'] = blanks_count

# Write back
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'w') as f:
    yaml.dump(activities, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print(f"✅ Fixed Activity 7 (unjumble) - added 13 items with proper words arrays")
print(f"✅ Fixed Activity 11 (cloze) - added blanks: {blanks_count}")
