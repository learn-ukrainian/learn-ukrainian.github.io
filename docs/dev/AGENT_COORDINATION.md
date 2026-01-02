# Agent Coordination Hub

**Last Updated:** 2026-01-02 (afternoon)
**Coordinator:** Claude 1 (this session)

## Active Agents

| Code | Agent | Subscription | Current Task | Issue | Status |
|------|-------|--------------|--------------|-------|--------|
| **A** | Gemini 1 | User's | B2 M111 | #349 | ✅ Complete (reviewed) |
| **M** | Gemini 2 | User's | B2 M112 | #349 | ✅ Complete (reviewed) |
| **K** | Gemini 3 | User's | B1 M81-84 | #351 | ✅ Complete (4 modules created) |
| **C1-b** | Claude 1 (other session) | User's | B2 enrichment | #349 | 🔄 M01-M10 done |
| **Opus** | Antigravity Opus | Google AI Pro #1 | Grammar validation refactor | #352 | 🔄 In progress |
| **C2** | Claude 2 | Different sub | (standing by) | - | ⏳ Available |

## This Session (C1-a: Coordinator)

- **Role:** Review hub, agent coordination, issue management
- **Same Claude, different session:** C1-b is doing B2 migration
- **Tracking:** All agent progress, reviewing completed work

## Context Files

| Agent | Context Document | Model |
|-------|------------------|-------|
| Agent M (Gemini 2) | `docs/dev/GEMINI2_B1_MIGRATION_CONTEXT.md` | gemini-3-flash |
| C1-b (Claude other session) | `docs/dev/CLAUDE_B2_MIGRATION_CONTEXT.md` | Sonnet |
| **Gemini (B1 M81-84)** | **`docs/dev/GEMINI_B1_M81-84_CONTEXT.md`** | **gemini-3-flash (pilot on M81)** |
| Agent K (Gemini 3) | TBD - assign when context resets | gemini-3-flash |
| C2 (Claude 2) | TBD - standing by for assignment | Sonnet/Opus |

## Migration Progress

| Level | Modules | Extraction | Enrichment | Content Quality | Status |
|-------|---------|------------|------------|-----------------|--------|
| A1 | 34 | ✅ Done | ✅ Done | ✅ 34/34 pass | ✅ Complete |
| A2 | 57 | ✅ Done | ✅ Done | ✅ 57/57 pass | ✅ Complete |
| B1 | 91 | ✅ Done | ✅ Done | ⚠️ 76/91 pass (15 need word count fixes) | 🔄 Quality issues |
| B2 | 145 | ✅ Done | 🔄 10/145 | ⚠️ 123/145 pass (8 fail, 14 unbuilt) | 🔄 In progress |

## C1-b B2 Enrichment Progress

```
☒ Run B2 vocabulary extraction script
☒ Verify extraction (110 YAML files)
☒ Enrich M01-M03 (passive voice)
☒ Enrich M04-M10 (passive voice remainder)
☐ Enrich vocabulary M11-M30 (syntax, registers)
☐ Enrich vocabulary M31-M70 (idioms, synonyms)
☐ Run global vocab audit validation
☐ Test pipeline on B2
```

**Note:** M71-M110 (history modules) not yet in enrichment queue.

## B2 Module Status

| Range | Count | Content | Vocabulary YAML | Enrichment | Audit Status |
|-------|-------|---------|-----------------|------------|--------------|
| M01-M10 | 10 | ✅ | ✅ | ✅ Done | ✅ Pass |
| M11-M70 | 60 | ✅ | ✅ | ❌ Pending | ✅ Pass |
| M71-M110 | 40 | ✅ | ✅ | ❌ Pending | ✅ Pass |
| M111-M115 | 5 | ✅ | ✅ | ❌ Pending | ✅ Pass |
| M116 | 1 | ✅ | ✅ | ❌ Pending | ❌ FAIL: 1653/1750 words |
| M117 | 1 | ✅ | ✅ | ❌ Pending | ✅ Pass |
| M118-M120 | 3 | ✅ | ✅ | ❌ Pending | ❌ FAIL: <1750 words |
| M121-M122 | 2 | ✅ | ✅ | ❌ Pending | ✅ Pass |
| M123-M124 | 2 | ✅ | ✅ | ❌ Pending | ❌ FAIL: <1750 words |
| M125-M126 | 2 | ✅ | ✅ | ❌ Pending | ✅ Pass |
| M127-M128 | 2 | ✅ | ✅ | ❌ Pending | ❌ FAIL: <1750 words |
| M129-M131 | 3 | ✅ | ✅ | ❌ Pending | ✅ Pass |
| M132-M145 | 14 | ❌ Need to build | ❌ | ❌ | - |

**Total:** 123/145 modules PASS (85%), 8 FAIL word count, 14 not built

**CRITICAL: B2+ 1750-word target is HARD requirement (not soft warning)**

**Failed modules (need content expansion):**
- M116: 1653/1750 (-97) → needs +100 words
- M118: 1706/1750 (-44) → needs +50 words
- M119: 1742/1750 (-8) → needs +10 words
- M120: 1724/1750 (-26) → needs +30 words
- M123: 1709/1750 (-41) → needs +50 words
- M124: 1676/1750 (-74) → needs +80 words
- M127: 1656/1750 (-94) → needs +100 words
- M128: 1720/1750 (-30) → needs +35 words

## Issue Tracking

- **#340** - Epic: Vocabulary YAML Architecture (Agent A - A2) - ✅ CLOSED
- **#349** - B2 YAML Migration (C1-b) - 🔄 IN PROGRESS
- **#350** - B1 YAML Migration (Agent M) - ⏸️ BLOCKED by #352
- **#351** - B1.7 Expansion (Agent K) - ✅ CLOSED (M81-M84 complete)
- **#352** - Grammar Validation Refactor (Antigravity Opus) - 🔄 IN PROGRESS

## Issue #352: Grammar Validation System Refactor

**Agent:** Antigravity Opus (Google AI Pro #1)
**Priority:** P0 - BLOCKS ALL CONTENT WORK
**Status:** 🔄 In progress (corrected scope assigned)

### Problem
- Queue generation still in pipeline (`scripts/pipeline.py` line 306)
- Next pipeline run will recreate 300+ deleted queue files
- Grammar validation is overcomplicated and unreliable

### Solution Required

**Phase 1: Remove Queue Generation**
- Remove `grammar_queue` from pipeline default steps
- Delete queue generation scripts: `generate_grammar_queue.py`, `generate_grammar_review_queue.py`, `finalize_validation.py`
- Remove `step_grammar_queue()` from `scripts/pipeline.py`

**Phase 2: Implement Direct LLM Validation**
- Add `--validate-grammar` flag to audit script (opt-in like content quality)
- Use Gemini API directly on flagged sentences (no queue intermediary)
- Update `scripts/audit/ukrainian_grammar_validator_prompt.md`

**Phase 3: Documentation**
- Update CLAUDE.md, SCRIPTS.md, CONTENT-QUALITY-AUDIT.md
- Remove queue references

**Verification:**
```bash
npm run pipeline l2-uk-en b1 1
ls curriculum/l2-uk-en/b1/queue/  # Should not exist
```

**Blocks:** B1 word count fixes (15 modules), all content work

## Remaining B2 Work: M132-M145 (14 modules)

| Module | Title | Type | Status |
|--------|-------|------|--------|
| 132 | Медицина (поглиблено) | Domain | ❌ Not started |
| 133 | Технології та ШІ | Domain | ❌ Not started |
| 134 | Наука і дослідження | Domain | ❌ Not started |
| 135 | Мистецтво і література | Domain | ❌ Not started |
| 136 | Психологія та розум | Domain | ❌ Not started |
| 137 | Український менталітет | Culture | ❌ Not started |
| 138 | Сучасна діаспора | Culture | ❌ Not started |
| 139 | Релігія в Україні | Culture | ❌ Not started |
| 140 | Академічне письмо | Skills | ❌ Not started |
| 141 | Аналіз тексту | Skills | ❌ Not started |
| 142 | Capstone: Дослідження | Project | ❌ Not started |
| 143 | Capstone: Презентація | Project | ❌ Not started |
| 144 | B2 Підсумковий огляд | Review | ❌ Not started |
| 145 | B2 ФІНАЛЬНИЙ ІСПИТ | Exam | ❌ Not started |

## B1 Issues (15 modules need fixes)

### Issue #350: B1 Content Quality

**Word Count Issues (15 modules - need expansion):**
- M44: 1474/1500 (-26 words)
- M45: 1473/1500 (-27 words)
- M47: 1499/1500 (-1 word)
- M49: 1434/1500 (-66 words)
- M52: 1462/1500 (-38 words)
- M53: 1453/1500 (-47 words)
- M55: 1453/1500 (-47 words)
- M57: 1454/1500 (-46 words)
- M60: 1472/1500 (-28 words)
- M61: 1450/1500 (-50 words)
- M66: 1454/1500 (-46 words)
- M68: 1445/1500 (-55 words)
- M69: 1490/1500 (-10 words)
- M70: 1452/1500 (-48 words)
- M79: 1447/1500 (-53 words)

**All modules need minor content expansions (1-66 words each).**

### Issue #351: B1.7 Expansion ✅ COMPLETE

**Status:** ✅ Complete (2026-01-02)
- M81: Біг в Україні (1855 words, 97% immersion, 96% richness) ✅
- M82: Гори та трейлраннінг (1740 words, 97% immersion, 96% richness) ✅
- M83: Велосипед та водні види (1734 words, 97% immersion, 99% richness) ✅
- M84: Зимові види спорту (1651 words, 98% immersion, 96% richness) ✅
- Renumbering complete: M80-86 → M85-91 ✅
- Total B1 modules: 86 → 91 ✅

---

## Agent Assignments Available

**Priority 1 - Fix B2 failing modules (8 modules):**
- M116, M118-120, M123-124, M127-128 need content expansion
- All have activities/engagement/richness ✅ - just need more narrative (50-100 words each)

**Priority 2 - Fix B1 modules (15 modules):**
- M44-45, M47, M49, M52-53, M55, M57, M60-61, M66, M68-70, M79 need word count expansion
- Simple task: add 1-66 words to each module

**Priority 3 - Build B2 remaining modules:**
- M132-M145 (14 modules: 5 domain, 3 culture, 2 skills, 4 capstone)

## Model Assignment Matrix

| Task Type | Model | Reasoning | Examples |
|-----------|-------|-----------|----------|
| **Vocabulary enrichment** | Claude Sonnet / Gemini 3-flash | Structured, repetitive data transformation | B2 M11-131 enrichment |
| **Word count fixes** | Claude Sonnet / Gemini 3-flash | Simple content expansion | B1 M44-70, B2 M116-128 |
| **Pedagogy fixes** | Claude Sonnet / Gemini 3-flash | H1/H2 changes, callout additions | B1 M81-84 (old) pedagogy |
| **Module content creation** | Claude Opus / Gemini 3-flash | Complex cultural narratives, domain expertise | B1 M81-84 (testing flash), B2 M132-145 |
| **Coordination/audits** | Claude Sonnet | File operations, batch processing | This session |

**Key Insight:**
- **Sonnet/Gemini 3-flash:** 95% quality at 20% cost for structured work
- **Opus/Gemini 3-flash:** Required for creative content creation
- Gemini 3-flash > Gemini 2.5-pro in capability

**Experiment Results (B1 M81-84):**
- ✅ gemini-3-flash validated for B1 cultural content creation
- 4/4 modules created with 96-99% richness, 97-98% immersion
- Quality equals gemini-3-pro at fraction of cost
- Recommendation: Use gemini-3-flash for B1 word count fixes

## Communication Protocol

1. Agents comment on their assigned issues with progress
2. Coordinator (this session) reviews and updates this file
3. Cross-agent dependencies flagged in issue comments
