"""GitHub transport: REST-first, conditional disk cache, and bounded budgets.

All GitHub I/O belongs here. Publishing admission still belongs to
``scripts.publish``; this module does not grant permission to publish.
Conditional GETs follow GitHub's documented ETag protocol. No request is retried.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import time
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode, urlparse

RESERVE = 10
ANSI = re.compile(rb"\x1b\[[0-?]*[ -/]*[@-~]")


def colour_safe_environment(env=None):
    result = dict(os.environ if env is None else env)
    for key in ("FORCE_COLOR", "CLICOLOR_FORCE", "GH_FORCE_TTY"):
        result.pop(key, None)
    result.update(NO_COLOR="1", GH_PAGER="cat", GH_PROMPT_DISABLED="1")
    return result


@dataclass
class Response:
    status: int
    headers: dict[str, str]
    body: bytes


@dataclass
class Result:
    value: Any = None
    status: int = 200
    stale: bool = False
    age_seconds: float = 0
    error: str | None = None
    reset_at: int | None = None
    headers: dict[str, str] = field(default_factory=dict)

    def require_fresh(self):
        if self.error == "github_rate_limited" or self.stale:
            raise GitHubRateLimited(self.reset_at)
        if self.error:
            raise RuntimeError(self.error)
        return self.value


class GitHubRateLimited(RuntimeError):
    code = "github_rate_limited"

    def __init__(self, reset_at):
        self.reset_at = reset_at
        super().__init__(f"github_rate_limited reset_at={reset_at}")


def _cache_directory(cwd):
    override = os.environ.get("LU_GITHUB_CACHE_DIR")
    if override:
        return Path(override)
    root = Path(cwd or Path.cwd()).resolve()
    for parent in (root, *root.parents):
        marker = parent / ".git"
        if marker.is_dir():
            root = parent
            break
        if marker.is_file():
            content = marker.read_text().strip()
            if content.startswith("gitdir: "):
                gitdir = (parent / content[8:]).resolve()
                common = gitdir / "commondir"
                root = (gitdir / common.read_text().strip()).resolve().parent if common.is_file() else gitdir.parent
                break
    return root / "batch_state" / "github-client"


def parse_http(raw):
    separator = b"\r\n\r\n" if b"\r\n\r\n" in raw else b"\n\n"
    head, sep, body = raw.partition(separator)
    lines = ANSI.sub(b"", head).splitlines()
    if not sep or not lines or not re.match(rb"HTTP/\S+ \d{3}", lines[0]):
        raise RuntimeError("GitHub transport omitted response headers")
    headers = {}
    for line in lines[1:]:
        key, colon, value = line.partition(b":")
        if colon:
            headers[key.decode().lower().strip()] = value.decode().strip()
    return Response(int(lines[0].split()[1]), headers, body)


def _cached_value(cached):
    return cached[0] if json.loads(cached[1]).get("_github_binary") else json.loads(cached[0])


def _store_budget(db, scope, resource, remaining, reset):
    db.execute(
        """INSERT INTO budget VALUES(?,?,?,?)
        ON CONFLICT(scope,resource) DO UPDATE SET
        remaining=CASE WHEN excluded.reset=budget.reset THEN min(budget.remaining,excluded.remaining) ELSE excluded.remaining END,
        reset=excluded.reset WHERE excluded.reset>=budget.reset""",
        (scope, resource, remaining, reset),
    )


def _store_cache(db, scope, key, body, headers, at):
    db.execute(
        """INSERT INTO cache VALUES(?,?,?,?,?)
        ON CONFLICT(scope,key) DO UPDATE SET body=excluded.body,headers=excluded.headers,at=excluded.at
        WHERE excluded.at>=cache.at""",
        (scope, key, body, json.dumps(headers), at),
    )


def _transport_process(command, *, input, env, cwd, timeout, output_file=None, **_kwargs):
    """Bound one CLI process and its descendants without polling or retrying."""
    import signal
    import threading

    with subprocess.Popen(
        command,
        stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
        stdout=output_file if output_file is not None else subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=cwd,
        start_new_session=True,
    ) as child:
        previous = {}

        def forward(signum, _frame):
            with suppress(ProcessLookupError):
                os.killpg(child.pid, signum)

        if threading.current_thread() is threading.main_thread():
            previous = {
                signum: signal.signal(signum, forward) for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
            }
        try:
            try:
                output, error = child.communicate(input=input, timeout=timeout)
                if output_file is not None:
                    with suppress(ProcessLookupError):
                        os.killpg(child.pid, signal.SIGKILL)
            except BaseException:
                with suppress(ProcessLookupError):
                    os.killpg(child.pid, signal.SIGKILL)
                child.communicate()
                raise
            return subprocess.CompletedProcess(command, child.returncode, output, error)
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)


def _spooled_transport_process(command, *, max_response_bytes, **kwargs):
    """Keep an existing caller's byte ceiling before materializing its body."""
    import http.client
    import tempfile

    with tempfile.TemporaryFile() as output:
        proc = _transport_process(command, output_file=output, **kwargs)
        output.seek(0)
        status = output.readline(http.client._MAXLINE + 1)
        if not re.match(rb"HTTP/\S+ \d{3}", status):
            proc.stdout = b""
            return proc
        try:
            http.client.parse_headers(output)
        except http.client.HTTPException:
            proc.stdout = b""
            return proc
        body_offset = output.tell()
        body = output.read(max_response_bytes + 1)
        output.seek(0)
        proc.stdout = output.read(body_offset) + body
        return proc


class GitHubClient:
    def __init__(
        self,
        *,
        cache_dir=None,
        env=None,
        cwd=None,
        transport=None,
        runner=None,
        clock=time.time,
        max_response_bytes=None,
    ):
        self.env = colour_safe_environment(env)
        self.cwd = cwd
        self.transport = transport
        self.runner = runner
        self.clock = clock
        if max_response_bytes is not None and (type(max_response_bytes) is not int or max_response_bytes < 0):
            raise ValueError("invalid GitHub response byte limit")
        self.max_response_bytes = max_response_bytes
        self.host = self.env.get("GH_HOST", "github.com")
        # A digest isolates credentials without storing credentials or account IDs.
        credential = (
            self.env.get("GH_TOKEN") or self.env.get("GITHUB_TOKEN")
            if self.host == "github.com" or self.host.endswith(".ghe.com")
            else self.env.get("GH_ENTERPRISE_TOKEN") or self.env.get("GITHUB_ENTERPRISE_TOKEN")
        )
        if credential:
            credential = re.sub(r"^(?:Bearer|token)\s+", "", credential, flags=re.IGNORECASE)
        if not credential:
            config = Path(
                self.env.get("GH_CONFIG_DIR")
                or str(Path(self.env.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")) / "gh")
            )
            try:
                credential = hashlib.sha256((config / "hosts.yml").read_bytes()).hexdigest()
            except OSError:
                credential = "unconfigured-cli"
        self.scope = hashlib.sha256((self.host + "\0" + credential).encode()).hexdigest()
        self.cache_dir = Path(cache_dir) if cache_dir is not None else _cache_directory(cwd)

    @contextmanager
    def _db(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = self.cache_dir / "cache.sqlite3"
        db = sqlite3.connect(path, timeout=5)
        os.chmod(path, 0o600)
        db.execute(
            "CREATE TABLE IF NOT EXISTS cache (scope TEXT, key TEXT, body BLOB, headers TEXT, at REAL, PRIMARY KEY(scope,key))"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS budget (scope TEXT, resource TEXT, remaining INTEGER, reset INTEGER, PRIMARY KEY(scope,resource))"
        )
        try:
            with db:
                yield db
        finally:
            db.close()

    def _send(self, method, endpoint, headers, body, timeout):
        if self.transport:
            response = self.transport(method, endpoint, headers, body, timeout)
            return self._bounded_response(response)
        executable = self.env.get("AGENT_REAL_GH", "gh")
        if self.runner is None:
            from scripts.opsec.prepublish import PublishBlocked, real_gh

            try:
                executable = real_gh({**self.env, "AGENT_ORIGINAL_PATH": self.env.get("PATH", os.defpath)})
            except PublishBlocked:
                return Response(599, {}, b'{"message":"github_transport_unavailable"}')
        command = [executable, "api", "--include", "--method", method, endpoint]
        if self.host != "github.com":
            command.extend(["--hostname", self.host])
        for name, value in headers.items():
            command.extend(["-H", f"{name}: {value}"])
        if body is not None:
            command.extend(["--input", "-"])
        executor = self.runner or _transport_process
        if self.runner is None and self.max_response_bytes is not None:
            executor = _spooled_transport_process
        limit = {"max_response_bytes": self.max_response_bytes} if executor is _spooled_transport_process else {}
        proc = executor(
            command,
            **limit,
            input=body,
            capture_output=True,
            env=self.env,
            cwd=self.cwd,
            timeout=timeout,
            check=False,
        )
        raw = proc.stdout.encode() if isinstance(proc.stdout, str) else proc.stdout or b""
        # Injected existing runners can supply plain JSON; real transports must
        # provide the HTTP status and budget headers.
        if self.runner and not ANSI.sub(b"", raw).startswith(b"HTTP/"):
            return self._bounded_response(Response(200 if proc.returncode == 0 else 500, {}, raw))
        if not ANSI.sub(b"", raw).startswith(b"HTTP/"):
            return Response(599, {}, b'{"message":"github_transport_unavailable"}')
        return self._bounded_response(parse_http(raw))

    def _bounded_response(self, response):
        if self.max_response_bytes is not None and len(response.body) > self.max_response_bytes:
            return Response(413, response.headers, b'{"message":"github_response_too_large"}')
        return response

    def request(self, method, endpoint, *, payload=None, timeout=30, fresh=False, headers=None, raw_response=False):
        method = method.upper()
        if endpoint.startswith("https://"):
            parsed = urlparse(endpoint)
            allowed = (
                {"api.github.com", "uploads.github.com", "github.com"} if self.host == "github.com" else {self.host}
            )
            if parsed.hostname not in allowed:
                raise ValueError("GitHub endpoint host mismatch")
        raw = (
            payload
            if isinstance(payload, bytes)
            else json.dumps(payload, ensure_ascii=False).encode()
            if payload is not None
            else None
        )
        resource_path = (
            urlparse(endpoint).path.lstrip("/")
            if endpoint.startswith("https://")
            else endpoint.lstrip("/").split("?", 1)[0]
        )
        graphql = resource_path == "graphql"
        document = json.loads(raw) if graphql and isinstance(payload, bytes) else payload
        read = method == "GET" or (graphql and document and not re.search(r"\bmutation\b", document.get("query", "")))
        resource = "graphql" if graphql else "search" if resource_path.startswith("search/") else "core"
        key = hashlib.sha256(
            (
                method
                + "\0"
                + endpoint
                + "\0"
                + json.dumps(headers or {}, sort_keys=True)
                + ("raw" if raw_response else "json")
            ).encode()
            + (raw or b"")
        ).hexdigest()
        now = self.clock()
        with self._db() as db:
            cached = db.execute(
                "SELECT body,headers,at FROM cache WHERE scope=? AND key=? AND (? IS NULL OR length(body)<=?)",
                (self.scope, key, self.max_response_bytes, self.max_response_bytes),
            ).fetchone()
            budget = db.execute(
                "SELECT remaining,reset FROM budget WHERE scope=? AND resource IN (?, 'secondary') ORDER BY reset DESC",
                (self.scope, resource),
            ).fetchall()
        limited = next((reset for remaining, reset in budget if remaining <= RESERVE and reset > now), None)

        def deferred(reset):
            if read and cached and not fresh:
                return Result(
                    _cached_value(cached),
                    stale=True,
                    age_seconds=max(0, now - cached[2]),
                    reset_at=reset,
                    headers=json.loads(cached[1]),
                )
            return Result(status=429, error="github_rate_limited", reset_at=reset)

        if limited is not None:
            return deferred(limited)
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", **(headers or {})}
        if cached and method == "GET":
            old_headers = json.loads(cached[1])
            if old_headers.get("etag"):
                headers["If-None-Match"] = old_headers["etag"]
        response = self._send(method, endpoint, headers, raw, timeout)
        h = {k.lower(): v for k, v in response.headers.items()}
        reset = None
        with self._db() as db:
            if "x-ratelimit-remaining" in h and "x-ratelimit-reset" in h:
                with suppress(ValueError):
                    remaining, reset = int(h["x-ratelimit-remaining"]), int(h["x-ratelimit-reset"])
                    _store_budget(db, self.scope, h.get("x-ratelimit-resource", resource), remaining, reset)
            if response.status == 429 or (
                response.status == 403
                and (
                    h.get("x-ratelimit-remaining") == "0"
                    or "retry-after" in h
                    or b"rate limit" in response.body.lower()
                )
            ):
                with suppress(ValueError):
                    reset = int(now + float(h["retry-after"])) if "retry-after" in h else reset
                reset = reset or int(now + 60)
                blocked_resource = (
                    "secondary"
                    if "retry-after" in h or h.get("x-ratelimit-remaining") != "0"
                    else h.get("x-ratelimit-resource", resource)
                )
                _store_budget(db, self.scope, blocked_resource, 0, reset)
                return deferred(reset)
            if response.status == 304:
                if not cached:
                    return Result(status=304, error="github_cache_miss", headers=h)
                # 304 is authoritative freshness; its remaining header is used,
                # never decremented locally.
                h = {**json.loads(cached[1]), **h}
                db.execute(
                    "UPDATE cache SET at=?,headers=? WHERE scope=? AND key=? AND at<=?",
                    (now, json.dumps(h), self.scope, key, now),
                )
                return Result(_cached_value(cached), status=304, headers=h)
            if 200 <= response.status < 300 and (raw_response or headers.get("Accept") == "application/octet-stream"):
                if read:
                    _store_cache(db, self.scope, key, response.body, {**h, "_github_binary": True}, now)
                return Result(response.body, status=response.status, headers=h)
            try:
                value = json.loads(response.body) if response.body else None
            except ValueError:
                if read and 200 <= response.status < 300:
                    _store_cache(db, self.scope, key, response.body, {**h, "_github_binary": True}, now)
                return Result(
                    response.body,
                    status=response.status,
                    error=None if 200 <= response.status < 300 else "github_http_error",
                    headers=h,
                )
            if (
                graphql
                and isinstance(value, dict)
                and any(
                    e.get("type") in {"RATE_LIMIT", "RATE_LIMITED"}
                    for e in value.get("errors", [])
                    if isinstance(e, dict)
                )
            ):
                reset = reset or int(now + 60)
                _store_budget(db, self.scope, resource, 0, reset)
                return deferred(reset)
            if graphql and isinstance(value, dict) and value.get("errors"):
                return Result(value, status=response.status, error="github_graphql_error", headers=h)
            if not 200 <= response.status < 300:
                return Result(value, status=response.status, error="github_http_error", reset_at=reset, headers=h)
            if resource_path == "rate_limit" and isinstance(value, dict):
                for name, rate in value.get("resources", {}).items():
                    if isinstance(rate, dict) and type(rate.get("remaining")) is int and type(rate.get("reset")) is int:
                        _store_budget(db, self.scope, name, rate["remaining"], rate["reset"])
            if read:
                _store_cache(db, self.scope, key, response.body, h, now)
            else:
                # Any write can affect list/detail cache entries. Retain them
                # for stale status, but never treat them as fresh without GET.
                pass
        return Result(value, status=response.status, headers=h)


def _options(args):
    options, positional = {}, []
    valued = {
        "--repo",
        "-R",
        "--json",
        "--jq",
        "-q",
        "--template",
        "--state",
        "--head",
        "--base",
        "--limit",
        "-L",
        "--search",
        "--label",
        "--author",
        "--assignee",
        "--branch",
        "--event",
        "--workflow",
        "--status",
        "--created",
        "--commit",
        "--job",
        "--pattern",
        "-p",
        "--output",
        "-O",
        "--dir",
        "-D",
        "--method",
        "-X",
        "--input",
        "--header",
        "-H",
        "--field",
        "-F",
        "--raw-field",
        "-f",
        "--hostname",
        "--title",
        "--body",
        "--body-file",
        "--match-head-commit",
        "--subject",
        "--comment",
        "--reason",
        "--ref",
        "--name",
        "--color",
        "--description",
        "--milestone",
        "--add-label",
        "--remove-label",
        "--target",
        "--notes-file",
        "-s",
        "-B",
        "-l",
        "-S",
        "-A",
        "-a",
    }
    iterator = iter(args)
    for arg in iterator:
        if arg == "--":
            positional.extend(iterator)
            break
        if arg.startswith("-"):
            flag, eq, value = arg.partition("=")
            value = value if eq else next(iterator) if flag in valued else True
            options.setdefault(flag, []).append(value)
        else:
            positional.append(arg)
    return options, positional


def _opt(options, *keys, default=None):
    return next((options[k][-1] for k in keys if k in options), default)


def _repo(options, client):
    repo = _opt(options, "--repo", "-R") or client.env.get("GH_REPO") or client.env.get("GITHUB_REPOSITORY")
    if repo:
        return repo.removeprefix("github.com/")
    from scripts.opsec.gh_snapshot import repository

    value = repository(Path(client.cwd or Path.cwd()), client.env)
    if value == "unknown":
        raise ValueError("GitHub repository unresolved")
    return value.split("/", 1)[1]


def _next_link(headers):
    return next((m.group(1) for m in re.finditer(r'<([^>]+)>;\s*rel="next"', headers.get("link", ""))), None)


def _pages(client, endpoint, *, timeout, fresh, paginate):
    pages = []
    for _ in range(100):
        result = client.request("GET", endpoint, timeout=timeout, fresh=fresh)
        if result.error:
            return result
        pages.append(result)
        endpoint = _next_link(result.headers) if paginate else None
        if not endpoint:
            return pages
    raise RuntimeError("GitHub pagination exceeds safety bound")


def _merge_observation(result, *observations):
    for other in observations:
        result.stale |= other.stale
        result.age_seconds = max(result.age_seconds, other.age_seconds)
        if other.reset_at is not None:
            result.reset_at = other.reset_at
    return result


def _project(row, kind):
    value = dict(row)
    for old, new in {
        "html_url": "url",
        "node_id": "id",
        "created_at": "createdAt",
        "updated_at": "updatedAt",
        "closed_at": "closedAt",
        "merged_at": "mergedAt",
        "head_sha": "headSha",
        "head_branch": "headBranch",
        "display_title": "displayTitle",
        "run_number": "number",
        "database_id": "databaseId",
        "tag_name": "tagName",
        "target_commitish": "targetCommitish",
    }.items():
        if old in row:
            value[new] = row[old]
    value["databaseId"] = row.get("id")
    if "changed_files" in row:
        value["changedFiles"] = row["changed_files"]
    if kind == "comment":
        value.update(author=row.get("user"), authorAssociation=row.get("author_association"))
    if kind in {"pr", "issue"}:
        value["state"] = "MERGED" if row.get("merged_at") else str(row.get("state", "")).upper()
        value["author"] = row.get("user")
    if kind == "pr":
        head, base = row.get("head") or {}, row.get("base") or {}
        value.update(
            isDraft=row.get("draft"),
            headRefOid=head.get("sha"),
            headRefName=head.get("ref"),
            baseRefOid=base.get("sha"),
            baseRefName=base.get("ref"),
            merged=bool(row.get("merged_at")),
            isCrossRepository=(head.get("repo") or {}).get("full_name") != (base.get("repo") or {}).get("full_name"),
            autoMergeRequest=row.get("auto_merge"),
            mergeable="MERGEABLE"
            if row.get("mergeable") is True
            else "CONFLICTING"
            if row.get("mergeable") is False
            else "UNKNOWN",
        )
        value["mergeCommit"] = (
            {"oid": row["merge_commit_sha"]} if row.get("merged_at") and row.get("merge_commit_sha") else None
        )
        value["mergeStateStatus"] = {
            "clean": "CLEAN",
            "blocked": "BLOCKED",
            "behind": "BEHIND",
            "dirty": "DIRTY",
            "unstable": "UNSTABLE",
            "draft": "DRAFT",
        }.get(row.get("mergeable_state"), "UNKNOWN")
    if kind == "run":
        value["workflowName"] = row.get("name")
    if kind == "release":
        value["assets"] = [
            {**asset, "url": asset.get("browser_download_url"), "size": asset.get("size")}
            for asset in row.get("assets", [])
        ]
    return value


def _read_command(client, kind, action, options, positional, *, timeout, fresh):
    repo = (
        positional[0].removeprefix("https://github.com/").removeprefix("github.com/").rstrip("/")
        if kind == "repo" and positional
        else _repo(options, client)
    )
    root = f"repos/{repo}"
    fields = str(_opt(options, "--json", default="")).split(",")
    number = positional[0] if positional else None
    if number and "/" in number and re.search(r"/(pull|issues)/\d+", number):
        number = number.rstrip("/").split("/")[-1]
    query = {"per_page": 100}
    for flag, parameter in {
        "--state": "state",
        "--base": "base",
        "--event": "event",
        "--branch": "branch",
        "--commit": "head_sha",
        "--status": "status",
        "--created": "created",
    }.items():
        if flag in options:
            query[parameter] = _opt(options, flag)
    if query.get("state") == "merged":
        query["state"] = "closed"
    if "--head" in options:
        head = _opt(options, "--head")
        query["head"] = head if ":" in head else repo.split("/")[0] + ":" + head
    limit = int(_opt(options, "--limit", "-L", default=30))
    if kind == "pr" and action in {"view", "checks", "diff"}:
        if not number or not str(number).isdigit():
            head = (
                number
                or subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=client.cwd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=True,
                ).stdout.strip()
            )
            found = client.request(
                "GET",
                root + "/pulls?" + urlencode({"state": "all", "head": repo.split("/")[0] + ":" + head}),
                timeout=timeout,
                fresh=fresh,
            )
            if found.error or not found.value:
                return found if found.error else Result(status=404, error="github_pr_not_found")
            number = str(found.value[0]["number"])
        result = client.request("GET", f"{root}/pulls/{number}", timeout=timeout, fresh=fresh)
        if result.error:
            return result
        value = _project(result.value, "pr")
        if action == "diff":
            pages = _pages(
                client, f"{root}/pulls/{number}/files?per_page=100", timeout=timeout, fresh=fresh, paginate=True
            )
            if isinstance(pages, Result):
                return pages
            files = [f for page in pages for f in page.value]
            if "--name-only" in options:
                value = "\n".join(f["filename"] for f in files)
            else:
                diff = client.request(
                    "GET",
                    f"{root}/pulls/{number}",
                    headers={"Accept": "application/vnd.github.diff"},
                    timeout=timeout,
                    fresh=fresh,
                )
                if diff.error:
                    return diff
                pages.append(diff)
                value = diff.value
            _merge_observation(result, *pages)
        if action == "checks" or "statusCheckRollup" in fields:
            checks = client.request(
                "GET", f"{root}/commits/{value['headRefOid']}/check-runs?per_page=100", timeout=timeout, fresh=fresh
            )
            if checks.error:
                return checks
            rows = checks.value.get("check_runs", [])
            if checks.value.get("total_count", 0) > len(rows):
                return Result(error="github_checks_incomplete")
            status = client.request(
                "GET", f"{root}/commits/{value['headRefOid']}/status?per_page=100", timeout=timeout, fresh=fresh
            )
            if status.error:
                return status
            if status.value.get("total_count", 0) > len(status.value.get("statuses", [])):
                return Result(error="github_statuses_incomplete")
            rollup = [
                {
                    "__typename": "CheckRun",
                    "name": r.get("name"),
                    "status": str(r.get("status", "")).upper(),
                    "conclusion": str(r.get("conclusion") or "").upper(),
                    "detailsUrl": r.get("html_url"),
                    "startedAt": r.get("started_at"),
                    "completedAt": r.get("completed_at"),
                }
                for r in rows
            ]
            rollup.extend(
                {
                    "__typename": "StatusContext",
                    "context": r.get("context"),
                    "state": str(r.get("state", "")).upper(),
                    "targetUrl": r.get("target_url"),
                }
                for r in status.value.get("statuses", [])
            )
            value["statusCheckRollup"] = rollup
            _merge_observation(result, checks, status)
            if action == "checks":
                value = [
                    {
                        "name": r.get("name") or r.get("context"),
                        "state": r.get("conclusion") or r.get("state") or r.get("status"),
                        "bucket": "pass"
                        if (r.get("conclusion") or r.get("state")) in {"SUCCESS", "NEUTRAL", "SKIPPED"}
                        else "pending"
                        if (r.get("status") != "COMPLETED" and r.get("state") in {None, "PENDING"})
                        else "fail",
                    }
                    for r in rollup
                ]
    elif kind in {"pr", "issue"} and action in {"view", "list"}:
        endpoint = root + ("/pulls" if kind == "pr" else "/issues")
        endpoint += "/" + str(number) if action == "view" else "?" + urlencode(query)
        searching = action == "list" and "--search" in options
        if searching:
            terms = [f"repo:{repo}", "is:pr" if kind == "pr" else "is:issue", _opt(options, "--search")]
            state = _opt(options, "--state", default="open")
            if state != "all":
                terms.append("is:merged" if state == "merged" else f"state:{state}")
            terms.extend("label:" + json.dumps(label) for label in options.get("--label", []))
            endpoint = "search/issues?" + urlencode({"q": " ".join(terms), "per_page": 100})
        pages = _pages(client, endpoint, timeout=timeout, fresh=fresh, paginate=action == "list")
        if isinstance(pages, Result):
            return pages
        result = pages[0]
        if action == "list":
            if searching:
                if any(p.value.get("incomplete_results") for p in pages):
                    return Result(error="github_search_incomplete")
                rows = [r for page in pages for r in page.value["items"]][:limit]
                if kind == "pr":
                    details = []
                    for row in rows:
                        detail = client.request("GET", f"{root}/pulls/{row['number']}", timeout=timeout, fresh=fresh)
                        if detail.error:
                            return detail
                        pages.append(detail)
                        details.append(detail.value)
                    rows = details
            else:
                rows = [r for p in pages for r in p.value if kind == "pr" or "pull_request" not in r]
            if _opt(options, "--state") == "merged":
                rows = [r for r in rows if r.get("merged_at")]
            _merge_observation(result, *pages)
            if "--label" in options:
                wanted = set(options["--label"])
                rows = [r for r in rows if wanted <= {x["name"] for x in r.get("labels", [])}]
            value = [_project(r, kind) for r in rows[:limit]]
            if kind == "pr" and set(fields) & {
                "mergeable",
                "mergeStateStatus",
                "statusCheckRollup",
                "reviewDecision",
                "files",
                "reviews",
                "additions",
                "deletions",
                "changedFiles",
                "closingIssuesReferences",
            }:
                enriched = []
                for row in rows[:limit]:
                    detail = _read_command(
                        client, "pr", "view", options, [str(row["number"])], timeout=timeout, fresh=fresh
                    )
                    if detail.error:
                        return detail
                    _merge_observation(result, detail)
                    enriched.append(detail.value)
                value = enriched
        else:
            value = _project(result.value, kind)
    elif kind == "repo" and action == "view":
        result = client.request("GET", root, timeout=timeout, fresh=fresh)
        if result.error:
            return result
        value = _project(result.value, "repo")
        permissions = value.get("permissions") or {}
        value.update(
            nameWithOwner=value.get("full_name"),
            isPrivate=value.get("private"),
            visibility=str(value.get("visibility") or ("private" if value.get("private") else "public")).upper(),
            viewerPermission=next(
                (
                    name
                    for flag, name in (
                        ("admin", "ADMIN"),
                        ("maintain", "MAINTAIN"),
                        ("push", "WRITE"),
                        ("triage", "TRIAGE"),
                        ("pull", "READ"),
                    )
                    if permissions.get(flag)
                ),
                None,
            ),
            defaultBranchRef={"name": value.get("default_branch")},
        )
    elif kind == "run" and action in {"list", "view"}:
        if "--job" in options:
            endpoint = f"{root}/actions/jobs/{_opt(options, '--job')}" + ("/logs" if "--log" in options else "")
        else:
            runs_root = (
                f"{root}/actions/workflows/{quote(_opt(options, '--workflow'), safe='')}/runs"
                if "--workflow" in options
                else f"{root}/actions/runs"
            )
            endpoint = runs_root + ("/" + str(number) if action == "view" else "?" + urlencode(query))
        result = client.request("GET", endpoint, timeout=timeout, fresh=fresh)
        if result.error:
            return result
        value = (
            [_project(r, "run") for r in result.value.get("workflow_runs", [])[:limit]]
            if action == "list"
            else _project(result.value, "run")
            if isinstance(result.value, dict)
            else result.value
        )
        if action == "view" and "jobs" in fields and "--job" not in options:
            jobs = _pages(
                client, f"{root}/actions/runs/{number}/jobs?per_page=100", timeout=timeout, fresh=fresh, paginate=True
            )
            if isinstance(jobs, Result):
                return jobs
            value["jobs"] = [
                {
                    **r,
                    "databaseId": r.get("id"),
                    "startedAt": r.get("started_at"),
                    "completedAt": r.get("completed_at"),
                    "status": r.get("status"),
                    "conclusion": r.get("conclusion"),
                }
                for p in jobs
                for r in p.value["jobs"]
            ]
            _merge_observation(result, *jobs)
    elif kind == "release" and action == "view":
        result = client.request(
            "GET",
            root + "/releases/" + ("tags/" + quote(number, safe="") if number else "latest"),
            timeout=timeout,
            fresh=fresh,
        )
        if result.error:
            return result
        value = _project(result.value, "release")
    else:
        return Result(error="github_unsupported_command")
    if kind in {"pr", "issue"} and action == "view" and isinstance(value, dict) and "comments" in fields:
        pages = _pages(
            client, f"{root}/issues/{number}/comments?per_page=100", timeout=timeout, fresh=fresh, paginate=True
        )
        if isinstance(pages, Result):
            return pages
        value["comments"] = [_project(r, "comment") for p in pages for r in p.value]
        _merge_observation(result, *pages)
    if kind == "pr" and action == "view" and isinstance(value, dict):
        for field_name, path in (("files", "files"), ("reviews", "reviews")):
            if field_name in fields:
                pages = _pages(
                    client, f"{root}/pulls/{number}/{path}?per_page=100", timeout=timeout, fresh=fresh, paginate=True
                )
                if isinstance(pages, Result):
                    return pages
                rows = [r for page in pages for r in page.value]
                value[field_name] = (
                    [
                        {
                            "path": r.get("filename"),
                            "additions": r.get("additions"),
                            "deletions": r.get("deletions"),
                            "changeType": {
                                "added": "ADDED",
                                "removed": "DELETED",
                                "modified": "MODIFIED",
                                "renamed": "RENAMED",
                                "copied": "COPIED",
                                "changed": "CHANGED",
                                "unchanged": "UNCHANGED",
                            }.get(r.get("status"), "UNKNOWN"),
                        }
                        for r in rows
                    ]
                    if path == "files"
                    else [_project(r, "comment") for r in rows]
                )
                _merge_observation(result, *pages)
    if (
        kind == "pr"
        and action == "view"
        and isinstance(value, dict)
        and set(fields) & {"reviewDecision", "closingIssuesReferences", "autoMergeRequest"}
    ):
        selections = []
        if "reviewDecision" in fields:
            selections.append("reviewDecision")
        # REST auto_merge has no enabledAt timestamp used by closeout readers.
        if "autoMergeRequest" in fields:
            selections.append("autoMergeRequest{enabledAt}")
        if "closingIssuesReferences" in fields:
            selections.append("closingIssuesReferences(first:100){totalCount pageInfo{hasNextPage} nodes{number url}}")
        owner, name = repo.split("/", 1)
        query = (
            "query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){"
            + " ".join(selections)
            + "}}}"
        )
        aggregate = client.request(
            "POST",
            "graphql",
            payload={"query": query, "variables": {"owner": owner, "name": name, "number": int(number)}},
            timeout=timeout,
            fresh=fresh,
        )
        if aggregate.error:
            return aggregate
        pull = (aggregate.value.get("data") or {}).get("repository", {}).get("pullRequest")
        if not isinstance(pull, dict):
            return Result(error="github_pr_aggregate_unknown")
        if "closingIssuesReferences" in fields:
            references = pull.get("closingIssuesReferences")
            if (
                not isinstance(references, dict)
                or references.get("pageInfo", {}).get("hasNextPage")
                or references.get("totalCount") != len(references.get("nodes", []))
            ):
                return Result(error="github_closing_references_incomplete")
            pull["closingIssuesReferences"] = references["nodes"]
        value.update(pull)
        _merge_observation(result, aggregate)
    if fields != [""]:
        if isinstance(value, list):
            value = [{f: row.get(f) for f in fields} for row in value]
        elif isinstance(value, dict):
            value = {f: value.get(f) for f in fields}
    result.value = value
    return result


def _write_command(client, kind, action, options, positional, *, timeout, input=None):
    if (
        client.env.get("AGENT_NO_MERGE") == "1"
        and kind == "pr"
        and (action == "merge" or (action == "review" and "--approve" in options))
    ):
        return Result(error="github_worker_write_forbidden")
    repo = _repo(options, client) if kind != "gist" else ""
    root = f"repos/{repo}"
    number = positional[0] if positional else None
    payload = {}
    for key in ("title", "body", "head", "base", "color", "description", "ref", "name"):
        if "--" + key in options:
            payload[key] = _opt(options, "--" + key)
    if "--body-file" in options:
        source = _opt(options, "--body-file")
        payload["body"] = (
            (input.decode() if isinstance(input, bytes) else input) if source == "-" else Path(source).read_text()
        )
    if kind in {"pr", "issue"}:
        endpoint = root + ("/pulls" if kind == "pr" else "/issues")
        if action == "create":
            if kind == "pr":
                payload["draft"] = "--draft" in options
            if "--label" in options:
                payload["labels"] = options["--label"]
            method = "POST"
        else:
            endpoint += "/" + str(number)
            method = "PATCH"
            if action == "comment":
                endpoint, method = f"{root}/issues/{number}/comments", "POST"
            elif action in {"close", "reopen"}:
                payload["state"] = "closed" if action == "close" else "open"
                if "--reason" in options:
                    payload["state_reason"] = "completed" if _opt(options, "--reason") == "completed" else "not_planned"
            elif action == "review":
                endpoint += "/reviews"
                method = "POST"
                payload["event"] = (
                    "APPROVE"
                    if "--approve" in options
                    else "REQUEST_CHANGES"
                    if "--request-changes" in options
                    else "COMMENT"
                )
            elif action == "update-branch":
                endpoint += "/update-branch"
                method = "PUT"
            elif action in {"ready", "merge"}:
                owner, name = repo.split("/", 1)
                query = "query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){id isMergeQueueEnabled}}}"
                queue = client.request(
                    "POST",
                    "graphql",
                    payload={"query": query, "variables": {"owner": owner, "name": name, "number": int(number)}},
                    timeout=timeout,
                    fresh=True,
                )
                if queue.error:
                    return queue
                pull = queue.value.get("data", {}).get("repository", {}).get("pullRequest")
                if not isinstance(pull, dict) or not pull.get("id"):
                    return Result(error="github_queue_unknown")
                if action == "ready" or "--disable-auto" in options or pull.get("isMergeQueueEnabled"):
                    mutation = (
                        "markPullRequestReadyForReview"
                        if action == "ready"
                        else "disablePullRequestAutoMerge"
                        if "--disable-auto" in options
                        else "enqueuePullRequest"
                    )
                    input_payload = {"pullRequestId": pull["id"]}
                    if action == "merge" and "--disable-auto" not in options and _opt(options, "--match-head-commit"):
                        input_payload["expectedHeadOid"] = _opt(options, "--match-head-commit")
                    return client.request(
                        "POST",
                        "graphql",
                        payload={
                            "query": f"mutation($input:{mutation[0].upper() + mutation[1:]}Input!){{{mutation}(input:$input){{clientMutationId}}}}",
                            "variables": {"input": input_payload},
                        },
                        timeout=timeout,
                        fresh=True,
                    )
                if pull.get("isMergeQueueEnabled") is not False:
                    return Result(error="github_queue_unknown")
                endpoint += "/merge"
                method = "PUT"
                payload = {
                    "merge_method": "squash",
                    "sha": _opt(options, "--match-head-commit"),
                    "commit_title": _opt(options, "--subject"),
                    "commit_message": payload.get("body"),
                }
                payload = {k: v for k, v in payload.items() if v is not None}
            elif action != "edit":
                return Result(error="github_unsupported_command")
            if action == "close" and "--comment" in options:
                comment = client.request(
                    "POST",
                    f"{root}/issues/{number}/comments",
                    payload={"body": _opt(options, "--comment")},
                    timeout=timeout,
                    fresh=True,
                )
                if comment.error:
                    return comment
        if action in {"create", "edit"} and (
            "--add-label" in options
            or "--remove-label" in options
            or "--label" in options
            or "--milestone" in options
            or "--remove-milestone" in options
        ):
            if kind == "pr" and action == "edit":
                endpoint = f"{root}/issues/{number}"
            if "--add-label" in options or "--remove-label" in options:
                labels = client.request("GET", f"{root}/issues/{number}/labels", timeout=timeout, fresh=True)
                if labels.error:
                    return labels
                payload["labels"] = sorted(
                    ({r["name"] for r in labels.value} | set(options.get("--add-label", [])))
                    - set(options.get("--remove-label", []))
                )
            if "--remove-milestone" in options:
                payload["milestone"] = None
            elif "--milestone" in options:
                milestones = _pages(
                    client, f"{root}/milestones?state=all&per_page=100", timeout=timeout, fresh=True, paginate=True
                )
                if isinstance(milestones, Result):
                    return milestones
                target = _opt(options, "--milestone")
                matched = next((r["number"] for page in milestones for r in page.value if r["title"] == target), None)
                if matched is None:
                    return Result(error="github_milestone_not_found")
                payload["milestone"] = matched
    elif kind == "run" and action == "rerun":
        endpoint, method = (
            f"{root}/actions/runs/{number}/rerun" + ("-failed-jobs" if "--failed" in options else ""),
            "POST",
        )
    elif kind == "workflow" and action == "run":
        endpoint, method = f"{root}/actions/workflows/{quote(number, safe='')}/dispatches", "POST"
    elif kind == "gist" and action == "create":
        endpoint, method = "gists", "POST"
        payload["public"] = "--public" in options
        payload["files"] = {Path(path).name: {"content": Path(path).read_text()} for path in positional}
    elif kind == "release" and action in {"create", "edit", "upload"}:
        tag, *assets = positional
        if action == "create":
            payload = {
                "tag_name": tag,
                "name": payload.pop("title", tag),
                "body": Path(_opt(options, "--notes-file")).read_text() if "--notes-file" in options else "",
                "target_commitish": _opt(options, "--target"),
            }
            payload = {k: v for k, v in payload.items() if v is not None}
            for flag in ("draft", "prerelease"):
                if "--" + flag in options:
                    payload[flag] = _opt(options, "--" + flag) in {True, "true"}
            result = client.request("POST", f"{root}/releases", payload=payload, timeout=timeout, fresh=True)
        else:
            result = client.request("GET", f"{root}/releases/tags/{quote(tag, safe='')}", timeout=timeout, fresh=True)
        if result.error:
            return result
        release = result.value
        if action == "edit":
            payload = {"name": payload["title"]} if "title" in payload else {}
            if "--notes-file" in options:
                payload["body"] = Path(_opt(options, "--notes-file")).read_text()
            for flag in ("draft", "prerelease"):
                if "--" + flag in options:
                    payload[flag] = _opt(options, "--" + flag) in {True, "true"}
            return client.request(
                "PATCH", f"{root}/releases/{release['id']}", payload=payload, timeout=timeout, fresh=True
            )
        for asset in assets:
            name = Path(asset).name
            if "--clobber" in options:
                for existing in release.get("assets", []):
                    if existing.get("name") == name:
                        removed = client.request(
                            "DELETE", f"{root}/releases/assets/{existing['id']}", timeout=timeout, fresh=True
                        )
                        if removed.error:
                            return removed
            upload = release["upload_url"].split("{", 1)[0] + "?" + urlencode({"name": name})
            result = client.request(
                "POST",
                upload,
                payload=Path(asset).read_bytes(),
                headers={"Content-Type": "application/octet-stream"},
                timeout=timeout,
                fresh=True,
            )
            if result.error:
                return result
        return result
    elif kind == "label" and action in {"create", "edit"}:
        endpoint, method = (
            f"{root}/labels" + ("/" + quote(number, safe="") if action == "edit" else ""),
            "POST" if action == "create" else "PATCH",
        )
        payload["name"] = payload.get("name", number)
    else:
        return Result(error="github_unsupported_command")
    return client.request(method, endpoint, payload=payload, timeout=timeout, fresh=True)


def _format_value(value, options, *, api=False):
    expression = _opt(options, "--jq", "-q")
    if expression:
        # jq stays local: gh must not fetch again to format a cached response.
        p = subprocess.run(
            ["jq", "-r", expression], input=json.dumps(value), text=True, capture_output=True, check=True, timeout=5
        )
        return p.stdout.encode()
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode()
    if not api and "--json" not in options and isinstance(value, dict) and value.get("html_url"):
        return (value["html_url"] + "\n").encode()
    return json.dumps(value, ensure_ascii=False).encode()


def _run_command(args, *, runner=None, client=None, fresh=False, **kwargs):
    """subprocess.run-compatible seam; non-GitHub commands pass through.

    A CompletedProcess carries ``github_result``. Stale reads also emit a
    typed diagnostic to stderr, never a silently fresh status. Admission of
    public writes remains the caller's responsibility.
    """
    if not args or Path(str(args[0])).name not in {"gh", "gh.real"}:
        return (runner or subprocess.run)(args, **kwargs)
    if args[1:] in (["--version"], ["version"]):
        environment = colour_safe_environment(kwargs.get("env"))
        kwargs["env"] = environment
        if runner is None:
            from scripts.opsec.prepublish import PublishBlocked, real_gh

            try:
                executable = real_gh({**environment, "AGENT_ORIGINAL_PATH": environment.get("PATH", os.defpath)})
            except PublishBlocked:
                return _result_process(args, Result(error="github_transport_unavailable"), {}, kwargs)
            args = [executable, *args[1:]]
        return (runner or subprocess.run)(args, **kwargs)
    limit = kwargs.pop("max_response_bytes", None)
    if limit is not None and (type(limit) is not int or limit < 0):
        raise ValueError("invalid GitHub response byte limit")
    if client is not None and limit is not None:
        from copy import copy

        client = copy(client)
        client.max_response_bytes = (
            min(client.max_response_bytes, limit) if client.max_response_bytes is not None else limit
        )
    client = client or GitHubClient(
        env=kwargs.get("env"), cwd=kwargs.get("cwd"), runner=runner, max_response_bytes=limit
    )
    timeout = kwargs.get("timeout") or 30
    if args[1:3] == ["auth", "status"]:
        # Authentication health is a conditional identity read, not an opaque
        # CLI network request whose response headers cannot be observed.
        result = client.request("GET", "user", timeout=timeout, fresh=fresh)
        return _result_process(args, result, {}, kwargs)
    options, positional = _options(args[2:] if args[1] == "api" else args[3:])
    for short, long in {
        "-s": "--state",
        "-B": "--base",
        "-l": "--label",
        "-S": "--search",
        "-A": "--author",
        "-a": "--assignee",
    }.items():
        if short in options and long not in options:
            options[long] = options[short]
    if "--hostname" in options:
        client.host = _opt(options, "--hostname")
        client.scope = hashlib.sha256((client.scope + "\0" + client.host).encode()).hexdigest()
    if args[1] == "api":
        request_headers = {}
        for raw_header in options.get("-H", []) + options.get("--header", []):
            name, _, value = raw_header.partition(":")
            request_headers[name.strip()] = value.strip()
        endpoint = positional[0]
        payload = None
        frozen_input = None
        if "--input" in options:
            source = _opt(options, "--input")
            raw = kwargs.get("input") if source == "-" else Path(source).read_bytes()
            payload = json.loads(raw)
            frozen_input = raw.encode() if isinstance(raw, str) else raw
        for flag in ("-f", "--raw-field", "-F", "--field"):
            for value in options.get(flag, []):
                key, _, data = value.partition("=")
                frozen_input = None
                payload = payload or {}
                payload[key] = (
                    data
                    if flag in {"-f", "--raw-field"}
                    else json.loads(data)
                    if data.isdigit() or data in {"true", "false", "null"}
                    else data
                )
        method = _opt(options, "--method", "-X", default="POST" if payload else "GET")
        if method == "GET" and payload:
            endpoint += ("&" if "?" in endpoint else "?") + urlencode(payload)
            payload = None
            frozen_input = None
        elif frozen_input is not None:
            payload = frozen_input
        if "--paginate" in options and method == "GET":
            pages = _pages(client, endpoint, timeout=timeout, fresh=fresh, paginate=True)
            if isinstance(pages, Result):
                result = pages
            else:
                result = pages[0]
                result.value = (
                    [p.value for p in pages]
                    if "--slurp" in options
                    else [item for p in pages for item in p.value]
                    if all(isinstance(p.value, list) for p in pages)
                    else pages[0].value
                )
                _merge_observation(result, *pages)
        else:
            result = client.request(
                method, endpoint, payload=payload, timeout=timeout, fresh=fresh, headers=request_headers
            )
    else:
        kind, action = args[1:3]
        if action == "download":
            result = _download_command(client, kind, options, positional, timeout=timeout)
        elif action in {"view", "list", "checks", "diff"}:
            result = _read_command(client, kind, action, options, positional, timeout=timeout, fresh=fresh)
        else:
            result = _write_command(
                client, kind, action, options, positional, timeout=timeout, input=kwargs.get("input")
            )
    return _result_process(args, result, options, kwargs, api=args[1] == "api")


def run(args, *, runner=None, client=None, fresh=False, **kwargs):
    """Return command/configuration errors through the subprocess contract."""
    try:
        return _run_command(args, runner=runner, client=client, fresh=fresh, **kwargs)
    except ValueError:
        return _result_process(args, Result(error="github_invalid_command"), {}, kwargs)


def check_output(args, **kwargs):
    kwargs.pop("check", None)
    return run(args, check=True, stdout=subprocess.PIPE, **kwargs).stdout


def http_open(request, *, timeout=30, opener=None, **kwargs):
    """HTTP seam for existing TLS/redirect-constrained GitHub integrations.

    The supplied opener keeps its security policy. Credential lifecycle
    responses are never cached; only budget headers are persisted.
    """
    import io
    import urllib.error
    import urllib.request

    host = urlparse(request.full_url).hostname
    client = GitHubClient(
        env={
            "GH_HOST": "github.com" if host in {"api.github.com", "uploads.github.com"} else host or "github.com",
            "GH_TOKEN": request.get_header("Authorization") or "http-unauthenticated",
            "GH_ENTERPRISE_TOKEN": request.get_header("Authorization") or "http-unauthenticated",
        }
    )
    method = request.get_method()

    def transport(_method, endpoint, headers, body, request_timeout):
        for key, value in headers.items():
            if key.lower() not in {k.lower() for k in request.headers}:
                request.add_header(key, value)
        try:
            opened = (opener or urllib.request.urlopen)(request, timeout=request_timeout, **kwargs)
        except urllib.error.HTTPError as exc:
            opened = exc
        with opened as response:
            return Response(response.status, dict(response.headers.items()), response.read())

    client.transport = transport
    # POST/DELETE token endpoints contain sensitive responses and have no read cache.
    result = client.request(
        method,
        request.full_url,
        payload=None,
        timeout=timeout,
        fresh=True,
        raw_response=True,
        headers=dict(request.header_items()),
    )
    if result.error and result.error != "github_rate_limited":
        encoded = json.dumps(result.value).encode()
        raise urllib.error.HTTPError(
            request.full_url, result.status, "GitHub HTTP request failed", result.headers, io.BytesIO(encoded)
        )
    value = result.require_fresh()
    stream = io.BytesIO(value if isinstance(value, bytes) else json.dumps(value).encode() if value is not None else b"")
    stream.status = result.status
    stream.headers = result.headers
    return stream


def command(args, *, runner=None, **kwargs):
    """Preserve the publisher's injectable whole-command test seam.

    Production uses ``run``; injected command executors replace the entire
    client, rather than pretending to be an HTTP transport. HTTP-level tests
    inject GitHubClient.transport instead.
    """
    if runner is None:
        return run(args, **kwargs)
    kwargs["env"] = colour_safe_environment(kwargs.get("env"))
    return runner(args, **kwargs)


def rest_read(operation, repo, fields, *, runner=None, env=None, cwd=None, **kwargs):
    """REST equivalents of former named GraphQL reads, with legacy shapes."""
    client = GitHubClient(env=env, cwd=cwd)
    observed = []

    def get(endpoint, *, paginate=False, optional=False):
        args = ["gh", "api", "--method", "GET", endpoint]
        if paginate:
            args += ["--paginate"]
        proc = (
            command(
                args,
                runner=runner,
                client=client,
                fresh=operation != "budget",
                capture_output=True,
                text=True,
                cwd=cwd,
                env=env,
                timeout=kwargs.get("timeout"),
            )
            if runner is None
            else command(
                args, runner=runner, capture_output=True, text=True, cwd=cwd, env=env, timeout=kwargs.get("timeout")
            )
        )
        observed.append(getattr(proc, "github_result", None))
        if proc.returncode:
            observation = getattr(proc, "github_result", None)
            if optional and observation and observation.status == 404:
                return None
            if optional and runner is not None:
                # Command adapters may serialize the client's typed result.
                with suppress(ValueError, TypeError):
                    detail = json.loads(proc.stdout)
                    if detail.get("error") == "github_http_error" and detail.get("status") == 404:
                        return None
            if getattr(proc, "github_result", None) and proc.github_result.error == "github_rate_limited":
                raise GitHubRateLimited(proc.github_result.reset_at)
            raise RuntimeError("GitHub REST read failed")
        return json.loads(proc.stdout)

    root = f"repos/{repo}"
    try:
        if operation == "budget":
            rate = get("rate_limit")["resources"]["graphql"]
            from datetime import UTC, datetime

            value = {
                "data": {
                    "rateLimit": {
                        **{k: rate[k] for k in ("limit", "remaining", "used")},
                        "resetAt": datetime.fromtimestamp(rate["reset"], UTC).isoformat().replace("+00:00", "Z"),
                    }
                }
            }
        elif operation == "default-head":
            repository = get(root)
            branch = repository["default_branch"]
            head = get(root + "/commits/" + quote(branch, safe=""))
            value = {
                "data": {
                    "repository": {
                        "nameWithOwner": repository["full_name"],
                        "defaultBranchRef": {"name": branch, "target": {"oid": head["sha"]}},
                    }
                }
            }
        elif operation == "pr-bases":
            rows = get(root + "/pulls?state=open&per_page=100", paginate=True)
            count = get("search/issues?" + urlencode({"q": f"repo:{repo} is:pr is:open", "per_page": 1}))
            if count.get("incomplete_results") is not False or type(count.get("total_count")) is not int:
                raise ValueError("incomplete GitHub search")
            value = {
                "data": {
                    "repository": {
                        "pullRequests": {
                            "totalCount": count["total_count"],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [{"number": r["number"], "baseRefOid": r["base"]["sha"]} for r in rows],
                        }
                    }
                }
            }
        elif operation == "issue-states":
            states = {}
            for number in fields["numbers"]:
                issue = get(root + f"/issues/{number}", optional=True)
                states[f"i{number}"] = {"number": number, "state": str(issue["state"]).upper()} if issue else None
            value = {"data": {"repository": states}}
        elif operation in {"issue-parent", "issue-scope", "subissues", "subissues-next", "subissue-batch"}:

            def connection(number, cursor=None):
                if cursor is not None:
                    # This client returns complete REST collections. An opaque
                    # GraphQL cursor cannot safely be reinterpreted as a page.
                    raise ValueError("obsolete GitHub pagination cursor")
                rows = get(root + f"/issues/{number}/sub_issues?per_page=100", paginate=True)
                nodes = [
                    {
                        "number": r["number"],
                        "repository": {"nameWithOwner": r["repository_url"].split("/repos/", 1)[1]},
                        "subIssuesSummary": {"total": (r.get("sub_issues_summary") or {}).get("total")},
                    }
                    for r in rows
                ]
                return {"nodes": nodes, "pageInfo": {"hasNextPage": False, "endCursor": None}}

            if operation == "subissue-batch":
                issues = {}
                for number, cursor in fields["cursors"].items():
                    parent = get(root + f"/issues/{number}", optional=True)
                    if parent is None:
                        issues[f"i{number}"] = None
                        continue
                    issue = {"subIssues": connection(number, cursor)}
                    if number in fields["body_roots"] and cursor is None:
                        issue["body"] = parent["body"]
                    issues[f"i{number}"] = issue
                value = {"data": {"repository": issues}}
            else:
                number = fields["number"]
                issue = get(root + f"/issues/{number}")
                if operation in {"issue-parent", "issue-scope"}:
                    parent = get(root + f"/issues/{number}/parent", optional=True)
                    parent = (
                        {
                            "number": parent["number"],
                            "url": parent["html_url"],
                            "repository": {"nameWithOwner": parent["repository_url"].split("/repos/", 1)[1]},
                        }
                        if parent
                        else None
                    )
                    row = {
                        "number": number,
                        "state": str(issue["state"]).upper(),
                        "url": issue["html_url"],
                        "parent": parent,
                    }
                    if operation == "issue-scope":
                        row.update(body=issue["body"], labels={"nodes": [{"name": r["name"]} for r in issue["labels"]]})
                else:
                    row = {"body": issue["body"], "subIssues": connection(number, fields.get("cursor"))}
                value = {"data": {"repository": {"nameWithOwner": repo, "issue": row}}}
        elif operation == "merge-facts":
            groups = {}
            for slug, number in fields["batch"]:
                groups.setdefault(slug, []).append(number)
            value = {
                "data": {
                    f"r{i}": {f"p{n}": {"mergedAt": get(f"repos/{slug}/pulls/{n}")["merged_at"]} for n in numbers}
                    for i, (slug, numbers) in enumerate(groups.items())
                }
            }
        else:
            raise ValueError("unknown REST read")
    except GitHubRateLimited as exc:
        result = Result(error=exc.code, reset_at=exc.reset_at, status=429)
    except (ValueError, KeyError, TypeError):
        result = Result(error="github_invalid_read")
    except RuntimeError:
        result = Result(error="github_read_failed", status=502)
    else:
        result = Result(
            value,
            stale=any(r.stale for r in observed if r),
            age_seconds=max((r.age_seconds for r in observed if r), default=0),
            reset_at=next((r.reset_at for r in observed if r and r.reset_at), None),
        )
    return _result_process(["github", operation], result, {}, kwargs)


def queue_read(operation, repo, fields, *, env=None, cwd=None, **kwargs):
    """Queue-only GraphQL fields joined to ordinary conditional REST reads."""
    client = GitHubClient(env=env, cwd=cwd)
    timeout = kwargs.get("timeout") or 30
    owner, name = repo.split("/", 1)
    observations = []
    if operation == "queue-snapshot":
        proc = run(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                repo,
                "--state",
                "open",
                "--limit",
                "1000",
                "--json",
                "id,number,title,isDraft,headRefOid,baseRefName,mergeStateStatus,labels",
            ],
            client=client,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        ordinary = proc.github_result
        observations.append(ordinary)
        if ordinary.error:
            return _result_process(["github", operation], ordinary, {}, kwargs)
        rows = ordinary.value
        selections = " ".join(
            f"p{r['number']}:pullRequest(number:{r['number']}){{isInMergeQueue autoMergeRequest{{enabledAt}}}}"
            for r in rows
        )
        selections += " " + " ".join(
            f"q{i}:mergeQueue(branch:{json.dumps(branch)}){{url}}"
            for i, branch in enumerate(sorted(fields["branches"]))
        )
        query = (
            "query($owner:String!,$name:String!){rateLimit{remaining cost resetAt} repository(owner:$owner,name:$name){"
            + selections
            + "}}"
        )
        response = client.request(
            "POST", "graphql", payload={"query": query, "variables": {"owner": owner, "name": name}}, timeout=timeout
        )
        if response.error:
            return _result_process(["github", operation], response, {}, kwargs)
        observations.append(response)
        data = response.value.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("repository"), dict):
            return _result_process(["github", operation], Result(error="github_queue_unknown"), {}, kwargs)
        repository = data["repository"]
        for row in rows:
            membership = repository.pop(f"p{row['number']}", None)
            row["isInMergeQueue"] = membership.get("isInMergeQueue") if isinstance(membership, dict) else None
            row["autoMergeRequest"] = membership.get("autoMergeRequest") if isinstance(membership, dict) else None
        repository["pullRequests"] = {"totalCount": len(rows), "pageInfo": {"hasNextPage": False}, "nodes": rows}
        value = response.value
    elif operation == "queue-status":
        proc = run(
            [
                "gh",
                "pr",
                "view",
                str(fields["number"]),
                "--repo",
                repo,
                "--json",
                "number,title,state,merged,mergeable,mergeStateStatus,headRefName,headRefOid,baseRefName",
            ],
            client=client,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        ordinary = proc.github_result
        if ordinary.error:
            return _result_process(["github", operation], ordinary, {}, kwargs)
        observations.append(ordinary)
        query = "query($owner:String!,$name:String!,$number:Int!,$branch:String!){repository(owner:$owner,name:$name){pullRequest(number:$number){isInMergeQueue isMergeQueueEnabled mergeQueueEntry{id position state enqueuedAt estimatedTimeToMerge jump solo headCommit{oid}}} mergeQueue(branch:$branch){url nextEntryEstimatedTimeToMerge entries(first:50){totalCount nodes{position state enqueuedAt estimatedTimeToMerge pullRequest{number}}}}}}"
        response = client.request(
            "POST",
            "graphql",
            payload={"query": query, "variables": {"owner": owner, "name": name, **fields}},
            timeout=timeout,
        )
        if response.error:
            return _result_process(["github", operation], response, {}, kwargs)
        observations.append(response)
        value = response.value
        repository = (value.get("data") or {}).get("repository")
        if isinstance(repository, dict) and isinstance(repository.get("pullRequest"), dict):
            repository["pullRequest"] = {**ordinary.value, **repository["pullRequest"]}
    else:
        raise ValueError("unknown queue operation")
    result = Result(
        value,
        stale=any(r.stale for r in observations),
        age_seconds=max(r.age_seconds for r in observations),
        reset_at=next((r.reset_at for r in observations if r.reset_at), None),
    )
    return _result_process(["github", operation], result, {}, kwargs)


def _result_process(args, result, options, kwargs, *, api=True):
    if result.error:
        detail = {"error": result.error, "reset_at": result.reset_at}
        if result.error == "github_http_error":
            detail["status"] = result.status
        output = json.dumps(detail).encode()
        error = output
        code = 75 if result.error == "github_rate_limited" else 1
    else:
        output = _format_value(result.value, options, api=api)
        error = (
            json.dumps({"stale": True, "age_seconds": result.age_seconds, "reset_at": result.reset_at}).encode()
            if result.stale
            else b""
        )
        code = 0
    if kwargs.get("text") or kwargs.get("universal_newlines") or kwargs.get("encoding"):
        output, error = output.decode(kwargs.get("encoding") or "utf-8"), error.decode()
    completed = subprocess.CompletedProcess(args, code, output, error)
    completed.github_result = result
    for key, content in (("stdout", output), ("stderr", error)):
        target = kwargs.get(key)
        if target not in (None, subprocess.PIPE, subprocess.DEVNULL, subprocess.STDOUT):
            target.write(content)
        elif target is None and not kwargs.get("capture_output"):
            import sys

            stream = getattr(sys, key)
            if isinstance(content, bytes):
                stream.buffer.write(content)
            else:
                stream.write(content)
    if kwargs.get("check") and code:
        failure = subprocess.CalledProcessError(code, args, output=output, stderr=error)
        failure.github_result = result
        raise failure
    return completed


def _download_command(client, kind, options, positional, *, timeout):
    import fnmatch
    import io
    import stat
    import zipfile

    repo = _repo(options, client)
    root = f"repos/{repo}"
    pattern = _opt(options, "--pattern", "-p", default="*")
    if kind == "release":
        tag = positional[0] if positional else None
        release = client.request(
            "GET",
            root + "/releases/" + ("tags/" + quote(tag, safe="") if tag else "latest"),
            timeout=timeout,
            fresh=True,
        )
        if release.error:
            return release
        selected = [r for r in release.value.get("assets", []) if fnmatch.fnmatchcase(r["name"], pattern)]
    elif kind == "run":
        pages = _pages(
            client,
            f"{root}/actions/runs/{positional[0]}/artifacts?per_page=100",
            timeout=timeout,
            fresh=True,
            paginate=True,
        )
        if isinstance(pages, Result):
            return pages
        selected = [
            r
            for page in pages
            for r in page.value["artifacts"]
            if fnmatch.fnmatchcase(r["name"], pattern) and not r.get("expired")
        ]
    else:
        return Result(error="github_unsupported_command")
    if not selected:
        return Result(error="github_asset_not_found")
    output = _opt(options, "--output", "-O")
    if output and len(selected) != 1:
        return Result(error="github_asset_ambiguous")
    directory = Path(_opt(options, "--dir", "-D", default=client.cwd or Path.cwd()))
    for row in selected:
        endpoint = f"{root}/releases/assets/{row['id']}" if kind == "release" else row["archive_download_url"]
        downloaded = client.request(
            "GET", endpoint, headers={"Accept": "application/octet-stream"}, timeout=timeout, fresh=True
        )
        if downloaded.error:
            return downloaded
        if not isinstance(downloaded.value, bytes):
            return Result(error="github_asset_invalid")
        if output == "-":
            return downloaded
        if kind == "release":
            destination = Path(output) if output else directory / row["name"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(downloaded.value)
        else:
            destination = directory if len(selected) == 1 else directory / row["name"]
            destination.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(downloaded.value)) as archive:
                for member in archive.infolist():
                    path = Path(member.filename)
                    if path.is_absolute() or ".." in path.parts or stat.S_ISLNK(member.external_attr >> 16):
                        return Result(error="github_archive_unsafe")
                    target = (destination / path).resolve()
                    if not target.is_relative_to(destination.resolve()):
                        return Result(error="github_archive_unsafe")
                archive.extractall(destination)
    return Result("")


def timer(function):
    """A timer skips one run on a typed limit; it does not wait or retry."""
    from functools import wraps

    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except GitHubRateLimited as exc:
            print(f"GitHub timer: skipped github_rate_limited reset_at={exc.reset_at}")
            return 0
        except subprocess.CalledProcessError as exc:
            observation = getattr(exc, "github_result", None)
            if (
                exc.returncode != 75
                or not isinstance(observation, Result)
                or observation.error != "github_rate_limited"
            ):
                raise
            reset = observation.reset_at
            print(f"GitHub timer: skipped github_rate_limited reset_at={reset}")
            return 0

    return wrapped


def rate_limited_command(function):
    """Keep an exhausted publishing preflight in the typed command contract."""
    from functools import wraps

    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except GitHubRateLimited as exc:
            result = Result(error=exc.code, reset_at=exc.reset_at, status=429)
            return _result_process(["github", "publish"], result, {}, kwargs)

    return wrapped
