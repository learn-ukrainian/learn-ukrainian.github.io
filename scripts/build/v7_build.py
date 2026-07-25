#!/usr/bin/env python3
"""CLI wrapper for the V7 linear module pipeline."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.agent_runtime.errors import AgentStalledError
from scripts.audit.llm_qg_store import (
    current_payload_for_module,
    llm_qg_file_is_current_for_module,
    prompt_hash_for_text,
    record_llm_qg,
)
from scripts.audit.wiki_completeness_gate import SEMINAR_LEVELS
from scripts.build import linear_pipeline, run_archive
from scripts.build.phases.implementation_map import (
    read_implementation_map,
    seed_implementation_map,
    write_implementation_map,
)
from scripts.common.thresholds import QG_DIMS, terminal_dims_for
from scripts.orchestration import reap_worktrees

DEFAULT_WRITER_TIMEOUT_S = 1800
FETCH_TIMEOUT_S = 30
WORKTREE_AUTO = "auto"
WRITER_ALIASES = {
    "claude": "claude-tools",
    "gemini": "gemini-tools",
    "codex": "codex-tools",
    "grok": "grok-tools",
    "cursor": "cursor-tools",
    "deepseek": "deepseek-tools",
    "qwen": "qwen-tools",
    "agy": "agy-tools",
}
WRITER_CHOICES = (*linear_pipeline.WRITER_CHOICES, *WRITER_ALIASES)
LLM_QG_DIM_MAX_ATTEMPTS = 2


@dataclass(slots=True)
class LastEventTracker:
    event_type: str | None = None
    event_ts: str | None = None

    def emit(self, event: str, **fields: Any) -> None:
        self.event_type = event
        self.event_ts = datetime.now(UTC).isoformat()
        emit_event(event, **fields)


@dataclass(slots=True)
class BuildWorktree:
    path: Path
    branch: str
    base_sha: str
    repo_root: Path
    run_id: str


class WorktreeSetupError(RuntimeError):
    exit_code = 1


class WorktreeRepoError(WorktreeSetupError):
    exit_code = 2


class WorktreePathExists(WorktreeSetupError):
    exit_code = 3


class WorktreeAddFailed(WorktreeSetupError):
    exit_code = 4


class PrimaryCheckoutSafetyError(RuntimeError):
    exit_code = 5


class PrimaryCheckoutBuildError(PrimaryCheckoutSafetyError):
    pass


class PrimaryCheckoutPersistError(PrimaryCheckoutSafetyError):
    pass


_MODULE_ARTIFACT_NAMES = (
    "writer_prompt.md",
    "writer_output.raw.md",
    "hermes.write.jsonl",
    "writer_tool_calls.json",
    "knowledge_packet.md",
    "wiki_manifest.json",
    "implementation_map.json",
    "module.md",
    "activities.yaml",
    "vocabulary.yaml",
    "resources.yaml",
    "wiki_completeness_gate.json",
    "stress_annotation.json",
    "ulp_fidelity_gate.json",
    "python_qg.json",
    "wiki_coverage_gate.json",
    "wiki_coverage_review.json",
    "python_qg_correction_loop.json",
    "llm_qg_correction_loop.json",
    "llm_qg.json",
)
_MODULE_ARTIFACT_GLOBS = (
    "python_qg_correction_r*.json",
    "wiki_coverage_correction_r*.json",
    "llm-qg-*-prompt.md",
    "llm-qg-*-response.raw.md",
    "wiki-coverage-review-prompt.md",
    "wiki-coverage-review-response.raw.md",
)


def emit_event(event: str, **fields: Any) -> None:
    linear_pipeline.emit_event(event, **fields)


def _positive_int(raw: str) -> int:
    value = int(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def _default_module_dir(level: str, slug: str) -> Path:
    return PROJECT_ROOT / "curriculum" / "l2-uk-en" / level.lower() / slug


def _resolve_output_dir(raw: str | None, level: str, slug: str) -> Path:
    if raw is None:
        return _default_module_dir(level, slug)
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _resolve_project_path(raw: str | None) -> Path | None:
    if raw is None:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _run_git(
    args: list[str],
    *,
    cwd: Path,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env=reap_worktrees.sanitized_git_env(),
    )


def _format_process_failure(proc: subprocess.CompletedProcess[str]) -> str:
    detail = (proc.stderr or proc.stdout or "").strip()
    if detail:
        return detail.splitlines()[-1]
    return f"exit {proc.returncode}"


def _git_top_level(path: Path) -> Path:
    try:
        proc = _run_git(["rev-parse", "--show-toplevel"], cwd=path)
    except (OSError, subprocess.SubprocessError) as exc:
        raise WorktreeRepoError(f"cannot resolve git top-level for {path}: {exc}") from exc
    if proc.returncode != 0:
        raise WorktreeRepoError(
            f"cannot resolve git top-level for {path}: {_format_process_failure(proc)}"
        )
    return Path((proc.stdout or "").strip()).resolve()


def _repo_root_from_cwd() -> Path:
    try:
        proc = _run_git(["rev-parse", "--show-toplevel"], cwd=Path.cwd())
    except (OSError, subprocess.SubprocessError) as exc:
        raise WorktreeRepoError(
            f"cwd must be inside the repository to use --worktree: {exc}"
        ) from exc
    if proc.returncode != 0:
        detail = _format_process_failure(proc)
        raise WorktreeRepoError(
            f"cwd must be inside the repository to use --worktree: {detail}"
        )
    repo_root = Path((proc.stdout or "").strip()).resolve()
    if repo_root != PROJECT_ROOT:
        raise WorktreeRepoError(
            "cwd must be inside this repository to use --worktree "
            f"(got {repo_root}, expected {PROJECT_ROOT})"
        )
    return repo_root


def _main_checkout_root(repo_root: Path) -> Path:
    proc = _run_git(["rev-parse", "--git-common-dir"], cwd=repo_root)
    if proc.returncode != 0:
        return repo_root
    common_dir = Path((proc.stdout or "").strip())
    if not common_dir.is_absolute():
        common_dir = repo_root / common_dir
    common_dir = common_dir.resolve()
    if common_dir.name == ".git":
        return common_dir.parent
    return repo_root


def _python_executable(repo_root: Path) -> Path:
    main_checkout = _main_checkout_root(repo_root)
    main_python = main_checkout / ".venv" / "bin" / "python"
    if main_python.exists():
        return main_python
    return repo_root / ".venv" / "bin" / "python"


def _safe_component(raw: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._/-]+", "-", raw).strip("./-")
    safe = re.sub(r"/{2,}", "/", safe)
    return safe


def _safe_path_component(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip("./-")


def _utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def _has_timestamp_suffix(raw: str) -> bool:
    return re.search(r"\d{8}-\d{6}$", raw) is not None


def _default_worktree_path(repo_root: Path, level: str, slug: str, timestamp: str) -> Path:
    safe_level = _safe_path_component(level) or "level"
    safe_slug = _safe_path_component(slug) or "module"
    return repo_root / ".worktrees" / "builds" / f"{safe_level}-{safe_slug}-{timestamp}"


def _derive_build_branch(
    *,
    level: str,
    slug: str,
    timestamp: str,
    path: Path,
    explicit_path: bool,
) -> str:
    safe_level = _safe_component(level) or "level"
    default_suffix = f"{_safe_component(slug) or 'module'}-{timestamp}"
    if explicit_path:
        path_suffix = _safe_component(path.name)
        if not path_suffix:
            suffix = default_suffix
        elif _has_timestamp_suffix(path_suffix):
            suffix = path_suffix
        else:
            suffix = f"{path_suffix}-{timestamp}"
    else:
        suffix = default_suffix
    return f"build/{safe_level}/{suffix}"


def _resolve_worktree_output_dir(
    raw: str | None,
    *,
    worktree_path: Path,
    level: str,
    slug: str,
) -> Path:
    if raw is None:
        return worktree_path / "curriculum" / "l2-uk-en" / level.lower() / slug
    path = Path(raw)
    if not path.is_absolute():
        path = worktree_path / path
    return path


def _worktree_mdx_path(
    raw_out: str | None,
    *,
    worktree_path: Path,
    module_dir: Path,
    level: str,
    slug: str,
) -> Path:
    if raw_out is None:
        return (
            worktree_path
            / "site"
            / "src"
            / "content"
            / "docs"
            / level.lower()
            / f"{slug}.mdx"
        )
    return module_dir / f"{slug}.mdx"


def _relative_to_worktree(worktree_path: Path, path: Path) -> str | None:
    resolved_worktree = worktree_path.resolve()
    resolved_path = path.resolve()
    try:
        return str(resolved_path.relative_to(resolved_worktree))
    except ValueError:
        return None


def _existing_module_artifacts(module_dir: Path) -> list[Path]:
    paths = [module_dir / name for name in _MODULE_ARTIFACT_NAMES]
    for pattern in _MODULE_ARTIFACT_GLOBS:
        paths.extend(sorted(module_dir.glob(pattern)))
    return [path for path in paths if path.exists()]


def _persist_artifact_paths(
    worktree: BuildWorktree,
    *,
    level: str,
    slug: str,
    module_dir: Path | None = None,
    mdx_path: Path | None = None,
) -> list[str]:
    level = level.lower()
    default_module_dir = (
        worktree.path / "curriculum" / "l2-uk-en" / level / slug
    )
    candidate_paths: list[Path] = []
    artifact_dirs = [default_module_dir]
    if module_dir is not None and module_dir != default_module_dir:
        artifact_dirs.append(module_dir)
    for artifact_dir in artifact_dirs:
        candidate_paths.extend(_existing_module_artifacts(artifact_dir))

    # Gemini-routed writes can place the Hermes trace at the repository root.
    candidate_paths.append(worktree.path / "hermes.write.jsonl")

    default_mdx = (
        worktree.path
        / "site"
        / "src"
        / "content"
        / "docs"
        / level
        / f"{slug}.mdx"
    )
    for path in (mdx_path, default_mdx):
        if path is not None and path.exists():
            candidate_paths.append(path)

    archive_dir = run_archive.archive_dir_for(
        worktree.path,
        level=level,
        slug=slug,
        run_id=worktree.run_id,
    )
    if archive_dir.exists():
        candidate_paths.extend(
            path for path in sorted(archive_dir.rglob("*")) if path.is_file()
        )

    rel_paths = []
    seen = set()
    for path in candidate_paths:
        if not path.exists():
            continue
        relative = _relative_to_worktree(worktree.path, path)
        if relative is None or relative in seen:
            continue
        rel_paths.append(relative)
        seen.add(relative)
    return rel_paths


def _ensure_persist_target_is_not_primary_checkout(worktree: BuildWorktree) -> None:
    target_top_level = _git_top_level(worktree.path)
    primary_checkout = reap_worktrees.primary_checkout_root(worktree.repo_root).resolve()
    if target_top_level == primary_checkout:
        raise PrimaryCheckoutPersistError(
            "Refusing to persist v7_build artifacts in the primary checkout; "
            "target git top-level is the primary checkout. Pass --worktree so "
            "artifacts are committed in an isolated worktree. See #2884."
        )


def _ensure_top_level_invocation_is_not_primary_checkout() -> None:
    cwd_top_level = _git_top_level(Path.cwd())
    primary_checkout = reap_worktrees.primary_checkout_root(cwd_top_level).resolve()
    if cwd_top_level == primary_checkout:
        raise PrimaryCheckoutBuildError(
            "Refusing to run v7_build in the primary checkout; pass --worktree "
            "(artifacts are committed and must land in an isolated worktree). "
            "See #2884."
        )


def _writer_model_effort(writer: str, effort_override: str | None) -> tuple[str, str]:
    defaults = linear_pipeline.WRITER_DEFAULTS.get(writer, {})
    model = defaults.get("model", "unknown")
    effort = effort_override or defaults.get("effort", "unknown")
    return model, effort


def _writer_prompt_template_sha(writer: str) -> str | None:
    return run_archive.file_sha256(linear_pipeline.writer_prompt_path(writer))


def _fetch_origin_main(repo_root: Path) -> bool:
    try:
        fetch = _run_git(["fetch", "origin"], cwd=repo_root, timeout=FETCH_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        print(
            f"Warning: git fetch origin timed out after {FETCH_TIMEOUT_S}s; "
            "falling back to local main.",
            file=sys.stderr,
        )
        return False
    except OSError as exc:
        print(
            f"Warning: git fetch origin failed ({exc}); falling back to local main.",
            file=sys.stderr,
        )
        return False
    if fetch.returncode != 0:
        detail = (fetch.stderr or fetch.stdout or "git fetch origin failed").strip()
        print(
            f"Warning: {detail}; falling back to local main.",
            file=sys.stderr,
        )
        return False
    verify = _run_git(["rev-parse", "--verify", "origin/main"], cwd=repo_root)
    if verify.returncode == 0:
        return True
    detail = (verify.stderr or verify.stdout or "origin/main is unavailable").strip()
    print(
        f"Warning: {detail}; falling back to local main.",
        file=sys.stderr,
    )
    return False


def _resolve_short_sha(repo_root: Path, ref: str) -> str:
    proc = _run_git(["rev-parse", "--short", ref], cwd=repo_root)
    if proc.returncode != 0:
        return ref
    return (proc.stdout or "").strip() or ref


def _provision_data_symlinks(worktree_path: Path, main_checkout_root: Path) -> None:
    for relative in (Path("data") / "sources.db", Path("data") / "vesum.db"):
        source = main_checkout_root / relative
        if not source.exists():
            print(
                f"Warning: skipping worktree data link for missing {source}",
                file=sys.stderr,
            )
            continue
        target = worktree_path / relative
        if target.exists() or target.is_symlink():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source.resolve())


def _setup_worktree(level: str, slug: str, raw_path: str | None) -> BuildWorktree:
    repo_root = _repo_root_from_cwd()
    timestamp = _utc_timestamp()
    explicit_path = raw_path not in (None, WORKTREE_AUTO)
    if explicit_path:
        path = Path(str(raw_path)).expanduser()
        if not path.is_absolute():
            path = repo_root / path
        worktree_path = path.resolve()
    else:
        worktree_path = _default_worktree_path(repo_root, level, slug, timestamp)
    branch = _derive_build_branch(
        level=level,
        slug=slug,
        timestamp=timestamp,
        path=worktree_path,
        explicit_path=explicit_path,
    )

    if worktree_path.exists():
        raise WorktreePathExists(
            f"Worktree path {worktree_path} exists; remove with "
            f"`git worktree remove {worktree_path}` or pass a different "
            "`--worktree PATH`."
        )

    base_ref = "origin/main" if _fetch_origin_main(repo_root) else "main"
    base_sha = _resolve_short_sha(repo_root, base_ref)
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    proc = _run_git(
        ["worktree", "add", "-b", branch, str(worktree_path), base_ref],
        cwd=repo_root,
    )
    if proc.returncode != 0:
        raise WorktreeAddFailed(
            (proc.stderr or proc.stdout or "git worktree add failed").strip()
        )

    _provision_data_symlinks(worktree_path, _main_checkout_root(repo_root))
    return BuildWorktree(
        path=worktree_path,
        branch=branch,
        base_sha=base_sha,
        repo_root=repo_root,
        run_id=timestamp,
    )


def _strip_worktree_args(argv: list[str]) -> list[str]:
    stripped: list[str] = []
    skip_next = False
    for idx, item in enumerate(argv):
        if skip_next:
            skip_next = False
            continue
        if item == "--worktree":
            if idx + 1 < len(argv) and not argv[idx + 1].startswith("-"):
                skip_next = True
            continue
        if item.startswith("--worktree="):
            continue
        stripped.append(item)
    return stripped


def _print_worktree_summary(
    worktree: BuildWorktree,
    *,
    level: str,
    slug: str,
    result: str,
    cleanup_result: reap_worktrees.ReapResult | None = None,
) -> None:
    print(f"BUILD_WORKTREE={worktree.path}")
    print(f"BUILD_BRANCH={worktree.branch}")
    print(f"BUILD_BASE={worktree.base_sha}")
    print(f"BUILD_RESULT={result}")
    if cleanup_result is not None:
        print(f"BUILD_WORKTREE_CLEANUP={cleanup_result.action}: {cleanup_result.reason}")
        if cleanup_result.error:
            print(f"BUILD_WORKTREE_CLEANUP_ERROR={cleanup_result.error}")
    if cleanup_result is not None and cleanup_result.action == "removed":
        print("Build worktree removed after artifact commit; branch retained for recovery.")
        return
    print("Next steps if successful:")
    print(f"  cd {worktree.path}")
    print("  git status")
    print(
        "  git add "
        f"curriculum/l2-uk-en/{level}/{slug}/*.yaml "
        f"site/src/content/docs/{level}/{slug}.mdx"
    )
    print('  git commit -m "feat(content): build module"')
    print(f"  git push -u origin {worktree.branch}")
    print('  gh pr create --title "feat(content): build module" --body "..."')
    print("Next steps if you want to discard:")
    print(f"  git worktree remove {worktree.path}")
    print(f"  git branch -D {worktree.branch}")


def _persist_build_artifacts(
    worktree: BuildWorktree,
    *,
    level: str,
    slug: str,
    result: str,
    module_dir: Path | None = None,
    mdx_path: Path | None = None,
) -> bool:
    """Commit scoped build artifacts to the worktree's build branch.

    Build artifacts (writer_prompt.md, writer_output.raw.md, hermes.write.jsonl,
    writer_tool_calls.json, knowledge_packet.md, implementation_map.json, the
    module.md + yaml siblings, and the assembled MDX if the build reached the
    publish phase) are LOAD-BEARING for diagnosis and for the self-correction
    loop. They MUST survive worktree removal — otherwise `git worktree remove`
    silently destroys forensic evidence (encoded as #M-10 in MEMORY.md after
    the 2026-05-19→20 incident where 7 worktrees were cleaned up and today's
    diagnostic artifacts were lost).

    Strategy: from inside the worktree's working tree, explicitly add the
    known artifact paths and then commit with ``--allow-empty``.
    The build branch is private to this worktree (created from origin/main in
    ``_setup_worktree`` with the unique timestamped suffix) so the commit
    cannot collide with another build of the same module. We deliberately
    do NOT push — keeps origin clean while preserving locally. Users who
    want shareable provenance for a specific build can push that branch
    manually.

    Ordinary git errors here are non-fatal: persistence is best-effort. The
    primary-checkout guard is fatal because committing build artifacts on main
    is worse than crashing this wrapper.
    """
    _ensure_persist_target_is_not_primary_checkout(worktree)
    artifact_paths = _persist_artifact_paths(
        worktree,
        level=level,
        slug=slug,
        module_dir=module_dir,
        mdx_path=mdx_path,
    )
    try:
        if artifact_paths:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(worktree.path),
                    "add",
                    "--force",
                    "--",
                    *artifact_paths,
                ],
                check=True,
                capture_output=True,
                text=True,
                env=reap_worktrees.sanitized_git_env(),
            )
        # --allow-empty so empty builds (rare, e.g. dry-run paths or
        # failed-before-writer setups) still leave a commit on the branch
        # marking that the worktree was used. Caller can prune later.
        subprocess.run(
            [
                "git",
                "-C",
                str(worktree.path),
                "commit",
                "--allow-empty",
                "--no-verify",
                "-m",
                f"build({level}/{slug}): artifacts ({result})",
            ],
            check=True,
            capture_output=True,
            text=True,
            env=reap_worktrees.sanitized_git_env(),
        )
        return True
    except (subprocess.CalledProcessError, OSError) as exc:
        stderr_tail = ""
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            stderr_tail = exc.stderr.strip().splitlines()[-1] if exc.stderr.strip() else ""
        print(
            f"v7_build: warning — failed to commit build artifacts on "
            f"branch {worktree.branch!r}: {exc}. {stderr_tail}".rstrip(),
            file=sys.stderr,
        )
        return False


def _run_in_worktree(args: argparse.Namespace, raw_argv: list[str]) -> int:
    level = args.level.lower()
    slug = args.slug
    writer = _normalize_writer(args.writer)
    try:
        worktree = _setup_worktree(level, slug, args.worktree)
    except WorktreeSetupError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code

    model, effort = _writer_model_effort(writer, args.effort)
    archive = run_archive.RunArchive.start(
        project_root=worktree.path,
        worktree_path=worktree.path,
        level=level,
        slug=slug,
        run_id=worktree.run_id,
        writer=writer,
        model=model,
        effort=effort,
        prompt_sha=_writer_prompt_template_sha(writer),
        base_ref=worktree.base_sha,
    )
    result = "failed"
    child_argv = _strip_worktree_args(raw_argv)
    command = [
        str(_python_executable(worktree.repo_root)),
        "scripts/build/v7_build.py",
        *child_argv,
    ]
    child_env = os.environ.copy()
    child_env.update(archive.env())
    try:
        proc = subprocess.run(command, cwd=worktree.path, check=False, env=child_env)
        exit_code = proc.returncode
        if exit_code == 0:
            result = "success"
    except OSError as exc:
        print(f"v7_build worktree child failed to start: {exc}", file=sys.stderr)
        exit_code = 1
    finally:
        module_dir = _resolve_worktree_output_dir(
            args.out,
            worktree_path=worktree.path,
            level=level,
            slug=slug,
        )
        mdx_path = _worktree_mdx_path(
            args.out,
            worktree_path=worktree.path,
            module_dir=module_dir,
            level=level,
            slug=slug,
        )
        archive.terminal(
            status="complete" if result == "success" else "failed",
            artifact_dir=module_dir,
            extra_paths=[mdx_path],
        )
        archive.write_commit_diff_summary(worktree_path=worktree.path)
        # Persist artifacts BEFORE printing the summary so the summary
        # can include the commit-status line. Even if the build crashed,
        # the writer_prompt + partial writer_output remain queryable via
        # the build branch SHA. Without this, `git worktree remove`
        # silently destroys forensic evidence.
        try:
            persisted = _persist_build_artifacts(
                worktree,
                level=level,
                slug=slug,
                result=result,
                module_dir=module_dir,
                mdx_path=mdx_path,
            )
        except PrimaryCheckoutSafetyError as exc:
            print(f"v7_build: error — {exc}", file=sys.stderr)
            return exc.exit_code
        cleanup_result = None
        if result == "success" and persisted and not args.keep_worktree:
            cleanup_result = reap_worktrees.reap_success_worktree(
                repo_root=worktree.repo_root,
                worktree_path=worktree.path,
                reason="build success after artifact commit",
                apply=True,
            )
        _print_worktree_summary(
            worktree,
            level=level,
            slug=slug,
            result=result,
            cleanup_result=cleanup_result,
        )
    return exit_code


def _phase_done(
    phase: str,
    started_at: float,
    *,
    level: str,
    slug: str,
    event_sink: Callable[..., None] = emit_event,
    archive: run_archive.RunArchive | None = None,
    artifact_dir: Path | None = None,
    **fields: Any,
) -> None:
    event_sink(
        "phase_done",
        level=level,
        slug=slug,
        phase=phase,
        duration_s=round(time.monotonic() - started_at, 3),
        **fields,
    )
    if archive is not None:
        extra_paths = []
        output = fields.get("output")
        if isinstance(output, Path):
            extra_paths.append(output)
        archive.phase_succeeded(
            phase,
            artifact_dir=artifact_dir,
            extra_paths=extra_paths,
            fields=fields,
        )


def _phase_started(archive: run_archive.RunArchive | None, phase: str) -> None:
    if archive is not None:
        archive.phase_started(phase)


def _archive_failure(
    archive: run_archive.RunArchive | None,
    *,
    phase: str,
    module_dir: Path | None,
    plan_path: Path | None,
    exc: Exception,
) -> None:
    if archive is None:
        return
    failed_mdx = archive.write_failed_mdx(
        module_dir=module_dir,
        plan_path=plan_path,
        failed_phase=phase,
    )
    archive.phase_failed(
        phase,
        artifact_dir=module_dir,
        failure_class=type(exc).__name__,
        reason=str(exc),
    )
    archive.terminal(
        status="failed",
        failed_phase=phase,
        failure_class=type(exc).__name__,
        artifact_dir=module_dir,
        extra_paths=[failed_mdx] if failed_mdx is not None else None,
    )


def _archive_failure_best_effort(
    archive: run_archive.RunArchive | None,
    *,
    phase: str,
    module_dir: Path | None,
    plan_path: Path | None,
    exc: Exception,
) -> None:
    """Preserve failure artifacts without masking the original terminal event."""
    try:
        _archive_failure(
            archive,
            phase=phase,
            module_dir=module_dir,
            plan_path=plan_path,
            exc=exc,
        )
    except Exception as archive_exc:
        print(
            f"v7_build warning: failed to archive failure for phase {phase}: {archive_exc}",
            file=sys.stderr,
            flush=True,
        )


def _writer_prompt(
    *,
    plan: Mapping[str, Any],
    plan_content: str,
    knowledge_packet: str,
    wiki_manifest: str | Mapping[str, Any],
    implementation_map: Mapping[str, Any],
    writer: str,
    plan_path: Path | None = None,
    use_generator: bool = False,
    obligation_checklist: Mapping[str, Any] | None = None,
) -> str:
    return linear_pipeline.render_writer_prompt(
        plan=plan,
        plan_path=plan_path,
        plan_content=plan_content,
        knowledge_packet=knowledge_packet,
        wiki_manifest=wiki_manifest,
        implementation_map=implementation_map,
        writer=writer,
        use_generator=use_generator,
        obligation_checklist=obligation_checklist,
    )


_PRE_EMIT_AUDIT_LINE_RE = re.compile(
    r"<(?P<tag>implementation_map_audit|bad_form_audit|activity_split_audit)\b"
    r"[^>]*>.*?</(?P=tag)>",
    re.DOTALL,
)


def _writer_preemit_audit_context(module_dir: Path) -> str:
    path = module_dir / "writer_output.raw.md"
    if not path.exists():
        return ""
    raw_output = path.read_text(encoding="utf-8")
    lines = [
        " ".join(match.group(0).split())
        for match in _PRE_EMIT_AUDIT_LINE_RE.finditer(raw_output)
    ]
    if not lines:
        return ""
    return "## writer_output.raw.md pre-emit audit lines\n\n" + "\n".join(lines)


def _generated_content(module_dir: Path) -> str:
    parts = []
    audit_context = _writer_preemit_audit_context(module_dir)
    if audit_context:
        parts.append(audit_context)
    for artifact in linear_pipeline.WRITER_ARTIFACTS:
        path = module_dir / artifact
        parts.append(f"## {artifact}\n\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(parts)


def _reviewer_for_writer(writer: str, reviewer_override: str | None = None) -> str:
    if reviewer_override:
        return _normalize_writer(reviewer_override)
    if writer == "claude-tools":
        return "gemini-tools"
    if writer == "grok-tools":
        return "claude-tools"
    if writer == "cursor-tools":
        return "cursor-tools"
    return "claude-tools"


def _reviewer_uses_gemini(reviewer: str) -> bool:
    defaults = linear_pipeline.REVIEWER_DEFAULTS.get(reviewer)
    model = str(defaults.get("model") if defaults else "")
    return "gemini" in reviewer.lower() or "gemini" in model.lower()


def _reviewer_model_differs(writer: str, reviewer: str) -> bool:
    writer_defaults = linear_pipeline.WRITER_DEFAULTS.get(writer)
    reviewer_defaults = linear_pipeline.REVIEWER_DEFAULTS.get(reviewer)
    if not writer_defaults or not reviewer_defaults:
        return True
    return writer_defaults["model"] != reviewer_defaults["model"]


def _llm_qg_reviewer_override_for_level(
    *,
    level: str,
    writer: str,
    reviewer_override: str | None,
) -> str | None:
    """Route seminar LLM-QG to Claude/GPT-family reviewers, never Gemini."""
    normalized = _normalize_writer(reviewer_override) if reviewer_override else None
    if level.lower() not in SEMINAR_LEVELS:
        return normalized
    if (
        normalized
        and not _reviewer_uses_gemini(normalized)
        and _reviewer_model_differs(writer, normalized)
    ):
        return normalized
    for candidate in ("claude-tools", "codex-tools"):
        if not _reviewer_uses_gemini(candidate) and _reviewer_model_differs(writer, candidate):
            return candidate
    raise linear_pipeline.LinearPipelineError(
        "No non-Gemini LLM-QG reviewer is available without same-model self-review"
    )


def _normalize_writer(writer: str) -> str:
    return WRITER_ALIASES.get(writer, writer)


_LLM_QG_GROUNDING_QUOTE_RE = re.compile(
    r'"([^"\n]{8,500})"|'
    r"«([^»\n]{8,500})»|"
    r"“([^”\n]{8,500})”|"
    r"`([^`\n]{8,500})`"
)


def _normalize_llm_qg_grounding_text(value: str) -> str:
    text = str(value)
    for marker in ("**", "__", "`", "*", "_"):
        text = text.replace(marker, "")
    return " ".join(text.split())


def _strip_llm_qg_quote_markup(value: str) -> str:
    text = _normalize_llm_qg_grounding_text(value).strip()
    text = text.strip('"“”«»`')
    return _normalize_llm_qg_grounding_text(text)


def _llm_qg_quotes_from_value(value: Any) -> list[str]:
    quotes: list[str] = []
    if isinstance(value, list):
        for item in value:
            quotes.extend(_llm_qg_quotes_from_value(item))
        return quotes
    if not isinstance(value, str):
        return quotes

    text = value.strip()
    if not text:
        return quotes
    for match in _LLM_QG_GROUNDING_QUOTE_RE.finditer(text):
        quote = next((group for group in match.groups() if group), "")
        quote = _strip_llm_qg_quote_markup(quote)
        if len(quote) >= 8:
            quotes.append(quote)
    if not quotes:
        quote = _strip_llm_qg_quote_markup(text)
        if len(quote) >= 8:
            quotes.append(quote)
    return quotes


def _llm_qg_grounding_quotes(entry: Mapping[str, Any]) -> list[str]:
    quotes: list[str] = []
    quotes.extend(_llm_qg_quotes_from_value(entry.get("evidence_quotes")))
    quotes.extend(_llm_qg_quotes_from_value(entry.get("evidence")))
    findings = entry.get("findings")
    if isinstance(findings, list):
        for finding in findings:
            if isinstance(finding, Mapping):
                quotes.extend(_llm_qg_quotes_from_value(finding.get("quote")))
    return list(dict.fromkeys(quotes))


def _validate_llm_qg_dim_grounding(
    entry: Mapping[str, Any],
    *,
    dim: str,
    generated_content: str,
    response_path: Path,
) -> None:
    content = _normalize_llm_qg_grounding_text(generated_content)
    ungrounded = [
        quote
        for quote in _llm_qg_grounding_quotes(entry)
        if quote and _normalize_llm_qg_grounding_text(quote) not in content
    ]
    if not ungrounded:
        return
    sample = ungrounded[0]
    raise linear_pipeline.LinearPipelineError(
        f"LLM QG {dim} ungrounded reviewer evidence in {response_path}: "
        f"{sample!r} is not present in generated module artifacts"
    )


def _llm_qg_retry_prompt(prompt: str, error: linear_pipeline.LinearPipelineError) -> str:
    return "\n\n".join(
        [
            "## Previous Response Rejected",
            "Your previous JSON response failed validation and was discarded.",
            f"Validation error: {error}",
            (
                "Return a fresh JSON object. Copy every `evidence_quotes`, "
                "`evidence`, and `findings[].quote` value exactly from Generated "
                "Content; do not repair grammar or reconstruct quotes from memory."
            ),
            prompt,
        ]
    )


def _llm_qg_balanced_json_objects(text: str) -> list[str]:
    objects: list[str] = []
    depth = 0
    start = -1
    in_string = False
    escape = False
    for idx, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            if depth == 0:
                start = idx
            depth += 1
            continue
        if ch == "}":
            if depth == 0:
                continue
            depth -= 1
            if depth == 0 and start >= 0:
                objects.append(text[start : idx + 1])
    return objects


def _parse_llm_qg_dim_response(response: str, *, dim: str, response_path: Path) -> dict[str, Any]:
    if not response.strip():
        raise linear_pipeline.LinearPipelineError(
            f"LLM QG {dim} empty backend response in {response_path}"
        )
    try:
        return linear_pipeline.parse_review_response(response, dim)
    except linear_pipeline.LinearPipelineError as exc:
        for candidate in reversed(_llm_qg_balanced_json_objects(response)):
            try:
                return linear_pipeline.parse_review_response(candidate, dim)
            except linear_pipeline.LinearPipelineError:
                continue
        raise linear_pipeline.LinearPipelineError(
            f"LLM QG {dim} malformed backend response in {response_path}: {exc}"
        ) from exc


def _resume_llm_qg_dim_if_current(
    *,
    dim: str,
    prompt: str,
    prompt_path: Path,
    response_path: Path,
    generated_content: str,
) -> dict[str, Any] | None:
    if not prompt_path.exists() or not response_path.exists():
        return None
    try:
        if prompt_path.read_text(encoding="utf-8") != prompt:
            return None
        response = response_path.read_text(encoding="utf-8")
        parsed = _parse_llm_qg_dim_response(response, dim=dim, response_path=response_path)
        _validate_llm_qg_dim_grounding(
            parsed,
            dim=dim,
            generated_content=generated_content,
            response_path=response_path,
        )
    except OSError as exc:
        print(
            f"[llm-qg] {dim}: could not read existing artifacts; retrying ({exc})",
            file=sys.stderr,
            flush=True,
        )
        return None
    except linear_pipeline.LinearPipelineError as exc:
        print(
            f"[llm-qg] {dim}: existing response artifact is unusable; retrying ({exc})",
            file=sys.stderr,
            flush=True,
        )
        return None

    print(f"[llm-qg] {dim}: resumed from {response_path.name}", flush=True)
    return parsed


def _run_llm_qg(
    *,
    plan: Mapping[str, Any],
    plan_content: str,
    module_dir: Path,
    writer: str,
    profile: str | None = None,
    reviewer_override: str | None = None,
    wiki_manifest: str | Mapping[str, Any] | None = None,
    implementation_map: Mapping[str, Any] | None = None,
    stdout_silence_timeout: int | None = None,
    use_generator: bool = False,
    obligation_checklist: Mapping[str, Any] | None = None,
    event_sink: Callable[..., None] | None = None,
    reviewer_samples: int = 1,
) -> dict[str, Any]:
    from scripts.agent_runtime.runner import invoke

    reviewer = _reviewer_for_writer(writer, reviewer_override)
    defaults = linear_pipeline.REVIEWER_DEFAULTS[reviewer]
    sample_count = max(1, int(reviewer_samples))

    assert linear_pipeline.WRITER_DEFAULTS[writer]["model"] != defaults["model"], \
        f"same-model self-review forbidden: writer={writer} reviewer={reviewer}"

    agent_name = reviewer.split("-", 1)[0]
    generated_content = _generated_content(module_dir)
    report: dict[str, Any] = {}

    for dim in QG_DIMS:
        prompt = linear_pipeline.render_review_prompt(
            plan,
            plan_content,
            generated_content,
            dim,
            wiki_manifest,
            implementation_map,
            use_generator=use_generator,
            obligation_checklist=obligation_checklist,
        )
        prompt_path = module_dir / f"llm-qg-{dim}-prompt.md"
        response_path = module_dir / f"llm-qg-{dim}-response.raw.md"
        if sample_count == 1:
            resumed = _resume_llm_qg_dim_if_current(
                dim=dim,
                prompt=prompt,
                prompt_path=prompt_path,
                response_path=response_path,
                generated_content=generated_content,
            )
            if resumed is not None:
                report[dim] = resumed
                continue

        prompt_path.write_text(prompt, encoding="utf-8")
        dim_results: list[dict[str, Any]] = []
        raw_responses: list[str] = []
        for sample_index in range(sample_count):
            sample_response_path = (
                response_path
                if sample_count == 1
                else module_dir / f"llm-qg-{dim}-sample-{sample_index + 1}-response.raw.md"
            )
            task_id = f"linear-v7-qg-{plan['slug']}-{dim}"
            if sample_count > 1:
                task_id = f"{task_id}-s{sample_index + 1}"
            last_error: linear_pipeline.LinearPipelineError | None = None
            for attempt in range(1, LLM_QG_DIM_MAX_ATTEMPTS + 1):
                attempt_prompt = _llm_qg_retry_prompt(prompt, last_error) if last_error is not None else prompt
                if attempt > 1:
                    prompt_path.write_text(attempt_prompt, encoding="utf-8")
                result = invoke(
                    agent_name,
                    attempt_prompt,
                    mode="read-only",
                    cwd=module_dir,
                    model=defaults["model"],
                    task_id=task_id,
                    entrypoint="dispatch",
                    effort=defaults["effort"],
                    tool_config={"output_format": "stream-json"},
                    stdout_silence_timeout=stdout_silence_timeout,
                )
                response = str(getattr(result, "response", "") or "")
                # Persist raw reviewer response BEFORE parse so #M-10 forensic
                # continuity holds when the parser raises (build #10, 2026-05-21
                # exposed prose-wrapped JSON shape with no saved artifact).
                sample_response_path.write_text(response, encoding="utf-8")
                try:
                    parsed = _parse_llm_qg_dim_response(
                        response,
                        dim=dim,
                        response_path=sample_response_path,
                    )
                    _validate_llm_qg_dim_grounding(
                        parsed,
                        dim=dim,
                        generated_content=generated_content,
                        response_path=sample_response_path,
                    )
                    dim_results.append(parsed)
                    raw_responses.append(response)
                    break
                except linear_pipeline.LinearPipelineError as exc:
                    last_error = exc
                    if attempt < LLM_QG_DIM_MAX_ATTEMPTS:
                        print(
                            f"[llm-qg] {dim}: attempt {attempt}/{LLM_QG_DIM_MAX_ATTEMPTS} failed; retrying ({exc})",
                            file=sys.stderr,
                            flush=True,
                        )
                        continue
                    raise linear_pipeline.LinearPipelineError(
                        f"LLM QG {dim} failed after {LLM_QG_DIM_MAX_ATTEMPTS} attempt(s); "
                        f"raw response saved to {sample_response_path}: {last_error}"
                    ) from last_error

        if sample_count == 1:
            report[dim] = dim_results[0]
        else:
            scores = [float(result["score"]) for result in dim_results]
            chosen_index = linear_pipeline.llm_qg_median_sample_index(scores)
            response_path.write_text(raw_responses[chosen_index], encoding="utf-8")
            report[dim] = linear_pipeline.select_median_llm_review_sample(
                dim_results,
                dim=dim,
                reviewer=reviewer,
                module=f"{str(plan['level']).lower()}/{plan['slug']}",
                writer_under_review=writer,
                event_sink=event_sink,
            )

    return linear_pipeline.aggregate_llm_review(
        report,
        str(plan["level"]),
        profile=profile,
    )


def _persist_llm_qg_result(
    *,
    level: str,
    slug: str,
    module_dir: Path,
    llm_qg: dict[str, Any],
    reviewer: str,
    source: str,
) -> None:
    defaults = linear_pipeline.REVIEWER_DEFAULTS.get(reviewer, {})
    try:
        record_llm_qg(
            level=level,
            slug=slug,
            module_dir=module_dir,
            payload=llm_qg,
            gate_version="v7.llm_qg.1",
            prompt_hash=_combined_llm_qg_prompt_hash(module_dir),
            reviewer_model=defaults.get("model"),
            reviewer_family=reviewer,
            source=source,
        )
    except Exception as exc:
        raise linear_pipeline.LinearPipelineError(
            f"LLM QG completed but result persistence failed: {exc}"
        ) from exc


def _combined_llm_qg_prompt_hash(module_dir: Path) -> str | None:
    prompt_parts: list[str] = []
    for dim in QG_DIMS:
        prompt_path = module_dir / f"llm-qg-{dim}-prompt.md"
        if not prompt_path.exists():
            return None
        prompt_parts.append(f"## {dim}\n{prompt_path.read_text(encoding='utf-8')}")
    return prompt_hash_for_text("\n\n".join(prompt_parts))


def _run_wiki_coverage_review(
    *,
    plan: Mapping[str, Any],
    plan_content: str,
    module_dir: Path,
    writer: str,
    reviewer_override: str | None = None,
    wiki_manifest: str | Mapping[str, Any],
    wiki_coverage_gate: Mapping[str, Any],
    stdout_silence_timeout: int | None = None,
) -> dict[str, Any]:
    from scripts.agent_runtime.runner import invoke

    reviewer = _reviewer_for_writer(writer, reviewer_override)
    defaults = linear_pipeline.REVIEWER_DEFAULTS[reviewer]

    assert linear_pipeline.WRITER_DEFAULTS[writer]["model"] != defaults["model"], \
        f"same-model self-review forbidden: writer={writer} reviewer={reviewer}"

    agent_name = reviewer.split("-", 1)[0]
    generated_content = _generated_content(module_dir)
    prompt = linear_pipeline.render_wiki_coverage_review_prompt(
        plan,
        plan_content,
        generated_content,
        wiki_manifest,
        wiki_coverage_gate,
    )
    (module_dir / "wiki-coverage-review-prompt.md").write_text(
        prompt,
        encoding="utf-8",
    )
    result = invoke(
        agent_name,
        prompt,
        mode="read-only",
        cwd=module_dir,
        model=defaults["model"],
        task_id=f"linear-v7-wiki-coverage-{plan['slug']}",
        entrypoint="dispatch",
        effort=defaults["effort"],
        tool_config={"output_format": "stream-json"},
        stdout_silence_timeout=stdout_silence_timeout,
    )
    response = str(getattr(result, "response", "") or "")
    # Persist raw reviewer response BEFORE parse so #M-10 forensic continuity
    # holds when the parser raises. Build #10 (a1/my-morning, 2026-05-21)
    # exposed prose-wrapped JSON: codex-tools emitted "I have verified all
    # **18 obligations**..." narrative around the structured payload, the
    # parser failed, no artifact was saved, and the only diagnostic was the
    # YAML-parser error string in the build event log.
    (module_dir / "wiki-coverage-review-response.raw.md").write_text(
        response,
        encoding="utf-8",
    )
    return linear_pipeline.parse_wiki_coverage_review_response(response)


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description=(
            "Build one V7 curriculum module through scripts.build.linear_pipeline.\n"
            "Use for single-module V7 reboot builds; do not use for V6 legacy "
            "batch, rewrite, or regeneration workflows."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/build/v7_build.py a1 my-morning --dry-run\n"
            "  .venv/bin/python scripts/build/v7_build.py a1 my-morning --worktree\n"
            "  .venv/bin/python scripts/build/v7_build.py a1 my-morning --writer gemini-tools\n"
            "  .venv/bin/python scripts/build/v7_build.py a1 my-morning --writer codex-tools --telemetry-out audit/bakeoff-2026-05-05/gpt55.write.jsonl\n"
            "  .venv/bin/python scripts/build/v7_build.py b1-pro intro --out /tmp/v7-intro\n\n"
            "Outputs:\n"
            "  Emits JSONL monitor events to stdout, or appends them to --telemetry-out. Full builds write the writer "
            "artifacts, knowledge_packet.md, writer_prompt.md, python_qg.json, "
            "llm_qg.json, and {slug}.mdx under --out or "
            "curriculum/l2-uk-en/{level}/{slug}/. Dry runs do not write files.\n\n"
            "Worktrees:\n"
            "  Pass --worktree to create .worktrees/builds/{level}-{slug}-{timestamp}/ "
            "and run this build there on a build/{level}/{slug}-{timestamp} branch. "
            "Pass --worktree PATH to choose the worktree path; relative paths "
            "resolve from the repository root. If --out is also passed, relative "
            "--out paths resolve inside the build worktree.\n\n"
            "Exit codes:\n"
            "  0 on successful build or dry run.\n"
            "  1 on plan, packet, writer, QG, review, MDX, or filesystem failure.\n"
            "  2 on command-line usage errors from argparse or --worktree outside this repo.\n"
            "  3 when the requested --worktree path already exists.\n"
            "  4 when git worktree add fails.\n\n"
            "  5 when a primary-checkout safety guard refuses the run.\n\n"
            "  124 when a writer subprocess is killed after --writer-timeout "
            "seconds of stdout silence.\n\n"
            "Related:\n"
            "  Pipeline: scripts/build/linear_pipeline.py\n"
            "  Writer prompts: scripts/build/phases/linear-write*.md\n"
            "  Reviewer prompt: scripts/build/phases/linear-review-dim.md\n"
            "  ADR-007: docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md\n"
            "  ADR-008: docs/decisions/2026-04-28-targeted-gate-correction-paths.md\n"
            "  Issue: #1637"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    parser.add_argument(
        "level",
        help="Curriculum level code, for example a1, b1-pro, or hist.",
    )
    parser.add_argument(
        "slug",
        help="Module slug matching curriculum/l2-uk-en/plans/{level}/{slug}.yaml.",
    )
    parser.add_argument(
        "--writer",
        choices=WRITER_CHOICES,
        default="claude-tools",
        help=(
            "Writer backend for the one-shot V7 write phase "
            "(default: claude-tools; claude/gemini/codex/grok/deepseek/qwen/agy "
            "aliases normalize to <name>-tools)."
        ),
    )
    parser.add_argument(
        "--reviewer",
        choices=WRITER_CHOICES,
        default=None,
        help=(
            "Override the reviewer backend for wiki coverage review and LLM QG. "
            "Defaults to the pipeline's writer-specific reviewer routing; aliases "
            "normalize to <name>-tools."
        ),
    )
    parser.add_argument(
        "--writer-timeout",
        metavar="SECONDS",
        type=_positive_int,
        default=DEFAULT_WRITER_TIMEOUT_S,
        help=(
            "Kill the writer subprocess and exit 124 if it produces no stdout "
            f"for SECONDS (default: {DEFAULT_WRITER_TIMEOUT_S})."
        ),
    )
    parser.add_argument(
        "--effort",
        choices=("low", "medium", "high", "xhigh", "max"),
        default=None,
        help=(
            "Override reasoning effort for the writer phase. Defaults to "
            "WRITER_DEFAULTS[writer]['effort'] when unset. The 2026-05-19 B1 "
            "writer bakeoff validated deepseek-tools at xhigh (medium fails "
            "with scaffolding-only on B1+ word targets); use --effort xhigh "
            "for deepseek/qwen-routed builds at A2+ until the per-writer "
            "defaults are revised."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Load the plan and build the knowledge packet, then stop before "
            "writer invocation and file writes (default: false)."
        ),
    )
    parser.add_argument(
        "--out",
        metavar="PATH",
        default=None,
        help=(
            "Output directory for full-build artifacts (default: "
            "curriculum/l2-uk-en/{level}/{slug}/). Relative paths resolve "
            "from the repository root, or from the build worktree root when "
            "--worktree is used."
        ),
    )
    parser.add_argument(
        "--worktree",
        nargs="?",
        const=WORKTREE_AUTO,
        default=None,
        metavar="PATH",
        help=(
            "Create a fresh git worktree and run the build inside it. With no "
            "PATH, uses .worktrees/builds/{level}-{slug}-{YYYYMMDD-HHMMSS}/ "
            "and branch build/{level}/{slug}-{YYYYMMDD-HHMMSS}. With PATH, "
            "uses that path and derives the branch from its basename when "
            "possible."
        ),
    )
    parser.add_argument(
        "--keep-worktree",
        action="store_true",
        help=(
            "When --worktree succeeds, keep the build worktree instead of "
            "reaping it after artifact persistence."
        ),
    )
    parser.add_argument(
        "--telemetry-out",
        metavar="PATH",
        default=None,
        help=(
            "Append JSONL monitor events to PATH instead of stdout. Relative "
            "paths resolve from the repository root; default: stdout."
        ),
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help=(
            "Force a full rebuild from scratch. Default behavior resumes from "
            "the last failed phase using artifact existence checks."
        ),
    )
    parser.add_argument(
        "--use-generator",
        action="store_true",
        help=(
            "V7.2 Step 5 (opt-in): compose the writer + reviewer prompts from "
            "the universal-rules registry + wiki manifest via "
            "scripts/build/prompt_generator.py (templates "
            "linear-write.generated.md / linear-review-dim.generated.md) "
            "instead of the legacy linear-write.md / linear-review-dim.md. "
            "Default OFF — the legacy template path is unchanged."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = parse_args(raw_argv)
    if args.worktree is not None:
        return _run_in_worktree(args, raw_argv)
    if run_archive.ENV_KEY not in os.environ:
        try:
            _ensure_top_level_invocation_is_not_primary_checkout()
        except PrimaryCheckoutSafetyError as exc:
            print(str(exc), file=sys.stderr)
            return exc.exit_code
    telemetry_out = _resolve_project_path(args.telemetry_out)
    with linear_pipeline.telemetry_event_sink(telemetry_out):
        return _run(args)


# ----- Resume helpers ---------------------------------------------------------
#
# Resume policy: skip a phase iff its on-disk artifact exists AND reports the
# canonical success shape for that phase. Any missing / failed artifact forces
# the phase to re-run. Once one phase re-runs, every downstream phase also
# re-runs unconditionally (the corrections may invalidate later verdicts).
#
# Codified after the 2026-05-21 cascade burned ~14 minutes of writer time per
# iteration on phase-6 fixes. With resume, iteration drops to ~45s for the
# review-only re-run path.

def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _phase_artifact_passes(module_dir: Path, phase: str) -> bool:
    """Return True if `phase`'s on-disk artifact exists and reports success.

    The on-disk shapes mirror the success conditions enforced in `_run` itself
    (see the post-phase guards: `gates.passed`,
    `wiki_completeness_gate.verdict == "PASS"`, `wiki_coverage_gate.passed`,
    `wiki_coverage_review.overall_verdict == "PASS"`, and
    `aggregate.terminal_verdict == "PASS"`). Any deviation means the phase
    needs to re-run.
    """
    if phase == "knowledge_packet":
        return (module_dir / "knowledge_packet.md").exists() and (
            module_dir / "wiki_manifest.json"
        ).exists()
    if phase == "writer":
        required = (
            "module.md",
            "activities.yaml",
            "vocabulary.yaml",
            "resources.yaml",
            "writer_output.raw.md",
            "implementation_map.json",
        )
        return all((module_dir / name).exists() for name in required)
    if phase == "stress_annotation":
        data = _read_json(module_dir / "stress_annotation.json")
        return (
            isinstance(data, Mapping)
            and data.get("passed") is True
            and (module_dir / "module.md").exists()
            and (module_dir / "vocabulary.yaml").exists()
        )
    if phase == "ulp_fidelity_gate":
        data = _read_json(module_dir / "ulp_fidelity_gate.json")
        return isinstance(data, Mapping) and data.get("passed") is True
    if phase == "python_qg":
        data = _read_json(module_dir / "python_qg.json")
        if not isinstance(data, Mapping):
            return False
        gates = data.get("gates")
        return isinstance(gates, Mapping) and gates.get("passed") is True
    if phase == "wiki_completeness_gate":
        data = _read_json(module_dir / "wiki_completeness_gate.json")
        return isinstance(data, Mapping) and data.get("verdict") == "PASS"
    if phase == "wiki_coverage_gate":
        data = _read_json(module_dir / "wiki_coverage_gate.json")
        return isinstance(data, Mapping) and data.get("passed") is True
    if phase == "wiki_coverage_review":
        data = _read_json(module_dir / "wiki_coverage_review.json")
        return (
            isinstance(data, Mapping)
            and str(data.get("overall_verdict", "")).upper() == "PASS"
        )
    if phase == "llm_qg":
        return _current_db_llm_qg_passes(module_dir)
    return False


def _llm_qg_payload_passes(payload: Mapping[str, Any] | None) -> bool:
    if not isinstance(payload, Mapping):
        return False
    aggregate = payload.get("aggregate")
    if not isinstance(aggregate, Mapping):
        return False
    terminal_verdict = aggregate.get("terminal_verdict", aggregate.get("verdict", ""))
    return str(terminal_verdict).upper() == "PASS"


def _current_db_llm_qg_payload(module_dir: Path) -> dict[str, Any] | None:
    level = module_dir.parent.name
    slug = module_dir.name
    return current_payload_for_module(level, slug, module_dir)


def _current_db_llm_qg_passes(module_dir: Path) -> bool:
    return _llm_qg_payload_passes(_current_db_llm_qg_payload(module_dir))


def _run_stress_annotation_for_level(module_dir: Path, level: str) -> dict[str, Any]:
    if level.lower() in SEMINAR_LEVELS:
        return linear_pipeline.strip_stress_marks_for_seminar(module_dir)
    return linear_pipeline.run_stress_annotation(module_dir)


def _run(args: argparse.Namespace) -> int:
    level = args.level.lower()
    slug = args.slug
    writer = _normalize_writer(args.writer)
    reviewer_override = _normalize_writer(args.reviewer) if args.reviewer else None
    # Optional flag (argparse always sets it; test SimpleNamespace fixtures may
    # omit it, mirroring the getattr handling of no_resume below).
    use_generator = getattr(args, "use_generator", False)
    module_started_at = time.monotonic()
    phase = "start"
    timeout_agent = writer
    tracker = LastEventTracker()
    archive = run_archive.RunArchive.from_env()
    plan_path: Path | None = None
    module_dir: Path | None = None

    # Resume is the default. Pass --no-resume for a forced full restart.
    # Per architectural reset 2026-05-23
    # (docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md
    # decision #8), each of 6 failed builds 2026-05-22 to 2026-05-23 burned
    # 5-20 minutes replaying writer when only a later phase had failed.
    resume_enabled = not getattr(args, "no_resume", False)
    force_rerun = False

    tracker.emit("module_start", level=level, slug=slug)

    try:
        phase = "plan"
        _phase_started(archive, phase)
        started_at = time.monotonic()
        plan_path = linear_pipeline.plan_path_for(level, slug)
        plan_content = plan_path.read_text(encoding="utf-8")
        plan = linear_pipeline.load_plan(plan_path)
        linear_pipeline.validate_plan(plan)
        profile = linear_pipeline.curriculum_profile_for_level(level)
        _phase_done(
            phase,
            started_at,
            level=level,
            slug=slug,
            event_sink=tracker.emit,
            archive=archive,
        )

        phase = "knowledge_packet"
        _phase_started(archive, phase)
        started_at = time.monotonic()
        resume_module_dir = _resolve_output_dir(args.out, level, slug)
        if (
            resume_enabled
            and not force_rerun
            and _phase_artifact_passes(resume_module_dir, "knowledge_packet")
        ):
            knowledge_packet = (resume_module_dir / "knowledge_packet.md").read_text(
                encoding="utf-8",
            )
            wiki_manifest = (resume_module_dir / "wiki_manifest.json").read_text(
                encoding="utf-8",
            )
            wiki_manifest_data = json.loads(wiki_manifest)
            tracker.emit("phase_resumed", phase=phase, level=level, slug=slug)
        else:
            if resume_enabled:
                force_rerun = True
            knowledge_packet = linear_pipeline.build_knowledge_packet(
                level=level,
                slug=slug,
                plan=plan,
            )
            wiki_manifest_data = linear_pipeline.build_wiki_manifest_data(
                level=level,
                slug=slug,
                plan=plan,
            )
            wiki_manifest = json.dumps(wiki_manifest_data, ensure_ascii=False, indent=2)
        _phase_done(
            phase,
            started_at,
            level=level,
            slug=slug,
            event_sink=tracker.emit,
            archive=archive,
        )

        module_dir = _resolve_output_dir(args.out, level, slug)

        phase = "wiki_completeness_gate"
        _phase_started(archive, phase)
        started_at = time.monotonic()
        module_dir.mkdir(parents=True, exist_ok=True)
        if (
            resume_enabled
            and not force_rerun
            and _phase_artifact_passes(module_dir, "wiki_completeness_gate")
        ):
            wiki_completeness_gate = _read_json(module_dir / "wiki_completeness_gate.json")
            tracker.emit("phase_resumed", phase=phase, level=level, slug=slug)
        else:
            if resume_enabled:
                force_rerun = True
            wiki_completeness_gate = linear_pipeline.run_wiki_completeness_gate(
                level=level,
                slug=slug,
                wiki_manifest=wiki_manifest_data,
            )
            linear_pipeline.write_json(
                module_dir / "wiki_completeness_gate.json", wiki_completeness_gate
            )
        _phase_done(
            phase,
            started_at,
            level=level,
            slug=slug,
            event_sink=tracker.emit,
            archive=archive,
            artifact_dir=module_dir,
        )
        if not isinstance(wiki_completeness_gate, Mapping) or wiki_completeness_gate.get("verdict") != "PASS":
            diagnostic = (
                wiki_completeness_gate.get("diagnostic")
                if isinstance(wiki_completeness_gate, Mapping)
                else "Wiki completeness gate returned malformed output"
            )
            raise linear_pipeline.LinearPipelineError(str(diagnostic))

        if args.dry_run:
            sections = [
                str(item.get("section"))
                for item in plan.get("content_outline", [])
                if isinstance(item, Mapping) and item.get("section")
            ]
            linear_pipeline.emit_writer_response_telemetry(
                "",
                writer=writer,
                module=f"{level.lower()}/{int(plan['sequence'])}",
                sections=sections,
                tool_calls=[],
                event_sink=tracker.emit,
            )
            tracker.emit(
                "module_done",
                level=level,
                slug=slug,
                dry_run=True,
                duration_s=round(time.monotonic() - module_started_at, 3),
            )
            return 0

        phase = "writer"
        _phase_started(archive, phase)
        timeout_agent = writer
        started_at = time.monotonic()
        module_dir.mkdir(parents=True, exist_ok=True)
        impl_map_path = module_dir / "implementation_map.json"
        obligation_checklist: Mapping[str, Any] | None = None
        if (
            resume_enabled
            and not force_rerun
            and _phase_artifact_passes(module_dir, "writer")
        ):
            writer_output = (module_dir / "writer_output.raw.md").read_text(
                encoding="utf-8",
            )
            if impl_map_path.exists():
                impl_map = read_implementation_map(impl_map_path)
            else:
                impl_map = seed_implementation_map(wiki_manifest_data, plan=plan)
                write_implementation_map(impl_map, impl_map_path)
            if use_generator:
                obligation_checklist = linear_pipeline.build_wiki_coverage_obligation_checklist(
                    wiki_manifest_data,
                    seeded_map=impl_map,
                )
            tracker.emit("phase_resumed", phase=phase, level=level, slug=slug)
        else:
            if resume_enabled:
                force_rerun = True
            impl_map = seed_implementation_map(wiki_manifest_data, plan=plan)
            write_implementation_map(impl_map, impl_map_path)
            if use_generator:
                obligation_checklist = linear_pipeline.build_wiki_coverage_obligation_checklist(
                    wiki_manifest_data,
                    seeded_map=impl_map,
                )
            tracker.emit(
                "implementation_map_seeded",
                slug=slug,
                entry_count=len(impl_map["entries"]),
                path=str(impl_map_path),
            )
            prompt = _writer_prompt(
                plan=plan,
                plan_path=plan_path,
                plan_content=plan_content,
                knowledge_packet=knowledge_packet,
                wiki_manifest=wiki_manifest,
                implementation_map=impl_map,
                writer=writer,
                use_generator=use_generator,
                obligation_checklist=obligation_checklist,
            )
            # gemini-tools must load .gemini/settings.json from repo root;
            # module_dir cwd would leave its MCP catalog empty. See
            # audit/gemini-tools-review-2026-05-09/REPORT.html E5/E6.
            # grok-tools routes to grok-hermes (Hermes MCP via ~/.hermes/config.yaml)
            # and can run from the module directory like claude-tools/codex-tools.
            writer_cwd = PROJECT_ROOT if writer == "gemini-tools" else module_dir
            writer_output = linear_pipeline.invoke_writer(
                prompt,
                writer,
                cwd=writer_cwd,
                tool_trace_path=module_dir / "writer_tool_calls.json",
                stdout_silence_timeout=args.writer_timeout,
                effort=args.effort,
            )
            # Save raw writer output + prompt + knowledge packet BEFORE parse so any
            # parse failure is fully debuggable. Without this, a parse error like
            # "Writer output contains unnamed fenced block at line 113" leaves
            # nothing on disk to inspect — the writer_output is held only in memory
            # and is lost on the LinearPipelineError raise.
            (module_dir / "writer_output.raw.md").write_text(
                writer_output,
                encoding="utf-8",
            )
            (module_dir / "writer_prompt.md").write_text(prompt, encoding="utf-8")
            (module_dir / "knowledge_packet.md").write_text(
                knowledge_packet,
                encoding="utf-8",
            )
            (module_dir / "wiki_manifest.json").write_text(
                wiki_manifest,
                encoding="utf-8",
            )
            artifacts = linear_pipeline.parse_writer_output(writer_output)
            linear_pipeline.write_writer_artifacts(module_dir, artifacts)

        precheck_path = module_dir / "writer_length_precheck.json"
        if level in SEMINAR_LEVELS and (force_rerun or not precheck_path.exists()):
            length_precheck = linear_pipeline.run_writer_draft_length_precheck(
                plan=plan,
                module_dir=module_dir,
                plan_path=plan_path,
                writer=writer,
                event_sink=tracker.emit,
            )
            linear_pipeline.write_json(precheck_path, length_precheck)
            if length_precheck.get("applied") is True:
                force_rerun = True

        _phase_done(
            phase,
            started_at,
            level=level,
            slug=slug,
            writer=writer,
            event_sink=tracker.emit,
            archive=archive,
            artifact_dir=module_dir,
        )

        phase = "stress_annotation"
        _phase_started(archive, phase)
        started_at = time.monotonic()
        if level in SEMINAR_LEVELS:
            stress_annotation = _run_stress_annotation_for_level(module_dir, level)
            linear_pipeline.write_json(
                module_dir / "stress_annotation.json",
                stress_annotation,
            )
        elif (
            resume_enabled
            and not force_rerun
            and _phase_artifact_passes(module_dir, "stress_annotation")
        ):
            stress_annotation = _read_json(module_dir / "stress_annotation.json")
            tracker.emit("phase_resumed", phase=phase, level=level, slug=slug)
        else:
            if resume_enabled:
                force_rerun = True
            stress_annotation = _run_stress_annotation_for_level(module_dir, level)
            linear_pipeline.write_json(
                module_dir / "stress_annotation.json",
                stress_annotation,
            )
        _phase_done(
            phase,
            started_at,
            level=level,
            slug=slug,
            event_sink=tracker.emit,
            archive=archive,
            artifact_dir=module_dir,
        )
        if not isinstance(stress_annotation, Mapping) or stress_annotation.get("passed") is not True:
            raise linear_pipeline.LinearPipelineError("Stress annotation failed")

        phase = "ulp_fidelity_gate"
        _phase_started(archive, phase)
        started_at = time.monotonic()
        if (
            resume_enabled
            and not force_rerun
            and _phase_artifact_passes(module_dir, "ulp_fidelity_gate")
        ):
            ulp_fidelity_gate = _read_json(module_dir / "ulp_fidelity_gate.json")
            tracker.emit("phase_resumed", phase=phase, level=level, slug=slug)
        else:
            if resume_enabled:
                force_rerun = True
            ulp_fidelity_gate = linear_pipeline.run_ulp_fidelity_with_correction(
                module_dir,
                plan_path,
                profile=profile,
                writer=writer,
            )
            linear_pipeline.write_json(
                module_dir / "ulp_fidelity_gate.json",
                ulp_fidelity_gate,
            )
        _phase_done(
            phase,
            started_at,
            level=level,
            slug=slug,
            event_sink=tracker.emit,
            archive=archive,
            artifact_dir=module_dir,
        )
        if not isinstance(ulp_fidelity_gate, Mapping) or ulp_fidelity_gate.get("passed") is not True:
            failed = (
                ulp_fidelity_gate.get("failed_checks")
                if isinstance(ulp_fidelity_gate, Mapping)
                else "malformed ulp_fidelity report"
            )
            raise linear_pipeline.LinearPipelineError(f"ULP fidelity gate failed: {failed}")

        phase = "python_qg"
        _phase_started(archive, phase)
        started_at = time.monotonic()
        if (
            resume_enabled
            and not force_rerun
            and _phase_artifact_passes(module_dir, "python_qg")
        ):
            python_qg = _read_json(module_dir / "python_qg.json")
            tracker.emit("phase_resumed", phase=phase, level=level, slug=slug)
        else:
            if resume_enabled:
                force_rerun = True
            python_qg = linear_pipeline.run_python_qg_with_corrections(
                module_dir,
                plan_path,
                writer=writer,
            )
            linear_pipeline.write_json(module_dir / "python_qg.json", python_qg)
        _phase_done(
            phase,
            started_at,
            level=level,
            slug=slug,
            event_sink=tracker.emit,
            archive=archive,
            artifact_dir=module_dir,
        )
        gates = python_qg.get("gates") if isinstance(python_qg, Mapping) else None
        if not isinstance(gates, Mapping) or gates.get("passed") is not True:
            raise linear_pipeline.LinearPipelineError(
                "Python QG failed after ADR-008 correction paths"
            )

        phase = "wiki_coverage_gate"
        _phase_started(archive, phase)
        started_at = time.monotonic()
        if (
            resume_enabled
            and not force_rerun
            and _phase_artifact_passes(module_dir, "wiki_coverage_gate")
        ):
            wiki_coverage_gate = _read_json(module_dir / "wiki_coverage_gate.json")
            tracker.emit("phase_resumed", phase=phase, level=level, slug=slug)
        else:
            if resume_enabled:
                force_rerun = True
            wiki_coverage_gate = linear_pipeline.run_wiki_coverage_with_corrections(
                plan=plan,
                manifest=wiki_manifest,
                writer_output=writer_output,
                module_dir=module_dir,
                level=level,
                event_sink=tracker.emit,
                obligation_checklist=obligation_checklist,
            )
            linear_pipeline.write_json(
                module_dir / "wiki_coverage_gate.json", wiki_coverage_gate
            )
        _phase_done(
            phase,
            started_at,
            level=level,
            slug=slug,
            event_sink=tracker.emit,
            archive=archive,
            artifact_dir=module_dir,
        )
        if not isinstance(wiki_coverage_gate, Mapping) or wiki_coverage_gate.get("passed") is not True:
            raise linear_pipeline.LinearPipelineError(
                "Wiki coverage gate failed after batched + narrow correction passes"
            )

        phase = "wiki_coverage_review"
        _phase_started(archive, phase)
        timeout_agent = _reviewer_for_writer(writer, reviewer_override)
        started_at = time.monotonic()
        if (
            resume_enabled
            and not force_rerun
            and _phase_artifact_passes(module_dir, "wiki_coverage_review")
        ):
            wiki_coverage_review = _read_json(module_dir / "wiki_coverage_review.json")
            tracker.emit("phase_resumed", phase=phase, level=level, slug=slug)
        else:
            if resume_enabled:
                force_rerun = True
            wiki_coverage_review = _run_wiki_coverage_review(
                plan=plan,
                plan_content=plan_content,
                module_dir=module_dir,
                writer=writer,
                reviewer_override=reviewer_override,
                wiki_manifest=wiki_manifest,
                wiki_coverage_gate=wiki_coverage_gate,
                stdout_silence_timeout=args.writer_timeout,
            )
            linear_pipeline.write_json(
                module_dir / "wiki_coverage_review.json",
                wiki_coverage_review,
            )
        # Phase 5 Goodhart sentinel telemetry (PR4)
        stuffing_count = sum(
            1
            for v in wiki_coverage_review.get("verdicts", [])
            if str(v.get("verdict", "")).upper() == "KEYWORD_STUFFING"
        )
        partial_count = sum(
            1
            for v in wiki_coverage_review.get("verdicts", [])
            if str(v.get("verdict", "")).upper() == "PARTIAL"
        )
        tracker.emit(
            "wiki_coverage_goodhart_sentinel",
            level=level,
            slug=slug,
            overall_verdict=wiki_coverage_review["overall_verdict"],
            keyword_stuffing_count=stuffing_count,
            partial_count=partial_count,
            total_verdicts=len(wiki_coverage_review.get("verdicts", [])),
        )
        _phase_done(
            phase,
            started_at,
            level=level,
            slug=slug,
            event_sink=tracker.emit,
            archive=archive,
            artifact_dir=module_dir,
        )
        if wiki_coverage_review["overall_verdict"] == "FAIL":
            raise linear_pipeline.LinearPipelineError("Wiki coverage review failed")

        phase = "llm_qg"
        _phase_started(archive, phase)
        llm_qg_reviewer_override = _llm_qg_reviewer_override_for_level(
            level=level,
            writer=writer,
            reviewer_override=reviewer_override,
        )
        llm_qg_reviewer_samples = linear_pipeline.llm_qg_reviewer_samples_for_level(level)
        timeout_agent = _reviewer_for_writer(writer, llm_qg_reviewer_override)
        started_at = time.monotonic()
        resumed_llm_qg = _current_db_llm_qg_payload(module_dir)
        if (
            resume_enabled
            and not force_rerun
            and _llm_qg_payload_passes(resumed_llm_qg)
        ):
            llm_qg = resumed_llm_qg
            llm_qg_source = "v7_build:resumed-db"
            tracker.emit("phase_resumed", phase=phase, level=level, slug=slug)
        else:
            if resume_enabled:
                force_rerun = True
            llm_qg = linear_pipeline.run_llm_qg_with_corrections(
                plan=plan,
                plan_path=plan_path,
                plan_content=plan_content,
                module_dir=module_dir,
                writer=writer,
                llm_qg_runner=_run_llm_qg,
                reviewer_override=llm_qg_reviewer_override,
                profile=profile,
                wiki_manifest=wiki_manifest,
                implementation_map=impl_map,
                stdout_silence_timeout=args.writer_timeout,
                use_generator=use_generator,
                obligation_checklist=obligation_checklist,
                max_rounds=linear_pipeline.llm_qg_max_rounds_for_level(level),
                event_sink=tracker.emit,
                reviewer_samples=llm_qg_reviewer_samples,
            )
            linear_pipeline.write_json(module_dir / "llm_qg.json", llm_qg)
            llm_qg_source = "v7_build"
        _persist_llm_qg_result(
            level=level,
            slug=slug,
            module_dir=module_dir,
            llm_qg=llm_qg,
            reviewer=_reviewer_for_writer(writer, llm_qg_reviewer_override),
            source=llm_qg_source,
        )
        aggregate = llm_qg["aggregate"]
        tracker.emit(
            "review_score",
            level=level,
            slug=slug,
            score=aggregate["min_score"],
            verdict=aggregate["verdict"],
        )
        _phase_done(
            phase,
            started_at,
            level=level,
            slug=slug,
            event_sink=tracker.emit,
            archive=archive,
            artifact_dir=module_dir,
        )
        terminal_verdict = aggregate.get("terminal_verdict", aggregate["verdict"])

        # Emit warning telemetry when warning dims drove the non-PASS aggregate.
        # Build continues regardless of warning-dim verdict; reviewer output stays
        # in llm_qg.json for human review. Per architectural reset 2026-05-23
        # (docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md).
        warning_dims = aggregate.get("warning_dims") or ()
        if aggregate["verdict"] != "PASS" and warning_dims:
            tracker.emit(
                "llm_qg_warning",
                level=level,
                slug=slug,
                aggregate_verdict=aggregate["verdict"],
                terminal_verdict=terminal_verdict,
                warning_dims=list(warning_dims),
                rejected_dims=list(aggregate.get("rejected_dims") or ()),
                min_dim=aggregate.get("min_dim"),
                min_score=aggregate.get("min_score"),
            )

        # Only terminal-dim verdicts kill the build.
        if terminal_verdict != "PASS":
            failing_terminal_dims = [
                dim
                for dim in aggregate.get("failing_dims", ())
                if dim in terminal_dims_for(profile)
            ]
            raise linear_pipeline.LinearPipelineError(
                f"LLM QG terminal verdict was {terminal_verdict} "
                f"(failing terminal dims: {failing_terminal_dims})"
            )

        phase = "mdx"
        _phase_started(archive, phase)
        started_at = time.monotonic()
        # MDX is the BUILT artifact and goes where Site reads it. Source
        # artifacts (.md, *.yaml) stay in curriculum/ as authoring source. When
        # --out is set (test/sandbox builds), MDX colocates with the artifact
        # dump so the test stays self-contained.
        if args.out is None:
            site_dir = (
                PROJECT_ROOT
                / "site"
                / "src"
                / "content"
                / "docs"
                / level.lower()
            )
            site_dir.mkdir(parents=True, exist_ok=True)
            mdx_path = site_dir / f"{slug}.mdx"
        else:
            mdx_path = module_dir / f"{slug}.mdx"
        linear_pipeline.assemble_mdx(module_dir, mdx_path, plan_path)
        _phase_done(
            phase,
            started_at,
            level=level,
            slug=slug,
            output=mdx_path,
            event_sink=tracker.emit,
            archive=archive,
            artifact_dir=module_dir,
        )

        tracker.emit(
            "module_done",
            level=level,
            slug=slug,
            duration_s=round(time.monotonic() - module_started_at, 3),
        )
        return 0
    except AgentStalledError as exc:
        tracker.emit(
            "writer_timeout",
            level=level,
            slug=slug,
            writer=timeout_agent,
            phase=phase,
            timeout_s=args.writer_timeout,
            last_event_type=tracker.event_type,
            last_event_ts=tracker.event_ts,
            total_wall_time_s=round(time.monotonic() - module_started_at, 3),
        )
        print(f"v7_build timed out in phase {phase}: {exc}", file=sys.stderr, flush=True)
        _archive_failure_best_effort(
            archive,
            phase=phase,
            module_dir=module_dir,
            plan_path=plan_path,
            exc=exc,
        )
        return 124
    except Exception as exc:
        tracker.emit(
            "module_failed",
            level=level,
            slug=slug,
            phase=phase,
            reason=str(exc)[:500],
        )
        print(f"v7_build failed in phase {phase}: {exc}", file=sys.stderr, flush=True)
        _archive_failure_best_effort(
            archive,
            phase=phase,
            module_dir=module_dir,
            plan_path=plan_path,
            exc=exc,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
