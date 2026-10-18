"""Fail-closed public GitHub branch cleanup; metadata races use Git's restore path."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import re
import subprocess
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http.client import HTTPException
from pathlib import Path
from urllib.error import URLError
from urllib.parse import parse_qs, quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from scripts.common import github_client

KEEP_PATH = ".github/branch-cleanup-keep.txt"
API = "https://api.github.com"
MIN_AGE = timedelta(hours=48)


class Unknown(ValueError):
    """Evidence is unavailable or invalid; deletion is forbidden."""


def git(*args: str) -> str:
    """Run argument arrays, without disclosing potentially sensitive diagnostics."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Unknown("git unavailable or timed out; outcome unknown") from exc
    if result.returncode:
        raise Unknown("git refused operation")
    return result.stdout


def branch_name(value: object) -> str:
    if not isinstance(value, str) or not value or any(unicodedata.category(c).startswith("C") for c in value):
        raise Unknown("invalid branch name")
    git("check-ref-format", f"refs/heads/{value}")
    return value


def sha(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise Unknown("invalid commit SHA")
    return value


def repository(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+", value):
        raise Unknown("invalid repository identity")
    if value.split("/")[1] in {".", ".."}:
        raise Unknown("invalid repository identity")
    return value


def utc_timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", value):
        raise Unknown("invalid UTC committer timestamp")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError as exc:
        raise Unknown("invalid UTC committer timestamp") from exc


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Unknown("API redirect refused")


class GitHub:
    def __init__(self, repo: str, token: str):
        self.repo = repository(repo)
        self.repository_id: int | None = None
        self.token = token
        self.opener = build_opener(NoRedirect())

    def get(self, endpoint: str) -> tuple[object, str]:
        request = Request(
            f"{API}/repos/{self.repo}/{endpoint}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Cache-Control": "no-cache",
            },
        )
        try:
            with github_client.http_open(request, opener=self.opener.open, timeout=30) as response:
                if response.status != 200:
                    raise Unknown("API status unknown")
                return json.load(response), response.headers.get("link", "")
        except (URLError, OSError, ValueError, HTTPException, github_client.GitHubRateLimited) as exc:
            raise Unknown("API unavailable or malformed") from exc

    def pages(self, endpoint: str) -> list[dict]:
        """Validate every Link; a full final page also requires an empty sentinel page."""
        items = []
        for page in range(1, 10001):
            separator = "&" if "?" in endpoint else "?"
            path = f"{endpoint}{separator}per_page=100&page={page}"
            data, link = self.get(path)
            if not isinstance(data, list) or len(data) > 100 or any(not isinstance(x, dict) for x in data):
                raise Unknown("malformed pagination")
            relations = {}
            if link:
                for part in link.split(","):
                    match = re.fullmatch(r'\s*<([^<>]+)>; rel="(next|last|first|prev)"\s*', part)
                    if not match or match[2] in relations:
                        raise Unknown("malformed pagination link")
                    url, relation = match.groups()
                    try:
                        parsed = urlsplit(url)
                        expected = urlsplit(f"{API}/repos/{self.repo}/{endpoint}")
                        paths = {expected.path}
                        if self.repository_id is not None:
                            paths.add(f"/repositories/{self.repository_id}/{urlsplit(endpoint).path}")
                        query = parse_qs(parsed.query, keep_blank_values=True)
                        expected_query = parse_qs(expected.query)
                        page_value = query.pop("page", [])
                        page_number = (
                            int(page_value[0])
                            if len(page_value) == 1 and page_value[0].isascii() and page_value[0].isdigit()
                            else 0
                        )
                    except ValueError as exc:
                        raise Unknown("malformed pagination link") from exc
                    if (
                        parsed.scheme != expected.scheme
                        or parsed.netloc != expected.netloc
                        or parsed.path not in paths
                        or parsed.fragment
                        or query != {**expected_query, "per_page": ["100"]}
                        or page_number < 1
                    ):
                        raise Unknown("untrusted pagination link")
                    relations[relation] = page_number
                if "next" in relations and relations["next"] != page + 1:
                    raise Unknown("incomplete pagination")
                if relations.get("last", page) > page and "next" not in relations:
                    raise Unknown("incomplete pagination")
            items.extend(data)
            if "next" not in relations and len(data) < 100:
                return items
            if not data:
                raise Unknown("incomplete pagination")
        raise Unknown("pagination limit reached")

    def object(self, endpoint: str) -> dict:
        data, _ = self.get(endpoint)
        if not isinstance(data, dict):
            raise Unknown("malformed API object")
        return data


@dataclass(frozen=True)
class Candidate:
    name: str
    sha: str
    committed: datetime
    protected: bool


@dataclass(frozen=True)
class Evidence:
    default: str
    revision: str
    keep_blob: str
    keep: frozenset[str]
    protected: frozenset[str]
    prs: frozenset[tuple[int, str, str, str, str]]


def branch_record(data: dict) -> tuple[str, str, bool]:
    name = branch_name(data.get("name"))
    commit = data.get("commit")
    if not isinstance(commit, dict) or type(data.get("protected")) is not bool:
        raise Unknown("unknown branch protection or commit")
    return name, sha(commit.get("sha")), data["protected"]


def read_evidence(api: GitHub) -> tuple[Evidence, list[str]]:
    repo = api.object("")
    if repository(repo.get("full_name")).lower() != api.repo.lower() or repo.get("private") is not False:
        raise Unknown("repository identity/public state mismatch")
    repo_id = repo.get("id")
    if type(repo_id) is not int or repo_id <= 0 or api.repository_id not in {None, repo_id}:
        raise Unknown("repository ID unknown or changed")
    api.repository_id = repo_id
    default = branch_name(repo.get("default_branch"))
    name, revision, _ = branch_record(api.object(f"branches/{quote(default, safe='')}"))
    if name != default:
        raise Unknown("default branch mismatch")
    content = api.object(f"contents/{KEEP_PATH}?ref={revision}")
    if content.get("type") != "file" or content.get("encoding") != "base64" or content.get("path") != KEEP_PATH:
        raise Unknown("unknown keep file")
    try:
        raw = base64.b64decode("".join(content["content"].split()), validate=True)
        text = raw.decode("utf-8")
    except (KeyError, AttributeError, ValueError, UnicodeError, binascii.Error) as exc:
        raise Unknown("malformed keep file") from exc
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if sha(content.get("sha")) != blob:
        raise Unknown("keep blob mismatch")
    keep = frozenset(branch_name(line) for line in text.splitlines() if line and not line.startswith("#"))
    branches = [branch_record(item) for item in api.pages("branches")]
    if len({b[0] for b in branches}) != len(branches) or (default, revision) not in {(b[0], b[1]) for b in branches}:
        raise Unknown("inconsistent branch inventory")
    prs = set()
    numbers = set()
    for pr in api.pages("pulls?state=open"):
        head, base = pr.get("head"), pr.get("base")
        number = pr.get("number")
        if (
            pr.get("state") != "open"
            or type(number) is not int
            or number <= 0
            or number in numbers
            or not isinstance(head, dict)
            or not isinstance(base, dict)
        ):
            raise Unknown("malformed open PR")
        numbers.add(number)
        head_repo, base_repo = head.get("repo"), base.get("repo")
        if not isinstance(head_repo, dict) or not isinstance(base_repo, dict):
            raise Unknown("unknown PR repository")
        if repository(base_repo.get("full_name")).lower() != api.repo.lower():
            raise Unknown("PR base repository mismatch")
        prs.add(
            (
                number,
                repository(head_repo.get("full_name")).lower(),
                branch_name(head.get("ref")),
                sha(head.get("sha")),
                branch_name(base.get("ref")),
            )
        )
    return Evidence(default, revision, blob, keep, frozenset(b[0] for b in branches if b[2]), frozenset(prs)), [
        b[0] for b in branches
    ]


def read_candidate(api: GitHub, name: str) -> Candidate:
    actual, head, protected = branch_record(api.object(f"branches/{quote(name, safe='')}"))
    if actual != name:
        raise Unknown("candidate name mismatch")
    commit = api.object(f"git/commits/{head}")
    committer = commit.get("committer")
    if sha(commit.get("sha")) != head or not isinstance(committer, dict):
        raise Unknown("candidate commit mismatch")
    return Candidate(name, head, utc_timestamp(committer.get("date")), protected)


def eligible(candidate: Candidate, evidence: Evidence, repo: str, now: datetime) -> bool:
    if now.tzinfo != UTC:
        raise Unknown("clock must be UTC")
    excluded = {"main", evidence.default} | evidence.keep | evidence.protected
    excluded |= {ref for _, owner, ref, _, _ in evidence.prs if owner == repo.lower()}
    excluded |= {base for _, _, _, _, base in evidence.prs}
    return (
        candidate.name not in excluded
        and not candidate.protected
        and timedelta(0) <= now - candidate.committed
        and now - candidate.committed >= MIN_AGE
    )


def delete(candidate: Candidate) -> None:
    name, head = branch_name(candidate.name), sha(candidate.sha)
    ref = f"refs/heads/{name}"
    output = git(
        "-c",
        "remote.origin.mirror=false",
        "-c",
        "push.followTags=false",
        "push",
        "--porcelain",
        f"--force-with-lease={ref}:{head}",
        "--no-follow-tags",
        "origin",
        f":{ref}",
    )
    # A zero exit alone can mean 'up to date'. Only Git's deletion receipt counts.
    if f"-\t:{ref}\t[deleted]" not in output.splitlines():
        raise Unknown("no confirmed deletion receipt; outcome unknown")


def validate_source(api: GitHub, evidence: Evidence) -> None:
    expected = f"https://github.com/{api.repo}.git"
    for args in [("remote", "get-url", "--all", "origin"), ("remote", "get-url", "--push", "--all", "origin")]:
        if git(*args).splitlines() != [expected]:
            raise Unknown("untrusted origin URL")
    if (
        os.environ.get("GITHUB_EVENT_NAME") not in {"schedule", "workflow_dispatch"}
        or os.environ.get("GITHUB_REF") != f"refs/heads/{evidence.default}"
        or sha(os.environ.get("GITHUB_SHA")) != evidence.revision
        or git("rev-parse", "HEAD").strip() != evidence.revision
    ):
        raise Unknown("execution requires the current trusted default-branch revision")


def cleanup(api: GitHub, now: datetime) -> dict:
    report = {
        "deleted": [],
        "retained": [],
        "failures": [],
        "source_sha": None,
        "git_version": git("--version").strip(),
        "clock_utc": now.isoformat(),
    }
    try:
        initial, names = read_evidence(api)
        validate_source(api, initial)
        report["source_sha"] = initial.revision
        for name in names:
            try:
                candidate = read_candidate(api, name)
                if not eligible(candidate, initial, api.repo, now):
                    report["retained"].append({"name": name, "reason": "ineligible"})
                    continue
                fresh, _ = read_evidence(api)
                current = read_candidate(api, name)
                if fresh != initial or current != candidate or not eligible(current, fresh, api.repo, now):
                    report["retained"].append({"name": name, "reason": "eligibility evidence changed"})
                    continue
                delete(current)
                report["deleted"].append({"name": name, "sha": current.sha})
            except Unknown as exc:
                report["failures"].append({"name": name, "reason": str(exc)})
                # Stop on unknown evidence or ambiguous operation; never infer success from absence.
                break
    except Unknown as exc:
        report["failures"].append({"reason": str(exc)})
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Delete eligible public GitHub branches at least 48 hours old.\n"
        "Use only in the default-branch scheduled/manual workflow; never for local worktree cleanup.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python -m scripts.hygiene.remote_branch_cleanup --repo learn-ukrainian/learn-ukrainian.github.io\n"
        "Outputs: JSON stdout and GITHUB_STEP_SUMMARY; conditional remote branch deletes.\n"
        "Exit codes: 0 completed (possibly no eligible branches); 1 unknown evidence or deletion failure.\n"
        "Related: docs/runbooks/remote-branch-cleanup.md, #10945.\n"
        "Requires GH_TOKEN and GitHub Actions event/ref/SHA environment; no local apply mode.",
    )
    parser.add_argument(
        "--repo", required=True, help="Exact owner/repository identity, e.g. learn-ukrainian/learn-ukrainian.github.io"
    )
    args = parser.parse_args(argv)
    try:
        repo = repository(args.repo)
        if repository(os.environ.get("GITHUB_REPOSITORY")) != repo or not os.environ.get("GH_TOKEN"):
            raise Unknown("missing or mismatched workflow identity/token")
        report = cleanup(GitHub(repo, os.environ["GH_TOKEN"]), datetime.now(UTC))
    except Unknown as exc:
        report = {"deleted": [], "failures": [{"reason": str(exc)}]}
    rendered = json.dumps(report, ensure_ascii=True, indent=2)
    print(rendered)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write(
                "## Remote branch cleanup\n\n" + "\n".join("    " + line for line in rendered.splitlines()) + "\n"
            )
    return int(bool(report["failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
