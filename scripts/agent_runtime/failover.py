"""Runner-level provider failover configuration, cooldowns, and classifiers."""
from __future__ import annotations

import contextlib
import logging
import os
import re
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .result import ParseResult
from .routes import (
    RUNTIME_ROUTE_TOOL_CONFIG_KEY,
    forbidden_glm_error,
    is_forbidden_glm_route,
)

RUNNER_FAILOVER_MARKER = "AGENT_RUNTIME_FAILOVER_SUBSTITUTION"
FAILOVER_CONFIG_ENV = "AGENT_RUNTIME_FAILOVER_CONFIG"
FAILOVER_COOLDOWN_DB_ENV = "AGENT_RUNTIME_FAILOVER_COOLDOWN_DB"
DEFAULT_COOLDOWN_TTL_S = 5 * 60

_RATE_LIMIT_RE = re.compile(
    r"rate limit|rate_limit|quota exceeded|too many requests|"
    r"resource_exhausted|\bHTTP 429\b|\bstatus 429\b|\b429\b",
    re.IGNORECASE,
)
# Credential-absence phrasings included: hermes refuses to start a provider
# whose key is missing/disabled with "Provider '<name>' is set in config.yaml
# but no API key was found ..." (live-captured 2026-07-06). Rotating to the
# next route on a dead credential is the point of the chain, so these
# classify as auth. Judgment call: the phrasings are broad enough that a
# provider passing through a verbose downstream error body could false-match;
# accepted because the classifier only ever sees text from an already-failed
# attempt, so the cost of a false positive is one extra route rotation.
_AUTH_RE = re.compile(
    r"\b(?:401|403)\b|unauthorized|forbidden|invalid api key|"
    r"authentication failed|auth(?:orization)? failed|"
    r"no api key(?: was)? (?:found|set|configured)|missing api key|"
    r"no credentials? (?:found|set|configured|available)",
    re.IGNORECASE,
)
_OVERLOADED_RE = re.compile(
    r"\b5\d{2}\b|server error|service unavailable|bad gateway|"
    r"gateway timeout|overloaded|over capacity|upstream error",
    re.IGNORECASE,
)
_TRANSPORT_RE = re.compile(
    r"connection refused|connection reset|connection aborted|"
    r"econnrefused|econnreset|etimedout|network is unreachable|"
    r"read timeout|timed out|timeout while connecting|temporarily unavailable",
    re.IGNORECASE,
)
_EMPTY_RESPONSE_RE = re.compile(
    r"empty response|empty stream|no content|parsed but empty|"
    r"no parsed response|zero-length response",
    re.IGNORECASE,
)
_CONTENT_POLICY_RE = re.compile(
    r"content[-_ ]?policy|content filter|safety filter|policy refusal|"
    r"\brefusal\b|refused for safety|blocked by safety",
    re.IGNORECASE,
)
_REQUEST_FORMAT_RE = re.compile(
    r"\b400\b|bad request|invalid[_ -]?request|request format|"
    r"unsupported parameter|unknown parameter|schema validation|"
    r"malformed request|not found|\b404\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class FailoverRoute:
    """One non-secret route identity from a per-lane failover chain."""

    provider: str
    model: str
    profile: str | None = None
    index: int = 0

    def cooldown_key(self, *, agent_name: str) -> str:
        return "|".join(
            (
                agent_name,
                self.provider,
                self.model,
                self.profile or "",
            )
        )

    def as_tool_config(self) -> dict[str, str]:
        route = {
            "provider": self.provider,
            "model": self.model,
        }
        if self.profile:
            route["profile"] = self.profile
        return route


@dataclass(frozen=True)
class FailoverChain:
    """Ordered routes and cooldown policy for one runtime lane."""

    agent_name: str
    routes: tuple[FailoverRoute, ...]
    cooldown_ttl_s: int = DEFAULT_COOLDOWN_TTL_S


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_failover_config_path() -> Path:
    return _repo_root() / "scripts" / "config" / "agent_runtime_failover.yaml"


def default_cooldown_db_path() -> Path:
    return _repo_root() / "batch_state" / "agent_runtime_failover_cooldowns.sqlite3"


def _configured_path(env_name: str, default: Path) -> Path:
    raw = os.environ.get(env_name)
    if raw:
        return Path(raw).expanduser().resolve()
    return default


def load_failover_chain(
    agent_name: str,
    *,
    effective_model: str,
    path: Path | None = None,
) -> FailoverChain | None:
    """Return the configured failover chain for ``agent_name``, if any.

    Missing config, missing lane, or fewer than two usable routes all mean
    "feature disabled" so the runner keeps its pre-failover behavior exactly.
    """
    config_path = path or _configured_path(
        FAILOVER_CONFIG_ENV,
        default_failover_config_path(),
    )
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(data, dict):
        return None

    chains = data.get("chains")
    if not isinstance(chains, dict):
        return None
    lane = chains.get(agent_name)
    if lane is None:
        return None

    cooldown_ttl_s = DEFAULT_COOLDOWN_TTL_S
    if isinstance(lane, dict):
        raw_routes = lane.get("routes")
        raw_ttl = lane.get("cooldown_ttl_s")
        if isinstance(raw_ttl, int) and raw_ttl > 0:
            cooldown_ttl_s = raw_ttl
    elif isinstance(lane, list):
        raw_routes = lane
    else:
        return None

    if not isinstance(raw_routes, list):
        return None

    routes: list[FailoverRoute] = []
    for index, raw_route in enumerate(raw_routes):
        if not isinstance(raw_route, dict):
            continue
        provider = str(raw_route.get("provider") or agent_name).strip()
        model = str(raw_route.get("model") or (effective_model if index == 0 else "")).strip()
        profile_raw = raw_route.get("profile")
        profile = str(profile_raw).strip() if profile_raw is not None else None
        if not provider or not model:
            # Fail-safe by design (malformed config must never break
            # dispatches), but LOUD: a dropped route can silently disable
            # the whole chain via the len<2 check below (review D4,
            # PR #4580). Only route 0 may omit model (inherits request).
            logging.getLogger(__name__).warning(
                "runner failover chain %s[%d] dropped: missing %s "
                "(routes after index 0 must set an explicit model)",
                agent_name,
                index,
                "provider" if not provider else "model",
            )
            continue
        if is_forbidden_glm_route(provider, model):
            raise ValueError(
                forbidden_glm_error(
                    provider=provider,
                    model=model,
                    source=f"runner failover chain {agent_name}[{index}]",
                )
            )
        routes.append(
            FailoverRoute(
                provider=provider,
                model=model,
                profile=profile or None,
                index=index,
            )
        )

    if len(routes) < 2:
        return None
    return FailoverChain(
        agent_name=agent_name,
        routes=tuple(routes),
        cooldown_ttl_s=cooldown_ttl_s,
    )


class FailoverCooldownStore:
    """SQLite-backed route cooldown store shared by parallel dispatches."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _configured_path(
            FAILOVER_COOLDOWN_DB_ENV,
            default_cooldown_db_path(),
        )

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.path), timeout=10.0)
        conn.execute("PRAGMA busy_timeout=5000")
        with contextlib.suppress(sqlite3.DatabaseError):
            conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS route_cooldowns (
                route_key TEXT PRIMARY KEY,
                agent TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                profile TEXT,
                trigger TEXT NOT NULL,
                expires_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
            """
        )
        return conn

    def is_cooling(
        self,
        route: FailoverRoute,
        *,
        agent_name: str,
        now: float | None = None,
    ) -> bool:
        now = time.time() if now is None else now
        route_key = route.cooldown_key(agent_name=agent_name)
        with self._connect() as conn:
            conn.execute("DELETE FROM route_cooldowns WHERE expires_at <= ?", (now,))
            row = conn.execute(
                "SELECT expires_at FROM route_cooldowns WHERE route_key = ?",
                (route_key,),
            ).fetchone()
        return bool(row and float(row[0]) > now)

    def mark_cooldown(
        self,
        route: FailoverRoute,
        *,
        agent_name: str,
        trigger: str,
        ttl_s: int,
        now: float | None = None,
    ) -> None:
        now = time.time() if now is None else now
        expires_at = now + max(1, ttl_s)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO route_cooldowns (
                    route_key, agent, provider, model, profile,
                    trigger, expires_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(route_key) DO UPDATE SET
                    trigger = excluded.trigger,
                    expires_at = excluded.expires_at,
                    updated_at = excluded.updated_at
                """,
                (
                    route.cooldown_key(agent_name=agent_name),
                    agent_name,
                    route.provider,
                    route.model,
                    route.profile,
                    trigger,
                    expires_at,
                    now,
                ),
            )


def ordered_available_routes(
    chain: FailoverChain,
    store: FailoverCooldownStore,
) -> tuple[FailoverRoute, ...]:
    """Return chain routes not currently cooling, preserving configured order."""
    return tuple(
        route
        for route in chain.routes
        if not store.is_cooling(route, agent_name=chain.agent_name)
    )


def classify_failover_trigger(
    *,
    parse: ParseResult,
    returncode: int | None,
    kill_reason: str | None,
    stdout_text: str,
    stderr_text: str,
) -> str | None:
    """Map one failed attempt to an eligible failover trigger, if any."""
    text = "\n".join(
        part
        for part in (
            parse.stderr_excerpt or "",
            stderr_text or "",
            stdout_text or "",
        )
        if part
    )

    if _CONTENT_POLICY_RE.search(text):
        return None
    if _REQUEST_FORMAT_RE.search(text) and not (
        parse.rate_limited
        or _RATE_LIMIT_RE.search(text)
        or _AUTH_RE.search(text)
        or _OVERLOADED_RE.search(text)
    ):
        return None

    if parse.rate_limited or _RATE_LIMIT_RE.search(text):
        return "rate_limited"
    if _AUTH_RE.search(text):
        return "auth"
    if _OVERLOADED_RE.search(text):
        return "overloaded"
    if _TRANSPORT_RE.search(text):
        return "transport"
    if kill_reason == "initial_response_timeout":
        return "transport"
    if _EMPTY_RESPONSE_RE.search(text):
        return "empty_response"
    if (
        not parse.ok
        and returncode == 0
        and not (parse.response or "").strip()
        and not text.strip()
    ):
        return "empty_response"
    return None


def tool_config_with_route(
    tool_config: dict | None,
    route: FailoverRoute,
) -> dict:
    """Clone tool_config and pin the adapter-visible runtime route."""
    merged = dict(tool_config or {})
    merged[RUNTIME_ROUTE_TOOL_CONFIG_KEY] = route.as_tool_config()
    return merged


def substitution_for_route(
    *,
    requested_route: FailoverRoute,
    actual_route: FailoverRoute,
    source: str,
    adapter_substitution: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Build a runner substitution record, preserving adapter actual route."""
    actual_provider = actual_route.provider
    actual_model = actual_route.model
    if isinstance(adapter_substitution, dict):
        actual_provider = str(
            adapter_substitution.get("actual_provider") or actual_provider
        )
        actual_model = str(adapter_substitution.get("actual_model") or actual_model)

    substituted = (
        actual_provider != requested_route.provider
        or actual_model != requested_route.model
    )
    if not substituted:
        return adapter_substitution

    return {
        "requested_provider": requested_route.provider,
        "requested_model": requested_route.model,
        "actual_provider": actual_provider,
        "actual_model": actual_model,
        "substituted": True,
        "source": source,
        "marker": RUNNER_FAILOVER_MARKER,
    }


def emit_runner_substitution_marker(
    substitution: dict[str, Any] | None,
    *,
    logger: logging.Logger,
) -> None:
    """Emit the loud stderr/logger marker required for runner failover."""
    if not substitution or not substitution.get("substituted"):
        return
    if substitution.get("marker") != RUNNER_FAILOVER_MARKER:
        return
    message = (
        f"{RUNNER_FAILOVER_MARKER}: "
        f"{substitution.get('requested_provider')}/"
        f"{substitution.get('requested_model')} -> "
        f"{substitution.get('actual_provider')}/"
        f"{substitution.get('actual_model')} "
        f"source={substitution.get('source')}"
    )
    logger.warning(message)
    print(message, file=sys.stderr)
