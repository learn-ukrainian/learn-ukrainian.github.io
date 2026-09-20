# Practice Hub scouting harness (#8317)

Standalone Node script (not a Playwright test: no `*.spec.ts`, so `npx playwright test` never runs it).

```bash
cd site
node e2e/scouting/run.mjs --help
node e2e/scouting/run.mjs --slice C1 --live --out /tmp/scout-c1        # deployed site
npm run preview &  node e2e/scouting/run.mjs --slice C1 --out /tmp/scout-c1   # local (127.0.0.1:4321)
```

Flags: `--slice C1..C8` (only C1 is implemented; C2-C8 write a stub report), `--out <dir>`,
`--profile desktop|phone|android|fast|explorer` (comma list; default `desktop,phone,android`),
`--live`, `--base <url>`. `SCOUT_COMMIT=<sha>` tags the report with the deployed commit.

Slice C1 journeys per profile, each in a fresh context (clean storage) with its own trace:
`j1-home` (home → practice), `j2-word` (lexicon search → word page → practice),
`j3-direct` (`/words-of-the-day/practice/`, time to first interactive control).

Output: `report-c1.json`, `report-c1.md`, `shot-*.png`, `trace-c1-<profile>-<journey>.zip`.

## Viewing traces

```bash
npx playwright show-trace /tmp/scout-c1/trace-c1-desktop-j3-direct.zip
```
or drag the zip into <https://trace.playwright.dev>. Baseline traces are published on the
`practice-scouting` GitHub release (`gh release upload practice-scouting <zip> --clobber`).

## Mobile emulation caveat

Phone profiles use Playwright device descriptors (`iPhone 14`, `Pixel 7`, touch enabled) running in
**Chromium**. This is emulation only. It is not a substitute for a physical iPhone in Safari, real
WebKit rendering, or on-screen-keyboard behaviour. The harness probes for Playwright WebKit and
records whether it is installed (`npx playwright install webkit` to add it).
