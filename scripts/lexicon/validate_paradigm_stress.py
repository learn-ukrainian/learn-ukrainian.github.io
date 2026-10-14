"""Audit every manifest morphology row against local ULIF/VESUM authority (#9820)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lexicon.enrich_manifest import _base_lemma, _decode_tag, _paradigm_row_kind
from scripts.verification.stress import _strip_stress, verify_stress
from scripts.verification.ulif_stress import analysis_features, readings, select_analyses
from scripts.verification.vesum import verify_lemma

_SLOT_KEYS = frozenset({"upos", "Case", "Number"})


def _witness_choices(lemma: str, witness: dict[str, Any]) -> set[str]:
    """Accents one VESUM analysis licenses for its own slot: ULIF, else the tagged oracle."""
    form = witness["word_form"]
    supplied = analysis_features(witness)
    slot = {tag for tag in supplied if tag.split("=", 1)[0] in _SLOT_KEYS}
    matches = readings(form, supplied=supplied, lemma=lemma, vesum=[witness])
    matches = [m for m in matches if slot <= set(m["required_tags"])]
    if not matches:
        oracle = verify_stress(form, lemma=lemma, tags=witness["tags"])
        if oracle["status"] == "ok":
            candidates = oracle["matches"]
            if candidates and all(
                slot <= set(m["required_tags"]) and select_analyses(m.get("vesum_analyses", []), supplied, lemma)
                for m in candidates
            ):
                matches = candidates
    return {m["stressed_form"] for m in matches}


def _choices(lemma: str, witnesses: list[dict[str, Any]], memo: dict[tuple[str, str, str], set[str]]) -> set[str]:
    """The single accent all witnesses license, else nothing."""
    choices: set[str] = set()
    for witness in witnesses:
        key = (witness["word_form"], witness["tags"], witness.get("pos") or "")
        if key not in memo:
            memo[key] = _witness_choices(lemma, witness)
        choices |= memo[key]
    # Multiple indistinguishable lexical readings cannot select an accent.
    return choices if len(choices) == 1 else set()


def validate_manifest_stress(manifest: dict[str, Any]) -> dict[str, Any]:
    """Count all rows, compare each stored accent, and reject unbound display stress.

    Legacy rows without raw tags are joined through their decoded label and exact
    VESUM spelling. Missing stress is reported separately from incorrect stress.
    No missing or ambiguous authority may authenticate a stored accent. The display
    map is checked against the lemma's whole modern VESUM paradigm, because the
    card renders paradigm cells beyond the capped ``forms`` rows.
    """
    report: dict[str, Any] = {
        "entries": 0,
        "rows": 0,
        "authority_rows": 0,
        "stressed_rows": 0,
        "unresolved_rows": 0,
        "missing_stress_rows": 0,
        "display_values": 0,
        "disagreements": [],
    }
    for entry in manifest.get("entries", []):
        morphology = (entry.get("enrichment") or {}).get("morphology") or {}
        rows = [*morphology.get("forms", []), *morphology.get("marked_forms", [])]
        if not rows:
            continue
        report["entries"] += 1
        lemma = _base_lemma(str(entry.get("lemma") or ""))
        analyses = [{**v, "lemma": lemma} for v in verify_lemma(lemma)]
        memo: dict[tuple[str, str, str], set[str]] = {}
        for row in rows:
            report["rows"] += 1
            form = row["form"]
            witnesses = [
                v
                for v in analyses
                if v["word_form"] == form
                and (v["tags"] == row["tags"] if row.get("tags") else _decode_tag(v["tags"]) == row.get("label", ""))
            ]
            choices = _choices(lemma, witnesses, memo)
            report["authority_rows" if choices else "unresolved_rows"] += 1
            stored = row.get("stress")
            if stored:
                report["stressed_rows"] += 1
                if stored not in choices or _strip_stress(stored) != _strip_stress(form):
                    report["disagreements"].append(
                        {
                            "lemma": lemma,
                            "form": form,
                            "tags": row.get("tags"),
                            "label": row.get("label"),
                            "stored": stored,
                            "expected": sorted(choices),
                        }
                    )
            elif choices:
                report["missing_stress_rows"] += 1
        display = (morphology.get("stress") or {}).get("forms", {})
        # Every modern reading of a spelling, including ones past the row cap or
        # dropped as same-label duplicates, must license the displayed accent.
        # The separate marked group never feeds the modern display map.
        allowed_by_form: dict[str, list[set[str]]] = {}
        if display:
            for analysis in analyses:
                if _paradigm_row_kind(analysis) == "modern":
                    allowed_by_form.setdefault(analysis["word_form"], []).append(_choices(lemma, [analysis], memo))
        for form, stored in display.items():
            report["display_values"] += 1
            forms, accents = form.split(" / "), stored.split(" / ")
            valid = len(forms) == len(accents) and all(
                part in allowed_by_form and all(accent in choices for choices in allowed_by_form[part])
                for part, accent in zip(forms, accents, strict=False)
            )
            if not valid:
                report["disagreements"].append(
                    {
                        "lemma": lemma,
                        "form": form,
                        "stored": stored,
                        "kind": "display_stress",
                    }
                )
    report["disagreement_count"] = len(report["disagreements"])
    return report


def build_parser() -> argparse.ArgumentParser:
    """Describe the read-only manifest stress audit."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate every paradigm row and display stress against local ULIF/VESUM.\n"
            "Use before accepting an enriched candidate; this never repairs or publishes cards."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.lexicon.validate_paradigm_stress --manifest candidate.json\n"
            "Outputs: JSON report on stdout; no file or database writes.\n"
            "Exit codes: 0 = zero disagreements with a nonempty denominator; "
            "1 = disagreements or empty denominator; 2 = invalid invocation.\n"
            "Related: #9820; scripts/lexicon/enrich_manifest.py; WORD_CARDS_DATA_PLAN.md W1b/W2."
        ),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Local candidate manifest JSON to audit, for example pilot-manifest.json (required; no default).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Print a complete denominator and return failure on any stored disagreement."""
    args = build_parser().parse_args(argv)
    report = validate_manifest_stress(json.loads(args.manifest.read_text(encoding="utf-8")))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(bool(report["disagreement_count"]) or not report["rows"])


if __name__ == "__main__":
    raise SystemExit(main())
