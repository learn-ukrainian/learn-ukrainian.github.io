"""Static UI contracts for the Work evidence-rail dashboard (unified P3)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "dashboards" / "work.html"
INDEX = ROOT / "dashboards" / "index.html"

PRIVATE_URL = "http://127.0.0.1:8767/v1/projection"
SCHEMA_DIGEST = "89fb9c1eec41baaa00a328d456340111163c1e3ab899cd7baa15e284fff65bde"
PUBLIC_COMMIT = "f522c8dba5a68d86fe29d1a36bd8cfeb8c3acb9d"


def test_work_page_evidence_rail_and_a11y_surface():
    html = WORK.read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="/monitor.css">' in html
    assert 'class="monitor-nav"' in html
    assert 'aria-label="Monitor sections"' in html
    assert 'class="active" href="/work.html"' in html
    assert "Evidence rail" in html or "evidence rail" in html.lower()
    assert 'role="listbox"' in html
    assert "prefers-reduced-motion" in html
    assert "max-width: 420px" in html or "max-width: 390px" in html or "420px" in html
    assert "focus-visible" in html
    assert "⌘K" in html or "Ctrl+K" in html or "cmd" in html
    assert "FOUNDATION_COMPLETE" in html
    assert 'data-read-only="true"' in html
    # No dark-console aesthetic fork
    assert "#0d1117" not in html
    # Saved-view allowlist present client-side
    assert "ALLOWED_FILTER_KEYS" in html
    assert "private_endpoint" in html  # rejected explicitly
    assert "All repositories" in html


def test_work_page_has_no_mutation_controls():
    html = WORK.read_text(encoding="utf-8")
    for banned in (
        "method: 'POST'",
        'method: "POST"',
        "/api/delegate/dispatch",
        "auto-merge",
        "mutate",
        "Apply proposal",
    ):
        assert banned not in html


def test_work_page_keyboard_handlers_present():
    html = WORK.read_text(encoding="utf-8")
    assert "ArrowDown" in html
    assert "ArrowUp" in html
    assert "Escape" in html
    assert "keydown" in html


def test_index_and_primary_nav_link_to_work():
    index = INDEX.read_text(encoding="utf-8")
    assert 'href="/work.html"' in index
    assert ">Work<" in index
    for name in ("fleet.html", "orient.html", "runtime.html", "delegate.html"):
        html = (ROOT / "dashboards" / name).read_text(encoding="utf-8")
        assert 'href="/work.html"' in html, name


def test_saved_view_client_writes_only_allowlisted_keys():
    html = WORK.read_text(encoding="utf-8")
    match = re.search(r"ALLOWED_FILTER_KEYS = new Set\(\[(.*?)\]\)", html, re.S)
    assert match
    keys = re.findall(r"'([a-z_]+)'", match.group(1))
    assert "health" in keys
    assert "kind" in keys
    assert "source_id" in keys
    assert "q" not in keys
    assert "endpoint" not in keys


def test_work_page_public_refresh_and_private_fixed_url_contract():
    """Public refresh may use fresh=true; private URL is a non-configurable constant."""
    html = WORK.read_text(encoding="utf-8")
    assert "fresh.replace(" not in html
    assert ".replace('&', '&')" not in html
    assert '.replace("&", "&")' not in html
    assert f"'{PRIVATE_URL}'" in html or f'"{PRIVATE_URL}"' in html
    assert html.count(PRIVATE_URL) >= 1
    assert "PRIVATE_TIMEOUT_MS = 5000" in html or "timeoutMs: PRIVATE_TIMEOUT_MS" in html
    assert "Promise.allSettled" in html
    assert "credentials: 'omit'" in html or 'credentials: "omit"' in html
    assert "cache: 'no-store'" in html or 'cache: "no-store"' in html
    assert "referrerPolicy: 'no-referrer'" in html or 'referrerPolicy: "no-referrer"' in html
    assert "Accept: 'application/json'" in html or 'Accept: "application/json"' in html
    assert SCHEMA_DIGEST in html
    assert PUBLIC_COMMIT in html
    # Public path appears as the constant / composition site only (not private URL host).
    assert html.count("/api/work/v1/projection") == 1
    assert "fresh=true" in html
    # Filters must not be composed into the private request.
    assert "PRIVATE_PROJECTION_URL" in html
    assert "queryString(filters)" not in html


def test_work_page_closed_private_status_vocabulary():
    html = WORK.read_text(encoding="utf-8")
    for token in (
        "unavailable · timeout",
        "unavailable · unreachable",
        "unavailable · schema_mismatch",
        "unavailable · identity_collision",
        "Work projection unavailable · public=",
        "No source projection is available. Retry refresh.",
    ):
        assert token in html
    # Must not template raw exception text into the banner.
    assert "err.message" not in html
    assert "console.error" not in html
    assert "console.log" not in html


def test_work_page_fetchjson_keeps_timeout_through_json_parse():
    """Private AbortController budget must cover status handling + body parse."""
    html = WORK.read_text(encoding="utf-8")
    start = html.index("function fetchJson(")
    end = html.index("function classifyPublicFailure(", start)
    body = html[start:end]
    # Single finalization path clears the timer after settlement.
    assert ".finally(" in body
    assert body.count("clearTimeout(timer)") == 1
    # Abort during body read is typed timeout, not schema_mismatch / raw error.
    assert "aborted(parseErr)" in body
    assert "err.code = 'timeout'" in body or 'err.code = "timeout"' in body
    # Degraded sections are terminal (no admitted counts/items).
    assert "'degraded'" in html
    terminal_line = [
        line for line in html.splitlines() if "new Set(['unavailable', 'permission_denied', 'timeout'" in line
    ]
    assert terminal_line, "terminal section status set missing"
    assert "degraded" in terminal_line[0]


def test_work_page_shareable_url_strips_private_selectors():
    html = WORK.read_text(encoding="utf-8")
    assert "PUBLIC_SINGLETON_REPO" in html
    assert "shareableFilters" in html
    assert "private-local-adapter" in html
    # Private source/repo must not be written into transferable saved-view state.
    assert "value !== PUBLIC_SINGLETON_REPO" in html or "value !== PUBLIC_SINGLETON_REPO" in html
    assert "value !== PUBLIC_SOURCE_ID" in html
