"""Fail-closed PR-tier classification; stdlib only for the Changes job."""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.parse
from collections import defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path, PurePosixPath

from scripts.ci.frontend_change_scope import load_denominator, path_in_denominator

# Content CI owns these trees. Other exemptions are Markdown in known docs trees.
CONTENT_PREFIXES = ("wiki/", "curriculum/")
DOC_PREFIXES = (
    "docs/", "agents_extensions/shared/skills/", ".claude/", ".codex/", ".agent/",
)

SAFETY_NET = "tests/test_ci_shard_partition.py"
SELECTED_CANDIDATE_CEILING = 80

_TEST_FILE_RE = re.compile(r"(?:^|/)(?:test_[^/]+\.py|[^/]+_test\.py)$")


def is_docs(path: str) -> bool:
    if path.startswith(CONTENT_PREFIXES):
        return True
    return path.endswith(".md") and ("/" not in path or path.startswith(DOC_PREFIXES))


def _norm(path: str) -> str:
    return path.replace("\\", "/")


def is_test_file(path: str) -> bool:
    """True for tests/**/test_*.py or tests/**/*_test.py."""
    p = _norm(path)
    return p.startswith("tests/") and bool(_TEST_FILE_RE.search(p))


def hits_shared_root_denylist(path: str) -> bool:
    """Any hit forces full; never selected."""
    p = _norm(path)
    name = PurePosixPath(p).name
    if p.startswith((".github/", "scripts/ci/", "scripts/config/", "scripts/build/")):
        return True
    if p == "scripts/__init__.py":
        return True
    if p.startswith("scripts/audit/") and p.endswith(".json") and p.count("/") == 2:
        return True
    if name == "conftest.py" or p.endswith("/conftest.py"):
        return True
    if p in {"pyproject.toml", "uv.lock", "requirements.lock", ".python-version"}:
        return True
    if name.startswith("requirements") and name.endswith(".txt"):
        return True
    if p.startswith(("packages/", "schemas/", "site/", "curriculum/")):
        return True
    return p == "docs/lesson-schema.yaml" or (p.startswith("docs/") and p.endswith(".yaml"))


def git_tree_paths(repo_root: Path | None = None) -> set[str]:
    """List paths at HEAD via git object tree (sparse-checkout safe)."""
    command = ["git", "ls-tree", "-r", "--name-only", "HEAD"]
    raw = subprocess.check_output(
        command,
        text=True,
        timeout=120,
        cwd=str(repo_root) if repo_root is not None else None,
    )
    return {line for line in raw.splitlines() if line}


def _stem_map_tests(stem: str, tree: Iterable[str]) -> list[str]:
    """Map scripts/.../FOO.py to tests/**/test_{FOO,foo}.py and test_{FOO,foo}_*.py."""
    variants = {stem, stem.lower()}
    out: list[str] = []
    for path in tree:
        if not path.startswith("tests/") or not path.endswith(".py"):
            continue
        name = PurePosixPath(path).name
        for variant in variants:
            if not variant:
                continue
            if name == f"test_{variant}.py" or (
                name.startswith(f"test_{variant}_") and name.endswith(".py")
            ):
                out.append(path)
                break
    return sorted(set(out))


def _script_stems_in_tree(tree: Iterable[str]) -> dict[str, list[str]]:
    by_stem: dict[str, list[str]] = defaultdict(list)
    for path in tree:
        if path.startswith("scripts/") and path.endswith(".py"):
            by_stem[PurePosixPath(path).stem].append(path)
    return by_stem


def build_selected_candidates(paths: Sequence[str], tree: Iterable[str]) -> list[str] | None:
    """Return sorted candidates, or None when classification must upgrade to full."""
    tree_set = set(tree)
    stems = _script_stems_in_tree(tree_set)
    candidates: set[str] = set()
    script_changed = False

    for path in paths:
        p = _norm(path)
        if hits_shared_root_denylist(p):
            return None
        if p.startswith("tests/"):
            if not is_test_file(p):
                return None
            if p not in tree_set:
                # Deleted or rename-away old matching test path → full.
                return None
            candidates.add(p)
            continue
        if p.startswith("scripts/"):
            if not p.endswith(".py"):
                return None
            script_changed = True
            stem = PurePosixPath(p).stem
            if len(stems.get(stem, [])) > 1:
                return None
            mapped = _stem_map_tests(stem, tree_set)
            if not mapped:
                # Unmapped script — safety-net does not exempt.
                return None
            candidates.update(mapped)
            continue
        return None

    if script_changed:
        if SAFETY_NET not in tree_set:
            return None
        candidates.add(SAFETY_NET)

    if not candidates or len(candidates) >= SELECTED_CANDIDATE_CEILING:
        return None
    return sorted(candidates)


def _full(shard_count: int, *, frontend: str = "true") -> dict[str, str]:
    return {
        "docs_only": "false",
        "frontend": frontend,
        "shards": json.dumps(list(range(1, shard_count + 1))),
        "pytest_mode": "full",
        "shard_count": str(shard_count),
        "pytest_candidates": "[]",
    }


def _docs() -> dict[str, str]:
    return {
        "docs_only": "true",
        "frontend": "false",
        "shards": "[1]",
        "pytest_mode": "docs",
        "shard_count": "1",
        "pytest_candidates": "[]",
    }


def _selected(candidates: Sequence[str]) -> dict[str, str]:
    return {
        "docs_only": "false",
        "frontend": "false",
        "shards": "[1]",
        "pytest_mode": "selected",
        "shard_count": "1",
        "pytest_candidates": json.dumps(sorted(candidates), separators=(",", ":")),
    }


def classify(
    paths: list[str],
    *,
    event: str,
    labels: list[str],
    shard_count: int,
    denominator: list[str],
    tree_paths: Iterable[str] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    """Unknown paths run every pytest shard; only explicit docs may skip."""
    if shard_count < 1:
        raise ValueError("shard_count must be positive")

    # Non-PR / full-ci / empty / capped: force full including frontend (P1.1).
    if event != "pull_request" or "full-ci" in labels or not paths or len(paths) >= 300:
        return _full(shard_count)

    frontend = any(path_in_denominator(path, denominator) for path in paths)
    docs_only = all(is_docs(path) for path in paths) and not frontend
    if docs_only:
        return _docs()

    tree: set[str] | None
    if tree_paths is not None:
        tree = set(tree_paths)
    else:
        try:
            tree = git_tree_paths(repo_root or Path.cwd())
        except (OSError, subprocess.SubprocessError):
            return _full(shard_count, frontend="true" if frontend else "false")

    candidates = build_selected_candidates(paths, tree)
    if candidates is not None:
        return _selected(candidates)
    return _full(shard_count, frontend="true" if frontend else "false")


def compare_paths(base: str, head: str, repo: str) -> list[str]:
    """Keep rename sources and structured filenames; never split paths on newlines."""
    if not base or set(base) <= {"0"} or not head:
        raise ValueError("missing comparison SHA")
    spec = urllib.parse.quote(f"{base}...{head}", safe=".")
    # GitHub returns files only on the first page, capped at 300. No commit
    # pagination is needed; classify() treats reaching the file cap as full.
    raw = subprocess.check_output(
        ["gh", "api", f"repos/{repo}/compare/{spec}"], text=True, timeout=60,
    )
    files = json.loads(raw)["files"]
    if not isinstance(files, list):
        raise ValueError("invalid comparison files")
    paths = []
    for item in files:
        name = item["filename"]
        previous = item.get("previous_filename")
        if not isinstance(name, str) or not name:
            raise ValueError("invalid comparison filename")
        paths.append(name)
        if previous is not None:
            if not isinstance(previous, str) or not previous:
                raise ValueError("invalid previous filename")
            paths.append(previous)
    return paths


def main() -> None:
    shard_count = int(os.environ["PYTEST_SHARD_COUNT"])
    event = os.environ.get("EVENT_NAME", "")
    paths: list[str] = []
    labels: list[str] = []
    denominator: list[str] = []
    tree_paths: set[str] | None = None
    try:
        payload = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        if event == "pull_request":
            labels = [label["name"] for label in payload["pull_request"]["labels"]]
            if "full-ci" not in labels:
                denominator = load_denominator()["paths"]
                paths = compare_paths(
                    os.environ.get("BASE", ""),
                    os.environ.get("HEAD", ""),
                    os.environ["REPO"],
                )
                tree_paths = git_tree_paths(Path.cwd())
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        # Missing/malformed event, denominator, API response, or git tree → full.
        paths = []
        tree_paths = None
    result = classify(
        paths,
        event=event,
        labels=labels,
        shard_count=shard_count,
        denominator=denominator,
        tree_paths=tree_paths,
        repo_root=Path.cwd(),
    )
    print(f"files={len(paths)} " + " ".join(f"{key}={value}" for key, value in result.items()))
    if output := os.environ.get("GITHUB_OUTPUT"):
        with Path(output).open("a", encoding="utf-8") as handle:
            handle.write("".join(f"{key}={value}\n" for key, value in result.items()))


if __name__ == "__main__":
    main()
