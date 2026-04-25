# Session Handoff — 2026-03-25 (evening)

## Critical: What's NOT working yet

The new 4-tab lesson design exists as disconnected pieces. **The pipeline does NOT produce the new format yet.** M01 was built but renders with the OLD 2-tab design.

### What's broken in the pipeline:
1. **PUBLISH still uses old DSL→MDX path** — the V2 activity injection (from activities YAML) and 4-tab builder exist in code but the old path runs first and produces old format
2. **Writer still generates inline DSL exercises** alongside injection markers — both systems coexist, old one wins
3. **Landing pages use old design** — build_landing_pages.py doesn't know about new components

### What MUST happen next session (in this exact order):
1. **Fix PUBLISH** to use V2 path when activities YAML exists — strip old DSL, inject from YAML, build 4 tabs
2. **Fix writer prompt** to NOT generate `:::quiz` / `:::fill-in` DSL — only injection markers
3. **Test ONE module end-to-end** — M01 through full pipeline → new 4-tab MDX → Starlight renders correctly
4. **THEN scale** to all 55 A1 modules

## What was accomplished this session

### Pipeline improvements (13 issues closed)
- #1022 RAG collections, #1032 CLAUDE.md, #1027 review versioning
- #985 preflight auto-fixes, #989 validation FPs, #1018 VERIFY flags
- #1028 aggregation, #1029 orchestration index
- #998 chunking, #1033 review calibration, #1014 golden examples
- #1016 exercise verification, #984 plan review, #1023 activity hints tool

### Activity System V2 (4 issues closed: #1041-#1044)
- JSON Schema for 31 activity types
- Pipeline step (step_activities) with separate LLM call
- PUBLISH integration code (activity_renderer.py) — exists but not wired correctly
- Starlight components: RuleBox, MythBuster, SourceBox, FlashcardDeck
- lesson.css with dark mode

### Infrastructure
- Supply chain hardening (SHA-pinned actions, requirements.lock, Dependabot)
- Unified dispatch module with logging
- Writer tools 15→18, reviewer tools 6→14
- Gemini MCP fixed (10→21 tools visible)
- RAG crash fix (graceful disconnect)
- Major project cleanup (234 root scripts moved, 72 docs organized)

### Activity level awareness fix
- Activity generator now knows learner level
- A1.1: English instructions, letter-focused activities, Anna's video refs
- A1.2+: graduated Ukrainian introduction

### Issues created
- #1040: Scrape МійКлас grammar (the native reviewer's find)
- #1041-#1044: Activity System V2 (all closed)

### Closed: #1031 (Figma — not needed)

## Open issues blocking A1 rebuild

| Priority | What | Why |
|----------|------|-----|
| P0 | Fix PUBLISH to produce new 4-tab format | M01 renders old design |
| P0 | Fix writer to stop generating DSL exercises | Old and new systems conflict |
| P0 | Test one module end-to-end with new design | Nothing verified E2E |
| P1 | Run upgrade_activity_hints.py a1 --all | 43 vague hints need upgrading |
| P1 | Run review_plan.py a1 --all | Plans not adversarially reviewed |
| P2 | Rebuild all 55 A1 modules | Only after P0 is proven |

## Key technical notes

### Services
```bash
./services.sh status  # RAG on 8766, API on 8765, Starlight on 4321/4322
```

### Build command
```bash
.venv/bin/python scripts/build/v6_build.py a1 1 --writer gemini-tools
```

### New tools created this session
```bash
.venv/bin/python scripts/audit/review_plan.py a1 --all           # adversarial plan review
.venv/bin/python scripts/tools/upgrade_activity_hints.py a1 --all # upgrade vague hints
.venv/bin/python scripts/validate/validate_activities_v2.py a1 --all  # validate activity YAML
.venv/bin/python scripts/build/orch_index.py a1 --all             # orchestration indexes
.venv/bin/python scripts/audit/aggregate_review_findings.py a1    # aggregate findings
```

### New rule added to MEMORY.md
**SEQUENCE DISCIPLINE:** Finish what's started. Verify end-to-end. Push back on disorder. One working example FIRST, then scale.

## 400+ new tests this session
