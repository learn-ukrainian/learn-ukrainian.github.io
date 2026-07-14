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
import contextlib
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
import unicodedata
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import llm_reviewer, llm_reviewer_dispatch, qg_factcheck_scoring, qg_schema
from scripts.audit.qg_run_serializer import RUN_SCHEMA_VERSION, serialize_qg_run_v2
from scripts.audit.runtime_tool_events import map_runtime_tool_calls

FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "qg_bakeoff"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "audit"
BENCHMARK_V1_MANIFEST = PROJECT_ROOT / "benchmarks" / "v1" / "MANIFEST.json"
SCORECARD_NAME = "SCORECARD.md"
SCORECARD_STRICT_NAME = "SCORECARD-STRICT.md"
# Provenance tag for offline ``--regate`` rescoring: live_admissible uses STRICT
# grounding (gate tag + scorer neutralization); model_judgment is unchanged.
GROUNDING_STRICT_SCORE_SEMANTICS = "grounding_strict.v1"
_GROUNDING_STRICT_BANNER = (
    "Scores in this scorecard use **STRICT grounding** (`grounding_strict.v1`): "
    "`live_admissible` credits only self-grounded positive verdicts; "
    "`model_judgment` keeps the raw engine verdict. "
    "Regenerated offline via `--regate` — no model calls. "
    "Compare to `SCORECARD.md` only when that file was produced under the same semantics."
)
ANCHOR_SLUG = "vesnianky"
MISSING_CLAIM_PENALTY = -10
BAKEOFF_LEVEL = "folk"
BAKEOFF_POLICY_FAMILY = "seminar"
LM_EVAL_RESULTS_PREFIX = "results_"
LM_EVAL_TASK_MODEL_JUDGMENT = "qg_factuality_model_judgment"
LM_EVAL_TASK_U_HONESTY = "qg_factuality_u_honesty"
LM_EVAL_TASK_M_ALIGNMENT = "qg_factuality_m_alignment"
LM_EVAL_TASK_HARNESS_LIFT = "qg_factuality_harness_lift"
# Arms of the bakeoff. TOOLED = the shipped grounded+gated reviewer path;
# BARE = the tool-free control (model judges from its own knowledge, no gates)
# so tooled − bare per model quantifies the harness lift (#2156 step 3).
TOOLED_ARM = "tooled"
BARE_ARM = "bare"
BOTH_ARM = "both"
_ARM_CHOICES = (TOOLED_ARM, BARE_ARM, BOTH_ARM)
OPENCODE_TRANSPORT = "opencode"
OPENCODE_ENTRYPOINT = "qg_bakeoff_opencode"
OPENCODE_MEASUREMENT_TIER = "opencode_bare_or_tooled"
DEEPSEEK_DIRECT_FLASH_PIN = "deepseek-direct/deepseek-v4-flash"
DEEPSEEK_DIRECT_PRO_PIN = "deepseek-direct/deepseek-v4-pro"
DEEPSEEK_DIRECT_PINS = (DEEPSEEK_DIRECT_FLASH_PIN, DEEPSEEK_DIRECT_PRO_PIN)
DEEPSEEK_OPENROUTER_FLASH_PIN = "openrouter/deepseek/deepseek-v4-flash"
DEEPSEEK_OPENROUTER_PRO_PIN = "openrouter/deepseek/deepseek-v4-pro"
DEEPSEEK_OPENROUTER_PINS = (DEEPSEEK_OPENROUTER_FLASH_PIN, DEEPSEEK_OPENROUTER_PRO_PIN)
BARE_RUNTIME_ENTRYPOINT = "qg_bakeoff_runtime"
TOOLED_RUNTIME_ENTRYPOINT = "qg_bakeoff_runtime_tooled"
SUBSCRIPTION_RUNTIME_BARE_TIER = "subscription_runtime_bare"
SUBSCRIPTION_RUNTIME_TOOLED_TIER = "subscription_runtime_tooled"
SUBSCRIPTION_BARE_BANNER = (
    "subscription-runtime bare — not raw completion; do not compare to opencode bare rows or external leaderboards."
)
SUBSCRIPTION_TOOLED_BANNER = (
    "subscription-runtime tooled — separate transport row from opencode tooled; do not blend with open-weight bakeoff rows."
)
FAILURE_CLASS_TRANSPORT = "transport"
FAILURE_CLASS_OPS_QUOTA = "ops_quota"
FAILURE_CLASS_MODEL_FAILURE = "model_failure"
_FAILURE_CLASSES = {
    FAILURE_CLASS_TRANSPORT,
    FAILURE_CLASS_OPS_QUOTA,
    FAILURE_CLASS_MODEL_FAILURE,
}
_RUN_SUFFIX_RE = re.compile(r"__r([1-9][0-9]*)$")
# Verbatim reuse markers: the bare prompt slices the LIVE verdict taxonomy out of
# the reviewer template so the fact-check verdict set can never fork from tooled.
_TAXONOMY_START = "Each fact check MUST use exactly one verdict from this taxonomy:"
_TAXONOMY_END = "Few-shot anchors:"
_LEADING_CLAIM_FILLER_RE = re.compile(r"^(?:або|чи)\s+", re.IGNORECASE)

DOMAIN_BY_SLUG: Mapping[str, str] = MappingProxyType(
    {
        "vesnianky": "folk",
        "kupalski": "folk",
        "zhnyvarski": "folk",
        "koliadky": "folk",
        "holosinnia": "folk",
        "rusalii": "folk",
        "vesilnyi-obriad": "folk",
        "andriivski-vechornytsi": "folk",
        "vertep": "folk",
        "khmelnytskyi-1648": "history",
        "khreshchennia-rusi": "history",
        "yaroslav-sofiya": "history",
        "zaporozka-sich": "history",
        # The almanac fixture is routed to history because the measurement
        # target is publication context and cultural-national movement history.
        "rusalka-dnistrova": "history",
        "kyrylo-metodiivske-tovarystvo": "history",
        "ahatanhel-krymskyi": "bio",
        "franko-ivan": "bio",
        "lesya-ukrainka": "bio",
        "skovoroda-hryhorii": "bio",
        "kotliarevskyi-ivan": "bio",
        "lysenko-mykola": "bio",
    }
)


@dataclass(frozen=True, slots=True)
class CandidateModel:
    label: str
    pin: str
    unresolved: bool = False


# TODO(#2156): resolve exact subscription-family pins at run time via
# ``--models`` after checking the currently served native CLI/model list. Do not
# guess. DeepSeek runs FIRST-PARTY ONLY (user order 2026-07-07; openrouter/deepseek
# is guard-refused after the account drain). ``DEEPSEEK_OPENROUTER_PINS`` name the
# historical baseline pins for artifact/scorecard readers; running them requires
# LU_ROUTING_GUARD_OVERRIDE=1 with explicit user authorization.
DEFAULT_CANDIDATE_MODELS: tuple[CandidateModel, ...] = (
    CandidateModel("gemma-4-31b", "openrouter/google/gemma-4-31b-it"),
    CandidateModel("deepseek-v4-flash-direct", DEEPSEEK_DIRECT_FLASH_PIN),
    CandidateModel("deepseek-v4-pro-direct", DEEPSEEK_DIRECT_PRO_PIN),
    CandidateModel("claude-frontier-openrouter-unreachable", "TODO_OPENROUTER_ANTHROPIC_FRONTIER_PIN", unresolved=True),
    CandidateModel("gpt-frontier-openrouter-unreachable", "TODO_OPENROUTER_OPENAI_FRONTIER_PIN", unresolved=True),
    CandidateModel("gemini-frontier-openrouter-unreachable", "TODO_OPENROUTER_GOOGLE_GEMINI_FRONTIER_PIN", unresolved=True),
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
    canary_sentence: str | None = None


@dataclass(frozen=True, slots=True)
class BakeoffRun:
    artifact_path: Path
    artifact: dict[str, Any]
    skipped: bool = False


@dataclass(frozen=True, slots=True)
class RouteIdentity:
    transport: str
    entrypoint: str
    session_policy: str
    measurement_tier: str
    pricing_basis: str
    resolved_model: str | None = None
    cli_version: str = "unknown"
    runtime_agent: str | None = None
    tool_config: Mapping[str, Any] | None = None


class BakeoffConfigError(ValueError):
    """Configuration or fixture validation error."""


class BakeoffCellError(ValueError):
    """Per-cell failure carrying the raw response head for diagnosis."""

    def __init__(self, message: str, *, response_head: str | None = None) -> None:
        super().__init__(message)
        self.response_head = response_head


class BakeoffTransportError(llm_reviewer_dispatch.ReviewerProviderError):
    """Transport/CLI failure for retryable bare runtime cells."""

    def __init__(
        self,
        message: str,
        *,
        timed_out: bool = False,
        returncode: int | None = None,
    ) -> None:
        super().__init__(message)
        self.timed_out = timed_out
        self.returncode = returncode


class BakeoffOpsQuotaError(llm_reviewer_dispatch.ReviewerProviderError):
    """Auth/headroom/quota failure; excluded from judgment aggregates."""


class BakeoffModelFailure(BakeoffCellError):
    """Model returned empty/refusal/malformed content; measured as a model cell."""


ProviderRunner = Callable[
    [llm_reviewer_dispatch.ReviewerRoute, str, str],
    llm_reviewer_dispatch.DispatchResult | str,
]

# The bare control arm's runner is the SAME shape as ProviderRunner. It exists as
# a named seam (#2156 step 5): OpenRouter/opencode bare cells and the phase-1
# subscription-runtime bare cells both plug in here while sharing parsing,
# scoring, artifacts, and scorecards.
BareRunner = ProviderRunner


CLAUDE_SUBSCRIPTION_BARE_MODEL_ID = "claude-opus-4-8"
GPT_SUBSCRIPTION_BARE_MODEL_ID = "gpt-5.5"
GEMINI_SUBSCRIPTION_BARE_MODEL_ID = "gemini-3.1-pro-high"
_SUBSCRIPTION_PRICING_BASIS = (
    "subscription runtime bare seat; marginal token pricing is not exposed by the CLI, "
    "so per-cell price is recorded as 0.0 and must not be compared as API spend"
)


def _runtime_bridge_command(agent: str, model: str, *, entrypoint: str = BARE_RUNTIME_ENTRYPOINT) -> tuple[str, ...]:
    """Return the audited runtime call shape, not an ask-* bridge wrapper."""
    if agent == "claude":
        return (
            "agent_runtime.invoke",
            "claude",
            "--entrypoint",
            entrypoint,
            "--model",
            model,
            "--hard-timeout",
            "1800",
            "--tool-config",
            # use_bare=false is LOAD-BEARING: `claude --bare` skips the OAuth
            # session entirely and requires ANTHROPIC_API_KEY — on the
            # subscription machine it returns "Not logged in" (live-probed
            # 2026-07-06, apiKeySource=none, error=authentication_failed).
            # The subscription seat runs the standard -p path; the BARE part
            # of the measurement is the prompt, not the CLI harness.
            "use_bare=false,output_format=stream-json",
        )
    if agent == "codex":
        return (
            "agent_runtime.invoke",
            "codex",
            "--entrypoint",
            entrypoint,
            "--model",
            model,
            "--hard-timeout",
            "1800",
        )
    if agent == "agy":
        return (
            "agent_runtime.invoke",
            "agy",
            "--entrypoint",
            entrypoint,
            "--model",
            model,
            "--hard-timeout",
            "1800",
        )
    raise BakeoffConfigError(f"unsupported subscription bare runtime agent: {agent!r}")


SUBSCRIPTION_BARE_ROUTES: tuple[llm_reviewer_dispatch.ReviewerRoute, ...] = (
    llm_reviewer_dispatch.ReviewerRoute(
        route_name="bare_runtime_claude",
        bridge_command=_runtime_bridge_command("claude", CLAUDE_SUBSCRIPTION_BARE_MODEL_ID),
        reviewer_model_id=CLAUDE_SUBSCRIPTION_BARE_MODEL_ID,
        reviewer_family="anthropic",
        purpose="Subscription-runtime bare fact-check control via Claude Code",
        input_usd_per_mtok=0.0,
        output_usd_per_mtok=0.0,
        requires_mcp=False,
    ),
    llm_reviewer_dispatch.ReviewerRoute(
        route_name="bare_runtime_gpt",
        bridge_command=_runtime_bridge_command("codex", GPT_SUBSCRIPTION_BARE_MODEL_ID),
        reviewer_model_id=GPT_SUBSCRIPTION_BARE_MODEL_ID,
        reviewer_family="openai",
        purpose="Subscription-runtime bare fact-check control via Codex exec",
        input_usd_per_mtok=0.0,
        output_usd_per_mtok=0.0,
        requires_mcp=False,
    ),
    llm_reviewer_dispatch.ReviewerRoute(
        route_name="bare_runtime_gemini",
        bridge_command=_runtime_bridge_command("agy", GEMINI_SUBSCRIPTION_BARE_MODEL_ID),
        reviewer_model_id=GEMINI_SUBSCRIPTION_BARE_MODEL_ID,
        reviewer_family="google",
        purpose="Subscription-runtime bare fact-check control via Agy/Gemini",
        input_usd_per_mtok=0.0,
        output_usd_per_mtok=0.0,
        requires_mcp=False,
    ),
)

_SUBSCRIPTION_BARE_ROUTES_BY_PIN = {
    route.reviewer_model_id: route for route in SUBSCRIPTION_BARE_ROUTES
}


def _subscription_tooled_tool_config(runtime_agent: str) -> dict[str, Any]:
    from scripts.agent_runtime.tool_config import build_mcp_tool_config

    if runtime_agent == "agy":
        config, diagnostics = build_mcp_tool_config("agy", mcp_servers=["sources"])
    elif runtime_agent == "claude":
        config, diagnostics = build_mcp_tool_config(
            "claude",
            mcp_servers=["sources"],
            allowed_tools="mcp__sources__*",
        )
        if config is not None:
            config = {
                **config,
                "output_format": "stream-json",
                "use_bare": False,
            }
    elif runtime_agent == "codex":
        config, diagnostics = build_mcp_tool_config("codex", mcp_servers=["sources"])
    else:
        raise BakeoffConfigError(f"subscription tooled runtime not wired for agent {runtime_agent!r}")
    if config is None:
        raise BakeoffConfigError(f"subscription tooled MCP config unavailable: {diagnostics}")
    return dict(config)


SUBSCRIPTION_TOOLED_ROUTES: tuple[llm_reviewer_dispatch.ReviewerRoute, ...] = (
    llm_reviewer_dispatch.ReviewerRoute(
        route_name="tooled_runtime_claude",
        bridge_command=_runtime_bridge_command(
            "claude",
            CLAUDE_SUBSCRIPTION_BARE_MODEL_ID,
            entrypoint=TOOLED_RUNTIME_ENTRYPOINT,
        ),
        reviewer_model_id=CLAUDE_SUBSCRIPTION_BARE_MODEL_ID,
        reviewer_family="anthropic",
        purpose="Subscription-runtime tooled fact-check via Claude Code (#4763)",
        input_usd_per_mtok=0.0,
        output_usd_per_mtok=0.0,
        requires_mcp=True,
    ),
    llm_reviewer_dispatch.ReviewerRoute(
        route_name="tooled_runtime_gpt",
        bridge_command=_runtime_bridge_command(
            "codex",
            GPT_SUBSCRIPTION_BARE_MODEL_ID,
            entrypoint=TOOLED_RUNTIME_ENTRYPOINT,
        ),
        reviewer_model_id=GPT_SUBSCRIPTION_BARE_MODEL_ID,
        reviewer_family="openai",
        purpose="Subscription-runtime tooled fact-check via Codex exec (#4762)",
        input_usd_per_mtok=0.0,
        output_usd_per_mtok=0.0,
        requires_mcp=True,
    ),
    llm_reviewer_dispatch.ReviewerRoute(
        route_name="tooled_runtime_gemini",
        bridge_command=_runtime_bridge_command(
            "agy",
            GEMINI_SUBSCRIPTION_BARE_MODEL_ID,
            entrypoint=TOOLED_RUNTIME_ENTRYPOINT,
        ),
        reviewer_model_id=GEMINI_SUBSCRIPTION_BARE_MODEL_ID,
        reviewer_family="google",
        purpose="Subscription-runtime tooled fact-check via Agy/Gemini (#4761)",
        input_usd_per_mtok=0.0,
        output_usd_per_mtok=0.0,
        requires_mcp=True,
    ),
)

_SUBSCRIPTION_TOOLED_ROUTES_BY_PIN = {
    route.reviewer_model_id: route for route in SUBSCRIPTION_TOOLED_ROUTES
}
_SUBSCRIPTION_BARE_IDENTITIES: dict[str, RouteIdentity] = {
    "bare_runtime_claude": RouteIdentity(
        transport="runtime-claude",
        entrypoint=BARE_RUNTIME_ENTRYPOINT,
        session_policy="fresh",
        measurement_tier=SUBSCRIPTION_RUNTIME_BARE_TIER,
        pricing_basis=_SUBSCRIPTION_PRICING_BASIS,
        resolved_model=CLAUDE_SUBSCRIPTION_BARE_MODEL_ID,
        runtime_agent="claude",
        tool_config={"use_bare": False, "output_format": "stream-json"},
    ),
    "bare_runtime_gpt": RouteIdentity(
        transport="runtime-codex",
        entrypoint=BARE_RUNTIME_ENTRYPOINT,
        session_policy="fresh",
        measurement_tier=SUBSCRIPTION_RUNTIME_BARE_TIER,
        pricing_basis=_SUBSCRIPTION_PRICING_BASIS,
        resolved_model=GPT_SUBSCRIPTION_BARE_MODEL_ID,
        runtime_agent="codex",
        tool_config=None,
    ),
    "bare_runtime_gemini": RouteIdentity(
        transport="runtime-agy",
        entrypoint=BARE_RUNTIME_ENTRYPOINT,
        session_policy="fresh",
        measurement_tier=SUBSCRIPTION_RUNTIME_BARE_TIER,
        pricing_basis=_SUBSCRIPTION_PRICING_BASIS,
        resolved_model=GEMINI_SUBSCRIPTION_BARE_MODEL_ID,
        runtime_agent="agy",
        tool_config=None,
    ),
}
_SUBSCRIPTION_TOOLED_IDENTITIES: dict[str, RouteIdentity] = {
    "tooled_runtime_claude": RouteIdentity(
        transport="runtime-claude",
        entrypoint=TOOLED_RUNTIME_ENTRYPOINT,
        session_policy="fresh",
        measurement_tier=SUBSCRIPTION_RUNTIME_TOOLED_TIER,
        pricing_basis=_SUBSCRIPTION_PRICING_BASIS,
        resolved_model=CLAUDE_SUBSCRIPTION_BARE_MODEL_ID,
        runtime_agent="claude",
        tool_config=None,
    ),
    "tooled_runtime_gpt": RouteIdentity(
        transport="runtime-codex",
        entrypoint=TOOLED_RUNTIME_ENTRYPOINT,
        session_policy="fresh",
        measurement_tier=SUBSCRIPTION_RUNTIME_TOOLED_TIER,
        pricing_basis=_SUBSCRIPTION_PRICING_BASIS,
        resolved_model=GPT_SUBSCRIPTION_BARE_MODEL_ID,
        runtime_agent="codex",
        tool_config=None,
    ),
    "tooled_runtime_gemini": RouteIdentity(
        transport="runtime-agy",
        entrypoint=TOOLED_RUNTIME_ENTRYPOINT,
        session_policy="fresh",
        measurement_tier=SUBSCRIPTION_RUNTIME_TOOLED_TIER,
        pricing_basis=_SUBSCRIPTION_PRICING_BASIS,
        resolved_model=GEMINI_SUBSCRIPTION_BARE_MODEL_ID,
        runtime_agent="agy",
        tool_config=None,
    ),
}


def _lenient_first_json_object(response_text: str) -> Mapping[str, Any] | None:
    """Parse the FIRST JSON object from a response with leading/trailing garbage.

    Measured live (deepseek-v4-flash): a valid payload followed by extra text
    ("Extra data: char 7498"). JSON hygiene is a contract defect worth
    counting, not a reason to void the fact-check measurement.

    Measured live (claude-opus tooled, 2026-07-08): prose preamble before the
    JSON object ("I've completed the required search protocol..."). Returns None
    when no object parses.
    """
    text = response_text.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1]
    elif text.startswith("```"):
        text = text.split("```", 1)[1]
    text = text.lstrip()
    for candidate in (text, text[text.find("{") :] if "{" in text else ""):
        if not candidate or not candidate.lstrip().startswith("{"):
            continue
        try:
            payload, _end = json.JSONDecoder().raw_decode(candidate.lstrip())
        except json.JSONDecodeError:
            continue
        if isinstance(payload, Mapping):
            return payload
    return None


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
    canary_sentence = _optional_canary_sentence(raw, passage_md, path)
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
        _assert_claim_not_canary_overlap(path, claim_id, claim, canary_sentence)
        claims.append(
            FixtureClaim(
                claim_id=claim_id,
                claim=claim,
                is_true=is_true,
                fabrication_class=fabrication_class,
                distractor_evidence=distractor,
            )
        )
    return BakeoffFixture(
        slug=slug,
        title=title,
        passage_md=passage_md,
        claims=tuple(claims),
        canary_sentence=canary_sentence,
    )


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


def route_for_matrix_pin(pin: str, *, arm: str) -> llm_reviewer_dispatch.ReviewerRoute:
    """Resolve a requested pin to the only route allowed for the requested arm."""
    if arm == BARE_ARM:
        subscription_route = _SUBSCRIPTION_BARE_ROUTES_BY_PIN.get(pin)
        if subscription_route is not None:
            return subscription_route
    elif arm == TOOLED_ARM:
        subscription_route = _SUBSCRIPTION_TOOLED_ROUTES_BY_PIN.get(pin)
        if subscription_route is not None:
            return subscription_route
        if pin in _SUBSCRIPTION_BARE_ROUTES_BY_PIN:
            raise BakeoffConfigError(
                "subscription-runtime native pin is bare-only for this seat; "
                f"pin={pin!r} was requested with --arm {arm!r}"
            )
    elif pin in _SUBSCRIPTION_BARE_ROUTES_BY_PIN or pin in _SUBSCRIPTION_TOOLED_ROUTES_BY_PIN:
        raise BakeoffConfigError(
            "subscription-runtime native pins do not support --arm both yet; "
            f"pin={pin!r} was requested with --arm {arm!r}"
        )
    return bakeoff_route_for_model(pin)


def _route_identity(route: llm_reviewer_dispatch.ReviewerRoute) -> RouteIdentity:
    if route.route_name in _SUBSCRIPTION_BARE_IDENTITIES:
        return _SUBSCRIPTION_BARE_IDENTITIES[route.route_name]
    if route.route_name in _SUBSCRIPTION_TOOLED_IDENTITIES:
        return _SUBSCRIPTION_TOOLED_IDENTITIES[route.route_name]
    return RouteIdentity(
        transport=OPENCODE_TRANSPORT,
        entrypoint=OPENCODE_ENTRYPOINT,
        session_policy="fresh",
        measurement_tier=OPENCODE_MEASUREMENT_TIER,
        pricing_basis="route-specific API pricing or measured scorecard profile; see reviewer dispatch cost basis",
        resolved_model=route.reviewer_model_id,
        cli_version="unknown",
        runtime_agent=None,
        tool_config=None,
    )


def _route_transport(route: llm_reviewer_dispatch.ReviewerRoute) -> str:
    return _route_identity(route).transport


def _transport_slug(transport: str) -> str:
    return pin_slug(transport)


def _validate_run_index(run_index: int) -> int:
    if isinstance(run_index, bool) or not isinstance(run_index, int) or run_index < 1:
        raise BakeoffConfigError(f"run_index must be an integer >= 1; got {run_index!r}")
    return run_index


def _artifact_run_index(artifact: Mapping[str, Any]) -> int:
    """Return the artifact's authoritative 1-based run index.

    ``run_index`` is additive for ``qg_bakeoff_run.v2``: legacy artifacts omit
    it and are therefore run 1. Invalid explicit values fail closed because
    aggregation and canary refusal depend on this field not being ambiguous.
    """
    raw = artifact.get("run_index", 1)
    if isinstance(raw, bool) or not isinstance(raw, int) or raw < 1:
        raise BakeoffConfigError(f"artifact run_index must be an integer >= 1; got {raw!r}")
    return raw


def _artifact_filename_run_index(path: Path) -> int:
    match = _RUN_SUFFIX_RE.search(path.stem)
    if match is None:
        return 1
    return int(match.group(1))


def _assert_artifact_filename_matches_run_index(path: Path, artifact: Mapping[str, Any]) -> None:
    field_run_index = _artifact_run_index(artifact)
    filename_run_index = _artifact_filename_run_index(path)
    if field_run_index != filename_run_index:
        raise BakeoffConfigError(
            f"{path}: artifact run_index={field_run_index} does not match "
            f"filename run index={filename_run_index}"
        )


def _cell_artifact_path(
    output_dir: Path,
    route: llm_reviewer_dispatch.ReviewerRoute,
    fixture: BakeoffFixture,
    arm: str,
    run_index: int = 1,
) -> Path:
    """Build the unique artifact path for one model/passage/arm/run cell."""
    run_index = _validate_run_index(run_index)
    if arm not in (TOOLED_ARM, BARE_ARM):
        raise BakeoffConfigError(f"cell artifact arm must be {TOOLED_ARM!r} or {BARE_ARM!r}; got {arm!r}")
    stem = f"{pin_slug(route.reviewer_model_id)}__{fixture.slug}"
    if arm == BARE_ARM:
        stem += f"__bare__{_transport_slug(_route_transport(route))}"
    if run_index > 1:
        stem += f"__r{run_index}"
    return output_dir / f"{stem}.json"


def domain_for_slug(slug: str) -> str:
    """Return the locked bakeoff domain for a fixture slug, failing closed."""
    try:
        return DOMAIN_BY_SLUG[slug]
    except KeyError as exc:
        raise BakeoffConfigError(f"missing DOMAIN_BY_SLUG mapping for fixture slug: {slug!r}") from exc


def _is_subscription_bare_route(route: llm_reviewer_dispatch.ReviewerRoute) -> bool:
    return route.route_name in _SUBSCRIPTION_BARE_IDENTITIES


def _is_subscription_tooled_route(route: llm_reviewer_dispatch.ReviewerRoute) -> bool:
    return route.route_name in _SUBSCRIPTION_TOOLED_IDENTITIES


def _subscription_identity(route: llm_reviewer_dispatch.ReviewerRoute) -> RouteIdentity:
    identity = _route_identity(route)
    if not identity.runtime_agent:
        raise BakeoffConfigError(f"route is not a subscription-runtime route: {route.route_name!r}")
    return identity


def invoke_bakeoff_route(
    route: llm_reviewer_dispatch.ReviewerRoute,
    prompt: str,
    task_id: str,
) -> llm_reviewer_dispatch.DispatchResult:
    """Invoke an experiment route over opencode or subscription runtime."""
    if _is_subscription_tooled_route(route):
        return invoke_subscription_tooled_route(route, prompt, task_id)
    del task_id
    return llm_reviewer_dispatch._invoke_opencode_reviewer(
        prompt,
        route,
        default_timeout_s=1800,
        require_mcp=True,
        no_module_persistence=True,
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
    """Bare control invocation over either opencode or subscription runtime.

    Opencode bare mirrors ``invoke_bakeoff_route`` with ``require_mcp=False``:
    the model judges from its own knowledge with no sources. Subscription
    bare routes go through ``agent_runtime.invoke`` with the same bare prompt,
    no ask-* wrappers, and no standing-rules bridge framing.
    """
    if _is_subscription_bare_route(route):
        return invoke_subscription_bare_route(route, prompt, task_id)
    del task_id
    return llm_reviewer_dispatch._invoke_opencode_reviewer(
        prompt,
        route,
        default_timeout_s=1800,
        require_mcp=False,
        no_module_persistence=True,
    )


_NEUTRAL_RUNTIME_CWD: Path | None = None


def _neutral_runtime_cwd() -> Path:
    """Out-of-repo cwd for subscription bare cells (standing-rules firewall).

    Agent CLIs discover project standing rules by walking UP from cwd —
    claude loads CLAUDE.md, codex loads AGENTS.md, gemini/agy loads GEMINI.md.
    Running bare cells from PROJECT_ROOT silently injects those rules (VESUM
    mandates, review protocols) into a measurement that promises a bare
    prompt — exactly the framing the design v2 forbids. A per-process temp
    dir outside the repo keeps the prompt bare. User-GLOBAL config
    (~/.claude/CLAUDE.md etc.) may still load — that residue is part of what
    measurement_tier=subscription_runtime_bare + the scorecard banner declare.
    """
    global _NEUTRAL_RUNTIME_CWD
    if _NEUTRAL_RUNTIME_CWD is None or not _NEUTRAL_RUNTIME_CWD.exists():
        candidate = Path(tempfile.mkdtemp(prefix="qg-bakeoff-bare-"))
        repo_root = PROJECT_ROOT.resolve()
        if candidate.resolve() == repo_root or candidate.resolve().is_relative_to(repo_root):
            # TMPDIR pointed under the repo — the firewall would silently
            # fail (codex review, #4577). Force a genuinely external dir.
            candidate = Path(tempfile.mkdtemp(prefix="qg-bakeoff-bare-", dir="/tmp"))
        _NEUTRAL_RUNTIME_CWD = candidate
    return _NEUTRAL_RUNTIME_CWD


def invoke_subscription_bare_route(
    route: llm_reviewer_dispatch.ReviewerRoute,
    prompt: str,
    task_id: str,
) -> llm_reviewer_dispatch.DispatchResult:
    """Invoke a subscription bare route through ``agent_runtime.invoke`` only."""
    identity = _subscription_identity(route)
    try:
        from scripts.agent_runtime import runner as agent_runner
        from scripts.agent_runtime.errors import (
            AgentStalledError,
            AgentTimeoutError,
            AgentUnavailableError,
            RateLimitedError,
        )

        result = agent_runner.invoke(
            identity.runtime_agent or "",
            prompt,
            mode="read-only",
            cwd=_neutral_runtime_cwd(),
            model=route.reviewer_model_id,
            task_id=task_id,
            session_id=None,
            tool_config=dict(identity.tool_config or {}),
            entrypoint=BARE_RUNTIME_ENTRYPOINT,
            hard_timeout=1800,
            stall_timeout=600,
        )
    except RateLimitedError as exc:
        raise BakeoffOpsQuotaError(str(exc)) from exc
    except AgentTimeoutError as exc:
        raise BakeoffTransportError(str(exc), timed_out=True) from exc
    except AgentStalledError as exc:
        raise BakeoffTransportError(str(exc), timed_out=False) from exc
    except AgentUnavailableError as exc:
        raise BakeoffTransportError(str(exc), timed_out=False) from exc
    except OSError as exc:
        raise BakeoffTransportError(str(exc), timed_out=False) from exc
    except Exception as exc:
        raise BakeoffTransportError(str(exc), timed_out=False) from exc

    usage = dict(result.usage_record or {})
    usage.update(
        {
            "agent": result.agent,
            "entrypoint": BARE_RUNTIME_ENTRYPOINT,
            "cli_version": result.cli_version,
            "resolved_model": result.model,
            "returncode": result.returncode,
            # Standing-rules firewall trail: bare cells run from an
            # out-of-repo temp dir so project CLAUDE.md/AGENTS.md/GEMINI.md
            # never reach the measured prompt.
            "cwd_policy": "neutral-tmp",
        }
    )
    if result.rate_limited:
        raise BakeoffOpsQuotaError(result.stderr_excerpt or "runtime reported rate limit")
    if result.returncode not in (0, None) and not result.ok:
        raise BakeoffTransportError(
            result.stderr_excerpt or f"runtime returned non-zero exit {result.returncode}",
            returncode=result.returncode,
        )
    if not result.ok:
        raise BakeoffModelFailure(result.stderr_excerpt or "runtime returned no usable response")
    response = (result.response or "").strip()
    if not response:
        raise BakeoffModelFailure("runtime returned empty response")
    return llm_reviewer_dispatch.DispatchResult(
        response_text=response,
        reviewer_model_id=route.reviewer_model_id,
        reviewer_family=route.reviewer_family,
        route_name=route.route_name,
        observed_prompt_tokens=llm_reviewer_dispatch.estimate_tokens(prompt),
        observed_completion_tokens=llm_reviewer_dispatch.estimate_tokens(response),
        observed_cost_usd=0.0,
        usage=usage,
        tool_call_count=int(result.tool_calls_total or 0),
        tools_used=tuple(
            str(call.get("name") or call.get("tool") or "")
            for call in result.tool_calls
            if isinstance(call, Mapping) and (call.get("name") or call.get("tool"))
        ),
        tool_events=map_runtime_tool_calls(
            [call for call in result.tool_calls if isinstance(call, Mapping)]
        ),
    )


def invoke_subscription_tooled_route(
    route: llm_reviewer_dispatch.ReviewerRoute,
    prompt: str,
    task_id: str,
) -> llm_reviewer_dispatch.DispatchResult:
    """Invoke a subscription tooled route through ``agent_runtime.invoke``."""
    identity = _subscription_identity(route)
    runtime_agent = identity.runtime_agent or ""
    tool_config = _subscription_tooled_tool_config(runtime_agent)
    mode = "danger" if runtime_agent == "agy" else "workspace-write"
    try:
        from scripts.agent_runtime import runner as agent_runner
        from scripts.agent_runtime.errors import (
            AgentStalledError,
            AgentTimeoutError,
            AgentUnavailableError,
            RateLimitedError,
        )

        result = agent_runner.invoke(
            runtime_agent,
            prompt,
            mode=mode,
            cwd=_neutral_runtime_cwd(),
            model=route.reviewer_model_id,
            task_id=task_id,
            session_id=None,
            tool_config=tool_config,
            entrypoint=TOOLED_RUNTIME_ENTRYPOINT,
            hard_timeout=1800,
            stall_timeout=600,
            effort="xhigh" if runtime_agent == "claude" else None,
        )
    except RateLimitedError as exc:
        raise BakeoffOpsQuotaError(str(exc)) from exc
    except AgentTimeoutError as exc:
        raise BakeoffTransportError(str(exc), timed_out=True) from exc
    except AgentStalledError as exc:
        raise BakeoffTransportError(str(exc), timed_out=False) from exc
    except AgentUnavailableError as exc:
        raise BakeoffTransportError(str(exc), timed_out=False) from exc
    except OSError as exc:
        raise BakeoffTransportError(str(exc), timed_out=False) from exc
    except Exception as exc:
        raise BakeoffTransportError(str(exc), timed_out=False) from exc

    usage = dict(result.usage_record or {})
    usage.update(
        {
            "agent": result.agent,
            "entrypoint": TOOLED_RUNTIME_ENTRYPOINT,
            "cli_version": result.cli_version,
            "resolved_model": result.model,
            "returncode": result.returncode,
            "cwd_policy": "neutral-tmp",
        }
    )
    if result.rate_limited:
        raise BakeoffOpsQuotaError(result.stderr_excerpt or "runtime reported rate limit")
    if result.returncode not in (0, None) and not result.ok:
        raise BakeoffTransportError(
            result.stderr_excerpt or f"runtime returned non-zero exit {result.returncode}",
            returncode=result.returncode,
        )
    if not result.ok:
        raise BakeoffModelFailure(result.stderr_excerpt or "runtime returned no usable response")
    response = (result.response or "").strip()
    if not response:
        raise BakeoffModelFailure("runtime returned empty response")
    mapped_events = map_runtime_tool_calls(
        [call for call in result.tool_calls if isinstance(call, Mapping)]
    )
    return llm_reviewer_dispatch.DispatchResult(
        response_text=response,
        reviewer_model_id=route.reviewer_model_id,
        reviewer_family=route.reviewer_family,
        route_name=route.route_name,
        observed_prompt_tokens=llm_reviewer_dispatch.estimate_tokens(prompt),
        observed_completion_tokens=llm_reviewer_dispatch.estimate_tokens(response),
        observed_cost_usd=0.0,
        usage=usage,
        tool_call_count=max(int(result.tool_calls_total or 0), len(mapped_events)),
        tools_used=tuple(
            str(event.get("tool") or "")
            for event in mapped_events
            if str(event.get("tool") or "").strip()
        ),
        tool_events=mapped_events,
    )


def preflight_subscription_bare_routes(routes: Sequence[llm_reviewer_dispatch.ReviewerRoute]) -> dict[str, Any]:
    """Fail fast on local auth/headroom prerequisites before burning native cells."""
    native_routes = [route for route in routes if _is_subscription_bare_route(route)]
    if not native_routes:
        return {"status": "skipped", "routes": []}
    failures: list[str] = []
    checked: list[str] = []
    for route in native_routes:
        identity = _subscription_identity(route)
        checked.append(route.route_name)
        agent = identity.runtime_agent or ""
        if agent == "claude":
            if not (shutil.which("npx") or shutil.which("claude")):
                failures.append("claude: neither npx nor claude CLI is on PATH")
            if not (Path.home() / ".claude").exists() and not os.environ.get("ANTHROPIC_API_KEY"):
                failures.append("claude: no ~/.claude login state or ANTHROPIC_API_KEY visible")
        elif agent == "codex":
            if not shutil.which("codex"):
                failures.append("codex: codex CLI is not on PATH")
        elif agent == "agy":
            agy_path = shutil.which("agy") or str(Path.home() / ".local/bin/agy")
            if not Path(agy_path).exists():
                failures.append("agy: agy CLI is not on PATH or ~/.local/bin/agy")
        else:
            failures.append(f"{route.route_name}: unsupported runtime agent {agent!r}")

        try:
            from scripts.agent_runtime.usage import has_headroom

            ok, reason = has_headroom(agent, route.reviewer_model_id)
        except Exception as exc:  # pragma: no cover - degraded local preflight only
            failures.append(f"{agent}: headroom check failed: {type(exc).__name__}: {exc}")
        else:
            if not ok:
                failures.append(f"{agent}/{route.reviewer_model_id}: no headroom: {reason}")

    if failures:
        raise BakeoffConfigError("subscription-runtime bare preflight failed: " + "; ".join(failures))
    return {"status": "passed", "routes": checked}


_VERDICT_ALIAS_MAP: dict[str, str] = {
    "VERIFIED_TRUE": "CONFIRMED",
    "VERIFIED_FALSE": "REFUTED_BY_CONTRADICTION",
    "VERIFIED": "CONFIRMED",
    "TRUE": "CONFIRMED",
    "FALSE": "REFUTED_BY_CONTRADICTION",
    "REFUTED": "REFUTED_BY_CONTRADICTION",
    "UNVERIFIED": "UNVERIFIED_INSUFFICIENT_SEARCH",
    "UNATTESTED": "UNATTESTED_AFTER_SEARCH",
    "INSUFFICIENT_SEARCH": "UNVERIFIED_INSUFFICIENT_SEARCH",
}

_GROUNDING_REQUIRED_VERDICTS = frozenset(
    {"CONFIRMED", "REFUTED_BY_CONTRADICTION", "CONTESTED"}
)

_SUBSCRIPTION_TOOLED_JSON_FOOTER = (
    "\n\n### JSON output contract (binding for this bakeoff)\n"
    "Respond with ONE JSON object only — no markdown fences, no prose before or after.\n"
    "Each `fact_checks[]` row MUST use the field name `verdict` (never `status`) with "
    "exactly one of: CONFIRMED | REFUTED_BY_CONTRADICTION | UNATTESTED_AFTER_SEARCH | "
    "CONTESTED | UNVERIFIED_INSUFFICIENT_SEARCH.\n"
    "CONFIRMED / REFUTED_BY_CONTRADICTION / CONTESTED require a nested `grounding` object "
    "with `tool`, `query`, and `evidence_excerpt` (verbatim substring from that tool result).\n"
    "Do NOT use top-level `grounding_excerpt`, `grounding_source`, or `evidence`.\n"
    "\n"
    "Example fact_check row:\n"
    '{"claim": "…", "verdict": "CONFIRMED", "grounding": {"tool": '
    '"mcp__sources__query_wikipedia", "query": "Колядки", "evidence_excerpt": '
    '"Коля́дки — величальні календарно-обрядові пісні зимового циклу"}}\n'
    "\n"
    "### Verdict selection (binding)\n"
    "Use CONFIRMED when retrieved evidence supports the passage claim; "
    "REFUTED_BY_CONTRADICTION when retrieved evidence contradicts it. "
    "Reserve UNATTESTED_AFTER_SEARCH only when you searched but found no evidence "
    "to support or refute the claim — not when you already hold a supporting or "
    "contradicting verbatim excerpt.\n"
    "Hard tool budget: at most 40 tool calls per review; after the cap, stop searching "
    "and score remaining claims with UNVERIFIED_INSUFFICIENT_SEARCH.\n"
    "\n"
    "### Grounding excerpt rule (binding)\n"
    "`evidence_excerpt` MUST be copied character-for-character from the tool result — "
    "no paraphrase, no stitched spans joined by `...`, no case changes. If you cannot "
    "quote a contiguous verbatim substring, use UNATTESTED_AFTER_SEARCH instead of "
    "CONFIRMED or REFUTED_BY_CONTRADICTION.\n"
)


def _admissibly_downgrade(fact_check: Mapping[str, Any]) -> dict[str, Any]:
    """Downgrade a positive verdict to UNVERIFIED for live-admissible scoring.

    Preserves the raw model verdict in ``original_verdict`` and sets
    ``admissibility_downgraded`` so ``_judgment_verdict`` keeps crediting the raw
    judgment in the ``model_judgment`` column while ``live_admissible`` (which reads
    ``verdict``) sees the downgrade. Mirrors the deep-read summary-only downgrade in
    ``llm_reviewer_dispatch.enforce_grounding_against_tool_events`` so both admissibility
    paths behave identically. Idempotent: an already-downgraded row is returned as-is.
    """
    item = dict(fact_check)
    if item.get("admissibility_downgraded") is True:
        return item
    item["original_verdict"] = str(item.get("verdict") or "")
    item["verdict"] = "UNVERIFIED_INSUFFICIENT_SEARCH"
    item["admissibility_downgraded"] = True
    item["grounding"] = None
    return item


def _coerce_claim_aliases(fact_check: Mapping[str, Any]) -> dict[str, Any]:
    """Map frontier claim field aliases onto the bakeoff ``claim`` key."""
    item = dict(fact_check)
    claim = item.get("claim")
    if not isinstance(claim, str) or not claim.strip():
        for key in ("claim_text", "claim_span", "passage_claim", "text"):
            alt = item.get(key)
            if isinstance(alt, str) and alt.strip():
                item["claim"] = alt.strip()
                break
    return item


def _coerce_flat_grounding_fields(fact_check: Mapping[str, Any]) -> dict[str, Any]:
    """Hoist frontier flat grounding aliases into the nested ``grounding`` object."""
    item = _coerce_claim_aliases(fact_check)
    grounding = item.get("grounding")
    excerpt = ""
    if isinstance(grounding, Mapping):
        excerpt = str(grounding.get("evidence_excerpt") or "").strip()
    if not excerpt:
        for key in ("grounding_excerpt", "evidence_excerpt", "evidence", "citation"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                excerpt = value.strip()
                break
    if excerpt:
        rebuilt: dict[str, Any] = dict(grounding) if isinstance(grounding, Mapping) else {}
        rebuilt["evidence_excerpt"] = excerpt
        for key in ("tool", "query"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                rebuilt[key] = value.strip()
        item["grounding"] = rebuilt
    for key in ("grounding_excerpt", "grounding_source", "evidence", "citation"):
        item.pop(key, None)
    return item


def _coerce_fact_check_verdict_aliases(fact_check: Mapping[str, Any]) -> dict[str, Any]:
    """Bakeoff-only verdict normalization for frontier models that alias the contract.

    Maps common alternate field names (`status`) and verdict tokens (`VERIFIED_TRUE`)
    to the bakeoff taxonomy, and hoists flat grounding aliases into the nested
    ``grounding`` object. This is a pure token/shape remap — it never changes the
    verdict a model actually reached. Grounding admissibility (and any downgrade of
    an ungrounded positive verdict) is decided later, in
    ``_normalize_bakeoff_tooled_payload`` and the grounding gate, so the raw model
    judgment stays intact for the ``model_judgment`` scoring column.
    """
    item = _coerce_flat_grounding_fields(fact_check)
    verdict = item.get("verdict")
    if not isinstance(verdict, str) or not verdict.strip():
        for alt_key in ("status", "judgment", "result", "verdict_label"):
            alt_val = item.get(alt_key)
            if isinstance(alt_val, str) and alt_val.strip():
                verdict = alt_val
                break
    if isinstance(verdict, str):
        normalized = verdict.strip().upper().replace("-", "_").replace(" ", "_")
        item["verdict"] = _VERDICT_ALIAS_MAP.get(normalized, verdict.strip())
    return item


def _coerce_payload_fact_check_verdicts(payload: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    coerced: list[dict[str, Any]] = []
    for fact_check in out.get("fact_checks") or []:
        if not isinstance(fact_check, Mapping):
            continue
        coerced.append(_coerce_fact_check_verdict_aliases(fact_check))
    out["fact_checks"] = coerced
    return out


def _subscription_tooled_prompt_supplement(route: llm_reviewer_dispatch.ReviewerRoute) -> str:
    if not _is_subscription_tooled_route(route):
        return ""
    return _SUBSCRIPTION_TOOLED_JSON_FOOTER


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


def _normalize_bakeoff_tooled_payload(
    payload: Mapping[str, Any],
) -> tuple[dict[str, Any], bool]:
    """Best-effort bakeoff-only cleanup so fact-check measurement survives contract noise.

    STRICT grounding (#4761): frontier alias tokens/fields are remapped, but a
    grounding is accepted only when the model itself supplied a usable
    ``(tool, query, evidence_excerpt)`` triple. There is NO repair from captured
    telemetry — the harness never invents the tool/query a model failed to cite, so
    ``live_admissible`` credits only self-grounded verdicts. A positive verdict whose
    grounding is unusable is *admissibly downgraded* (``verdict`` → UNVERIFIED,
    ``original_verdict`` preserved, ``admissibility_downgraded`` set): the raw model
    judgment still scores in ``model_judgment`` via ``_judgment_verdict`` while
    ``live_admissible`` sees the downgrade and the cell stays schema-valid.

    Returns ``(normalized_payload, findings_schema_invalid)``.
    """
    out = dict(payload)
    out = _coerce_payload_fact_check_verdicts(out)
    findings_schema_invalid = False
    kept_findings: list[dict[str, Any]] = []
    for finding in out.get("findings") or []:
        if not isinstance(finding, Mapping):
            findings_schema_invalid = True
            continue
        try:
            qg_schema.validate_grounded_finding(finding, BAKEOFF_POLICY_FAMILY)
        except ValueError:
            findings_schema_invalid = True
            continue
        kept_findings.append(dict(finding))
    out["findings"] = kept_findings

    normalized_fact_checks: list[dict[str, Any]] = []
    for fact_check in out.get("fact_checks") or []:
        if not isinstance(fact_check, Mapping):
            continue
        item = dict(fact_check)
        grounding = item.get("grounding")
        usable_grounding: dict[str, Any] | None = None
        if isinstance(grounding, Mapping):
            normalized = dict(grounding)
            # tool_call_id is advisory (see _grounding_matches_events). Tool-name
            # spelling (sources_* vs mcp__sources__*) is reconciled by the gate's
            # canonical comparison, so no rename here — a one-sided rename would
            # break the opencode case where events keep the bare sources_* form.
            if not str(normalized.get("tool_call_id") or "").strip():
                normalized["tool_call_id"] = "advisory-missing"
            missing_required = any(
                not str(normalized.get(key) or "").strip()
                for key in ("tool", "query", "evidence_excerpt")
            )
            if not missing_required:
                usable_grounding = normalized
        item["grounding"] = usable_grounding
        if usable_grounding is None and item.get("verdict") in _GROUNDING_REQUIRED_VERDICTS:
            item = _admissibly_downgrade(item)
        normalized_fact_checks.append(item)
    out["fact_checks"] = normalized_fact_checks
    return out, findings_schema_invalid


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

    payload = _coerce_payload_fact_check_verdicts(payload)
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
    runs: int = 1,
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
    runs = _validate_run_index(runs)
    if arm not in _ARM_CHOICES:
        raise BakeoffConfigError(f"arm must be one of {list(_ARM_CHOICES)}; got {arm!r}")
    routes = [route_for_matrix_pin(pin, arm=arm) for pin in model_pins]
    # Preflight EVERY pin against the standing routing orders before any cell
    # runs (codex review, PR #4500 finding 2): a subscription-family or qwen
    # pin must fail the whole matrix at config time, not burn N-1 cells first.
    # Defense-in-depth: _invoke_opencode_reviewer re-asserts at the transport,
    # covering injected runners and non-matrix callers.
    from scripts.ai_agent_bridge.routing_guard import assert_model_routing_allowed

    for route in routes:
        if _is_subscription_bare_route(route):
            continue
        assert_model_routing_allowed(route.reviewer_model_id, context="qg_bakeoff matrix pin")
    output_dir.mkdir(parents=True, exist_ok=True)
    run_tooled = arm in (TOOLED_ARM, BOTH_ARM)
    run_bare = arm in (BARE_ARM, BOTH_ARM)
    matrix_runs: list[BakeoffRun] = []
    for run_index in range(1, runs + 1):
        if run_bare and bare_runner is invoke_bakeoff_route_bare:
            preflight_subscription_bare_routes(routes)
        for route in routes:
            for fixture in fixtures:
                if run_tooled:
                    matrix_runs.append(
                        run_one(
                            route,
                            fixture,
                            output_dir=output_dir,
                            runner=runner,
                            force=force,
                            retry_failures=retry_failures,
                            run_index=run_index,
                        )
                    )
                if run_bare:
                    matrix_runs.append(
                        run_one_bare(
                            route,
                            fixture,
                            output_dir=output_dir,
                            runner=bare_runner,
                            force=force,
                            retry_failures=retry_failures,
                            run_index=run_index,
                        )
                    )
    write_scorecard(output_dir / SCORECARD_NAME, _load_all_artifacts(output_dir))
    return matrix_runs


def _is_bakeoff_cell(artifact: Mapping[str, Any]) -> bool:
    """True iff this JSON is a real bakeoff cell artifact, not a foreign file.

    Out-dirs accumulate non-cell JSONs (live trap: ``tier2-canary-verdict.json``
    from the canary checker) — scoring one fabricates an ``unknown`` scorecard
    row with a phantom passage count. Shared predicate for EVERY artifact-load
    path (codex review on #4581 caught the run_matrix sibling of the rescore fix).
    """
    schema = artifact.get("schema_version")
    return isinstance(schema, str) and schema.startswith("qg_bakeoff_run.")


def _load_all_artifacts(output_dir: Path) -> list[dict[str, Any]]:
    """Load every bakeoff CELL artifact JSON in ``output_dir`` (both arms), stable order."""
    artifacts: list[dict[str, Any]] = []
    for path in sorted(output_dir.glob("*.json")):
        try:
            artifact = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not _is_bakeoff_cell(artifact):
            continue
        _assert_artifact_filename_matches_run_index(path, artifact)
        artifacts.append(artifact)
    return artifacts


def _fixture_block(fixture: BakeoffFixture) -> dict[str, Any]:
    return {"slug": fixture.slug, "title": fixture.title, "claim_count": len(fixture.claims)}


def _model_block(
    route: llm_reviewer_dispatch.ReviewerRoute,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    identity = _route_identity(route)
    usage = dispatch.get("usage") if isinstance(dispatch, Mapping) else None
    usage_map = usage if isinstance(usage, Mapping) else {}
    resolved_model = str(
        usage_map.get("resolved_model")
        or usage_map.get("model")
        or identity.resolved_model
        or route.reviewer_model_id
    )
    cli_version = str(usage_map.get("cli_version") or identity.cli_version or "unknown")
    return {
        "pin": route.reviewer_model_id,
        "pin_slug": pin_slug(route.reviewer_model_id),
        "family": route.reviewer_family,
        "route_name": route.route_name,
        "bridge_command": list(route.bridge_command),
        "transport": identity.transport,
        "entrypoint": identity.entrypoint,
        "session_policy": identity.session_policy,
        "measurement_tier": identity.measurement_tier,
        "cli_version": cli_version,
        "pricing_basis": identity.pricing_basis,
        "resolved_model": resolved_model,
    }


def _failure_class(exc: Exception) -> str:
    try:
        from scripts.agent_runtime.errors import AgentStalledError, AgentTimeoutError, RateLimitedError
    except Exception:  # pragma: no cover - import path fallback only
        AgentStalledError = AgentTimeoutError = RateLimitedError = type("_UnavailableRuntimeError", (Exception,), {})
    if isinstance(exc, (BakeoffOpsQuotaError, RateLimitedError)):
        return FAILURE_CLASS_OPS_QUOTA
    if isinstance(
        exc,
        (
            BakeoffTransportError,
            llm_reviewer_dispatch.ReviewerProviderError,
            AgentTimeoutError,
            AgentStalledError,
        ),
    ):
        return FAILURE_CLASS_TRANSPORT
    return FAILURE_CLASS_MODEL_FAILURE


def _timed_out(exc: Exception) -> bool:
    try:
        from scripts.agent_runtime.errors import AgentTimeoutError
    except Exception:  # pragma: no cover - import path fallback only
        AgentTimeoutError = type("_UnavailableRuntimeTimeout", (Exception,), {})
    return bool(getattr(exc, "timed_out", False) or isinstance(exc, AgentTimeoutError))


def _error_artifact(
    route: llm_reviewer_dispatch.ReviewerRoute,
    fixture: BakeoffFixture,
    exc: Exception,
    wall_seconds: float,
    *,
    arm: str,
    run_index: int = 1,
    attempt_count: int = 1,
    transport_retry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a MEASURED error-cell artifact (score = every fixture claim missing).

    A model that cannot produce a valid payload (or a provider that errors out) is a
    per-cell outcome, never a matrix crash. Shared by both arms so the error schema
    stays identical apart from ``arm``.
    """
    failure_class = _failure_class(exc)
    return {
        "schema_version": RUN_SCHEMA_VERSION,
        "arm": arm,
        "run_index": _validate_run_index(run_index),
        "created_at": _now_z(),
        "fixture": _fixture_block(fixture),
        "model": _model_block(route),
        "status": "error",
        "failure_class": failure_class,
        "error": {
            "class": type(exc).__name__,
            "message": str(exc)[:2000],
            "response_head": getattr(exc, "response_head", None),
        },
        "workflow_verdict": "ERROR",
        "attempt_count": attempt_count,
        "timed_out": _timed_out(exc),
        "transport_retry": dict(transport_retry or {"attempted": False, "reason": None}),
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
    run_index: int = 1,
) -> BakeoffRun:
    """Run or resume one model x passage TOOLED bakeoff artifact.

    Belt-and-suspenders (cursor re-review nit): the LIVE default runner is
    guarded here too; injected runners are offline by construction and stay
    guard-free so scripted tests need no env setup.
    """
    if runner is invoke_bakeoff_route:
        require_offline_opt_in()
    run_index = _validate_run_index(run_index)
    artifact_path = _cell_artifact_path(output_dir, route, fixture, TOOLED_ARM, run_index)
    if artifact_path.exists() and not force:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        _assert_artifact_filename_matches_run_index(artifact_path, artifact)
        _assert_resume_transport_matches(artifact, route, artifact_path)
        # retry_failures is a RESUME MODIFIER: missing cells always run (plain
        # resume behavior), completed cells always skip, and error cells re-run
        # only under the flag (codex review of #4463 pinned these semantics).
        if not (retry_failures and artifact.get("status") == "error"):
            return BakeoffRun(artifact_path=artifact_path, artifact=artifact, skipped=True)

    # ``folk`` is the track level; it maps to the seminar policy family in
    # content_surface_gates. There is no literal ``seminar`` level.
    prompt = llm_reviewer.build_reviewer_prompt(BAKEOFF_LEVEL, f"bakeoff-{fixture.slug}", fixture.passage_md)
    prompt += _subscription_tooled_prompt_supplement(route)
    task_id = f"qg-bakeoff-{pin_slug(route.reviewer_model_id)}-{fixture.slug}"
    if run_index > 1:
        task_id = f"{task_id}-r{run_index}"
    started = time.monotonic()
    try:
        gate_result = _invoke_and_gate(route, prompt, task_id, runner)
    except (ValueError, llm_reviewer_dispatch.ReviewerDispatchError) as exc:
        # A model that cannot produce a schema-valid grounded payload (or a
        # provider that errors out) is a MEASURED per-cell outcome, never a
        # matrix crash (first live run: gemma findings flunked validate_finding
        # and killed all 24 cells). Score = every fixture claim missing.
        wall_seconds = round(time.monotonic() - started, 3)
        artifact = _error_artifact(route, fixture, exc, wall_seconds, arm=TOOLED_ARM, run_index=run_index)
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
    artifact = serialize_qg_run_v2(
        dispatch,
        gate_result["payload"],
        {
            "schema_version": RUN_SCHEMA_VERSION,
            "arm": TOOLED_ARM,
            "run_index": run_index,
            "created_at": _now_z(),
            "fixture": _fixture_block(fixture),
            "model": _model_block(route, dispatch),
            "status": gate_result["status"],
            "workflow_verdict": gate_result["workflow_verdict"],
            "findings_schema_invalid": bool(gate_result.get("findings_schema_invalid")),
            "response_parse_lenient": bool(gate_result.get("response_parse_lenient")),
            "attempt_count": gate_result["attempt_count"],
            "timed_out": False,
            "transport_retry": {"attempted": False, "reason": None},
            "gate_outcomes": gate_outcomes,
            # Raw model response is persisted alongside dispatch.tool_events so a
            # future normalization/scoring change can be replayed OFFLINE from disk
            # (no model re-run, no subscription quota burned). See docs note in #4761.
            "raw_response": gate_result.get("raw_response_text"),
            "score": score,
            "tool_call_count": int(dispatch.get("tool_call_count") or 0),
            "wall_seconds": wall_seconds,
        },
    )
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return BakeoffRun(artifact_path=artifact_path, artifact=artifact)


def _bare_artifact_path(
    output_dir: Path,
    route: llm_reviewer_dispatch.ReviewerRoute,
    fixture: BakeoffFixture,
    run_index: int = 1,
) -> Path:
    return _cell_artifact_path(output_dir, route, fixture, BARE_ARM, run_index)


def _assert_resume_transport_matches(
    artifact: Mapping[str, Any],
    route: llm_reviewer_dispatch.ReviewerRoute,
    artifact_path: Path,
) -> None:
    artifact_transport = _artifact_transport(artifact)
    route_transport = _route_transport(route)
    if artifact_transport != route_transport:
        raise BakeoffConfigError(
            f"{artifact_path}: existing artifact transport={artifact_transport!r} "
            f"does not match route transport={route_transport!r}; use --force with a clean "
            "artifact path instead of silently overwriting a different transport"
        )


def _invoke_bare_with_transport_retry(
    route: llm_reviewer_dispatch.ReviewerRoute,
    prompt: str,
    task_id: str,
    runner: BareRunner,
) -> tuple[llm_reviewer_dispatch.DispatchResult, int, dict[str, Any]]:
    retry_meta = {"attempted": False, "reason": None}
    try:
        return _coerce_dispatch_result(runner(route, prompt, task_id), route, prompt), 1, retry_meta
    except Exception as exc:
        if _failure_class(exc) != FAILURE_CLASS_TRANSPORT:
            _attach_attempt_metadata(exc, attempt_count=1, transport_retry=retry_meta)
            raise
        retry_meta = {"attempted": True, "reason": str(exc)[:500]}
    try:
        return _coerce_dispatch_result(runner(route, prompt, task_id), route, prompt), 2, retry_meta
    except Exception as exc:
        _attach_attempt_metadata(exc, attempt_count=2, transport_retry=retry_meta)
        raise


def _attach_attempt_metadata(exc: Exception, *, attempt_count: int, transport_retry: Mapping[str, Any]) -> None:
    with contextlib.suppress(Exception):
        exc.attempt_count = attempt_count  # type: ignore[attr-defined]
    with contextlib.suppress(Exception):
        exc.transport_retry = dict(transport_retry)  # type: ignore[attr-defined]


def run_one_bare(
    route: llm_reviewer_dispatch.ReviewerRoute,
    fixture: BakeoffFixture,
    *,
    output_dir: Path,
    runner: BareRunner = invoke_bakeoff_route_bare,
    force: bool = False,
    retry_failures: bool = False,
    run_index: int = 1,
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
    run_index = _validate_run_index(run_index)
    artifact_path = _bare_artifact_path(output_dir, route, fixture, run_index)
    if artifact_path.exists() and not force:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        _assert_artifact_filename_matches_run_index(artifact_path, artifact)
        _assert_resume_transport_matches(artifact, route, artifact_path)
        if not (retry_failures and artifact.get("status") == "error"):
            return BakeoffRun(artifact_path=artifact_path, artifact=artifact, skipped=True)

    prompt = build_bare_factcheck_prompt(fixture.title, fixture.passage_md)
    task_id = f"qg-bakeoff-bare-{pin_slug(route.reviewer_model_id)}-{fixture.slug}"
    if run_index > 1:
        task_id = f"{task_id}-r{run_index}"
    started = time.monotonic()
    attempt_count = 1
    transport_retry = {"attempted": False, "reason": None}
    try:
        result, attempt_count, transport_retry = _invoke_bare_with_transport_retry(route, prompt, task_id, runner)
        payload, response_parse_lenient, findings_schema_invalid = _parse_bare_payload(result.response_text)
    except (ValueError, llm_reviewer_dispatch.ReviewerDispatchError) as exc:
        wall_seconds = round(time.monotonic() - started, 3)
        artifact = _error_artifact(
            route,
            fixture,
            exc,
            wall_seconds,
            arm=BARE_ARM,
            run_index=run_index,
            attempt_count=int(getattr(exc, "attempt_count", attempt_count) or attempt_count),
            transport_retry=getattr(exc, "transport_retry", transport_retry),
        )
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
        "run_index": run_index,
        "created_at": _now_z(),
        "fixture": _fixture_block(fixture),
        "model": _model_block(route, dispatch),
        "status": "ran",
        "workflow_verdict": "BARE",
        "findings_schema_invalid": findings_schema_invalid,
        "response_parse_lenient": response_parse_lenient,
        "attempt_count": attempt_count,
        "timed_out": False,
        "transport_retry": transport_retry,
        "dispatch": dispatch,
        "gate_outcomes": {},
        "payload": payload,
        "raw_response": result.response_text,
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
        # STRICT live-admissible (#4761): a positive verdict whose grounding the
        # gate tagged inadmissible (present but not backed by a matching tool
        # event) earns NO live credit. Its raw judgment is still scored in
        # model_judgment via judgment_verdict. Verdicts downgraded upstream
        # (admissibility_downgraded) already carry UNVERIFIED in `verdict`, so
        # this only handles the gate-tag path.
        live_scoring_verdict = live_verdict
        if (
            row.get("grounding_admissible") is False
            and live_verdict.strip().upper() in _GROUNDING_REQUIRED_VERDICTS
        ):
            live_scoring_verdict = "UNVERIFIED_INSUFFICIENT_SEARCH"
        model_points = qg_factcheck_scoring.score_verdict(judgment_verdict, claim_is_true=claim.is_true)
        live_points = qg_factcheck_scoring.score_verdict(live_scoring_verdict, claim_is_true=claim.is_true)
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
                "live_admissible_neutralized": live_scoring_verdict != live_verdict,
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


def write_scorecard(
    path: Path,
    artifacts: Sequence[Mapping[str, Any]],
    *,
    title: str = "QG Bakeoff Scorecard",
    banner_lines: Sequence[str] = (),
) -> None:
    """Write a markdown scorecard for the current artifact set."""
    regular_artifacts = [a for a in artifacts if not _is_subscription_runtime_artifact(a)]
    subscription_artifacts = [a for a in artifacts if _is_subscription_runtime_artifact(a)]
    judgment_artifacts = [a for a in regular_artifacts if not _is_ops_quota_artifact(a)]
    all_judgment_artifacts = [a for a in artifacts if not _is_ops_quota_artifact(a)]
    multi_run = _max_run_index(artifacts) > 1
    lines = [
        f"# {title}",
        "",
        f"Generated: {_now_z()}",
        "",
    ]
    for banner in banner_lines:
        lines.extend([banner, ""])
    lines.extend(
        [
            "Fractions are exact. `low-N` marks denominators below 10.",
            "",
        ]
    )
    lines.extend(_runs_table_section("Runs", regular_artifacts, show_run=multi_run))
    lines.extend(_ops_quota_section(regular_artifacts))
    lines.extend(_totals_and_lift_section("With Anchor", judgment_artifacts))
    lines.extend(
        _totals_and_lift_section(
            "Without Anchor",
            [a for a in judgment_artifacts if _fixture_slug(a) != ANCHOR_SLUG],
        )
    )
    if multi_run:
        lines.extend(_run_variance_section(all_judgment_artifacts, scheduled_runs=_max_run_index(artifacts)))
        lines.extend(_domain_totals_section(all_judgment_artifacts))
    if subscription_artifacts:
        lines.extend(
            [
                "",
                "## Subscription Runtime Rows",
                "",
                SUBSCRIPTION_BARE_BANNER,
                "",
                SUBSCRIPTION_TOOLED_BANNER,
                "",
            ]
        )
        lines.extend(_runs_table(subscription_artifacts, show_run=multi_run))
        lines.extend(_ops_quota_section(subscription_artifacts))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _runs_table_section(title: str, artifacts: Sequence[Mapping[str, Any]], *, show_run: bool = False) -> list[str]:
    return ["", f"## {title}", "", *_runs_table(artifacts, show_run=show_run)]


def _runs_table(artifacts: Sequence[Mapping[str, Any]], *, show_run: bool = False) -> list[str]:
    if show_run:
        lines = [
            "| model | transport | entrypoint | passage | arm | run | status | failure_class | parse_lenient | model judgment | live admissible | missing | U honesty | M alignment | true unsupported | invalid | inadmissible | tools | wall_s |",
            "| --- | --- | --- | --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    else:
        lines = [
            "| model | transport | entrypoint | passage | arm | status | failure_class | parse_lenient | model judgment | live admissible | missing | U honesty | M alignment | true unsupported | invalid | inadmissible | tools | wall_s |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    if not artifacts:
        if show_run:
            lines.append("| n/a | n/a | n/a | n/a | n/a | 0 | n/a | n/a | n/a | 0 | 0 | 0 | 0/0 low-N | 0/0 low-N | 0/0 low-N | 0 | 0 | 0 | 0 |")
        else:
            lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 0 | 0/0 low-N | 0/0 low-N | 0/0 low-N | 0 | 0 | 0 | 0 |")
        return lines
    for artifact in sorted(artifacts, key=_artifact_sort_key):
        score = _score(artifact)
        fractions = score.get("fractions", {})
        values = {
            "model": _model_label(artifact),
            "transport": _artifact_transport(artifact),
            "entrypoint": _artifact_entrypoint(artifact),
            "passage": _fixture_slug(artifact),
            "arm": _artifact_arm(artifact),
            "run": _artifact_run_index(artifact),
            "status": artifact.get("status", "unknown"),
            "failure_class": artifact.get("failure_class") or "n/a",
            "parse_lenient": bool(artifact.get("response_parse_lenient")),
            "model_score": score.get("model_judgment_score", 0),
            "live_score": score.get("live_admissible_score", 0),
            "missing": score.get("missing_claims", 0),
            "u": _fraction_label(fractions.get("class_u_honesty")),
            "m": _fraction_label(fractions.get("class_m_alignment")),
            "true_bad": _fraction_label(fractions.get("false_unsupported_on_true")),
            "invalid": score.get("invalid_fact_checks", 0),
            "inadmissible": score.get("inadmissible_positive_verdicts", 0),
            "tools": artifact.get("tool_call_count", 0),
            "wall": artifact.get("wall_seconds", 0),
        }
        if show_run:
            lines.append(
                "| {model} | {transport} | {entrypoint} | {passage} | {arm} | {run} | {status} | {failure_class} | {parse_lenient} | {model_score} | {live_score} | {missing} | {u} | {m} | {true_bad} | {invalid} | {inadmissible} | {tools} | {wall} |".format(
                    **values
                )
            )
        else:
            lines.append(
                "| {model} | {transport} | {entrypoint} | {passage} | {arm} | {status} | {failure_class} | {parse_lenient} | {model_score} | {live_score} | {missing} | {u} | {m} | {true_bad} | {invalid} | {inadmissible} | {tools} | {wall} |".format(
                    **values
                )
            )
    return lines


def _ops_quota_section(artifacts: Sequence[Mapping[str, Any]]) -> list[str]:
    ops = [artifact for artifact in artifacts if _is_ops_quota_artifact(artifact)]
    if not ops:
        return []
    lines = [
        "",
        "## Ops/Quota Excluded Cells",
        "",
        "| model | transport | entrypoint | passage | arm | message |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for artifact in sorted(ops, key=_artifact_sort_key):
        error = artifact.get("error")
        message = ""
        if isinstance(error, Mapping):
            message = str(error.get("message") or "")[:300].replace("\n", " ")
        lines.append(
            "| {model} | {transport} | {entrypoint} | {passage} | {arm} | {message} |".format(
                model=_model_label(artifact),
                transport=_artifact_transport(artifact),
                entrypoint=_artifact_entrypoint(artifact),
                passage=_fixture_slug(artifact),
                arm=_artifact_arm(artifact),
                message=message or "n/a",
            )
        )
    return lines


def default_output_dir(day: date | None = None, *, multi_run: bool = False) -> Path:
    effective = day or datetime.now(UTC).date()
    suffix = "-qg-bakeoff-multirun" if multi_run else "-qg-bakeoff"
    return DEFAULT_OUTPUT_ROOT / f"{effective.isoformat()}{suffix}"


def model_pins_from_args(values: Sequence[str] | None) -> list[str]:
    """Parse ``--models`` values or fail closed on unresolved default slots."""
    if values:
        pins: list[str] = []
        for value in values:
            pins.extend(piece.strip() for piece in value.split(",") if piece.strip())
        if not pins:
            raise BakeoffConfigError("--models was provided but no model pins were parsed")
        # Fail fast on malformed pins (live burn 2026-07-05: a space-separated
        # --models string parsed as ONE mega-pin and ran 4 garbage cells
        # instead of erroring). Pins are comma-separated; whitespace inside a
        # pin is always a caller mistake.
        malformed = [pin for pin in pins if any(ch.isspace() for ch in pin)]
        if malformed:
            raise BakeoffConfigError(
                f"model pins must not contain whitespace (use commas to separate): {malformed!r}"
            )
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


def _artifact_arm_from_path(path: Path, artifact: Mapping[str, Any]) -> str:
    """Resolve arm from artifact field or legacy filename convention."""
    arm = artifact.get("arm")
    if isinstance(arm, str) and arm in _ARM_CHOICES:
        return arm
    return BARE_ARM if "__bare" in path.stem else TOOLED_ARM


def _strict_regate_payload(
    payload: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> llm_reviewer_dispatch.GroundingGateResult:
    """Re-run the STRICT grounding gate offline from a stored payload + dispatch."""
    return llm_reviewer_dispatch.enforce_grounding_against_tool_events(
        payload,
        dispatch,
        policy_family=BAKEOFF_POLICY_FAMILY,
    )


def regate_one_artifact(
    artifact: Mapping[str, Any],
    fixture: BakeoffFixture,
    arm: str,
) -> dict[str, Any]:
    """Apply STRICT offline regate + score to one in-memory bakeoff cell.

    Tooled cells re-run ``enforce_grounding_against_tool_events`` against stored
    ``dispatch.tool_events``, persist the gated payload (including
    ``grounding_admissible`` tags), then score. Bare cells only re-score — they
    carry no grounding telemetry and are unaffected by STRICT semantics.
    """
    out = dict(artifact)
    payload = dict(out.get("payload") or {})
    dispatch = out.get("dispatch") if isinstance(out.get("dispatch"), Mapping) else {}

    if arm == TOOLED_ARM:
        gate = _strict_regate_payload(payload, dispatch)
        payload = gate.payload
        out["payload"] = payload
        gate_outcomes = dict(out.get("gate_outcomes") or {})
        gate_outcomes["grounding"] = {
            "ungrounded_findings": gate.ungrounded_findings,
            "required_ungrounded_findings": gate.required_ungrounded_findings,
            "invalid_fact_checks": gate.invalid_fact_checks,
            "inadmissible_positive_verdicts": gate.inadmissible_positive_verdicts,
        }
        gate_outcomes["grounding_strict"] = True
        out["gate_outcomes"] = gate_outcomes
        score = score_payload(payload, fixture)
        score["invalid_fact_checks"] = gate.invalid_fact_checks
        score["inadmissible_positive_verdicts"] = gate.inadmissible_positive_verdicts
    else:
        score = score_payload(payload, fixture)
        score["invalid_fact_checks"] = 0
        score["inadmissible_positive_verdicts"] = 0

    out["score"] = score
    out["arm"] = arm
    out["grounding_strict"] = True
    out["score_semantics"] = GROUNDING_STRICT_SCORE_SEMANTICS
    out["regated_at"] = _now_z()
    return out


def _offline_rewrite_artifacts(
    output_dir: Path,
    fixtures_dir: Path,
    *,
    rewrite: Callable[[dict[str, Any], BakeoffFixture, str], dict[str, Any]],
    scorecard_name: str,
    scorecard_title: str,
    scorecard_banner: Sequence[str] = (),
    unsafe_allow_frozen: bool = False,
    manifest_path: Path = BENCHMARK_V1_MANIFEST,
) -> int:
    """Shared iterator for offline ``--rescore`` / ``--regate`` artifact rewrites."""
    if not unsafe_allow_frozen:
        _refuse_frozen_reference_offline_rewrite(output_dir, manifest_path)
    fixtures = {f.slug: f for f in load_fixtures(fixtures_dir)}
    artifacts: list[dict[str, Any]] = []
    count = 0
    for path in sorted(output_dir.glob("*.json")):
        artifact = json.loads(path.read_text(encoding="utf-8"))
        if not _is_bakeoff_cell(artifact):
            continue
        _assert_artifact_filename_matches_run_index(path, artifact)
        arm = _artifact_arm_from_path(path, artifact)
        slug = (artifact.get("fixture") or {}).get("slug")
        fixture = fixtures.get(slug) if isinstance(slug, str) else None
        if fixture is None:
            artifacts.append(artifact)
            continue
        updated = rewrite(artifact, fixture, arm)
        path.write_text(
            json.dumps(updated, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        artifacts.append(updated)
        count += 1
    write_scorecard(
        output_dir / scorecard_name,
        artifacts,
        title=scorecard_title,
        banner_lines=scorecard_banner,
    )
    return count


def rescore_artifacts(
    output_dir: Path,
    fixtures_dir: Path = FIXTURE_DIR,
    *,
    unsafe_allow_frozen: bool = False,
    manifest_path: Path = BENCHMARK_V1_MANIFEST,
) -> int:
    """Recompute scores for existing artifacts from their STORED payloads.

    Zero model invocations — pure offline rescoring, for matcher/scoring
    changes (e.g. the containment matcher). Does NOT re-run the grounding
    gate; use ``regate_artifacts`` when ``live_admissible`` semantics change.
    Rewrites each artifact's score block and ``SCORECARD.md``.
    """

    def _rescore_one(artifact: dict[str, Any], fixture: BakeoffFixture, arm: str) -> dict[str, Any]:
        out = dict(artifact)
        out["arm"] = arm
        score = score_payload(out.get("payload") or {}, fixture)
        grounding = (out.get("gate_outcomes") or {}).get("grounding") or {}
        score["invalid_fact_checks"] = int(grounding.get("invalid_fact_checks") or 0)
        score["inadmissible_positive_verdicts"] = int(grounding.get("inadmissible_positive_verdicts") or 0)
        out["score"] = score
        out["rescored_at"] = _now_z()
        return out

    return _offline_rewrite_artifacts(
        output_dir,
        fixtures_dir,
        rewrite=_rescore_one,
        scorecard_name=SCORECARD_NAME,
        scorecard_title="QG Bakeoff Scorecard",
        unsafe_allow_frozen=unsafe_allow_frozen,
        manifest_path=manifest_path,
    )


def regate_artifacts(
    output_dir: Path,
    fixtures_dir: Path = FIXTURE_DIR,
    *,
    unsafe_allow_frozen: bool = False,
    manifest_path: Path = BENCHMARK_V1_MANIFEST,
) -> int:
    """Re-run STRICT grounding + score offline from stored payloads and tool_events.

    Zero model invocations. Tooled cells re-apply ``enforce_grounding_against_tool_events``
    so ``live_admissible`` reflects STRICT semantics; bare cells are re-scored only.
    Tags each artifact with ``grounding_strict`` / ``score_semantics`` and writes
    ``SCORECARD-STRICT.md`` (leaves legacy ``SCORECARD.md`` untouched unless you
    also run ``--rescore``).
    """
    return _offline_rewrite_artifacts(
        output_dir,
        fixtures_dir,
        rewrite=regate_one_artifact,
        scorecard_name=SCORECARD_STRICT_NAME,
        scorecard_title="QG Bakeoff Scorecard (STRICT grounding)",
        scorecard_banner=(_GROUNDING_STRICT_BANNER,),
        unsafe_allow_frozen=unsafe_allow_frozen,
        manifest_path=manifest_path,
    )


def _refuse_frozen_reference_offline_rewrite(output_dir: Path, manifest_path: Path) -> None:
    if not manifest_path.exists():
        return
    scorecard_path = output_dir / SCORECARD_NAME
    if not scorecard_path.exists():
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BakeoffConfigError(f"{manifest_path}: invalid benchmark manifest JSON: {exc}") from exc
    if not isinstance(manifest, Mapping):
        raise BakeoffConfigError(f"{manifest_path}: benchmark manifest must be a JSON object")
    reference = manifest.get("reference_result")
    if not isinstance(reference, Mapping):
        return
    expected_sha = reference.get("sha256")
    if not isinstance(expected_sha, str) or not expected_sha:
        return
    if _sha256_file(scorecard_path) != expected_sha:
        return
    reference_path = reference.get("path") or SCORECARD_NAME
    raise BakeoffConfigError(
        f"{output_dir}: refuses to rewrite frozen benchmark reference artifacts because "
        f"{scorecard_path.name} matches {manifest_path} reference_result ({reference_path}); "
        "copy the directory for explicit re-analysis or pass --unsafe-allow-frozen"
    )


def _refuse_frozen_reference_rescore(output_dir: Path, manifest_path: Path) -> None:
    """Backward-compatible alias for frozen-reference guard."""
    _refuse_frozen_reference_offline_rewrite(output_dir, manifest_path)


def emit_lm_eval_results_from_dir(output_dir: Path, emit_dir: Path) -> list[Path]:
    """Emit lang-uk/lm_eval-shaped result files from artifacts already on disk."""
    return emit_lm_eval_results(_load_all_artifacts(output_dir), emit_dir)


def emit_lm_eval_results(artifacts: Sequence[Mapping[str, Any]], emit_dir: Path) -> list[Path]:
    """Write one ``results_<created_at>.json`` file per measured model identity."""
    emit_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for artifact in artifacts:
        if _is_ops_quota_artifact(artifact):
            continue
        grouped[_model_key(artifact)].append(artifact)

    pin_counts: dict[str, int] = defaultdict(int)
    for pin, _transport, _entrypoint in grouped:
        pin_counts[pin] += 1

    written: list[Path] = []
    for model_key, model_artifacts in sorted(grouped.items()):
        payload = _lm_eval_payload_for_model(model_key, model_artifacts)
        stamp = _lm_eval_filename_stamp(model_artifacts)
        model_dir = emit_dir / _lm_eval_model_dir_name(
            model_key,
            duplicate_pin=pin_counts[model_key[0]] > 1,
        )
        model_dir.mkdir(parents=True, exist_ok=True)
        path = model_dir / f"{LM_EVAL_RESULTS_PREFIX}{stamp}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return written


def _lm_eval_payload_for_model(
    model_key: tuple[str, str, str],
    artifacts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    pin, transport, entrypoint = model_key
    totals = _aggregate_by_model_arm(artifacts)
    available_arms = sorted({arm for key, arm in totals if key == model_key})
    primary_arm = (
        TOOLED_ARM
        if (model_key, TOOLED_ARM) in totals
        else (available_arms[0] if available_arms else TOOLED_ARM)
    )
    row = totals.get((model_key, primary_arm), _empty_total_row())
    primary_artifacts = [
        artifact
        for artifact in artifacts
        if _model_key(artifact) == model_key and _artifact_arm(artifact) == primary_arm
    ]
    partial_reasons = _partial_reasons(primary_artifacts)
    task_meta = _lm_eval_task_meta(
        model_key,
        primary_arm,
        row,
        available_arms=available_arms,
        partial_reasons=partial_reasons,
    )
    results: dict[str, dict[str, Any]] = {
        LM_EVAL_TASK_MODEL_JUDGMENT: {
            "score": _row_numeric_metric(row, "model_judgment_score"),
            "qg_meta": task_meta | {"metric": "model_judgment_score"},
        },
        LM_EVAL_TASK_U_HONESTY: {
            "score": _row_fraction_metric(row, "class_u"),
            "qg_meta": task_meta
            | {
                "metric": "class_u_honesty",
                "fraction": _row_fraction_meta(row, "class_u"),
            },
        },
        LM_EVAL_TASK_M_ALIGNMENT: {
            "score": _row_fraction_metric(row, "class_m"),
            "qg_meta": task_meta
            | {
                "metric": "class_m_alignment",
                "fraction": _row_fraction_meta(row, "class_m"),
            },
        },
    }
    lift = _lm_eval_harness_lift_for_model(model_key, artifacts)
    if lift is not None:
        results[LM_EVAL_TASK_HARNESS_LIFT] = {
            "score": lift["score"],
            "qg_meta": {
                "metric": "harness_lift",
                "arm": BOTH_ARM,
                "available_arms": available_arms,
                "primary_arm": TOOLED_ARM,
                "comparison_arm": BARE_ARM,
                "runs": lift["runs"],
                "run_indices": lift["run_indices"],
                "paired_passages": lift["paired_passages"],
                "low_n": lift["paired_passages"] < 10,
                "partial": bool(lift["partial_reasons"]),
                "partial_reasons": lift["partial_reasons"],
                "transport": transport,
                "entrypoint": entrypoint,
                "model_pin": pin,
                "anchor_included": True,
            },
        }
    return {
        "config_general": {"model_name": pin},
        "results": results,
        "qg_meta": {
            "schema_version": RUN_SCHEMA_VERSION,
            "source": "qg_bakeoff",
            "model_pin": pin,
            "transport": transport,
            "entrypoint": entrypoint,
            "available_arms": available_arms,
            "created_at": _lm_eval_filename_stamp(artifacts),
            "partial": bool(_partial_reasons(artifacts)),
        },
    }


def _lm_eval_model_dir_name(model_key: tuple[str, str, str], *, duplicate_pin: bool = False) -> str:
    pin, transport, entrypoint = model_key
    if duplicate_pin:
        return f"{pin_slug(pin)}__{pin_slug(transport)}__{pin_slug(entrypoint)}"
    return pin_slug(pin)


def _lm_eval_filename_stamp(artifacts: Sequence[Mapping[str, Any]]) -> str:
    stamps = [
        str(artifact.get("created_at")).strip()
        for artifact in artifacts
        if isinstance(artifact.get("created_at"), str) and str(artifact.get("created_at")).strip()
    ]
    return max(stamps) if stamps else "unknown"


def _lm_eval_task_meta(
    model_key: tuple[str, str, str],
    arm: str,
    row: Mapping[str, Any],
    *,
    available_arms: Sequence[str],
    partial_reasons: Sequence[str],
) -> dict[str, Any]:
    pin, transport, entrypoint = model_key
    runs = int(row.get("runs") or 1)
    run_indices = list(row.get("run_indices") or range(1, runs + 1))
    passages = row.get("passages_per_run") if row.get("multi_run") else [int(row.get("passages") or 0)]
    return {
        "arm": arm,
        "available_arms": list(available_arms),
        "runs": runs,
        "run_indices": run_indices,
        "passages_per_run": passages,
        "low_n": _row_any_low_n(row),
        "partial": bool(partial_reasons),
        "partial_reasons": list(partial_reasons),
        "transport": transport,
        "entrypoint": entrypoint,
        "model_pin": pin,
        "anchor_included": True,
    }


def _row_numeric_metric(row: Mapping[str, Any], key: str) -> float:
    value = row.get(key)
    if isinstance(value, Mapping):
        return float(value.get("mean") or 0.0)
    return float(value or 0.0)


def _row_fraction_metric(row: Mapping[str, Any], prefix: str) -> float:
    if row.get("multi_run"):
        value = row.get(f"{prefix}_honesty" if prefix == "class_u" else f"{prefix}_alignment")
        return float(value.get("mean") or 0.0) if isinstance(value, Mapping) else 0.0
    denominator = int(row.get(f"{prefix}_total") or 0)
    if denominator <= 0:
        return 0.0
    return int(row.get(f"{prefix}_good") or 0) / denominator


def _row_fraction_meta(row: Mapping[str, Any], prefix: str) -> dict[str, Any]:
    if row.get("multi_run"):
        value = row.get(f"{prefix}_honesty" if prefix == "class_u" else f"{prefix}_alignment")
        if isinstance(value, Mapping):
            return {
                "denominators": list(value.get("denominators") or []),
                "low_n": bool(value.get("low_n")),
            }
        return {"denominators": [], "low_n": True}
    numerator = int(row.get(f"{prefix}_good") or 0)
    denominator = int(row.get(f"{prefix}_total") or 0)
    return {
        "numerator": numerator,
        "denominator": denominator,
        "text": f"{numerator}/{denominator}",
        "low_n": denominator < 10,
    }


def _row_any_low_n(row: Mapping[str, Any]) -> bool:
    if row.get("multi_run"):
        return any(
            bool(value.get("low_n"))
            for key in ("class_u_honesty", "class_m_alignment", "false_unsupported_on_true")
            if isinstance((value := row.get(key)), Mapping)
        )
    return any(int(row.get(key) or 0) < 10 for key in ("class_u_total", "class_m_total", "true_total"))


def _partial_reasons(artifacts: Sequence[Mapping[str, Any]]) -> list[str]:
    reasons: set[str] = set()
    for artifact in artifacts:
        if "created_at" not in artifact:
            reasons.add("missing_created_at")
        if "arm" not in artifact:
            reasons.add("missing_arm")
        if "run_index" not in artifact:
            reasons.add("missing_run_index")
        if not isinstance(artifact.get("fixture"), Mapping):
            reasons.add("missing_fixture")
        model = artifact.get("model")
        if not isinstance(model, Mapping):
            reasons.add("missing_model")
        else:
            if not isinstance(model.get("pin"), str):
                reasons.add("missing_model_pin")
            if not isinstance(model.get("transport"), str):
                reasons.add("missing_transport")
            if not isinstance(model.get("entrypoint"), str):
                reasons.add("missing_entrypoint")
        score = artifact.get("score")
        if not isinstance(score, Mapping):
            reasons.add("missing_score")
            continue
        for key in ("model_judgment_score", "fractions"):
            if key not in score:
                reasons.add(f"missing_score_{key}")
        fractions = score.get("fractions")
        if not isinstance(fractions, Mapping):
            reasons.add("missing_score_fractions")
            continue
        for key in ("class_u_honesty", "class_m_alignment"):
            if key not in fractions:
                reasons.add(f"missing_fraction_{key}")
    return sorted(reasons)


def _lm_eval_harness_lift_for_model(
    model_key: tuple[str, str, str],
    artifacts: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    cells: dict[str, dict[str, dict[int, Mapping[str, Any]]]] = defaultdict(lambda: defaultdict(dict))
    for artifact in artifacts:
        if _is_ops_quota_artifact(artifact) or _model_key(artifact) != model_key:
            continue
        cells[_fixture_slug(artifact)][_artifact_arm(artifact)][_artifact_run_index(artifact)] = artifact
    paired = sorted(slug for slug, arms in cells.items() if TOOLED_ARM in arms and BARE_ARM in arms)
    if not paired:
        return None
    paired_artifacts = [
        artifact
        for slug in paired
        for arm in (TOOLED_ARM, BARE_ARM)
        for artifact in cells[slug][arm].values()
    ]
    partial_reasons = _partial_reasons(paired_artifacts)
    scheduled_runs = _max_run_index(
        [artifact for arms in cells.values() for runs in arms.values() for artifact in runs.values()]
    )
    if scheduled_runs > 1:
        lifts = [
            _arm_mean_for_fixture(cells[slug][TOOLED_ARM], "model_judgment_score")
            - _arm_mean_for_fixture(cells[slug][BARE_ARM], "model_judgment_score")
            for slug in paired
        ]
        run_indices = sorted(
            {run for slug in paired for arm in (TOOLED_ARM, BARE_ARM) for run in cells[slug][arm]}
        )
        return {
            "score": _mean(lifts),
            "runs": max((len(cells[slug][arm]) for slug in paired for arm in (TOOLED_ARM, BARE_ARM)), default=1),
            "run_indices": run_indices,
            "paired_passages": len(paired),
            "partial_reasons": partial_reasons,
        }
    tooled = sum(
        int(_score(cells[slug][TOOLED_ARM][1]).get("model_judgment_score") or 0)
        for slug in paired
        if 1 in cells[slug][TOOLED_ARM]
    )
    bare = sum(
        int(_score(cells[slug][BARE_ARM][1]).get("model_judgment_score") or 0)
        for slug in paired
        if 1 in cells[slug][BARE_ARM]
    )
    return {
        "score": float(tooled - bare),
        "runs": 1,
        "run_indices": [1],
        "paired_passages": len(paired),
        "partial_reasons": partial_reasons,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures-dir", type=Path, default=FIXTURE_DIR)
    parser.add_argument("--fixture", action="append", dest="fixtures", help="Fixture slug; repeatable")
    parser.add_argument(
        "--models",
        action="append",
        help=(
            "Comma-separated or repeated model pins. opencode provider/model pins "
            "(including deepseek-direct/... and OpenRouter baselines) work for tooled/bare; "
            "subscription native pins (claude-opus-4-8,gpt-5.5,gemini-3.1-pro-high) are --arm bare only. "
            "LU_ROUTING_GUARD_OVERRIDE=1 is invalid for published scorecards."
        ),
    )
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
    parser.add_argument("--runs", type=int, default=1, help="Repeat every requested cell N times (default: 1)")
    parser.add_argument(
        "--rescore",
        action="store_true",
        help="Recompute scores for EXISTING artifacts from stored payloads (no model calls)",
    )
    parser.add_argument(
        "--regate",
        action="store_true",
        help=(
            "Offline STRICT grounding: re-run the grounding gate from stored payload + "
            "dispatch.tool_events, then score (no model calls). Tags artifacts "
            f"``{GROUNDING_STRICT_SCORE_SEMANTICS}`` and writes {SCORECARD_STRICT_NAME}."
        ),
    )
    parser.add_argument(
        "--unsafe-allow-frozen",
        action="store_true",
        help=(
            "Allow --rescore or --regate to rewrite an out-dir whose SCORECARD.md matches "
            "the benchmark-v1 frozen reference. Use only on explicit re-analysis copies."
        ),
    )
    parser.add_argument(
        "--emit-lm-eval",
        type=Path,
        default=None,
        metavar="DIR",
        help="Write lang-uk/lm_eval-shaped results_<created_at>.json files from artifacts on disk",
    )
    args = parser.parse_args(argv)

    try:
        if args.rescore and args.regate:
            raise BakeoffConfigError("--rescore and --regate are mutually exclusive")
        if args.rescore:
            output_dir = args.out_dir or default_output_dir()
            n = rescore_artifacts(output_dir, args.fixtures_dir, unsafe_allow_frozen=args.unsafe_allow_frozen)
            emitted = emit_lm_eval_results_from_dir(output_dir, args.emit_lm_eval) if args.emit_lm_eval else []
            print(f"rescored {n} artifacts under {output_dir}")
            print(f"scorecard: {output_dir / SCORECARD_NAME}")
            if args.emit_lm_eval:
                print(f"lm-eval results: {len(emitted)} files under {args.emit_lm_eval}")
            return 0
        if args.regate:
            output_dir = args.out_dir or default_output_dir()
            n = regate_artifacts(output_dir, args.fixtures_dir, unsafe_allow_frozen=args.unsafe_allow_frozen)
            emitted = emit_lm_eval_results_from_dir(output_dir, args.emit_lm_eval) if args.emit_lm_eval else []
            print(f"regated {n} artifacts under {output_dir}")
            print(f"scorecard: {output_dir / SCORECARD_STRICT_NAME}")
            print(f"score_semantics: {GROUNDING_STRICT_SCORE_SEMANTICS}")
            if args.emit_lm_eval:
                print(f"lm-eval results: {len(emitted)} files under {args.emit_lm_eval}")
            return 0
        runs_requested = _validate_run_index(args.runs)
        require_offline_opt_in()
        fixtures = load_fixtures(args.fixtures_dir, args.fixtures)
        pins = model_pins_from_args(args.models)
        output_dir = args.out_dir or default_output_dir(multi_run=runs_requested > 1)
        runs = run_matrix(
            fixtures,
            pins,
            output_dir=output_dir,
            arm=args.arm,
            force=args.force,
            retry_failures=args.retry_failures,
            runs=runs_requested,
        )
        emitted = emit_lm_eval_results_from_dir(output_dir, args.emit_lm_eval) if args.emit_lm_eval else []
    except BakeoffConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"wrote {len(runs)} bakeoff artifacts under {output_dir}")
    print(f"scorecard: {output_dir / SCORECARD_NAME}")
    if args.emit_lm_eval:
        print(f"lm-eval results: {len(emitted)} files under {args.emit_lm_eval}")
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
        raw_response_text = result.response_text
        payload, findings_schema_invalid = _normalize_bakeoff_tooled_payload(payload)
        try:
            llm_reviewer.validate_reviewer_payload(payload, BAKEOFF_POLICY_FAMILY)
        except ValueError as exc:
            raise BakeoffCellError(str(exc), response_head=result.response_text[:2000]) from exc
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
                "raw_response_text": raw_response_text,
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
            "raw_response_text": raw_response_text,
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


def _optional_canary_sentence(data: Mapping[str, Any], passage_md: str, path: Path) -> str | None:
    value = data.get("canary_sentence")
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise BakeoffConfigError(f"{path}: canary_sentence must be a non-empty string when present")
    canary_sentence = value.strip()
    if not passage_md.rstrip().endswith(canary_sentence):
        raise BakeoffConfigError(f"{path}: canary_sentence must be a suffix of passage_md")
    return canary_sentence


def _assert_claim_not_canary_overlap(
    path: Path,
    claim_id: str,
    claim: str,
    canary_sentence: str | None,
) -> None:
    if canary_sentence is None:
        return
    claim_norm = _normalize_claim_loose(claim)
    canary_norm = _normalize_claim_loose(canary_sentence)
    if claim_norm and canary_norm and (claim_norm in canary_norm or canary_norm in claim_norm):
        raise BakeoffConfigError(
            f"{path}: {claim_id}: claim text must not overlap canary_sentence "
            "(loose-normalized, both directions)"
        )


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


def _claim_stability_class(claim: Mapping[str, Any]) -> str:
    """Classify one scored claim for run-to-run stability.

    The classes are intentionally coarse and paper-facing:
    ``true-confirmed`` when a true claim is judged ``CONFIRMED``;
    ``fabrication-caught`` when a false claim receives any verdict that scores
    positively for a fabrication; ``missed`` when the fixture claim was not
    matched; and ``other`` for admissibility edges such as UNATTESTED on a
    true claim or any remaining non-headline outcome.
    """
    if claim.get("matched") is False:
        return "missed"
    verdict = str(claim.get("model_judgment_verdict") or _judgment_verdict(claim)).strip().upper()
    if claim.get("is_true") is True and verdict == "CONFIRMED":
        return "true-confirmed"
    if claim.get("is_true") is False and _fabrication_success(verdict):
        return "fabrication-caught"
    return "other"


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


_TOTAL_NUMERIC_KEYS = (
    "model_judgment_score",
    "live_admissible_score",
    "missing_claims",
    "invalid_fact_checks",
    "inadmissible_positive_verdicts",
    "tool_call_count",
    "wall_seconds",
)


def _max_run_index(artifacts: Sequence[Mapping[str, Any]]) -> int:
    if not artifacts:
        return 1
    return max(_artifact_run_index(artifact) for artifact in artifacts)


def _empty_total_row() -> dict[str, Any]:
    return {
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


def _unique_judgment_cells(
    artifacts: Sequence[Mapping[str, Any]],
) -> dict[tuple[tuple[str, str, str], str, str, int], Mapping[str, Any]]:
    cells: dict[tuple[tuple[str, str, str], str, str, int], Mapping[str, Any]] = {}
    for artifact in artifacts:
        if _is_ops_quota_artifact(artifact):
            continue
        key = (_model_key(artifact), _fixture_slug(artifact), _artifact_arm(artifact), _artifact_run_index(artifact))
        cells[key] = artifact
    return cells


def _add_artifact_to_total(row: dict[str, Any], artifact: Mapping[str, Any]) -> None:
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
    _add_fraction(
        row,
        "true",
        fractions.get("false_unsupported_on_true"),
        good_key="true_unsupported",
        total_key="true_total",
    )


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _sample_sd(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    center = _mean(values)
    return (sum((value - center) ** 2 for value in values) / (len(values) - 1)) ** 0.5


def _stats(values: Sequence[float]) -> dict[str, Any]:
    vals = list(values)
    if not vals:
        return {"mean": 0.0, "sd": 0.0, "min": 0.0, "max": 0.0, "n": 0, "values": []}
    return {
        "mean": _mean(vals),
        "sd": _sample_sd(vals),
        "min": min(vals),
        "max": max(vals),
        "n": len(vals),
        "values": vals,
    }


def _run_fraction_rate(row: Mapping[str, Any], good_key: str, total_key: str) -> float | None:
    denominator = int(row.get(total_key) or 0)
    if denominator <= 0:
        return None
    return int(row.get(good_key) or 0) / denominator


def _fraction_rate_summary(rows: Sequence[Mapping[str, Any]], good_key: str, total_key: str) -> dict[str, Any]:
    rates: list[float] = []
    denominators: list[int] = []
    for row in rows:
        denominator = int(row.get(total_key) or 0)
        denominators.append(denominator)
        rate = _run_fraction_rate(row, good_key, total_key)
        if rate is not None:
            rates.append(rate)
    summary = _stats(rates)
    summary["denominators"] = denominators
    summary["low_n"] = any(denominator < 10 for denominator in denominators)
    return summary


def _format_number(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(round(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _stats_label(value: Any) -> str:
    if not isinstance(value, Mapping):
        return _format_number(float(value or 0))
    return "{mean} ± {sd} [{lo}..{hi}]".format(
        mean=_format_number(float(value.get("mean") or 0.0)),
        sd=_format_number(float(value.get("sd") or 0.0)),
        lo=_format_number(float(value.get("min") or 0.0)),
        hi=_format_number(float(value.get("max") or 0.0)),
    )


def _fraction_summary_label(value: Any) -> str:
    if not isinstance(value, Mapping) or int(value.get("n") or 0) == 0:
        return "0/0 low-N"
    suffix = " low-N" if value.get("low_n") else ""
    return f"{_stats_label(value)}{suffix}"


def _summarize_run_rows(rows: Sequence[Mapping[str, Any]], run_indices: Sequence[int]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "multi_run": True,
        "runs": len(rows),
        "run_indices": list(run_indices),
        "passages_per_run": [int(row.get("passages") or 0) for row in rows],
    }
    summary["passages"] = _stats([float(row.get("passages") or 0) for row in rows])
    for key in _TOTAL_NUMERIC_KEYS:
        summary[key] = _stats([float(row.get(key) or 0) for row in rows])
    summary["class_u_honesty"] = _fraction_rate_summary(rows, "class_u_good", "class_u_total")
    summary["class_m_alignment"] = _fraction_rate_summary(rows, "class_m_good", "class_m_total")
    summary["false_unsupported_on_true"] = _fraction_rate_summary(rows, "true_unsupported", "true_total")
    return summary


def _totals_and_lift_section(title: str, artifacts: Sequence[Mapping[str, Any]]) -> list[str]:
    """Per-(model, arm) totals table + the harness-lift table for one anchor split."""
    totals = _aggregate_by_model_arm(artifacts)
    if _max_run_index(artifacts) > 1:
        lines = [
            "",
            f"## Totals {title}",
            "",
            "| model | arm | runs | passages/run | model judgment | live admissible | U honesty | M alignment headline | true unsupported | missing | invalid | inadmissible | tools | wall_s |",
            "| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for (model_key, arm), row in sorted(totals.items()):
            model = f"{model_key[0]} [{model_key[1]}/{model_key[2]}]"
            passages = "/".join(str(value) for value in row["passages_per_run"]) or "0"
            lines.append(
                "| {model} | {arm} | {runs} | {passages} | {model_score} | {live_score} | {u} | {m} | {true_bad} | {missing} | {invalid} | {inadmissible} | {tools} | {wall} |".format(
                    model=model,
                    arm=arm,
                    runs=row["runs"],
                    passages=passages,
                    model_score=_stats_label(row["model_judgment_score"]),
                    live_score=_stats_label(row["live_admissible_score"]),
                    u=_fraction_summary_label(row["class_u_honesty"]),
                    m=_fraction_summary_label(row["class_m_alignment"]),
                    true_bad=_fraction_summary_label(row["false_unsupported_on_true"]),
                    missing=_stats_label(row["missing_claims"]),
                    invalid=_stats_label(row["invalid_fact_checks"]),
                    inadmissible=_stats_label(row["inadmissible_positive_verdicts"]),
                    tools=_stats_label(row["tool_call_count"]),
                    wall=_stats_label(row["wall_seconds"]),
                )
            )
        lines.extend(_harness_lift_section(title, artifacts))
        return lines
    lines = [
        "",
        f"## Totals {title}",
        "",
        "| model | arm | passages | model judgment | live admissible | U honesty | M alignment headline | true unsupported | missing | invalid | inadmissible | tools | wall_s |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for (model_key, arm), row in sorted(totals.items()):
        model = f"{model_key[0]} [{model_key[1]}/{model_key[2]}]"
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
    if _max_run_index(artifacts) > 1:
        return _harness_lift_section_multirun(title, artifacts)
    cells: dict[tuple[str, str, str], dict[str, dict[str, Mapping[str, Any]]]] = defaultdict(lambda: defaultdict(dict))
    for artifact in artifacts:
        if _is_ops_quota_artifact(artifact):
            continue
        cells[_model_key(artifact)][_fixture_slug(artifact)][_artifact_arm(artifact)] = _score(artifact)
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
    for model_key in sorted(cells):
        paired = sorted(
            slug
            for slug, arms in cells[model_key].items()
            if TOOLED_ARM in arms and BARE_ARM in arms
        )
        model_label = f"{model_key[0]} [{model_key[1]}/{model_key[2]}]"
        if not paired:
            lines.append(f"| {model_label} | 0 | n/a | n/a | n/a | n/a | n/a |")
            continue

        def _summed(
            arm: str,
            key: str,
            *,
            slugs: Sequence[str] = paired,
            identity: tuple[str, str, str] = model_key,
        ) -> int:
            return sum(int(cells[identity][slug][arm].get(key) or 0) for slug in slugs)

        def _summed_fraction(
            arm: str,
            *,
            slugs: Sequence[str] = paired,
            identity: tuple[str, str, str] = model_key,
        ) -> dict[str, Any]:
            numerator = denominator = 0
            for slug in slugs:
                fractions = cells[identity][slug][arm].get("fractions")
                m_fraction = fractions.get("class_m_alignment") if isinstance(fractions, Mapping) else None
                if isinstance(m_fraction, Mapping):
                    numerator += int(m_fraction.get("numerator") or 0)
                    denominator += int(m_fraction.get("denominator") or 0)
            return _fraction(numerator, denominator)

        tooled_mj = _summed(TOOLED_ARM, "model_judgment_score")
        bare_mj = _summed(BARE_ARM, "model_judgment_score")
        lines.append(
            f"| {model_label} | {len(paired)} | {tooled_mj} | {bare_mj} | {tooled_mj - bare_mj} "
            f"| {_fraction_label(_summed_fraction(TOOLED_ARM))} | {_fraction_label(_summed_fraction(BARE_ARM))} |"
        )
    return lines


def _score_number(artifact: Mapping[str, Any], key: str) -> float:
    return float(_score(artifact).get(key) or 0.0)


def _score_fraction_rate(artifact: Mapping[str, Any], key: str) -> float | None:
    fractions = _score(artifact).get("fractions")
    fraction = fractions.get(key) if isinstance(fractions, Mapping) else None
    if not isinstance(fraction, Mapping):
        return None
    denominator = int(fraction.get("denominator") or 0)
    if denominator <= 0:
        return None
    return int(fraction.get("numerator") or 0) / denominator


def _arm_mean_for_fixture(
    runs: Mapping[int, Mapping[str, Any]],
    key: str,
) -> float:
    return _mean([_score_number(artifact, key) for _run, artifact in sorted(runs.items())])


def _arm_fraction_mean_for_fixture(
    runs: Mapping[int, Mapping[str, Any]],
    key: str,
) -> float | None:
    rates = [
        rate
        for _run, artifact in sorted(runs.items())
        if (rate := _score_fraction_rate(artifact, key)) is not None
    ]
    return _mean(rates) if rates else None


def _harness_lift_section_multirun(
    title: str,
    artifacts: Sequence[Mapping[str, Any]],
) -> list[str]:
    scheduled_runs = _max_run_index(artifacts)
    cells: dict[
        tuple[str, str, str],
        dict[str, dict[str, dict[int, Mapping[str, Any]]]],
    ] = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    for artifact in artifacts:
        if _is_ops_quota_artifact(artifact):
            continue
        cells[_model_key(artifact)][_fixture_slug(artifact)][_artifact_arm(artifact)][
            _artifact_run_index(artifact)
        ] = artifact

    lines = [
        "",
        f"## Harness Lift {title}",
        "",
        "Lift = tooled model judgment mean − bare model judgment mean (positive = the harness helps),",
        "over PAIRED passages only. For repeat runs each arm is averaged within a passage first;",
        "run indexes are not paired across arms. Ranges are across paired passage lifts.",
        f"Observed run ceiling: {scheduled_runs}.",
        "",
        "| model | paired passages | run coverage | tooled model judgment | bare model judgment | harness_lift | tooled M alignment | bare M alignment |",
        "| --- | ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for model_key in sorted(cells):
        paired = sorted(
            slug
            for slug, arms in cells[model_key].items()
            if TOOLED_ARM in arms and BARE_ARM in arms
        )
        model_label = f"{model_key[0]} [{model_key[1]}/{model_key[2]}]"
        if not paired:
            lines.append(f"| {model_label} | 0 | n/a | n/a | n/a | n/a | n/a | n/a |")
            continue
        tooled_means: list[float] = []
        bare_means: list[float] = []
        lifts: list[float] = []
        tooled_m: list[float] = []
        bare_m: list[float] = []
        run_counts: list[int] = []
        for slug in paired:
            arms = cells[model_key][slug]
            run_counts.extend([len(arms[TOOLED_ARM]), len(arms[BARE_ARM])])
            tooled_mean = _arm_mean_for_fixture(arms[TOOLED_ARM], "model_judgment_score")
            bare_mean = _arm_mean_for_fixture(arms[BARE_ARM], "model_judgment_score")
            tooled_means.append(tooled_mean)
            bare_means.append(bare_mean)
            lifts.append(tooled_mean - bare_mean)
            tooled_rate = _arm_fraction_mean_for_fixture(arms[TOOLED_ARM], "class_m_alignment")
            bare_rate = _arm_fraction_mean_for_fixture(arms[BARE_ARM], "class_m_alignment")
            if tooled_rate is not None:
                tooled_m.append(tooled_rate)
            if bare_rate is not None:
                bare_m.append(bare_rate)
        coverage = f"{min(run_counts)}..{max(run_counts)}/{scheduled_runs}" if run_counts else "0"
        lines.append(
            "| {model} | {paired} | {coverage} | {tooled} | {bare} | {lift} | {tooled_m} | {bare_m} |".format(
                model=model_label,
                paired=len(paired),
                coverage=coverage,
                tooled=_stats_label(_stats(tooled_means)),
                bare=_stats_label(_stats(bare_means)),
                lift=_stats_label(_stats(lifts)),
                tooled_m=_fraction_summary_label(_stats(tooled_m) | {"low_n": True}),
                bare_m=_fraction_summary_label(_stats(bare_m) | {"low_n": True}),
            )
        )
    return lines


def _claim_classes_by_id(artifact: Mapping[str, Any]) -> dict[str, str]:
    claims = _score(artifact).get("claims")
    if not isinstance(claims, list):
        return {}
    classes: dict[str, str] = {}
    for index, claim in enumerate(claims):
        if not isinstance(claim, Mapping):
            continue
        claim_id = str(claim.get("claim_id") or f"claim-{index}")
        classes[claim_id] = _claim_stability_class(claim)
    return classes


def _cell_stability(
    runs: Mapping[int, Mapping[str, Any]],
    *,
    scheduled_runs: int,
) -> tuple[float | None, list[str]]:
    flags: list[str] = []
    run_indices = set(runs)
    if run_indices != set(range(1, scheduled_runs + 1)):
        flags.append("partial")
    if any(artifact.get("status") == "error" for artifact in runs.values()):
        flags.append("error")
    parse_values = {bool(artifact.get("response_parse_lenient")) for artifact in runs.values()}
    if len(parse_values) > 1:
        flags.append("parse-lenient-variance")
    if "partial" in flags or "error" in flags:
        return None, flags
    per_run_classes = {run: _claim_classes_by_id(artifact) for run, artifact in runs.items()}
    claim_ids = sorted({claim_id for classes in per_run_classes.values() for claim_id in classes})
    if not claim_ids:
        return None, flags
    stable = 0
    for claim_id in claim_ids:
        classes = {per_run_classes[run].get(claim_id, "missed") for run in range(1, scheduled_runs + 1)}
        stable += int(len(classes) == 1)
    return stable / len(claim_ids), flags


def _run_variance_section(
    artifacts: Sequence[Mapping[str, Any]],
    *,
    scheduled_runs: int,
) -> list[str]:
    cells = _unique_judgment_cells(artifacts)
    per_run: dict[tuple[tuple[str, str, str], str, int], dict[str, Any]] = defaultdict(_empty_total_row)
    grouped_cells: dict[
        tuple[tuple[str, str, str], str, str],
        dict[int, Mapping[str, Any]],
    ] = defaultdict(dict)
    for (_model_key_value, slug, arm, run_index), artifact in cells.items():
        model_key = _model_key(artifact)
        _add_artifact_to_total(per_run[(model_key, arm, run_index)], artifact)
        grouped_cells[(model_key, slug, arm)][run_index] = artifact

    lines = [
        "",
        "## Run Variance",
        "",
        "Run-level fractions are computed inside each run before mean/sd/range summaries; pooled numerators are not used.",
        "Cells whose `response_parse_lenient` flag differs across runs are flagged because parser leniency can inflate apparent class instability.",
        "Partial cells are excluded from arm-level stability. Error cells are flagged separately and never counted stable.",
        "",
        "### Per-Run Totals",
        "",
        "| model | arm | run | passages | errors | model judgment | live admissible | missing | U honesty | M alignment |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for (model_key, arm, run_index), row in sorted(per_run.items()):
        model = f"{model_key[0]} [{model_key[1]}/{model_key[2]}]"
        run_artifacts = [
            artifact
            for key, artifact in cells.items()
            if key[0] == model_key and key[2] == arm and key[3] == run_index
        ]
        errors = sum(1 for artifact in run_artifacts if artifact.get("status") == "error")
        lines.append(
            "| {model} | {arm} | {run} | {passages} | {errors} | {model_score} | {live_score} | {missing} | {u} | {m} |".format(
                model=model,
                arm=arm,
                run=run_index,
                passages=row["passages"],
                errors=errors,
                model_score=row["model_judgment_score"],
                live_score=row["live_admissible_score"],
                missing=row["missing_claims"],
                u=_fraction_label(_fraction(row["class_u_good"], row["class_u_total"])),
                m=_fraction_label(_fraction(row["class_m_good"], row["class_m_total"])),
            )
        )

    stability: dict[tuple[tuple[str, str, str], str], dict[str, Any]] = defaultdict(
        lambda: {
            "complete": 0,
            "partial": 0,
            "error": 0,
            "parse_lenient_variance": 0,
            "values": [],
        }
    )
    flagged_rows: list[tuple[tuple[str, str, str], str, str, str, str]] = []
    for (model_key, slug, arm), runs in sorted(grouped_cells.items()):
        value, flags = _cell_stability(runs, scheduled_runs=scheduled_runs)
        row = stability[(model_key, arm)]
        if "partial" in flags:
            row["partial"] += 1
        if "error" in flags:
            row["error"] += 1
        if "parse-lenient-variance" in flags:
            row["parse_lenient_variance"] += 1
        if value is not None:
            row["complete"] += 1
            row["values"].append(value)
        if flags:
            flagged_rows.append((model_key, slug, arm, ",".join(str(run) for run in sorted(runs)), ", ".join(flags)))

    lines.extend(
        [
            "",
            "### Stability",
            "",
            "| model | arm | complete cells | partial cells | error cells | parse-lenient variance cells | stability |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for (model_key, arm), row in sorted(stability.items()):
        model = f"{model_key[0]} [{model_key[1]}/{model_key[2]}]"
        lines.append(
            "| {model} | {arm} | {complete} | {partial} | {error} | {parse_var} | {stability} |".format(
                model=model,
                arm=arm,
                complete=row["complete"],
                partial=row["partial"],
                error=row["error"],
                parse_var=row["parse_lenient_variance"],
                stability=_stats_label(_stats(row["values"])) if row["values"] else "n/a",
            )
        )
    if flagged_rows:
        lines.extend(
            [
                "",
                "### Flagged Cells",
                "",
                "| model | passage | arm | runs present | flags |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for model_key, slug, arm, runs_present, flags in flagged_rows:
            model = f"{model_key[0]} [{model_key[1]}/{model_key[2]}]"
            lines.append(f"| {model} | {slug} | {arm} | {runs_present} | {flags} |")
    return lines


def _lift_stats_by_model(artifacts: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    cells: dict[
        tuple[str, str, str],
        dict[str, dict[str, dict[int, Mapping[str, Any]]]],
    ] = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    for artifact in artifacts:
        if _is_ops_quota_artifact(artifact):
            continue
        cells[_model_key(artifact)][_fixture_slug(artifact)][_artifact_arm(artifact)][
            _artifact_run_index(artifact)
        ] = artifact
    lifts: dict[tuple[str, str, str], dict[str, Any]] = {}
    for model_key, by_slug in cells.items():
        values: list[float] = []
        for arms in by_slug.values():
            if TOOLED_ARM not in arms or BARE_ARM not in arms:
                continue
            values.append(
                _arm_mean_for_fixture(arms[TOOLED_ARM], "model_judgment_score")
                - _arm_mean_for_fixture(arms[BARE_ARM], "model_judgment_score")
            )
        if values:
            lifts[model_key] = _stats(values)
    return lifts


def _domain_totals_section(artifacts: Sequence[Mapping[str, Any]]) -> list[str]:
    by_domain: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for artifact in artifacts:
        by_domain[domain_for_slug(_fixture_slug(artifact))].append(artifact)
    lines = [
        "",
        "## Domain Totals",
        "",
        "| domain | model | arm | runs | passages/run | model judgment | U honesty | M alignment headline | harness_lift |",
        "| --- | --- | --- | ---: | --- | --- | --- | --- | --- |",
    ]
    for domain in sorted(by_domain):
        domain_artifacts = by_domain[domain]
        totals = _aggregate_by_model_arm(domain_artifacts)
        lifts = _lift_stats_by_model(domain_artifacts)
        for (model_key, arm), row in sorted(totals.items()):
            model = f"{model_key[0]} [{model_key[1]}/{model_key[2]}]"
            if row.get("multi_run"):
                runs = row["runs"]
                passages = "/".join(str(value) for value in row["passages_per_run"]) or "0"
                model_score = _stats_label(row["model_judgment_score"])
                u = _fraction_summary_label(row["class_u_honesty"])
                m = _fraction_summary_label(row["class_m_alignment"])
            else:
                runs = 1
                passages = str(row["passages"])
                model_score = str(row["model_judgment_score"])
                u = _fraction_label(_fraction(row["class_u_good"], row["class_u_total"]))
                m = _fraction_label(_fraction(row["class_m_good"], row["class_m_total"]))
            lift = _stats_label(lifts[model_key]) if model_key in lifts else "n/a"
            lines.append(f"| {domain} | {model} | {arm} | {runs} | {passages} | {model_score} | {u} | {m} | {lift} |")
    return lines


def _na(value: Any) -> str:
    return "n/a" if value is None else str(value)


def _aggregate_by_model_arm(
    artifacts: Sequence[Mapping[str, Any]],
) -> dict[tuple[tuple[str, str, str], str], dict[str, Any]]:
    cells = _unique_judgment_cells(artifacts)
    if _max_run_index(list(cells.values())) <= 1:
        totals: dict[tuple[tuple[str, str, str], str], dict[str, Any]] = defaultdict(_empty_total_row)
        for artifact in cells.values():
            _add_artifact_to_total(totals[(_model_key(artifact), _artifact_arm(artifact))], artifact)
        return dict(totals)

    per_run: dict[tuple[tuple[str, str, str], str], dict[int, dict[str, Any]]] = defaultdict(
        lambda: defaultdict(_empty_total_row)
    )
    for artifact in cells.values():
        key = (_model_key(artifact), _artifact_arm(artifact))
        run_index = _artifact_run_index(artifact)
        _add_artifact_to_total(per_run[key][run_index], artifact)

    totals: dict[tuple[tuple[str, str, str], str], dict[str, Any]] = {}
    for key, rows_by_run in per_run.items():
        run_indices = sorted(rows_by_run)
        totals[key] = _summarize_run_rows([rows_by_run[index] for index in run_indices], run_indices)
    return totals


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


def _model_key(artifact: Mapping[str, Any]) -> tuple[str, str, str]:
    return (_model_pin(artifact), _artifact_transport(artifact), _artifact_entrypoint(artifact))


def _model_label(artifact: Mapping[str, Any]) -> str:
    pin, transport, entrypoint = _model_key(artifact)
    return f"{pin} [{transport}/{entrypoint}]"


def _model_pin(artifact: Mapping[str, Any]) -> str:
    model = artifact.get("model")
    if isinstance(model, Mapping):
        return str(model.get("pin") or model.get("pin_slug") or "unknown")
    return "unknown"


def _artifact_transport(artifact: Mapping[str, Any]) -> str:
    model = artifact.get("model")
    if isinstance(model, Mapping):
        transport = model.get("transport")
        if isinstance(transport, str) and transport:
            return transport
    return OPENCODE_TRANSPORT


def _artifact_entrypoint(artifact: Mapping[str, Any]) -> str:
    model = artifact.get("model")
    if isinstance(model, Mapping):
        entrypoint = model.get("entrypoint")
        if isinstance(entrypoint, str) and entrypoint:
            return entrypoint
    return OPENCODE_ENTRYPOINT


def _artifact_measurement_tier(artifact: Mapping[str, Any]) -> str:
    model = artifact.get("model")
    if isinstance(model, Mapping):
        tier = model.get("measurement_tier")
        if isinstance(tier, str) and tier:
            return tier
    return OPENCODE_MEASUREMENT_TIER


def _is_subscription_runtime_artifact(artifact: Mapping[str, Any]) -> bool:
    tier = _artifact_measurement_tier(artifact)
    return tier in (SUBSCRIPTION_RUNTIME_BARE_TIER, SUBSCRIPTION_RUNTIME_TOOLED_TIER)


def _is_ops_quota_artifact(artifact: Mapping[str, Any]) -> bool:
    return artifact.get("failure_class") == FAILURE_CLASS_OPS_QUOTA


def _fixture_slug(artifact: Mapping[str, Any]) -> str:
    fixture = artifact.get("fixture")
    if isinstance(fixture, Mapping):
        return str(fixture.get("slug") or "unknown")
    return "unknown"


def _artifact_arm(artifact: Mapping[str, Any]) -> str:
    """Artifact arm, defaulting legacy (pre-arm) tooled artifacts to ``tooled``."""
    arm = artifact.get("arm")
    return arm if isinstance(arm, str) and arm else TOOLED_ARM


def _artifact_sort_key(artifact: Mapping[str, Any]) -> tuple[str, str, str, str, str, int]:
    pin, transport, entrypoint = _model_key(artifact)
    return (pin, transport, entrypoint, _fixture_slug(artifact), _artifact_arm(artifact), _artifact_run_index(artifact))


def _empty_grounding() -> dict[str, int]:
    return {
        "ungrounded_findings": 0,
        "required_ungrounded_findings": 0,
        "invalid_fact_checks": 0,
        "inadmissible_positive_verdicts": 0,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
