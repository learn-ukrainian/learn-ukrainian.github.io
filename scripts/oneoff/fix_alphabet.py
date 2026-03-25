import yaml
import re

# Fix Markdown
with open("curriculum/l2-uk-en/a1/completing-the-alphabet.md", "r") as f:
    md_text = f.read()

# Fix 1: IPA_BANNED
md_text = md_text.replace("phase: A1.1 [First Contact]", "phase: A1.1 (First Contact)")

# Fix 2: 'Завершуємо'
md_text = md_text.replace("Завершуємо алфавіт", "Кінець алфавіту")

# Fix 3: 'пройшли'
md_text = md_text.replace(
    "Ви вже пройшли великий шлях. You have come a long way. In Module 1,", 
    "Це великий крок. This is a big step. In Module 1,"
)

# Fix 4: 'вивчите'
md_text = md_text.replace(
    "Ви також вивчите африкати **Ц**, **Ч**, **Щ**.", 
    "Далі — африкати **Ц**, **Ч**, **Щ**. Next are the affricates **Ц**, **Ч**, **Щ**."
)

# Fix 5 & 6: 'зможете', 'прочитати'
md_text = md_text.replace(
    "Після цього модуля ви зможете прочитати все. After this module, you will be able to read *any* Ukrainian word.", 
    "Це фінал. This is the finale. After this module, you will be able to read *any* Ukrainian word."
)

# Fix 7: 'Уявіть'
md_text = md_text.replace(
    "Уявіть літеру без звуку. Imagine a letter with no sound of its own.", 
    "Imagine a letter with no sound of its own."
)

# Fix 8: 'бачите'
md_text = md_text.replace(
    "Коли ви бачите **Ь**, place your tongue closer to the roof of your mouth.", 
    "With the letter **Ь**, place your tongue closer to the roof of your mouth."
)

# Fix 9: 'Зверніть'
md_text = md_text.replace(
    "Зверніть увагу на правила.", 
    "Look at the rules."
)

# Fix 10, 11, 12: 'знаєте', 'Спробуйте', 'вимовити'
md_text = md_text.replace(
    "Ви вже знаєте вітання **Добрий день!** (Good day!). Now you see why there is a **Ь** at the end. The **Н** is soft. Спробуйте вимовити це.", 
    "Here is the greeting **Добрий день!** (Good day!). Now you see why there is a **Ь** at the end. The **Н** is soft. Try to pronounce this."
)

# Fix 13 & 14: 'пишеться', 'стоїть'
md_text = md_text.replace(
    "Апостроф пишеться після приголосних **Б**, **П**, **В**, **М**, **Ф**, **Р**. Він стоїть перед **Я**, **Ю**, **Є**, **Ї**.", 
    "Апостроф — після приголосних **Б**, **П**, **В**, **М**, **Ф**, **Р**. Апостроф — перед **Я**, **Ю**, **Є**, **Ї**."
)

# Fix 15: 'Зверніть'
md_text = md_text.replace(
    "Зверніть увагу. **м'ясо** (meat),", 
    "Notice this: **м'ясо** (meat),"
)

# Fix 16: 'Почніть', 'перейдіть'
md_text = md_text.replace(
    "Почніть зі звуку **Т**. Плавно перейдіть у **С**.", 
    "Start with the sound **Т**. Smoothly transition to **С**."
)
md_text = md_text.replace(
    "Почніть зі звуку «ш». Одразу додайте «ч.»", 
    "Start with the sound «ш». Immediately add «ч.»"
)

# Fix other verbs in instructions
md_text = md_text.replace(
    "Спробуйте вимовити ці слова.", 
    "Try to pronounce these words."
)
md_text = md_text.replace(
    "Не замінюйте **Щ** на звук «ш.»", 
    "Do not replace **Щ** with the sound «ш.»"
)
md_text = md_text.replace(
    "Пам'ятайте: **Щ** = **Ш** + **Ч**.", 
    "Remember: **Щ** = **Ш** + **Ч**."
)
md_text = md_text.replace(
    "Ви часто бачитимете **Ц** у закінченнях", 
    "You will often see **Ц** in endings"
)
md_text = md_text.replace(
    "Спробуйте прочитати цей текст.", 
    "Try to read this text."
)
md_text = md_text.replace(
    "Ви це зробили!", 
    "You did it!"
)
md_text = md_text.replace(
    "Ви можете прочитати будь-яке слово.", 
    "You can read any word."
)
md_text = md_text.replace(
    "Тепер ви знаєте всі літери.", 
    "Now you know all the letters."
)

# Fix 19: REDUNDANCY (Remove iframes)
# The safest way is to remove all iframes to eliminate the redundancy
md_text = re.sub(r'<iframe.*?</iframe>\n*', '', md_text)

with open("curriculum/l2-uk-en/a1/completing-the-alphabet.md", "w") as f:
    f.write(md_text)

# Fix YAML
with open("curriculum/l2-uk-en/a1/activities/completing-the-alphabet.yaml", "r") as f:
    yaml_text = f.read()

# Replace image-to-letter answers
yaml_text = yaml_text.replace("answer: ДЖ\n      distractors: [ДЗ, Ж]", "answer: Б\n      distractors: [Д, Ж]")
yaml_text = yaml_text.replace("answer: ДЗ\n      distractors: [ДЖ, З]", "answer: Д\n      distractors: [З, В]")
yaml_text = yaml_text.replace("answer: ДЗ\n      distractors: [ДЖ, С]", "answer: Д\n      distractors: [С, З]")

# Replace fill-in activity
old_fill_in = """- type: fill-in
  title: Читання фраз
  instruction: Заповніть пропуски в українських фразах.
  items:
    - sentence: До_рий день! (Good day!)
      answer: б
      options: [б, п, в, м]
    - sentence: Як спр_ви? (How are you?)
      answer: а
      options: [а, е, и, і]
    - sentence: До поб_чення! (Goodbye!)
      answer: а
      options: [а, о, у, е]
    - sentence: Д_кую! (Thank you!)
      answer: я
      options: [я, ю, є, і]
    - sentence: Будь л_ска! (Please!)
      answer: а
      options: [а, е, и, о]
    - sentence: Добрий р_нок! (Good morning!)
      answer: а
      options: [а, о, е, и]"""

new_fill_in = """- type: fill-in
  title: Читання фраз
  instruction: Заповніть пропуски в українських фразах.
  items:
    - sentence: "_____ день! (Good day!)"
      answer: Добрий
      options: [Добрий, Добре, Добра]
    - sentence: "Як _____? (How are you?)"
      answer: справи
      options: [справи, справа, справ]
    - sentence: "До _____! (Goodbye!)"
      answer: побачення
      options: [побачення, побачень, побачити]
    - sentence: "_____! (Thank you!)"
      answer: Дякую
      options: [Дякую, Дякуємо, Дякувати]
    - sentence: "Будь _____! (Please!)"
      answer: ласка
      options: [ласка, ласки, ласко]
    - sentence: "Добрий _____! (Good morning!)"
      answer: ранок
      options: [ранок, ранку, ранком]"""

yaml_text = yaml_text.replace(old_fill_in, new_fill_in)

with open("curriculum/l2-uk-en/a1/activities/completing-the-alphabet.yaml", "w") as f:
    f.write(yaml_text)

print("Done")
