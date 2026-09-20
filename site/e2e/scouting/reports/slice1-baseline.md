# Practice Hub scouting — Slice 1 baseline (#8317)

- Target: https://learn-ukrainian.github.io (live), run 2026-09-20 ~19:50 UTC
- Commit: `af3ac9e159` (origin/main at run time; the Pages deploy commit is not exposed by the site, so the deployed build may lag slightly)
- Harness: `site/e2e/scouting/run.mjs --slice C1 --live`; Chromium emulation only, WebKit **not installed** on this host (`webkit-2336` missing)
- Single run per profile from a fast network: treat TTFI as indicative, not a distribution.

## TTFI — direct landing on `/words-of-the-day/practice/`

| Profile | TTFI ms | Load ms | First interactive control | Overflow-x | Targets <44px |
|---|---|---|---|---|---|
| Desktop Chrome | 1197 | 1203 | ⚙️ Settings | no | 1 |
| iPhone 14 (emulated) | 1529 | 1531 | ⚙️ Settings | no | 2 |
| Pixel 7 (emulated) | 1299 | 1300 | ⚙️ Settings | no | 2 |

Landing renders the dashboard hero, stats, session-budget buttons (10 / 20 / until-zero), a start-session button, 8 track cards and 22 mode buttons. No modal or drawer is open on load. The daily deck shows a loading state at first paint.

## Entry-point discoverability

| Start | Direct link to the hub? | Clicks | Path |
|---|---|---|---|
| Home `/` | No | 2 | nav "Words of the Day" → "Practice — spaced repetition…" |
| Word page `/lexicon/офіс/` (via `/lexicon/browse/` search) | No | 2 | nav "Words of the Day" → "Practice…" |
| `/lexicon/browse/` | No practice link | — | — |

Results were identical across all three profiles.

## Friction points

1. **Home has no practice entry.** The only "practice" text is on the B1 card (points to `/b1/practice-exam/`, a different feature); a learner who wants drills must guess that "Words of the Day" holds them. The nav label does not say practice.
2. **Word pages and lexicon browse offer no drill link**, even though drills are word-based. A dead end for the "I just looked up a word, now let me practise it" moment.
3. **First interactive control is "⚙️ Settings"**, not a start/practice action. TTFI measures the first control, not the first useful one; `practice-start-session` appears alongside it but the primary action is not first in DOM order.
4. **Small touch targets** (<44 px) on the landing: 1 on desktop, 2 on both phones.
5. **Two 404 resource requests** logged on the word page (`/lexicon/офіс/`); URLs not captured by this run (follow-up: log failed request URLs).
6. **22 mode buttons** visible at once, including the ZNO set, on first landing for an unfamiliar learner; worth checking in slice C2+ with real task completion.

## Limits

No physical-device, real Safari, or on-screen-keyboard coverage. Journeys 1-2 use a first-link heuristic, not a human's search behaviour. Traces: `trace-c1-<profile>-<journey>.zip` in the `practice-scouting` release.
