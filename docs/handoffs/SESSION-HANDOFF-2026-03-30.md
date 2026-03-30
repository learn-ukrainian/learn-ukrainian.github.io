# Session Handoff — 2026-03-30

## What was accomplished

### A1 Content Building — 39/55 modules built
| Range | Status | Notes |
|-------|--------|-------|
| M01-M07 | ✅ Built + audited | M01-M03 rebuilt with Claude (was Gemini). Unit 1 complete |
| M08-M14 | 🔄 Rebuilding | New dialogue situations (pet shop, book fair, bakery, etc.) replacing сумка/стіл |
| M15-M27 | ✅ Built | M15 rebuilt (immersion fix). M18/M26/M27 missing reviews (Gemini down) |
| M28-M39 | ✅ Built | From overnight batch. All audit passing |
| M40-M55 | ❌ Not built | 16 modules remaining |

### Pipeline Fixes (20+)
1. **--resume flag** — smart recovery from interrupted builds, skips completed phases
2. **--range flag** — batch builds with auto-skip for complete modules
3. **Activity timeout** 300→600s — prevents first-attempt timeouts
4. **Gemini review** — 5 retries, 900s timeout, adaptive backoff, latency probe
5. **LEARN_UKRAINIAN_PIPELINE=1** — skips hooks in dispatch (26s→5s startup)
6. **YAML preamble stripping** — handles LLM commentary before YAML
7. **Short response rejection** — <2000 chars = instant retry
8. **Post-review fix verification** — runs BEFORE enrich (was after, causing false positives)
9. **Stress-mark aware verification** — strips ´ before comparing
10. **Multi-line fix matching** — normalizes whitespace for cross-line fixes
11. **MDX validation** — checks imports, props, braces, tab matching after publish
12. **Activity sequencing check** (gf-013) — markers must appear after concepts taught
13. **Checkpoint vocab skip** — descriptive entries like "recycled from M01-M06" not treated as missing words
14. **Content redundancy fix** — excludes Підсумок, Словник, dialogues, tables from cross-comparison
15. **Hard Rule #10** — "EVERY module MUST end with Підсумок" prevents missing summary
16. **Immersion ceiling** — M01-M03 raised to 25% (phonetics modules need more Ukrainian)
17. **--approval-mode=yolo** — Gemini CLI v0.35.3 compatibility
18. **Skeleton warning** suppressed during --step review
19. **Guard against missing content file** — clean exit instead of crash

### Activity & Schema Fixes
1. **error-correction** — parser accepts both `correction` and `answer` fields
2. **unjumble** — schema accepts both `answer` (string) and `correct_order` (array)
3. **error-correction added to A1** schema — checkpoint modules can use it
4. **Checkpoint relaxed restrictions** — error-correction, select, translate allowed at A1 checkpoints
5. **27 modules republished** with working error-correction activities

### Dialogue Situations (#1102)
- **A1**: 50/50 modules — reviewed by Claude agent, 8 fixes applied
- **A2**: 54/54 modules — done, needs Gemini review
- **B1**: 91/91 modules — done, needs review
- **Documentation**: `docs/best-practices/dialogue-situations.md`
- **Schema**: `dialogue_situations` field added to `module-plan.schema.json`
- **Pipeline**: `_build_dialogue_situations()` reads from plan, injects into write prompt

### B2-C2 Architecture (#1115)
- New activity types: `reading_situations`, `listening_situations`, `writing_tasks`, `discussion_topics`
- Schema updated with 4 new fields
- Architecture doc: `docs/best-practices/b2-c2-plan-architecture.md`
- B2 plans: 90 written by Gemini but need fixes (word_target wrong, missing activity_hints)

### Review Quality Improvements
- **Proof of absence** rule — reviewer must search before claiming something is missing
- **Euphony gf-014** — у/в alternation is MINOR, never CRITICAL
- **Dialogue variety** — banned recycled settings, specific objects per module
- **Immersion rule #1** in write prompt — "LEARNER CANNOT READ CYRILLIC" for M01-M03
- **Video-first pedagogy** — M01-M03 letters introduced by Anna Ohoiko videos

### Infrastructure
- **Qdrant migrated** from Colima to OrbStack
- **Colima removed** — freed ~2GB (LLVM, Lima)
- **Data cleanup** — removed 4.2GB of backed-up JSONL source dirs
- **Backup script** — simplified to rsync entire data/ minus qdrant/
- **Landing page generator** — `scripts/generate_landing_pages.py` for all 22 tracks

### Issues
- Closed: #1054, #1055 (pending Gemini review), #1094, #1095, #1115
- Created: #1102 (dialogue situations), #1114 (pipeline refactor), #1116 (B2 plans), #1117 (C1 plans), #1118 (C2 plans), #1119 (A2 plan review), #1120 (B1 plan review)

## Next session priorities

### 1. Finish A1 building
- M08-M14 rebuilding now — check results
- M40-M55 need building: `a1 40 --range 55 --writer claude-tools --reviewer claude-tools`
- M29 needs `--step activities` (missing activities sidecar)
- M18, M26, M27 need review when Gemini is back

### 2. Commit overnight build results
- M09-M14 rebuilds (with new dialogue situations)
- M15 rebuild
- M35 rebuild
- Update landing page

### 3. Gemini tasks (when stable)
- B2 plans: fix word_target to 4000, add activity_hints (#1116)
- Review A2 dialogue situations (#1102 AC6)
- Review B1 dialogue situations (#1102 AC7)

### 4. Before A2 content building
- Pipeline refactor (#1114) — BuildContext + pipeline engine
- A2 plan RAG verification (#1119)
- B1 plan RAG verification (#1120)

## Services
```bash
./services.sh status  # RAG on 8766, API on 8765, Starlight on 4321
```

## Build commands
```bash
# Single module
.venv/bin/python scripts/build/v6_build.py a1 {N} --writer claude-tools --reviewer claude-tools

# Batch
.venv/bin/python scripts/build/v6_build.py a1 40 --range 55 --writer claude-tools --reviewer claude-tools

# Resume interrupted
.venv/bin/python scripts/build/v6_build.py a1 {N} --resume --writer claude-tools --reviewer claude-tools

# Republish only
.venv/bin/python scripts/build/v6_build.py a1 {N} --step publish --writer claude-tools

# Landing page
.venv/bin/python scripts/generate_landing_pages.py --track a1
```

## Key learnings
- **Dialogue situations with specific objects** prevent the writer from defaulting to сумка/стіл
- **Error-correction is a great activity type** — works for all levels, especially checkpoints
- **Content redundancy checker** was too aggressive — summaries, dialogues, and vocab tables legitimately repeat
- **Gemini is unreliable** for live reviews — use Claude as reviewer, or create GH issues for async review
- **Fix verification must run BEFORE enrich** — enrich changes the content and causes false positives
- **--resume saves hours** when builds get interrupted by rate limits
