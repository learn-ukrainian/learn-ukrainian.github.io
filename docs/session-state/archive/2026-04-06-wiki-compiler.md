# Session State: Wiki Compiler — 2026-04-06

## What we did this session

### 1. Fixed wiki review loop (3 bugs preventing 9/10)
- Decimal score parsing (`8.8/10` now works)
- Fresh article text in every review prompt
- Final review applies fixes + preserves review_text on API failure
- Commits: `a37ab976a`, `a6aecd2c9`

### 2. Built split-path review architecture
- Dimension score parsing (all 5 + overall)
- Copyedit path (old:/new: + INSERT AFTER:) when all dimensions ≥ 8
- Structural rewrite path when any dimension < 8
- One rewrite max per article (prevents oscillation: 8.4→7.4→7.8→7.0)
- Peak score tracking — reverts to best version on regression
- Pipe prompts via stdin (fixes CLI arg length limit crash)
- Commits: multiple, ending at `297b60098`

### 3. Replaced RAG with direct textbook JSONL loading
- RAG returned thin results (13 chunks, 3/10 language). Same approach as seminars — load 40 ukrmova textbook JSONL files directly, score by keyword overlap
- C1/C2 also include ukrlit textbooks
- Min 2 keyword hits, global sort, top 40 chunks
- No hardcoded grade filtering — keyword relevance handles it
- Commits: `575dd4ab6` through `256d0ac7c`

### 4. Added external resource ingestion
- `scripts/wiki/fetch_external_sources.py` — fetches ULP blogs (164), other blogs (75), YouTube subtitles (in progress)
- YouTube channels: ULP, Реальна Історія, imtgsh, Istoria-Movy, Комік Історик
- Enrichment wires cached JSONL content into compilation (URL-matched, www-normalized)
- Rate limiting: 10s YouTube delay, 90s batch pause
- Commits: multiple, ending at `2e7f9929f`

### 5. Redesigned compilation prompts (#1161)
Root cause analysis: compared 9.6 articles (adjective-comparison, active-participles-past) against 5.0 articles (building-domain-expertise). Key findings:
- Good articles had embedded source citations, paradigm tables, error pairs, teaching phases
- Bad articles had dense prose, missing sections, Russianisms endorsed, prompt echo corruption

**Prompt changes (all 4 templates):**
- Mandatory inline source citations: `(Source N)` or `(Джерело: chunk_id)`
- Minimum examples per section (10-15 for grammar, 10 for academic, 4 for pedagogy)
- Anti-patterns section (what NOT to do — specific examples from failed articles)
- Factual honesty clause: mark `<!-- VERIFY -->` when sources don't cover a claim
- Decolonization section: `MANDATORY — never omit`
- Higher word minimums: academic 1,500→2,000
- Error pairs: minimum 5, in ❌→✅ table format

### 6. Fixed rewrite extraction bugs
Three bugs caused rewrites to produce corrupted articles:

1. **Prompt echo leak**: Gemini echoed rewrite instructions in response. Fixed: `_clean_rewrite_response()` strips prompt fragments + takes LAST top-level heading instead of first.

2. **Agent bridge metadata**: `_send_review` captured agent bridge's stdout diagnostics (`✓ Message acknowledged`, etc.) which corrupted the response. Fixed: regex strip of metadata lines.

3. **Truncation detection**: Added detection for mid-word/mid-sentence cutoffs. Rejects truncated rewrites instead of saving corrupted content.

New function: `_clean_rewrite_response()` with 12 tests covering all edge cases.

### 7. Validation results (5 worst articles)

| Article | Old Score | New Score | Status |
|---------|-----------|-----------|--------|
| C2 building-domain-expertise | **5.0** | **9.4** | ✅ PASSED |
| C1 academic-style-markers | **6.0** | **9.2** | ✅ PASSED |
| B1 active-participles-phrases | **6.6** | **9.8** | ✅ PASSED |
| C2 academic-publishing | **6.2** | **8.8** | Close |
| C1 advanced-punctuation | **6.8** | **8.0** peak (regressed) | Needs work |

**Biggest wins:** Decolonization 6→10 across the board. Actionable 3→9. Completeness 4→10.

## What needs doing next

### Priority 1: Batch A2 (69 articles)
The prompts are validated. Time to compile the full A2 track:
```bash
.venv/bin/python scripts/wiki/compile.py --track a2 --all --review
```

### Priority 2: Investigate C1 advanced-punctuation regression
Peaked at 8.0 but regressed to 6.6 in round 3 (completeness oscillation). This is the known oscillation problem — the review loop alternately demands more content vs better focus. May need a prompt tweak for topics with thin source material.

### Priority 3: Push academic-publishing past 9.0
At 8.8 — needs one more rewrite round to add the missing sections.

### Priority 4: Continue YouTube subtitle fetching
ULP channel partially done (rate limited), other channels pending.

## Open issues
- #1150 — Wiki compilation (main tracking issue)
- #1151 — External source ingestion (YouTube subtitles in progress)
- #1161 — Prompt redesign (validation complete, 3/5 passed)

## Files changed this session (continued)
- `scripts/wiki/prompts/compile_academic.md` — completely rewritten
- `scripts/wiki/prompts/compile_grammar_brief.md` — strengthened
- `scripts/wiki/prompts/compile_pedagogy_brief.md` — strengthened
- `scripts/wiki/prompts/compile_article.md` — strengthened
- `scripts/wiki/compile.py` — _clean_rewrite_response(), metadata stripping, truncation detection
- `tests/test_wiki_compiler.py` — 12 new tests (62 total)
