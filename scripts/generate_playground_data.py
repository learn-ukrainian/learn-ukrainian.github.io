#!/usr/bin/env python3
"""Generate aggregated status data for playground dashboards."""

import json
from pathlib import Path
from datetime import datetime

CURRICULUM_ROOT = Path(__file__).parent.parent / "curriculum" / "l2-uk-en"

LEVELS = [
    {"id": "a1", "name": "A1 - Beginner", "path": "a1"},
    {"id": "a2", "name": "A2 - Elementary", "path": "a2"},
    {"id": "b1", "name": "B1 - Intermediate", "path": "b1"},
    {"id": "b2", "name": "B2 - Upper Intermediate", "path": "b2"},
    {"id": "c1", "name": "C1 - Advanced", "path": "c1"},
    {"id": "c2", "name": "C2 - Mastery", "path": "c2"},
    {"id": "b2-hist", "name": "B2-HIST - History Track", "path": "b2-hist"},
    {"id": "c1-bio", "name": "C1-BIO - Biography Track", "path": "c1-bio"},
    {"id": "lit", "name": "LIT - Literature Track", "path": "lit"},
]


def parse_word_count(message: str) -> tuple[int, int]:
    """Extract word count and target from message like '3375/3000 (raw: 3539)'."""
    try:
        parts = message.split("/")
        count = int(parts[0])
        target = int(parts[1].split()[0])
        return count, target
    except:
        return 0, 0


def parse_activity_count(message: str) -> int:
    """Extract activity count from message like '13/8'."""
    try:
        return int(message.split("/")[0])
    except:
        return 0


def parse_naturalness(message: str) -> int:
    """Extract naturalness score from message like '9/10 (High)'."""
    try:
        return int(message.split("/")[0])
    except:
        return 0


def load_level_status(level_info: dict) -> dict:
    """Load all module statuses for a level."""
    status_dir = CURRICULUM_ROOT / level_info["path"] / "status"

    if not status_dir.exists():
        return {
            "id": level_info["id"],
            "name": level_info["name"],
            "modules": [],
            "total": 0,
            "pass_count": 0,
            "fail_count": 0,
            "pending_count": 0,
        }

    modules = []
    for status_file in sorted(status_dir.glob("*.json")):
        try:
            with open(status_file) as f:
                data = json.load(f)

            # Extract module info
            gates = data.get("gates", {})
            overall = data.get("overall", {})

            lesson_msg = gates.get("lesson", {}).get("message", "0/0")
            word_count, word_target = parse_word_count(lesson_msg)

            activity_msg = gates.get("activities", {}).get("message", "0/0")
            activity_count = parse_activity_count(activity_msg)

            nat_msg = gates.get("naturalness", {}).get("message", "0/0")
            naturalness = parse_naturalness(nat_msg)

            # Determine status
            status = overall.get("status", "pending")
            if status == "pass":
                status_str = "pass"
            elif status == "fail":
                status_str = "fail"
            else:
                status_str = "pending"

            # Extract module number from filename
            filename = status_file.stem
            try:
                num = int(filename.split("-")[0])
            except:
                num = len(modules) + 1

            modules.append({
                "id": filename,
                "num": num,
                "title": filename.replace("-", " ").title(),
                "status": status_str,
                "wordCount": word_count,
                "wordTarget": word_target or 3000,
                "activityCount": activity_count,
                "naturalness": naturalness,
                "gates": {
                    gate: info.get("status", "pending")
                    for gate, info in gates.items()
                },
                "violations": overall.get("blocking_issues", []),
            })
        except Exception as e:
            print(f"Error loading {status_file}: {e}")

    # Sort by module number
    modules.sort(key=lambda m: m["num"])

    pass_count = sum(1 for m in modules if m["status"] == "pass")
    fail_count = sum(1 for m in modules if m["status"] == "fail")
    pending_count = sum(1 for m in modules if m["status"] == "pending")

    return {
        "id": level_info["id"],
        "name": level_info["name"],
        "modules": modules,
        "total": len(modules),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pending_count": pending_count,
    }


def main():
    """Generate aggregated status data."""
    output = {
        "generated": datetime.now().isoformat(),
        "levels": {},
    }

    total_modules = 0
    total_pass = 0
    total_fail = 0

    for level_info in LEVELS:
        level_data = load_level_status(level_info)
        output["levels"][level_info["id"]] = level_data
        total_modules += level_data["total"]
        total_pass += level_data["pass_count"]
        total_fail += level_data["fail_count"]
        print(f"{level_info['id']}: {level_data['total']} modules ({level_data['pass_count']} pass, {level_data['fail_count']} fail)")

    output["summary"] = {
        "total_modules": total_modules,
        "total_pass": total_pass,
        "total_fail": total_fail,
        "total_pending": total_modules - total_pass - total_fail,
    }

    # Write to playgrounds directory
    output_path = Path(__file__).parent.parent / "playgrounds" / "data" / "status.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nGenerated {output_path}")
    print(f"Total: {total_modules} modules ({total_pass} pass, {total_fail} fail)")


if __name__ == "__main__":
    main()
