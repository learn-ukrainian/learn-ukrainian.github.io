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
  analyticsClassForState,
  loadAtlasClientShellEntry,
  type AtlasClientShellState,
} from "../lib/lexicon/word-atlas-client-shell";

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

    const source = new HttpAtlasDataSource(createBrowserAtlasFetch(fetchImpl), {
      assetBaseUrl: atlasBase,
      pointerTtlMs: 0,
    });

    void loadAtlasClientShellEntry(slug, source).then((next) => {
      if (!cancelled) setState(next);
    });

    return () => {
      cancelled = true;
    };
  }, [slug, atlasBase, fetchImpl, retryToken]);

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
    return bindEtymologyHandlers(articleHostRef.current);
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
        <h1>Слово не знайдено</h1>
        <p>
          Немає публічної статті для «{state.slug}».
        </p>
        <p>
          <a href={absoluteSitePath("/lexicon/", resolvedBase)}>До Атласу</a>
          {" · "}
          <a href={absoluteSitePath("/lexicon/", resolvedBase) + "#lexicon-landing-search"}>
            Пошук
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
      />
    </div>
  );
}
