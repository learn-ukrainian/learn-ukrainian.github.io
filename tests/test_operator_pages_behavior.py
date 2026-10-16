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


def check_orient_browser_mixed_partial_counters_are_inert(browser_page):
    page = browser_page
    inert = '50%" data-injected="inert"><b data-injected>inert</b>'
    responses = {
        "/api/orient": {
            "git": {"ahead_of_origin": inert, "branch": inert},
            "pipeline": {"summary": {"tracks": {
                "bad": {"total": inert, "research_done": inert, "content_done": inert, "audit_passing": inert},
                "good": {"total": 2, "research_done": 0, "content_done": 1, "audit_passing": 2},
                "missing": None,
            }}},
            "wiki": {"by_track": {"bad": {"compiled": inert, "total": inert, "pct": inert},
                                    "good": {"compiled": 0, "total": 2, "pct": 50}, "missing": None}},
            "delegate": {"active_count": None, "recent": []},
            "health": {"api": True, "mcp_sources": None, "mcp_rag": False, "sources_db": False},
        },
        "/api/discussions/active": {"discussions": [None, {"thread_id": inert, "channel": inert,
            "agents": [inert], "last_round": inert, "message_count": inert, "status": "brand-new-status"}]},
        "/api/delegate/tasks?limit=5": {"total": 8, "tasks": [None,
            {"task_id": inert, "status": "needs_finalize"}, {"task_id": "safe", "status": "brand-new-status"}]},
        "/api/epics/v1": {"streams": [{"stream_id": inert, "lease": {"state": "Active"}}]},
    }
    errors = serve_page(page, "orient", responses)
    expect(page.locator("#delegate-content")).to_contain_text("needs_finalize")
    expect(page.locator("#delegate-content")).to_contain_text("brand-new-status")
    expect(page.locator("#delegate-content")).to_contain_text("1 malformed rows omitted")
    expect(page.locator("#delegate-muted")).to_have_text("unknown active")
    expect(page.locator("#health-content .mini-card").nth(1)).to_contain_text("unknown")
    expect(page.locator("#health-content .mini-card").nth(2)).to_contain_text("down")
    expect(page.locator("#glance-epics tbody td").last).to_have_text("unknown")
    expect(page.locator("#wiki-content")).to_contain_text("0/2 (50%)")
    expect(page.locator("#pipeline-content")).to_contain_text("research 0/2")
    expect(page.locator("#discussions-content")).to_contain_text("round unknown")
    expect(page.locator("[data-injected], b, img")).to_have_count(0)
    assert page.locator("#wiki-content .bar-fill").evaluate_all("nodes => nodes.map(n => n.style.width)") == ["0%", "50%", "0%"]
    assert page.locator("#pipeline-content .bar-fill").evaluate_all("nodes => nodes.map(n => n.style.width)") == ["0%", "100%", "0%"]
    expect(page.locator("#git-content")).to_contain_text(inert)
    assert not errors


def check_epics_browser_case_variant_lease_filter_and_detail(browser_page):
    page = browser_page
    rows = [{"stream_id": f"epic:{i}", "lease": {"state": "aCtIvE", **expiry}}
            for i, expiry in enumerate(({}, {"expires_at": "bad"}, {"expires_at": "2999-01-01"},
                                       {"expires_at": "2000-01-01"}), start=1)]
    responses = {"/api/epics/v1": {"schema": "remote-epic-lifecycle.v1", "streams": rows}}
    for row in rows:
        responses[f"/api/epics/v1/{quote(row['stream_id'], safe='')}"] = {
            "schema": "remote-epic-lifecycle.v1", **row, "digest": {"pinned": [], "recent": []}}
    errors = serve_page(page, "epics", responses)
    expect(page.locator("#epics-tbody .pill.active")).to_have_count(1)
    expect(page.locator("#epics-tbody .pill.unknown")).to_have_count(2)
    expect(page.locator("#epics-tbody .pill.expired")).to_have_count(1)
    page.locator("#filter-state").select_option("active")
    expect(page.locator("tr.epic-row")).to_have_count(1)
    expect(page.locator("tr.epic-row")).to_have_attribute("data-stream-id", "epic:3")
    page.locator("#filter-state").select_option("unknown")
    expect(page.locator("tr.epic-row")).to_have_count(2)
    page.locator("tr.epic-row").first.click()
    expect(page.locator("#detail-pane .pill.unknown")).to_have_count(1)
    assert not errors


def check_graph_browser_explicit_complete_empty_and_null_membership(browser_page):
    page = browser_page
    data = {"schema": "epics-graph.v1", "membership_complete": None, "incomplete_nodes": [],
            "nodes": {"areas": [], "epics": [{"id": "epic:7", "number": 7, "lease": {"state": "Active"},
                        "open_issue_count": 0, "closed_issue_count": 0}]}, "edges": [],
            "issues_by_epic": {"7": {"items": [], "total_open": 0, "truncated": False}}}
    errors = serve_page(page, "epics-map", {"/api/epics/graph/v1": data})
    page.locator(".epic-list button").click()
    expect(page.locator("#detail-pane")).to_contain_text("membership is unknown")
    expect(page.locator(".epic-meta")).to_contain_text("Open: unknown")
    expect(page.locator(".epic-list .status-chip")).to_have_text("Lease unknown")
    data["membership_complete"] = True
    page.get_by_role("button", name="Refresh", exact=True).click()
    expect(page.locator("#detail-pane")).to_contain_text("0 open issues in the cache")
    expect(page.locator(".epic-meta")).to_contain_text("Open: 0")
    data["incomplete_nodes"] = [9]
    page.get_by_role("button", name="Refresh", exact=True).click()
    expect(page.locator("#detail-pane")).to_contain_text("membership is incomplete")
    expect(page.locator("#detail-pane")).not_to_contain_text("0 open issues")
    assert not errors


def check_routing_browser_malformed_sibling_and_known_zero(browser_page):
    page = browser_page
    routing = {"agents": {}, "in_flight": {}}
    errors = serve_page(page, "routing", {
        "/api/state/routing-budget": routing,
        "/api/delegate/tasks?limit=100": {"total": 8, "tasks": [None,
            {"task_id": 'safe" data-injected="yes', "status": "needs_finalize"},
            {"task_id": "other", "status": "new-status"}]},
        "/api/runtime/agents": {"agents": []},
        "/api/runtime/usage?days=7": {"records_total": 0, "by_agent": {}},
    })
    flight = page.locator("#summary-grid .panel").nth(1).locator(".value")
    expect(flight).to_have_text("unknown")
    expect(page.locator("#delegate-table")).to_contain_text("needs_finalize")
    expect(page.locator("#delegate-table")).to_contain_text("2 of 8")
    expect(page.locator("#delegate-table")).to_contain_text("1 malformed rows omitted")
    expect(page.locator("[data-injected]")).to_have_count(0)
    routing["in_flight"] = {"safe": 0}
    page.get_by_role("button", name="Refresh", exact=True).click()
    expect(flight).to_have_text("0")
    assert not errors


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
        check_orient_browser_mixed_partial_counters_are_inert,
        check_epics_browser_case_variant_lease_filter_and_detail,
        check_graph_browser_explicit_complete_empty_and_null_membership,
        check_routing_browser_malformed_sibling_and_known_zero,
    ]
    for check in checks:
        with browser_page() as browser:
            check(browser)
        print(f"PASS {check.__name__}")
    print(f"{len(checks)} Chromium behavior scenarios passed")
