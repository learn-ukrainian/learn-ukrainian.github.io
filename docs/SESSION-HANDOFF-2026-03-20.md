# Session Handoff — 2026-03-20

**Continue from here next session. Read this first.**

---

## What was accomplished

### A1 Plans: COMPLETE ✅
- 55/55 plans written in `curriculum/l2-uk-en/plans/a1/`
- All Gemini-reviewed, all fixes applied
- All pass `check_plan.py`
- 8 phases: A1.1-A1.8 (sounds → past/future/graduation)

### A2 Design: COMPLETE ✅
- 60 modules across 8 phases in `docs/l2-uk-en/A2-CURRICULUM-V3.md`
- Gemini-reviewed, gap analysis done, all State Standard items covered
- 3 metalanguage bridge modules (M55-57) prepare for B1 immersion
- `curriculum.yaml` updated with V3 A2 slugs
- **Plans NOT written yet** — design only

### V6 Pipeline: BUILT, NEEDS QUALITY ITERATION
- All components built in `scripts/build/`:
  - `research/build_knowledge_packet.py` (#994) — RAG textbook queries
  - `phases/v6-write.md` (#995) — writing prompt template
  - `quick_verify.py` (#1006) — structural check + retry loop
  - `exercises/fill_placeholders.py` (#996) — exercise DSL skeleton
  - `v6_build.py` — orchestrator with retry, correction directive injection
- Tests: 39/39 pass in `tests/test_build_knowledge_packet.py`, `tests/test_quick_verify.py`, `tests/test_fill_placeholders.py`
- Stress annotator + VESUM verification: existing code, works

### M01 First Build: 2/10 from Gemini
- Pipeline runs end-to-end: `CHECK → RESEARCH → WRITE → QUICK VERIFY → RETRY → EXERCISES → ANNOTATE → VERIFY → PUBLISH`
- Prose quality is good ("top-tier pedagogy" per Gemini round 1)
- **Three blockers preventing 8+/10:**

## M01 Build Results (3 attempts)

### Attempt 1: Claude → 435 words, FAILED (no H2 headings)
### Attempt 2: Claude + correction directive → 148 words, FAILED
### Attempt 3: Gemini (circuit breaker) → 2,216 words, PASSED quick verify
### Gemini review scores: 4/10 → 2/10 → 5/10

**Prose quality is good** — Gemini praised pedagogy, phonetics, textbook integration.
**Exercise quality is the bottleneck** — stray quotes, no fill-in context, wrong item counts.
**Claude consistently fails to produce long content** with this prompt. Gemini succeeds.

## BLOCKERS — Fix these next

### 1. Writer produces bad exercise placeholder metadata
- **Problem:** Writer (both Claude and Gemini) produces exercise placeholders with:
  - Stray single quotes in YAML values (`"'В"`, `"зву́ки'"`)
  - Fill-in exercises with no sentence context (just `"___"`)
  - Wrong item counts (plan says 6, writer provides 2)
  - Vague metadata that the filler can't turn into good exercises
- **Fix options:**
  a. Better prompt guidance for exercise placeholder format (show more examples)
  b. Post-processing to strip stray quotes from exercise YAML
  c. Separate LLM pass specifically for exercise content generation
  d. Move exercise generation to a dedicated Gemini call with the prose as context
- **Estimated scope:** Option (d) is most reliable — ~150 lines for exercise-specific LLM call

### 2. Claude fails to produce long content with current prompt
- **Problem:** Claude Opus consistently produces 150-500 word responses instead of 1200+
- Both attempts in the latest build failed (435 words, 148 words)
- Gemini succeeds on first try with 2,216 words
- **Options:**
  a. Use Gemini as default writer for A1 (Claude reviews instead)
  b. Investigate why Claude truncates — may be prompt too long (22K chars)
  c. Try different Claude invocation (longer max_turns, different flags)

### 3. Writer produces factual errors (Київ gaffe from attempt 2)
- **Problem:** Claude wrote "this one is и, not ї" about Київ — which is wrong (Київ has both)
- **Fix options:**
  a. Add factual verification step (check Ukrainian claims against VESUM/RAG)
  b. Better prompt: "Never make claims about specific Ukrainian words without verifying"
  c. Both
- **Where:** Post-processing in `step_annotate` or new verification in `step_verify`

### 3. LLM writing fingerprint
- **Problem:** "Good news:", "Don't panic", "That's a story for Module 2" — conversational but not premium
- **Fix:** Add negative examples to prompt (`phases/v6-write.md`): "Avoid: 'Good news', 'Don't worry', generic cheerfulness"
- **Estimated scope:** 5 lines added to prompt

## Key design decisions (don't re-discuss these)

- **Stress marks:** Writer produces NONE → deterministic annotator adds them. A1-A2 all words, B1+ vocabulary only.
- **Error recovery:** Max 2 retries, whole-module regeneration, model switching (Gemini↔Claude), no anchoring (don't include failed output in retry).
- **A1 writer:** Claude writes, Gemini reviews. B1+ flip (Gemini writes, Claude reviews).
- **Cases before verbs** in A2 (Genitive first — highest utility).
- **B1 100% Ukrainian immersion** from lesson 1 — metalanguage taught at end of A2.

## Key commands

```bash
# Build M01
.venv/bin/python scripts/build/v6_build.py a1 1 --writer claude

# Run plan checker
.venv/bin/python scripts/audit/check_plan.py a1 --first 55

# Run V6 tests
.venv/bin/python -m pytest tests/test_build_knowledge_packet.py tests/test_quick_verify.py tests/test_fill_placeholders.py -v

# Send to Gemini for review
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini "Review M01 content..." --task-id issue-981 --model gemini-3.1-pro-preview

# Knowledge packet standalone
.venv/bin/python scripts/build/research/build_knowledge_packet.py curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml
```

## Open issues (active)

| Issue | What | Priority |
|-------|------|----------|
| #982 | Epic: V6 Pipeline | HIGH — in progress |
| #981 | Epic: A1 rebuild | HIGH — plans done, content building |
| #994 | Research packet | ✅ DONE |
| #995 | Writing prompt | ✅ DONE (needs refinement) |
| #1006 | Quick verify + retry | ✅ DONE |
| #996 | Exercise filler | ⚠️ PARTIAL — skeletons work, needs LLM content |
| #988 | Stress annotation | ✅ DONE (existing code works) |
| #989 | Verification | ✅ DONE (existing code works) |
| #991 | Review calibration | ⬜ NOT STARTED |
| #997 | DSL→MDX converter | ✅ DONE (existing code works) |
| #1002 | B1 curriculum design | ⬜ DEFERRED |

## File locations

```
curriculum/l2-uk-en/plans/a1/     — 55 V3 plans
curriculum/l2-uk-en/plans/a2/     — empty (ready for V3 plans)
docs/l2-uk-en/A1-A2-CURRICULUM-V3.md — A1 curriculum design
docs/l2-uk-en/A2-CURRICULUM-V3.md — A2 curriculum design (60 modules)
docs/pipeline-v6-design.md        — V6 pipeline design
scripts/build/v6_build.py         — V6 orchestrator (682 lines)
scripts/build/research/           — knowledge packet generator
scripts/build/exercises/           — exercise filler
scripts/build/quick_verify.py     — structural checks
scripts/build/phases/v6-write.md  — writing prompt template
```
