# Practice Hub scouting harness (#8317)

Standalone Node script (not a Playwright test: no `*.spec.ts`, so `npx playwright test` never runs it).

```bash
cd site
node e2e/scouting/run.mjs --help
node e2e/scouting/run.mjs --slice C1 --live --out /tmp/scout-c1        # deployed site
npm run preview &  node e2e/scouting/run.mjs --slice C1 --out /tmp/scout-c1   # local (127.0.0.1:4321)
```

Flags: `--slice C1..C8`, `--out <dir>`,
`--profile desktop|phone|android|fast|explorer` (comma list; default `desktop,phone,android`),
`--live`, `--base <url>`. `SCOUT_COMMIT=<sha>` tags the report with the deployed commit.

Every journey runs in a fresh context (clean storage) with its own trace. All artifacts are named
`<run-timestamp>-<slice>-<profile>-<journey>` so reruns never overwrite earlier evidence.

- **C1** entry points (`e1-home`, `e2-header-nav`, `e3-phone-menu`, `e4-footer`, `e5-words-of-the-day`,
  `e6*-word-page`, `e7-direct-practice-url`), the full A1 10-budget Flashcards session to the end screen
  (`s1-flashcards-a1-10`), and landing TTFI (`t1-landing-ttfi`).
- **C2** vocab modes (mixed, flashcards, matching, choice) · **C3** form modes (cloze, synonym, paronym, heritage) ·
  **C4** grammar (paradigm, imperative) · **C5** grammar (stress, classify) · **C6** exams (ZNO + culture) ·
  **C7** settings drawer, deck picker, level switch · **C8** phone pass (defaults to phone,android).
  Each mode journey opens the mode, records what rendered, attempts one interaction and screenshots.

## Detector (#8477)

Slices only watch. `--detect` plays one A1 Flashcards session with the same player as
`s1-flashcards-a1-10` and **exits 1** when the session breaks a rule:

1. **Progress** — every `practice-session-progress` reading (start + after each answer) must go
   `0/{budget}` → `{budget}/{budget}` in +1 steps with a fixed denominator (`--budget 10|20`, default 20).
   `0/9` … `9/9` after clicking 20 fails.
2. **`pageerror`** — any uncaught page error fails.
3. **Pronunciation** — the flashcard control is pressed once; `/audio/pronunciation/manifest.json` 404, a
   `window.speechSynthesis.speak` call, or no clip request/`play()` fails. Voice quality is not scored.

```bash
cd site
node e2e/scouting/run.mjs --detect --budget 20 --live --out /tmp/detect-20; echo exit=$?
node --test e2e/scouting/invariants.test.mjs        # pure rules, no browser
```

The pure rules live in `invariants.mjs`; the report gains a `verdict` block. Slices C1–C8 record the
same `progressReadings`, `progressCheck` and `pronunciation` fields but stay observational (exit 0).

`fixtures/mock-hub.mjs` is a throwaway hub with the same DOM contract, for proving the exit codes
without the live site (which currently fails both rules: `0/8` for any budget, empty manifest):

```bash
node e2e/scouting/fixtures/mock-hub.mjs --port 4322 &                      # clean -> exit 0
node e2e/scouting/fixtures/mock-hub.mjs --port 4323 --broken progress &    # 0/9 … 9/9 -> exit 1
node e2e/scouting/run.mjs --detect --budget 20 --base http://127.0.0.1:4323 --out /tmp/detect-mock
```
`--broken audio` (manifest 404 → browser voice) and `--broken pageerror` also exit 1.

Output (in `--out`, gitignored under `reports/artifacts/`): `<ts>-report-<slice>.{json,md}`, `*.png`, `*.zip` traces.

## Viewing traces

```bash
npx playwright show-trace /tmp/scout-c1/<ts>-c1-desktop-t1-landing-ttfi.zip
```
or drag the zip into <https://trace.playwright.dev>. Baseline traces are published on the
`practice-scouting` GitHub release (`gh release upload practice-scouting <file>`). Filenames are
timestamped and immutable: never overwrite or `--clobber` an uploaded asset; a rerun gets new names.

## Mobile emulation caveat

Phone profiles use Playwright device descriptors (`iPhone 14`, `Pixel 7`, touch enabled) running in
**Chromium**. This is emulation only. It is not a substitute for a physical iPhone in Safari, real
WebKit rendering, or on-screen-keyboard behaviour. The harness probes for Playwright WebKit and
records whether it is installed (`npx playwright install webkit` to add it).
