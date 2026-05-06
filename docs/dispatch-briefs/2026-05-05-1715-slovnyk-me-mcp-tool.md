# Codex dispatch brief — #1715 slovnyk.me MCP tool

> **Issue:** #1715
> **Branch base:** `origin/main`
> **Worktree:** `.worktrees/dispatch/codex/1715-slovnyk-me-mcp-tool/`
> **Branch:** `codex/1715-slovnyk-me-mcp-tool`
> **Mode:** danger
> **Hard timeout:** 7200s (120 min — non-trivial: ingest + tool + smoke + docs)
> **Effort:** xhigh (dictionary ingestion is high-stakes for content quality; design choices here affect all future curriculum modules)
> **Reviewer:** Claude (cross-family)

## Goal

Build the slovnyk.me MCP tool. Tonight's bakeoff blocker (per Codex msg 528, Q7): the V7 writer + reviewer prompts can't pin slovnyk.me as a verification source until an MCP tool exists. Without it, the heritage-defense logic the user wants (differentiating authentic Ukrainian archaisms/historisms/dialectisms from Russianism/surzhyk) can't be enforced in the prompts.

## Strategic decisions you make in this PR

These are NOT pre-decided in the issue. Make the calls, document in PR body:

1. **Ingestion mechanism.** Check `https://slovnyk.me/` for: (a) public data dump / API / git repo / archive; (b) `robots.txt` + Terms-of-Service for scraping; (c) any existing GitHub mirrors of the underlying dictionaries (some are public domain — Грінченко 1907 is, СУМ-20 may not be). Default preference: data dump or upstream public-domain source > polite respectful scrape > rejected.

2. **Scope of dictionaries to ingest.** The aggregator hosts ~10+ dictionaries. Some we already have (Грінченко 1907, ЕСУМ vol 1 via `search_esum`, Балла EN→UK via `translate_en_uk`, Антоненко-Давидович 279 entries via `search_style_guide`). Decide: (a) ingest only what we don't already have — primarily СУМ-20 + dialect dicts + Голоскевич + Караванський; (b) ingest everything for cross-reference + redundancy; (c) ingest URL-references only (link out, don't index full text). Default preference: (a) — ingest the gaps, leave existing tools alone, add a heritage-defense merge tool that queries multiple sources.

3. **MCP tool surface.** Per acceptance criteria in #1715: `mcp__sources__search_slovnyk_me` (single-source) + `mcp__sources__search_heritage` (multi-source merger). Decide tool config schema, ranking algorithm for merger, max-result defaults. The merger is the higher-leverage tool because it's what the V7 prompt will actually call.

4. **Sovietization risk classification on СУМ-20.** Apply the same classification we use for СУМ-11 (`sovietization_risk` 0/1/2 + `sovietization_keywords`)? Or assume СУМ-20 is clean? Run a quick scan; document the result.

## Numbered execution

1. Verify worktree base clean.
2. Investigate slovnyk.me ingestion mechanism. Check robots.txt, ToS, any data dump endpoints, GitHub mirrors. Document findings in a working notes file `docs/audits/slovnyk-me-ingestion-feasibility.md` (commit it).
3. If feasible: write the ingester under `scripts/ingest/slovnyk_me_ingest.py`. CLI standard from `.claude/rules/cli-help-standard.md`. Output is `data/sources.db` (FTS5) rows.
4. Build the two MCP tools per #1715 acceptance criteria. Mirror the structure of existing tools in `scripts/sources/` (find them via `grep -rn 'def search_definitions\|def search_grinchenko' scripts/sources/`). Add to MCP server config.
5. Smoke tests in `tests/test_slovnyk_me_tool.py`:
   - `search_slovnyk_me("блакитний")` returns rows; assert at least one row from СУМ-20 (or whatever modern dict we ingested) with `is_modern: true`.
   - `search_slovnyk_me("кобета")` — Polish-influenced regional/archaic word for "woman" — assert a dialect-dict row appears, NOT classified as Russianism.
   - `search_heritage("гаразд")` — common authentic Ukrainian word — assert merged result includes Грінченко + slovnyk.me + (if available) ЕСУМ.
6. Update `.claude/rules/mcp-sources-and-dictionaries.md`:
   - Add slovnyk.me + search_heritage entries to "Core tools" / "Dictionary tools" sections
   - Add slovnyk.me row to the dictionaries table at the bottom
   - Add a "Heritage defense" section explaining how `search_heritage` is the canonical tool for the writer/reviewer prompts when verifying potential archaism vs Russianism
   - Update the Sovietization caveat to point at slovnyk.me/СУМ-20 as supersession path
7. Run `.venv/bin/ruff check scripts/ingest/ scripts/sources/ tests/`
8. Run `.venv/bin/pytest tests/test_slovnyk_me_tool.py -v`
9. Get Claude review:
   ```
   git add -A
   git diff --cached > /tmp/1715-slovnyk-me-diff.txt
   .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
       "Adversarial review for #1715 slovnyk.me MCP tool. Read /tmp/1715-slovnyk-me-diff.txt and docs/audits/slovnyk-me-ingestion-feasibility.md. Focus: (1) ingestion legality + ToS compliance (we are non-commercial educational; how does that interact with slovnyk.me's terms?); (2) sovietization risk handling for СУМ-20 — was the scan run, what were the results, are flagged entries handled correctly?; (3) the search_heritage merger ranking algorithm — does it actually surface authentic-Ukrainian-with-Proto-Slavic-roots over a modern Russianism, given typical query patterns the writer will use?; (4) did you avoid duplicating data we already index from Грінченко/ЕСУМ/Балла/Антоненко-Давидович, or is there double-storage in sources.db?" \
       --task-id 1715-slovnyk-me-review
   ```
10. Apply feedback; commit with `Reviewed-By: claude-opus-4-7 (1715-slovnyk-me-review)` trailer.
11. Push + open PR titled `feat(mcp): slovnyk.me ingester + search_slovnyk_me + search_heritage tools (#1715)`. PR body must document strategic decisions 1-4 above.

## Constraints

- **No auto-merge.**
- **Non-commercial use only** — the project is permanently non-profit per `LICENSE-CONTENT.md`. If slovnyk.me's ToS forbids any redistribution including non-commercial educational, STOP and report — we'll work around with link-out-only references.
- **Don't touch existing search_grinchenko_1907 / search_esum / translate_en_uk / search_style_guide tools** — those keep working independently. The merger reads them via the existing tool calls, not by re-ingesting.
- **CLI help standard** on the ingester.
- **Tests are non-negotiable** including the heritage-defense smoke tests (the кобета case is the load-bearing one — that's literally what the user described as a heritage-defense failure mode).
- **No content edits to the curriculum** — this is infrastructure only.

## Failure modes to surface

- ToS forbids the ingestion → STOP, report. We'll punt to link-out-only or to a future contact with the slovnyk.me maintainers.
- Data is locked behind a JS-rendered SPA without an underlying API → STOP, propose Playwright-based scrape OR upstream-source fallback (Грінченко GitHub mirrors, СУМ-20 from `https://services.ulif.org.ua/expl` if accessible).
- СУМ-20 sovietization scan finds high-risk entries → don't drop them, but mark with `sovietization_risk` ≥1 in the index and document in PR body.
