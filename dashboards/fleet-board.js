/* Read-only fleet board. Talks only to /api/fleet/v1. */
(function (root) {
  const REFRESH_MS = 30000;
  const STALE_MS = 120000;
  const STATES = ["working", "idle", "stuck", "dead", "paused", "off"];
  const STATE_ORDER = { dead: 0, stuck: 1, working: 2, idle: 3, paused: 4, off: 5 };
  const KIND_LABEL = {
    dead_driver: "Dead driver",
    stuck_driver: "Stuck driver",
    red_foundation: "Red foundation",
    unqueued_pr: "Green PR not queued",
    alert: "Alert",
    usage: "Usage near limit",
  };
  const STATUS_RANK = { ok: 0, stale: 1, unavailable: 2, not_configured: 3 };

  function esc(value) {
    return String(value ?? "").replace(/[&<>"]/g, (ch) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
    }[ch]));
  }

  function isFleetPath(path) {
    if (typeof path !== "string") return false;
    if (path.includes("://") || path.includes("\\") || path.includes("..")) return false;
    if (!path.startsWith("/api/fleet/v1")) return false;
    const rest = path.slice("/api/fleet/v1".length);
    if (rest === "/now" || rest === "/epics" || rest === "/agents") return true;
    const epic = /^\/epics\/([^/]+)$/.exec(rest);
    if (epic) return epic[1].length > 0 && !/%2f/i.test(epic[1]);
    const agent = /^\/agents\/([^/]+)$/.exec(rest);
    if (agent) return agent[1].length > 0 && !/%2f/i.test(agent[1]);
    return false;
  }

  function parseRoute(hash) {
    const fragment = hash || "#/home";
    const raw = fragment.charAt(0) === "#" ? fragment.slice(1) : fragment;
    const splitAt = raw.indexOf("?");
    const path = splitAt === -1 ? raw : raw.slice(0, splitAt);
    const query = splitAt === -1 ? "" : raw.slice(splitAt + 1);
    const parts = path.split("/").filter(Boolean);
    let epicId = "";
    if (parts[0] === "epic" && parts[1]) {
      try {
        epicId = decodeURIComponent(parts[1]);
      } catch (error) {
        epicId = parts[1];
      }
    }
    return {
      view: parts[0] || "home",
      parts,
      params: new URLSearchParams(query),
      epicId,
    };
  }

  function withParams(hash, updates) {
    const route = parseRoute(hash || "#/home");
    const params = new URLSearchParams(route.params);
    Object.keys(updates).forEach((key) => {
      const value = updates[key];
      if (value) params.set(key, value);
      else params.delete(key);
    });
    const path = route.parts.length ? route.parts.join("/") : "home";
    const query = params.toString();
    return "#/" + path + (query ? "?" + query : "");
  }

  function stateClass(state) {
    return STATES.indexOf(state) === -1 ? "off" : state;
  }

  function statePill(state) {
    const known = STATES.indexOf(state) !== -1;
    return `<span class="fb-state is-${stateClass(state)}">${esc(known ? state : "unknown")}</span>`;
  }

  function sinceLabel(value) {
    if (!value) return "unknown";
    const match = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}):\d{2}Z$/.exec(String(value));
    if (!match) return String(value);
    return match[2] + " UTC";
  }

  function taskText(task) {
    if (!task || (task.kind !== "pr" && task.kind !== "issue")) return "no current task";
    const label = task.kind === "pr" ? "PR" : "Issue";
    const number = Number.isInteger(task.number) ? " #" + task.number : "";
    const title = task.title ? " · " + task.title : "";
    return label + number + title;
  }

  function subtitle(epic) {
    const parts = [epic.epic || "no epic id"];
    if (epic.focus) parts.push(epic.focus);
    if (epic.parent) parts.push("parent " + epic.parent);
    parts.push(epic.layer == null ? "layer unknown" : "layer " + epic.layer);
    parts.push("intended " + (epic.intended || "unknown"));
    return parts.join(" · ");
  }

  function haystack(epic) {
    const driver = epic.driver || {};
    const task = epic.task || {};
    const workers = Array.isArray(epic.workers) ? epic.workers : [];
    const parts = [
      epic.epic, epic.title, epic.focus, epic.parent, epic.state, epic.state_reason,
      driver.cli, driver.model, driver.harness, driver.agent_id,
      task.kind, task.number, task.title,
    ];
    workers.forEach((worker) => {
      if (!worker) return;
      parts.push(worker.agent_id, worker.cli, worker.model, worker.state);
      if (typeof worker.task === "string") {
        parts.push(worker.task);
      } else if (worker.task && typeof worker.task === "object" && !Array.isArray(worker.task)) {
        parts.push(worker.task.kind, worker.task.number, worker.task.title);
      }
    });
    return parts.filter((part) => (typeof part === "string" && part !== "") ||
      (typeof part === "number" && Number.isFinite(part))).join(" ").toLowerCase();
  }

  function titleOf(epic) {
    return String((epic && (epic.title || epic.epic)) || "");
  }

  function compareEpics(a, b, sort) {
    if (sort === "name") return titleOf(a).localeCompare(titleOf(b));
    if (sort === "layer") {
      const layer = (a.layer ?? 99) - (b.layer ?? 99);
      return layer || titleOf(a).localeCompare(titleOf(b));
    }
    const rank = (STATE_ORDER[a.state] ?? 9) - (STATE_ORDER[b.state] ?? 9);
    return rank || titleOf(a).localeCompare(titleOf(b));
  }

  function filterEpics(epics, params) {
    const query = params instanceof URLSearchParams ? params : new URLSearchParams(params || "");
    const layer = query.get("layer") || "";
    const state = query.get("state") || "";
    const harness = query.get("harness") || "";
    const q = (query.get("q") || "").trim().toLowerCase();
    const sort = query.get("sort") || "attention";
    const rows = (Array.isArray(epics) ? epics : []).filter((epic) => {
      if (!epic) return false;
      if (layer && String(epic.layer ?? "") !== layer) return false;
      if (state && epic.state !== state) return false;
      const epicHarness = (epic.driver && epic.driver.harness) || "";
      if (harness && epicHarness !== harness) return false;
      if (q && haystack(epic).indexOf(q) === -1) return false;
      return true;
    });
    return rows.slice().sort((a, b) => compareEpics(a, b, sort));
  }

  function metricText(value, suffix) {
    if (typeof value !== "number" || !Number.isFinite(value)) return "?";
    const shown = Number.isInteger(value) ? String(value) : String(Math.round(value * 10) / 10);
    return suffix ? shown + suffix : shown;
  }

  function contextClass(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) return "";
    if (value >= 85) return "is-bad";
    if (value >= 70) return "is-warn";
    return "";
  }

  function idleClass(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) return "";
    return value >= 30 ? "is-bad" : "";
  }

  function stopsClass(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) return "";
    return value > 0 ? "is-warn" : "";
  }

  function healthOf(epic) {
    const health = epic && epic.health;
    if (!health || typeof health !== "object") return null;
    return health;
  }

  function tile(metric, label, value, cls) {
    const extra = cls ? " " + cls : "";
    return `<div class="fb-tile${extra}" data-metric="${metric}"><span>${label}</span><b>${esc(value)}</b></div>`;
  }

  function harnessTiles(health) {
    const row = health || {};
    return `<div class="fb-tiles">
      ${tile("context", "context", metricText(row.context_pct, "%"), contextClass(row.context_pct))}
      ${tile("compactions", "compactions", metricText(row.compactions, ""), "")}
      ${tile("stops", "stops / asks", metricText(row.stop_to_ask_count, ""), stopsClass(row.stop_to_ask_count))}
      ${tile("idle", "idle", metricText(row.idle_min, " m"), idleClass(row.idle_min))}
    </div>`;
  }

  function workerSummary(workers) {
    if (!Array.isArray(workers) || workers.length === 0) return "no workers";
    const bits = workers.map((worker) => {
      const model = (worker && worker.model) || "unknown model";
      const state = worker && STATES.indexOf(worker.state) !== -1 ? worker.state : "unknown";
      return model + " (" + state + ")";
    });
    const noun = workers.length === 1 ? "worker" : "workers";
    return workers.length + " " + noun + ": " + bits.join(", ");
  }

  function attentionHref(item) {
    const target = item && item.target;
    if (!target || typeof target.id !== "string" || !target.id) return "#/home";
    if (target.type === "epic") return "#/epic/" + encodeURIComponent(target.id);
    if (target.type === "pr") return "#/prs?pr=" + encodeURIComponent(target.id);
    return "#/home";
  }

  function kindLabel(kind) {
    return KIND_LABEL[kind] || "Needs attention";
  }

  function attentionItem(item) {
    const severity = item && item.severity === "bad" ? "bad" : "warn";
    const title = item && item.title ? item.title : "Needs attention";
    const summary = item && item.summary ? item.summary : "";
    return `<a class="fb-attn-item ${severity}" href="${esc(attentionHref(item))}">
      <div class="fb-k">${esc(kindLabel(item && item.kind))}</div>
      <div class="fb-t">${esc(title)}</div>
      <div class="fb-s">${esc(summary)}</div>
    </a>`;
  }

  function cardHtml(epic) {
    const state = stateClass(epic.state);
    const id = String(epic.epic || "");
    const href = "#/epic/" + encodeURIComponent(id);
    const driver = epic.driver;
    const driverLine = driver
      ? `<p class="fb-sub">driver: <b>${esc(driver.cli || "unknown cli")}</b> · ${esc(driver.model || "unknown model")}</p>`
      : `<p class="fb-sub">no driver</p>`;
    return `<a class="fb-card is-${state}" href="${esc(href)}">
      <div class="fb-card-top"><div><h3>${esc(epic.title || id || "Untitled")}</h3>
        <p class="fb-sub">${esc(subtitle(epic))}</p></div>${statePill(epic.state)}</div>
      <p class="fb-reason">${esc(epic.state_reason || "unknown reason")} <span class="fb-sub">since ${esc(sinceLabel(epic.since))}</span></p>
      ${driverLine}
      <div class="fb-task">${esc(taskText(epic.task))}</div>
      ${harnessTiles(healthOf(epic))}
      <p class="fb-workers">${esc(workerSummary(epic.workers))}</p>
    </a>`;
  }

  function selectOptions(values, current, allLabel) {
    const items = values.slice();
    if (current && items.indexOf(current) === -1) items.push(current);
    let html = `<option value="">${esc(allLabel)}</option>`;
    items.forEach((value) => {
      const selected = value === current ? " selected" : "";
      html += `<option value="${esc(value)}"${selected}>${esc(value)}</option>`;
    });
    return html;
  }

  function sortOptions(current) {
    const items = [["attention", "Sort: attention"], ["layer", "Sort: layer"], ["name", "Sort: name"]];
    return items.map(([value, label]) => {
      const selected = value === current ? " selected" : "";
      return `<option value="${value}"${selected}>${label}</option>`;
    }).join("");
  }

  function toolbar(epics, query) {
    const layers = [];
    const harnesses = [];
    epics.forEach((epic) => {
      if (epic.layer != null && layers.indexOf(String(epic.layer)) === -1) layers.push(String(epic.layer));
      const harness = epic.driver && epic.driver.harness;
      if (harness && harnesses.indexOf(harness) === -1) harnesses.push(harness);
    });
    layers.sort((a, b) => Number(a) - Number(b));
    harnesses.sort();
    const q = query.get("q") || "";
    return `<div class="fb-toolbar">
      <input id="fb-search" type="search" aria-label="Search epic, model, task, or PR" placeholder="Search epic, model, task, PR" value="${esc(q)}">
      <select data-filter="layer" aria-label="Layer">${selectOptions(layers, query.get("layer") || "", "All layers")}</select>
      <select data-filter="state" aria-label="State">${selectOptions(STATES, query.get("state") || "", "All states")}</select>
      <select data-filter="harness" aria-label="Harness">${selectOptions(harnesses, query.get("harness") || "", "All harnesses")}</select>
      <select data-filter="sort" aria-label="Sort">${sortOptions(query.get("sort") || "attention")}</select>
    </div>`;
  }

  function sourceStatus(sources, name) {
    let status = "";
    let best = -1;
    (sources || []).forEach((row) => {
      if (!row || row.name !== name) return;
      const score = STATUS_RANK[row.status];
      if (score == null || score <= best) return;
      best = score;
      status = row.status;
    });
    return status;
  }

  function sourceLabel(status) {
    if (status === "not_configured") return "not installed";
    if (status === "unavailable") return "unavailable";
    if (status === "stale") return "stale";
    if (status === "ok") return "ok";
    return "unknown";
  }

  function panelStatus(sources, name) {
    if (!name) return "later slice";
    const status = sourceStatus(sources, name);
    if (status === "not_configured") return "not installed";
    if (status === "unavailable") return "unavailable";
    if (status === "stale") return "stale";
    return "later slice";
  }

  function statusRows(sources, pairs) {
    return pairs.map(([label, name]) => {
      const value = panelStatus(sources, name);
      return `<div class="fb-place-row"><span>${esc(label)}</span><b>${esc(value)}</b></div>`;
    }).join("");
  }

  function panel(title, endpoint, body) {
    return `<section class="fb-panel fb-placeholder"><h3>${esc(title)}</h3>${body}<p class="fb-src">source: ${esc(endpoint)}</p></section>`;
  }

  function harnessCaption(sources) {
    if (panelStatus(sources, "harness_snapshot") !== "not installed") return "";
    return `<p class="fb-src">Harness health: not installed</p>`;
  }

  function sourcesOf(envelope) {
    const rows = envelope && envelope.sources;
    return Array.isArray(rows) ? rows : [];
  }

  function mergeSources() {
    const out = [];
    for (let i = 0; i < arguments.length; i += 1) {
      sourcesOf(arguments[i]).forEach((row) => out.push(row));
    }
    return out;
  }

  function notableSources(sources) {
    const byName = Object.create(null);
    (sources || []).forEach((row) => {
      if (!row || !row.name) return;
      const prev = byName[row.name];
      if (!prev || (STATUS_RANK[row.status] || 0) > (STATUS_RANK[prev.status] || 0)) byName[row.name] = row;
    });
    return Object.keys(byName).map((name) => byName[name]).filter((row) => row.status && row.status !== "ok");
  }

  function sourceList(sources) {
    const rows = notableSources(sources);
    if (!rows.length) return "";
    const items = rows.map((row) => {
      const name = String(row.name).replace(/_/g, " ");
      return `<li><span>${esc(name)}</span> <b>${esc(sourceLabel(row.status))}</b></li>`;
    });
    return `<ul class="fb-source-list">${items.join("")}</ul>`;
  }

  function staleState(sources, ageMs, refreshFailed) {
    const sourceStale = (sources || []).some((row) => row && row.status === "stale");
    const ageStale = typeof ageMs === "number" && ageMs > STALE_MS;
    const failed = !!refreshFailed;
    return { sourceStale, ageStale, refreshFailed: failed, stale: sourceStale || ageStale || failed };
  }

  function staleMessage(state) {
    const parts = [];
    if (state.ageStale) parts.push("The last successful refresh was over 2 minutes ago.");
    if (state.sourceStale) parts.push("A source is stale.");
    if (state.refreshFailed) parts.push("The last refresh failed; values below are from an earlier refresh.");
    if (!parts.length) return "";
    return parts.join(" ") + " Values below may be out of date.";
  }

  function staleBanner(state) {
    const hidden = state.stale ? "" : " hidden";
    return `<p id="fb-stale" class="fb-stale" role="status"${hidden}>${esc(staleMessage(state))}</p>`;
  }

  function homeModel(nowEnvelope, epicsEnvelope) {
    const nowData = (nowEnvelope && nowEnvelope.data) || {};
    const epicData = (epicsEnvelope && epicsEnvelope.data) || {};
    const fromEpics = Array.isArray(epicData.epics) ? epicData.epics : null;
    const fromNow = Array.isArray(nowData.epics) ? nowData.epics : [];
    return {
      attention: Array.isArray(nowData.attention) ? nowData.attention : [],
      epics: fromEpics || fromNow,
      sources: mergeSources(nowEnvelope, epicsEnvelope),
    };
  }

  function ageOption(options) {
    if (!options || !Object.prototype.hasOwnProperty.call(options, "ageMs")) return null;
    return options.ageMs;
  }

  function optionFlag(options, key) {
    return !!(options && options[key]);
  }

  function renderHome(model, params, options) {
    const query = params instanceof URLSearchParams ? params : new URLSearchParams(params || "");
    const epics = Array.isArray(model.epics) ? model.epics : [];
    const attention = Array.isArray(model.attention) ? model.attention : [];
    const sources = model.sources || [];
    const filtered = filterEpics(epics, query);
    const banner = staleBanner(staleState(sources, ageOption(options), optionFlag(options, "failed")));
    const cards = filtered.map(cardHtml).join("") || `<p class="fb-empty">No epics match these filters.</p>`;
    const attn = attention.map(attentionItem).join("") || `<p class="fb-empty">Nothing needs attention.</p>`;
    const roster = panel(
      "Roster",
      "/api/fleet/v1/roster",
      statusRows(sources, [["Roster", "roster_snapshot"]]),
    );
    const budget = panel(
      "Routing budget and pace",
      "/api/fleet/v1/budget",
      statusRows(sources, [["Budget", ""]]),
    );
    const ops = panel(
      "Ops",
      "/api/fleet/v1/alerts",
      statusRows(sources, [
        ["Alerts", "alerts"],
        ["Backups", "backups"],
        ["Downloads", "downloads"],
        ["Stats", "stats"],
        ["Links", "links"],
      ]),
    );
    return `${banner}
      <section>
        <h2>Needs attention <span class="fb-count">${attention.length} items</span></h2>
        <div class="fb-attn">${attn}</div>
        <p class="fb-src">source: /api/fleet/v1/now</p>
      </section>
      <section>
        <h2>Dependency layers</h2>
        ${roster}
      </section>
      <section>
        <h2>Epics and drivers <span class="fb-count">${filtered.length} of ${epics.length}</span></h2>
        ${toolbar(epics, query)}
        ${harnessCaption(sources)}
        <div class="fb-grid">${cards}</div>
        <p class="fb-src">source: /api/fleet/v1/now · /api/fleet/v1/epics</p>
      </section>
      <div class="fb-bottom">${budget}${ops}</div>
      ${sourceList(sources)}`;
  }

  function liveness(driver) {
    if (!driver || driver.pid_alive == null) return "liveness unknown";
    return driver.pid_alive ? "process alive" : "process is not alive";
  }

  function driverBlock(epic, sources) {
    const driver = epic.driver;
    const source = `<p class="fb-src">source: /api/fleet/v1/epics/${esc(epic.epic || "")} · /api/fleet/v1/agents</p>`;
    if (!driver) {
      return `<section class="fb-panel"><h3>Driver</h3><p class="fb-sub">No driver.</p>
        <h3 class="fb-subhead">Harness health</h3>${harnessTiles(null)}${harnessCaption(sources)}${source}</section>`;
    }
    return `<section class="fb-panel"><h3>Driver</h3>
      <dl class="fb-kv">
        <dt>CLI / harness</dt><dd>${esc(driver.cli || "unknown")} / ${esc(driver.harness || "unknown")}</dd>
        <dt>Model</dt><dd>${esc(driver.model || "unknown")}</dd>
        <dt>Liveness</dt><dd>${esc(liveness(driver))}</dd>
        <dt>Current task</dt><dd>${esc(taskText(epic.task))}</dd>
      </dl>
      <h3 class="fb-subhead">Harness health</h3>
      ${harnessTiles(healthOf(epic))}
      ${harnessCaption(sources)}
      ${source}
    </section>`;
  }

  function workersTable(workers) {
    const rows = Array.isArray(workers) ? workers : [];
    if (!rows.length) {
      return `<section class="fb-panel"><h3>Workers</h3><p class="fb-sub">No workers.</p>
        <p class="fb-src">source: /api/fleet/v1/agents</p></section>`;
    }
    const body = rows.map((worker) => `<tr>
      <td data-l="Agent"><button type="button" class="fb-link" data-agent="${esc(worker.agent_id || "")}">${esc(worker.agent_id || "unknown")}</button></td>
      <td data-l="Model">${esc(worker.model || "unknown")}</td>
      <td data-l="Task">${esc(worker.task || "none")}</td>
      <td data-l="State">${statePill(worker.state)}</td>
      <td data-l="Since">${esc(sinceLabel(worker.since || worker.last_seen))}</td>
    </tr>`).join("");
    return `<section class="fb-panel"><h3>Workers <span class="fb-sub">${rows.length}</span></h3>
      <table class="fb-table"><thead><tr><th>Agent</th><th>Model</th><th>Task</th><th>State</th><th>Since</th></tr></thead>
      <tbody>${body}</tbody></table>
      <p class="fb-src">source: /api/fleet/v1/agents</p></section>`;
  }

  function phaseActions() {
    return `<div class="fb-actions"><span class="fb-ph2">Phase 2</span>
      <button type="button" class="fb-btn" disabled>Pause epic</button>
      <button type="button" class="fb-btn" disabled>Nudge driver</button>
      <button type="button" class="fb-btn" disabled>Restart driver</button>
    </div>`;
  }

  function epicHeader(epic) {
    return `<p class="fb-crumbs"><a href="#/home">Home</a> <span aria-hidden="true">›</span> epic</p>
      <div class="fb-title"><h2>${esc(epic.title || epic.epic || "Epic")}</h2>${statePill(epic.state)}
        <p class="fb-sub">${esc(subtitle(epic))}</p></div>
      <p class="fb-reason">${esc(epic.state_reason || "unknown reason")} <span class="fb-sub">since ${esc(sinceLabel(epic.since))}</span></p>
      ${phaseActions()}`;
  }

  function agentsCurrent(epicEnvelope, agentsEnvelope, options) {
    if (optionFlag(options, "agentsFailed")) return false;
    const agentsAt = Date.parse(agentsEnvelope && agentsEnvelope.generated_at);
    if (Number.isNaN(agentsAt)) return false;
    const epicAt = Date.parse(epicEnvelope && epicEnvelope.generated_at);
    if (Number.isNaN(epicAt)) return true;
    return agentsAt >= epicAt;
  }

  function renderEpic(epicEnvelope, agentsEnvelope, options) {
    const sources = mergeSources(epicEnvelope, agentsEnvelope);
    const banner = staleBanner(staleState(sources, ageOption(options), optionFlag(options, "failed")));
    const epic = epicEnvelope && epicEnvelope.data;
    if (!epic || typeof epic !== "object") {
      return `${banner}<p class="fb-empty">This epic is not on the board.</p>${sourceList(sources)}`;
    }
    const agentsData = agentsEnvelope && agentsEnvelope.data;
    const agents = agentsData && Array.isArray(agentsData.agents) && agentsCurrent(epicEnvelope, agentsEnvelope, options)
      ? agentsData.agents
      : null;
    const workers = agents
      ? agents.filter((agent) => agent && agent.epic === epic.epic && agent.role === "worker")
      : (Array.isArray(epic.workers) ? epic.workers : []);
    const prs = panel(
      "PRs for this epic",
      "/api/fleet/v1/prs",
      statusRows(sources, [["Merge queue", "mq_state"]]),
    );
    const deps = panel(
      "Dependencies and restart",
      "/api/fleet/v1/roster",
      statusRows(sources, [["Roster", "roster_snapshot"]]),
    );
    return `${banner}
      ${epicHeader(epic)}
      <div class="fb-cols"><div>${driverBlock(epic, sources)}${workersTable(workers)}${prs}</div><div>${deps}</div></div>
      ${sourceList(sources)}`;
  }

  function renderPrs(params, sources, options) {
    const query = params instanceof URLSearchParams ? params : new URLSearchParams(params || "");
    const selected = query.get("pr");
    const banner = staleBanner(staleState(sources || [], ageOption(options), optionFlag(options, "failed")));
    const extra = selected
      ? `<p class="fb-sub">Selected PR #${esc(selected)}. Detail arrives in a later slice.</p>`
      : "";
    const body = panel(
      "PR pipeline",
      "/api/fleet/v1/prs",
      statusRows(sources, [["Merge queue", "mq_state"]]),
    );
    return `${banner}
      <p class="fb-crumbs"><a href="#/home">Home</a> <span aria-hidden="true">›</span> PR pipeline</p>
      <h2>PR pipeline</h2>${extra}${body}${sourceList(sources)}`;
  }

  function renderAgent(agent) {
    const close = `<button type="button" class="fb-btn" data-action="close">Close</button>`;
    if (!agent) return `${close}<p class="fb-empty">This agent is not on the board.</p>`;
    const epic = agent.epic
      ? `<a href="#/epic/${esc(encodeURIComponent(agent.epic))}">${esc(agent.epic)}</a>`
      : "none";
    return `${close}
      <p class="fb-crumbs">Agent</p>
      <h2>${esc(agent.agent_id || "Agent")}</h2>
      <dl class="fb-kv">
        <dt>Role</dt><dd>${esc(agent.role || "unknown")}</dd>
        <dt>Epic</dt><dd>${epic}</dd>
        <dt>CLI</dt><dd>${esc(agent.cli || "unknown")}</dd>
        <dt>Model</dt><dd>${esc(agent.model || "unknown")}</dd>
        <dt>Task</dt><dd>${esc(typeof agent.task === "string" ? agent.task : taskText(agent.task))}</dd>
        <dt>State</dt><dd>${statePill(agent.state)}</dd>
        <dt>Reason</dt><dd>${esc(agent.state_reason || "unknown")}</dd>
        <dt>Last seen</dt><dd>${esc(sinceLabel(agent.last_seen || agent.since))}</dd>
      </dl>
      <div class="fb-actions"><span class="fb-ph2">Phase 2</span>
        <button type="button" class="fb-btn" disabled>Cancel task</button></div>
      <p class="fb-src">source: /api/fleet/v1/agents</p>`;
  }

  function agoLabel(ms) {
    const seconds = Math.max(0, Math.floor(ms / 1000));
    if (seconds < 60) return seconds + " s ago";
    const minutes = Math.floor(seconds / 60);
    const rest = seconds % 60;
    return minutes + " min " + rest + " s ago";
  }

  function updatedLabel(age) {
    if (age == null) return "waiting";
    return agoLabel(age);
  }

  function routeSlots(route) {
    return route && route.view === "epic" ? ["epic", "agents"] : ["now", "epics"];
  }

  function routeFailed(failures, route) {
    return routeSlots(route).some((slot) => !!(failures && failures[slot]));
  }

  function routeKey(route) {
    const view = route && route.view ? route.view : "home";
    if (view === "epic") return "epic:" + (route.epicId || "");
    return view;
  }

  function responseCurrent(ticket, generation, route) {
    return !!ticket && ticket.generation === generation && ticket.key === routeKey(route);
  }

  function rosterUnavailable(body) {
    return sourcesOf(body).some((row) => row && row.name === "roster_snapshot" && row.status === "unavailable");
  }

  function payloadUsable(slot, body) {
    const data = body && body.data;
    if (!data || typeof data !== "object") return false;
    if (slot === "now") {
      const attention = Array.isArray(data.attention) ? data.attention.length : 0;
      const epics = Array.isArray(data.epics) ? data.epics.length : 0;
      return attention + epics > 0;
    }
    if (slot === "epics") return Array.isArray(data.epics) && data.epics.length > 0;
    if (slot === "epic") return typeof data.epic === "string" && data.epic.length > 0;
    if (slot === "agents") return Array.isArray(data.agents) && data.agents.length > 0;
    return false;
  }

  function adoptPayload(slot, previous, incoming) {
    if (!incoming) return { body: previous || null, fresh: false };
    if (rosterUnavailable(incoming) && !payloadUsable(slot, incoming) && payloadUsable(slot, previous)) {
      const sources = sourcesOf(incoming);
      return {
        body: {
          schema: previous.schema,
          generated_at: previous.generated_at,
          sources: sources.length ? sources : sourcesOf(previous),
          data: previous.data,
        },
        fresh: false,
      };
    }
    return { body: incoming, fresh: true };
  }

  function displayedAge(stamps, route, now) {
    const keys = route && route.view === "epic" ? ["epic", "agents"] : ["now", "epics"];
    let oldest = null;
    keys.forEach((key) => {
      const at = stamps && stamps[key];
      if (typeof at !== "number" || at <= 0) return;
      const age = now - at;
      if (oldest == null || age > oldest) oldest = age;
    });
    return oldest;
  }

  function commitBoard(state, ticket, incoming, now) {
    if (!responseCurrent(ticket, state.generation, state.route)) return state;
    const nextSnapshot = Object.assign({}, state.snapshot);
    const freshAt = Object.assign({}, state.freshAt);
    const failures = Object.assign({}, state.failures);
    routeSlots(state.route).forEach((slot) => {
      const prior = slot === "epic" && nextSnapshot.epicId !== state.route.epicId ? null : nextSnapshot[slot];
      const body = incoming ? incoming[slot] : null;
      const adopted = adoptPayload(slot, prior, body);
      nextSnapshot[slot] = adopted.body;
      failures[slot] = !body;
      if (adopted.fresh) freshAt[slot] = now;
    });
    if (state.route && state.route.view === "epic") nextSnapshot.epicId = state.route.epicId;
    return { generation: state.generation, route: state.route, snapshot: nextSnapshot, freshAt, failures };
  }

  const api = {
    REFRESH_MS,
    STALE_MS,
    esc,
    isFleetPath,
    parseRoute,
    withParams,
    filterEpics,
    metricText,
    harnessTiles,
    stateClass,
    statePill,
    attentionHref,
    sourceLabel,
    staleState,
    staleMessage,
    homeModel,
    routeKey,
    responseCurrent,
    routeSlots,
    routeFailed,
    adoptPayload,
    displayedAge,
    commitBoard,
    renderHome,
    renderEpic,
    renderPrs,
    renderAgent,
    cardHtml,
  };
  root.FleetBoard = api;

  if (typeof document === "undefined" || !document.getElementById) return;

  const snapshot = { now: null, epics: null, epic: null, epicId: "", agents: null };
  const freshAt = { now: 0, epics: 0, epic: 0, agents: 0 };
  const failures = { now: false, epics: false, epic: false, agents: false };
  let refreshGen = 0;
  let appliedKey = "";
  let openAgentId = null;
  let searchTimer = 0;
  let failed = false;
  let chord = false;

  function ageMs() {
    return displayedAge(freshAt, parseRoute(location.hash || "#/home"), Date.now());
  }

  function viewSources(route) {
    if (route.view === "epic") return mergeSources(snapshot.epic, snapshot.agents);
    return mergeSources(snapshot.now, snapshot.epics);
  }

  function findAgent(id) {
    const agents = snapshot.agents && snapshot.agents.data && snapshot.agents.data.agents;
    if (Array.isArray(agents)) {
      const found = agents.find((agent) => agent && agent.agent_id === id);
      if (found) return found;
    }
    const epics = [];
    const listed = snapshot.epics && snapshot.epics.data && snapshot.epics.data.epics;
    const nowEpics = snapshot.now && snapshot.now.data && snapshot.now.data.epics;
    if (Array.isArray(listed)) listed.forEach((epic) => epics.push(epic));
    else if (Array.isArray(nowEpics)) nowEpics.forEach((epic) => epics.push(epic));
    if (snapshot.epic && snapshot.epic.data) epics.push(snapshot.epic.data);
    for (let i = 0; i < epics.length; i += 1) {
      const epic = epics[i];
      if (!epic) continue;
      if (epic.driver && epic.driver.agent_id === id) {
        return {
          agent_id: id,
          role: "driver",
          epic: epic.epic,
          cli: epic.driver.cli,
          model: epic.driver.model,
          task: taskText(epic.task),
          state: epic.state,
          state_reason: epic.state_reason,
          last_seen: epic.since,
        };
      }
      const workers = Array.isArray(epic.workers) ? epic.workers : [];
      for (let j = 0; j < workers.length; j += 1) {
        if (workers[j] && workers[j].agent_id === id) {
          return Object.assign({ role: "worker", epic: epic.epic }, workers[j]);
        }
      }
    }
    return null;
  }

  function fillDrawer(id) {
    const drawer = document.getElementById("fb-drawer");
    if (!drawer) return;
    drawer.hidden = false;
    drawer.classList.add("is-open");
    drawer.innerHTML = renderAgent(findAgent(id));
  }

  function closeDrawer() {
    openAgentId = null;
    const drawer = document.getElementById("fb-drawer");
    if (!drawer) return;
    drawer.classList.remove("is-open");
    drawer.hidden = true;
    drawer.innerHTML = "";
  }

  function openAgent(id) {
    if (!id) return;
    openAgentId = id;
    fillDrawer(id);
    const close = document.querySelector("#fb-drawer [data-action='close']");
    if (close) close.focus();
  }

  function markNav(view) {
    document.querySelectorAll(".fb-views a").forEach((link) => {
      const on = link.getAttribute("data-nav") === view;
      link.classList.toggle("is-on", on);
      if (on) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  }

  function syncStamp(route) {
    const age = ageMs();
    const state = staleState(viewSources(route), age, routeFailed(failures, route));
    const ago = document.getElementById("fb-ago");
    const label = document.getElementById("fb-stamp-label");
    const stamp = document.getElementById("fb-stamp");
    if (ago) ago.textContent = updatedLabel(age);
    if (label) label.hidden = age == null;
    if (stamp) stamp.classList.toggle("is-stale", state.stale);
    const banner = document.getElementById("fb-stale");
    if (banner) {
      banner.hidden = !state.stale;
      banner.textContent = staleMessage(state);
    }
  }

  function paint() {
    const app = document.getElementById("fb-app");
    if (!app) return;
    const route = parseRoute(location.hash || "#/home");
    const drafting = document.activeElement && document.activeElement.id === "fb-search" && searchTimer;
    const draft = drafting ? document.activeElement.value : null;
    const selection = drafting ? document.activeElement.selectionStart : null;
    const y = window.scrollY;
    const sources = viewSources(route);
    const options = {
      ageMs: ageMs(),
      failed: routeFailed(failures, route),
      agentsFailed: !!failures.agents,
    };
    let html;
    if (route.view === "epic") {
      const data = snapshot.epic && snapshot.epic.data;
      const id = data && data.epic;
      const matches = snapshot.epicId === route.epicId && snapshot.epic && (id === route.epicId || data === null);
      if (matches) html = renderEpic(snapshot.epic, snapshot.agents, options);
      else if (failed && snapshot.epicId === route.epicId) html = `<p class="fb-empty">The board could not be read.</p>`;
      else html = `<p class="fb-empty">Loading the board…</p>`;
    } else if (route.view === "prs") {
      html = renderPrs(route.params, sources, options);
    } else if (!snapshot.now && !snapshot.epics) {
      html = failed ? `<p class="fb-empty">The board could not be read.</p>` : `<p class="fb-empty">Loading the board…</p>`;
    } else {
      html = renderHome(homeModel(snapshot.now, snapshot.epics), route.params, options);
    }
    app.innerHTML = html;
    markNav(route.view);
    syncStamp(route);
    if (draft != null) {
      const field = document.getElementById("fb-search");
      if (field) {
        field.value = draft;
        field.focus();
        const pos = selection == null ? draft.length : selection;
        if (field.setSelectionRange) field.setSelectionRange(pos, pos);
      }
    }
    window.scrollTo(0, y);
    if (openAgentId) fillDrawer(openAgentId);
  }

  async function fetchJson(path) {
    if (!isFleetPath(path)) return null;
    try {
      const init = {
        headers: { Accept: "application/json" },
        cache: "no-store",
      };
      if (typeof AbortSignal !== "undefined" && typeof AbortSignal.timeout === "function") {
        init.signal = AbortSignal.timeout(20000);
      }
      const response = await fetch(path, init);
      let body = null;
      try {
        body = await response.json();
      } catch (error) {
        body = null;
      }
      if (!response.ok && response.status !== 404) return null;
      if (!body || typeof body !== "object") return null;
      return body;
    } catch (error) {
      return null;
    }
  }

  async function refresh() {
    const generation = ++refreshGen;
    const route = parseRoute(location.hash || "#/home");
    const ticket = { generation, key: routeKey(route) };
    const incoming = {};
    try {
      if (route.view === "epic" && route.epicId) {
        const epicPath = "/api/fleet/v1/epics/" + encodeURIComponent(route.epicId);
        const [epicBody, agentsBody] = await Promise.all([
          fetchJson(epicPath),
          fetchJson("/api/fleet/v1/agents"),
        ]);
        incoming.epic = epicBody;
        incoming.agents = agentsBody;
      } else {
        const [nowBody, epicsBody] = await Promise.all([
          fetchJson("/api/fleet/v1/now"),
          fetchJson("/api/fleet/v1/epics"),
        ]);
        incoming.now = nowBody;
        incoming.epics = epicsBody;
      }
    } finally {
      const current = parseRoute(location.hash || "#/home");
      if (responseCurrent(ticket, refreshGen, current)) {
        const committed = commitBoard(
          { generation: refreshGen, route: current, snapshot, freshAt, failures },
          ticket,
          incoming,
          Date.now(),
        );
        Object.keys(snapshot).forEach((key) => {
          snapshot[key] = committed.snapshot[key];
        });
        Object.keys(freshAt).forEach((key) => {
          freshAt[key] = committed.freshAt[key] || 0;
        });
        Object.keys(failures).forEach((key) => {
          failures[key] = !!committed.failures[key];
        });
        const slots = routeSlots(current);
        const anyBody = slots.some((slot) => incoming[slot]);
        const anyShown = slots.some((slot) => snapshot[slot]);
        failed = !anyBody && !anyShown;
        appliedKey = ticket.key;
        paint();
      }
    }
  }

  function openHelp() {
    const help = document.getElementById("fb-help-modal");
    if (!help) return;
    help.hidden = false;
    const close = document.getElementById("fb-help-close");
    if (close) close.focus();
  }

  function closeHelp() {
    const help = document.getElementById("fb-help-modal");
    if (help) help.hidden = true;
  }

  function setTheme(theme) {
    const next = theme === "dark" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem("fleet-board-theme", next);
    } catch (error) {
      /* the toggle still applies for this view */
    }
  }

  function focusSearch() {
    const route = parseRoute(location.hash || "#/home");
    if (route.view !== "home") {
      location.hash = "#/home";
      window.setTimeout(() => {
        const field = document.getElementById("fb-search");
        if (field) field.focus();
      }, 50);
      return;
    }
    const field = document.getElementById("fb-search");
    if (field) field.focus();
  }

  function moveCard(delta) {
    const cards = Array.prototype.slice.call(document.querySelectorAll(".fb-card"));
    if (!cards.length) return;
    const index = cards.indexOf(document.activeElement);
    const next = cards[Math.max(0, Math.min(cards.length - 1, (index === -1 ? (delta > 0 ? -1 : 0) : index) + delta))];
    if (next) next.focus();
  }

  function boot() {
    const app = document.getElementById("fb-app");
    if (!app || app.dataset.booted === "1") return;
    app.dataset.booted = "1";
    if (!location.hash) history.replaceState(null, "", "#/home");

    app.addEventListener("change", (event) => {
      const key = event.target.getAttribute && event.target.getAttribute("data-filter");
      if (!key) return;
      history.replaceState(null, "", withParams(location.hash || "#/home", { [key]: event.target.value }));
      paint();
    });
    app.addEventListener("input", (event) => {
      if (!event.target || event.target.id !== "fb-search") return;
      const value = event.target.value;
      window.clearTimeout(searchTimer);
      searchTimer = window.setTimeout(() => {
        searchTimer = 0;
        history.replaceState(null, "", withParams(location.hash || "#/home", { q: value.trim() ? value : "" }));
        paint();
      }, 250);
    });
    app.addEventListener("click", (event) => {
      const button = event.target.closest && event.target.closest("[data-agent]");
      if (!button) return;
      event.preventDefault();
      openAgent(button.getAttribute("data-agent"));
    });

    const drawer = document.getElementById("fb-drawer");
    if (drawer) {
      drawer.addEventListener("click", (event) => {
        if (event.target.closest && event.target.closest("[data-action='close']")) closeDrawer();
      });
    }
    const theme = document.getElementById("fb-theme");
    if (theme) {
      theme.addEventListener("click", () => {
        const current = document.documentElement.getAttribute("data-theme");
        setTheme(current === "dark" ? "light" : "dark");
      });
    }
    const help = document.getElementById("fb-help");
    if (help) help.addEventListener("click", openHelp);
    const helpClose = document.getElementById("fb-help-close");
    if (helpClose) helpClose.addEventListener("click", closeHelp);
    const modal = document.getElementById("fb-help-modal");
    if (modal) {
      modal.addEventListener("click", (event) => {
        if (event.target === modal) closeHelp();
      });
    }

    document.addEventListener("keydown", (event) => {
      const tag = event.target && event.target.tagName;
      if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") {
        if (event.key === "Escape") event.target.blur();
        return;
      }
      if (chord) {
        chord = false;
        if (event.key === "h") location.hash = "#/home";
        if (event.key === "p") location.hash = "#/prs";
        return;
      }
      if (event.key === "g") {
        chord = true;
        window.setTimeout(() => { chord = false; }, 800);
        return;
      }
      if (event.key === "/") {
        event.preventDefault();
        focusSearch();
      } else if (event.key === "t") {
        const current = document.documentElement.getAttribute("data-theme");
        setTheme(current === "dark" ? "light" : "dark");
      } else if (event.key === "?") {
        openHelp();
      } else if (event.key === "Escape") {
        closeHelp();
        closeDrawer();
      } else if (event.key === "r") {
        refresh();
      } else if (event.key === "j" || event.key === "k") {
        moveCard(event.key === "j" ? 1 : -1);
      }
    });

    window.addEventListener("hashchange", () => {
      const route = parseRoute(location.hash || "#/home");
      paint();
      if (routeKey(route) !== appliedKey) refresh();
    });

    paint();
    refresh();
    window.setInterval(refresh, REFRESH_MS);
    window.setInterval(() => syncStamp(parseRoute(location.hash || "#/home")), 1000);
  }

  if (document.getElementById("fb-app")) boot();
  else document.addEventListener("DOMContentLoaded", boot);
})(typeof globalThis !== "undefined" ? globalThis : this);
