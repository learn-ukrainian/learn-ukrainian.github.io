"""Measure the Curated Practice A union B floor without reading teacher prose."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.audit.lexeme_filter import practice_ineligibility_reason
from scripts.lexicon.curated_membership import (
    DEFAULT_MEMBERSHIP_PATH,
    _key,
    apply_membership,
    build_membership,
    read_manifest_entries,
    read_membership,
    read_teacher_inventory_keys,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEACHER_INVENTORY = ROOT / "site" / "src" / "data" / "lexicon-teacher-cloze.json"
DEFAULT_PRACTICE_DIR = ROOT / "site" / "public" / "lexicon"


def _index_items(practice_dir: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(practice_dir.glob("practice-index.*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        level_items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(level_items, list):
            raise ValueError(f"{path}: index items must be a list")
        items.extend(item for item in level_items if isinstance(item, dict))
    return items


def _residual_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Count private-source residuals without printing their lemma text."""
    reasons = Counter(str(row.get("reason") or "unspecified") for row in rows)
    return {"rows": len(rows), "reasons": dict(sorted(reasons.items()))}


def measure_membership(
    *,
    homework_seed_path: Path,
    teacher_inventory_path: Path,
    manifest_path: Path,
    membership_path: Path,
    practice_dir: Path,
) -> dict[str, Any]:
    expected_payload, expected_report = build_membership(
        homework_seed_path=homework_seed_path,
        teacher_inventory_path=teacher_inventory_path,
        manifest_path=manifest_path,
    )
    actual_members = read_membership(membership_path)
    expected_members = expected_payload["members"]
    expected_by_slug = {_key(member["slug"]): member for member in expected_members}
    actual_by_slug = {_key(member["slug"]): member for member in actual_members}
    homework_expected = {
        slug for slug, member in expected_by_slug.items() if "homework" in member["sources"]
    }
    manifest_entries, _membership_report = apply_membership(
        read_manifest_entries(manifest_path), actual_members
    )
    entries_by_slug = {
        _key(entry.get("url_slug")): entry
        for entry in manifest_entries
        if _key(entry.get("url_slug"))
    }
    ineligible_homework = Counter(
        reason
        for slug in homework_expected
        if (reason := practice_ineligibility_reason(entries_by_slug[slug])) is not None
    )
    eligible_homework = {
        slug
        for slug in homework_expected
        if practice_ineligibility_reason(entries_by_slug[slug]) is None
    }
    practice_items = _index_items(practice_dir)
    practice_keys = {
        _key(item.get("lemmaId"))
        for item in practice_items
        if _key(item.get("lemmaId"))
    }
    levels: dict[str, dict[str, int]] = {}
    for item in practice_items:
        level = str(item.get("cefr") or "")
        if not level:
            continue
        row = levels.setdefault(level, {"lexemes": 0, "flashcards": 0, "matching": 0, "choice": 0})
        row["lexemes"] += 1
        modes = item.get("modes")
        if isinstance(modes, list):
            for mode in ("flashcards", "matching", "choice"):
                if mode in modes:
                    row[mode] += 1
    return {
        "schema": "curated-practice-membership-measurement-v1",
        "homework": {
            "unique_lemmas": expected_report["homework"]["unique_lemmas"],
            "public_route_rows": expected_report["homework"]["public_route_rows"],
            "local_only_rows": expected_report["homework"]["local_only_rows"],
            "missing_from_curated_keys": len(homework_expected - set(actual_by_slug)),
            "eligible_routes": len(eligible_homework),
            "missing_from_practice_indexes": len(eligible_homework - practice_keys),
            "ineligible_routes": dict(sorted(ineligible_homework.items())),
        },
        "teacher_inventory": {
            "cards": len(read_teacher_inventory_keys(teacher_inventory_path)),
            "unique_keys": len({_key(value) for value in read_teacher_inventory_keys(teacher_inventory_path)}),
            "resolved_membership_routes": sum(
                "teacher_inventory" in member["sources"] for member in actual_members
            ),
        },
        "curated_membership": {"unique_routes": len(actual_members)},
        "recognition_mode_eligibility": dict(sorted(levels.items())),
        "unkeyable_homework_residual": {
            "atlas_failures": _residual_summary(expected_report["homework"]["admission"]["atlas_failures"]),
            "not_practice_admitted": _residual_summary(
                expected_report["homework"]["admission"]["practice_skipped_not_admitted"]
            ),
            "local_only_no_public_route": expected_report["homework"]["local_only_rows"],
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--homework-seed", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--teacher-inventory", type=Path, default=DEFAULT_TEACHER_INVENTORY)
    parser.add_argument("--membership", type=Path, default=DEFAULT_MEMBERSHIP_PATH)
    parser.add_argument("--practice-dir", type=Path, default=DEFAULT_PRACTICE_DIR)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    payload = measure_membership(
        homework_seed_path=args.homework_seed,
        teacher_inventory_path=args.teacher_inventory,
        manifest_path=args.manifest,
        membership_path=args.membership,
        practice_dir=args.practice_dir,
    )
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        args.json_out.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
