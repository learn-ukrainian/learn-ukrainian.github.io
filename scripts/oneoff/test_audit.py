import yaml
with open("curriculum/l2-uk-en/a1/activities/vowel-sounds.yaml", "r") as f:
    text = f.read()

text = text.replace(" И", " І").replace("- И", "- І").replace("мома", "мапа").replace("мума", "сума").replace("сик", "суп")

with open("curriculum/l2-uk-en/a1/activities/vowel-sounds-test.yaml", "w") as f:
    f.write(text)
