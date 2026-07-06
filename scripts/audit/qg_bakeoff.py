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
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import llm_reviewer, llm_reviewer_dispatch, qg_factcheck_scoring, qg_schema

FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "qg_bakeoff"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "audit"
RUN_SCHEMA_VERSION = "qg_bakeoff_run.v2"
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
OPENCODE_TRANSPORT = "opencode"
OPENCODE_ENTRYPOINT = "qg_bakeoff_opencode"
OPENCODE_MEASUREMENT_TIER = "opencode_bare_or_tooled"
BARE_RUNTIME_ENTRYPOINT = "qg_bakeoff_runtime"
SUBSCRIPTION_RUNTIME_BARE_TIER = "subscription_runtime_bare"
SUBSCRIPTION_BARE_BANNER = (
    "subscription-runtime bare — not raw completion; do not compare to opencode bare rows or external leaderboards."
)
FAILURE_CLASS_TRANSPORT = "transport"
FAILURE_CLASS_OPS_QUOTA = "ops_quota"
FAILURE_CLASS_MODEL_FAILURE = "model_failure"
_FAILURE_CLASSES = {
    FAILURE_CLASS_TRANSPORT,
    FAILURE_CLASS_OPS_QUOTA,
    FAILURE_CLASS_MODEL_FAILURE,
}
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


def _runtime_bridge_command(agent: str, model: str) -> tuple[str, ...]:
    """Return the audited runtime call shape, not an ask-* bridge wrapper."""
    if agent == "claude":
        return (
            "agent_runtime.invoke",
            "claude",
            "--entrypoint",
            BARE_RUNTIME_ENTRYPOINT,
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
            BARE_RUNTIME_ENTRYPOINT,
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
            BARE_RUNTIME_ENTRYPOINT,
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


def route_for_matrix_pin(pin: str, *, arm: str) -> llm_reviewer_dispatch.ReviewerRoute:
    """Resolve a requested pin to the only route allowed for the requested arm."""
    subscription_route = _SUBSCRIPTION_BARE_ROUTES_BY_PIN.get(pin)
    if subscription_route is not None:
        if arm != BARE_ARM:
            raise BakeoffConfigError(
                "subscription-runtime native pins are bare-only; "
                f"pin={pin!r} was requested with --arm {arm!r}"
            )
        return subscription_route
    return bakeoff_route_for_model(pin)


def _route_identity(route: llm_reviewer_dispatch.ReviewerRoute) -> RouteIdentity:
    if route.route_name in _SUBSCRIPTION_BARE_IDENTITIES:
        return _SUBSCRIPTION_BARE_IDENTITIES[route.route_name]
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


def _is_subscription_bare_route(route: llm_reviewer_dispatch.ReviewerRoute) -> bool:
    return route.route_name in _SUBSCRIPTION_BARE_IDENTITIES


def _subscription_identity(route: llm_reviewer_dispatch.ReviewerRoute) -> RouteIdentity:
    identity = _SUBSCRIPTION_BARE_IDENTITIES.get(route.route_name)
    if identity is None or not identity.runtime_agent:
        raise BakeoffConfigError(f"route is not a subscription-runtime bare route: {route.route_name!r}")
    return identity


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
        tool_events=tuple(dict(call) for call in result.tool_calls if isinstance(call, Mapping)),
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
    if bare_runner is invoke_bakeoff_route_bare:
        preflight_subscription_bare_routes(routes)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_tooled = arm in (TOOLED_ARM, BOTH_ARM)
    run_bare = arm in (BARE_ARM, BOTH_ARM)
    runs: list[BakeoffRun] = []
    for route in routes:
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
        "model": _model_block(route, dispatch),
        "status": gate_result["status"],
        "workflow_verdict": gate_result["workflow_verdict"],
        "findings_schema_invalid": bool(gate_result.get("findings_schema_invalid")),
        "response_parse_lenient": bool(gate_result.get("response_parse_lenient")),
        "attempt_count": gate_result["attempt_count"],
        "timed_out": False,
        "transport_retry": {"attempted": False, "reason": None},
        "dispatch": dispatch,
        "gate_outcomes": gate_outcomes,
        "payload": gate_result["payload"],
        "score": score,
        "tool_call_count": int(dispatch.get("tool_call_count") or 0),
        "wall_seconds": wall_seconds,
    }
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return BakeoffRun(artifact_path=artifact_path, artifact=artifact)


def _bare_artifact_path(
    output_dir: Path,
    route: llm_reviewer_dispatch.ReviewerRoute,
    fixture: BakeoffFixture,
) -> Path:
    return output_dir / (
        f"{pin_slug(route.reviewer_model_id)}__{fixture.slug}__bare__"
        f"{_transport_slug(_route_transport(route))}.json"
    )


def _assert_resume_transport_matches(
    artifact: Mapping[str, Any],
    route: llm_reviewer_dispatch.ReviewerRoute,
    artifact_path: Path,
) -> None:
    artifact_transport = _artifact_transport(artifact)
    route_transport = _route_transport(route)
    if artifact_transport != route_transport:
        raise BakeoffConfigError(
            f"{artifact_path}: existing bare artifact transport={artifact_transport!r} "
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
    artifact_path = _bare_artifact_path(output_dir, route, fixture)
    if artifact_path.exists() and not force:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        _assert_resume_transport_matches(artifact, route, artifact_path)
        if not (retry_failures and artifact.get("status") == "error"):
            return BakeoffRun(artifact_path=artifact_path, artifact=artifact, skipped=True)

    prompt = build_bare_factcheck_prompt(fixture.title, fixture.passage_md)
    task_id = f"qg-bakeoff-bare-{pin_slug(route.reviewer_model_id)}-{fixture.slug}"
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
    regular_artifacts = [a for a in artifacts if not _is_subscription_runtime_artifact(a)]
    subscription_artifacts = [a for a in artifacts if _is_subscription_runtime_artifact(a)]
    judgment_artifacts = [a for a in regular_artifacts if not _is_ops_quota_artifact(a)]
    lines = [
        "# QG Bakeoff Scorecard",
        "",
        f"Generated: {_now_z()}",
        "",
        "Fractions are exact. `low-N` marks denominators below 10.",
        "",
    ]
    lines.extend(_runs_table_section("Runs", regular_artifacts))
    lines.extend(_ops_quota_section(regular_artifacts))
    lines.extend(_totals_and_lift_section("With Anchor", judgment_artifacts))
    lines.extend(
        _totals_and_lift_section(
            "Without Anchor",
            [a for a in judgment_artifacts if _fixture_slug(a) != ANCHOR_SLUG],
        )
    )
    if subscription_artifacts:
        lines.extend(
            [
                "",
                "## Subscription Runtime Bare Rows",
                "",
                SUBSCRIPTION_BARE_BANNER,
                "",
            ]
        )
        lines.extend(_runs_table(subscription_artifacts))
        lines.extend(_ops_quota_section(subscription_artifacts))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _runs_table_section(title: str, artifacts: Sequence[Mapping[str, Any]]) -> list[str]:
    return ["", f"## {title}", "", *_runs_table(artifacts)]


def _runs_table(artifacts: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [
        "| model | transport | entrypoint | passage | arm | status | failure_class | parse_lenient | model judgment | live admissible | missing | U honesty | M alignment | true unsupported | invalid | inadmissible | tools | wall_s |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    if not artifacts:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 0 | 0/0 low-N | 0/0 low-N | 0/0 low-N | 0 | 0 | 0 | 0 |")
        return lines
    for artifact in sorted(artifacts, key=_artifact_sort_key):
        score = _score(artifact)
        fractions = score.get("fractions", {})
        lines.append(
            "| {model} | {transport} | {entrypoint} | {passage} | {arm} | {status} | {failure_class} | {parse_lenient} | {model_score} | {live_score} | {missing} | {u} | {m} | {true_bad} | {invalid} | {inadmissible} | {tools} | {wall} |".format(
                model=_model_label(artifact),
                transport=_artifact_transport(artifact),
                entrypoint=_artifact_entrypoint(artifact),
                passage=_fixture_slug(artifact),
                arm=_artifact_arm(artifact),
                status=artifact.get("status", "unknown"),
                failure_class=artifact.get("failure_class") or "n/a",
                parse_lenient=bool(artifact.get("response_parse_lenient")),
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
        schema = artifact.get("schema_version")
        if not (isinstance(schema, str) and schema.startswith("qg_bakeoff_run.")):
            # Foreign JSON in the out-dir (e.g. tier2-canary-verdict.json) is
            # NOT a bakeoff cell — scoring it fabricates an 'unknown' scorecard
            # row with a phantom passage count (caught live 2026-07-06 when a
            # canary verdict file polluted the totals table).
            continue
        # Backfill ``arm`` for backward compat: pre-arm tooled artifacts have no
        # field (→ "tooled"); a ``__bare`` filename identifies a bare artifact even
        # if it somehow lacks the field. Rescore covers BOTH arms — the bare grounding
        # counters resolve to 0 because a bare artifact carries no gate_outcomes.
        artifact["arm"] = artifact.get("arm") or (BARE_ARM if "__bare" in path.stem else TOOLED_ARM)
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
    parser.add_argument(
        "--models",
        action="append",
        help=(
            "Comma-separated or repeated model pins. OpenRouter/opencode pins work for tooled/bare; "
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


def _na(value: Any) -> str:
    return "n/a" if value is None else str(value)


def _aggregate_by_model_arm(
    artifacts: Sequence[Mapping[str, Any]],
) -> dict[tuple[tuple[str, str, str], str], dict[str, Any]]:
    totals: dict[tuple[tuple[str, str, str], str], dict[str, Any]] = defaultdict(
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
        if _is_ops_quota_artifact(artifact):
            continue
        row = totals[(_model_key(artifact), _artifact_arm(artifact))]
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
    return _artifact_measurement_tier(artifact) == SUBSCRIPTION_RUNTIME_BARE_TIER


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


def _artifact_sort_key(artifact: Mapping[str, Any]) -> tuple[str, str, str, str, str]:
    pin, transport, entrypoint = _model_key(artifact)
    return (pin, transport, entrypoint, _fixture_slug(artifact), _artifact_arm(artifact))


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
