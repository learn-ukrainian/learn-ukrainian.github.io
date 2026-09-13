/**
 * Client-mounted Word Atlas shell for GH Pages 404 fallback (PR3 D2/R9).
 *
 * When `location.pathname` is `/lexicon/<slug>/`, fetches the entry via
 * `HttpAtlasDataSource` and mounts `WordAtlasArticle`. Non-lexicon paths
 * render nothing so the generic 404 stays visible.
 *
 * Do not edit WordAtlasArticle internals here — mount as-is.
 */

import { useEffect, useRef, useState } from "react";
import WordAtlasArticle from "./WordAtlasArticle";
import {
  parseLexiconArticleSlug,
} from "../lib/lexicon/atlas-lexicon-path";
import {
  reportAtlasShellAnalytics,
  suppressGoatcounterAutoload,
} from "../lib/lexicon/atlas-shell-analytics";
import {
  createBrowserAtlasFetch,
  DEFAULT_ATLAS_ASSET_BASE,
} from "../lib/lexicon/browser-atlas-fetch";
import { HttpAtlasDataSource } from "../lib/lexicon/http-atlas-data-source";
import { absoluteSitePath } from "../lib/lexicon/site-base";
import {
  loadAtlasLinkCatalog,
  analyticsClassForState,
  loadAtlasClientShellEntry,
  preflightAtlasSlugInSearchIndex,
  type AtlasClientShellState,
} from "../lib/lexicon/word-atlas-client-shell";
import {
  buildAtlasLinkResolver,
  type AtlasLinkCatalog,
  type AtlasSearchArticleRow,
} from "../lib/lexicon/word-atlas-article-model";

export interface WordAtlasClientShellProps {
  /** Same-origin atlas root; default `/atlas` (base-aware absolute). */
  assetBaseUrl?: string;
  /** Site base URL (`import.meta.env.BASE_URL`). */
  baseUrl?: string;
  /** Override pathname (tests). */
  pathname?: string;
  /** Inject fetch for hermetic tests. */
  fetchImpl?: typeof fetch;
}

function bindEtymologyHandlers(root: ParentNode | null): () => void {
  if (!root) return () => {};
  const stages = root.querySelectorAll<HTMLElement>("[data-ety-note]");
  const listeners: Array<{ el: HTMLElement; fn: () => void }> = [];
  stages.forEach((stage) => {
    const fn = () => {
      root.querySelectorAll("[data-ety-note]").forEach((item) => {
        item.classList.remove("active");
      });
      stage.classList.add("active");
      const output = stage
        .closest(".atlas-section")
        ?.querySelector<HTMLElement>("[data-ety-note-output]");
      if (output) {
        output.textContent = stage.dataset.etyNote || output.textContent;
        output.style.background = "var(--teal-light)";
      }
    };
    stage.addEventListener("click", fn);
    listeners.push({ el: stage, fn });
  });
  return () => {
    for (const { el, fn } of listeners) el.removeEventListener("click", fn);
  };
}

function bindHeteronymHandlers(root: ParentNode | null): () => void {
  if (!root) return () => {};
  const tabs = root.querySelectorAll<HTMLElement>("[data-heteronym-target]");
  const panels = root.querySelectorAll<HTMLElement>("[data-heteronym-idx]");
  const jumpButtons = root.querySelectorAll<HTMLElement>("[data-heteronym-jump]");
  if (!tabs.length || !panels.length) return () => {};

  const activateTab = (index: number, updateHash = true) => {
    if (index < 0 || index >= tabs.length) return;
    tabs.forEach((tab, i) => {
      const isTarget = i === index;
      tab.classList.toggle("active", isTarget);
      tab.setAttribute("aria-selected", isTarget ? "true" : "false");
      tab.tabIndex = isTarget ? 0 : -1;
    });
    panels.forEach((panel, i) => {
      const isTarget = i === index;
      panel.style.display = isTarget ? "block" : "none";
      if (isTarget) {
        panel.removeAttribute("hidden");
      } else {
        panel.setAttribute("hidden", "true");
      }
    });
    const headword = tabs[index]?.getAttribute("data-heteronym-headword");
    if (updateHash && headword) {
      history.replaceState(null, "", `#${headword}`);
    }
  };

  const listeners: Array<{ el: HTMLElement; event: string; fn: EventListener }> = [];

  tabs.forEach((tab, idx) => {
    const clickHandler: EventListener = (e) => {
      e.preventDefault();
      activateTab(idx, true);
    };
    const keyHandler: EventListener = (e) => {
      const keyboardEvent = e as KeyboardEvent;
      let targetIdx = -1;
      if (keyboardEvent.key === "ArrowRight") {
        targetIdx = (idx + 1) % tabs.length;
      } else if (keyboardEvent.key === "ArrowLeft") {
        targetIdx = (idx - 1 + tabs.length) % tabs.length;
      } else if (keyboardEvent.key === "Home") {
        targetIdx = 0;
      } else if (keyboardEvent.key === "End") {
        targetIdx = tabs.length - 1;
      }
      if (targetIdx >= 0) {
        keyboardEvent.preventDefault();
        activateTab(targetIdx, true);
        tabs[targetIdx]?.focus();
      }
    };
    tab.addEventListener("click", clickHandler);
    tab.addEventListener("keydown", keyHandler);
    listeners.push({ el: tab, event: "click", fn: clickHandler });
    listeners.push({ el: tab, event: "keydown", fn: keyHandler });
  });

  jumpButtons.forEach((btn) => {
    const jumpHandler: EventListener = (e) => {
      e.preventDefault();
      const targetStr = btn.getAttribute("data-heteronym-jump");
      if (targetStr !== null) {
        const targetIdx = parseInt(targetStr, 10);
        activateTab(targetIdx, true);
        const nav = root.querySelector(".atlas-heteronym-nav");
        if (nav && "scrollIntoView" in nav) {
          (nav as HTMLElement).scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
      }
    };
    btn.addEventListener("click", jumpHandler);
    listeners.push({ el: btn, event: "click", fn: jumpHandler });
  });

  const syncHash = () => {
    const rawHash = decodeURIComponent(location.hash.replace(/^#/, "").trim());
    if (!rawHash) return;
    const clean = (s: string) => s.normalize("NFC").replace(/[\u0300\u0301]/g, "").toLowerCase();
    const cleanTarget = clean(rawHash);
    tabs.forEach((tab, i) => {
      const hw = tab.getAttribute("data-heteronym-headword") || "";
      if (hw.normalize("NFC") === rawHash.normalize("NFC") || clean(hw) === cleanTarget) {
        activateTab(i, false);
      }
    });
  };

  syncHash();
  window.addEventListener("hashchange", syncHash);

  return () => {
    for (const { el, event, fn } of listeners) {
      el.removeEventListener(event, fn);
    }
    window.removeEventListener("hashchange", syncHash);
  };
}

function ShellSkeleton() {
  return (
    <div
      role="status"
      aria-busy="true"
      data-word-atlas-state="loading"
      className="atlas-client-shell-state atlas-client-shell-loading"
    >
      <div className="atlas-client-shell-skeleton" aria-hidden="true">
        <div className="atlas-client-shell-skel-line wide" />
        <div className="atlas-client-shell-skel-line" />
        <div className="atlas-client-shell-skel-line mid" />
        <div className="atlas-client-shell-skel-block" />
      </div>
      <p>Завантаження статті Атласу…</p>
    </div>
  );
}

export default function WordAtlasClientShell({
  assetBaseUrl,
  baseUrl = "/",
  pathname,
  fetchImpl,
}: WordAtlasClientShellProps) {
  const resolvedBase = baseUrl;
  const atlasBase =
    assetBaseUrl ??
    (absoluteSitePath(DEFAULT_ATLAS_ASSET_BASE, resolvedBase).replace(/\/$/, "") ||
      DEFAULT_ATLAS_ASSET_BASE);

  const path =
    pathname ??
    (typeof window !== "undefined" ? window.location.pathname : "");
  const slug = parseLexiconArticleSlug(path, resolvedBase);

  const [state, setState] = useState<AtlasClientShellState | null>(() =>
    slug ? { status: "loading", slug } : null,
  );
  const [atlasLinkCatalog, setAtlasLinkCatalog] = useState<AtlasLinkCatalog | null>(null);
  const [retryToken, setRetryToken] = useState(0);
  const articleHostRef = useRef<HTMLDivElement | null>(null);
  const reportedRef = useRef<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    suppressGoatcounterAutoload();
    document.documentElement.dataset.atlasShell = "active";
    document.querySelectorAll("[data-generic-404]").forEach((el) => {
      el.setAttribute("hidden", "");
    });
    document.querySelectorAll("[data-atlas-shell-boot]").forEach((el) => {
      el.setAttribute("hidden", "");
    });
  }, [slug]);

  useEffect(() => {
    if (!slug) return;
    let cancelled = false;
    setState({ status: "loading", slug });
    setAtlasLinkCatalog(null);

    const run = async () => {
      const fetchFn = fetchImpl ?? fetch.bind(globalThis);
      let articleRows: AtlasSearchArticleRow[] | undefined;
      const preflight = await preflightAtlasSlugInSearchIndex(
        slug,
        fetchFn,
        resolvedBase,
        (rows) => {
          articleRows = rows;
        },
      );
      if (cancelled) return;
      if (preflight === "missing") {
        setState({ status: "not_found", slug });
        return;
      }

      const source = new HttpAtlasDataSource(createBrowserAtlasFetch(fetchImpl), {
        assetBaseUrl: atlasBase,
        pointerTtlMs: 0,
      });
      const [next, linkCatalog] = await Promise.all([
        loadAtlasClientShellEntry(slug, source),
        loadAtlasLinkCatalog(fetchFn, resolvedBase, articleRows),
      ]);
      if (next.status === "ready") {
        const enrichment = next.record.entry.enrichment as
          | { verb_pedagogy?: { aspect_partner?: { url_slug?: string } } }
          | null
          | undefined;
        const rawPartnerSlug = enrichment?.verb_pedagogy?.aspect_partner?.url_slug?.trim();
        if (rawPartnerSlug && linkCatalog) {
          const resolver = buildAtlasLinkResolver(
            linkCatalog,
            next.record.relations.map((r) => r.related_slug),
          );
          const resolvedPartnerSlug = resolver.resolveSlug(
            rawPartnerSlug,
            next.record.entry.url_slug,
          );
          if (resolvedPartnerSlug) {
            try {
              const partnerResult = await source.getEntry(resolvedPartnerSlug);
              if (partnerResult.kind === "entry") {
                next.record.partnerRecord = partnerResult.record;
              }
            } catch {
              // Fail closed: partner lookup failure leaves partnerRecord null/undefined
            }
          }
        }
      }
      if (!cancelled) {
        setAtlasLinkCatalog(linkCatalog);
        setState(next);
      }
    };

    void run();

    return () => {
      cancelled = true;
    };
  }, [slug, atlasBase, fetchImpl, retryToken, resolvedBase]);

  useEffect(() => {
    if (!state || state.status === "loading") return;
    const classification = analyticsClassForState(state);
    if (!classification) return;
    const reportKey = `${classification}:${state.slug}:${state.status === "ready" ? state.record.entry.lemma : ""}`;
    if (reportedRef.current === reportKey) return;
    reportedRef.current = reportKey;
    reportAtlasShellAnalytics({
      classification,
      slug: state.slug,
      lemma: state.status === "ready" ? state.record.entry.lemma : undefined,
      baseUrl: resolvedBase,
    });
  }, [state, resolvedBase]);

  useEffect(() => {
    if (!state || state.status !== "ready") return;
    const cleanupEty = bindEtymologyHandlers(articleHostRef.current);
    const cleanupHet = bindHeteronymHandlers(articleHostRef.current);
    return () => {
      cleanupEty();
      cleanupHet();
    };
  }, [state]);

  if (!slug || !state) return null;

  if (state.status === "loading") {
    return <ShellSkeleton />;
  }

  if (state.status === "not_found") {
    return (
      <div
        role="alert"
        data-word-atlas-state="not_found"
        data-http-status="404"
        className="atlas-client-shell-state"
      >
        <h1 className="lu-i18n-block">
          <span data-loc="en">Word not found</span>
          <span data-loc="uk">Слово не знайдено</span>
        </h1>
        <p className="lu-i18n-block">
          <span data-loc="en">No public article for «{state.slug}».</span>
          <span data-loc="uk">Немає публічної статті для «{state.slug}».</span>
        </p>
        <p>
          <a href={absoluteSitePath("/lexicon/", resolvedBase)}>
            <span className="lu-i18n">
              <span data-loc="en">Back to Atlas</span>
              <span data-loc="uk">До Атласу</span>
            </span>
          </a>
          {" · "}
          <a href={absoluteSitePath("/lexicon/", resolvedBase) + "#lexicon-landing-search"}>
            <span className="lu-i18n">
              <span data-loc="en">Search</span>
              <span data-loc="uk">Пошук</span>
            </span>
          </a>
        </p>
      </div>
    );
  }

  if (state.status === "corrupt") {
    return (
      <div
        role="alert"
        data-word-atlas-state="corrupt"
        data-http-status="503"
        className="atlas-client-shell-state"
      >
        <h1>Дані статті пошкоджені</h1>
        <p>Не вдалося прочитати словникові дані для «{state.slug}».</p>
        <p className="atlas-client-shell-detail">{state.message}</p>
        <p>
          <a href={absoluteSitePath("/lexicon/", resolvedBase)}>До Атласу</a>
        </p>
      </div>
    );
  }

  if (state.status === "network_error") {
    return (
      <div
        role="alert"
        data-word-atlas-state="network_error"
        data-http-status="503"
        className="atlas-client-shell-state"
      >
        <h1>Не вдалося завантажити</h1>
        <p>Мережева помилка під час завантаження «{state.slug}».</p>
        <p className="atlas-client-shell-detail">{state.message}</p>
        <p>
          <button
            type="button"
            data-word-atlas-retry
            onClick={() => {
              reportedRef.current = null;
              setRetryToken((n) => n + 1);
            }}
          >
            Спробувати знову
          </button>
        </p>
      </div>
    );
  }

  return (
    <div ref={articleHostRef} data-atlas-client-article>
      <WordAtlasArticle
        record={state.record}
        generatedAt={state.generatedAt}
        manifestVersion={state.manifestVersion}
        atlasLinkCatalog={atlasLinkCatalog ?? undefined}
        partnerRecord={state.record.partnerRecord}
      />
    </div>
  );
}
