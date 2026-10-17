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

## Native speech device check (#10706)

`native-speech-probe.mjs` adds one diagnostic page, `native-speech-check.html`, to an existing
immutable static build. An evaluator with a Mac or iPhone that already has a local Ukrainian voice
uses it to record real native speech and its interruption through six app transitions: Next, Home,
route, deck, level and locale. The pasted JSON (`window.practiceAudioProbe`) is then checked
off-device against the frozen manifest. The page never changes the practice player. It opens the
practice app in its own same-origin window, because the site's anti-clickjacking guard in
`CourseLayout.astro` refuses to render inside a frame; the receipt stays in the page's memory
(no storage, cookies or network submission). On iPhone the window opens as a new tab: switch back
to the check page to tick boxes, and reopen the window after a route departure.

```bash
cd site
# 1. Build a clean checkout at the merged SHA into managed scratch (no Astro config change).
npm run build -- --outDir "$OUT"
# 2. Bind the page to that build; refuses dirty/moved/unknown source, symlinked or non-build output.
node e2e/scouting/native-speech-probe.mjs prepare --source <clean checkout> --source-sha <merged sha> \
  --out "$OUT" --manifest "$SCRATCH/native-manifest.json"
# 3. Serve the same outDir on loopback only with the existing preview CLI.
npx astro preview --outDir "$OUT" --host 127.0.0.1 --port 4321 --ignore-lock
# 4. After the evaluator pastes the JSON back:
node e2e/scouting/native-speech-probe.mjs validate --manifest "$SCRATCH/native-manifest.json" \
  --receipt receipt.json --out "$OUT"; echo exit=$?   # 0 only for DEVICE_CONTROLS_PASSED
```

`prepare` hashes the whole output first, then requires that adding the page is the only change.
The manifest records the merged source SHA, the helper SHA (whose branch diff must touch only this
helper's four files), the committed helper bytes, the build digest and the served JS hashes. Keep
the manifest and receipts in scratch; never publish private URLs, paths or topology. Reaching the
page from the device needs an existing approved route, which the driver supplies. A local HTTP 200
does not prove the device can reach it. On a plain-HTTP non-loopback origin the browser exposes no
WebCrypto, so hashing reports `INSECURE` and the receipt can never pass.

What the page records, privacy-safe only (no voice names or URIs, spoken text, URLs or raw SRS):

- the voice catalog after it stops changing (8 identical reads 250 ms apart, at most 15 s): total,
  Ukrainian, local Ukrainian and non-Ukrainian counts. An empty catalog stays UNKNOWN, never absence;
- per transition: trusted Play and control taps, whether the control was one tap away at native
  start, the selected voice's Ukrainian/local flags and match with the player's own filter, the
  click-to-`start` latency against the 10000 ms budget, speech still active at the tap, the app's
  `cancel()` call and silence, new starts in a fixed 3000 ms quiet window, a clip played instead of
  speech, and for Next only whether `lu-lexicon-srs` stayed unchanged (a boolean);
- three manual checkboxes per row (heard speech, stopped at once, nothing resumed). They count only
  when the evaluator taps them, and are reset when that row is re-attempted;
- separate Stop and retry outcomes: a second Play while the attempt is still open is Stop, kept as
  `stops.preStart` (before native start) or `stops.postStart` (after it). A clip already observed
  on that attempt stays on the retained Stop record. The next Play that reaches
  native start is that phase's fresh retry, kept on `retries`, including when a later Home row is
  also recorded. Cancellation on the six transition rows is unchanged;
- whether media and speech observation were available, once per practice document and again on each
  attempt. If either API is missing, that attempt's quiet-window duration, 3000 ms minimum and
  success checks stay unmet, and the receipt says the observation was unavailable. P11-C02 stays
  UNKNOWN unless every row that supports it was observed;

`DEVICE_CONTROLS_PASSED` needs every field to pass on all six rows, both Stop phases and both fresh
retries. It is a provisional device checklist result, never the driver's verdict, issue closure or
proof that a voice is absent. The validator recomputes it, ignores the page's own claim, refuses
unknown fields and maps P11-C02, NA-07, NA-08 and NA-09 to `PROVISIONAL_DEVICE_PASS` or `UNKNOWN`.
Deck and level controls are not shown during an active session, so those rows read NOT_EXPOSED.
NA-09 Stop/retry stays UNKNOWN until a pre-start Stop, a post-start Stop, a fresh retry after each,
and an audible native start are all present. P11-C02 stays UNKNOWN when media or speech observation
is missing on a supporting row. The other P11-C02 inventory classes stay UNKNOWN.
Unit mocks (`tests/unit/native-speech-probe.test.ts`) prove only tool behaviour.
