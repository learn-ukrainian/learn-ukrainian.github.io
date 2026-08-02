"""Build and apply the lemma-only Curated Practice membership union.

The homework seed and the legacy teacher inventory are separate authorities for
membership.  This module deliberately consumes only lexical identifiers from
the inventory, never sentence bodies or distractors.  Sentence admission stays
with the public cloze-source and rights gates.
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.lexicon.curated_seed_atlas_admission import _read_jsonl, prepare_practice_seed

SCHEMA = "curated-practice-membership-v1"
DEFAULT_MEMBERSHIP_PATH = Path("site/src/data/lexicon-teacher-curated-membership.json")


def _text(value: object) -> str:
    return str(value or "").strip()


def _key(value: object) -> str:
    return unicodedata.normalize("NFC", _text(value)).casefold()


def read_manifest_entries(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("entries") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        raise ValueError(f"{path}: manifest entries must be a list")
    return [entry for entry in entries if isinstance(entry, dict)]


def read_teacher_inventory_keys(path: Path) -> list[str]:
    """Read only legacy inventory lemma identifiers, never its prose fields."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    cards = payload.get("cloze") if isinstance(payload, dict) else payload
    if not isinstance(cards, list):
        raise ValueError(f"{path}: expected a cloze list")
    return [_text(card.get("lemmaId")) for card in cards if isinstance(card, dict) and _text(card.get("lemmaId"))]


def _public_routes(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    routes: dict[str, dict[str, Any]] = {}
    for entry in entries:
        slug = _text(entry.get("url_slug"))
        lemma = _text(entry.get("lemma"))
        if not slug or not lemma:
            continue
        routes.setdefault(_key(slug), entry)
        routes.setdefault(_key(lemma), entry)
    return routes


def build_membership(
    *,
    homework_seed_path: Path,
    teacher_inventory_path: Path,
    manifest_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a public-route-only A union B membership payload and local report.

    A uses the existing VESUM-attested curated admission resolver.  B is
    resolved only by an exact canonical Atlas lemma/slug match: legacy cards
    sometimes carry a last-token cloze target, which must not be promoted as a
    guessed multiword headword.
    """
    homework_rows = _read_jsonl(homework_seed_path)
    practice_seed, homework_report = prepare_practice_seed(homework_rows, manifest_path)
    entries = read_manifest_entries(manifest_path)
    routes = _public_routes(entries)
    members: dict[str, dict[str, Any]] = {}

    def add(entry: dict[str, Any], source: str) -> None:
        slug = _text(entry.get("url_slug"))
        lemma = _text(entry.get("lemma"))
        if not slug or not lemma:
            raise ValueError("resolved membership entry requires lemma and url_slug")
        record = members.setdefault(slug, {"lemma": lemma, "slug": slug, "sources": set()})
        record["sources"].add(source)

    homework_public = 0
    homework_local_only = 0
    for row in practice_seed["entries"]:
        if row.get("localOnly") is True:
            homework_local_only += 1
            continue
        target = routes.get(_key(row.get("slug")))
        if target is None:
            raise ValueError(f"curated homework seed route is absent from manifest: {row.get('slug')!r}")
        add(target, "homework")
        homework_public += 1

    teacher_keys = read_teacher_inventory_keys(teacher_inventory_path)
    teacher_unique = sorted({_key(value) for value in teacher_keys})
    unresolved_teacher_keys: list[str] = []
    for key in teacher_unique:
        target = routes.get(key)
        if target is None:
            unresolved_teacher_keys.append(key)
            continue
        add(target, "teacher_inventory")

    serialized_members = [
        {"lemma": record["lemma"], "slug": record["slug"], "sources": sorted(record["sources"])}
        for _slug, record in sorted(members.items(), key=lambda item: (_key(item[1]["lemma"]), item[0]))
    ]
    payload = {
        "schema": SCHEMA,
        "schemaVersion": 1,
        "members": serialized_members,
    }
    report = {
        "schema": "curated-practice-membership-report-v1",
        "homework": {
            "rows": len(homework_rows),
            "unique_lemmas": len({_key(row.get("lemma")) for row in homework_rows if _key(row.get("lemma"))}),
            "public_route_rows": homework_public,
            "local_only_rows": homework_local_only,
            "admission": homework_report,
        },
        "teacher_inventory": {
            "cards": len(teacher_keys),
            "unique_keys": len(teacher_unique),
            "resolved_keys": len(teacher_unique) - len(unresolved_teacher_keys),
            "unresolved_keys": unresolved_teacher_keys,
        },
        "membership": {
            "unique_routes": len(serialized_members),
            "by_source": dict(
                sorted(Counter(source for member in serialized_members for source in member["sources"]).items())
            ),
        },
    }
    return payload, report


def read_membership(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise ValueError(f"{path}: unsupported curated membership schema")
    members = payload.get("members")
    if not isinstance(members, list):
        raise ValueError(f"{path}: members must be a list")
    validated: list[dict[str, Any]] = []
    seen_slugs: set[str] = set()
    for index, member in enumerate(members):
        if not isinstance(member, dict):
            raise ValueError(f"{path}: members[{index}] must be an object")
        lemma = _text(member.get("lemma"))
        slug = _text(member.get("slug"))
        sources = member.get("sources")
        if not lemma or not slug or not isinstance(sources, list) or not all(_text(source) for source in sources):
            raise ValueError(f"{path}: members[{index}] requires lemma, slug, and sources")
        slug_key = _key(slug)
        if slug_key in seen_slugs:
            raise ValueError(f"{path}: duplicate membership slug {slug!r}")
        seen_slugs.add(slug_key)
        validated.append({"lemma": lemma, "slug": slug, "sources": sorted({_text(source) for source in sources})})
    return validated


def apply_membership(entries: list[dict[str, Any]], members: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Mark exact public Atlas routes as practice members without admitting cloze."""
    by_slug = {_key(entry.get("url_slug")): index for index, entry in enumerate(entries) if _key(entry.get("url_slug"))}
    merged = list(entries)
    unresolved: list[dict[str, str]] = []
    for member in members:
        index = by_slug.get(_key(member["slug"]))
        if index is None:
            unresolved.append({"slug": member["slug"], "reason": "missing_atlas_route"})
            continue
        target = merged[index]
        if _key(target.get("lemma")) != _key(member["lemma"]):
            raise ValueError(f"membership lemma does not match Atlas route {member['slug']!r}")
        admission = target.get("surface_admission")
        merged_admission = dict(admission) if isinstance(admission, dict) else {}
        merged_admission["practice"] = True
        merged[index] = {**target, "surface_admission": merged_admission, "curated_membership": True}
    if unresolved:
        raise ValueError(f"curated membership contains {len(unresolved)} unresolved Atlas route(s): {unresolved[:5]}")
    return merged, {"members": len(members), "resolved": len(members)}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--homework-seed", type=Path, required=True)
    parser.add_argument("--teacher-inventory", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_MEMBERSHIP_PATH)
    parser.add_argument("--report-out", type=Path)
    args = parser.parse_args(argv)
    payload, report = build_membership(
        homework_seed_path=args.homework_seed,
        teacher_inventory_path=args.teacher_inventory,
        manifest_path=args.manifest,
    )
    _write_json(args.out, payload)
    if args.report_out:
        _write_json(args.report_out, report)
    print(
        "curated membership "
        f"routes={report['membership']['unique_routes']} "
        f"homework_public={report['homework']['public_route_rows']} "
        f"teacher_keys={report['teacher_inventory']['unique_keys']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
