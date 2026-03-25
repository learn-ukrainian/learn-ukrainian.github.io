# Session Handoff — 2026-03-20

**Continue from here next session. Read this first.**

---

## What was accomplished

### A1 Plans: COMPLETE ✅
- 55/55 plans written in `curriculum/l2-uk-en/plans/a1/`
- All Gemini-reviewed, all fixes applied
- All pass `check_plan.py`

### A2 Design: COMPLETE ✅
- 60 modules across 8 phases in `docs/l2-uk-en/A2-CURRICULUM-V3.md`
- Gemini-reviewed, gap analysis done, all State Standard items covered
- 3 metalanguage bridge modules (M55-57) prepare for B1 immersion
- Plans NOT written yet — design only

### V6 Pipeline: BUILT, ITERATING ON QUALITY
All components in `scripts/build/`:
- `research/build_knowledge_packet.py` (#994) ✅
- `phases/v6-write.md` (#995) ✅
- `quick_verify.py` (#1006) ✅
- `exercises/fill_placeholders.py` (#996) ✅
- `phases/v6-review.md` (#991) ✅ — 10-dimension structured rubric
- `v6_build.py` — orchestrator with retry + correction directive injection
- Tests: 39/39 pass

### M01 Writer Comparison (#1001): COMPLETE
- **Claude: 8.55/10** — attempt 1, 1,779 words
- **Gemini: 8.35/10** — attempt 2, 2,191 words
- **Decision: Claude writes, Gemini reviews** (Claude wins on tone/pedagogy)
- Both fail on same 2 things: exercises (stray quotes, no fill-in context) and missing словник/videos

### Key fix applied this session: Claude CLI invocation
- **Root cause:** `-p` was passed a file PATH, not prompt CONTENT
- **Fix:** pipe via stdin: `subprocess.run(["claude", "-p", ...], input=prompt)`
- Claude now produces 1,800+ words on attempt 1

---

## BLOCKERS — Fix these next session

### 1. Stray quotes in exercise YAML (QUICK FIX)
- **Problem:** Writer produces `"'В"` and `"зву́ки'"` — rogue single quotes
- **Where:** Output of exercise filler DSL
- **Fix:** Add regex post-processing in `_post_process_content()` to strip stray quotes from :::exercise blocks
- **Estimated scope:** ~10 lines

### 2. Fill-in exercises have no context (MEDIUM)
- **Problem:** `sentence: "___"` with no surrounding text — learner can't guess the answer
- **Fix options:**
  a. Better prompt: tell writer to provide `questions:` field with contextual sentences
  b. Post-process: inject dialogue context from surrounding prose
  c. Dedicated LLM call for exercise enrichment
- **Recommended:** Option (a) — update `v6-write.md` with fill-in examples

### 3. Step 7b ENRICH not implemented (MEDIUM)
- **What it does:** Adds словник table, Anna's videos, external resources, dialogue formatting
- **Design:** Already in `docs/pipeline-v6-design.md` Step 7b
- **Components needed:**
  - Vocabulary table generator (from plan `vocabulary_hints`)
  - Video embed generator (from plan `pronunciation_videos`)
  - External resources tab content
  - Dialogue formatter (wrap conversations in `:::dialogue`)
- **Estimated scope:** ~200 lines new code

### 4. Exercise item count doesn't match plan (MINOR)
- Plan says 6 quiz items, writer provides 4-5
- Fix: add item count to quick verify checks

---

## Architecture decisions (don't re-discuss)

- **Writer:** Claude (better tone/pedagogy, 8.55 vs 8.35)
- **Reviewer:** Gemini (adversarial, 10-dimension rubric)
- **Stress marks:** Writer produces NONE → deterministic annotator. A1-A2 all words, B1+ vocab only.
- **Error recovery:** Max 2 retries, whole-module regen, model switch, no anchoring
- **Tab structure:** Урок / Ресурси / Зошит (lesson / resources / workbook)
- **Default writer invocation:** `claude -p --model claude-opus-4-6 --output-format text` via stdin pipe

## Key commands

```bash
# Build M01 with Claude
.venv/bin/python scripts/build/v6_build.py a1 1 --writer claude

# Build M01 with Gemini
.venv/bin/python scripts/build/v6_build.py a1 1 --writer gemini

# Run V6 tests
.venv/bin/python -m pytest tests/test_build_knowledge_packet.py tests/test_quick_verify.py tests/test_fill_placeholders.py -v

# Send to Gemini for structured review
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini "..." --task-id issue-1001 --model gemini-3.1-pro-preview

# Plan checker
.venv/bin/python scripts/audit/check_plan.py a1 --first 55
```

## Open issues (active)

| Issue | What | Status |
|-------|------|--------|
| #982 | Epic: V6 Pipeline | IN PROGRESS |
| #981 | Epic: A1 rebuild | Plans done, M01 built |
| #994 | Research packet | ✅ DONE |
| #995 | Writing prompt | ✅ DONE (needs fill-in examples) |
| #1006 | Quick verify + retry | ✅ DONE |
| #996 | Exercise filler | ✅ DONE (needs stray quote fix) |
| #988 | Stress annotation | ✅ DONE |
| #989 | Verification | ✅ DONE |
| #991 | Review prompt | ✅ DONE (10-dimension rubric) |
| #997 | DSL→MDX converter | ✅ DONE (existing) |
| #1001 | Writer comparison | ✅ DONE — Claude wins |

## File locations

```
curriculum/l2-uk-en/plans/a1/                          — 55 V3 plans
curriculum/l2-uk-en/a1/sounds-letters-and-hello-claude.md  — Claude M01 (8.55/10)
curriculum/l2-uk-en/a1/sounds-letters-and-hello-gemini.md  — Gemini M01 (8.35/10)
docs/l2-uk-en/A2-CURRICULUM-V3.md                      — A2 design (60 modules)
docs/pipeline-v6-design.md                             — V6 pipeline design
scripts/build/v6_build.py                              — V6 orchestrator
scripts/build/research/build_knowledge_packet.py       — RAG query engine
scripts/build/exercises/fill_placeholders.py            — exercise DSL generator
scripts/build/quick_verify.py                          — structural checks + retry
scripts/build/phases/v6-write.md                       — writing prompt template
scripts/build/phases/v6-review.md                      — 10-dimension review rubric
```

## Next session priority order
1. Fix stray quotes in exercises (10 min)
2. Fix fill-in context (update prompt, 15 min)
3. Build Step 7b ENRICH — словник + videos (1 hour)
4. Rebuild M01, get PASS from Gemini (target: 9+/10)
5. Scale to M02-M07 (A1.1 phase)
