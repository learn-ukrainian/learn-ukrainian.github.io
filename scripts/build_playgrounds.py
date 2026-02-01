#!/usr/bin/env python3
"""Build playground HTML files with embedded real data."""

import json
from pathlib import Path

PLAYGROUNDS_DIR = Path(__file__).parent.parent / "playgrounds"
DATA_FILE = PLAYGROUNDS_DIR / "data" / "status.json"


def build_status_dashboard():
    """Build the module status dashboard with real data."""

    # Load real data
    with open(DATA_FILE) as f:
        data = json.load(f)

    summary = data["summary"]
    levels_data = data["levels"]

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Module Status Dashboard - Real Data</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      min-height: 100vh;
      padding: 24px;
    }}

    .back-link {{
      display: inline-block;
      color: #3b82f6;
      text-decoration: none;
      font-size: 13px;
      margin-bottom: 20px;
    }}

    .back-link:hover {{ text-decoration: underline; }}

    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
    }}

    .header h1 {{
      font-size: 24px;
      font-weight: 600;
    }}

    .header-stats {{
      display: flex;
      gap: 24px;
    }}

    .stat {{
      text-align: center;
    }}

    .stat-value {{
      font-size: 28px;
      font-weight: 700;
      color: #3b82f6;
    }}

    .stat-value.pass {{ color: #10b981; }}
    .stat-value.fail {{ color: #ef4444; }}

    .stat-label {{
      font-size: 11px;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .filters {{
      display: flex;
      gap: 12px;
      margin-bottom: 24px;
      flex-wrap: wrap;
    }}

    .filter-btn {{
      padding: 8px 16px;
      font-size: 13px;
      background: #1e293b;
      border: 1px solid #334155;
      color: #e2e8f0;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.15s;
    }}

    .filter-btn:hover {{ background: #334155; }}
    .filter-btn.active {{ background: #3b82f6; border-color: #60a5fa; }}

    .status-filter {{
      margin-left: auto;
      display: flex;
      gap: 8px;
    }}

    .status-btn {{
      padding: 6px 12px;
      font-size: 12px;
      border-radius: 6px;
      border: none;
      cursor: pointer;
      transition: all 0.15s;
    }}

    .status-btn.pass {{ background: #166534; color: #bbf7d0; }}
    .status-btn.fail {{ background: #991b1b; color: #fecaca; }}
    .status-btn.pending {{ background: #854d0e; color: #fef08a; }}
    .status-btn.all {{ background: #475569; color: #e2e8f0; }}
    .status-btn.active {{ box-shadow: 0 0 0 2px #e2e8f0; }}

    .dashboard {{
      display: grid;
      grid-template-columns: 1fr 380px;
      gap: 24px;
    }}

    .levels-grid {{
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .level-card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 12px;
      overflow: hidden;
    }}

    .level-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      background: #334155;
      cursor: pointer;
    }}

    .level-header:hover {{ background: #3f4f66; }}

    .level-name {{
      font-size: 16px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .level-badge {{
      font-size: 11px;
      padding: 3px 8px;
      border-radius: 4px;
      background: #475569;
    }}

    .level-progress {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .progress-bar {{
      width: 120px;
      height: 8px;
      background: #1e293b;
      border-radius: 4px;
      overflow: hidden;
    }}

    .progress-fill {{
      height: 100%;
      background: linear-gradient(90deg, #10b981, #34d399);
      transition: width 0.3s;
    }}

    .progress-text {{
      font-size: 13px;
      color: #94a3b8;
      min-width: 50px;
    }}

    .modules-grid {{
      display: none;
      padding: 16px;
      gap: 6px;
      flex-wrap: wrap;
      background: #0f172a;
    }}

    .level-card.expanded .modules-grid {{
      display: flex;
    }}

    .module-cell {{
      width: 28px;
      height: 28px;
      border-radius: 4px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      font-weight: 600;
      transition: all 0.15s;
      position: relative;
    }}

    .module-cell:hover {{
      transform: scale(1.2);
      z-index: 10;
    }}

    .module-cell.pass {{ background: #166534; color: #bbf7d0; }}
    .module-cell.fail {{ background: #991b1b; color: #fecaca; }}
    .module-cell.pending {{ background: #854d0e; color: #fef08a; }}
    .module-cell.warn {{ background: #854d0e; color: #fef08a; }}
    .module-cell.selected {{ box-shadow: 0 0 0 2px #3b82f6; }}

    .detail-panel {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 20px;
      position: sticky;
      top: 24px;
      max-height: calc(100vh - 48px);
      overflow-y: auto;
    }}

    .detail-empty {{
      text-align: center;
      color: #64748b;
      padding: 40px 20px;
    }}

    .detail-header {{
      margin-bottom: 20px;
    }}

    .detail-title {{
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 4px;
    }}

    .detail-subtitle {{
      font-size: 12px;
      color: #64748b;
      font-family: ui-monospace, monospace;
    }}

    .detail-status {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      margin-top: 8px;
    }}

    .detail-status.pass {{ background: #166534; color: #bbf7d0; }}
    .detail-status.fail {{ background: #991b1b; color: #fecaca; }}
    .detail-status.pending {{ background: #854d0e; color: #fef08a; }}

    .detail-section {{
      margin-bottom: 20px;
    }}

    .detail-section h4 {{
      font-size: 11px;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 10px;
    }}

    .metrics-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }}

    .metric {{
      background: #0f172a;
      padding: 12px;
      border-radius: 8px;
    }}

    .metric-value {{
      font-size: 20px;
      font-weight: 700;
    }}

    .metric-label {{
      font-size: 11px;
      color: #64748b;
    }}

    .metric.pass .metric-value {{ color: #10b981; }}
    .metric.fail .metric-value {{ color: #ef4444; }}
    .metric.warn .metric-value {{ color: #f59e0b; }}

    .gates-list {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .gate-item {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 12px;
      background: #0f172a;
      border-radius: 6px;
    }}

    .gate-name {{
      font-size: 13px;
    }}

    .gate-status {{
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 600;
    }}

    .gate-status.pass {{ background: #166534; color: #bbf7d0; }}
    .gate-status.fail {{ background: #991b1b; color: #fecaca; }}
    .gate-status.warn {{ background: #854d0e; color: #fef08a; }}

    .violations-list {{
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .violation {{
      padding: 10px 12px;
      background: #450a0a;
      border-left: 3px solid #ef4444;
      border-radius: 0 6px 6px 0;
      font-size: 12px;
      color: #fecaca;
    }}

    .prompt-area {{
      margin-top: 24px;
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 16px 20px;
    }}

    .prompt-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }}

    .prompt-header h3 {{
      font-size: 12px;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .copy-btn {{
      padding: 6px 14px;
      font-size: 12px;
      background: #3b82f6;
      border: none;
      color: white;
      border-radius: 6px;
      cursor: pointer;
    }}

    .copy-btn:hover {{ background: #2563eb; }}
    .copy-btn.copied {{ background: #10b981; }}

    .prompt-text {{
      font-family: ui-monospace, monospace;
      font-size: 13px;
      line-height: 1.5;
      color: #e2e8f0;
      background: #0f172a;
      padding: 12px 16px;
      border-radius: 6px;
      white-space: pre-wrap;
    }}
  </style>
</head>
<body>
  <a href="index.html" class="back-link">← Back to Playgrounds</a>

  <div class="header">
    <h1>📊 Module Status Dashboard</h1>
    <div class="header-stats">
      <div class="stat">
        <div class="stat-value" id="total-modules">{summary["total_modules"]}</div>
        <div class="stat-label">Total Modules</div>
      </div>
      <div class="stat">
        <div class="stat-value pass" id="pass-count">{summary["total_pass"]}</div>
        <div class="stat-label">Passing</div>
      </div>
      <div class="stat">
        <div class="stat-value fail" id="fail-count">{summary["total_fail"]}</div>
        <div class="stat-label">Failing</div>
      </div>
    </div>
  </div>

  <div class="filters">
    <button class="filter-btn active" data-level="all">All Levels</button>
    <button class="filter-btn" data-level="a1">A1</button>
    <button class="filter-btn" data-level="a2">A2</button>
    <button class="filter-btn" data-level="b1">B1</button>
    <button class="filter-btn" data-level="b2">B2</button>
    <button class="filter-btn" data-level="c1">C1</button>
    <button class="filter-btn" data-level="c2">C2</button>
    <button class="filter-btn" data-level="b2-hist">B2-HIST</button>
    <button class="filter-btn" data-level="c1-bio">C1-BIO</button>
    <button class="filter-btn" data-level="lit">LIT</button>

    <div class="status-filter">
      <button class="status-btn all active" data-status="all">All</button>
      <button class="status-btn pass" data-status="pass">Pass</button>
      <button class="status-btn fail" data-status="fail">Fail</button>
    </div>
  </div>

  <div class="dashboard">
    <div class="levels-grid" id="levels-grid"></div>

    <div class="detail-panel" id="detail-panel">
      <div class="detail-empty">
        <p>Click a module to view details</p>
      </div>
    </div>
  </div>

  <div class="prompt-area">
    <div class="prompt-header">
      <h3>Generated Prompt</h3>
      <button class="copy-btn" onclick="copyPrompt()">Copy to Clipboard</button>
    </div>
    <div class="prompt-text" id="prompt-output">Select modules or apply filters to generate a status summary prompt.</div>
  </div>

  <script>
    // ==================== REAL DATA ====================

    const LEVELS_DATA = {json.dumps(levels_data, indent=2)};

    // ==================== STATE ====================

    const state = {{
      selectedLevel: 'all',
      selectedStatus: 'all',
      selectedModule: null,
      expandedLevels: new Set()
    }};

    // ==================== RENDERING ====================

    function renderLevels() {{
      const container = document.getElementById('levels-grid');
      const levelIds = state.selectedLevel === 'all'
        ? Object.keys(LEVELS_DATA)
        : [state.selectedLevel];

      container.innerHTML = levelIds.filter(id => LEVELS_DATA[id]).map(levelId => {{
        const level = LEVELS_DATA[levelId];
        if (!level || level.total === 0) return '';

        const filtered = filterModules(level.modules);
        const passCount = filtered.filter(m => m.status === 'pass').length;
        const progress = Math.round((passCount / level.total) * 100);
        const isExpanded = state.expandedLevels.has(levelId);

        return `
          <div class="level-card ${{isExpanded ? 'expanded' : ''}}">
            <div class="level-header" onclick="toggleLevel('${{levelId}}')">
              <div class="level-name">
                ${{level.name}}
                <span class="level-badge">${{level.total}} modules</span>
              </div>
              <div class="level-progress">
                <div class="progress-bar">
                  <div class="progress-fill" style="width: ${{progress}}%"></div>
                </div>
                <span class="progress-text">${{progress}}%</span>
              </div>
            </div>
            <div class="modules-grid">
              ${{level.modules.map((m, idx) => {{
                const visible = state.selectedStatus === 'all' || m.status === state.selectedStatus;
                const selected = state.selectedModule?.id === m.id;
                return `
                  <div class="module-cell ${{m.status}} ${{selected ? 'selected' : ''}}"
                       style="opacity: ${{visible ? 1 : 0.2}}"
                       onclick="selectModule('${{levelId}}', ${{idx}})"
                       title="M${{m.num}}: ${{m.title}}">
                    ${{m.num}}
                  </div>
                `;
              }}).join('')}}
            </div>
          </div>
        `;
      }}).join('');

      updateStats();
    }}

    function filterModules(modules) {{
      if (state.selectedStatus === 'all') return modules;
      return modules.filter(m => m.status === state.selectedStatus);
    }}

    function renderDetail() {{
      const panel = document.getElementById('detail-panel');
      const m = state.selectedModule;

      if (!m) {{
        panel.innerHTML = '<div class="detail-empty"><p>Click a module to view details</p></div>';
        return;
      }}

      const wordPct = Math.round((m.wordCount / m.wordTarget) * 100);

      panel.innerHTML = `
        <div class="detail-header">
          <div class="detail-title">M${{m.num}}: ${{m.title}}</div>
          <div class="detail-subtitle">${{m.id}}</div>
          <span class="detail-status ${{m.status}}">${{m.status.toUpperCase()}}</span>
        </div>

        <div class="detail-section">
          <h4>Metrics</h4>
          <div class="metrics-grid">
            <div class="metric ${{wordPct >= 95 ? 'pass' : wordPct >= 80 ? 'warn' : 'fail'}}">
              <div class="metric-value">${{m.wordCount.toLocaleString()}}</div>
              <div class="metric-label">Words (target: ${{m.wordTarget.toLocaleString()}})</div>
            </div>
            <div class="metric ${{m.activityCount >= 8 ? 'pass' : 'warn'}}">
              <div class="metric-value">${{m.activityCount}}</div>
              <div class="metric-label">Activities</div>
            </div>
            <div class="metric ${{m.naturalness >= 7 ? 'pass' : m.naturalness >= 5 ? 'warn' : 'fail'}}">
              <div class="metric-value">${{m.naturalness || '—'}}</div>
              <div class="metric-label">Naturalness (≥7)</div>
            </div>
            <div class="metric">
              <div class="metric-value">${{wordPct}}%</div>
              <div class="metric-label">Word Target</div>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4>Audit Gates</h4>
          <div class="gates-list">
            ${{Object.entries(m.gates).map(([gate, status]) => `
              <div class="gate-item">
                <span class="gate-name">${{gate}}</span>
                <span class="gate-status ${{status}}">${{status.toUpperCase()}}</span>
              </div>
            `).join('')}}
          </div>
        </div>

        ${{m.violations && m.violations.length > 0 ? `
          <div class="detail-section">
            <h4>Violations</h4>
            <div class="violations-list">
              ${{m.violations.map(v => `<div class="violation">${{v}}</div>`).join('')}}
            </div>
          </div>
        ` : ''}}
      `;
    }}

    function updateStats() {{
      let total = 0, pass = 0, fail = 0;

      const levelIds = state.selectedLevel === 'all'
        ? Object.keys(LEVELS_DATA)
        : [state.selectedLevel];

      levelIds.forEach(levelId => {{
        const level = LEVELS_DATA[levelId];
        if (!level) return;
        const modules = filterModules(level.modules);
        total += modules.length;
        pass += modules.filter(m => m.status === 'pass').length;
        fail += modules.filter(m => m.status === 'fail').length;
      }});

      document.getElementById('total-modules').textContent = total;
      document.getElementById('pass-count').textContent = pass;
      document.getElementById('fail-count').textContent = fail;
    }}

    function updatePrompt() {{
      const output = document.getElementById('prompt-output');
      const m = state.selectedModule;

      let prompt = '';

      if (m) {{
        prompt = `Module Status Report: ${{m.id}}

Status: ${{m.status.toUpperCase()}}
Word Count: ${{m.wordCount.toLocaleString()}} / ${{m.wordTarget.toLocaleString()}} (${{Math.round((m.wordCount / m.wordTarget) * 100)}}%)
Activities: ${{m.activityCount}}
Naturalness: ${{m.naturalness || 'Not scored'}}

Gates:
${{Object.entries(m.gates).map(([g, s]) => \`- ${{g}}: ${{s}}\`).join('\\n')}}`;

        if (m.violations && m.violations.length > 0) {{
          prompt += `\\n\\nViolations:\\n${{m.violations.map(v => \`- ${{v}}\`).join('\\n')}}`;
        }}

        if (m.status === 'fail') {{
          prompt += `\\n\\nPlease fix this module by addressing the violations. Run audit_module.sh after fixes.`;
        }}
      }} else {{
        const levelIds = state.selectedLevel === 'all'
          ? Object.keys(LEVELS_DATA)
          : [state.selectedLevel];

        const stats = levelIds.map(levelId => {{
          const level = LEVELS_DATA[levelId];
          if (!level || level.total === 0) return null;
          return \`${{levelId.toUpperCase()}}: ${{level.pass_count}}/${{level.total}} passing (${{Math.round((level.pass_count / level.total) * 100)}}%)\`;
        }}).filter(Boolean);

        prompt = \`Curriculum Status Overview

${{stats.join('\\n')}}

Filter: ${{state.selectedStatus === 'all' ? 'All statuses' : state.selectedStatus.toUpperCase() + ' only'}}

Click a module cell to see detailed audit results.\`;
      }}

      output.textContent = prompt;
    }}

    function updateAll() {{
      renderLevels();
      renderDetail();
      updatePrompt();
    }}

    // ==================== INTERACTIONS ====================

    function toggleLevel(level) {{
      if (state.expandedLevels.has(level)) {{
        state.expandedLevels.delete(level);
      }} else {{
        state.expandedLevels.add(level);
      }}
      renderLevels();
    }}

    function selectModule(levelId, index) {{
      state.selectedModule = LEVELS_DATA[levelId].modules[index];
      updateAll();
    }}

    function copyPrompt() {{
      const text = document.getElementById('prompt-output').textContent;
      navigator.clipboard.writeText(text).then(() => {{
        const btn = document.querySelector('.copy-btn');
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(() => {{
          btn.textContent = 'Copy to Clipboard';
          btn.classList.remove('copied');
        }}, 2000);
      }});
    }}

    // ==================== EVENT LISTENERS ====================

    document.querySelectorAll('.filter-btn').forEach(btn => {{
      btn.onclick = () => {{
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.selectedLevel = btn.dataset.level;
        state.selectedModule = null;
        state.expandedLevels.clear();
        if (state.selectedLevel !== 'all') {{
          state.expandedLevels.add(state.selectedLevel);
        }}
        updateAll();
      }};
    }});

    document.querySelectorAll('.status-btn').forEach(btn => {{
      btn.onclick = () => {{
        document.querySelectorAll('.status-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.selectedStatus = btn.dataset.status;
        updateAll();
      }};
    }});

    // ==================== INIT ====================

    state.expandedLevels.add('a1');
    updateAll();
  </script>
</body>
</html>'''

    output_path = PLAYGROUNDS_DIR / "playground-module-status.html"
    with open(output_path, "w") as f:
        f.write(html)

    print(f"Built {output_path}")


def main():
    """Build all playgrounds."""
    print("Building playgrounds with real data...\n")
    build_status_dashboard()
    print("\nDone! Open playgrounds/index.html to see the landing page.")


if __name__ == "__main__":
    main()
