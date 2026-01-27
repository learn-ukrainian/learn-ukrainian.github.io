# A2 Improvement Plan

**Status:** ✅ COMPLETE
**Created:** 2024-12-14
**Completed:** 2024-12
**Based on:** Claude + Gemini pedagogical assessments

---

## Current State

| Metric | Value |
|--------|-------|
| Planned Modules | 50 (restructured to 57) |
| Implemented | 57 (100%) ✅ |
| Missing | 0 |
| Grade | A+ |

**Note:** A2 was intentionally restructured from 50 to 57 modules. All modules pass structural and semantic audits (including AI-powered review-module).

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
**GitHub Issue:** [#109](https://github.com/krisztiankoos/learn-ukrainian/issues/109)

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
**Status:** ✅ COMPLETE
**GitHub Issue:** [#110](https://github.com/krisztiankoos/learn-ukrainian/issues/110)

The curriculum plan header stated 1,500 words but the summary showed 1,050. This was reconciled.

**Resolution:** ~1,250 words per level (~25 words × 50 modules base + checkpoint reviews)

**Action:**
- [x] Decide on vocabulary target → ~1,250 words
- [x] Update `A2-CURRICULUM-PLAN.md` header to match decision
- [x] Verify vocabulary lists in plan sum to target

---

### 2. Fix Immersion Progression

**Priority:** P0 (Critical)
**Effort:** Low
**Status:** ✅ COMPLETE

A2 starting immersion was lower than A1 ending immersion. This was fixed.

**Implemented progression:**

| Level Phase | Immersion Target |
|-------------|------------------|
| A1 end | 40% |
| A2 start | 45% |
| A2 mid | 55% |
| A2 end | 65% |

**Action:**
- [x] Update `A2-CURRICULUM-PLAN.md` immersion targets
- [x] Verify modules meet immersion targets
- [x] Apply corrected targets to all modules

---

### 3. Consider Word Formation Reordering

**Priority:** P1 (High)
**Effort:** Medium
**Status:** ✅ RESOLVED - Kept current order

Original concern: Word Formation after Complex Sentences.

**Decision:** Kept current order with restructured module distribution:
- M25-34: Complex Sentences (telling stories, clauses, reported speech)
- M35-43: Word Formation (prefixes, suffixes, root families)

The restructuring from 50 to 57 modules allowed better pacing without reordering.

**Action:**
- [x] Evaluate reordering impact → decided to keep order
- [x] Restructured module distribution for better pacing
- [x] Updated curriculum plan with 57-module structure

---

### 4. Consolidate Vocabulary Expansion Modules

**Priority:** P1 (High)
**Effort:** Medium
**Status:** ✅ COMPLETE

Original concern: 12 siloed vocabulary domain modules risking "word list fatigue."

**Resolution:** Vocabulary expansion restructured to 11 thematic modules (M44-54):
- M44: Food and Cooking
- M45: Home and Furniture
- M46: Nature and Weather
- M47: Emotions and Personality
- M48: Work and Professions
- M49: Technology and Media
- M50: Hobbies and Leisure
- M51: Education and Learning
- M52: Shopping and Services
- M53: Sports and Fitness
- M54: Health and Body

Each module integrates vocabulary with practical contexts and activities.

**Action:**
- [x] Restructured vocabulary modules with thematic integration
- [x] Added integration activities connecting domains
- [x] Updated curriculum plan with 57-module structure

---

### 5. Add Missing Checkpoints

**Priority:** P1 (High)
**Effort:** Medium
**Status:** ✅ COMPLETE

All checkpoints implemented with skill-based structure:

| Module | Checkpoint | Covers |
|--------|-----------|--------|
| M11 | Checkpoint: Cases | Dative, Instrumental, Prepositions (M01-10) |
| M24 | Checkpoint: Aspect & Comparison | Aspect, свій, Comparison (M12-23) |
| M34 | Checkpoint: Complex Ideas | Complex sentences, clauses (M25-33) |
| M43 | Checkpoint: Word Formation | Prefixes, suffixes, root families (M35-42) |
| M55 | Checkpoint: Vocabulary | All vocabulary domains (M44-54) |

Plus M56-57: Grammar Review and Final Review (A2 Capstone)

**Action:**
- [x] All checkpoints implemented with skill-based format
- [x] Self-Check sections with `[!solution]` blocks
- [x] External resources (YouTube, grammar guides)
- [x] Production tasks integrated

---

### 6. Enhance свій Coverage

**Priority:** P1 (High)
**Effort:** Low
**Status:** ✅ COMPLETE

The reflexive possessive свій has comprehensive contrastive teaching in M17.

**Implementation (M17: Possessive Свій vs Його):**
- Full contrastive section: свій vs його/її/їхній
- Decision algorithm: "Is possessor = subject?"
- Edge cases and common error patterns
- Match-up activity: "Свій vs Його"
- Practical examples in narratives

**Action:**
- [x] M17 dedicated to свій introduction
- [x] Contrastive section with clear examples
- [x] Activities testing свій vs його/її/їхній distinction
- [x] Common error patterns included

---

### 7. Complete Module Implementation (M06-M50)

**Priority:** P0 (Critical)
**Effort:** Very High (45 modules)
**Status:** ✅ COMPLETE (restructured to 57 modules)
**GitHub Issue:** [#111](https://github.com/krisztiankoos/learn-ukrainian/issues/111)

All modules implemented with restructured distribution:

| Phase | Modules | Content | Status |
|-------|---------|---------|--------|
| A2.1 | M01-M11 | Cases (Dative, Instrumental, All Cases) | ✅ |
| A2.2 | M12-M24 | Aspect, свій, Comparison | ✅ |
| A2.3 | M25-M34 | Complex Sentences, Clauses | ✅ |
| A2.4 | M35-M43 | Word Formation | ✅ |
| A2.5 | M44-M55 | Vocabulary Expansion | ✅ |
| A2.6 | M56-M57 | Grammar Review, Final Review | ✅ |

**Per-module requirements met:**
- 12+ activities (full A2 variety) ✅
- Appropriate immersion levels ✅
- IPA in vocabulary tables ✅
- Engagement boxes ✅
- Production activities (error-correction, translate, cloze) ✅

**Action:**
- [x] All 57 modules complete
- [x] All modules pass structural audit
- [x] All modules pass semantic audit (AI review-module)

---

### 8. Maintain Quality Standards

**Priority:** P1 (High)
**Effort:** Ongoing
**Status:** ✅ COMPLETE

All modules meet quality standards established by M01-M05.

**Quality checklist:**
- [x] 12+ activities per module
- [x] Full A2 activity variety (error-correction, cloze)
- [x] IPA in all vocabulary tables
- [x] Engagement boxes (cultural, pop culture, real-world)
- [x] Cultural integration (Ukrainian context)
- [x] Mini-dialogues for conversational practice
- [x] Reading passages with comprehension questions
- [x] Appropriate immersion levels

**Action:**
- [x] Quality maintained through structural audit
- [x] Semantic audit (AI review-module) ensures content quality
- [x] All modules verified before completion

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

- [x] Reconcile vocabulary target → ~1,250 words
- [x] Fix immersion progression in plan
- [x] Decide on word formation reordering → kept order, restructured modules

### Phase 2: Module Creation (P0 implementation)

- [x] Create M01-M11 (Cases + Checkpoint)
- [x] Create M12-M24 (Aspect, Comparison + Checkpoint)
- [x] Create M25-M34 (Complex Sentences + Checkpoint)
- [x] Create M35-M43 (Word Formation + Checkpoint)
- [x] Create M44-M57 (Vocabulary + Reviews)

### Phase 3: Quality Assurance (P1)

- [x] All checkpoints with skill-based format
- [x] свій contrastive section in M17
- [x] Vocabulary modules with thematic integration
- [x] All 57 modules pass audit

### Phase 4: Enhancement (P2)

- [x] External resources (YouTube, podcasts) in checkpoints
- [x] Audio from authentic YouTube sources

---

## Success Criteria

A2 achieves **A+ rating** when:

- [x] All modules implemented ✅ (restructured from 50 to 57)
- [x] Vocabulary target reconciled ✅ (~1,250 words per level)
- [x] Immersion progression maintained ✅
- [x] All checkpoints have skill-based structure with Self-Check and `[!solution]` blocks ✅ (M11, M24, M34, M43, M55)
- [x] свій has contrastive section with activities ✅ (M17: Possessive Свій vs Його)
- [x] IPA present in all vocabulary tables ✅
- [x] Each module has 12+ activities with full A2 variety ✅
- [x] Production activities (error-correction, translate, cloze) ✅ (56/57 modules)
- [x] All modules pass audit ✅ (structural + semantic AI review)

**Status: A2 COMPLETE** (December 2024)

---

## Notes

- A2 restructured from 50 to 57 modules for better pedagogical flow
- 5 checkpoints with skill-based format and external resources
- Semantic audits using AI (review-module) ensure content quality
- True micro-write (AI-graded) deferred to B1+ - see [#174](https://github.com/krisztiankoos/learn-ukrainian/issues/174)

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

**GitHub Issue:** [#112](https://github.com/krisztiankoos/learn-ukrainian/issues/112) (Finalize vocabulary)

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
├── A1 completion ✅ (provides foundation vocabulary and grammar)
├── Vocabulary reconciliation ✅ (~1,250 words target)
└── Plan fixes ✅ (restructured to 57 modules)

B1 depends on:
└── A2 completion ✅ (aspect mastery provided for B1)
```

**Status:** All dependencies satisfied. B1 can proceed.
