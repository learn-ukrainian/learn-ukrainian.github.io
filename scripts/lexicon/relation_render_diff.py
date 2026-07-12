#!/usr/bin/env python3
"""Diff rendered Word Atlas relation sections before manifest promotion.

This gate intentionally compares the manifest that the site renders, rather
than source database rows. Section caps and merge order can displace visible
chips even when all raw relation facts remain present.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SECTION_RELATIONS = {
    "synonyms": "synonym",
    "antonyms": "antonym",
    "homonyms": "homonym",
    "paronyms": "paronym",
}
RELATIONS = tuple(SECTION_RELATIONS.values())
SECTION_CAPS = {relation: 8 for relation in RELATIONS}
_STRESS_MARK_RE = re.compile("[\u0300\u0301]")
_ARROW_TARGET_RE = re.compile(r"→\s*(.+?)(?:\s+\[[^\]]*\])?$")


@dataclass(frozen=True, slots=True)
class RenderedEdge:
    """One relation a learner can see in a rendered manifest section."""

    lemma: str
    lemma_key: str
    relation: str
    displayed_target: str
    target_key: str
    order: int
    provenance: tuple[str, ...]

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.lemma_key, self.relation, self.target_key)

    @property
    def source_bucket(self) -> str:
        source_labels = [label for label in self.provenance if not label.startswith("url: ")]
        labels = " ".join(source_labels).casefold()
        if source_labels and "ukrajinet" in labels and all("ukrajinet" in label.casefold() for label in source_labels):
            return "ukrajinet_only"
        return "retained_source"


def normalized_displayed_target(value: object) -> str:
    """Normalize visible text for stable relation-edge identity comparison."""
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = _STRESS_MARK_RE.sub("", text)
    text = unicodedata.normalize("NFC", text)
    text = text.replace("`", "'").replace("’", "'").replace("ʼ", "'")
    return re.sub(r"\s+", " ", text).strip().casefold()


def _displayed_target(relation: str, item: object) -> str | None:
    if isinstance(item, str):
        return item.strip() or None
    if not isinstance(item, dict):
        return None
    if relation in {"synonym", "antonym"}:
        value = item.get("text") or item.get("item")
        return str(value).strip() or None

    word = str(item.get("word") or item.get("text") or "").strip()
    if not word:
        return None
    detail_key = "gloss" if relation == "homonym" else "distinction"
    detail = str(item.get(detail_key) or "").strip()
    return f"{word} — {detail}" if detail else word


def _target_specific_source(label: str) -> str | None:
    match = _ARROW_TARGET_RE.search(label)
    if not match:
        return None
    return normalized_displayed_target(match.group(1).removesuffix(" (reciprocal)"))


def _section_provenance(section: dict[str, Any], target_key: str) -> tuple[str, ...]:
    labels: list[str] = []
    source = section.get("source")
    if isinstance(source, str):
        for label in (part.strip() for part in source.split(" + ")):
            target = _target_specific_source(label)
            if label and (target is None or target == target_key or target_key.startswith(f"{target} — ")):
                labels.append(label)
    source_urls = section.get("source_urls")
    if isinstance(source_urls, list):
        labels.extend(f"url: {url}" for url in source_urls if str(url).strip())
    return tuple(dict.fromkeys(labels))


def rendered_edges(manifest: dict[str, Any]) -> list[RenderedEdge]:
    """Extract canonical relation edges from display-ready manifest sections."""
    edges: list[RenderedEdge] = []
    seen: set[tuple[str, str, str]] = set()
    for entry in manifest.get("entries", []):
        if not isinstance(entry, dict):
            continue
        lemma = str(entry.get("lemma") or "").strip()
        lemma_key = normalized_displayed_target(lemma)
        if not lemma_key:
            continue
        sections = entry.get("sections")
        if not isinstance(sections, dict):
            continue
        for section_name, relation in SECTION_RELATIONS.items():
            section = sections.get(section_name)
            if not isinstance(section, dict):
                continue
            items = section.get("items")
            if not isinstance(items, list):
                continue
            for order, item in enumerate(items):
                displayed_target = _displayed_target(relation, item)
                target_key = normalized_displayed_target(displayed_target)
                if not displayed_target or not target_key:
                    continue
                key = (lemma_key, relation, target_key)
                if key in seen:
                    continue
                seen.add(key)
                provenance = list(_section_provenance(section, target_key))
                if isinstance(item, dict) and relation == "paronym":
                    raw_provenance = item.get("exam_provenance")
                    values = raw_provenance if isinstance(raw_provenance, list) else [raw_provenance]
                    provenance.extend(str(value).strip() for value in values if str(value).strip())
                edges.append(
                    RenderedEdge(
                        lemma=lemma,
                        lemma_key=lemma_key,
                        relation=relation,
                        displayed_target=displayed_target,
                        target_key=target_key,
                        order=order,
                        provenance=tuple(dict.fromkeys(provenance)),
                    )
                )
    return edges


def _load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Manifest must be a JSON object: {path}")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError(f"Manifest entries must be a list: {path}")
    return payload


def _edge_map(edges: list[RenderedEdge]) -> dict[tuple[str, str, str], RenderedEdge]:
    return {edge.key: edge for edge in edges}


def _relation_totals(
    old: dict[tuple[str, str, str], RenderedEdge],
    new: dict[tuple[str, str, str], RenderedEdge],
) -> dict[str, dict[str, int]]:
    return {
        relation: {
            "old": sum(edge.relation == relation for edge in old.values()),
            "new": sum(edge.relation == relation for edge in new.values()),
            "gained": sum(key not in old and edge.relation == relation for key, edge in new.items()),
            "lost": sum(key not in new and edge.relation == relation for key, edge in old.items()),
        }
        for relation in RELATIONS
    }


def _source_totals(
    old: dict[tuple[str, str, str], RenderedEdge],
    new: dict[tuple[str, str, str], RenderedEdge],
) -> dict[str, dict[str, int]]:
    totals: dict[str, dict[str, int]] = {}
    for bucket in ("retained_source", "ukrajinet_only"):
        totals[bucket] = {
            "old": sum(edge.source_bucket == bucket for edge in old.values()),
            "new": sum(edge.source_bucket == bucket for edge in new.values()),
            "gained": sum(
                key not in old and edge.source_bucket == bucket for key, edge in new.items()
            ),
            "lost": sum(
                key not in new and edge.source_bucket == bucket for key, edge in old.items()
            ),
        }
    return totals


def _per_lemma(
    old: dict[tuple[str, str, str], RenderedEdge],
    new: dict[tuple[str, str, str], RenderedEdge],
) -> list[dict[str, Any]]:
    keys = set(old) | set(new)
    lemma_keys = sorted({key[0] for key in keys})
    results: list[dict[str, Any]] = []
    for lemma_key in lemma_keys:
        old_edges = [edge for edge in old.values() if edge.lemma_key == lemma_key]
        new_edges = [edge for edge in new.values() if edge.lemma_key == lemma_key]
        gained = [edge for key, edge in new.items() if key not in old and edge.lemma_key == lemma_key]
        lost = [edge for key, edge in old.items() if key not in new and edge.lemma_key == lemma_key]
        if not gained and not lost:
            continue
        exemplar = (new_edges or old_edges)[0]
        results.append(
            {
                "lemma": exemplar.lemma,
                "old": len(old_edges),
                "new": len(new_edges),
                "gained": [_edge_label(edge) for edge in sorted(gained, key=_edge_sort_key)],
                "lost": [_edge_label(edge) for edge in sorted(lost, key=_edge_sort_key)],
            }
        )
    return results


def _edge_label(edge: RenderedEdge) -> str:
    return f"{edge.relation} → {edge.displayed_target}"


def _edge_sort_key(edge: RenderedEdge) -> tuple[str, str, int, str]:
    return (edge.lemma_key, edge.relation, edge.order, edge.target_key)


def _displaced_by_caps(
    old: dict[tuple[str, str, str], RenderedEdge],
    new: dict[tuple[str, str, str], RenderedEdge],
) -> list[dict[str, Any]]:
    displaced: list[dict[str, Any]] = []
    for key, lost_edge in old.items():
        if key in new:
            continue
        replacement_edges = [
            edge
            for edge in new.values()
            if edge.lemma_key == lost_edge.lemma_key and edge.relation == lost_edge.relation
        ]
        cap = SECTION_CAPS[lost_edge.relation]
        if len(replacement_edges) < cap:
            continue
        gained = [
            edge.displayed_target
            for edge in replacement_edges
            if edge.key not in old
        ]
        displaced.append(
            {
                "lemma": lost_edge.lemma,
                "relation": lost_edge.relation,
                "lost_target": lost_edge.displayed_target,
                "cap": cap,
                "new_targets": [edge.displayed_target for edge in sorted(replacement_edges, key=_edge_sort_key)],
                "gained_targets": gained,
            }
        )
    return sorted(
        displaced,
        key=lambda item: (
            normalized_displayed_target(item["lemma"]),
            item["relation"],
            normalized_displayed_target(item["lost_target"]),
        ),
    )


def diff_manifests(baseline: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic report data for two built manifests."""
    old = _edge_map(rendered_edges(baseline))
    new = _edge_map(rendered_edges(current))
    lost = [edge for key, edge in old.items() if key not in new]
    emptied = [
        {"lemma": edges[0].lemma, "old": len(edges), "new": 0}
        for lemma_key in sorted({edge.lemma_key for edge in old.values()})
        if (edges := [edge for edge in old.values() if edge.lemma_key == lemma_key])
        and not any(edge.lemma_key == lemma_key for edge in new.values())
    ]
    return {
        "relations": _relation_totals(old, new),
        "sources": _source_totals(old, new),
        "per_lemma": _per_lemma(old, new),
        "nonempty_to_empty": emptied,
        "lost_provenance": [
            {
                "lemma": edge.lemma,
                "relation": edge.relation,
                "target": edge.displayed_target,
                "provenance": list(edge.provenance),
            }
            for edge in sorted(lost, key=_edge_sort_key)
        ],
        "cap_displacements": _displaced_by_caps(old, new),
    }


def format_report(report: dict[str, Any]) -> str:
    """Render a concise human review gate report with all loss evidence."""
    lines = ["=== RENDERED RELATION DIFF ===", "", "GLOBAL TOTALS"]
    for relation in RELATIONS:
        totals = report["relations"][relation]
        lines.append(
            f"  {relation:8} old={totals['old']} new={totals['new']} "
            f"gained={totals['gained']} lost={totals['lost']}"
        )
    lines.extend(["", "SOURCE TOTALS"])
    for bucket, label in (("retained_source", "retained-source"), ("ukrajinet_only", "Ukrajinet-only")):
        totals = report["sources"][bucket]
        lines.append(
            f"  {label:16} old={totals['old']} new={totals['new']} "
            f"gained={totals['gained']} lost={totals['lost']}"
        )

    lines.extend(["", "PER-LEMMA CHANGES"])
    if not report["per_lemma"]:
        lines.append("  none")
    for item in report["per_lemma"]:
        lines.append(f"  {item['lemma']}: old={item['old']} new={item['new']}")
        if item["gained"]:
            lines.append(f"    gained: {', '.join(item['gained'])}")
        if item["lost"]:
            lines.append(f"    lost: {', '.join(item['lost'])}")

    lines.extend(["", "NONEMPTY → EMPTY"])
    if not report["nonempty_to_empty"]:
        lines.append("  none")
    for item in report["nonempty_to_empty"]:
        lines.append(f"  {item['lemma']}: old={item['old']} new=0")

    lines.extend(["", "LOST TARGET PROVENANCE"])
    if not report["lost_provenance"]:
        lines.append("  none")
    for item in report["lost_provenance"]:
        provenance = "; ".join(item["provenance"]) or "<missing rendered provenance>"
        lines.append(f"  {item['lemma']} → {item['relation']} → {item['target']} [{provenance}]")

    lines.extend(["", "CAP DISPLACEMENTS"])
    if not report["cap_displacements"]:
        lines.append("  none")
    for item in report["cap_displacements"]:
        gained = ", ".join(item["gained_targets"]) or "none"
        lines.append(
            f"  {item['lemma']} → {item['relation']} lost {item['lost_target']}; "
            f"new section is at cap {item['cap']}; gained={gained}"
        )
    return "\n".join(lines)


def run(baseline_path: Path, current_path: Path, *, as_json: bool = False) -> dict[str, Any]:
    report = diff_manifests(_load_manifest(baseline_path), _load_manifest(current_path))
    print(json.dumps(report, ensure_ascii=False, indent=2) if as_json else format_report(report))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Diff rendered relation sections between two Atlas manifests.")
    parser.add_argument("baseline", type=Path, help="Previously built manifest JSON.")
    parser.add_argument("current", type=Path, help="Newly built manifest JSON.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable report JSON.")
    args = parser.parse_args()
    run(args.baseline, args.current, as_json=args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
