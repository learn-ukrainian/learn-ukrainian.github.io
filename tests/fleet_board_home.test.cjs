const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "dashboards/fleet-board.html"), "utf8");
const css = fs.readFileSync(path.join(root, "dashboards/fleet-board.css"), "utf8");
const js = fs.readFileSync(path.join(root, "dashboards/fleet-board.js"), "utf8");

const context = {
  URLSearchParams,
  encodeURIComponent,
  decodeURIComponent,
  Number,
  String,
  Math,
  Object,
  Array,
  JSON,
};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(js, context, { filename: path.join(root, "dashboards/fleet-board.js") });
const FB = context.FleetBoard;

const VOID = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"]);

function decode(value) {
  return String(value)
    .replace(/&quot;/g, "\"")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&");
}

function parseAttrs(raw) {
  const attrs = {};
  const re = /([A-Za-z_:][-A-Za-z0-9_:.]*)(?:\s*=\s*"([^"]*)")?/g;
  let match;
  while ((match = re.exec(raw))) {
    attrs[match[1]] = match[2] == null ? "" : decode(match[2]);
  }
  return attrs;
}

function parseHtml(source) {
  const rootNode = { tag: "root", attrs: {}, children: [] };
  let node = rootNode;
  const re = /<!--[\s\S]*?-->|<\/([A-Za-z0-9]+)>|<([A-Za-z0-9]+)([^>]*?)\/?>|([^<]+)/g;
  let match;
  while ((match = re.exec(source))) {
    if (match[0].startsWith("<!--")) continue;
    if (match[1]) {
      const tag = match[1].toLowerCase();
      let cursor = node;
      while (cursor && cursor.tag !== tag) cursor = cursor.parent;
      if (cursor && cursor.parent) node = cursor.parent;
      continue;
    }
    if (match[2]) {
      const tag = match[2].toLowerCase();
      const el = { tag, attrs: parseAttrs(match[3] || ""), children: [], parent: node };
      node.children.push(el);
      const selfClose = /\/\s*$/.test(match[3] || "") || VOID.has(tag);
      if (!selfClose) node = el;
      continue;
    }
    if (match[4]) node.children.push({ text: match[4] });
  }
  return rootNode;
}

function walk(node, visit) {
  if (!node || !node.tag || node.tag === "text") return;
  if (node.tag !== "root") visit(node);
  (node.children || []).forEach((child) => walk(child, visit));
}

function queryAll(node, className) {
  const out = [];
  walk(node, (el) => {
    const cls = (el.attrs && el.attrs.class) || "";
    if (cls.split(/\s+/).includes(className)) out.push(el);
  });
  return out;
}

function textContent(node) {
  if (!node) return "";
  if (node.text != null && !node.tag) return node.text;
  return (node.children || []).map(textContent).join("");
}

function source(name, status) {
  return {
    name,
    status,
    age_s: status === "ok" || status === "stale" ? 4 : null,
    error: null,
  };
}

const sources = [
  source("roster_snapshot", "ok"),
  source("harness_snapshot", "not_configured"),
  source("downloads", "not_configured"),
  source("backups", "ok"),
  source("mq_state", "not_configured"),
  source("stats", "stale"),
  source("alerts", "not_configured"),
  source("links", "not_configured"),
  source("delegate", "ok"),
  source("occupancy", "ok"),
];

const cedar = {
  epic: "cedar",
  title: "Cedar",
  focus: "sample focus",
  parent: "parent-one",
  layer: 1,
  intended: "running",
  state: "stuck",
  state_reason: "idle while intended running",
  since: "2026-10-09T09:00:00Z",
  driver: {
    agent_id: "driver-cedar",
    cli: "cli-a",
    model: "model-a",
    harness: "harness-a",
    pid_alive: true,
  },
  task: { kind: "pr", number: 17, title: "sample change" },
  workers: [{
    agent_id: "worker-cedar",
    cli: "cli-a",
    model: "model-b",
    task: "sample review",
    state: "working",
    state_reason: "active task",
    since: "2026-10-09T09:10:00Z",
  }],
};

const birch = {
  epic: "birch",
  title: "Birch",
  focus: null,
  parent: null,
  layer: 0,
  intended: "running",
  state: "working",
  state_reason: "recorded working",
  since: "2026-10-09T09:20:00Z",
  driver: {
    agent_id: "driver-birch",
    cli: "cli-b",
    model: "model-a",
    harness: "harness-b",
    pid_alive: true,
  },
  task: { kind: "issue", number: 18, title: "sample issue" },
  workers: [],
};

const aspen = {
  epic: "aspen",
  title: "Aspen",
  focus: null,
  parent: null,
  layer: null,
  intended: "paused",
  state: "paused",
  state_reason: "paused by roster",
  since: null,
  driver: null,
  task: { kind: "none", number: null, title: null },
  workers: [],
};

const nowEnvelope = {
  schema: "fleet.v1.now",
  generated_at: "2026-10-09T09:31:52Z",
  sources,
  data: {
    attention: [
      {
        severity: "bad",
        kind: "stuck_driver",
        title: "Cedar",
        summary: "idle while intended running",
        target: { type: "epic", id: "cedar" },
      },
      {
        severity: "warn",
        kind: "unqueued_pr",
        title: "sample change",
        summary: "green with approval at head and not queued",
        target: { type: "pr", id: "17" },
      },
    ],
    epics: [birch, cedar, aspen],
  },
};

const epicsEnvelope = {
  schema: "fleet.v1.epics",
  generated_at: "2026-10-09T09:31:52Z",
  sources,
  data: { epics: [birch, cedar, aspen] },
};

const agentsEnvelope = {
  schema: "fleet.v1.agents",
  generated_at: "2026-10-09T09:31:52Z",
  sources,
  data: {
    agents: [
      {
        agent_id: "driver-cedar",
        role: "driver",
        epic: "cedar",
        cli: "cli-a",
        model: "model-a",
        task: "sample change",
        state: "stuck",
        state_reason: "idle while intended running",
        last_seen: "2026-10-09T09:00:00Z",
      },
      {
        agent_id: "worker-cedar",
        role: "worker",
        epic: "cedar",
        cli: "cli-a",
        model: "model-b",
        task: "sample review",
        state: "working",
        state_reason: "active task",
        last_seen: "2026-10-09T09:10:00Z",
      },
      {
        agent_id: "worker-birch",
        role: "worker",
        epic: "birch",
        cli: "cli-b",
        model: "model-c",
        task: "other review",
        state: "idle",
        state_reason: "waiting",
        last_seen: "2026-10-09T09:15:00Z",
      },
    ],
  },
};

function homeHtml(params, options) {
  const model = FB.homeModel(nowEnvelope, epicsEnvelope);
  return FB.renderHome(model, params || new URLSearchParams(), options || { ageMs: 1000 });
}

function cardHrefs(sourceHtml) {
  return queryAll(parseHtml(sourceHtml), "fb-card").map((card) => card.attrs.href);
}

function assertClean(text, label) {
  const patterns = [
    [/localhost/i, "localhost"],
    [/127\.0\.0\.1/, "loopback"],
    [/https?:\/\//i, "absolute url"],
    [/^[\s\S]*github\.com[\s\S]*$/i, "github"],
    [/\/home\//, "home path"],
    [/\/Users\//, "users path"],
    [/\/tmp\//, "tmp path"],
    [/tmux/i, "tmux"],
  ];
  patterns.forEach(([pattern, name]) => {
    assert.doesNotMatch(text, pattern, `${label} contains ${name}`);
  });
}

test("publication assertions reject forbidden domain text at any position", () => {
  for (const text of [
    "github.com", "GITHUB.COM", "before github.com after",
    "github.com.example", "examplegithub.com", "before\ngithub.com\nafter",
  ]) {
    assert.throws(() => assertClean(text, "probe"), /probe contains github/);
  }
  assert.doesNotThrow(() => assertClean("clean public label", "probe"));
});

test("page shell follows the dashboard conventions", () => {
  assert.match(html, /<link rel="stylesheet" href="\/monitor\.css">/);
  assert.match(html, /<link rel="stylesheet" href="\/fleet-board\.css">/);
  assert.match(html, /<script src="\/fleet-board\.js"><\/script>/);
  assert.match(html, /class="monitor-nav"/);
  for (const href of ["/", "/orient.html", "/fleet.html", "/work.html", "/artifacts/", "/runtime.html", "/docs"]) {
    assert.match(html, new RegExp(`href="${href.replace("/", "\\/")}"`));
  }
  assert.match(html, /data-read-only="true"/);
  assert.match(html, /data-nav="home"/);
  assert.match(html, /data-nav="prs"/);
  assert.doesNotMatch(html, /cdn|googleapis|unpkg|jsdelivr/i);
  assert.match(css, /#7a1c20/);
  assert.match(css, /#faf6ef/);
  assert.match(css, /\[data-theme="dark"\]/);
  assert.match(css, /max-width:\s*820px/);
  assert.match(css, /\.fb-attn\s*\{[^}]*overflow-x:\s*auto/);
  assert.match(css, /grid-template-columns:\s*1fr/);
  assert.equal(FB.REFRESH_MS, 30000);
  assert.equal(FB.STALE_MS, 120000);
  assert.match(js, /setInterval\(refresh, REFRESH_MS\)/);
  assert.doesNotMatch(js, /https?:\/\//i);
});

test("home renders attention, cards, unknown harness, and not installed", () => {
  const rendered = homeHtml();
  const doc = parseHtml(rendered);
  const items = queryAll(doc, "fb-attn-item");
  assert.equal(items.length, 2);
  assert.equal(items[0].attrs.href, "#/epic/cedar");
  assert.match(textContent(items[0]), /Cedar/);
  assert.match(textContent(items[0]), /idle while intended running/);
  assert.equal(items[1].attrs.href, "#/prs?pr=17");
  assert.match(textContent(items[1]), /Green PR not queued/);

  const cards = queryAll(doc, "fb-card");
  assert.deepEqual(cardHrefs(rendered), ["#/epic/cedar", "#/epic/birch", "#/epic/aspen"]);
  const cedarCard = cards[0];
  assert.match(cedarCard.attrs.class, /is-stuck/);
  assert.match(textContent(cedarCard), /cli-a/);
  assert.match(textContent(cedarCard), /model-a/);
  assert.match(textContent(cedarCard), /PR #17/);
  assert.match(textContent(cedarCard), /sample change/);
  assert.match(textContent(cedarCard), /1 worker: model-b \(working\)/);
  assert.match(textContent(cedarCard), /stuck/);

  const tiles = queryAll(doc, "fb-tile");
  assert.equal(tiles.length, 15);
  tiles.forEach((tile) => {
    assert.match(textContent(tile), /unknown/);
    assert.doesNotMatch(textContent(tile), /0/);
  });
  assert.match(rendered, /Harness health: not installed/);
  assert.match(rendered, /not installed/);
  assert.match(rendered, /A source is stale/);
  assert.match(rendered, /Values below may be out of date/);
  assert.match(rendered, /Optional Fleet board observations/);
  assert.doesNotMatch(rendered, /Nothing needs attention|later slice/);
});

test("filters, search, and sort stay in the rendered query", () => {
  const working = homeHtml(new URLSearchParams("state=working"));
  assert.deepEqual(cardHrefs(working), ["#/epic/birch"]);
  assert.match(working, /value="working" selected|selected>working|value="working" selected/);

  const found = homeHtml(new URLSearchParams("q=model-b"));
  assert.deepEqual(cardHrefs(found), ["#/epic/cedar"]);
  assert.match(found, /value="model-b"/);

  const harness = homeHtml(new URLSearchParams("harness=harness-b"));
  assert.deepEqual(cardHrefs(harness), ["#/epic/birch"]);

  const byName = homeHtml(new URLSearchParams("sort=name"));
  assert.deepEqual(cardHrefs(byName), ["#/epic/aspen", "#/epic/birch", "#/epic/cedar"]);

  const byLayer = homeHtml(new URLSearchParams("sort=layer"));
  assert.deepEqual(cardHrefs(byLayer), ["#/epic/birch", "#/epic/cedar", "#/epic/aspen"]);

  assert.equal(
    FB.withParams("#/home?layer=1", { state: "stuck", layer: "" }),
    "#/home?state=stuck",
  );
  assert.equal(FB.parseRoute("#/epic/cedar?q=model-b").epicId, "cedar");
  assert.equal(FB.parseRoute("#/epic/cedar?q=model-b").params.get("q"), "model-b");
});

test("worker task strings and structured fields are searchable without object coercion", () => {
  function matches(task, query) {
    const epic = { ...cedar, workers: [{ ...cedar.workers[0], task }] };
    return FB.filterEpics([epic], new URLSearchParams({ q: query })).length;
  }
  assert.equal(matches("unique review", "unique review"), 1);
  for (const kind of ["issue", "pr"]) {
    const task = { kind, number: 2468, title: "Unique structured task" };
    for (const query of [kind, "2468", "unique structured task"]) {
      assert.equal(matches(task, query), 1);
    }
    assert.equal(matches(task, "[object object]"), 0);
  }
  for (const task of [null, undefined, true, 2468, ["hidden"], { title: { nested: "hidden" } }]) {
    assert.equal(matches(task, "[object object]"), 0);
    assert.equal(matches(task, "hidden"), 0);
    assert.equal(matches(task, "worker-cedar"), 1);
  }
});

test("unknown harness values stay unknown and a real zero stays zero", () => {
  assert.equal(FB.metricText(null, "%"), "?");
  assert.equal(FB.metricText(undefined, " m"), "?");
  assert.equal(FB.metricText(0, " m"), "0 m");
  assert.equal(FB.metricText(0, "%"), "0%");
  const rendered = FB.harnessTiles({
    context_pct: null,
    compactions: null,
    status: "ok",
    stop_count: null,
    ask_count: 0,
    idle_min: 0,
  });
  const doc = parseHtml(rendered);
  const idle = queryAll(doc, "fb-tile").find((el) => el.attrs["data-metric"] === "idle");
  const context = queryAll(doc, "fb-tile").find((el) => el.attrs["data-metric"] === "context");
  assert.match(textContent(idle), /0 m/);
  assert.match(textContent(context), /unknown/);
  assert.doesNotMatch(textContent(context), /0/);
});

test("a fresh ok payload does not warn or say not installed", () => {
  const quiet = sources.map((row) => source(row.name, "ok"));
  const model = FB.homeModel(
    { data: nowEnvelope.data, sources: quiet },
    { data: epicsEnvelope.data, sources: quiet },
  );
  const rendered = FB.renderHome(model, new URLSearchParams(), { ageMs: 1000 });
  assert.doesNotMatch(rendered, /not installed/);
  assert.doesNotMatch(rendered, /out of date/);
  const aged = FB.renderHome(model, new URLSearchParams(), { ageMs: 120001 });
  assert.match(aged, /over 2 minutes ago/);
  assert.match(aged, /out of date/);
});

test("epic detail uses agents and keeps phase 2 controls disabled", () => {
  const epic = {
    schema: "fleet.v1.epic",
    sources,
    data: {
      ...cedar,
      workers: [{
        agent_id: "only-on-epic",
        cli: "cli-a",
        model: "model-z",
        task: "decoy",
        state: "idle",
        state_reason: "decoy",
        since: "2026-10-09T09:00:00Z",
      }],
    },
  };
  const rendered = FB.renderEpic(epic, agentsEnvelope, { ageMs: 1000 });
  const doc = parseHtml(rendered);
  assert.match(rendered, /process alive/);
  assert.match(rendered, /cli-a \/ harness-a/);
  assert.match(rendered, /worker-cedar/);
  assert.match(rendered, /sample review/);
  assert.doesNotMatch(rendered, /only-on-epic/);
  assert.doesNotMatch(rendered, /worker-birch/);
  assert.match(rendered, /not installed/);
  const buttons = queryAll(doc, "fb-btn");
  assert.ok(buttons.length >= 3);
  buttons.forEach((button) => {
    assert.ok(Object.prototype.hasOwnProperty.call(button.attrs, "disabled"));
  });
  assert.match(textContent(doc), /Pause epic/);
  assert.match(textContent(doc), /Nudge driver/);
  assert.match(textContent(doc), /Restart driver/);

  const fallback = FB.renderEpic(epic, null, { ageMs: 0 });
  assert.match(fallback, /only-on-epic/);

  const missing = FB.renderEpic({ data: null, sources }, agentsEnvelope, { ageMs: 0 });
  assert.match(missing, /not on the board/);
});

test("untrusted text is escaped and fetches stay on the fleet v1 paths", () => {
  const model = FB.homeModel(nowEnvelope, epicsEnvelope);
  model.attention = [{
    severity: "bad",
    kind: "alert",
    title: "<img alt=\"x\">",
    summary: "<b>",
    target: { type: "alert", id: "x" },
  }];
  model.epics = [{ ...cedar, title: "<img alt=\"x\">" }];
  const rendered = FB.renderHome(model, new URLSearchParams(), { ageMs: 0 });
  assert.match(rendered, /&lt;img/);
  assert.doesNotMatch(rendered, /<img/);
  assert.equal(FB.attentionHref({ target: { type: "alert", id: "x" } }), "#/home");
  assert.equal(FB.isFleetPath("/api/fleet/v1/now"), true);
  assert.equal(FB.isFleetPath("/api/fleet/v1/epics"), true);
  assert.equal(FB.isFleetPath("/api/fleet/v1/epics/cedar"), true);
  assert.equal(FB.isFleetPath("/api/fleet/v1/agents/driver-cedar"), true);
  assert.equal(FB.isFleetPath("/api/fleet/v1/epics/cedar/extra"), false);
  assert.equal(FB.isFleetPath("/api/fleet/v1/now?x=1"), false);
  assert.equal(FB.isFleetPath("/api/other"), false);
  assert.equal(FB.isFleetPath("/api/fleet/v1/epics/.."), false);
  assert.equal(FB.sourceLabel("not_configured"), "not installed");
});

test("a superseded epic response is discarded and each payload keeps its own age", () => {
  const birch = FB.parseRoute("#/epic/birch");
  const cedar = FB.parseRoute("#/epic/cedar");
  const birchBody = { schema: "fleet.v1.epic", data: { epic: "birch", title: "Birch" }, sources: [] };
  const started = {
    generation: 2,
    route: cedar,
    snapshot: { now: null, epics: null, epic: null, epicId: "", agents: null },
    freshAt: { now: 0, epics: 0, epic: 0, agents: 0 },
  };
  const discarded = FB.commitBoard(
    started,
    { generation: 1, key: FB.routeKey(birch) },
    { epic: birchBody },
    5000,
  );
  assert.equal(discarded, started);
  assert.equal(discarded.snapshot.epic, null);
  assert.equal(FB.responseCurrent({ generation: 2, key: FB.routeKey(cedar) }, 2, cedar), true);

  const nowBody = {
    schema: "fleet.v1.now",
    generated_at: "2026-10-09T12:00:00Z",
    data: {
      attention: [{ title: "Cedar", kind: "alert", severity: "warn", summary: "check", target: { type: "alert", id: "x" } }],
      epics: [{ epic: "cedar", title: "Cedar" }],
    },
    sources: [{ name: "roster_snapshot", status: "ok", age_s: 1, error: null }],
  };
  const home = FB.parseRoute("#/home");
  let state = {
    generation: 1,
    route: home,
    snapshot: { now: null, epics: null, epic: null, epicId: "", agents: null },
    freshAt: { now: 0, epics: 0, epic: 0, agents: 0 },
  };
  state = FB.commitBoard(state, { generation: 1, key: FB.routeKey(home) }, { now: nowBody, epics: null }, 1000);
  assert.equal(state.freshAt.now, 1000);
  assert.equal(state.freshAt.epics, 0);
  const epicsBody = {
    schema: "fleet.v1.epics",
    data: { epics: [{ epic: "cedar", title: "Cedar" }] },
    sources: [{ name: "roster_snapshot", status: "ok", age_s: 1, error: null }],
  };
  state = FB.commitBoard(state, { generation: 1, key: FB.routeKey(home) }, { now: null, epics: epicsBody }, 181000);
  assert.equal(state.freshAt.now, 1000);
  assert.equal(state.freshAt.epics, 181000);
  assert.equal(state.snapshot.now.data.attention[0].title, "Cedar");
  const age = FB.displayedAge(state.freshAt, home, 181000);
  assert.equal(age, 180000);
  assert.equal(FB.staleState([], age).ageStale, true);

  const failedNow = {
    schema: "fleet.v1.now",
    generated_at: "2026-10-09T12:03:00Z",
    data: { attention: [], epics: [] },
    sources: [{ name: "roster_snapshot", status: "unavailable", age_s: null, error: "unavailable" }],
  };
  state = FB.commitBoard(state, { generation: 1, key: FB.routeKey(home) }, { now: failedNow }, 200000);
  assert.equal(state.snapshot.now.data.attention[0].title, "Cedar");
  assert.equal(state.snapshot.now.sources[0].status, "unavailable");
  assert.equal(state.freshAt.now, 1000);
  const rendered = FB.renderHome(
    FB.homeModel(state.snapshot.now, state.snapshot.epics),
    new URLSearchParams(),
    { ageMs: FB.displayedAge(state.freshAt, home, 200000) },
  );
  assert.match(rendered, /Cedar/);
  assert.match(rendered, /unavailable/);
  assert.match(rendered, /over 2 minutes/);
});

test("the PR view is an observed pipeline with explicit unmet history and owner", () => {
  const rendered = FB.renderPrs(new URLSearchParams("pr=17"), sampleReads(), { now: NOW });
  assert.match(rendered, /PR pipeline/);
  assert.match(rendered, /Selected PR #17/);
  assert.match(rendered, /Accountable owner/);
  assert.match(rendered, /unknown \(D04; canonical PR association unavailable\)/);
  assert.match(rendered, /Merged history/);
  assert.match(rendered, /Head head-new/);
  assert.doesNotMatch(rendered, /later slice|Detail arrives/);
});

test("shipped files and the fixture carry no hosts, absolute urls, or session names", () => {
  assertClean(html, "html");
  assertClean(css, "css");
  assertClean(js, "js");
  assertClean(JSON.stringify({ nowEnvelope, epicsEnvelope, agentsEnvelope }), "fixture");
});

test("a failed endpoint keeps cached data but flags the refresh as failed", () => {
  const home = FB.parseRoute("#/home");
  const key = { generation: 1, key: FB.routeKey(home) };
  const cachedNow = {
    schema: "fleet.v1.now",
    generated_at: "2026-10-09T12:00:00Z",
    data: { attention: [], epics: [{ epic: "cedar", title: "Cedar" }] },
    sources: [{ name: "roster_snapshot", status: "ok", age_s: 1, error: null }],
  };
  let state = {
    generation: 1,
    route: home,
    snapshot: { now: null, epics: null, epic: null, epicId: "", agents: null },
    freshAt: { now: 0, epics: 0, epic: 0, agents: 0 },
    failures: { now: false, epics: false, epic: false, agents: false },
  };
  state = FB.commitBoard(state, key, { now: cachedNow, epics: null }, 1000);
  assert.equal(state.failures.now, false);
  assert.equal(state.failures.epics, true);

  state = FB.commitBoard(state, key, { now: null, epics: null }, 2000);
  assert.equal(state.failures.now, true);
  assert.equal(state.snapshot.now.data.epics[0].title, "Cedar");
  assert.equal(state.snapshot.now.sources[0].status, "ok");
  assert.equal(state.freshAt.now, 1000);
  assert.equal(FB.routeFailed(state.failures, home), true);

  const failed = FB.renderHome(
    FB.homeModel(state.snapshot.now, state.snapshot.epics),
    new URLSearchParams(),
    { ageMs: 1000, failed: FB.routeFailed(state.failures, home) },
  );
  assert.match(failed, /last refresh failed/);
  assert.match(failed, /Cedar/);
  const quiet = FB.renderHome(
    FB.homeModel(state.snapshot.now, state.snapshot.epics),
    new URLSearchParams(),
    { ageMs: 1000, failed: false },
  );
  assert.doesNotMatch(quiet, /last refresh failed/);

  state = FB.commitBoard(state, key, { now: cachedNow, epics: null }, 3000);
  assert.equal(state.failures.now, false);
  assert.equal(state.freshAt.now, 3000);
});

test("epic workers come from the current epic when agents fail or are older", () => {
  const epic = {
    schema: "fleet.v1.epic",
    generated_at: "2026-10-09T12:00:00Z",
    sources,
    data: {
      ...cedar,
      epic: "birch",
      title: "Birch",
      workers: [{
        agent_id: "worker-fresh",
        cli: "cli-a",
        model: "model-z",
        task: "fresh task",
        state: "idle",
        state_reason: "idle",
        since: "2026-10-09T09:00:00Z",
      }],
    },
  };
  const cachedAgents = {
    schema: "fleet.v1.agents",
    generated_at: "2026-10-09T12:00:00Z",
    data: {
      agents: [{
        agent_id: "worker-cached",
        role: "worker",
        epic: "birch",
        cli: "cli-a",
        model: "model-z",
        task: "cached task",
        state: "idle",
        state_reason: "idle",
        since: "2026-10-09T08:00:00Z",
      }],
    },
    sources,
  };
  const failed = FB.renderEpic(epic, cachedAgents, { ageMs: 0, agentsFailed: true });
  assert.match(failed, /worker-fresh/);
  assert.doesNotMatch(failed, /worker-cached/);

  const older = { ...cachedAgents, generated_at: "2026-10-09T11:00:00Z" };
  const olderRendered = FB.renderEpic(epic, older, { ageMs: 0, agentsFailed: false });
  assert.match(olderRendered, /worker-fresh/);
  assert.doesNotMatch(olderRendered, /worker-cached/);

  const current = FB.renderEpic(epic, cachedAgents, { ageMs: 0, agentsFailed: false });
  assert.match(current, /worker-cached/);
  assert.doesNotMatch(current, /worker-fresh/);
});

function mountedBoard() {
  const nodes = new Map();
  const timeouts = new Map();
  const intervals = new Map();
  const windowEvents = {};
  let timerId = 0;
  const document = { activeElement: null, events: {} };
  function node(id) {
    const classes = new Set();
    return {
      id, tagName: "DIV", dataset: {}, attrs: {}, events: {}, hidden: true,
      innerHTML: "", textContent: "", value: "", selectionStart: 0,
      classList: {
        add: (name) => classes.add(name), remove: (name) => classes.delete(name),
        toggle: (name, on) => on ? classes.add(name) : classes.delete(name),
        contains: (name) => classes.has(name),
      },
      getAttribute(name) { return this.attrs[name] ?? null; },
      setAttribute(name, value) { this.attrs[name] = value; },
      removeAttribute(name) { delete this.attrs[name]; },
      addEventListener(name, handler) { this.events[name] = handler; },
      focus() { document.activeElement = this; },
      blur() { document.activeElement = null; },
      setSelectionRange(start) { this.selectionStart = start; },
    };
  }
  ["fb-app", "fb-drawer", "fb-ago", "fb-stamp-label", "fb-stamp", "fb-stale",
    "fb-search", "fb-theme", "fb-help", "fb-help-close", "fb-help-modal", "drawer-close",
    "card-one", "card-two"].forEach((id) => nodes.set(id, node(id)));
  const nav = ["home", "prs"].map((view) => {
    const link = node(view); link.attrs["data-nav"] = view; return link;
  });
  document.documentElement = node("html");
  document.getElementById = (id) => nodes.get(id) || null;
  document.querySelector = () => nodes.get("drawer-close");
  document.querySelectorAll = (selector) => selector === ".fb-views a" ? nav : [nodes.get("card-one"), nodes.get("card-two")];
  document.addEventListener = (name, handler) => { document.events[name] = handler; };
  const location = { hash: "" };
  const requests = [];
  const overrides = {};
  let mode = "ok";
  const window = {
    scrollY: 7, scrollTo() {},
    addEventListener(name, handler) { windowEvents[name] = handler; },
    setTimeout(handler, delay) { const id = ++timerId; timeouts.set(id, { handler, delay }); return id; },
    clearTimeout(id) { timeouts.delete(id); },
    setInterval(handler, delay) { intervals.set(delay, handler); return ++timerId; },
  };
  const sandbox = {
    URLSearchParams, document, location, window, Date,
    history: { replaceState(a, b, hash) { location.hash = hash; } },
    localStorage: { setItem(key, value) { sandbox.savedTheme = value; } },
    AbortSignal: { timeout: () => ({}) },
    async fetch(url, init) {
      requests.push({ url, init });
      if (mode === "throw") throw new Error("synthetic fetch failure");
      const bodies = {
        "/api/fleet/v1/now": nowEnvelope, "/api/fleet/v1/epics": epicsEnvelope,
        "/api/fleet/v1/epics/cedar": { schema: "fleet.v1.epic", sources, data: cedar },
        "/api/fleet/v1/agents": agentsEnvelope,
      };
      return { ok: mode !== "bad", status: mode === "bad" ? 500 : 200, async json() {
        if (mode === "invalid-json") throw new Error("synthetic JSON failure");
        return url in overrides ? overrides[url] : bodies[url] || null;
      } };
    },
  };
  vm.createContext(sandbox);
  vm.runInContext(js, sandbox, { filename: path.join(root, "dashboards/fleet-board.js") });
  return {
    nodes, location, document, nav, requests, intervals, timeouts, sandbox,
    setMode(value) { mode = value; },
    overrides,
    async settle() { await new Promise(setImmediate); },
    async navigate(hash) { location.hash = hash; windowEvents.hashchange(); await this.settle(); },
    key(key, target = nodes.get("fb-app")) { document.events.keydown({ key, target, preventDefault() {} }); },
  };
}

test("mounted board refreshes, filters, preserves failure state, and recovers", async () => {
  const board = mountedBoard();
  const app = board.nodes.get("fb-app");
  await board.settle();
  assert.equal(board.location.hash, "#/home");
  assert.match(app.innerHTML, /Cedar/);
  assert.equal(board.nav[0].attrs["aria-current"], "page");
  assert.ok(board.intervals.has(30000));
  assert.ok(board.intervals.has(1000));
  assert.ok(board.requests.every(({ url, init }) => (url.startsWith("/api/fleet/v1/") || Object.values(FB.READS).includes(url)) && init.cache === "no-store"));
  const filter = { getAttribute: () => "state", value: "working" };
  app.events.change({ target: filter });
  assert.match(board.location.hash, /state=working/);
  assert.match(app.innerHTML, /Birch/);
  app.events.change({ target: { getAttribute: () => null } });
  app.events.input({ target: { id: "unrelated" } });
  const search = board.nodes.get("fb-search");
  search.value = "Birch"; search.focus();
  app.events.input({ target: search });
  board.intervals.get(1000)();
  for (const { handler, delay } of board.timeouts.values()) if (delay === 250) handler();
  assert.match(board.location.hash, /q=Birch/);
  assert.match(app.innerHTML, /Birch/);
  board.setMode("bad"); board.intervals.get(30000)(); await board.settle();
  assert.match(app.innerHTML, /Birch/);
  assert.equal(board.nodes.get("fb-stale").hidden, false);
  assert.match(board.nodes.get("fb-stale").textContent, /refresh failed/i);
  board.setMode("ok"); board.key("r"); await board.settle();
  assert.doesNotMatch(board.nodes.get("fb-stale").textContent, /refresh failed/i);
  await board.navigate("#/epic/cedar");
  assert.match(app.innerHTML, /Cedar/);
  app.events.click({ target: { closest: () => ({ getAttribute: () => "worker-cedar" }) }, preventDefault() {} });
  assert.equal(board.nodes.get("fb-drawer").hidden, false);
  assert.match(board.nodes.get("fb-drawer").innerHTML, /worker-cedar/);
  board.intervals.get(30000)(); await board.settle();
  board.nodes.get("fb-drawer").events.click({ target: { closest: () => true } });
  assert.equal(board.nodes.get("fb-drawer").hidden, true);
  board.nodes.get("fb-theme").events.click();
  assert.equal(board.sandbox.savedTheme, "dark");
  board.key("t"); assert.equal(board.sandbox.savedTheme, "light");
  board.nodes.get("fb-help").events.click();
  assert.equal(board.nodes.get("fb-help-modal").hidden, false);
  board.nodes.get("fb-help-close").events.click();
  board.key("?"); board.nodes.get("fb-help-modal").events.click({ target: board.nodes.get("fb-help-modal") });
  assert.equal(board.nodes.get("fb-help-modal").hidden, true);
  board.key("?"); board.key("Escape");
  assert.equal(board.nodes.get("fb-help-modal").hidden, true);
  board.key("j"); assert.equal(board.document.activeElement.id, "card-one");
  board.key("j"); assert.equal(board.document.activeElement.id, "card-two");
  board.key("k"); assert.equal(board.document.activeElement.id, "card-one");
  board.key("/");
  for (const { handler, delay } of board.timeouts.values()) if (delay === 50) handler();
  assert.equal(board.document.activeElement.id, "fb-search");
  board.key("Escape", { tagName: "INPUT", blur() { search.blur(); } });
  assert.equal(board.document.activeElement, null);
  board.key("g"); board.key("p"); assert.equal(board.location.hash, "#/prs");
  await board.navigate("#/prs"); assert.match(app.innerHTML, /PR pipeline/);
  board.key("g"); board.key("h"); assert.equal(board.location.hash, "#/home");
});

test("mounted board reports initial fetch and malformed JSON failures", async () => {
  const board = mountedBoard();
  await board.settle();
  board.setMode("throw"); await board.navigate("#/epic/missing");
  assert.match(board.nodes.get("fb-app").innerHTML, /could not be read/);
  board.setMode("invalid-json"); board.key("r"); await board.settle();
  assert.match(board.nodes.get("fb-app").innerHTML, /could not be read/);
  assert.equal(board.nodes.get("fb-stale").hidden, false);
});


test("health tiles keep separate counters and withhold stale or unknown values", () => {
  const row = { status: "ok", stop_count: 0, ask_count: 2.5, context_pct: 0, idle_min: 0 };
  const current = parseHtml(FB.harnessTiles(row));
  const get = (doc, name) => textContent(queryAll(doc, "fb-tile").find((el) => el.attrs["data-metric"] === name));
  assert.match(get(current, "stops"), /stops\s*0$/);
  assert.match(get(current, "asks"), /asks\s*2\.5$/);
  assert.match(get(current, "compactions"), /unknown/);
  for (const status of ["stale", "unknown"]) {
    const rendered = FB.harnessTiles({ ...row, status });
    const doc = parseHtml(rendered);
    for (const name of ["context", "compactions", "stops", "asks", "idle"]) {
      assert.match(get(doc, name), new RegExp(status));
      assert.doesNotMatch(get(doc, name), /[0-9]/);
    }
  }
});

const NOW = Date.parse('2026-10-15T12:00:00Z');
const at = seconds => new Date(NOW - seconds * 1000).toISOString();
const envelope = (key, data, reports = [source(key, 'ok')]) => ({ schema: 'fleet.v1.' + key, sources: reports, data });
function sampleBodies() {
  const item = {
    work_id: 'pr:sample:17', resource_kind: 'pr', repository_id: 'sample/repo', remote_id: '17',
    title: 'Sample PR', lifecycle: 'open', flags: { source_ok: true, has_blocker: false },
    projections: { verification: { head_sha: 'head-new', ci_state: 'green' }, review: { review_decision: 'APPROVED' },
      dispatch: { accountable_owner: 'unknown', owner_reason: 'owner_unknown' }, stream: { status: 'n/a', fresh: true } },
    authority: [{ domain: 'github', observed_at: at(20), age_s: 20, stale: false }], omissions: [],
  };
  return {
    registry: { streams: [{ stream_id: 'epic:1', registered: true, stream_name: 'cedar', title: 'Cedar registry',
      lease: { state: 'active', heartbeat_at: at(10), expires_at: at(-100), holder: { agent: 'driver-a', task_id: 'task-a', harness: 'native' } },
      last_state: { body: 'Recorded state', created_at: at(90) }, last_decision: { body: 'Recorded decision', created_at: at(95) } },
      { stream_id: 'epic:2', registered: false, title: 'Unregistered stream', lease: null }] },
    work: { items: [item], sources: [{ source_id: 'public-monitor', status: 'ok', sections: { prs: { status: 'ok', count: 1, observed_at: at(20), age_s: 20 } } }], cache_age_s: 0 },
    hosts: { hosts: { 'host-a': { status: 'fresh', observed_at: at(4), age_seconds: 4, cpu_count: 4, loadavg: [0,1,2], mem: { used: 42 } },
      'host-b': { status: 'unavailable', age_seconds: 0 }, 'host-c': { status: 'stale', observed_at: at(400), age_seconds: 400, cpu_count: 2, loadavg: [1] } } },
    workers: { counts: { live: 99, workers_total: 4, skipped: 2 }, hosts: [
      { host_id: 'host-a', freshness: 'fresh', workers_status: 'reported', age_s: 5, workers: [{ id: 'worker-a', agent: 'agent-a', harness: 'native', kind: 'delegate', state: 'live', age_s: 6 }] },
      { host_id: 'host-b', freshness: 'stale', workers_status: 'reported', age_s: 400, workers: [{ id: 'worker-b', state: 'live', age_s: 4 }] },
      { host_id: 'unattributed', freshness: 'fresh', workers_status: 'reported', workers: [{ id: 'worker-c', state: 'live' }] },
      { host_id: 'host-c', freshness: 'unknown', workers_status: 'unreported', workers: [{ id: 'worker-d', state: 'starting' }] },
    ] },
    tasks: { total: 22, tasks: ['running','spawning','done','failed','timeout','rate_limited','cancelled','crashed','needs_finalize','no_deliverable','dry_run'].map((status,i) => ({task_id: 'task-' + i, status})) },
    slots: { schema: 'test-slots.status.v1', enabled: true, pool_size: 2, slots_in_use: 2, slots_free: 0, queue_depth: 0, error: null },
    accounts: { claude_accounts: { 'claude:a': {status: 'ok', updated: at(10), session5h: {left_pct: 0, pace: 'on pace'}, weekly: {left_pct: 40}}, 'claude:b': {status: 'unknown', reason: 'account_ambiguous', updated: null, session5h: {left_pct: 99}} } },
    proposals: { pending: [{ source_module: 'Sample proposal', root_cause_summary: 'A proposal is not an operator decision', queued_at: at(40) }], count: 1 },
    messages: { messages: [], availability: 'available', total: 5 },
    prs: envelope('prs', { prs: [{number:17, repo:'sample/repo', title:'Sample PR', head_sha:'head-old', cf:{verdict:'APPROVE',at_head:true}, ci:'green', gate:'green', mq:'queued', owner_lane:'branch-derived', keeper:{hold:false}, blocker:{kind:'none'}}] }, [source('github','ok'),source('mq_state','ok')]),
    alerts: envelope('alerts', { alerts: [{ name: 'Sample alert', state: 'active', severity:'warning', summary:'Check sample', starts_at:at(50) }] }),
    backups: envelope('backups', {age_h:0, stale:false, last_result:{at:at(60),status:'success'}, restore_test:null}),
    downloads: envelope('downloads', {state:'ok',items:[{source:'unlisted',state:'active',done:1,total:null,pct:100,last_progress_at:null,stalled:null},{source:'unlisted',state:'active',done:2,total:10,pct:20,last_progress_at:at(600),stalled:true}]}),
    stats: envelope('stats', {stats:[{name:'sample count',value:0,status:'ok'},{name:'sample unavailable',value:99,status:'unavailable'}],by_repo:[{repo:'sample/repo',backlog:0,days:[]}],by_lane:[]},[source('stats','ok'),source('stale_prs','not_configured')]),
    links: envelope('links', {links:[{name:'Overview',href:'javascript:bad()'}]}),
  };
}
function sampleReads() {
  return Object.fromEntries(Object.entries(sampleBodies()).map(([key,body]) => [key, FB.readResult(key,body,'',null,NOW)]));
}
function operator(reads = sampleReads(), view = 'home', params = '') {
  return FB.renderOperator(reads, {view, params:new URLSearchParams(params)}, NOW);
}

test('Q01-Q14 render registry, task denominators, governor, account windows and named missing obligations', () => {
  const out = operator();
  for (const label of ['Needs attention','Lanes and drivers','Workers','Host and test capacity','Account capacity','PR pipeline','Ops',
    'Cedar registry','Unregistered stream','driver-a / task-a','Recorded state','Recorded decision','2 streams known to the session store',
    '11 loaded tasks of 22','Pool 2; occupied 2; free 0; queued 0','claude:a','claude:b','0%',
    'D02','D03','D04','D05','D11-AL','D11-BA','D11-DL','D11-ST','D11-LI','D12','D13','RETAIN-02']) assert.ok(out.includes(label),label);
  for (const status of sampleBodies().tasks.tasks.map(t => t.status)) assert.ok(out.includes(status), status);
  assert.doesNotMatch(out,/Nothing needs|no blockers|later slice|working from active/);
  assert.match(out,/proposals, not confirmed operator decisions/);
  assert.match(out,/No rows returned; coverage\/age unknown/);
});

test('P02 counts final fresh reporting hosts and excludes stale, unreported and unattributed live states', () => {
  const result = FB.workerBuckets(sampleBodies().workers);
  assert.equal(result.counts.live,1);
  assert.equal(result.counts.fresh,1);
  assert.equal(result.counts.stale,1);
  assert.equal(result.counts.unknown,1);
  assert.equal(result.counts.unreported,1);
  const out = operator(sampleReads(),'workers');
  assert.match(out,/1 observed live workers/);
  assert.doesNotMatch(out,/99 observed live/);
  assert.match(out,/last observed: live/);
  assert.match(out,/reported total 4; skipped 2/);
});

test('P03-P05 distinguish unavailable age zero, real zero slots, disabled governor and ambiguous accounts', () => {
  let reads = sampleReads();
  let out = operator(reads,'capacity');
  const unavailable = textContent(parseHtml(out)).split('host-b')[1].split('host-c')[0];
  assert.match(unavailable,/unavailable \/ unknown/);
  assert.doesNotMatch(unavailable,/0 s/);
  const accountB = textContent(parseHtml(out)).split('claude:b')[1];
  assert.doesNotMatch(accountB,/99%/);
  reads.slots = FB.readResult('slots',{...sampleBodies().slots,enabled:false},'',null,NOW);
  assert.match(operator(reads,'capacity'),/Governor disabled/);
  reads.slots = FB.readResult('slots',{...sampleBodies().slots,error:{reason:'unavailable'}},'',null,NOW);
  assert.match(operator(reads,'capacity'),/governor read failed/);
  assert.equal(FB.elapsedSeconds(at(-1),NOW),null);
  assert.equal(FB.elapsedSeconds('invalid',NOW),null);
  assert.equal(FB.advancedAge(20,NOW,NOW+5000),25);
  assert.equal(FB.advancedAge(null,NOW,NOW),null);
});

test('P06-P08 keep old-head approval unknown and qualify each PR source independently', () => {
  let reads = sampleReads();
  let out = operator(reads,'prs');
  assert.match(out,/CF unknown; Work review APPROVED is not exact-head approval/);
  assert.match(out,/branch-derived; provenance unverified/);
  assert.match(out,/Work PR flags carry no blocker evidence/);
  assert.doesNotMatch(out,/CF APPROVE at observed head/);
  reads.prs.body.data.prs[0].head_sha='head-new';
  assert.match(operator(reads,'prs'),/CF APPROVE at observed head/);
  reads.prs.body.sources[0].status='unavailable';
  out = operator(reads,'prs');
  assert.match(out,/Partial \/ unavailable source/);
  assert.match(out,/Sample PR/);
  assert.doesNotMatch(out,/CF APPROVE at observed head/);
  reads.work.body.items[0].authority[0].stale=true;
  assert.doesNotMatch(operator(reads,'prs'),/Work review APPROVED/);
});

test('P09-P14 separate posted obligations, restore proof, unknown total, event clocks and withheld destinations', () => {
  const out = operator();
  assert.match(out,/Posted blockers and confirmed operator decisions require a safe typed projection/);
  assert.match(out,/Restore test unknown; restore event age unknown/);
  assert.equal((out.match(/Unidentified download \(D12\)/g)||[]).length,2);
  assert.match(out,/1 \/ unknown total/);
  assert.match(out,/PR throughput unknown/);
  assert.match(out,/Destination unavailable: boundary approval unknown/);
  assert.doesNotMatch(out,/javascript:bad|href="javascript|100%/);
  const doc=parseHtml(out);
  const badStat=textContent(doc).split('sample unavailable')[1].split('PR throughput')[0];
  assert.doesNotMatch(badStat,/99/);
});

test('response boundary separates malformed success, valid empty, partial rows and retained failed observations', () => {
  const bodies=sampleBodies();
  for (const [key,body] of Object.entries(bodies)) {
    assert.equal(FB.validRead(key,body),true,key);
    const invalid=FB.readResult(key,{},'',null,NOW);
    assert.equal(invalid.body,null,key);
    assert.match(invalid.error,/Malformed/);
  }
  const old=FB.readResult('registry',bodies.registry,'',null,NOW-10000);
  const failed=FB.readResult('registry',null,'Request failed',old,NOW);
  assert.equal(failed.body,old.body);
  assert.equal(failed.fetchedAt,NOW-10000);
  const empty=FB.readResult('registry',{streams:[]},'',old,NOW);
  assert.equal(empty.error,'');
  assert.equal(empty.body.streams.length,0);
  assert.match(operator({registry:failed}),/retained historical observation/);
  assert.match(operator({registry:empty}),/0 streams known to the session store/);
  const partial=FB.readResult('registry',{streams:[null,bodies.registry.streams[0]]},'',null,NOW);
  assert.equal(partial.omitted,1);
  assert.match(operator({registry:partial}),/Partial: 1 malformed rows omitted/);
  assert.match(operator({registry:partial}),/Cedar registry/);
  const broken=FB.readResult('registry',{streams:[null]},'',null,NOW);
  assert.match(broken.error,/Malformed/);
});

test('untrusted metadata never creates elements, attributes, handlers or destinations', () => {
  const reads=sampleReads();
  const attack='"><img src=x onerror=bad()>';
  reads.registry.body.streams[0].title=attack;
  reads.registry.body.streams[0].stream_id=attack;
  reads.work.body.items[0].title=attack;
  reads.alerts.body.data.alerts[0].summary=attack;
  const out=operator(reads);
  assert.match(out,/&lt;img/);
  assert.doesNotMatch(out,/<img|href="javascript|<script/);
  for (const node of queryAll(parseHtml(out),'fb-panel')) {
    assert.ok(node.attrs['data-read']);
    assert.match(textContent(node),/Source age unknown/);
    assert.match(textContent(node),/Last successful fetch/);
  }
  assert.ok(!Object.values(FB.READS).some(p=> /fresh=true|agent-monitor\/status/.test(p)));
});

test('each navigation view remains usable and explicitly identifies its unavailable sources', () => {
  for (const view of ['attention','workers','capacity','prs','ops']) {
    const loading=operator({},view);
    assert.match(loading,/Loading/);
    assert.match(loading,/aria-busy="true"/);
    const reads=sampleReads();
    reads.alerts.body.sources[0].status='not_configured';
    assert.doesNotMatch(operator(reads,view),/later slice/);
  }
  assert.match(operator(sampleReads(),'ops'),/Partial \/ not installed source/);
});

const indexHtml = fs.readFileSync(path.join(root,'dashboards/index.html'),'utf8');
const indexScript = [...indexHtml.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join('\n');
function mountedIndex() {
  const nodes=new Map();
  for (const match of indexHtml.matchAll(/id="([^"]+)"/g)) nodes.set(match[1],{
    textContent:'',innerHTML:'',hidden:false,attrs:{},events:{},
    setAttribute(k,v){this.attrs[k]=v;},addEventListener(k,f){this.events[k]=f;},
  });
  const overrides={};
  const sandbox={document:{getElementById:id=>nodes.get(id)||null},location:{host:'sample.test'},
    AbortController,setTimeout,clearTimeout,Date,URLSearchParams,console,
    async fetch(url){
      const value=url in overrides ? overrides[url] : null;
      if(value instanceof Error || value===null) throw new Error('Synthetic unavailable source');
      return {ok:true,async text(){return JSON.stringify(value);}};
    },
  };
  vm.createContext(sandbox);
  vm.runInContext(indexScript,sandbox);
  return {nodes,overrides,sandbox,eval:code=>vm.runInContext(code,sandbox),async settle(){await new Promise(setImmediate);}};
}

test('R11 directory exposes all 21 content workflows including home and map', () => {
  const pages=['index','fleet-board','acp','admin','artifacts','build-events','consultation','cost','curriculum-dashboard',
    'delegate','epics-map','epics','fleet','image-explorer','orient','progress','quality','routing','runtime','wiki','work'];
  for (const page of pages) assert.match(indexHtml,page==='index' ? /href="\/"/ : new RegExp('href="/' + page + '\\.html'));
});

test('R11 task summaries retain every attention state and count only done as successful completion', async () => {
  const page=mountedIndex();await page.settle();
  const statuses=['running','spawning','done','failed','timeout','rate_limited','cancelled','crashed','needs_finalize','dry_run','no_deliverable'];
  page.sandbox.testTasks=statuses.map((status,i)=>({task_id:'task-'+i,status,started_at:new Date().toISOString()}));
  const out=page.eval('taskSummary(testTasks,30)');
  assert.match(out,/2 active · 1 done · 8 attention/);
  assert.match(out,/1 finished today · 11 loaded \/ 30 total/);
  for(const status of statuses.slice(3)) assert.ok(out.includes(status),status);
  assert.match(page.nodes.get('card-stat-delegate').textContent,/Unavailable/);
});

test('R11 independent source failure, malformed success, missing numerics and contracts injection stay honest', async () => {
  const page=mountedIndex(); await page.settle();
  page.overrides['/api/runtime/agents']={agents:[{agent:'sample'}]};
  page.overrides['/api/delegate/tasks?limit=100']={};
  page.overrides['/api/analytics/cost']={windows:{}};
  page.overrides['/api/contracts/routes']={route_contracts:[{source_of_truth:'<img src=x onerror=bad()>'}],page_contracts:[]};
  await page.eval('loadStats()');await page.settle();
  assert.match(page.nodes.get('card-stat-runtime').textContent,/1 agents/);
  assert.match(page.nodes.get('card-stat-delegate').textContent,/Malformed success response/);
  assert.match(page.nodes.get('card-stat-cost').textContent,/Cost unknown/);
  assert.match(page.nodes.get('api-surfaces').textContent,/<img/);
  assert.equal(page.nodes.get('api-surfaces').innerHTML,'');
  assert.equal(page.eval('sumDashboardTotals([{module_count:1,stats:{}}]).published'),'unknown');
  assert.equal(page.eval('buildStateSummary({current_builds:2},null).backlog'),null);
  assert.equal(page.eval('validSummary("/api/runtime/agents", {agents:42})'),false);
  assert.equal(page.nodes.get('stats-row').attrs['aria-busy'],'false');
});

test('P05 provider windows remain separate from account attribution and never use fleet burn as quota',()=>{
  const reads=sampleReads();
  reads.accounts.body.agents={codex:{codexbar:{freshness:'fresh',age_s:20,windows:{primary:{used_pct:0,remaining_pct:100,resets_at:at(-50)}}}},
    cursor:{remaining_pct:77,burn_pct_7d:23,codexbar:{freshness:'unavailable',weekly_remaining_pct:99}}};
  const out=operator(reads,'capacity');
  assert.match(out,/Provider meters; account attribution and shared-meter parity unverified/);
  assert.match(out,/100%/);
  assert.doesNotMatch(out,/77%|99%/);
  assert.match(out,/never summed or counted as separate accounts/);
});

test('mounted registry-only detail survives absent roster and failed sibling reads', async()=>{
  const board=mountedBoard();await board.settle();
  for (const [key,body] of Object.entries(sampleBodies())) board.overrides[FB.READS[key]]=body;
  board.overrides['/api/fleet/v1/epics/cedar']={schema:'fleet.v1.epic',sources:[source('roster_snapshot','not_configured')],data:null};
  await board.navigate('#/epic/cedar');
  const app=board.nodes.get('fb-app');
  assert.match(app.innerHTML,/Selected session-store stream/);
  assert.match(app.innerHTML,/Cedar registry/);
  assert.match(app.innerHTML,/Optional board detail unavailable/);
  await board.navigate('#/capacity');
  assert.match(app.innerHTML,/Pool 2; occupied 2; free 0; queued 0/);
  board.overrides[FB.READS.slots]={};
  board.intervals.get(30000)();await board.settle();
  assert.match(app.innerHTML,/Malformed success response; retained historical observation/);
  assert.match(app.innerHTML,/claude:a/);
});

test('R11 pipeline count strings cannot enter the module stat HTML',async()=>{
  const page=mountedIndex();await page.settle();
  assert.equal(page.eval('displayBuildCount("<img src=x onerror=bad()>")'),'unknown');
  assert.equal(page.eval('displayBuildCount(0)'),'0');
  assert.equal(page.eval('validSummary("/api/state/summary",{tracks:{sample:null}})'),false);
});

test('P08 non-unknown Work fields without canonical PR association cannot certify owner or stream',()=>{
  const reads=sampleReads();
  const p=reads.work.body.items[0].projections;
  p.dispatch.accountable_owner='unverified-owner';
  p.stream={status:'ok',fresh:true,authority_missing:false,streams:['unverified-stream']};
  const out=operator(reads,'prs');
  assert.doesNotMatch(out,/unverified-owner|unverified-stream/);
  assert.match(out,/canonical PR association unavailable/);
  assert.match(out,/canonical PR membership unavailable/);
});

test('refresh keeps a focused card or table row at its visible position until focus leaves',()=>{
  const row={id:'cedar'}, first={id:'birch'}, second={id:'aspen'};
  const parent={children:[first,second,row],insertBefore(child,before){
    this.children=this.children.filter(el=>el!==child);
    this.children.splice(before ? this.children.indexOf(before) : this.children.length,0,child);
  }};
  row.parentElement=parent;
  const element={closest:()=>row};
  FB.preserveFocusedRow(element,0);
  assert.deepEqual(parent.children.map(el=>el.id),['cedar','birch','aspen']);
  FB.preserveFocusedRow(element,1);
  assert.deepEqual(parent.children.map(el=>el.id),['birch','cedar','aspen']);
  FB.preserveFocusedRow(element,-1);
  assert.deepEqual(parent.children.map(el=>el.id),['birch','cedar','aspen']);
  assert.doesNotThrow(()=>FB.preserveFocusedRow(null,0));
});

test('duplicate task destinations and source retries have distinct focus identities',()=>{
  const out=operator();
  for(const task of sampleBodies().tasks.tasks) assert.ok(out.includes('data-focus-key="task:'+task.task_id+'"'));
  assert.match(out,/data-focus-key="work:Derived impediments"/);
  assert.match(out,/data-focus-key="work:Public PR observations"/);
  assert.match(out,/data-focus-key="pr:sample\/repo:17"/);
});

test('source disclosure focus identity is scoped to its panel',()=>{
  const out=operator();
  assert.match(out,/<summary data-focus-key="source:work:Derived impediments">Source qualifications/);
  assert.match(out,/<summary data-focus-key="source:work:Public PR observations">Source qualifications/);
});

test('board cards distinguish their focus from registry links to the same epic',()=>{
  const out=FB.cardHtml(cedar);
  assert.match(out,/data-focus-key="board:cedar"/);
  assert.match(out,/href="#\/epic\/cedar"/);
});
