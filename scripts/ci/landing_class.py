#!/usr/bin/env python3
"""Classify landing events for the two-tier CI workflow.

Fail-closed: empty path lists, unreadable git, unexpected errors, and any
path outside the allowlist yield ``full``. Only an exhaustive allowlist match
yields ``docs_skills``.

Allowlist (deny by omission):
  - ``agents_extensions/shared/skills/**``
  - ``docs/**/*.md``
  - repo-root ``*.md``

On a plain push to ``main``, ``mq_validated`` is emitted only when the exact
push SHA has one ``ci.yml`` merge-group run whose Gate, four Python jobs, and
four shard artifacts prove the pytest spine, and the run's queue base matches
the push parent. Any uncertainty returns ``full``. The proof is the run, not a
cache (#7173).

Stdlib only so GitHub runners can invoke it with system ``python3`` before
``actions/setup-python``. The CLI always exits 0 and always emits ``class=``
(``full`` on any failure) so CI Gate can require downstream jobs as success
via no-op paths, never via ``skipped`` (#5762).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

CLASS_DOCS_SKILLS = "docs_skills"
CLASS_FULL = "full"
CLASS_MQ_VALIDATED = "mq_validated"

SKILLS_PREFIX = "agents_extensions/shared/skills"
CI_WORKFLOW_PATH = ".github/workflows/ci.yml"
SELF_REFERENCE_PATHS = frozenset(
    {
        CI_WORKFLOW_PATH,
        "scripts/ci/landing_class.py",
        "scripts/ci/gate_required_results.py",
    }
)
PYTHON_JOB_RE = re.compile(r"^Python \(pytest\)\s*\[?([1-4])\s*/\s*4\]?$")
GIT_DIFF_TIMEOUT_SECONDS = 30
GITHUB_API_TIMEOUT_SECONDS = 10

ApiGet = Callable[[str], Any]


def path_allowed(path: str) -> bool:
    """Return True when a repo-relative POSIX path is on the docs/skills allowlist."""
    text = PurePosixPath(path.strip()).as_posix()
    if not text or text in {".", "/"}:
        return False
    if text == SKILLS_PREFIX or text.startswith(f"{SKILLS_PREFIX}/"):
        return True
    if text.startswith("docs/") and text.endswith(".md"):
        return True
    return "/" not in text and text.endswith(".md")


def classify(paths: Iterable[str]) -> str:
    """Return ``docs_skills`` only when every path is allowlisted; else ``full``."""
    normalized = [p.strip() for p in paths if p and p.strip()]
    if not normalized:
        return CLASS_FULL
    if all(path_allowed(path) for path in normalized):
        return CLASS_DOCS_SKILLS
    return CLASS_FULL


def _parse_nul_delimited_paths(raw: bytes) -> list[str]:
    return sorted(path.decode("utf-8", errors="surrogateescape") for path in raw.split(b"\0") if path)


def changed_files(git_range: str, *, cwd: Path | None = None) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "diff",
            "--no-ext-diff",
            "--name-only",
            "-z",
            git_range,
        ],
        check=True,
        capture_output=True,
        cwd=cwd or Path.cwd(),
        timeout=GIT_DIFF_TIMEOUT_SECONDS,
    )
    return _parse_nul_delimited_paths(result.stdout)


def comparison_range(base: str, head: str = "HEAD") -> str:
    """Three-dot merge-base range (``BASE...HEAD``) for landing classification."""
    return base if "..." in base else f"{base}...{head}"


def read_paths_from_stdin(stream: Iterable[str] | None = None) -> list[str]:
    source = sys.stdin if stream is None else stream
    return [line.strip() for line in source if line.strip()]


def write_github_output(
    landing_class: str,
    path: Path | None = None,
    *,
    validating_run_id: str | None = None,
) -> None:
    output = path
    if output is None:
        raw = os.environ.get("GITHUB_OUTPUT")
        if not raw:
            return
        output = Path(raw)
    with output.open("a", encoding="utf-8") as handle:
        handle.write(f"class={landing_class}\n")
        if landing_class == CLASS_MQ_VALIDATED and validating_run_id:
            handle.write(f"validating_run_id={validating_run_id}\n")


def write_step_summary(
    landing_class: str,
    *,
    path_count: int,
    path: Path | None = None,
    validating_run_id: str | None = None,
) -> None:
    summary = path
    if summary is None:
        raw = os.environ.get("GITHUB_STEP_SUMMARY")
        if not raw:
            return
        summary = Path(raw)
    with summary.open("a", encoding="utf-8") as handle:
        handle.write("## Landing class (#7018)\n\n")
        handle.write(f"`class={landing_class}` changed_files={path_count}\n")
        if landing_class == CLASS_MQ_VALIDATED and validating_run_id:
            handle.write(f"`validating_run_id={validating_run_id}`\n")


def emit(
    landing_class: str,
    *,
    path_count: int,
    as_json: bool,
    github_output: bool,
    validating_run_id: str | None = None,
) -> None:
    payload: dict[str, Any] = {"class": landing_class, "changed_files": path_count}
    if landing_class == CLASS_MQ_VALIDATED and validating_run_id:
        payload["validating_run_id"] = validating_run_id
    if as_json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(landing_class)
    write_step_summary(landing_class, path_count=path_count, validating_run_id=validating_run_id)
    if github_output:
        write_github_output(landing_class, validating_run_id=validating_run_id)


def _api_items(payload: Any, key: str) -> list[Mapping[str, Any]]:
    """Return object entries from a GitHub collection response."""
    if isinstance(payload, Mapping):
        raw = payload.get(key, [])
    elif key in {"jobs", "artifacts"} and isinstance(payload, list):
        raw = payload
    else:
        raw = []
    return [item for item in raw if isinstance(item, Mapping)] if isinstance(raw, list) else []


def github_api_get(
    path: str,
    *,
    token: str | None = None,
    api_url: str | None = None,
    timeout: int = GITHUB_API_TIMEOUT_SECONDS,
) -> Any:
    """Read one GitHub REST resource with a bounded request."""
    base_url = (api_url or os.environ.get("GITHUB_API_URL") or "https://api.github.com").rstrip("/")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{base_url}/{path.lstrip('/')}", headers=headers)
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _repository(repository: str) -> str:
    value = repository.strip()
    if not value or "/" not in value:
        raise ValueError("GITHUB_REPOSITORY must be OWNER/REPOSITORY")
    return value


def _matching_merge_group_run(
    *,
    repository: str,
    head_sha: str,
    api_get: ApiGet,
) -> Mapping[str, Any]:
    query = urlencode({"event": "merge_group", "head_sha": head_sha, "per_page": 100})
    payload = api_get(f"repos/{repository}/actions/workflows/ci.yml/runs?{query}")
    candidates: list[Mapping[str, Any]] = []
    for run in _api_items(payload, "workflow_runs"):
        run_path = run.get("path")
        if run.get("event") != "merge_group" or run.get("head_sha") != head_sha:
            continue
        if run_path is not None and str(run_path).strip() not in {CI_WORKFLOW_PATH, "ci.yml"}:
            continue
        candidates.append(run)
    if len(candidates) != 1:
        raise ValueError(f"expected exactly one ci.yml merge_group run, found {len(candidates)}")
    return candidates[0]


def _merge_group_base_sha(
    run: Mapping[str, Any],
    *,
    repository: str,
    head_sha: str,
    api_get: ApiGet,
) -> str:
    """Resolve the queue base; REST run objects do not expose event payload fields.

    GitHub's merge-group synthetic commit has the event's ``base_sha`` as its
    first parent. Fixtures may provide the event field directly; production
    falls back to the commit endpoint rather than guessing from branch names.
    """
    direct = run.get("base_sha")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    merge_group = run.get("merge_group")
    if isinstance(merge_group, Mapping):
        nested = merge_group.get("base_sha")
        if isinstance(nested, str) and nested.strip():
            return nested.strip()
    head_commit = run.get("head_commit")
    parents = head_commit.get("parents") if isinstance(head_commit, Mapping) else None
    if not isinstance(parents, list) or not parents:
        commit = api_get(f"repos/{repository}/commits/{quote(head_sha, safe='')}")
        parents = commit.get("parents") if isinstance(commit, Mapping) else None
    if not isinstance(parents, list) or not parents:
        raise ValueError("merge_group head commit has no parent to bind base_sha")
    parent = parents[0]
    base_sha = parent.get("sha") if isinstance(parent, Mapping) else None
    if not isinstance(base_sha, str) or not base_sha.strip():
        raise ValueError("merge_group head commit has an invalid first parent")
    return base_sha.strip()


def _verify_merge_group_run(
    run: Mapping[str, Any],
    *,
    repository: str,
    head_sha: str,
    api_get: ApiGet,
) -> str:
    run_id = run.get("id")
    if run_id is None or not str(run_id).strip():
        raise ValueError("validating merge_group run has no id")
    run_id_text = str(run_id)
    jobs_payload = api_get(f"repos/{repository}/actions/runs/{quote(run_id_text, safe='')}/jobs?per_page=100")
    jobs = _api_items(jobs_payload, "jobs")
    gate_jobs = [
        job
        for job in jobs
        if job.get("name") == "CI Gate" or job.get("id") == "ci-gate"
    ]
    if len(gate_jobs) != 1 or gate_jobs[0].get("conclusion") != "success":
        raise ValueError("validating merge_group run has no successful CI Gate job")

    python_jobs: dict[int, list[Mapping[str, Any]]] = {}
    for job in jobs:
        name = job.get("name")
        if not isinstance(name, str):
            continue
        match = PYTHON_JOB_RE.fullmatch(name.strip())
        if match:
            python_jobs.setdefault(int(match.group(1)), []).append(job)
    for shard in range(1, 5):
        shard_jobs = python_jobs.get(shard, [])
        if len(shard_jobs) != 1 or shard_jobs[0].get("conclusion") != "success":
            raise ValueError(f"validating merge_group run is missing successful Python shard {shard}")

    artifacts_payload = api_get(
        f"repos/{repository}/actions/runs/{quote(run_id_text, safe='')}/artifacts?per_page=100"
    )
    artifact_names = {
        str(artifact.get("name"))
        for artifact in _api_items(artifacts_payload, "artifacts")
        if artifact.get("expired") is not True
    }
    required_artifacts = {f"pytest-shard-{shard}" for shard in range(1, 5)}
    if not required_artifacts <= artifact_names:
        missing = sorted(required_artifacts - artifact_names)
        raise ValueError(f"validating merge_group run is missing shard artifacts: {', '.join(missing)}")

    return _merge_group_base_sha(
        run,
        repository=repository,
        head_sha=head_sha,
        api_get=api_get,
    )


def _has_self_reference(paths: Iterable[str]) -> bool:
    return any(PurePosixPath(path.strip()).as_posix() in SELF_REFERENCE_PATHS for path in paths)


def classify_push_to_main(
    paths: Sequence[str],
    *,
    before_sha: str,
    head_sha: str,
    event_name: str,
    ref: str,
    forced: str,
    kill_switch: str,
    repository: str,
    api_get: ApiGet | None = None,
    cwd: Path | None = None,
) -> tuple[str, str | None]:
    """Classify a landing and return ``(class, validating_run_id)``."""
    landing = classify(paths)
    if landing == CLASS_DOCS_SKILLS:
        return landing, None
    if event_name != "push" or ref != "refs/heads/main" or forced != "false" or kill_switch != "on":
        return CLASS_FULL, None
    if not before_sha or set(before_sha) == {"0"} or not head_sha or _has_self_reference(paths):
        return CLASS_FULL, None
    try:
        repository = _repository(repository)
    except ValueError:
        return CLASS_FULL, None

    get = api_get or (lambda path: github_api_get(path, token=os.environ.get("GITHUB_TOKEN")))
    try:
        # Re-derive from the exact push range; do not trust an earlier class
        # or any cached artifact as evidence of the merge-group result.
        rederived_paths = changed_files(f"{before_sha}..{head_sha}", cwd=cwd)
        if classify(rederived_paths) == CLASS_DOCS_SKILLS or _has_self_reference(rederived_paths):
            return CLASS_FULL, None
        run = _matching_merge_group_run(repository=repository, head_sha=head_sha, api_get=get)
        base_sha = _verify_merge_group_run(
            run,
            repository=repository,
            head_sha=head_sha,
            api_get=get,
        )
        if before_sha != base_sha:
            return CLASS_FULL, None
        return CLASS_MQ_VALIDATED, str(run["id"])
    except Exception:
        # API errors, timeouts, malformed responses, and unexpected git state
        # are all unknown proof and therefore full CI.
        return CLASS_FULL, None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        default="",
        help="base SHA/ref for git diff (merge_group.base_sha / push before). "
        "Omit to read newline-delimited paths from stdin.",
    )
    parser.add_argument(
        "--head",
        default="HEAD",
        help="head SHA/ref (merge_group.head_sha / github.sha); default HEAD",
    )
    parser.add_argument(
        "--before",
        default=os.environ.get("GITHUB_EVENT_BEFORE", ""),
        help="push before SHA (github.event.before), used for the MQ proof",
    )
    parser.add_argument(
        "--event",
        default=os.environ.get("GITHUB_EVENT_NAME", ""),
        help="GitHub event name",
    )
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", ""),
        help="OWNER/REPOSITORY for the Actions API",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit {\"class\": ..., \"changed_files\": N} on stdout",
    )
    parser.add_argument(
        "--github-output",
        action="store_true",
        help="append class=... to $GITHUB_OUTPUT when set",
    )
    as_json = False
    github_output = False
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        as_json = bool(args.json)
        github_output = bool(args.github_output)
        base = (args.base or "").strip()
        head = (args.head or "HEAD").strip() or "HEAD"
        event_name = (args.event or "").strip()
        if base:
            if set(base) == {"0"}:
                emit(CLASS_FULL, path_count=-1, as_json=as_json, github_output=github_output)
                return 0
            if event_name == "push":
                paths = changed_files(f"{base}..{head}")
            else:
                paths = changed_files(comparison_range(base, head))
        elif github_output:
            # CI without a usable base SHA — fail closed (do not read stdin).
            emit(CLASS_FULL, path_count=-1, as_json=as_json, github_output=github_output)
            return 0
        elif sys.stdin.isatty():
            # No paths and no git range — fail closed.
            emit(CLASS_FULL, path_count=0, as_json=as_json, github_output=github_output)
            return 0
        else:
            paths = read_paths_from_stdin()
        before = (args.before or "").strip() or (base if event_name == "push" else "")
        landing, validating_run_id = classify_push_to_main(
            paths,
            before_sha=before,
            head_sha=head,
            event_name=event_name,
            ref=os.environ.get("GITHUB_REF", ""),
            forced=os.environ.get("GITHUB_EVENT_FORCED", "false").strip().lower(),
            kill_switch=os.environ.get("CI_PUSH_DEDUP", ""),
            repository=args.repository or "",
        )
        emit(
            landing,
            path_count=len(paths),
            as_json=as_json,
            github_output=github_output,
            validating_run_id=validating_run_id,
        )
        return 0
    except Exception as exc:
        # Fail closed to full; never crash the landing-class job.
        print(f"landing-class: error → {CLASS_FULL} ({exc})", file=sys.stderr)
        emit(CLASS_FULL, path_count=-1, as_json=as_json, github_output=github_output)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
