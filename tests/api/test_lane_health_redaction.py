"""Lane-health served fields redact host names, private paths, addresses and credential URLs (#9899).

Raw provider diagnostics stay in the local task record by design; the
lane-health view is where they leave that context, so every free-text field
it serves passes through the shared secret redactor followed by diagnostic
rules confined to lane health.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_routing_budget_endpoint import _configure

from scripts.api import state_router
from scripts.api.lane_health import (
    BASIS_SCAN_UNAVAILABLE,
    MAX_ERROR_EXCERPT_CHARS,
    LaneHealthScan,
    redact_lane_health_text,
    sanitize_error_excerpt,
)
from scripts.api.lane_health_redaction import redact_lane_health_diagnostics
from scripts.api.monitor_context import fixture_context
from scripts.api.opsec_sanitize import opsec_path_sanitizer_middleware

_HOST_USER = "deploy-bot@prod-bastion-7"
_HOST_PORT = "db-primary-9.internal:5432"
_PRIVATE_PATH = "/home/ops/learn-ukrainian/data/vesum.db"
_IPV4 = "203.0.113.7"
_IPV6 = "2001:db8::1"
_CRED_PASSWORD = "Sup3rSecret9"
# Assemble synthetic credentials at runtime so source scans do not see secrets.
_GH_TOKEN = "".join(("ghp_", "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8"))


def _write_task(tasks_dir: Path, task_id: str, agent: str, started_at: datetime, stderr_excerpt: str) -> None:
    data = {
        "task_id": task_id,
        "agent": agent,
        "status": "failed",
        "returncode": 1,
        "duration_s": 10.0,
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "stderr_excerpt": stderr_excerpt,
    }
    (tasks_dir / f"{task_id}.json").write_text(json.dumps(data), encoding="utf-8")


@pytest.mark.parametrize(
    ("excerpt", "markers", "placeholder"),
    [
        ("ssh deploy-bot@prod-bastion-7 exit 255", [_HOST_USER], "[redacted-host]"),
        ("dial db-primary-9.internal:5432 refused", ["db-primary-9.internal"], "[redacted-host]"),
        ("open /home/ops/learn-ukrainian/data/vesum.db: permission denied", [_PRIVATE_PATH], "[redacted-path]"),
        ("connect to 203.0.113.7:443 timed out", [_IPV4], "[redacted-ip]"),
        ("reach [2001:db8::1]:8443 failed", [_IPV6], "[redacted-ip]"),
        (
            "".join(("postgres", "://", "deploy:", _CRED_PASSWORD, "@", _HOST_PORT, "/app refused")),
            [_CRED_PASSWORD, "db-primary-9.internal"],
            "[redacted-host]",
        ),
        (
            "".join(
                (
                    "fatal: Authentication failed for '",
                    "https",
                    "://",
                    "ci-bot:",
                    _GH_TOKEN,
                    "@git-corp.internal/org/repo.git/'",
                )
            ),
            [_GH_TOKEN],
            "[REDACTED_SECRET]",
        ),
    ],
    ids=["host-user-at", "host-port", "private-path", "ipv4", "ipv6", "credential-url", "token-url"],
)
def test_sanitize_error_excerpt_redacts_marker_classes(excerpt, markers, placeholder):
    served = sanitize_error_excerpt(excerpt)
    assert served is not None
    for marker in markers:
        assert marker not in served
    assert placeholder in served


def test_sanitize_error_excerpt_keeps_ordinary_diagnostic_text():
    ordinary = "UnknownError Unexpected server error; retrying"
    assert sanitize_error_excerpt(ordinary) == ordinary
    assert sanitize_error_excerpt("spawn failed with exit code 1") == "spawn failed with exit code 1"


def test_lane_health_redacts_adjacent_markdown_paths():
    raw = "".join(("Open `/", "tmp/first`;`/home/fixture/second`next."))
    expected = "Open `[redacted-path]`;`[redacted-path]`next."
    assert redact_lane_health_text(raw) == expected
    assert redact_lane_health_text(expected) == expected


def test_sanitize_error_excerpt_redacts_before_truncating():
    # A marker straddling the 200-char excerpt cap must not leak through it.
    served = sanitize_error_excerpt("x" * 190 + " /home/ops/secret-token.pem unreadable")
    assert served is not None
    assert served == "x" * 190


@pytest.mark.parametrize(
    "marker",
    [
        "/home/fixture/private/key.pem",
        "getaddrinfo ENOTFOUND node.example.invalid",
        "203.0.113.7",
        _GH_TOKEN,
    ],
)
def test_sanitize_error_excerpt_never_splits_any_placeholder(marker):
    redacted = redact_lane_health_text(marker)
    placeholder_start = redacted.index("[")
    placeholder_end = redacted.index("]", placeholder_start) + 1
    for inside_offset in range(1, placeholder_end - placeholder_start):
        prefix = "x" * (MAX_ERROR_EXCERPT_CHARS - placeholder_start - inside_offset - 1) + " "
        expected = (prefix + redacted)[: len(prefix) + placeholder_start].rstrip()
        assert sanitize_error_excerpt(prefix + marker) == expected
        assert sanitize_error_excerpt(expected) == expected

    prefix = "x" * (MAX_ERROR_EXCERPT_CHARS - placeholder_end - 1) + " "
    assert sanitize_error_excerpt(prefix + marker + " tail") == prefix + redacted


def test_sanitize_error_excerpt_keeps_plain_truncation_and_literal_brackets():
    assert sanitize_error_excerpt("retry " * 50) == ("retry " * 50)[:MAX_ERROR_EXCERPT_CHARS]
    raw = "x" * 190 + " [ordinary diagnostic]"
    assert sanitize_error_excerpt(raw) == raw[:MAX_ERROR_EXCERPT_CHARS]


def test_health_for_redacts_the_served_scan_error_field():
    scan = LaneHealthScan(observed=False, error="scan failed: /home/ops/tasks on 203.0.113.7")
    served = scan.health_for("codex")
    assert served["basis"] == BASIS_SCAN_UNAVAILABLE
    assert "/home/ops" not in served["error"]
    assert _IPV4 not in served["error"]


def test_health_for_redacts_a_raw_record_last_error():
    scan = LaneHealthScan(
        observed=True,
        records={
            "claude": {
                "healthy": False,
                "consecutive_failures": 2,
                "span_minutes": 5,
                "last_error": "dial db-primary-9.internal:5432 refused",
            }
        },
    )
    assert scan.health_for("claude")["last_error"] == "dial [redacted-host] refused"


def test_routing_budget_endpoint_serves_redacted_lane_health(monkeypatch, tmp_path):
    """The real handler serves redacted health; the local task record keeps the raw text."""
    _configure(monkeypatch, tmp_path, [])
    tasks_dir = tmp_path / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)

    marker_excerpt = (
        f"spawn failed: ssh {_HOST_USER} exit 255; "
        f"fallback connect to {_IPV4}:443 timed out; "
        f"log {_PRIVATE_PATH}; "
        + "".join(("auth ", "postgres", "://", "deploy:", _CRED_PASSWORD, "@", _HOST_PORT, "/app"))
    )
    ordinary_excerpt = "UnknownError Unexpected server error"
    _write_task(tasks_dir, "c-1", "claude", now - timedelta(minutes=30), marker_excerpt)
    _write_task(tasks_dir, "c-2", "claude", now - timedelta(minutes=10), marker_excerpt)
    _write_task(tasks_dir, "x-1", "codex", now - timedelta(minutes=30), ordinary_excerpt)
    _write_task(tasks_dir, "x-2", "codex", now - timedelta(minutes=10), ordinary_excerpt)

    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(state_router.router, prefix="/api/state")
    response = TestClient(app).get("/api/state/routing-budget")

    assert response.status_code == 200
    body = response.text
    for marker in (_HOST_USER, "prod-bastion-7", "db-primary-9.internal", _PRIVATE_PATH, _IPV4, _CRED_PASSWORD):
        assert marker not in body

    health = response.json()["agents"]["claude"]["health"]
    assert health["healthy"] is False
    last_error = health["last_error"]
    assert "[redacted-host]" in last_error
    assert "[redacted-ip]" in last_error
    assert "[redacted-path]" in last_error
    # Ordinary diagnostic text survives unredacted on a healthy-text lane.
    assert response.json()["agents"]["codex"]["health"]["last_error"] == ordinary_excerpt

    # Non-goal: the local task record keeps the raw excerpt for local debugging.
    record = json.loads((tasks_dir / "c-2.json").read_text(encoding="utf-8"))
    assert record["stderr_excerpt"] == marker_excerpt


@pytest.mark.repo_invariant
@pytest.mark.parametrize(
    ("text", "token", "placeholder"),
    [
        ("getaddrinfo ENOTFOUND node.example.invalid", "node.example.invalid", "[redacted-host]"),
        ("getaddrinfo EAI_AGAIN resolver-alias", "resolver-alias", "[redacted-host]"),
        ("EAI_NONAME 'node.example.invalid'.", "node.example.invalid", "[redacted-host]"),
        ("ENODATA node.example.invalid.", "node.example.invalid", "[redacted-host]"),
        (r"open C:\Users\fixture\private\key.pem: denied", r"C:\Users\fixture\private\key.pem", "[redacted-path]"),
        ("open C:/Users/fixture/private/key.pem: denied", "C:/Users/fixture/private/key.pem", "[redacted-path]"),
        (r"open \\fixture-server\private\key.pem: denied", r"\\fixture-server\private\key.pem", "[redacted-path]"),
        ("open ~/.ssh/fixture-key: denied", "~/.ssh/fixture-key", "[redacted-path]"),
        ("open ~fixture/.ssh/fixture-key: denied", "~fixture/.ssh/fixture-key", "[redacted-path]"),
        ("open ~_fixture-1/.ssh/fixture-key: denied", "~_fixture-1/.ssh/fixture-key", "[redacted-path]"),
        (
            "".join(("auth ", "https", "://", "bot:", "[REDACTED_SECRET]", "@node.example.invalid/api denied")),
            "node.example.invalid",
            "[redacted-host]",
        ),
        (
            "".join(("auth ", "https", "://", "bot:", "[REDACTED_SECRET]", "@node.example.invalid:443/api denied")),
            "node.example.invalid:443",
            "[redacted-host]",
        ),
    ],
)
def test_lane_health_redacts_resolver_hosts_and_private_path_variants(text, token, placeholder):
    redacted = redact_lane_health_text(text)
    assert redacted == text.replace(token, placeholder)
    assert redact_lane_health_text(redacted) == redacted


_URL_SHAPES = [
    (
        "fetch failed http://devbox.lan:8080/health",
        "devbox.lan:8080",
        "fetch failed http://[redacted-host]/health",
    ),
    ("GET http://localhost:5173/@vite/client 404", "localhost:5173", "GET http://[redacted-host]/@vite/client 404"),
    ("http://localhost:4873/@scope/pkg", "localhost:4873", "http://[redacted-host]/@scope/pkg"),
    ("https://example.invalid:443/@user/post", "example.invalid:443", "https://[redacted-host]/@user/post"),
    (
        "".join(("https", "://", "u:", "12345/path@host.invalid/post")),
        "u:12345",
        "https://[redacted-host]/path@host.invalid/post",
    ),
    ("https://node.example.invalid", "node.example.invalid", "https://[redacted-host]"),
    ("http://203.0.113.7:8080/health", "203.0.113.7:8080", "http://[redacted-ip]/health"),
    ("http://[2001:db8::7]:8080/health", "[2001:db8::7]:8080", "http://[redacted-ip]/health"),
    ("https://bot@node.example.invalid:443/api", "node.example.invalid:443", "https://bot@[redacted-host]/api"),
    (
        "Retry scripts/api/lane_health.py; see https://docs.example.org/guide?part=2#errors",
        "docs.example.org",
        "Retry scripts/api/lane_health.py; see https://[redacted-host]/guide?part=2#errors",
    ),
    (
        "https://node.example.invalid:443/assets/fixture/%2f/@user/post?part=%2B+&next=%2Ftmp%2Ffixture#203.0.113.7",
        "node.example.invalid:443",
        "https://[redacted-host]/assets/fixture/%2f/@user/post?part=%2B+&next=%2Ftmp%2Ffixture#203.0.113.7",
    ),
    (
        "https://node.example.invalid?part=2&next=~/.ssh/fixture#user@other.invalid",
        "node.example.invalid",
        "https://[redacted-host]?part=2&next=~/.ssh/fixture#user@other.invalid",
    ),
    (
        "http://node.example.invalid#retry EAI_AGAIN resolver-alias; dial private.example.invalid:8080",
        "node.example.invalid",
        "http://[redacted-host]#retry EAI_AGAIN [redacted-host]; dial [redacted-host]",
    ),
    (
        "http://one.invalid:8080/@vite/client and https://two.invalid:443/@scope/pkg",
        "one.invalid:8080",
        "http://[redacted-host]/@vite/client and https://[redacted-host]/@scope/pkg",
    ),
]


@pytest.mark.parametrize(("excerpt", "marker", "expected"), _URL_SHAPES)
def test_lane_health_redacts_url_authorities_and_preserves_suffix_bytes(excerpt, marker, expected):
    redacted = redact_lane_health_text(excerpt)
    assert marker not in redacted
    assert redacted == expected
    assert redact_lane_health_text(redacted) == redacted


@pytest.mark.parametrize("password", ["canary?tail", "canary#tail", "canary/tail?more#end"])
@pytest.mark.parametrize("username", ["u", ""])
@pytest.mark.parametrize("host, placeholder", [("host.invalid:443", "[redacted-host]"), ("[2001:db8::7]:443", "[redacted-ip]")])
def test_diagnostic_rule_itself_reuses_malformed_userinfo_redaction(password, username, host, placeholder):
    raw = "".join(("https", "://", username, ":", password, "@", host, "/api?part=2#tail"))
    expected = "".join(("https", "://", username, ":", "[REDACTED_SECRET]", "@", placeholder, "/api?part=2#tail"))
    assert redact_lane_health_diagnostics(raw) == expected
    assert redact_lane_health_diagnostics(expected) == expected


def test_diagnostic_redactor_preserves_url_suffixes_that_resemble_private_paths():
    # The response middleware retains its separate private-path policy.
    raw = "".join(("https://node.example.invalid:443/home/fixture/%2f/@user/post?next=/", "tmp/fixture#203.0.113.7"))
    expected = "".join(("https://[redacted-host]/home/fixture/%2f/@user/post?next=/", "tmp/fixture#203.0.113.7"))
    assert redact_lane_health_text(raw) == expected
    assert redact_lane_health_text(expected) == expected


_REVIEW_SHAPES = [
    *_URL_SHAPES,
    *[
        (
            "".join(("auth ", "https", "://", "u:", password, "@git.example.invalid/r.git denied")),
            password,
            "".join(("auth ", "https", "://", "u:", "[REDACTED_SECRET]", "@[redacted-host]/r.git denied")),
        )
        for password in (
            "Ab3dE/fG", "Ab3dE+fG", "Ab3dE=fG", "Ab3dE?fG", "Ab3dE#fG",
            "Ab3dE/fG+h9=?tail#end", "Ab3dE%2FfG%2B%3D", "12345",
        )
    ],
    ("getaddrinfo ENOTFOUND node.example.invalid", "node.example.invalid", "getaddrinfo ENOTFOUND [redacted-host]"),
    (
        r"open C:\Users\fixture\private\key.pem denied",
        r"C:\Users\fixture\private\key.pem",
        "open [redacted-path] denied",
    ),
    ("open ~/.ssh/fixture-key denied", "~/.ssh/fixture-key", "open [redacted-path] denied"),
    (
        "".join(("auth ", "https", "://", "bot:", "Alpha!Beta$", "@node.example.invalid:443/api denied")),
        "Alpha!Beta$",
        "".join(("auth ", "https", "://", "bot:", "[REDACTED_SECRET]", "@[redacted-host]/api denied")),
    ),
    (
        "".join(("auth ", "postgres", "://", "bot:", "canary-pass", "@[2001:db8::7]:5432/app denied")),
        "canary-pass",
        "".join(("auth ", "postgres", "://", "bot:", "[REDACTED_SECRET]", "@[redacted-ip]/app denied")),
    ),
    (
        "".join(("auth https://example.org/file?sig=", "canary-secret", "&part=2 denied")),
        "canary-secret",
        "auth https://[redacted-host]/file?sig=[REDACTED_SECRET]&part=2 denied",
    ),
    (
        "".join(("auth ", "https", "://", ":", "Ab3dE/fG+h9=", "@git.example.invalid/r.git denied")),
        "Ab3dE/fG+h9=",
        "".join(("auth ", "https", "://", ":", "[REDACTED_SECRET]", "@[redacted-host]/r.git denied")),
    ),
    (
        "".join(("auth ", "https", "://", "u:", "Ab3dE/fG+h9=", "@[2001:db8::7]:443/api denied")),
        "Ab3dE/fG+h9=",
        "".join(("auth ", "https", "://", "u:", "[REDACTED_SECRET]", "@[redacted-ip]/api denied")),
    ),
    (
        "".join(
            (
                "auth ",
                "https",
                "://",
                "u:",
                "canary",
                "@one.invalid/a and ",
                "https",
                "://",
                "u:",
                "Ab3dE/fG",
                "@two.invalid/b",
            )
        ),
        "canary",
        "".join(
            (
                "auth ",
                "https",
                "://",
                "u:",
                "[REDACTED_SECRET]",
                "@[redacted-host]/a and ",
                "https",
                "://",
                "u:",
                "[REDACTED_SECRET]",
                "@[redacted-host]/b",
            )
        ),
    ),
    ("open ~fixture/.ssh/key denied", "~fixture/.ssh/key", "open [redacted-path] denied"),
    ("open C:/Users/fixture/key denied", "C:/Users/fixture/key", "open [redacted-path] denied"),
    (r"open \\fixture-server\private\key denied", r"\\fixture-server\private\key", "open [redacted-path] denied"),
    *[
        (
            "".join((f"auth https://example.org/file?{key}=", "canary-secret", "&part=2 denied")),
            "canary-secret",
            f"auth https://[redacted-host]/file?{key}=[REDACTED_SECRET]&part=2 denied",
        )
        for key in ("signature", "X-Amz-Signature", "X-Goog-Signature", "s%69g", "api%5Fkey")
    ],
]


@pytest.mark.parametrize(("excerpt", "marker", "expected"), _REVIEW_SHAPES)
@pytest.mark.parametrize("field", ["last_error", "error"])
def test_endpoint_redacts_review_shapes_in_each_served_field(monkeypatch, tmp_path, excerpt, marker, expected, field):
    """Synthetic task records and .diag bytes survive the production response boundary."""
    _configure(monkeypatch, tmp_path, [])
    tasks_dir = tmp_path / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True)
    now = datetime.now(UTC)
    for index, minutes in enumerate((30, 10)):
        _write_task(tasks_dir, f"c-{index}", "claude", now - timedelta(minutes=minutes), excerpt)
    diag = tasks_dir / "c-1.diag"
    diag.write_text(excerpt, encoding="utf-8")
    files_before = {path: path.read_bytes() for path in tasks_dir.iterdir()}
    if field == "error":
        monkeypatch.setattr(
            state_router, "scan_lane_health", lambda *a, **k: LaneHealthScan(observed=False, error=excerpt)
        )

    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.middleware("http")(opsec_path_sanitizer_middleware)
    app.include_router(state_router.router, prefix="/api/state")
    response = TestClient(app).get("/api/state/routing-budget")

    assert response.status_code == 200
    assert marker not in response.text
    assert response.json()["agents"]["claude"]["health"][field] == expected
    assert {path: path.read_bytes() for path in tasks_dir.iterdir()} == files_before


@pytest.mark.parametrize(
    "excerpt",
    [
        "UnknownError Unexpected server error; retrying",
        "Budget ~500K/1M, fraction ~2/3",
        "codes: ENOTFOUND EAI_AGAIN EAI_NONAME ENODATA",
        "ENOTFOUND scripts/api/lane_health.py",
        "x" * 190 + " /home/fixture/private/key.pem denied",
    ],
)
@pytest.mark.parametrize("field", ["last_error", "error"])
def test_endpoint_preserves_safe_text_and_placeholder_boundaries(monkeypatch, tmp_path, excerpt, field):
    _configure(monkeypatch, tmp_path, [])
    tasks_dir = tmp_path / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True)
    now = datetime.now(UTC)
    for index, minutes in enumerate((30, 10)):
        _write_task(tasks_dir, f"c-{index}", "claude", now - timedelta(minutes=minutes), excerpt)
    if field == "error":
        monkeypatch.setattr(
            state_router, "scan_lane_health", lambda *a, **k: LaneHealthScan(observed=False, error=excerpt)
        )
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.middleware("http")(opsec_path_sanitizer_middleware)
    app.include_router(state_router.router, prefix="/api/state")
    response = TestClient(app).get("/api/state/routing-budget")
    assert response.status_code == 200
    expected = excerpt
    if excerpt.startswith("x" * 190):
        expected = "x" * 190 + " [redacted-path] denied" if field == "error" else "x" * 190
    assert response.json()["agents"]["claude"]["health"][field] == expected


@pytest.mark.parametrize(
    ("marker", "prefix_text", "placeholder", "served_prefix"),
    [
        ("/home/fixture/private/key.pem", "", "[redacted-path]", ""),
        ("ENOTFOUND node.example.invalid", "ENOTFOUND ", "[redacted-host]", "ENOTFOUND "),
        ("203.0.113.7", "", "[redacted-ip]", ""),
        (
            "".join(("https", "://", "u:", "Ab3dE/fG", "@host.invalid/api")),
            "https://u:",
            "[REDACTED_SECRET]",
            "https://[redacted-host]",
        ),
    ],
)
def test_endpoint_never_splits_any_placeholder(monkeypatch, tmp_path, marker, prefix_text, placeholder, served_prefix):
    """Probe every interior cutoff position through the production handler."""
    _configure(monkeypatch, tmp_path, [])
    tasks_dir = tmp_path / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True)
    now = datetime.now(UTC)
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.middleware("http")(opsec_path_sanitizer_middleware)
    app.include_router(state_router.router, prefix="/api/state")
    with TestClient(app) as client:
        for offset in range(1, len(placeholder)):
            prefix = "x" * (MAX_ERROR_EXCERPT_CHARS - len(prefix_text) - offset - 1) + " "
            excerpt = prefix + marker
            for index, minutes in enumerate((30, 10)):
                _write_task(tasks_dir, f"c-{index}", "claude", now - timedelta(minutes=minutes), excerpt)
            response = client.get("/api/state/routing-budget")
            assert response.status_code == 200
            # A second serve-time pass also hides any incomplete URL authority
            # left before the truncated credential placeholder.
            expected = (prefix + served_prefix).rstrip()
            if len(expected) > MAX_ERROR_EXCERPT_CHARS:
                expected = (prefix + "https://").rstrip()
            assert response.json()["agents"]["claude"]["health"]["last_error"] == expected
