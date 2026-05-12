#!/usr/bin/env python3
"""Measure manifest coverage heuristically for an existing module.md."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build.phases.wiki_manifest import extract_manifest


def measure_wiki_coverage(wiki_path: Path, module_path: Path) -> dict[str, Any]:
    manifest = extract_manifest(wiki_path)
    module_text = module_path.read_text(encoding="utf-8")
    return {
        "wiki_path": str(wiki_path),
        "module_path": str(module_path),
        "l2_errors": _measure_l2(manifest["l2_errors"], module_text),
        "sequence_steps": _measure_sequence(manifest["sequence_steps"], module_text),
        "phonetic_rules": _measure_phonetic(manifest["phonetic_rules"], module_text),
    }


def _measure_l2(items: list[dict[str, Any]], text: str) -> dict[str, Any]:
    results = []
    for item in items:
        incorrect_present = _any_marker_present(str(item.get("incorrect") or ""), text)
        correct_present = _any_marker_present(str(item.get("correct") or ""), text)
        results.append(
            {
                "id": item.get("id"),
                "covered": incorrect_present and correct_present,
                "incorrect_present": incorrect_present,
                "correct_present": correct_present,
            }
        )
    return _summary(results)


def _measure_sequence(items: list[dict[str, Any]], text: str) -> dict[str, Any]:
    results = []
    for item in items:
        markers = _claim_markers(str(item.get("required_claim") or ""))
        present = [marker for marker in markers if _contains(text, marker)]
        covered = len(present) >= min(3, max(1, len(markers)))
        results.append(
            {
                "id": item.get("id"),
                "covered": covered,
                "markers_present": present,
                "markers_required": markers,
            }
        )
    return _summary(results)


def _measure_phonetic(items: list[dict[str, Any]], text: str) -> dict[str, Any]:
    results = []
    for item in items:
        written_present = _contains(text, str(item.get("written") or ""))
        spoken_present = _contains(text, str(item.get("spoken") or ""))
        results.append(
            {
                "id": item.get("id"),
                "covered": written_present and spoken_present,
                "written_present": written_present,
                "spoken_present": spoken_present,
            }
        )
    return _summary(results)


def _summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    covered = sum(1 for item in results if item["covered"])
    total = len(results)
    return {
        "covered": covered,
        "total": total,
        "coverage": f"{covered}/{total}",
        "items": results,
    }


def _contains(text: str, marker: str) -> bool:
    return _normalize(marker) in _normalize(text)


def _normalize(text: str) -> str:
    text = re.sub(r"[`*_]", "", text.casefold())
    text = text.replace("’", "'").replace("ʼ", "'")
    return re.sub(r"\s+", " ", text)


def _marker_candidates(text: str) -> list[str]:
    cleaned = re.sub(r"^(?:Вимова|Pronunciation)\s*:\s*", "", text.strip(), flags=re.IGNORECASE)
    raw_parts = re.split(r"\s*/\s*|\s+або\s+|\s+чи\s+", cleaned)
    parts = []
    for part in raw_parts:
        part = re.sub(r"\[[SС]\d+\]", "", part)
        part = re.sub(r"[`*_]", "", part).strip(" .;:,")
        if part:
            parts.append(part)
    return parts


def _any_marker_present(markers: str, text: str) -> bool:
    candidates = _marker_candidates(markers)
    return bool(candidates) and any(_contains(text, candidate) for candidate in candidates)


def _claim_markers(claim: str) -> list[str]:
    markers = re.findall(r"`([^`]+)`|\*([^*]{2,80})\*", claim)
    flattened = [left or right for left, right in markers if (left or right)]
    if flattened:
        return [marker for marker in flattened if len(marker.strip()) >= 2]
    stop = {
        "крок",
        "учні",
        "учень",
        "повинні",
        "потрібно",
        "використовуючи",
        "наприклад",
        "зокрема",
        "введення",
        "вводяться",
        "засвоєння",
        "засвоїти",
        "зворотних",
        "дієслів",
        "дієслова",
        "граматичного",
        "фонетичного",
        "після",
        "ранок",
        "ранку",
    }
    terms = re.findall(r"[А-Яа-яІіЇїЄєҐґA-Za-z][\w'’ʼ-]{4,}", _normalize(claim))
    result = []
    for term in terms:
        if term in stop or term in result:
            continue
        result.append(term)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wiki_path", type=Path)
    parser.add_argument("module_path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    report = measure_wiki_coverage(args.wiki_path, args.module_path)
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
