"""Dashboard and route contract tests for the Epics Map UI (#10403, #7295)."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.api.main import app
from scripts.api.route_contracts import contract_for_page

ROOT = Path(__file__).resolve().parents[1]
DASHBOARDS = ROOT / "dashboards"
EPICS_MAP_HTML = DASHBOARDS / "epics-map.html"


def test_epics_map_page_is_a_read_only_observer() -> None:
    html = EPICS_MAP_HTML.read_text(encoding="utf-8")

    assert 'data-read-only="true"' in html
    assert "Relationship map · cached membership" in html
    assert "Epics grouped by their operating area." in html
    assert "Read-only operator dashboard:" in html
    assert "/api/epics/graph/v1" in html
    assert 'class="monitor-nav"' in html
    assert '<a class="active" href="/epics-map.html">Map</a>' in html
    assert '<link rel="stylesheet" href="/monitor.css">' in html
    assert 'id="error-banner"' in html
    assert 'id="btn-refresh"' in html
    assert 'id="last-updated-text"' in html
    assert 'id="map-content"' in html
    assert 'id="detail-pane"' in html

    # Strict read-only invariant: no mutating POST/PUT/DELETE forms or fetch methods
    for prohibited in (
        "<form",
        "method: 'POST'",
        'method: "POST"',
        "method: 'PUT'",
        'method: "PUT"',
        "method: 'DELETE'",
        'method: "DELETE"',
        "/claim",
        "/heartbeat",
        "/handoff",
        "/release",
    ):
        assert prohibited not in html


def test_epics_map_page_opsec_and_privacy_guarantees() -> None:
    html = EPICS_MAP_HTML.read_text(encoding="utf-8")

    # The HTML template itself must not embed raw private paths or IP addresses
    assert "/Users/" not in html
    assert "/home/" not in html
    assert "127.0.0.1" not in html
    assert "localhost:" not in html
    assert "#0d1117" not in html


def test_epics_map_page_contract_registration() -> None:
    contract = contract_for_page("epics-map.html")
    assert contract is not None
    assert contract.url == "/epics-map.html"
    assert "/api/epics/graph/v1" in contract.source_of_truth
    assert "15s" in contract.freshness
    assert "read-only" in contract.purpose.lower()


def test_epics_map_page_serves_over_http() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/epics-map.html")
    assert response.status_code == 200
    assert "Epics grouped by their operating area." in response.text


def test_epics_map_js_behavioral_membership_logic() -> None:
    """Evaluate epics-map.html JS membership rendering and predicates in Node (AC-01, AC-02)."""
    if shutil.which("node") is None:
        pytest.skip("node required for JS parity check")

    html_path = json.dumps(str(EPICS_MAP_HTML))
    script = f"""
    const fs = require('fs');
    const html = fs.readFileSync({html_path}, 'utf8');

    const document = {{
      getElementById: (id) => ({{
        id,
        textContent: '',
        innerHTML: '',
        classList: {{ add: () => {{}}, remove: () => {{}} }},
        addEventListener: () => {{}},
      }}),
      createElement: (tag) => {{
        let _text = '';
        return {{
          set textContent(v) {{ _text = String(v); }},
          get textContent() {{ return _text; }},
          get innerHTML() {{
            return _text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
          }},
        }};
      }},
    }};

    const scriptStart = html.indexOf('const state = {{');
    const scriptEnd = html.indexOf('async function loadGraph()');
    if (scriptStart < 0 || scriptEnd <= scriptStart) throw new Error('script slice not found');
    const body = html.slice(scriptStart, scriptEnd);

    const runner = new Function('document', `
      ${{body}}
      return {{
        state,
        renderIssueSection,
        isObject,
        nonNegativeInteger,
        positiveInteger,
        epicNumber,
      }};
    `);
    const env = runner(document);

    // Helpers behavior tests
    const helperResults = {{
      nonNegValidNum: env.nonNegativeInteger(0),
      nonNegPositive: env.nonNegativeInteger(42),
      nonNegStr: env.nonNegativeInteger("7"),
      nonNegNeg: env.nonNegativeInteger(-1),
      nonNegNullNoFallback: env.nonNegativeInteger(null),
      nonNegNullWithFallback: env.nonNegativeInteger(null, 99),
      nonNegInvalidStr: env.nonNegativeInteger("abc"),
      posIntValid: env.positiveInteger(5),
      posIntZero: env.positiveInteger(0),
      posIntNeg: env.positiveInteger(-3),
      posIntStr: env.positiveInteger("12"),
      posIntInvalid: env.positiveInteger("xyz"),
      isObjPlain: env.isObject({{ a: 1 }}),
      isObjArray: env.isObject([]),
      isObjNull: env.isObject(null),
      isObjPrim: env.isObject("str"),
      epicNumDirect: env.epicNumber({{ number: 7177 }}),
      epicNumId: env.epicNumber({{ id: "epic:6943" }}),
      epicNumInvalid: env.epicNumber({{ id: "custom:foo" }}),
    }};

    // 1. Missing buckets
    env.state.data = {{ status: "no-cache", issues_by_epic: {{}} }};
    const missingBucketNoCache = env.renderIssueSection({{ number: 7919 }});

    env.state.data = {{ status: "ok", issues_by_epic: {{}} }};
    const missingBucketWarming = env.renderIssueSection({{ number: 7919 }});

    // 2. Feed-wide incompleteness (membership_complete: false)
    env.state.data = {{
      membership_complete: false,
      incomplete_nodes: [7100],
      stale: false,
      issues_by_epic: {{
        "7919": {{ items: null, total_open: null, truncated: null }},
      }},
    }};
    const incompleteFresh = env.renderIssueSection({{ number: 7919 }});

    env.state.data.stale = true;
    const incompleteStale = env.renderIssueSection({{ number: 7919 }});

    // Feed-wide incompleteness via incomplete_nodes without explicit membership_complete: false
    env.state.data = {{
      incomplete_nodes: [7100],
      stale: false,
      issues_by_epic: {{
        "7919": {{
          items: [{{ number: 101, title: "Usable-looking row" }}],
          total_open: null,
          truncated: null,
        }},
      }},
    }};
    const incompleteNodesWithRows = env.renderIssueSection({{ number: 7919 }});

    // 3. Null items/total on complete response without completeness markers
    env.state.data = {{
      stale: false,
      issues_by_epic: {{
        "7919": {{ items: null, total_open: null, truncated: null }},
      }},
    }};
    const nullItemsAndTotalFresh = env.renderIssueSection({{ number: 7919 }});

    env.state.data.stale = true;
    const nullItemsAndTotalStale = env.renderIssueSection({{ number: 7919 }});

    // Total is null but items array contains usable-looking rows: must NOT count rows
    env.state.data = {{
      stale: false,
      issues_by_epic: {{
        "7919": {{
          items: [
            {{ number: 1, title: "Row 1" }},
            {{ number: 2, title: "Row 2" }},
          ],
          total_open: null,
          truncated: null,
        }},
      }},
    }};
    const nullTotalWithRows = env.renderIssueSection({{ number: 7919 }});

    // Items is null but total_open is a number: must NOT imply zero or complete
    env.state.data = {{
      stale: false,
      issues_by_epic: {{
        "7919": {{ items: null, total_open: 5, truncated: null }},
      }},
    }};
    const nullItemsWithTotal = env.renderIssueSection({{ number: 7919 }});

    // 4. Complete zero (known zero)
    env.state.data = {{
      membership_complete: true,
      stale: false,
      issues_by_epic: {{
        "7919": {{ items: [], total_open: 0, truncated: false }},
      }},
    }};
    const completeZeroFresh = env.renderIssueSection({{ number: 7919 }});

    env.state.data.stale = true;
    const completeZeroStale = env.renderIssueSection({{ number: 7919 }});

    // 5. Complete nonzero (known nonzero)
    env.state.data = {{
      membership_complete: true,
      stale: false,
      issues_by_epic: {{
        "7919": {{
          items: [{{ number: 8888, title: "A single open task", state: "open" }}],
          total_open: 1,
          truncated: false,
        }},
      }},
    }};
    const completeOneFresh = env.renderIssueSection({{ number: 7919 }});

    env.state.data = {{
      membership_complete: true,
      stale: false,
      issues_by_epic: {{
        "7919": {{
          items: [
            {{ number: 8881, title: "Task 1", state: "open" }},
            {{ number: 8882, title: "Task 2", state: "open" }},
            {{ number: 8883, title: "Task 3", state: "open" }},
            {{ number: 8884, title: "Task 4", state: "open" }},
          ],
          total_open: 4,
          truncated: false,
        }},
      }},
    }};
    const completeFourFresh = env.renderIssueSection({{ number: 7919 }});

    const sixtyItems = Array.from({{ length: 50 }}, (_, i) => ({{
      number: 1000 + i,
      title: "Capped item " + i,
      state: "open",
    }}));
    env.state.data = {{
      membership_complete: true,
      stale: false,
      issues_by_epic: {{
        "7919": {{
          items: sixtyItems,
          total_open: 60,
          truncated: true,
        }},
      }},
    }};
    const completeTruncated = env.renderIssueSection({{ number: 7919 }});

    const results = {{
      helperResults,
      missingBucketNoCache,
      missingBucketWarming,
      incompleteFresh,
      incompleteStale,
      incompleteNodesWithRows,
      nullItemsAndTotalFresh,
      nullItemsAndTotalStale,
      nullTotalWithRows,
      nullItemsWithTotal,
      completeZeroFresh,
      completeZeroStale,
      completeOneFresh,
      completeFourFresh,
      completeTruncated,
    }};
    console.log(JSON.stringify(results));
    """

    proc = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True, timeout=30)
    out = json.loads(proc.stdout)

    # 1. Helper predicates and formatters
    h = out["helperResults"]
    assert h["nonNegValidNum"] == 0
    assert h["nonNegPositive"] == 42
    assert h["nonNegStr"] is None  # Remote counters require numeric observations.
    assert h["nonNegNeg"] is None
    assert h["nonNegNullNoFallback"] is None
    assert h["nonNegNullWithFallback"] == 99
    assert h["nonNegInvalidStr"] is None
    assert h["posIntValid"] == 5
    assert h["posIntZero"] is None
    assert h["posIntNeg"] is None
    assert h["posIntStr"] == 12
    assert h["posIntInvalid"] is None
    assert h["isObjPlain"] is True
    assert h["isObjArray"] is False
    assert h["isObjNull"] is False
    assert h["isObjPrim"] is False
    assert h["epicNumDirect"] == 7177
    assert h["epicNumId"] == 6943
    assert h["epicNumInvalid"] is None

    # 2. Missing buckets
    assert out["missingBucketNoCache"] == (
        '<section class="detail-section"><h5>Cached issue membership</h5>'
        '<div class="empty"><strong>Not yet cached.</strong><br>'
        "Issue membership is not yet cached because the background audit has no completed cache."
        "</div></section>"
    )
    assert out["missingBucketWarming"] == (
        '<section class="detail-section"><h5>Cached issue membership</h5>'
        '<div class="empty"><strong>Not yet cached.</strong><br>'
        "Issue membership for this epic is not yet cached. The background audit may still be warming the feed."
        "</div></section>"
    )

    # 3. Feed-wide incompleteness (incomplete state / incomplete membership)
    assert out["incompleteFresh"] == (
        '<section class="detail-section"><h5>Cached issue membership</h5>'
        '<p class="detail-lede">Open issue membership is incomplete in the cache.</p>'
        '<div class="empty compact">No issue rows are available in the cached membership.</div>'
        "</section>"
    )
    assert out["incompleteStale"] == (
        '<section class="detail-section"><h5>Cached issue membership</h5>'
        '<p class="detail-lede">Open issue membership is incomplete in the stale cache.</p>'
        '<div class="empty compact">No issue rows are available in the cached membership.</div>'
        "</section>"
    )
    assert out["incompleteNodesWithRows"] == (
        '<section class="detail-section"><h5>Cached issue membership</h5>'
        '<p class="detail-lede">Open issue membership is incomplete in the cache.</p>'
        '<div class="empty compact">No issue rows are available in the cached membership.</div>'
        "</section>"
    )
    # Crucial invariant: never assert zero on incomplete membership
    assert "0 open issues" not in out["incompleteFresh"]
    assert "0 open issues" not in out["incompleteStale"]
    assert "0 open issues" not in out["incompleteNodesWithRows"]

    # 4. Null items / totals on complete responses without completeness markers (unknown membership)
    assert out["nullItemsAndTotalFresh"] == (
        '<section class="detail-section"><h5>Cached issue membership</h5>'
        '<p class="detail-lede">Open issue membership is unknown in the cache.</p>'
        '<div class="empty compact">No issue rows are available in the cached membership.</div>'
        "</section>"
    )
    assert out["nullItemsAndTotalStale"] == (
        '<section class="detail-section"><h5>Cached issue membership</h5>'
        '<p class="detail-lede">Open issue membership is unknown in the stale cache.</p>'
        '<div class="empty compact">No issue rows are available in the cached membership.</div>'
        "</section>"
    )
    assert out["nullTotalWithRows"] == (
        '<section class="detail-section"><h5>Cached issue membership</h5>'
        '<p class="detail-lede">Open issue membership is unknown in the cache.</p>'
        '<div class="empty compact">No issue rows are available in the cached membership.</div>'
        "</section>"
    )
    assert out["nullItemsWithTotal"] == (
        '<section class="detail-section"><h5>Cached issue membership</h5>'
        '<p class="detail-lede">Open issue membership is unknown in the cache.</p>'
        '<div class="empty compact">No issue rows are available in the cached membership.</div>'
        "</section>"
    )
    assert "0 open issues" not in out["nullItemsAndTotalFresh"]
    assert "0 open issues" not in out["nullItemsAndTotalStale"]
    assert "0 open issues" not in out["nullTotalWithRows"]
    assert "0 open issues" not in out["nullItemsWithTotal"]

    # 5. Known complete zero
    assert out["completeZeroFresh"] == (
        '<section class="detail-section"><h5>Cached issue membership</h5>'
        '<p class="detail-lede">0 open issues in the cache.</p>'
        '<div class="empty compact">No issue rows are available in the cached membership.</div>'
        "</section>"
    )
    assert out["completeZeroStale"] == (
        '<section class="detail-section"><h5>Cached issue membership</h5>'
        '<p class="detail-lede">0 open issues in the stale cache.</p>'
        '<div class="empty compact">No issue rows are available in the cached membership.</div>'
        "</section>"
    )

    # 6. Known complete nonzero
    assert out["completeOneFresh"] == (
        '<section class="detail-section"><h5>Cached issue membership</h5>'
        '<p class="detail-lede">1 open issue in the cache.</p>'
        '<ul class="issue-list"><li class="issue-item">'
        '<a class="issue-link" href="https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8888" '
        'target="_blank" rel="noopener noreferrer"><span class="issue-row">'
        '<span class="issue-number">#8888</span>'
        '<span class="issue-title">A single open task</span>'
        '<span class="issue-state">open</span>'
        "</span></a></li></ul></section>"
    )
    assert "4 open issues in the cache." in out["completeFourFresh"]
    assert '<span class="issue-number">#8881</span>' in out["completeFourFresh"]

    # Truncation cap behavior
    assert "Showing 50 of 60 open issues." in out["completeTruncated"]
    assert "View all 60 on GitHub" in out["completeTruncated"]
    assert "The feed caps this panel at 50 issue rows." in out["completeTruncated"]
