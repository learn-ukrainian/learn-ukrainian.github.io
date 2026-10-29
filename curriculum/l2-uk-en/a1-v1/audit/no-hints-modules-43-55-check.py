"""Reconcile the modules 43-55 no-hints ledger with source and learner payloads."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.generate_mdx.converters import yaml_activities_to_jsx
from scripts.yaml_activities import ActivityParser

PAYLOAD = re.compile(r"(?:items|questions)=\{JSON.parse\(`(.*?)`\)\}")
HINT = re.compile(r"\([^)]*(?:tense|speaker|Use |Say |I |Then|During|Earlier|Now|morning|evening|Finally|reason|Compare|Tell|Ask)[^)]*\)|\b(?:Which sentence means|Which question asks about tomorrow|keeps the A1 compound future|Choose the infinitive|Keep the infinitive|You want to say|How do you say|You need to say)\b", re.I)


def parse_payload(value):
    return json.loads(re.sub(r"\\([\\`$])", lambda match: match[1], value))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blind", action="store_true", help="Print prompts and options with keys and feedback withheld.")
    args = parser.parse_args()
    here = Path(__file__).parent
    ledger = json.loads((here / "no-hints-modules-43-55-items.json").read_text())
    modules = yaml.safe_load((ROOT / "curriculum/l2-uk-en/curriculum.yaml").read_text())["levels"]["a1-v1"]["modules"][42:55]
    assert ledger["modules"] == modules
    evidence = {}
    for line in (here / "no-hints-modules-43-55-evidence.jsonl").read_text().splitlines():
        row = json.loads(line)
        receipt = row.pop("receipt_sha256")
        assert hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest() == receipt
        evidence[row["id"]] = row
    cache = {}
    fields = 0
    labels = 0
    literal_label_checks = 0
    for slug in modules:
        source = ROOT / f"curriculum/l2-uk-en/a1-v1/{slug}/activities.yaml"
        raw = yaml.safe_load(source.read_text())
        offsets = {}
        offset = 0
        for section, activities in raw.items():
            offsets[section] = offset
            offset += len(activities)
            for activity in activities:
                labels += len([field for field in ("title", "instruction") if field in activity])
                for field in ("title", "instruction"):
                    assert not HINT.search(activity.get(field, "")), (slug, section, activity.get("id"), field)
                label = activity.get("title", "") + " " + activity.get("instruction", "")
                for item in activity.get("items", []):
                    if not isinstance(item, dict):
                        continue
                    if activity.get("type") in ("fill-in", "quiz"):
                        options = [o["text"] if isinstance(o, dict) else o for o in item.get("options", [])]
                        key = item.get("answer") if activity["type"] == "fill-in" else next(o["text"] for o in item["options"] if o["correct"])
                        named = [o for o in options if re.search("[А-Яа-яІіЇїЄєҐґ]", o) and re.search(r"(?<!\w)" + re.escape(o) + r"(?!\w)", label, re.I)]
                        literal_label_checks += 1
                        if key in named and set(named) != set(options):
                            raise AssertionError((slug, section, activity.get("id"), "label excludes alternatives"))
                    for field in ("sentence", "prompt", "statement", "text", "context", "hint"):
                        if field in item:
                            fields += 1
                            assert not HINT.search(str(item[field])), (slug, field, item[field])
        page = (ROOT / f"site/src/content/docs/a1-v1/{slug}.mdx").read_text()
        blocks = [parse_payload(match[1]) for match in PAYLOAD.finditer(page)]
        component_lines = [(line, parse_payload(PAYLOAD.search(line)[1])) for line in page.splitlines() if line.startswith(("<FillIn ", "<Quiz ", "<Translate ")) and PAYLOAD.search(line)]
        for block in blocks:
            for item in block:
                if isinstance(item, dict):
                    for field in ("sentence", "question", "statement", "prompt", "hint"):
                        assert not HINT.search(str(item.get(field, ""))), (slug, field, item)
        cache[slug] = raw, offsets, ActivityParser().parse(source), blocks, component_lines, page
    blind = []
    for row in ledger["items"]:
        raw, offsets, activities, blocks, component_lines, page = cache[row["module"]]
        source_activity = raw[row["section"]][row["activity_index"]]
        assert source_activity["items"][row["item_index"]] == row["after"], row["id"]
        assert row["activity_title"] == source_activity["title"], row["id"]
        assert row["instruction"] == source_activity["instruction"], row["id"]
        assert "### " + source_activity["title"] in page.splitlines(), (row["id"], "heading parity")
        assert row["sources"] and all(s in evidence for s in row["sources"]), row["id"]
        activity = activities[offsets[row["section"]] + row["activity_index"]]
        generated = yaml_activities_to_jsx([activity], is_ukrainian_forced=False)
        expected = parse_payload(PAYLOAD.search(generated)[1])[row["item_index"]]
        assert any(expected == item for block in blocks for item in block), (row["id"], "payload parity")
        assert any(expected in items and "instruction={" + json.dumps(row["instruction"], ensure_ascii=False) + "}" in line for line, items in component_lines), (row["id"], "instruction parity")
        options = [option["text"] if isinstance(option, dict) else option for option in expected["options"]]
        named = [option for option in options if re.search("[А-Яа-яІіЇїЄєҐґ]", option) and re.search(r"(?<!\w)" + re.escape(option) + r"(?!\w)", row["activity_title"] + " " + row["instruction"], re.I)]
        assert row["key"] not in named or set(named) == set(options), (row["id"], "visible label singles out key")
        blind.append({"id": row["id"], "type": row["type"], "activity_title": row["activity_title"], "instruction": row["instruction"], "prompt": expected.get("question", expected.get("sentence")), "options": options})
    assert len(blind) == ledger["counts"]["items_reworded"] + ledger["counts"]["items_replaced"]
    if args.blind:
        print(json.dumps(blind, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"items": len(blind), "modules": len(modules), "prompt_fields_scanned": fields, "activity_labels_scanned": labels, "choice_items_checked_for_literal_label_disclosure": literal_label_checks, "pattern_hints_remaining": 0, "source_and_payload_parity": "PASS", "counts": ledger["counts"]}))


if __name__ == "__main__":
    main()
