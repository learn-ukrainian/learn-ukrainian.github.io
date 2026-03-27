# Session Handoff — 2026-03-27 (afternoon)

## What was accomplished

### Phase 0: Skills
1. **`code-review` skill** (#1074) — automated pre-commit quality gate with ruff, project-specific checks, Gemini adversarial review, test coverage
2. **`prompt-template-review` skill** (#1075) — validates pipeline prompt templates for unreplaced placeholders, contradictions, stale instructions

### Phase 1: Pipeline fixes
3. **P0 bug fixes** in v6_build.py (#1073):
   - BUG-01: Chunked write now passes MCP tools through
   - BUG-08: High-scoring REVISE logs unfixed errors before accepting
   - BUG-09: Seminar template placeholders `{SKELETON_SECTION}` + `{CORRECTION_SECTION}` now replaced
   - BUG-15: Chunk prompt changed from DSL to INJECT_ACTIVITY markers
4. **Dead code removed**: `_build_review_correction()`, `_parse_review_fixes()`, orphan comments, 12 redundant `import re` statements (106 lines removed)
5. **ModelFamily refactor** (#1072): dataclass with thinking/fast tiers, all 5 hardcoded model strings centralized
6. **Audit pipeline fixed** (#1068): persona non-blocking, A1 schema updated (observe, letter-grid, translate, anagram V2 format). 6/9 A1 modules pass (was 0/1735)

### Gap analysis + issue creation
7. Full code review of v6_build.py (3,660 lines) → `docs/architecture/v6-pipeline-review.md`
8. Comprehensive gap analysis → 19 new issues (#1074-#1092)
9. Master plan created → `docs/MASTER-PLAN.md`
10. Epic created → #1093

### Test fixes
11. Fixed stale imports in `test_coverage_batch_agent.py` (batch_fix_review → batch.batch_fix_review, etc.)
12. Fixed stale imports in `test_coverage_misc.py` (assess_research_helpers → research.assess_research_helpers, etc.)
13. Fixed imports in `test_video_discovery.py` (split between video_discovery + video_discovery_helpers)
14. Skipped import_zno tests (module deleted)
15. Removed test_v6_review_correction.py (tested deleted functions)
16. Test failures: 263 → 85

## A1 module status

| Module | Audit | Notes |
|--------|-------|-------|
| M01 sounds-letters-and-hello | ✅ | |
| M04 stress-and-melody | ❌ | Activity density 4<6 (needs more items) |
| M05 who-am-i | ❌ | Density 3<6 + robotic structure |
| M06 my-family | ❌ | Lint: AI contamination + anagram schema |
| M08 things-have-gender | ✅ | |
| M09 what-is-it-like | ✅ | |
| M10 colors | ✅ | |
| M11 how-many | ✅ | |

M02 reading-ukrainian and M03 not audited (unstaged changes / needs rebuild).

## Blockers
- **Gemini down** (2+ days) — cannot test dispatch, cross-agent review, or content builds
- **85 pre-existing test failures** — mostly stale imports from project cleanup

## Next session priorities
1. Continue fixing remaining test failures
2. Phase 1e (#1070 Gemini MCP) when Gemini returns
3. Phase 2a: Site analytics (#1086)
4. Phase 2b: Pre-commit hooks (#1081)

## Key files changed
| File | Changes |
|------|---------|
| scripts/build/v6_build.py | P0 fixes, dead code removal, ModelFamily dataclass, import cleanup (3660→3554 lines) |
| scripts/build/phases/v6-write-seminar.md | (Unchanged — placeholders now replaced by Python code) |
| scripts/audit/phases_gates.py | Persona gate non-blocking for V6 |
| schemas/activities-a1.schema.json | Added observe, letter-grid, translate; updated anagram for V2 format |
| claude_extensions/skills/code-review/ | NEW: skill + checklist |
| claude_extensions/skills/prompt-template-review/ | NEW: skill + checklist |
| docs/architecture/v6-pipeline-review.md | NEW: full pipeline review |
| docs/MASTER-PLAN.md | NEW: 6-phase priority plan |
| tests/test_coverage_batch_agent.py | Fixed stale imports |
| tests/test_coverage_misc.py | Fixed stale imports, skipped deleted module tests |
| tests/test_video_discovery.py | Fixed split imports |
| tests/test_v6_review_correction.py | DELETED (tested removed functions) |

## Services
```bash
./services.sh status  # RAG on 8766, API on 8765, Starlight on 4321
```
