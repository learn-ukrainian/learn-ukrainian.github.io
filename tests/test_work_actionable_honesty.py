"""Static + behavioral contracts for #7084 Work dashboard actionable view honesty.

Ensures the default view=actionable explains filtered-out non-actionable items
(such as ON_TRACK + OPEN_GITHUB issues) and provides a link to view=all without
modifying the #6850 isActionable deny-list semantics.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "dashboards" / "work.html"


def test_actionable_honesty_banner_and_controls_present_in_work_html():
    """#7084: Actionable default must include honesty banner, copy, and link to All."""
    html = WORK.read_text(encoding="utf-8")
    assert 'id="actionable-banner"' in html
    assert 'class="actionable-banner' in html or "class='actionable-banner" in html
    assert ".actionable-banner" in html
    assert "renderActionableBanner" in html
    assert "allViewUrl" in html
    assert "filtered out" in html
    assert "non-actionable" in html
    assert "Switch to All" in html
    assert "actionable-view-all-link" in html
    assert "filteredCount" in html
    assert "totalMatching" in html


def test_actionable_view_behavioral_js_filtering_and_counts():
    """#7084: Evaluate applyLocalFilters and banner generation in Node against mixed datasets."""
    if shutil.which("node") is None:
        pytest.skip("node required for JS behavioral check")

    script = """
    const fs = require('fs');
    const html = fs.readFileSync(__HTML_PATH__, 'utf8');

    // Extract constants and functions
    const codeStart = html.indexOf('const NON_ACTIONABLE_ACTION_CODES');
    const codeEnd = html.indexOf('function railClasses(');
    if (codeStart < 0 || codeEnd <= codeStart) {
      throw new Error('Required JS functions not found in work.html');
    }
    eval(html.slice(codeStart, codeEnd));

    const sampleProjection = {
      schema_version: 'work-projection.v1',
      cache_age_s: 10,
      sources: [{ source_id: 'public-monitor', status: 'ok' }],
      items: [
        {
          work_id: 'wp1:public-monitor:repo:pr:1',
          resource_kind: 'pr',
          remote_id: '1',
          health: 'AT_RISK',
          safe_next_action: { code: 'FIX_CI' },
        },
        {
          work_id: 'wp1:public-monitor:repo:issue:7073',
          resource_kind: 'issue',
          remote_id: '7073',
          health: 'ON_TRACK',
          safe_next_action: { code: 'OPEN_GITHUB' },
        },
        {
          work_id: 'wp1:public-monitor:repo:issue:7074',
          resource_kind: 'issue',
          remote_id: '7074',
          health: 'ON_TRACK',
          safe_next_action: { code: 'OPEN_GITHUB' },
        },
        {
          work_id: 'wp1:public-monitor:repo:task:100',
          resource_kind: 'task',
          remote_id: '100',
          health: 'UNKNOWN',
          safe_next_action: { code: 'INSPECT_UNKNOWN' },
        },
      ],
      attention: [
        { work_id: 'wp1:public-monitor:repo:pr:1', health: 'AT_RISK' },
        { work_id: 'wp1:public-monitor:repo:task:100', health: 'UNKNOWN' },
        { work_id: 'wp1:public-monitor:repo:issue:7073', health: 'ON_TRACK' },
        { work_id: 'wp1:public-monitor:repo:issue:7074', health: 'ON_TRACK' },
      ],
    };

    // Scenario 1: default view=actionable
    const actResult = applyLocalFilters(sampleProjection, { view: 'actionable' });

    // Scenario 2: view=all
    const allResult = applyLocalFilters(sampleProjection, { view: 'all' });

    // Scenario 3: all items non-actionable
    const nonActProjection = {
      items: [
        { work_id: 'wp1:a', health: 'ON_TRACK', safe_next_action: { code: 'OPEN_GITHUB' } },
        { work_id: 'wp1:b', health: 'ON_TRACK', safe_next_action: { code: 'OPEN_GITHUB' } },
      ],
      attention: [
        { work_id: 'wp1:a', health: 'ON_TRACK' },
        { work_id: 'wp1:b', health: 'ON_TRACK' },
      ],
    };
    const emptyActResult = applyLocalFilters(nonActProjection, { view: 'actionable' });

    // Scenario 4: truly empty projection
    const emptyProjection = { items: [], attention: [] };
    const emptyResult = applyLocalFilters(emptyProjection, { view: 'actionable' });

    const out = {
      actItemsCount: actResult.items.length,
      actFilteredCount: actResult.filteredCount,
      actTotalMatching: actResult.totalMatching,
      actItemIds: actResult.items.map(i => i.work_id),
      allItemsCount: allResult.items.length,
      allFilteredCount: allResult.filteredCount,
      allTotalMatching: allResult.totalMatching,
      emptyActItemsCount: emptyActResult.items.length,
      emptyActFilteredCount: emptyActResult.filteredCount,
      emptyActTotalMatching: emptyActResult.totalMatching,
      trulyEmptyFilteredCount: emptyResult.filteredCount,
      trulyEmptyTotalMatching: emptyResult.totalMatching,
    };
    console.log(JSON.stringify(out));
    """.replace("__HTML_PATH__", json.dumps(str(WORK)))
    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    out = json.loads(result.stdout)

    # In default actionable view: 1 actionable item, 3 non-actionable filtered out, 4 total
    assert out["actItemsCount"] == 1
    assert out["actFilteredCount"] == 3
    assert out["actTotalMatching"] == 4
    assert out["actItemIds"] == ["wp1:public-monitor:repo:pr:1"]

    # In all view: 4 items shown, 0 filtered out, 4 total
    assert out["allItemsCount"] == 4
    assert out["allFilteredCount"] == 0
    assert out["allTotalMatching"] == 4

    # When all items are non-actionable: 0 items shown, 2 filtered out, 2 total
    assert out["emptyActItemsCount"] == 0
    assert out["emptyActFilteredCount"] == 2
    assert out["emptyActTotalMatching"] == 2

    # When projection is empty: 0 items shown, 0 filtered out, 0 total
    assert out["trulyEmptyFilteredCount"] == 0
    assert out["trulyEmptyTotalMatching"] == 0


def test_actionable_banner_and_empty_state_dom_behavior():
    """#7084: Test renderActionableBanner and empty list state formatting in Node."""
    if shutil.which("node") is None:
        pytest.skip("node required for JS DOM check")

    script = """
    const fs = require('fs');
    const html = fs.readFileSync(__HTML_PATH__, 'utf8');

    // Mock minimal DOM and state before eval
    const bannerEl = {
      classList: {
        classes: new Set(['hidden']),
        add(c) { this.classes.add(c); },
        remove(c) { this.classes.delete(c); },
        contains(c) { return this.classes.has(c); },
      },
      innerHTML: '',
      querySelector(sel) { return null; },
    };

    const listEl = {
      innerHTML: '',
      removeAttribute(attr) {},
      querySelectorAll(sel) { return []; },
      querySelector(sel) { return null; },
    };

    const mockElements = {
      'actionable-banner': bannerEl,
      'attention-list': listEl,
      'filter-view': { value: 'actionable' },
      'filter-health': { value: '' },
      'filter-kind': { value: '' },
      'filter-lifecycle': { value: '' },
      'filter-orphan': { value: '' },
      'filter-source': { value: '' },
      'filter-repo': { value: '' },
    };

    global.document = {
      getElementById(id) {
        return mockElements[id] || { classList: { add() {}, remove() {}, contains() { return false; } }, textContent: '' };
      },
    };

    global.window = {
      location: { pathname: '/work.html', search: '' },
      history: { replaceState() {} },
    };

    // Extract constants and functions up to event listeners
    const codeStart = html.indexOf('const ALLOWED_FILTER_KEYS');
    const codeEnd = html.indexOf("document.getElementById('btn-refresh')");
    if (codeStart < 0 || codeEnd <= codeStart) {
      throw new Error('Required JS functions not found in work.html');
    }

    const testSnippet = `
      state.currentView = 'actionable';
      state.filteredCount = 583;
      state.totalMatching = 595;
      state.attention = [];
      state.merged = {};
      state.itemsById = new Map();

      renderActionableBanner();
      const bannerVisible = !bannerEl.classList.contains('hidden');
      const bannerHtml = bannerEl.innerHTML;

      renderList();
      const listEmptyHtml = listEl.innerHTML;

      state.currentView = 'all';
      state.filteredCount = 0;
      renderActionableBanner();
      const bannerHiddenOnAll = bannerEl.classList.contains('hidden');

      console.log(JSON.stringify({
        bannerVisible,
        bannerHtml,
        listEmptyHtml,
        bannerHiddenOnAll,
      }));
    `;
    eval(html.slice(codeStart, codeEnd) + '\\n' + testSnippet);
    """.replace("__HTML_PATH__", json.dumps(str(WORK)))
    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    out = json.loads(result.stdout)

    assert out["bannerVisible"] is True
    assert "583" in out["bannerHtml"]
    assert "Switch to All (595)" in out["bannerHtml"]
    assert "OPEN_GITHUB" in out["bannerHtml"] or "non-actionable" in out["bannerHtml"]
    assert "actionable-view-all-link" in out["bannerHtml"]

    assert "No actionable items" in out["listEmptyHtml"]
    assert "583" in out["listEmptyHtml"]
    assert "Switch to All" in out["listEmptyHtml"]

    assert out["bannerHiddenOnAll"] is True


def test_server_ssot_deny_list_preserves_open_github():
    """#6850 deny-list still includes OPEN_GITHUB and maintains expected truth table."""
    from scripts.work.attention import NON_ACTIONABLE_ACTION_CODES, is_actionable

    assert "OPEN_GITHUB" in NON_ACTIONABLE_ACTION_CODES
    assert "INSPECT_UNKNOWN" in NON_ACTIONABLE_ACTION_CODES
    assert "NONE" in NON_ACTIONABLE_ACTION_CODES

    # ON_TRACK + OPEN_GITHUB remains non-actionable (must not be pick-list work)
    assert not is_actionable({"health": "ON_TRACK", "safe_next_action": {"code": "OPEN_GITHUB"}})
    # UNKNOWN + OPEN_GITHUB is non-actionable
    assert not is_actionable({"health": "UNKNOWN", "safe_next_action": {"code": "OPEN_GITHUB"}})
    # AT_RISK or OFF_TRACK demands attention regardless of action code
    assert is_actionable({"health": "AT_RISK", "safe_next_action": {"code": "OPEN_GITHUB"}})
    assert is_actionable({"health": "OFF_TRACK", "safe_next_action": {"code": "OPEN_GITHUB"}})
    assert is_actionable({"health": "OFF_TRACK", "safe_next_action": {"code": "NONE"}})
