import re

file_path = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/syllables-and-word-division.md"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix remaining stress unknowns
content = content.replace("*у-ніверсите́т*", "*у-ніверситет*")
content = content.replace("У-кра-ї́-на", "У-кра-ї-на")
content = content.replace("У - кра - ї́ - на", "У - кра - ї - на")
content = content.replace("мо-ло-ко́", "мо-ло-ко")
content = content.replace("мо - ло - ко́", "мо - ло - ко")
content = content.replace("се-стра́", "се-стра")
content = content.replace("сес-тра́", "сес-тра")
content = content.replace("сест-ра́", "сест-ра")
content = content.replace("сіль-ськи́й", "сіль-ський")
content = content.replace("у-ні-вер-си-те́т", "у-ні-вер-си-тет")

# Check if I missed any other hyphenated words with stress marks
def remove_stress_from_hyphenated(match):
    word = match.group(0)
    # Remove stress mark \u0301
    return word.replace("\u0301", "")

# Matches words with hyphens and stress marks
content = re.sub(r'[\wа-яА-ЯіїєґІЇЄҐ]+\u0301?-[\wа-яА-ЯіїєґІЇЄҐ\u0301-]+', remove_stress_from_hyphenated, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done")
