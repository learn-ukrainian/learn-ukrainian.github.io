"""Measure and enforce repository-controlled Claude Code cold-start budgets.

The source set is selected by the trusted *lead-session* profile. Delegated
Sol/Terra/Luna routing is reported for matrix checks but cannot change startup
sources, the lead window, the budget, or rollover policy.

By default token counts use a conservative deterministic estimate. Pass
``--token-count-url`` when a gateway/model tokenizer endpoint is available;
its response must expose ``input_tokens``, ``tokens``, ``count``, or
``usage.input_tokens``. ``--transcript`` adds an observed first-assistant-turn
input/cache count and the larger of planned versus observed usage drives the
gate.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

PROJECT_ROOT = Path(__file__).resolve().parents[2]
try:
    from scripts.lib.context_profiles import resolve_profile
except ModuleNotFoundError as exc:
    if __package__ or exc.name != "scripts":
        raise
    sys.path.insert(0, os.fspath(PROJECT_ROOT))
    from scripts.lib.context_profiles import resolve_profile

BASELINE_DOC = PROJECT_ROOT / "docs/monitor-api/cold-start-baseline.md"
DEFAULT_MONITOR_BASE_URL = "http://127.0.0.1:8765"
DEFAULT_FETCH_TIMEOUT_S = 30.0
CONSERVATIVE_BYTES_PER_TOKEN = 3
CONSERVATIVE_SOURCE_OVERHEAD_TOKENS = 32
REQUIRED_STARTUP_SOURCE_NAMES = {
    "project-instructions",
    "session-profile-capsule",
    "session-manifest",
    "orientation",
    "active-delegates",
    "worktrees",
    "lane-inbox",
}


@dataclass(frozen=True, slots=True)
class SourceSpec:
    name: str
    kind: str
    provenance: str
    locator: str = ""
    generated_payload: bytes | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class SourceResult:
    name: str
    kind: str
    provenance: str
    status: int | None
    bytes: int
    tokens: int
    token_count_method: str
    elapsed_ms: float
    error: str | None = None


@dataclass(frozen=True, slots=True)
class TranscriptObservation:
    path: str
    tokens: int | None
    method: str
    error: str | None = None


@dataclass(slots=True)
class ColdStartMeasurement:
    label: str
    timestamp: str
    requested_profile_id: str | None
    selected_profile_id: str
    profile_resolution_reason: str
    profile_trusted: bool
    main_model_id: str
    delegated_model_id: str | None
    cold_start_profile: str
    main_context_window_tokens: int
    cold_start_budget_tokens: int
    rollover_warning_percentages: list[float]
    source_count: int
    total_bytes: int
    estimated_input_tokens: int
    observed_first_turn_tokens: int | None
    gate_input_tokens: int
    budget_percent: float | None
    context_window_percent: float | None
    complete: bool
    within_budget: bool
    sources: list[SourceResult] = field(default_factory=list)
    transcript_observation: TranscriptObservation | None = None
    notes: str = ""


def _session_profile_capsule(profile: dict[str, Any], session_id: str) -> bytes:
    auto_compact = profile.get("auto_compact_capacity_tokens")
    lines = [
        "--- SESSION PROFILE CAPSULE ---",
        f"Profile: {profile.get('profile_id', 'fallback')}",
        f"Requested Profile: {profile.get('requested_profile_id') or 'None'}",
        f"Declared Model: {profile.get('expected_main_model_id') or profile.get('main_model_id', 'unknown')}",
        f"Declared Window: {profile.get('expected_main_context_window_tokens') or 0}",
        f"Effective Window: {profile.get('main_context_window_tokens') or 0}",
        f"Cold Start: {profile.get('cold_start_profile', 'compact')}",
        f"Budget: {profile.get('cold_start_budget_tokens') or 0}",
        f"Auto-Compact Capacity: {auto_compact if auto_compact is not None else 'None'}",
        f"Trusted: {1 if profile.get('trusted') else 0} ({profile.get('resolution_reason', 'missing-profile')})",
        f"Session ID: {session_id}",
        "--------------------------------",
    ]
    return ("\n".join(lines) + "\n").encode()


def build_source_specs(
    profile: dict[str, Any],
    *,
    session_id: str,
    agent: str,
    monitor_base_url: str = DEFAULT_MONITOR_BASE_URL,
    session_start_output: Path | None = None,
) -> list[SourceSpec]:
    """Return the exact repository-controlled startup sources for a profile."""
    base = monitor_base_url.rstrip("/")
    encoded_session = quote(session_id, safe="")
    encoded_agent = quote(agent, safe="")
    compact = profile.get("cold_start_profile") == "compact"
    orient_query = "lean=true&" if compact else ""

    if session_start_output is None:
        capsule = SourceSpec(
            name="session-profile-capsule",
            kind="generated",
            provenance="generated:profile-capsule",
            generated_payload=_session_profile_capsule(profile, session_id),
        )
    else:
        capsule = SourceSpec(
            name="session-profile-capsule",
            kind="file",
            provenance=f"captured-session-start:{session_start_output}",
            locator=os.fspath(session_start_output),
        )

    specs = [
        SourceSpec(
            name="project-instructions",
            kind="file",
            provenance="harness-injected:CLAUDE.md",
            locator="CLAUDE.md",
        ),
        capsule,
        SourceSpec(
            name="session-manifest",
            kind="endpoint",
            provenance="monitor-api:session-bound-manifest",
            locator=f"{base}/api/state/manifest?session={encoded_session}",
        ),
        SourceSpec(
            name="orientation",
            kind="endpoint",
            provenance=(
                "monitor-api:lean-orient" if compact else "monitor-api:full-orient"
            ),
            locator=(
                f"{base}/api/orient?{orient_query}session={encoded_session}"
            ),
        ),
        SourceSpec(
            name="active-delegates",
            kind="endpoint",
            provenance="monitor-api:delegate-active",
            locator=f"{base}/api/delegate/active",
        ),
        SourceSpec(
            name="worktrees",
            kind="endpoint",
            provenance="monitor-api:worktrees",
            locator=f"{base}/api/worktrees",
        ),
        SourceSpec(
            name="lane-inbox",
            kind="endpoint",
            provenance="monitor-api:lane-inbox",
            locator=f"{base}/api/comms/inbox?agent={encoded_agent}",
        ),
    ]
    names = {spec.name for spec in specs}
    if names != REQUIRED_STARTUP_SOURCE_NAMES:
        missing = sorted(REQUIRED_STARTUP_SOURCE_NAMES - names)
        extra = sorted(names - REQUIRED_STARTUP_SOURCE_NAMES)
        raise ValueError(
            f"cold-start source contract drift: missing={missing}, extra={extra}"
        )
    return specs


def _load_source(
    spec: SourceSpec, *, timeout: float = DEFAULT_FETCH_TIMEOUT_S
) -> tuple[bytes, int | None, float, str | None]:
    start = time.monotonic()
    if spec.kind == "generated":
        payload = spec.generated_payload or b""
        return payload, 200, 0.0, None
    if spec.kind == "file":
        path = Path(spec.locator)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        try:
            payload = path.read_bytes()
        except OSError as exc:
            return (
                b"",
                None,
                round((time.monotonic() - start) * 1000, 1),
                f"{type(exc).__name__}: {exc}",
            )
        return payload, 200, round((time.monotonic() - start) * 1000, 1), None
    if spec.kind != "endpoint":
        return b"", None, 0.0, f"unsupported source kind: {spec.kind}"
    try:
        with urllib.request.urlopen(spec.locator, timeout=timeout) as response:
            payload = response.read()
            return (
                payload,
                response.status,
                round((time.monotonic() - start) * 1000, 1),
                None,
            )
    except (OSError, urllib.error.URLError) as exc:
        return (
            b"",
            None,
            round((time.monotonic() - start) * 1000, 1),
            f"{type(exc).__name__}: {exc}",
        )


def _gateway_token_count(
    payload: bytes,
    *,
    model_id: str,
    token_count_url: str,
    timeout: float,
) -> int:
    request = urllib.request.Request(
        token_count_url,
        data=json.dumps(
            {
                "model": model_id,
                "input": payload.decode("utf-8", errors="replace"),
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read())
    candidates = [
        result.get("input_tokens") if isinstance(result, dict) else None,
        result.get("tokens") if isinstance(result, dict) else None,
        result.get("count") if isinstance(result, dict) else None,
        (
            result.get("usage", {}).get("input_tokens")
            if isinstance(result, dict) and isinstance(result.get("usage"), dict)
            else None
        ),
    ]
    for value in candidates:
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value
    raise ValueError("token-count endpoint returned no supported integer count")


def count_payload_tokens(
    payload: bytes,
    *,
    model_id: str,
    token_count_url: str | None,
    timeout: float = DEFAULT_FETCH_TIMEOUT_S,
) -> tuple[int, str]:
    """Count one source with a model endpoint or a conservative fallback."""
    if token_count_url:
        try:
            count = _gateway_token_count(
                payload,
                model_id=model_id,
                token_count_url=token_count_url,
                timeout=timeout,
            )
            # The configured URL may contain user-info or query credentials. Record
            # the counting method, never the endpoint value itself.
            return count, "gateway-token-count"
        except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError) as exc:
            fallback_reason = type(exc).__name__
    else:
        fallback_reason = "endpoint-unavailable"
    if not payload:
        return 0, f"conservative-bytes/{CONSERVATIVE_BYTES_PER_TOKEN}:{fallback_reason}"
    estimate = math.ceil(len(payload) / CONSERVATIVE_BYTES_PER_TOKEN)
    estimate += CONSERVATIVE_SOURCE_OVERHEAD_TOKENS
    return (
        estimate,
        f"conservative-bytes/{CONSERVATIVE_BYTES_PER_TOKEN}+{CONSERVATIVE_SOURCE_OVERHEAD_TOKENS}:{fallback_reason}",
    )


def observe_first_turn(path: Path) -> TranscriptObservation:
    """Read the first assistant input/cache usage from a Claude transcript."""
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get("type") != "assistant":
                    continue
                message = row.get("message")
                usage = message.get("usage") if isinstance(message, dict) else None
                if not isinstance(usage, dict):
                    continue
                tokens = sum(
                    int(usage.get(field) or 0)
                    for field in (
                        "input_tokens",
                        "cache_read_input_tokens",
                        "cache_creation_input_tokens",
                    )
                )
                if tokens > 0:
                    return TranscriptObservation(
                        path=os.fspath(path),
                        tokens=tokens,
                        method="transcript:first-assistant-input-cache-usage",
                    )
    except OSError as exc:
        return TranscriptObservation(
            path=os.fspath(path),
            tokens=None,
            method="unavailable",
            error=f"{type(exc).__name__}: {exc}",
        )
    return TranscriptObservation(
        path=os.fspath(path),
        tokens=None,
        method="unavailable",
        error="no assistant usage record found",
    )


def measure(
    label: str,
    *,
    profile_id: str | None = None,
    model_id: str | None = None,
    delegated_model_id: str | None = None,
    session_id: str = "cold-start-measurement",
    agent: str = "claude-infra",
    monitor_base_url: str = DEFAULT_MONITOR_BASE_URL,
    token_count_url: str | None = None,
    session_start_output: Path | None = None,
    transcript: Path | None = None,
) -> ColdStartMeasurement:
    profile = resolve_profile(profile_id, model_id)
    specs = build_source_specs(
        profile,
        session_id=session_id,
        agent=agent,
        monitor_base_url=monitor_base_url,
        session_start_output=session_start_output,
    )
    source_results: list[SourceResult] = []
    for spec in specs:
        payload, status, elapsed_ms, error = _load_source(spec)
        tokens, method = count_payload_tokens(
            payload,
            model_id=str(profile.get("main_model_id") or "unknown"),
            token_count_url=token_count_url,
        )
        source_results.append(
            SourceResult(
                name=spec.name,
                kind=spec.kind,
                provenance=spec.provenance,
                status=status,
                bytes=len(payload),
                tokens=tokens,
                token_count_method=method,
                elapsed_ms=elapsed_ms,
                error=error,
            )
        )

    estimated_tokens = sum(source.tokens for source in source_results)
    observation = observe_first_turn(transcript) if transcript is not None else None
    observed_tokens = observation.tokens if observation is not None else None
    gate_tokens = max(estimated_tokens, observed_tokens or 0)
    budget = int(profile.get("cold_start_budget_tokens") or 0)
    window = int(profile.get("main_context_window_tokens") or 0)
    complete = all(source.error is None for source in source_results) and (
        observation is None or observation.error is None
    )
    trusted = bool(profile.get("trusted")) and window > 0 and budget > 0
    within_budget = complete and trusted and gate_tokens <= budget

    warnings = profile.get("rollover_warning_percentages") or []
    return ColdStartMeasurement(
        label=label,
        timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        requested_profile_id=profile.get("requested_profile_id"),
        selected_profile_id=str(profile.get("profile_id") or "fallback"),
        profile_resolution_reason=str(profile.get("resolution_reason") or "unknown"),
        profile_trusted=trusted,
        main_model_id=str(profile.get("main_model_id") or "unknown"),
        delegated_model_id=delegated_model_id,
        cold_start_profile=str(profile.get("cold_start_profile") or "compact"),
        main_context_window_tokens=window,
        cold_start_budget_tokens=budget,
        rollover_warning_percentages=[float(value) for value in warnings],
        source_count=len(source_results),
        total_bytes=sum(source.bytes for source in source_results),
        estimated_input_tokens=estimated_tokens,
        observed_first_turn_tokens=observed_tokens,
        gate_input_tokens=gate_tokens,
        budget_percent=(round(gate_tokens * 100.0 / budget, 2) if budget else None),
        context_window_percent=(
            round(gate_tokens * 100.0 / window, 2) if window else None
        ),
        complete=complete,
        within_budget=within_budget,
        sources=source_results,
        transcript_observation=observation,
        notes=(
            "Gate uses the larger of source estimate and observed first-turn usage."
            if observation is not None
            else "Repository-controlled startup sources only; add --transcript for end-to-end observed usage."
        ),
    )


def _render_markdown(measurement: ColdStartMeasurement) -> str:
    status = "PASS" if measurement.within_budget else "FAIL"
    lines = [
        f"## {measurement.label} — {measurement.timestamp}",
        "",
        f"- **Profile**: `{measurement.selected_profile_id}` / `{measurement.cold_start_profile}`",
        f"- **Lead model/window**: `{measurement.main_model_id}` / {measurement.main_context_window_tokens:,} tokens",
        f"- **Delegated model**: `{measurement.delegated_model_id or 'unset'}` (informational only)",
        f"- **Measured sources**: {measurement.source_count} / {measurement.total_bytes:,} bytes",
        f"- **Estimated source tokens**: {measurement.estimated_input_tokens:,}",
        f"- **Observed first-turn tokens**: {measurement.observed_first_turn_tokens if measurement.observed_first_turn_tokens is not None else 'not supplied'}",
        f"- **Gate**: **{status}** — {measurement.gate_input_tokens:,} / {measurement.cold_start_budget_tokens:,} tokens ({measurement.budget_percent}%)",
        f"- **Context share**: {measurement.context_window_percent}%",
        f"- **Complete**: {measurement.complete}",
        "",
        "| Source | Kind | Provenance | Status | Bytes | Tokens | Count method | Error |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    for source in measurement.sources:
        lines.append(
            f"| `{source.name}` | {source.kind} | {source.provenance} | {source.status or '—'} | "
            f"{source.bytes:,} | {source.tokens:,} | {source.token_count_method} | {source.error or ''} |"
        )
    lines.extend(["", f"> {measurement.notes}", ""])
    return "\n".join(lines)


def _append_markdown(measurement: ColdStartMeasurement) -> None:
    BASELINE_DOC.parent.mkdir(parents=True, exist_ok=True)
    header = ""
    if not BASELINE_DOC.exists():
        header = (
            "# Monitor API Cold-Start Baseline\n\n"
            "Profile-aware repository-controlled startup measurements.\n\n---\n\n"
        )
    with BASELINE_DOC.open("a", encoding="utf-8") as handle:
        if header:
            handle.write(header)
        handle.write(_render_markdown(measurement))
        handle.write("\n---\n\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label")
    parser.add_argument("--no-append", action="store_true")
    parser.add_argument("--json-only", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--profile")
    parser.add_argument("--model")
    parser.add_argument("--subagent-model")
    parser.add_argument("--session-id", default="cold-start-measurement")
    parser.add_argument("--agent", default="claude-infra")
    parser.add_argument("--monitor-base-url", default=DEFAULT_MONITOR_BASE_URL)
    parser.add_argument("--token-count-url")
    parser.add_argument("--session-start-output", type=Path)
    parser.add_argument("--transcript", type=Path)
    args = parser.parse_args()

    profile_id = (
        args.profile
        or os.environ.get("LEARN_UKRAINIAN_REQUESTED_PROFILE_ID")
        or os.environ.get("LEARN_UKRAINIAN_PROFILE_ID")
    )
    model_id = (
        args.model
        or os.environ.get("LEARN_UKRAINIAN_OBSERVED_MODEL_ID")
        or os.environ.get("LEARN_UKRAINIAN_MAIN_MODEL_ID")
    )
    delegated_model = args.subagent_model or os.environ.get(
        "CLAUDE_CODE_SUBAGENT_MODEL"
    )
    token_count_url = args.token_count_url or os.environ.get(
        "LEARN_UKRAINIAN_TOKEN_COUNT_URL"
    )
    measurement = measure(
        args.label or "ad-hoc",
        profile_id=profile_id,
        model_id=model_id,
        delegated_model_id=delegated_model,
        session_id=args.session_id,
        agent=args.agent,
        monitor_base_url=args.monitor_base_url,
        token_count_url=token_count_url,
        session_start_output=args.session_start_output,
        transcript=args.transcript,
    )
    print(json.dumps(asdict(measurement), indent=2))

    if args.label and not args.no_append and not args.json_only:
        _append_markdown(measurement)
    if measurement.within_budget:
        return 0
    if not measurement.complete:
        print("ERROR: cold-start measurement is incomplete", file=os.sys.stderr)
    elif not measurement.profile_trusted:
        print("ERROR: cold-start route is not trusted", file=os.sys.stderr)
    else:
        print(
            f"ERROR: cold start uses {measurement.gate_input_tokens} tokens, "
            f"exceeding budget {measurement.cold_start_budget_tokens}",
            file=os.sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
