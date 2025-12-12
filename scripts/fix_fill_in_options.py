#!/usr/bin/env python3
"""
Add missing > [!options] blocks to fill-in activities.
Extracts the correct answer and creates options with the answer + 2 distractors.
"""

import re
import sys
import os

# Common distractor pairs by category
DISTRACTORS = {
    # Cases
    'вітальні': ['спальні', 'кухні'],
    'спальні': ['вітальні', 'кабінеті'],
    'кухні': ['вітальні', 'ванній'],
    'шафі': ['комоді', 'тумбочці'],
    'диван': ['стілець', 'ліжко'],
    'Килим': ['Штори', 'Лампа'],
    'Прибираю': ['Готую', 'Ремонтую'],
    'Пилососю': ['Мию', 'Прасую'],
    'Витираю': ['Мию', 'Пилососю'],
    'Прасую': ['Перу', 'Сушу'],
    'кабінеті': ['вітальні', 'спальні'],
    # Nature
    'лісі': ['полі', 'горі'],
    'гору': ['долину', 'озеро'],
    'озера': ['моря', 'ріки'],
    'сонячно': ['хмарно', 'дощ'],
    'дощ': ['сніг', 'сонце'],
    'сніг': ['дощ', 'лід'],
    'Літо': ['Зима', 'Осінь'],
    'Восени': ['Влітку', 'Взимку'],
    'Навесні': ['Восени', 'Взимку'],
    'хмари': ['сонце', 'зорі'],
    'гроза': ['туман', 'вітер'],
    'пляжі': ['горі', 'лісі'],
    # Emotions
    'радість': ['сум', 'страх'],
    'сумно': ['радісно', 'весело'],
    'добрий': ['злий', 'сумний'],
    'смілива': ['боязлива', 'сором\'язлива'],
    'Хвилююся': ['Радію', 'Сумую'],
    'терплячий': ['нетерплячий', 'злий'],
    'задоволений': ['розчарований', 'сумний'],
    'розчарована': ['задоволена', 'щаслива'],
    'здивована': ['спокійна', 'байдужа'],
    'чесний': ['нечесний', 'брехливий'],
    'страшно': ['радісно', 'весело'],
    'щасливі': ['сумні', 'злі'],
    # Work
    'лікарем': ['вчителем', 'інженером'],
    'працює': ['відпочиває', 'спить'],
    'кар\'єра': ['робота', 'відпустка'],
    'зарплату': ['відпустку', 'підвищення'],
    'відпустка': ['робота', 'зарплата'],
    'підвищення': ['звільнення', 'відпустку'],
    'досвіду': ['роботи', 'зарплати'],
    'Керую': ['Працюю', 'Відпочиваю'],
    'співпрацюємо': ['працюємо', 'відпочиваємо'],
    'офісі': ['фабриці', 'лікарні'],
    'співбесіда': ['зустріч', 'робота'],
    # Default fallback
    'default': ['варіант А', 'варіант Б'],
}

def get_distractors(answer):
    """Get 2 distractors for a given answer."""
    # Clean answer
    clean = answer.strip().rstrip('.,!?')
    
    if clean in DISTRACTORS:
        return DISTRACTORS[clean]
    
    # Try lowercase
    if clean.lower() in DISTRACTORS:
        return DISTRACTORS[clean.lower()]
    
    # Generate generic distractors based on the answer
    return ['варіант А', 'варіант Б']

def add_options_to_fill_in(filepath):
    """Add missing [!options] blocks to fill-in activities."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    modified = False
    new_lines = []
    in_fill_in = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Detect fill-in activity header
        if stripped.startswith('## fill-in:'):
            in_fill_in = True
            new_lines.append(line)
            i += 1
            continue
        
        # Exit fill-in section on next ## header
        if stripped.startswith('## ') and not stripped.startswith('## fill-in:'):
            in_fill_in = False
            new_lines.append(line)
            i += 1
            continue
        
        # In fill-in section, look for answer blocks without options
        if in_fill_in and stripped.startswith('> [!answer]'):
            answer_match = re.match(r'>\s*\[!answer\]\s*(.+)$', stripped)
            if answer_match:
                answer = answer_match.group(1).strip()
                new_lines.append(line)
                
                # Check if next line already has options
                if i + 1 < len(lines) and '> [!options]' in lines[i + 1]:
                    # Already has options, skip
                    i += 1
                    continue
                
                # Add options block
                distractors = get_distractors(answer)
                options = f"   > [!options] {answer} | {distractors[0]} | {distractors[1]}"
                new_lines.append(options)
                modified = True
                i += 1
                continue
        
        new_lines.append(line)
        i += 1
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        print(f"  ✅ Added options blocks to {os.path.basename(filepath)}")
        return True
    
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fix_fill_in_options.py <file.md> [file2.md ...]")
        sys.exit(1)
    
    total_fixed = 0
    for filepath in sys.argv[1:]:
        if add_options_to_fill_in(filepath):
            total_fixed += 1
    
    print(f"\n✅ Added options to fill-in activities in {total_fixed} files.")

if __name__ == "__main__":
    main()
