#!/usr/bin/env python3
"""Seat-viability decision metric for the QG grounded-reviewer bakeoff (#4797).

Replaces the tooled−bare aggregate lift as the go/no-go seat metric. The
DEFER_ALL post-mortem (docs/projects/qg-quality-gate/model-evidence.md,
"Subscription-runtime 1×17 STRICT sweep — CORRECTED") showed lift is
structurally broken for decisions: the bare arm was scored grounding-free
while the tooled arm was scored grounding-STRICT, so the difference is
negative by arithmetic, not behavior. Lift remains an ablation diagnostic.

The decision consumes only the EFFECTIVE (post-gate) verdict stream —
grounding admissibility is a hard precondition on credit, never an extra
rate floor — and emits per-seat decisions with machine failure reasons:

- ``VIABLE`` / ``VIABLE_WITH_AUDIT`` / ``NOT_VIABLE`` / ``INSUFFICIENT_DATA``
- reasons: ``UNSAFE_ACCEPT``, ``U_RECALL_FLOOR``, ``M_RECALL_FLOOR``,
  ``TRUE_RETENTION_FLOOR``, ``TRUE_REFUTED_GUARDRAIL``, ``COVERAGE_FLOOR``,
  ``DOMAIN_FLOOR_<domain>_<metric>``, plus audit notes
  ``DOMAIN_LOW_N_<domain>``, ``UNSAFE_ACCEPTS_UNKNOWN``,
  ``TRUE_RETENTION_UNKNOWN`` (degraded input mode).

This module is OFFLINE-ONLY: it reads stored bakeoff artifact JSONs (or, in
an explicitly-labeled degraded mode, a committed SCORECARD.md) and never
triggers model calls. Thresholds are quality floors documented in
docs/projects/qg-quality-gate/calibration_criteria.md — never lowered to
make a seat pass (non-negotiable rules).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import qg_factcheck_scoring

# Domain routing mirrors qg_bakeoff.DOMAIN_BY_SLUG; imported lazily in the CLI
# to keep this module pure/stdlib for library consumers (qg_bakeoff pulls the
# full reviewer-dispatch import chain).
DECISION_VIABLE = "VIABLE"
DECISION_VIABLE_WITH_AUDIT = "VIABLE_WITH_AUDIT"
DECISION_NOT_VIABLE = "NOT_VIABLE"
DECISION_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

# Floors are MINIMUMS (non-negotiable rules). Provenance:
# calibration_criteria.md §6 (seat-decision thresholds v1). E3 = the live
# Tier-2 exit criteria in the same file.
U_RECALL_FLOOR = 0.75  # E3(c): class-U honesty ≥ 3/4
M_RECALL_FLOOR = 4 / 7  # E3(b): class-M alignment ≥ 4/7
TRUE_RETENTION_FLOOR = 0.5  # NEW v1 floor — operator-gated with the paid re-sweep
TRUE_REFUTED_CEILING = 0.1  # NEW v1 guardrail — refuting true content is a −50 event
COVERAGE_FLOOR = 0.9  # E3(b) missing_claims=0, scaled to a multi-transport matrix
MIN_DOMAIN_N = 4  # below this a domain is flagged low-N, not judged
LOW_N_DENOMINATOR = 10  # matches the scorecard low-N convention

_UNSUPPORTED_VERDICTS = {"UNATTESTED_AFTER_SEARCH", "UNVERIFIED_INSUFFICIENT_SEARCH"}
_NEUTRALIZED_VERDICT = "UNVERIFIED_INSUFFICIENT_SEARCH"
_MISSING = "MISSING"

_Z_95 = 1.959963984540054  # two-sided 95%


class SeatDecisionError(ValueError):
    """Input or parse error for the seat-decision CLI."""


@dataclass(frozen=True, slots=True)
class ClaimObservation:
    """One effective (post-gate) claim outcome from one judged cell."""

    seat: str
    arm: str
    slug: str
    domain: str
    run: int
    claim_id: str | None
    is_true: bool
    fabrication_class: str | None
    effective_verdict: str  # MISSING when the model omitted the claim


@dataclass(slots=True)
class RateWithCI:
    numerator: int
    denominator: int

    @property
    def rate(self) -> float | None:
        return self.numerator / self.denominator if self.denominator else None

    @property
    def wilson95(self) -> tuple[float, float] | None:
        return wilson_interval(self.numerator, self.denominator)

    @property
    def low_n(self) -> bool:
        return self.denominator < LOW_N_DENOMINATOR

    def as_dict(self) -> dict[str, Any]:
        interval = self.wilson95
        return {
            "numerator": self.numerator,
            "denominator": self.denominator,
            "rate": self.rate,
            "wilson95": list(interval) if interval else None,
            "low_n": self.low_n,
        }

    def label(self) -> str:
        if self.denominator == 0:
            return "n/a"
        interval = self.wilson95
        assert interval is not None
        suffix = " low-N" if self.low_n else ""
        return f"{self.numerator}/{self.denominator} = {self.rate:.3f} [{interval[0]:.3f}..{interval[1]:.3f}]{suffix}"


@dataclass(slots=True)
class SeatReport:
    seat: str
    runs: int
    cells: int
    unsafe_accepts: RateWithCI | None  # None = unknown (degraded input)
    unsafe_accept_claims: list[dict[str, Any]] = field(default_factory=list)
    u_recall: RateWithCI = field(default_factory=lambda: RateWithCI(0, 0))
    m_recall: RateWithCI = field(default_factory=lambda: RateWithCI(0, 0))
    true_retention: RateWithCI | None = None  # None = unknown (degraded input)
    true_refuted: RateWithCI | None = None
    true_unsupported: RateWithCI = field(default_factory=lambda: RateWithCI(0, 0))
    coverage: RateWithCI | None = None
    by_domain: dict[str, dict[str, RateWithCI]] = field(default_factory=dict)
    decision: str = DECISION_INSUFFICIENT_DATA
    reasons: list[str] = field(default_factory=list)
    audit_notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "seat": self.seat,
            "runs": self.runs,
            "cells": self.cells,
            "decision": self.decision,
            "reasons": self.reasons,
            "audit_notes": self.audit_notes,
            "unsafe_accepts": self.unsafe_accepts.as_dict() if self.unsafe_accepts else None,
            "unsafe_accept_claims": self.unsafe_accept_claims,
            "u_recall": self.u_recall.as_dict(),
            "m_recall": self.m_recall.as_dict(),
            "true_retention": self.true_retention.as_dict() if self.true_retention else None,
            "true_refuted": self.true_refuted.as_dict() if self.true_refuted else None,
            "true_unsupported": self.true_unsupported.as_dict(),
            "coverage": self.coverage.as_dict() if self.coverage else None,
            "by_domain": {
                domain: {name: rate.as_dict() for name, rate in metrics.items()}
                for domain, metrics in self.by_domain.items()
            },
        }


def wilson_interval(successes: int, total: int, z: float = _Z_95) -> tuple[float, float] | None:
    """Wilson score interval for a binomial proportion; None when total == 0."""
    if total == 0:
        return None
    if successes < 0 or successes > total:
        raise SeatDecisionError(f"invalid fraction {successes}/{total}")
    phat = successes / total
    denom = 1 + z * z / total
    center = (phat + z * z / (2 * total)) / denom
    margin = (z / denom) * math.sqrt(phat * (1 - phat) / total + z * z / (4 * total * total))
    return (max(0.0, center - margin), min(1.0, center + margin))


def _fabrication_caught(verdict: str) -> bool:
    return qg_factcheck_scoring.score_verdict(verdict, claim_is_true=False) > 0


def effective_verdict(per_claim_row: Mapping[str, Any]) -> str:
    """The post-gate verdict the live path would credit (STRICT #4761 semantics)."""
    if per_claim_row.get("matched") is False:
        return _MISSING
    if per_claim_row.get("live_admissible_neutralized") is True:
        return _NEUTRALIZED_VERDICT
    return str(per_claim_row.get("verdict") or "").strip().upper()


def observations_from_artifacts(
    artifacts: Iterable[Mapping[str, Any]],
    domain_by_slug: Mapping[str, str],
) -> list[ClaimObservation]:
    """Extract effective claim outcomes from tooled, judged bakeoff artifacts.

    ops_quota cells are excluded (not model behavior); error cells are judged
    cells scored all-missing upstream and flow through unchanged.
    """
    observations: list[ClaimObservation] = []
    for artifact in artifacts:
        if artifact.get("failure_class") == "ops_quota":
            continue
        arm = str(artifact.get("arm") or "tooled")
        model = artifact.get("model")
        if isinstance(model, Mapping):
            seat = (
                f"{model.get('pin') or model.get('pin_slug') or 'unknown'} "
                f"[{model.get('transport') or 'opencode'}/{model.get('entrypoint') or 'qg_bakeoff_opencode'}]"
            )
        else:
            seat = "unknown [opencode/qg_bakeoff_opencode]"
        fixture = artifact.get("fixture")
        slug = str(fixture.get("slug")) if isinstance(fixture, Mapping) else "unknown"
        run = int(artifact.get("run_index") or 1)
        score = artifact.get("score")
        claims = score.get("claims") if isinstance(score, Mapping) else None
        if not isinstance(claims, list):
            continue
        for row in claims:
            if not isinstance(row, Mapping):
                continue
            observations.append(
                ClaimObservation(
                    seat=seat,
                    arm=arm,
                    slug=slug,
                    domain=domain_by_slug.get(slug, "unknown"),
                    run=run,
                    claim_id=row.get("claim_id"),
                    is_true=bool(row.get("is_true")),
                    fabrication_class=row.get("fabrication_class"),
                    effective_verdict=effective_verdict(row),
                )
            )
    return observations


def decide_seat(
    seat: str,
    observations: Sequence[ClaimObservation],
    *,
    unsafe_accept_allowlist: Sequence[Mapping[str, Any]] = (),
) -> SeatReport:
    """Compute the seat metrics and decision from effective claim outcomes."""
    tooled = [o for o in observations if o.seat == seat and o.arm == "tooled"]
    runs = len({o.run for o in tooled})
    cells = len({(o.slug, o.run) for o in tooled})

    allow = {(str(e.get("fixture")), str(e.get("claim_id"))) for e in unsafe_accept_allowlist}
    unsafe_rows = [
        o
        for o in tooled
        if not o.is_true and o.effective_verdict == "CONFIRMED" and (o.slug, str(o.claim_id)) not in allow
    ]
    false_total = sum(1 for o in tooled if not o.is_true)

    u_rows = [o for o in tooled if o.fabrication_class == "U"]
    m_rows = [o for o in tooled if o.fabrication_class == "M"]
    true_rows = [o for o in tooled if o.is_true]

    report = SeatReport(seat=seat, runs=runs, cells=cells, unsafe_accepts=RateWithCI(len(unsafe_rows), false_total))
    report.unsafe_accept_claims = [{"fixture": o.slug, "claim_id": o.claim_id, "run": o.run} for o in unsafe_rows]
    report.u_recall = RateWithCI(sum(1 for o in u_rows if _fabrication_caught(o.effective_verdict)), len(u_rows))
    report.m_recall = RateWithCI(sum(1 for o in m_rows if _fabrication_caught(o.effective_verdict)), len(m_rows))
    report.true_retention = RateWithCI(sum(1 for o in true_rows if o.effective_verdict == "CONFIRMED"), len(true_rows))
    report.true_refuted = RateWithCI(
        sum(1 for o in true_rows if o.effective_verdict == "REFUTED_BY_CONTRADICTION"), len(true_rows)
    )
    report.true_unsupported = RateWithCI(
        sum(1 for o in true_rows if o.effective_verdict in _UNSUPPORTED_VERDICTS), len(true_rows)
    )
    report.coverage = RateWithCI(sum(1 for o in tooled if o.effective_verdict != _MISSING), len(tooled))
    for domain in sorted({o.domain for o in tooled}):
        rows = [o for o in tooled if o.domain == domain]
        report.by_domain[domain] = {
            "u_recall": RateWithCI(
                sum(1 for o in rows if o.fabrication_class == "U" and _fabrication_caught(o.effective_verdict)),
                sum(1 for o in rows if o.fabrication_class == "U"),
            ),
            "m_recall": RateWithCI(
                sum(1 for o in rows if o.fabrication_class == "M" and _fabrication_caught(o.effective_verdict)),
                sum(1 for o in rows if o.fabrication_class == "M"),
            ),
            "true_retention": RateWithCI(
                sum(1 for o in rows if o.is_true and o.effective_verdict == "CONFIRMED"),
                sum(1 for o in rows if o.is_true),
            ),
        }
    _apply_decision(report)
    return report


def _apply_decision(report: SeatReport) -> None:
    """Shared decision logic for full and degraded (scorecard) inputs."""
    if report.u_recall.denominator == 0 or report.m_recall.denominator == 0:
        report.decision = DECISION_INSUFFICIENT_DATA
        report.reasons = ["INSUFFICIENT_DATA"]
        return

    reasons: list[str] = []
    notes: list[str] = list(report.audit_notes)

    if report.unsafe_accepts is None:
        notes.append("UNSAFE_ACCEPTS_UNKNOWN")
    elif report.unsafe_accepts.numerator > 0:
        reasons.append("UNSAFE_ACCEPT")
    if report.u_recall.rate is not None and report.u_recall.rate < U_RECALL_FLOOR:
        reasons.append("U_RECALL_FLOOR")
    if report.m_recall.rate is not None and report.m_recall.rate < M_RECALL_FLOOR:
        reasons.append("M_RECALL_FLOOR")
    if report.true_retention is None:
        notes.append("TRUE_RETENTION_UNKNOWN")
    elif report.true_retention.rate is not None and report.true_retention.rate < TRUE_RETENTION_FLOOR:
        reasons.append("TRUE_RETENTION_FLOOR")
    if (
        report.true_refuted is not None
        and report.true_refuted.rate is not None
        and report.true_refuted.rate > TRUE_REFUTED_CEILING
    ):
        reasons.append("TRUE_REFUTED_GUARDRAIL")
    if report.coverage is not None and report.coverage.rate is not None and report.coverage.rate < COVERAGE_FLOOR:
        reasons.append("COVERAGE_FLOOR")

    floors = (("u_recall", U_RECALL_FLOOR), ("m_recall", M_RECALL_FLOOR), ("true_retention", TRUE_RETENTION_FLOOR))
    for domain, metrics in sorted(report.by_domain.items()):
        for name, floor in floors:
            rate = metrics.get(name)
            if rate is None or rate.denominator == 0:
                continue
            if rate.denominator < MIN_DOMAIN_N:
                note = f"DOMAIN_LOW_N_{domain}"
                if note not in notes:
                    notes.append(note)
                continue
            assert rate.rate is not None
            if rate.rate < floor:
                reasons.append(f"DOMAIN_FLOOR_{domain}_{name}")

    report.reasons = reasons
    report.audit_notes = notes
    if reasons:
        report.decision = DECISION_NOT_VIABLE
    elif notes:
        report.decision = DECISION_VIABLE_WITH_AUDIT
    else:
        report.decision = DECISION_VIABLE


# ---------------------------------------------------------------------------
# Degraded input: committed SCORECARD.md (raw artifacts swept from disk).
# The Runs table is emitted by qg_bakeoff._runs_table; the parser is
# round-trip-tested against it. Per-claim verdicts are NOT recoverable, so
# unsafe accepts and true retention are UNKNOWN → the decision is capped at
# VIABLE_WITH_AUDIT even when every computable floor passes.
# ---------------------------------------------------------------------------

_FRACTION_RE = re.compile(r"^(\d+)/(\d+)")


def _parse_fraction(text: str) -> tuple[int, int]:
    match = _FRACTION_RE.match(text.strip())
    if not match:
        raise SeatDecisionError(f"unparseable fraction cell: {text!r}")
    return int(match.group(1)), int(match.group(2))


def parse_scorecard_runs_table(markdown: str) -> list[dict[str, Any]]:
    """Parse per-cell rows from a scorecard's ``## Runs`` table."""
    lines = markdown.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == "## Runs")
    except StopIteration as exc:
        raise SeatDecisionError("no '## Runs' section in scorecard") from exc
    header: list[str] | None = None
    rows: list[dict[str, Any]] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if header is None:
            header = [cell.lower() for cell in cells]
            continue
        if set("".join(cells)) <= {"-", ":", " "}:
            continue
        rows.append(dict(zip(header, cells, strict=False)))
    if header is None:
        raise SeatDecisionError("no table header under '## Runs'")
    required = {"model", "passage", "arm", "status", "u honesty", "m alignment", "true unsupported", "missing"}
    missing_columns = required - set(header)
    if missing_columns:
        raise SeatDecisionError(f"scorecard Runs table missing columns: {sorted(missing_columns)}")
    return rows


def seat_reports_from_scorecard(
    markdown: str,
    domain_by_slug: Mapping[str, str],
    claims_per_fixture: Mapping[str, int],
) -> list[SeatReport]:
    """Build degraded-mode seat reports from a committed scorecard."""
    rows = parse_scorecard_runs_table(markdown)
    by_seat: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("arm") == "tooled":
            by_seat[row["model"]].append(row)
    reports: list[SeatReport] = []
    for seat in sorted(by_seat):
        cells = by_seat[seat]
        u_good = u_total = m_good = m_total = 0
        true_unsup = true_total = 0
        missing = claims_total = 0
        domain_acc: dict[str, dict[str, list[int]]] = defaultdict(lambda: {"u": [0, 0], "m": [0, 0]})
        for cell in cells:
            slug = cell["passage"]
            domain = domain_by_slug.get(slug, "unknown")
            for key, prefix in (("u honesty", "u"), ("m alignment", "m")):
                good, total = _parse_fraction(cell[key])
                domain_acc[domain][prefix][0] += good
                domain_acc[domain][prefix][1] += total
                if prefix == "u":
                    u_good, u_total = u_good + good, u_total + total
                else:
                    m_good, m_total = m_good + good, m_total + total
            unsupported, total_true = _parse_fraction(cell["true unsupported"])
            true_unsup += unsupported
            true_total += total_true
            missing += int(cell["missing"])
            fixture_claims = claims_per_fixture.get(slug)
            if fixture_claims is None:
                raise SeatDecisionError(f"no fixture claim count for scorecard passage {slug!r}")
            claims_total += fixture_claims
        report = SeatReport(
            seat=seat,
            runs=len({cell.get("run", "1") for cell in cells}),
            cells=len(cells),
            unsafe_accepts=None,
            u_recall=RateWithCI(u_good, u_total),
            m_recall=RateWithCI(m_good, m_total),
            true_retention=None,
            true_refuted=None,
            true_unsupported=RateWithCI(true_unsup, true_total),
            coverage=RateWithCI(claims_total - missing, claims_total),
        )
        report.by_domain = {
            domain: {
                "u_recall": RateWithCI(*acc["u"]),
                "m_recall": RateWithCI(*acc["m"]),
            }
            for domain, acc in sorted(domain_acc.items())
        }
        _apply_decision(report)
        reports.append(report)
    return reports


# ---------------------------------------------------------------------------
# Rendering + CLI
# ---------------------------------------------------------------------------

_THRESHOLDS = {
    "u_recall_floor": U_RECALL_FLOOR,
    "m_recall_floor": M_RECALL_FLOOR,
    "true_retention_floor": TRUE_RETENTION_FLOOR,
    "true_refuted_ceiling": TRUE_REFUTED_CEILING,
    "coverage_floor": COVERAGE_FLOOR,
    "min_domain_n": MIN_DOMAIN_N,
}


def render_markdown(reports: Sequence[SeatReport], *, source: str, degraded: bool) -> str:
    lines = [
        "# QG Seat Decision (#4797 decision metric v2)",
        "",
        f"Source: `{source}` — offline, no model calls.",
        "Thresholds: docs/projects/qg-quality-gate/calibration_criteria.md §6 "
        "(floors are minimums — never lowered to pass a seat).",
        "The tooled−bare lift is NOT an input to these decisions (ablation diagnostic only).",
        "",
    ]
    if degraded:
        lines += [
            "> DEGRADED INPUT: per-claim verdicts are not recoverable from a scorecard, so",
            "> unsafe accepts and true retention are UNKNOWN and every passing seat is capped",
            "> at VIABLE_WITH_AUDIT. A full verdict needs the artifact JSONs (paid re-sweep).",
            "",
        ]
    lines += [
        "| seat | decision | reasons | U recall | M recall | true retention | true refuted | true unsupported | unsafe accepts | coverage |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for report in reports:

        def _cell(rate: RateWithCI | None) -> str:
            return rate.label() if rate is not None else "unknown"

        reasons = ", ".join(report.reasons + report.audit_notes) or "—"
        lines.append(
            f"| {report.seat} | **{report.decision}** | {reasons} "
            f"| {_cell(report.u_recall)} | {_cell(report.m_recall)} "
            f"| {_cell(report.true_retention)} | {_cell(report.true_refuted)} "
            f"| {_cell(report.true_unsupported)} | {_cell(report.unsafe_accepts)} "
            f"| {_cell(report.coverage)} |"
        )
    lines.append("")
    for report in reports:
        if not report.by_domain:
            continue
        lines += [f"### {report.seat} — per-domain", ""]
        lines += ["| domain | " + " | ".join(sorted(next(iter(report.by_domain.values())))) + " |"]
        lines += ["| --- |" + " --- |" * len(next(iter(report.by_domain.values())))]
        for domain, metrics in sorted(report.by_domain.items()):
            cells = " | ".join(metrics[name].label() for name in sorted(metrics))
            lines.append(f"| {domain} | {cells} |")
        lines.append("")
    return "\n".join(lines)


def _load_artifacts(out_dir: Path) -> list[dict[str, Any]]:
    artifacts = []
    for path in sorted(out_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SeatDecisionError(f"unreadable artifact {path}: {exc}") from exc
        if isinstance(data, dict) and isinstance(data.get("fixture"), dict):
            artifacts.append(data)
    return artifacts


def _claims_per_fixture(fixtures_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in sorted(fixtures_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        claims = data.get("claims")
        if isinstance(data.get("slug"), str) and isinstance(claims, list):
            counts[data["slug"]] = len(claims)
    if not counts:
        raise SeatDecisionError(f"no fixtures with claims under {fixtures_dir}")
    return counts


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        type=Path,
        help="Bakeoff out-dir with artifact JSONs, or a SCORECARD*.md (degraded mode)",
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=PROJECT_ROOT / "tests" / "fixtures" / "qg_bakeoff",
        help="Fixture corpus (claim totals for coverage in scorecard mode)",
    )
    parser.add_argument(
        "--allowlist",
        type=Path,
        default=None,
        help="JSON file with unsafe_accept_allowlist: [{fixture, claim_id}] (reviewed commits only)",
    )
    parser.add_argument("--json-out", type=Path, default=None, help="Write decision JSON here")
    parser.add_argument("--md-out", type=Path, default=None, help="Write DECISION.md here")
    args = parser.parse_args(argv)

    from scripts.audit.qg_bakeoff import DOMAIN_BY_SLUG

    allowlist: list[Mapping[str, Any]] = []
    if args.allowlist is not None:
        payload = json.loads(args.allowlist.read_text(encoding="utf-8"))
        entries = payload.get("unsafe_accept_allowlist")
        if not isinstance(entries, list):
            raise SeatDecisionError("allowlist file needs an unsafe_accept_allowlist array")
        allowlist = entries

    try:
        if args.target.is_file() and args.target.suffix == ".md":
            degraded = True
            if allowlist:
                raise SeatDecisionError("allowlist requires artifact JSONs (per-claim identity)")
            reports = seat_reports_from_scorecard(
                args.target.read_text(encoding="utf-8"),
                DOMAIN_BY_SLUG,
                _claims_per_fixture(args.fixtures_dir),
            )
        elif args.target.is_dir():
            degraded = False
            artifacts = _load_artifacts(args.target)
            if not artifacts:
                raise SeatDecisionError(f"no bakeoff artifact JSONs under {args.target}")
            observations = observations_from_artifacts(artifacts, DOMAIN_BY_SLUG)
            seats = sorted({o.seat for o in observations if o.arm == "tooled"})
            reports = [decide_seat(seat, observations, unsafe_accept_allowlist=allowlist) for seat in seats]
        else:
            raise SeatDecisionError(f"target is neither a directory nor a .md scorecard: {args.target}")
    except SeatDecisionError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    markdown = render_markdown(reports, source=str(args.target), degraded=degraded)
    print(markdown)
    if args.md_out:
        args.md_out.write_text(markdown, encoding="utf-8")
    if args.json_out:
        payload = {
            "source": str(args.target),
            "degraded_input": degraded,
            "thresholds": _THRESHOLDS,
            "seats": [report.as_dict() for report in reports],
        }
        args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
