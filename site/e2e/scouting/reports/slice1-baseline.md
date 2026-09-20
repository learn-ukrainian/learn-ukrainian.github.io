# Practice Hub scouting — Slice 1 baseline (#8317)

- Target: https://learn-ukrainian.github.io (live), run `2026-09-20T20-14-53Z`
- Harness: `site/e2e/scouting/run.mjs --slice C1 --live` (Chromium; phone/android are Playwright device emulation; WebKit not installed on this host)
- Evidence: immutable assets on the `practice-scouting` release, named `2026-09-20T20-14-53-956Z-c1-<profile>-<journey>.zip` (traces) and `….png` (screenshots); full machine report `2026-09-20T20-14-53-956Z-report-c1.{json,md}`.
- One run per profile on a fast network: timings are indicative, not a distribution. Profiles: desktop, phone (iPhone 14), android (Pixel 7).
- Denominator covered: Home `/`, header nav, phone menu, footer, `/words-of-the-day/`, word page, direct `/practice/`, plus the first A1 Flashcards session and landing TTFI.

## Findings

### F-01 — Direct `/practice/` is a 404
- **Surface:** `/practice/` (direct URL)
- **Viewport:** all (desktop, phone, android)
- **Observation:** HTTP 404, title "Page Not Found". The hub lives only at `/words-of-the-day/practice/`.
- **Status:** confirmed, reproducible
- **Severity:** medium (baseline for #8328)
- **What the learner sees:** A "Page Not Found" screen when typing or sharing the obvious URL.
- **Expected:** `/practice/` reaches (or redirects to) the Practice Hub.
- **Repro steps:** Open `https://learn-ukrainian.github.io/practice/`.
- **Evidence:** journey `e7-direct-practice-url` (trace + `-direct-practice.png`, all profiles).

### F-02 — Home page has no route to practice
- **Surface:** Home `/` main content
- **Viewport:** all
- **Observation:** The only "practice" link in `main` is the B1 card (`/b1/practice-exam/`, a different feature). No link to the hub.
- **Status:** confirmed
- **Severity:** high
- **What the learner sees:** No visible way to drill words from the home page.
- **Expected:** A direct practice entry on home.
- **Repro steps:** Open `/`; look for practice links in the page body.
- **Evidence:** journey `e1-home` (`reached:false`, `practiceLinksInScope:1`, non-hub).

### F-03 — Header, phone menu and footer reach practice only in 2 clicks, via "Words of the Day"
- **Surface:** Header nav (`nav.lu-nav`), phone menu (`details.lu-mobile-menu`), footer
- **Viewport:** header nav: desktop only (hidden on phone/android); phone menu: phone/android only; footer: all
- **Observation:** No direct hub link in any of the three; each reaches `/words-of-the-day/` first, then the "Practice — spaced repetition…" link. 2 clicks each.
- **Status:** confirmed
- **Severity:** medium
- **What the learner sees:** Nav labels never say "practice"; the drills are hidden under "Words of the Day".
- **Expected:** A labelled practice entry (or 1-click path) in global navigation.
- **Repro steps:** Open `/`; use header nav (desktop) / hamburger menu (phone) / footer → "Words of the Day" → practice link.
- **Evidence:** journeys `e2-header-nav`, `e3-phone-menu`, `e4-footer`. (`e2` on phone and `e3` on desktop are n/a by viewport.)

### F-04 — `/words-of-the-day/` links directly to practice (1 click)
- **Surface:** `/words-of-the-day/`
- **Viewport:** all
- **Observation:** 2 practice links in `main`; first one reaches the hub. This is the only 1-click entry found.
- **Status:** confirmed (positive baseline)
- **Severity:** info
- **What the learner sees:** A clear practice card.
- **Expected:** —
- **Repro steps:** Open `/words-of-the-day/`, click the practice card.
- **Evidence:** journey `e5-words-of-the-day`.

### F-05 — Word pages return 404 on the live site, so no practice entry is testable
- **Surface:** `/lexicon/вода/`, `/lexicon/офіс/`, `/lexicon/вареник/`, and the first hit of a `/lexicon/browse/` search
- **Viewport:** all
- **Observation:** HTTP 404 "Page Not Found" for each. Browse search for "вода" returns "брила" first, whose link `/lexicon/брила/` is also a 404. `/lexicon/` itself is 200.
- **Status:** confirmed at run time; could be a partial deploy or unpublished lemma pages — not root-caused here
- **Severity:** high
- **What the learner sees:** Clicking a word from lexicon browse lands on "Page Not Found".
- **Expected:** A word page with a route to practice.
- **Repro steps:** `curl -I https://learn-ukrainian.github.io/lexicon/вода/`; or search "вода" at `/lexicon/browse/` and open the first result.
- **Evidence:** journeys `e6-word-page`, `e6b-word-page-control`, `e6c-word-via-browse` (each logs the 404 response). Note: the word-page → practice path is therefore unmeasured, and the earlier prose draft's "word page has no drill link" claim is superseded.

### F-06 — A1 Flashcards session with budget 10 delivers 8 cards
- **Surface:** Practice Hub → A1 → budget 10 → Flashcards
- **Viewport:** all
- **Observation:** Progress shows `0/8`. The scripted session answered all 8 with "Good" (each needs «Далі», by policy) and reached the end screen: "Session complete", Correct 8, Score 8/8, "Another session", "Done", "Keep exploring".
- **Status:** confirmed; whether 8 is the intended pool size is unverified
- **Severity:** low
- **What the learner sees:** Chose 10 cards, got 8, with no explanation.
- **Expected:** 10 cards, or an explanation of the smaller pool.
- **Repro steps:** Fresh browser → `/words-of-the-day/practice/` → level A1 → budget 10 → Flashcards.
- **Evidence:** journey `s1-flashcards-a1-10` (`-end-screen.png`, all profiles). Also logs repeated 404s for `/audio/pronunciation/manifest.json`.

### F-07 — Landing TTFI and first control
- **Surface:** `/words-of-the-day/practice/`
- **Viewport:** desktop 1206 ms / phone 1518 ms / android 1887 ms (load ≈ same)
- **Observation:** The first interactive control is "⚙️ Settings", not a start action. Small touch targets (<44 px) in `main`: 1 desktop, 2 phone, 2 android. No horizontal overflow. 22 mode buttons visible at once.
- **Status:** confirmed
- **Severity:** low
- **What the learner sees:** A busy dashboard whose first focusable control is settings.
- **Expected:** Primary action first; ≥44 px targets.
- **Repro steps:** Open the hub in a fresh context.
- **Evidence:** journey `t1-landing-ttfi` (`-landing.png`).

## Limits

No physical device, real Safari, or on-screen-keyboard coverage. Discoverability results use first-matching-link heuristics, not human search behaviour.
