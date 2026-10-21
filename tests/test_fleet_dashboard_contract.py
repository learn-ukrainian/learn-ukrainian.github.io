"""Dashboard and route-registration contract for the unified fleet observer."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_PROJECTS_RENDER_JS = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('dashboards/fleet.html', 'utf8');
const slice = (start, end) => html.slice(html.indexOf(start), html.indexOf(end));
const nodes = {};
const context = vm.createContext({
  document: {getElementById(id) { return nodes[id] ||= {innerHTML: ''}; }},
});
vm.runInContext(
  "function escapeHtml(v) { return String(v ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;'); }"
  + slice('function short(', 'function formatTime(')
  + slice('function pill(', 'function allowlistedSafeUrl(')
  + slice('function renderProjects(', 'function renderWorkers('),
  context,
);
const sha = 'b'.repeat(40);
context.renderProjects({hosts: {'host-teacher': {
  host_id: 'host-teacher', freshness: 'fresh', age_s: 0,
  primary: {head_sha: sha, origin_main_sha: sha, dirty_count: 0}, attention: [],
  services: [
    {name: 'api', state: 'running', repo: 'learn-ukrainian', serving_mode: 'unknown',
     serving_sha: null, checkout_sha: null, unresolved_reason: 'cwd_not_git_repo', drift: 'unknown'},
    {name: 'sources', state: 'running', repo: 'learn-ukrainian', serving_mode: 'checkout',
     serving_sha: null, checkout_sha: sha, unresolved_reason: null, drift: false},
  ],
}}});
process.stdout.write(nodes['projects-content'].innerHTML);
"""


def test_fleet_projects_render_unresolved_serving_mode_without_error() -> None:
    """#8591: an unknown serving_mode renders as unresolved, never as release/error."""
    result = subprocess.run(
        ["node", "-e", _PROJECTS_RENDER_JS],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    rows = result.stdout.split("<tr>")
    api_row = next(row for row in rows if "<td>api</td>" in row)
    assert '<span class="pill unresolved">unresolved</span>' in api_row
    assert "cwd not git repo" in api_row
    assert "release" not in api_row
    assert "failed" not in api_row
    sources_row = next(row for row in rows if "<td>sources</td>" in row)
    assert '<span class="pill checkout">checkout</span>' in sources_row
