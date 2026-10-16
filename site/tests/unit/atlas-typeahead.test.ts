// @vitest-environment happy-dom
import { afterEach, describe, expect, test, vi } from "vitest";
import { fireEvent, waitFor } from "@testing-library/react";
import { bindAtlasTypeaheads } from "@site/src/lib/lexicon/atlas-typeahead";
import type { SearchRow, SearchAlias, SearchShardManifest } from "@site/src/lib/lexicon/search";

const rows: SearchRow[] = [
  { l: "Alpha", s: "alpha", r: "alpha", g: "first", t: "lemma" },
  { l: "Alpine", s: "alpine", r: "alpine", g: null, t: "expression" },
];
const aliases: SearchAlias[] = [{ a: "redirect", s: "alpha", k: "form", h: "Alpha" }];
const shard = { path: "/lexicon/shard-a.json", count: 2, bytes: 1, sha256: "fixture" };
const manifest: SearchShardManifest = {
  schema: "atlas-search-shards", schemaVersion: 1, total: 2,
  fullIndex: shard, shardCount: 1, prefixMap: { a: "a" }, shards: { a: shard },
};
const disposers: Array<() => void> = [];
function widget(id = "one") {
  const host = document.createElement("div");
  host.innerHTML = `<div data-atlas-typeahead><input id="${id}-input" role="combobox" aria-controls="${id}-list" aria-expanded="false" data-atlas-typeahead-input><ul id="${id}-list" role="listbox" hidden data-atlas-typeahead-list></ul></div>`;
  document.body.append(host);
  const input = host.querySelector("input");
  const list = host.querySelector("ul");
  if (!input || !list) throw new Error("missing test widget");
  return { host, input, list };
}
function bind(host: ParentNode | null) {
  const dispose = bindAtlasTypeaheads(host);
  disposers.push(dispose);
  return dispose;
}
function serve(options: { manifestFails?: boolean; shardRows?: SearchRow[]; shardFails?: boolean; aliasesFail?: boolean; fullFails?: boolean } = {}) {
  const fetcher = vi.fn(async (input: RequestInfo | URL) => {
    const path = String(input);
    if (path.endsWith("search-shards.json")) return new Response(JSON.stringify(manifest), { status: options.manifestFails ? 503 : 200 });
    if (path.endsWith("search-aliases.json")) return new Response(JSON.stringify(aliases), { status: options.aliasesFail ? 503 : 200 });
    if (path.endsWith("search-index.json")) return new Response(JSON.stringify(rows), { status: options.fullFails ? 503 : 200 });
    return new Response(JSON.stringify(options.shardRows ?? rows), { status: options.shardFails ? 503 : 200 });
  });
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}
async function search(input: HTMLInputElement, value = "al") {
  fireEvent.input(input, { target: { value } });
  await waitFor(() => expect(input.parentElement?.querySelectorAll("a")).toHaveLength(2));
}
afterEach(() => {
  disposers.splice(0).forEach((dispose) => dispose());
  document.body.innerHTML = "";
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
describe("shared Atlas typeahead", () => {
  test("renders ranked links, pointer and arrow navigation, exact Enter and two-stage Escape", async () => {
    serve();
    const { host, input, list } = widget();
    const navigate = vi.spyOn(window.location, "assign").mockImplementation(() => {});
    bind(host);
    await search(input);
    expect(Array.from(list.querySelectorAll("a"), (a) => a.getAttribute("href"))).toEqual(["/lexicon/alpha/", "/lexicon/alpine/"]);
    expect(list.textContent).toContain("first");
    fireEvent.keyDown(input, { key: "Enter" });
    expect(navigate).toHaveBeenLastCalledWith("/lexicon/alpha/");
    fireEvent.keyDown(input, { key: "ArrowUp" });
    expect(input.getAttribute("aria-activedescendant")).toBe("one-list-option-1");
    fireEvent.keyDown(input, { key: "Enter" });
    expect(navigate).toHaveBeenLastCalledWith("/lexicon/alpine/");
    fireEvent.keyDown(input, { key: "ArrowDown" });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(navigate).toHaveBeenLastCalledWith("/lexicon/alpha/");
    const link = list.querySelector("a");
    if (!link) throw new Error("missing result");
    fireEvent.mouseDown(link);
    fireEvent.click(link);
    expect(navigate).toHaveBeenCalledTimes(4);
    fireEvent.keyDown(input, { key: "Escape" });
    expect(list.hidden).toBe(true);
    expect(input.value).toBe("al");
    fireEvent.keyDown(input, { key: "Escape" });
    expect(input.value).toBe("");
    fireEvent.input(input, { target: { value: "alpha" } });
    await waitFor(() => expect(list.querySelectorAll("a")).toHaveLength(1));
    fireEvent.keyDown(input, { key: "Enter" });
    expect(navigate).toHaveBeenLastCalledWith("/lexicon/alpha/");
    fireEvent.input(input, { target: { value: "" } });
    expect(list.hidden).toBe(true);
  });
  test.each([{ manifestFails: true }, { shardFails: true }, { shardRows: [] }])("full-index fallback %j", async (options) => {
    const fetcher = serve(options);
    const { host, input } = widget();
    bind(host);
    await search(input);
    expect(fetcher).toHaveBeenCalledWith("/lexicon/search-index.json");
  });
  test("aliases resolve to articles; repeated queries use cached rows", async () => {
    const fetcher = serve();
    const { host, input, list } = widget();
    bind(host);
    fireEvent.focus(input);
    await search(input);
    fireEvent.input(input, { target: { value: "redirect" } });
    await waitFor(() => expect(list.querySelectorAll("a")).toHaveLength(1));
    expect(list.querySelector("a")?.getAttribute("href")).toBe("/lexicon/alpha/");
    expect(list.querySelector('[data-kind="alias"]')).not.toBeNull();
    await search(input);
    expect(fetcher.mock.calls.filter(([path]) => path === "/lexicon/shard-a.json")).toHaveLength(1);
    fireEvent.input(input, { target: { value: "zzz" } });
    await waitFor(() => expect(list.textContent).toContain("Нічого не знайдено"));
    fireEvent.click(document.body);
    expect(list.hidden).toBe(true);
  });
  test("failed full index and aliases yield empty results", async () => {
    serve({ manifestFails: true, aliasesFail: true, fullFails: true });
    const { host, input, list } = widget();
    bind(host);
    fireEvent.focus(input);
    fireEvent.input(input, { target: { value: "al" } });
    await waitFor(() => expect(list.textContent).toContain("Нічого не знайдено"));
    expect(list.querySelector("a")).toBeNull();
  });
  test("repeated binding keeps one owner and cleanup permits remount", async () => {
    serve();
    const { host, input, list } = widget();
    const navigate = vi.spyOn(window.location, "assign").mockImplementation(() => {});
    const dispose = bind(host);
    bind(host)();
    await search(input);
    fireEvent.keyDown(input, { key: "ArrowDown" });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(navigate).toHaveBeenCalledTimes(1);
    dispose();
    dispose();
    fireEvent.input(input, { target: { value: "al" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(list.hidden).toBe(true);
    expect(navigate).toHaveBeenCalledTimes(1);
    bind(host);
    await search(input);
    fireEvent.keyDown(input, { key: "ArrowDown" });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(navigate).toHaveBeenCalledTimes(2);
  });
  test.each(["dispose", "escape", "outside", "clear", "new-query"])("late responses cannot overwrite %s", async (action) => {
    let release: (response: Response) => void = () => {};
    const pending = new Promise<Response>((resolve) => { release = resolve; });
    const normal = serve();
    vi.stubGlobal("fetch", vi.fn((path: RequestInfo | URL) => String(path).endsWith("search-index.json") ? pending : normal(path)));
    const { host, input, list } = widget();
    const dispose = bind(host);
    fireEvent.focus(input);
    fireEvent.input(input, { target: { value: "zzz" } });
    await waitFor(() => expect(normal).toHaveBeenCalledWith("/lexicon/search-aliases.json"));
    if (action === "dispose") dispose();
    if (action === "escape") fireEvent.keyDown(input, { key: "Escape" });
    if (action === "outside") fireEvent.click(document.body);
    if (action === "clear") fireEvent.input(input, { target: { value: "" } });
    if (action === "new-query") await search(input);
    release(new Response(JSON.stringify(rows)));
    await pending;
    await new Promise((resolve) => setTimeout(resolve, 20));
    if (action === "new-query") expect(list.querySelectorAll("a")).toHaveLength(2);
    else expect(list.innerHTML).toBe("");
  });
  test("independent widgets keep separate results, active IDs and ownership", async () => {
    serve();
    const first = widget();
    const second = widget();
    const disposeFirst = bind(first.host);
    bind(second.host);
    await search(first.input);
    await search(second.input);
    fireEvent.keyDown(second.input, { key: "ArrowUp" });
    expect(second.input.getAttribute("aria-activedescendant")).toBe(`${second.list.id}-option-1`);
    expect(first.input.hasAttribute("aria-activedescendant")).toBe(false);
    disposeFirst();
    expect(second.list.querySelectorAll("a")).toHaveLength(2);
    fireEvent.click(second.input);
    expect(second.list.hidden).toBe(false);
  });
  test("invalid network records cannot become results; invalid manifest uses full-index fallback", async () => {
    vi.stubGlobal("fetch", async (path: RequestInfo | URL) => {
      const value = String(path).endsWith("search-shards.json") ? { schema: "unexpected" }
        : String(path).endsWith("search-aliases.json") ? [null, { a: "al" }, ...aliases]
        : [null, { l: "bad" }, { ...rows[0], t: 7 }, ...rows];
      return new Response(JSON.stringify(value));
    });
    const { host, input, list } = widget();
    bind(host);
    await search(input);
    expect(Array.from(list.querySelectorAll("a"), (a) => a.getAttribute("href"))).toEqual(["/lexicon/alpha/", "/lexicon/alpine/"]);
  });

  test("result content is escaped and article slugs are URL encoded", async () => {
    const row = { l: '<alpha & "quoted">', s: 'alpha/"&', r: "alpha", g: "<img src=x>", t: "<custom>" };
    serve({ shardRows: [row] });
    const { host, input, list } = widget();
    bind(host);
    fireEvent.input(input, { target: { value: "alpha" } });
    await waitFor(() => expect(list.querySelectorAll("a")).toHaveLength(1));
    expect(list.querySelector("a")?.getAttribute("href")).toBe("/lexicon/alpha%2F%22%26/");
    expect(list.textContent).toContain(row.l);
    expect(list.querySelector("img")).toBeNull();
    expect(list.querySelector('[data-kind="<custom>"]')).not.toBeNull();
  });

  test("a pending focus initializer cannot reopen a disposed or rebound widget", async () => {
    let release: (response: Response) => void = () => {};
    const pending = new Promise<Response>((resolve) => { release = resolve; });
    const normal = serve();
    vi.stubGlobal("fetch", (path: RequestInfo | URL) => String(path).endsWith("search-shards.json") ? pending : normal(path));
    const { host, input, list } = widget();
    const dispose = bind(host);
    input.value = "al";
    fireEvent.focus(input);
    dispose();
    bind(host);
    release(new Response(JSON.stringify(manifest)));
    await pending;
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(list.hidden).toBe(true);
    await search(input);
  });

  test("null hosts and incomplete widgets are harmless", () => {
    bind(null)();
    const host = document.createElement("div");
    host.innerHTML = "<div data-atlas-typeahead></div>";
    bind(host)();
    expect(host.querySelector("[data-atlas-typeahead-ready]")).toBeNull();
  });
});
