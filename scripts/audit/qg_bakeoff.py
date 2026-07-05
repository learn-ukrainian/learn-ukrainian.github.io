#!/usr/bin/env python3
"""Offline tier-bakeoff harness for grounded QG fact-check reviewers.

This harness is intentionally separate from live reviewer routing. It builds
local per-pin opencode routes cloned from ``FRONTIER_OPENCODE_ROUTE`` and never
registers them in ``ROUTES`` or asks the live ``assert_route_allowed`` policy to
approve them. That keeps the production DeepSeek/Hermes ban intact while
allowing a small, explicit offline experiment under ``QG_BAKEOFF=1``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import llm_reviewer, llm_reviewer_dispatch, qg_factcheck_scoring, qg_schema

FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "qg_bakeoff"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "audit"
RUN_SCHEMA_VERSION = "qg_bakeoff_run.v1"
SCORECARD_NAME = "SCORECARD.md"
ANCHOR_SLUG = "vesnianky"
MISSING_CLAIM_PENALTY = -10
BAKEOFF_LEVEL = "folk"
BAKEOFF_POLICY_FAMILY = "seminar"
# Arms of the bakeoff. TOOLED = the shipped grounded+gated reviewer path;
# BARE = the tool-free control (model judges from its own knowledge, no gates)
# so tooled − bare per model quantifies the harness lift (#2156 step 3).
TOOLED_ARM = "tooled"
BARE_ARM = "bare"
BOTH_ARM = "both"
_ARM_CHOICES = (TOOLED_ARM, BARE_ARM, BOTH_ARM)
# Verbatim reuse markers: the bare prompt slices the LIVE verdict taxonomy out of
# the reviewer template so the fact-check verdict set can never fork from tooled.
_TAXONOMY_START = "Each fact check MUST use exactly one verdict from this taxonomy:"
_TAXONOMY_END = "Few-shot anchors:"
_LEADING_CLAIM_FILLER_RE = re.compile(r"^(?:або|чи)\s+", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class CandidateModel:
    label: str
    pin: str
    unresolved: bool = False


# TODO(#2156): resolve exact OpenRouter pins at run time via ``--models`` after
# checking the currently served opencode/OpenRouter model list. Do not guess.
DEFAULT_CANDIDATE_MODELS: tuple[CandidateModel, ...] = (
    CandidateModel("gemma-4-31b", "openrouter/google/gemma-4-31b-it"),
    CandidateModel("deepseek-v4", "TODO_OPENROUTER_DEEPSEEK_V4_PIN", unresolved=True),
    CandidateModel("claude-frontier", "TODO_OPENROUTER_ANTHROPIC_FRONTIER_PIN", unresolved=True),
    CandidateModel("gpt-frontier", "TODO_OPENROUTER_OPENAI_FRONTIER_PIN", unresolved=True),
    CandidateModel("gemini-frontier", "TODO_OPENROUTER_GOOGLE_GEMINI_FRONTIER_PIN", unresolved=True),
)


@dataclass(frozen=True, slots=True)
class FixtureClaim:
    claim_id: str
    claim: str
    is_true: bool
    fabrication_class: str | None = None
    distractor_evidence: str | None = None


@dataclass(frozen=True, slots=True)
class BakeoffFixture:
    slug: str
    title: str
    passage_md: str
    claims: tuple[FixtureClaim, ...]


@dataclass(frozen=True, slots=True)
class BakeoffRun:
    artifact_path: Path
    artifact: dict[str, Any]
    skipped: bool = False


class BakeoffConfigError(ValueError):
    """Configuration or fixture validation error."""


class BakeoffCellError(ValueError):
    """Per-cell failure carrying the raw response head for diagnosis."""

    def __init__(self, message: str, *, response_head: str | None = None) -> None:
        super().__init__(message)
        self.response_head = response_head


ProviderRunner = Callable[
    [llm_reviewer_dispatch.ReviewerRoute, str, str],
    llm_reviewer_dispatch.DispatchResult | str,
]

# The bare control arm's runner is the SAME shape as ProviderRunner. It exists as
# a named seam (#2156 step 5): subscription-lane bare runners (claude / gpt /
# gemini NATIVE) plug in here — they are OUT OF SCOPE for this harness because the
# handoff forbids routing subscription families over OpenRouter. A native bare
# transport can be injected as ``bare_runner`` without touching scoring, artifacts,
# or the scorecard; the default below is the OpenRouter-legitimate opencode lane
# (gemma + deepseek), and the routing guard on main still refuses other families.
BareRunner = ProviderRunner


def _lenient_first_json_object(response_text: str) -> Mapping[str, Any] | None:
    """Parse the FIRST JSON object from a response with trailing garbage.

    Measured live (deepseek-v4-flash): a valid payload followed by extra text
    ("Extra data: char 7498"). JSON hygiene is a contract defect worth
    counting, not a reason to void the fact-check measurement. Returns None
    when no leading object parses.
    """
    text = response_text.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1]
    elif text.startswith("```"):
        text = text.split("```", 1)[1]
    text = text.lstrip()
    try:
        payload, _end = json.JSONDecoder().raw_decode(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, Mapping) else None


def require_offline_opt_in() -> None:
    """Refuse CI and require explicit local experiment opt-in."""
    if os.environ.get("CI"):
        raise BakeoffConfigError("qg_bakeoff refuses to run when CI is set")
    if os.environ.get("QG_BAKEOFF") != "1":
        raise BakeoffConfigError("qg_bakeoff requires QG_BAKEOFF=1")


def load_fixture(path: Path) -> BakeoffFixture:
    """Load and validate one bakeoff fixture JSON file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BakeoffConfigError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise BakeoffConfigError(f"{path}: fixture must be a JSON object")

    slug = _required_str(raw, "slug", path)
    title = _required_str(raw, "title", path)
    passage_md = _required_str(raw, "passage_md", path)
    claims_raw = raw.get("claims")
    if not isinstance(claims_raw, list) or not claims_raw:
        raise BakeoffConfigError(f"{path}: claims must be a non-empty list")

    seen: set[str] = set()
    claims: list[FixtureClaim] = []
    for index, item in enumerate(claims_raw, start=1):
        if not isinstance(item, Mapping):
            raise BakeoffConfigError(f"{path}: claim #{index} must be an object")
        claim_id = _required_str(item, "claim_id", path)
        if claim_id in seen:
            raise BakeoffConfigError(f"{path}: duplicate claim_id {claim_id!r}")
        seen.add(claim_id)
        claim = _required_str(item, "claim", path)
        is_true = item.get("is_true")
        if not isinstance(is_true, bool):
            raise BakeoffConfigError(f"{path}: {claim_id}: is_true must be a boolean")
        fabrication_class = item.get("fabrication_class")
        if fabrication_class not in {"U", "M", None}:
            raise BakeoffConfigError(f"{path}: {claim_id}: fabrication_class must be U, M, or null")
        distractor = item.get("distractor_evidence")
        if distractor is not None and not isinstance(distractor, str):
            raise BakeoffConfigError(f"{path}: {claim_id}: distractor_evidence must be a string or null")
        if is_true and fabrication_class is not None:
            raise BakeoffConfigError(f"{path}: {claim_id}: true claims must not set fabrication_class")
        if not is_true and fabrication_class is None:
            raise BakeoffConfigError(f"{path}: {claim_id}: false claims require fabrication_class")
        if fabrication_class == "M" and not (isinstance(distractor, str) and distractor.strip()):
            raise BakeoffConfigError(f"{path}: {claim_id}: class-M claims require distractor_evidence")
        if _normalize_claim_loose(claim) not in _normalize_claim_loose(passage_md):
            # Load-bearing (first scored matrix, 2026-07-05): models fact-check
            # by quoting PASSAGE spans; paraphrased fixture claims can never
            # match and score as "missing". Claims MUST be literal sub-spans.
            raise BakeoffConfigError(
                f"{path}: {claim_id}: claim text must be a literal sub-span of passage_md "
                f"(loose-normalized) — paraphrases break claim matching"
            )
        claims.append(
            FixtureClaim(
                claim_id=claim_id,
                claim=claim,
                is_true=is_true,
                fabrication_class=fabrication_class,
                distractor_evidence=distractor,
            )
        )
    return BakeoffFixture(slug=slug, title=title, passage_md=passage_md, claims=tuple(claims))


def load_fixtures(fixtures_dir: Path = FIXTURE_DIR, slugs: Sequence[str] | None = None) -> list[BakeoffFixture]:
    """Load requested fixtures, or all fixture JSONs in stable slug order."""
    paths = [fixtures_dir / f"{slug}.json" for slug in slugs] if slugs else sorted(fixtures_dir.glob("*.json"))
    fixtures = [load_fixture(path) for path in paths]
    if not fixtures:
        raise BakeoffConfigError(f"no bakeoff fixtures found in {fixtures_dir}")
    return fixtures


def bakeoff_route_for_model(pin: str) -> llm_reviewer_dispatch.ReviewerRoute:
    """Return a local unregistered opencode experiment route for one model pin."""
    family = llm_reviewer_dispatch.normalize_family(pin) or llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE.reviewer_family
    return replace(
        llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE,
        route_name=f"bakeoff_{pin_slug(pin)}",
        bridge_command=("ask-opencode", "--model", pin),
        reviewer_model_id=pin,
        reviewer_family=family,
    )


def invoke_bakeoff_route(
    route: llm_reviewer_dispatch.ReviewerRoute,
    prompt: str,
    task_id: str,
) -> llm_reviewer_dispatch.DispatchResult:
    """Invoke an experiment route over the same opencode transport.

    ``invoke_bridge_route`` is live-policy-owned and only accepts registered
    route names, so bakeoff routes use its opencode backend directly.
    """
    del task_id
    return llm_reviewer_dispatch._invoke_opencode_reviewer(
        prompt,
        route,
        default_timeout_s=1800,
        require_mcp=True,
    )


def _reviewer_verdict_taxonomy() -> str:
    """Slice the fact-check verdict taxonomy VERBATIM from the live template.

    The bare arm must score identically to the tooled reviewer, so the verdict
    set cannot fork. Rather than re-typing the five verdicts here (a fork waiting
    to drift), read them out of the SAME ``reviewer_prompt.md`` the tooled path
    uses. If the template ever loses the taxonomy markers this fails loudly —
    that is the intended signal to re-sync, not to silently diverge.
    """
    template = llm_reviewer.load_reviewer_prompt_template()
    start = template.find(_TAXONOMY_START)
    end = template.find(_TAXONOMY_END, start)
    if start == -1 or end == -1:
        raise BakeoffConfigError(
            "reviewer prompt template is missing the fact-check verdict taxonomy "
            "markers; the bare arm must reuse the live taxonomy verbatim (do not fork)"
        )
    return template[start:end].strip()


_BARE_PREAMBLE = (
    "You are an expert Ukrainian linguist and fact-checker running a CONTROL review "
    "with NO tools and NO sources. Judge every factual claim in the passage below "
    "using ONLY your own parametric knowledge — you cannot search, retrieve, or "
    "ground anything."
)

_BARE_INSTRUCTIONS = (
    "### How to answer (bare / tool-free control)\n"
    "\n"
    "* Enumerate EVERY factual claim in the passage. Each `claim` MUST be an exact, "
    "literal substring copied from the passage (a verbatim span) — never a paraphrase.\n"
    "* Judge each claim from your own knowledge alone. You have NO tools, NO source "
    "search, and NO grounding. Do not invent citations or `grounding` objects; if you "
    "emit any, they are ignored by bare scoring.\n"
    "* Because you cannot consult sources, when you cannot verify a claim from your own "
    "knowledge use `UNVERIFIED_INSUFFICIENT_SEARCH` (\"cannot verify without sources\") "
    "rather than guessing `CONFIRMED`.\n"
    "* Output ONLY a single JSON object — no markdown fence, no prose before or after — "
    "of the shape:\n"
    "\n"
    '{"fact_checks": [{"claim": "<verbatim span from the passage>", '
    '"verdict": "<one taxonomy verdict>"}]}'
)


def build_bare_factcheck_prompt(title: str, passage_md: str) -> str:
    """Assemble the tool-free control prompt for one passage.

    Same output contract as the tooled reviewer (a top-level ``fact_checks`` list of
    ``{claim, verdict}`` using the reused taxonomy) so ``score_payload`` treats bare
    and tooled identically — but with NO tool instructions and NO grounding mandate.
    """
    taxonomy = _reviewer_verdict_taxonomy()
    return (
        f"{_BARE_PREAMBLE}\n\n"
        f"{taxonomy}\n\n"
        f"{_BARE_INSTRUCTIONS}\n\n"
        f"## Passage: {title}\n"
        f"{passage_md}\n"
    )


def invoke_bakeoff_route_bare(
    route: llm_reviewer_dispatch.ReviewerRoute,
    prompt: str,
    task_id: str,
) -> llm_reviewer_dispatch.DispatchResult:
    """Bare control invocation over the SAME opencode transport, tools NOT required.

    Mirrors ``invoke_bakeoff_route`` but passes ``require_mcp=False``: a bare run
    judges from model knowledge with no sources, so the grounded-MCP precondition
    does not apply and there is no tool telemetry to gate on. Legitimate OpenRouter
    lane only (gemma + deepseek); the routing guard on main still refuses
    subscription families — that is correct and must not be overridden.
    """
    del task_id
    return llm_reviewer_dispatch._invoke_opencode_reviewer(
        prompt,
        route,
        default_timeout_s=1800,
        require_mcp=False,
    )


def _validate_bare_fact_checks(fact_checks: Any) -> None:
    """Validate ONLY the fact_checks shape — claim + verdict, NO grounding.

    Reuses the live contract constants (``FACT_CHECK_VERDICTS`` /
    ``MAX_REVIEWER_FACT_CHECKS``) so the verdict set and cap never fork, but drops
    the tooled grounding requirement: a bare model has no tools, so a `CONFIRMED`
    with no grounding is a legitimate bare judgment, not a schema defect.
    """
    if not isinstance(fact_checks, list):
        raise ValueError("reviewer payload fact_checks must be a list")
    if len(fact_checks) > qg_schema.MAX_REVIEWER_FACT_CHECKS:
        raise ValueError(
            f"reviewer payload fact_checks exceeds cap: {len(fact_checks)} > "
            f"{qg_schema.MAX_REVIEWER_FACT_CHECKS}"
        )
    for fact_check in fact_checks:
        if not isinstance(fact_check, Mapping):
            raise ValueError("reviewer payload fact_checks entries must be mappings")
        claim = fact_check.get("claim")
        if not isinstance(claim, str) or not claim.strip():
            raise ValueError("fact_check.claim must be a non-empty string")
        verdict = fact_check.get("verdict")
        if not isinstance(verdict, str) or verdict not in qg_schema.FACT_CHECK_VERDICTS:
            raise ValueError(f"unsupported fact_check.verdict: {verdict!r}")


def _validate_bare_payload_shape(payload: Mapping[str, Any]) -> None:
    """Validate a bare payload: findings/evidence_gaps via the live validator,
    fact_checks via the grounding-free bare checker.

    ``findings``/``evidence_gaps`` go through ``llm_reviewer.validate_reviewer_payload``
    with ``fact_checks`` emptied, so the tooled fact-check grounding requirement never
    fires on a tool-free payload; the real fact_checks are then validated for shape only.
    """
    envelope = {
        "findings": payload.get("findings", []),
        "fact_checks": [],
        "evidence_gaps": payload.get("evidence_gaps", []),
    }
    llm_reviewer.validate_reviewer_payload(envelope, BAKEOFF_POLICY_FAMILY)
    _validate_bare_fact_checks(payload.get("fact_checks", []))


def _parse_bare_payload(response_text: str) -> tuple[dict[str, Any], bool, bool]:
    """Parse + validate a bare response. NO gates — bare has no tool telemetry.

    Returns ``(payload, response_parse_lenient, findings_schema_invalid)``. Uses the
    same lenient-first-object machinery as tooled and mirrors the tooled orthogonal
    split: non-conforming ``findings`` are stripped and flagged (they are irrelevant
    to the fact-check measurement), while invalid ``fact_checks`` are a real error cell.
    """
    response_parse_lenient = False
    try:
        payload = dict(llm_reviewer_dispatch._json_payload_from_response(response_text))
    except ValueError as exc:
        lenient = _lenient_first_json_object(response_text)
        if lenient is None:
            raise BakeoffCellError(str(exc), response_head=response_text[:2000]) from exc
        payload = dict(lenient)
        response_parse_lenient = True

    findings_schema_invalid = False
    try:
        _validate_bare_payload_shape(payload)
    except ValueError:
        stripped = dict(payload)
        stripped["findings"] = []
        try:
            _validate_bare_payload_shape(stripped)
        except ValueError as exc2:
            # fact_checks / evidence_gaps themselves are invalid → real error cell.
            raise BakeoffCellError(str(exc2), response_head=response_text[:2000]) from exc2
        findings_schema_invalid = True
        payload = stripped
    # Strip every fact_checks row to the two bare-legitimate fields (codex
    # review, PR #4500 finding 3): score_payload honors gate-produced fields
    # like admissibility_downgraded/original_verdict (_judgment_verdict), so a
    # bare model could self-emit them and split the judgment/live columns. No
    # bare gate produced them — they are untrusted input, not measurements.
    payload["fact_checks"] = [
        {"claim": row["claim"], "verdict": row["verdict"]}
        for row in payload.get("fact_checks", [])
    ]
    return payload, response_parse_lenient, findings_schema_invalid


def run_matrix(
    fixtures: Sequence[BakeoffFixture],
    model_pins: Sequence[str],
    *,
    output_dir: Path,
    runner: ProviderRunner = invoke_bakeoff_route,
    bare_runner: BareRunner = invoke_bakeoff_route_bare,
    arm: str = TOOLED_ARM,
    force: bool = False,
    retry_failures: bool = False,
) -> list[BakeoffRun]:
    """Run or resume every model x fixture pair for the requested arm(s).

    ``arm`` selects ``tooled`` (default — existing behavior), ``bare`` (the
    tool-free control), or ``both``. Each arm writes its own artifact per cell, so
    resume/force/retry apply independently. The scorecard is rebuilt from EVERY
    artifact on disk (not just this run's arm) so a ``bare`` run after a ``tooled``
    run shows both side by side with the harness-lift column.

    Guarded on EVERY entry path (cursor review of #4458, blocker): a direct
    programmatic call with the default live runner must not bypass the
    CI-refusal / ``QG_BAKEOFF=1`` opt-in that ``main()`` enforces.
    """
    require_offline_opt_in()
    if arm not in _ARM_CHOICES:
        raise BakeoffConfigError(f"arm must be one of {list(_ARM_CHOICES)}; got {arm!r}")
    # Preflight EVERY pin against the standing routing orders before any cell
    # runs (codex review, PR #4500 finding 2): a subscription-family or qwen
    # pin must fail the whole matrix at config time, not burn N-1 cells first.
    # Defense-in-depth: _invoke_opencode_reviewer re-asserts at the transport,
    # covering injected runners and non-matrix callers.
    from scripts.ai_agent_bridge.routing_guard import assert_model_routing_allowed

    for pin in model_pins:
        assert_model_routing_allowed(pin, context="qg_bakeoff matrix pin")
    output_dir.mkdir(parents=True, exist_ok=True)
    run_tooled = arm in (TOOLED_ARM, BOTH_ARM)
    run_bare = arm in (BARE_ARM, BOTH_ARM)
    runs: list[BakeoffRun] = []
    for pin in model_pins:
        route = bakeoff_route_for_model(pin)
        for fixture in fixtures:
            if run_tooled:
                runs.append(
                    run_one(
                        route,
                        fixture,
                        output_dir=output_dir,
                        runner=runner,
                        force=force,
                        retry_failures=retry_failures,
                    )
                )
            if run_bare:
                runs.append(
                    run_one_bare(
                        route,
                        fixture,
                        output_dir=output_dir,
                        runner=bare_runner,
                        force=force,
                        retry_failures=retry_failures,
                    )
                )
    write_scorecard(output_dir / SCORECARD_NAME, _load_all_artifacts(output_dir))
    return runs


def _load_all_artifacts(output_dir: Path) -> list[dict[str, Any]]:
    """Load every bakeoff artifact JSON in ``output_dir`` (both arms), stable order."""
    artifacts: list[dict[str, Any]] = []
    for path in sorted(output_dir.glob("*.json")):
        try:
            artifacts.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return artifacts


def _fixture_block(fixture: BakeoffFixture) -> dict[str, Any]:
    return {"slug": fixture.slug, "title": fixture.title, "claim_count": len(fixture.claims)}


def _model_block(route: llm_reviewer_dispatch.ReviewerRoute) -> dict[str, Any]:
    return {
        "pin": route.reviewer_model_id,
        "pin_slug": pin_slug(route.reviewer_model_id),
        "family": route.reviewer_family,
        "route_name": route.route_name,
        "bridge_command": list(route.bridge_command),
    }


def _error_artifact(
    route: llm_reviewer_dispatch.ReviewerRoute,
    fixture: BakeoffFixture,
    exc: Exception,
    wall_seconds: float,
    *,
    arm: str,
) -> dict[str, Any]:
    """Build a MEASURED error-cell artifact (score = every fixture claim missing).

    A model that cannot produce a valid payload (or a provider that errors out) is a
    per-cell outcome, never a matrix crash. Shared by both arms so the error schema
    stays identical apart from ``arm``.
    """
    return {
        "schema_version": RUN_SCHEMA_VERSION,
        "arm": arm,
        "created_at": _now_z(),
        "fixture": _fixture_block(fixture),
        "model": _model_block(route),
        "status": "error",
        "error": {
            "class": type(exc).__name__,
            "message": str(exc)[:2000],
            "response_head": getattr(exc, "response_head", None),
        },
        "workflow_verdict": "ERROR",
        "attempt_count": None,
        "dispatch": {},
        "gate_outcomes": {},
        "payload": {},
        "score": score_payload({"fact_checks": []}, fixture),
        "tool_call_count": 0,
        "wall_seconds": wall_seconds,
    }


def run_one(
    route: llm_reviewer_dispatch.ReviewerRoute,
    fixture: BakeoffFixture,
    *,
    output_dir: Path,
    runner: ProviderRunner = invoke_bakeoff_route,
    force: bool = False,
    retry_failures: bool = False,
) -> BakeoffRun:
    """Run or resume one model x passage TOOLED bakeoff artifact.

    Belt-and-suspenders (cursor re-review nit): the LIVE default runner is
    guarded here too; injected runners are offline by construction and stay
    guard-free so scripted tests need no env setup.
    """
    if runner is invoke_bakeoff_route:
        require_offline_opt_in()
    artifact_path = output_dir / f"{pin_slug(route.reviewer_model_id)}__{fixture.slug}.json"
    if artifact_path.exists() and not force:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        # retry_failures is a RESUME MODIFIER: missing cells always run (plain
        # resume behavior), completed cells always skip, and error cells re-run
        # only under the flag (codex review of #4463 pinned these semantics).
        if not (retry_failures and artifact.get("status") == "error"):
            return BakeoffRun(artifact_path=artifact_path, artifact=artifact, skipped=True)

    # ``folk`` is the track level; it maps to the seminar policy family in
    # content_surface_gates. There is no literal ``seminar`` level.
    prompt = llm_reviewer.build_reviewer_prompt(BAKEOFF_LEVEL, f"bakeoff-{fixture.slug}", fixture.passage_md)
    task_id = f"qg-bakeoff-{pin_slug(route.reviewer_model_id)}-{fixture.slug}"
    started = time.monotonic()
    try:
        gate_result = _invoke_and_gate(route, prompt, task_id, runner)
    except (ValueError, llm_reviewer_dispatch.ReviewerDispatchError) as exc:
        # A model that cannot produce a schema-valid grounded payload (or a
        # provider that errors out) is a MEASURED per-cell outcome, never a
        # matrix crash (first live run: gemma findings flunked validate_finding
        # and killed all 24 cells). Score = every fixture claim missing.
        wall_seconds = round(time.monotonic() - started, 3)
        artifact = _error_artifact(route, fixture, exc, wall_seconds, arm=TOOLED_ARM)
        artifact_path.write_text(
            json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return BakeoffRun(artifact_path=artifact_path, artifact=artifact)
    wall_seconds = round(time.monotonic() - started, 3)
    score = score_payload(gate_result["payload"], fixture)
    gate_outcomes = gate_result["gate_outcomes"]
    score["invalid_fact_checks"] = int(gate_outcomes["grounding"].get("invalid_fact_checks") or 0)
    score["inadmissible_positive_verdicts"] = int(
        gate_outcomes["grounding"].get("inadmissible_positive_verdicts") or 0
    )
    dispatch = gate_result["dispatch"]
    artifact = {
        "schema_version": RUN_SCHEMA_VERSION,
        "arm": TOOLED_ARM,
        "created_at": _now_z(),
        "fixture": _fixture_block(fixture),
        "model": _model_block(route),
        "status": gate_result["status"],
        "workflow_verdict": gate_result["workflow_verdict"],
        "findings_schema_invalid": bool(gate_result.get("findings_schema_invalid")),
        "response_parse_lenient": bool(gate_result.get("response_parse_lenient")),
        "attempt_count": gate_result["attempt_count"],
        "dispatch": dispatch,
        "gate_outcomes": gate_outcomes,
        "payload": gate_result["payload"],
        "score": score,
        "tool_call_count": int(dispatch.get("tool_call_count") or 0),
        "wall_seconds": wall_seconds,
    }
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return BakeoffRun(artifact_path=artifact_path, artifact=artifact)


def run_one_bare(
    route: llm_reviewer_dispatch.ReviewerRoute,
    fixture: BakeoffFixture,
    *,
    output_dir: Path,
    runner: BareRunner = invoke_bakeoff_route_bare,
    force: bool = False,
    retry_failures: bool = False,
) -> BakeoffRun:
    """Run or resume one model x passage BARE (tool-free control) artifact.

    Identical resume/force/retry semantics to ``run_one`` but: a ``__bare`` artifact
    suffix, the bare prompt (no tool mandate), NO theatre/budget/deep-read/grounding
    gates (bare has no tool telemetry by design), and only the fact_checks shape is
    validated. Scoring reuses ``score_payload`` unchanged, so tooled and bare are
    directly comparable per model.
    """
    if runner is invoke_bakeoff_route_bare:
        require_offline_opt_in()
    artifact_path = output_dir / f"{pin_slug(route.reviewer_model_id)}__{fixture.slug}__bare.json"
    if artifact_path.exists() and not force:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        if not (retry_failures and artifact.get("status") == "error"):
            return BakeoffRun(artifact_path=artifact_path, artifact=artifact, skipped=True)

    prompt = build_bare_factcheck_prompt(fixture.title, fixture.passage_md)
    task_id = f"qg-bakeoff-bare-{pin_slug(route.reviewer_model_id)}-{fixture.slug}"
    started = time.monotonic()
    try:
        result = _coerce_dispatch_result(runner(route, prompt, task_id), route, prompt)
        payload, response_parse_lenient, findings_schema_invalid = _parse_bare_payload(result.response_text)
    except (ValueError, llm_reviewer_dispatch.ReviewerDispatchError) as exc:
        wall_seconds = round(time.monotonic() - started, 3)
        artifact = _error_artifact(route, fixture, exc, wall_seconds, arm=BARE_ARM)
        artifact_path.write_text(
            json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return BakeoffRun(artifact_path=artifact_path, artifact=artifact)
    wall_seconds = round(time.monotonic() - started, 3)
    dispatch = result.metadata()
    score = score_payload(payload, fixture)
    # Bare has no grounding gate: the orthogonal admissibility counters are 0 by
    # construction (kept for scorecard/aggregation parity with tooled).
    score["invalid_fact_checks"] = 0
    score["inadmissible_positive_verdicts"] = 0
    artifact = {
        "schema_version": RUN_SCHEMA_VERSION,
        "arm": BARE_ARM,
        "created_at": _now_z(),
        "fixture": _fixture_block(fixture),
        "model": _model_block(route),
        "status": "ran",
        "workflow_verdict": "BARE",
        "findings_schema_invalid": findings_schema_invalid,
        "response_parse_lenient": response_parse_lenient,
        "attempt_count": 1,
        "dispatch": dispatch,
        "gate_outcomes": {},
        "payload": payload,
        "score": score,
        "tool_call_count": int(dispatch.get("tool_call_count") or 0),
        "wall_seconds": wall_seconds,
    }
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return BakeoffRun(artifact_path=artifact_path, artifact=artifact)


_CLAIM_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)


def _normalize_claim_loose(text: str) -> str:
    """Claim matching only: punctuation-insensitive on top of the base norm.

    Live finding: fixture claims end with «.» where the model's sentence-quote
    continues with «,» — containment failed on the period alone.
    """
    return " ".join(_CLAIM_PUNCT_RE.sub(" ", _normalize_claim_text(text)).split())


def _match_rows_to_claims(
    rows: list[dict[str, Any]],
    fixture: BakeoffFixture,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Map model fact-check rows onto fixture claims (containment matching).

    Live finding (first scored matrix, 2026-07-05): models quote PASSAGE
    SENTENCES verbatim while fixture claims are trimmed sub-spans of those
    sentences — exact-normalized matching left 22-30/35 claims "missing" and
    the scorecard measured claim-echo fidelity instead of verdict quality.

    Matching, in precedence order per fixture claim:
    1. exact normalized equality (the anchor-fixture path, unchanged);
    2. containment: normalized fixture claim is a substring of a model row's
       normalized claim (models quote whole sentences; fixture claims are
       sub-spans). Among multiple containing rows the TIGHTEST (shortest) row
       wins — first-row-wins was row-order dependent and could score a broad
       row's verdict over a more specific one (codex review, PR #4485).
       A single model row MAY cover multiple fixture claims, but broad-row
       verdict transfer is polarity-guarded: confirming a sentence that
       contains a fabricated sub-claim IS confirming the fabrication (the
       shared-sentence M-traps), and any verdict on a span containing a
       fabrication is a judgment ABOUT that fabrication — but a NEGATIVE
       verdict on a compound sentence usually targets the fabricated part,
       so it must NOT transfer to a TRUE sub-claim the model never separately
       judged (it would score refuted-true −50 for a verdict the model never
       issued; the claim counts missing −10 instead).
    3. reverse containment (model row quotes a sub-span of the fixture claim),
       guarded by a length floor so tiny fragments cannot claim-jack; among
       multiple candidates the LONGEST (most coverage) wins.
    Rows that match nothing stay unmatched (counted, visible in artifacts).
    """
    matched: dict[str, dict[str, Any]] = {}
    used_rows: set[int] = set()
    norm_rows = [(_normalize_claim_loose(str(r.get("claim") or "")), r) for r in rows]

    for claim in fixture.claims:
        want = _normalize_claim_loose(claim.claim)
        if not want:
            continue
        # 1. exact
        hit = next((i for i, (nr, _r) in enumerate(norm_rows) if nr == want), None)
        # 2. fixture-claim ⊆ model-row: tightest containing row; only a
        #    CONFIRMED judgment transfers from a broader span to a TRUE claim.
        if hit is None:
            candidates = [
                i
                for i, (nr, r) in enumerate(norm_rows)
                if nr
                and want in nr
                and (not claim.is_true or _judgment_verdict(r) == "CONFIRMED")
            ]
            if candidates:
                hit = min(candidates, key=lambda i: len(norm_rows[i][0]))
        # 3. model-row ⊆ fixture-claim (length floor: ≥60% of the fixture
        #    claim): longest contained row.
        if hit is None:
            candidates = [
                i
                for i, (nr, _r) in enumerate(norm_rows)
                if nr and nr in want and len(nr) >= max(20, int(0.6 * len(want)))
            ]
            if candidates:
                hit = max(candidates, key=lambda i: len(norm_rows[i][0]))
        if hit is not None:
            matched[claim.claim_id] = norm_rows[hit][1]
            used_rows.add(hit)

    unmatched = [r for i, (_nr, r) in enumerate(norm_rows) if i not in used_rows]
    return matched, unmatched


def score_payload(payload: Mapping[str, Any], fixture: BakeoffFixture) -> dict[str, Any]:
    """Score a gated payload against fixture truth, keyed by stable claim_id."""
    fact_checks = payload.get("fact_checks")
    rows = [dict(row) for row in fact_checks] if isinstance(fact_checks, list) else []
    matched, unmatched_rows = _match_rows_to_claims(rows, fixture)

    truth_by_claim_id = {claim.claim_id: claim.is_true for claim in fixture.claims}
    scoring_rows: list[dict[str, Any]] = []
    per_claim: list[dict[str, Any]] = []
    live_score = 0
    missing_claims = 0
    class_u_good = class_u_total = 0
    class_m_good = class_m_total = 0
    true_unsupported = true_total = 0
    for claim in fixture.claims:
        row = matched.get(claim.claim_id)
        if row is None:
            missing_claims += 1
            live_score += MISSING_CLAIM_PENALTY
            per_claim.append(
                {
                    "claim_id": claim.claim_id,
                    "matched": False,
                    "is_true": claim.is_true,
                    "fabrication_class": claim.fabrication_class,
                    "model_judgment_points": MISSING_CLAIM_PENALTY,
                    "live_admissible_points": MISSING_CLAIM_PENALTY,
                    "reason": "missing_claim",
                }
            )
            if claim.fabrication_class == "U":
                class_u_total += 1
            if claim.fabrication_class == "M":
                class_m_total += 1
            if claim.is_true:
                true_total += 1
            continue

        judgment_verdict = _judgment_verdict(row)
        scoring_row = dict(row)
        scoring_row["claim"] = claim.claim_id
        scoring_row["verdict"] = judgment_verdict
        scoring_rows.append(scoring_row)
        live_verdict = str(row.get("verdict") or "")
        model_points = qg_factcheck_scoring.score_verdict(judgment_verdict, claim_is_true=claim.is_true)
        live_points = qg_factcheck_scoring.score_verdict(live_verdict, claim_is_true=claim.is_true)
        live_score += live_points
        if claim.fabrication_class == "U":
            class_u_total += 1
            class_u_good += int(_fabrication_success(judgment_verdict))
        if claim.fabrication_class == "M":
            class_m_total += 1
            class_m_good += int(_fabrication_success(judgment_verdict))
        if claim.is_true:
            true_total += 1
            true_unsupported += int(judgment_verdict in {"UNATTESTED_AFTER_SEARCH", "UNVERIFIED_INSUFFICIENT_SEARCH"})
        per_claim.append(
            {
                "claim_id": claim.claim_id,
                "matched": True,
                "claim": claim.claim,
                "model_claim": row.get("claim"),
                "is_true": claim.is_true,
                "fabrication_class": claim.fabrication_class,
                "verdict": live_verdict,
                "original_verdict": row.get("original_verdict"),
                "admissibility_downgraded": row.get("admissibility_downgraded") is True,
                "model_judgment_verdict": judgment_verdict,
                "model_judgment_points": model_points,
                "live_admissible_points": live_points,
            }
        )

    model_score = qg_factcheck_scoring.score_fact_checks(scoring_rows, truth_by_claim_id)
    model_score += missing_claims * MISSING_CLAIM_PENALTY
    return {
        "model_judgment_score": model_score,
        "live_admissible_score": live_score,
        "missing_claims": missing_claims,
        "unmatched_fact_checks": len(unmatched_rows),
        "claims": per_claim,
        "fractions": {
            "class_u_honesty": _fraction(class_u_good, class_u_total),
            "class_m_alignment": _fraction(class_m_good, class_m_total),
            "false_unsupported_on_true": _fraction(true_unsupported, true_total),
        },
    }


def write_scorecard(path: Path, artifacts: Sequence[Mapping[str, Any]]) -> None:
    """Write a markdown scorecard for the current artifact set."""
    lines = [
        "# QG Bakeoff Scorecard",
        "",
        f"Generated: {_now_z()}",
        "",
        "Fractions are exact. `low-N` marks denominators below 10.",
        "",
        "## Runs",
        "",
        "| model | passage | arm | model judgment | live admissible | missing | U honesty | M alignment | true unsupported | invalid | inadmissible | tools | wall_s |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for artifact in sorted(artifacts, key=_artifact_sort_key):
        score = _score(artifact)
        fractions = score.get("fractions", {})
        lines.append(
            "| {model} | {passage} | {arm} | {model_score} | {live_score} | {missing} | {u} | {m} | {true_bad} | {invalid} | {inadmissible} | {tools} | {wall} |".format(
                model=_model_pin(artifact),
                passage=_fixture_slug(artifact),
                arm=_artifact_arm(artifact),
                model_score=score.get("model_judgment_score", 0),
                live_score=score.get("live_admissible_score", 0),
                missing=score.get("missing_claims", 0),
                u=_fraction_label(fractions.get("class_u_honesty")),
                m=_fraction_label(fractions.get("class_m_alignment")),
                true_bad=_fraction_label(fractions.get("false_unsupported_on_true")),
                invalid=score.get("invalid_fact_checks", 0),
                inadmissible=score.get("inadmissible_positive_verdicts", 0),
                tools=artifact.get("tool_call_count", 0),
                wall=artifact.get("wall_seconds", 0),
            )
        )
    lines.extend(_totals_and_lift_section("With Anchor", artifacts))
    lines.extend(
        _totals_and_lift_section("Without Anchor", [a for a in artifacts if _fixture_slug(a) != ANCHOR_SLUG])
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def default_output_dir(day: date | None = None) -> Path:
    effective = day or datetime.now(UTC).date()
    return DEFAULT_OUTPUT_ROOT / f"{effective.isoformat()}-qg-bakeoff"


def model_pins_from_args(values: Sequence[str] | None) -> list[str]:
    """Parse ``--models`` values or fail closed on unresolved default slots."""
    if values:
        pins: list[str] = []
        for value in values:
            pins.extend(piece.strip() for piece in value.split(",") if piece.strip())
        if not pins:
            raise BakeoffConfigError("--models was provided but no model pins were parsed")
        return pins
    unresolved = [candidate.label for candidate in DEFAULT_CANDIDATE_MODELS if candidate.unresolved]
    if unresolved:
        joined = ", ".join(unresolved)
        raise BakeoffConfigError(f"default candidate pins still have TODO slots ({joined}); pass --models")
    return [candidate.pin for candidate in DEFAULT_CANDIDATE_MODELS]


def pin_slug(pin: str) -> str:
    normalized = unicodedata.normalize("NFKD", pin).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "model"



def rescore_artifacts(output_dir: Path, fixtures_dir: Path = FIXTURE_DIR) -> int:
    """Recompute scores for existing artifacts from their STORED payloads.

    Zero model invocations — pure offline rescoring, for matcher/scoring
    changes (e.g. the containment matcher). Rewrites each artifact's score
    block and the scorecard.
    """
    fixtures = {f.slug: f for f in load_fixtures(fixtures_dir)}
    artifacts: list[dict[str, Any]] = []
    count = 0
    for path in sorted(output_dir.glob("*.json")):
        artifact = json.loads(path.read_text(encoding="utf-8"))
        # Backfill ``arm`` for backward compat: pre-arm tooled artifacts have no
        # field (→ "tooled"); a ``__bare`` filename identifies a bare artifact even
        # if it somehow lacks the field. Rescore covers BOTH arms — the bare grounding
        # counters resolve to 0 because a bare artifact carries no gate_outcomes.
        artifact["arm"] = artifact.get("arm") or (BARE_ARM if path.stem.endswith("__bare") else TOOLED_ARM)
        slug = (artifact.get("fixture") or {}).get("slug")
        fixture = fixtures.get(slug)
        if fixture is None:
            artifacts.append(artifact)
            continue
        score = score_payload(artifact.get("payload") or {}, fixture)
        grounding = (artifact.get("gate_outcomes") or {}).get("grounding") or {}
        score["invalid_fact_checks"] = int(grounding.get("invalid_fact_checks") or 0)
        score["inadmissible_positive_verdicts"] = int(grounding.get("inadmissible_positive_verdicts") or 0)
        artifact["score"] = score
        artifact["rescored_at"] = _now_z()
        path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        artifacts.append(artifact)
        count += 1
    write_scorecard(output_dir / SCORECARD_NAME, artifacts)
    return count


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures-dir", type=Path, default=FIXTURE_DIR)
    parser.add_argument("--fixture", action="append", dest="fixtures", help="Fixture slug; repeatable")
    parser.add_argument("--models", action="append", help="Comma-separated or repeated OpenRouter/opencode model pins")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument(
        "--arm",
        choices=list(_ARM_CHOICES),
        default=TOOLED_ARM,
        help=(
            "Which arm(s) to run: 'tooled' (default — grounded+gated reviewer, existing "
            "behavior), 'bare' (tool-free control), or 'both'. Harness lift = tooled − bare."
        ),
    )
    parser.add_argument("--force", action="store_true", help="Redo runs even when artifact JSON exists")
    parser.add_argument(
        "--retry-failures",
        action="store_true",
        help=(
            "Resume modifier: in addition to running MISSING cells (normal resume), "
            "re-run cells whose existing artifact has status=error. Completed cells stay skipped."
        ),
    )
    parser.add_argument(
        "--rescore",
        action="store_true",
        help="Recompute scores for EXISTING artifacts from stored payloads (no model calls)",
    )
    args = parser.parse_args(argv)

    try:
        if args.rescore:
            output_dir = args.out_dir or default_output_dir()
            n = rescore_artifacts(output_dir, args.fixtures_dir)
            print(f"rescored {n} artifacts under {output_dir}")
            print(f"scorecard: {output_dir / SCORECARD_NAME}")
            return 0
        require_offline_opt_in()
        fixtures = load_fixtures(args.fixtures_dir, args.fixtures)
        pins = model_pins_from_args(args.models)
        output_dir = args.out_dir or default_output_dir()
        runs = run_matrix(
            fixtures,
            pins,
            output_dir=output_dir,
            arm=args.arm,
            force=args.force,
            retry_failures=args.retry_failures,
        )
    except BakeoffConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"wrote {len(runs)} bakeoff artifacts under {output_dir}")
    print(f"scorecard: {output_dir / SCORECARD_NAME}")
    return 0


def _invoke_and_gate(
    route: llm_reviewer_dispatch.ReviewerRoute,
    prompt: str,
    task_id: str,
    runner: ProviderRunner,
) -> dict[str, Any]:
    theatre_retried = False
    deep_read_retried = False
    attempt_prompt = prompt
    attempt_count = 0
    attempts: list[dict[str, Any]] = []
    while True:
        attempt_count += 1
        result = _coerce_dispatch_result(runner(route, attempt_prompt, task_id), route, prompt)
        dispatch = result.metadata()
        # Budget BEFORE parse/theatre — mirrors qg_workflow._run_tier2 ordering
        # (cursor review of #4458): an over-budget run hard-fails identically
        # in the harness and in live gating.
        llm_reviewer_dispatch.enforce_tool_budget(dispatch)
        response_parse_lenient = False
        try:
            payload = dict(llm_reviewer_dispatch._json_payload_from_response(result.response_text))
        except ValueError as exc:
            lenient = _lenient_first_json_object(result.response_text)
            if lenient is None:
                # Preserve what the model actually said — the first live run
                # left only "Expecting value: char 0", undiagnosable offline.
                raise BakeoffCellError(str(exc), response_head=result.response_text[:2000]) from exc
            payload = dict(lenient)
            response_parse_lenient = True
        # MEASUREMENT-VALIDITY SPLIT (live gemma cells, 2026-07-05): the bakeoff
        # measures FACT-CHECK quality; strict `findings` schema compliance is an
        # ORTHOGONAL axis. gemma emitted valid fact_checks with non-conforming
        # findings — voiding the cell would confound the central metric with
        # contract-following noise. Harness-only: strip non-conforming findings,
        # count the defect (`findings_schema_invalid`), keep gating fact_checks
        # strictly. The LIVE pipeline stays strict (SCHEMA_FAILURE) — unchanged.
        findings_schema_invalid = False
        try:
            llm_reviewer.validate_reviewer_payload(payload, BAKEOFF_POLICY_FAMILY)
        except ValueError as exc:
            stripped = dict(payload)
            stripped["findings"] = []
            try:
                llm_reviewer.validate_reviewer_payload(stripped, BAKEOFF_POLICY_FAMILY)
            except ValueError:
                # fact_checks/evidence_gaps themselves are invalid → real error cell.
                raise BakeoffCellError(str(exc), response_head=result.response_text[:2000]) from exc
            findings_schema_invalid = True
            payload = stripped
        attempt = {
            "attempt": attempt_count,
            "tool_call_count": dispatch.get("tool_call_count"),
            "tools_used": dispatch.get("tools_used", []),
            "tool_budget": {"status": "passed"},
        }
        theatre = llm_reviewer_dispatch.tool_theatre_violation(
            policy_family=BAKEOFF_POLICY_FAMILY,
            payload=payload,
            dispatch_meta=dispatch,
        )
        if theatre is not None:
            attempt["theatre"] = theatre
            attempts.append(attempt)
            if not theatre_retried:
                theatre_retried = True
                attempt_prompt = llm_reviewer_dispatch.reviewer_retry_prompt(
                    prompt,
                    llm_reviewer_dispatch.INVALID_TOOL_THEATRE,
                )
                continue
            return {
                "status": llm_reviewer_dispatch.RETRY_EXHAUSTED,
                "workflow_verdict": llm_reviewer_dispatch.INVALID_TOOL_THEATRE,
                "attempt_count": attempt_count,
                "dispatch": dispatch,
                "payload": payload,
                "gate_outcomes": {
                    "attempts": attempts,
                    "theatre": theatre,
                    "tool_budget": {"status": "passed"},
                    "deep_read": {"required": False, "retried": deep_read_retried},
                    "grounding": _empty_grounding(),
                    "factual_sweep": {"incomplete": True},
                },
            }
        attempt["theatre"] = {"status": "passed"}

        if llm_reviewer_dispatch.deep_read_required(payload, dispatch):
            attempt["deep_read"] = {"required": True, "retried": deep_read_retried}
            attempts.append(attempt)
            if not deep_read_retried:
                deep_read_retried = True
                attempt_prompt = llm_reviewer_dispatch.reviewer_retry_prompt(
                    prompt,
                    llm_reviewer_dispatch.DEEP_READ_REQUIRED,
                )
                continue
            payload = llm_reviewer_dispatch.mark_deep_read_attempted(payload)
            llm_reviewer.validate_reviewer_payload(payload, BAKEOFF_POLICY_FAMILY)
            attempt["deep_read"] = {"required": True, "retried": True, "marked_attempted": True}
        else:
            attempt["deep_read"] = {"required": False, "retried": deep_read_retried}

        grounding_gate = llm_reviewer_dispatch.enforce_grounding_against_tool_events(
            payload,
            dispatch,
            policy_family=BAKEOFF_POLICY_FAMILY,
        )
        payload = grounding_gate.payload
        if grounding_gate.inadmissible_positive_verdicts:
            payload["inadmissible_positive_verdicts"] = grounding_gate.inadmissible_positive_verdicts
        sweep_incomplete = llm_reviewer_dispatch.factual_sweep_incomplete(
            payload,
            policy_family=BAKEOFF_POLICY_FAMILY,
            invalid_fact_checks=grounding_gate.invalid_fact_checks,
        )
        grounding = {
            "ungrounded_findings": grounding_gate.ungrounded_findings,
            "required_ungrounded_findings": grounding_gate.required_ungrounded_findings,
            "invalid_fact_checks": grounding_gate.invalid_fact_checks,
            "inadmissible_positive_verdicts": grounding_gate.inadmissible_positive_verdicts,
        }
        attempt["grounding"] = grounding
        attempt["factual_sweep"] = {"incomplete": sweep_incomplete}
        attempt["findings_schema_invalid"] = findings_schema_invalid
        attempts.append(attempt)
        status = _status_for_gates(grounding_gate, sweep_incomplete)
        workflow_verdict = "FAIL" if sweep_incomplete else ("WARN" if status != "ran" else "PASS")
        return {
            "status": status,
            "workflow_verdict": workflow_verdict,
            "attempt_count": attempt_count,
            "dispatch": dispatch,
            "payload": payload,
            "findings_schema_invalid": findings_schema_invalid,
            "response_parse_lenient": response_parse_lenient,
            "gate_outcomes": {
                "attempts": attempts,
                "theatre": {"status": "passed", "retried": theatre_retried},
                "tool_budget": {"status": "passed"},
                "deep_read": attempt["deep_read"],
                "grounding": grounding,
                "factual_sweep": {"incomplete": sweep_incomplete},
                "findings_schema_invalid": findings_schema_invalid,
                "response_parse_lenient": response_parse_lenient,
            },
        }


def _status_for_gates(
    grounding_gate: llm_reviewer_dispatch.GroundingGateResult,
    sweep_incomplete: bool,
) -> str:
    if grounding_gate.inadmissible_positive_verdicts and not (
        grounding_gate.invalid_fact_checks or grounding_gate.required_ungrounded_findings
    ):
        return "inadmissible_citations"
    if grounding_gate.required_ungrounded_findings or grounding_gate.invalid_fact_checks:
        return llm_reviewer_dispatch.UNGROUNDED_FINDINGS
    if sweep_incomplete:
        return "factual_sweep_incomplete"
    return "ran"


def _coerce_dispatch_result(
    raw: llm_reviewer_dispatch.DispatchResult | str,
    route: llm_reviewer_dispatch.ReviewerRoute,
    prompt: str,
) -> llm_reviewer_dispatch.DispatchResult:
    if isinstance(raw, llm_reviewer_dispatch.DispatchResult):
        return raw
    response = str(raw)
    return llm_reviewer_dispatch.DispatchResult(
        response_text=response,
        reviewer_model_id=route.reviewer_model_id,
        reviewer_family=route.reviewer_family,
        route_name=route.route_name,
        observed_prompt_tokens=llm_reviewer_dispatch.estimate_tokens(prompt),
        observed_completion_tokens=llm_reviewer_dispatch.estimate_tokens(response),
    )


def _required_str(data: Mapping[str, Any], key: str, path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BakeoffConfigError(f"{path}: {key} must be a non-empty string")
    return value


def _normalize_claim_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text).lower()
    normalized = normalized.replace("’", "'").replace("`", "'")
    normalized = re.sub(r"\s+", " ", normalized).strip(" \t\r\n.。")
    return _LEADING_CLAIM_FILLER_RE.sub("", normalized)


def _judgment_verdict(row: Mapping[str, Any]) -> str:
    if row.get("admissibility_downgraded") is True and isinstance(row.get("original_verdict"), str):
        return str(row["original_verdict"]).strip().upper()
    return str(row.get("verdict") or "").strip().upper()


def _fabrication_success(verdict: str) -> bool:
    return qg_factcheck_scoring.score_verdict(verdict, claim_is_true=False) > 0


def _fraction(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "text": f"{numerator}/{denominator}",
        "low_n": denominator < 10,
    }


def _fraction_label(value: Any) -> str:
    if not isinstance(value, Mapping):
        return "0/0 low-N"
    suffix = " low-N" if value.get("low_n") else ""
    return f"{value.get('text', '0/0')}{suffix}"


def _totals_and_lift_section(title: str, artifacts: Sequence[Mapping[str, Any]]) -> list[str]:
    """Per-(model, arm) totals table + the harness-lift table for one anchor split."""
    totals = _aggregate_by_model_arm(artifacts)
    lines = [
        "",
        f"## Totals {title}",
        "",
        "| model | arm | passages | model judgment | live admissible | U honesty | M alignment headline | true unsupported | missing | invalid | inadmissible | tools | wall_s |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for (model, arm), row in sorted(totals.items()):
        lines.append(
            "| {model} | {arm} | {passages} | {model_score} | {live_score} | {u} | {m} | {true_bad} | {missing} | {invalid} | {inadmissible} | {tools} | {wall} |".format(
                model=model,
                arm=arm,
                passages=row["passages"],
                model_score=row["model_judgment_score"],
                live_score=row["live_admissible_score"],
                u=_fraction_label(_fraction(row["class_u_good"], row["class_u_total"])),
                m=_fraction_label(_fraction(row["class_m_good"], row["class_m_total"])),
                true_bad=_fraction_label(_fraction(row["true_unsupported"], row["true_total"])),
                missing=row["missing_claims"],
                invalid=row["invalid_fact_checks"],
                inadmissible=row["inadmissible_positive_verdicts"],
                tools=row["tool_call_count"],
                wall=round(row["wall_seconds"], 3),
            )
        )
    lines.extend(_harness_lift_section(title, artifacts))
    return lines


def _harness_lift_section(
    title: str,
    artifacts: Sequence[Mapping[str, Any]],
) -> list[str]:
    """Per-model tooled-vs-bare comparison with the headline harness-lift column.

    Lift = tooled model_judgment − bare model_judgment (positive = tooling helps),
    computed over PAIRED (model, fixture) cells ONLY — fixtures with an artifact
    in BOTH arms for that model (codex review, PR #4500 finding 1: subtracting
    unpaired aggregate totals fabricates lift from missing cells). Error
    artifacts count (they are measured cells, scored all-missing); ABSENT
    artifacts do not. A model with zero paired fixtures shows ``n/a`` — never a
    fabricated number.
    """
    cells: dict[str, dict[str, dict[str, Mapping[str, Any]]]] = defaultdict(lambda: defaultdict(dict))
    for artifact in artifacts:
        cells[_model_pin(artifact)][_fixture_slug(artifact)][_artifact_arm(artifact)] = _score(artifact)
    lines = [
        "",
        f"## Harness Lift {title}",
        "",
        "Lift = tooled model judgment − bare model judgment (positive = the harness helps),",
        "over PAIRED passages only (both arms on disk for that model+passage).",
        "M alignment is the discriminating fraction; low-N marks denominators below 10.",
        "",
        "| model | paired passages | tooled model judgment | bare model judgment | harness_lift | tooled M alignment | bare M alignment |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for model in sorted(cells):
        paired = sorted(
            slug
            for slug, arms in cells[model].items()
            if TOOLED_ARM in arms and BARE_ARM in arms
        )
        if not paired:
            lines.append(f"| {model} | 0 | n/a | n/a | n/a | n/a | n/a |")
            continue

        def _summed(arm: str, key: str, *, slugs: Sequence[str] = paired, pin: str = model) -> int:
            return sum(int(cells[pin][slug][arm].get(key) or 0) for slug in slugs)

        def _summed_fraction(arm: str, *, slugs: Sequence[str] = paired, pin: str = model) -> dict[str, Any]:
            numerator = denominator = 0
            for slug in slugs:
                fractions = cells[pin][slug][arm].get("fractions")
                m_fraction = fractions.get("class_m_alignment") if isinstance(fractions, Mapping) else None
                if isinstance(m_fraction, Mapping):
                    numerator += int(m_fraction.get("numerator") or 0)
                    denominator += int(m_fraction.get("denominator") or 0)
            return _fraction(numerator, denominator)

        tooled_mj = _summed(TOOLED_ARM, "model_judgment_score")
        bare_mj = _summed(BARE_ARM, "model_judgment_score")
        lines.append(
            f"| {model} | {len(paired)} | {tooled_mj} | {bare_mj} | {tooled_mj - bare_mj} "
            f"| {_fraction_label(_summed_fraction(TOOLED_ARM))} | {_fraction_label(_summed_fraction(BARE_ARM))} |"
        )
    return lines


def _na(value: Any) -> str:
    return "n/a" if value is None else str(value)


def _aggregate_by_model_arm(
    artifacts: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    totals: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "passages": 0,
            "model_judgment_score": 0,
            "live_admissible_score": 0,
            "class_u_good": 0,
            "class_u_total": 0,
            "class_m_good": 0,
            "class_m_total": 0,
            "true_unsupported": 0,
            "true_total": 0,
            "missing_claims": 0,
            "invalid_fact_checks": 0,
            "inadmissible_positive_verdicts": 0,
            "tool_call_count": 0,
            "wall_seconds": 0.0,
        }
    )
    for artifact in artifacts:
        row = totals[(_model_pin(artifact), _artifact_arm(artifact))]
        score = _score(artifact)
        row["passages"] += 1
        row["model_judgment_score"] += int(score.get("model_judgment_score") or 0)
        row["live_admissible_score"] += int(score.get("live_admissible_score") or 0)
        row["missing_claims"] += int(score.get("missing_claims") or 0)
        row["invalid_fact_checks"] += int(score.get("invalid_fact_checks") or 0)
        row["inadmissible_positive_verdicts"] += int(score.get("inadmissible_positive_verdicts") or 0)
        row["tool_call_count"] += int(artifact.get("tool_call_count") or 0)
        row["wall_seconds"] += float(artifact.get("wall_seconds") or 0.0)
        raw_fractions = score.get("fractions")
        fractions = raw_fractions if isinstance(raw_fractions, Mapping) else {}
        _add_fraction(row, "class_u", fractions.get("class_u_honesty"))
        _add_fraction(row, "class_m", fractions.get("class_m_alignment"))
        _add_fraction(row, "true", fractions.get("false_unsupported_on_true"), good_key="true_unsupported", total_key="true_total")
    return dict(totals)


def _add_fraction(
    row: dict[str, Any],
    prefix: str,
    value: Any,
    *,
    good_key: str | None = None,
    total_key: str | None = None,
) -> None:
    if not isinstance(value, Mapping):
        return
    row[good_key or f"{prefix}_good"] += int(value.get("numerator") or 0)
    row[total_key or f"{prefix}_total"] += int(value.get("denominator") or 0)


def _score(artifact: Mapping[str, Any]) -> Mapping[str, Any]:
    score = artifact.get("score")
    return score if isinstance(score, Mapping) else {}


def _model_pin(artifact: Mapping[str, Any]) -> str:
    model = artifact.get("model")
    if isinstance(model, Mapping):
        return str(model.get("pin") or model.get("pin_slug") or "unknown")
    return "unknown"


def _fixture_slug(artifact: Mapping[str, Any]) -> str:
    fixture = artifact.get("fixture")
    if isinstance(fixture, Mapping):
        return str(fixture.get("slug") or "unknown")
    return "unknown"


def _artifact_arm(artifact: Mapping[str, Any]) -> str:
    """Artifact arm, defaulting legacy (pre-arm) tooled artifacts to ``tooled``."""
    arm = artifact.get("arm")
    return arm if isinstance(arm, str) and arm else TOOLED_ARM


def _artifact_sort_key(artifact: Mapping[str, Any]) -> tuple[str, str, str]:
    return (_model_pin(artifact), _fixture_slug(artifact), _artifact_arm(artifact))


def _empty_grounding() -> dict[str, int]:
    return {
        "ungrounded_findings": 0,
        "required_ungrounded_findings": 0,
        "invalid_fact_checks": 0,
        "inadmissible_positive_verdicts": 0,
    }


def _now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
