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
HINT = re.compile(r"\([^)]*(?:tense|speaker|Use |Say |I |Then|During|Earlier|Now|morning|evening|Finally|reason|Compare|Tell|Ask)[^)]*\)|\b(?:Which sentence means|You want to say|How do you say|You need to say)\b", re.I)


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
    for slug in modules:
        source = ROOT / f"curriculum/l2-uk-en/a1-v1/{slug}/activities.yaml"
        raw = yaml.safe_load(source.read_text())
        offsets = {}
        offset = 0
        for section, activities in raw.items():
            offsets[section] = offset
            offset += len(activities)
            for activity in activities:
                for item in activity.get("items", []):
                    if not isinstance(item, dict):
                        continue
                    for field in ("sentence", "prompt", "statement", "text", "context", "hint"):
                        if field in item:
                            fields += 1
                            assert not HINT.search(str(item[field])), (slug, field, item[field])
        page = (ROOT / f"site/src/content/docs/a1-v1/{slug}.mdx").read_text()
        blocks = [parse_payload(match[1]) for match in PAYLOAD.finditer(page)]
        for block in blocks:
            for item in block:
                if isinstance(item, dict):
                    for field in ("sentence", "question", "statement", "prompt", "hint"):
                        assert not HINT.search(str(item.get(field, ""))), (slug, field, item)
        cache[slug] = raw, offsets, ActivityParser().parse(source), blocks
    blind = []
    payloads = []
    for row in ledger["items"]:
        raw, offsets, activities, blocks = cache[row["module"]]
        assert raw[row["section"]][row["activity_index"]]["items"][row["item_index"]] == row["after"], row["id"]
        assert row["sources"] and all(s in evidence for s in row["sources"]), row["id"]
        activity = activities[offsets[row["section"]] + row["activity_index"]]
        generated = yaml_activities_to_jsx([activity], is_ukrainian_forced=False)
        expected = parse_payload(PAYLOAD.search(generated)[1])[row["item_index"]]
        assert any(expected == item for block in blocks for item in block), (row["id"], "payload parity")
        options = [option["text"] if isinstance(option, dict) else option for option in expected["options"]]
        blind.append({"id": row["id"], "type": row["type"], "instruction": row["instruction"], "prompt": expected.get("question", expected.get("sentence")), "options": options})
        payloads.append({"id": row["id"], "type": row["type"], "payload": expected})
    assert len(blind) == ledger["counts"]["items_reworded"] + ledger["counts"]["items_replaced"]
    if args.blind:
        print(json.dumps(blind, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"items": len(blind), "modules": len(modules), "prompt_fields_scanned": fields, "pattern_hints_remaining": 0, "source_and_payload_parity": "PASS", "counts": ledger["counts"]}))


if __name__ == "__main__":
    main()
