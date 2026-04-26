import json
from pathlib import Path

import yaml

files = [
    "curriculum/l2-uk-en/plans/b1/aspect-in-imperatives.yaml",
    "curriculum/l2-uk-en/plans/b1/aspect-in-narration.yaml",
    "curriculum/l2-uk-en/plans/b1/aspect-in-negation.yaml",
    "curriculum/l2-uk-en/plans/b1/aspect-past-tense.yaml",
    "curriculum/l2-uk-en/plans/b1/b1-baseline-future-aspect.yaml",
    "curriculum/l2-uk-en/plans/b1/b1-baseline-past-present.yaml",
    "curriculum/l2-uk-en/plans/b1/cases-with-ordinal-numerals.yaml",
    "curriculum/l2-uk-en/plans/b1/cases-with-quantity-expressions.yaml",
    "curriculum/l2-uk-en/plans/b1/checkpoint-aspect.yaml",
]

strings = set()


def extract(obj):
    if isinstance(obj, str):
        strings.add(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            extract(v)
    elif isinstance(obj, list):
        for item in obj:
            extract(item)


for f in files:
    if not Path(f).exists():
        continue
    with open(f) as fp:
        data = yaml.safe_load(fp)

        if "title" in data:
            strings.add(data["title"])
        if "subtitle" in data:
            strings.add(data["subtitle"])
        if "objectives" in data:
            for obj in data["objectives"]:
                strings.add(obj)
        if "content_outline" in data:
            for section in data["content_outline"]:
                strings.add(section.get("section", ""))
                for p in section.get("points", []):
                    strings.add(p)
                for sc in section.get("subsections", []):
                    strings.add(sc)
                for kc in section.get("key_concepts", []):
                    strings.add(kc)
        if "dialogue_situations" in data:
            for ds in data["dialogue_situations"]:
                if "setting" in ds:
                    strings.add(ds["setting"])
                if "motivation" in ds:
                    strings.add(ds["motivation"])
        if "reading_situations" in data:
            for rs in data.get("reading_situations", []):
                if "topic" in rs:
                    strings.add(rs["topic"])
                if "motivation" in rs:
                    strings.add(rs["motivation"])
        if "activity_hints" in data:
            for ah in data["activity_hints"]:
                if "focus" in ah:
                    strings.add(ah["focus"])
        if "grammar" in data:
            for g in data["grammar"]:
                strings.add(g)
        if "references" in data:
            for ref in data["references"]:
                if "notes" in ref:
                    strings.add(ref["notes"])
        if "prerequisites" in data:
            for pr in data["prerequisites"]:
                strings.add(pr)
        if "connects_to" in data:
            for ct in data["connects_to"]:
                strings.add(ct)
        if "phase" in data:
            strings.add(data["phase"])

with open("strings.json", "w") as f:
    json.dump(list(strings), f, indent=2, ensure_ascii=False)
