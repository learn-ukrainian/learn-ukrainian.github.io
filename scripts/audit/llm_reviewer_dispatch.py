#!/usr/bin/env python3
"""Live LLM reviewer dispatcher for the QG workflow.

This module owns model routing, cross-family lineage checks, canary artifact
exactness, and local spend persistence. The workflow calls it through the same
``Reviewer(target, prompt)`` shape used by precomputed reviewer responses.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from scripts.audit import llm_qg_canaries, llm_reviewer
from scripts.audit.content_surface_gates import policy_for_level

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DAILY_SPEND_PATH = PROJECT_ROOT / "data" / "telemetry" / "llm_reviewer_spend.jsonl"
CANARY_SCHEMA_VERSION = "llm_reviewer_dispatch_canary.v1"

GEMMA_MODEL_ID = "openrouter/google/gemma-4-31b-it"
FRONTIER_MODEL_ID = "gemini-3.1-pro-high"
CLAUDE_SPOT_AUDIT_MODEL_ID = "claude-opus-4.6"

_TOKEN_DIVISOR = 3.5
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


class ReviewerDispatchError(RuntimeError):
    """Base error for dispatcher hard gates."""


class ReviewerProviderError(ReviewerDispatchError):
    """Provider invocation failed before a parseable reviewer response."""


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

    def asdict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "bridge_command": list(self.bridge_command),
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

    def metadata(self) -> dict[str, Any]:
        return {
            "reviewer_model_id": self.reviewer_model_id,
            "reviewer_family": self.reviewer_family,
            "route_name": self.route_name,
            "observed_prompt_tokens": self.observed_prompt_tokens,
            "observed_completion_tokens": self.observed_completion_tokens,
            "observed_cost_usd": self.observed_cost_usd,
            "usage": dict(self.usage or {}),
        }


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
FRONTIER_FACTUAL_ROUTE = ReviewerRoute(
    route_name="agy_frontier",
    bridge_command=("ask-agy", "--to-model", FRONTIER_MODEL_ID, "--review"),
    reviewer_model_id=FRONTIER_MODEL_ID,
    reviewer_family="google",
    purpose="Seminar, contested-gold, or factual-sensitive review",
    input_usd_per_mtok=1.25,
    output_usd_per_mtok=10.0,
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
    CLAUDE_SPOT_AUDIT_ROUTE,
)


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
        return FRONTIER_FACTUAL_ROUTE
    return GEMMA_SURFACE_ROUTE


def assert_route_allowed(route: ReviewerRoute) -> None:
    """Hard-ban DeepSeek/Hermes->OpenRouter automated reviewer routes."""

    haystack = " ".join(
        [route.route_name, route.reviewer_model_id, route.reviewer_family, *route.bridge_command]
    )
    lowered = haystack.lower()
    if normalize_family(haystack) == "deepseek" or "hermes" in lowered:
        raise ReviewerRouteError("DeepSeek/Hermes/OpenRouter reviewer routes are forbidden")


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
    cost = (
        prompt_tokens * route.input_usd_per_mtok
        + estimated_completion_tokens * route.output_usd_per_mtok
    ) / 1_000_000
    return {
        "policy_family": policy_family,
        "route_name": route.route_name,
        "reviewer_model_id": route.reviewer_model_id,
        "reviewer_family": route.reviewer_family,
        "estimated_prompt_tokens": prompt_tokens,
        "estimated_completion_tokens": estimated_completion_tokens,
        "estimated_total_tokens": prompt_tokens + estimated_completion_tokens,
        "estimated_cost_usd": round(cost, 6),
        "basis": "route-specific prompt byte estimate; calibrate before broad spend",
    }


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
        return result


def invoke_bridge_route(route: ReviewerRoute, prompt: str, task_id: str) -> DispatchResult:
    """Invoke the route's approved backend and return response text.

    Gemma uses the same opencode helper behind ``ask-gemma`` because that bridge
    command records responses in the inbox rather than returning them. AGY and
    Claude are invoked through their public bridge commands with temporary
    output files where supported.
    """

    assert_route_allowed(route)
    if route.route_name == GEMMA_SURFACE_ROUTE.route_name:
        from scripts.ai_agent_bridge._opencode import _invoke_opencode

        try:
            response = _invoke_opencode(
                prompt,
                route.reviewer_model_id,
                output_format="json",
            )
        except SystemExit as exc:
            raise ReviewerProviderError(str(exc)) from exc
        return _result_from_text(prompt, response, route)
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
