import os

import ruamel.yaml

base_dir = "curriculum/l2-uk-en/plans/b1"
yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)

# Gap 1: Possessive adjectives
fpath_adj = os.path.join(base_dir, "word-formation-adjectives.yaml")
with open(fpath_adj, encoding="utf-8") as f:
    data_adj = yaml.load(f)

has_gap1 = any("Присвійні прикметники" in sec.get("title", "") for sec in data_adj.get("content_outline", []))
if not has_gap1:
    data_adj["objectives"].append("Learner can form and decline possessive adjectives (присвійні прикметники) like батьків, материн, сестрин, братів")
    data_adj["content_outline"].insert(1, {
        "section": "Присвійні прикметники (Possessive Adjectives)",
        "words": 600,
        "points": [
            "Formation of possessive adjectives from nouns denoting people (and sometimes animals).",
            "Suffixes: -ів/-їв (батько -> батьків, Сергій -> Сергіїв) and -ин/-їн (мама -> материн, Марія -> Маріїн).",
            "Declension: they decline like hard-stem adjectives but have short forms in Nominative/Accusative singular masculine (батьків дім, not батьківий).",
            "Practice: forming possessive adjectives from family members and names."
        ]
    })
    data_adj["vocabulary_hints"]["required"].extend(["присвійний прикметник (possessive adjective)", "батьків (father's)", "материн (mother's)"])
with open(fpath_adj, "w", encoding="utf-8") as f:
    yaml.dump(data_adj, f)

# Gap 2: Homogeneous members
fpath_intro = os.path.join(base_dir, "introductory-words.yaml")
with open(fpath_intro, encoding="utf-8") as f:
    data_intro = yaml.load(f)
has_gap2 = any("Однорідні члени речення" in sec.get("section", "") for sec in data_intro.get("content_outline", []))
if not has_gap2:
    data_intro["title"] = "Вставні слова та Однорідні члени речення"
    data_intro["objectives"].append("Learner can use homogeneous members of a sentence (однорідні члени речення) and apply correct punctuation, including generalizing words (узагальнювальні слова).")
    data_intro["content_outline"].insert(0, {
        "section": "Однорідні члени речення (Homogeneous Members)",
        "words": 700,
        "points": [
            "Definition: Multiple words answering the same question and relating to the same word in the sentence.",
            "Punctuation rules: commas between them if not joined by 'і/та', or if joined by contrasting conjunctions 'а', 'але'.",
            "Generalizing words (узагальнювальні слова): punctuation before (colon) and after (dash) homogeneous members.",
            "Practice: combining simple sentences into one with homogeneous members and punctuating correctly."
        ]
    })
    data_intro["vocabulary_hints"]["required"].extend(["однорідні члени речення (homogeneous members)", "узагальнювальне слово (generalizing word)"])
with open(fpath_intro, "w", encoding="utf-8") as f:
    yaml.dump(data_intro, f)

# Gap 3: Work/employment
fpath_daily = os.path.join(base_dir, "daily-life-and-routines.yaml")
with open(fpath_daily, encoding="utf-8") as f:
    data_daily = yaml.load(f)
data_daily["vocabulary_hints"]["required"].extend(["пошук роботи (job search)", "співбесіда (interview)", "робоче місце (workplace)", "колега (colleague)", "обов'язки (duties)"])
data_daily["objectives"].append("Learner can discuss workplace environments, job hunting, and professional duties.")
with open(fpath_daily, "w", encoding="utf-8") as f:
    yaml.dump(data_daily, f)

# Gap 4: Restaurant/food
fpath_leisure = os.path.join(base_dir, "leisure-culture-festivals.yaml")
with open(fpath_leisure, encoding="utf-8") as f:
    data_leisure = yaml.load(f)
data_leisure["vocabulary_hints"]["required"].extend(["ресторан (restaurant)", "меню (menu)", "замовлення (order)", "страва (dish)", "шеф-кухар (chef)"])
data_leisure["objectives"].append("Learner can discuss dining out, restaurant experiences, and regional cuisine.")
with open(fpath_leisure, "w", encoding="utf-8") as f:
    yaml.dump(data_leisure, f)

print("B1 gaps fixed.")
