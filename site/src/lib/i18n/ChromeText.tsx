import React from 'react';
import { CHROME_STRINGS, type ChromeKey } from './chrome';

/**
 * React counterpart of components/chrome/ChromeText.astro — FOUC-safe dual-render
 * of an approved chrome string. Both locale variants render into the HTML; the CSS
 * in CourseLayout shows exactly one based on `html[data-chrome-locale]`. Rendering
 * both avoids React hydration mismatch (SSR and client agree on markup) and needs
 * no locale state. Keys are the typed ChromeKey union — no raw-string fallback.
 */
export default function ChromeText({ k }: { k: ChromeKey }): React.ReactElement {
  return (
    <span className="lu-i18n" data-i18n={k}>
      <span data-loc="en" lang="en">{CHROME_STRINGS.en[k]}</span>
      <span data-loc="uk" lang="uk">{CHROME_STRINGS.uk[k]}</span>
    </span>
  );
}

/**
 * Dual-render two pre-formatted locale strings (for templated phrases like
 * "3 of 10 completed (30%)" where numbers are interpolated). Same CSS show/hide.
 */
export function ChromeDual({ en, uk }: { en: string; uk: string }): React.ReactElement {
  return (
    <span className="lu-i18n">
      <span data-loc="en" lang="en">{en}</span>
      <span data-loc="uk" lang="uk">{uk}</span>
    </span>
  );
}
