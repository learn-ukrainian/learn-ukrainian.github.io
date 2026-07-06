#!/usr/bin/env python3
"""Deterministic contested-calque sidecar for the UA-GEC gold fixture (#4364).

UA-GEC ``F/Calque`` gold contains non-calque lexical/register edits (e.g.
«уверх»→«вгору», «вішалкою»→«вішаком», «срібляним»→«срібним» flag valid native
Ukrainian). The gold stays IMMUTABLE; this tool writes a transparent,
reproducible sidecar (``<fixture>.contested.json``) that scorers/reviewers can
use to report calque-axis precision with vs without contested items.

Heritage-defense rule (deterministic, source-backed — issue #4364):
an item is ``contested`` when the flagged (error) form is attested as valid
native Ukrainian by the CANONICAL local classifier,
:mod:`scripts.lexicon.heritage_classifier` — the same VESUM + heritage-
dictionary + russian-shadow logic the Word Atlas gates trust. Specifically:

    classification == "standard"  (VESUM/heritage-attested native)
    AND not is_russianism         (no style-guide condemnation)
    AND not russian_shadow        (no Russian-pattern morphology signal)
    AND calque_warning is None    (no known-calque replacement entry)

The first implementation reimplemented raw Грінченко/ЕСУМ SQL with a
LIKE-prefix fallback and an FTS body-text match; the real-DB run produced
pseudo-evidence (alphabetical runs of unrelated ЕСУМ articles matched on body
text, OCR junk headwords). Reusing the classifier is the root-cause fix: one
canonical attestation logic, one place to improve it.

Multi-word error forms are never evaluated (single-word heritage defense
only) and are recorded with ``basis: "multiword_not_evaluated"``.

Idempotent: stable key order, stable evidence order — re-runs are
byte-identical for unchanged inputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.heritage_classifier import classify_surface_form

DEFAULT_FIXTURE = PROJECT_ROOT / "data" / "ua-gec-gold" / "ua-gec-gold.json"


def contested_entry(status: dict[str, Any]) -> dict[str, Any]:
    """Map a heritage-classifier status onto a sidecar entry."""
    is_contested = (
        status.get("classification") == "standard"
        and not status.get("is_russianism")
        and not status.get("russian_shadow")
        and status.get("calque_warning") is None
    )
    evidence = [
        {
            "source": str(att.get("source") or ""),
            "ref": str(att.get("ref") or ""),
            "detail": str(att.get("detail") or ""),
        }
        for att in (status.get("attestations") or [])
        if isinstance(att, dict)
    ]
    evidence.sort(key=lambda ev: (ev["source"], ev["ref"], ev["detail"]))
    return {
        "contested": is_contested,
        "basis": "heritage_classifier",
        "classification": status.get("classification"),
        "russian_shadow": bool(status.get("russian_shadow")),
        "calque_warning": bool(status.get("calque_warning")),
        "evidence": evidence,
    }


def process_fixture(
    fixture_path: Path,
    *,
    sources_db: Path | None = None,
    vesum_db: Path | None = None,
    classify=classify_surface_form,
) -> dict[str, Any]:
    """Build the sidecar mapping (item id → contested entry). Never mutates gold.

    ``classify`` is injectable for tests; production uses the canonical
    heritage classifier against the real local databases.
    """
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError(f"gold fixture missing items list: {fixture_path}")

    sidecar: dict[str, Any] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        if not item_id:
            continue
        if item.get("tag") != "F/Calque":
            sidecar[item_id] = {
                "contested": False,
                "basis": "non_calque_tag",
                "evidence": [],
            }
            continue
        error_form = str(item.get("error") or "").strip()
        if not error_form or " " in error_form:
            sidecar[item_id] = {
                "contested": False,
                "basis": "multiword_not_evaluated",
                "evidence": [],
            }
            continue
        status = classify(
            error_form,
            db_path=sources_db,
            vesum_db_path=vesum_db,
        )
        sidecar[item_id] = contested_entry(status)

    return dict(sorted(sidecar.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-path",
        type=Path,
        default=DEFAULT_FIXTURE,
        help="Path to the gold fixture JSON file.",
    )
    parser.add_argument(
        "--sources-db",
        type=Path,
        default=None,
        help="Override sources.db path (default: classifier's canonical path).",
    )
    parser.add_argument(
        "--vesum-db",
        type=Path,
        default=None,
        help="Override vesum.db path (default: classifier's canonical path).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Sidecar output path (default: <fixture>.contested.json).",
    )
    args = parser.parse_args()

    sidecar = process_fixture(
        args.fixture_path,
        sources_db=args.sources_db,
        vesum_db=args.vesum_db,
    )

    output_path = args.output or args.fixture_path.with_suffix(".contested.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    contested = sum(1 for entry in sidecar.values() if entry["contested"])
    print(f"Wrote sidecar to {output_path} ({contested}/{len(sidecar)} contested)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
