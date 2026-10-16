import {
  normalize,
  rankSearchResults,
  highlight,
  searchShardForQuery,
  type SearchAlias,
  type SearchResult,
  type SearchRow,
  type SearchShardManifest,
} from "./search";
import {
  resolveTypeaheadEnterSelection,
  resolveTypeaheadEscapeAction,
} from "./atlas-typeahead-keys";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isSearchRow(value: unknown): value is SearchRow {
  return isRecord(value) && typeof value.l === "string" && typeof value.s === "string" &&
    (value.g === null || typeof value.g === "string") &&
    ["r", "k", "c", "cls", "t"].every((key) => value[key] === undefined || typeof value[key] === "string");
}

function isSearchAlias(value: unknown): value is SearchAlias {
  return isRecord(value) && ["a", "k", "s", "h"].every((key) => typeof value[key] === "string");
}

function isShardMeta(value: unknown): value is SearchShardManifest["fullIndex"] {
  return isRecord(value) && typeof value.path === "string" && typeof value.count === "number" &&
    typeof value.bytes === "number" && typeof value.sha256 === "string";
}

function isShardManifest(value: unknown): value is SearchShardManifest {
  return isRecord(value) && value.schema === "atlas-search-shards" && value.schemaVersion === 1 &&
    typeof value.total === "number" && typeof value.shardCount === "number" &&
    isShardMeta(value.fullIndex) && isRecord(value.prefixMap) && isRecord(value.shards) &&
    Object.values(value.prefixMap).every((key) => typeof key === "string") &&
    Object.values(value.shards).every(isShardMeta);
}

const EMPTY_MESSAGE = "Нічого не знайдено — спробуйте українською, латиницею або англійською";
const LOADING_MESSAGE = "Завантажуємо…";
const ENTRY_TYPE_LABELS: Record<string, string> = {
  lemma: "слово",
  expression: "вираз",
  phraseologism: "фразеологізм",
  proverb: "прислів'я",
  multiword_term: "термін",
  proper_name: "власна назва",
};

const taEsc = (value: unknown): string =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[c] ?? c,
  );

const closeList = (input: HTMLInputElement, list: HTMLUListElement) => {
  list.innerHTML = "";
  list.hidden = true;
  input.setAttribute("aria-expanded", "false");
  input.removeAttribute("aria-activedescendant");
};

const resultPills = (result: SearchResult): string => {
  if (result.matchedAlias) {
    return '<span class="ata-kind" data-kind="alias">форма</span>';
  }
  const entryType = result.article.t;
  const label = entryType ? ENTRY_TYPE_LABELS[entryType] : "стаття";
  return `<span class="ata-kind" data-kind="${taEsc(entryType ?? "article")}">${taEsc(label)}</span>`;
};

const initialized = new WeakSet<HTMLElement>();
let nextWidgetId = 0;

const initAtlasTypeahead = (ta: HTMLElement): (() => void) => {
  if (initialized.has(ta)) return () => {};

  const taInput = ta.querySelector<HTMLInputElement>("[data-atlas-typeahead-input]");
  const taList = ta.querySelector<HTMLUListElement>("[data-atlas-typeahead-list]");
  if (!taInput || !taList) return () => {};

  // React fallback markup can appear more than once in the same document.
  // Preserve SSR IDs unless this widget would refer to another widget's nodes.
  if (ta.ownerDocument.getElementById(taInput.id) !== taInput ||
      ta.ownerDocument.getElementById(taList.id) !== taList) {
    let id: string;
    do {
      id = `atlas-typeahead-${++nextWidgetId}`;
    } while (ta.ownerDocument.getElementById(`${id}-input`) || ta.ownerDocument.getElementById(`${id}-list`));
    taInput.id = `${id}-input`;
    taList.id = `${id}-list`;
    taInput.setAttribute("aria-controls", taList.id);
    ta.querySelector("label")?.setAttribute("for", taInput.id);
  }

  initialized.add(ta);
  ta.dataset.atlasTypeaheadReady = "true";
  const listeners = new AbortController();
  let disposed = false;

  let taManifest: SearchShardManifest | null = null;
  let taManifestLoading: Promise<SearchShardManifest> | null = null;
  let taFullIndex: SearchRow[] | null = null;
  let taFullLoading: Promise<SearchRow[]> | null = null;
  let taAliases: SearchAlias[] | null = null;
  let taAliasesLoading: Promise<SearchAlias[]> | null = null;
  const taShardCache = new Map<string, Promise<SearchRow[]>>();
  let taItems: SearchResult[] = [];
  let taActive = -1;
  let taState: "loading" | "empty" | null = null;
  let taRequest = 0;

  const taOptionId = (i: number) => `${taList.id || taInput.id}-option-${i}`;

  const taRender = () => {
    if (!taItems.length) {
      taInput.removeAttribute("aria-activedescendant");
      taActive = -1;
      if (!taState) {
        closeList(taInput, taList);
        return;
      }

      const message = taState === "loading" ? LOADING_MESSAGE : EMPTY_MESSAGE;
      taList.innerHTML = `<li class="atlas-typeahead-state" role="option" aria-disabled="true">${taEsc(
        message,
      )}</li>`;
      taList.hidden = false;
      taInput.setAttribute("aria-expanded", "true");
      return;
    }

    taList.innerHTML = taItems
      .map((item, i) => {
        const article = item.article;
        const gloss = article.g ? `<span class="ata-gloss">${highlight(article.g, taInput.value)}</span>` : "";
        const headword = item.matchedAlias
          ? `${highlight(item.matchedAlias, taInput.value)} <span class="ata-alias-arrow" aria-hidden="true">→</span> ${taEsc(article.l)}`
          : highlight(article.l, taInput.value);
        return `<li role="option" id="${taEsc(taOptionId(i))}" class="atlas-typeahead-opt${
          i === taActive ? " active" : ""
        }" data-slug="${taEsc(article.s)}" aria-selected="${i === taActive}">
          <a class="ata-main" href="/lexicon/${encodeURIComponent(article.s)}/" tabindex="-1" style="color:inherit;text-decoration:none">
            <span class="ata-lemma">${headword}</span>
            ${gloss}
          </a>
          <span class="ata-kinds">${resultPills(item)}</span>
        </li>`;
      })
      .join("");
    taList.hidden = false;
    taInput.setAttribute("aria-expanded", "true");
    if (taActive >= 0) {
      taInput.setAttribute("aria-activedescendant", taOptionId(taActive));
      taList.querySelector<HTMLElement>(".active")?.scrollIntoView({ block: "nearest" });
    }
  };

  const taLoadManifest = () => {
    if (taManifest) return Promise.resolve(taManifest);
    if (!taManifestLoading) {
      taManifestLoading = fetch("/lexicon/search-shards.json")
        .then((response) => {
          if (!response.ok) throw new Error(`search shard manifest fetch failed: ${response.status}`);
          return response.json();
        })
        .then((data: unknown) => {
          if (!isShardManifest(data)) throw new Error("invalid search shard manifest");
          taManifest = data;
          return data;
        })
        .catch((error) => {
          taManifestLoading = null;
          throw error;
        });
    }
    return taManifestLoading;
  };

  const taLoadFull = () => {
    if (taFullIndex) return Promise.resolve(taFullIndex);
    if (!taFullLoading) {
      taFullLoading = fetch("/lexicon/search-index.json")
        .then((response) => {
          if (!response.ok) throw new Error(`search index fetch failed: ${response.status}`);
          return response.json();
        })
        .then((data: unknown) => {
          taFullIndex = Array.isArray(data) ? data.filter(isSearchRow) : [];
          return taFullIndex;
        })
        .catch(() => {
          taFullIndex = [];
          return taFullIndex;
        });
    }
    return taFullLoading;
  };

  const taLoadAliases = () => {
    if (taAliases) return Promise.resolve(taAliases);
    if (!taAliasesLoading) {
      taAliasesLoading = fetch("/lexicon/search-aliases.json")
        .then((response) => {
          if (!response.ok) throw new Error(`search alias fetch failed: ${response.status}`);
          return response.json();
        })
        .then((data: unknown) => {
          taAliases = Array.isArray(data) ? data.filter(isSearchAlias) : [];
          return taAliases;
        })
        .catch(() => {
          taAliases = [];
          return taAliases;
        });
    }
    return taAliasesLoading;
  };

  const taLoadShardRows = async (q: string): Promise<{ rows: SearchRow[]; full: boolean }> => {
    try {
      const manifest = await taLoadManifest();
      const shard = searchShardForQuery(manifest, q);
      if (!shard) return { rows: await taLoadFull(), full: true };
      let loading = taShardCache.get(shard.path);
      if (!loading) {
        loading = fetch(shard.path)
          .then((response) => {
            if (!response.ok) throw new Error(`search shard fetch failed: ${response.status}`);
            return response.json();
          })
          .then((data: unknown) => Array.isArray(data) ? data.filter(isSearchRow) : [])
          .catch((error) => {
            taShardCache.delete(shard.path);
            throw error;
          });
        taShardCache.set(shard.path, loading);
      }
      return { rows: await loading, full: false };
    } catch {
      return { rows: await taLoadFull(), full: true };
    }
  };

  const taSearch = (q: string) => {
    const request = ++taRequest;
    if (!normalize(q)) {
      taItems = [];
      taState = null;
      taRender();
      return;
    }

    taState = "loading";
    taRender();

    void Promise.all([taLoadShardRows(q), taLoadAliases()]).then(async ([{ rows, full }, aliases]) => {
      if (disposed || request !== taRequest) return;
      let matches = rankSearchResults(rows, aliases, q, 12);
      if (!matches.length && !full) {
        matches = rankSearchResults(await taLoadFull(), aliases, q, 12);
        if (disposed || request !== taRequest) return;
      }
      taItems = matches;
      // No auto-highlight — Enter prefers an exact lemma match until the
      // learner arrows to a suggestion (scout #7 / K3 B1).
      taActive = -1;
      taState = taItems.length ? null : "empty";
      taRender();
    });
  };

  const taGo = (slug: string | null) => {
    if (slug) window.location.assign(`/lexicon/${encodeURIComponent(slug)}/`);
  };

  const taListboxOpen = () => !taList.hidden;

  taInput.addEventListener("focus", () => {
    const request = taRequest;
    void taLoadManifest().catch(() => taLoadFull()).then(() => {
      if (!disposed && request === taRequest) taSearch(taInput.value);
    });
  }, { signal: listeners.signal });

  taInput.addEventListener("input", () => {
    taSearch(taInput.value);
  }, { signal: listeners.signal });

  taInput.addEventListener("keydown", (ev) => {
    if (ev.key === "ArrowDown") {
      ev.preventDefault();
      if (taItems.length) {
        taActive = taActive < 0 ? 0 : (taActive + 1) % taItems.length;
        taRender();
      }
    } else if (ev.key === "ArrowUp") {
      ev.preventDefault();
      if (taItems.length) {
        taActive =
          taActive < 0
            ? taItems.length - 1
            : (taActive - 1 + taItems.length) % taItems.length;
        taRender();
      }
    } else if (ev.key === "Enter") {
      const chosen = resolveTypeaheadEnterSelection(
        taInput.value,
        taItems.map((item) => ({
          lemma: item.article.l,
          slug: item.article.s,
          item,
        })),
        taActive,
      );
      if (chosen) {
        ev.preventDefault();
        taGo(chosen.slug);
      }
    } else if (ev.key === "Escape") {
      ev.preventDefault();
      ++taRequest;
      const action = resolveTypeaheadEscapeAction(taListboxOpen() && (taItems.length > 0 || taState !== null));
      if (action === "close-listbox") {
        taItems = [];
        taState = null;
        taActive = -1;
        taRender();
        return;
      }
      taInput.value = "";
      taItems = [];
      taState = null;
      taActive = -1;
      taRender();
    }
  }, { signal: listeners.signal });

  taList.addEventListener("mousedown", (ev) => {
    ev.preventDefault();
  }, { signal: listeners.signal });

  taList.addEventListener("click", (ev) => {
    const target = ev.target instanceof Element ? ev.target : null;
    const li = target?.closest("[data-slug]");
    if (li instanceof HTMLElement) {
      ev.preventDefault();
      taGo(li.getAttribute("data-slug"));
    }
  }, { signal: listeners.signal });

  ta.ownerDocument.addEventListener("click", (ev) => {
    const target = ev.target instanceof Node ? ev.target : null;
    if (target && !ta.contains(target)) {
      ++taRequest;
      taItems = [];
      taState = null;
      taRender();
    }
  }, { signal: listeners.signal });

  return () => {
    if (disposed) return;
    disposed = true;
    ++taRequest;
    listeners.abort();
    closeList(taInput, taList);
    initialized.delete(ta);
    delete ta.dataset.atlasTypeaheadReady;
  };
};

/** Bind only widgets in this host; each caller disposes only its own bindings. */
export function bindAtlasTypeaheads(root: ParentNode | null): () => void {
  const cleanups = Array.from(
    root?.querySelectorAll<HTMLElement>("[data-atlas-typeahead]") ?? [],
    initAtlasTypeahead,
  );
  return () => cleanups.forEach((cleanup) => cleanup());
}
