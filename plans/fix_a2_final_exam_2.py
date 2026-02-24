import re
import yaml

md_path = "curriculum/l2-uk-en/a2/a2-final-exam.md"
with open(md_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Euphony
text = text.replace("в знахідному", "у знахідному")

# 2. Transliteration
text = text.replace("Питання (Questions)", "Питання")

# 3. Robotic sentences: "ви можете..."
# In "Деколонізація: Здати чи скласти?"
text = text.replace("Ви можете здати гроші. Ви можете здати старий папір.", "Людина може здати гроші. Також є можливість здати старий папір.")
# In "Слова для успіху та невдачі"
text = text.replace("Ви можете **отримати високу оцінку**. Ви можете **успішно завершити** курс. Ви можете **отримати сертифікат**.",
                    "Студент здатний **отримати високу оцінку**. Він може **успішно завершити** курс. Ще один варіант — **отримати сертифікат**.")

with open(md_path, "w", encoding="utf-8") as f:
    f.write(text)

# Fix Activities
act_path = "curriculum/l2-uk-en/a2/activities/a2-final-exam.yaml"
with open(act_path, "r", encoding="utf-8") as f:
    acts = yaml.safe_load(f)

for act in acts:
    if act.get('title') == 'Знайдіть дієслова' or act.get('type') == 'mark-the-words':
        if len(act.get('answers', [])) == 4:
            act['text'] += " Студент прямує додому. Він посміхається."
            act['answers'].extend(["прямує", "посміхається"])
            print("Fixed mark-the-words")

with open(act_path, "w", encoding="utf-8") as f:
    yaml.dump(acts, f, allow_unicode=True, sort_keys=False)

