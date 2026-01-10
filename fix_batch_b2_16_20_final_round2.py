
import yaml
import re
import os
import datetime

yaml_path_19 = "curriculum/l2-uk-en/b2/activities/19-register-official-legal.yaml"

# Schema Fix for M19
def fix_m19_schema():
    with open(yaml_path_19, 'r') as f:
        # Load safely to avoid date conversion if possible, but PyYAML converts automatically.
        # We need to process the loaded data.
        activities = yaml.safe_load(f)
    
    for act in activities:
        if act.get('title') == 'Основи офіційно-ділового стилю': # or relevant quiz
             for item in act.get('items', []):
                 for opt in item.get('options', []):
                     if isinstance(opt.get('text'), (datetime.date, datetime.datetime)):
                         opt['text'] = str(opt['text']) # Convert to string
    
    with open(yaml_path_19, 'w') as f:
        yaml.dump(activities, f, allow_unicode=True, sort_keys=False)
    print("Fixed M19 schema (date).")

# Unjumble Replacements (Expansion for remaining short items)
unjumble_expansions = {
    # M16
    "Шановний пане Коваленко!": "Шановний пане Коваленко! Дозвольте висловити Вам свою глибоку повагу.",
    "З повагою, Марія Петренко.": "З повагою та найкращими побажаннями, менеджер Марія Петренко.",
    "До побачення, до зустрічі.": "До побачення! Сподіваюся на швидку та приємну зустріч найближчим часом.",
    "Шановна пані директоре!": "Шановна пані директоре! Вітаю Вас з професійним святом.",
    
    # M17
    "Шановний пане директоре!": "Шановний пане директоре! Звертаюся до Вас із важливим питанням.",
    "З повагою Марія Петренко.": "З повагою та надією на відповідь, Марія Петренко.",
    
    # M19
    "З повагою, Марія Петренко.": "З повагою та найкращими побажаннями, директор Марія Петренко.",
    "Долучено до матеріалів справи.": "Всі зазначені документи офіційно долучено до матеріалів кримінальної справи.",
    "Шановний пане директоре!": "Шановний пане директоре! Прошу Вас розглянути мою заяву.",
    "Засідання оголошено закритим.": "Після голосування засідання ради було офіційно оголошено закритим.",
    "Слухали доповідь. Ухвалили.": "Слухали змістовну доповідь голови комісії. Ухвалили затвердити звіт.",
    "Кандидатуру обрано одноголосно.": "Запропоновану кандидатуру на посаду голови було обрано одноголосно.",
    
    # M20
    "Запивайте таблетки водою.": "Запивайте ці таблетки великою кількістю чистої негазованої води.",
    "Дотримуйтесь ліжкового режиму.": "Будь ласка, суворо дотримуйтесь ліжкового режиму протягом трьох днів.",
    "Робіть інгаляції двічі на день.": "Робіть парові інгаляції з лікувальними травами двічі на день.",
    "Якщо температура підніметься, приймайте жарознижувальне.": "Якщо температура тіла підніметься вище 38 градусів, негайно приймайте жарознижувальне."
}

# Quiz Prompt Expansions
quiz_patterns = [
    (r"Яка форма доречна (.*)\?", r"Яка з наведених граматичних форм є найбільш доречною та стилістично правильною \1?"),
    (r"Яке звертання (.*)\?", r"Яке з наведених звертань є офіційно прийнятим та найбільш шанобливим \1?"),
    (r"Яке слово (.*)\?", r"Яке з поданих слів або словосполучень найкраще відповідає значенню \1?"),
    (r"Яка формула (.*)\?", r"Яка мовна формула є стандартною та найбільш вживаною для \1?"),
    (r"Що означає (.*)\?", r"Поясніть значення: що саме означає термін або вираз \1?"),
    (r"Як правильно (.*)\?", r"Як граматично та стилістично правильно \1 згідно з нормами?"),
    (r"У якій ситуації (.*)\?", r"У якій із наведених комунікативних ситуацій буде доречно \1?"),
    (r"Яке прощання (.*)\?", r"Яке з наведених формулювань прощання є найбільш \1?"),
    (r"Який елемент (.*)\?", r"Який структурний елемент є обов'язковим та невід'ємним \1?"),
    (r"Чому (.*)\?", r"Поясніть причину: чому в офіційно-діловому стилі зазвичай \1?"),
    (r"Яка головна (.*)\?", r"Яка найголовніша та найбільш визначальна \1?"),
    (r"Який документ (.*)\?", r"Який офіційний документ зазвичай \1?"),
    (r"Яке питання (.*)\?", r"Яке стандартне питання зазвичай \1?"),
    (r"Яка різниця (.*)\?", r"У чому полягає принципова різниця між \1?")
]

def process_file(filepath):
    print(f"Processing {filepath}...")
    with open(filepath, 'r') as f:
        activities = yaml.safe_load(f)
    
    modified = False
    
    # Unjumble
    for act in activities:
        if act.get('type') == 'unjumble':
            for item in act.get('items', []):
                ans = item.get('answer', '')
                if ans in unjumble_expansions:
                    item['answer'] = unjumble_expansions[ans]
                    item['words'] = [w.strip(".,!?;") for w in unjumble_expansions[ans].split() if w.strip(".,!?;")]
                    modified = True

    # Quiz
    for act in activities:
        if act.get('type') in ['quiz', 'select']:
            for item in act.get('items', []):
                q = item.get('question', '')
                if len(q.split()) < 10:
                    matched = False
                    for pattern, repl in quiz_patterns:
                        if re.match(pattern, q):
                            item['question'] = re.sub(pattern, repl, q)
                            modified = True
                            matched = True
                            break
    
    if modified:
        with open(filepath, 'w') as f:
            yaml.dump(activities, f, allow_unicode=True, sort_keys=False)
        print("  Updated.")

# Run
fix_m19_schema()

import glob
for i in range(16, 21):
    path = f"curriculum/l2-uk-en/b2/activities/{i}-*.yaml"
    files = glob.glob(path)
    for f in files:
        process_file(f)
