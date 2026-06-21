# ADR: en/uk web-UI chrome i18n via a single-URL runtime "Chrome Locale Runtime" (NOT route i18n)

- **Date:** 2026-06-21
- **Status:** Accepted (design) — implementation DEFERRED to the infra-Claude lane; toggle exposure gated on chrome-string stabilization.
- **Tracks:** site-wide (all courses + the global Readings reference).
- **Issue:** #3671.
- **Author:** folk track-driver (Claude), per user order 2026-06-21 ("design the principled approach with Codex before building").
- **Consulted:** Codex — design (task `i18n-chrome-design-3671`, msg #1336) + default-language correction (task `i18n-chrome-confirm-3671`, msg #1338).
- **Governing rule:** project immersion rule **#M-13** (never raise English; maximum Ukrainian immersion in the **learning content**). Threat-backed, top priority. NB: #M-13 governs content language, **not** navigation chrome — see "Default language".
- **Expiry / revisit:** when site chrome strings stabilize enough to expose the visible toggle (see Sequencing).

## Context

The site is **fully static Astro 6.4.7 (SSG)** — no SSR adapter, `output` unset,
`trailingSlash:'always'`, ~4405 prerendered pages. There is **no i18n integration
today**; chrome (nav, titles, section labels, search/browse strings, sidebar
labels, counters, homepage cards, track labels) is hardcoded English inline in
`.astro` components and the single `CourseLayout.astro` (303 lines) — the current
"Word Atlas model": **English chrome + Ukrainian content**.

We want a learner-facing **en/uk toggle that switches ONLY the chrome language**,
next to the existing `lu-theme` dark/light toggle. It must **never** touch module/
teaching content, dialogues, teaching voice, vocab glosses, or primary-source
texts, nor work titles, author names, genre headers («Дума»/«Колядка»), lemmas, or
attributions — those stay Ukrainian regardless of the toggle (#M-13).

## Decision

Adopt a **Chrome Locale Runtime** — a single-URL, runtime chrome-string layer,
deliberately separate from content i18n. **Reject Astro routing i18n** (`/en/`,
`/uk/` prefixes): it is URL/route-oriented, would duplicate all ~4405 routes into
two prefixes carrying *identical invariant Ukrainian content*, and would muddy
canonical URLs/SEO while implying content localization that must not happen. The
toggle is chrome-only, so per-page URLs must not change.

### Architecture
- **`src/lib/i18n/chrome.ts`** — the dictionary + typed API.
  - `type ChromeLocale = 'uk' | 'en'`; `const DEFAULT_CHROME_LOCALE = 'uk'`.
  - `const chromeStrings = { uk: {...}, en: {...} } satisfies Record<ChromeLocale, Record<ChromeKey, string>>`.
  - helpers `t(locale, key)`, `formatCount(locale, key, n)` (counters/plurals).
  - keys come from a **typed `ChromeKey` union** — no `t(rawString)` fallback.
- **`src/components/chrome/ChromeText.astro`** — accepts a typed `ChromeKey`,
  renders only approved chrome strings. For above-the-fold chrome, **dual-render
  both locale variants** and show/hide by attribute (FOUC handling below).
- **`CourseLayout.astro`** — owns the toggle next to the theme toggle; persists
  `lu-chrome-locale` to localStorage; an `is:inline` head script sets
  `data-chrome-locale` on `<html>` **before paint**, mirroring the `lu-theme`
  pattern exactly.

### FOUC / first paint
Pages are prerendered, so a "replace text after load" swap would flash the wrong
language. Instead, **dual-render the tiny chrome strings and toggle via CSS**:

```html
<span data-i18n="nav.readings">
  <span data-locale-text="uk" lang="uk">Читання</span>
  <span data-locale-text="en" lang="en">Readings</span>
</span>
```
```css
html[data-chrome-locale='uk'] [data-locale-text='en'],
html[data-chrome-locale='en'] [data-locale-text='uk'] { display: none; }
```

The pre-paint `is:inline` script reads `lu-chrome-locale` and sets
`data-chrome-locale` before first paint (no flash). For non-text chrome —
`aria-label`, `placeholder`, `<title>` — a small runtime applier updates them from
the same typed dictionary on load.

### Default language — chrome follows the user (USER DECISION 2026-06-21)
**Chrome defaults to the user's own interface language; Ukrainian chrome is the
opt-in.** Detection precedence (all client-side, pre-paint, in the `is:inline`
script):
1. **Explicit toggle choice in `localStorage` (`lu-chrome-locale`) wins** (wrapped
   in `try/catch` — Safari private / hardened contexts can throw on access).
2. else **`navigator.languages?.[0] ?? navigator.language`**, lowercased, split on
   `-`, **primary subtag only**: `uk` → Ukrainian chrome; anything else → English.
   Region is irrelevant (`uk`, `uk-UA` … all mean Ukrainian chrome).
3. **No-JS / pre-JS fallback = English**, baked into the static HTML as
   `data-chrome-locale="en"`; the script then switches to `uk` synchronously before
   paint when detection says so.

**Why this, not Ukrainian-default (corrects the first draft):** this is the
`l2-uk-en` track — **"Ukrainian for English speakers"**, audience = English
speakers incl. absolute A1 beginners. Ukrainian-default *chrome* would leave a
beginner unable to read the nav and therefore unable to reach the immersive
Ukrainian lesson content — i.e. *less* immersion, not more. **#M-13 governs the
learning CONTENT (texts, teaching voice, dialogues, vocab, work titles, genre
headers — always Ukrainian, for everyone), NOT the navigation chrome.** English
chrome for an English-speaking beginner does not "raise English in the learning";
the learning is still 100% Ukrainian. This is the standard
*interface-follows-user, content-is-target* model (Duolingo/Babbel). Codex
withdrew its earlier "no auto-detect" point **for chrome specifically** (msg
#1338) — that point had conflated chrome usability with content immersion.

> ✅ **Keeps the current "English chrome" default** (Word Atlas model, PR #3669)
> for English-browser visitors, and *adds* (a) auto-selected Ukrainian chrome for
> Ukrainian-locale browsers and (b) an explicit toggle either way. No regression
> for beginners; opt-in extra exposure for those who want it.

### `<html lang>`
Keep the document default biased to Ukrainian: `<html lang="uk"
data-chrome-locale="…">`. Mark English chrome containers/spans `lang="en"` when
English UI is active (W3C/WCAG language-of-page + language-of-parts). Do **not**
flip global `<html lang>` with the toggle first; revisit only once every Ukrainian
content region is reliably wrapped `lang="uk"`.

### Content protection — mechanical, not by discipline
- CI: **ban `data-i18n` in `src/content/**`**.
- CI: **ban `t(...)`/`ChromeText` outside approved chrome/layout/component files.**
- All keys from the typed `ChromeKey` union; no raw-string fallback.
- Keep primary-source/rendering components separate from chrome components.
- Lint: every `data-i18n` key must exist in `chromeStrings`; no content file
  carries an i18n marker.
- Never pipe titles, author names, genre headers, lemmas, or attributions through
  `ChromeText`; wrap Ukrainian content `lang="uk"`.

## Sequencing (the defer call, refined)
The issue's "defer until chrome strings stabilize" is right for the **visible
toggle**, but **not** for the preparatory architecture:
1. Centralize stable shared chrome strings now behind `t(DEFAULT_CHROME_LOCALE, key)` (ships English-or-Ukrainian-only; no behavior change).
2. Add the parity test + the "no i18n in content" lint rule.
3. Expose the toggle only once the key surface is stable and **both** dictionaries are complete.

This avoids maintaining two fast-churning label sets while still moving toward the
right architecture.

## Lane / ownership
Per the 2026-06-20 fleet restructure, site/code/CI = **infra-Claude lane**. This
ADR is the **spec**; the folk driver produced it (the design was the user's order)
but does **not** implement it. Hand to infra Claude for build, in the sequenced
order above. The **default-language question is resolved** (user decision
2026-06-21: chrome follows the user's locale, English fallback — see "Default
language" above), so no further user gate blocks the build.

## Alternatives rejected
- **Astro routing i18n (`/en/`,`/uk/`)** — route explosion + content duplication + canonical/SEO mess; URL-oriented, wrong tool for chrome-only swap.
- **Pure post-load JS text replacement** — English→Ukrainian flash on every load; fails FOUC bar.
- **Ukrainian-default chrome (first-draft idea, rejected by user 2026-06-21)** — for the English-speakers track it strands A1 beginners who can't read the nav, *reducing* effective immersion; conflated chrome with content (#M-13 governs content, not chrome).
- **Server-side `Accept-Language`** — impossible on static GitHub Pages (no SSR / no `Vary`). Client-side `navigator.language` detection (above) is the correct equivalent.

## Biggest risk
Not the toggle — it's **keeping the chrome/content boundary enforceable as the UI
grows.** The typed `ChromeText` boundary + the CI lint rules are the load-bearing
parts; without them, a future contributor localizes a work title or genre header
and breaks immersion.

## References
- Astro i18n (route/URL-oriented): https://docs.astro.build/en/guides/internationalization/
- Astro `is:inline` (pre-paint setter): https://docs.astro.build/en/reference/directives-reference/#isinline
- W3C language declarations: https://www.w3.org/International/questions/qa-html-language-declarations
- MDN `lang` a11y: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/lang
