/**
 * DailyWords loading / error DOM state (#6771, #6711 review).
 * Shared by the processed DailyWords module script and unit tests.
 *
 * The is:inline CDN-fail watchdog in DailyWords.astro intentionally duplicates
 * the fallback paint path and must NOT import this module (#6771 resilience).
 */

export function setDailyLoadingStatus(
  status: HTMLElement | null,
  loadingHtml: string,
): void {
  if (!status) return;
  status.hidden = false;
  status.dataset.dailyLoading = "true";
  status.innerHTML = loadingHtml;
}

export function setDailyStatusContent(
  status: HTMLElement | null,
  html: string,
  opts: { loading?: boolean; hidden?: boolean } = {},
): void {
  if (!status) return;
  status.hidden = Boolean(opts.hidden);
  if (opts.loading) status.dataset.dailyLoading = "true";
  else status.removeAttribute("data-daily-loading");
  status.innerHTML = html;
}

/** Paint the load-error fallback and clear the loading spinner. */
export function applyDailyLoadFallback(section: HTMLElement): void {
  if (section.dataset.dailyReady === "true") return;
  const status = section.querySelector<HTMLElement>("[data-daily-status]");
  const fallback = section.querySelector<HTMLElement>("[data-daily-fallback]");
  const list = section.querySelector("[data-daily-list]");
  if (list) list.innerHTML = "";
  if (status) {
    status.hidden = true;
    status.textContent = "";
    status.removeAttribute("data-daily-loading");
  }
  if (fallback) fallback.hidden = false;
  section.hidden = false;
  section.dataset.dailyReady = "true";
}

/** Hide fallback and restore the loading status (retry / fresh fetch). */
export function beginDailyReload(
  section: HTMLElement,
  loadingHtml: string,
): void {
  const fallback = section.querySelector<HTMLElement>("[data-daily-fallback]");
  const status = section.querySelector<HTMLElement>("[data-daily-status]");
  if (fallback) fallback.hidden = true;
  setDailyLoadingStatus(status, loadingHtml);
  section.dataset.dailyReady = "false";
}

/** Mark success: loading attr gone, section ready (list may already be filled). */
export function markDailyLoadSuccess(
  section: HTMLElement,
  statusHtml?: string | null,
): void {
  const status = section.querySelector<HTMLElement>("[data-daily-status]");
  const fallback = section.querySelector<HTMLElement>("[data-daily-fallback]");
  if (fallback) fallback.hidden = true;
  if (status) {
    if (statusHtml == null) {
      status.hidden = true;
      status.textContent = "";
      status.removeAttribute("data-daily-loading");
    } else {
      setDailyStatusContent(status, statusHtml, { loading: false, hidden: false });
    }
  }
  section.dataset.dailyReady = "true";
}
