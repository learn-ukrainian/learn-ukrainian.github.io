/**
 * Lexicon article path helpers for the 404-fallback client shell (PR3 D2).
 */

import { isValidAtlasSlug } from "./atlas-data-source.ts";
import { stripSiteBase } from "./site-base.ts";

const LEXICON_ARTICLE_RE = /^\/lexicon\/([^/]+)\/?$/;

/**
 * If `pathname` is a lexicon article URL (`/lexicon/<slug>/`), return the
 * decoded NFC slug. Otherwise null (generic 404 / non-article lexicon routes).
 */
export function parseLexiconArticleSlug(
  pathname: string,
  baseUrl: string | undefined | null = "/",
): string | null {
  const path = stripSiteBase(pathname, baseUrl);
  const match = path.match(LEXICON_ARTICLE_RE);
  if (!match) return null;
  let slug: string;
  try {
    slug = decodeURIComponent(match[1]!).normalize("NFC");
  } catch {
    return null;
  }
  if (!isValidAtlasSlug(slug)) return null;
  return slug;
}

/** Canonical article path for a slug (trailing slash, base-aware). */
export function lexiconArticlePath(
  slug: string,
  baseUrl: string | undefined | null = "/",
): string {
  const base = baseUrl && baseUrl !== "/" ? String(baseUrl).replace(/\/$/, "") : "";
  return `${base}/lexicon/${slug}/`;
}
