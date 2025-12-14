# A2 Improvement Plan

**Status:** Draft
**Created:** 2024-12-14
**Based on:** Claude + Gemini pedagogical assessments

---

## Current State

| Metric | Value |
|--------|-------|
| Planned Modules | 50 |
| Implemented | 5 (10%) |
| Missing | 45 (M06-M50) |
| Grade | B+ (A- plan, F implementation) |

**Note:** The 5 implemented modules (M01-M05) are the highest quality modules in the entire curriculum.

---

## Issues Identified

### From Claude Assessment

1. **Massive Implementation Gap** - Only 5 of 50 modules exist (10%)
2. **Vocabulary Discrepancy** - Header says 1,500 words, summary shows 1,050
3. **Missing All Checkpoints** - M10, M20, M30, M40, M50 don't exist
4. **Plan Complexity** - 6 phases (A2.1-A2.6) may need simplification

### From Gemini Assessment

5. **Word Formation Placement** - Currently after Complex Sentences (M21-30), but Complex Sentences could benefit from word formation patterns
6. **Vocabulary Expansion Design** - 12 siloed domain modules (M37-48) risks "word list fatigue"
7. **Immersion Regression** - Plan shows 35% at A2 start (< A1 end 40%)
8. **Missing Checkpoints** - No checkpoint after Word Formation (M36) or Vocabulary Expansion (M48)
9. **свій Introduction** - Needs explicit contrastive section (він любить свою роботу vs його роботу)

---

## Action Items

### 0. State Standard 2024 Compliance Gaps

**Priority:** P0 (Critical)
**Effort:** Medium
**Reference:** `docs/l2-uk-en/STATE-STANDARD-COMPLIANCE-ANALYSIS.md`
**GitHub Issue:** [#109](https://github.com/krisztiankoos/curricula-opus/issues/109)

The Ukrainian State Standard 2024 (Каталог В) requires explicit teaching of these elements at A2:

| Gap | Requirement | Action |
|-----|-------------|--------|
| Explicit aspect pairs | Видова пара (писати-написати) | Add dedicated aspect pair vocabulary lists; drill common pairs |
| Verb prefixes for aspect | Префіксальне творення виду | Explicit teaching of how prefixes change aspect |
| свій contrastive | свій vs його/її/їхній distinction | Add explicit contrastive section with activities |
| Numerals with cases | Числівники + іменники в різних відмінках | Add practice with numeral-noun agreement patterns |

**Aspect pairs implementation:**
```markdown
## Видові пари — Aspect Pairs

> [!observe] Pattern Discovery
>
> Most Ukrainian verbs come in pairs:
> - **Imperfective** (процес) — ongoing, repeated
> - **Perfective** (результат) — completed, one-time

| Imperfective | Perfective | Meaning |
|--------------|------------|---------|
| писати | написати | to write |
| читати | прочитати | to read |
| робити | зробити | to do/make |
| їсти | з'їсти | to eat |
| пити | випити | to drink |

> [!note] Prefix Rule
> Adding a prefix often creates the perfective:
> - писати → **на**писати
> - читати → **про**читати
> - робити → **з**робити
```

**Numerals with cases implementation:**
```markdown
## Числівники з іменниками

| Number | + Nominative | Pattern |
|--------|--------------|---------|
| 1 | одна книга | singular nom |
| 2-4 | дві книги | nominative plural |
| 5-20 | п'ять книг | genitive plural |
| 21 | двадцять одна книга | like 1 |
| 22-24 | двадцять дві книги | like 2-4 |
```

**Action:**
- [ ] Add aspect pair vocabulary lists to A2.2 (M06-M10)
- [ ] Add verb prefix patterns section explaining aspect formation
- [ ] Enhance свій section (already in item 6) with contrastive activities
- [ ] Add numeral + case agreement practice to appropriate module

---

### 1. Reconcile Vocabulary Target

**Priority:** P0 (Critical)
**Effort:** Low
**GitHub Issue:** [#110](https://github.com/krisztiankoos/curricula-opus/issues/110)

The curriculum plan header states 1,500 words but the summary shows 1,050. This must be reconciled before module creation.

**Decision needed:**
- **Option A:** 1,050 words (aligns with State Standard 2024)
- **Option B:** 1,500 words (more ambitious, requires expanding vocabulary lists)

**Recommendation:** Use 1,050 as target (State Standard alignment), update header.

**Action:**
- [ ] Decide on vocabulary target
- [ ] Update `A2-CURRICULUM-PLAN.md` header to match decision
- [ ] Verify vocabulary lists in plan sum to target

---

### 2. Fix Immersion Progression

**Priority:** P0 (Critical)
**Effort:** Low

A2 starting immersion (35%) is lower than A1 ending immersion (40%). This breaks the progression.

**Expected progression:**
| Level Phase | Immersion Target |
|-------------|------------------|
| A1 end | 40% |
| A2 start | 45% |
| A2 mid | 55% |
| A2 end | 65% |

**Action:**
- [ ] Update `A2-CURRICULUM-PLAN.md` immersion targets
- [ ] Verify M01-M05 meet 45%+ immersion
- [ ] Apply corrected targets to new modules

---

### 3. Consider Word Formation Reordering

**Priority:** P1 (High)
**Effort:** Medium

Current order:
- M21-30: Complex Sentences
- M31-36: Word Formation

Gemini suggests Word Formation before Complex Sentences so learners can use derived words in complex sentences.

**Options:**
1. **Keep current order** - Complex sentences first, then word formation
2. **Swap order** - Word formation (M21-26), then complex sentences (M27-36)
3. **Interleave** - Mix word formation lessons throughout complex sentence phase

**Recommendation:** Option 2 (swap order) makes pedagogical sense. Word formation provides vocabulary building blocks for complex sentences.

**Action:**
- [ ] Evaluate reordering impact on module dependencies
- [ ] Update curriculum plan if reordering approved
- [ ] Renumber affected module specifications

---

### 4. Consolidate Vocabulary Expansion Modules

**Priority:** P1 (High)
**Effort:** Medium

Current design has 12 siloed vocabulary domain modules (M37-48):
- Health & Body
- Travel & Transport
- Shopping & Money
- Technology & Media
- etc.

This risks "word list fatigue" — learners memorizing disconnected lists.

**Recommendation:** Consolidate to 8-9 integrated modules by combining related domains:
- Health + Body → "Taking Care of Yourself"
- Travel + Transport → "Getting Around"
- Shopping + Money → "Making Purchases"
- Technology + Media → "Digital Life"

**Action:**
- [ ] Map current 12 modules to 8-9 consolidated modules
- [ ] Design integration activities connecting domains
- [ ] Update curriculum plan with new structure

---

### 5. Add Missing Checkpoints

**Priority:** P1 (High)
**Effort:** Medium

The plan has checkpoints at M10, M20, M30, M40, M50 but:
- None are implemented yet
- No checkpoint after Word Formation (M36)
- No checkpoint after Vocabulary Expansion (M48)

**Proposed checkpoint structure:**
| Module | Checkpoint | Covers |
|--------|-----------|--------|
| M10 | Checkpoint: Case Review | Cases & Verb Pairs (M01-09) |
| M20 | Checkpoint: Aspect & Time | Aspect, Comparison, Time (M11-19) |
| M30 | Checkpoint: Complex Sentences | Subordination & Clauses (M21-29) |
| M36 | Checkpoint: Word Formation | Prefixes, Suffixes, Compounds (M31-35) |
| M40 | Checkpoint: Vocabulary I | First half of domain vocabulary |
| M48 | Checkpoint: Vocabulary II | Second half of domain vocabulary |
| M50 | Checkpoint: A2 Capstone | Full A2 mastery assessment |

**Action:**
- [ ] Add M36 checkpoint specification to curriculum plan
- [ ] Add M48 checkpoint specification to curriculum plan
- [ ] Include CEFR can-do rubrics in all checkpoints
- [ ] Design production tasks for each checkpoint

---

### 6. Enhance свій Coverage

**Priority:** P1 (High)
**Effort:** Low

The reflexive possessive свій needs explicit contrastive teaching.

**Required content:**
```markdown
## свій vs його/її/їхній

| Sentence | Meaning |
|----------|---------|
| Він любить **свою** роботу | He loves **his own** work |
| Він любить **його** роботу | He loves **someone else's** work |

> [!observe] Pattern Discovery
>
> When the possessor = subject → use свій
> When the possessor ≠ subject → use його/її/їхній
```

**Action:**
- [ ] Identify which module introduces свій
- [ ] Add contrastive section with clear examples
- [ ] Add activities testing свій vs його/її/їхній distinction
- [ ] Include common error patterns

---

### 7. Complete Module Implementation (M06-M50)

**Priority:** P0 (Critical)
**Effort:** Very High (45 modules)
**GitHub Issue:** [#111](https://github.com/krisztiankoos/curricula-opus/issues/111)

This is the main work. Create remaining 45 modules following the curriculum plan.

**Phased approach:**
| Phase | Modules | Content | Priority |
|-------|---------|---------|----------|
| A2.2 | M06-M10 | Aspect & Comparison | P0-a |
| A2.3 | M11-M20 | Time & Clauses | P0-b |
| A2.4 | M21-M30 | Complex Sentences | P0-c |
| A2.5 | M31-M40 | Word Formation + Vocab I | P0-d |
| A2.6 | M41-M50 | Vocab II + Capstone | P0-e |

**Per-module requirements:**
- 12+ activities (full A2 variety)
- 45%+ immersion
- IPA in vocabulary tables
- 2+ engagement boxes
- 2+ production activities (translate, transform)

**Action:**
- [ ] Complete A2.2 (M06-M10) with aspect/comparison focus
- [ ] Complete A2.3 (M11-M20) with time expressions
- [ ] Complete A2.4 (M21-M30) with complex sentences
- [ ] Complete A2.5 (M31-M40) with word formation
- [ ] Complete A2.6 (M41-M50) with vocabulary expansion

---

### 8. Maintain Quality Standards

**Priority:** P1 (High)
**Effort:** Ongoing

M01-M05 set a high bar. New modules must match this quality.

**Quality checklist:**
- [ ] 12+ activities per module
- [ ] Full A2 activity variety (error-correction, cloze, dialogue-reorder)
- [ ] IPA in all vocabulary tables
- [ ] 2+ engagement boxes (🎬🌍💡🎮🎯)
- [ ] Cultural integration (Ukrainian holidays, traditions, media)
- [ ] Mini-dialogues for conversational practice
- [ ] Reading passages with comprehension questions
- [ ] 45%+ Ukrainian immersion

**Action:**
- [ ] Create A2 module template based on M01 quality
- [ ] Run audit on each new module before committing
- [ ] Review first module of each phase before batch creation

---

## Priority Matrix

| Priority | Items | Total Effort |
|----------|-------|--------------|
| **P0** | 0. State Standard gaps (aspect pairs, prefixes, numerals), 1. Vocabulary reconciliation, 2. Immersion fix, 7. Module implementation | Very High |
| **P1** | 3. Word formation reorder, 4. Vocab consolidation, 5. Checkpoints, 6. свій, 8. Quality | High |
| **P2** | Future: External resources, audio | Low |

---

## Implementation Phases

### Phase 1: Plan Fixes (P0 planning)
- [ ] Reconcile vocabulary target (1,050 vs 1,500)
- [ ] Fix immersion progression in plan
- [ ] Decide on word formation reordering

### Phase 2: Module Creation (P0 implementation)
- [ ] Create M06-M10 (Aspect & Comparison)
- [ ] Create M11-M20 (Time & Clauses)
- [ ] Create M21-M30 (Complex Sentences)
- [ ] Create M31-M40 (Word Formation + Vocab I)
- [ ] Create M41-M50 (Vocab II + Capstone)

### Phase 3: Quality Assurance (P1)
- [ ] Add checkpoints with rubrics
- [ ] Enhance свій contrastive section
- [ ] Consolidate vocabulary expansion modules
- [ ] Run full audit on all 50 modules

### Phase 4: Enhancement (P2)
- [ ] Add external resources
- [ ] Add audio placeholders

---

## Success Criteria

A2 achieves **A+ rating** when:

- [ ] All 50 modules implemented
- [ ] Vocabulary target reconciled and met
- [ ] Immersion progression maintained (45% → 65%)
- [ ] All checkpoints have CEFR rubrics
- [ ] свій has contrastive section with activities
- [ ] IPA present in all vocabulary tables
- [ ] Each module has 12+ activities with full variety
- [ ] Each module has 2+ production activities
- [ ] All modules pass audit

---

## Notes

- A2 has the highest quality implemented modules but lowest completion (10%)
- M01-M05 should serve as templates for remaining modules
- Word formation reordering decision should be made before creating M21+
- Vocabulary consolidation applies to M37-48 range

---

## Implementation Strategy

### Component Chain

When adding a curriculum improvement, keep these components in sync:

| Component | Purpose | Location |
|-----------|---------|----------|
| **Curriculum Plan** | WHAT to teach | `docs/l2-uk-en/A2-CURRICULUM-PLAN.md` |
| **Module Creation Prompts** | HOW to write modules | `claude_extensions/commands/module-create.md`, `docs/l2-uk-en/module-prompt.md` |
| **Richness Guidelines** | QUALITY standards | `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` |
| **Audit Config** | THRESHOLDS (min vocab, immersion %) | `scripts/audit/config.py` |
| **Audit Checks** | VERIFY compliance | `scripts/audit/checks/*.py` |
| **Existing Modules** | FIX based on audit | `curriculum/l2-uk-en/a2/` |
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

**Issues for this level:** #109-#112

### Vocabulary Workflow (Phased)

**GitHub Issue:** [#112](https://github.com/krisztiankoos/curricula-opus/issues/112) (Finalize vocabulary)

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

**Critical:** Linguistic/grammatical terminology must be explicitly taught BEFORE using it in Ukrainian explanations.

**Problem:** At higher immersion, learners encounter Ukrainian metalanguage (grammar terms) without explanation:
- "Оберіть правильний вид дієслова" — but what is "вид"?
- "Поставте у давальний відмінок" — but what is "давальний відмінок"?

**Solution:** A2 must explicitly teach these grammatical terms as vocabulary:

| Term | Ukrainian | When to Introduce |
|------|-----------|-------------------|
| aspect | вид | M06 (Aspect introduction) |
| perfective | доконаний вид | M06 |
| imperfective | недоконаний вид | M06 |
| case names | називний, знахідний, родовий, давальний, орудний, місцевий, кличний | When each case is used |
| comparison | вищий/найвищий ступінь | Comparison module |
| tense | час (теперішній, минулий, майбутній) | Tense modules |

**Implementation:**
- Add grammatical terms to vocabulary sections BEFORE they appear in Ukrainian instructions
- First occurrence: provide English equivalent in parentheses
- Subsequent occurrences: Ukrainian only (true immersion)

Without this scaffolding, high immersion becomes confusion rather than natural learning.

---

## Dependencies

```
A2 depends on:
├── A1 completion (provides foundation vocabulary and grammar)
├── Vocabulary reconciliation (before module creation)
└── Plan fixes (before M21+ creation)

B1 depends on:
└── A2 completion (aspect mastery required for B1)
```
