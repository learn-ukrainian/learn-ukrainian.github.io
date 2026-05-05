# Gemini dispatch — source availability check for #1663 (Antonenko-Davydovych) and #1664 (Karavansky)

## Context

Two MCP P1 ingestion issues are queued. Before writing ingester briefs, we need to verify the upstream sources are actually live and accessible. Today's #1665 Holovashchuk dispatch found its kpdi.edu.ua PDF returns 404 — wasted dispatch. Same risk for these two. This is a 5-min fact-finding mission.

## Tasks

### Task 1 — Issue #1663 Antonenko-Davydovych «Як ми говоримо» (full 169-page text)

**Background:** The MCP currently has 279 entries indexed of the ~600+ in the source (per `claude_extensions/rules/mcp-sources-and-dictionaries.md`). #1663 wants to ingest the FULL 169-page text.

**Verify:**
1. Read the full body of issue #1663 (`gh issue view 1663`). Capture any URLs / publisher info / ISBN it mentions.
2. For every URL in the issue body, run `curl -sLI` and report HTTP status + content-length.
3. If the issue cites a host like `chtyvo.org.ua`, `archive.org`, `kpdi.edu.ua`, `litopys.org.ua`, etc., verify each.
4. Search for the book on Internet Archive: `curl -sL 'https://archive.org/advancedsearch.php?q=title%3A%22%D0%AF%D0%BA+%D0%BC%D0%B8+%D0%B3%D0%BE%D0%B2%D0%BE%D1%80%D0%B8%D0%BC%D0%BE%22&output=json'` — capture any matches.
5. Check whether the existing 279 entries in our DB came from a known source (look at any provenance metadata in `data/sources.db` — `sqlite3 data/sources.db "SELECT DISTINCT source FROM antonenko_davydovych LIMIT 5"` if that table exists, or the closest analogue).

**Report on issue #1663:** verdict (LIVE / DEAD), recommended ingest path with concrete URL, OCR vs. structured-text decision, estimated effort.

### Task 2 — Issue #1664 Karavansky «Російсько-український словник складної лексики»

**Background:** "r2u digital edition" — likely the Movahid / r2u.org.ua / r2u.ipost.ua project. Not a raw PDF; a structured digital dictionary. Different ingest path than scan-based ingestion.

**Verify:**
1. Read the full body of issue #1664 (`gh issue view 1664`). Capture any URLs / API endpoints / data-dump links.
2. For every URL, run `curl -sLI` + report HTTP status.
3. Probe `r2u.org.ua` / `r2u.ipost.ua` / `r2u.movahid.ua` — does the dictionary expose a programmatic interface (REST/JSON, downloadable corpus, GitHub repo with TSV)?
4. If a GitHub repo is referenced, run `curl -sL https://api.github.com/repos/<owner>/<repo>` to confirm it exists and capture stars / last commit date.
5. Determine: structured DB ingest (preferred) vs. HTML scrape (fallback) vs. PDF OCR (last resort).

**Report on issue #1664:** verdict (LIVE / DEAD), data-shape (JSON / TSV / HTML / PDF), recommended ingest pattern (e.g. "clone repo + parse TSV" vs. "iterate API + cache locally"), estimated effort.

## Acceptance criteria

- Both issues #1663 and #1664 have a comment posted with the verdict
- Each verdict cites the specific URL(s) checked + HTTP status
- Each recommends a concrete next step (ingest brief / fallback / wait)
- No code changes, no commits, no PR — pure research

## Discipline

- Per-query fair use; no automated bulk scraping in this dispatch
- If a URL requires `User-Agent` to bypass anti-bot, document the working header
- Reference the issue numbers (#1663 / #1664) in the comments
- Stop and report if you find both sources are 404 — do NOT improvise alternative dictionaries

## Why Gemini

Research / data inspection / fact-finding. Uncapped + fast turnaround. Same pattern as today's successful #1666 slovnyk.me research dispatch.
