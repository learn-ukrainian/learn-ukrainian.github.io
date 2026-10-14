"""Audit every manifest morphology row against local ULIF/VESUM authority (#9820)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.lexicon.enrich_manifest import _base_lemma, _decode_tag
from scripts.verification.stress import _strip_stress, verify_stress
from scripts.verification.ulif_stress import analysis_features, readings, select_analyses
from scripts.verification.vesum import verify_lemma


def validate_manifest_stress(manifest: dict[str, Any]) -> dict[str, Any]:
    """Count all rows, compare each stored accent, and reject unbound display stress.

    Legacy rows without raw tags are joined through their decoded label and exact
    VESUM spelling. Missing stress is reported separately from incorrect stress.
    No missing or ambiguous authority may authenticate a stored accent.
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
        analyses = verify_lemma(lemma)
        allowed_by_form: dict[str, list[set[str]]] = {}
        for row in rows:
            report["rows"] += 1
            form = row["form"]
            witnesses = [
                {**v, "lemma": lemma}
                for v in analyses
                if v["word_form"] == form
                and (v["tags"] == row["tags"] if row.get("tags") else _decode_tag(v["tags"]) == row.get("label", ""))
            ]
            choices: set[str] = set()
            for witness in witnesses:
                supplied = analysis_features(witness)
                slot = {tag for tag in supplied if tag.split("=", 1)[0] in {"upos", "Case", "Number"}}
                matches = readings(form, supplied=supplied, lemma=lemma, vesum=[witness])
                matches = [m for m in matches if slot <= set(m["required_tags"])]
                if not matches:
                    oracle = verify_stress(form, lemma=lemma, tags=witness["tags"])
                    if oracle["status"] == "ok":
                        candidates = oracle["matches"]
                        if candidates and all(
                            slot <= set(m["required_tags"])
                            and select_analyses(m.get("vesum_analyses", []), supplied, lemma)
                            for m in candidates
                        ):
                            matches = candidates
                choices.update(m["stressed_form"] for m in matches)
            # Multiple indistinguishable lexical readings cannot select an accent.
            if len(choices) != 1:
                choices = set()
            # The modern display map never includes the separate marked group.
            if not row.get("marker"):
                allowed_by_form.setdefault(form, []).append(choices)
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
        for form, stored in (morphology.get("stress") or {}).get("forms", {}).items():
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
