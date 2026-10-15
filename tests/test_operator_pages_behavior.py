"""Execute the shipped B2 page scripts with synthetic response boundaries."""

import subprocess
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def test_operator_pages_behavior():
    result = subprocess.run(
        ["node", "--test", "tests/operator_pages_behavior.test.cjs", "tests/orient_glance.test.cjs"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@contextmanager
def browser_page():
    with sync_playwright() as runner:
        browser = runner.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()


def serve_page(page, name, responses):
    """Serve the real page and stylesheet; all reads stay synthetic and local."""
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    def route(request):
        path = request.request.url.split("monitor.test", 1)[-1]
        if path == f"/{name}.html":
            request.fulfill(path=ROOT / "dashboards" / f"{name}.html", content_type="text/html")
        elif path == "/monitor.css":
            request.fulfill(path=ROOT / "dashboards" / "monitor.css", content_type="text/css")
        else:
            payload = responses.get(path)
            if callable(payload):
                payload = payload(request)
                if payload is None:
                    return
            if payload is None:
                request.fulfill(status=503, json={"detail": "Synthetic unavailable source"})
            else:
                request.fulfill(json=payload)

    page.route("http://monitor.test/**", route)
    page.goto(f"http://monitor.test/{name}.html")
    return errors


def check_delegate_browser_keyboard_inert_attributes_and_focus_return(browser_page):
    page = browser_page
    task_id = 'safe\'" data-injected="yes"><img src=x onerror="window.injected=true">'
    responses = {
        "/api/delegate/tasks?limit=100": {
            "total": 1,
            "tasks": [{"task_id": task_id, "status": "needs_finalize", "agent": "seat-a"}],
        }
    }
    errors = serve_page(page, "delegate", responses)
    button = page.locator("#completed-content button")
    expect(button).to_have_count(1)
    expect(button).to_have_attribute("data-task-id", task_id)
    expect(page.locator("[data-injected], img")).to_have_count(0)
    responses[f"/api/delegate/tasks/{quote(task_id, safe='~()*!.\'')}"] = {
        "task": {"task_id": task_id, "status": "needs_finalize"},
        "result": None,
        "result_truncated": False,
    }
    button.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("dialog")).to_be_visible()
    expect(page.locator("#task-result")).to_contain_text("completion is not established")
    page.keyboard.press("Shift+Tab")
    expect(page.get_by_role("button", name="Close", exact=True)).to_be_focused()
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Close", exact=True)).to_be_focused()
    page.keyboard.press("Escape")
    expect(button).to_be_focused()
    assert page.evaluate("window.injected") is None
    assert not errors
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def check_epics_browser_selection_reverse_responses_and_filters(browser_page):
    page = browser_page
    pending = []
    rows = [{"stream_id": f"epic:{number}", "registered": False, "lease": None} for number in (1, 2)]
    responses = {
        "/api/epics/v1": {"schema": "remote-epic-lifecycle.v1", "streams": rows},
        "/api/epics/v1/epic%3A1": lambda route: pending.append(route),
        "/api/epics/v1/epic%3A2": {"schema": "remote-epic-lifecycle.v1", **rows[1], "digest": {"pinned": [], "recent": []}},
    }
    errors = serve_page(page, "epics", responses)
    row = page.locator("tr.epic-row").first
    row.focus()
    page.keyboard.press("Enter")
    page.wait_for_function("document.querySelector('#detail-meta').textContent.includes('Loading')")
    page.locator("tr.epic-row").nth(1).click()
    expect(page.locator("#detail-meta")).to_contain_text("epic:2")
    expect(page.locator("#detail-pane h4")).to_have_text("epic:2")
    assert len(pending) == 1
    pending[0].fulfill(json={"schema": "remote-epic-lifecycle.v1", **rows[0], "digest": {"pinned": [], "recent": []}})
    expect(page.locator("#detail-pane h4")).to_have_text("epic:2")
    page.locator("#filter-search").fill("epic:1")
    expect(page.locator("tr.epic-row")).to_have_count(1)
    page.get_by_role("button", name="Reset", exact=True).click()
    expect(page.locator("tr.epic-row")).to_have_count(2)
    assert not errors
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def check_graph_browser_list_alternative_and_quote_labels(browser_page):
    page = browser_page
    title = 'safe" onfocus="window.injected=true'
    data = {
        "schema": "epics-graph.v1",
        "nodes": {
            "areas": [{"id": 'area:"unsafe', "stream_id": "area-one", "title": "Area one"}],
            "epics": [{"id": "epic:7", "number": 7, "title": title, "area_id": "area-one", "lease": None}],
        },
        "edges": [],
        "membership_complete": False,
        "issues_by_epic": {"7": {"items": None, "total_open": None, "truncated": None}},
    }
    errors = serve_page(page, "epics-map", {"/api/epics/graph/v1": data})
    page.get_by_text("Relationship list alternative").click()
    button = page.locator("#map-content details button")
    button.focus()
    page.keyboard.press("Enter")
    expect(page.locator("#detail-pane")).to_contain_text("membership is incomplete")
    expect(page.locator("#detail-pane")).not_to_contain_text("0 open issues")
    expect(page.locator("[onfocus]")).to_have_count(0)
    assert page.evaluate("window.injected") is None
    assert not errors
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def check_routing_browser_partial_success_and_recovery(browser_page):
    page = browser_page
    responses = {
        "/api/state/routing-budget": {
            "agents": {}, "in_flight": {},
            "claude_accounts": {"claude:a": {"status": "unknown", "age_s": None, "reason": "not_probed"}},
        },
        "/api/runtime/agents": {"agents": [{"name": "seat-a", "supported_modes": []}]},
        "/api/runtime/usage?days=7": None,
        "/api/delegate/tasks?limit=100": None,
    }
    errors = serve_page(page, "routing", responses)
    expect(page.locator("#refresh-status")).to_contain_text("2 failed")
    expect(page.locator("#agent-table")).to_contain_text("seat-a")
    expect(page.locator("#summary-grid")).to_contain_text("unknown/unknown recent")
    expect(page.locator("#claude-accounts-table")).to_contain_text("Source age unknown")
    expect(page.locator("#claude-accounts-table")).not_to_contain_text("0s ago")
    responses["/api/runtime/usage?days=7"] = {"records_total": 0, "by_agent": {}}
    responses["/api/delegate/tasks?limit=100"] = {"total": 0, "tasks": []}
    page.get_by_role("button", name="Refresh", exact=True).click()
    expect(page.locator("#refresh-status")).to_contain_text("Feeds read")
    expect(page.locator("#delegate-table")).to_contain_text("No task rows returned")
    assert not errors
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def check_orient_browser_nullable_health_and_independent_feed(browser_page):
    page = browser_page
    errors = serve_page(page, "orient", {
        "/api/orient": {"health": {"api": True, "sources_db": False, "mcp_sources": None}},
        "/api/discussions/active": {"discussions": []},
        "/api/epics/v1": {"streams": []},
        "/api/occupancy": {"hosts": {}},
        "/api/fleet/workers/v1": {"hosts": []},
        "/api/fleet/projects/v1": {"hosts": {}},
    })
    expect(page.locator("#health-content")).to_contain_text("healthy")
    expect(page.locator("#health-content")).to_contain_text("down")
    assert page.locator("#health-content").inner_text().count("unknown") == 3  # Two fields plus source age.
    expect(page.locator("#git-content")).to_contain_text("State unknown")
    expect(page.locator("#discussions-content")).to_contain_text("Source age unknown")
    assert not errors
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def check_routing_browser_retained_age_advances_without_refresh(browser_page):
    page = browser_page
    serve_page(page, "routing", {
        "/api/state/routing-budget": {
            "agents": {},
            "claude_accounts": {"claude:a": {"status": "stale", "age_s": 10, "weekly": {"left_pct": 5}}},
        },
        "/api/runtime/agents": {"agents": []},
        "/api/runtime/usage?days=7": {"records_total": 0, "by_agent": {}},
        "/api/delegate/tasks?limit=100": {"total": 0, "tasks": []},
    })
    age = page.locator("#claude-accounts-table [data-source-age]")
    expect(age).to_have_count(1)
    page.evaluate("""() => {
      const node = document.querySelector('[data-source-age]');
      node.dataset.ageAt = String(Date.now() - 65000);
      updateSourceAges();
    }""")
    expect(age).to_have_text("1m ago")
    expect(page.locator("#claude-accounts-table")).to_contain_text("stale historical sample")


if __name__ == "__main__":
    # Browser proof is explicit: standard CI does not install a Chromium binary.
    # The default pytest entry runs the Node regressions without downloading one.
    checks = [
        check_delegate_browser_keyboard_inert_attributes_and_focus_return,
        check_epics_browser_selection_reverse_responses_and_filters,
        check_graph_browser_list_alternative_and_quote_labels,
        check_routing_browser_partial_success_and_recovery,
        check_orient_browser_nullable_health_and_independent_feed,
        check_routing_browser_retained_age_advances_without_refresh,
    ]
    for check in checks:
        with browser_page() as browser:
            check(browser)
        print(f"PASS {check.__name__}")
    print(f"{len(checks)} Chromium behavior scenarios passed")
