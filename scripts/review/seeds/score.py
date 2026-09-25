"""Score a reviewer seat on the seeded and clean measurement lessons (#8430 R3-A).

Computed only from the findings database (attempts, ``seed_results``, ``clean_results``) and the private records
of the units (their dimension and origin). Nothing is measured here: the arithmetic is tested against
hand-computed fixtures, the numbers come from runs.

**Units and observations.** The unit is the seed (or the clean lesson). The scored observation is the seat's
**first** attempt on it (lowest ``seq``). A first attempt that failed, timed out, or was rejected by the validator
counts as *not detected* and stays in every denominator, including the evidence-validation rate; a retry is
reported (its count and outcome) and never scored as a second independent observation. A first attempt that was
accepted but is not adjudicated yet cannot be scored: the run refuses (``adjudication_pending``) unless the caller
allows a partial report, which then lists it.

**Metrics** (each with its interval, at ``interval_confidence_percent``):

* recall per dimension (detection: a finding mapped ``planted``) and blocking recall (disposition: a planted finding
  that is active or persisting BLOCKER/MAJOR): proportion of seeds, Wilson;
* recall on valid first attempts (accepted and adjudicated), a **secondary** number, never the headline;
* findings per clean lesson: findings adjudicated ``false`` over the clean lessons, Poisson exact. A
  ``genuine_additional`` finding is a defect the seat really found and is never counted false;
* share of clean lessons falsely blocked: Wilson;
* evidence validation rate: accepted first attempts over all first attempts, rejected and failed ones in the
  denominator: Wilson;
* paired comparison of two seats on the same seeds: exact McNemar on the discordant pairs.

**Sets.** ``first`` and ``confirmation`` runs verify the confirmation lock (its hash, its units, its assignments)
before anything is scored; a ``first`` report never contains a locked unit. A seat is scored only on units its
family may review (``manifest.independence_violations``): a seed planted by the seat's own family is not part of its
pool and is listed as not applicable, not counted as missed.

**Labels.** A report is threshold-eligible only when every unit in it is a real built lesson and every required
dimension has at least ``min_planted_per_dimension`` scored seeds and there are at least ``min_clean_lessons`` scored
clean lessons; anything else is titled EXPLORATORY.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import statistics
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from scripts.review import findings_db
from scripts.review.seeds import manifest as seed_manifest

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = ("audit", "reviewer-measurement")
EXPLORATORY_TITLE = "EXPLORATORY — not for choosing a threshold"

ADJUDICATION_PENDING = "adjudication_pending"
UNIT_NOT_ATTEMPTED = "unit_not_attempted"
NO_ATTEMPTS = "no_attempts"
MIXED_SEAT = "mixed_seat"
CONFIRMATION_LEAK = "confirmation_leak"
IDENTITY_MISMATCH = "seed_identity_mismatch"
EMPTY_SET = "empty_set"
SETS_WITHOUT_LOCK = ("rolling",)  # the only set that may be scored before the confirmation set is frozen


class ScoreError(Exception):
    """A set cannot be scored (or scored honestly); carries a named ``code``."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


# --- interval arithmetic ----------------------------------------------------------------


def z_value(confidence: float) -> float:
    """The two-sided normal quantile for ``confidence`` (0.95 -> 1.95996...)."""
    return statistics.NormalDist().inv_cdf(1 - (1 - confidence) / 2)


def wilson_interval(successes: int, n: int, confidence: float) -> tuple[float, float] | None:
    """Wilson score interval of a proportion; ``None`` when there are no trials.

    The ends are exactly 0 for no successes and exactly 1 for all successes, as the closed form gives.
    """
    if n <= 0:
        return None
    if not 0 <= successes <= n:
        raise ValueError(f"{successes} successes in {n} trials")
    z = z_value(confidence)
    p = successes / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    low = 0.0 if successes == 0 else max(0.0, centre - half)
    high = 1.0 if successes == n else min(1.0, centre + half)
    return low, high


def _poisson_cdf(k: int, mean: float) -> float:
    """P(X <= k) for X ~ Poisson(mean)."""
    if mean <= 0:
        return 1.0
    log_mean = math.log(mean)
    return min(1.0, sum(math.exp(-mean + i * log_mean - math.lgamma(i + 1)) for i in range(k + 1)))


def _bisect(function: Callable[[float], float], low: float, high: float) -> float:
    """The root of a monotone ``function`` on ``[low, high]`` (its sign differs at the ends)."""
    increasing = function(high) > function(low)
    for _ in range(200):
        middle = (low + high) / 2
        if (function(middle) < 0) == increasing:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def poisson_exact_interval(events: int, exposure: float, confidence: float) -> tuple[float, float] | None:
    """Exact (Garwood) interval of the rate ``events / exposure``; ``None`` when there is no exposure.

    The mean's lower end solves P(X >= events) = alpha/2 and the upper P(X <= events) = alpha/2; both are divided by
    the exposure (here: the number of clean lessons).
    """
    if exposure <= 0:
        return None
    if events < 0:
        raise ValueError("negative event count")
    tail = (1 - confidence) / 2
    upper = float(events + 10)
    while _poisson_cdf(events, upper) > tail:
        upper *= 2
    high = _bisect(lambda mean: _poisson_cdf(events, mean) - tail, float(events), upper)
    low = 0.0 if events == 0 else _bisect(lambda mean: (1 - _poisson_cdf(events - 1, mean)) - tail, 0.0, float(events))
    return low / exposure, high / exposure


def mcnemar_exact(only_a: int, only_b: int) -> float | None:
    """Two-sided exact McNemar p-value from the two discordant counts; ``None`` when there are no discordant pairs.

    Under the null each discordant pair is a fair coin: ``p = min(1, 2 * P(X <= min(only_a, only_b)))`` for
    ``X ~ Binomial(only_a + only_b, 1/2)``.
    """
    total = only_a + only_b
    if total == 0:
        return None
    tail = sum(math.comb(total, i) for i in range(min(only_a, only_b) + 1))
    return min(1.0, 2 * tail / 2**total)


def proportion(successes: int, n: int, confidence: float) -> dict[str, Any]:
    interval = wilson_interval(successes, n, confidence)
    return {
        "k": successes,
        "n": n,
        "point": successes / n if n else None,
        "low": interval[0] if interval else None,
        "high": interval[1] if interval else None,
        "method": "wilson",
        "confidence": confidence,
    }


def rate(events: int, exposure: int, confidence: float) -> dict[str, Any]:
    interval = poisson_exact_interval(events, exposure, confidence)
    return {
        "events": events,
        "lessons": exposure,
        "point": events / exposure if exposure else None,
        "low": interval[0] if interval else None,
        "high": interval[1] if interval else None,
        "method": "poisson_exact",
        "confidence": confidence,
    }


# --- observations -----------------------------------------------------------------------


@dataclass(frozen=True)
class Observation:
    """The seat's first attempt on one unit, as it counts."""

    unit_id: str
    kind: str  # "seed" or "clean"
    dimension: str | None
    source_kind: str
    review_id: str
    attempt_id: str
    outcome: str  # "accepted" | "rejected" | "failed"
    detected: bool = False  # seeds: a finding was mapped planted
    blocking: bool = False  # seeds: a planted finding is blocking
    false_findings: int = 0  # clean lessons
    falsely_blocked: bool = False  # clean lessons
    classes: dict[str, int] = field(default_factory=dict)  # adjudicated finding classes of this attempt
    retries: tuple[tuple[str, str], ...] = ()  # (attempt_id, outcome) of every later attempt by the seat

    @property
    def valid(self) -> bool:
        return self.outcome == "accepted"


@dataclass
class SeatScore:
    """One seat on one set: the per-unit observations and the report computed from them."""

    seat: str
    set_name: str
    observations: dict[str, Observation]
    report: dict[str, Any]


def _outcome(verdict: str) -> str:
    return {"APPROVE": "accepted", "REVISE": "accepted", "REJECTED": "rejected"}.get(verdict, "failed")


def _default_db_path_for(repo_root: Path | None) -> Callable[[str], Path]:
    return lambda level: findings_db.db_path(level, repo_root)


def _units_of(set_name: str, repo_root: Path | None) -> tuple[list[str], seed_manifest.ConfirmationLock | None]:
    """The units assigned to ``set_name`` after the lock checks that must come first."""
    if set_name not in seed_manifest.SETS:
        raise ScoreError(f"unknown set {set_name!r}", EMPTY_SET)
    lock = None
    try:
        lock = seed_manifest.verify_confirmation_lock(repo_root)
    except seed_manifest.MeasurementError as error:
        if not (error.code == seed_manifest.CONFIRMATION_LOCK_MISSING and set_name in SETS_WITHOUT_LOCK):
            raise
    assignments = seed_manifest.load_assignments(repo_root)
    units = sorted(unit for unit, name in assignments.items() if name == set_name)
    if set_name == "first" and lock is not None and lock.unit_ids & set(units):
        raise ScoreError(
            f"{sorted(lock.unit_ids & set(units))} are confirmation units in a first-set run", CONFIRMATION_LEAK
        )
    if set_name == "confirmation" and lock is not None and set(units) != lock.unit_ids:
        raise ScoreError("the confirmation run does not cover exactly the frozen list", CONFIRMATION_LEAK)
    if not units:
        raise ScoreError(f"no units are assigned to the {set_name} set", EMPTY_SET)
    return units, lock


def collect(
    seat: str,
    set_name: str,
    *,
    repo_root: Path | None = None,
    model: str | None = None,
    db_path_for: Callable[[str], Path] | None = None,
    allow_partial: bool | None = None,
) -> tuple[dict[str, Observation], dict[str, Any], seed_manifest.ConfirmationLock | None]:
    """The seat's first-attempt observations over a set, and what was left out (with why).

    Returns ``(observations, excluded, lock)``. ``excluded`` has ``not_applicable`` (unit -> the independence codes
    that keep this seat off it), ``not_attempted`` and ``pending`` (accepted, not adjudicated) lists, and the seat's
    ``family`` and ``models``.
    """
    partial_ok = set_name == "rolling" if allow_partial is None else allow_partial
    units, lock = _units_of(set_name, repo_root)
    path_for = db_path_for or _default_db_path_for(repo_root)
    records = {
        unit: seed_manifest.load_clean(unit, repo_root)
        if seed_manifest.is_clean_id(unit)
        else seed_manifest.load_seed(unit, repo_root)
        for unit in units
    }
    connections: dict[str, sqlite3.Connection] = {}
    try:

        def conn_for(level: str) -> sqlite3.Connection:
            if level not in connections:
                connections[level] = findings_db.connect(path_for(level))
            return connections[level]

        by_unit = {
            unit: [
                row
                for row in findings_db.measurement_attempts(conn_for(record.level), unit)
                if row["harness"] == seat and (model is None or row["reviewer_model"] == model)
            ]
            for unit, record in records.items()
        }
        families = {row["reviewer_family"] for rows in by_unit.values() for row in rows}
        models = sorted({row["reviewer_model"] for rows in by_unit.values() for row in rows})
        if not families:
            raise ScoreError(f"seat {seat!r} has no attempt on any unit of the {set_name} set", NO_ATTEMPTS)
        if len(families) > 1 or (len(models) > 1 and model is None):
            raise ScoreError(
                f"seat {seat!r} recorded attempts under models {models} and families {sorted(families)}: name one model",
                MIXED_SEAT,
            )
        family = families.pop()
        excluded: dict[str, Any] = {
            "not_applicable": {},
            "not_attempted": [],
            "pending": [],
            "family": family,
            "models": models,
        }
        observations: dict[str, Observation] = {}
        for unit, record in records.items():
            violations = _violations(record, family)
            if violations:
                if by_unit[unit]:
                    raise ScoreError(
                        f"{unit} was attempted by a family that may not review it: {violations}", violations[0]
                    )
                excluded["not_applicable"][unit] = violations
                continue
            attempts = by_unit[unit]
            if not attempts:
                excluded["not_attempted"].append(unit)
                continue
            observation = _observe(conn_for(record.level), unit, record, attempts)
            if observation is None:
                excluded["pending"].append(unit)
                continue
            observations[unit] = observation
    finally:
        for conn in connections.values():
            conn.close()
    left_out = excluded["not_attempted"] + excluded["pending"]
    if left_out and not partial_ok:
        code = ADJUDICATION_PENDING if excluded["pending"] else UNIT_NOT_ATTEMPTED
        raise ScoreError(
            f"the {set_name} set is not complete for seat {seat!r}: not attempted {excluded['not_attempted']}, "
            f"not adjudicated {excluded['pending']} (allow a partial report to score what exists)",
            code,
        )
    if not observations:
        raise ScoreError(f"no unit of the {set_name} set can be scored for seat {seat!r}", NO_ATTEMPTS)
    return observations, excluded, lock


def _violations(record: seed_manifest.Seed | seed_manifest.Clean, family: str) -> list[str]:
    if isinstance(record, seed_manifest.Clean):
        return [seed_manifest.REVIEWER_IS_WRITER] if record.writer_family == family else []
    return seed_manifest.independence_violations(record, writer_family=record.writer_family, reviewer_family=family)


def _observe(
    conn: sqlite3.Connection,
    unit: str,
    record: seed_manifest.Seed | seed_manifest.Clean,
    attempts: list[sqlite3.Row],
) -> Observation | None:
    """The first attempt as an observation; ``None`` while it is accepted but not adjudicated."""
    first, later = attempts[0], attempts[1:]
    clean = isinstance(record, seed_manifest.Clean)
    if not clean:
        _check_identity_row(conn, record)
    retries = tuple((row["attempt_id"], _outcome(row["verdict"])) for row in later)
    common: dict[str, Any] = {
        "unit_id": unit,
        "kind": "clean" if clean else "seed",
        "dimension": None if clean else record.dimension,
        "source_kind": record.source_kind,
        "review_id": first["review_id"],
        "attempt_id": first["attempt_id"],
        "outcome": _outcome(first["verdict"]),
        "retries": retries,
    }
    if common["outcome"] != "accepted":
        return Observation(**common)
    if clean:
        result = findings_db.get_clean_result(conn, first["review_id"], first["attempt_id"])
        if result is None:
            return None
        extra = {"false_findings": result["false_findings"], "falsely_blocked": bool(result["falsely_blocked"])}
    else:
        result = findings_db.get_seed_result(conn, first["review_id"], first["attempt_id"])
        if result is None:
            return None
        extra = {"detected": bool(result["planted_found"]), "blocking": bool(result["planted_blocking"])}
    classes = Counter(item["class"] for item in json.loads(result["mapping_json"]))
    return Observation(**common, **extra, classes=dict(sorted(classes.items())))


def _check_identity_row(conn: sqlite3.Connection, seed: seed_manifest.Seed) -> None:
    """The identities recorded in the database, when present, are the manifest's: a drifted seed is not scored."""
    row = findings_db.get_seed_identity(conn, seed.seed_id)
    if row is not None and {key: row[key] for key in seed.identity_row()} != seed.identity_row():
        raise ScoreError(f"{seed.seed_id}: seed_identities differs from its scoring manifest", IDENTITY_MISMATCH)


# --- the report -------------------------------------------------------------------------


def _dimension_rows(seeds: list[Observation], required: list[str], confidence: float) -> dict[str, Any]:
    names = sorted({*required, *(item.dimension for item in seeds if item.dimension)})
    rows: dict[str, Any] = {}
    for name in names:
        group = [item for item in seeds if item.dimension == name]
        valid = [item for item in group if item.valid]
        rows[name] = {
            "recall": proportion(sum(item.detected for item in group), len(group), confidence),
            "blocking_recall": proportion(sum(item.blocking for item in group), len(group), confidence),
            "recall_valid_first_attempts": proportion(sum(item.detected for item in valid), len(valid), confidence),
        }
    return rows


def compute_report(
    seat: str,
    set_name: str,
    observations: dict[str, Observation],
    excluded: dict[str, Any],
    lock: seed_manifest.ConfirmationLock | None,
    params: dict[str, Any],
    *,
    today: date | None = None,
    partial: bool = False,
) -> dict[str, Any]:
    """Every metric of a measurement report with its interval, from the observations alone."""
    confidence = params["interval_confidence_percent"] / 100
    seeds = [item for item in observations.values() if item.kind == "seed"]
    cleans = [item for item in observations.values() if item.kind == "clean"]
    everything = list(observations.values())
    _, required = seed_manifest.lesson_dimensions()
    per_dimension = _dimension_rows(seeds, required, confidence)
    valid_seeds = [item for item in seeds if item.valid]

    real_seeds = Counter(item.dimension for item in seeds if item.source_kind == "real_built")
    real_cleans = sum(1 for item in cleans if item.source_kind == "real_built")
    not_real = sorted(item.unit_id for item in everything if item.source_kind != "real_built")
    reasons: list[str] = []
    for name in required:
        if real_seeds[name] < params["min_planted_per_dimension"]:
            reasons.append(
                f"{name}: {real_seeds[name]} scored planted defects on real built lessons, "
                f"{params['min_planted_per_dimension']} needed"
            )
    if real_cleans < params["min_clean_lessons"]:
        reasons.append(
            f"{real_cleans} scored clean lessons on real built lessons, {params['min_clean_lessons']} needed"
        )
    if not_real:
        reasons.append(f"{len(not_real)} units are not real built lessons (canary or fixture): {not_real}")
    if partial:
        reasons.append(
            f"the run is partial (not attempted {len(excluded['not_attempted'])}, not adjudicated "
            f"{len(excluded['pending'])})"
        )

    retries = {item.unit_id: list(item.retries) for item in everything if item.retries}
    return {
        "seat": seat,
        "models": excluded["models"],
        "family": excluded["family"],
        "set": set_name,
        "date": (today or datetime.now(UTC).date()).isoformat(),
        "confirmation_lock_sha256": lock.sha256 if lock else None,
        "admission_threshold": params["admission_threshold"],
        "threshold_eligible": not reasons,
        "exploratory_reasons": reasons,
        "eligibility": {
            "min_planted_per_dimension": params["min_planted_per_dimension"],
            "min_clean_lessons": params["min_clean_lessons"],
            "real_built_seeds_by_dimension": {name: real_seeds[name] for name in required},
            "real_built_clean_lessons": real_cleans,
        },
        "confidence": confidence,
        "units": {"seeds": len(seeds), "clean": len(cleans)},
        "recall_by_dimension": {name: row["recall"] for name, row in per_dimension.items()},
        "blocking_recall_by_dimension": {name: row["blocking_recall"] for name, row in per_dimension.items()},
        "recall_valid_first_attempts_by_dimension": {
            name: row["recall_valid_first_attempts"] for name, row in per_dimension.items()
        },
        "recall_pooled": proportion(sum(item.detected for item in seeds), len(seeds), confidence),
        "blocking_recall_pooled": proportion(sum(item.blocking for item in seeds), len(seeds), confidence),
        "recall_valid_first_attempts_pooled": proportion(
            sum(item.detected for item in valid_seeds), len(valid_seeds), confidence
        ),
        "false_findings_per_clean_lesson": rate(sum(item.false_findings for item in cleans), len(cleans), confidence),
        "clean_lessons_falsely_blocked": proportion(
            sum(item.falsely_blocked for item in cleans), len(cleans), confidence
        ),
        "evidence_validation": proportion(sum(item.valid for item in everything), len(everything), confidence),
        "first_attempt_outcomes": dict(sorted(Counter(item.outcome for item in everything).items())),
        "retries": {
            "units": len(retries),
            "attempts": sum(len(value) for value in retries.values()),
            "outcomes": dict(sorted(Counter(outcome for value in retries.values() for _, outcome in value).items())),
            "by_unit": dict(sorted(retries.items())),
            "note": "reported only: a retry is never scored as a second independent observation",
        },
        "adjudicated_classes": {
            "seeds": dict(sorted(sum((Counter(item.classes) for item in seeds), Counter()).items())),
            "clean": dict(sorted(sum((Counter(item.classes) for item in cleans), Counter()).items())),
        },
        "excluded": {
            "not_applicable": dict(sorted(excluded["not_applicable"].items())),
            "not_attempted": sorted(excluded["not_attempted"]),
            "pending_adjudication": sorted(excluded["pending"]),
        },
    }


def score_seat(
    seat: str,
    set_name: str,
    *,
    repo_root: Path | None = None,
    model: str | None = None,
    db_path_for: Callable[[str], Path] | None = None,
    allow_partial: bool | None = None,
    params: dict[str, Any] | None = None,
    today: date | None = None,
) -> SeatScore:
    """Score ``seat`` on ``set_name`` (``first``, ``confirmation`` or ``rolling``); ScoreError when it cannot be done honestly.

    ``first`` and ``confirmation`` verify the confirmation lock before anything is read from the database.
    ``model`` narrows a seat that has recorded attempts under more than one model.
    """
    parameters = params if params is not None else findings_db.load_parameters()
    partial_ok = set_name == "rolling" if allow_partial is None else allow_partial
    observations, excluded, lock = collect(
        seat, set_name, repo_root=repo_root, model=model, db_path_for=db_path_for, allow_partial=allow_partial
    )
    partial = bool(excluded["not_attempted"] or excluded["pending"])
    report = compute_report(
        seat, set_name, observations, excluded, lock, parameters, today=today, partial=partial and partial_ok
    )
    return SeatScore(seat, set_name, observations, report)


def paired_comparison(first: SeatScore, second: SeatScore) -> dict[str, Any]:
    """Two seats on the same seeds: exact McNemar on the discordant pairs (detection, first attempts).

    Only seeds both seats were scored on are paired; a seed a seat could not review (its own family planted it) or
    has not attempted is not a pair. The two seats' independent intervals are not a substitute for this.
    """
    seeds_a = {unit: item for unit, item in first.observations.items() if item.kind == "seed"}
    seeds_b = {unit: item for unit, item in second.observations.items() if item.kind == "seed"}
    shared = sorted(seeds_a.keys() & seeds_b.keys())
    only_a = [unit for unit in shared if seeds_a[unit].detected and not seeds_b[unit].detected]
    only_b = [unit for unit in shared if seeds_b[unit].detected and not seeds_a[unit].detected]
    both = sum(1 for unit in shared if seeds_a[unit].detected and seeds_b[unit].detected)
    return {
        "seat_a": first.seat,
        "seat_b": second.seat,
        "test": "mcnemar_exact",
        "paired_seeds": len(shared),
        "both_detected": both,
        "neither_detected": len(shared) - both - len(only_a) - len(only_b),
        "only_a_detected": len(only_a),
        "only_b_detected": len(only_b),
        "p_value": mcnemar_exact(len(only_a), len(only_b)),
        "discordant_seeds": {"only_a": only_a, "only_b": only_b},
    }


# --- rendering --------------------------------------------------------------------------

KNOWN_LIMITS = (
    "Recall is measured against the defects we thought of.",
    'A "clean" lesson is not known to be clean: its label comes from adjudication, and a finding that is a real defect is '
    "`genuine_additional`, not false.",
    "A fixed set is learned over time and must be regenerated.",
    "Agreement between two seats cannot expose an error both share.",
    "Blocking recall assumes every planted defect is one the severity rubric blocks on.",
    "Failed and invalid first attempts count as not detected in recall and add no false findings on clean lessons: "
    "the second is in the seat's favour, so read it beside the evidence validation rate.",
)
SIZE_NOTE = (
    "Size: about 21 planted defects per dimension separate 80 % recall from 55 % (one-sample, one-sided α = 0.05, "
    "power 0.8; 32.6 for 80 % against 60 %); below about ten per dimension the numbers mean nothing. Comparing two seats "
    "on the same seeds is a paired analysis (exact McNemar), not two independent groups."
)


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{100 * value:.1f} %"


def _cell(item: dict[str, Any]) -> str:
    if item["n"] == 0:
        return "no units"
    return f"{item['k']}/{item['n']} = {_pct(item['point'])} [{_pct(item['low'])}, {_pct(item['high'])}]"


def render_report(score: SeatScore, paired: dict[str, Any] | None = None) -> str:
    """The REPORT.md text; titled EXPLORATORY unless the report is threshold-eligible."""
    report = score.report
    label = "Reviewer measurement" if report["threshold_eligible"] else f"{EXPLORATORY_TITLE}: reviewer measurement"
    level = f"{round(100 * report['confidence'])} %"
    lines = [
        f"# {label} — {report['seat']}, {report['set']} set, {report['date']}",
        "",
    ]
    if report["threshold_eligible"]:
        lines.append(
            "Threshold-eligible: every required dimension and the clean set reach the contract's size on real built "
            "lessons."
        )
    else:
        lines.append(f"**{EXPLORATORY_TITLE}.** " + " ".join(f"{reason}." for reason in report["exploratory_reasons"]))
    lines += [
        "",
        f"Seat `{report['seat']}` (family {report['family']}, models {', '.join(report['models'])}). "
        f"Units: {report['units']['seeds']} seeded, {report['units']['clean']} clean. Intervals at {level}: "
        "Wilson for proportions, Poisson exact for the false-finding rate, unit = seed (or clean lesson), the scored "
        "observation is the seat's first attempt.",
    ]
    if report["confirmation_lock_sha256"]:
        lines.append(f"Confirmation lock sha256: `{report['confirmation_lock_sha256']}`.")
    threshold = report["admission_threshold"]
    lines.append(f"Admission threshold: {'not set (the operator sets it)' if threshold is None else threshold}.")
    lines += ["", "## Recall by dimension (detection) and blocking recall (disposition)", ""]
    lines += [
        "| dimension | recall | blocking recall | recall on valid first attempts (secondary) |",
        "|---|---|---|---|",
    ]
    for name, row in report["recall_by_dimension"].items():
        lines.append(
            f"| {name} | {_cell(row)} | {_cell(report['blocking_recall_by_dimension'][name])} | "
            f"{_cell(report['recall_valid_first_attempts_by_dimension'][name])} |"
        )
    lines.append(
        f"| pooled | {_cell(report['recall_pooled'])} | {_cell(report['blocking_recall_pooled'])} | "
        f"{_cell(report['recall_valid_first_attempts_pooled'])} |"
    )
    fp, blocked, validation = (
        report["false_findings_per_clean_lesson"],
        report["clean_lessons_falsely_blocked"],
        report["evidence_validation"],
    )
    fp_text = (
        "no units"
        if fp["lessons"] == 0
        else (
            f"{fp['events']} false findings over {fp['lessons']} clean lessons = {fp['point']:.3f} per lesson "
            f"[{fp['low']:.3f}, {fp['high']:.3f}]"
        )
    )
    lines += [
        "",
        "## Clean lessons",
        "",
        f"- False findings per clean lesson: {fp_text}.",
        f"- Clean lessons falsely blocked: {_cell(blocked)}.",
        f"- Findings adjudicated on clean lessons: {report['adjudicated_classes']['clean'] or 'none'} "
        "(`genuine_additional` is a real defect, never counted false).",
        "",
        "## Evidence validation",
        "",
        f"- Evidence validation rate (rejected and failed first attempts in the denominator): {_cell(validation)}.",
        f"- First attempts: {report['first_attempt_outcomes']}.",
        "",
        "## Retries (reported, never scored)",
        "",
        f"- {report['retries']['attempts']} retries on {report['retries']['units']} units; outcomes "
        f"{report['retries']['outcomes'] or 'none'}.",
    ]
    excluded = report["excluded"]
    if excluded["not_applicable"] or excluded["not_attempted"] or excluded["pending_adjudication"]:
        lines += ["", "## Left out", ""]
        if excluded["not_applicable"]:
            lines.append(
                "- Not applicable to this seat (its family may not review them): "
                + ", ".join(f"{unit} ({', '.join(codes)})" for unit, codes in excluded["not_applicable"].items())
            )
        if excluded["not_attempted"]:
            lines.append(f"- Not attempted: {', '.join(excluded['not_attempted'])}")
        if excluded["pending_adjudication"]:
            lines.append(f"- Accepted, not adjudicated yet: {', '.join(excluded['pending_adjudication'])}")
    if paired is not None:
        p_value = "no discordant pairs" if paired["p_value"] is None else f"p = {paired['p_value']:.4f}"
        lines += [
            "",
            f"## Paired comparison: {paired['seat_a']} against {paired['seat_b']}",
            "",
            f"- {paired['paired_seeds']} seeds both seats were scored on: both detected {paired['both_detected']}, "
            f"only {paired['seat_a']} {paired['only_a_detected']}, only {paired['seat_b']} {paired['only_b_detected']}, "
            f"neither {paired['neither_detected']}.",
            f"- Exact McNemar on the discordant pairs: {p_value}.",
        ]
    lines += ["", "## Reading the size", "", SIZE_NOTE, "", "## Known limits", ""]
    lines += [f"- {item}" for item in KNOWN_LIMITS]
    return "\n".join(lines) + "\n"


def report_path(seat: str, day: date, repo_root: Path | None = None) -> Path:
    """``audit/reviewer-measurement/<date>-<seat>/REPORT.md``: where the runner writes the report."""
    base = Path(repo_root) if repo_root is not None else REPO_ROOT
    return base.joinpath(*REPORT_DIR, f"{day.isoformat()}-{seat}", "REPORT.md")


# --- CLI --------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.review.seeds.score",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Score one reviewer seat on a measurement set from the findings database and the adjudications, and print\n"
            "the report (#8430 R3). first and confirmation runs verify the confirmation lock first. The report is titled\n"
            "EXPLORATORY unless it reaches the contract's size on real built lessons.\n"
            "Do NOT use it to choose a threshold from an exploratory report."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.review.seeds.score --seat codex --set first\n"
            "  .venv/bin/python -m scripts.review.seeds.score --seat agy --set rolling --json\n"
            "\nOutputs: the markdown report (or JSON) on stdout. Exit codes: 0 scored; 2 refused (error and code on stderr)."
        ),
    )
    parser.add_argument("--seat", required=True, help="the reviewer seat's harness (attempts.harness)")
    parser.add_argument("--set", dest="set_name", required=True, choices=seed_manifest.SETS)
    parser.add_argument("--model", default=None, help="narrow the seat to one model")
    parser.add_argument("--partial", action="store_true", help="score what exists and list the rest")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        score = score_seat(
            args.seat,
            args.set_name,
            repo_root=args.repo_root,
            model=args.model,
            allow_partial=True if args.partial else None,
        )
    except (ScoreError, seed_manifest.MeasurementError, findings_db.FindingsDbError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(
        json.dumps(score.report, indent=2, sort_keys=True, ensure_ascii=False) if args.json else render_report(score),
        end="",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
