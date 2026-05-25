# Dispatch brief — Issue #2052 Karavansky scraper (R2U difficult-lexis)

**Agent**: gemini (unmetered)
**Mode**: danger
**Effort**: high
**Branch base**: `origin/main`
**Task ID**: `issue-2052-karavansky-scraper-2026-05-25`

## Read first
- `gh issue view 2052` — full background + the gap (PR #1755 landed only the ingester, never the scraper)
- `gh issue view 1664` — the original Karavansky-data issue that was closed without the scraper landing
- `gh issue view 2048` — the COMPANION ingest issue (do NOT touch; that's tracked separately and was explicitly skipped per user direction 2026-05-25). This dispatch is ONLY about producing the source file.
- `scripts/ingest/dictionary_ingest.py` — the existing post-scrape ingester (read to understand the schema it expects)

## Background
Karavansky's "Російсько-український словник складної лексики" (Russian-Ukrainian dictionary of difficult lexis, ~5K entries) is hosted at r2u.org.ua but no scraper exists. The PR #1755 claim "Implemented" was misleading; only the post-scrape ingester landed.

## Verifiable claims preamble (#M-4)
- "scraper runs end-to-end" → quote `.venv/bin/python scripts/scrape/karavansky_r2u.py --out docs/references/private/karavansky.txt` final stdout line (file size + row count)
- "output schema matches ingester" → quote `.venv/bin/python scripts/ingest/dictionary_ingest.py --source karavansky --input docs/references/private/karavansky.txt --dry-run` showing N rows parsed
- "no live ingest yet" → state explicitly that this PR ONLY adds the scraper; ingestion is per issue #2048 and is OUT OF SCOPE for this dispatch
- ruff + pytest green per usual

## Steps

1. `git worktree add -B feat/issue-2052-karavansky-scraper .worktrees/dispatch/gemini/issue-2052 origin/main && cd .worktrees/dispatch/gemini/issue-2052`
2. Research r2u.org.ua's Karavansky pages: probe the URL structure, identify entry shape (search for entries A-Я), respect robots.txt + rate-limit politely (1 req/sec max).
3. Write `scripts/scrape/karavansky_r2u.py` that produces `karavansky.txt` in the schema the ingester expects (consult `scripts/ingest/dictionary_ingest.py` to learn the format).
4. Run the scraper and produce `docs/references/private/karavansky.txt` (gitignored; do NOT commit the file itself — it's in `data/references/private/` per existing pattern).
5. Verify ingester can parse it (dry-run only, do not write to sources.db in this dispatch).
6. Add unit tests for the parser logic at `tests/test_karavansky_scraper.py` — use a small HTML fixture (NOT live network requests).
7. `.venv/bin/ruff check scripts tests`
8. Commit: `feat(scrape): Karavansky R2U difficult-lexis scraper (closes #2052)`
9. Push, open PR. In the PR body, include row-count of the produced karavansky.txt.

## Stop conditions
- r2u.org.ua structure is dynamic-JS-only (cannot scrape via simple requests + parser) → STOP and report; the issue then needs a different acquisition strategy (e.g. Selenium / archive.org / direct email to r2u maintainers).
- Robots.txt explicitly disallows scraping → STOP.
- Karavansky entries are paywalled / require auth → STOP.

## Done criteria
PR URL + scraper output row count + sample of 5 entries + the dry-run ingester success quote. Ingestion into sources.db is NOT in scope — that's #2048.
