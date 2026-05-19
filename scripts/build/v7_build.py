#!/usr/bin/env python3
"""CLI wrapper for the V7 linear module pipeline."""

from __future__ import annotations

import argparse
import json
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
from scripts.build import linear_pipeline
from scripts.build.phases.implementation_map import (
    seed_implementation_map,
    write_implementation_map,
)
from scripts.common.thresholds import QG_DIMS

DEFAULT_WRITER_TIMEOUT_S = 1800
FETCH_TIMEOUT_S = 30
WORKTREE_AUTO = "auto"
WRITER_ALIASES = {
    "claude": "claude-tools",
    "gemini": "gemini-tools",
    "codex": "codex-tools",
    "grok": "grok-tools",
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


def _run_in_worktree(args: argparse.Namespace, raw_argv: list[str]) -> int:
    level = args.level.lower()
    slug = args.slug
    try:
        worktree = _setup_worktree(level, slug, args.worktree)
    except WorktreeSetupError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code

    result = "failed"
    child_argv = _strip_worktree_args(raw_argv)
    command = [
        str(_python_executable(worktree.repo_root)),
        "scripts/build/v7_build.py",
        *child_argv,
    ]
    try:
        proc = subprocess.run(command, cwd=worktree.path, check=False)
        exit_code = proc.returncode
        if exit_code == 0:
            result = "success"
    except OSError as exc:
        print(f"v7_build worktree child failed to start: {exc}", file=sys.stderr)
        exit_code = 1
    finally:
        _print_worktree_summary(worktree, level=level, slug=slug, result=result)
    return exit_code


def _phase_done(
    phase: str,
    started_at: float,
    *,
    level: str,
    slug: str,
    event_sink: Callable[..., None] = emit_event,
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


def _generated_content(module_dir: Path) -> str:
    parts = []
    for artifact in linear_pipeline.WRITER_ARTIFACTS:
        path = module_dir / artifact
        parts.append(f"## {artifact}\n\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(parts)


def _reviewer_for_writer(writer: str) -> str:
    if writer == "claude-tools":
        return "gemini-tools"
    if writer == "grok-tools":
        return "claude-tools"
    return "claude-tools"


def _normalize_writer(writer: str) -> str:
    return WRITER_ALIASES.get(writer, writer)


def _run_llm_qg(
    *,
    plan: Mapping[str, Any],
    plan_content: str,
    module_dir: Path,
    writer: str,
    stdout_silence_timeout: int | None = None,
) -> dict[str, Any]:
    from scripts.agent_runtime.runner import invoke

    reviewer = _reviewer_for_writer(writer)
    defaults = linear_pipeline.WRITER_DEFAULTS[reviewer]
    agent_name = reviewer.split("-", 1)[0]
    generated_content = _generated_content(module_dir)
    report: dict[str, Any] = {}

    for dim in QG_DIMS:
        prompt = linear_pipeline.render_review_prompt(
            plan,
            plan_content,
            generated_content,
            dim,
        )
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
        report[dim] = linear_pipeline.parse_review_response(response, dim)

    return linear_pipeline.aggregate_llm_review(report, str(plan["level"]))


def _run_wiki_coverage_review(
    *,
    plan: Mapping[str, Any],
    plan_content: str,
    module_dir: Path,
    writer: str,
    wiki_manifest: str | Mapping[str, Any],
    wiki_coverage_gate: Mapping[str, Any],
    stdout_silence_timeout: int | None = None,
) -> dict[str, Any]:
    from scripts.agent_runtime.runner import invoke

    reviewer = _reviewer_for_writer(writer)
    defaults = linear_pipeline.REVIEWER_DEFAULTS[reviewer]
    agent_name = reviewer.split("-", 1)[0]
    generated_content = _generated_content(module_dir)
    prompt = linear_pipeline.render_wiki_coverage_review_prompt(
        plan,
        plan_content,
        generated_content,
        wiki_manifest,
        wiki_coverage_gate,
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
    return linear_pipeline.parse_wiki_coverage_review_response(response)


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description=(
            "Build one V7 curriculum module through scripts.build.linear_pipeline.\n"
            "Use for single-module V7 reboot builds; do not use for V6 legacy "
            "batch, resume, rewrite, or regeneration workflows."
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
            "(default: claude-tools; claude/gemini/codex/grok aliases normalize to "
            "claude-tools/gemini-tools/codex-tools/grok-tools)."
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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = parse_args(raw_argv)
    if args.worktree is not None:
        return _run_in_worktree(args, raw_argv)
    telemetry_out = _resolve_project_path(args.telemetry_out)
    with linear_pipeline.telemetry_event_sink(telemetry_out):
        return _run(args)


def _run(args: argparse.Namespace) -> int:
    level = args.level.lower()
    slug = args.slug
    writer = _normalize_writer(args.writer)
    module_started_at = time.monotonic()
    phase = "start"
    timeout_agent = writer
    tracker = LastEventTracker()

    tracker.emit("module_start", level=level, slug=slug)

    try:
        phase = "plan"
        started_at = time.monotonic()
        plan_path = linear_pipeline.plan_path_for(level, slug)
        plan_content = plan_path.read_text(encoding="utf-8")
        plan = linear_pipeline.load_plan(plan_path)
        linear_pipeline.validate_plan(plan)
        _phase_done(phase, started_at, level=level, slug=slug, event_sink=tracker.emit)

        phase = "knowledge_packet"
        started_at = time.monotonic()
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
        _phase_done(phase, started_at, level=level, slug=slug, event_sink=tracker.emit)

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

        module_dir = _resolve_output_dir(args.out, level, slug)

        phase = "writer"
        timeout_agent = writer
        started_at = time.monotonic()
        module_dir.mkdir(parents=True, exist_ok=True)
        impl_map = seed_implementation_map(wiki_manifest_data, plan=plan)
        impl_map_path = module_dir / "implementation_map.json"
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
        )

        phase = "python_qg"
        started_at = time.monotonic()
        python_qg = linear_pipeline.run_python_qg_with_corrections(
            module_dir,
            plan_path,
            writer=writer,
        )
        linear_pipeline.write_json(module_dir / "python_qg.json", python_qg)
        _phase_done(phase, started_at, level=level, slug=slug, event_sink=tracker.emit)
        gates = python_qg.get("gates")
        if not isinstance(gates, Mapping) or gates.get("passed") is not True:
            raise linear_pipeline.LinearPipelineError(
                "Python QG failed after ADR-008 correction paths"
            )

        phase = "wiki_coverage_gate"
        started_at = time.monotonic()
        wiki_coverage_gate = linear_pipeline.run_wiki_coverage_with_corrections(
            plan=plan,
            manifest=wiki_manifest,
            writer_output=writer_output,
            module_dir=module_dir,
            level=level,
            event_sink=tracker.emit,
        )
        linear_pipeline.write_json(module_dir / "wiki_coverage_gate.json", wiki_coverage_gate)
        _phase_done(phase, started_at, level=level, slug=slug, event_sink=tracker.emit)
        if wiki_coverage_gate.get("passed") is not True:
            raise linear_pipeline.LinearPipelineError(
                "Wiki coverage gate failed after batched + narrow correction passes"
            )

        phase = "wiki_coverage_review"
        timeout_agent = _reviewer_for_writer(writer)
        started_at = time.monotonic()
        wiki_coverage_review = _run_wiki_coverage_review(
            plan=plan,
            plan_content=plan_content,
            module_dir=module_dir,
            writer=writer,
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
        _phase_done(phase, started_at, level=level, slug=slug, event_sink=tracker.emit)
        if wiki_coverage_review["overall_verdict"] == "FAIL":
            raise linear_pipeline.LinearPipelineError("Wiki coverage review failed")

        phase = "llm_qg"
        timeout_agent = _reviewer_for_writer(writer)
        started_at = time.monotonic()
        llm_qg = _run_llm_qg(
            plan=plan,
            plan_content=plan_content,
            module_dir=module_dir,
            writer=writer,
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
        _phase_done(phase, started_at, level=level, slug=slug, event_sink=tracker.emit)
        if aggregate["verdict"] != "PASS":
            raise linear_pipeline.LinearPipelineError(
                f"LLM QG verdict was {aggregate['verdict']}"
            )

        phase = "mdx"
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
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
