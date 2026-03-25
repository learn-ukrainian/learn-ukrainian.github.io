import sys
from pprint import pprint
# Assuming scripts directory is in PYTHONPATH or we can just append it
sys.path.append('.')

from scripts.rag.query import search_text, verify_words

topics = [
    "чергування голосних і о е",
    "чергування приголосних к ц г з",
    "чергування дієслів",
    "доконаний недоконаний вид",
    "родовий відмінок немає",
    "родовий відмінок кількість",
    "родовий відмінок числівники дати"
]

print("=== TEXTBOOK REFERENCES ===")
for topic in topics:
    print(f"\nTopic: {topic}")
    for grade in [3, 4, 5, 6]:
        results = search_text(topic, grade=grade, limit=2)
        if results:
            for r in results:
                # We don't know the exact structure of results, let's print a small summary
                print(f"Grade {grade} - {r.get('metadata', {}).get('author', 'Unknown')} p.{r.get('metadata', {}).get('page', '?')}: {r.get('text', '')[:100]}...")

words_to_verify = [
    "ніс", "носа", "рука", "руці", "ходити", "ходжу", "просити", "прошу",
    "робити", "зробити", "читати", "прочитати", "писати", "написати", "дивитися", "подивитися", "купувати", "купити", "розуміти", "зрозуміти",
    "немає", "часу", "грошей", "багато", "мало", "кілька", "студент", "студента", "водій", "водія", "лікар", "лікаря", "викладач", "викладача", "книга", "книги", "аудиторія", "аудиторії", "вікно", "вікна", "життя", "життя",
    "перше", "першого", "десяте", "десятого", "березень", "березня", "гривня", "гривень", "долар", "доларів", "євро"
]

print("\n=== VERIFY WORDS ===")
res = verify_words(words_to_verify)
print("Invalid words:")
# check what structure verify_words returns
for word in words_to_verify:
    if word not in res or not res[word]:
        print(f"NOT FOUND: {word}")

