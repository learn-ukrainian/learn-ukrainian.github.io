"""Kimi seats admit neutral coding only.

Every Kimi seat (``kimi``, ``kimicc``, the ``acpx-kimi*`` ACP seats, and any
``kimi-code/*`` / ``kimi-k*`` model id) is limited to workspace-write
implementation in code and test paths: no reviews, consults, discussions,
Ukrainian-language content, rules/policy, or private material. The checks
here are pure and run before any side effect; ``delegate.py dispatch`` and the
runner's ACP admission call them so no driver can route other work to Kimi.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import Any

KIMI_AGENT_IDS = frozenset({"kimi", "kimicc"})
KIMI_ALTERNATIVES = (
    "use claude, codex, or grok for reviews, consults, and discussions; "
    "claude, codex, or agy for Ukrainian-language content"
)
_POLICY = "KIMI NEUTRAL-CODING-ONLY"
_ADMITTED_MODE = "workspace-write"

# Owned paths a Kimi seat may write. Everything else is refused, and the
# protected families below are refused even when they sit under an allowed root.
NEUTRAL_CODING_ROOTS = ("scripts/", "tests/", "site/", ".github/", ".dagger/")
PROTECTED_PATH_PREFIXES = (
    "curriculum/",
    "wiki/",
    "data/",
    "registry/",
    "docs/",
    "agents_extensions/shared/rules/",
    "agents_extensions/shared/memory/",
    "agents_extensions/shared/skills/",
    ".claude/",
    ".agent/",
    ".codex/",
    "site/src/content/",
    "site/src/data/",
    "site/src/lexicon/",
    "site/public/",
)
PROTECTED_ROOT_FILES = frozenset({"CLAUDE.md", "AGENTS.md", "GEMINI.md"})
# Path components that mark agent-private state wherever they appear.
PRIVATE_STATE_COMPONENTS = frozenset({".claude", ".agent", ".codex"})
# Fleet repository roles a Kimi seat may target (scripts/config/fleet_repos.yaml).
NEUTRAL_REPO_ROLES = frozenset({"public-monorepo"})
# Research tracks that are always curriculum tracks, in addition to every level
# key of the curriculum manifest.
_CURRICULUM_TRACK_NAMES = frozenset({"core", "seminar", "seminars", "hramatka"})
_CURRICULUM_TRACK_PREFIXES = ("l2-uk",)


def is_kimi_model(model: str | None) -> bool:
    """True for any Kimi model id or alias spelling (``kimi-code/*``, ``kimi-k3*``, ``k3``...)."""
    text = str(model or "").strip().casefold()
    if not text:
        return False
    if text.startswith("kimi"):
        return True
    try:
        from scripts.review.model_catalog import kimi_model_aliases

        return text in {alias.casefold() for alias in kimi_model_aliases()}
    except Exception:  # catalog unavailable: the prefix rule above still applies
        return False


def is_kimi_seat(agent: str | None, *, model: str | None = None) -> bool:
    """True when ``agent`` is a Kimi seat or ``model`` names a Kimi model."""
    name = str(agent or "").strip().casefold()
    if name in KIMI_AGENT_IDS or name.startswith("acpx-kimi"):
        return True
    return is_kimi_model(model)


def _normalize_owned_path(path: str) -> str:
    text = str(path).strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text


def protected_path_reason(path: str) -> str | None:
    """Why ``path`` is outside neutral coding, or None when a Kimi seat may own it."""
    text = _normalize_owned_path(path)
    parts = PurePosixPath(text).parts
    if not text or text.startswith("/") or ".." in parts:
        return f"owned path {path!r} is not a repository-relative path"
    if text in PROTECTED_ROOT_FILES:
        return f"owned path {text!r} is an agent instruction file"
    for prefix in PROTECTED_PATH_PREFIXES:
        if text == prefix.rstrip("/") or text.startswith(prefix):
            return f"owned path {text!r} is under protected {prefix!r}"
    if PRIVATE_STATE_COMPONENTS.intersection(parts):
        return f"owned path {text!r} is agent-private state"
    if not any(text == root.rstrip("/") or text.startswith(root) for root in NEUTRAL_CODING_ROOTS):
        return f"owned path {text!r} is outside the neutral coding roots {list(NEUTRAL_CODING_ROOTS)}"
    return None


def _curriculum_level_keys(repo_root: Path) -> frozenset[str] | None:
    manifest = repo_root / "curriculum" / "l2-uk-en" / "curriculum.yaml"
    try:
        import yaml

        levels = (yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}).get("levels") or {}
    except Exception:
        return None
    if not isinstance(levels, dict):
        return None
    keys = {str(key).strip().casefold() for key in levels}
    # Versioned level keys (``a1-v1``) name the same track as their base.
    keys |= {key.rsplit("-v", 1)[0] for key in keys if "-v" in key}
    return frozenset(keys)


def curriculum_track_reason(track: str | None, *, repo_root: Path) -> str | None:
    """Why a research track is a curriculum track, or None when it is neutral.

    Fails closed: when the curriculum manifest cannot be read, any track is
    treated as a curriculum track.
    """
    text = str(track or "").strip().casefold()
    if not text:
        return None
    if text in _CURRICULUM_TRACK_NAMES or text.startswith(_CURRICULUM_TRACK_PREFIXES):
        return f"--research-track {track!r} is a curriculum track"
    levels = _curriculum_level_keys(repo_root)
    if levels is None:
        return f"--research-track {track!r} cannot be proven neutral (curriculum manifest unreadable)"
    if text in levels:
        return f"--research-track {track!r} is a curriculum track"
    return None


def prompt_file_reason(prompt_file: str | None) -> str | None:
    """Why the prompt file is private agent state, or None."""
    if not prompt_file:
        return None
    parts = Path(str(prompt_file)).expanduser().parts
    if PRIVATE_STATE_COMPONENTS.intersection(parts):
        return f"--prompt-file {prompt_file!r} lives in agent-private state"
    return None


def neutral_coding_refusal(
    *,
    agent: str,
    model: str | None = None,
    mode: str,
    repo_root: Path,
    review: bool = False,
    review_attempt: bool = False,
    require_review_verdict: bool = False,
    review_profile: str | None = None,
    language_lane: bool = False,
    research_track: str | None = None,
    owned_paths: Iterable[str] = (),
    prompt_file: str | None = None,
    repo_key: str | None = None,
    repo_role: str | None = None,
) -> str | None:
    """The refusal message for a Kimi dispatch outside neutral coding, else None.

    Returns None for every non-Kimi seat. Each reason is collected so the
    caller sees every violated condition at once.
    """
    if not is_kimi_seat(agent, model=model):
        return None
    reasons: list[str] = []
    if mode != _ADMITTED_MODE:
        reasons.append(f"--mode {mode} (only {_ADMITTED_MODE} implementation is admitted)")
    if review or review_attempt or require_review_verdict or review_profile:
        reasons.append("review dispatches (--review-attempt, --require-review-verdict, --review-profile, review type)")
    if language_lane:
        reasons.append("Ukrainian-language work (--language-lane, a Ukrainian review profile or curriculum path)")
    track_reason = curriculum_track_reason(research_track, repo_root=repo_root)
    if track_reason:
        reasons.append(track_reason)
    for path in owned_paths:
        path_reason = protected_path_reason(path)
        if path_reason:
            reasons.append(path_reason)
    file_reason = prompt_file_reason(prompt_file)
    if file_reason:
        reasons.append(file_reason)
    if repo_role is not None and repo_role not in NEUTRAL_REPO_ROLES:
        reasons.append(f"--repo {repo_key or repo_role!r} is a private repository")
    if not reasons:
        return None
    return format_refusal(agent, reasons)


def acp_refusal(participant: str, *, target_agent: str | None = None, model: str | None = None) -> str | None:
    """ACP calls (asks, consults, discussions, ACP reviews) are never neutral coding."""
    if not (is_kimi_seat(participant) or is_kimi_seat(target_agent, model=model)):
        return None
    return format_refusal(participant, ["ACP asks, consults, discussions, and reviews"])


def format_refusal(agent: str, reasons: Iterable[Any]) -> str:
    joined = "; ".join(str(reason) for reason in reasons)
    return (
        f"ROUTING REFUSED: {_POLICY}: {agent} seats are limited to neutral coding "
        f"(workspace-write in {', '.join(NEUTRAL_CODING_ROOTS)}; no Ukrainian-language content, "
        f"rules/policy, or private material). Refused: {joined}. Alternative seats: {KIMI_ALTERNATIVES}."
    )
