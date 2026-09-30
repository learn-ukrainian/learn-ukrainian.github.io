"""Kimi seats admit web, UI and backend coding only.

Kimi: web, UI and backend coding only — no Ukrainian-language content, no
reviews, consults, design or rules.

Every Kimi seat (``kimi``, ``kimicc``, the ``acpx-kimi*`` ACP seats, and any
``kimi-code/*`` / ``kimi-k*`` model id) is limited to workspace-write
implementation in site UI code, backend/tooling code and tests. The checks here
are pure and run before any side effect. Entry points call them first:
``delegate.py dispatch`` and its worker, ``runner.invoke``, the Kimi adapters,
the ACP ask/discussion seams, the fleet-comms authority, and ``ask-* --review``.
"""

from __future__ import annotations

import posixpath
import re
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath
from typing import Any

POLICY_LINE = (
    "Kimi: web, UI and backend coding only — no Ukrainian-language content, no reviews, consults, design or rules."
)
KIMI_AGENT_IDS = frozenset({"kimi", "kimicc"})
KIMI_ALTERNATIVES = (
    "use claude, codex, or grok for reviews, consults, and discussions; "
    "claude, codex, or agy for Ukrainian-language content"
)
_POLICY = "KIMI CODING-ONLY"
ADMITTED_MODE = "workspace-write"
ACP_ACTIVITY = "ACP asks, consults, discussions, and reviews"

# Owned paths a Kimi seat may write: site UI code, backend/tooling code, tests,
# CI and the Dagger module. Everything else is refused, and the protected
# families below are refused even when they sit under an allowed root.
CODING_ROOTS = (
    "scripts/",
    "tests/",
    ".github/",
    ".dagger/",
    "site/src/components/",
    "site/src/layouts/",
    "site/src/pages/",
    "site/src/styles/",
    "site/src/css/",
    "site/src/assets/",
    "site/src/lib/",
    "site/tests/",
    "site/e2e/",
)
# Site build/test configuration at the site root (astro.config.mjs, vitest.config.ts...).
_SITE_CONFIG_FILE = re.compile(r"^site/[^/]+\.config\.[^/]+$")
# Code directories whose logic encodes Ukrainian grammar, morphology, stress,
# lexicon or language-correctness rules (site/src/lib/ and scripts/ otherwise
# admit coding). Each entry carries its one-line reason.
UKRAINIAN_CODE_FAMILIES = {
    "site/src/lib/lexicon/": "grammar mechanics, VESUM form keys, heteronyms and lexicon runtime for the word atlas",
    "scripts/lexicon/": "lexicon builders, VESUM shards, heteronym and calque corrections",
    "scripts/linguistics/": "Ukrainian tokenizer",
    "scripts/verification/": "VESUM, stress and Russian-morphology checks",
    "scripts/vocab/": "vocabulary extraction and lexical sandbox over Ukrainian words",
    "scripts/vocab_audit/": "vocabulary audit of Ukrainian word lists",
    "scripts/mphdict/": "morphological dictionary queries",
    "scripts/etymology/": "etymology, cognate and Ukrainian transliteration logic",
    "scripts/practice/": "per-part-of-speech grammar mechanics engines and paradigm densification",
    "scripts/atlas/": "lexical projection, normalization and VESUM attestation for the word atlas",
    "scripts/audit/checks/": "language-correctness checks: grammar, euphony, morphology, stress, russicisms",
    "scripts/projects/open_model_data/": "Ukrainian grammar, decolonization and correction datasets",
    "scripts/projects/ua_eval_harness/": "Ukrainian-language evaluation cases",
    "scripts/projects/ua_open_weight_eval/": "Ukrainian-language model evaluation",
    "scripts/data/": "stress overrides and other Ukrainian language data tables",
    "scripts/build/universal_rules/": "Ukrainian-language writing and grammar rules for the build",
}
UKRAINIAN_CODE_PREFIXES = tuple(UKRAINIAN_CODE_FAMILIES)
# File and directory names under these roots that mark Ukrainian language logic
# wherever they sit (scripts/pipeline/stress_annotator.py, scripts/audit/russianism_eval.py...).
_LANGUAGE_CODE_ROOTS = ("scripts/", "site/src/lib/")
_LANGUAGE_CODE_NAME = re.compile(
    r"vesum|pymorphy|morph|stress|grammar|euphon|russic|russianism|calque|mechanics|paradigm|declens"
    r"|conjug|inflect|phonet|orthoepy|translit|lexicon|lexical|heteronym"
)
PROTECTED_PATH_PREFIXES = (
    # Ukrainian-language content and data.
    "curriculum/",
    "wiki/",
    "data/",
    "registry/",
    "site/src/content/",
    "site/src/data/",
    "site/src/lexicon/",
    "site/src/lib/i18n/",
    # Ukrainian grammar, morphology, stress and lexicon code: it encodes
    # language rules, so editing it is Ukrainian-language work.
    *UKRAINIAN_CODE_PREFIXES,
    # Rules, instructions and private agent state.
    "docs/",
    "agents_extensions/shared/rules/",
    "agents_extensions/shared/memory/",
    "agents_extensions/shared/skills/",
    ".claude/",
    ".agent/",
    ".codex/",
)
PROTECTED_ROOT_FILES = frozenset({"claude.md", "agents.md", "gemini.md"})
# Path components that mark agent-private state wherever they appear.
PRIVATE_STATE_COMPONENTS = frozenset({".claude", ".agent", ".codex"})
# Locale and translation files are Ukrainian-language content wherever they sit.
_LOCALE_COMPONENTS = frozenset({"i18n", "l10n", "locale", "locales", "translation", "translations"})
_LOCALE_SUFFIXES = frozenset({".po", ".pot", ".mo", ".ftl", ".xliff", ".xlf", ".arb"})
# Language-tagged message catalogs such as ``uk.json`` or ``messages.uk-UA.yaml``.
_LOCALE_TAGGED_NAME = re.compile(r"(^|[._-])(uk|uk[-_]ua)\.(json|ya?ml|toml|properties|strings|resx)$")
# Fleet repository roles a Kimi seat may target (scripts/config/fleet_repos.yaml).
CODING_REPO_ROLES = frozenset({"public-monorepo"})
# Research tracks that are always curriculum tracks, in addition to every level
# key of the curriculum manifest.
_CURRICULUM_TRACK_NAMES = frozenset({"core", "seminar", "seminars", "hramatka"})
_CURRICULUM_TRACK_PREFIXES = ("l2-uk",)
# tool_config keys that mark a review or sealed review attempt.
_REVIEW_TOOL_CONFIG_KEYS = ("review_verdict_required", "review_isolation", "review_id")


class KimiAdmissionRefused(ValueError):
    """A Kimi seat was asked for work outside web, UI and backend coding."""


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


def normalize_owned_path(path: str) -> str | None:
    """The repository-relative POSIX form of ``path``, or None when it is absolute or escapes the repository.

    Separators are unified and collapsed and ``.``/``..`` segments are resolved
    lexically, so ``site//src/content/x`` and ``./docs/../docs/x`` reach the
    prefix checks in their canonical form.
    """
    text = str(path).strip().replace("\\", "/")
    if not text or text.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", text):
        return None
    normalized = posixpath.normpath(text)
    if normalized == "." or normalized == ".." or normalized.startswith("../"):
        return None
    return normalized


def _is_locale_path(parts: tuple[str, ...]) -> bool:
    if _LOCALE_COMPONENTS.intersection(parts):
        return True
    name = parts[-1]
    return PurePosixPath(name).suffix in _LOCALE_SUFFIXES or bool(_LOCALE_TAGGED_NAME.search(name))


def protected_path_reason(path: str) -> str | None:
    """Why ``path`` is outside web, UI and backend coding, or None when a Kimi seat may own it."""
    normalized = normalize_owned_path(path)
    if normalized is None:
        return f"owned path {path!r} is not a repository-relative path"
    folded = normalized.casefold()
    parts = PurePosixPath(folded).parts
    if folded in PROTECTED_ROOT_FILES:
        return f"owned path {normalized!r} is an agent instruction file"
    for prefix in PROTECTED_PATH_PREFIXES:
        if folded == prefix.rstrip("/") or folded.startswith(prefix):
            return f"owned path {normalized!r} is under protected {prefix!r}"
    if PRIVATE_STATE_COMPONENTS.intersection(parts):
        return f"owned path {normalized!r} is agent-private state"
    if folded.startswith(_LANGUAGE_CODE_ROOTS) and any(_LANGUAGE_CODE_NAME.search(part) for part in parts):
        return f"owned path {normalized!r} is Ukrainian grammar, morphology, stress or lexicon code"
    if _is_locale_path(parts):
        return f"owned path {normalized!r} is a locale or translation file"
    if _SITE_CONFIG_FILE.match(folded):
        return None
    if not any(folded == root.rstrip("/") or folded.startswith(root) for root in CODING_ROOTS):
        return f"owned path {normalized!r} is outside the coding roots {list(CODING_ROOTS)}"
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
    """Why a research track is a curriculum track, or None when it is not.

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
        return f"--research-track {track!r} cannot be proven non-curriculum (curriculum manifest unreadable)"
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


def _mode_reason(mode: str) -> str | None:
    if mode != ADMITTED_MODE:
        return f"--mode {mode} (only {ADMITTED_MODE} implementation is admitted)"
    return None


def dispatch_refusal(
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
    """The refusal message for a Kimi dispatch outside web, UI and backend coding, else None.

    Returns None for every non-Kimi seat. Each reason is collected so the
    caller sees every violated condition at once.
    """
    if not is_kimi_seat(agent, model=model):
        return None
    reasons: list[str] = []
    mode_reason = _mode_reason(mode)
    if mode_reason:
        reasons.append(mode_reason)
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
    if repo_role is not None and repo_role not in CODING_REPO_ROLES:
        reasons.append(f"--repo {repo_key or repo_role!r} is a private repository")
    if not reasons:
        return None
    return format_refusal(agent, reasons)


def runtime_refusal(
    agent: str,
    *,
    mode: str,
    model: str | None = None,
    tool_config: Mapping[str, Any] | None = None,
    review: bool = False,
) -> str | None:
    """The runtime-boundary refusal for a Kimi invocation, else None.

    ``runner.invoke``, the Kimi adapters and the delegate worker call this
    before any spawn: only workspace-write invocations with no review marker
    are admitted.
    """
    if not is_kimi_seat(agent, model=model):
        return None
    reasons: list[str] = []
    mode_reason = _mode_reason(mode)
    if mode_reason:
        reasons.append(mode_reason)
    config = tool_config or {}
    if review or any(config.get(key) for key in _REVIEW_TOOL_CONFIG_KEYS):
        reasons.append("review dispatches")
    if not reasons:
        return None
    return format_refusal(agent, reasons)


def require_runtime_admission(
    agent: str,
    *,
    mode: str,
    model: str | None = None,
    tool_config: Mapping[str, Any] | None = None,
    review: bool = False,
) -> None:
    """Raise ``KimiAdmissionRefused`` when ``runtime_refusal`` refuses the invocation."""
    refusal = runtime_refusal(agent, mode=mode, model=model, tool_config=tool_config, review=review)
    if refusal:
        raise KimiAdmissionRefused(refusal)


def acp_refusal(
    participant: str,
    *,
    target_agent: str | None = None,
    model: str | None = None,
    activity: str = ACP_ACTIVITY,
) -> str | None:
    """ACP calls (asks, consults, discussions, ACP reviews) and ask reviews are never coding."""
    if not (is_kimi_seat(participant) or is_kimi_seat(target_agent, model=model)):
        return None
    return format_refusal(participant, [activity])


def require_acp_admission(
    participant: str,
    *,
    target_agent: str | None = None,
    model: str | None = None,
    activity: str = ACP_ACTIVITY,
) -> None:
    """Raise ``KimiAdmissionRefused`` for a Kimi participant; entry points call this before any side effect."""
    refusal = acp_refusal(participant, target_agent=target_agent, model=model, activity=activity)
    if refusal:
        raise KimiAdmissionRefused(refusal)


def format_refusal(agent: str, reasons: Iterable[Any]) -> str:
    joined = "; ".join(str(reason) for reason in reasons)
    return (
        f"ROUTING REFUSED: {_POLICY}: {POLICY_LINE} {agent} seats take workspace-write implementation in "
        f"{', '.join(CODING_ROOTS)} and site/*.config.* only. Refused: {joined}. "
        f"Alternative seats: {KIMI_ALTERNATIVES}."
    )
