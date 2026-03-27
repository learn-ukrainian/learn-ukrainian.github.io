# Session Handoff — 2026-03-27

## What was accomplished (22 commits)

### P0: Infrastructure fixes
1. **Stress annotator** (#1052) — body-only check, 5% threshold
2. **VESUM false positives** (#1053) — bracket stripping, whitelist, POS abbreviations
3. **Exercise counting** (#1054) — INJECT_ACTIVITY markers + JSX components
4. **Writer prompt** (#1055) — 5 hard rules enforcing knowledge packet terminology
5. **Pedagogy patterns** (#1051) — 15 topic patterns injected into activities prompt

### P1: МійКлас + ULP integration
6. **МійКлас URL index** (#1040) — 70 lesson URLs, auto-fetch in knowledge packet
7. **ULP article index** (#1056) — 70+ articles from sitemap
8. **ENRICH auto-matching** — tag-based fallback for both indexes
9. **Re-enriched + re-annotated M01-M11** — new links + stress marks

### P2: Audit pipeline (#1068)
10. **Audit passes 6/11 modules** (was 0/1735) — plan-based metadata, V6 format, immersion thresholds, engagement regex, section balance, outline compliance

### P3: Pipeline improvements
11. **Dimension floor** — never PASS content with identified errors
12. **Auto-clean artifacts** on full rebuild
13. **RAG health check** + /health endpoint on MCP server
14. **--reviewer flag** for reviewer override
15. **Section-level rewrite** replaces find/replace fix loop
16. **Model tiering** — Sonnet for skeleton/activities/vocab, Opus for write/review
17. **Flash-Lite model config** (Gemini MCP configured but not calling tools)
18. **Frontend redesign epic** (#1067) created for POC lesson design

## Critical issues discovered

### Gemini doesn't call MCP tools (#1070)
- Gemini connects to RAG MCP server but makes ZERO tool calls during writing
- Direct test: Gemini DOES call tools when explicitly asked (short prompt)
- Root cause: 33K-char write prompt — Gemini ignores tool instructions when confident
- Fix needed: pre-write verification phase (dispatch tools BEFORE writing)

### Fix rounds degrade content (#1071)
- Find/replace breaks prose flow — scores oscillate instead of converging
- M02 rebuilt 6+ times, never reached PASS
- Section-level rewrite implemented but Claude outputted "changes table" instead of content
- Body extraction bug (TAB:Урок at pos 0) fixed with `_extract_body()` helper

### v6_build.py needs full code review (#1073) — BLOCKS EVERYTHING
- 3,662 lines patched 20+ times without understanding the whole system
- Agent found: 150 lines dead code, tool prefix bug, wrong defaults, stale comments
- Proper ModelFamily refactor designed (#1072) but blocked on review

## M02 status
- 6 rebuild attempts, best score 8.8/10 (linguistic accuracy 10, engagement 6-8)
- Claude hallucinates phonetic details (вулиця letters wrong)
- Gemini writes correct Ukrainian but weak engagement/dialogues
- Neither alone solves it
- Currently has content from last Claude build (8.6/10, review found errors)

## A1 module status

| Module | Score | Audit | Notes |
|--------|-------|-------|-------|
| M01 | 9.8 | ✅ | |
| M02 | 8.6 | ? | Needs rebuild after code review |
| M03 | 9.1 | ❌ | Needs rebuild (pedagogy) |
| M04 | 9.2 | ✅ | |
| M05 | 9.7 | ❌ | Activity density |
| M06 | 10.0 | ❌ | Activity density |
| M07 | 6.0 | ❌ | Needs rebuild (REJECT) |
| M08 | 9.8 | ✅ | |
| M09 | 9.9 | ✅ | |
| M10 | 9.2 | ✅ | |
| M11 | 10.0 | ❌ | Activity density |

## What to do next session — PRIORITY ORDER

### 1. Full code review (#1073) — FIRST, before touching anything
Read every line of v6_build.py, every prompt template, dispatch.py.
Document the architecture in `docs/architecture/v6-pipeline-review.md`.
This blocks all other pipeline work.

### 2. ModelFamily refactor (#1072) — after review
Replace scattered model resolution with ModelFamily dataclass.
Two CLI flags: `--writer {claude,gemini}` + `--reviewer {claude,gemini}`.
Each family has thinking (Opus/Pro) + fast (Sonnet/Flash) tiers.

### 3. Fix Gemini MCP tool usage (#1070) — after refactor
Pre-write verification phase: dispatch tools BEFORE writing.

### 4. Rebuild M02, M03, M07 — after pipeline is solid

### 5. Frontend redesign (#1067) — after content is stable

## Open issues
| # | Title | Priority |
|---|-------|----------|
| 1073 | Code review: v6_build.py + prompts + dispatch | P0 (BLOCKS ALL) |
| 1072 | Refactor: ModelFamily dispatch system | P1 |
| 1071 | Fix rounds degrade content | P1 (section rewrite implemented) |
| 1070 | Gemini ignores MCP tools | P1 |
| 1068 | Audit pipeline V6 format (6/11 pass) | P2 |
| 1067 | Frontend redesign — POC lesson design | P3 |
| 1050 | EPIC: A1 rebuild | Parent epic |

## Key files changed this session
| File | Changes |
|------|---------|
| scripts/build/v6_build.py | Rewrite loop, model tiering, artifact cleanup, body extraction, dead code removal |
| scripts/build/phases/v6-write.md | Knowledge packet enforcement, mandatory tool verification |
| scripts/build/phases/v6-review.md | Dimension floor, error-must-have-fix rule |
| scripts/build/phases/v6-activities.md | Pedagogy patterns injection |
| scripts/pipeline/stress_annotator.py | Body-only check, named threshold |
| scripts/audit/checks/morphological_validator.py | Bracket stripping |
| scripts/audit/core.py | Plan-based metadata, V6 template skip |
| scripts/audit/phases_gates.py | Engagement regex, persona/priority non-blocking |
| scripts/build/enrich.py | Auto-match МійКлас + ULP from tag indexes |
| scripts/research/build_knowledge_packet.py | МійКлас auto-fetch |
| docs/rules/pedagogy-patterns.yaml | NEW: 15 exercise patterns |
| docs/resources/miyklas-url-index.yaml | NEW: 70 lesson URLs |
| docs/resources/ulp-articles-index.yaml | NEW: 70+ article URLs |
| .mcp/servers/rag/server.py | /health endpoint |
| .gemini/settings.json | MCP RAG server config |

## Services
```bash
./services.sh status  # RAG on 8766, API on 8765, Starlight on 4321
```

## Build command (after pipeline is fixed)
```bash
.venv/bin/python scripts/build/v6_build.py a1 2 --writer claude-tools --reviewer claude-tools
```
