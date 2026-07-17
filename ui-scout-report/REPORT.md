# UI SCOUT REPORT (live site, 2026-07-17)

**Scope:** Live public walkthrough of Atlas + Practice on https://learn-ukrainian.github.io  
**Method:** Playwright Chromium headless, desktop 1280×900 and mobile 390×844. Screenshots under `ui-scout-report/shots/`. Raw machine log: `findings.json`, `letter-results.json`, `word-pages.json`, `practice-modes.json`.  
**Role:** Scout only — observations and evidence. No fixes, no improvement specs.

---

## Summary table

| ID | Severity | Surface | One-line observation |
| --- | --- | --- | --- |
| 1 | major | `/lexicon/` size impression | **8 206 is on the page**, but labelled `ПУБЛІЧНИЙ АТЛАС` amid competing counts (8 552 / 9 969 / 4 858 / 300) — easy to miss “dictionary size” |
| 2 | blocker | Locale toggle | Clicking to `ENG` **Ukrainian-izes the site nav** and **does not English the Atlas body** (stats stay UA) |
| 3 | polish | Typeahead Latin `voda` | Suggestions appear (Latin→lemma works) |
| 4 | minor | Typeahead Escape | Escape clears input and closes suggestions |
| 5 | polish | Typeahead Cyrillic `вода` | Suggestions appear (`role=option` ≥1) |
| 6 | polish | Typeahead paste `алергія` | Paste/fill yields a suggestion |
| 7 | major | Typeahead Enter | Typing `вода` → ArrowDown → Enter opens **`гаряча вода`**, not `вода` |
| 8 | minor | `/lexicon/browse` | States **“8206 записів Атласу · 33 літери”**; empty-state until a letter is chosen |
| 9 | minor | Browse search | `?q=вода` → **“2 збігів”** results (works) |
| 10 | major | Browse letters И, Ь | Letters **И** and **Ь** are **disabled / `is-empty` / `data-base-count=0`** but still drawn in the strip |
| 11–16 | minor | Word pages (6) | Pages load; rich UA chrome; **no audio** controls observed; etymology/relations sections present to varying degrees |
| 17 | polish | `вода` in-page links | 8 main links followed; **0 broken** |
| 18 | blocker | Practice hub language | `/lexicon/practice` → `/words-of-the-day/practice/`; **H1 + intro + back/eyebrow are Ukrainian-only** |
| 19 | minor | Mixed session start | “Почати сесію / Start session” starts a dual-labelled flashcard mix; SRS buttons dual |
| 20 | major | Practice keyboard | Space/Enter/1–2 advance; **“Skip to content” stays stuck visible** after keyboard use |
| 21 | polish | Mode Flashcards | Session UI dual for chrome; card lemma UA |
| 22 | polish | Mode Matching | Dual instruction + EN gloss column present |
| 23 | polish | Mode Choice | Dual stem (“Which word means …?”); options are UA lemmas |
| 24 | major | Mode Cloze | Input **placeholder Ukrainian-only and truncated** (`наберіть слово у потрібній фо`) |
| 25–27 | minor | Stress / Classify / Paradigm | Modes open; prompts mostly dual |
| 28 | major | Mode Synonyms | **Empty:** “Усі картки на зараз повторено.” / Session **0/0** (message UA-only) |
| 29 | minor | Mode Paronyms | Opens with items |
| 30 | major | Mode Heritage | **Empty for A1:** “Вправи зі спадщини для цього рівня ще готуються.” (UA-only) |
| 31 | minor | `/words-of-the-day/` | Dual H1; practice CTA; level chips |
| 32 | polish | WOTD → word | Word cards link to lemma pages (nav “Word Atlas” also links `/lexicon/`) |
| 33 | minor | `/readings/` | “Reading reference” nav works; EN title vs UA atlas chrome inconsistency |
| 34–35 | major | 404 word URLs | 404 page also shows **“Завантаження статті Атласу…”**; requests **`/atlas/current.json` → 404** |
| 36–42 | minor | Mobile 390px | No horizontal overflow on probed pages; UA chrome denser |
| 43 | blocker | Mobile practice | Same hub UA-only chrome; in-session classify prompt dual |
| 44–46 | minor | Mobile flash/choice/cloze | Modes usable; same cloze placeholder issue |

**Severity counts (refined):** blocker 2 · major 8 · minor 20+ · polish rest.

---

## What impression the site gives about dictionary size

**The number 8 206 is present on the live Atlas landing** (`/lexicon/`), in the “ДАНІ / Покриття Атласу” grid, card title **`ПУБЛІЧНИЙ АТЛАС`**, large figure **`8 206`**, subline `9 969 пошукових словоформ · 66 сегментів пошуку`.

At 1280×900 it sits roughly mid-viewport under the search hero (`y≈656` for the figure) — visible without deep scroll in this viewport. Screenshots: `shots/001-desktop-lexicon-landing-full.png`, `shots/002-desktop-lexicon-landing-viewport.png`.

Why a visitor can still fail to “see 8,206 words”:

1. **Not labelled “words”.** The card says **ПУБЛІЧНИЙ АТЛАС**, not “8 206 words / слів”. Browse is clearer: **“8206 записів Атласу · 33 літери”** (`shots/009-desktop-browse-landing.png`). Letter counts sum to **8206** (`letter-results.json`).
2. **Competing big numbers on the same panel:** МАНІФЕСТ **8 552**, search wordforms **9 969**, ПРАКТИКА **4 858**, СЛОВА ДНЯ **300**, ДЖЕРЕЛА **519**. A glance does not answer “how big is the dictionary?”
3. **Default chrome for the data panel is Ukrainian-only.** An English-speaking first visit that never discovers a working locale still sees opaque labels.
4. **Locale toggle does not English this panel** (Finding 2): with the control showing `ENG`, body stats remain `ПУБЛІЧНИЙ АТЛАС` / `МАНІФЕСТ` / etc. (`shots/003-desktop-lexicon-locale-eng.png`, `shots/075-locale-eng-viewport.png`).
5. Word **entries** themselves do not restate the global catalog size; mid-tail pages often show many “очікує джерело” tiles, which can feel like a thin dictionary even when the catalog is large (`shots/008-desktop-typeahead-enter.png` for `гаряча вода`).

**Bottom line for the owner’s “I expected to see 8,206 words”:** the figure is live and real; the page does not present it as an obvious English “8,206 words” headline, and adjacent counts + UA labels + broken ENG locale make the scale easy to miss or distrust.

---

## Numbered findings

### 1. Dictionary size hard to read as “8,206 words”
- **Surface:** `/lexicon/`
- **Repro:** Open https://learn-ukrainian.github.io/lexicon/ at 1280×900; read hero + “Покриття Атласу”.
- **What happens:** Hero is search-first (`Атлас слів`, placeholder `офіс / ofis / office`). Count **8 206** appears under **ПУБЛІЧНИЙ АТЛАС** beside several other large metrics.
- **Why it hurts a learner:** They cannot tell whether the atlas is “thousands of words” or a small course list.
- **Severity:** major
- **Screenshot:** `ui-scout-report/shots/002-desktop-lexicon-landing-viewport.png`
- **Console/network:** none specific

### 2. Locale toggle inverts / fails to English Atlas body
- **Surface:** Site-wide control `button.lu-locale-toggle` on `/lexicon/`
- **Repro:** Load `/lexicon/` (nav in English: Home, Word Atlas…). Click locale control until it shows `ENG`.
- **What happens:** Control accessible name/text can read as mashed **`УКРENG`**. After click to `ENG`, **top nav becomes Ukrainian** (`Головна`, `Слова дня`, `Атлас слів`, `Хрестоматія`) while **Atlas hero + data cards stay Ukrainian** (`ПУБЛІЧНИЙ АТЛАС`, etc.). No “Public Atlas” / “8,206 words” English labelling appears.
- **Why it hurts a learner:** The only obvious language control makes English harder, not easier.
- **Severity:** blocker
- **Screenshot:** `ui-scout-report/shots/003-desktop-lexicon-locale-eng.png`, `ui-scout-report/shots/075-locale-eng-viewport.png`
- **Console/network:** none specific

### 3. Latin typeahead (`voda`) returns suggestions
- **Surface:** `/lexicon/` search
- **Repro:** Type `voda`.
- **What happens:** Suggestion UI appears (listbox/option nodes present).
- **Why it hurts a learner:** (Does not — Latin entry works.)
- **Severity:** polish
- **Screenshot:** `ui-scout-report/shots/004-desktop-typeahead-latin-voda.png`

### 4. Escape clears search
- **Surface:** `/lexicon/` typeahead
- **Repro:** Open suggestions, press Escape.
- **What happens:** Input value becomes empty; options count 0.
- **Why it hurts a learner:** Aggressive clear may surprise users who only wanted to dismiss the dropdown.
- **Severity:** minor
- **Screenshot:** `ui-scout-report/shots/005-desktop-typeahead-escape.png`

### 5. Cyrillic typeahead (`вода`) works
- **Surface:** `/lexicon/` search
- **Repro:** Type `вода`.
- **What happens:** Options appear (including lemma + related phrases in later runs).
- **Severity:** polish
- **Screenshot:** `ui-scout-report/shots/006-desktop-typeahead-cyrillic-voda.png`

### 6. Paste into search works
- **Surface:** `/lexicon/` search
- **Repro:** Fill/paste `алергія`.
- **What happens:** At least one suggestion.
- **Severity:** polish
- **Screenshot:** `ui-scout-report/shots/007-desktop-typeahead-paste-alergiya.png`

### 7. Enter from `вода` lands on `гаряча вода`
- **Surface:** `/lexicon/` typeahead
- **Repro:** Type `вода`, ArrowDown, Enter.
- **What happens:** Navigates to `/lexicon/гаряча-вода/` (“hot water” multiword), not `/lexicon/вода/`.
- **Why it hurts a learner:** Common lemma search feels “wrong”; learner may think `вода` is missing.
- **Severity:** major
- **Screenshot:** `ui-scout-report/shots/008-desktop-typeahead-enter.png`

### 8. Browse landing states 8206 records
- **Surface:** `/lexicon/browse/`
- **Repro:** Open browse with no letter selected.
- **What happens:** Copy: **“8206 записів Атласу · 33 літери”**; prompt to choose a letter; alphabet is **buttons** (`button.atlas-letter-link`), not links.
- **Severity:** minor (positive clarity vs landing, still UA)
- **Screenshot:** `ui-scout-report/shots/009-desktop-browse-landing.png`

### 9. Browse global search returns hits
- **Surface:** `/lexicon/browse/?q=…`
- **Repro:** Search `вода`, Enter.
- **What happens:** URL `?q=вода`; UI reports **“2 збігів”** (2 matches).
- **Severity:** minor (works)
- **Screenshot:** `ui-scout-report/shots/010-desktop-browse-search-voda.png`, `ui-scout-report/shots/076-browse-search-voda-results.png`

### 10. Letters И and Ь are disabled zeros in the alphabet strip
- **Surface:** `/lexicon/browse/` letter nav
- **Repro:** Click every letter А–Я.
- **What happens:** 31 letters load rows with counts; letter totals sum to **8206**. **И** and **Ь** are `disabled`, class `is-empty`, `data-base-count="0"` — not clickable. Examples: Ж 54, Ц 59, Ю 7, Ґ 4, П 1451 (with “Показати ще” when capped at 150 visible links).
- **Why it hurts a learner:** Looks like a broken/incomplete alphabet unless the empty state is explained.
- **Severity:** major
- **Screenshot:** `ui-scout-report/shots/011-desktop-browse-letter-А.png`, `…-Ж.png`, `…-Ц.png`, `…-Ю.png`, `…-И-disabled.png`, `…-Ь-disabled.png`
- **Evidence:** `ui-scout-report/letter-results.json`

### 11. Word page `а`
- **Surface:** `/lexicon/а/`
- **Repro:** Open page.
- **What happens:** Loads; meaning/etymology/morphology/relations/course sections flagged present; **no `<audio>` / play control**; practice link `?lemmaId=а`.
- **Severity:** minor (no audio)
- **Screenshot:** `ui-scout-report/shots/020-desktop-word-a.png`

### 12. Word page `вода`
- **Surface:** `/lexicon/вода/`
- **Repro:** Open page; click etymology/ЕСУМ control if present.
- **What happens:** Dense entry; stress `[вода́]`; atlas data grid; practice link present; **no audio**; etymology control clickable.
- **Severity:** minor
- **Screenshot:** `ui-scout-report/shots/022-desktop-word-voda.png`, `021-…-ety.png`

### 13. Word page `алергія` (mid-tail)
- **Surface:** `/lexicon/алергія/`
- **Repro:** Open page.
- **What happens:** Loads with similar section pattern; practice link present; **no audio**.
- **Severity:** minor
- **Screenshot:** `ui-scout-report/shots/023-desktop-word-alergiya.png`

### 14. Word page from Ж — `жаба`
- **Surface:** `/lexicon/жаба/` (from browse Ж)
- **Repro:** Browse Ж → first row.
- **What happens:** Loads; **no “Практикувати це слово”** link observed; **no audio**.
- **Severity:** minor
- **Screenshot:** `ui-scout-report/shots/025-desktop-word-zh-жаба.png`

### 15. Word page from Ц — `цвіль`
- **Surface:** `/lexicon/цвіль/`
- **Repro:** Browse Ц → first row.
- **What happens:** Loads; practice link present; **no audio**.
- **Severity:** minor
- **Screenshot:** `ui-scout-report/shots/026-desktop-word-ts-цвіль.png`

### 16. Word page from Ю — `юліанський`
- **Surface:** `/lexicon/юліанський/`
- **Repro:** Browse Ю → first row.
- **What happens:** Loads; sparse main links; **no practice link**; **no audio**.
- **Severity:** minor
- **Screenshot:** `ui-scout-report/shots/027-desktop-word-yu-юліанський.png`

### 17. `вода` main links all resolve
- **Surface:** word page links
- **Repro:** Follow main/article internal links from `/lexicon/вода/`.
- **What happens:** 8 probed; **0 broken**.
- **Severity:** polish
- **Screenshot:** `ui-scout-report/shots/022-desktop-word-voda.png`

### 18. Practice hub: UA-only H1, intro, back/eyebrow (owner dual-language order)
- **Surface:** `/lexicon/practice` → `/words-of-the-day/practice/`
- **Repro:** Open practice hub in default УКР locale; inventory chrome.
- **What happens:** Redirect works. Many session/mode cards are dual (`Флешкартки / Flashcards`, stats with `/ EN` lines). **Ukrainian-only chrome a beginner hits immediately:**
  - Back control: `← Слова дня`
  - Eyebrow: `СЛОВА ДНЯ · ПРАКТИКА`
  - H1: `Практика`
  - Intro paragraph (no English sibling): *«Інтервальне повторення слів вашого рівня (CEFR, накопичувально) — картки, добір, вибір і пропуски. Прогрес зберігається локально у цьому браузері.»*
- **Why it hurts a learner:** Absolute beginner cannot understand what Practice is before any exercise starts (matches #5355 / owner dual-language order).
- **Severity:** blocker
- **Screenshot:** `ui-scout-report/shots/028-desktop-practice-hub.png`
- **Console/network:** `practice-index.A1.json` saw `net::ERR_ABORTED` once during session (desktop evidence bag)

### 19. “Start session” opens mixed flashcards with dual SRS chrome
- **Surface:** Practice hub → Почати сесію
- **Repro:** Click `Почати сесію / Start session`.
- **What happens:** Inline session: `Сесія 0/8 / Session 0/8`, `Мікс · Флешкартки / Mixed · Flashcards`, SRS `Ще раз/Again` … `Легко/Easy`. Lemma on card is UA (expected).
- **Severity:** minor (works; residual UA on site chrome above session)
- **Screenshot:** `ui-scout-report/shots/029-desktop-practice-session-started.png`

### 20. Keyboard path works but leaves “Skip to content” stuck on screen
- **Surface:** In-session practice
- **Repro:** After starting a session, press Space / Enter / Digit1 / Digit2 / ArrowRight / etc.
- **What happens:** Session advances (e.g. into Matching). A bright yellow **“Skip to content”** control remains painted over the layout after keyboard focus.
- **Why it hurts a learner:** Looks broken; obscures header/logo.
- **Severity:** major
- **Screenshot:** `ui-scout-report/shots/030-desktop-practice-keyboard-pass.png`, also visible on mode shots `031+`

### 21. Flashcards mode
- **Surface:** Focus practice → Флешкартки
- **Repro:** Click mode card.
- **What happens:** Dual title/buttons; card shows lemma + English POS.
- **Severity:** polish
- **Screenshot:** `ui-scout-report/shots/031-desktop-practice-mode-Флешкартки.png`

### 22. Matching mode
- **Surface:** Добір пар
- **Repro:** Click mode card.
- **What happens:** Dual instruction; UA column + English gloss column.
- **Severity:** polish
- **Screenshot:** `ui-scout-report/shots/033-desktop-practice-mode-Добір-пар.png`

### 23. Choice mode
- **Surface:** Вибір
- **Repro:** Click mode card.
- **What happens:** Dual stem e.g. `Яке слово означає «to listen»? / Which word means «to listen»?`; options are Ukrainian words (no EN on options — exercise content).
- **Severity:** polish
- **Screenshot:** `ui-scout-report/shots/035-desktop-practice-mode-Вибір.png`, `072-choice-detail.png`

### 24. Cloze placeholder truncated + Ukrainian-only
- **Surface:** Пропуск / Cloze
- **Repro:** Open cloze mode; inspect input placeholder.
- **What happens:** Prompt sentence UA with EN gloss beneath (`I see the school.`); Check button dual; **placeholder** reads truncated Ukrainian-only **`наберіть слово у потрібній фо`** (cuts off).
- **Why it hurts a learner:** Beginner cannot read the input hint; truncation looks buggy.
- **Severity:** major
- **Screenshot:** `ui-scout-report/shots/037-desktop-practice-mode-Пропуск.png`

### 25–27. Stress / Classify / Paradigm modes open
- **Surface:** Наголос, Група, Форма
- **Repro:** Open each mode card.
- **What happens:** Sessions start with dual titles; prompts generally bilingual in sampled runs.
- **Severity:** minor
- **Screenshots:** `039-…Наголос.png`, `041-…Група.png`, `043-…Форма.png`

### 28. Synonyms mode empty (0/0) with UA-only message
- **Surface:** Синоніми
- **Repro:** Click Synonyms at A1 with fresh local progress.
- **What happens:** `Сесія 0/0`; message **«Усі картки на зараз повторено.»** (no English sibling on that line).
- **Why it hurts a learner:** Dead-end “mode” with no explanation in English.
- **Severity:** major
- **Screenshot:** `ui-scout-report/shots/073-synonyms-empty.png`, `045-desktop-practice-mode-Синоніми.png`

### 29. Paronyms mode opens
- **Surface:** Пароніми
- **Repro:** Click mode.
- **What happens:** Items appear (sampled).
- **Severity:** minor
- **Screenshot:** `ui-scout-report/shots/047-desktop-practice-mode-Пароніми.png`

### 30. Heritage mode not ready for level (UA-only)
- **Surface:** Спадщина
- **Repro:** Click Heritage at A1.
- **What happens:** **«Вправи зі спадщини для цього рівня ще готуються.»** — Ukrainian-only empty state.
- **Severity:** major
- **Screenshot:** `ui-scout-report/shots/074-heritage-empty.png`, `049-…Спадщина.png`

### 31. Words of the Day landing
- **Surface:** `/words-of-the-day/`
- **Repro:** Open page.
- **What happens:** Dual H1 `Слова дня / Words of the Day`; practice CTA; A1–C2 chips; cards show lemma + EN gloss.
- **Severity:** minor
- **Screenshot:** `ui-scout-report/shots/051-desktop-wotd.png`

### 32. WOTD word cards link into Atlas
- **Surface:** WOTD → `/lexicon/{lemma}/`
- **Repro:** Click a daily word card (not the nav “Word Atlas” item).
- **What happens:** Cards link to encoded lemma URLs (e.g. `/lexicon/фінал/`). Nav “Word Atlas” separately goes to `/lexicon/`.
- **Severity:** polish
- **Screenshot:** `ui-scout-report/shots/052-desktop-wotd-to-atlas.png` (nav path); card hrefs recorded in scout log

### 33. Reading reference cross-nav
- **Surface:** Nav → `/readings/`
- **Repro:** Click “Reading reference”.
- **What happens:** Lands on Reading reference; English page title vs UA-heavy Atlas/Practice chrome.
- **Severity:** minor
- **Screenshot:** `ui-scout-report/shots/053-desktop-reading.png`

### 34–35. Non-existent word URLs: 404 + “loading” + missing `atlas/current.json`
- **Surface:** `/lexicon/{missing}/`
- **Repro:** Open `/lexicon/неіснуючесловоxyzqqq/` and `/lexicon/zzzz-not-a-lemma-999/`.
- **What happens:** HTTP 404. Page title `Page Not Found`. Body mixes English 404 copy with Ukrainian footer when locale=`ENG`. Also shows **«Завантаження статті Атласу…»** (loading atlas article) on the 404 surface. Network: page URL **404**; **`https://learn-ukrainian.github.io/atlas/current.json` → 404**; console `Failed to load resource: … 404`.
- **Why it hurts a learner:** Conflicting “not found” vs “loading”; no clear search box to recover the typo.
- **Severity:** major
- **Screenshot:** `ui-scout-report/shots/054-desktop-404-неіснуючесловоxyzq.png`, `055-desktop-404-zzzz-not-a-lemma-9.png`, `077-404-detail.png`
- **Console/network:** `atlas/current.json` 404; document 404

### 36–42. Mobile 390px — no overflow; denser UA chrome
- **Surface:** `/lexicon/`, browse, `вода`, practice, WOTD, typeahead, browse Ж
- **Repro:** 390×844 viewport.
- **What happens:** `scrollWidth === clientWidth` on probed pages (no horizontal overflow). Letter strip and stats wrap tightly; hamburger `Menu`. Typeahead for `вода` shows suggestions.
- **Severity:** minor
- **Screenshots:** `056–067-mobile-*.png`

### 43. Mobile practice — same hub language gap
- **Surface:** Practice @390px
- **Repro:** Open hub; start session.
- **What happens:** Same UA-only H1/intro/back; in-session classify sample was dual (`Which group does «…» belong to?`).
- **Severity:** blocker (same as #18 on the device beginners use)
- **Screenshot:** `ui-scout-report/shots/068-mobile-practice-session.png`, `063-mobile-practice-viewport.png`

### 44–46. Mobile flashcards / choice / cloze
- **Surface:** Modes @390px
- **Repro:** Tap each mode card.
- **What happens:** Modes render; cloze inherits truncated UA placeholder.
- **Severity:** minor (cloze placeholder already major in #24)
- **Screenshots:** `069–071-mobile-mode-*.png`

---

## Practice language inventory (beginner-visible UA-only)

Recorded on live hub / sessions (dual lines that also have English siblings are **not** listed):

| String (as shown) | Where |
| --- | --- |
| `← Слова дня` | Practice hub back control |
| `СЛОВА ДНЯ · ПРАКТИКА` | Practice eyebrow |
| `Практика` | H1 |
| Intro paragraph about інтервальне повторення… (full UA paragraph, no EN) | Under H1 |
| `наберіть слово у потрібній фо` (truncated) | Cloze input placeholder |
| `Усі картки на зараз повторено.` | Synonyms empty state |
| `Вправи зі спадщини для цього рівня ще готуються.` | Heritage empty state |
| Word-page chrome such as `Дані Атласу`, `Практикувати це слово →`, section titles | Atlas entries (not practice, but learner-facing) |

In-session SRS / mode titles sampled (`Ще раз / Again`, `Вибір / Choice`, etc.) **are dual** when the English line is present.

---

## Console & network bag (session-level)

**Desktop**
- Console errors: `Failed to load resource: the server responded with a status of 404 ()` (tied to missing lemma URLs and `/atlas/current.json`).
- Network ≥400:  
  - `GET /lexicon/{missing}/` → 404  
  - `GET /atlas/current.json` → 404 (seen when hitting missing lemma routes)  
- Request failed: `GET /lexicon/practice-index.A1.json` → `net::ERR_ABORTED` (at least once)

**Mobile 390:** no console errors / 4xx captured in the mobile evidence bag for the happy-path pages probed.

---

## Artifact index

| Path | Contents |
| --- | --- |
| `ui-scout-report/REPORT.md` | This report |
| `ui-scout-report/shots/*.png` | 77 screenshots |
| `ui-scout-report/findings.json` | Machine findings + console bags |
| `ui-scout-report/letter-results.json` | Per-letter browse counts |
| `ui-scout-report/word-pages.json` | Six word-page probes |
| `ui-scout-report/practice-modes.json` | Ten mode probes |
| `ui-scout-report/scout.mjs` | Reproducible Playwright scout script |

---

*End of scout report. No site code was modified.*
