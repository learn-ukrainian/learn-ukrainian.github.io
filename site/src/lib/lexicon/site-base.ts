/**
 * Base-aware absolute site paths (spec R4).
 * Astro `BASE_URL` is `/` on the production Pages root deploy.
 */

export function normalizeBaseUrl(baseUrl: string | undefined | null): string {
  if (!baseUrl || baseUrl === "/") return "/";
  const withSlash = baseUrl.startsWith("/") ? baseUrl : `/${baseUrl}`;
  return withSlash.endsWith("/") ? withSlash.slice(0, -1) || "/" : withSlash;
}

/** Join site base with a root-absolute path (`/lexicon/…`, `/atlas`). */
export function absoluteSitePath(
  path: string,
  baseUrl: string | undefined | null = "/",
): string {
  const base = normalizeBaseUrl(baseUrl);
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  if (base === "/") return normalizedPath;
  return `${base}${normalizedPath}`;
}

/** Strip the site base prefix from a location pathname. */
export function stripSiteBase(
  pathname: string,
  baseUrl: string | undefined | null = "/",
): string {
  const base = normalizeBaseUrl(baseUrl);
  if (base === "/") return pathname || "/";
  if (pathname === base) return "/";
  if (pathname.startsWith(`${base}/`)) return pathname.slice(base.length) || "/";
  return pathname || "/";
}
