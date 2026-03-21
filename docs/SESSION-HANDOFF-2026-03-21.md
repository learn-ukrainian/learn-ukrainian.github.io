# Session Handoff — 2026-03-21

**Continue from here next session. Read this first.**

---

## What was accomplished

### Issue Hygiene: COMPLETE ✅
- Audited all 9 "done" V6 issues — only #1001 was genuinely done (closed)
- 8 issues (#994, #995, #996, #997, #1006, #988, #989, #991) kept open with updated ACs
- 4 untracked blockers mapped to existing issues
- Created 5 new issues:
  - **#1007** — Monitor API V6 migration
  - **#1008** — Visual QA (Chrome-based, Claude-only)
  - **#1009** — Step 7b ENRICH
  - **#1010** — WORKSTREAMS.md rewrite
  - **#1011** — A2 plan writing epic

### V6 Pipeline Fixes: 1,525 lines added, 124 tests pass ✅
| Issue | Fix | Status |
|-------|-----|--------|
| **#996** | Strip stray LLM quotes, fill-in context sentences, TODO fallbacks replaced | ✅ Done |
| **#997** | DSL→MDX handles V6 YAML format, YouTube URL conversion | ✅ Done |
| **#1006** | Exercise item count check in quick_verify | ✅ Done |
| **#1007** | V6 writes state.json, API detects V6, build-stats endpoint | ✅ Done (Phase A+B) |
| **#1009** | ENRICH step: словник, videos, resources, dialogues | ✅ Done |

### Code Quality (/simplify review): COMPLETE ✅
- Extracted shared `text_utils.py` (strip_stray_quotes, parse_vocab_hint)
- Normalized V6 status to "complete" (not "done") — eliminated scattered workarounds
- Fixed `has_research_file()` bug for V6 knowledge-packet paths

### API Web Interface: UPDATED ✅
- Index page shows V6 + V5 counts
- Progress page recognizes V6 phases, chips show V6 modules correctly
- V6 modules no longer marked "obsolete"

### Documentation: IN PROGRESS 🔧
- WORKSTREAMS.md rewrite for V6 era (agent running)
- MONITOR-API.md V6 documentation (agent running)

---

## Pipeline Flow (complete)

```
CHECK → RESEARCH → WRITE+RETRY → EXERCISES → ANNOTATE → ENRICH → VERIFY → PUBLISH
```

All steps wired into orchestrator with state.json tracking.

---

## What's ready for next session

### Immediate: Rebuild M01
The pipeline can now produce a complete lesson with prose, exercises, vocabulary table, video embeds, and resources:

```bash
.venv/bin/python scripts/build/v6_build.py a1 1 --writer claude
```

### After M01 builds:
1. **Visual QA (#1008)** — open in Chrome, assess rendering
2. **Gemini adversarial review** → iterate until 9+/10
3. Scale to M02-M07 (A1.1 phase)

---

## Three quality pillars

```
Content quality    → Gemini adversarial review (target: 9+/10)
Structural quality → Audit gates (all green)
Visual quality     → Chrome visual inspection (#1008)
```

---

## Open issues (active, priority order)

### Epic #982: V6 Pipeline
| Issue | What | Status |
|-------|------|--------|
| #1007 | Monitor API V6 migration | ✅ Phase A+B done, web UI updated |
| #996 | Exercise filler fixes | ✅ Stray quotes + context done. LLM filler + VESUM verification still open |
| #997 | DSL→MDX converter | ✅ V6 format + YouTube done. Starlight build test still open |
| #1006 | Quick verify + retry | ✅ Item count done. Integration tests + friction auto-gen still open |
| #1009 | ENRICH step | ✅ Built + wired. Tab structure (Урок/Ресурси/Зошит) not yet implemented |
| #1008 | Visual QA | NOT STARTED — after M01 rebuild |
| #991 | Review calibration | 1/6 ACs — review step not wired into orchestrator |
| #994 | Research packet | 7/9 ACs — no assess_research quality gate |
| #995 | Writing prompt | 5/10 ACs — no chunking, no citation format |
| #988 | Stress annotation | 3/7 ACs — only tested on 1 module |
| #989 | Validation | 2/6 ACs — no fix loop |
| #985 | Preflight auto-fixes | NOT STARTED |
| #984 | LLM adversarial plan review | NOT STARTED |

### Epic #981: A1 Rebuild
| Issue | What | Status |
|-------|------|--------|
| #1011 | A2 plan writing | NOT STARTED — after A1.1 ships |

### Other
| Issue | What | Status |
|-------|------|--------|
| #1010 | WORKSTREAMS.md rewrite | IN PROGRESS |

---

## Architecture decisions (don't re-discuss)

- **Writer:** Claude (better tone/pedagogy, 8.55 vs 8.35)
- **Reviewer:** Gemini (adversarial, 10-dimension rubric)
- **Visual QA:** Claude only (browser tools)
- **Stress marks:** Writer produces NONE → deterministic annotator
- **Error recovery:** Max 2 retries, whole-module regen, model switch
- **Tab structure:** Урок / Ресурси / Зошит (planned, not yet in ENRICH)
- **Status normalization:** V6 uses "complete" (same as V5) — no "done" divergence
- **API is cognitive infrastructure:** gives Claude instant project state, not just a dashboard

## Key commands

```bash
# Build M01 with Claude (full pipeline)
.venv/bin/python scripts/build/v6_build.py a1 1 --writer claude

# Run single step
.venv/bin/python scripts/build/v6_build.py a1 1 --step enrich

# Run V6 tests (124 pass)
.venv/bin/python -m pytest tests/test_fill_placeholders.py tests/test_quick_verify.py tests/test_dsl_to_mdx.py tests/test_enrich.py -v

# Check API build stats
curl -s http://localhost:8765/api/state/build-stats/a1

# V6 pipeline versions
curl -s http://localhost:8765/api/state/pipeline-versions
```
