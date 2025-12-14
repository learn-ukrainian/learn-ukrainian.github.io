# C1 Improvement Plan

**Status:** Draft
**Created:** 2024-12-14
**Based on:** Claude + Gemini pedagogical assessments

---

## Current State

| Metric | Value |
|--------|-------|
| Planned Modules | 115 |
| Implemented | 2 (1.7%) |
| Missing | 113 (M03-M115) |
| Grade | A- (A+ plan, F implementation) |

**Note:** The 2 implemented modules (M01-M02) are **exceptional quality** (~100KB each, 21-23 activities). They set the standard for C1 content.

---

## Issues Identified

### From Claude Assessment

1. **Massive Implementation Gap** - Only 2 of 115 modules exist (1.7%)
2. **Folk Culture Detail** - C1.4 (M56-80) has only summary specs
3. **Literature Specs** - C1.5-C1.6 have summary specs only
4. **Capstone Vagueness** - M111-112 need detailed requirements
5. **B2 Dependency** - C1 cannot proceed until B2 is complete (0%)

### From Gemini Assessment

6. **Vocabulary Discrepancy** - Header says ~2,900 words, summary shows ~2,800
7. **Immersion Jump** - 80% → 95% is largest jump between levels
8. **Literature Module Specificity** - Contemporary authors get less depth than classics
9. **Capstone Scope Undefined** - Length, topics, rubric not specified
10. **Folk Culture Positioning** - Could inform stylistics (archaic forms)
11. **Activity Density Risk** - 16+ activities × 115 modules = quality risk

---

## Action Items

### 0. State Standard 2024 Compliance Verification

**Priority:** P0 (Critical)
**Effort:** Low
**Reference:** `docs/l2-uk-en/STATE-STANDARD-COMPLIANCE-ANALYSIS.md`
**GitHub Issue:** [#121](https://github.com/krisztiankoos/curricula-opus/issues/121)

The C1-CURRICULUM-PLAN.md has comprehensive State Standard mapping. Verify coverage:

| State Standard Requirement | Plan Coverage | Status |
|---------------------------|---------------|--------|
| All 5 functional styles | C1.3 (M36-55) | ✅ Explicit coverage |
| Advanced syntax | C1.3 (M36-55) | ✅ Stylistics & Rhetoric |
| Professional language | C1.2 (M21-35) | ✅ Professional & Social |
| Regional/historical awareness | C1.4-C1.6 | ✅ Folk culture, dialects, Surzhyk |

**Action:**
- [ ] Verify M01-02 (existing modules) align with State Standard
- [ ] Ensure C1.3 Stylistics covers all required sentence constructions
- [ ] Document alignment in curriculum plan header

**Note:** C1's main gap is implementation (1.7%), not plan coverage. M01-02 are exceptional quality templates.

---

### 1. Reconcile Vocabulary Target

**Priority:** P0 (Critical)
**Effort:** Low
**GitHub Issue:** [#122](https://github.com/krisztiankoos/curricula-opus/issues/122)

**Discrepancies found:**
| Source | C1 New Words | Cumulative |
|--------|--------------|------------|
| Header (line 5-6) | ~2,900 | ~10,550+ |
| Summary (line 1700) | ~2,800 | ~9,000 |

**Recommendation:** Use ~2,800 as target (matches phase breakdown sum).

**Action:**
- [ ] Sum vocabulary targets from all 6 phases
- [ ] Update header with correct figure
- [ ] Reconcile cumulative total with earlier level totals
- [ ] Verify alignment with State Standard 2024

---

### 2. Implement Graduated Immersion

**Priority:** P1 (High)
**Effort:** Low

Current plan jumps from B2 (80%) to C1 (95%). This 15-point jump is the largest in the curriculum.

**Proposed graduated immersion:**
| Phase | Content Type | Immersion |
|-------|-------------|-----------|
| C1.1 (M01-20) | Academic (metalinguistic) | 85% |
| C1.2 (M21-35) | Professional/Social | 90% |
| C1.3 (M36-55) | Stylistics/Rhetoric | 90% |
| C1.4 (M56-80) | Folk Culture | 95% |
| C1.5 (M81-95) | Literature Classics | 95% |
| C1.6 (M96-115) | Literature Modern + Capstone | 95% |

**Rationale:** Academic content requires more metalinguistic explanation. Cultural/literary content can sustain higher immersion.

**Action:**
- [ ] Update immersion targets in curriculum plan
- [ ] Document graduated progression
- [ ] Apply to module creation guidelines

---

### 3. Expand Literature Module Specificity

**Priority:** P1 (High)
**Effort:** Medium

**Current imbalance:**
- Classics (3 Shevchenko modules): M83-85 with detailed specs
- Contemporary (single modules): M104 Андрухович, M105 Забужко, M106 Жадан

**Proposed expansion:**
| Current | Proposed |
|---------|----------|
| M104: Андрухович | M104: Андрухович: Життя та контекст |
| M105: Забужко | M105: Андрухович: Проза (Perverzion, Moscoviada) |
| M106: Жадан | M106: Забужко: Польові дослідження |
| — | M107: Жадан: Поезія |
| M107: Воєнна література | M108: Жадан: Проза (Ворошиловград, Інтернат) |
| — | M109: Воєнна література |

**Note:** This would require expanding C1.6 by 2 modules (117 total) or consolidating elsewhere.

**Alternative:** Add sub-sections within single modules for each contemporary author.

**Action:**
- [ ] Decide: Expand module count or add depth within existing modules
- [ ] Update C1.6 specifications accordingly
- [ ] Ensure contemporary authors get comparable treatment to classics

---

### 4. Define Capstone Project Scope

**Priority:** P1 (High)
**Effort:** Medium

M111-112 specifications are too vague.

**Proposed capstone structure:**

```markdown
## M111: Capstone - Research Paper (Дослідницька робота)

**Requirements:**
- 2,000-3,000 words in Ukrainian
- Academic register throughout
- Minimum 5 sources (Ukrainian-language preferred)
- Proper citation format (ДСТУ or APA)

**Topic Options:**
1. Literary analysis (author, period, or theme)
2. Cultural study (tradition, region, or practice)
3. Sociolinguistic research (dialects, Surzhyk, language policy)
4. Current affairs analysis (post-2014 Ukraine)

**Structure:**
- Вступ (Introduction with thesis)
- Огляд літератури (Literature review)
- Основна частина (Analysis/argument)
- Висновки (Conclusions)
- Література (References)

**Model Answer:** [Full 2,500-word example provided]

---

## M112: Capstone - Oral Defense (Захист)

**Format:**
- 10-15 minute presentation in Ukrainian
- Visual aids optional (slides in Ukrainian)
- 5-10 minute Q&A simulation

**Assessment Rubric:**
| Criterion | Points |
|-----------|--------|
| Content accuracy & depth | 25 |
| Academic register mastery | 25 |
| Argument structure & logic | 20 |
| Pronunciation & fluency | 15 |
| Response to questions | 15 |

**Model Defense:** [Audio/video example or transcript]
```

**Action:**
- [ ] Expand M111-112 specifications with full details
- [ ] Create model capstone project (research paper + defense)
- [ ] Design detailed assessment rubric
- [ ] Add topic suggestions by interest area

---

### 5. Add Intermediate Checkpoints

**Priority:** P1 (High)
**Effort:** Medium

Current checkpoints: M20, M35, M55, M80, M95, M115 (6 total)

This is adequate for 115 modules. Verify each checkpoint includes:

**Checkpoint requirements:**
| Component | Description |
|-----------|-------------|
| Self-Assessment | CEFR can-do checklist |
| Vocabulary Test | Cumulative phase vocabulary |
| Grammar Review | Phase grammar structures |
| Production Task | Essay or oral presentation |
| Rubric | Clear scoring criteria |

**Action:**
- [ ] Verify all 6 checkpoints have full specifications
- [ ] Add CEFR can-do rubrics to each
- [ ] Design production tasks appropriate to phase content
- [ ] Include model answers for writing tasks

---

### 6. Expand Folk Culture & Literature Specs

**Priority:** P1 (High)
**Effort:** High

C1.4 (Folk Culture) and C1.5-C1.6 (Literature) have only summary specifications.

**Required for each module:**
- Full vocabulary list (24 words average)
- Grammar focus (if applicable)
- Signature activities (3-4 per module)
- Engagement boxes
- Model answers for production tasks

**Action:**
- [ ] Expand C1.4 (M56-80) with detailed specs for 25 modules
- [ ] Expand C1.5 (M81-95) with detailed specs for 15 modules
- [ ] Expand C1.6 (M96-115) with detailed specs for 20 modules
- [ ] Ensure vocabulary lists sum to ~1,350 words for these phases

---

### 7. Consider Folk Culture Positioning

**Priority:** P2 (Medium)
**Effort:** Low (planning decision)

Folk Culture (C1.4) is positioned after Professional (C1.2) and Stylistics (C1.3).

**Trade-offs:**
| Current Position | Alternative |
|-----------------|-------------|
| **Pro:** Stylistics skills prepare for folk text analysis | **Pro:** Folk content informs archaic forms in Stylistics |
| **Con:** Archaic forms (M47-50) lack cultural context | **Con:** Would require renumbering |

**Gemini's suggestion:** Interleave folk music/beliefs with archaic forms modules.

**Recommendation:** Keep current positioning but add cross-references:
- In M47 (Archaic Verb Forms): Reference koliadky, dumy as sources
- In M49 (Church Slavonicisms): Reference religious ritual context
- In C1.4: Back-reference to stylistics concepts learned

**Action:**
- [ ] Decide: Keep current order or interleave
- [ ] If keeping: Add explicit cross-references
- [ ] If interleaving: Develop new phase structure

---

### 8. Adjust Activity Density Strategy

**Priority:** P1 (High)
**Effort:** Low (planning change)

Current requirement: 16+ activities per module
Risk: 115 modules × 16 activities = 1,840+ activities (quality risk)

**Adjusted requirements:**
| Module Type | Activity Count | Rationale |
|-------------|---------------|-----------|
| Academic (C1.1) | 16+ | Complex, needs more practice |
| Professional (C1.2) | 14+ | Scenario-based, fewer but deeper |
| Stylistics (C1.3) | 14+ | Analysis-heavy |
| Folk Culture (C1.4) | 12+ | Reading/comprehension focused |
| Literature (C1.5-C1.6) | 12+ | Text analysis, fewer drills |
| Checkpoints | 18+ | Comprehensive review |

**Additional requirements:**
- All writing tasks MUST have Model Answers
- Production tasks count as 2 activities (higher effort)
- Self-assessment rubrics included in checkpoints

**Action:**
- [ ] Update MODULE-RICHNESS-GUIDELINES-v2.md for C1 specifics
- [ ] Document activity count by module type
- [ ] Ensure signature activities remain mandatory
- [ ] Require Model Answers for all production tasks

---

### 9. Complete Module Implementation (M03-M115)

**Priority:** P0 (Critical)
**Effort:** Very High (113 modules)
**GitHub Issue:** [#123](https://github.com/krisztiankoos/curricula-opus/issues/123)

This is the main work. All modules need creation using M01-02 as quality baseline.

**Phased approach:**
| Priority | Phase | Modules | Content |
|----------|-------|---------|---------|
| P0-a | C1.1 | M03-20 | Academic Foundation (18 remaining) |
| P0-b | C1.3 | M36-55 | Stylistics & Rhetoric |
| P0-c | C1.5 | M81-95 | Literature - Classics |
| P0-d | C1.2 | M21-35 | Professional & Social |
| P0-e | C1.4 | M56-80 | Folk Culture & Arts |
| P0-f | C1.6 | M96-115 | Literature - Modern & Capstone |

**Per-module requirements:**
- 12-16 activities (varies by type)
- 85-95% immersion (graduated)
- 24 vocabulary words average
- Signature activities as specified
- Model answers for writing tasks
- TTT pedagogy (Test → Teach → Test)

**Action:**
- [ ] Complete plan fixes (items 1-4) before starting
- [ ] Create M03-10 as quality baseline continuation
- [ ] Review and refine approach
- [ ] Continue in batches of 10-15 modules

---

### 10. Resolve B2 Dependency

**Priority:** P0 (Critical - BLOCKER)
**Effort:** N/A (external dependency)

C1 cannot realistically proceed until B2 has significant content. Learners need:
- All 4 passive voice forms
- Register mastery (5 functional styles)
- Phraseology (proverbs, idioms)
- ~6,200 cumulative vocabulary

**Current B2 status:** 0% implemented

**Action:**
- [ ] Prioritize B2 implementation before C1 expansion
- [ ] Alternatively: Create C1 modules in parallel, accepting they cannot be tested until B2 exists
- [ ] Document dependency in curriculum documentation

---

## Priority Matrix

| Priority | Items | Total Effort |
|----------|-------|--------------|
| **P0** | 1. Vocabulary, 9. Implementation, 10. B2 dependency | Very High |
| **P1** | 2. Immersion, 3. Literature depth, 4. Capstone, 5. Checkpoints, 6. Specs expansion, 8. Activity density | High |
| **P2** | 7. Folk culture positioning | Low |

---

## Implementation Phases

### Phase 1: Plan Fixes (Before Any New Modules)
- [ ] Reconcile vocabulary target (~2,800)
- [ ] Define graduated immersion (85% → 95%)
- [ ] Expand literature module specificity
- [ ] Define capstone scope with rubrics
- [ ] Verify checkpoint specifications
- [ ] Update activity density guidelines

### Phase 2: Specification Expansion
- [ ] Expand C1.4 (M56-80) with detailed specs
- [ ] Expand C1.5 (M81-95) with detailed specs
- [ ] Expand C1.6 (M96-115) with detailed specs

### Phase 3: Module Creation (Priority Order)
- [ ] Complete C1.1 (M03-20) — Academic foundation
- [ ] Create C1.3 (M36-55) — Stylistics core
- [ ] Create C1.5 (M81-95) — Classic literature
- [ ] Create C1.2 (M21-35) — Professional/social
- [ ] Create C1.4 (M56-80) — Folk culture
- [ ] Create C1.6 (M96-115) — Modern literature & capstone

### Phase 4: Quality Assurance
- [ ] Run full audit on all modules
- [ ] Verify checkpoint completeness
- [ ] Test immersion progression
- [ ] Validate vocabulary totals

---

## Success Criteria

C1 achieves **A+ rating** when:

- [ ] Vocabulary target reconciled (~2,800 words)
- [ ] Graduated immersion implemented (85% → 95%)
- [ ] All 115 modules implemented
- [ ] Contemporary authors have comparable depth to classics
- [ ] Capstone fully specified with model answer and rubric
- [ ] All checkpoints have CEFR rubrics
- [ ] Folk culture cross-references in stylistics modules
- [ ] Activity counts appropriate per module type
- [ ] All modules pass audit
- [ ] All writing tasks have Model Answers

---

## Dependencies

```
C1 depends on:
├── B2 completion (CRITICAL - currently 0%)
│   ├── Register mastery (5 functional styles)
│   ├── All 4 passive voice forms
│   └── ~6,200 cumulative vocabulary
├── Plan fixes (items 1-4)
└── Specification expansion (C1.4-C1.6)

C2 depends on:
└── C1 completion (currently 1.7%)
```

---

## Notes

1. **M01-M02 are exemplary** - Use as template for all remaining modules
2. **B2 is the critical blocker** - 0% implementation prevents C1 testing
3. **Plan quality is excellent** - Focus is on implementation
4. **State Standard alignment** - Already documented in plan
5. **Sociolinguistic content unique to C1** - Dialects, Surzhyk, language policy
6. **Literature depth** - Covers 250+ years (Kotlyarevsky to war literature)
7. **Folk Culture moved from B2** - For vocabulary balance across levels

---

## Implementation Strategy

### Component Chain

When adding a curriculum improvement, keep these components in sync:

| Component | Purpose | Location |
|-----------|---------|----------|
| **Curriculum Plan** | WHAT to teach | `docs/l2-uk-en/C1-CURRICULUM-PLAN.md` |
| **Module Creation Prompts** | HOW to write modules | `claude_extensions/commands/module-create.md`, `docs/l2-uk-en/module-prompt.md` |
| **Richness Guidelines** | QUALITY standards | `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` |
| **Audit Config** | THRESHOLDS (min vocab, immersion %) | `scripts/audit/config.py` |
| **Audit Checks** | VERIFY compliance | `scripts/audit/checks/*.py` |
| **Existing Modules** | FIX based on audit | `curriculum/l2-uk-en/c1/` |
| **Vocabulary DB** | REBUILD after changes | `npm run vocab:rebuild` |
| **Generators** | If format changes | `scripts/generate-mdx.ts`, `scripts/generate-json.ts` |

**Update flow:**
```
Curriculum Plan updated
    ↓
Module Creation Prompts updated
    ↓
Richness Guidelines updated (if quality standards change)
    ↓
Audit Script updated (to detect compliance)
    ↓
Run audit → Fix existing modules
    ↓
Rebuild vocabulary DB → Regenerate output
```

### Two Types of Improvements

| Type | Approach | Examples |
|------|----------|----------|
| **Curriculum/Plan** | Manual/Strategic | Vocabulary targets, module specs, phase structure |
| **Module Fixes** | Audit-Driven | Activity counts, IPA, metalanguage, immersion % |

**For curriculum changes:** Review → Update plan → Update prompts → Apply to new modules

**For module fixes:** Add audit check → Run audit → Fix flagged modules → Re-run to verify

### GitHub Issue Sync

**When module structure changes (add/shift/reorder), update related GitHub issues:**

| Change | Action |
|--------|--------|
| Add modules | Update "Build modules XX-XX" issue title and description |
| Remove modules | Update issue title and description |
| Reorder phases | Update issue descriptions to reflect new module ranges |
| Split/merge modules | Update issue scope accordingly |

**Issues for this level:** #121-#124

### Vocabulary Workflow (Phased)

**GitHub Issue:** [#124](https://github.com/krisztiankoos/curricula-opus/issues/124) (Finalize vocabulary)

**Problem:** Expanding vocabulary at module level during creation leads to endless recursion.

**Solution:** Phased approach:

| Phase | Action | Vocabulary Handling |
|-------|--------|---------------------|
| **Planning** | Set targets in curriculum plan | Define minimum words per module carefully |
| **Creation** | Write modules following plan | Use EXACTLY the vocabulary from plan - NO improvisation |
| **Level Complete** | All modules exist | Run audit, finalize vocabulary in MD + DB |

```
Curriculum Plan (vocabulary targets set)
    ↓
Module Creation (use plan vocabulary EXACTLY)
    ↓
Level fully built (all modules exist)
    ↓
Vocabulary Audit (verify counts, find gaps)
    ↓
Finalize vocabulary (MD files + rebuild DB)
    ↓
Verify totals match plan
```

**Key rules:**
- During creation: NO vocabulary improvisation, follow plan exactly
- Vocabulary finalization happens ONCE per level, at the end
- Audit script drives the finalization, not manual review

---

## Technical Reminders

### Vocabulary Commands

```bash
npm run vocab:rebuild    # Rebuild master vocabulary database
python3 scripts/audit_module.py [path]  # Validate module vocabulary
```

### Immersion & Metalanguage Scaffolding

**Critical:** At C1's 85-95% immersion, nearly all instruction is in Ukrainian. Academic and literary metalanguage must be explicitly taught.

**Problem:** C1 content requires understanding of academic/literary terminology:
- "Проаналізуйте стилістичні засоби" — but what are "стилістичні засоби"?
- "Визначте функціональний стиль" — but what are the 5 стилі?
- "Риторичні прийоми" — but what is "риторика"?

**Solution:** C1 must teach comprehensive metalanguage vocabulary:

| Domain | Terms to Teach |
|--------|----------------|
| Functional Styles | офіційно-діловий, науковий, публіцистичний, художній, розмовний |
| Literary Analysis | метафора, епітет, персоніфікація, гіпербола, алюзія |
| Rhetoric | аргументація, тези, антитеза, риторичне питання |
| Academic | тема, ідея, структура, аналіз, висновок, джерело, цитата |
| Sociolinguistics | діалект, суржик, мовна політика, літературна мова |

**Implementation:**
- M01 (Bridge) should consolidate B2 metalanguage before C1 content
- Each phase should introduce domain-specific terminology first
- C1.1 Academic phase: teach academic instruction vocabulary
- C1.3 Stylistics phase: teach all 5 functional style names

**Verify M01-02:** Check that existing exemplary modules follow this scaffolding pattern.

Without this scaffolding, high immersion becomes confusion rather than natural learning.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Quality degradation at scale | Use M01-02 as template; batch creation (10-15); review after each batch |
| B2 dependency | Create C1 modules in parallel; cannot test until B2 exists |
| Literature imbalance | Expand contemporary author coverage in C1.6 |
| Capstone ambiguity | Define full specs with model answer before creating modules |
| Activity quantity vs quality | Adjust counts by module type; prioritize production tasks |
