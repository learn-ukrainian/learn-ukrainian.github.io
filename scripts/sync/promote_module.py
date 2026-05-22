#!/usr/bin/env python3
"""Promote V7 build-branch artifacts into the canonical curriculum tree."""

from __future__ import annotations

import argparse
import contextlib
import difflib
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_ROOT = Path("curriculum") / "l2-uk-en"
DOCS_ROOT = Path("starlight") / "src" / "content" / "docs"

LESSON_SOURCE_FILES = frozenset(
    {
        "module.md",
        "activities.yaml",
        "vocabulary.yaml",
        "resources.yaml",
    }
)
FORENSICS_FILES = frozenset(
    {
        "writer_prompt.md",
        "writer_output.raw.md",
        "hermes.write.jsonl",
        "writer_tool_calls.json",
        "python_qg.json",
        "llm_qg.json",
        "knowledge_packet.md",
        "implementation_map.json",
    }
)

_BUILD_BRANCH_RE = re.compile(r"^(?:refs/heads/|origin/)?build/(?P<level>[^/]+)/(?P<slug>.+)-(?P<stamp>\d{8}-\d{6})$")
_WORKTREE_NAME_RE = re.compile(r"^(?P<level>[^-]+)-(?P<slug>.+)-(?P<stamp>\d{8}-\d{6})$")


@dataclass(frozen=True)
class SourceSpec:
    build_ref: str
    level: str
    slug: str
    worktree: Path | None = None


@dataclass(frozen=True)
class SourceFile:
    source_rel: Path
    dest_rel: Path
    content: bytes


def _sanitized_git_env() -> dict[str, str]:
    """Drop ambient GIT_* / PRE_COMMIT* vars so `-C <repo_root>` resolves the
    target repo's context cleanly even when this script is invoked from
    inside a pre-commit hook or a parent git process that has set GIT_DIR /
    GIT_INDEX_FILE / etc."""
    return {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PRE_COMMIT"))}


def _run_git(repo_root: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=check,
        capture_output=True,
        env=_sanitized_git_env(),
    )


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_build_branch(ref: str) -> tuple[str, str, str] | None:
    match = _BUILD_BRANCH_RE.match(ref)
    if match is None:
        return None
    return match.group("level").lower(), match.group("slug"), match.group("stamp")


def _parse_worktree_name(path: Path) -> tuple[str, str, str] | None:
    match = _WORKTREE_NAME_RE.match(path.name)
    if match is None:
        return None
    return match.group("level").lower(), match.group("slug"), match.group("stamp")


def _write_atomically(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_name = ""
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
            tmp_name = tmp.name
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, path)
    finally:
        if tmp_name:
            with contextlib.suppress(FileNotFoundError):
                Path(tmp_name).unlink()


def _source_rel_for_lesson(level: str, slug: str, filename: str) -> Path:
    return CURRICULUM_ROOT / level / slug / filename


def _build_rel_for_mdx(level: str, slug: str) -> Path:
    """Path where `assemble_mdx` writes the freshly-built MDX inside the build branch.

    The build is the SOURCE of truth for the rendered MDX content. Reading from
    DOCS_ROOT in the build branch instead would silently pick up whatever stale
    Starlight-tree MDX happened to be there from a prior PR, which is exactly
    how the m20 (a1/my-morning) revert (2026-05-23) shipped a broken module —
    the build wrote a fresh MDX to `curriculum/.../{slug}.mdx`, but the promote
    read DOCS_ROOT, found an unchanged stale exemplar, and the diff was empty.
    """
    return CURRICULUM_ROOT / level / slug / f"{slug}.mdx"


def _dest_rel_for_mdx(level: str, slug: str) -> Path:
    """Path Starlight reads to render the lesson page (deploy target)."""
    return DOCS_ROOT / level / f"{slug}.mdx"


def _read_build_file(repo_root: Path, source: SourceSpec, source_rel: Path) -> bytes | None:
    if source.build_ref:
        proc = _run_git(repo_root, ["show", f"{source.build_ref}:{source_rel.as_posix()}"], check=False)
        if proc.returncode == 0:
            return proc.stdout

    if source.worktree is None:
        return None

    disk_path = source.worktree / source_rel
    try:
        return disk_path.read_bytes()
    except FileNotFoundError:
        return None


def _resolve_latest_branch(repo_root: Path, level: str, slug: str) -> str:
    pattern = f"refs/heads/build/{level}/{slug}-*"
    proc = _run_git(
        repo_root,
        ["for-each-ref", "--sort=-creatordate", pattern, "--format=%(refname:short)"],
    )
    refs = [line.strip() for line in _decode(proc.stdout).splitlines() if line.strip()]
    if not refs:
        raise ValueError(f"no build branches match build/{level}/{slug}-*")

    def sort_key(ref: str) -> tuple[str, str]:
        parsed = _parse_build_branch(ref)
        return ((parsed[2] if parsed is not None else ""), ref)

    return max(refs, key=sort_key)


def _branch_for_worktree(worktree: Path) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(worktree), "rev-parse", "--abbrev-ref", "HEAD"],
        check=False,
        capture_output=True,
        env=_sanitized_git_env(),
    )
    if proc.returncode != 0:
        return None
    branch = _decode(proc.stdout).strip()
    return branch if branch and branch != "HEAD" else None


def _resolve_source(args: argparse.Namespace, repo_root: Path) -> SourceSpec:
    if args.latest:
        if not args.level or not args.slug:
            raise ValueError("--latest requires --level and --slug")
        level = args.level.lower()
        build_ref = _resolve_latest_branch(repo_root, level, args.slug)
        return SourceSpec(build_ref=build_ref, level=level, slug=args.slug)

    if args.build_branch:
        parsed = _parse_build_branch(args.build_branch)
        if parsed is None:
            if not args.level or not args.slug:
                raise ValueError("--build-branch must look like build/<level>/<slug>-<YYYYMMDD-HHMMSS>")
            return SourceSpec(build_ref=args.build_branch, level=args.level.lower(), slug=args.slug)
        level, slug, _stamp = parsed
        return SourceSpec(build_ref=args.build_branch, level=level, slug=slug)

    worktree = Path(args.worktree).expanduser().resolve()
    branch = _branch_for_worktree(worktree)
    parsed = _parse_build_branch(branch or "") if branch else None
    if parsed is None:
        parsed = _parse_worktree_name(worktree)
    if parsed is None:
        if not args.level or not args.slug:
            raise ValueError("could not infer level/slug from worktree; pass --level and --slug")
        level, slug = args.level.lower(), args.slug
    else:
        level, slug, _stamp = parsed
    return SourceSpec(build_ref=branch or "", level=level, slug=slug, worktree=worktree)


def _collect_source_files(repo_root: Path, source: SourceSpec) -> tuple[list[SourceFile], list[Path], list[Path]]:
    files: list[SourceFile] = []
    missing_required: list[Path] = []
    missing_optional: list[Path] = []

    for filename in sorted(LESSON_SOURCE_FILES):
        source_rel = _source_rel_for_lesson(source.level, source.slug, filename)
        content = _read_build_file(repo_root, source, source_rel)
        if content is None:
            missing_required.append(source_rel)
        else:
            files.append(SourceFile(source_rel=source_rel, dest_rel=source_rel, content=content))

    mdx_source_rel = _build_rel_for_mdx(source.level, source.slug)
    mdx_dest_rel = _dest_rel_for_mdx(source.level, source.slug)
    mdx = _read_build_file(repo_root, source, mdx_source_rel)
    if mdx is None:
        missing_required.append(mdx_source_rel)
    else:
        files.append(SourceFile(source_rel=mdx_source_rel, dest_rel=mdx_dest_rel, content=mdx))

    for filename in sorted(FORENSICS_FILES):
        source_rel = _source_rel_for_lesson(source.level, source.slug, filename)
        content = _read_build_file(repo_root, source, source_rel)
        if content is None:
            missing_optional.append(source_rel)
        else:
            files.append(SourceFile(source_rel=source_rel, dest_rel=source_rel, content=content))

    return files, missing_required, missing_optional


def _diff_summary(path: Path, current: bytes, wanted: bytes) -> str:
    current_text = _decode(current).splitlines(keepends=True)
    wanted_text = _decode(wanted).splitlines(keepends=True)
    diff = difflib.unified_diff(
        current_text,
        wanted_text,
        fromfile=f"{path.as_posix()} (current)",
        tofile=f"{path.as_posix()} (build)",
        n=3,
    )
    lines = list(diff)
    if lines:
        return "".join(lines[:80])
    return (
        f"{path.as_posix()}: binary or encoding-only difference "
        f"current={_sha256(current)} build={_sha256(wanted)}\n"
    )


def _classify_destination(repo_root: Path, source: SourceSpec, files: list[SourceFile]) -> tuple[bool, list[str]]:
    required_dest_rels = {
        _source_rel_for_lesson(source.level, source.slug, filename)
        for filename in LESSON_SOURCE_FILES
    }
    required_dest_rels.add(_dest_rel_for_mdx(source.level, source.slug))

    required_by_dest = {item.dest_rel: item for item in files if item.dest_rel in required_dest_rels}
    any_required_exists = False
    mismatches: list[str] = []

    for dest_rel, item in sorted(required_by_dest.items(), key=lambda pair: pair[0].as_posix()):
        dest = repo_root / dest_rel
        if not dest.exists():
            mismatches.append(f"{dest_rel.as_posix()}: missing in current tree")
            continue
        any_required_exists = True
        current = dest.read_bytes()
        if current != item.content:
            mismatches.append(_diff_summary(dest_rel, current, item.content))

    return any_required_exists, mismatches


def _dry_run(repo_root: Path, files: list[SourceFile], missing_optional: list[Path]) -> None:
    print("DRY-RUN promote plan:")
    for item in files:
        dest = repo_root / item.dest_rel
        if dest.exists():
            current = dest.read_bytes()
            action = "unchanged" if current == item.content else "update"
        else:
            action = "create"
        print(f"  {action} {item.dest_rel.as_posix()}")
        if action == "update":
            print(_diff_summary(item.dest_rel, current, item.content), end="")
    for rel in missing_optional:
        print(f"  optional missing {rel.as_posix()}")


def _commit(repo_root: Path, rels: list[Path], message: str) -> None:
    rel_args = [rel.as_posix() for rel in rels]
    _run_git(repo_root, ["add", "--", *rel_args])
    staged = _run_git(repo_root, ["diff", "--cached", "--quiet"], check=False)
    if staged.returncode == 0:
        print("OK no staged changes")
        return
    _run_git(repo_root, ["commit", "-m", message])


def promote(args: argparse.Namespace, *, repo_root: Path = ROOT) -> int:
    repo_root = repo_root.resolve()
    try:
        source = _resolve_source(args, repo_root)
        files, missing_required, missing_optional = _collect_source_files(repo_root, source)
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1

    for rel in missing_optional:
        print(f"optional missing {rel.as_posix()}")

    if missing_required:
        print("ERROR missing required build artifacts:", file=sys.stderr)
        for rel in missing_required:
            print(f"  {rel.as_posix()}", file=sys.stderr)
        return 2

    if args.dry_run:
        _dry_run(repo_root, files, missing_optional)
        return 0

    any_required_exists, mismatches = _classify_destination(repo_root, source, files)
    if any_required_exists and mismatches and not args.force:
        print("ERROR partial or conflicting promotion detected; use --force to overwrite", file=sys.stderr)
        for mismatch in mismatches:
            print(mismatch, file=sys.stderr, end="" if mismatch.endswith("\n") else "\n")
        return 1

    if any_required_exists and not mismatches:
        print("OK already-promoted")
        return 0

    written: list[Path] = []
    for item in files:
        dest = repo_root / item.dest_rel
        if dest.exists() and dest.read_bytes() == item.content:
            continue
        _write_atomically(dest, item.content)
        written.append(item.dest_rel)
        print(f"wrote {item.dest_rel.as_posix()}")

    if not written:
        print("OK no changes")
        return 0

    if args.no_commit:
        print("OK promoted without commit (--no-commit)")
        return 0

    message = args.message or f"feat(content): promote {source.level}/{source.slug} from {source.build_ref}"
    try:
        _commit(repo_root, written, message)
    except subprocess.CalledProcessError as exc:
        print(_decode(exc.stderr), file=sys.stderr, end="")
        return exc.returncode or 1
    print("OK promoted and committed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--build-branch", help="Build branch ref, e.g. build/a1/my-morning-20260520-123456")
    source.add_argument("--worktree", help="Build worktree directory to read from")
    source.add_argument("--latest", action="store_true", help="Use most recent build/<level>/<slug>-* branch")
    parser.add_argument("--level", help="Level for --latest, or fallback when a ref cannot be parsed")
    parser.add_argument("--slug", help="Slug for --latest, or fallback when a ref cannot be parsed")
    parser.add_argument("--dry-run", action="store_true", help="Show planned writes and diffs without writing")
    parser.add_argument("--no-commit", action="store_true", help="Write files but skip git commit")
    parser.add_argument("--message", help="Override the default commit message")
    parser.add_argument("--force", action="store_true", help="Overwrite conflicting in-tree lesson source")
    return parser


def main(argv: list[str] | None = None, *, repo_root: Path = ROOT) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return promote(args, repo_root=repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
