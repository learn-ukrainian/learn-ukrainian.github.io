"""Kimi seats admit web, UI and backend coding only.

Kimi: web, UI and backend coding only — no Ukrainian-language content, no
reviews, consults, design or rules.

Every Kimi seat (``kimi``, ``kimicc``, the ``acpx-kimi*`` ACP seats, and any
``kimi-code/*`` / ``kimi-k*`` model id) is limited to workspace-write
implementation of paths on an explicit allowlist. Anything not on the
allowlist is refused.

``refuse_kimi_if_disallowed`` is the one gate. Every entry point calls it
first, after resolving the effective seats and models (overrides, pins and
substitutes) and before any telemetry, broker message, failure record, state
write, artifact store or channel write. A refusal raises
``KimiAdmissionRefused`` to the caller and records nothing.

Ukrainian content is recognised by content, not by path: an owned file, or any
file under an owned directory or glob, that contains a Cyrillic character is
refused, and ``refuse_kimi_changes`` rejects a Kimi change set that adds one or
adds content that cannot be read as text. The git hooks and push block around a
Kimi worktree live in ``kimi_boundary``.
"""

from __future__ import annotations

import codecs
import os
import posixpath
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
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

# Modes. Only workspace-write implementation is admitted; the other labels
# name the activity an entry point is about to perform.
ADMITTED_MODE = "workspace-write"
ACP_MODE = "acp"
REVIEW_MODE = "review"
_MODE_ACTIVITIES = {
    ACP_MODE: "ACP asks, consults, discussions, and reviews",
    REVIEW_MODE: "review dispatches",
}

# Backend/tooling packages verified to hold no Ukrainian-language data,
# prompts or grammar. Each admits the package and its tests under tests/<same>/.
_BACKEND_PACKAGES = {
    "agent_runtime": "agent CLI adapters, runner, routing and telemetry",
    "api": "monitoring API routers and dashboards",
    "orchestration": "dispatch, worktree, task-record and merge tooling",
    "ci": "CI sharding, timing and change-classification helpers",
    "fleet_comms": "fleet message plane, request executor and artifact store",
    "hygiene": "repository and session hygiene guards",
    "storage": "storage topology, artifacts and data-volume guards",
}

# The allowlist: the only paths a Kimi seat may own. Keys ending in ``/`` are
# directory roots; other keys are single files. Each carries its reason.
KIMI_OWNED_ROOTS: dict[str, str] = {
    "site/src/components/": "site UI components",
    "site/src/layouts/": "site page layouts",
    "site/src/pages/": "site routes and page shells",
    "site/src/styles/": "site stylesheets",
    "site/src/css/": "site stylesheets",
    "site/src/assets/": "site static assets",
    "site/src/lib/a1-archive-routes.ts": "archive route helper; no language data",
    "site/src/lib/arc.ts": "arc data types and helpers; no language data",
    "site/src/lib/doc-nav.ts": "docs page route helpers",
    "site/src/lib/readings.ts": "reading visibility predicate",
    **{f"scripts/{name}/": reason for name, reason in _BACKEND_PACKAGES.items()},
    **{f"tests/{name}/": f"tests of scripts/{name}/" for name in _BACKEND_PACKAGES},
    ".github/workflows/": "CI workflows",
    ".github/actions/": "composite CI actions",
    ".github/codeql/": "CodeQL configuration",
    ".github/dependabot.yml": "dependency update configuration",
    ".dagger/": "Dagger CI module",
}
# Site build and test configuration at the site root (astro.config.mjs, vitest.config.ts...).
SITE_CONFIG_REASON = "site build and test configuration"
_SITE_CONFIG_FILE = re.compile(r"^site/[^/]+\.config\.[^/]+$")

# Paths inside an allowlisted root that are still refused. Keys match as
# prefixes, so ``scripts/api/hramatka_`` covers every Hramatka module.
KIMI_EXCLUDED_PATHS: dict[str, str] = {
    "scripts/agent_runtime/kimi_admission.py": "the Kimi admission gate is routing policy",
    "scripts/agent_runtime/kimi_boundary.py": "the Kimi worktree boundary is routing policy",
    "scripts/agent_runtime/kimi_hooks/": "the Kimi worktree boundary is routing policy",
    "scripts/agent_runtime/env_sanitize.py": "the agent credential boundary, including Kimi's push block",
    "scripts/agent_runtime/adapters/kimi.py": "Kimi's own runtime refusal is routing policy",
    "scripts/agent_runtime/adapters/kimicc.py": "Kimi's own runtime refusal is routing policy",
    "scripts/agent_runtime/kimicc_headless.sh": "Kimi's own runtime refusal is routing policy",
    "tests/agent_runtime/adapters/test_kimi_adapter.py": "tests of Kimi's routing policy",
    "tests/agent_runtime/adapters/test_kimicc_headless.py": "tests of Kimi's routing policy",
    "scripts/agent_runtime/profiles/": "reviewer prompt profiles",
    "scripts/api/hramatka_": "Hramatka lesson generation and grammar quality gates",
    "tests/api/test_hramatka_": "Hramatka lesson generation and grammar quality gates",
    "scripts/api/sources_router.py": "Ukrainian dictionary and corpus lookups",
    "tests/api/test_sources_router": "Ukrainian dictionary and corpus lookups",
    "scripts/orchestration/curriculum_": "curriculum lifecycle, readiness and preparation",
    "tests/orchestration/test_curriculum_": "curriculum lifecycle, readiness and preparation",
    "scripts/orchestration/prompt_contracts.py": "curriculum phase prompt contracts",
    "tests/orchestration/test_prompt_contracts.py": "curriculum phase prompt contracts",
    "scripts/orchestration/preparation_evidence.py": "curriculum preparation evidence",
}

# Fleet repository roles a Kimi seat may target (scripts/config/fleet_repos.yaml).
CODING_REPO_ROLES = frozenset({"public-monorepo"})
# Research tracks that are always curriculum tracks, in addition to every level
# key of the curriculum manifest.
_CURRICULUM_TRACK_NAMES = frozenset({"core", "seminar", "seminars", "hramatka"})
_CURRICULUM_TRACK_PREFIXES = ("l2-uk",)
# tool_config keys that mark a review or sealed review attempt.
_REVIEW_TOOL_CONFIG_KEYS = ("review_verdict_required", "review_isolation", "review_id")
# Components of a prompt-file path that mark agent-private state.
_PRIVATE_STATE_COMPONENTS = frozenset({".claude", ".agent", ".codex"})
# The Cyrillic and Cyrillic Supplement blocks: any such character marks Ukrainian content.
CYRILLIC = re.compile("[Ѐ-ӿԀ-ԯ]")
_GLOB_CHARS = frozenset("*?[")
# Build and dependency output skipped when a directory or glob scope is expanded.
_SCOPE_SKIPPED_DIRS = frozenset({".git", "node_modules", "__pycache__", ".pytest_cache", ".astro", "dist"})
_DIFF_SAMPLE_LIMIT = 5


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
    """True when ``agent`` is a Kimi seat (``kimi``, ``kimicc``, ``kimi-<lane>`` slots, ``acpx-kimi*``) or ``model`` names a Kimi model."""
    name = str(agent or "").strip().casefold()
    if name in KIMI_AGENT_IDS or name.startswith(("kimi-", "acpx-kimi")):
        return True
    return is_kimi_model(model)


def normalize_owned_path(path: str) -> str | None:
    """The repository-relative POSIX form of ``path``, or None when it is absolute or escapes the repository.

    Separators are unified and collapsed and ``.``/``..`` segments are resolved
    lexically, so ``site//src/components/x`` and ``./docs/../scripts/x`` reach
    the allowlist in their canonical form.
    """
    text = str(path).strip().replace("\\", "/")
    if not text or text.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", text):
        return None
    normalized = posixpath.normpath(text)
    if normalized == "." or normalized == ".." or normalized.startswith("../"):
        return None
    return normalized


def _allowlist_match(normalized: str) -> str | None:
    for root in KIMI_OWNED_ROOTS:
        if normalized == root.rstrip("/") or (root.endswith("/") and normalized.startswith(root)):
            return root
    if _SITE_CONFIG_FILE.match(normalized):
        return "site/*.config.*"
    return None


def owned_path_reason(path: str) -> str | None:
    """Why a Kimi seat may not own ``path``, or None when the allowlist admits it.

    The allowlist matches case-sensitively, so a differently cased path is
    refused; exclusions match case-insensitively, so a case-insensitive
    filesystem cannot reach an excluded file through another spelling.
    """
    normalized = normalize_owned_path(path)
    if normalized is None:
        return f"owned path {path!r} is not a repository-relative path"
    if _allowlist_match(normalized) is None:
        return f"owned path {normalized!r} is not on the Kimi allowlist"
    folded = normalized.casefold()
    for prefix, reason in KIMI_EXCLUDED_PATHS.items():
        if folded.startswith(prefix):
            return f"owned path {normalized!r} is excluded ({reason})"
    return None


def _walk_files(repo_root: Path, base: str) -> Iterable[str]:
    for directory, subdirs, files in os.walk(repo_root / base):
        subdirs[:] = sorted(name for name in subdirs if name not in _SCOPE_SKIPPED_DIRS)
        rel_dir = Path(directory).relative_to(repo_root).as_posix()
        for name in sorted(files):
            yield f"{rel_dir}/{name}" if rel_dir != "." else name


def scope_files(normalized: str, *, repo_root: Path) -> tuple[bool, list[str]]:
    """Whether ``normalized`` is a directory or glob scope, and the existing files it owns.

    Ownership is read as dispatch reads it: a directory owns its subtree and a
    glob is a case-sensitive ``fnmatch`` pattern whose ``*`` also crosses
    ``/``. A single file owns itself; a path that does not exist yet owns no
    existing file.
    """
    import fnmatch

    if _GLOB_CHARS.intersection(normalized):
        literal: list[str] = []
        for segment in normalized.split("/"):
            if _GLOB_CHARS.intersection(segment):
                break
            literal.append(segment)
        base = "/".join(literal)
        if not base or not (repo_root / base).is_dir():
            return True, []
        return True, [rel for rel in _walk_files(repo_root, base) if fnmatch.fnmatchcase(rel, normalized)]
    target = repo_root / normalized
    if target.is_dir():
        return True, list(_walk_files(repo_root, normalized))
    return False, [normalized] if target.is_file() else []


def _has_cyrillic(path: Path) -> bool:
    # A file that reads as no text (a binary asset) carries no text content.
    return any(CYRILLIC.search(text) for text in text_readings(path.read_bytes()).values())


def _sample(paths: list[str]) -> str:
    shown = ", ".join(repr(path) for path in paths[:_DIFF_SAMPLE_LIMIT])
    return shown + (f" and {len(paths) - _DIFF_SAMPLE_LIMIT} more" if len(paths) > _DIFF_SAMPLE_LIMIT else "")


def owned_scope_reasons(path: str, *, repo_root: Path | None) -> list[str]:
    """Why an allowlisted owned path is still refused for its content or its descendants.

    Any owned file, or file under an owned directory or glob, that contains a
    Cyrillic character is Ukrainian content. A directory or glob scope that
    also covers an excluded or off-allowlist file must be narrowed to specific
    files or clean subdirectories. Fails closed without a repository root.
    """
    normalized = normalize_owned_path(path)
    if normalized is None:
        return []
    if repo_root is None:
        return [f"owned path {normalized!r} cannot be checked for Ukrainian content (no repository root)"]
    is_scope, files = scope_files(normalized, repo_root=repo_root)
    reasons: list[str] = []
    if is_scope:
        blocked = [rel for rel in files if owned_path_reason(rel)]
        if blocked:
            reasons.append(
                f"owned scope {normalized!r} contains excluded or off-allowlist paths ({_sample(blocked)}); "
                "narrow it to specific files or clean subdirectories"
            )
    try:
        cyrillic = [rel for rel in files if _has_cyrillic(repo_root / rel)]
    except OSError as exc:
        return [*reasons, f"owned path {normalized!r} cannot be checked for Ukrainian content ({exc})"]
    if cyrillic:
        where = f"owned scope {normalized!r} holds" if is_scope else "owned file holds"
        reasons.append(f"{where} Ukrainian content (Cyrillic text in {_sample(cyrillic)})")
    return reasons


@dataclass(frozen=True)
class FileChange:
    """One changed path: its content before and after, as bytes.

    ``before`` is None for a new file. ``after`` is None for a deleted file
    (``deleted``) or for a post-image that could not be read.
    """

    path: str
    before: bytes | None
    after: bytes | None
    deleted: bool = False


# Byte-order marks, longest first: the UTF-32-LE mark begins with the UTF-16-LE one.
_BOM_ENCODINGS = (
    (codecs.BOM_UTF32_LE, "utf-32"),
    (codecs.BOM_UTF32_BE, "utf-32"),
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)
_WIDE_ENCODINGS = ("utf-16-le", "utf-16-be", "utf-32-le", "utf-32-be")


def text_readings(data: bytes) -> dict[str, str]:
    """Every way ``data`` reads as text, by encoding; empty when it reads as none.

    A byte-order mark fixes the encoding. Without one the bytes are read as
    UTF-8 and, when they hold a NUL, also as UTF-16 and UTF-32 in both byte
    orders, so neither a NUL byte (which makes git call a file binary) nor a
    wide encoding hides Cyrillic text.
    """
    for bom, encoding in _BOM_ENCODINGS:
        if data.startswith(bom):
            try:
                return {encoding: data.decode(encoding)}
            except UnicodeDecodeError:
                return {}
    readings: dict[str, str] = {}
    candidates = ("utf-8", *_WIDE_ENCODINGS) if b"\0" in data else ("utf-8",)
    for encoding in candidates:
        try:
            readings[encoding] = data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return readings


def added_cyrillic_lines(before: bytes | None, after: bytes) -> list[str] | None:
    """The lines ``after`` adds over ``before`` that contain a Cyrillic character; None when ``after`` is not text.

    Lines are compared per reading, as multisets, so moving a line that already
    held Cyrillic text adds nothing and a second copy of it adds one.
    """
    readings = text_readings(after)
    if not readings:
        return None
    previous = text_readings(before) if before is not None else {}
    added: list[str] = []
    for encoding, text in readings.items():
        existing = Counter(previous.get(encoding, "").splitlines())
        for line in text.splitlines():
            if not CYRILLIC.search(line):
                continue
            if existing[line]:
                existing[line] -= 1
                continue
            sample = line.strip()[:80]
            if sample not in added:
                added.append(sample)
    return added


def change_reasons(changes: Iterable[FileChange]) -> list[str]:
    """Why a Kimi change set is refused: it adds Cyrillic text or a Cyrillic file name, or adds content that is not text."""
    cyrillic: list[str] = []
    unreadable: list[str] = []
    for change in changes:
        if change.deleted:
            continue
        if CYRILLIC.search(change.path):
            cyrillic.append(f"{change.path}: (file name)")
        lines = None if change.after is None else added_cyrillic_lines(change.before, change.after)
        if lines is None:
            unreadable.append(change.path)
            continue
        cyrillic.extend(f"{change.path}: {line}" for line in lines)
    reasons: list[str] = []
    if cyrillic:
        shown = "; ".join(cyrillic[:_DIFF_SAMPLE_LIMIT])
        more = f"; and {len(cyrillic) - _DIFF_SAMPLE_LIMIT} more" if len(cyrillic) > _DIFF_SAMPLE_LIMIT else ""
        reasons.append(f"the changes add Ukrainian content (Cyrillic text: {shown}{more})")
    if unreadable:
        reasons.append(
            f"the changes add content that cannot be read as text ({_sample(unreadable)}); "
            "binary files cannot be checked for Ukrainian content"
        )
    return reasons


def refuse_kimi_changes(agent: str, changes: Iterable[FileChange]) -> None:
    """Raise ``KimiAdmissionRefused`` when a Kimi worker's changes add Cyrillic text or unreadable content."""
    reasons = change_reasons(changes)
    if reasons:
        raise KimiAdmissionRefused(format_refusal(agent, reasons))


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


def curriculum_track_reason(track: str | None, *, repo_root: Path | None) -> str | None:
    """Why a research track is a curriculum track, or None when it is not.

    Fails closed: when the curriculum manifest cannot be read, any track is
    treated as a curriculum track.
    """
    text = str(track or "").strip().casefold()
    if not text:
        return None
    if text in _CURRICULUM_TRACK_NAMES or text.startswith(_CURRICULUM_TRACK_PREFIXES):
        return f"--research-track {track!r} is a curriculum track"
    levels = _curriculum_level_keys(repo_root) if repo_root is not None else None
    if levels is None:
        return f"--research-track {track!r} cannot be proven non-curriculum (curriculum manifest unreadable)"
    if text in levels:
        return f"--research-track {track!r} is a curriculum track"
    return None


def _kimi_seat_name(participants: Iterable[str | None], models: Iterable[str | None]) -> str | None:
    for participant in participants:
        if is_kimi_seat(participant):
            return str(participant).strip()
    for model in models:
        if is_kimi_model(model):
            return str(model).strip()
    return None


def refuse_kimi_if_disallowed(
    effective_participants: Iterable[str | None],
    effective_models: Iterable[str | None] = (),
    *,
    mode: str,
    paths: Iterable[str] = (),
    repo: str | None = None,
    review: bool = False,
    tool_config: Mapping[str, Any] | None = None,
    language_lane: bool = False,
    research_track: str | None = None,
    prompt_file: str | None = None,
    repo_root: Path | None = None,
    execution_root: Path | None = None,
) -> None:
    """Raise ``KimiAdmissionRefused`` when any effective seat or model is Kimi and the work is not admitted.

    ``effective_participants`` and ``effective_models`` are the seats and
    models after every override, pin and substitution. ``mode`` is the
    runtime mode (only ``workspace-write`` is admitted) or an activity label
    (``ACP_MODE``, ``REVIEW_MODE``). ``paths`` are the owned paths, each of
    which must be on the allowlist, free of Cyrillic text and, for a directory
    or glob, free of excluded descendants, read in ``execution_root`` — the
    checkout the worker runs in — or ``repo_root`` when it is not given.
    ``repo`` is the fleet repository role. It reads only the owned files and
    the curriculum manifest under ``repo_root`` (for ``research_track``) and
    never writes. Returns None for every non-Kimi call.
    """
    seat = _kimi_seat_name(tuple(effective_participants), tuple(effective_models))
    if seat is None:
        return
    reasons: list[str] = []
    if mode != ADMITTED_MODE:
        reasons.append(_MODE_ACTIVITIES.get(mode) or f"--mode {mode} (only {ADMITTED_MODE} implementation is admitted)")
    config = tool_config or {}
    if review or any(config.get(key) for key in _REVIEW_TOOL_CONFIG_KEYS):
        reasons.append("review dispatches")
    if language_lane:
        reasons.append("Ukrainian-language work (--language-lane, a Ukrainian review profile or curriculum path)")
    track_reason = curriculum_track_reason(research_track, repo_root=repo_root)
    if track_reason:
        reasons.append(track_reason)
    for path in paths:
        path_reason = owned_path_reason(path)
        if path_reason:
            reasons.append(path_reason)
        else:
            reasons.extend(owned_scope_reasons(path, repo_root=execution_root or repo_root))
    if prompt_file and _PRIVATE_STATE_COMPONENTS.intersection(Path(str(prompt_file)).expanduser().parts):
        reasons.append(f"--prompt-file {prompt_file!r} lives in agent-private state")
    if repo is not None and repo not in CODING_REPO_ROLES:
        reasons.append(f"--repo role {repo!r} is a private repository")
    if reasons:
        raise KimiAdmissionRefused(format_refusal(seat, reasons))


def format_refusal(agent: str, reasons: Iterable[Any]) -> str:
    joined = "; ".join(str(reason) for reason in reasons)
    return (
        f"ROUTING REFUSED: {_POLICY}: {POLICY_LINE} {agent} seats take workspace-write implementation of "
        f"allowlisted UI and backend paths without Cyrillic text only "
        f"(KIMI_OWNED_ROOTS in scripts/agent_runtime/kimi_admission.py). "
        f"Refused: {joined}. Alternative seats: {KIMI_ALTERNATIVES}."
    )
