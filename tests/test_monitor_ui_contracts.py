import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DASHBOARDS = ROOT / "dashboards"
PRIMARY_NAV_HREFS = [
    "/",
    "/orient.html",
    "/fleet.html",
    "/artifacts/",
    "/runtime.html",
    "/docs",
]


def test_index_page_uses_shared_parchment_monitor_design():
    html = (DASHBOARDS / "index.html").read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="/monitor.css">' in html
    assert '<a class="active" href="/">Home</a>' in html
    assert "Operations launchpad" in html
    assert 'href="/artifacts/"' in html
    assert "comms-stat" not in html
    assert "/api/comms/batch-progress" not in html
    assert "#0d1117" not in html
    for href in [
        "/admin.html",
        "/fleet.html",
        "/audit-dashboard.html",
        "/build-events.html",
        "/consultation.html",
        "/cost.html",
        "/curriculum-dashboard.html",
        "/delegate.html",
        "/routing.html",
        "/artifacts/",
        "/image-explorer.html",
        "/orient.html",
        "/progress.html",
        "/quality.html",
        "/runtime.html",
        "/track-health.html",
        "/wiki.html",
    ]:
        assert f'href="{href}"' in html


@pytest.mark.parametrize(
    ("filename", "active_link", "heading"),
    [
        ("orient.html", '<a class="active" href="/orient.html">Orient</a>', "One-page session orientation snapshot"),
    ],
)
def test_playground_page_uses_shared_parchment_monitor_design(filename, active_link, heading):
    html = (ROOT / "dashboards" / filename).read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="/monitor.css">' in html
    assert 'class="monitor-nav"' in html
    assert 'aria-label="Monitor sections"' in html
    assert active_link in html
    assert heading in html
    assert ":root" not in html
    assert "!important" not in html
    assert "#0d1117" not in html


@pytest.mark.parametrize("filename", ["channels.html", "comms.html"])
def test_retired_comms_pages_redirect_to_fleet(filename: str) -> None:
    html = (DASHBOARDS / filename).read_text(encoding="utf-8")
    assert 'content="0; url=/fleet.html"' in html
    assert 'href="/fleet.html"' in html


def test_channels_page_is_a_read_only_observer() -> None:
    html = (DASHBOARDS / "channels.html").read_text(encoding="utf-8")
    assert "Agent Channels is retired" in html
    for prohibited in ("post-form", "post-btn", "replyTo", "/post", "method: 'POST'"):
        assert prohibited not in html


def test_orient_page_renders_active_discussions_widget():
    html = (DASHBOARDS / "orient.html").read_text(encoding="utf-8")
    assert "Active Discussions" in html
    assert "/api/discussions/active" in html
    assert "Promise.allSettled" in html
    assert "Discussion lookup unavailable" in html
    assert "renderDiscussions" in html
    assert "fleet.html?conversation=" in html
    assert "channels.html?channel=" not in html


def test_runtime_page_keeps_primary_monitor_nav():
    html = (DASHBOARDS / "runtime.html").read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="/monitor.css">' in html
    assert '<a class="active" href="/runtime.html">Runtime</a>' in html
    for href in [
        "/orient.html",
        "/fleet.html",
        "/artifacts/",
        "/runtime.html",
    ]:
        assert f'href="{href}"' in html


def test_runtime_page_renders_read_only_acpx_shadow_transport_overview():
    html = (DASHBOARDS / "runtime.html").read_text(encoding="utf-8")

    assert "/api/runtime/acpx?days=7" in html
    assert "transport.default_mode" in html
    assert "seat.evidence?.total" in html
    assert "seat.evidence_state" in html
    assert "snapshot.comparison_evidence" in html
    assert "comparison.classification_parity" in html
    assert "Duplicates suppressed" in html
    assert "Busy refusals" in html
    assert "safeWhenTrue" in html
    assert "explicit_pilot_only: 'Explicit pilot only'" in html
    assert "Object.hasOwn(safeWhenTrue, key) && value === true" in html
    assert "aggregate_evidence" not in html
    assert "snapshot.shadow_calls" not in html
    assert "transport.default ??" not in html
    assert "ACPX Shadow Transport" in html
    assert "Native runtime authoritative" in html
    assert "ACPX evidence is observational only." in html
    assert "No shadow calls or comparisons in window" in html
    assert "ACPX pin" in html
    assert "No dispatch authority" in html
    assert 'class="acpx-rail"' in html
    assert "@media (max-width: 820px)" in html
    assert 'aria-labelledby="acpx-heading"' in html


def test_runtime_page_acpx_panel_has_no_mutating_transport_controls():
    html = (DASHBOARDS / "runtime.html").read_text(encoding="utf-8")
    acpx_panel = html[html.index('id="acpx-heading"') : html.index('function renderAgents')]

    for prohibited in ["<form", "acpx-send", "acpx-post", "acpx-chat", "acpx-session", "acpx-toggle", "acpx-retry", "acpx-cancel"]:
        assert prohibited not in acpx_panel


def test_runtime_page_renders_recent_body_free_acp_observability_without_controls():
    html = (DASHBOARDS / "runtime.html").read_text(encoding="utf-8")
    acp_panel = html[html.index('id="acp-heading"') : html.index('id="acpx-heading"')]

    assert "ACP Conversations" in acp_panel
    assert "Read-only, body-free event history" in acp_panel
    assert 'href="/acp.html"' in acp_panel
    assert "Open ACP conversations" in acp_panel
    assert "/api/runtime/acp/conversations" not in html

    for prohibited in [
        "<form",
        "acp-send",
        "acp-post",
        "acp-session",
        "acp-toggle",
        "acp-retry",
        "acp-cancel",
        "acp-route",
        "acp-review",
        "acp-config",
    ]:
        assert prohibited not in acp_panel


def test_acp_page_is_a_read_only_master_detail_conversation_reader():
    html = (DASHBOARDS / "acp.html").read_text(encoding="utf-8")

    assert '<link rel="stylesheet" href="/monitor.css">' in html
    assert '<a class="active" href="/acp.html">Conversations</a>' in html
    assert "/api/runtime/acp/conversations?limit=50" in html
    assert "/api/runtime/acp/conversations/" in html
    assert "const TRANSCRIPT_SUFFIX = '/transcript'" in html
    assert "Local-only transcript access." in html
    assert "Round-based conversation view" in html
    assert "Operational event rail" in html
    assert "make('details', 'event-rail')" in html
    assert "function groupTranscript(messages)" in html
    assert "Shared prompt" in html
    assert "Participant responses" in html
    assert "Other protocol messages" in html
    assert "Final synthesis" in html
    assert "No participant response message was recorded for this round." in html
    assert "No final synthesis message was recorded." in html
    assert "Raw protocol messages" in html
    assert "make('details', 'protocol-log')" in html
    assert "text(value).toLowerCase() === 'root' ? 'Coordinator'" in html
    assert "copy.textContent = body" in html
    assert "transcript.setAttribute('aria-live', 'polite')" not in html
    assert 'id="conversation-load-status" role="status" aria-live="polite"' in html
    assert "function announceConversationStatus(message)" in html
    assert "transcriptState(message)" in html
    assert "announceConversationStatus(message)" in html
    assert "white-space: pre-wrap" in html
    assert "Transcript is local-only. Open this page at localhost on the API host." in html
    assert "Transcript is unavailable on this local Monitor instance." in html
    assert "This conversation has no transcript messages." in html
    assert "Transcript data was malformed and was not rendered." in html
    assert "Transcript could not be loaded." in html
    assert "new URLSearchParams(location.search).get('conversation')" in html
    assert "Recent conversations" in html
    assert "Event flow" in html
    assert "Message bodies are requested only from the loopback Monitor API." in html
    assert "conversation.updated_at" in html
    assert "event.outcome" in html
    assert "event.duration_ms" in html
    assert "event.token_count" in html
    assert "Conversation storage is unavailable." in html
    assert "Malformed conversation data" in html
    assert "No recent ACP conversations." in html
    assert "@media (max-width: 880px)" in html
    assert ".reader { order: 1; }.ledger { order: 2; }" in html
    assert ":focus-visible" in html
    assert "prefers-reduced-motion" in html
    for href in PRIMARY_NAV_HREFS:
        assert f'href="{href}"' in html

    for prohibited in [
        "<form",
        "acp-send",
        "acp-post",
        "acp-start",
        "acp-session",
        "acp-toggle",
        "acp-retry",
        "acp-cancel",
        "acp-route",
        "acp-review",
        "acp-config",
        "fetch(url, { method:",
        "localStorage",
        "sessionStorage",
        "navigator.clipboard",
    ]:
        assert prohibited not in html


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
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
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


def test_routing_page_uses_live_monitor_sources():
    html = (DASHBOARDS / "routing.html").read_text(encoding="utf-8")
    assert "Static snapshot" not in html
    assert "refreshed manually" not in html
    assert "/api/state/routing-budget" in html
    assert "/api/runtime/agents" in html
    assert "/api/runtime/usage?days=7" in html
    assert "/api/delegate/tasks?limit=100" in html
    assert "Live routing budget" in html


def test_shared_monitor_css_targets_unified_nav_classes():
    css = (DASHBOARDS / "monitor.css").read_text(encoding="utf-8")
    assert ".topbar .nav" not in css
    assert ".topbar .monitor-nav" in css
    assert ".top-bar .monitor-nav" in css


def test_comms_page_keeps_secondary_dashboard_links():
    html = (DASHBOARDS / "comms.html").read_text(encoding="utf-8")
    assert 'href="/fleet.html"' in html


def test_progress_page_surfaces_freshness_and_dossiers():
    html = (DASHBOARDS / "progress.html").read_text(encoding="utf-8")
    assert "freshness-banner" in html
    assert "/api/state/summary?fresh=true" in html
    assert "/api/state/pipeline-versions?fresh=true" in html
    assert "dossier_done" in html
    assert "published_mdx" in html
    assert "audit_stale" in html
    assert "nextAction" in html
    assert "Research gap" in html
    assert "Build content" in html
    index_html = (DASHBOARDS / "index.html").read_text(encoding="utf-8")
    assert "t.dossier_done ?? 0" in index_html


def test_monitor_dashboards_hide_legacy_pipeline_version_labels():
    dashboard_text = {
        path.name: path.read_text(encoding="utf-8")
        for path in [
            DASHBOARDS / "index.html",
            DASHBOARDS / "progress.html",
            DASHBOARDS / "track-health.html",
            DASHBOARDS / "curriculum-dashboard.html",
            DASHBOARDS / "comms.html",
            DASHBOARDS / "delegate.html",
            DASHBOARDS / "orient.html",
            DASHBOARDS / "cost.html",
        ]
    }
    stale_strings = [
        "V6 Pipeline",
        " v6",
        " v5",
        "v5-${",
        "modules on v6",
        "manual refresh only",
        "dispatch-usage snapshot",
        "Legacy gaps",
        "Pipeline state across all tracks",
        "Waiting for manual refresh",
        "<th>Ver</th>",
    ]

    for page, html in dashboard_text.items():
        for stale_string in stale_strings:
            assert stale_string not in html, f"{page} exposes stale Monitor UI copy: {stale_string!r}"

    assert "Current Builds" in dashboard_text["index.html"]
    assert "Rebuild Backlog" in dashboard_text["progress.html"]
    assert "Build State" in dashboard_text["track-health.html"]
    assert "<th>Build</th>" in dashboard_text["curriculum-dashboard.html"]


def test_track_health_uses_live_track_inventory():
    html = (DASHBOARDS / "track-health.html").read_text(encoding="utf-8")
    assert "const TRACKS =" not in html
    assert "/api/state/summary?fresh=true" in html
    assert "orderedTrackIds" in html
    assert "module_source !== 'plans-fallback'" in html


def test_operational_dashboards_hide_plan_fallback_tracks():
    dashboard_text = {
        path.name: path.read_text(encoding="utf-8")
        for path in [
            DASHBOARDS / "index.html",
            DASHBOARDS / "progress.html",
            DASHBOARDS / "track-health.html",
            DASHBOARDS / "curriculum-dashboard.html",
            DASHBOARDS / "wiki.html",
        ]
    }

    for page, html in dashboard_text.items():
        assert "plans-fallback" in html, f"{page} must filter fallback-only plan tracks"

    assert "operationalTrackIdSetFromSummary" in dashboard_text["index.html"]
    assert "operationalTrackEntries" in dashboard_text["progress.html"]
    assert "operationalTracks" in dashboard_text["curriculum-dashboard.html"]
    assert "/api/state/summary?fresh=true" in dashboard_text["wiki.html"]


def test_operational_track_filters_treat_empty_sets_as_valid():
    index_html = (DASHBOARDS / "index.html").read_text(encoding="utf-8")
    progress_html = (DASHBOARDS / "progress.html").read_text(encoding="utf-8")
    wiki_html = (DASHBOARDS / "wiki.html").read_text(encoding="utf-8")

    assert "if (summaryIds) return summaryIds.has(track.id)" in index_html
    assert "dashboardTracks.length ? sumDashboardTotals" not in index_html
    assert "trackIds?.size && pv?.per_track" not in index_html
    assert "trackIds?.size && pv?.per_track" not in progress_html
    assert "if (operationalTrackIds.size)" not in wiki_html
    assert "let operationalTrackIds = null" in wiki_html


def test_comms_page_is_read_only_legacy_ops_without_duplicate_build_activity():
    html = (DASHBOARDS / "comms.html").read_text(encoding="utf-8")
    assert "Broker Ops is retired" in html
    for prohibited in (
        "Live Activity",
        "/api/build/events/active",
        "/api/build/events/recent",
        "compose-panel",
        "sendMessage",
        "/api/comms/send",
        "/api/comms/acknowledge",
        "method: 'POST'",
    ):
        assert prohibited not in html


def test_artifacts_page_uses_metadata_endpoint_and_filters():
    html = (DASHBOARDS / "artifacts.html").read_text(encoding="utf-8")
    assert "/api/artifacts/html" in html
    assert "class-filter" in html
    assert "status-filter" in html
    assert "author-filter" in html
    assert "date-filter" in html
    assert "artifact-card" in html


def test_artifacts_page_preserves_secondary_dashboard_links():
    html = (DASHBOARDS / "artifacts.html").read_text(encoding="utf-8")
    assert 'href="/"' in html
    for href in [
        "/admin.html",
        "/fleet.html",
        "/audit-dashboard.html",
        "/build-events.html",
        "/consultation.html",
        "/cost.html",
        "/curriculum-dashboard.html",
        "/delegate.html",
        "/routing.html",
        "/image-explorer.html",
        "/orient.html",
        "/progress.html",
        "/quality.html",
        "/runtime.html",
        "/track-health.html",
        "/wiki.html",
    ]:
        assert f'href="{href}"' in html
        assert (DASHBOARDS / href.lstrip("/")).exists()


def test_all_playground_pages_use_single_monitor_shell():
    for path in sorted(DASHBOARDS.glob("*.html")):
        if path.name in {"channels.html", "comms.html"}:
            continue
        html = path.read_text(encoding="utf-8")
        assert '<link rel="stylesheet" href="/monitor.css">' in html, path.name
        assert 'class="monitor-nav"' in html, path.name
        required_hrefs = PRIMARY_NAV_HREFS
        if path.name in {"fleet.html", "index.html"}:
            required_hrefs = [
                href for href in PRIMARY_NAV_HREFS if href not in {"/channels.html", "/comms.html"}
            ] + ["/fleet.html"]
        for href in required_hrefs:
            assert f'href="{href}"' in html, path.name
        if "#0d1117" in html:
            assert html.rfind('<link rel="stylesheet" href="/monitor.css">') > html.rfind("</style>"), path.name


def test_operations_pages_keep_secondary_navigation():
    pages_to_hrefs = {
        "audit-dashboard.html": ["/track-health.html", "/docs"],
        "curriculum-dashboard.html": [
            "/audit-dashboard.html",
            "/progress.html",
            "/quality.html",
            "/track-health.html",
        ],
        "progress.html": ["/audit-dashboard.html", "/quality.html", "/track-health.html", "/docs"],
        "quality.html": ["/audit-dashboard.html", "/progress.html", "/track-health.html", "/docs"],
        "track-health.html": [
            "/progress.html",
            "/audit-dashboard.html",
            "/quality.html",
            "/curriculum-dashboard.html",
            "/docs",
        ],
    }
    for page, hrefs in pages_to_hrefs.items():
        html = (DASHBOARDS / page).read_text(encoding="utf-8")
        assert 'class="ops-nav"' in html, page
        for href in hrefs:
            assert f'href="{href}"' in html, page
