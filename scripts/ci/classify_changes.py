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

# Events classified by changed paths. Everything else (schedule, dispatch,
# unknown) forces the full tier without touching the compare API.
_PATH_CLASSIFIED_EVENTS = frozenset({"pull_request", "merge_group"})
_FULL_CI_LABEL = "full-ci"
# Merge-queue group branch, e.g. refs/heads/gh-readonly-queue/main/pr-8656-<sha>.
# GitHub documents the `gh-readonly-queue/{base_branch}` prefix (docs.github.com
# managing-a-merge-queue); the `pr-<number>-<parent sha>` tail is the observed
# live format, where the parent SHA is the group ahead in the queue (or the base
# branch head). Anything else fails closed to full.
_QUEUE_REF = re.compile(
    r"^refs/heads/gh-readonly-queue/(?P<base>.+)/pr-(?P<number>[1-9][0-9]*)-(?P<parent>[0-9a-f]{40})$"
)
_MAX_QUEUE_DEPTH = 100

# Content class (#8399): learner-facing content with no imported code surface.
# Every changed path must live under one of these roots for the class to apply.
CONTENT_CLASS_PREFIXES = (
    "curriculum/l2-uk-en/",
    "curriculum/l2-uk-direct/",
    "site/src/content/docs/",
    "wiki/",
)

# Track roots whose top level also carries code-imported manifests/data.
_CONTENT_TRACK_ROOTS = ("curriculum/l2-uk-en/", "curriculum/l2-uk-direct/")

# Data/code extensions that are never prose content anywhere under the roots.
_CONTENT_CODE_SUFFIXES = (".py", ".db", ".sqlite")

# Exact code-imported files inside the content roots (#8399 D3). Each forces
# the full tier on both events and is excluded from the docs exemption; the
# importing modules are listed in is_code_load_bearing_content's docstring.
_CONTENT_CODE_PATHS = frozenset({
    "curriculum/l2-uk-direct/manifest.yaml",
    "curriculum/l2-uk-direct/bolshakova-letter-order.yaml",
    "curriculum/l2-uk-en/module-mapping.json",
    "curriculum/l2-uk-en/vocabulary.db",
})

DOC_PREFIXES = (
    "docs/", "agents_extensions/shared/skills/", ".claude/", ".codex/", ".agent/",
)

SAFETY_NET = "tests/test_ci_shard_partition.py"
SELECTED_CANDIDATE_CEILING = 80

_TEST_FILE_RE = re.compile(r"(?:^|/)(?:test_[^/]+\.py|[^/]+_test\.py)$")


def is_code_load_bearing_content(path: str) -> bool:
    """True for code-imported files that live inside the content roots.

    Each of these forces the full tier on both pull_request and merge_group
    and is also excluded from the docs exemption (#8399 D3): neither the
    content lane nor the docs lane runs the code that imports them. Verified
    importers (``grep -rln`` over ``scripts/``):

    - ``curriculum/**/curriculum.yaml``: generated track manifest imported by
      scripts/level_config.py, scripts/pipeline/{config_tables,
      learner_state}.py, scripts/generate_mdx/*, scripts/sync/*,
      scripts/manifest_utils.py.
    - ``curriculum/l2-uk-direct/manifest.yaml``: imported by
      scripts/build/build_module_direct.py,
      scripts/generate_mdx/generate_mdx_direct.py,
      scripts/validate/validate_direct.py, scripts/api/agent_router.py,
      scripts/audit/layerb_qualify.py, scripts/audit/atlas_source_census.py.
    - ``curriculum/l2-uk-direct/bolshakova-letter-order.yaml``: imported by
      scripts/audit/atlas_source_census.py.
    - ``curriculum/l2-uk-en/module-mapping.json``: imported by
      scripts/legacy/typescript/{migrate-modules,merge-levels}.ts.
    - ``curriculum/l2-uk-en/vocabulary.db``: SQLite imported by
      scripts/vocab/*, scripts/practice/numeral_agreement_engine.py,
      scripts/audit/checks/vocabulary.py,
      scripts/lexicon/backfill_course_usage.py.
    - Any ``*.py`` / ``*.db`` / ``*.sqlite`` under the content roots, and any
      ``*.json`` at a track root: code/data surface by extension, even before
      a specific importer is named.

    Schemas live outside the roots (``schemas/``, ``docs/**/*.yaml``) and
    already miss the prefix check; everything else under the roots is gated
    by the Contracts job, Content CI, or the ``reads_content`` pytest lane,
    all of which still run for the content class.
    """
    p = _norm(path)
    if p.startswith("curriculum/") and PurePosixPath(p).name == "curriculum.yaml":
        return True
    if p in _CONTENT_CODE_PATHS:
        return True
    if not p.startswith(CONTENT_CLASS_PREFIXES):
        return False
    if p.endswith(_CONTENT_CODE_SUFFIXES):
        return True
    return any(
        p.startswith(root) and "/" not in p[len(root):] and p.endswith(".json")
        for root in _CONTENT_TRACK_ROOTS
    )


def is_docs(path: str) -> bool:
    if path.startswith(CONTENT_PREFIXES):
        # Code-imported files inside the content roots are never a docs skip
        # (#8399 D3): the docs lane runs no pytest at all, so they force full.
        return not is_code_load_bearing_content(path)
    return path.endswith(".md") and ("/" not in path or path.startswith(DOC_PREFIXES))


def is_content_class_path(path: str) -> bool:
    """True when a path is learner content with no code-imported surface.

    Exclusions inside the content roots — each forces the full tier on both
    events instead — are exactly is_code_load_bearing_content().
    """
    p = _norm(path)
    if not p.startswith(CONTENT_CLASS_PREFIXES):
        return False
    return not is_code_load_bearing_content(p)


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
    if name in {"conftest.py", "pytest.ini", "setup.cfg", "tox.ini"} or p.endswith("/conftest.py"):
        return True
    if p in {
        "pyproject.toml",
        "pytest.ini",
        "setup.cfg",
        "tox.ini",
        "uv.lock",
        "requirements.lock",
        ".python-version",
    }:
        return True
    if name.startswith("requirements") and name.endswith(".txt"):
        return True
    if p.startswith(("packages/", "schemas/", "site/", "curriculum/")):
        return True
    if p.startswith("tests/") and not is_test_file(p):
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
        "backend": "true",
        "shards": json.dumps(list(range(1, shard_count + 1))),
        "pytest_mode": "full",
        "shard_count": str(shard_count),
        "pytest_candidates": "[]",
    }


def _docs() -> dict[str, str]:
    return {
        "docs_only": "true",
        "frontend": "false",
        "backend": "true",
        "shards": "[1]",
        "pytest_mode": "docs",
        "shard_count": "1",
        "pytest_candidates": "[]",
    }


def _content() -> dict[str, str]:
    # docs_only=false keeps Ruff and Contracts on (cheap content gates).
    # Frontend is forced on: curriculum/wiki content renders through the site
    # build even though only site/ paths match the frontend denominator.
    return {
        "docs_only": "false",
        "frontend": "true",
        "backend": "true",
        "shards": "[1]",
        "pytest_mode": "content",
        "shard_count": "1",
        "pytest_candidates": "[]",
    }


def _selected(candidates: Sequence[str]) -> dict[str, str]:
    return {
        "docs_only": "false",
        "frontend": "false",
        "backend": "true",
        "shards": "[1]",
        "pytest_mode": "selected",
        "shard_count": "1",
        "pytest_candidates": json.dumps(sorted(candidates), separators=(",", ":")),
    }


# Site and activity-kit changes are exercised by the Frontend job (npm test).
# Learner docs under site/src/content/docs stay on the content lane instead.
_PURE_FRONTEND_PREFIXES = ("site/", "packages/activity-kit/")


def is_pure_frontend_path(path: str) -> bool:
    """True for a frontend tree path that is not a content-class learner page."""
    p = _norm(path)
    if is_content_class_path(p):
        return False
    return p.startswith(_PURE_FRONTEND_PREFIXES)


def _frontend_only() -> dict[str, str]:
    return {
        "docs_only": "false",
        "frontend": "true",
        "backend": "false",
        "shards": "[]",
        "pytest_mode": "frontend",
        "shard_count": "0",
        "pytest_candidates": "[]",
    }


# Early PR preflight (#8750): the pytest lanes whose shards run the repo_wide
# set (#8707) — every file in full, the explicit repo_wide leg in selected.
# Preflight repeats that set in its own job so a repo-wide failure reports
# minutes before the shards finish. The docs lane already runs it in one
# short shard; the content and frontend lanes do not run it at all, so a
# preflight there would change what the gate proves.
_PREFLIGHT_PYTEST_MODES = frozenset({"full", "selected"})


def preflight_for(event: str, tier: dict[str, str]) -> str:
    """The single "should preflight run" decision; ci.yml never re-derives it.

    True only on pull_request: merge_group, schedule and workflow_dispatch
    keep their tiers unchanged and run no preflight.
    """
    runs = (
        event == "pull_request"
        and tier["backend"] == "true"
        and tier["pytest_mode"] in _PREFLIGHT_PYTEST_MODES
    )
    return "true" if runs else "false"


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
    """Tier outputs plus the ``preflight`` flag derived from them."""
    tier = classify_tier(
        paths,
        event=event,
        labels=labels,
        shard_count=shard_count,
        denominator=denominator,
        tree_paths=tree_paths,
        repo_root=repo_root,
    )
    return {**tier, "preflight": preflight_for(event, tier)}


def classify_tier(
    paths: list[str],
    *,
    event: str,
    labels: list[str],
    shard_count: int,
    denominator: list[str],
    tree_paths: Iterable[str] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    """Unknown paths run every pytest shard; only explicit docs/content may skip."""
    if shard_count < 1:
        raise ValueError("shard_count must be positive")

    # Non-classified event / full-ci / empty / capped: force full (P1.1).
    if event not in _PATH_CLASSIFIED_EVENTS or has_full_ci(labels) or not paths or len(paths) >= 300:
        return _full(shard_count)

    frontend = any(path_in_denominator(path, denominator) for path in paths)
    # Operator 2026-09-21 (#8437): pull_request and merge_group use the same
    # path classes. A docs or backend-only change must not rebuild the site,
    # and a frontend-only change must not run the Python shards. The nightly
    # schedule and an unknown event still enter through the full return above.
    if all(is_pure_frontend_path(path) for path in paths):
        return _frontend_only()
    if all(is_content_class_path(path) for path in paths) and any(
        _norm(path).startswith("site/src/content/docs/") for path in paths
    ):
        # Learner pages under site/src/content/docs render through the site
        # and are read by the reads_content pytest lane (#8399). Curriculum
        # and wiki markdown that never touch those pages stay on the docs
        # lane, including on the merge queue (#8437).
        return _content()
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


def has_full_ci(labels: Iterable[str]) -> bool:
    """GitHub label names are case-insensitive, so `Full-CI` counts too."""
    return any(label.casefold() == _FULL_CI_LABEL for label in labels)


def current_pr_labels(repo: str, number: int) -> list[str]:
    """Current PR labels from the API, not the (possibly stale) event payload."""
    if number < 1:
        raise ValueError("invalid pull request number")
    raw = subprocess.check_output(
        ["gh", "api", f"repos/{repo}/pulls/{number}", "--jq", ".labels[].name"],
        text=True,
        timeout=60,
    )
    return [line for line in raw.splitlines() if line]


def queue_refs_by_sha(repo: str, base_branch: str) -> dict[str, str]:
    """Live merge-queue group refs for ``base_branch``, keyed by group head SHA.

    Two refs on one SHA make the chain walk ambiguous: keeping either would
    silently drop the other PR and its labels. Raise instead, so the caller
    fails closed to full.
    """
    prefix = urllib.parse.quote(f"heads/gh-readonly-queue/{base_branch}/")
    raw = subprocess.check_output(
        [
            "gh", "api", "--paginate", f"repos/{repo}/git/matching-refs/{prefix}",
            "--jq", '.[] | .object.sha + " " + .ref',
        ],
        text=True,
        timeout=60,
    )
    refs: dict[str, str] = {}
    for line in raw.splitlines():
        sha, _, ref = line.partition(" ")
        if not sha or not ref:
            raise ValueError("invalid matching-refs line")
        if sha in refs:
            raise ValueError(f"merge-queue refs {refs[sha]!r} and {ref!r} share {sha}")
        refs[sha] = ref
    return refs


def on_base_branch(repo: str, base_branch: str, sha: str) -> bool:
    """True when ``sha`` is the head of ``base_branch`` or one of its ancestors."""
    spec = urllib.parse.quote(f"{base_branch}...{sha}", safe="/.")
    raw = subprocess.check_output(
        ["gh", "api", f"repos/{repo}/compare/{spec}", "--jq", ".status"],
        text=True,
        timeout=60,
    )
    return raw.strip() in {"identical", "behind"}


def merge_group_pr_numbers(head_ref: str, base_sha: str, repo: str) -> list[int]:
    """Every PR in a merge group: the queue ref's PR plus each PR ahead of it.

    A group holds its own PR plus the PRs ahead of it in the queue, and its ref
    names only its own PR. GitHub sends ``merge_group.base_sha`` as the group's
    parent commit, which is the ref's trailing SHA: the head of the group ahead,
    or the base branch commit for the first group (live runs 35989980156 and
    35990749894). So ``base_sha`` cannot mark the end of the queue. Follow the
    parent chain through the live queue refs until it leaves the queue, then
    require that commit to be on the base branch. A malformed ref, a parent
    that differs from ``base_sha``, or a chain that ends off the base branch
    raises, and the caller fails closed to full.
    """
    match = _QUEUE_REF.match(head_ref)
    if match is None:
        raise ValueError(f"unrecognised merge-queue ref: {head_ref!r}")
    if match["parent"] != base_sha:
        raise ValueError(f"merge-queue ref parent {match['parent']} is not base_sha {base_sha!r}")
    base_branch = match["base"]
    numbers = [int(match["number"])]
    parent = match["parent"]
    refs = queue_refs_by_sha(repo, base_branch)
    while parent in refs:
        ahead = _QUEUE_REF.match(refs[parent])
        if (
            ahead is None
            or ahead["base"] != base_branch
            or int(ahead["number"]) in numbers
            or len(numbers) >= _MAX_QUEUE_DEPTH
        ):
            raise ValueError(f"cannot resolve merge-queue group ahead at {parent}")
        numbers.append(int(ahead["number"]))
        parent = ahead["parent"]
    # A group ahead that already merged is on the base branch, so its PR no
    # longer needs checking. A group ahead that left the queue unmerged is not,
    # and GitHub rebuilds this group anyway.
    if not on_base_branch(repo, base_branch, parent):
        raise ValueError(f"merge-queue chain ends at {parent}, which is not on {base_branch}")
    return numbers


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
        # Labels come from the API, not the event payload: a manual "Re-run
        # jobs" replays the original payload, and a merge_group payload has no
        # labels at all (#8505). Any lookup failure raises into the except
        # below and fails closed to full.
        if event == "pull_request":
            payload = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
            labels = current_pr_labels(os.environ["REPO"], payload["pull_request"]["number"])
        elif event == "merge_group":
            # full-ci on ANY PR in the group forces full in the queue run.
            for number in merge_group_pr_numbers(
                os.environ.get("HEAD_REF", ""), os.environ.get("BASE", ""), os.environ["REPO"],
            ):
                labels.extend(current_pr_labels(os.environ["REPO"], number))
        if event in _PATH_CLASSIFIED_EVENTS and not has_full_ci(labels):
            # pull_request and merge_group both classify by changed paths;
            # the workflow maps pull_request.base/head or merge_group
            # .base_sha/.head_sha into BASE/HEAD. For a merge group that is
            # this queue entry's own diff: base_sha is the head of the group
            # ahead, and each entry runs its own required CI (the ruleset's
            # ALLGREEN grouping). Any failure here leaves paths empty → fail
            # closed to full.
            denominator = load_denominator()["paths"]
            paths = compare_paths(
                os.environ.get("BASE", ""),
                os.environ.get("HEAD", ""),
                os.environ["REPO"],
            )
            tree_paths = git_tree_paths(Path.cwd())
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        # Missing/malformed event, labels, queue ref, denominator, API
        # response, or git tree → full.
        paths = []
        labels = [_FULL_CI_LABEL]
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
