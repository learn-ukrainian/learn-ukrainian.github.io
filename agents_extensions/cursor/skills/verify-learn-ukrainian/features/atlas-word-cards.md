# Atlas word cards

Learners search and browse the Word Atlas (`/lexicon/`), open alphabetical browse, and read lemma word-card pages with practice CTAs — without dumping the entire catalog into the first paint.

## Sub-features

- `atlas-landing` shows search-first Atlas chrome at `/lexicon/`.
- `atlas-browse` at `/lexicon/browse/` starts empty until letter, search, or category is chosen.
- `atlas-search` filters by query (`[data-index-search]`, URL `?q=`).
- `atlas-letter` filters by alphabet button (`[data-letter]`).
- `atlas-word-card` loads a lemma page such as `/lexicon/прапор/` or `/lexicon/вареник/`.

## How to get to it (user POV)

- Choose Atlas in site chrome (`/lexicon/`, nav key `nav.atlas`).
- Follow "browse" into `/lexicon/browse/`.
- Type a query, pick a category chip (e.g. `русизм`), or pick a letter.
- Open a lemma link to `/lexicon/<slug>/`.

## Driving it with Playwright

Preconditions:

- Preview is healthy (`doctor.sh` OK).
- Committed Atlas artifacts pass `npm run verify:artifacts` inside `site/` (launch's `build:shell` runs this).
- Full hydrate (`LU_VERIFY_BUILD_MODE=full`) when proving runtime shards that require the public release manifest download; shell build covers browse/landing when committed public JSON is present.

- **Browse empty-then-search.** Run `bash .cursor/skills/verify-learn-ukrainian/bin/drive-playwright.sh atlas`. Spec opens `/lexicon/browse/`, expects zero `.atlas-index-item` and the empty-state copy, then fills `[data-index-search]` with `офіс` and sees `.atlas-index-link` for that lemma and `?q=офіс`.
- **Category and letter.** Same drive: category `русизм` sets `?cls=rus`; letter `Д` sets `?letter=Д` with cards visible.
- **Word card pages.** Same spec family hits `/lexicon/прапор/` and `/lexicon/вареник/` (see `e2e/atlas-practice.spec.ts`).
- **Proof.** `$LU_VERIFY_EVIDENCE_DIR/playwright-atlas.log` exit `0`, with URL query params matching the filters exercised.

## Gotchas

- Browse must not render all cards on first paint — a full dump is a regression (`cards` count starts at 0).
- Manifest hydrate downloads a large public GitHub Release asset; network failure is an env gap for `full` build, not a product FAIL for shell-mode lesson proof.
- Client-shell mode serves some lemma bodies dynamically; a 404 HTML shell that then hydrates can still be valid — trust the Playwright assertions, not a single static HTML grep.
- Do not hand-edit `site/src/data/lexicon-manifest.json` (gitignored hydrate output).
