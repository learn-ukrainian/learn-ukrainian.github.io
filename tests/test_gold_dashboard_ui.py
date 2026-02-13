"""
UI tests for the Gold dashboard (batch-monitor.html).

Uses Playwright headless Chromium against the running FastAPI server.
Tests that the dashboard:
  1. Loads without JS errors
  2. Detects the API (dispatch status not OFFLINE)
  3. Renders track cards with data
  4. Shows real-time progress and active modules
  5. All API fetches succeed (no 404s in network log)
  6. Key UI sections are visible and populated

Requires: uvicorn running on localhost:8090
"""

import pytest
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8888"
DASHBOARD = f"{BASE}/v2-gold/batch-monitor.html"


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
    # The dashboard updates #debug-info after refreshAll() completes
    try:
        page.wait_for_function(
            "document.getElementById('debug-info')?.textContent?.trim().length > 0",
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


class TestPageLoads:
    """Basic page load checks."""

    def test_no_js_errors(self, page_with_data):
        errors = page_with_data._test_js_errors
        assert errors == [], f"JavaScript errors on page: {errors}"

    def test_no_failed_api_requests(self, page_with_data):
        failed = page_with_data._test_failed_requests
        assert failed == [], f"Failed API requests: {failed}"

    def test_title_contains_gold(self, page_with_data):
        assert "GOLD" in page_with_data.title()

    def test_api_calls_were_made(self, page_with_data):
        """At least some API calls should have succeeded."""
        ok = page_with_data._test_successful_api_requests
        assert len(ok) > 0, "No successful API calls were made at all"


class TestApiDetection:
    """Dashboard should detect the API is online."""

    def test_dispatcher_status_online(self, page_with_data):
        """#dispatch-status should not say 'OFFLINE'."""
        status = page_with_data.inner_text("#dispatch-status")
        assert "OFFLINE" not in status, f"Dispatcher status is {status}, expected RUNNING or STOPPED"

    def test_debug_info_populated(self, page_with_data):
        """#debug-info should show sync time and track counts."""
        info = page_with_data.inner_text("#debug-info")
        assert "Sync:" in info, "Debug info missing sync time"
        assert "Tracks:" in info, "Debug info missing track count"


class TestTrackCards:
    """Track cards should render with real data."""

    def test_track_cards_exist(self, page_with_data):
        """Should render track cards."""
        cards = page_with_data.query_selector_all(".track-card")
        assert len(cards) > 0, "No .track-card elements found"

    def test_at_least_10_tracks(self, page_with_data):
        """Should show at least 10 tracks (Gold finds all from manifest)."""
        cards = page_with_data.query_selector_all(".track-card")
        assert len(cards) >= 10, f"Only {len(cards)} track cards, expected >10"

    def test_b1_shows_progress(self, page_with_data):
        """B1 track should show >0 passed modules."""
        # Find the card with "B1" title
        b1_card = page_with_data.evaluate("""
            () => {
                const cards = Array.from(document.querySelectorAll('.track-card'));
                const b1 = cards.find(c => c.querySelector('.track-label').textContent.includes('B1'));
                return b1 ? b1.textContent : null;
            }
        """)
        assert b1_card is not None, "B1 track card not found"
        # Check text content for "passed" logic
        # Card text format: "B1 ... X / Y passed ... Z%"
        assert "passed" in b1_card
        assert "0 /" not in b1_card, f"B1 card shows 0 passed: {b1_card}"


class TestHeatmap:
    """Heatmap should render modules."""

    def test_heatmap_dots_exist(self, page_with_data):
        dots = page_with_data.query_selector_all(".module-dot")
        assert len(dots) > 0, "No heatmap dots found"

    def test_heatmap_shows_passed(self, page_with_data):
        passed = page_with_data.query_selector_all(".dot-pass")
        assert len(passed) > 0, "No passed (green) dots in heatmap"


class TestNetworkIntegrity:
    """Verify Gold-specific API calls succeed."""

    def test_gold_endpoints_succeed(self, page_with_data):
        """Fetch Gold endpoints from the page context."""
        results = page_with_data.evaluate("""
            async () => {
                const endpoints = [
                    '/api/gold/health',
                    '/api/gold/ground-truth',
                    '/api/gold/active-orchestration'
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
        assert failed == [], f"Gold API calls failed from browser: {failed}"
