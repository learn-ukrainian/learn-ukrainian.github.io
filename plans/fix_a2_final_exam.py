import re

import yaml

md_path = "curriculum/l2-uk-en/a2/a2-final-exam.md"
with open(md_path, encoding="utf-8") as f:
    text = f.read()

# 1. Participles
text = text.replace("бажаний **сертифіка́т**", "важливий **сертифіка́т**")
text = text.replace("Якщо дія має завершений, успішний результат", "Якщо дія має фінальний, успішний результат")

# 2. Sentence too long
old_sentence = "І найголовніше, ви дізналися про культурне значення слова «скласти іспит» та роль ЗНО/НМТ як антикорупційного стандарту в Україні."
new_sentence = "І найголовніше, ви дізналися про культурне значення слова «скласти іспит». Ви зрозуміли роль ЗНО/НМТ як антикорупційного стандарту в Україні."
text = text.replace(old_sentence, new_sentence)

# 3. Metalanguage inline English
text = text.replace("Недоконаний вид (Imperfective aspect)", "Недоконаний вид")
text = text.replace("Доконаний вид (Perfective aspect)", "Доконаний вид")
text = text.replace("наказовий спосіб (Imperative mood)", "наказовий спосіб")

# 4. Transliteration
text = text.replace("| Відмінок (Case) |", "| Відмінок |")
text = text.replace("Відмінок (Case)", "Відмінок")

# 5. Robotic structure
old_robotic = "Ми відповідаємо не на папір. Ми відповідаємо живому викладачу. Тут починає працювати давальний відмінок (Dative). Ми відповідаємо (кому?) викладачу, професору, другу."
new_robotic = "Студент відповідає не на папір. Він говорить живому викладачу. Тут починає працювати давальний відмінок (Dative). Студент відповідає (кому?) професору, другу."
text = text.replace(old_robotic, new_robotic)

# In case my regex/replace above fails to match exactly, I'll do partial:
text = text.replace("Ми відповідаємо не на папір. Ми відповідаємо живому викладачу.", "Студент відповідає не на папір. Він говорить живому викладачу.")
text = text.replace("Ми відповідаємо (кому?) викладачу, професору, другу.", "Студент відповідає (кому?) професору, другу.")

# 6. Engagement callout formats (remove [!tip] > to > [!tip])
text = re.sub(r'\[!([a-z-]+)\]\n>\s*\*\*', r'> [!\1]\n> **', text)

# 7. Checkpoint Format Errors
# Replace Headers in Skill 1
text = text.replace("### Діалог: Студенти говорять про тести", "### Модель: Студенти говорять про тести")
# insert Practice and Self-Check before Skill 2
skill1_end = "Я сподіваюся на гарну оцінку."
skill1_insert = f"""{skill1_end}

### Практика: Відмінки
Прочитайте діалог ще раз. Знайдіть усі слова в знахідному відмінку.

### Самоперевірка
Який відмінок ми використовуємо для живої людини (наприклад, викладача)?
"""
text = text.replace(skill1_end, skill1_insert)

# Skill 2
text = text.replace("### Ситуація: У класі", "### Модель: У класі")
skill2_end = "Я хочу успішно скласти цей тест."
skill2_insert = f"""{skill2_end}

### Практика: Процес чи результат
Подумайте про свої дії сьогодні. Скажіть два речення: одне про процес, друге про результат.

### Самоперевірка
Чому слово «складав» ніколи не означає «I passed»?
"""
text = text.replace(skill2_end, skill2_insert)

# Skill 3
text = text.replace("### Діалог: Де моя аудиторія?", "### Модель: Де моя аудиторія?")
skill3_end = "Бажаю успішно скласти іспит!"
skill3_insert = f"""{skill3_end}

### Практика: Навігація
Поясніть своєму другу українською мовою, як пройти до центру НМТ.

### Самоперевірка
Що означає слово «прямувати» і з яким прийменником ми його використовуємо?
"""
text = text.replace(skill3_end, skill3_insert)

with open(md_path, "w", encoding="utf-8") as f:
    f.write(text)

# Fix Activities
act_path = "curriculum/l2-uk-en/a2/activities/a2-final-exam.yaml"
try:
    with open(act_path, encoding="utf-8") as f:
        acts = yaml.safe_load(f)
    for act in acts:
        if act.get('id') == 'mark-the-words-a2-final-exam-9':
            if len(act['items']) == 4:
                act['items'].extend([
                    "Студенти {прямують} до центру тестування.",
                    "Я {отримав} сертифікат після іспиту."
                ])
                print("Added items to activity")
    with open(act_path, "w", encoding="utf-8") as f:
        yaml.dump(acts, f, allow_unicode=True, sort_keys=False)
except Exception as e:
    print(f"Error updating activities: {e}")

# Add vocab words
vocab_path = "curriculum/l2-uk-en/a2/vocabulary/a2-final-exam.yaml"
try:
    with open(vocab_path, encoding="utf-8") as f:
        voc = yaml.safe_load(f)

    new_vocabs = [
        {"lemma": "недоконаний", "ipa": "[nɛdɔˈkɔnɑnɪj]", "translation": "imperfective (aspect)", "pos": "adj"},
        {"lemma": "родовий", "ipa": "[rɔdɔˈʋɪj]", "translation": "genitive (case)", "pos": "adj"},
        {"lemma": "вид", "ipa": "[ʋɪd]", "translation": "aspect", "pos": "noun", "gender": "m"},
        {"lemma": "доконаний", "ipa": "[dɔˈkɔnɑnɪj]", "translation": "perfective (aspect)", "pos": "adj"},
        {"lemma": "орудний", "ipa": "[ɔˈrudnɪj]", "translation": "instrumental (case)", "pos": "adj"},
        {"lemma": "знахідний", "ipa": "[znɑxʲiˈdnɪj]", "translation": "accusative (case)", "pos": "adj"},
        {"lemma": "давальний", "ipa": "[dɑˈʋɑlʲnɪj]", "translation": "dative (case)", "pos": "adj"}
    ]
    voc['items'].extend(new_vocabs)
    with open(vocab_path, "w", encoding="utf-8") as f:
        yaml.dump(voc, f, allow_unicode=True, sort_keys=False)
    print("Added vocab")
except Exception as e:
    print(f"Error updating vocab: {e}")

