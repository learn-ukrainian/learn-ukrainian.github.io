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
from scripts.build import linear_pipeline, run_archive
from scripts.build.phases.implementation_map import (
    read_implementation_map,
    seed_implementation_map,
    write_implementation_map,
)
from scripts.common.thresholds import LLM_QG_TERMINAL_DIMS, QG_DIMS

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
    )


def _repo_root_from_cwd() -> Path:
    try:
        proc = _run_git(["rev-parse", "--show-toplevel"], cwd=Path.cwd())
    except (OSError, subprocess.SubprocessError) as exc:
        raise WorktreeRepoError(
            f"cwd must be inside the repository to use --worktree: {exc}"
        ) from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "not a git repository").strip()
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
            / "starlight"
            / "src"
            / "content"
            / "docs"
            / level.lower()
            / f"{slug}.mdx"
        )
    return module_dir / f"{slug}.mdx"


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
) -> None:
    print(f"BUILD_WORKTREE={worktree.path}")
    print(f"BUILD_BRANCH={worktree.branch}")
    print(f"BUILD_BASE={worktree.base_sha}")
    print(f"BUILD_RESULT={result}")
    print("Next steps if successful:")
    print(f"  cd {worktree.path}")
    print("  git status")
    print(
        "  git add "
        f"curriculum/l2-uk-en/{level}/{slug}/*.yaml "
        f"starlight/src/content/docs/{level}/{slug}.mdx"
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
) -> None:
    """Commit ALL build artifacts to the worktree's build branch.

    Build artifacts (writer_prompt.md, writer_output.raw.md, hermes.write.jsonl,
    writer_tool_calls.json, knowledge_packet.md, implementation_map.json, the
    module.md + yaml siblings, and the assembled MDX if the build reached the
    publish phase) are LOAD-BEARING for diagnosis and for the self-correction
    loop. They MUST survive worktree removal — otherwise `git worktree remove`
    silently destroys forensic evidence (encoded as #M-10 in MEMORY.md after
    the 2026-05-19→20 incident where 7 worktrees were cleaned up and today's
    diagnostic artifacts were lost).

    Strategy: from inside the worktree's working tree, ``git add -A &&
    git commit --allow-empty -m "build(level/slug): artifacts (<result>)"``.
    The build branch is private to this worktree (created from origin/main in
    ``_setup_worktree`` with the unique timestamped suffix) so the commit
    cannot collide with another build of the same module. We deliberately
    do NOT push — keeps origin clean while preserving locally. Users who
    want shareable provenance for a specific build can push that branch
    manually.

    Errors here are non-fatal: persistence is best-effort. A failure to
    commit (e.g. git config not set, hooks blocking) prints a warning and
    returns. Better to leave the worktree dir as-is than to crash the
    wrapper after the actual build already finished.
    """
    try:
        # Stage every file in the worktree relative to its working tree.
        # The worktree was created from origin/main with no local edits,
        # so any staged change here came from the build run.
        subprocess.run(
            ["git", "-C", str(worktree.path), "add", "-A"],
            check=True,
            capture_output=True,
            text=True,
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
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        stderr_tail = ""
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            stderr_tail = exc.stderr.strip().splitlines()[-1] if exc.stderr.strip() else ""
        print(
            f"v7_build: warning — failed to commit build artifacts on "
            f"branch {worktree.branch!r}: {exc}. {stderr_tail}".rstrip(),
            file=sys.stderr,
        )


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
        project_root=worktree.repo_root,
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
        _persist_build_artifacts(worktree, level=level, slug=slug, result=result)
        _print_worktree_summary(worktree, level=level, slug=slug, result=result)
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
) -> str:
    return linear_pipeline.render_writer_prompt(
        plan=plan,
        plan_content=plan_content,
        knowledge_packet=knowledge_packet,
        wiki_manifest=wiki_manifest,
        implementation_map=implementation_map,
        writer=writer,
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


def _normalize_writer(writer: str) -> str:
    return WRITER_ALIASES.get(writer, writer)


def _run_llm_qg(
    *,
    plan: Mapping[str, Any],
    plan_content: str,
    module_dir: Path,
    writer: str,
    reviewer_override: str | None = None,
    wiki_manifest: str | Mapping[str, Any] | None = None,
    implementation_map: Mapping[str, Any] | None = None,
    stdout_silence_timeout: int | None = None,
) -> dict[str, Any]:
    from scripts.agent_runtime.runner import invoke

    reviewer = _reviewer_for_writer(writer, reviewer_override)
    defaults = linear_pipeline.REVIEWER_DEFAULTS[reviewer]

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
        )
        (module_dir / f"llm-qg-{dim}-prompt.md").write_text(prompt, encoding="utf-8")
        result = invoke(
            agent_name,
            prompt,
            mode="read-only",
            cwd=module_dir,
            model=defaults["model"],
            task_id=f"linear-v7-qg-{plan['slug']}-{dim}",
            entrypoint="dispatch",
            effort=defaults["effort"],
            tool_config={"output_format": "stream-json"},
            stdout_silence_timeout=stdout_silence_timeout,
        )
        response = str(getattr(result, "response", "") or "")
        # Persist raw reviewer response BEFORE parse so #M-10 forensic
        # continuity holds when the parser raises (build #10, 2026-05-21
        # exposed prose-wrapped JSON shape with no saved artifact).
        (module_dir / f"llm-qg-{dim}-response.raw.md").write_text(
            response,
            encoding="utf-8",
        )
        report[dim] = linear_pipeline.parse_review_response(response, dim)

    return linear_pipeline.aggregate_llm_review(report, str(plan["level"]))


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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = parse_args(raw_argv)
    if args.worktree is not None:
        return _run_in_worktree(args, raw_argv)
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
        data = _read_json(module_dir / "llm_qg.json")
        if not isinstance(data, Mapping):
            return False
        aggregate = data.get("aggregate")
        if not isinstance(aggregate, Mapping):
            return False
        terminal_verdict = aggregate.get("terminal_verdict", aggregate.get("verdict", ""))
        return str(terminal_verdict).upper() == "PASS"
    return False


def _run(args: argparse.Namespace) -> int:
    level = args.level.lower()
    slug = args.slug
    writer = _normalize_writer(args.writer)
    reviewer_override = _normalize_writer(args.reviewer) if args.reviewer else None
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
            tracker.emit("phase_resumed", phase=phase, level=level, slug=slug)
        else:
            if resume_enabled:
                force_rerun = True
            impl_map = seed_implementation_map(wiki_manifest_data, plan=plan)
            write_implementation_map(impl_map, impl_map_path)
            tracker.emit(
                "implementation_map_seeded",
                slug=slug,
                entry_count=len(impl_map["entries"]),
                path=str(impl_map_path),
            )
            prompt = _writer_prompt(
                plan=plan,
                plan_content=plan_content,
                knowledge_packet=knowledge_packet,
                wiki_manifest=wiki_manifest,
                implementation_map=impl_map,
                writer=writer,
            )
            # gemini-tools must load .gemini/settings.json from repo root;
            # module_dir cwd would leave its MCP catalog empty. See
            # audit/gemini-tools-review-2026-05-09/REPORT.html E5/E6.
            # grok-tools gets MCP from ~/.hermes/config.yaml and can run from
            # the module directory like claude-tools/codex-tools.
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
        timeout_agent = _reviewer_for_writer(writer, reviewer_override)
        started_at = time.monotonic()
        if (
            resume_enabled
            and not force_rerun
            and _phase_artifact_passes(module_dir, "llm_qg")
        ):
            llm_qg = _read_json(module_dir / "llm_qg.json")
            tracker.emit("phase_resumed", phase=phase, level=level, slug=slug)
        else:
            if resume_enabled:
                force_rerun = True
            llm_qg = _run_llm_qg(
                plan=plan,
                plan_content=plan_content,
                module_dir=module_dir,
                writer=writer,
                reviewer_override=reviewer_override,
                wiki_manifest=wiki_manifest,
                implementation_map=impl_map,
                stdout_silence_timeout=args.writer_timeout,
            )
            linear_pipeline.write_json(module_dir / "llm_qg.json", llm_qg)
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
                if dim in LLM_QG_TERMINAL_DIMS
            ]
            raise linear_pipeline.LinearPipelineError(
                f"LLM QG terminal verdict was {terminal_verdict} "
                f"(failing terminal dims: {failing_terminal_dims})"
            )

        phase = "mdx"
        _phase_started(archive, phase)
        started_at = time.monotonic()
        # MDX is the BUILT artifact and goes where Starlight reads it. Source
        # artifacts (.md, *.yaml) stay in curriculum/ as authoring source. When
        # --out is set (test/sandbox builds), MDX colocates with the artifact
        # dump so the test stays self-contained.
        if args.out is None:
            starlight_dir = (
                PROJECT_ROOT
                / "starlight"
                / "src"
                / "content"
                / "docs"
                / level.lower()
            )
            starlight_dir.mkdir(parents=True, exist_ok=True)
            mdx_path = starlight_dir / f"{slug}.mdx"
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
