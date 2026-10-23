"""Static UI contracts for the Work evidence-rail dashboard (unified P3)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "dashboards" / "work.html"
PRIVATE_URL = "http://127.0.0.1:8769/v1/projection"
SCHEMA_DIGEST = "89fb9c1eec41baaa00a328d456340111163c1e3ab899cd7baa15e284fff65bde"
PUBLIC_COMMIT = "f522c8dba5a68d86fe29d1a36bd8cfeb8c3acb9d"


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
