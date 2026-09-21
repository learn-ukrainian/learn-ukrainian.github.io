# Practice Hub Scouting Synthesis & UI Backlog Plan (#8325, #8326)

**Date:** 2026-09-21
**Author:** Yellow Team (Gemini Atlas Driver)
**Evaluator:** Anthropic Claude family (`claude-sonnet-5` independent evaluation)
**Epic:** #4387 (Word Atlas + Practice Hub)
**Parent Program:** #8326
**Synthesis Issue:** #8325
**Live Target:** `https://learn-ukrainian.github.io`
**Deployed SHA:** `e4efde4fde52ee0b773928a5bf9346c8cc2f2c1c`
**Atlas Data Version:** `atlas-v1-90605067cb27589f`
**Practice Deck Version:** `atlas-practice-v1-c0c3f3242b5134b6`
**Evidence Store:** GitHub Release `practice-scouting` (150+ traces & screenshots)

---

## 1. Executive Summary & "What Good Looks Like" (AC-05)

### What Good Looks Like
> A learner landing on Practice should feel immediate clarity and momentum: one tap from anywhere on the site, zero dead ends, clear level boundaries, and exercises that respond instantly with rich pedagogical feedback. Ukrainian immersion is central, supported by English scaffolding on A1/A2 and course tiles that guides rather than confuses. No broken layouts, no silent failures, and no unfulfilled promises—every card and tile either delivers active learning or honestly communicates what is coming next.

### Key Outcomes of Program C
1. **Practice is a First-Class Destination**: Delivered via #8328 (PR #8364, commit `dde9bfed6a`) and deployed to production. The primary S1 blocker identified in baseline scouting (missing navigation and direct `/practice/` 404) is 100% resolved and verified live.
2. **Comprehensive Live Audit Complete**: Slices C1 through C8 executed across Desktop Chrome, iPhone 14, and Pixel 7 device profiles. All 12 practice modes and 10 exam decks evaluated under authentic learner conditions.
3. **Independent Evaluation Verified**: `claude-sonnet-5` evaluated 5 held-out unscripted journeys (all passed) and spot-checked 10 "none" interaction behaviors across 9 distinct matrix rows (10/10 agreed, with C2-05 tested across both Matching and Choice sub-modes). Zero valid findings were rejected.
4. **Ranked Backlog Filed**: 8 concrete, ready-to-dispatch practice task cards filed under stream epic #4387 (`[4387][practice-ux]` and `[4387][practice-content]`), addressing the practice hub S2 defects, in-practice friction points, accessibility targets, and future card decks (with lexical entry cross-linking C1-05 tracked in #8316).

---

## 2. Complete Finding Ledger (AC-01)

### Breakdown by Observation, Status, and Severity (Exact Counts)

| Dimension | Category | Count | Notes |
|---|---|---|---|
| **Observation** | `none` | 16 | Flawless interactions verified across modes & settings |
| | `defect` | 10 | Layout overflow, 404 missing manifests/shards |
| | `friction` | 9 | Level-switch guidance, mobile mixed transition, course labels |
| | `content` | 1 | ЗНО/Culture audience mismatch for A2 persona |
| **Status** | `live` | 31 | Present on live deployed production site |
| | `fixed / resolved` | 3 | C1-01 (/practice/ route), C1-02 (header nav), C1-03 (home card) |
| | `announced-unfinished`| 2 | Synonym & Imperative tiles display "0 · No exercises yet" |
| **Severity** | `S1` | 2 | Both resolved and verified live by #8328 |
| | `S2` | 15 | Layout overflow, console 404s, level-gate friction |
| | `S3` | 19 | Working flows (16), announced-unfinished (2), mobile touch targets (1) |
| **Total Rows** | | **36** | Denominator-complete across all 8 slices (7+5+5+4+4+4+3+4) |

### Itemized Finding Matrix

| ID | Slice | Surface | Viewport | Obs | Status | Sev | Description | Dedup / Tracking |
|---|---|---|---|---|---|---|---|---|
| C1-01 | C1 | `/practice/` | All | `defect` | `fixed` | S1 | Direct `/practice/` returned 404 | Resolved in PR #8364; verified HTTP 200 live |
| C1-02 | C1 | Nav Header | Desktop | `defect` | `fixed` | S1 | Practice link missing in header nav | Resolved in PR #8364; verified 1-click live |
| C1-03 | C1 | Home Page | All | `friction`| `fixed` | S2 | Practice card missing on index page | Resolved in PR #8364; "Available Now" card live |
| C1-04 | C1 | Words of the Day | All | `none` | `live` | S3 | Practice banner present and clickable | Verified 1-click live |
| C1-05 | C1 | Word Pages | All | `friction`| `live` | S2 | Lexicon entry pages lack CTA to practice | Routed to #8316 (Atlas entry enrichment) |
| C1-06 | C1 | Flashcards | All | `none` | `live` | S3 | 8-card A1 session completes to end-screen | Verified with score & streak counters |
| C1-07 | C1 | Landing TTFI | All | `none` | `live` | S3 | First control visible in ~1.1s, enabled ~1.4s | Verified prompt skeleton replacement |
| C2-01 | C2 | Main session | Desktop | `defect` | `live` | S2 | Horizontal scrollbar on desktop during session | Primary for #8377 (desktop overflow) |
| C2-02 | C2 | Pronunciation | All | `defect` | `live` | S2 | 404 on `/audio/pronunciation/manifest.json` | Primary for #8378 (audio manifest 404) |
| C2-03 | C2 | Imperative shards | All | `defect` | `live` | S2 | Background 404s for imperative shards | Primary for #8379 (imperative shard 404s) |
| C2-04 | C2 | Mixed mode button | Phone | `friction`| `live` | S2 | Mixed click remains on daily hero | Primary for #8382 (mobile mixed transition) |
| C2-05 | C2 | Core modes | All | `none` | `live` | S3 | Flashcards, Matching, Choice interactive | Verified state updates and transitions |
| C3-01 | C3 | Synonym tile | All | `friction`| `announced`| S3 | Tile disabled with "0 · No exercises yet" | Tracked in #8386 (practice decks for Synonym & Imperative modes) |
| C3-02 | C3 | Paronym tile | All | `friction`| `live` | S2 | Enabled at A1 but clicks do not launch session | Primary for #8380 (level-gate feedback) |
| C3-03 | C3 | Heritage tile | All | `friction`| `live` | S2 | Enabled at A1 with 2 items but no session start | Deduplicated into #8380 (level-gate feedback) |
| C3-04 | C3 | Cloze mode | All | `none` | `live` | S3 | Sentences render with textbook citations | Verified textbook source attribution |
| C3-05 | C3 | Imperative shards | All | `defect` | `live` | S2 | Background 404 on imperative shards | Deduplicated into #8379 |
| C4-01 | C4 | Paradigm mode | All | `none` | `live` | S3 | Case selector chips and prompt interactive | Verified case filtering mechanics |
| C4-02 | C4 | Imperative tile | Phone | `friction`| `announced`| S3 | Disabled on mobile with "0 · No exercises yet"| Tracked in #8386 (practice decks for Synonym & Imperative modes) |
| C4-03 | C4 | Imperative shards | All | `defect` | `live` | S2 | Background 404 on imperative shards | Deduplicated into #8379 |
| C4-04 | C4 | Paradigm layout | Desktop | `defect` | `live` | S2 | Desktop horizontal overflow in paradigm | Deduplicated into #8377 |
| C5-01 | C5 | Classify mode | All | `none` | `live` | S3 | Category selection chips function cleanly | Verified grammar category updates |
| C5-02 | C5 | Stress mode | All | `none` | `live` | S3 | Stress stage renders clickable syllables | Verified syllable target responsiveness |
| C5-03 | C5 | Classify layout | Desktop | `defect` | `live` | S2 | Desktop horizontal overflow in classify | Deduplicated into #8377 |
| C5-04 | C5 | Imperative shards | All | `defect` | `live` | S2 | Background 404 on imperative shards | Deduplicated into #8379 |
| C6-01 | C6 | Course tiles | All | `friction`| `live` | S2 | 10 tile labels Ukrainian-only on English UI | Primary for #8381 (course subtitles) |
| C6-02 | C6 | Culture of Speech| All | `none` | `live` | S3 | Error-correction sentence options interactive | Verified selection and error highlights |
| C6-03 | C6 | 9 ЗНО decks | All | `none` | `live` | S3 | Authentic Ukrainian exam questions render | Verified question counters and options |
| C6-04 | C6 | Exam audience | All | `content` | `live` | S2 | All 10 decks judged advanced-only (B2–C1) | Primary for #8381 (difficulty badges & CEFR scaffolding) |
| C7-01 | C7 | Settings drawer | All | `none` | `live` | S3 | Settings drawer opens with deck options | Verified 3 active deck options |
| C7-02 | C7 | Settings Escape | All | `none` | `live` | S3 | Drawer dismissed by Escape key | Verified keyboard accessibility |
| C7-03 | C7 | Level switcher | All | `none` | `live` | S3 | Level chips toggle curriculum level | Verified level filtering updates |
| C8-01 | C8 | Phone loading | Phone | `none` | `live` | S3 | TTFI 553–669ms; skeleton resolves promptly | Refutes seed observation |
| C8-02 | C8 | Phone Flashcards | Phone | `none` | `live` | S3 | Complete 8-card session completed | Verified score and streak progression |
| C8-03 | C8 | Phone Matching | Phone | `none` | `live` | S3 | Touch selection and pair resolution work | Verified responsive mobile matching |
| C8-04 | C8 | Header targets | Phone | `friction`| `live` | S3 | Two buttons in header measure <44px | Primary for #8383 (mobile touch targets) |

---

## 3. Independent Evaluation Report (AC-02)

*Conducted by `claude-sonnet-5` (Anthropic Claude family) on 2026-09-21 against live production deployment `e4efde4fde52ee0b773928a5bf9346c8cc2f2c1c`.*

### Five Held-Out Journeys

| Journey | Description | Result | Verdict | Evidence Assets (Release `practice-scouting`) |
|---|---|---|---|---|
| **H1: Session budget 20** | Selected budget 20, started Flashcards; verified card count respects available card pool | Budget 20 active, progress 0/8 (capped to available due cards) | **PASS** | `2026-09-21T06-57-37-427Z-eval-H1-session-budget-20-budget-20-started.png`, `2026-09-21T06-57-37-427Z-eval-H1-session-budget-20.zip` |
| **H2: Interruption & Resumption** | Completed 1 card, navigated away to `/`, returned to `/practice/`; verified storage state | Progress 1/8 before nav; `hasStorage: true` preserved on return | **PASS** | `2026-09-21T06-57-37-427Z-eval-H2-interruption-resumption-mid-session.png`, `2026-09-21T06-57-37-427Z-eval-H2-interruption-resumption-after-return.png`, `2026-09-21T06-57-37-427Z-eval-H2-interruption-resumption.zip` |
| **H3: Secondary tools in Settings** | Opened settings drawer, expanded secondary tools summary | Expanded successfully; revealed custom deck studio, import/export controls | **PASS** | `2026-09-21T06-57-37-427Z-eval-H3-settings-secondary-tools-secondary-tools-open.png`, `2026-09-21T06-57-37-427Z-eval-H3-settings-secondary-tools.zip` |
| **H4: Theme & Locale toggle** | Toggled theme and language on `/practice/`; verified DOM classes and bilingual headers | Dark mode toggled; language toggle active; zero broken layout | **PASS** | `2026-09-21T06-57-37-427Z-eval-H4-theme-locale-toggle-theme-locale-state.png`, `2026-09-21T06-57-37-427Z-eval-H4-theme-locale-toggle.zip` |
| **H5: Keyboard-only navigation** | Focused card, pressed `Space` to flip, rated, pressed `Enter` to advance | Card flipped cleanly with `Space`, advanced via `Enter` | **PASS** | `2026-09-21T06-57-37-427Z-eval-H5-keyboard-navigation-keyboard-session-advance.png`, `2026-09-21T06-57-37-427Z-eval-H5-keyboard-navigation.zip` |

### Ten Spot-Checks of "None" Findings (Across 9 Distinct Rows)

*Note: SC-02 and SC-03 independently evaluate the Matching and Choice interactive sub-modes bundled under matrix row C2-05.*

| Check | Target Finding | Evaluator Observation | Verdict | Evidence Assets (Release `practice-scouting`) |
|---|---|---|---|---|
| **SC-01** | C1-06 (Flashcards complete) | Flashcards session completes with summary screen and continue links | **AGREE** | `2026-09-21T06-57-37-427Z-eval-SC1-flashcards-complete-end-screen.png`, `2026-09-21T06-57-37-427Z-eval-SC1-flashcards-complete.zip` |
| **SC-02** | C2-05 (Matching mode) | Matching tiles render and resolve matching pairs cleanly | **AGREE** | `2026-09-21T06-57-37-427Z-eval-SC2-matching-mode-matching-active.png`, `2026-09-21T06-57-37-427Z-eval-SC2-matching-mode.zip` |
| **SC-03** | C2-05 (Choice mode) | Choice options render and submit selection state | **AGREE** | `2026-09-21T06-57-37-427Z-eval-SC3-choice-mode-choice-selected.png`, `2026-09-21T06-57-37-427Z-eval-SC3-choice-mode.zip` |
| **SC-04** | C3-04 (Cloze citations) | Cloze displays textbook citation: "Ukrainian school textbook — Kravtsova 2021" | **AGREE** | `2026-09-21T06-57-37-427Z-eval-SC4-cloze-citations-cloze-citation.png`, `2026-09-21T06-57-37-427Z-eval-SC4-cloze-citations.zip` |
| **SC-05** | C4-01 (Paradigm cases) | Paradigm mode displays active case selection chips | **AGREE** | `2026-09-21T06-57-37-427Z-eval-SC5-paradigm-cases-paradigm-cases.png`, `2026-09-21T06-57-37-427Z-eval-SC5-paradigm-cases.zip` |
| **SC-06** | C5-01 (Classify mode) | Classify mode renders grammatical category options | **AGREE** | `2026-09-21T06-57-37-427Z-eval-SC6-classify-mode-classify-active.png`, `2026-09-21T06-57-37-427Z-eval-SC6-classify-mode.zip` |
| **SC-07** | C5-02 (Stress stage) | Stress stage renders interactive syllable targets | **AGREE** | `2026-09-21T06-57-37-427Z-eval-SC7-stress-stage-stress-stage.png`, `2026-09-21T06-57-37-427Z-eval-SC7-stress-stage.zip` |
| **SC-08** | C6-02 (Culture of Speech) | Culture of Speech displays interactive sentence error-correction prompt | **AGREE** | `2026-09-21T06-57-37-427Z-eval-SC8-culture-speech-culture-session.png`, `2026-09-21T06-57-37-427Z-eval-SC8-culture-speech.zip` |
| **SC-09** | C6-03 (ЗНО exam deck) | ЗНО Orthography session renders authentic exam multiple-choice item | **AGREE** | `2026-09-21T06-57-37-427Z-eval-SC9-zno-deck-zno-session.png`, `2026-09-21T06-57-37-427Z-eval-SC9-zno-deck.zip` |
| **SC-10** | C7-02 (Settings Escape) | Settings drawer dismissed immediately by Escape key: true | **AGREE** | Full Playwright action trace: `2026-09-21T06-57-37-427Z-eval-SC10-settings-escape.zip` (DOM drawer visibility transition verified; trace records Escape keypress) |

### Rejected Findings Audit
- **Audit result:** Zero S1 or S2 findings were rejected or hidden. All real defect and friction observations were captured in the ledger.

---

## 4. Ranked Practice UI Backlog (AC-03)

The following 8 task cards have been formally created on GitHub under stream epic #4387 (`[4387][practice-ux]` and `[4387][practice-content]`):

1. **#8377**: `[4387][practice-ux] Fix desktop horizontal overflow during active practice sessions` (S2 Defect)
2. **#8378**: `[4387][practice-ux] Suppress missing audio pronunciation manifest 404 on Flashcard sessions` (S2 Defect)
3. **#8379**: `[4387][practice-ux] Prevent background 404 fetches for undeployed imperative practice shards` (S2 Defect)
4. **#8380**: `[4387][practice-ux] Level-gate feedback and empty-state messaging for Paronyms and Heritage tiles` (S2 Friction)
5. **#8381**: `[4387][practice-ux] Add English subtitles, CEFR level badges, and scaffolding to 10 exam and course tiles on English UI` (S2 Friction / Content — covers C6-01 subtitles and C6-04 exam audience scaffolding)
6. **#8382**: `[4387][practice-ux] Direct-to-session transition on mobile Mixed mode click` (S2 Friction)
7. **#8383**: `[4387][practice-ux] Increase mobile header touch targets to 44px minimum` (S3 Polish)
8. **#8386**: `[4387][practice-content] Author and deploy practice card decks for Synonym and Imperative modes` (S3 Polish / Content — covers C3-01 and C4-02)

---

## 5. Status of Blocking (S1) Findings (AC-04)

- **Finding C1-01 / C1-02**: In the pre-#8328 baseline, Practice was not discoverable from main navigation and direct URL `/practice/` returned a 404.
- **Resolution**: Implemented in PR #8364 (#8328), reviewed and approved by Codex (`review-8328-codex-r2` / `gpt-6-astra`), merged to `main` at commit `dde9bfed6a`.
- **Live Deployment & Verification**: Deployed to GitHub Pages at commit `e4efde4fde`. Re-run C1 post-fix test suite (entry points e1–e7 across Desktop, iPhone, and Android profiles) verified that `/practice/` returns HTTP 200, and is 1 click from home (e1), header nav (e2), mobile drawer menu (e3), and footer (e4). Exact trace evidence in release `practice-scouting`: `2026-09-21T00-06-32-732Z-c1-desktop-e1-home.zip`, `...-c1-desktop-e2-header-nav.zip`, `...-c1-phone-e3-phone-menu.zip`, `...-c1-desktop-e4-footer.zip`, `...-c1-desktop-e7-direct-practice-url.zip`.
- **Residual S1**: **Zero unresolved S1 blockers remain.**
