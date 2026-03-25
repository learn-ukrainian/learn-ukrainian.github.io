# Session Handoff — 2026-03-21

**Continue from here next session. Read this first.**

---

## What was accomplished (8 commits)

### Issue Hygiene ✅
- Audited all 9 "done" V6 issues — only #1001 genuinely done (closed)
- Updated ACs on #996, #1006, #997, #991 with gaps found
- Created 7 new issues: #1007-#1014
- Closed #1001 (writer comparison), #1010 (WORKSTREAMS rewrite)

### V6 Pipeline Fixes (1,525 lines, 124 tests) ✅
| Issue | Fix |
|-------|-----|
| #996 | Stray quotes stripped, fill-in context, TODO fallbacks replaced |
| #997 | DSL→MDX handles V6 YAML format, YouTube URL conversion |
| #1006 | Exercise item count check in quick_verify |
| #1007 | V6 writes state.json, API detects V6, build-stats endpoint, web UI updated |
| #1009 | ENRICH step: словник, videos, resources, dialogues. Wired into orchestrator |
| #991 | Review step wired into orchestrator with deterministic score calculation |

### Prompt Engineering (2 rounds of Gemini adversarial review) ✅
| Round | Writing | Review | Key fixes |
|-------|---------|--------|-----------|
| Before | 7/10 | 3/10 | — |
| Round 1 | Fixed | Fixed | Rule 5 contradiction, stress marks, token exhaustion, словník penalty |
| Round 2 | 8.5→fixed | 6.5→fixed | XML injection tags, deterministic math, VERIFY flag, RAG verification |

### Prompt Optimization (#1013, #1014) ✅
- 6 Ukrainian textbook exercise patterns (Заболотний, Авраменко)
- 5 forbidden LLM tropes (Cheerleader, Announcer, Translator, Wall of Text, Filler)
- 4 dynamic golden fragments via `config_tables.py` (Early Beginner → Advanced bands)

### Lesson Page Design (#1012) ✅
- Product interview: 4 tabs (Урок/Словник/Зошит/Ресурси)
- Inline textbook-style exercises, flip flashcards, curated external resources
- Gemini-reviewed, findings incorporated
- Issue created with full ACs

### Code Quality ✅
- Shared `text_utils.py` (strip_stray_quotes, parse_vocab_hint)
- Normalized V6 status to "complete"
- Fixed has_research_file() bug
- /simplify review with 3 parallel agents

### Documentation ✅
- WORKSTREAMS.md rewritten for V6 era
- MONITOR-API.md updated with V6 endpoints
- Session handoff

---

## Pipeline Flow (complete)

```
CHECK → RESEARCH → WRITE+RETRY → EXERCISES → ANNOTATE → ENRICH → VERIFY → REVIEW → PUBLISH
```

---

## Next session priority

### 1. Rebuild M01
```bash
.venv/bin/python scripts/build/v6_build.py a1 1 --writer claude
```

### 2. Visual QA (#1008)
Open Starlight dev server, inspect M01 in Chrome

### 3. Iterate to 9+/10
Gemini adversarial review → fix → rebuild → repeat

### 4. Implement lesson page layout (#1012)
Tab structure, flashcards, external resources from existing data

### 5. Scale to M02-M07

---

## Open issues (priority order)

### Epic #982: V6 Pipeline
| Issue | What | Status |
|-------|------|--------|
| #1012 | Lesson page design (4 tabs) | Gemini-reviewed, ready to implement |
| #1013 | Exercise patterns + forbidden tropes | Prompt text done, filler support + test pending |
| #1014 | Dynamic golden fragments | 4 bands done, seminar example + test pending |
| #1008 | Visual QA | After M01 rebuild |
| #1007 | Monitor API V6 | Phase A+B done, web UI updated |
| #1009 | ENRICH step | Built, tab structure not yet |
| #996 | Exercise filler | Core fixes done, LLM filler + VESUM pending |
| #997 | DSL→MDX | V6 format done, Starlight build test pending |
| #991 | Review calibration | Wired into orchestrator, calibration pending |
| #1006 | Quick verify | Item count done, integration tests pending |
| #995 | Writing prompt | Prompt fixes done, chunking pending |

### Epic #981: A1 Rebuild
| Issue | What | Status |
|-------|------|--------|
| #1011 | A2 plan writing | After A1.1 ships |

---

## Key commands

```bash
# Build M01 (full pipeline)
.venv/bin/python scripts/build/v6_build.py a1 1 --writer claude

# Single step
.venv/bin/python scripts/build/v6_build.py a1 1 --step enrich

# Tests (124 pass)
.venv/bin/python -m pytest tests/test_fill_placeholders.py tests/test_quick_verify.py tests/test_dsl_to_mdx.py tests/test_enrich.py -v

# API
curl -s http://localhost:8765/api/state/build-stats/a1
curl -s http://localhost:8765/api/state/pipeline-versions
```

## Architecture decisions (don't re-discuss)

- Writer: Claude | Reviewer: Gemini | Visual QA: Claude (browser)
- Stress marks: deterministic tool, NOT in prompts
- V6 status: "complete" (same as V5, no "done" divergence)
- Injected context wrapped in XML tags (anti-injection)
- Review score: LLM outputs raw scores, Python calculates weighted total
- Golden examples: 4 dynamic bands for core, static for seminars
- Lesson tabs: Урок / Словник / Зошит (coming soon) / Ресурси
- External resources: fill from existing `external_resources.yaml` + resource DBs now
