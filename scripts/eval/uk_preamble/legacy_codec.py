"""Frozen legacy codec for resume of historical evaluation manifests and adjudications.

Preserves delegate's historical argument defaults, fingerprinting, path strings
and prompt composition for legacy evidence verification. Never use this module
to create or launch legacy tasks. It contains no launcher or dispatch
implementation. Defaults and prompt strings are evidence
format bytes: changing them invalidates historical hashes. The sparse reader is
restricted to the no-owned-path evaluation frame.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from collections.abc import Callable, Collection, Sequence
from pathlib import Path
from typing import Any

from scripts.common.repo_root import main_checkout_root as _main_checkout_root
from scripts.common.repo_root import project_interpreter
from scripts.lib import rules_core
from scripts.storage.topology import STORE_FILES

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GIT_TIMEOUT_S = 30.0

DISPATCH_ARGS_HASH_EXCLUDED_FIELDS = {
    "run_nonce": "unique per attempt; only used for stale cross-host split-brain detection (#7168)",
    "force_new": "a retry/idempotency knob for reusing an existing --task-id, not part of what the seat is asked",
    "initiator": "orchestrator attribution metadata, auto-detected when omitted",
}

_DISPATCH_ARGS_HASH_ARGPARSE_KEYS = frozenset({"command", "func"})


def dispatch_args_sha256(args: argparse.Namespace) -> str:
    """sha256 of the canonical JSON of every parsed ``dispatch`` argument that binds the record.

    Additive to ``prompt_sha256``/``effective_prompt_sha256`` (which prove the prompt): this proves the
    *arguments* that produced the dispatch, so a record cannot pass a check that compares only a named
    subset of fields while carrying an unchecked extra flag (e.g. a caller-supplied --output-schema).
    Canonical means ``sort_keys=True`` and no separator whitespace, so the same arguments always hash the
    same regardless of argv order.
    """
    payload = {
        key: value
        for key, value in vars(args).items()
        if key not in DISPATCH_ARGS_HASH_EXCLUDED_FIELDS
        and key not in _DISPATCH_ARGS_HASH_ARGPARSE_KEYS
        and not (key == "review_mode" and value == "cross_family")
        and not (key == "authoring_review_plan" and value == "cross_family")
        and not (key == "claude_account" and value in (None, "a"))
        and not (key == "verify_command" and value is None)
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_WRITE_CAPABLE_MODES = frozenset({"workspace-write", "danger"})

_GIT_ENV_DENYLIST = {
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


def _sanitized_git_env() -> dict[str, str]:
    """Select the explicit repository and refuse interactive credential prompts."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _GIT_ENV_DENYLIST and not key.startswith("PRE_COMMIT")
    }
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


_DISPATCH_SPARSE_EXCLUDE_DEFAULT = frozenset(
    {
        "curriculum",
        "wiki",
        "data/projects",
        "data/lexicon",
        "registry/projects",
        "data/datasets",
        "data/processed",
        "registry/lexicon/source-inventory",
        "registry/lexicon/source-inventory-review-decisions",
        "site/src/content",
        "site/src/data",
    }
)

_DISPATCH_SPARSE_ANCHORS: dict[str, tuple[str, ...]] = {
    "curriculum": (
        "curriculum/l2-uk-direct/a1",
        "curriculum/l2-uk-en/lesson-plans",
        "curriculum/l2-uk-en/plans/a1",
    ),
    "registry/lexicon/source-inventory": ("registry/lexicon/source-inventory/grade-01",),
    "registry/projects": ("registry/projects/open_model_data/integrations",),
}


def _normalize_sparse_include(raw: Sequence[str] | None) -> tuple[str, ...]:
    """Normalize --sparse-include values to unique default-excluded trees.

    Fail closed: explicit values must be names in the default exclusion set
    (``_DISPATCH_SPARSE_EXCLUDE_DEFAULT``). Other nested paths and unknown
    names raise :class:`ValueError`.
    """
    if not raw:
        return ()
    seen: set[str] = set()
    ordered: list[str] = []
    allowed = ", ".join(sorted(_DISPATCH_SPARSE_EXCLUDE_DEFAULT))
    for item in raw:
        name = str(item).strip().strip("/")
        if not name or name in {".", ".."} or name.startswith("../") or "/../" in f"/{name}/":
            raise ValueError(
                f"--sparse-include {item!r} is empty or invalid; "
                "pass a default-excluded tree such as 'curriculum', 'wiki', 'data/projects', "
                "or 'registry/projects'"
            )
        if name not in _DISPATCH_SPARSE_EXCLUDE_DEFAULT:
            if "/" in name:
                raise ValueError(f"--sparse-include {item!r} must name a default-excluded tree. Allowed: {allowed}")
            raise ValueError(f"--sparse-include {name!r} is not a default-excluded tree; allowed: {allowed}")
        if name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return tuple(ordered)


def _infer_sparse_include_from_text(text: str | None) -> tuple[str, ...]:
    """Detect default-excluded path prefixes referenced in a prompt."""
    if not text:
        return ()
    found: list[str] = []
    for name in sorted(_DISPATCH_SPARSE_EXCLUDE_DEFAULT, key=len, reverse=True):
        # Path-like reference: curriculum/…, data/projects/… — not bare words.
        if re.search(rf"(?<![\w.-]){re.escape(name)}/", text):
            found.append(name)
    return tuple(found)


def _list_worktree_dirs(worktree_path: Path, *tree_path: str, at_ref: str = "HEAD") -> list[str]:
    """Return directory names from ``git ls-tree -d`` at ``at_ref``.

    With no ``tree_path``, lists top-level directories. ``data/`` lists the
    children (``data/projects``, …) so new ``data/*`` dirs are included
    automatically and only the named exclusions drop out.
    """
    label = "/".join(tree_path) if tree_path else "top-level"
    try:
        proc = subprocess.run(
            ["git", "ls-tree", "-d", "--name-only", at_ref, *tree_path],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"could not list {label} dirs in {worktree_path}: timed out after {DEFAULT_GIT_TIMEOUT_S}s"
        ) from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "git ls-tree failed").strip()
        raise RuntimeError(f"could not list {label} dirs in {worktree_path}: {detail}")
    return [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]


def _list_worktree_top_dirs(worktree_path: Path, *, at_ref: str = "HEAD") -> list[str]:
    """Return top-level directory names at ``at_ref`` inside a worktree."""
    return _list_worktree_dirs(worktree_path, at_ref=at_ref)


def _dispatch_sparse_cone_dirs(
    list_dirs: Callable[[str], Sequence[str]],
    exclude: Collection[str],
) -> tuple[list[str], list[str]]:
    """Build a cone include list that drops excluded dirs at directory level.

    ``list_dirs("")`` returns the top-level directories and
    ``list_dirs("site/src")`` the repo-relative child directories of
    ``site/src``. A nested exclusion (``data/projects``,
    ``site/src/data``) is expressed by listing the sibling directories at
    every level down to it instead of their parent. Cone mode then keeps
    files directly in each parent and preserves the other sibling trees.
    A parent whose every child directory is excluded keeps its own files
    only when an anchor sits below it, since cone mode has no file entries.
    """
    exclude_set = {name.strip("/") for name in exclude}
    cone: list[str] = []
    excluded: list[str] = []

    def walk(parent: str) -> None:
        for child in list_dirs(parent):
            if parent and not child.startswith(parent + "/"):
                # Not a child of ``parent``: descending again would never end.
                continue
            if child in exclude_set:
                excluded.append(child)
            elif any(name.startswith(child + "/") for name in exclude_set):
                cone_mark, excluded_mark = len(cone), len(excluded)
                walk(child)
                if len(excluded) == excluded_mark:
                    # Nothing beneath exists at this ref: keep the whole tree,
                    # including the files directly in it.
                    del cone[cone_mark:]
                    cone.append(child)
            else:
                cone.append(child)

    walk("")
    return cone, sorted(excluded)


def _dispatch_sparse_profile(
    list_dirs: Callable[[str], Sequence[str]],
    sparse_include: Sequence[str] = (),
) -> tuple[list[str], list[str]]:
    """Return ``(cone_dirs, excluded_trees)`` for the default dispatch profile.

    ``sparse_include`` names default-excluded trees to keep. Anchors of a
    tree that stays excluded join the cone when they exist at HEAD.
    """
    includes = _normalize_sparse_include(sparse_include)
    exclude = set(_DISPATCH_SPARSE_EXCLUDE_DEFAULT) - set(includes)
    included, excluded = _dispatch_sparse_cone_dirs(list_dirs, exclude)
    for tree in excluded:
        for anchor in _DISPATCH_SPARSE_ANCHORS.get(tree, ()):
            parent = anchor.rpartition("/")[0]
            if anchor in list_dirs(parent):
                included.append(anchor)
    return included, excluded


def _worktree_dir_lister(worktree_path: Path) -> Callable[[str], list[str]]:
    """List directories at HEAD in ``worktree_path`` for the sparse profile."""

    def list_dirs(parent: str) -> list[str]:
        if not parent:
            return _list_worktree_top_dirs(worktree_path)
        return _list_worktree_dirs(worktree_path, parent + "/")

    return list_dirs


def _resolve_primary_root_for_worktree(cwd_or_worktree: Path) -> Path:
    """Resolve the primary checkout root for a worktree or arbitrary cwd."""
    primary_root = _main_checkout_root(cwd_or_worktree)
    if primary_root == cwd_or_worktree and cwd_or_worktree != _REPO_ROOT:
        primary_root = _main_checkout_root(_REPO_ROOT)
    return primary_root


def _primary_database_path(primary_root: Path, name: str) -> Path:
    """Reproduce legacy evidence path bytes without accessing a live store."""
    store = "sources" if name == STORE_FILES["sources"][0] else "vesum"
    filename, override_key = STORE_FILES[store]
    if store == "sources":
        override = os.environ.get(override_key)
        if override:
            path = Path(override).expanduser()
            return path.resolve() if path.is_absolute() else (primary_root / path).resolve()
    return (primary_root / "data" / filename).resolve()


def _primary_database_connect_code(target: Path) -> str:
    """Return Python connect code opening target read-only via RFC file URI (#9122)."""
    uri = f"{target.resolve().as_uri()}?mode=ro"
    return f"sqlite3.connect({uri!r}, uri=True)"


def _augment_prompt_with_worktree(
    prompt: str,
    worktree_path: Path | None,
    *,
    mode: str = "read-only",
    sparse_telemetry: dict[str, Any] | None = None,
    delegate_commits: bool = False,
) -> str:
    """Inject worktree context into the delegated prompt when relevant.

    ``delegate_commits`` (Kimi seats) replaces the commit-and-push closeout:
    the worker leaves its changes in the tree and delegate commits the owned
    paths after checking that the diff adds no Cyrillic text.
    """
    if worktree_path is None:
        return prompt
    sparse_note = ""
    if sparse_telemetry and not sparse_telemetry.get("full_checkout"):
        excluded = sparse_telemetry.get("excluded") or []
        if excluded:
            add_commands = " ".join(f"`git sparse-checkout add {name}`" for name in excluded)
            sparse_note = (
                "Sparse-checkout is active: these trees are NOT present: "
                + ", ".join(str(p) for p in excluded)
                + ". To materialize one inside this worktree, run "
                + add_commands
                + " (for example `git sparse-checkout add data/projects`). "
                + "A test that fails because a file under one of these trees is missing needs that "
                + "command, not a code change. Do not invent content for missing paths.\n"
            )
    delivery_note = ""
    if mode in _WRITE_CAPABLE_MODES and delegate_commits:
        delivery_note = (
            "\n[write-mode closeout]\n"
            "Do not commit or push. Leave your changes in this worktree, inside the owned paths.\n"
            "After you exit, delegate checks the diff and commits and pushes the owned paths; "
            "a diff that adds any Cyrillic character, or content that is not text, is refused and "
            "nothing is committed. This worktree's git hooks refuse the same commits, and it has no push access.\n"
            "Delete scratch files before you finish.\n"
        )
    elif mode in _WRITE_CAPABLE_MODES:
        delivery_note = (
            "\n[write-mode closeout]\n"
            "After each coherent completed step, run the applicable validation. Once it passes, "
            "commit and push that step using the instructions below before starting the next step; "
            "do not wait until exit to publish completed steps.\n"
            "Leave unfinished steps uncommitted. If a push is refused, retain your work, "
            "stop and report the actual blocker. Keep the final exit checks below.\n"
            "Commit your work (use the literal trailer in `$LU_X_AGENT_TRAILER`).\n"
            "`git push -u origin HEAD`\n"
            "The push runs a pre-push gate on that exact commit (the pre-commit pre-push stage with the OPSEC "
            "and internal-ID scans; it runs no tests, CI runs the full suite); a refusal names the failing hooks, "
            "and `validation_incomplete` means it did not finish: stop and report, never `--no-verify`.\n"
            "Do not merge `origin/main` into your branch unless `git merge-tree` against a freshly fetched "
            "main reports a conflict, or the driver orders it.\n"
            "Leave `git status --porcelain` empty (commit or delete scratch files).\n"
            "For scratch git repositories and probes, use `$TMPDIR`, the managed lease, "
            "never a literal system temp path.\n"
            "Keep durable task artifacts in `$LU_TASK_EVIDENCE_DIR`; task cleanup preserves that directory.\n"
            "Do not open or merge PRs unless the brief says so; "
            "report the pushed head SHA and clean status.\n"
            "\n[optional delivery signal]\n"
            "If you finish with zero commits (a verified no-op), you MAY end your final response "
            "with one machine-readable line as positive proof: "
            '`DELIVERABLE: {"outcome":"no_change","reason":"why no changes are required"}`. '
            "This line is optional — its absence never fails the dispatch.\n"
        )
    # #9057: every worktree dispatch carries one test-scope rule. Write modes
    # run only the tests for files they changed, including importers of a
    # changed shared helper; review modes cite CI. The PR's own CI, and the
    # merge queue on the merged tree, are the full-suite proof — a dispatch
    # `gh workflow run` does not satisfy the PR's required check.
    if mode in _WRITE_CAPABLE_MODES:
        test_scope = (
            "\n[test scope]\n"
            "Run only the tests that cover the files you changed, including tests of "
            "code that imports a changed shared helper, and name those test files explicitly.\n"
            "Never collect the whole `tests/` tree (`pytest tests`, `pytest tests -k …`); "
            "never `-n auto` or `-n` above 2.\n"
            "A run that prints `TEST SLOTS: waiting … queue position` is queued for host test slots, "
            "not hung; let it wait.\n"
            "Run tests in the foreground and wait for them "
            "(never end the turn while a test runs in the background).\n"
            "The full suite runs in the PR's CI (and again in the merge queue on the merged "
            "tree) — that is the proof; do not trigger extra full runs. "
            "Use `gh workflow run ci.yml --ref <branch>` only when the brief explicitly asks "
            "for it (a branch with no PR yet, a baseline capture, or diagnosis).\n"
        )
    else:
        test_scope = (
            "\n[test scope]\n"
            "Do not re-run test suites that the PR's CI runs. Review the diff.\n"
            "Run at most the specific tests that reproduce a finding you are checking.\n"
            "Cite CI run ids for suite results.\n"
        )
    db_note = ""
    if worktree_path is not None:
        primary_root = _resolve_primary_root_for_worktree(worktree_path)
        primary_sources = _primary_database_path(primary_root, "sources.db")
        primary_vesum = _primary_database_path(primary_root, "vesum.db")
        sources_code = _primary_database_connect_code(primary_sources)
        vesum_code = _primary_database_connect_code(primary_vesum)
        db_note = (
            "\n[database access in worktrees]\n"
            "Primary databases (data/sources.db, data/vesum.db) reside in the primary checkout, "
            "not in this worktree. Prefer MCP tools (`sources` server: `verify_words`, `search_text`, etc.) "
            "which resolve databases automatically. If running ad-hoc Python/SQLite queries, NEVER use a relative "
            "path like `data/sources.db` or `data/vesum.db` (which creates an empty file in the worktree and triggers "
            "read-only checkout mutation failure); connect to the primary database using its absolute path read-only: "
            f"`{sources_code}` or `{vesum_code}`.\n"
        )
    # #8775: the path is data. ASCII JSON quoting keeps it one quoted line even
    # if an unvalidated path ever reaches this block.
    return (
        "[delegate worktree]\n"
        "Run all file edits, tests, and git commands inside this worktree "
        f"(JSON-quoted path): {json.dumps(str(worktree_path))}\n"
        "Do not switch branches in the main checkout.\n"
        # #5803 follow-up: remove the workflow reason to visit the primary.
        # A linked worktree shares the canonical `origin` remote, so fresh
        # main is always one fetch away from INSIDE the worktree.
        "If you need a fresh base, run `git fetch origin main` INSIDE this worktree — "
        "`origin` here points at the canonical GitHub remote and fetch works from any "
        "linked worktree. NEVER use the primary checkout as a source of freshness "
        "(no `git -C <primary> pull/fetch/checkout`); it is the human's interactive home.\n"
        "\n[shared project interpreter]\n"
        "Never create, copy, symlink, activate, or use a `.venv` inside this worktree. "
        f"Run every project Python command with `{project_interpreter()}` "
        "(the absolute primary interpreter), never `python`, `.venv/bin/python`, or "
        "`python -m venv .venv`. Do not change `PYTHONPATH` merely because the worker "
        "cwd is a worktree.\n"
        f"{sparse_note}{test_scope}{delivery_note}{db_note}\n"
        "[held work]\n"
        "Keep patches, handoffs and diagnostics needed after exit in `$LU_TASK_EVIDENCE_DIR`, "
        "this task's `evidence/` directory outside the worktree, and cite each file in your final response. "
        "Task cleanup preserves that directory with a retrieval receipt before removing the runtime lease. "
        "Runtime scratch elsewhere is deleted at exit. "
        "Cite regular files, not directories or symlinks; automatic preservation has a 256 MiB cap.\n\n"
        f"{prompt}"
    )


def _evidence_prompt_block() -> str:
    """Name the supported evidence directory whose contents task cleanup preserves (#11342).

    The block is deliberately independent of the task's runtime lease: the
    worker reads the concrete ``evidence/`` path from ``$LU_TASK_EVIDENCE_DIR``
    (see :func:`_build_worker_env`) and the task record keeps it in
    ``evidence_dir``. Keeping the path out of the prompt means the prompt text,
    its SHA-256 and the evaluation harness's paired frame stay identical across
    tasks, so exact-prompt verification still holds.
    """
    return (
        "\n[evidence]\n"
        "Durable evidence (reports, archives, logs, screenshots) belongs in "
        "`$LU_TASK_EVIDENCE_DIR`, this task's `evidence/` directory.\n"
        "Task cleanup copies that directory to `batch_state/preserved/<task>/` with a retrieval "
        "receipt before it removes the runtime lease. Files left elsewhere in the worktree or "
        "runtime temp root are not preserved and can be deleted when the task ends.\n"
        "Put every artifact a later reader needs there and cite it from your result.\n"
    )


def _compose_dispatch_prompt(
    base: str,
    *,
    worktree_path: Path | None,
    mode: str,
    sparse_telemetry: dict[str, Any] | None,
    delegate_commits: bool,
    research_block: str,
    advisory_block: str,
    advisory_block_kind: str | None,
    rules_seat: str | None,
    blocks: list[str] | None = None,
    agent: str | None = None,
    review_route: bool = False,
    evidence_dir: Path | str | None = None,
) -> str:
    """The prompt a worker receives: ``base`` (the brief and any lifecycle block) inside the dispatcher blocks.

    In prompt order: the rules core, the worktree block, ``base``, the evidence
    block, the research pointers and the advisory block. ``blocks``, when given,
    gets the kinds added, in prompt order. The bounded worker rebuilds its
    expected prompt with this function (#9275), so the two cannot drift apart.

    ``evidence_dir`` is the *presence* signal for the supported evidence
    directory (``None`` means the dispatch has none): its concrete, task-specific
    lease path is never interpolated, so every task's prompt and SHA-256 stay
    comparable. The worker reads the path from ``$LU_TASK_EVIDENCE_DIR`` and the
    task record keeps it in ``evidence_dir``.
    """
    prompt = _augment_prompt_with_worktree(
        base,
        worktree_path,
        mode=mode,
        sparse_telemetry=sparse_telemetry,
        delegate_commits=delegate_commits,
    )
    if worktree_path is not None and blocks is not None:
        blocks.insert(0, "worktree")
    if evidence_dir is not None:
        prompt = prompt + _evidence_prompt_block()
        if blocks is not None:
            blocks.append("evidence")
    if research_block and blocks is not None:
        blocks.append("research")
    prompt = prompt + research_block
    if advisory_block_kind is not None:
        if blocks is not None:
            blocks.append(advisory_block_kind)
        prompt = prompt + advisory_block
    # Every worker and review seat starts with the rules core, read from this checkout.
    cored_prompt = rules_core.with_core(prompt, rules_seat)
    if cored_prompt != prompt:
        if blocks is not None:
            blocks.insert(0, "rules_core")
        prompt = cored_prompt
    if agent == "agy" and mode in ("workspace-write", "danger") and not review_route:
        from scripts.agent_runtime.adapters.agy import _WRITE_MODE_PROMPT_CONTRACT

        prompt += _WRITE_MODE_PROMPT_CONTRACT
        if blocks is not None:
            blocks.append("agy_write_contract")
    return prompt


def build_parser() -> argparse.ArgumentParser:
    """Parse only the frozen dispatch evidence format; never execute it."""
    parser = argparse.ArgumentParser()
    dispatch = parser.add_subparsers(dest="command", required=True).add_parser("dispatch")
    dispatch.add_argument(
        "--agent",
        dest="agent",
        default=None,
        required=True,
        choices=[
            "codex",
            "gemini",
            "claude",
            "grok",
            "grok-build",
            "grok-hermes",
            "kimi",
            "deepseek",
            "agy",
            "cursor",
            "glm",
            "muse",
        ],
    )
    dispatch.add_argument("--harness", dest="harness", default=None, choices=["kimicc", "native"])
    dispatch.add_argument("--task-id", dest="task_id", default=None, required=True)
    dispatch.add_argument("--force-new", dest="force_new", default=False, action="store_true")
    dispatch.add_argument("--force-admission", dest="force_admission", default=None)
    dispatch.add_argument("--initiator", dest="initiator", default=None)
    dispatch.add_argument("--run-nonce", dest="run_nonce", default=None)
    dispatch.add_argument("--prompt", dest="prompt", default=None)
    dispatch.add_argument("--prompt-file", dest="prompt_file", default=None)
    dispatch.add_argument("--allow-dor-warn", dest="allow_dor_warn", default=None)
    dispatch.add_argument("--lifecycle-file", dest="lifecycle_file", default=None)
    dispatch.add_argument(
        "--mode", dest="mode", default="read-only", choices=["read-only", "workspace-write", "danger"]
    )
    dispatch.add_argument("--model", dest="model", default=None)
    dispatch.add_argument("--claude-account", dest="claude_account", default=None)
    dispatch.add_argument("--provider", dest="provider", default=None, choices=["openrouter"])
    dispatch.add_argument("--effort", dest="effort", default=None, choices=["low", "medium", "high", "xhigh", "max"])
    dispatch.add_argument("--repo", dest="repo", default=None)
    dispatch.add_argument("--cwd", dest="cwd", default=None)
    dispatch.add_argument("--worktree", dest="worktree", default=None, nargs="?", const="auto")
    dispatch.add_argument("--pr", dest="pr", default=None, type=int)
    dispatch.add_argument("--pinned-head", dest="pinned_head", default=None)
    dispatch.add_argument("--branch", dest="branch", default=None)
    dispatch.add_argument("--keep-worktree", dest="keep_worktree", default=False, action="store_true")
    dispatch.add_argument("--finalize-open-pr", dest="finalize_open_pr", default=False, action="store_true")
    dispatch.add_argument("--require-review-verdict", dest="require_review_verdict", default=False, action="store_true")
    dispatch.add_argument(
        "--review-profile", dest="review_profile", default=None, choices=["code", "infra", "ukrainian"]
    )
    dispatch.add_argument("--review-author-model", dest="review_author_model", default=None)
    dispatch.add_argument(
        "--review-risk", dest="review_risk", default=None, choices=["low", "medium", "high", "critical"]
    )
    dispatch.add_argument(
        "--authoring-review-risk",
        dest="authoring_review_risk",
        default=None,
        choices=["low", "medium", "high", "critical"],
    )
    dispatch.add_argument("--subject-seat", dest="subject_seat", default=None, action="append")
    dispatch.add_argument("--subject-family", dest="subject_family", default=None, action="append")
    dispatch.add_argument("--review-attempt", dest="review_attempt", default=None)
    dispatch.add_argument("--review-access", dest="review_access", default="full", choices=["full", "isolated"])
    dispatch.add_argument("--review-id", dest="review_id", default=None)
    dispatch.add_argument("--attempt-id", dest="attempt_id", default=None)
    dispatch.add_argument("--full-checkout", dest="full_checkout", default=False, action="store_true")
    dispatch.add_argument("--sparse-include", dest="sparse_include", default=None, action="append")
    dispatch.add_argument("--base", dest="base", default=None)
    dispatch.add_argument("--allow-merge", dest="allow_merge", default=False, action="store_true")
    dispatch.add_argument("--language-lane", dest="language_lane", default=False, action="store_true")
    dispatch.add_argument("--check-budget", dest="check_budget", default=False, action="store_true")
    dispatch.add_argument("--force-agent", dest="force_agent", default=False, action="store_true")
    dispatch.add_argument("--dry-run", dest="dry_run", default=False, action="store_true")
    dispatch.add_argument("--hard-timeout", dest="hard_timeout", default=7200, type=int)
    dispatch.add_argument("--silence-timeout", dest="silence_timeout", default=3600, type=int)
    dispatch.add_argument("--initial-response-timeout", dest="initial_response_timeout", default=600, type=int)
    dispatch.add_argument("--max-budget-usd", dest="max_budget_usd", default=None, type=float)
    dispatch.add_argument("--output-schema", dest="output_schema", default=None)
    dispatch.add_argument("--research-role", dest="research_role", default=None)
    dispatch.add_argument("--research-task-family", dest="research_task_family", default=None)
    dispatch.add_argument("--research-track", dest="research_track", default=None)
    dispatch.add_argument("--research-owned-path", dest="research_owned_path", default=None, action="append")
    dispatch.add_argument("--rules-seat", dest="rules_seat", default=None, choices=["core", "content"])
    dispatch.add_argument("--owned-path", dest="owned_path", default=None, action="append")
    dispatch.add_argument("--advisory-task", dest="advisory_task", default=None)
    dispatch.add_argument("--advisory-role", dest="advisory_role", default=None, choices=["bounded_advisory_envelope"])
    dispatch.add_argument("--advisory-binding", dest="advisory_binding", default=None)
    dispatch.add_argument("--print-advisory-binding", dest="print_advisory_binding", default=False, action="store_true")
    dispatch.add_argument("--allow-path-overlap", dest="allow_path_overlap", default=None)
    dispatch.add_argument("--preflight-triage", dest="preflight_triage", default=False, action="store_true")
    dispatch.add_argument("--preflight-base", dest="preflight_base", default=None)
    dispatch.add_argument("--preflight-test-log", dest="preflight_test_log", default=None)
    dispatch.add_argument("--verify-command", dest="verify_command", default=None)
    dispatch.add_argument(
        "--review-mode", dest="review_mode", default=argparse.SUPPRESS, choices=["cross_family", "red_team"]
    )
    dispatch.add_argument(
        "--authoring-review-plan",
        dest="authoring_review_plan",
        default=argparse.SUPPRESS,
        choices=["cross_family", "red_team"],
    )
    return parser


def _infer_sparse_include(explicit, *, owned_paths=None, prompt_text=None):
    """Frozen no-owned-path frame used by historical preamble evaluations."""
    if owned_paths:
        raise ValueError("legacy evidence codec does not support owned paths")
    return tuple(dict.fromkeys((*_normalize_sparse_include(explicit), *_infer_sparse_include_from_text(prompt_text))))
