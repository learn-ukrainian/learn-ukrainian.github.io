"""Browser-local dual-source Work projection proofs (unified P3).

Source-blind fixtures only. Never prints private payloads. Does not require a
real private repository or live adapter process.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORK_HTML = ROOT / "dashboards" / "work.html"
PRIVATE_URL = "http://127.0.0.1:8769/v1/projection"
PUBLIC_PATH = "/api/work/v1/projection"
SCHEMA_DIGEST = "89fb9c1eec41baaa00a328d456340111163c1e3ab899cd7baa15e284fff65bde"
PUBLIC_COMMIT = "f522c8dba5a68d86fe29d1a36bd8cfeb8c3acb9d"
PUBLIC_REPO = "learn-ukrainian/learn-ukrainian.github.io"
# Source-blind synthetic private slug — not a real private repository identifier.
SYNTH_PRIVATE_REPO = "fixture-owner/fixture-repo"
CANARY = "FX07_CANARY_SHOULD_NEVER_APPEAR_IN_DOM_OR_URL"
FIXED_PUBLIC_PORT = 8765
FIXED_PRIVATE_PORT = 8769
# Linux system Chrome/Chromium candidates for CI runners without Puppeteer's cache.
LINUX_CHROME_CANDIDATES: tuple[str, ...] = (
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
)


def _node_modules() -> Path | None:
    candidates: list[Path] = [ROOT / "node_modules"]
    # Dispatch worktrees live under .worktrees/dispatch/<agent>/<task>/
    if len(ROOT.parents) >= 4:
        candidates.append(ROOT.parents[3] / "node_modules")
    try:
        common = subprocess.check_output(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=ROOT,
            text=True,
            timeout=5,
        ).strip()
        # git-common-dir is <repo>/.git → parents[0] is repo root when bare path ends with .git
        git_path = Path(common)
        repo_root = git_path.parent if git_path.name == ".git" else git_path
        candidates.append(repo_root / "node_modules")
    except (subprocess.SubprocessError, OSError):
        pass
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve() if candidate.exists() else candidate
        if resolved in seen:
            continue
        seen.add(resolved)
        if (candidate / "puppeteer").exists():
            return candidate
    return None


def _require_puppeteer() -> Path:
    nm = _node_modules()
    if nm is None:
        pytest.skip("puppeteer not available for headless browser proofs")
    return nm


def _path_is_executable(path: str) -> bool:
    candidate = Path(path)
    return candidate.is_file() and os.access(candidate, os.X_OK)


def _resolve_chrome_executable(
    *,
    env: Mapping[str, str] | None = None,
    candidates: Sequence[str] | None = None,
    is_executable: Callable[[str], bool] | None = None,
) -> str | None:
    """Pick a Chrome/Chromium binary for Puppeteer, or None for managed browser.

    Order:
    1. ``PUPPETEER_EXECUTABLE_PATH`` when it names an existing executable
    2. First existing Linux system candidate
    3. None — omit ``executablePath`` so local Puppeteer uses its cache
    """
    check = is_executable or _path_is_executable
    environ = env if env is not None else os.environ
    env_path = (environ.get("PUPPETEER_EXECUTABLE_PATH") or "").strip()
    if env_path and check(env_path):
        return env_path
    for candidate in candidates if candidates is not None else LINUX_CHROME_CANDIDATES:
        if check(candidate):
            return candidate
    return None


def _puppeteer_launch_options(
    *,
    env: Mapping[str, str] | None = None,
    candidates: Sequence[str] | None = None,
    is_executable: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    """Deterministic launch options shared by every Puppeteer script here."""
    options: dict[str, Any] = {
        "headless": "new",
        "args": ["--no-sandbox", "--disable-setuid-sandbox"],
    }
    executable = _resolve_chrome_executable(
        env=env,
        candidates=candidates,
        is_executable=is_executable,
    )
    if executable is not None:
        options["executablePath"] = executable
    return options


def _public_min() -> dict[str, Any]:
    item = {
        "work_id": f"wp1:public-monitor:{PUBLIC_REPO}:issue:5921",
        "source_id": "public-monitor",
        "repository_id": PUBLIC_REPO,
        "resource_kind": "issue",
        "remote_id": "5921",
        "title": "Public attention item",
        "lifecycle": "open",
        "labels": ["infrastructure"],
        "assignees": [],
        "urls": {
            "html": f"https://github.com/{PUBLIC_REPO}/issues/5921",
        },
        "timestamps": {
            "created_at": "2026-08-16T00:00:00Z",
            "updated_at": "2026-08-16T00:00:00Z",
        },
        "projections": {
            "stream": {
                "status": "orphan",
                "streams": [],
                "fresh": True,
                "authority_missing": False,
            },
            "dispatch": {"task_ids": [], "statuses": [], "unresolved": False},
            "review": {
                "review_ids": [],
                "states": [],
                "sealed_verdict_available": False,
            },
            "verification": {"kind": "none", "state": "n/a"},
        },
        "relationships": [],
        "health": "AT_RISK",
        "attention_rank": 0,
        "safe_next_action": {
            "code": "TRIAGE_ORPHAN",
            "reason_codes": ["stream_orphan"],
        },
        "authority": [
            {
                "domain": "github",
                "observed_at": "2026-08-16T00:00:00Z",
                "age_s": 0,
                "stale": False,
            }
        ],
        "omissions": [],
        "flags": {"orphan": True, "has_blocker": False},
    }
    return {
        "schema_version": "work-projection.v1",
        "generated_at": "2026-08-16T00:00:00Z",
        "cache_age_s": 1.0,
        "budget": {"warm_target_s": 2, "timeout_s": 5},
        "sources": [
            {
                "source_id": "public-monitor",
                "status": "ok",
                "freshness": {"observed_at": "2026-08-16T00:00:00Z", "age_s": 1.0},
                "capabilities": {"mutation": False, "private_fields": False},
                "truncation": {"issues": False, "prs": False, "limit": 1000},
                "sections": {
                    "issues": {"status": "ok", "count": 1},
                    "prs": {"status": "ok", "count": 0},
                    "streams": {"status": "ok", "count": 1},
                    "delegate_active": {"status": "ok", "count": 0},
                    "delegate_tasks": {"status": "ok", "count": 0},
                    "fleet_reviews": {"status": "ok", "count": 0},
                },
            },
            {
                "source_id": "private-local-adapter",
                "status": "unavailable",
                "freshness": {"observed_at": None, "age_s": None},
                "capabilities": {"mutation": False, "private_fields": False},
                "truncation": {"issues": False, "prs": False, "limit": 1000},
                "sections": {},
                "reason": "not_configured",
            },
        ],
        "items": [item],
        "attention": [
            {
                "work_id": item["work_id"],
                "attention_rank": 0,
                "health": item["health"],
                "safe_next_action": item["safe_next_action"],
                "title": item["title"],
                "resource_kind": item["resource_kind"],
                "repository_id": item["repository_id"],
                "remote_id": item["remote_id"],
            }
        ],
        "denominator": {
            "issues_open": 1,
            "prs_open": 0,
            "streams_complete": True,
            "class4": {
                "delegate_active": True,
                "delegate_tasks": True,
                "fleet_reviews": True,
            },
            "omissions": [{"class": "private_adapter", "reason": "not_configured", "count": 0}],
        },
        "capabilities": {
            "mutation": False,
            "private_source": {
                "source_id": "private-local-adapter",
                "available": False,
                "schema_version": "work-projection.v1",
                "schema_digest_sha256": None,
                "public_schema_commit": None,
                "endpoint": None,
                "capabilities": [],
                "redaction": "allowlist_v1",
                "reason_if_unavailable": "not_configured",
            },
        },
        "foundation_status": "FOUNDATION_COMPLETE",
    }


def _healthy_public_item(*, remote_id: str = "5922", title: str = "Healthy public issue") -> dict[str, Any]:
    work_id = f"wp1:public-monitor:{PUBLIC_REPO}:issue:{remote_id}"
    return {
        "work_id": work_id,
        "source_id": "public-monitor",
        "repository_id": PUBLIC_REPO,
        "resource_kind": "issue",
        "remote_id": remote_id,
        "title": title,
        "lifecycle": "open",
        "labels": ["healthy"],
        "assignees": [],
        "urls": {
            "html": f"https://github.com/{PUBLIC_REPO}/issues/{remote_id}",
        },
        "timestamps": {
            "created_at": "2026-08-16T00:00:00Z",
            "updated_at": "2026-08-16T00:00:00Z",
        },
        "projections": {
            "stream": {
                "status": "on_track",
                "streams": [],
                "fresh": True,
                "authority_missing": False,
            },
            "dispatch": {"task_ids": [], "statuses": [], "unresolved": False},
            "review": {
                "review_ids": [],
                "states": [],
                "sealed_verdict_available": False,
            },
            "verification": {"kind": "none", "state": "n/a"},
        },
        "relationships": [],
        "health": "ON_TRACK",
        "attention_rank": 1,
        "safe_next_action": {
            "code": "OPEN_GITHUB",
            "reason_codes": ["healthy_on_track"],
        },
        "authority": [
            {
                "domain": "github",
                "observed_at": "2026-08-16T00:00:00Z",
                "age_s": 0,
                "stale": False,
            }
        ],
        "omissions": [],
        "flags": {"orphan": False, "has_blocker": False},
    }


def _public_with_healthy_item() -> dict[str, Any]:
    doc = _public_min()
    healthy = _healthy_public_item()
    doc["items"].append(healthy)
    doc["attention"].append(
        {
            "work_id": healthy["work_id"],
            "attention_rank": healthy["attention_rank"],
            "health": healthy["health"],
            "safe_next_action": healthy["safe_next_action"],
            "title": healthy["title"],
            "resource_kind": healthy["resource_kind"],
            "repository_id": healthy["repository_id"],
            "remote_id": healthy["remote_id"],
        }
    )
    doc["denominator"]["issues_open"] = 2
    for src in doc["sources"]:
        if src["source_id"] == "public-monitor":
            src["sections"]["issues"]["count"] = 2
    return doc


def _private_ok(*, remote_id: str = "7", kind: str = "issue", rank: int = 0) -> dict[str, Any]:
    title = f"private-{kind}-{remote_id}"
    work_id = f"wp1:private-local-adapter:{SYNTH_PRIVATE_REPO}:{kind}:{remote_id}"
    item = {
        "work_id": work_id,
        "source_id": "private-local-adapter",
        "repository_id": SYNTH_PRIVATE_REPO,
        "resource_kind": kind,
        "remote_id": remote_id,
        "title": title,
        "lifecycle": "open" if kind == "issue" else "draft",
        "labels": [],
        "assignees": [],
        "urls": {"html": None},
        "timestamps": {"created_at": "2026-08-16T00:00:00Z", "updated_at": None},
        "projections": {
            "stream": {},
            "dispatch": {},
            "review": {},
            "verification": {},
        },
        "relationships": [],
        "health": "UNKNOWN",
        "attention_rank": rank,
        "safe_next_action": {
            "code": "INSPECT_UNKNOWN",
            "reason_codes": [
                "private_metadata_redacted",
                "no_private_authority_evidence",
            ],
        },
        "authority": [],
        "omissions": [
            {"class": "private_content", "reason": "redacted"},
            {"class": "stream_authority", "reason": "not_collected"},
            {"class": "review_authority", "reason": "not_collected"},
        ],
    }
    issue_count = 1 if kind == "issue" else 0
    pr_count = 1 if kind == "pr" else 0
    return {
        "schema_version": "work-projection.v1",
        "generated_at": "2026-08-16T00:00:00Z",
        "cache_age_s": 3.0,
        "budget": {"warm_target_s": 2, "timeout_s": 5},
        "sources": [
            {
                "source_id": "private-local-adapter",
                "status": "ok",
                "freshness": {"observed_at": "2026-08-16T00:00:00Z", "age_s": 3.0},
                "capabilities": {"mutation": False, "private_fields": False},
                "truncation": {"issues": False, "prs": False, "limit": 1000},
                "sections": {
                    "issues": {"status": "ok", "count": issue_count},
                    "prs": {"status": "ok", "count": pr_count},
                },
            }
        ],
        "items": [item],
        "attention": [
            {
                "work_id": work_id,
                "attention_rank": rank,
                "health": "UNKNOWN",
                "safe_next_action": item["safe_next_action"],
                "title": title,
                "resource_kind": kind,
                "repository_id": SYNTH_PRIVATE_REPO,
                "remote_id": remote_id,
            }
        ],
        "denominator": {
            "issues_open": issue_count,
            "prs_open": pr_count,
            "streams_complete": True,
            "class4": {
                "delegate_active": False,
                "delegate_tasks": False,
                "fleet_reviews": False,
            },
            "omissions": [],
        },
        "capabilities": {
            "mutation": False,
            "private_source": {
                "source_id": "private-local-adapter",
                "available": True,
                "schema_version": "work-projection.v1",
                "schema_digest_sha256": SCHEMA_DIGEST,
                "public_schema_commit": PUBLIC_COMMIT,
                "endpoint": PRIVATE_URL,
                "capabilities": ["projection", "capabilities", "health"],
                "redaction": "strict-metadata-only",
                "reason_if_unavailable": None,
            },
        },
        "foundation_status": "FOUNDATION_COMPLETE",
    }


def _private_with_extra_canary() -> dict[str, Any]:
    doc = _private_ok()
    # Closed-world rejection: free-text / canary-shaped extra key.
    doc["canary_note"] = CANARY
    return doc


def _public_stale_with_unknown_items() -> dict[str, Any]:
    """Public projection with stale streams and UNKNOWN item health (FX-03)."""
    doc = _public_min()
    for src in doc["sources"]:
        if src["source_id"] == "public-monitor":
            src["status"] = "stale"
            src["sections"]["streams"]["status"] = "stale"
    item = doc["items"][0]
    item["health"] = "UNKNOWN"
    item["projections"]["stream"] = {
        "status": "unknown",
        "streams": [],
        "fresh": False,
        "authority_missing": True,
    }
    item["safe_next_action"] = {
        "code": "INSPECT_UNKNOWN",
        "reason_codes": ["stream_authority_stale"],
    }
    doc["attention"][0]["health"] = "UNKNOWN"
    doc["attention"][0]["safe_next_action"] = item["safe_next_action"]
    # Stale streams still count as denominator-complete on the public envelope;
    # merge AND with private must not be what the public card reads (R-UI-3).
    doc["denominator"]["streams_complete"] = True
    return doc


def _public_streams_unavailable() -> dict[str, Any]:
    """Public envelope whose streams section is not complete (R-UI-3)."""
    doc = _public_min()
    for src in doc["sources"]:
        if src["source_id"] == "public-monitor":
            src["sections"]["streams"]["status"] = "unavailable"
            src["sections"]["streams"]["count"] = 0
    doc["denominator"]["streams_complete"] = False
    return doc


def _public_with_private_id_collision(private_doc: dict[str, Any]) -> dict[str, Any]:
    pub = _public_min()
    # Duplicate the private work_id into public items so merge detects collision.
    clone = json.loads(json.dumps(private_doc["items"][0]))
    # Public may carry arbitrary work_id strings under loose public admission.
    pub["items"].append(clone)
    pub["attention"].append(
        {
            "work_id": clone["work_id"],
            "attention_rank": 1,
            "health": clone["health"],
            "safe_next_action": clone["safe_next_action"],
            "title": clone["title"],
            "resource_kind": clone["resource_kind"],
            "repository_id": clone["repository_id"],
            "remote_id": clone["remote_id"],
        }
    )
    return pub


class _FixtureState:
    def __init__(self) -> None:
        self.public_body: bytes | None = None
        self.public_status = 200
        self.private_body: bytes | None = None
        self.private_status = 200
        self.private_delay_s = 0.0
        self.public_requests: list[dict[str, Any]] = []
        self.private_requests: list[dict[str, Any]] = []
        self.options_count = 0
        self.html = WORK_HTML.read_bytes()


def _make_handler(state: _FixtureState, *, role: str, allowed_origins: set[str]):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _send(
            self,
            code: int,
            body: bytes,
            *,
            content_type: str,
            origin: str | None,
            extra: dict[str, str] | None = None,
        ) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            # Echo the allowlisted constant (not the request header) so CodeQL
            # does not treat this as HTTP response splitting (py/http-response-splitting).
            allowed_origin = next((item for item in allowed_origins if item == origin), None)
            if allowed_origin is not None:
                self.send_header("Access-Control-Allow-Origin", allowed_origin)
                self.send_header("Vary", "Origin")
            if extra:
                for key, value in extra.items():
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self) -> None:
            state.options_count += 1
            origin = self.headers.get("Origin")
            self._send(204, b"", content_type="text/plain", origin=origin)

        def do_GET(self) -> None:
            origin = self.headers.get("Origin")
            path = self.path.split("?", 1)[0]
            accept = self.headers.get("Accept", "")
            record = {
                "path": self.path,
                "path_only": path,
                "accept": accept,
                "origin": origin,
                "method": "GET",
            }
            if role == "public":
                state.public_requests.append(record)
                if path == "/work.html":
                    self._send(200, state.html, content_type="text/html; charset=utf-8", origin=origin)
                    return
                if path == PUBLIC_PATH:
                    body = state.public_body if state.public_body is not None else b"{}"
                    self._send(
                        state.public_status,
                        body,
                        content_type="application/json",
                        origin=origin,
                    )
                    return
                self._send(404, b"missing", content_type="text/plain", origin=origin)
                return

            # private role
            state.private_requests.append(record)
            if state.private_delay_s:
                time.sleep(state.private_delay_s)
            if path != "/v1/projection":
                self._send(404, b"missing", content_type="text/plain", origin=origin)
                return
            body = state.private_body if state.private_body is not None else b"{}"
            self._send(
                state.private_status,
                body,
                content_type="application/json",
                origin=origin,
            )

    return Handler


def _port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def _start_server(
    host: str,
    port: int,
    handler: type[BaseHTTPRequestHandler],
) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _run_puppeteer(script: str, *, node_modules: Path, timeout: int = 60) -> dict[str, Any]:
    env = {
        **dict(**{k: v for k, v in os.environ.items()}),
        "NODE_PATH": str(node_modules),
    }
    # Avoid color warnings noise
    env.pop("NO_COLOR", None)
    env.pop("FORCE_COLOR", None)
    # CommonJS + async: wrap user script body so top-level await is legal.
    wrapped = (
        "(async () => {\n"
        + script
        + "\n})().catch((err) => { console.error(err && err.stack ? err.stack : err); process.exit(1); });\n"
    )
    proc = subprocess.run(
        ["node", "-e", wrapped],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
        cwd=str(ROOT),
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"puppeteer script failed rc={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    # Last JSON line is the result; never print fixture payloads from Python.
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("{")]
    assert lines, f"no JSON result from puppeteer\nstdout={proc.stdout}\nstderr={proc.stderr}"
    return json.loads(lines[-1])


def _browser_scenario(
    *,
    public_doc: dict[str, Any] | None,
    private_doc: dict[str, Any] | None,
    public_status: int = 200,
    private_status: int = 200,
    private_delay_ms: int = 0,
    private_hang_json: bool = False,
    assert_early_public: bool = False,
    private_raw: bytes | None = None,
    public_raw: bytes | None = None,
    filter_query: str = "",
    actions: list[dict[str, Any]] | None = None,
    viewport: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Serve work.html on an ephemeral public origin and intercept both GETs."""
    nm = _require_puppeteer()
    state = _FixtureState()
    if public_raw is not None:
        state.public_body = public_raw
    elif public_doc is not None:
        state.public_body = json.dumps(public_doc, separators=(",", ":")).encode("utf-8")
    else:
        state.public_status = public_status if public_status != 200 else 503
        state.public_body = b'{"detail":"down"}'
    if public_status != 200:
        state.public_status = public_status

    if private_raw is not None:
        state.private_body = private_raw
    elif private_doc is not None:
        state.private_body = json.dumps(private_doc, separators=(",", ":")).encode("utf-8")
    else:
        state.private_status = private_status if private_status != 200 else 503
        state.private_body = b"nope"
    if private_status != 200:
        state.private_status = private_status
    state.private_delay_s = private_delay_ms / 1000.0

    # Ephemeral public server for HTML + public projection (same origin).
    public_handler = _make_handler(state, role="public", allowed_origins={"http://127.0.0.1", "http://localhost"})
    public_server = ThreadingHTTPServer(("127.0.0.1", 0), public_handler)
    public_port = public_server.server_address[1]
    thread = threading.Thread(target=public_server.serve_forever, daemon=True)
    thread.start()

    # Ephemeral private server is NOT used for the fixed URL — browser uses 8769.
    # Intercept both URLs inside Chromium so proofs do not need free fixed ports.
    public_json = state.public_body.decode("utf-8") if state.public_body else "{}"
    private_json = state.private_body.decode("utf-8") if state.private_body else "{}"
    actions_json = json.dumps(actions or [])
    viewport = viewport or {"width": 1280, "height": 800}
    origin = f"http://127.0.0.1:{public_port}"
    page_url = f"{origin}/work.html{filter_query}"
    hang_json_js = "true" if private_hang_json else "false"
    # Hang-json proofs still need the 5s abort budget + small settle margin.
    settle_floor_ms = 9000 if private_hang_json else 10000
    launch_options_json = json.dumps(_puppeteer_launch_options())

    script = f"""
const puppeteer = require('puppeteer');
const PUBLIC_STATUS = {state.public_status};
const PRIVATE_STATUS = {state.private_status};
const PRIVATE_DELAY_MS = {private_delay_ms};
const PRIVATE_HANG_JSON = {hang_json_js};
const PUBLIC_JSON = {json.dumps(public_json)};
const PRIVATE_JSON = {json.dumps(private_json)};
const PAGE_URL = {json.dumps(page_url)};
const ACTIONS = {actions_json};
const VIEWPORT = {json.dumps(viewport)};
const PRIVATE_URL = {json.dumps(PRIVATE_URL)};
const CANARY = {json.dumps(CANARY)};
const LAUNCH_OPTIONS = {launch_options_json};

const observed = {{ public: [], private: [], options: 0, consoleErrors: [], pageErrors: [] }};

const browser = await puppeteer.launch(LAUNCH_OPTIONS);
try {{
  const page = await browser.newPage();
  await page.setViewport(VIEWPORT);
  page.on('console', (msg) => {{
    if (msg.type() === 'error') observed.consoleErrors.push(msg.text());
  }});
  page.on('pageerror', (err) => observed.pageErrors.push(String(err && err.message ? err.message : err)));

  // Source-blind body-stall mock: fulfilled 200 Response whose json() never
  // settles unless AbortSignal fires. Proves the private 5s budget covers body
  // parse, not only response headers. No real private service is contacted.
  if (PRIVATE_HANG_JSON) {{
    await page.evaluateOnNewDocument((privateUrl) => {{
      const originalFetch = window.fetch.bind(window);
      window.fetch = function(input, init) {{
        const url = typeof input === 'string' ? input : (input && input.url) || '';
        if (url === privateUrl || url.startsWith(privateUrl + '?')) {{
          const signal = init && init.signal;
          const body = new ReadableStream({{
            start(controller) {{
              const fail = () => {{
                try {{
                  controller.error(new DOMException('The user aborted a request.', 'AbortError'));
                }} catch (_e) {{
                  // already errored/closed
                }}
              }};
              if (signal) {{
                if (signal.aborted) {{
                  fail();
                  return;
                }}
                signal.addEventListener('abort', fail, {{ once: true }});
              }}
              // Never enqueue/close — body/json() hangs until abort.
            }},
          }});
          return Promise.resolve(new Response(body, {{
            status: 200,
            headers: {{
              'Content-Type': 'application/json',
              'Cache-Control': 'no-store',
            }},
          }}));
        }}
        return originalFetch(input, init);
      }};
    }}, PRIVATE_URL);
  }}

  await page.setRequestInterception(true);
  // Fulfill every request exactly once. networkidle0 hangs on some non-2xx
  // cross-origin fulfills under interception; settle via DOM instead.
  page.on('request', (req) => {{
    const finish = async () => {{
      try {{
        const url = req.url();
        const method = req.method();
        if (method === 'OPTIONS') observed.options += 1;
        if (url.includes('/api/work/v1/projection')) {{
          observed.public.push({{
            url,
            method,
            headers: req.headers(),
          }});
          await req.respond({{
            status: PUBLIC_STATUS,
            contentType: 'application/json',
            body: PUBLIC_JSON,
            headers: {{ 'Cache-Control': 'no-store' }},
          }});
          return;
        }}
        if (url === PRIVATE_URL || url.startsWith(PRIVATE_URL + '?')) {{
          observed.private.push({{
            url,
            method,
            headers: req.headers(),
          }});
          // Body-stall proofs are owned by the page-level fetch mock; leave any
          // native private request pending rather than fulfilling a body.
          if (PRIVATE_HANG_JSON) {{
            return;
          }}
          if (PRIVATE_DELAY_MS > 0) {{
            await new Promise((r) => setTimeout(r, PRIVATE_DELAY_MS));
          }}
          const originHeader = 'http://127.0.0.1:' + (new URL(PAGE_URL)).port;
          await req.respond({{
            status: PRIVATE_STATUS,
            contentType: 'application/json',
            body: PRIVATE_JSON,
            headers: {{
              'Cache-Control': 'no-store',
              'Access-Control-Allow-Origin': originHeader,
              'Vary': 'Origin',
            }},
          }});
          return;
        }}
        await req.continue();
      }} catch (err) {{
        try {{
          await req.abort('failed');
        }} catch (_e) {{
          // already handled
        }}
      }}
    }};
    finish();
  }});

  // domcontentloaded: dual GETs settle after navigation; do not use networkidle0
  // (non-2xx intercept fulfills can leave the lifecycle watcher pending).
  await page.goto(PAGE_URL, {{ waitUntil: 'domcontentloaded', timeout: 30000 }});
  await page.waitForSelector('#source-private-meta', {{ timeout: 15000 }});
  if ({str(assert_early_public).lower()}) {{
    await page.waitForFunction(() => document.querySelectorAll('.work-row').length > 0, {{ timeout: 2000 }});
    const pending = await page.$eval('#source-private-meta', el => el.textContent);
    if (pending !== 'Checking capability…') throw new Error('Public rows did not paint while private was pending');
  }}
  // Wait until dual-source settlement replaces the loading placeholders.
  const settleBudget = Math.max({settle_floor_ms}, PRIVATE_DELAY_MS + 3000);
  await page.waitForFunction(() => {{
    const priv = (document.getElementById('source-private-meta')?.textContent || '').trim();
    const pub = (document.getElementById('source-public-meta')?.textContent || '').trim();
    const err = document.getElementById('error-banner');
    const errText = (err && err.textContent) || '';
    const errHidden = !err || err.classList.contains('hidden');
    const loadingPriv = !priv || priv === 'Checking capability…';
    const loadingPub = !pub || pub === 'Loading…';
    if (!errHidden && errText.includes('Work projection unavailable')) return true;
    if (!loadingPriv && !loadingPub) return true;
    // Private-only path sets public meta to status=unavailable|schema_mismatch.
    if (!loadingPriv && pub.startsWith('status=')) return true;
    return false;
  }}, {{ timeout: settleBudget }});
  await new Promise((r) => setTimeout(r, 150));

  for (const action of ACTIONS) {{
    if (action.type === 'select') {{
      await page.select(action.selector, action.value);
    }} else if (action.type === 'click') {{
      await page.click(action.selector);
    }} else if (action.type === 'key') {{
      await page.keyboard.press(action.key);
    }} else if (action.type === 'wait') {{
      await new Promise((r) => setTimeout(r, action.ms || 200));
    }}
  }}
  await new Promise((r) => setTimeout(r, 200));

  const snapshot = await page.evaluate((canary) => {{
    const rows = Array.from(document.querySelectorAll('.work-row')).map((row) => ({{
      id: row.getAttribute('data-id'),
      text: row.textContent || '',
      health: (row.querySelector('.pill.ON_TRACK, .pill.AT_RISK, .pill.OFF_TRACK, .pill.UNKNOWN') || {{}}).textContent || '',
    }}));
    const overflow = document.documentElement.scrollWidth > document.documentElement.clientWidth + 1
      || document.body.scrollWidth > document.body.clientWidth + 1;
    const active = document.activeElement;
    return {{
      publicMeta: document.getElementById('source-public-meta')?.textContent || '',
      privateMeta: document.getElementById('source-private-meta')?.textContent || '',
      error: document.getElementById('error-banner')?.textContent || '',
      errorHidden: document.getElementById('error-banner')?.classList.contains('hidden') ?? true,
      listText: document.getElementById('attention-list')?.textContent || '',
      rowCount: rows.length,
      rowIds: rows.map((r) => r.id),
      rowTexts: rows.map((r) => r.text),
      rowHealths: rows.map((r) => r.health),
      activeElementId: active ? (active.id || '') : '',
      paletteHidden: document.getElementById('cmd')?.hidden ?? true,
      href: location.href,
      search: location.search,
      hash: location.hash,
      localStorageKeys: Object.keys(localStorage || {{}}),
      sessionStorageKeys: Object.keys(sessionStorage || {{}}),
      cookie: document.cookie || '',
      bodyText: document.body.innerText || '',
      hasCanary: (document.documentElement.outerHTML || '').includes(canary),
      overflow,
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
    }};
  }}, CANARY);

  console.log(JSON.stringify({{
    ok: true,
    observed: {{
      publicCount: observed.public.length,
      privateCount: observed.private.length,
      options: observed.options,
      public: observed.public,
      private: observed.private,
      consoleErrors: observed.consoleErrors,
      pageErrors: observed.pageErrors,
    }},
    snapshot,
  }}));
}} finally {{
  await browser.close();
}}
"""
    try:
        return _run_puppeteer(script, node_modules=nm, timeout=90)
    finally:
        public_server.shutdown()
        public_server.server_close()


# ---------------------------------------------------------------------------
# Static / unit contracts
# ---------------------------------------------------------------------------


def test_static_private_url_is_exact_fixed_constant():
    """FX-09 adjacent: private URL is a fixed constant, never storage/cookie driven."""
    html = WORK_HTML.read_text(encoding="utf-8")
    assert f"'{PRIVATE_URL}'" in html
    assert html.count("127.0.0.1:8769") == html.count(PRIVATE_URL)
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "document.cookie" not in html
    assert "Promise.allSettled" in html
    assert "admitPrivateDocument" in html
    assert "identity_collision" in html
    assert SCHEMA_DIGEST in html
    assert PUBLIC_COMMIT in html
    # R-UI-1..3 helpers
    assert "formatAdmittedPrivateMeta" in html
    assert "publicStreamsComplete" in html
    assert "sectionCount" in html


def test_private_fixture_shape_is_source_blind():
    """FX-07: public fixtures stay source-blind (synthetic slug, public-safe canary only)."""
    doc = _private_ok()
    blob = json.dumps(doc)
    assert "learn-ukrainian-infra" not in blob
    assert "/Users/" not in blob
    assert CANARY not in blob
    assert doc["capabilities"]["private_source"]["endpoint"] == PRIVATE_URL
    assert doc["capabilities"]["private_source"]["schema_digest_sha256"] == SCHEMA_DIGEST


def test_puppeteer_launch_options_honors_env_executable():
    opts = _puppeteer_launch_options(
        env={"PUPPETEER_EXECUTABLE_PATH": "/custom/chrome"},
        candidates=("/usr/bin/google-chrome",),
        is_executable=lambda path: path == "/custom/chrome",
    )
    assert opts["executablePath"] == "/custom/chrome"
    assert opts["headless"] == "new"
    assert opts["args"] == ["--no-sandbox", "--disable-setuid-sandbox"]


def test_puppeteer_launch_options_ignores_missing_env_and_picks_first_candidate():
    opts = _puppeteer_launch_options(
        env={"PUPPETEER_EXECUTABLE_PATH": "/missing/chrome"},
        candidates=(
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ),
        is_executable=lambda path: path in {"/usr/bin/chromium", "/usr/bin/chromium-browser"},
    )
    assert opts["executablePath"] == "/usr/bin/chromium"


def test_puppeteer_launch_options_omits_path_when_none_available():
    opts = _puppeteer_launch_options(
        env={},
        candidates=("/nope/a", "/nope/b"),
        is_executable=lambda _path: False,
    )
    assert "executablePath" not in opts
    assert opts["headless"] == "new"
    assert "--no-sandbox" in opts["args"]
    assert "--disable-setuid-sandbox" in opts["args"]


def test_resolve_chrome_executable_order_matches_linux_candidates():
    seen: list[str] = []

    def probe(path: str) -> bool:
        seen.append(path)
        return path == "/usr/bin/chromium-browser"

    resolved = _resolve_chrome_executable(
        env={},
        candidates=LINUX_CHROME_CANDIDATES,
        is_executable=probe,
    )
    assert resolved == "/usr/bin/chromium-browser"
    assert seen == list(LINUX_CHROME_CANDIDATES)


# ---------------------------------------------------------------------------
# Headless browser behavioral proofs (request interception)
# ---------------------------------------------------------------------------


def test_browser_dual_success_merges_exactly_once():
    """R-UI-1/2: per-source counts on the matching card after dual admit."""
    public = _public_min()
    private = _private_ok()
    result = _browser_scenario(public_doc=public, private_doc=private, filter_query="?view=all")
    snap = result["snapshot"]
    obs = result["observed"]
    assert obs["publicCount"] >= 1
    assert obs["privateCount"] >= 1
    assert obs["options"] == 0
    priv_req = obs["private"][0]
    assert priv_req["url"] == PRIVATE_URL
    assert priv_req["method"] == "GET"
    assert "accept" in {k.lower() for k in priv_req["headers"]}
    # No query string on private
    assert "?" not in priv_req["url"]
    assert snap["rowCount"] == 2
    assert len(set(snap["rowIds"])) == 2
    assert any("Public attention item" in t for t in snap["rowTexts"])
    assert any("private-issue-7" in t for t in snap["rowTexts"])
    # Public card: public envelope counts only (not merged denom issues=2).
    assert "status=ok" in snap["publicMeta"]
    assert "issues=1" in snap["publicMeta"]
    assert "prs=0" in snap["publicMeta"]
    assert "streams=complete" in snap["publicMeta"]
    # Private card: admitted status + private section counts; no streams claim; no URL.
    assert "status=ok" in snap["privateMeta"]
    assert "issues=1" in snap["privateMeta"]
    assert "prs=0" in snap["privateMeta"]
    assert "streams=" not in snap["privateMeta"]
    assert PRIVATE_URL not in snap["privateMeta"]
    assert PRIVATE_URL not in snap["publicMeta"]
    assert snap["errorHidden"] is True
    assert CANARY not in snap["bodyText"]
    assert not snap["hasCanary"]
    assert not obs["pageErrors"]
    assert not any(CANARY in e for e in obs["consoleErrors"])


def test_browser_private_unreachable_leaves_public_usable():
    """FX-02: private absent/unreachable leaves public usable; public counts stay public."""
    result = _browser_scenario(public_doc=_public_min(), private_doc=None, private_status=503)
    snap = result["snapshot"]
    assert snap["rowCount"] == 1
    assert "Public attention item" in snap["listText"]
    assert "unavailable · unreachable" in snap["privateMeta"]
    assert "status=ok" in snap["publicMeta"]
    assert "issues=1" in snap["publicMeta"]
    assert snap["errorHidden"] is True


def test_browser_private_timeout_leaves_public_usable():
    """FX-06: private AbortController timeout is typed; public remains usable."""
    # AbortController budget is 5s; delay beyond that.
    result = _browser_scenario(
        public_doc=_public_min(),
        private_doc=_private_ok(),
        private_delay_ms=5500,
        assert_early_public=True,
    )
    snap = result["snapshot"]
    assert snap["rowCount"] == 1
    assert "Public attention item" in snap["listText"]
    assert "unavailable · timeout" in snap["privateMeta"]
    assert snap["errorHidden"] is True


def test_browser_private_stalled_json_body_is_typed_timeout():
    """FX-06: fulfilled headers + never-settling json() must still hit the 5s budget.

    Source-blind page fetch mock only — no real private adapter process.
    """
    started = time.monotonic()
    result = _browser_scenario(
        public_doc=_public_min(),
        private_doc=_private_ok(),
        private_hang_json=True,
    )
    elapsed = time.monotonic() - started
    snap = result["snapshot"]
    obs = result["observed"]
    assert snap["rowCount"] == 1
    assert "Public attention item" in snap["listText"]
    assert "unavailable · timeout" in snap["privateMeta"]
    assert snap["errorHidden"] is True
    # Typed meta only — never raw abort/exception text in banner or strip.
    assert "AbortError" not in snap["privateMeta"]
    assert "AbortError" not in snap["error"]
    assert "TypeError" not in snap["error"]
    assert "Failed to fetch" not in snap["error"]
    # Budget is 5s; allow Chromium/settle overhead but refuse unbounded hang.
    assert elapsed < 12.0, f"stalled-body timeout took too long: {elapsed:.2f}s"
    assert elapsed >= 4.0, f"stalled-body timed out too early: {elapsed:.2f}s"
    assert not any("AbortError" in e for e in obs.get("pageErrors") or [])
    assert not any("AbortError" in e for e in obs.get("consoleErrors") or [])


def test_browser_private_schema_mismatch_and_canary_rejected():
    """FX-06 + FX-07: extra-key / canary private payload → schema_mismatch; canary absent."""
    result = _browser_scenario(
        public_doc=_public_min(),
        private_doc=_private_with_extra_canary(),
    )
    snap = result["snapshot"]
    assert snap["rowCount"] == 1
    assert "unavailable · schema_mismatch" in snap["privateMeta"]
    assert not snap["hasCanary"]
    assert CANARY not in snap["bodyText"]
    assert CANARY not in snap["error"]
    assert CANARY not in snap["href"]
    assert CANARY not in snap["search"]
    assert CANARY not in snap["listText"]


def test_browser_identity_collision_keeps_public():
    """FX-01: colliding work_id rejects private; public document remains."""
    private = _private_ok()
    public = _public_with_private_id_collision(private)
    result = _browser_scenario(public_doc=public, private_doc=private)
    snap = result["snapshot"]
    # Public remains usable; private rejected for collision.
    assert "unavailable · identity_collision" in snap["privateMeta"]
    assert snap["errorHidden"] is True
    # Public rows still render (may include the colliding id from public side once).
    assert snap["rowCount"] >= 1
    assert "Public attention item" in snap["listText"]


def test_browser_public_failure_private_success():
    """FX-02 adjacency: public transport failure does not block admitted private rows."""
    result = _browser_scenario(
        public_doc=None,
        public_status=503,
        private_doc=_private_ok(),
        filter_query="?view=all",
    )
    snap = result["snapshot"]
    assert snap["rowCount"] == 1
    assert "private-issue-7" in snap["listText"]
    assert "status=unavailable" in snap["publicMeta"]
    assert "status=ok" in snap["privateMeta"]
    assert "issues=1" in snap["privateMeta"]
    assert snap["errorHidden"] is True


def test_browser_public_schema_mismatch_private_success():
    """FX-06: public schema_mismatch leaves private usable when admitted."""
    result = _browser_scenario(
        public_doc={"not": "valid"},
        private_doc=_private_ok(),
        filter_query="?view=all",
    )
    snap = result["snapshot"]
    assert snap["rowCount"] == 1
    assert "private-issue-7" in snap["listText"]
    assert "status=schema_mismatch" in snap["publicMeta"]
    assert "status=ok" in snap["privateMeta"]


def test_browser_both_failures_typed_banner():
    """FX-06: both transports fail → typed banner vocabulary only."""
    result = _browser_scenario(
        public_doc=None,
        public_status=503,
        private_doc=None,
        private_status=503,
    )
    snap = result["snapshot"]
    assert snap["errorHidden"] is False
    assert snap["error"] == "Work projection unavailable · public=unreachable · private=unreachable"
    assert snap["listText"].strip() == "No source projection is available. Retry refresh."
    assert "HTTP" not in snap["error"]
    assert "TypeError" not in snap["error"]
    assert "fetch" not in snap["error"].lower()


def test_browser_filters_apply_locally_and_never_hit_private_query():
    """FX-09: local filters never append a query string to the private GET."""
    result = _browser_scenario(
        public_doc=_public_min(),
        private_doc=_private_ok(),
        actions=[
            {"type": "select", "selector": "#filter-health", "value": "AT_RISK"},
            {"type": "click", "selector": "#btn-apply"},
            {"type": "wait", "ms": 200},
        ],
    )
    snap = result["snapshot"]
    obs = result["observed"]
    # After apply (local only), only public AT_RISK remains.
    assert snap["rowCount"] == 1
    assert "Public attention item" in snap["listText"]
    assert "private-issue-7" not in snap["listText"]
    for req in obs["private"]:
        assert req["url"] == PRIVATE_URL
        assert "?" not in req["url"]
    # Shareable URL may keep health
    assert "health=AT_RISK" in snap["search"]


def test_browser_private_repo_filter_not_shareable_in_url():
    """FX-09: private repository_id / source_id never enter location.search."""
    result = _browser_scenario(
        public_doc=_public_min(),
        private_doc=_private_ok(),
        filter_query="?view=all",
        actions=[
            {
                "type": "select",
                "selector": "#filter-repo",
                "value": SYNTH_PRIVATE_REPO,
            },
            {"type": "click", "selector": "#btn-apply"},
            {"type": "wait", "ms": 200},
        ],
    )
    snap = result["snapshot"]
    assert snap["rowCount"] == 1
    assert "private-issue-7" in snap["listText"]
    assert SYNTH_PRIVATE_REPO not in snap["search"]
    assert "private-local-adapter" not in snap["search"]
    assert snap["hash"] == ""
    assert snap["localStorageKeys"] == []
    assert snap["sessionStorageKeys"] == []
    assert snap["cookie"] == ""


def test_browser_private_source_filter_lists_rows_without_url_leak():
    """R-UI-2 + FX-09: in-memory source=private lists rows; never writes source_id to URL."""
    result = _browser_scenario(
        public_doc=_public_min(),
        private_doc=_private_ok(),
        filter_query="?view=all",
        actions=[
            {
                "type": "select",
                "selector": "#filter-source",
                "value": "private-local-adapter",
            },
            {"type": "click", "selector": "#btn-apply"},
            {"type": "wait", "ms": 200},
        ],
    )
    snap = result["snapshot"]
    assert snap["rowCount"] == 1
    assert "private-issue-7" in snap["listText"]
    assert "Public attention item" not in snap["listText"]
    assert "private-local-adapter" not in snap["search"]
    assert "source_id=" not in snap["search"]
    assert PRIVATE_URL not in snap["search"]
    assert PRIVATE_URL not in snap["href"]


def test_browser_dense_order_and_no_duplicate_ids():
    """FX-01 adjacent: densified attention keeps distinct work_ids across sources."""
    public = _public_min()
    # Public ON_TRACK + private UNKNOWN + public OFF_TRACK-like via health change
    public["items"][0]["health"] = "ON_TRACK"
    public["attention"][0]["health"] = "ON_TRACK"
    private = _private_ok(remote_id="3", rank=0)
    result = _browser_scenario(public_doc=public, private_doc=private, filter_query="?view=all")
    snap = result["snapshot"]
    assert snap["rowCount"] == 2
    assert len(set(snap["rowIds"])) == 2
    # UNKNOWN before ON_TRACK
    assert snap["rowIds"][0].startswith("wp1:private-local-adapter:")
    assert snap["rowIds"][1].startswith("wp1:public-monitor:")


def test_browser_mobile_viewport_no_horizontal_overflow_and_keyboard():
    """FX-08: narrow viewport has no horizontal overflow; keyboard navigation works."""
    result = _browser_scenario(
        public_doc=_public_min(),
        private_doc=_private_ok(),
        filter_query="?view=all",
        viewport={"width": 390, "height": 844},
        actions=[
            {"type": "key", "key": "ArrowDown"},
            {"type": "wait", "ms": 100},
        ],
    )
    snap = result["snapshot"]
    obs = result["observed"]
    assert snap["overflow"] is False
    assert snap["scrollWidth"] <= snap["clientWidth"] + 1
    assert not obs["pageErrors"]
    # Uncaught console errors only (ignore optional 3rd-party noise if empty)
    assert snap["rowCount"] == 2


def test_browser_palette_escape_restores_list_focus():
    """FX-08 residual: Esc closes the palette and returns focus to the attention list."""
    result = _browser_scenario(
        public_doc=_public_min(),
        private_doc=_private_ok(),
        filter_query="?view=all",
        actions=[
            {"type": "click", "selector": "#btn-palette"},
            {"type": "wait", "ms": 150},
            {"type": "key", "key": "Escape"},
            {"type": "wait", "ms": 150},
        ],
    )
    snap = result["snapshot"]
    assert snap["paletteHidden"] is True
    assert snap["activeElementId"] == "attention-list"


def test_browser_public_only_when_adapter_absent():
    """FX-02: adapter absent (404) → private unreachable; public still renders."""
    result = _browser_scenario(public_doc=_public_min(), private_doc=None, private_status=404)
    snap = result["snapshot"]
    assert snap["rowCount"] == 1
    assert "Public attention item" in snap["listText"]
    assert "unavailable · unreachable" in snap["privateMeta"]
    assert "status=ok" in snap["publicMeta"]
    assert "issues=1" in snap["publicMeta"]


def test_browser_refresh_uses_fresh_on_public_only():
    result = _browser_scenario(
        public_doc=_public_min(),
        private_doc=_private_ok(),
        actions=[{"type": "click", "selector": "#btn-refresh"}, {"type": "wait", "ms": 400}],
    )
    obs = result["observed"]
    assert obs["publicCount"] >= 2
    assert obs["privateCount"] >= 2
    public_urls = [r["url"] for r in obs["public"]]
    assert any("fresh=true" in u for u in public_urls)
    for req in obs["private"]:
        assert req["url"] == PRIVATE_URL


def test_browser_stale_public_healthy_private_keeps_public_stale():
    """R-TEST-2 / FX-03: healthy private must not rewrite public status or paint public ON_TRACK."""
    public = _public_stale_with_unknown_items()
    private = _private_ok()
    result = _browser_scenario(public_doc=public, private_doc=private, filter_query="?view=all")
    snap = result["snapshot"]
    assert "status=stale" in snap["publicMeta"]
    assert "status=ok" in snap["privateMeta"]
    assert "issues=1" in snap["publicMeta"]
    assert "issues=1" in snap["privateMeta"]
    assert "streams=" not in snap["privateMeta"]
    assert snap["rowCount"] == 2
    for row_id, health, text_row in zip(snap["rowIds"], snap["rowHealths"], snap["rowTexts"], strict=True):
        if row_id.startswith("wp1:public-monitor:"):
            assert health == "UNKNOWN"
            assert "ON_TRACK" not in text_row
            assert "UNKNOWN" in text_row
        if row_id.startswith("wp1:private-local-adapter:"):
            assert health == "UNKNOWN"


def test_browser_public_streams_not_implied_by_private_list_success():
    """R-UI-3: private list-enumeration success must not mark public streams complete."""
    public = _public_streams_unavailable()
    private = _private_ok()
    assert private["denominator"]["streams_complete"] is True
    result = _browser_scenario(public_doc=public, private_doc=private, filter_query="?view=all")
    snap = result["snapshot"]
    assert "streams=incomplete" in snap["publicMeta"]
    assert "streams=" not in snap["privateMeta"]
    assert "status=ok" in snap["privateMeta"]


def test_browser_actionable_default_view_filters_non_actionable_rows():
    """R-UI-2: default view=actionable hides private INSPECT_UNKNOWN rows."""
    # Public item 1 is AT_RISK (actionable); public item 2 is ON_TRACK / OPEN_GITHUB (healthy non-actionable);
    # private item is UNKNOWN / INSPECT_UNKNOWN (non-actionable).
    public = _public_with_healthy_item()
    private = _private_ok()
    result = _browser_scenario(public_doc=public, private_doc=private)
    snap = result["snapshot"]
    # In default view, only public actionable item renders.
    assert snap["rowCount"] == 1
    assert "Public attention item" in snap["listText"]
    assert "Healthy public issue" not in snap["listText"]
    assert "private-issue-7" not in snap["listText"]
    # URL search remains clean without query params
    assert snap["search"] == ""
    # Private card still glanceable with counts while rows stay non-actionable.
    assert "status=ok" in snap["privateMeta"]
    assert "issues=1" in snap["privateMeta"]


def test_browser_switch_view_between_actionable_and_all():
    """R-UI-2: view=all lists private rows; actionable default hides them."""
    public = _public_with_healthy_item()
    private = _private_ok()
    # Step 1: Start at default actionable view -> 1 row
    result_default = _browser_scenario(public_doc=public, private_doc=private)
    assert result_default["snapshot"]["rowCount"] == 1
    assert "Healthy public issue" not in result_default["snapshot"]["listText"]
    assert result_default["snapshot"]["search"] == ""

    # Step 2: Switch to 'all' via UI select + apply -> 3 rows, URL is ?view=all
    result_all = _browser_scenario(
        public_doc=public,
        private_doc=private,
        actions=[
            {"type": "select", "selector": "#filter-view", "value": "all"},
            {"type": "click", "selector": "#btn-apply"},
            {"type": "wait", "ms": 200},
        ],
    )
    snap_all = result_all["snapshot"]
    assert snap_all["rowCount"] == 3
    assert "Public attention item" in snap_all["listText"]
    assert "Healthy public issue" in snap_all["listText"]
    assert "private-issue-7" in snap_all["listText"]
    assert "view=all" in snap_all["search"]

    # Step 3: Switch back to 'actionable' via UI select + apply -> 1 row, clean URL
    result_back = _browser_scenario(
        public_doc=public,
        private_doc=private,
        filter_query="?view=all",
        actions=[
            {"type": "select", "selector": "#filter-view", "value": "actionable"},
            {"type": "click", "selector": "#btn-apply"},
            {"type": "wait", "ms": 200},
        ],
    )
    snap_back = result_back["snapshot"]
    assert snap_back["rowCount"] == 1
    assert "Public attention item" in snap_back["listText"]
    assert "Healthy public issue" not in snap_back["listText"]
    assert "private-issue-7" not in snap_back["listText"]
    assert snap_back["search"] == ""


def test_browser_direct_actionable_url_normalizes_to_clean_path():
    """FX-09: ?view=actionable renders actionable view and normalizes URL."""
    public = _public_with_healthy_item()
    private = _private_ok()
    result = _browser_scenario(public_doc=public, private_doc=private, filter_query="?view=actionable")
    snap = result["snapshot"]
    assert snap["rowCount"] == 1
    assert "Public attention item" in snap["listText"]
    assert "Healthy public issue" not in snap["listText"]
    assert "private-issue-7" not in snap["listText"]
    # Normalizes to clean URL
    assert snap["search"] == ""


def test_browser_actionable_with_kind_and_health_filters():
    """Existing filters like kind and health continue working in actionable default view."""
    public = _public_with_healthy_item()
    private = _private_ok()
    # Filter by health=AT_RISK on actionable default
    result = _browser_scenario(public_doc=public, private_doc=private, filter_query="?health=AT_RISK")
    snap = result["snapshot"]
    assert snap["rowCount"] == 1
    assert "Public attention item" in snap["listText"]
    assert "Healthy public issue" not in snap["listText"]
    assert "health=AT_RISK" in snap["search"]
    # Filter by kind=issue on actionable default
    result_kind = _browser_scenario(public_doc=public, private_doc=private, filter_query="?kind=issue")
    snap_kind = result_kind["snapshot"]
    assert snap_kind["rowCount"] == 1
    assert "Public attention item" in snap_kind["listText"]
    assert "Healthy public issue" not in snap_kind["listText"]
    assert "kind=issue" in snap_kind["search"]


# ---------------------------------------------------------------------------
# Real fixed-port CORS smoke (no payload printing)
# ---------------------------------------------------------------------------


def _cors_handler_factory(hits: dict[str, Any], allowed: set[str], body: bytes):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: Any) -> None:
            return

        def do_OPTIONS(self) -> None:
            hits["options"] = hits.get("options", 0) + 1
            self.send_response(204)
            self.end_headers()

        def do_GET(self) -> None:
            origin = self.headers.get("Origin")
            path = self.path.split("?", 1)[0]
            hits.setdefault("gets", []).append(
                {
                    "path": self.path,
                    "path_only": path,
                    "method": "GET",
                    "accept": self.headers.get("Accept"),
                    "origin": origin,
                }
            )
            if path != "/v1/projection":
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            # Use the allowlisted string, not the raw Origin header value.
            allowed_origin = next((item for item in allowed if item == origin), None)
            if allowed_origin is not None:
                self.send_header("Access-Control-Allow-Origin", allowed_origin)
                self.send_header("Vary", "Origin")
            # No Access-Control-Allow-Credentials
            self.end_headers()
            self.wfile.write(body)

    return Handler


def test_real_fixed_port_cors_http_and_browser_smoke():
    """Live CORS on fixed ports 8765/8769 with real browser GET (no preflight)."""
    if not _port_free("127.0.0.1", FIXED_PUBLIC_PORT) or not _port_free("127.0.0.1", FIXED_PRIVATE_PORT):
        pytest.skip("fixed ports 8765/8769 busy; interception proofs already cover behavior")

    nm = _require_puppeteer()
    private_hits: dict[str, Any] = {"options": 0, "gets": []}
    public_hits: dict[str, Any] = {"options": 0, "gets": []}
    private_body = json.dumps(_private_ok(), separators=(",", ":")).encode("utf-8")
    public_body = json.dumps(_public_min(), separators=(",", ":")).encode("utf-8")
    html = WORK_HTML.read_bytes()

    class PublicHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: Any) -> None:
            return

        def do_OPTIONS(self) -> None:
            public_hits["options"] = public_hits.get("options", 0) + 1
            self.send_response(204)
            self.end_headers()

        def do_GET(self) -> None:
            path = self.path.split("?", 1)[0]
            public_hits.setdefault("gets", []).append(
                {"path": self.path, "path_only": path, "accept": self.headers.get("Accept")}
            )
            if path == "/work.html":
                body = html
                ctype = "text/html; charset=utf-8"
            elif path == "/monitor.css":
                body = b""
                ctype = "text/css; charset=utf-8"
            elif path == PUBLIC_PATH:
                body = public_body
                ctype = "application/json"
            else:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    private_handler = _cors_handler_factory(
        private_hits,
        allowed={"http://127.0.0.1:8765", "http://localhost:8765"},
        body=private_body,
    )
    public_server = _start_server("127.0.0.1", FIXED_PUBLIC_PORT, PublicHandler)
    private_server = _start_server("127.0.0.1", FIXED_PRIVATE_PORT, private_handler)
    try:
        # Pure HTTP CORS probe (no browser) — asserts headers + request shape.
        req = Request(
            PRIVATE_URL,
            headers={
                "Accept": "application/json",
                "Origin": "http://127.0.0.1:8765",
            },
            method="GET",
        )
        with urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            assert resp.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:8765"
            assert resp.headers.get("Vary") == "Origin"
            assert resp.headers.get("Access-Control-Allow-Credentials") in (None, "")
            # Drain body without printing
            _ = resp.read()

        assert private_hits["options"] == 0
        assert private_hits["gets"], "private fixture received no GET"
        got = private_hits["gets"][-1]
        assert got["path_only"] == "/v1/projection"
        assert got["path"] == "/v1/projection"  # exact no-query path
        assert got["accept"] == "application/json"
        assert got["origin"] == "http://127.0.0.1:8765"

        # Browser smoke from exact Monitor origin.
        launch_options_json = json.dumps(_puppeteer_launch_options())
        script = f"""
const puppeteer = require('puppeteer');
const LAUNCH_OPTIONS = {launch_options_json};
const browser = await puppeteer.launch(LAUNCH_OPTIONS);
try {{
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e.message || e)));
  await page.goto('http://127.0.0.1:8765/work.html?view=all', {{
    waitUntil: 'domcontentloaded',
    timeout: 30000,
  }});
  await page.waitForFunction(() => {{
    const el = document.getElementById('source-private-meta');
    return el && (el.textContent || '').includes('status=');
  }}, {{ timeout: 15000 }});
  const snap = await page.evaluate(() => ({{
    privateMeta: document.getElementById('source-private-meta')?.textContent || '',
    rowCount: document.querySelectorAll('.work-row').length,
    errorHidden: document.getElementById('error-banner')?.classList.contains('hidden') ?? true,
  }}));
  console.log(JSON.stringify({{ ok: true, snap, errors, privateGets: true }}));
}} finally {{
  await browser.close();
}}
"""
        result = _run_puppeteer(script, node_modules=nm, timeout=60)
        assert result["snap"]["rowCount"] == 2
        assert "status=ok" in result["snap"]["privateMeta"]
        assert result["snap"]["errorHidden"] is True
        assert not result["errors"]
        assert private_hits["options"] == 0
        # At least the HTTP probe + browser GET
        assert len(private_hits["gets"]) >= 2
        for entry in private_hits["gets"]:
            assert entry["path"] == "/v1/projection"
            assert entry["accept"] == "application/json"
    finally:
        public_server.shutdown()
        public_server.server_close()
        private_server.shutdown()
        private_server.server_close()


def test_real_fixed_port_cors_localhost_origin_smoke():
    """Second smoke: page addressed as http://localhost:8765 admits that origin."""
    if not _port_free("127.0.0.1", FIXED_PUBLIC_PORT) or not _port_free("127.0.0.1", FIXED_PRIVATE_PORT):
        pytest.skip("fixed ports 8765/8769 busy; interception proofs already cover behavior")

    private_hits: dict[str, Any] = {"options": 0, "gets": []}
    private_body = json.dumps(_private_ok(), separators=(",", ":")).encode("utf-8")

    class PublicHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: Any) -> None:
            return

        def do_GET(self) -> None:
            path = self.path.split("?", 1)[0]
            if path == "/work.html":
                body = WORK_HTML.read_bytes()
                ctype = "text/html; charset=utf-8"
            elif path == "/monitor.css":
                body = b""
                ctype = "text/css; charset=utf-8"
            elif path == PUBLIC_PATH:
                body = json.dumps(_public_min(), separators=(",", ":")).encode("utf-8")
                ctype = "application/json"
            else:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    private_handler = _cors_handler_factory(
        private_hits,
        allowed={"http://127.0.0.1:8765", "http://localhost:8765"},
        body=private_body,
    )
    public_server = _start_server("127.0.0.1", FIXED_PUBLIC_PORT, PublicHandler)
    private_server = _start_server("127.0.0.1", FIXED_PRIVATE_PORT, private_handler)
    nm = _require_puppeteer()
    try:
        req = Request(
            PRIVATE_URL,
            headers={
                "Accept": "application/json",
                "Origin": "http://localhost:8765",
            },
            method="GET",
        )
        with urlopen(req, timeout=5) as resp:
            assert resp.headers.get("Access-Control-Allow-Origin") == "http://localhost:8765"
            assert resp.headers.get("Vary") == "Origin"
            _ = resp.read()

        launch_options_json = json.dumps(_puppeteer_launch_options())
        script = f"""
const puppeteer = require('puppeteer');
const LAUNCH_OPTIONS = {launch_options_json};
const browser = await puppeteer.launch(LAUNCH_OPTIONS);
try {{
  const page = await browser.newPage();
  await page.goto('http://localhost:8765/work.html?view=all', {{
    waitUntil: 'domcontentloaded',
    timeout: 30000,
  }});
  await page.waitForFunction(() => {{
    const el = document.getElementById('source-private-meta');
    return el && (el.textContent || '').includes('status=');
  }}, {{ timeout: 15000 }});
  const snap = await page.evaluate(() => ({{
    privateMeta: document.getElementById('source-private-meta')?.textContent || '',
    rowCount: document.querySelectorAll('.work-row').length,
  }}));
  console.log(JSON.stringify({{ ok: true, snap }}));
}} finally {{
  await browser.close();
}}
"""
        result = _run_puppeteer(script, node_modules=nm, timeout=60)
        assert result["snap"]["rowCount"] == 2
        assert "status=ok" in result["snap"]["privateMeta"]
        assert private_hits["options"] == 0
        assert any(g.get("origin") == "http://localhost:8765" for g in private_hits["gets"])
    finally:
        public_server.shutdown()
        public_server.server_close()
        private_server.shutdown()
        private_server.server_close()
