"""Static UI contracts for the Work evidence-rail dashboard (unified P3)."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "dashboards" / "work.html"
INDEX = ROOT / "dashboards" / "index.html"

PRIVATE_URL = "http://127.0.0.1:8769/v1/projection"
SCHEMA_DIGEST = "89fb9c1eec41baaa00a328d456340111163c1e3ab899cd7baa15e284fff65bde"
PUBLIC_COMMIT = "f522c8dba5a68d86fe29d1a36bd8cfeb8c3acb9d"


def test_work_page_evidence_rail_and_a11y_surface():
    """FX-08 adjacent: reduced-motion, focus-visible, narrow breakpoints present."""
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
    """FX-10 design-only: Work surface stays mutation:false / no write controls."""
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
    """FX-08: keyboard handlers for list navigation and Esc are present."""
    html = WORK.read_text(encoding="utf-8")
    assert "ArrowDown" in html
    assert "ArrowUp" in html
    assert "Escape" in html
    assert "keydown" in html
    assert "els.list.focus()" in html


def test_index_and_primary_nav_link_to_work():
    index = INDEX.read_text(encoding="utf-8")
    assert 'href="/work.html"' in index
    assert ">Work<" in index
    for name in ("fleet.html", "orient.html", "runtime.html", "delegate.html"):
        html = (ROOT / "dashboards" / name).read_text(encoding="utf-8")
        assert 'href="/work.html"' in html, name


def test_saved_view_client_writes_only_allowlisted_keys():
    """FX-09: client allowlist excludes free-text / endpoint keys."""
    html = WORK.read_text(encoding="utf-8")
    match = re.search(r"ALLOWED_FILTER_KEYS = new Set\(\[(.*?)\]\)", html, re.S)
    assert match
    keys = re.findall(r"'([a-z_]+)'", match.group(1))
    assert "health" in keys
    assert "kind" in keys
    assert "source_id" in keys
    assert "view" in keys
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
    # R-UI-1..3: per-source card meta helpers
    assert "formatAdmittedPrivateMeta" in html
    assert "publicStreamsComplete" in html
    assert "sectionCount" in html


def test_work_page_closed_private_status_vocabulary():
    """FX-06: typed private failure vocabulary only (no raw exception templating)."""
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
    """FX-06: Private AbortController budget must cover status handling + body parse."""
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
    """FX-09: shareableFilters strips private slug/source; never writes private-local-adapter."""
    html = WORK.read_text(encoding="utf-8")
    assert "PUBLIC_SINGLETON_REPO" in html
    assert "shareableFilters" in html
    assert "private-local-adapter" in html
    # Private source/repo must not be written into transferable saved-view state.
    assert "value !== PUBLIC_SINGLETON_REPO" in html or "value !== PUBLIC_SINGLETON_REPO" in html
    assert "value !== PUBLIC_SOURCE_ID" in html


def test_work_page_admitted_unavailable_private_meta_omits_zero_counts():
    """Admitted private status=unavailable shows status without issues=0 · prs=0."""
    html = WORK.read_text(encoding="utf-8")
    fmt_start = html.index("function formatAdmittedPrivateMeta(")
    fmt_end = html.index("function isPlaceholderPrivateSource(", fmt_start)
    fmt_body = html[fmt_start:fmt_end]
    assert "priv.status === 'unavailable'" in fmt_body
    assert "issues=" in fmt_body
    assert "prs=" in fmt_body
    # Early return for unavailable must precede the issues=/prs= inventory line.
    assert fmt_body.index("priv.status === 'unavailable'") < fmt_body.index("' · issues='")

    ph_start = html.index("function isPlaceholderPrivateSource(")
    ph_end = html.index("function installView(", ph_start)
    ph_body = html[ph_start:ph_end]
    assert "not_configured" in ph_body
    # Admitted unavailable is not a placeholder; only not_configured is.
    assert "priv.status === 'unavailable'" not in ph_body


def test_work_page_actionable_default_view_contracts():
    html = WORK.read_text(encoding="utf-8")
    assert 'id="filter-view"' in html
    assert '<option value="actionable">Actionable</option>' in html
    assert '<option value="all">All</option>' in html
    assert "isActionable" in html
    assert "INSPECT_UNKNOWN" in html
    assert "OPEN_GITHUB" in html
    assert "NONE" in html
    assert "OFF_TRACK" in html
    assert "AT_RISK" in html


def test_work_page_actionable_predicate_parity_with_server_ssot():
    """The JS isActionable predicate must match scripts/work/attention.py (#6880).

    The server-side predicate is the SSOT for /api/work/v1/next; the dashboard
    keeps a JS mirror. Deny-list drift or a dropped OFF_TRACK/AT_RISK inclusion
    would silently fork the Actionable view from the machine pick list.
    """
    from scripts.work.attention import NON_ACTIONABLE_ACTION_CODES, is_actionable

    html = WORK.read_text(encoding="utf-8")
    match = re.search(r"NON_ACTIONABLE_ACTION_CODES = new Set\(\[(.*?)\]\)", html)
    assert match, "JS deny-list constant missing from work.html"
    js_codes = set(re.findall(r"'([A-Z_]+)'", match.group(1)))
    assert js_codes == set(NON_ACTIONABLE_ACTION_CODES)

    start = html.index("function isActionable(")
    end = html.index("function ", start + 1)
    body = html[start:end]
    # Health inclusion mirrors the Python short-circuit exactly.
    assert "item.health === 'OFF_TRACK' || item.health === 'AT_RISK'" in body
    assert "return true" in body
    # Fallback path consults the same deny list on safe_next_action.code.
    assert "safe_next_action" in body
    assert "NON_ACTIONABLE_ACTION_CODES.has(code)" in body
    assert "!!code" in body

    # Truth table over the Python SSOT — the semantics both sides must share.
    assert is_actionable({"health": "OFF_TRACK", "safe_next_action": {"code": "NONE"}})
    assert is_actionable({"health": "AT_RISK", "safe_next_action": {"code": "OPEN_GITHUB"}})
    assert is_actionable({"health": "ON_TRACK", "safe_next_action": {"code": "MERGE_WHEN_READY"}})
    for denied in sorted(NON_ACTIONABLE_ACTION_CODES):
        assert not is_actionable({"health": "ON_TRACK", "safe_next_action": {"code": denied}})
        assert not is_actionable({"health": "UNKNOWN", "safe_next_action": {"code": denied}})
    assert not is_actionable({"health": "ON_TRACK", "safe_next_action": {}})
    assert not is_actionable(None)


def test_work_page_actionable_predicate_behavioral_js_parity():
    """Run the live JS predicate in Node against shared fixtures (#6890 #4).

    Substring scans cannot catch a boolean inversion that keeps the scanned
    tokens; evaluating the extracted JS against the Python SSOT closes that gap.
    """
    if shutil.which("node") is None:
        pytest.skip("node required for JS actionable parity")

    from scripts.work.attention import NON_ACTIONABLE_ACTION_CODES, is_actionable

    fixtures = [
        None,
        {},
        {"health": "OFF_TRACK", "safe_next_action": {"code": "NONE"}},
        {"health": "AT_RISK", "safe_next_action": {"code": "OPEN_GITHUB"}},
        {"health": "ON_TRACK", "safe_next_action": {"code": "MERGE_WHEN_READY"}},
        {"health": "ON_TRACK", "safe_next_action": {"code": "FIX_CI"}},
        {"health": "UNKNOWN", "safe_next_action": {"code": "WAIT_CI"}},
        {"health": "ON_TRACK", "safe_next_action": {}},
        {"health": "ON_TRACK"},
        {"health": "UNKNOWN", "safe_next_action": {"code": ""}},
    ]
    for denied in sorted(NON_ACTIONABLE_ACTION_CODES):
        fixtures.append({"health": "ON_TRACK", "safe_next_action": {"code": denied}})
        fixtures.append({"health": "UNKNOWN", "safe_next_action": {"code": denied}})

    expected = [bool(is_actionable(item)) for item in fixtures]
    html_path = json.dumps(str(WORK))
    fixtures_json = json.dumps(fixtures)
    script = f"""
    const fs = require('fs');
    const html = fs.readFileSync({html_path}, 'utf8');
    const start = html.indexOf('const NON_ACTIONABLE_ACTION_CODES');
    const fnStart = html.indexOf('function isActionable(');
    const fnEnd = html.indexOf('function ', fnStart + 1);
    if (start < 0 || fnStart < 0 || fnEnd <= fnStart) {{
      throw new Error('isActionable block not found');
    }}
    eval(html.slice(start, fnEnd));
    const fixtures = {fixtures_json};
    console.log(JSON.stringify(fixtures.map((item) => isActionable(item))));
    """
    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    js_results = json.loads(result.stdout)
    assert js_results == expected
    # Explicit kill for the boolean-inversion residual the substring scan misses.
    assert expected[fixtures.index({"health": "ON_TRACK", "safe_next_action": {"code": "NONE"}})] is False
    assert expected[fixtures.index({"health": "ON_TRACK", "safe_next_action": {"code": "MERGE_WHEN_READY"}})] is True
