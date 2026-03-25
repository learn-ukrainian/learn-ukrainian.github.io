import yaml

with open("curriculum/l2-uk-en/a1/meta/imperative-and-requests.yaml", "r", encoding="utf-8") as f:
    meta = yaml.safe_load(f)

for section in meta["content_outline"]:
    if "title" in section:
        section["title"] = section["title"].split(" (")[0]

with open("curriculum/l2-uk-en/a1/meta/imperative-and-requests.yaml", "w", encoding="utf-8") as f:
    yaml.dump(meta, f, allow_unicode=True, sort_keys=False)

with open("curriculum/l2-uk-en/a1/imperative-and-requests.md", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("## Наказовий спосіб (Imperative mood)", "## Наказовий спосіб")
text = text.replace("## Вісім обов'язкових дієслів (Eight required verbs)", "## Вісім обов'язкових дієслів")
text = text.replace("## Ввічливе прохання (Polite requests)", "## Ввічливе прохання")
text = text.replace("## Заборони (Prohibitions)", "## Заборони")
text = text.replace("## Практика та підсумок (Practice and Summary)", "## Практика та підсумок")
text = text.replace("Ось головні правила (Here are the main rules):", "Ось головні правила:")

with open("curriculum/l2-uk-en/a1/imperative-and-requests.md", "w", encoding="utf-8") as f:
    f.write(text)

