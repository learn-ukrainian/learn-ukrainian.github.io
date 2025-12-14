# B2 Improvement Plan

**Status:** Draft
**Created:** 2024-12-14
**Based on:** Claude + Gemini pedagogical assessments

---

## Current State

| Metric | Value |
|--------|-------|
| Planned Modules | 125-135 (discrepancy) |
| Implemented | 0 (0%) |
| Missing | ALL |
| Grade | B+ (A plan, F implementation) |

**Note:** B2 is the largest implementation task in the entire curriculum with zero existing content.

---

## Issues Identified

### From Claude Assessment

1. **Zero Implementation** - 0/135 modules exist
2. **Module Count Discrepancy** - Header says 135, notes say 125
3. **Phase Numbering Inconsistency** - B2.3 listed as M61-85 AND M71-95
4. **Vocabulary Target Discrepancy** - 3,375 vs 3,150 words
5. **Missing Intermediate Checkpoints** - Only M110 and M125 visible
6. **Synonym/History Module Overlap** - M61-66 conflict

### From Gemini Assessment

7. **History Phase Placement** - Proverb modules may reference untaught historical contexts
8. **Immersion Level Jump** - B1 70% → B2 80% may be too aggressive
9. **Activity Density Risk** - 14+ activities × 135 modules = quality risk
10. **Capstone Project Scope** - M121-122 specifications too vague
11. **Folk Culture Gap** - Moved to C1 but needed for B2 proverb context

---

## Action Items

### 0. State Standard 2024 Compliance Verification

**Priority:** P0 (Critical)
**Effort:** Low
**Reference:** `docs/l2-uk-en/STATE-STANDARD-COMPLIANCE-ANALYSIS.md`
**GitHub Issue:** [#117](https://github.com/krisztiankoos/curricula-opus/issues/117)

The B2-CURRICULUM-PLAN.md appears to cover State Standard requirements, but verification is needed:

| State Standard Requirement | Plan Coverage | Status |
|---------------------------|---------------|--------|
| Passive voice (all types) | M01-05 | ✅ Verify alignment |
| Aspect nuances | Throughout | ✅ Verify alignment |
| Participles (all types) | M11-15 | ✅ Verify alignment |
| Complex syntax | M16-20 | ✅ Verify alignment |
| Register awareness | M26-30 | ✅ Verify alignment |

**Action:**
- [ ] Read State Standard 2024 Каталог В for B2 level
- [ ] Verify each grammar requirement is covered in curriculum plan
- [ ] Add any missing elements to appropriate modules
- [ ] Document alignment in curriculum plan header

**Note:** Unlike A1/A2/B1, B2's main gap is implementation (0%), not plan coverage.

---

### 1. Resolve Module Count Discrepancy

**Priority:** P0 (Critical)
**Effort:** Low
**GitHub Issue:** [#118](https://github.com/krisztiankoos/curricula-opus/issues/118)
**Status:** ✅ RESOLVED (2024-12-14)

~~The plan has conflicting module counts that must be resolved before implementation.~~

**Resolution:** Standardized to **135 modules** (matching Phase Distribution table and Summary Table).

The detailed module specifications have been renumbered:
- B2.3 History: M61-85 → M71-95
- B2.4 Biographies: M86-110 → M96-120
- B2.5 Capstone: M111-125 → M121-135

**Action:**
- [x] Audit all phase ranges and sum module counts
- [x] Determine correct total: **135 modules**
- [x] Update header to match (already correct at 135)
- [x] Update Phase Distribution table (already correct)
- [x] Ensure no module number gaps or overlaps (fixed)

---

### 2. Fix Phase Numbering Conflicts

**Priority:** P0 (Critical)
**Effort:** Medium
**Status:** ✅ RESOLVED (2024-12-14)

~~Two numbering schemes exist that conflict:~~

**Resolution:** Standardized to 135-module structure matching the Summary Table:
- B2.1: M01-40 (Grammar & Register, including 1b)
- B2.2: M41-70 (Phraseology & Synonymy)
- B2.3: M71-95 (Ukrainian History)
- B2.4: M96-120 (Biographies)
- B2.5: M121-135 (Skills & Capstone)

**Action:**
- [x] Choose one numbering scheme (used Summary Table structure)
- [x] Update all phase headers to be consistent
- [x] Update module tables in B2.3, B2.4, B2.5
- [x] Update Progress Tracker
- [x] Update Mermaid diagram
- [x] Update CLAUDE.md (B2 = 135 modules)

---

### 3. Reconcile Vocabulary Target

**Priority:** P0 (Critical)
**Effort:** Low

**Discrepancies:**
| Source | B2 New Words | Cumulative |
|--------|--------------|------------|
| Header | ~3,375 | ~7,900+ |
| Summary | ~3,150 | ~6,450 |
| Phase sum | ~3,150 | — |

**Recommendation:** Use ~3,150 (matches phase breakdown). Update header.

**Action:**
- [ ] Sum vocabulary targets from all phases
- [ ] Update header with correct figure
- [ ] Update cumulative total
- [ ] Verify alignment with State Standard 2024

---

### 4. Add Intermediate Checkpoints

**Priority:** P1 (High)
**Effort:** Medium

Current visible checkpoints: M110 (B2.4), M125 (Final)

**Proposed checkpoint structure:**
| Module | Checkpoint | Covers |
|--------|-----------|--------|
| M30 | Grammar Checkpoint | Passive, participles, syntax (M01-29) |
| M40 | Grammar Completion Check | Numerals, word formation (M31-39) |
| M70 | Phraseology Checkpoint | Idioms, proverbs, synonyms (M41-69) |
| M85/95 | History Checkpoint | Ukrainian history (varies by numbering) |
| M110/120 | Biography Checkpoint | 24 biographical modules |
| M125/135 | B2 Final Exam | Full B2 assessment |

**Action:**
- [ ] Insert checkpoint specifications at M30, M40, M70
- [ ] Add checkpoint after history phase
- [ ] Include CEFR can-do rubrics
- [ ] Design comprehensive review activities

---

### 5. Implement Graduated Immersion

**Priority:** P1 (High)
**Effort:** Low

Current plan jumps from B1 (50-70%) to B2 (80%). This may be too aggressive.

**Proposed graduated immersion:**
| Phase | Content Type | Immersion |
|-------|-------------|-----------|
| B2.1a-b (M01-40) | Grammar (metalinguistic) | 70-75% |
| B2.2 (M41-70) | Phraseology | 75-80% |
| B2.3 (M71-85/95) | History (narrative) | 80-85% |
| B2.4 (M86-110/96-120) | Biographies (narrative) | 80-85% |
| B2.5 (M111-125/121-135) | Capstone (pre-C1) | 85-90% |

**Rationale:** Grammar requires more metalinguistic explanation (English). Narrative content (history, biographies) can sustain higher immersion.

**Action:**
- [ ] Update immersion targets in curriculum plan
- [ ] Document graduated progression
- [ ] Apply to module creation guidelines

---

### 6. Adjust Activity Density

**Priority:** P1 (High)
**Effort:** Low (planning change)

Current requirement: 14+ activities per module
Risk: 135 modules × 14 activities = 1,890 activities (quality risk)

**Recommendation:** Prioritize quality over quantity.

**Adjusted requirements:**
| Module Type | Activity Count | Rationale |
|-------------|---------------|-----------|
| Grammar (G) | 14+ | Complex, needs more practice |
| Vocabulary (V) | 12+ | Synonym/nuance focused |
| History (H) | 10-12 | Reading comprehension focused |
| Biography (B) | 10-12 | Narrative focused |
| Checkpoint | 15+ | Comprehensive review |

**Action:**
- [ ] Update MODULE-RICHNESS-GUIDELINES-v2.md for B2
- [ ] Document activity count by module type
- [ ] Ensure signature activities remain mandatory

---

### 7. Define Capstone Project Scope

**Priority:** P1 (High)
**Effort:** Medium

M121-122 specifications are too vague:
- "Capstone: Project — Research"
- "Capstone: Presentation — Defense"

**Proposed capstone structure:**

```markdown
## M121: Capstone Project - Research

**Topic Guidelines:**
Choose ONE:
1. Historical figure not covered in curriculum
2. Ukrainian cultural phenomenon (music, art, cuisine)
3. Comparative study (Ukrainian vs English linguistics)
4. Current events analysis (2014-present)

**Requirements:**
- 800-1000 words
- 5+ sources (Ukrainian preferred)
- Proper citations
- Use of B2 vocabulary and grammar

**Model Answer:** [Full example provided]

---

## M122: Capstone Presentation - Defense

**Format:**
- 5-7 minute recorded presentation (audio or video)
- Visual aids optional
- Q&A simulation (self-generated questions and answers)

**Rubric:**
| Criterion | Points |
|-----------|--------|
| Content accuracy | 25 |
| Grammar & vocabulary | 25 |
| Register appropriateness | 20 |
| Pronunciation & fluency | 15 |
| Structure & coherence | 15 |
```

**Action:**
- [ ] Expand M121-122 specifications with full details
- [ ] Create model capstone project
- [ ] Design assessment rubric
- [ ] Add topic suggestions by interest area

---

### 8. Add Folk Culture Preview Modules

**Priority:** P2 (Medium)
**Effort:** Medium

Folk Culture (25 modules) moved to C1, but B2 proverb/idiom modules need cultural context.

**Recommendation:** Add 2-3 "Folk Culture Preview" modules to B2.2 (Phraseology).

**Proposed modules:**
| Module | Title | Content |
|--------|-------|---------|
| M41 | Folk Culture Overview | Vyshyvanka, pysanka, kobzar tradition |
| M42 | Folk Songs & Rituals | Koliadky, vesnianka, wedding songs |
| M43 | Folk Beliefs & Symbols | Motanka dolls, rushnyky, kalyna |

**Rationale:** This provides cultural scaffolding for M44-70 (proverbs, idioms, synonyms).

**Action:**
- [ ] Insert 2-3 folk culture modules at start of B2.2
- [ ] Adjust subsequent module numbers
- [ ] Ensure proverb/idiom modules don't assume untaught context

---

### 9. Verify History Phase Independence

**Priority:** P2 (Medium)
**Effort:** Low

Some phraseology modules may reference historical contexts not yet taught.

**Example concern:**
- M44 (Wisdom proverbs) might reference Skovoroda (not taught until M99)
- M52 (Wolf idioms) might reference historical wolf symbolism

**Action:**
- [ ] Audit phraseology modules for historical dependencies
- [ ] Add brief contextual notes where needed
- [ ] Consider moving 1-2 history modules earlier if critical

---

### 10. Implement Module Creation (M01-M125/135)

**Priority:** P0 (Critical)
**Effort:** Very High (125-135 modules)
**GitHub Issue:** [#119](https://github.com/krisztiankoos/curricula-opus/issues/119)

This is the main work. All modules need creation from scratch.

**Phased approach:**
| Priority | Phase | Modules | Content |
|----------|-------|---------|---------|
| P0-a | B2.1a | M01-30 | Grammar & Register |
| P0-b | B2.1b | M31-40 | Numerals, Word Formation |
| P0-c | B2.2 | M41-70 | Phraseology & Synonymy |
| P0-d | B2.3 | M71-85/95 | Ukrainian History |
| P0-e | B2.4 | M86-110/96-120 | Biographies |
| P0-f | B2.5 | M111-125/121-135 | Skills & Capstone |

**Per-module requirements:**
- 10-14 activities (varies by type)
- 70-90% immersion (graduated)
- 25 vocabulary words average
- Signature activities as specified
- Model answers for writing tasks

**Action:**
- [ ] Complete plan fixes (items 1-3) before starting
- [ ] Create M01-10 as quality baseline
- [ ] Review and refine approach
- [ ] Continue in batches of 10-15 modules

---

## Priority Matrix

| Priority | Items | Total Effort |
|----------|-------|--------------|
| **P0** | 1. Module count, 2. Phase numbering, 3. Vocabulary, 10. Implementation | Very High |
| **P1** | 4. Checkpoints, 5. Immersion, 6. Activity density, 7. Capstone | Medium |
| **P2** | 8. Folk culture preview, 9. History independence | Low |

---

## Implementation Phases

### Phase 1: Plan Fixes (Before Any Modules)
- [ ] Resolve module count (125 vs 135)
- [ ] Fix phase numbering conflicts
- [ ] Reconcile vocabulary targets
- [ ] Add checkpoint specifications
- [ ] Define graduated immersion
- [ ] Document activity density by type
- [ ] Expand capstone scope

### Phase 2: Foundation (M01-40)
- [ ] Create Grammar & Register modules (M01-30)
- [ ] Create Grammar Completion modules (M31-40)
- [ ] Run audits on each batch
- [ ] Refine approach based on first 40 modules

### Phase 3: Content (M41-110/120)
- [ ] Create Phraseology modules with folk culture preview (M41-70)
- [ ] Create History modules (M71-85/95)
- [ ] Create Biography modules (M86-110/96-120)

### Phase 4: Capstone (M111-125/121-135)
- [ ] Create Skills modules (M111-120/121-132)
- [ ] Create Capstone modules with full specifications
- [ ] Create Final Exam with comprehensive rubric

### Phase 5: Quality Assurance
- [ ] Run full audit on all modules
- [ ] Verify checkpoint completeness
- [ ] Test immersion progression
- [ ] Validate vocabulary totals

---

## Success Criteria

B2 achieves **A+ rating** when:

- [ ] Module count resolved and consistent
- [ ] Phase numbering unified
- [ ] All 125/135 modules implemented
- [ ] Graduated immersion applied (70% → 90%)
- [ ] Intermediate checkpoints added
- [ ] Activity counts appropriate per module type
- [ ] Capstone fully specified with model answer
- [ ] Folk culture context provided for phraseology
- [ ] All modules pass audit

---

## Dependencies

```
B2 depends on:
├── B1 completion (aspect mastery, complex sentences)
├── Plan fixes (before module creation)
└── Folk culture preview (before proverb modules)

C1 depends on:
└── B2 completion (register mastery required for C1)
```

---

## Notes

1. **Largest task:** B2 has more modules than A1, A2, and B1 combined (125-135 vs 164)
2. **Zero baseline:** Unlike other levels, B2 has no existing content to build on
3. **Plan quality high:** The curriculum plan is comprehensive; focus is on implementation
4. **Decolonization:** History modules include myth-busting content (Pereiaslav, Holodomor)
5. **Biography balance:** 13 women, 11 men (intentional emphasis on overlooked women)

---

## Implementation Strategy

### Component Chain

When adding a curriculum improvement, keep these components in sync:

| Component | Purpose | Location |
|-----------|---------|----------|
| **Curriculum Plan** | WHAT to teach | `docs/l2-uk-en/B2-CURRICULUM-PLAN.md` |
| **Module Creation Prompts** | HOW to write modules | `claude_extensions/commands/module-create.md`, `docs/l2-uk-en/module-prompt.md` |
| **Richness Guidelines** | QUALITY standards | `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` |
| **Audit Config** | THRESHOLDS (min vocab, immersion %) | `scripts/audit/config.py` |
| **Audit Checks** | VERIFY compliance | `scripts/audit/checks/*.py` |
| **Existing Modules** | FIX based on audit | `curriculum/l2-uk-en/b2/` |
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

**Issues for this level:** #117-#120

### Vocabulary Workflow (Phased)

**GitHub Issue:** [#120](https://github.com/krisztiankoos/curricula-opus/issues/120) (Finalize vocabulary)

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

**Critical:** At B2's 70-90% immersion, learners encounter sophisticated Ukrainian metalanguage. All grammatical terminology must be explicitly taught BEFORE use.

**Problem:** Instructions and explanations use terms learners have never been taught:
- "Визначте стиль тексту" — but what is "стиль"?
- "Перефразуйте в пасивний стан" — but what is "перефразуйте"?
- "Синоніми та антоніми" — but what are these terms in Ukrainian?

**Solution:** B2 must consolidate and expand grammatical vocabulary:

| Domain | Terms to Teach |
|--------|----------------|
| Register/Style | стиль, регістр, офіційний, розмовний, науковий |
| Vocabulary | синонім, антонім, пароніми, омоніми, фразеологізм |
| Syntax | підрядне речення, головне речення, сполучник |
| Instructions | перефразуйте, замініть, визначте, порівняйте, проаналізуйте |

**Implementation:**
- Create "Grammatical Vocabulary Reference" section for B2
- Introduce terms in first module of each phase
- First occurrence: provide English equivalent in parentheses
- Build instruction vocabulary progressively (визначте before проаналізуйте)

Without this scaffolding, high immersion becomes confusion rather than natural learning.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Quality degradation at scale | Batch creation (10-15), review after each batch |
| Inconsistent numbering | Fix ALL plan issues before starting modules |
| Activity burnout | Reduce count for narrative modules (10-12) |
| Cultural gaps | Add folk culture preview modules |
| Capstone vagueness | Define full specs with model answer |
