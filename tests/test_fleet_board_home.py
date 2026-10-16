"""DOM render contracts for the fleet board home."""

from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import urlsplit


def test_fleet_board_home_render() -> None:
    result = subprocess.run(
        ["node", "--test", "tests/fleet_board_home.test.cjs"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def verify_home_browser() -> None:
    """Run directly with an installed Chromium; all page reads are intercepted."""
    from playwright.sync_api import expect, sync_playwright

    root = Path(__file__).resolve().parents[1]
    reports = [{"name": name, "status": "ok", "age_s": 0, "error": None} for name in ("github", "mq_state")]
    epic = {"epic": "\udfff", "title": "Synthetic board", "state": "idle"}
    bodies = {
        "/api/epics/v1": {"streams": [{"stream_id": "\ud800", "stream_name": "\udfff", "title": "Synthetic lane"}]},
        "/api/work/v1/projection": {"items": [], "sources": []},
        "/api/ops/v1/test-slots": {
            "schema": "test-slots.status.v1",
            "enabled": True,
            "pool_exists": False,
            "pool_size": 2,
            "slots_in_use": 0,
            "slots_free": 2,
            "queue_depth": 0,
            "error": None,
        },
        "/api/fleet/v1/prs": {
            "schema": "fleet.v1.prs",
            "sources": reports,
            "data": {
                "prs": [
                    {
                        "repo": "sample/repo",
                        "number": 17,
                        "head_sha": "head-current",
                        "title": "Synthetic PR",
                        "cf": {"verdict": "APPROVE", "at_head": True},
                        "ci": "green",
                        "gate": "green",
                        "draft": False,
                        "hours_idle": 0,
                    }
                ]
            },
        },
        "/api/fleet/v1/now": {
            "schema": "fleet.v1.now",
            "sources": [],
            "data": {
                "attention": [{"title": "Synthetic attention", "target": {"type": "pr", "id": "\ud800"}}],
                "epics": [epic],
            },
        },
        "/api/fleet/v1/epics": {"schema": "fleet.v1.epics", "sources": [], "data": {"epics": [epic]}},
    }
    requests, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.clock.install()

        def serve(route):
            request = route.request
            target = urlsplit(request.url)
            path = target.path
            requests.append((request.method, path + ("?" + target.query if target.query else "")))
            if path.startswith("/api/"):
                route.fulfill(json=bodies.get(path))
            elif path in ("/fleet-board.html", "/fleet-board.js", "/fleet-board.css", "/monitor.css"):
                route.fulfill(path=root / "dashboards" / path.lstrip("/"))
            else:
                route.fulfill(status=404, body="")

        page.route("**/*", serve)
        page.goto("http://board.test/fleet-board.html")
        app = page.locator("#fb-app")
        expect(app).to_contain_text("Synthetic lane")
        expect(app).to_contain_text("CF APPROVE at observed head")
        expect(app).to_contain_text("Pool observation unknown")
        expect(page.locator(".fb-card[href]")).to_have_count(0)
        expect(page.locator(".fb-attn-item[href]")).to_have_count(0)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")

        bodies["/api/epics/v1"]["streams"][0].update(stream_id="epic:next", title="Recovered lane")
        bodies["/api/ops/v1/test-slots"]["pool_exists"] = True
        page.clock.fast_forward(30_001)
        expect(app).to_contain_text("Recovered lane")
        expect(app).to_contain_text("Pool 2; occupied 0; free 2; queued 0")
        expect(page.locator('a[href="/epics.html#epic%3Anext"]')).to_have_count(1)
        assert not errors
        assert all(method == "GET" for method, _ in requests)
        assert not any("fresh=true" in path or "agent-monitor" in path for _, path in requests)
        browser.close()


if __name__ == "__main__":
    verify_home_browser()
    print("PASS: shipped home renders surrogate identifiers and accepts the next poll; synthetic GETs only")
