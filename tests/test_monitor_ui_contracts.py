import json
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.reads_content

ROOT = Path(__file__).resolve().parents[1]
DASHBOARDS = ROOT / "dashboards"
def test_orient_page_renders_active_discussions_widget():
    html = (DASHBOARDS / "orient.html").read_text(encoding="utf-8")
    assert "Active Discussions" in html
    assert "/api/discussions/active" in html
    assert "Promise.allSettled" in html
    assert "Discussion lookup unavailable" in html
    assert "renderDiscussions" in html
    assert "fleet.html?conversation=" in html
    assert "channels.html?channel=" not in html
    # Client abort must outlast measured /api/orient latency (~4–5s) (#7976).
    assert "ORIENT_TIMEOUT_MS = 20000" in html
    assert "GLANCE_TIMEOUT_MS = 12000" in html
    assert "fetchJson('/api/orient', ORIENT_TIMEOUT_MS)" in html


def test_launchpad_defers_orient_off_first_paint_promise_all() -> None:
    """Home must not block first paint on ~4–5s /api/orient (#7975 residual)."""
    html = (DASHBOARDS / "index.html").read_text(encoding="utf-8")
    assert "async function loadOrientStat()" in html
    assert "void loadOrientStat();" in html
    assert "safeFetch('/api/orient')" in html
    # Orient must not sit in the critical Promise.all tuple with overview/summary.
    critical = html.split("await Promise.all([", 1)[1].split("]);", 1)[0]
    assert "safeFetch('/api/orient')" not in critical


def test_acp_page_groups_duplicate_fanout_and_keeps_protocol_order():
    html_path = json.dumps(str(DASHBOARDS / "acp.html"))
    script = f"""
    const fs = require('fs');
    const html = fs.readFileSync({html_path}, 'utf8');
    const start = html.indexOf('function transcriptMessages');
    const end = html.indexOf('function actorLabel');
    if (start < 0 || end <= start) throw new Error('grouping helpers not found');
    eval(html.slice(start, end));
    const messages = transcriptMessages({{messages: [
      {{kind: 'request', body: 'Shared question', sender: 'root', recipient: 'codex', created_at: '2026-01-01T00:00:00Z', ordinal: 1, round: 1}},
      {{kind: 'request', body: 'Shared question', sender: 'root', recipient: 'grok', created_at: '2026-01-01T00:00:00Z', ordinal: 2, round: 1}},
      {{kind: 'reply', body: 'Grok answer', sender: 'grok', recipient: 'root', created_at: '2026-01-01T00:00:02Z', ordinal: 3, round: 1}},
      {{kind: 'reply', body: 'Codex answer', sender: 'codex', recipient: 'root', created_at: '2026-01-01T00:00:01Z', ordinal: 4, round: 1}},
      {{kind: 'reply', body: 'Peer context', sender: 'grok', recipient: 'codex', created_at: '2026-01-01T00:00:03Z', ordinal: 5, round: 2}},
      {{kind: 'reply', body: 'Refined answer', sender: 'codex', recipient: 'root', created_at: '2026-01-01T00:00:04Z', ordinal: 6, round: 2}},
      {{kind: 'request', body: 'Unanswered prompt', sender: 'root', recipient: 'grok', created_at: '2026-01-01T00:00:05Z', ordinal: 7, round: 3}},
      {{kind: 'notice', body: 'Protocol note', sender: 'root', recipient: 'grok', created_at: '2026-01-01T00:00:06Z', ordinal: 8, round: 3}},
      {{kind: 'synthesis', body: 'Final answer', sender: 'codex', recipient: 'root', created_at: '2026-01-01T00:00:07Z', ordinal: 9, round: 3}}
    ]}});
    console.log(JSON.stringify({{
      grouped: groupTranscript(messages),
      withoutSynthesis: groupTranscript(messages.filter(message => message.kind !== 'synthesis'))
    }}));
    """
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True, timeout=30)
    output = json.loads(result.stdout)
    grouped = output["grouped"]

    assert [group["round"] for group in grouped["rounds"]] == [1, 2, 3]
    assert grouped["rounds"][0]["prompts"] == [
        {
            "body": "Shared question",
            "sender": "root",
            "recipients": ["codex", "grok"],
            "createdAt": "2026-01-01T00:00:00Z",
            "ordinal": 1,
        }
    ]
    assert [reply["body"] for reply in grouped["rounds"][0]["replies"]] == [
        "Grok answer",
        "Codex answer",
    ]
    assert [item["body"] for item in grouped["rounds"][1]["contexts"]] == ["Peer context"]
    assert [item["body"] for item in grouped["rounds"][1]["replies"]] == ["Refined answer"]
    assert grouped["rounds"][2]["replies"] == []
    assert [item["body"] for item in grouped["rounds"][2]["other"]] == ["Protocol note"]
    assert [item["body"] for item in grouped["finalization"]] == ["Final answer"]
    assert output["withoutSynthesis"]["finalization"] == []


def test_launchpad_and_progress_avoid_zero_backlog_when_pipeline_versions_unavailable():
    """Missing or timed-out pipeline-versions must not stringify as '0 backlog'."""
    index_html = (DASHBOARDS / "index.html").read_text(encoding="utf-8")
    progress_html = (DASHBOARDS / "progress.html").read_text(encoding="utf-8")

    for html in (index_html, progress_html):
        assert "BACKLOG_PENDING_LABEL = 'backlog pending'" in html
        assert "formatBacklogSegment" in html
        assert "if (!pv)" in html
        assert "pending: true" in html

    assert "0 backlog" not in index_html.split("formatBacklogSegment")[0]
    assert ".catch(() => ({}))" not in progress_html
    assert ".catch(() => null)" in progress_html

    index_helpers = index_html[
        index_html.index("function operationalTrackEntries")
        : index_html.index("async function loadStats")
    ]
    script = f"""
    {index_helpers}
    const summary = {{
      tracks: {{
        'l2-uk-en-a1': {{ total: 10, module_source: 'curriculum', dossier_done: 3, published_mdx: 1 }},
      }},
    }};
    const unavailable = resolveOperationalBuildState(null, summary);
    const progressCard = `${{displayBuildCount(unavailable.current)}} current · ${{formatBacklogSegment(unavailable)}} · 3 dossiers · 1 published`;
    const withData = resolveOperationalBuildState({{
      per_track: {{
        'l2-uk-en-a1': {{ v6: 2, v5: 5, v3: 1, unbuilt: 0 }},
      }},
    }}, summary);
    const resolvedCard = `${{displayBuildCount(withData.current)}} current · ${{formatBacklogSegment(withData)}} · 3 dossiers · 1 published`;
    console.log(JSON.stringify({{
      unavailable,
      progressCard,
      resolvedCard,
      showsZeroBacklog: progressCard.includes('0 backlog'),
    }}));
    """
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True, timeout=30)
    output = json.loads(result.stdout)

    assert output["unavailable"]["pending"] is True
    assert output["showsZeroBacklog"] is False
    assert output["progressCard"] == "— current · backlog pending · 3 dossiers · 1 published"
    assert output["resolvedCard"] == "2 current · 6 backlog · 3 dossiers · 1 published"


def test_delegate_detail_pane_projects_observer_safe_task_json() -> None:
    html = (DASHBOARDS / "delegate.html").read_text(encoding="utf-8")

    assert "function observerTaskView(task)" in html
    assert "JSON.stringify(observerTaskView(detail.task || {}), null, 2)" in html
    assert "Observer-safe task summary" in html
    for sensitive_key in (
        "cwd",
        "runtime_tmp_root",
        "worktree_path",
        "result_file",
        "stderr_excerpt",
    ):
        assert f"'{sensitive_key}'" not in html, (
            f"delegate detail pane must not reference raw task key {sensitive_key!r}"
        )
    assert "JSON.stringify(detail.task || {}, null, 2)" not in html


def test_orient_failure_path_clears_stranded_loading_skeletons() -> None:
    """A failed /api/orient load must not leave sections promising data forever (#7976)."""
    html = (DASHBOARDS / "orient.html").read_text(encoding="utf-8")
    assert "Unavailable — session snapshot failed to load" in html
    assert 'node.textContent.trim() === \'Loading...\'' in html


def test_launchpad_hides_api_surfaces_strip_until_populated() -> None:
    """No orphan empty chrome: the contracts note stays hidden until it has content (#7976)."""
    html = (DASHBOARDS / "index.html").read_text(encoding="utf-8")
    assert 'id="api-surfaces" class="contracts-note" hidden' in html
    assert "el.hidden = false;" in html


def test_launchpad_passing_stat_is_honest_when_no_audit_data() -> None:
    """A green 0 implies measured failure; absence of audits must render as unknown (#7976).

    Unaudited-only totals (pass=0, fail=0, unaudited=N) must NOT count as
    recorded audits — that state still shows Passing · no audit data.
    """
    html = (DASHBOARDS / "index.html").read_text(encoding="utf-8")
    assert "Passing · no audit data" in html
    assert "acc.fail += stats.fail || 0;" in html
    assert "acc.unaudited += stats.unaudited || 0;" in html
    assert "const auditsRecorded = (t.pass + t.fail) > 0;" in html
    assert "(t.pass + t.fail + t.unaudited) > 0" not in html
