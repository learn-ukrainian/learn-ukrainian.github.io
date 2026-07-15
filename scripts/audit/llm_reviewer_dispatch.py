#!/usr/bin/env python3
"""Live LLM reviewer dispatcher for the QG workflow.

This module owns model routing, cross-family lineage checks, canary artifact
exactness, and local spend persistence. The workflow calls it through the same
``Reviewer(target, prompt)`` shape used by precomputed reviewer responses.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import suppress
from dataclasses import asdict, dataclass, replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from scripts.audit import anchor_primitives, llm_qg_canaries, llm_reviewer, qg_schema
from scripts.audit.content_surface_gates import policy_for_level

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DAILY_SPEND_PATH = PROJECT_ROOT / "data" / "telemetry" / "llm_reviewer_spend.jsonl"
CANARY_SCHEMA_VERSION = "llm_reviewer_dispatch_canary.v1"

# DELIBERATELY still the OpenRouter endpoint (NOT the 2026-07-07 $0
# `google-ais/gemma-4-31b-it` bridge default, #4767): this calibration layer's
# MeasuredCostProfile rows + step-1 validation were measured ON this transport,
# and its runs are deliberate, spend-tracked cells (fractions of a cent).
# Migrating the seat to AIS-direct requires re-measuring the profile in a
# bakeoff cell first — do NOT silently swap the transport under measured data.
GEMMA_MODEL_ID = "openrouter/google/gemma-4-31b-it"
FRONTIER_MODEL_ID = "gemini-3.1-pro-high"
# TODO(#2156 step-3 bakeoff): pin `openrouter/google/gemini-3.1-pro` once it is
# reachable via `opencode models`. As of 2026-07-05 only `-preview` variants
# resolve (`opencode models | grep gemini-3.1-pro` -> `gemini-3.1-pro-preview`),
# so the seminar/factual opencode route pins the step-1-validated gemma-4-31b-it
# endpoint until the bakeoff selects the frontier model.
FRONTIER_OPENCODE_MODEL_ID = "openrouter/google/gemma-4-31b-it"
CLAUDE_SPOT_AUDIT_MODEL_ID = "claude-opus-4.6"
# The sources MCP endpoint opencode reviewer routes ground against (mirrors the
# `sources` entry in ~/.config/opencode/opencode.jsonc).
SOURCES_MCP_URL = "http://127.0.0.1:8766/mcp"
REVIEWER_MODULE_REVIEW_NAME = "review-review.md"
_PROMPT_LEVEL_SLUG_RE = re.compile(
    r"^Level:\s*(?P<level>[^\n]+)\s*\nSlug:\s*(?P<slug>[^\n]+)",
    re.MULTILINE,
)
MAX_REVIEWER_TOOLS = 40
INVALID_TOOL_THEATRE = "INVALID_TOOL_THEATRE"
RETRY_EXHAUSTED = "RETRY_EXHAUSTED"
UNGROUNDED_FINDINGS = "ungrounded_findings"
DEEP_READ_REQUIRED = "deep_read_required"

_TOKEN_DIVISOR = 3.5
_TOKEN_RE = re.compile(r"[\w’'-]+", re.UNICODE)
_AUTHOR_FIELDS = (
    "author_family",
    "writer_family",
    "agent_family",
    "family",
    "writer",
    "agent",
    "model",
    "reviewer",
)
_X_AGENT_RE = re.compile(r"^X-Agent:\s*([^/\s:]+)", re.IGNORECASE | re.MULTILINE)
_COAUTHOR_RE = re.compile(r"^Co-Authored-By:\s*([^<\n]+)", re.IGNORECASE | re.MULTILINE)
_SOURCE_TOOL_PREFIXES = ("sources_", "mcp__sources")
_WIKI_TOOL_MARKERS = ("wikipedia", "wiki")
_DEEP_READ_WIKI_MODES = {"section", "sections", "extract", "article", "page"}
_POSITIVE_FACT_CHECK_VERDICTS = frozenset({"CONFIRMED", "REFUTED_BY_CONTRADICTION", "CONTESTED"})
_ELLIPSIS_RE = re.compile(r"\[…\]|\[\.\.\.\]|…|\.{3,}")
SCORECARD_COST_BASIS_PATH = "audit/2026-07-05-qg-bakeoff/SCORECARD.md"
SCORECARD_COST_BASIS_GENERATED_AT = "2026-07-05T22:29:21.234824Z"
SCORECARD_COST_BASIS = (
    "measured tooled medians from "
    f"{SCORECARD_COST_BASIS_PATH} (Generated: {SCORECARD_COST_BASIS_GENERATED_AT}); "
    "tool_calls/passage median: gemma=4.0, ds-pro=15.5, ds-flash=30.0; "
    "wall_s observed range=16.499-267.781; soft tool anomaly band=>1.5x observed max; "
    f"hard tool cap={MAX_REVIEWER_TOOLS}"
)

_THEATRE_RETRY_REMINDER = """

---

## Reviewer Retry: Tools Required

The prior seminar/factual review did not satisfy the deterministic tool gate. You must call the sources MCP tools before answering. Use relevant queries that overlap the factual claims, then return only the required JSON object.
"""

_DEEP_READ_RETRY_REMINDER = """

---

## Reviewer Retry: Deep Read Required

The prior response used wiki summary-mode evidence where summary-only evidence is inadmissible for any verdict. Re-run the relevant wiki query in section/extract mode before deciding the verdict, then return only the required JSON object.
"""


class ReviewerDispatchError(RuntimeError):
    """Base error for dispatcher hard gates."""


class ReviewerProviderError(ReviewerDispatchError):
    """Provider invocation failed before a parseable reviewer response."""


class ReviewerPreflightError(ReviewerProviderError):
    """Batch-level live transport preflight failed with a named reason."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


class ReviewerLineageError(ReviewerDispatchError):
    """Module author lineage is unavailable in live mode."""


class ReviewerSelfReviewError(ReviewerDispatchError):
    """Reviewer route is from the same model family as the module author."""


class ReviewerRouteError(ReviewerDispatchError):
    """Reviewer route is disallowed or incoherent."""


@dataclass(frozen=True, slots=True)
class ReviewerRoute:
    """One concrete reviewer route."""

    route_name: str
    bridge_command: tuple[str, ...]
    reviewer_model_id: str
    reviewer_family: str
    purpose: str
    input_usd_per_mtok: float
    output_usd_per_mtok: float
    requires_mcp: bool = False

    def asdict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "bridge_command": list(self.bridge_command),
        }


@dataclass(frozen=True, slots=True)
class MeasuredCostProfile:
    """Scorecard-measured reviewer cost factors for one model class."""

    label: str
    input_usd_per_mtok: float
    output_usd_per_mtok: float
    observed_tool_call_min: int
    observed_tool_call_median: float
    observed_tool_call_max: int
    observed_wall_s_min: float
    observed_wall_s_median: float
    observed_wall_s_max: float
    pricing_basis: str

    @property
    def tool_call_anomaly_threshold(self) -> float:
        return self.observed_tool_call_max * 1.5

    def estimate_fields(self) -> dict[str, Any]:
        return {
            "measured_cost_profile": self.label,
            "estimated_tool_call_median": self.observed_tool_call_median,
            "observed_tool_call_min": self.observed_tool_call_min,
            "observed_tool_call_max": self.observed_tool_call_max,
            "tool_call_anomaly_threshold": self.tool_call_anomaly_threshold,
            "estimated_wall_s_median": self.observed_wall_s_median,
            "observed_wall_s_min": self.observed_wall_s_min,
            "observed_wall_s_max": self.observed_wall_s_max,
            "pricing_basis": self.pricing_basis,
        }


@dataclass(frozen=True, slots=True)
class AuthorLineage:
    """Resolved module author family and where it came from."""

    family: str | None
    source: str
    evidence: str | None = None

    @property
    def available(self) -> bool:
        return self.family is not None


@dataclass(frozen=True, slots=True)
class DispatchContext:
    """Routing context for one module or canary."""

    level: str
    slug: str
    module_dir: Path
    policy_family: str
    gate_version: str
    contested_gold_suppressed: bool = False
    factual_sensitive: bool = False
    escalation: bool = False
    author_family: str | None = None


@dataclass(frozen=True, slots=True)
class DispatchResult:
    """Provider response plus audited dispatch metadata."""

    response_text: str
    reviewer_model_id: str
    reviewer_family: str
    route_name: str
    observed_prompt_tokens: int | None = None
    observed_completion_tokens: int | None = None
    observed_cost_usd: float | None = None
    usage: Mapping[str, Any] | None = None
    tool_call_count: int = 0
    tools_used: tuple[str, ...] = ()
    tool_events: tuple[Mapping[str, Any], ...] = ()
    execution_provenance: Mapping[str, Any] | None = None
    author_lineage: Mapping[str, Any] | None = None
    cross_family_validated: bool = False

    def metadata(self) -> dict[str, Any]:
        metadata = {
            "reviewer_model_id": self.reviewer_model_id,
            "reviewer_family": self.reviewer_family,
            "route_name": self.route_name,
            "observed_prompt_tokens": self.observed_prompt_tokens,
            "observed_completion_tokens": self.observed_completion_tokens,
            "observed_cost_usd": self.observed_cost_usd,
            "usage": dict(self.usage or {}),
            "tool_call_count": self.tool_call_count,
            "tools_used": list(self.tools_used),
            "tool_events": [dict(event) for event in self.tool_events],
        }
        # Preserve the established metadata/artifact bytes for offline and
        # injected callers.  Certification provenance is additive only when a
        # dispatcher actually supplied it; live dispatches populate all three
        # fields together after resolving author lineage and route separation.
        if self.execution_provenance is not None:
            metadata["execution_provenance"] = dict(self.execution_provenance)
        if self.author_lineage is not None:
            metadata["author_lineage"] = dict(self.author_lineage)
        if self.execution_provenance is not None or self.author_lineage is not None or self.cross_family_validated:
            metadata["cross_family_validated"] = self.cross_family_validated
        return metadata


@dataclass(frozen=True, slots=True)
class GroundingGateResult:
    """Result of anti-fabricated-grounding filtering."""

    payload: dict[str, Any]
    ungrounded_findings: int = 0
    required_ungrounded_findings: int = 0
    invalid_fact_checks: int = 0
    inadmissible_positive_verdicts: int = 0


ProviderRunner = Callable[[ReviewerRoute, str, str], DispatchResult | str]

GEMMA_SURFACE_ROUTE = ReviewerRoute(
    route_name="gemma_surface",
    bridge_command=("ask-gemma", "--model", GEMMA_MODEL_ID),
    reviewer_model_id=GEMMA_MODEL_ID,
    reviewer_family="google",
    purpose="B1+ surface naturalness/register/calque review",
    input_usd_per_mtok=0.12,
    output_usd_per_mtok=0.35,
)
# Kept for fallback/reference (do NOT delete — #2156). `route_for_review` no
# longer returns this route; seminar/factual now flows through the tooled
# opencode route below so the reviewer can ground factual claims against the
# sources MCP. An ungrounded agy reviewer cannot catch the gemma fabrication
# class documented in docs/projects/ua-eval-harness/model-evidence.md.
FRONTIER_FACTUAL_ROUTE = ReviewerRoute(
    route_name="agy_frontier",
    bridge_command=("ask-agy", "--to-model", FRONTIER_MODEL_ID, "--review"),
    reviewer_model_id=FRONTIER_MODEL_ID,
    reviewer_family="google",
    purpose="Seminar, contested-gold, or factual-sensitive review",
    input_usd_per_mtok=1.25,
    output_usd_per_mtok=10.0,
)
# Tooled seminar/factual reviewer: opencode transport with the sources MCP
# wired in, so factual/decolonization findings are grounded (design D0/D5,
# #2156). Model per routing policy — see FRONTIER_OPENCODE_MODEL_ID TODO.
FRONTIER_OPENCODE_ROUTE = ReviewerRoute(
    route_name="opencode_frontier",
    bridge_command=("ask-opencode", "--model", FRONTIER_OPENCODE_MODEL_ID),
    reviewer_model_id=FRONTIER_OPENCODE_MODEL_ID,
    reviewer_family="google",
    purpose="Seminar/factual/contested-gold review, grounded via sources MCP over opencode",
    input_usd_per_mtok=0.12,
    output_usd_per_mtok=0.35,
    requires_mcp=True,
)
CLAUDE_SPOT_AUDIT_ROUTE = ReviewerRoute(
    route_name="claude_spot_audit",
    bridge_command=("ask-claude", "--to-model", CLAUDE_SPOT_AUDIT_MODEL_ID, "--review"),
    reviewer_model_id=CLAUDE_SPOT_AUDIT_MODEL_ID,
    reviewer_family="anthropic",
    purpose="Escalation/disputed spot audit only",
    input_usd_per_mtok=15.0,
    output_usd_per_mtok=75.0,
)
ROUTES: tuple[ReviewerRoute, ...] = (
    GEMMA_SURFACE_ROUTE,
    FRONTIER_FACTUAL_ROUTE,
    FRONTIER_OPENCODE_ROUTE,
    CLAUDE_SPOT_AUDIT_ROUTE,
)

_MEASURED_COST_PROFILES: dict[str, MeasuredCostProfile] = {
    "openrouter/google/gemma-4-31b-it": MeasuredCostProfile(
        label="gemma-4-31b-it",
        input_usd_per_mtok=0.12,
        output_usd_per_mtok=0.35,
        observed_tool_call_min=4,
        observed_tool_call_median=4.0,
        observed_tool_call_max=5,
        observed_wall_s_min=16.499,
        observed_wall_s_median=34.685,
        observed_wall_s_max=137.964,
        pricing_basis="OpenRouter gemma-4-31b-it pin",
    ),
    "openrouter/deepseek/deepseek-v4-pro": MeasuredCostProfile(
        label="deepseek-v4-pro",
        input_usd_per_mtok=0.435,
        output_usd_per_mtok=0.87,
        observed_tool_call_min=10,
        observed_tool_call_median=15.5,
        observed_tool_call_max=17,
        observed_wall_s_min=164.376,
        observed_wall_s_median=210.8475,
        observed_wall_s_max=267.781,
        pricing_basis="DeepSeek API deepseek-v4-pro cache-miss pricing",
    ),
    "openrouter/deepseek/deepseek-v4-flash": MeasuredCostProfile(
        label="deepseek-v4-flash",
        input_usd_per_mtok=0.14,
        output_usd_per_mtok=0.28,
        observed_tool_call_min=15,
        observed_tool_call_median=30.0,
        observed_tool_call_max=35,
        observed_wall_s_min=140.463,
        observed_wall_s_median=170.207,
        observed_wall_s_max=238.279,
        pricing_basis="DeepSeek API deepseek-v4-flash cache-miss pricing",
    ),
}


def normalize_family(raw: Any) -> str | None:
    """Normalize agent/model labels into cross-review family buckets."""

    if raw is None:
        return None
    text = str(raw).strip().lower()
    if not text:
        return None
    text = text.replace("_", "-")
    if "deepseek" in text:
        return "deepseek"
    if any(marker in text for marker in ("gemma", "gemini", "agy", "google")):
        return "google"
    if any(marker in text for marker in ("codex", "openai", "gpt-")):
        return "openai"
    if any(marker in text for marker in ("claude", "anthropic", "opus", "sonnet")):
        return "anthropic"
    if any(marker in text for marker in ("cursor", "composer")):
        return "cursor"
    if any(marker in text for marker in ("grok", "xai")):
        return "xai"
    if "qwen" in text:
        return "qwen"
    return text.split()[0].split("(")[0].strip("-") or None


def route_for_review(
    *,
    policy_family: str,
    contested_gold_suppressed: bool = False,
    factual_sensitive: bool = False,
    escalation: bool = False,
) -> ReviewerRoute:
    """Return the allowed reviewer route for this content type."""

    if escalation:
        return CLAUDE_SPOT_AUDIT_ROUTE
    if policy_family == "seminar" or contested_gold_suppressed or factual_sensitive:
        # Grounded (tooled) opencode route — not the ungrounded agy route (#2156
        # D0). FRONTIER_FACTUAL_ROUTE stays defined for fallback/reference.
        return FRONTIER_OPENCODE_ROUTE
    return GEMMA_SURFACE_ROUTE


def assert_mcp_required_for_policy(*, policy_family: str, route: ReviewerRoute) -> None:
    """Fail closed if a grounded policy resolves to a prompt-only route."""

    if policy_family.strip().lower() == "seminar" and not route.requires_mcp:
        raise ReviewerRouteError(
            "seminar live Tier-2 route must require the sources MCP; "
            f"route={route.route_name!r} reviewer_model_id={route.reviewer_model_id!r}"
        )


def assert_route_allowed(route: ReviewerRoute) -> None:
    """Hard-ban DeepSeek/Hermes automated reviewer routes."""

    haystack = " ".join(
        [route.route_name, route.reviewer_model_id, route.reviewer_family, *route.bridge_command]
    )
    lowered = haystack.lower()
    if normalize_family(haystack) == "deepseek" or "hermes" in lowered:
        raise ReviewerRouteError("DeepSeek/Hermes reviewer routes are forbidden")


def resolve_author_lineage(
    *,
    level: str,
    slug: str,
    module_dir: Path,
    explicit_author_family: str | None = None,
) -> AuthorLineage:
    """Resolve module author family from explicit input, metadata, then git."""

    explicit = normalize_family(explicit_author_family)
    if explicit:
        return AuthorLineage(family=explicit, source="explicit", evidence=explicit_author_family)
    metadata = _lineage_from_metadata(level=level, slug=slug, module_dir=module_dir)
    if metadata.available:
        return metadata
    git_lineage = _lineage_from_git(level=level, slug=slug, module_dir=module_dir)
    if git_lineage.available:
        return git_lineage
    return AuthorLineage(
        family=None,
        source="unavailable",
        evidence="pass --author-family for live reviewer runs",
    )


def validate_cross_family(route: ReviewerRoute, lineage: AuthorLineage) -> None:
    """Fail closed when reviewer and author are same-family or unknown."""

    assert_route_allowed(route)
    if not lineage.family:
        raise ReviewerLineageError("author family unavailable; pass --author-family")
    if route.reviewer_family == lineage.family:
        raise ReviewerSelfReviewError(
            f"self-review blocked: reviewer_family={route.reviewer_family} "
            f"author_family={lineage.family}"
        )


def estimate_tokens(text: str) -> int:
    """Return a conservative text-token estimate for budgeting."""

    return max(1, round(len(text.encode("utf-8")) / _TOKEN_DIVISOR))


def measured_cost_profile_for_model(model_id: str) -> MeasuredCostProfile | None:
    """Return the scorecard-measured cost profile for a reviewer model id."""

    lowered = model_id.strip().lower()
    if lowered in _MEASURED_COST_PROFILES:
        return _MEASURED_COST_PROFILES[lowered]
    for key, profile in _MEASURED_COST_PROFILES.items():
        if key.rsplit("/", 1)[-1] in lowered:
            return profile
    return None


def measured_cost_profile_for_policy(policy_family: str) -> MeasuredCostProfile:
    """Return the production scorecard profile used by the current policy route."""

    if policy_family.strip().lower() == "seminar":
        return _MEASURED_COST_PROFILES[FRONTIER_OPENCODE_MODEL_ID]
    return _MEASURED_COST_PROFILES[GEMMA_MODEL_ID]


def measured_estimated_cost_usd(
    *,
    prompt_tokens: int,
    completion_tokens: int,
    profile: MeasuredCostProfile,
) -> float:
    """Estimate token spend using measured model-class pricing."""

    cost = (
        prompt_tokens * profile.input_usd_per_mtok
        + completion_tokens * profile.output_usd_per_mtok
    ) / 1_000_000
    return round(cost, 6)


def measured_cost_basis(profile: MeasuredCostProfile) -> str:
    """Return the audit basis string attached to every measured estimate."""

    return f"{SCORECARD_COST_BASIS}; profile={profile.label}; pricing={profile.pricing_basis}"


def estimate_route_cost(
    prompt: str,
    route: ReviewerRoute,
    *,
    completion_tokens: int | None = None,
    policy_family: str | None = None,
) -> dict[str, Any]:
    """Estimate route-specific spend for one reviewer call."""

    prompt_tokens = estimate_tokens(prompt)
    estimated_completion_tokens = completion_tokens or (900 if policy_family == "seminar" else 600)
    profile = measured_cost_profile_for_model(route.reviewer_model_id)
    if profile is None:
        cost = (
            prompt_tokens * route.input_usd_per_mtok
            + estimated_completion_tokens * route.output_usd_per_mtok
        ) / 1_000_000
        estimated_cost_usd = round(cost, 6)
        measured_fields: dict[str, Any] = {}
        basis = "route-specific prompt byte estimate; no scorecard profile for reviewer model"
    else:
        estimated_cost_usd = measured_estimated_cost_usd(
            prompt_tokens=prompt_tokens,
            completion_tokens=estimated_completion_tokens,
            profile=profile,
        )
        measured_fields = profile.estimate_fields()
        basis = measured_cost_basis(profile)
    return {
        "policy_family": policy_family,
        "route_name": route.route_name,
        "reviewer_model_id": route.reviewer_model_id,
        "reviewer_family": route.reviewer_family,
        "estimated_prompt_tokens": prompt_tokens,
        "estimated_completion_tokens": estimated_completion_tokens,
        "estimated_total_tokens": prompt_tokens + estimated_completion_tokens,
        "estimated_cost_usd": estimated_cost_usd,
        **measured_fields,
        "basis": basis,
    }


def live_batch_preflight(routes: Sequence[ReviewerRoute], *, timeout_s: int = 10) -> dict[str, Any]:
    """Verify the live Tier-2 transport before a broad batch spends quota."""
    unique_routes = _unique_routes(routes)
    if not unique_routes:
        return {
            "status": "skipped",
            "reason": "no_live_routes",
            "routes": [],
        }
    opencode = shutil.which("opencode")
    if not opencode:
        raise ReviewerPreflightError(
            "opencode_unavailable",
            "opencode CLI not found on PATH; live Tier-2 batch preflight cannot proceed",
        )
    for route in unique_routes:
        try:
            assert_route_allowed(route)
            if route.requires_mcp:
                _assert_sources_mcp_available()
        except ReviewerRouteError as exc:
            raise ReviewerPreflightError("route_disallowed", str(exc)) from exc
        except ReviewerProviderError as exc:
            raise ReviewerPreflightError("sources_mcp_unavailable", str(exc)) from exc
    try:
        proc = subprocess.run(
            [opencode, "models"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        raise ReviewerPreflightError("opencode_models_timeout", str(exc)) from exc
    except OSError as exc:
        raise ReviewerPreflightError("opencode_models_unavailable", str(exc)) from exc
    if proc.returncode != 0:
        message = (proc.stderr or proc.stdout or "opencode models failed").strip()
        raise ReviewerPreflightError("opencode_models_failed", message[-1000:])
    model_listing = f"{proc.stdout}\n{proc.stderr}"
    missing = [
        route.reviewer_model_id
        for route in unique_routes
        if not _model_list_contains(model_listing, route.reviewer_model_id)
    ]
    if missing:
        raise ReviewerPreflightError(
            "reviewer_model_unavailable",
            "opencode models did not list required reviewer model(s): " + ", ".join(missing),
        )
    return {
        "status": "passed",
        "reason": None,
        "routes": [route.route_name for route in unique_routes],
        "reviewer_model_ids": [route.reviewer_model_id for route in unique_routes],
        "sources_mcp_required": any(route.requires_mcp for route in unique_routes),
    }


def _unique_routes(routes: Sequence[ReviewerRoute]) -> list[ReviewerRoute]:
    unique: list[ReviewerRoute] = []
    seen: set[str] = set()
    for route in routes:
        key = f"{route.route_name}\0{route.reviewer_model_id}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(route)
    return unique


def _model_list_contains(model_listing: str, model_id: str) -> bool:
    text = model_listing.lower()
    clean = model_id.strip().lower()
    tail = clean.rsplit("/", 1)[-1]
    return clean in text or tail in text


def prompt_template_hash() -> str:
    """Stable hash of the calibrated reviewer prompt template."""

    return _sha256_text(llm_reviewer.load_reviewer_prompt_template())


class LiveReviewerDispatcher:
    """Callable reviewer that routes and invokes the approved live model."""

    def __init__(
        self,
        *,
        policy_family: str,
        gate_version: str,
        contested_gold_suppressed: bool = False,
        factual_sensitive: bool = False,
        escalation: bool = False,
        author_family: str | None = None,
        runner: ProviderRunner | None = None,
    ) -> None:
        self.policy_family = policy_family
        self.gate_version = gate_version
        self.contested_gold_suppressed = contested_gold_suppressed
        self.factual_sensitive = factual_sensitive
        self.escalation = escalation
        self.author_family = author_family
        self.runner = runner or invoke_bridge_route

    def route(self) -> ReviewerRoute:
        return route_for_review(
            policy_family=self.policy_family,
            contested_gold_suppressed=self.contested_gold_suppressed,
            factual_sensitive=self.factual_sensitive,
            escalation=self.escalation,
        )

    def __call__(self, target: Any, prompt: str) -> DispatchResult:
        route = self.route()
        lineage = resolve_author_lineage(
            level=str(target.level),
            slug=str(target.slug),
            module_dir=Path(target.module_dir),
            explicit_author_family=self.author_family,
        )
        validate_cross_family(route, lineage)
        task_id = f"llm-qg-{target.level}-{target.slug}-{uuid4().hex[:8]}"
        if self.runner is invoke_bridge_route:
            raw = invoke_bridge_route(
                route,
                prompt,
                task_id,
                module_dir=Path(target.module_dir),
            )
        else:
            raw = self.runner(route, prompt, task_id)
        if isinstance(raw, DispatchResult):
            result = raw
        else:
            result = DispatchResult(
                response_text=str(raw),
                reviewer_model_id=route.reviewer_model_id,
                reviewer_family=route.reviewer_family,
                route_name=route.route_name,
                observed_prompt_tokens=estimate_tokens(prompt),
                observed_completion_tokens=estimate_tokens(str(raw)),
                observed_cost_usd=_cost_for_observed_text(prompt, str(raw), route),
            )
        if (
            result.reviewer_model_id != route.reviewer_model_id
            or result.reviewer_family != route.reviewer_family
            or result.route_name != route.route_name
        ):
            raise ReviewerProviderError("provider returned mismatched reviewer identity")
        # This metadata is emitted only after this dispatcher itself resolved
        # module lineage and accepted the route as cross-family.  QG workflow
        # captures additionally bind it to this concrete dispatcher path; a
        # caller-provided callback cannot promote itself by supplying fields
        # with the same names.
        return replace(
            result,
            execution_provenance={
                "kind": "live_reviewer_dispatcher",
                "dispatcher": "LiveReviewerDispatcher",
                "route_name": route.route_name,
            },
            author_lineage={
                "family": lineage.family,
                "source": lineage.source,
                "evidence": lineage.evidence,
            },
            cross_family_validated=True,
        )


def invoke_bridge_route(
    route: ReviewerRoute,
    prompt: str,
    task_id: str,
    *,
    no_module_persistence: bool = False,
    artifacts_dir: Path | None = None,
    module_dir: Path | None = None,
) -> DispatchResult:
    """Invoke the route's approved backend and return response text.

    Gemma uses the same opencode helper behind ``ask-gemma`` because that bridge
    command records responses in the inbox rather than returning them. AGY and
    Claude are invoked through their public bridge commands with temporary
    output files where supported.
    """

    assert_route_allowed(route)
    if route.route_name == GEMMA_SURFACE_ROUTE.route_name:
        # Surface/register review is prompt-only per design D1 — no MCP gate.
        return _invoke_opencode_reviewer(
            prompt,
            route,
            default_timeout_s=900,
            require_mcp=False,
            no_module_persistence=no_module_persistence,
            artifacts_dir=artifacts_dir,
            module_dir=module_dir,
        )
    if route.route_name == FRONTIER_OPENCODE_ROUTE.route_name:
        # Seminar/factual review MUST be grounded — fail-fast if the sources MCP
        # is not configured + reachable (design D0; step-1 lesson). Browsing +
        # dense tool sweeps run long, so allow a wider timeout than gemma.
        if not route.requires_mcp:
            raise ReviewerRouteError("opencode frontier route must require the sources MCP")
        return _invoke_opencode_reviewer(
            prompt,
            route,
            default_timeout_s=1800,
            require_mcp=route.requires_mcp,
            no_module_persistence=no_module_persistence,
            artifacts_dir=artifacts_dir,
            module_dir=module_dir,
        )
    if route.route_name == FRONTIER_FACTUAL_ROUTE.route_name:
        return _invoke_output_path_bridge(
            route,
            prompt,
            task_id,
            [
                ".venv/bin/python",
                "scripts/ai_agent_bridge/__main__.py",
                "ask-agy",
                "-",
                "--task-id",
                task_id,
                "--to-model",
                route.reviewer_model_id,
                "--review",
                "--stdout-only",
                "--output-path",
            ],
        )
    if route.route_name == CLAUDE_SPOT_AUDIT_ROUTE.route_name:
        return _invoke_agent_runtime("claude", route, prompt, task_id)
    raise ReviewerRouteError(f"unsupported reviewer route: {route.route_name}")


def build_canary_prompt(level: str) -> str:
    """Build a canary module prompt using the calibrated reviewer template."""

    canaries = llm_qg_canaries.list_canaries(level)
    snippets = "\n\n".join(f"- `{canary.canary_id}`: {canary.snippet}" for canary in canaries)
    return llm_reviewer.build_reviewer_prompt(
        level=level,
        slug=f"canary-{_canonical_level(level)}",
        module_md=(
            "# LLM-QG Canary Module\n\n"
            "Review these snippets exactly as learner-facing module content.\n\n"
            f"{snippets}\n"
        ),
        activities_yaml="[]\n",
        vocabulary_yaml="[]\n",
        resources_yaml="[]\n",
    )


def run_canary(
    *,
    level: str,
    gate_version: str,
    author_family: str,
    runner: ProviderRunner | None = None,
) -> dict[str, Any]:
    """Run a live canary through the same dispatcher route used by a batch."""

    policy = policy_for_level(level)
    prompt = build_canary_prompt(level)
    dispatcher = LiveReviewerDispatcher(
        policy_family=policy.family,
        gate_version=gate_version,
        author_family=author_family,
        runner=runner,
    )
    target = _CanaryTarget(level=level, slug=f"canary-{_canonical_level(level)}", module_dir=PROJECT_ROOT)
    result = dispatcher(target, prompt)
    payload = _json_payload_from_response(result.response_text)
    report = llm_qg_canaries.evaluate_canaries(payload, level)
    route = dispatcher.route()
    return {
        "schema_version": CANARY_SCHEMA_VERSION,
        "created_at": _now_z(),
        "level": _canonical_level(level),
        "gate_version": gate_version,
        "prompt_hash": _sha256_text(prompt),
        "prompt_template_hash": prompt_template_hash(),
        "reviewer_model_id": route.reviewer_model_id,
        "reviewer_family": route.reviewer_family,
        "route_name": route.route_name,
        "passed": bool(report.get("passed")),
        "report": report,
    }


def canary_artifact_passes(path: Path, *, level: str, gate_version: str, route: ReviewerRoute) -> bool:
    """Return True only when a canary artifact exactly matches this live route."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return canary_payload_passes(payload, level=level, gate_version=gate_version, route=route)


def canary_payload_passes(
    payload: Mapping[str, Any],
    *,
    level: str,
    gate_version: str,
    route: ReviewerRoute,
) -> bool:
    """Validate exact canary identity without reading from disk."""

    return (
        payload.get("schema_version") == CANARY_SCHEMA_VERSION
        and payload.get("level") == _canonical_level(level)
        and payload.get("gate_version") == gate_version
        and payload.get("prompt_template_hash") == prompt_template_hash()
        and payload.get("reviewer_model_id") == route.reviewer_model_id
        and payload.get("reviewer_family") == route.reviewer_family
        and payload.get("route_name") == route.route_name
        and payload.get("passed") is True
    )


def read_daily_spend(path: Path | None = None, *, day: date | None = None) -> float:
    """Read local daily reviewer spend from JSONL telemetry."""

    ledger = path or DEFAULT_DAILY_SPEND_PATH
    if not ledger.exists():
        return 0.0
    wanted = (day or datetime.now(UTC).date()).isoformat()
    total = 0.0
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("date") != wanted:
            continue
        total += float(row.get("observed_cost_usd") or row.get("estimated_cost_usd") or 0.0)
    return round(total, 6)


def append_daily_spend(
    *,
    path: Path | None = None,
    level: str,
    slug: str,
    route: ReviewerRoute,
    estimated_cost_usd: float,
    observed_cost_usd: float | None,
) -> None:
    """Persist one local spend row under ``data/telemetry``."""

    ledger = path or DEFAULT_DAILY_SPEND_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    row = {
        "timestamp": now.isoformat().replace("+00:00", "Z"),
        "date": now.date().isoformat(),
        "level": level,
        "slug": slug,
        "route_name": route.route_name,
        "reviewer_model_id": route.reviewer_model_id,
        "reviewer_family": route.reviewer_family,
        "estimated_cost_usd": round(float(estimated_cost_usd), 6),
        "observed_cost_usd": (
            round(float(observed_cost_usd), 6) if observed_cost_usd is not None else None
        ),
    }
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _lineage_from_metadata(*, level: str, slug: str, module_dir: Path) -> AuthorLineage:
    for path in _metadata_candidates(level=level, slug=slug, module_dir=module_dir):
        if not path.exists() or not path.is_file():
            continue
        data = _read_structured(path)
        if not isinstance(data, Mapping):
            continue
        family = _family_from_mapping(data)
        if family:
            return AuthorLineage(family=family, source=str(path), evidence=_evidence_from_mapping(data))
    return AuthorLineage(family=None, source="metadata_missing")


def _metadata_candidates(*, level: str, slug: str, module_dir: Path) -> list[Path]:
    level_dir = module_dir.parent
    return [
        module_dir / "build_meta.json",
        module_dir / "writer_meta.json",
        module_dir / "dispatch_meta.json",
        module_dir / "module_meta.json",
        level_dir / "meta" / f"{slug}.yaml",
        level_dir / "meta" / f"{slug}.yml",
        level_dir / "orchestration" / slug / "build_meta.json",
        *sorted((level_dir / "orchestration" / slug / "dispatch").glob("*-meta.json")),
        PROJECT_ROOT / "curriculum" / "l2-uk-en" / level / "meta" / f"{slug}.yaml",
        *sorted(
            (
                PROJECT_ROOT
                / "curriculum"
                / "l2-uk-en"
                / level
                / "orchestration"
                / slug
                / "dispatch"
            ).glob("*-meta.json")
        ),
    ]


def _read_structured(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        if path.suffix in {".yaml", ".yml"}:
            return yaml.safe_load(text)
        return json.loads(text)
    except (json.JSONDecodeError, yaml.YAMLError):
        return None


def _family_from_mapping(data: Mapping[str, Any]) -> str | None:
    for field in _AUTHOR_FIELDS:
        family = normalize_family(data.get(field))
        if family:
            return family
    for value in data.values():
        if isinstance(value, Mapping):
            family = _family_from_mapping(value)
            if family:
                return family
    return None


def _evidence_from_mapping(data: Mapping[str, Any]) -> str | None:
    for field in _AUTHOR_FIELDS:
        value = data.get(field)
        if isinstance(value, str) and value.strip():
            return f"{field}={value.strip()}"
    return None


def _lineage_from_git(*, level: str, slug: str, module_dir: Path) -> AuthorLineage:
    paths = _module_git_paths(level=level, slug=slug, module_dir=module_dir)
    if not paths:
        return AuthorLineage(family=None, source="git_no_paths")
    try:
        result = subprocess.run(
            ["git", "log", "--format=%B%n---END---", "--max-count=30", "--", *paths],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return AuthorLineage(family=None, source="git_unavailable")
    if result.returncode != 0:
        return AuthorLineage(family=None, source="git_failed", evidence=result.stderr[-400:])
    for body in result.stdout.split("---END---"):
        family = _family_from_commit_body(body)
        if family:
            return AuthorLineage(family=family, source="git_history", evidence=body.strip().splitlines()[0])
    return AuthorLineage(family=None, source="git_no_family")


def _module_git_paths(*, level: str, slug: str, module_dir: Path) -> list[str]:
    candidates = [module_dir]
    level_dir = PROJECT_ROOT / "curriculum" / "l2-uk-en" / level
    candidates.extend(
        [
            level_dir / slug,
            level_dir / "activities" / f"{slug}.yaml",
            level_dir / "vocabulary" / f"{slug}.yaml",
            level_dir / "resources" / f"{slug}.yaml",
            level_dir / "meta" / f"{slug}.yaml",
        ]
    )
    out: list[str] = []
    for path in candidates:
        try:
            rel = path.resolve().relative_to(PROJECT_ROOT)
        except (OSError, ValueError):
            continue
        text = str(rel)
        if text not in out:
            out.append(text)
    return out


def _family_from_commit_body(body: str) -> str | None:
    for match in _X_AGENT_RE.finditer(body):
        family = normalize_family(match.group(1))
        if family:
            return family
    for match in _COAUTHOR_RE.finditer(body):
        family = normalize_family(match.group(1))
        if family:
            return family
    return None


def _invoke_output_path_bridge(
    route: ReviewerRoute,
    prompt: str,
    task_id: str,
    base_argv: Sequence[str],
) -> DispatchResult:
    with tempfile.TemporaryDirectory(prefix="llm-reviewer-") as tmp:
        output_path = Path(tmp) / "response.txt"
        argv = [*base_argv, str(output_path)]
        try:
            result = subprocess.run(
                argv,
                input=prompt,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=1800,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ReviewerProviderError(str(exc)) from exc
        if result.returncode != 0:
            raise ReviewerProviderError(result.stderr[-2000:] or result.stdout[-2000:])
        try:
            response = output_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ReviewerProviderError(f"bridge did not write response: {exc}") from exc
    return _result_from_text(prompt, response, route)


def _invoke_agent_runtime(agent: str, route: ReviewerRoute, prompt: str, task_id: str) -> DispatchResult:
    try:
        from scripts.agent_runtime import runner as agent_runner

        result = agent_runner.invoke(
            agent,
            prompt,
            mode="read-only",
            cwd=PROJECT_ROOT,
            model=route.reviewer_model_id,
            task_id=task_id,
            session_id=None,
            tool_config=None,
            entrypoint="bridge",
            hard_timeout=1800,
            stall_timeout=600,
        )
    except Exception as exc:
        raise ReviewerProviderError(str(exc)) from exc
    if not result.ok or not result.response:
        raise ReviewerProviderError(result.stderr_excerpt or "provider returned no response")
    usage = result.usage_record or {}
    return DispatchResult(
        response_text=result.response,
        reviewer_model_id=route.reviewer_model_id,
        reviewer_family=route.reviewer_family,
        route_name=route.route_name,
        observed_prompt_tokens=estimate_tokens(prompt),
        observed_completion_tokens=estimate_tokens(result.response),
        observed_cost_usd=_cost_for_observed_text(prompt, result.response, route),
        usage=usage,
    )


def _result_from_text(prompt: str, response: str, route: ReviewerRoute) -> DispatchResult:
    return DispatchResult(
        response_text=response,
        reviewer_model_id=route.reviewer_model_id,
        reviewer_family=route.reviewer_family,
        route_name=route.route_name,
        observed_prompt_tokens=estimate_tokens(prompt),
        observed_completion_tokens=estimate_tokens(response),
        observed_cost_usd=_cost_for_observed_text(prompt, response, route),
    )


def reviewer_prompt_metadata(prompt: str) -> tuple[str, str] | None:
    """Return (level, slug) from the calibrated reviewer prompt metadata block."""
    match = _PROMPT_LEVEL_SLUG_RE.search(prompt)
    if match is None:
        return None
    return match.group("level").strip().lower(), match.group("slug").strip()


def module_dir_for_review(level: str, slug: str, *, module_dir: Path | None = None) -> Path:
    """Resolve the module directory used for reviewer markdown persistence."""
    if module_dir is not None:
        return module_dir
    return PROJECT_ROOT / "curriculum" / "l2-uk-en" / level.strip().lower() / slug.strip()


def persist_reviewer_module_review(
    *,
    level: str,
    slug: str,
    response_text: str,
    module_dir: Path | None = None,
    artifacts_dir: Path | None = None,
) -> Path:
    """Persist raw reviewer output for module-keyed workflows.

    Default layout: ``curriculum/l2-uk-en/{level}/{slug}/review-review.md``.
    When ``artifacts_dir`` is set, writes under that directory instead.
    """
    if artifacts_dir is not None:
        path = artifacts_dir / f"{slug.strip()}-review.raw.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(response_text, encoding="utf-8")
        return path
    target_dir = module_dir_for_review(level, slug, module_dir=module_dir)
    path = target_dir / REVIEWER_MODULE_REVIEW_NAME
    target_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(response_text, encoding="utf-8")
    return path


def _invoke_opencode_reviewer(
    prompt: str,
    route: ReviewerRoute,
    *,
    default_timeout_s: int,
    require_mcp: bool,
    no_module_persistence: bool = False,
    artifacts_dir: Path | None = None,
    module_dir: Path | None = None,
) -> DispatchResult:
    """Run a reviewer route over opencode, capturing tool telemetry.

    Both opencode reviewer routes (gemma surface + frontier factual) parse the
    NDJSON stream once so ``tool_call_count``/``tools_used`` land on the
    DispatchResult. ``require_mcp`` gates the grounded factual route on a
    configured + reachable sources MCP.
    """
    # Routing guard at the transport (codex review, PR #4500 finding 2): this
    # function runs its OWN opencode invocation — it never passes through the
    # bridge's guarded _run_opencode — so without this line a subscription-
    # family pin (openrouter/anthropic|openai|google/gemini-*) or a qwen pin
    # would reach OpenRouter unguarded from the reviewer/bakeoff paths.
    # RoutingGuardError deliberately propagates (config error, not a per-cell
    # provider flake).
    from scripts.ai_agent_bridge.routing_guard import assert_model_routing_allowed

    assert_model_routing_allowed(route.reviewer_model_id, context="reviewer opencode transport")
    if require_mcp:
        _assert_sources_mcp_available()
    from scripts.ai_agent_bridge._opencode import _invoke_opencode_detailed

    # #4642 second leak path: the reviewer is a TOOL-USING model with default
    # write/edit tools, and opencode resolves both its project root and any
    # relative tool-write against the subprocess cwd. Run it from an out-of-repo
    # temp dir so a stray model write (e.g. the observed
    # curriculum/l2-uk-en/<level>/status/<slug>-review.json) lands in the
    # throwaway dir, never the checkout. Mirrors the neutral-cwd firewall the
    # subscription bare routes already use (qg_bakeoff._neutral_runtime_cwd).
    # The reviewer needs no repo files: module content is in the prompt and the
    # sources MCP is a remote endpoint from the global opencode config. Our own
    # deterministic persistence (persist_reviewer_module_review) uses absolute
    # PROJECT_ROOT paths, so it is unaffected by the subprocess cwd.
    try:
        with tempfile.TemporaryDirectory(prefix="llm-reviewer-cwd-") as reviewer_cwd:
            parse = _invoke_opencode_detailed(
                prompt,
                route.reviewer_model_id,
                output_format="json",
                default_timeout_s=default_timeout_s,
                cwd=Path(reviewer_cwd),
            )
    except SystemExit as exc:
        raise ReviewerProviderError(str(exc)) from exc
    result = _result_from_stream(prompt, parse, route)
    if not no_module_persistence:
        meta = reviewer_prompt_metadata(prompt)
        if meta is not None:
            level, slug = meta
            persist_reviewer_module_review(
                level=level,
                slug=slug,
                response_text=result.response_text,
                module_dir=module_dir,
                artifacts_dir=artifacts_dir,
            )
    return result


def _result_from_stream(prompt: str, parse: Any, route: ReviewerRoute) -> DispatchResult:
    """Build a DispatchResult from an ``OpencodeStreamParse`` (text + tools)."""
    tool_events = tuple(getattr(parse, "tool_events", ()) or ())
    response = getattr(parse, "text", "") or ""
    return DispatchResult(
        response_text=response,
        reviewer_model_id=route.reviewer_model_id,
        reviewer_family=route.reviewer_family,
        route_name=route.route_name,
        observed_prompt_tokens=estimate_tokens(prompt),
        observed_completion_tokens=estimate_tokens(response),
        observed_cost_usd=_cost_for_observed_text(prompt, response, route),
        tool_call_count=len(tool_events),
        tools_used=_distinct_tools(tool_events),
        tool_events=tuple(dict(event) for event in tool_events),
    )


def _distinct_tools(tool_events: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    """Distinct tool names in first-seen order across the run's tool events."""
    seen: list[str] = []
    for event in tool_events:
        name = event.get("tool")
        if isinstance(name, str) and name and name not in seen:
            seen.append(name)
    return tuple(seen)


# --- Deterministic reviewer gates (design D4) ------------------------------


def reviewer_retry_prompt(prompt: str, reason: str) -> str:
    """Append a deterministic retry reminder to the reviewer prompt."""
    if reason == DEEP_READ_REQUIRED:
        return f"{prompt}{_DEEP_READ_RETRY_REMINDER}"
    return f"{prompt}{_THEATRE_RETRY_REMINDER}"


def tool_events_from_dispatch_meta(dispatch_meta: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Return normalized tool events from dispatch metadata."""
    raw_events = dispatch_meta.get("tool_events")
    if not isinstance(raw_events, Sequence) or isinstance(raw_events, (str, bytes)):
        return ()
    return tuple(dict(event) for event in raw_events if isinstance(event, Mapping))


def tool_call_count_from_dispatch_meta(dispatch_meta: Mapping[str, Any]) -> int:
    """Return the deterministic tool-call count, preferring explicit metadata."""
    raw_count = dispatch_meta.get("tool_call_count")
    try:
        count = int(raw_count) if raw_count is not None else 0
    except (TypeError, ValueError):
        count = 0
    return max(count, len(tool_events_from_dispatch_meta(dispatch_meta)))


def enforce_tool_budget(dispatch_meta: Mapping[str, Any]) -> None:
    """Hard-fail reviewer runs that exceed the tool budget."""
    count = tool_call_count_from_dispatch_meta(dispatch_meta)
    if count > MAX_REVIEWER_TOOLS:
        raise ReviewerDispatchError(
            f"reviewer used {count} tools; hard cap is {MAX_REVIEWER_TOOLS}"
        )


def tool_call_anomaly_warning(
    dispatch_meta: Mapping[str, Any],
    estimate: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return a soft telemetry warning when tool use exceeds measured norms."""

    try:
        threshold = float(estimate.get("tool_call_anomaly_threshold"))
        observed_max = int(estimate.get("observed_tool_call_max"))
    except (TypeError, ValueError):
        return None
    count = tool_call_count_from_dispatch_meta(dispatch_meta)
    if count <= threshold:
        return None
    return {
        "kind": "tool_call_anomaly",
        "severity": "warning",
        "observed_tool_call_count": count,
        "observed_tool_call_max": observed_max,
        "tool_call_anomaly_threshold": threshold,
        "measured_cost_profile": estimate.get("measured_cost_profile"),
        "basis": estimate.get("basis"),
    }


def tool_theatre_violation(
    *,
    policy_family: str,
    payload: Mapping[str, Any],
    dispatch_meta: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return a theatre-gate violation for grounded routes, else None."""
    if not _requires_grounded_tools(policy_family, dispatch_meta):
        return None
    count = tool_call_count_from_dispatch_meta(dispatch_meta)
    if count <= 0:
        return {"status": INVALID_TOOL_THEATRE, "reason": "no_tool_calls"}

    events = tool_events_from_dispatch_meta(dispatch_meta)
    claim_tokens = _payload_claim_tokens(payload)
    if events:
        if not any(_source_event_relevant(event, claim_tokens) for event in events):
            return {"status": INVALID_TOOL_THEATRE, "reason": "irrelevant_tool_calls"}
        return None

    tools_used = dispatch_meta.get("tools_used")
    if (
        isinstance(tools_used, Sequence)
        and not isinstance(tools_used, (str, bytes))
        and any(_source_tool_name_relevant(str(tool), claim_tokens) for tool in tools_used)
    ):
        return None
    return {"status": INVALID_TOOL_THEATRE, "reason": "no_relevant_source_tool_calls"}


def deep_read_required(payload: Mapping[str, Any], dispatch_meta: Mapping[str, Any]) -> bool:
    """Return True when summary-only wiki access requires one forced retry."""
    events = tool_events_from_dispatch_meta(dispatch_meta)
    if not events:
        return False
    fact_checks = payload.get("fact_checks")
    if not isinstance(fact_checks, list):
        return False
    for fact_check in fact_checks:
        if not isinstance(fact_check, Mapping):
            continue
        if (
            fact_check.get("deep_read_attempted") is not True
            and _positive_verdict_summary_only(fact_check, events)
        ):
            return True
        verdict = str(fact_check.get("verdict") or "")
        if not verdict.startswith(("UNATTESTED", "UNVERIFIED")):
            continue
        if fact_check.get("deep_read_attempted") is True:
            continue
        claim_tokens = _tokenize(str(fact_check.get("claim") or ""))
        summary_seen = False
        deep_seen = False
        for event in events:
            if not _is_wiki_event(event):
                continue
            query_tokens = _event_query_tokens(event)
            if claim_tokens and not claim_tokens.intersection(query_tokens):
                continue
            mode = _event_mode(event)
            summary_seen = summary_seen or mode == "summary"
            deep_seen = deep_seen or mode in _DEEP_READ_WIKI_MODES
        if summary_seen and not deep_seen:
            return True
    return False


def mark_deep_read_attempted(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Mark all fact checks as having received the shared forced deep-read retry.

    The flag is only consumed by :func:`deep_read_required`, and the workflow has
    one shared retry budget, so marking every fact-check records that this
    reviewer response was evaluated after the forced retry opportunity.
    """
    out = dict(payload)
    marked: list[dict[str, Any]] = []
    for fact_check in payload.get("fact_checks", []):
        if not isinstance(fact_check, Mapping):
            continue
        item = dict(fact_check)
        item["deep_read_attempted"] = True
        marked.append(item)
    out["fact_checks"] = marked
    return out


# Guard 3 abstain-recovery threshold (task guard3-abstain). Only exact-match (verbatim)
# multi-output abstains are recovered as provenance-passed; fuzzy near-tie abstains stay
# fail-closed until audited. SequenceMatcher.ratio() of a normalized verbatim window is 1.0.
_V2_ABSTAIN_RECOVERY_MIN_SIM = 1.0


def _v2_abstain_recovered(res) -> bool:
    """Guard 3 abstain-recovery (task guard3-abstain; fleet-reviewed codex/agy/cursor).

    ``res.abstained`` means the excerpt is verbatim-present in >=2 DIFFERENT captured tool
    outputs — Layer A provenance SATISFIED, source ambiguous. "Which of the real sources" is
    attribution (Layer B, not yet built), NOT a Layer A fabrication. The gate returns
    ``anchored=False`` for that ambiguity; enforcement previously mapped abstain to a hard
    REJECT, over-rejecting ~117 gold-true groundings (all sim=1.0). Recover ONLY exact-match
    (``similarity == 1.0``) multi-output abstains; fuzzy near-tie abstains (``similarity < 1.0``)
    stay fail-closed until audited (codex caution). The 5-round-hardened gate is untouched;
    it keeps ``source_index=None`` on abstain and callers record ``anchor_abstained`` so a future
    Layer B must still entail the excerpt against the RAW output (no self-proving).

    Excerpts with no salient tokens are rejected (``no_salient_anchor``) before Guard 3, but
    boilerplate WITH salient tokens (e.g. an error string) can reach abstain and recover here —
    that is a Layer B substance concern, not a Layer A fabrication (panel-accepted; matches v1's
    exact-substring behavior). Near-copy fabrication (digit/name swap, truncation) never reaches
    ``abstained=True`` — it fails the per-window salient-token opcode alignment first.
    """
    return res.abstained and res.similarity >= _V2_ABSTAIN_RECOVERY_MIN_SIM


def enforce_grounding_against_tool_events(
    payload: Mapping[str, Any],
    dispatch_meta: Mapping[str, Any],
    *,
    policy_family: str,
    gate_version: str | None = None,
) -> GroundingGateResult:
    """Drop findings whose claimed grounding is not present in this run's tools."""
    resolved_version = gate_version or os.environ.get("QG_GROUNDING_GATE_VERSION", "v1")

    events = tool_events_from_dispatch_meta(dispatch_meta)
    if not events:
        return GroundingGateResult(payload=dict(payload))

    kept_findings: list[dict[str, Any]] = []
    ungrounded = 0
    required_ungrounded = 0
    for finding in payload.get("findings", []):
        if not isinstance(finding, Mapping):
            continue
        item = dict(finding)
        grounding = item.get("grounding")
        if isinstance(grounding, Mapping):
            if resolved_version == "v2":
                from scripts.audit import grounding_gate_v2
                res = grounding_gate_v2.anchor_evidence_to_events(grounding, events)
                recovered_abstain = _v2_abstain_recovered(res)
                is_matched = res.anchored or recovered_abstain
                item["anchor_recovered_ambiguous"] = bool(recovered_abstain)
            else:
                is_matched = _grounding_matches_events(grounding, events)

            if not is_matched:
                ungrounded += 1
                if qg_schema.finding_requires_grounding(item, policy_family):
                    required_ungrounded += 1
                continue
        kept_findings.append(item)

    invalid_fact_checks = 0
    inadmissible_positive_verdicts = 0
    checked_fact_checks: list[dict[str, Any]] = []
    raw_fact_checks = payload.get("fact_checks", [])
    for fact_check in raw_fact_checks if isinstance(raw_fact_checks, list) else []:
        if not isinstance(fact_check, Mapping):
            continue
        item = dict(fact_check)
        grounding = item.get("grounding")
        if isinstance(grounding, Mapping):
            if resolved_version == "v2":
                from scripts.audit import grounding_gate_v2
                res = grounding_gate_v2.anchor_evidence_to_events(grounding, events)
                recovered_abstain = _v2_abstain_recovered(res)
                is_matched = res.anchored or recovered_abstain
                item["anchor_similarity"] = res.similarity
                item["anchor_abstained"] = res.abstained
                item["anchor_recovered_ambiguous"] = bool(recovered_abstain)
                item["grounding_gate_version"] = "v2"
                if res.anchor_low_signal_reason is not None:
                    item["anchor_low_signal_reason"] = res.anchor_low_signal_reason
            else:
                is_matched = _grounding_matches_events(grounding, events)

            if not is_matched:
                invalid_fact_checks += 1
                # Diagnostic tag: this grounding is not backed by a matching
                # (tool, query, excerpt) event in this run. The verdict is left
                # untouched here so the live pipeline's semantics are unchanged;
                # the bakeoff scorer reads this tag to strip the row from the
                # live-admissible column (STRICT grounding, #4761).
                item["grounding_admissible"] = False
            elif item.get("deep_read_attempted") is True and _positive_verdict_summary_only(item, events):
                original_verdict = str(item.get("verdict") or "")
                item["original_verdict"] = original_verdict
                item["verdict"] = "UNVERIFIED_INSUFFICIENT_SEARCH"
                item["admissibility_downgraded"] = True
                inadmissible_positive_verdicts += 1
        checked_fact_checks.append(item)

    out = dict(payload)
    out["findings"] = kept_findings
    if isinstance(raw_fact_checks, list):
        out["fact_checks"] = checked_fact_checks
    return GroundingGateResult(
        payload=out,
        ungrounded_findings=ungrounded,
        required_ungrounded_findings=required_ungrounded,
        invalid_fact_checks=invalid_fact_checks,
        inadmissible_positive_verdicts=inadmissible_positive_verdicts,
    )


def factual_sweep_incomplete(
    payload: Mapping[str, Any],
    *,
    policy_family: str,
    invalid_fact_checks: int = 0,
) -> bool:
    """Return True when a seminar response lacks a complete factual sweep."""
    if str(policy_family).strip().lower() != "seminar":
        return False
    fact_checks = payload.get("fact_checks")
    if not isinstance(fact_checks, list) or not fact_checks:
        return True
    if invalid_fact_checks:
        return True
    for fact_check in fact_checks:
        if not isinstance(fact_check, Mapping):
            return True
        if fact_check.get("verdict") == "UNVERIFIED_INSUFFICIENT_SEARCH":
            return True
    return False


def _requires_grounded_tools(policy_family: str, dispatch_meta: Mapping[str, Any]) -> bool:
    route_name = str(dispatch_meta.get("route_name") or "")
    return str(policy_family).strip().lower() == "seminar" or route_name == FRONTIER_OPENCODE_ROUTE.route_name


def is_source_tool(tool: str) -> bool:
    """Return whether a transport spelling names a configured sources tool.

    The check intentionally preserves the dispatcher's historical accepted
    spellings while normalizing MCP/server wrappers through the shared anchor
    primitive.  Consumers that need the same source-tool trust boundary (such
    as certification replay) must use this predicate rather than reimplement
    literal transport-prefix checks.
    """
    clean = str(tool or "").strip().casefold()
    canonical = anchor_primitives.canonical_tool_name(clean)
    return (
        clean.startswith(_SOURCE_TOOL_PREFIXES)
        or canonical.startswith(("search_", "query_"))
    )


def _is_source_tool(tool: str) -> bool:
    """Backward-compatible private spelling for existing gate helpers."""
    return is_source_tool(tool)


def _source_event_relevant(event: Mapping[str, Any], claim_tokens: set[str]) -> bool:
    tool = str(event.get("tool") or "")
    if not _is_source_tool(tool):
        return False
    if not claim_tokens:
        return True
    return bool(claim_tokens.intersection(_event_query_tokens(event)))


def _source_tool_name_relevant(tool: str, claim_tokens: set[str]) -> bool:
    if not _is_source_tool(tool):
        return False
    if not claim_tokens:
        return True
    return bool(claim_tokens.intersection(_tokenize(tool)))


def _payload_claim_tokens(payload: Mapping[str, Any]) -> set[str]:
    texts: list[str] = []
    fact_checks = payload.get("fact_checks")
    if isinstance(fact_checks, list):
        texts.extend(str(item.get("claim") or "") for item in fact_checks if isinstance(item, Mapping))
    findings = payload.get("findings")
    if isinstance(findings, list):
        for finding in findings:
            if isinstance(finding, Mapping):
                texts.append(str(finding.get("excerpt") or ""))
                texts.append(str(finding.get("message") or ""))
    return _tokenize(" ".join(texts))


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN_RE.findall(text) if len(token) >= 3}


def _event_query_tokens(event: Mapping[str, Any]) -> set[str]:
    return _tokenize(" ".join(_tool_query_candidates(event)))


def _tool_query_candidates(event: Mapping[str, Any]) -> list[str]:
    tool_input = event.get("input")
    candidates: list[str] = []
    if isinstance(tool_input, Mapping):
        for key in ("query", "q", "claim", "word", "headword", "lemma", "text"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                candidates.append(value.strip())
        query = tool_input.get("query") or tool_input.get("q")
        mode = tool_input.get("mode")
        if isinstance(query, str) and isinstance(mode, str):
            candidates.append(f"{query.strip()} mode={mode.strip()}")
        with suppress(TypeError, ValueError):
            candidates.append(json.dumps(tool_input, ensure_ascii=False, sort_keys=True))
    elif isinstance(tool_input, str) and tool_input.strip():
        candidates.append(tool_input.strip())
    return candidates


def _event_mode(event: Mapping[str, Any]) -> str:
    tool_input = event.get("input")
    if isinstance(tool_input, Mapping):
        mode = tool_input.get("mode")
        if isinstance(mode, str):
            return mode.strip().lower()
    return ""


def _is_wiki_event(event: Mapping[str, Any]) -> bool:
    tool = str(event.get("tool") or "").lower()
    return any(marker in tool for marker in _WIKI_TOOL_MARKERS)


def _positive_verdict_summary_only(fact_check: Mapping[str, Any], events: Sequence[Mapping[str, Any]]) -> bool:
    """True when a positive verdict's grounding is backed only by shallow wiki access.

    Fail-closed on wiki mode (cursor review of #4429): any matching wiki event
    whose mode is NOT a deep-read mode (``summary``, ``search``, missing/empty,
    unknown labels) counts as shallow — otherwise a summary-grade CONFIRMED
    slips through admissibility whenever telemetry omits the mode.
    """
    verdict = str(fact_check.get("verdict") or "")
    if verdict not in _POSITIVE_FACT_CHECK_VERDICTS:
        return False
    grounding = fact_check.get("grounding")
    if not isinstance(grounding, Mapping):
        return False
    matches = _grounding_matching_events(grounding, events)
    return (
        bool(matches)
        and all(_is_wiki_event(event) for event in matches)
        and not any(_event_mode(event) in _DEEP_READ_WIKI_MODES for event in matches)
    )


def _grounding_matches_events(
    grounding: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
) -> bool:
    """True when the grounding is backed by a captured tool event.

    Match semantics (live-proof fix, 2026-07-05): tool name + query must match
    a captured event AND the normalized excerpt must be present in that event's
    captured output. Abridged excerpts with ellipsis markers match only when all
    retained normalized segments appear in order in the SAME event output, with
    short-glue and evidence-mass guards. ``tool_call_id`` is ADVISORY — the transport-level id
    (e.g. ``chatcmpl-tool-…``) is never shown to the model, so requiring
    equality failed every legitimate grounding in the live «Веснянки» proof
    while adding nothing against fabrication (a fabricated excerpt still has
    to appear in a real captured output for a query really made).
    """
    return bool(_grounding_matching_events(grounding, events))


def _canonical_tool_name(name: Any) -> str:
    """Canonicalize an MCP tool name so grounding vs event comparison is transport-agnostic.

    Different harnesses and models spell the same tool differently:
    - opencode / bare: ``sources_query_wikipedia``, ``query_wikipedia``
    - agent-runtime adapters: ``mcp__sources__query_wikipedia``, ``mcp__sources_query_wikipedia``
    - codex/gpt-5.5 etc (dot form): ``mcp__sources.query_wikipedia``, ``sources.query_wikipedia``

    All refer to the same tool; the grounding gate must not fail on spelling.
    Strips the ``mcp__``/``mcp_`` wrapper. Then:
    - if a ``.`` is present, takes everything after the FIRST dot (``server.tool`` form;
      dot never appears inside a tool name) — but ONLY when both the server and tool
      segments are non-empty; a malformed ``sources.`` / ``.tool`` is left unchanged so
      the gate fails closed rather than collapsing to "" (which would wildcard the filter)
    - else strips the ``sources__``/``sources_`` server prefix (underscore forms)

    Then casefolds. Internal underscores/digits in tool names (e.g. ``search_grinchenko_1907``)
    are preserved; generic single-underscore stripping is intentionally avoided.
    """
    canonical = str(name or "").strip()
    if not canonical:
        return ""
    for prefix in ("mcp__", "mcp_"):
        if canonical.startswith(prefix):
            canonical = canonical[len(prefix):]
            break
    if "." in canonical:
        server, _, tool = canonical.partition(".")  # server.tool → tool
        # Only strip when BOTH segments are non-empty. A malformed dot form
        # (``sources.`` or ``.query_wikipedia``) must NOT collapse to "" — an
        # empty canonical is treated as "no tool" by _grounding_matching_events
        # (``if tool and ...``), which would turn a malformed citation into a
        # wildcard that bypasses the tool filter. Leave it unchanged so the
        # gate fails closed (non-empty, never matches a real event).
        if server and tool:
            canonical = tool
    else:
        for prefix in ("sources__", "sources_"):
            if canonical.startswith(prefix):
                canonical = canonical[len(prefix):]
                break
    return canonical.casefold()


def _grounding_matching_events(
    grounding: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    """Return captured events whose tool/query/output back this grounding."""
    query = str(grounding.get("query") or "").strip()
    excerpt = str(grounding.get("evidence_excerpt") or "").strip()
    if not query or not excerpt:
        return ()
    tool = _canonical_tool_name(grounding.get("tool"))
    matches: list[Mapping[str, Any]] = []
    for event in events:
        if tool and _canonical_tool_name(event.get("tool")) != tool:
            continue
        if not _event_input_matches_query(event, query):
            continue
        output = _event_output_text(event)
        if output is not None and _output_contains_excerpt(output, excerpt):
            matches.append(event)
    return tuple(matches)


def _event_output_text(event: Mapping[str, Any]) -> str | None:
    output = event.get("output")
    if output is None:
        return None
    if isinstance(output, str):
        return output
    if isinstance(output, (Mapping, list)):
        return json.dumps(output, ensure_ascii=False, default=str)
    return str(output)


def _output_contains_excerpt(output: str, excerpt: str) -> bool:
    normalized_output = _normalize_for_match(output)
    if not _ELLIPSIS_RE.search(excerpt):
        normalized_excerpt = _normalize_for_match(excerpt)
        return bool(normalized_output and normalized_excerpt and normalized_excerpt in normalized_output)

    segments = [segment for segment in _excerpt_segments(excerpt) if len(segment) >= 4]
    if not segments:
        return False
    evidence_mass = sum(len(segment.replace(" ", "")) for segment in segments)
    if evidence_mass < 12:
        return False

    cursor = 0
    for segment in segments:
        index = normalized_output.find(segment, cursor)
        if index == -1:
            return False
        cursor = index + len(segment)
    return True


def _normalize_for_match(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\u0301", "").replace("\u0341", "")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.casefold().strip()


def _excerpt_segments(excerpt: str) -> list[str]:
    return [segment for part in _ELLIPSIS_RE.split(excerpt) if (segment := _normalize_for_match(part))]


def _event_input_matches_query(event: Mapping[str, Any], query: str) -> bool:
    """Check if the real tool event query is matched by the model's cited query.

    Models decorate the cited query by APPENDING params/context to the real query
    (e.g. "Сковорода Григорій Савич mode=section 3 (Придворна капела)"). So we accept
    a PREFIX-BOUNDARY match: the real event query equals the cited query, or the cited
    query starts with the real query followed by a space. This is deliberately NOT
    arbitrary substring containment (`cand in cited`): a short real query (e.g. "сон",
    "гай") embedded mid-string in an unrelated cited query would wildcard the gate.
    Prefix-boundary recovers 100% of the observed decoration cases (claude 85→119,
    ds-flash 118→154) with no signal loss vs arbitrary containment, and closes the hole.

    ANTI-FABRICATION INVARIANT: Admissibility still strictly requires:
      1) The tool matches.
      2) The cited query prefix-matches the real event query (event_query is a bounded
         prefix of cited_query).
      3) The excerpt is a substring present in THAT SAME event's captured output.
    Fabrications cannot pass because the excerpt must still exist in the actual event output.
    """
    cited = _normalize_query(query)
    if not cited:
        return False
    for candidate in _tool_query_candidates(event):
        cand = _normalize_query(candidate)
        if not cand:
            continue
        # Prefix-boundary containment: exact, or real query + space-delimited decoration.
        if cited == cand or cited.startswith(cand + " "):
            return True
    return False


def _normalize_query(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


# --- Sources MCP fail-fast (design D0; step-1 lesson) ----------------------

_JSONC_TOKEN_RE = re.compile(r'"(?:\\.|[^"\\])*"|/\*.*?\*/|//[^\n]*', re.DOTALL)


def _loads_jsonc(text: str) -> Any:
    """Parse JSON-with-comments (opencode config) tolerantly; None on failure.

    Strips ``//`` line + ``/* */`` block comments (never inside string literals)
    and trailing commas before ``json.loads``.
    """

    def _strip(match: re.Match[str]) -> str:
        token = match.group(0)
        return token if token.startswith('"') else ""

    cleaned = _JSONC_TOKEN_RE.sub(_strip, text)
    cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return None


def _opencode_config_paths() -> list[Path]:
    """Candidate opencode config files, LOWEST -> HIGHEST precedence.

    Mirrors opencode's documented merge order: global config (home /
    $XDG_CONFIG_HOME), then a file named by $OPENCODE_CONFIG, then the nearest
    project ``opencode.json[c]`` walking up from cwd. Within one directory,
    ``.jsonc`` is listed after ``.json`` so it wins the merge (opencode's
    preferred extension). $OPENCODE_CONFIG_CONTENT (inline JSON) is handled
    separately in :func:`_iter_opencode_configs` as the top source.
    """
    paths: list[Path] = []
    home = Path.home()
    paths.append(home / ".config" / "opencode" / "opencode.json")
    paths.append(home / ".config" / "opencode" / "opencode.jsonc")
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        paths.append(Path(xdg) / "opencode" / "opencode.json")
        paths.append(Path(xdg) / "opencode" / "opencode.jsonc")
    env_cfg = os.environ.get("OPENCODE_CONFIG")
    if env_cfg:
        paths.append(Path(env_cfg))
    project = _nearest_project_opencode_config(Path.cwd())
    if project is not None:
        paths.append(project)
    return paths


def _nearest_project_opencode_config(start: Path) -> Path | None:
    """Nearest project ``opencode.json[c]`` walking up from ``start``.

    Stops at the first directory containing one (nearest wins, matching
    opencode's project-config discovery) or at a repo root (``.git``).
    """
    for parent in [start, *start.parents]:
        for name in ("opencode.jsonc", "opencode.json"):
            candidate = parent / name
            if candidate.exists():
                return candidate
        if (parent / ".git").exists():
            return None
    return None


def _iter_opencode_configs() -> Iterator[Any]:
    """Parsed opencode configs in LOWEST -> HIGHEST precedence order."""
    for path in _opencode_config_paths():
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        data = _loads_jsonc(text)
        if data is not None:
            yield data
    inline = os.environ.get("OPENCODE_CONFIG_CONTENT")
    if inline:
        data = _loads_jsonc(inline)
        if data is not None:
            yield data


def _load_opencode_config() -> Any:
    """The EFFECTIVE opencode config across its documented merge sources.

    opencode merges (low -> high): global config, $OPENCODE_CONFIG, nearest
    project ``opencode.json[c]``, inline $OPENCODE_CONFIG_CONTENT. Reading only
    the first global file can falsely BLOCK a legit grounded run (sources wired
    via project/env config) or falsely PASS one (a higher-precedence config
    disables it) — codex review of #4401. Shallow-merges top-level keys plus
    one level of the ``mcp`` map — sufficient for the sources gate; not a full
    deep merge.
    """
    merged: dict[str, Any] = {}
    found = False
    for data in _iter_opencode_configs():
        if not isinstance(data, Mapping):
            continue
        found = True
        for key, value in data.items():
            if (
                key == "mcp"
                and isinstance(value, Mapping)
                and isinstance(merged.get("mcp"), Mapping)
            ):
                merged["mcp"] = {**merged["mcp"], **value}
            else:
                merged[key] = value
    return merged if found else None


def _http_endpoint_responds(url: str, *, timeout_s: int = 3) -> bool:
    """True if the endpoint returns ANY HTTP status (design D0: any response = up).

    The MCP endpoint streams, so ``curl --max-time`` exits 28 (timeout) even
    though it received a status line — key on the emitted ``%{http_code}``, not
    curl's exit code. ``000`` (connection refused / DNS fail) means down.
    """
    curl = shutil.which("curl")
    if not curl:
        return False
    try:
        proc = subprocess.run(
            [curl, "-s", "-o", os.devnull, "-w", "%{http_code}", "--max-time", str(timeout_s), url],
            capture_output=True,
            text=True,
            timeout=timeout_s + 5,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    code = (proc.stdout or "").strip()
    return code.isdigit() and code != "000"


def _assert_sources_mcp_available() -> None:
    """Fail-fast unless the sources MCP is configured AND reachable.

    A grounded reviewer run without tools must never silently proceed (design
    D0; step-1 lesson). Reads the ambient opencode config for an enabled
    ``sources`` MCP entry, then probes its endpoint.
    """
    config = _load_opencode_config()
    sources = None
    if isinstance(config, Mapping):
        mcp = config.get("mcp")
        if isinstance(mcp, Mapping):
            sources = mcp.get("sources")
    if not isinstance(sources, Mapping) or sources.get("enabled") is False:
        raise ReviewerProviderError(
            "sources MCP is not configured/enabled in the effective opencode "
            "config (merged: global ~/.config/opencode/opencode.json[c], "
            "$OPENCODE_CONFIG, project opencode.json[c], "
            "$OPENCODE_CONFIG_CONTENT); a grounded reviewer run must not "
            "proceed without tools (design D0, #2156)."
        )
    url = str(sources.get("url") or SOURCES_MCP_URL)
    if not _http_endpoint_responds(url):
        raise ReviewerProviderError(
            f"sources MCP endpoint {url} is not reachable; start the MCP server "
            "before a grounded reviewer run (design D0, #2156)."
        )


def _cost_for_observed_text(prompt: str, response: str, route: ReviewerRoute) -> float:
    prompt_tokens = estimate_tokens(prompt)
    completion_tokens = estimate_tokens(response)
    return round(
        (
            prompt_tokens * route.input_usd_per_mtok
            + completion_tokens * route.output_usd_per_mtok
        )
        / 1_000_000,
        6,
    )


def _json_payload_from_response(response_text: str) -> Mapping[str, Any]:
    text = response_text.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()
    payload = json.loads(text)
    if not isinstance(payload, Mapping):
        raise ValueError("reviewer response JSON must be an object")
    return payload


def _canonical_level(level: str) -> str:
    policy = policy_for_level(level)
    if policy.family == "seminar":
        return "seminar"
    clean = str(level).strip().lower()
    if clean.startswith("b1"):
        return "b1"
    return clean


def _sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class _CanaryTarget:
    level: str
    slug: str
    module_dir: Path
