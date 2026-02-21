
import os

files = [
    'curriculum/l2-uk-en/c1/38-volodymyr-velykii.md',
    'curriculum/l2-uk-en/c1/39-kniaz-yaroslav-mudryi.md',
    'curriculum/l2-uk-en/c1/40-knyazhna-anna-yaroslavna.md'
]

content = """
Щоб закріпити матеріал, рекомендуємо:

1.  **Візуалізація:** Знайдіть портрети правителя у різних джерелах (літописи, монети, сучасні картини). Порівняйте їх.
2.  **Читання:** Прочитайте уривок з літопису про діяльність князя в оригіналі або адаптації.
3.  **Дискусія:** Обговоріть з партнером, як дії цього правителя вплинули на сучасну карту Європи.
4.  **Есе:** Напишіть короткий роздум на тему "Уроки історії: лідерство та відповідальність".

> [!resources]
>
> - [Енциклопедія історії України](http://history.org.ua) — біографічні відомості.
> - [Ізборник](http://litopys.org.ua) — тексти літописів.
> - [YouTube: Історія України](https://youtube.com) — відеолекції про епоху.
"""

for file_path in files:
    if not os.path.exists(file_path):
        continue
        
    with open(file_path, 'r') as f:
        file_content = f.read()
    
    # Check if section is empty
    if "## Потрібно більше практики?\n\n" in file_content and "## Потрібно більше практики?\n\nЩоб" not in file_content:
         # It's explicitly empty (just header)
         # Find where to insert
         parts = file_content.split("## Потрібно більше практики?")
         if len(parts) > 1:
             new_content = parts[0] + "## Потрібно більше практики?" + content + parts[1]
             with open(file_path, 'w') as f:
                 f.write(new_content)
             print(f"Filled section in {file_path}")
    elif "## Потрібно більше практики?" in file_content:
        # Check if already filled (heuristically)
        if "Щоб закріпити" not in file_content:
             # Append content
             with open(file_path, 'a') as f:
                 f.write("\n" + content)
             print(f"Appended section to {file_path}")
