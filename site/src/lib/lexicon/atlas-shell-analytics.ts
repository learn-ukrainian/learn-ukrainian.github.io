/**
 * GoatCounter classification for atlas 404-fallback pages (spec R2).
 *
 * Call after the shell settles. Suppresses the automatic /404/ pageview via
 * `goatcounter.no_onload` (set early on lexicon paths) so we emit exactly one
 * classified hit — never a double pageview.
 */

import type { AtlasAnalyticsClass } from "./word-atlas-client-shell.ts";
import { lexiconArticlePath } from "./atlas-lexicon-path.ts";

export type GoatCounterLike = {
  count?: (vars?: {
    path?: string;
    title?: string;
    event?: boolean;
  }) => void;
  no_onload?: boolean;
};

declare global {
  interface Window {
    goatcounter?: GoatCounterLike;
  }
}

export function suppressGoatcounterAutoload(): void {
  const existing = window.goatcounter ?? {};
  window.goatcounter = { ...existing, no_onload: true };
}

export function reportAtlasShellAnalytics(options: {
  classification: AtlasAnalyticsClass;
  slug: string;
  lemma?: string;
  baseUrl?: string;
  goatcounter?: GoatCounterLike | null;
  setDocumentTitle?: boolean;
}): void {
  const {
    classification,
    slug,
    lemma,
    baseUrl = "/",
    setDocumentTitle = true,
  } = options;
  const gc = options.goatcounter ?? window.goatcounter;
  const path = lexiconArticlePath(slug, baseUrl);
  const title = lemma ?? slug;

  if (classification === "atlas_tail_rendered") {
    if (setDocumentTitle) {
      document.title = `${title} · Learn Ukrainian`;
    }
    // One pageview with overridden path+title (not the generic /404/).
    gc?.count?.({ path, title });
    // Classification event (not a second pageview).
    gc?.count?.({ path: classification, title, event: true });
    return;
  }

  // Failures: classify as event only — still no /404/ pageview.
  gc?.count?.({ path: classification, title: slug, event: true });
}
