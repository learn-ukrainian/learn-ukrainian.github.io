# Seminar-content writer/reviewer scorecard — «Веснянки» fact-check (2026-07-04)

> Companion to `REPORT.md` (the deterministic UK-writing bakeoff, #4330). That probe found all 5
> candidates wrote **0-russicism, 95–100%-VESUM** prose on every profile — so it **cannot rank seminar
> content**, where the differentiator is FACTUAL ACCURACY, not surface cleanliness. This scorecard closes
> that gap with a **tool-backed fact-check** of the seminar sample (`## SECTION 3`, topic «Веснянки» /
> spring ritual songs), cross-verified by an independent-family fleet review.

## Method
1. **Deterministic layer (already done, #4330):** VESUM morphology + russian-shadow → all 5 clean. Not rankable.
2. **Fact-check layer (this doc):** every falsifiable claim in the 5 seminar passages verified against
   `mcp__sources__query_wikipedia` (uk.wikipedia «Веснянки», «Царинні пісні»), VESUM `verify_word`.
3. **Cross-family review layer:** the fact-check + the 5 passages sent to **codex + agy + deepseek**
   (independent families) to adversarially challenge the findings and catch anything missed.

## Verified reference facts (uk.wikipedia «Веснянки» / «Царинні пісні» / VESUM)
- **Веснянки** = old Slavic spring ritual songs. Calendar: first веснянка at **Стрітення (2 Feb)** →
  from **Благовіщення (25 Mar)** almost nightly → **until Івана Купала (24 June)**, after which
  жниварські (harvest) songs begin.
- **гаївки / гагілки** = the **western-region** name; tied to **Easter**; performed in **groves**
  (etym. «гай»). Ф. Колесса: гаївки sung *only* at Easter; веснянки span the whole spring cycle.
- **царинні пісні** = «царина» = the field beyond the village; songs of the **field-boundary
  procession («обхід поля») on Трійця**, aesthetically linked to колядки. A recognized subtype of
  веснянки (O. Голубець: закличні / хороводні / гаївки / юр'ївські / царинні / русальні-тройцькі).
- **Melodies:** narrow range, 1–2 repeated поспівки, closing **гукання / вигуки-заклички** — "most
  archaic in the Slavic мелос" is sourced.
- **Mainstream веснянки** = communal **open / liminal-space** ritual (hills, fences, riverbanks — chosen
  for acoustic carrying); **NOT house-to-house**. House-visiting spring songs = риндзівки / волочебні
  (regional, typically sung by парубки).

## Fact-check scorecard

| Candidate | Factual accuracy | Errors found |
|---|---|---|
| **codex** (gpt-5.5) | ✅ **Highest** | none — obeyed the brief ("do not invent specific attributions"); zero falsifiable claims, all statements general-and-true |
| **claude** | ✅ High | none — гаївки western/Easter ✓, calendar-ritual ✓, courtship/marriage motifs ✓, open-space gathering ✓ |
| **agy** | ✅ **Clean** | «біля церкви» is **accurate**, not an embellishment — the canonical Easter гаївки location in Western Ukraine is the churchyard/цвинтар (confirmed on cross-review by agy + codex; my initial "embellishment" flag was withdrawn). Modern jazz/electronica reinterpretation ✓ |
| **deepseek** | ⚠️ Richest, **highest-risk** | **HARD ERROR:** царинні = «пов'язані з першим вигоном худоби» (first cattle drive) is **WRONG** — царинні = field-boundary procession («обхід поля») on Трійця; deepseek conflated it with **юр'ївські** (Юрій Весняний cattle-drive) songs. _Confirmed independently by agy + codex with sources._ **Soft flag (decolonization overcorrection, per codex):** «не є частиною… східнослов'янської… культури» over-reaches — веснянки **are** old Slavic ritual songs ethnographically; the decolonized move is rejecting the imperial/Soviet lens, not the Slavic classification. Everything else (narrow звукоряд ✓, гаївки etymology ✓, гукання ✓) sourced and correct. _(My earlier «до Зелених свят» flag was **withdrawn** on cross-review: Зелені свята/Трійця is a canonical spring→summer cycle boundary — defensible, not an error.)_ |
| **cursor** | ⚠️ **Worst — 2 hard errors** | **HARD ERROR 1:** «ходили від хати до хати, вітали господарів» conflates веснянки with **риндзівки/волочебні** (Easter house-visiting songs, sung by парубки) — mainstream веснянка = open-space communal ritual. **HARD ERROR 2** _(missed on my first pass, caught by agy + codex):_ «Мелодії… легкі, м'які, співочі — на відміну від колядок» is **backward** — веснянки have archaic narrow-range melodies with piercing, high-tessitura delivery and гукання/вигуки-заклички; it is колядки/щедрівки that are the more lyrical/«співочі» genre. Cursor inverted the core musical phenomenology. Plus non-canonical **U+2019** apostrophes (13, per #4330). |

## The lesson this proves
The prior seminar ranking put **deepseek #1 on scholarly *tone*** — its three-way typology (власне
веснянки / гаївки / царинні), Slavic-мелос musicology, and narrow-звукоряд detail *read* as the most
authoritative. **Tool-verification inverts that:** deepseek's confident specificity is exactly where its
single hard factual error hides (царинні = cattle drive). **"Sounds scholarly" ≠ "is accurate."**
Confident specificity is the HIGHEST-risk seminar content until sourced — which is why the
`seminar-content-review` skill + this fact-check exist. codex's *discipline* (refusing to over-specify)
makes it the safest seminar writer; the strongest writers here are the ones who did not reach past what
they could ground.

## Cross-family review (codex · agy · deepseek)
Three independent-family reviewers adversarially challenged the fact-check above (each told to default to
"finding stands" only if unable to refute). **Unanimous outcome:**

- **Both hard errors confirmed with sources by all three.** codex + deepseek cited the uk.wikipedia
  «Царинні пісні» / «Юрій Весняний» / «Риндзівки» / «Волочебні» pages; **deepseek conceded its own error**
  ("CANNOT REFUTE — the orchestrator's finding stands"). The cattle-drive function belongs to **юр'ївські**
  (St. George / first pasture), not царинні.
- **A third hard error surfaced by review (I missed it), confirmed by all three:** cursor's
  «мелодії легкі, м'які, співочі» inverts the musicology — веснянки are the *archaic, narrow-range,
  piercing-гукання* layer; колядки/щедрівки are the lyrical ones.
- **Two of my flags withdrawn on review:** deepseek's «до Зелених свят» (agy: canonical spring→summer
  cycle boundary, not an error) and agy's «біля церкви» (agy + codex: accurate for Galician гаївки).
- **Nuances added:** (deepseek) its own three-way split «власне веснянки / гаївки / царинні» presents an
  **incomplete typology as complete** — Holubets lists six subtypes — and conflates «власне веснянки»
  with «закличні»; (deepseek) cursor's house-to-house error is best framed as *over-generalising the
  regional* **риндзівки** *variant into THE defining practice*, not free fabrication; (codex) deepseek's
  «не є частиною східнослов'янської культури» over-corrects — reject the imperial/Soviet lens, not the
  Slavic ethnographic classification.
- **Routing: unanimous agreement.** Writers = codex/claude/agy; folk carve-out (no deepseek) endorsed by
  all three. codex + deepseek both stress deepseek-as-reviewer must be **paired with a source-enforced
  fact-check gate** (exactly what `seminar-content-review` + the `sources` MCP provide), never a bare LLM pass.

## Routing decision (user, 2026-07-04)
- **Seminar WRITERS → codex + claude + agy** — the top-3 on factual accuracy, mutually cross-family.
- **Seminar REVIEWER → deepseek** (most scholarly; strongest at typology/musicology) **+ agy**, for
  **non-folk** seminars (HIST, BIO, LIT, OES, ISTORIO, RUTH) — **always paired with a source-enforced
  fact-check gate** (`seminar-content-review` skill + `sources` MCP), never a bare LLM pass. deepseek's
  own царинні slip is the reason: confident scholarly specificity must be verified, not trusted.
- **FOLK carve-out (hard rule, unchanged):** **NO deepseek for folk culture.** deepseek's царинні error
  here is fresh empirical proof it can be confidently wrong on folk-culture specifics. Folk review stays
  **cross-family GPT↔Claude** (writer's cross-family peer, or agy) per `docs/folk-epic/folk-review-rubric.md`.
