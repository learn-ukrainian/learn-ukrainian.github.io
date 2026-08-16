"""Static UI contracts for the Work evidence-rail dashboard."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "dashboards" / "work.html"
INDEX = ROOT / "dashboards" / "index.html"


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
    # Extract allowlist literal
    match = re.search(r"ALLOWED_FILTER_KEYS = new Set\(\[(.*?)\]\)", html, re.S)
    assert match
    keys = re.findall(r"'([a-z_]+)'", match.group(1))
    assert "health" in keys
    assert "kind" in keys
    assert "q" not in keys
    assert "endpoint" not in keys


def test_work_page_has_no_dead_fresh_url_self_replacement():
    """CodeQL: dead url construction used no-op replace('&','&') before finalUrl."""
    html = WORK.read_text(encoding="utf-8")
    assert "fresh.replace(" not in html
    assert ".replace('&', '&')" not in html
    assert '.replace("&", "&")' not in html
    # Single live composition for the projection request (public contract).
    assert "fetch(finalUrl" in html
    assert re.search(
        r"const finalUrl = `/api/work/v1/projection\$\{qs\}\$\{opts && opts\.fresh",
        html,
    )
    assert html.count("/api/work/v1/projection") == 1
