import json
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.reads_content

ROOT = Path(__file__).resolve().parents[1]
DASHBOARDS = ROOT / "dashboards"
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
