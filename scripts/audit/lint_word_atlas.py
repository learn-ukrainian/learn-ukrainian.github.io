#!/usr/bin/env python3
"""Sense-first Word Atlas entry lint (#6437 PR1): LINT-001 + LINT-002.

Read-only, advisory lint over the `senses[]` array documented in
``docs/runbooks/word-atlas-entry-model.md`` (§ Sense-Level Fields, #6437
delta). It never mutates a manifest — it only reports.

Rules implemented
==================
- **LINT-001** ``TRUNCATED_TEXT_CUTOFF`` — a learner-facing sense field
  (``uk_source_def``, ``learner_uk``, ``learner_en[]``, ``en_disambiguation``,
  ``grammar_notes``) ends in ``...``/``…`` while ``completeness`` is not
  honestly tagged ``"truncated"``.
- **LINT-002** ``AMBIGUOUS_BARE_EN`` — ``learner_en`` is a single-item list,
  the word is in the high-risk polysemy denylist below, and
  ``en_disambiguation`` is missing or blank.

Rules NOT implemented here (tracked against issue #6437, later PRs):
LINT-003 ``DRILL_SENSE_ID_MISSING``, LINT-004 ``UNVETTED_EN_SOURCE``,
LINT-101 ``MULTI_SENSE_UK_SINGLE_EN``, LINT-102 ``POS_TRANSFORMATION_MISMATCH``.

Scope
=====
Entries without a ``senses`` array are silently skipped — most of the
production manifest predates this schema, and PR1 does not bulk-migrate or
retranslate existing entries (issue #6437 non-goals). This script only lints
manifests/entries that already carry sense-first data.

Use when
========
- Local dry run against a small fixture while building sense-first content.
- Optional report mode against a local manifest — writes residual findings
  to a gitignored ``batch_state/`` path only; never to a tracked doc.

Examples
========

    .venv/bin/python scripts/audit/lint_word_atlas.py
    .venv/bin/python scripts/audit/lint_word_atlas.py --manifest path/to/manifest.json
    .venv/bin/python scripts/audit/lint_word_atlas.py --manifest path/to/manifest.json \\
        --report batch_state/atlas-drive/lint-word-atlas-residual.json
    .venv/bin/python scripts/audit/lint_word_atlas.py --strict   # exit 1 on any finding

Outputs
=======
- stdout: table of findings (rule, entry, sense, field, detail).
- exit 0 always, unless ``--strict`` is passed and findings exist (exit 1).
  No CI gate consumes this yet (advisory only — issue #6437 D6-7 sets the
  residual policy before any blocking wiring).

Related
=======
- Issue #6437 — sense-first lintable entry gate.
- Schema: docs/runbooks/word-atlas-entry-model.md § Sense-Level Fields.
- Sibling guardrails: scripts/audit/check_atlas_manifest_enrichment.py.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "atlas" / "sense_lint_sample.json"

# Learner-facing string fields checked by LINT-001. `uk_source_def` is raw
# ingestion text (immutable — see schema doc) but a dishonest completeness
# tag on it is still worth flagging: the lint reads it, it never rewrites it.
_TRUNCATION_CHECKED_FIELDS = (
    "uk_source_def",
    "learner_uk",
    "en_disambiguation",
    "grammar_notes",
)
_ELLIPSIS_MARKERS = ("...", "…")
_HONEST_TRUNCATED_TAG = "truncated"

# High-risk polysemy seed set (Gemini consult, #6437). A bare single-word EN
# target from this set reads as one common sense while hiding an unrelated
# one (e.g. "second" as ordinal vs "seconds" as manufacturing defects/брак).
# Not exhaustive by design — extend as new false-friend cases surface.
AMBIGUOUS_BARE_EN_DENYLIST = frozenset(
    {
        "second",
        "set",
        "bank",
        "match",
        "light",
        "bear",
        "fair",
        "spring",
        "bat",
        "date",
        "fine",
        "left",
        "right",
        "party",
        "book",
        "fly",
        "watch",
        "sound",
        "novel",
        "stable",
        "mine",
        "current",
        "seal",
        "tear",
        "wave",
        "pitch",
        "note",
        "trip",
        "letter",
    }
)

LINT_001 = "LINT-001"
LINT_002 = "LINT-002"


@dataclass(frozen=True)
class LintFinding:
    rule_id: str
    rule_name: str
    entry_slug: str
    sense_id: str
    field: str
    detail: str


def _entries(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    entries = manifest.get("entries")
    if isinstance(entries, list):
        return [entry for entry in entries if isinstance(entry, dict)]
    return []


def _entry_slug(entry: dict[str, Any]) -> str:
    slug = entry.get("slug") or entry.get("lemma")
    return str(slug) if slug else "<unknown-entry>"


def _senses(entry: dict[str, Any]) -> list[dict[str, Any]]:
    senses = entry.get("senses")
    if isinstance(senses, list):
        return [sense for sense in senses if isinstance(sense, dict)]
    return []


def _sense_id(sense: dict[str, Any]) -> str:
    sense_id = sense.get("id")
    return str(sense_id) if sense_id else "<missing-sense-id>"


def _is_truncated_text(value: object) -> bool:
    return isinstance(value, str) and value.rstrip().endswith(_ELLIPSIS_MARKERS)


def _check_truncated_text_cutoff(
    entry_slug: str, sense_id: str, sense: dict[str, Any]
) -> list[LintFinding]:
    if sense.get("completeness") == _HONEST_TRUNCATED_TAG:
        return []

    findings: list[LintFinding] = []
    for field in _TRUNCATION_CHECKED_FIELDS:
        value = sense.get(field)
        if _is_truncated_text(value):
            findings.append(
                LintFinding(
                    rule_id=LINT_001,
                    rule_name="TRUNCATED_TEXT_CUTOFF",
                    entry_slug=entry_slug,
                    sense_id=sense_id,
                    field=field,
                    detail=f"ends in an ellipsis without completeness={_HONEST_TRUNCATED_TAG!r}: {value!r}",
                )
            )

    learner_en = sense.get("learner_en")
    if isinstance(learner_en, list):
        for index, item in enumerate(learner_en):
            if _is_truncated_text(item):
                findings.append(
                    LintFinding(
                        rule_id=LINT_001,
                        rule_name="TRUNCATED_TEXT_CUTOFF",
                        entry_slug=entry_slug,
                        sense_id=sense_id,
                        field=f"learner_en[{index}]",
                        detail=f"ends in an ellipsis without completeness={_HONEST_TRUNCATED_TAG!r}: {item!r}",
                    )
                )
    return findings


def _check_ambiguous_bare_en(
    entry_slug: str, sense_id: str, sense: dict[str, Any]
) -> list[LintFinding]:
    learner_en = sense.get("learner_en")
    if not isinstance(learner_en, list) or len(learner_en) != 1:
        return []

    word = learner_en[0]
    if not isinstance(word, str):
        return []

    normalized = word.strip().casefold()
    if normalized not in AMBIGUOUS_BARE_EN_DENYLIST:
        return []

    disambiguation = sense.get("en_disambiguation")
    if isinstance(disambiguation, str) and disambiguation.strip():
        return []

    return [
        LintFinding(
            rule_id=LINT_002,
            rule_name="AMBIGUOUS_BARE_EN",
            entry_slug=entry_slug,
            sense_id=sense_id,
            field="learner_en",
            detail=(
                f"bare single-word EN {word!r} is a high-risk polysemy target "
                "with no en_disambiguation"
            ),
        )
    ]


def lint_manifest(manifest: dict[str, Any]) -> list[LintFinding]:
    """Return every LINT-001/LINT-002 finding for a manifest's ``senses[]``.

    Entries without a ``senses`` array are silently skipped (see module
    docstring: PR1 does not lint or migrate legacy non-sense-first entries).
    """
    findings: list[LintFinding] = []
    for entry in _entries(manifest):
        slug = _entry_slug(entry)
        for sense in _senses(entry):
            sense_id = _sense_id(sense)
            findings.extend(_check_truncated_text_cutoff(slug, sense_id, sense))
            findings.extend(_check_ambiguous_bare_en(slug, sense_id, sense))
    return findings


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"::error::cannot read manifest {path}: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict):
        print(f"::error::{path} must contain a JSON object", file=sys.stderr)
        sys.exit(2)
    return data


def print_report(findings: list[LintFinding]) -> None:
    if not findings:
        print("No LINT-001/LINT-002 findings — sense-first entries lint clean.")
        return

    rows = [
        (
            finding.rule_id,
            finding.rule_name,
            finding.entry_slug,
            finding.sense_id,
            finding.field,
            finding.detail,
        )
        for finding in findings
    ]
    headers = ("rule", "name", "entry", "sense_id", "field", "detail")
    widths = [
        max(len(headers[i]), max(len(str(row[i])) for row in rows)) for i in range(len(headers))
    ]
    header_line = "  ".join(h.ljust(w) for h, w in zip(headers, widths, strict=True))
    print(header_line)
    print("-" * len(header_line))
    for row in rows:
        print("  ".join(str(cell).ljust(w) for cell, w in zip(row, widths, strict=True)))

    by_rule: dict[str, int] = {}
    for finding in findings:
        by_rule[finding.rule_id] = by_rule.get(finding.rule_id, 0) + 1
    summary = ", ".join(f"{rule}={count}" for rule, count in sorted(by_rule.items()))
    print()
    print(f"⚠️  {len(findings)} finding(s) ({summary}) — advisory, not blocking.")


def write_report(findings: list[LintFinding], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "rule_ids": [LINT_001, LINT_002],
        "finding_count": len(findings),
        "findings": [asdict(finding) for finding in findings],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Advisory sense-first Word Atlas lint: LINT-001 TRUNCATED_TEXT_CUTOFF + "
            "LINT-002 AMBIGUOUS_BARE_EN (issue #6437 PR1)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_FIXTURE,
        help=f"Manifest JSON path with a top-level 'entries' list. Default: {DEFAULT_FIXTURE}.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help=(
            "Write findings as JSON to this path (residual report mode). Must resolve "
            "under a gitignored location such as batch_state/ — this script does not "
            "enforce that, but committing lint residuals is a policy violation."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when findings exist. Default is advisory (always exit 0).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = PROJECT_ROOT / manifest_path
    if not manifest_path.exists() or not manifest_path.is_file():
        parser.error(f"manifest does not exist or is not a file: {manifest_path}")

    manifest = _load_manifest(manifest_path)
    findings = lint_manifest(manifest)
    print_report(findings)

    if args.report:
        report_path = args.report if args.report.is_absolute() else PROJECT_ROOT / args.report
        write_report(findings, report_path)
        print(f"Residual report written to {report_path}")

    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
