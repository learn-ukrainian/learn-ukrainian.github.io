import json
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.reads_content

ROOT = Path(__file__).resolve().parents[1]
# Product pages moved to the product package (Monitor split, C-4687).
PRODUCT_PAGES = ROOT / "scripts" / "project_api" / "static"


def test_launchpad_and_progress_avoid_zero_backlog_when_pipeline_versions_unavailable():
    """Missing or timed-out pipeline-versions must not stringify as '0 backlog'."""
    index_html = (PRODUCT_PAGES / "index.html").read_text(encoding="utf-8")
    progress_html = (PRODUCT_PAGES / "progress.html").read_text(encoding="utf-8")

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


def test_launchpad_passing_stat_is_honest_when_no_audit_data() -> None:
    """A green 0 implies measured failure; absence of audits must render as unknown (#7976).

    Unaudited-only totals (pass=0, fail=0, unaudited=N) must NOT count as
    recorded audits — that state still shows Passing · no audit data.
    """
    html = (PRODUCT_PAGES / "index.html").read_text(encoding="utf-8")
    assert "Passing · no audit data" in html
    assert "acc.fail += stats.fail || 0;" in html
    assert "acc.unaudited += stats.unaudited || 0;" in html
    assert "const auditsRecorded = (t.pass + t.fail) > 0;" in html
    assert "(t.pass + t.fail + t.unaudited) > 0" not in html
