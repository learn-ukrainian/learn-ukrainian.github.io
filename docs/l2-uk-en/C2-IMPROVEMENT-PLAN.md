# C2 Improvement Plan

**Status:** Draft
**Created:** 2024-12-14
**Based on:** Claude + Gemini pedagogical assessments

---

## Current State

| Metric | Value |
|--------|-------|
| Planned Modules | 80 |
| Implemented | 0 (0%) |
| Missing | 80 (M01-M80) |
| Grade | A (A+ plan, F implementation) |

**Note:** C2 has the best-structured curriculum plan of any level, with explicit State Standard mapping, balanced phases, and a sophisticated professional skills approach.

---

## Issues Identified

### From Claude Assessment

1. **Zero Implementation** - 0 of 80 modules exist
2. **Partial Specifications** - C2.1 detailed; C2.2-C2.4 summary only
3. **Vocabulary Discrepancy** - Header vs cumulative inconsistency
4. **Capstone Scope** - Requirements exist but model answer needed
5. **Critical Dependencies** - B2 (0%) and C1 (1.7%) are blockers

### From Gemini Assessment

6. **Priority Order Clarified** - C2.1 → C2.4 (capstone) → C2.2 → C2.3
7. **Cumulative Vocabulary Discrepancy** - ~1,550 words gap from stated 12,550
8. **Immersion Strategic Use** - 2% English must be used strategically
9. **Capstone Timeline** - 6 modules may be insufficient for 10,000-word paper
10. **Creative Writing Density** - Only 2 modules (M31-32) for literary creation
11. **Activity Density Risk** - 16+ activities × 80 modules = quality risk

---

## Action Items

### 0. State Standard 2024 Compliance Verification

**Priority:** P0 (Critical)
**Effort:** Low
**Reference:** `docs/l2-uk-en/STATE-STANDARD-COMPLIANCE-ANALYSIS.md`
**GitHub Issue:** [#125](https://github.com/krisztiankoos/curricula-opus/issues/125)

The C2-CURRICULUM-PLAN.md has the best State Standard mapping of any level:

| State Standard Requirement | Plan Coverage | Status |
|---------------------------|---------------|--------|
| Native-like proficiency | Throughout | ✅ 98% immersion |
| All grammatical structures | All phases | ✅ Comprehensive |
| All 7 functional styles | C2.1 (M01-20) | ✅ Including religious & epistolary |
| Specialized domains | C2.3 (M41-60) | ✅ Professional meta-skills |
| Cultural mastery | C2.2 (M21-40) | ✅ Literary mastery |

**Action:**
- [ ] Verify plan covers all State Standard C2 grammar requirements
- [ ] Ensure 7 functional styles are explicitly taught
- [ ] Document alignment in curriculum plan header

**Note:** C2 has the best-structured plan. The only gap is implementation (0% of 80 modules).

---

### 1. Reconcile Vocabulary Targets

**Priority:** P0 (Critical)
**Effort:** Low
**GitHub Issue:** [#126](https://github.com/krisztiankoos/curricula-opus/issues/126)

**Discrepancies across curriculum:**
| Level | Plan Target | Stated Cumulative | Actual Sum |
|-------|-------------|-------------------|------------|
| A1 | ~750 | ~750 | ~750 |
| A2 | ~1,050 | ~1,800 | ? |
| B1 | ~1,500 | ~3,300 | ? |
| B2 | ~2,900 | ~6,200 | ? |
| C1 | ~2,800 | ~9,000 | ? |
| C2 | ~2,000 | ~12,550 | ~11,000 |

**Gap:** ~1,550 words between sum (~11,000) and stated cumulative (~12,550).

**Action:**
- [ ] Audit all level vocabulary targets
- [ ] Sum phase breakdowns for each level
- [ ] Identify where discrepancies originate
- [ ] Update all headers to match actual sums
- [ ] Ensure consistent progression across levels

---

### 2. Expand C2.2-C2.4 Specifications

**Priority:** P1 (High)
**Effort:** High

C2.1 (M01-20) has detailed module specifications. C2.2-C2.4 have only summary specs.

**Required for each module:**
- Full vocabulary list (25 words average)
- Grammar/skill focus
- Signature activities (3-4 per module)
- Engagement boxes
- Model answers for production tasks

**Action:**
- [ ] Expand C2.2 (M21-40) with detailed specs for 20 modules
- [ ] Expand C2.3 (M41-60) with detailed specs for 20 modules
- [ ] Expand C2.4 (M61-80) with detailed specs for 20 modules
- [ ] Ensure vocabulary lists sum to ~1,500 words for these phases

---

### 3. Expand Creative Writing Coverage

**Priority:** P1 (High)
**Effort:** Medium

Current: Only 2 modules (M31-32) for creative writing.
Problem: Learners choosing literary capstone need more preparation.

**Proposed expansion:**

| Current | Proposed |
|---------|----------|
| M31: Creative Writing: Poetry | M31: Poetry I - Forms & Techniques |
| M32: Creative Writing: Prose | M31b: Poetry II - Original Creation |
| — | M32: Prose I - Short Forms |
| — | M32b: Prose II - Longer Narratives |

**Alternative (without module count change):**
- Add creative writing exercises within C2.2 Practice modules (M37-38)
- Include poetry/prose creation in each literary theory module
- Add "mini-creation" activities throughout C2.2

**Action:**
- [ ] Decide: Expand module count or integrate within existing
- [ ] If expanding: Add M31b, M32b specifications
- [ ] If integrating: Add creative exercises to M37-38 Practice modules
- [ ] Ensure literary capstone has sufficient preparation

---

### 4. Define Capstone Timeline and Standards

**Priority:** P1 (High)
**Effort:** Medium

Current: 6 modules (M67-72) for capstone project.
Concern: 10,000-word research paper may need more support.

**Proposed capstone structure:**

```markdown
## Capstone Options and Standards

### Option 1: Research Paper (Дослідницька робота)
**Length:** 10,000-12,000 words
**Requirements:**
- Academic register throughout
- 15+ sources (Ukrainian-language preferred)
- ДСТУ citation format
- Original thesis/argument

**Timeline:**
| Module | Milestone | Deliverable |
|--------|-----------|-------------|
| M67 | Topic selection | Proposal (500 words) |
| M68 | Literature review | Annotated bibliography (20 sources) |
| M69 | First draft | Chapters 1-3 draft (5,000 words) |
| M70 | Full draft | Complete draft (10,000 words) |
| M71 | Revision | Final polished version |
| M72 | Defense | 20-minute presentation + Q&A |

### Option 2: Literary Work (Літературний твір)
**Length:** Poetry collection (20+ poems) OR Prose (15,000+ words)
**Requirements:**
- Consistent voice and theme
- Technical proficiency
- Original creative vision
- Editor's letter explaining choices

### Option 3: Translation Project (Перекладацький проєкт)
**Length:** 50+ pages of source text
**Requirements:**
- Source text approval
- Translator's preface
- Glossary of key terms
- Comparative analysis

### Option 4: Professional Portfolio (Професійне портфоліо)
**Contents:** 10+ diverse documents across 3+ styles
**Requirements:**
- Cover letter explaining selections
- Reflection on each piece
- Evidence of revision process
```

**Mini-Capstone Preparation:**
- Add "mini-project" in M56-57 (Professional Portfolio modules)
- 2,000-word practice paper in M37 (C2.2 Practice I)

**Action:**
- [ ] Expand M67-72 specifications with full timeline
- [ ] Define quality standards for each option
- [ ] Create model capstone for at least one option
- [ ] Add mini-project preparation in M56-57

---

### 5. Define Strategic English Use (2%)

**Priority:** P1 (High)
**Effort:** Low
**Status:** ✅ Implemented

At 98% immersion, only ~40 words of English per 2,000-word module.

**Strict 2% English Rule (Updated Dec 2025):**
| Use | Example |
|-----|---------|
| Translation discussion | "The English equivalent..." |
| Comparative linguistics | "Unlike English, Ukrainian..." |
| Metalinguistic terms | "This is called 'nominalization'" |
| Cross-cultural concepts | "What English speakers call..." |

**Inappropriate uses:**
- Explaining grammar rules
- Vocabulary definitions
- Instructions or explanations
- Cultural context

**Action:**
- [x] Document strategic English use guidelines
- [x] Apply to all C2 module creation
- [x] Ensure explanations are in Ukrainian with Ukrainian examples

---

### 6. Adjust Activity Density Strategy

**Priority:** P1 (High)
**Effort:** Low (planning change)

Current requirement: 16+ activities per module
Risk: 80 modules × 16 activities = 1,280+ activities (quality risk)

**Gemini's recommendation for C2:**
- 12 production activities (with Model Answers)
- 4 analytical/comprehension activities
- Quality over quantity

**Adjusted requirements by phase:**
| Phase | Activity Count | Focus |
|-------|---------------|-------|
| C2.1 Stylistic | 14+ | Style transformation, production |
| C2.2 Literary | 12+ | Analysis, creation |
| C2.3 Professional | 12+ | Document production, scenarios |
| C2.4 Capstone | 10+ | Project work, review |
| Checkpoints | 16+ | Comprehensive assessment |

**Model Answer requirement:**
- ALL production tasks MUST have Model Answers
- Literary creation: Show "gold standard" examples
- Style transformation: Show before/after pairs

**Action:**
- [ ] Update MODULE-RICHNESS-GUIDELINES-v2.md for C2 specifics
- [ ] Document activity count by phase
- [ ] Require Model Answers for all production tasks
- [ ] Emphasize quality over quantity

---

### 7. Complete Module Implementation (M01-M80)

**Priority:** P0 (Critical)
**Effort:** Very High (80 modules)
**GitHub Issue:** [#127](https://github.com/krisztiankoos/curricula-opus/issues/127)

This is the main work. All modules need creation from scratch.

**Gemini's priority order:**
| Priority | Phase | Modules | Rationale |
|----------|-------|---------|-----------|
| P0-a | C2.1 | M01-09 | Style foundation (9 modules) |
| P0-b | C2.4 | M67-72 | Capstone defines the goal |
| P0-c | C2.1 | M10-20 | Complete stylistic phase |
| P0-d | C2.2 | M21-32 | Literary mastery core |
| P0-e | C2.3 | M41-49 | Professional meta-skills |
| P0-f | Remaining | All others | Complete coverage |

**Per-module requirements:**
- 10-14 activities (varies by phase)
- 98% Ukrainian immersion
- 25 vocabulary words average
- Model answers for all production tasks
- Individual voice development

**Action:**
- [ ] Complete plan fixes (items 1-6) before starting
- [ ] Create M01-09 (style foundation) first
- [ ] Define capstone structure (M67-72) early
- [ ] Continue in phase order per Gemini's priorities

---

### 8. Resolve Dependency Chain

**Priority:** P0 (Critical - BLOCKER)
**Effort:** N/A (external dependency)

C2 cannot be tested until the entire dependency chain is complete:

```
C2 requires:
└── C1 completion (1.7%)
    └── B2 completion (0%)
        └── B1 completion (6%)
            └── A2 completion (10%)
                └── A1 completion (59%)
```

**Current bottlenecks:**
| Level | Status | Impact |
|-------|--------|--------|
| A1 | 59% | Can complete independently |
| A2 | 10% | Blocked by A1 completion preference |
| B1 | 6% | Blocked by A2 |
| B2 | 0% | **Critical - largest level** |
| C1 | 1.7% | Blocked by B2 |
| C2 | 0% | Blocked by C1 |

**Action:**
- [ ] Prioritize lower-level completion (A1 → A2 → B1 → B2)
- [ ] Create C2 modules in parallel (cannot test until chain complete)
- [ ] Document dependency in curriculum documentation

---

## Priority Matrix

| Priority | Items | Total Effort |
|----------|-------|--------------|
| **P0** | 1. Vocabulary, 7. Implementation, 8. Dependencies | Very High |
| **P1** | 2. Specs expansion, 3. Creative writing, 4. Capstone, 5. English use, 6. Activity density | High |
| **P2** | Future: Specialization tracks | Low |

---

## Implementation Phases

### Phase 1: Plan Fixes (Before Any Modules)
- [ ] Reconcile vocabulary targets across all levels
- [ ] Expand C2.2-C2.4 specifications
- [ ] Define creative writing coverage approach
- [ ] Define capstone timeline and standards
- [ ] Document strategic English use (2%)
- [ ] Update activity density guidelines

### Phase 2: Foundation Creation
- [ ] Create C2.1 M01-09 (style foundation)
- [ ] Define C2.4 M67-72 (capstone structure)
- [ ] Create model capstone project

### Phase 3: Core Content
- [ ] Complete C2.1 (M10-20)
- [ ] Create C2.2 (M21-40) — Literary mastery
- [ ] Create C2.3 (M41-60) — Professional skills

### Phase 4: Completion
- [ ] Create C2.4 (M61-66, M73-80)
- [ ] Run full audit on all modules
- [ ] Validate vocabulary totals
- [ ] Test immersion consistency

---

## Success Criteria

C2 achieves **A+ rating** when:

- [ ] Vocabulary targets reconciled across all levels
- [ ] All 80 modules implemented
- [ ] C2.2-C2.4 have detailed specifications
- [ ] Creative writing has sufficient coverage (4+ modules or integrated)
- [ ] Capstone fully specified with timeline and model
- [ ] Strategic English use documented and applied
- [ ] Activity counts appropriate per phase
- [ ] All production tasks have Model Answers
- [ ] All modules pass audit
- [ ] 98% immersion achieved throughout

---

## Dependencies

```
C2 depends on:
├── C1 completion (1.7% - CRITICAL)
│   └── B2 completion (0% - CRITICAL)
├── All 6 previous levels complete
├── ~9,000 cumulative vocabulary from C1
├── All 7 styles mastered at C1
└── Academic + literary analysis skills from C1

Nothing depends on C2:
└── C2 is the final level (mastery achieved)
```

---

## Notes

1. **Best-structured plan** - C2 curriculum plan is the most comprehensive
2. **Zero implementation** - Unlike C1 (which has 2 exemplary modules), C2 has nothing
3. **Dependency chain critical** - B2 at 0% blocks everything above it
4. **Specialization approach** - Meta-skills for ANY domain (excellent design decision)
5. **98% immersion** - Nearly full Ukrainian; 2% must be strategic
6. **7 functional styles** - Includes religious and epistolary (unique to C2)
7. **Capstone is substantial** - 10,000+ words or equivalent creative work
8. **Optional extension tracks** - Planned for future (Legal, Medical, IT, etc.)

---

## Implementation Strategy

### Component Chain

When adding a curriculum improvement, keep these components in sync:

| Component | Purpose | Location |
|-----------|---------|----------|
| **Curriculum Plan** | WHAT to teach | `docs/l2-uk-en/C2-CURRICULUM-PLAN.md` |
| **Module Creation Prompts** | HOW to write modules | `claude_extensions/commands/module-create.md`, `docs/l2-uk-en/module-prompt.md` |
| **Richness Guidelines** | QUALITY standards | `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` |
| **Audit Config** | THRESHOLDS (min vocab, immersion %) | `scripts/audit/config.py` |
| **Audit Checks** | VERIFY compliance | `scripts/audit/checks/*.py` |
| **Existing Modules** | FIX based on audit | `curriculum/l2-uk-en/c2/` |
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

**Issues for this level:** #125-#128

### Vocabulary Workflow (Phased)

**GitHub Issue:** [#128](https://github.com/krisztiankoos/curricula-opus/issues/128) (Finalize vocabulary)

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

**Critical:** At C2's 98% immersion, only ~40 words per module can be in English. All metalanguage must be thoroughly learned.

**Problem:** C2 assumes mastery of all grammatical/academic terminology from prior levels. Any gaps become critical blockers.

**Solution:** C2 must:
1. **Verify prerequisite metalanguage** - First module should confirm learner knows all grammatical terms
2. **Introduce C2-specific terminology** - 7 functional styles, literary criticism, translation theory
3. **Use 2% English strategically** - ONLY for concepts that have no Ukrainian equivalent

| Domain | C2-Specific Terms |
|--------|-------------------|
| 7 Styles | + релігійний, епістолярний (added to B2/C1's 5 styles) |
| Literary | інтертекстуальність, наратив, постмодернізм, дискурс |
| Translation | переклад, перекладач, вихідний текст, цільовий текст |
| Academic | дисертація, захист, рецензія, опонент, наукове дослідження |
| Professional | протокол, меморандум, договір, статут |

**Strategic English Use (2%):**
- ✅ Comparative linguistics: "Unlike English, Ukrainian..."
- ✅ Untranslatable concepts: "What English speakers call..."
- ❌ Grammar explanations (use Ukrainian)
- ❌ Vocabulary definitions (use Ukrainian)
- ❌ Activity instructions (use Ukrainian)

Without thorough metalanguage scaffolding from earlier levels, C2's 98% immersion is impossible.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Quality at scale | Batch creation (10 modules); review after each batch |
| Dependency chain | Create modules in parallel; cannot test until chain complete |
| Creative writing gap | Expand M31-32 or integrate throughout C2.2 |
| Capstone ambiguity | Define full specs with model before starting |
| Activity quantity vs quality | Reduce count; require Model Answers |
| Immersion challenge | Document strategic English use; review each module |

---

## Future: Specialization Tracks

After core C2 is complete, optional extension tracks can be developed:

| Track | Focus | Estimated Modules |
|-------|-------|-------------------|
| Правничий | Legal terminology, contracts, court | 20-30 |
| Медичний | Medical terminology, patient communication | 20-30 |
| Технічний/IT | Technical writing, documentation | 20-30 |
| Бізнес | Corporate communication, negotiations | 20-30 |
| Освітній | Academic Ukrainian, pedagogy | 20-30 |
| Дипломатичний | Protocol, international relations | 20-30 |
| Журналістський | Investigative journalism, media | 20-30 |

These will be separate documents (e.g., `C2-TRACK-LEGAL.md`) building on C2.3 foundation.
