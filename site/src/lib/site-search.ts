import {
  isSearchRow,
  isShardManifest,
  rankMatches,
  searchShardForQuery,
  type SearchRow,
  type SearchShardManifest,
} from "./lexicon/search";

/**
 * Site-wide `/search/` page (#12984).
 *
 * Page items (tracks, lessons, readings) are built into the page. Word Atlas
 * entries come from the same static prefix shards the Atlas typeahead reads
 * (`/lexicon/search-shards.json` + `/lexicon/search/<shard>.json`), so every
 * approved article is searchable without shipping the whole index.
 */
export interface SiteSearchItem {
  title: string;
  href: string;
  type: string;
  track: string;
  text: string;
}

export const PAGE_RESULT_LIMIT = 24;
export const ATLAS_RESULT_LIMIT = 12;
export const SUGGESTED_LIMIT = 9;

type Fetch = (input: string) => Promise<Pick<Response, "ok" | "status" | "json">>;

const SEARCH_I18N = {
  en: {
    resultsFor: "Results for",
    suggested: "Suggested Pages",
    match: "match",
    matches: "matches",
    matchesInIndex: "in the static learner index.",
    noPagesMatched: "No pages matched this query.",
    hint: "Start with a broad query or use the shortcuts.",
  },
  uk: {
    resultsFor: "Результати для",
    suggested: "Рекомендовані сторінки",
    match: "збіг",
    matches: "збігів",
    matchesInIndex: "у статичному покажчику курсу.",
    noPagesMatched: "Немає сторінок за цим запитом.",
    hint: "Почніть із загального запиту або скористайтеся посиланнями.",
  },
} as const;

const normalizePageText = (value: unknown) => String(value ?? "").toLocaleLowerCase("uk");

/** Substring match over the page items built into `/search/`. */
export function matchPages(items: SiteSearchItem[], query: string, limit = PAGE_RESULT_LIMIT): SiteSearchItem[] {
  const q = normalizePageText(query).trim();
  if (!q) return [];
  return items
    .filter((item) => normalizePageText(`${item.title} ${item.text} ${item.type} ${item.track}`).includes(q))
    .slice(0, limit);
}

/** Rank Atlas rows with the Atlas typeahead's own matcher and map them to result links. */
export function atlasItems(rows: SearchRow[], query: string, limit = ATLAS_RESULT_LIMIT): SiteSearchItem[] {
  return rankMatches(rows, query.trim(), limit).map((row) => ({
    title: row.l,
    href: `/lexicon/${encodeURIComponent(row.s)}/`,
    type: "Word Atlas",
    track: row.c ?? "Atlas",
    text: row.g ?? "",
  }));
}

/**
 * Load the Atlas rows that can match `query`: the manifest once, then the one
 * shard for the query's first normalized character. A query whose first
 * character has no shard (for example "(чайний) сервіз") reads the full index,
 * as the Atlas typeahead does. Failed fetches reject and are not cached, so the
 * next query retries.
 */
export function createAtlasRowLoader(fetchImpl: Fetch): (query: string) => Promise<SearchRow[]> {
  let manifest: Promise<SearchShardManifest> | null = null;
  const shards = new Map<string, Promise<SearchRow[]>>();

  const loadManifest = () => {
    manifest ??= fetchImpl("/lexicon/search-shards.json")
      .then(async (response) => {
        if (!response.ok) throw new Error(`search shard manifest fetch failed: ${response.status}`);
        const data: unknown = await response.json();
        if (!isShardManifest(data)) throw new Error("invalid search shard manifest");
        return data;
      })
      .catch((error: unknown) => {
        manifest = null;
        throw error;
      });
    return manifest;
  };

  return async (query: string) => {
    const loaded = await loadManifest();
    const shard = searchShardForQuery(loaded, query) ?? loaded.fullIndex;
    let rows = shards.get(shard.path);
    if (!rows) {
      rows = fetchImpl(shard.path)
        .then(async (response) => {
          if (!response.ok) throw new Error(`search shard fetch failed: ${response.status}`);
          const data: unknown = await response.json();
          return Array.isArray(data) ? data.filter(isSearchRow) : [];
        })
        .catch((error: unknown) => {
          shards.delete(shard.path);
          throw error;
        });
      shards.set(shard.path, rows);
    }
    return rows;
  };
}

const escapeHtml = (value: unknown) =>
  String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

/** Bind the `/search/` page: page matches render at once, Atlas matches when their shard arrives. */
export function initSiteSearch(root: HTMLElement | null, fetchImpl: Fetch = (input) => fetch(input)): void {
  if (!root) return;
  const input = root.querySelector<HTMLInputElement>("#course-search");
  const form = root.querySelector("form");
  const results = root.querySelector<HTMLElement>("[data-search-results]");
  const count = root.querySelector<HTMLElement>("[data-search-count]");
  const heading = root.querySelector<HTMLElement>("[data-search-heading]");
  const empty = root.querySelector<HTMLElement>("[data-search-empty]");
  const error = root.querySelector<HTMLElement>("[data-search-error]");
  const loading = root.querySelector<HTMLElement>("[data-search-loading]");
  const itemsJson = root.querySelector("[data-search-items]")?.textContent ?? "[]";
  if (!results || !count || !heading || !empty || !error || !loading) return;

  const items = JSON.parse(itemsJson) as SiteSearchItem[];
  const params = new URLSearchParams(window.location.search);
  const loadAtlasRows = createAtlasRowLoader(fetchImpl);
  const strings = () => SEARCH_I18N[document.documentElement.dataset.chromeLocale === "uk" ? "uk" : "en"];
  let request = 0;

  const paint = (query: string, matches: SiteSearchItem[], pending: boolean) => {
    const s = strings();
    const q = query.trim();
    loading.hidden = !pending || matches.length > 0;
    empty.hidden = pending || matches.length !== 0 || !q;
    heading.textContent = q ? `${s.resultsFor} "${query}"` : s.suggested;
    count.textContent = matches.length
      ? `${matches.length} ${matches.length === 1 ? s.match : s.matches} ${s.matchesInIndex}`
      : q && !pending
        ? s.noPagesMatched
        : q
          ? ""
          : s.hint;
    results.innerHTML = matches
      .map(
        (item) =>
          `<a href="${escapeHtml(item.href)}"><span>${escapeHtml(item.type)} · ${escapeHtml(item.track)}</span><strong>${escapeHtml(item.title)}</strong></a>`,
      )
      .join("");
  };

  const render = async (query: string) => {
    const current = ++request;
    error.hidden = params.get("state") !== "error";
    if (!error.hidden) {
      loading.hidden = true;
      return;
    }
    if (!query.trim()) {
      paint(query, items.slice(0, SUGGESTED_LIMIT), false);
      return;
    }
    const pages = matchPages(items, query);
    paint(query, pages, true);
    let atlas: SiteSearchItem[] = [];
    try {
      atlas = atlasItems(await loadAtlasRows(query), query);
    } catch {
      // Atlas shards unavailable: page results still stand on their own.
    }
    if (current === request) paint(query, [...pages, ...atlas], false);
  };

  if (input) {
    input.value = params.get("q") || "";
    input.addEventListener("input", () => void render(input.value));
  }
  form?.addEventListener("submit", (event) => {
    event.preventDefault();
    const query = input?.value || "";
    window.history.replaceState(null, "", query ? `/search/?q=${encodeURIComponent(query)}` : "/search/");
    void render(query);
  });
  void render(input?.value || "");
}
