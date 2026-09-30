"""Kimi seats admit web, UI and backend coding only.

Kimi: web, UI and backend coding only — no Ukrainian-language content, no
reviews, consults, design or rules.

Every Kimi seat (``kimi``, ``kimicc``, the ``acpx-kimi*`` ACP seats, and any
``kimi-code/*`` / ``kimi-k*`` model id) is limited to workspace-write
implementation of paths on an explicit allowlist. Anything not on the
allowlist is refused.

``refuse_kimi_if_disallowed`` is the one gate. Entry points reach it through
``target_admission.resolve_and_admit``, which resolves the effective seats and
models (attachments, compat names, route pins, slot holders, substitutes) and
gates them in the same step, before any telemetry, broker message, failure
record, state write, artifact store or channel write; delivery, insertion,
wake and launch sinks take the ``AdmittedTarget`` it returns. Execution-time
re-checks (``refuse_kimi_execution``) gate exactly the seat, model and tree
being run. A refusal raises ``KimiAdmissionRefused`` to the caller and records
nothing.

Content is admitted only as plain text: valid UTF-8 with no control
characters other than tab, LF and CR, and no Cyrillic character (Ukrainian
content is recognised by content, not by path). Anything else — UTF-16 with or
without a byte-order mark, another encoding, a binary file — is refused. The
rule covers every owned file, and every file under an owned directory or glob,
in the tree the worker starts from (``DirectoryTree`` on disk, ``CommitTree``
read with git plumbing), and every changed file's post-image
(``refuse_kimi_changes``). The git hooks and push block around a Kimi worktree
live in ``kimi_boundary``.
"""

from __future__ import annotations

import fnmatch
import json
import os
import posixpath
import re
import subprocess
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

POLICY_LINE = (
    "Kimi: web, UI and backend coding only — no Ukrainian-language content, no reviews, consults, design or rules."
)
KIMI_AGENT_IDS = frozenset({"kimi", "kimicc"})
_POLICY = "KIMI CODING-ONLY"

# Modes. Only workspace-write implementation is admitted; the other labels
# name the activity an entry point is about to perform.
ADMITTED_MODE = "workspace-write"
# ``tool_config`` key carrying the task's declared owned paths from dispatch to the
# runner and the adapters, which hand them to the same gate.
OWNED_PATHS_KEY = "kimi_owned_paths"
ACP_MODE = "acp"
REVIEW_MODE = "review"
BRIDGE_MODE = "bridge"
_MODE_ACTIVITIES = {
    ACP_MODE: "ACP asks, consults, discussions, and reviews",
    REVIEW_MODE: "review dispatches",
    BRIDGE_MODE: "bridge messages, channel posts and inbox drains (Kimi is not a bridge recipient)",
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
    "scripts/agent_runtime/target_admission.py": "target resolution and admission is routing policy",
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
# C0 controls other than tab, LF and CR, DEL, and the C1 controls.
_CONTROL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
TEXT_RULE = (
    "Kimi admits only UTF-8 text without control characters other than tab, LF and CR; "
    "UTF-16, other encodings and binary files are refused"
)
_GLOB_CHARS = frozenset("*?[")
# Build and dependency output skipped when a directory or glob scope is expanded.
_SCOPE_SKIPPED_DIRS = frozenset({".git", "node_modules", "__pycache__", ".pytest_cache", ".astro", "dist"})
_DIFF_SAMPLE_LIMIT = 5
_GIT_TIMEOUT_S = 60
_GIT_REDIRECT_ENV = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
        "GIT_CEILING_DIRECTORIES",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_COMMON_DIR",
    }
)


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


def _literal_base(glob: str) -> str:
    """The directory part of ``glob`` before its first wildcard segment."""
    literal: list[str] = []
    for segment in glob.split("/"):
        if _GLOB_CHARS.intersection(segment):
            break
        literal.append(segment)
    return "/".join(literal)


def scope_files(normalized: str, *, repo_root: Path) -> tuple[bool, list[str]]:
    """Whether ``normalized`` is a directory or glob scope, and the existing files it owns on disk.

    Ownership is read as dispatch reads it: a directory owns its subtree and a
    glob is a case-sensitive ``fnmatch`` pattern whose ``*`` also crosses
    ``/``. A single file owns itself; a path that does not exist yet owns no
    existing file.
    """
    if _GLOB_CHARS.intersection(normalized):
        base = _literal_base(normalized)
        if not base or not (repo_root / base).is_dir():
            return True, []
        return True, [rel for rel in _walk_files(repo_root, base) if fnmatch.fnmatchcase(rel, normalized)]
    target = repo_root / normalized
    if target.is_dir():
        return True, list(_walk_files(repo_root, normalized))
    return False, [normalized] if target.is_file() else []


class ContentTree(Protocol):
    """A tree of files a Kimi worker starts from."""

    def owned_files(self, normalized: str) -> tuple[bool, dict[str, bytes | None]]:
        """Whether ``normalized`` is a directory or glob scope, and each file it owns with its content.

        Content is None for an entry that holds no file content (a submodule).
        Raises ``OSError`` or ``RuntimeError`` when the tree cannot be read.
        """
        ...


@dataclass(frozen=True)
class DirectoryTree:
    """The files on disk under ``root``: a worktree as the worker sees it."""

    root: Path

    def __str__(self) -> str:
        return f"in {self.root}"

    def owned_files(self, normalized: str) -> tuple[bool, dict[str, bytes | None]]:
        is_scope, files = scope_files(normalized, repo_root=self.root)
        return is_scope, {rel: (self.root / rel).read_bytes() for rel in files}


@dataclass(frozen=True)
class CommitTree:
    """The files of ``commit`` in the repository at ``repo``, read with git plumbing and no checkout."""

    repo: Path
    commit: str
    env: Mapping[str, str] | None = None

    def __str__(self) -> str:
        return f"in commit {self.commit[:12]}"

    def _git(self, *args: str, stdin: bytes | None = None) -> bytes:
        proc = subprocess.run(
            ["git", *args],
            cwd=self.repo,
            input=stdin,
            capture_output=True,
            check=False,
            env=None if self.env is None else dict(self.env),
            timeout=_GIT_TIMEOUT_S,
        )
        if proc.returncode != 0:
            detail = proc.stderr.decode("utf-8", "replace").strip() or f"exit {proc.returncode}"
            raise RuntimeError(f"git {args[0]} {self.commit[:12]} failed: {detail}")
        return proc.stdout

    def _entries(self, base: str) -> dict[str, tuple[str, str]]:
        """``path -> (object type, object id)`` for every entry at or under ``base``."""
        entries: dict[str, tuple[str, str]] = {}
        for record in self._git("ls-tree", "-r", "-z", "--full-tree", self.commit, "--", base).split(b"\0"):
            if record:
                meta, _, path = record.partition(b"\t")
                _mode, kind, oid = meta.decode("ascii").split()
                entries[path.decode("utf-8", "surrogateescape")] = (kind, oid)
        return entries

    def _blobs(self, oids: Iterable[str]) -> dict[str, bytes]:
        wanted = sorted(set(oids))
        if not wanted:
            return {}
        out = self._git("cat-file", "--batch", stdin="".join(f"{oid}\n" for oid in wanted).encode("ascii"))
        blobs: dict[str, bytes] = {}
        pos = 0
        while pos < len(out):
            header_end = out.index(b"\n", pos)
            fields = out[pos:header_end].decode("ascii").split()
            if len(fields) != 3:
                raise RuntimeError(f"git cat-file cannot read {fields[0] if fields else 'an object'}")
            start = header_end + 1
            blobs[fields[0]] = out[start : start + int(fields[2])]
            pos = start + int(fields[2]) + 1
        return blobs

    def owned_files(self, normalized: str) -> tuple[bool, dict[str, bytes | None]]:
        if _GLOB_CHARS.intersection(normalized):
            base = _literal_base(normalized)
            entries = self._entries(base) if base else {}
            entries = {path: entry for path, entry in entries.items() if fnmatch.fnmatchcase(path, normalized)}
            is_scope = True
        else:
            entries = self._entries(normalized)
            is_scope = bool(entries) and normalized not in entries
        blobs = self._blobs(oid for kind, oid in entries.values() if kind == "blob")
        return is_scope, {path: blobs.get(oid) if kind == "blob" else None for path, (kind, oid) in entries.items()}


def _sample(paths: list[str]) -> str:
    shown = ", ".join(repr(path) for path in paths[:_DIFF_SAMPLE_LIMIT])
    return shown + (f" and {len(paths) - _DIFF_SAMPLE_LIMIT} more" if len(paths) > _DIFF_SAMPLE_LIMIT else "")


_CYRILLIC_TEXT = "Cyrillic text"


def content_problem(data: bytes | None) -> str | None:
    """Why ``data`` is not admissible Kimi content, or None when it is.

    Admissible content is UTF-8 text with no control characters other than
    tab, LF and CR, and no Cyrillic character. None (no file content) is not
    admissible either.
    """
    if data is None:
        return "no file content"
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return "not UTF-8"
    if _CONTROL.search(text):
        return "control characters"
    if CYRILLIC.search(text):
        return _CYRILLIC_TEXT
    return None


def owned_scope_reasons(path: str, tree: ContentTree) -> list[str]:
    """Why an allowlisted owned path is still refused for its content or its descendants in ``tree``.

    Every owned file, and every file under an owned directory or glob, must be
    plain UTF-8 text without Cyrillic text or a Cyrillic file name. A directory
    or glob scope that also covers an excluded or off-allowlist file must be
    narrowed to specific files or clean subdirectories. Fails closed when the
    tree cannot be read.
    """
    normalized = normalize_owned_path(path)
    if normalized is None:
        return []
    try:
        is_scope, files = tree.owned_files(normalized)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        return [f"owned path {normalized!r} cannot be checked for Ukrainian content {tree} ({exc})"]
    reasons: list[str] = []
    if is_scope:
        blocked = [rel for rel in files if owned_path_reason(rel)]
        if blocked:
            reasons.append(
                f"owned scope {normalized!r} contains excluded or off-allowlist paths ({_sample(blocked)}); "
                "narrow it to specific files or clean subdirectories"
            )
    cyrillic: list[str] = []
    not_text: list[str] = []
    for rel, data in files.items():
        problem = content_problem(data)
        if CYRILLIC.search(rel) or problem == _CYRILLIC_TEXT:
            cyrillic.append(rel)
        elif problem:
            not_text.append(rel)
    where = f"owned scope {normalized!r} holds" if is_scope else "owned file holds"
    if cyrillic:
        reasons.append(f"{where} Ukrainian content (Cyrillic text in {_sample(cyrillic)}, {tree})")
    if not_text:
        reasons.append(f"{where} content that is not plain text ({_sample(not_text)}, {tree}); {TEXT_RULE}")
    return reasons


@dataclass(frozen=True)
class FileChange:
    """One changed path and its post-image: None for a deleted file (``deleted``) or an unreadable one."""

    path: str
    after: bytes | None
    deleted: bool = False


def _first_cyrillic_line(data: bytes) -> str:
    text = data.decode("utf-8")
    return next(line.strip()[:80] for line in text.splitlines() if CYRILLIC.search(line))


def change_reasons(changes: Iterable[FileChange]) -> list[str]:
    """Why a Kimi change set is refused: a changed file is not plain UTF-8 text, or holds Cyrillic text or a Cyrillic name."""
    cyrillic: list[str] = []
    not_text: list[str] = []
    for change in changes:
        if change.deleted:
            continue
        if CYRILLIC.search(change.path):
            cyrillic.append(f"{change.path}: (file name)")
        problem = content_problem(change.after)
        if problem == _CYRILLIC_TEXT:
            cyrillic.append(f"{change.path}: {_first_cyrillic_line(change.after or b'')}")
        elif problem:
            not_text.append(change.path)
    reasons: list[str] = []
    if cyrillic:
        shown = "; ".join(cyrillic[:_DIFF_SAMPLE_LIMIT])
        more = f"; and {len(cyrillic) - _DIFF_SAMPLE_LIMIT} more" if len(cyrillic) > _DIFF_SAMPLE_LIMIT else ""
        reasons.append(f"the changed files hold Ukrainian content (Cyrillic text: {shown}{more})")
    if not_text:
        reasons.append(f"the changed files hold content that is not plain text ({_sample(not_text)}); {TEXT_RULE}")
    return reasons


def refuse_kimi_changes(agent: str, changes: Iterable[FileChange]) -> None:
    """Raise ``KimiAdmissionRefused`` when a Kimi worker's changed files are not plain text or hold Cyrillic text."""
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


# Metadata keys that can name the model or the recipient of a request. A stored
# ``data`` payload is merged into a message's metadata, so the gate reads these
# keys from every attachment, not just the explicit arguments.
MODEL_SELECTOR_KEYS = ("to_model", "model", "target_model", "requested_model")
SEAT_SELECTOR_KEYS = (
    "to",
    "to_llm",
    "to_agent",
    "to_agents",
    "agent",
    "agents",
    "target",
    "route",
    "recipient",
    "recipients",
    "participant",
    "participants",
)


def attachment_metadata(data: Any) -> dict[str, Any]:
    """The metadata a ``data`` attachment carries.

    A JSON-object string (or a mapping) is the metadata; any other text is
    stored as ``{"raw": text}``, exactly as ``send_message`` merges it.
    """
    if isinstance(data, Mapping):
        return dict(data)
    if not data or not isinstance(data, str):
        return {}
    if data.startswith("{"):
        try:
            loaded = json.loads(data)
        except (json.JSONDecodeError, ValueError):
            return {"raw": data}
        if isinstance(loaded, dict):
            return loaded
    return {"raw": data}


def _selector_names(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set, frozenset)):
        return [name for item in value for name in _selector_names(item)]
    return []


def effective_request_targets(
    recipients: Iterable[str | None],
    model: str | None = None,
    *attachments: Any,
) -> tuple[list[str | None], list[str | None]]:
    """The final ``(seats, models)`` a request addresses after its attachments are merged.

    A resolver: called only by ``target_admission.resolve_and_admit``.

    Precedence is the one ``send_message`` stores: an explicit ``model`` replaces
    an attachment's ``to_model``; every other model or recipient key an
    attachment carries (``MODEL_SELECTOR_KEYS``, ``SEAT_SELECTOR_KEYS``) is kept
    as written. Attachments may be JSON strings, mappings or lists of mappings.
    A selector value is read as both a seat and a model, so an alias under any
    key is caught.
    """
    seats: list[str | None] = list(recipients)
    models: list[str | None] = [model]
    for attachment in attachments:
        items = attachment if isinstance(attachment, (list, tuple)) else (attachment,)
        for item in items:
            metadata = attachment_metadata(item)
            for key in MODEL_SELECTOR_KEYS:
                if key == "to_model" and model:
                    continue  # the explicit model overrides the attached one
                models.extend(_selector_names(metadata.get(key)))
            for key in SEAT_SELECTOR_KEYS:
                names = _selector_names(metadata.get(key))
                seats.extend(names)
                models.extend(names)
    return seats, models


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
    trees: Sequence[ContentTree] | Callable[[], Sequence[ContentTree]] = (),
    declared_paths: Iterable[str] | None = None,
) -> None:
    """Raise ``KimiAdmissionRefused`` when any effective seat or model is Kimi and the work is not admitted.

    ``effective_participants`` and ``effective_models`` are the seats and
    models after every override, pin and substitution. ``mode`` is the
    runtime mode (only ``workspace-write`` is admitted) or an activity label
    (``ACP_MODE``, ``REVIEW_MODE``). ``paths`` are the owned paths, each of
    which must be on the allowlist; a workspace-write call must declare at
    least one (``declared_paths``, default ``paths``, is what counts as
    declared ownership) and empty ownership is refused. ``repo`` is the fleet repository role and
    ``repo_root`` holds the curriculum manifest read for ``research_track``.

    Only when every one of those checks admits are the owned paths read in
    ``trees`` — the trees the worker starts from (its worktree on disk, the
    commit it is checked out or created from). ``trees`` may be a callable,
    so resolving a base commit never precedes a policy refusal; a callable
    that raises, or owned paths with no tree to read, refuse. Never writes.
    Returns None for every non-Kimi call.
    """
    seat = _kimi_seat_name(tuple(effective_participants), tuple(effective_models))
    if seat is None:
        return
    owned = tuple(paths)
    declared = owned if declared_paths is None else tuple(declared_paths)
    reasons: list[str] = []
    if mode != ADMITTED_MODE:
        reasons.append(_MODE_ACTIVITIES.get(mode) or f"--mode {mode} (only {ADMITTED_MODE} implementation is admitted)")
    elif not declared:
        reasons.append(
            f"{ADMITTED_MODE} without an owned path (declare at least one allowlisted owned file or directory)"
        )
    config = tool_config or {}
    if review or any(config.get(key) for key in _REVIEW_TOOL_CONFIG_KEYS):
        reasons.append("review dispatches")
    if language_lane:
        reasons.append("Ukrainian-language work (--language-lane, a Ukrainian review profile or curriculum path)")
    track_reason = curriculum_track_reason(research_track, repo_root=repo_root)
    if track_reason:
        reasons.append(track_reason)
    reasons.extend(reason for path in owned if (reason := owned_path_reason(path)))
    if prompt_file and _PRIVATE_STATE_COMPONENTS.intersection(Path(str(prompt_file)).expanduser().parts):
        reasons.append(f"--prompt-file {prompt_file!r} lives in agent-private state")
    if repo is not None and repo not in CODING_REPO_ROLES:
        reasons.append(f"--repo role {repo!r} is a private repository")
    if not reasons and owned:
        reasons.extend(_content_reasons(owned, trees))
    if reasons:
        raise KimiAdmissionRefused(format_refusal(seat, reasons))


def _git_env() -> dict[str, str]:
    """The environment without repo-redirecting Git variables, so ``cwd`` names the repository."""
    return {
        key: value
        for key, value in os.environ.items()
        if key not in _GIT_REDIRECT_ENV and not key.startswith("PRE_COMMIT")
    }


def worktree_trees(worktree: Path, *, env: Mapping[str, str] | None = None) -> list[ContentTree]:
    """A worktree as a Kimi worker sees it: its files on disk and the commit checked out there.

    Raises ``RuntimeError`` when the checked-out commit cannot be resolved.
    """
    git_env = _git_env() if env is None else env
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", "HEAD^{commit}"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=dict(git_env),
            timeout=_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"cannot resolve the commit checked out in {worktree} ({exc})") from exc
    head = (proc.stdout or "").strip() if proc.returncode == 0 else ""
    if not head:
        raise RuntimeError(f"cannot resolve the commit checked out in {worktree}")
    return [DirectoryTree(worktree), CommitTree(worktree, head, env=git_env)]


def owned_paths_from_config(tool_config: Mapping[str, Any] | None) -> tuple[str, ...]:
    """The owned paths dispatch declared in ``tool_config`` (``OWNED_PATHS_KEY``); empty when absent."""
    raw = (tool_config or {}).get(OWNED_PATHS_KEY)
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, (list, tuple)):
        return ()
    return tuple(str(item) for item in raw if isinstance(item, str) and item.strip())


def refuse_kimi_execution(
    participants: Iterable[str | None],
    models: Iterable[str | None] = (),
    *,
    mode: str,
    cwd: Path | None,
    tool_config: Mapping[str, Any] | None,
) -> None:
    """The runtime and adapter form of the gate: ownership from ``tool_config``, content read in ``cwd``.

    Calls ``refuse_kimi_if_disallowed`` with the declared owned paths and the
    execution tree (``cwd`` on disk and at its checked-out commit); no cwd is
    a refusal. Runs before any launch plan, attribution or provisioning.
    """

    def trees() -> list[ContentTree]:
        if cwd is None:
            raise RuntimeError("no execution tree (no cwd)")
        return worktree_trees(Path(cwd))

    refuse_kimi_if_disallowed(
        participants,
        models,
        mode=mode,
        paths=owned_paths_from_config(tool_config),
        tool_config=tool_config,
        trees=trees,
    )


def _content_reasons(
    owned: Sequence[str], trees: Sequence[ContentTree] | Callable[[], Sequence[ContentTree]]
) -> list[str]:
    try:
        resolved = trees() if callable(trees) else trees
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        return [f"the tree the worker starts from cannot be read for Ukrainian content ({exc})"]
    if not resolved:
        return ["owned paths cannot be checked for Ukrainian content (no tree to read)"]
    reasons = [reason for tree in resolved for path in owned for reason in owned_scope_reasons(path, tree)]
    return list(dict.fromkeys(reasons))


def format_refusal(agent: str, reasons: Iterable[Any]) -> str:
    joined = "; ".join(str(reason) for reason in reasons)
    return (
        f"ROUTING REFUSED: {_POLICY}: {POLICY_LINE} {agent} seats take workspace-write implementation of "
        f"allowlisted UI and backend paths holding plain UTF-8 text without Cyrillic only "
        f"(KIMI_OWNED_ROOTS in scripts/agent_runtime/kimi_admission.py). "
        f"Refused: {joined}. Alternative seats: {_alternative_seats()}."
    )


def _alternative_seats() -> str:
    """Prefer catalog alternatives; unavailable catalog data must not interrupt a typed refusal."""
    try:
        from scripts.review.model_catalog import load_model_catalog

        catalog = load_model_catalog()
        models = catalog["models"]
        reviewers = sorted(
            {
                entry["route"]
                for entry in catalog["review_candidates"].values()
                if models[entry["model_id"]]["family"] in {"anthropic", "openai"}
                and catalog["review_scheduler"]["endpoints"].get(entry["route"], {}).get("formal_review_eligible")
            }
        )
        consults = sorted(
            {
                seat
                for seat, entry in catalog["orchestrator_seats"].items()
                if models.get(entry["model_id"], {}).get("family") in {"anthropic", "openai", "xai"}
            }
        )
    except Exception:  # Like is_kimi_model, refusal remains available without the catalog.
        reviewers, consults = ["claude", "codex"], ["claude", "codex", "grok"]
    return (
        f"reviews → {', '.join(reviewers)} (per the reviewer resolver); "
        f"consults and discussions → {', '.join(consults[:-1])}, or {consults[-1]}; "
        "claude, codex, or agy for Ukrainian-language content"
    )
