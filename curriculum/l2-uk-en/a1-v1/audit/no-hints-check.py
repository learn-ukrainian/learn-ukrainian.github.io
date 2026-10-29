"""Reconcile the no-hints item ledger with YAML and tracked learner payloads."""

import argparse
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


def parse_payload(value):
    return json.loads(re.sub(r"\\([\\`$])", lambda match: match[1], value))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", type=Path, default=Path(__file__).with_name("no-hints-modules-01-28-items.json"))
    parser.add_argument(
        "--blind", action="store_true", help="Print tracked prompts and options with keys and explanations withheld."
    )
    args = parser.parse_args()
    ledger = json.loads(args.items.read_text())
    cache = {}
    blind = []
    for row in ledger["items"]:
        slug = row["module"]
        if slug not in cache:
            source = ROOT / f"curriculum/l2-uk-en/a1-v1/{slug}/activities.yaml"
            raw = yaml.safe_load(source.read_text())
            sections = {"root": raw} if isinstance(raw, list) else raw
            offsets = {}
            offset = 0
            for section, activities in sections.items():
                offsets[section] = offset
                offset += len(activities)
            page = (ROOT / f"site/src/content/docs/a1-v1/{slug}.mdx").read_text()
            blocks = [parse_payload(match[1]) for match in PAYLOAD.finditer(page)]
            cache[slug] = sections, offsets, ActivityParser().parse(source), blocks
        sections, offsets, activities, blocks = cache[slug]
        source_item = sections[row["section"]][row["activity_index"]]["items"][row["item_index"]]
        assert source_item == row["after"], (row["id"], "source differs from ledger")
        activity = activities[offsets[row["section"]] + row["activity_index"]]
        generated = yaml_activities_to_jsx([activity], is_ukrainian_forced=False)
        expected = parse_payload(PAYLOAD.search(generated)[1])[row["item_index"]]
        assert any(expected == item for block in blocks for item in block), (row["id"], "tracked payload differs")
        options = [option["text"] if isinstance(option, dict) else option for option in expected["options"]]
        blind.append(
            {
                "id": row["id"],
                "type": row["type"],
                "instruction": row["instruction"],
                "prompt": expected.get("question", expected.get("sentence")),
                "options": options,
            }
        )
    counts = ledger["counts"]
    assert len(blind) == counts["items_reworded"] + counts["items_replaced"]
    if args.blind:
        print(json.dumps(blind, ensure_ascii=False, indent=2))
    else:
        print(
            json.dumps(
                {"items": len(blind), "modules": len(cache), "source_and_payload_parity": "PASS", "counts": counts}
            )
        )


if __name__ == "__main__":
    main()
