# Master Plan — Priority Sequencing

> 75 open issues. Zero shipped modules. This plan sequences everything so each phase unblocks the next.

---

## The Core Problem

We built massive infrastructure (1,735 module plans, RAG with 663K vectors, 14 dictionaries, 50+ React components, monitoring API) but **zero modules have reached learners**. Every quality system is producer-side — no learner signal exists.

The pipeline has critical bugs. The code has never been fully reviewed. There are no skills for systematic code review. There are no pre-commit hooks. Frontend has 4/50+ tests.

**We need to stop building new infrastructure and start shipping.**

---

## Tracking

**Epic: #1093** — read this at the START of every session. Update at the END.

---

## Phase 0: Skills (unblocks everything)
**Time: 1-2 sessions | Issues: #1074, #1075**

Build the tools that make all subsequent work faster and more reliable.

| Order | Issue | Skill | Why first |
|-------|-------|-------|-----------|
| 0a | #1074 | `code-review` | Every code fix needs review. Without this, pre-commit checklist is forgotten. |
| 0b | #1075 | `prompt-template-review` | Every prompt fix needs validation. 3 template bugs found in v6 review. |

---

## Phase 1: Fix the pipeline (unblocks content)
**Time: 2-3 sessions | Issues: #1073, #1072, #1068, #1070**

4 critical bugs and scattered model resolution. Until fixed, every build is broken.

| Order | Issue | What |
|-------|-------|------|
| 1a | #1073 | Fix P0 bugs (BUG-01, 08, 09, 15) |
| 1b | #1073 | Remove dead code (BUG-03, 04, 05) |
| 1c | #1072 | ModelFamily refactor |
| 1d | #1068 | Fix audit pipeline (0/11 pass) |
| 1e | #1070 | Fix Gemini MCP tool usage |

---

## Phase 2: Quality infrastructure + analytics (prevents regressions, starts learner signal)
**Time: 2-3 sessions | Issues: #1081, #1083, #1080, #1091, #1086**

Lock down quality and start collecting data from day one — so when A1 ships, we already have analytics running.

| Order | Issue | What |
|-------|-------|------|
| 2a | #1086 | Site analytics (Plausible/Umami) — just a script tag, instant value |
| 2b | #1081 | Pre-commit hooks + dependency lock + mypy |
| 2c | #1083 | Prompt versioning + regression testing |
| 2d | #1080 | Onboarding guide + requirements.txt |
| 2e | #1091 | Secret scanning in CI |

---

## Phase 3: Full code review (with proper skills)
**Time: 3-5 sessions | Issues: #1077, #1078, #1082**

Skills exist (Phase 0), pipeline stable (Phase 1), quality gates active (Phase 2). Now do thorough reviews.

| Order | Issue | What | Approach |
|-------|-------|------|----------|
| 3a | #1077 | Backend code review (13,500 lines) | Use `code-review` skill. Batch: audit/ → pipeline/ → build/ → research/ → tools/ → generate_mdx/ → agent_bridge/ → MCP server |
| 3b | #1078 | Frontend code review (50+ components) | Use `code-review` skill + browser tools. Verify props match activity_renderer.py. |
| 3c | #1082 | Frontend test coverage | Write tests for critical components found in 3b |

---

## Phase 4: Ship A1 M01-M11 (first content to learners)
**Time: 3-5 sessions | Issues: #1050, #1048, #1030, #1067, #1087**

Pipeline fixed, code reviewed, quality locked. Ship with confidence.

| Order | Issue | What |
|-------|-------|------|
| 4a | #1048 | Rebuild M02 + M03 (pedagogy issues) |
| 4b | #1030 | Quality pass on M04-M11 (fix activity density/types) |
| 4c | — | Full audit on all 11, fix remaining failures |
| 4d | #1067 | Apply POC lesson design to frontend |
| 4e | #1087 | Enable auto-deploy, staging, preview deploys |

After Phase 4: **11 modules live for learners.**

---

## Phase 5: Content scale (A1 complete → A2)
**Time: 5-10 sessions | Issues: #1050, #1011, #1089**

| Order | What |
|-------|------|
| 5a | Build A1 M12-M55 (remaining 44 modules) |
| 5b | A2 plan writing (#1011, 60 modules) |
| 5c | Vocabulary progression tracking (#1089) |

---

## Phase 6: Learner-facing quality
**Time: 3-5 sessions | Issues: #1088, #1084, #1090**

Analytics already running from Phase 2. Now add deeper quality signals.

| Order | Issue | What |
|-------|-------|------|
| 6a | #1088 | Accessibility standards |
| 6b | #1084 | Human evaluation framework (native speaker teacher) |
| 6c | #1090 | Style guide for human editors |

---

## Deferred (after A2 ships)

| Issue | What |
|-------|------|
| #1076 | Context-budget-audit skill |
| #1085 | Token cost tracking |
| #1079 | ADR system + diagrams |
| #1092 | Content licensing |

---

## Session Protocol

**START of session:**
1. Read epic #1093
2. Check which phase/issue is current
3. `curl -s http://localhost:8765/api/state/summary` for project state

**END of session:**
1. Update epic #1093 with progress
2. Write handoff to `docs/handoffs/SESSION-HANDOFF-{date}.md`
3. Commit all work
