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
vm.runInContext(js, context);
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
    [/github\.com/i, "github"],
    [/\/home\//, "home path"],
    [/\/Users\//, "users path"],
    [/\/tmp\//, "tmp path"],
    [/tmux/i, "tmux"],
  ];
  patterns.forEach(([pattern, name]) => {
    assert.doesNotMatch(text, pattern, `${label} contains ${name}`);
  });
}

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
  assert.equal(tiles.length, 12);
  tiles.forEach((tile) => {
    assert.match(textContent(tile), /\?/);
    assert.doesNotMatch(textContent(tile), /0/);
  });
  assert.match(rendered, /Harness health: not installed/);
  assert.match(rendered, /not installed/);
  assert.match(rendered, /A source is stale/);
  assert.match(rendered, /Values below may be out of date/);
  assert.match(rendered, /Dependency layers/);
  assert.match(rendered, /Routing budget and pace/);
  assert.match(rendered, /later slice/);
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

test("unknown harness values stay unknown and a real zero stays zero", () => {
  assert.equal(FB.metricText(null, "%"), "?");
  assert.equal(FB.metricText(undefined, " m"), "?");
  assert.equal(FB.metricText(0, " m"), "0 m");
  assert.equal(FB.metricText(0, "%"), "0%");
  const rendered = FB.harnessTiles({
    context_pct: null,
    compactions: null,
    stop_to_ask_count: null,
    idle_min: 0,
  });
  const doc = parseHtml(rendered);
  const idle = queryAll(doc, "fb-tile").find((el) => el.attrs["data-metric"] === "idle");
  const context = queryAll(doc, "fb-tile").find((el) => el.attrs["data-metric"] === "context");
  assert.match(textContent(idle), /0 m/);
  assert.match(textContent(context), /\?/);
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

test("the PR view stays a placeholder", () => {
  const rendered = FB.renderPrs(new URLSearchParams("pr=17"), sources, { ageMs: 1000 });
  const doc = parseHtml(rendered);
  assert.match(textContent(doc), /PR pipeline/);
  assert.match(textContent(doc), /Selected PR #17/);
  assert.match(textContent(doc), /not installed/);
  assert.match(textContent(doc), /later slice/);
  assert.match(rendered, /A source is stale/);
});

test("shipped files and the fixture carry no hosts, absolute urls, or session names", () => {
  assertClean(html, "html");
  assertClean(css, "css");
  assertClean(js, "js");
  assertClean(JSON.stringify({ nowEnvelope, epicsEnvelope, agentsEnvelope }), "fixture");
});
