import subprocess

words_m08 = [
    "стіл", "книга", "вікно", "кімната", "ліжко", "стілець", 
    "лампа", "телефон", "комп'ютер", "він", "вона", "воно", 
    "зошит", "ручка", "сумка", "крісло", "дзеркало", "ключ", 
    "фото", "стіна"
]
words_m09 = [
    "який", "яка", "яке", "великий", "маленький", "новий", 
    "старий", "гарний", "чистий", "дорогий", "дешевий", 
    "поганий", "брудний", "світлий", "темний", "а", "але", "рюкзак", "речі"
]

print("=== M08 Words ===")
for w in words_m08:
    res = subprocess.run(["python", "scripts/rag/query.py", "word", w], capture_output=True, text=True)
    if "✅" not in res.stdout:
        print(f"FAILED: {w}")
    else:
        # Just check the first line or so to confirm it's found
        print(f"OK: {w} - {res.stdout.splitlines()[0] if res.stdout else 'no output'}")

print("=== M09 Words ===")
for w in words_m09:
    res = subprocess.run(["python", "scripts/rag/query.py", "word", w], capture_output=True, text=True)
    if "✅" not in res.stdout:
        print(f"FAILED: {w}")
    else:
        print(f"OK: {w} - {res.stdout.splitlines()[0] if res.stdout else 'no output'}")
