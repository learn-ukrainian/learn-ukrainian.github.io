# Plan: Resolve Remaining Coding Tickets (#720, #726, #715, #723, #724, #712)

## Context

User asked to work on 6 tickets. Exploration reveals **4 are already implemented** and just need closing. **2 need real work**.

---

## Phase 1: Close Already-Done Issues (immediate)

| Issue | Finding | Action |
|-------|---------|--------|
| **#726** | Level-aware prompts fully implemented. `_get_prompt_tier()` dispatches to 3 tiers (beginner/core/seminar), 9 template files exist. | **Close** |
| **#723** | All 5 requested MCP tools exist: `query_wikipedia`, `query_grac`, `query_ulif`, `query_pravopys`, `query_r2u`, plus `verify_word`/`verify_lemma`. | **Close** |
| **#724** | 419 resources indexed in `blog_db.json` (240 ULP episodes, 60 FMU episodes, 119 blog articles). Integrated into discovery pipeline via `video_discovery.py`. | **Close** |
| **#712** | Benchmark script exists at `scripts/rag/benchmark_embeddings.py` with Recall@K, nDCG@K metrics, memory profiling, ground-truth YAML. | **Close** (or keep open if user wants published results) |

---

## Phase 2: Real Work

### Ticket #720 — Research Quality Evaluation (substance-based scoring)

**Problem**: Current `research_quality.py` only counts structural markers (URL count, table rows, blockquotes). A hallucinated research file scores 9/10.

**Current state**: 3 rubrics (core/history/professional), 6 dimensions each, all format-based.

**Approach**: Add substance checks using existing MCP RAG tools:

1. **Source verification** — Extract URLs from research, cross-check against known good sources (textbooks via `search_text`, ESU via `search_esu`)
2. **Claim grounding** — Check key Ukrainian terms/words via `verify_word` (do they exist in VESUM?)
3. **Factual spot-checks** — For history tracks, verify key dates/names against ESU
4. **Discovery integration** — Factor in discover phase results (external resources found → higher score)

**Files to modify**:
- `scripts/research_quality.py` — Add substance dimensions to each rubric
- `scripts/assess_research.py` — Wire in new scoring (already calls `assess_research()`)

**New dimensions per rubric**:
- `source_verification`: Are cited sources real? (check URLs, textbook refs)
- `claim_grounding`: Are Ukrainian words/terms verifiable via VESUM?
- `discovery_integration`: Does discover phase have matching external resources?

**Limitation**: Full substance eval requires LLM calls (expensive). Keep it hybrid: automated checks (VESUM, URL validation) + format scoring. No LLM-in-the-loop for the scoring itself.

### Ticket #715 — ZNO Dataset Integration

**Problem**: ZNO activity types documented in rules but not implemented. No data, no schemas, no curriculum content.

**Current state**:
- Activity types mentioned: `zno_row_select`, `zno_sentence_select`, `zno_error_find`, `zno_fill_ending`
- Not in activity schemas (`schemas/activities-base.schema.json`)
- No `data/zno/` directory
- Dataset available at `osyvokon/zno` on HuggingFace (MIT, 2,328 Ukrainian language questions)

**Approach** (3 phases):

1. **Download & process** — Fetch dataset, filter to Ukrainian language questions, convert to our YAML activity format
   - Script: `scripts/import_zno.py`
   - Output: `data/zno/questions.jsonl` (processed) + `data/zno/by_topic/*.yaml` (grouped)

2. **Add schema support** — Define ZNO activity types in JSON Schema
   - File: `schemas/activities-base.schema.json` — add 4 new `oneOf` entries
   - Each type needs: question, answers (with markers), correct_answers, source metadata (year, question_number)

3. **Topic mapping** — Map ZNO topics to CEFR levels and curriculum modules
   - наголос (stress) → A1-A2
   - орфографія (spelling) → A1-B1
   - морфологія (morphology) → A2-B2
   - синтаксис (syntax) → B1-C1
   - стилістика (stylistics) → B2-C2

**Files to create/modify**:
- `scripts/import_zno.py` (new) — Download + process + convert
- `schemas/activities-base.schema.json` — Add ZNO types
- `data/zno/` (new directory) — Processed dataset

---

## Execution Order

1. Close #726, #723, #724, #712 (5 min)
2. #715 — ZNO integration (schema + import script) (~2hr)
3. #720 — Research quality substance scoring (~3hr)

## Verification

- #715: `import_zno.py --stats` shows question counts by topic, schema validates
- #720: `assess_research.py hist --verbose` shows new substance dimensions, scores differ from format-only
