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
