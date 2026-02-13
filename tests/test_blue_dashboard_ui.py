"""
UI tests for the Blue dashboard (batch-monitor.html).

Uses Playwright headless Chromium against the running FastAPI server.
Tests that the dashboard:
  1. Loads without JS errors
  2. Detects the API (no "API offline" state)
  3. Renders track cards with data
  4. Shows the freshness banner
  5. All API fetches succeed (no 404s in network log)
  6. Key UI sections are visible and populated

Requires: uvicorn running on localhost:8000
"""

import re
import pytest
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
DASHBOARD = f"{BASE}/v2-blue/batch-monitor.html"


@pytest.fixture(scope="module")
def browser_context():
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    yield context
    context.close()
    browser.close()
    pw.stop()


@pytest.fixture(scope="module")
def page_with_data(browser_context):
    """Load dashboard and wait for initial data fetch."""
    page = browser_context.new_page()

    # Collect JS errors
    js_errors = []
    page.on("pageerror", lambda err: js_errors.append(str(err)))

    # Collect ALL console messages
    console_msgs = []
    page.on("console", lambda msg: console_msgs.append({"type": msg.type, "text": msg.text}))

    # Collect failed network requests
    failed_requests = []
    successful_api_requests = []
    def on_response(response):
        if "/api/" in response.url:
            if response.status >= 400:
                failed_requests.append(f"{response.status} {response.url}")
            else:
                successful_api_requests.append(f"{response.status} {response.url}")
    page.on("response", on_response)

    page.goto(DASHBOARD)

    # Wait for the dashboard to finish loading data
    # The dashboard updates #last-update after refreshAll() completes
    try:
        page.wait_for_function(
            "document.getElementById('last-update')?.textContent?.trim().length > 0",
            timeout=15000,
        )
    except Exception:
        pass  # We'll check what happened below

    # Give renders a moment to complete
    page.wait_for_timeout(2000)

    page._test_js_errors = js_errors
    page._test_console_msgs = console_msgs
    page._test_failed_requests = failed_requests
    page._test_successful_api_requests = successful_api_requests
    return page


# NOTE: `const S` is top-level in <script> — NOT on window in browsers.
# Use page.evaluate("S.field") which accesses the script's scope correctly.

class TestPageLoads:
    """Basic page load checks."""

    def test_no_js_errors(self, page_with_data):
        errors = page_with_data._test_js_errors
        assert errors == [], f"JavaScript errors on page: {errors}"

    def test_no_failed_api_requests(self, page_with_data):
        failed = page_with_data._test_failed_requests
        # Filter out known missing endpoints (legacy dispatcher start/stop/cleanup)
        known_missing = {"dispatcher/start", "dispatcher/stop", "cleanup"}
        real_failures = [
            f for f in failed
            if not any(k in f for k in known_missing)
        ]
        assert real_failures == [], f"Failed API requests: {real_failures}"

    def test_title_contains_blue(self, page_with_data):
        assert "Blue" in page_with_data.title()

    def test_api_calls_were_made(self, page_with_data):
        """At least some API calls should have succeeded."""
        ok = page_with_data._test_successful_api_requests
        assert len(ok) > 0, "No successful API calls were made at all"


class TestApiDetection:
    """Dashboard should detect the API is online."""

    def test_api_mode_active(self, page_with_data):
        """S.apiMode should be true (accessed via script scope, not window)."""
        api_mode = page_with_data.evaluate("S.apiMode")
        assert api_mode is True, (
            f"Dashboard failed to detect API (S.apiMode={api_mode}). "
            f"Console: {[m for m in page_with_data._test_console_msgs if 'Blue' in m.get('text','')]}"
        )

    def test_no_offline_banner(self, page_with_data):
        """Should not show 'API offline' or 'no data' state."""
        body_text = page_with_data.inner_text("body")
        assert "API offline" not in body_text, "Dashboard showing 'API offline'"
        assert "Could not connect" not in body_text, "Dashboard showing connection error"

    def test_server_note_hidden(self, page_with_data):
        """The 'server not running' note should be hidden when API is detected."""
        visible = page_with_data.evaluate(
            "document.getElementById('server-note')?.style.display !== 'none'"
        )
        # If apiMode is true, server-note should be display:none
        api_mode = page_with_data.evaluate("S.apiMode")
        if api_mode:
            assert not visible, "server-note is visible despite API being detected"


class TestTrackCards:
    """Track cards should render with real data."""

    def test_track_cards_exist(self, page_with_data):
        """Should render track cards."""
        cards = page_with_data.query_selector_all(".track-card")
        assert len(cards) > 0, "No .track-card elements found"

    def test_track_cards_have_names(self, page_with_data):
        """Each card should show a track name."""
        cards = page_with_data.query_selector_all(".track-card")
        empty_cards = []
        for i, card in enumerate(cards):
            text = card.inner_text().strip()
            if len(text) < 2:
                empty_cards.append(i)
        assert empty_cards == [], f"Track cards at indices {empty_cards} have no text content"

    def test_at_least_5_tracks(self, page_with_data):
        """Should show at least 5 tracks (a1, a2, b1, b2, c1 minimum)."""
        cards = page_with_data.query_selector_all(".track-card")
        assert len(cards) >= 5, f"Only {len(cards)} track cards, expected at least 5"


class TestDataPopulated:
    """State object should contain real data from the API."""

    def test_dispatcher_state_loaded(self, page_with_data):
        """S.dispatcherState should have tracks."""
        tracks = page_with_data.evaluate("Object.keys(S.dispatcherState?.tracks || {})")
        assert len(tracks) > 0, (
            "S.dispatcherState.tracks is empty. "
            f"S.apiMode={page_with_data.evaluate('S.apiMode')}"
        )

    def test_live_status_loaded(self, page_with_data):
        """S.liveStatus should have track data."""
        tracks = page_with_data.evaluate("Object.keys(S.liveStatus || {})")
        assert len(tracks) > 0, (
            "S.liveStatus is empty — /api/blue/live-status not loading. "
            f"S.apiMode={page_with_data.evaluate('S.apiMode')}"
        )

    def test_freshness_loaded(self, page_with_data):
        """S.freshness should have data source ages."""
        sources = page_with_data.evaluate("Object.keys(S.freshness || {})")
        assert len(sources) > 0, "S.freshness is empty — /api/blue/freshness not loading"

    def test_health_loaded(self, page_with_data):
        """S.health should have status ok."""
        status = page_with_data.evaluate("S.health?.status")
        assert status == "ok", f"S.health.status is {status}, expected 'ok'"

    def test_checkpoints_is_object(self, page_with_data):
        """S.checkpoints should be a dict (may be empty but must be object)."""
        cp_type = page_with_data.evaluate("typeof S.checkpoints")
        assert cp_type == "object", f"S.checkpoints type is {cp_type}"


class TestConsoleErrors:
    """Check for meaningful console errors (not just warnings)."""

    def test_no_critical_console_errors(self, page_with_data):
        """No console.error messages that indicate broken functionality."""
        errors = [
            m for m in page_with_data._test_console_msgs
            if m["type"] == "error"
            and ("TypeError" in m["text"] or "ReferenceError" in m["text"] or "SyntaxError" in m["text"])
        ]
        assert errors == [], f"Critical JS errors in console: {[e['text'] for e in errors]}"

    def test_no_blue_warn_for_404(self, page_with_data):
        """No [Blue] API warnings for our core endpoints (404 = misconfigured path)."""
        warns = [
            m for m in page_with_data._test_console_msgs
            if m["type"] == "warning"
            and "[Blue] API" in m["text"]
            and ("returned 4" in m["text"] or "failed" in m["text"])
        ]
        # Filter out known missing/legacy endpoints
        known_missing = {"dispatcher/start", "dispatcher/stop", "cleanup", "resolved-failures"}
        real_warns = [
            w for w in warns
            if not any(k in w["text"] for k in known_missing)
        ]
        assert real_warns == [], f"API warnings for core endpoints: {[w['text'] for w in real_warns]}"


class TestUIElements:
    """Key UI sections should be visible."""

    def test_topbar_visible(self, page_with_data):
        topbar = page_with_data.query_selector(".topbar")
        assert topbar is not None, ".topbar not found"
        assert topbar.is_visible(), ".topbar is not visible"

    def test_last_update_shows_time(self, page_with_data):
        """#last-update should show a timestamp, not 'never'."""
        text = page_with_data.inner_text("#last-update")
        assert text.strip() != "", "#last-update is empty"
        assert text.strip().lower() != "never", "#last-update still shows 'never'"

    def test_main_content_not_empty(self, page_with_data):
        """Page body should have substantial content."""
        body_text = page_with_data.inner_text("body")
        assert len(body_text) > 100, f"Page body has very little text ({len(body_text)} chars)"

    def test_api_badge_shows_api(self, page_with_data):
        """API/FILE badge should show 'API' when connected."""
        badge = page_with_data.query_selector(".badge-api")
        if badge:
            assert badge.inner_text().strip() == "API"


class TestNetworkIntegrity:
    """Verify all API calls from the dashboard actually succeed."""

    def test_all_blue_fetches_succeed(self, page_with_data):
        """Fetch all Blue endpoints from the page context."""
        results = page_with_data.evaluate("""
            async () => {
                const endpoints = [
                    '/api/blue/health',
                    '/api/blue/metrics',
                    '/api/blue/history',
                    '/api/blue/live-status',
                    '/api/blue/freshness',
                ];
                const results = [];
                for (const ep of endpoints) {
                    try {
                        const r = await fetch(ep);
                        results.push({ ep, status: r.status, ok: r.ok });
                    } catch (e) {
                        results.push({ ep, status: 0, ok: false, error: e.message });
                    }
                }
                return results;
            }
        """)
        failed = [r for r in results if not r["ok"]]
        assert failed == [], f"Blue API calls failed from browser: {failed}"

    def test_all_shared_fetches_succeed(self, page_with_data):
        """Fetch all shared endpoints from the page context."""
        results = page_with_data.evaluate("""
            async () => {
                const endpoints = [
                    '/api/batch/dispatcher',
                    '/api/batch/checkpoints',
                    '/api/batch/failures',
                    '/api/batch/usage',
                    '/api/batch/dispatcher/running',
                ];
                const results = [];
                for (const ep of endpoints) {
                    try {
                        const r = await fetch(ep);
                        results.push({ ep, status: r.status, ok: r.ok });
                    } catch (e) {
                        results.push({ ep, status: 0, ok: false, error: e.message });
                    }
                }
                return results;
            }
        """)
        failed = [r for r in results if not r["ok"]]
        assert failed == [], f"Shared API calls failed from browser: {failed}"


class TestDiagnostics:
    """Diagnostic tests that help debug failures — run last."""

    def test_dump_console_on_failure(self, page_with_data):
        """If apiMode is false, dump all console messages for debugging."""
        api_mode = page_with_data.evaluate("S.apiMode")
        if not api_mode:
            blue_msgs = [m for m in page_with_data._test_console_msgs if "Blue" in m.get("text", "")]
            all_msgs = page_with_data._test_console_msgs[:20]
            pytest.fail(
                f"apiMode is false! Console messages:\n"
                f"Blue-specific: {blue_msgs}\n"
                f"All (first 20): {all_msgs}\n"
                f"Failed requests: {page_with_data._test_failed_requests}\n"
                f"Successful requests: {page_with_data._test_successful_api_requests}"
            )
