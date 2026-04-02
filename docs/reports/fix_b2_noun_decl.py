import os

import ruamel.yaml

base_dir = "curriculum/l2-uk-en/plans/b2"
yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)

fpath = os.path.join(base_dir, "advanced-case-semantics.yaml")
with open(fpath, encoding="utf-8") as f:
    data = yaml.load(f)

# check if already expanded
outline = data.get("content_outline", [])
has_expansion = any("Складні випадки відмінювання іменників" in sec.get("section", "") for sec in outline)

if not has_expansion:
    # add objective
    data["objectives"].append("Learner can correctly decline advanced noun categories, including pluralia tantum and nouns with shifting declension types.")

    # insert section
    outline.insert(2, {
        "section": "Складні випадки відмінювання іменників (Advanced Noun Declension)",
        "words": 1000,
        "subsections": [
            "Відмінювання іменників pluralia tantum (двері, гроші, ножиці, штани).",
            "Особливості відмінювання іменників з подвійним родом або зміною парадигми.",
            "Складні випадки родового відмінка множини (нульове закінчення vs -ів)."
        ],
        "key_concepts": [
            "pluralia tantum",
            "нульове закінчення",
            "відмінкова парадигма",
            "граматичний рід"
        ]
    })

    # add vocabulary hints
    req_hints = data.get("vocabulary", {}).get("required", [])
    if "гроші" not in req_hints:
        req_hints.extend(["гроші", "ножиці", "штани", "окуляри", "парадигма"])

    with open(fpath, "w", encoding="utf-8") as f:
        yaml.dump(data, f)
    print("advanced-case-semantics expanded.")
else:
    print("advanced-case-semantics already expanded.")
