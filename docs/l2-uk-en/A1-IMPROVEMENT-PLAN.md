# A1 Improvement Plan

**Status:** ✅ COMPLETE
**Created:** 2024-12-14
**Completed:** 2024-12
**Based on:** Claude + Gemini pedagogical assessments

---

## Current State

| Metric | Value |
|--------|-------|
| Planned Modules | 34 |
| Implemented | 34 (100%) ✅ |
| Missing | 0 |
| Grade | A+ |

---

## Issues Identified

### From Claude Assessment

1. **Implementation Gap** - A1.3 entirely missing (modules 21-34)
2. **No Production Activities** - All activities are recognition-based
3. **Heavy Case Frontloading** - Acc/Loc/Gen in rapid succession (M11-16)
4. **Checkpoint ≠ Assessment** - No rubrics, no pass/fail criteria
5. **Audio Placeholders Missing** - Pronunciation modules lack audio hooks

### From Gemini Assessment

6. **Checkpoint Module Thinness** - M10, M20, M34 have only 10 vocabulary words each
7. **IPA Inconsistency Risk** - M01 has IPA; verify M11-20 maintain standard

---

## Action Items

### 0. State Standard 2024 Compliance Gaps

**Priority:** P0 (Critical)
**Effort:** Low
**Reference:** `docs/l2-uk-en/STATE-STANDARD-COMPLIANCE-ANALYSIS.md`
**GitHub Issue:** [#104](https://github.com/krisztiankoos/learn-ukrainian/issues/104)

The Ukrainian State Standard 2024 (Каталог В) requires two elements currently underrepresented in A1:

| Gap | Requirement | Action |
|-----|-------------|--------|
| Vocative basics | Звертання в українській мові | Add vocative forms (мамо!, тату!, друже!) in M32 (Family) |
| Reflexive possessive | свій/своя/своє | Add explicit teaching in M14 (Possessives) or M32 (Family) |

**Vocative implementation:**
```markdown
## Vocative Case (Кличний відмінок)

> [!observe] Pattern Discovery
>
> When calling someone directly, Ukrainian changes the word ending:
> - мама → мамо! (Mom!)
> - тато → тату! (Dad!)
> - друг → друже! (Friend!)

| Nominative | Vocative | Use |
|------------|----------|-----|
| мама | мамо | calling mom |
| тато | тату | calling dad |
| Оксана | Оксано | calling Oksana |
| друг | друже | calling a friend |
```

**свій implementation:**
```markdown
## свій vs його/її

| Sentence | Meaning |
|----------|---------|
| Він любить **свою** маму | He loves **his own** mom |
| Він любить **його** маму | He loves **someone else's** mom |

> [!observe] Pattern
> When subject = possessor → use свій
> When subject ≠ possessor → use його/її/їхній
```

**Action:**
- [ ] Add vocative basics to M32 (My Family)
- [ ] Add свій introduction to M14 (Possessives)
- [ ] Add practice activities for both forms

---

### 1. Complete A1.3 Modules (21-34)

**Priority:** P0 (Critical)
**Effort:** High (14 modules)
**GitHub Issue:** [#105](https://github.com/krisztiankoos/learn-ukrainian/issues/105)

A1 cannot achieve CEFR can-do outcomes without past/future tense, time, adjectives, and the capstone.

**Modules to create:**
| Module | Topic | Grammar |
|--------|-------|---------|
| 21 | Yesterday - Past Tense | L-participle |
| 22 | Tomorrow - Future Tense | буду + infinitive |
| 23 | What Time Is It? | Time expressions, calendar |
| 24 | Can, Must, Want | Modal constructions |
| 25 | My Daily Routine | Reflexive verbs (-ся/-сь) |
| 26 | Describing Things | Adjective agreement |
| 27 | Colors & Clothing | Adjectives in context |
| 28 | Description (Adverbs) | Manner & frequency adverbs |
| 29 | Weather & Nature | Impersonal constructions |
| 30 | Prepositions III | Direction vs Location vs Origin |
| 31 | Body & Health | "Болить..." pattern |
| 32 | My Family | Genitive for relationships |
| 33 | Holidays & Traditions | Dates, greetings |
| 34 | Checkpoint: Final Review | A1 Mastery assessment |

**Action:**
- [ ] Create modules following curriculum plan specifications
- [ ] Apply transliteration rule: first occurrence only (A1.3)
- [ ] Ensure 8+ activities per module
- [ ] Include 2+ production activities per module (see item 2)

---

### 2. Add Production Activities

**Priority:** P1 (High)
**Effort:** Medium
**Status:** ✅ REVISED - Achieved through controlled production

**Original concern:** All activities were recognition-based.

**Resolution:** A1 now has appropriate "controlled production" activities:

| Type | Level | Description |
|------|-------|-------------|
| `unjumble` | A1 | Sentence construction from given words |
| `anagram` | A1 M01-10 | Word construction from letters (Cyrillic scaffolding) |
| `translate` | A2+ | Translation multiple choice |
| `error-correction` | A2+ | Find and fix grammatical errors |

**Why true micro-write is deferred:**
1. **Cyrillic keyboard barrier** - A1 learners are still learning to read; typing is separate skill
2. **Auto-grading complexity** - Free-text needs AI evaluation (not yet available)
3. **Pedagogical sequence** - Recognition before production is sound methodology

**Current production support:**
- Checkpoints include "Practice" sections with toggleable `[!solution]` blocks
- Learners are prompted to write, then can reveal model answers
- This is "self-assessed production" without requiring AI grading

**Future:** See [#174](https://github.com/krisztiankoos/learn-ukrainian/issues/174) for micro-write activity planning (B1+ with AI support)

---

### 3. Enrich Checkpoint Modules

**Priority:** P1 (High)
**Effort:** Medium
**GitHub Issue:** [#107](https://github.com/krisztiankoos/learn-ukrainian/issues/107)

Checkpoints (M10, M20, M34) feel thin with only 10 vocabulary words and lack assessment structure.

**Add to each checkpoint:**

```markdown
## Self-Assessment Rubric

Rate yourself 1-5 on each can-do statement:

### Listening/Reading
- [ ] I can recognize all 33 Cyrillic letters
- [ ] I can read simple sentences without transliteration
- [ ] I can understand familiar words about self and family

### Speaking/Writing
- [ ] I can introduce myself (name, nationality, profession)
- [ ] I can ask and answer simple questions
- [ ] I can order food and drinks

### Grammar
- [ ] I can identify noun gender by ending
- [ ] I can conjugate Class I and II verbs
- [ ] I can use accusative case for direct objects
```

**Production tasks for checkpoints:**
- M10: Self-introduction monologue (50-75 words)
- M20: Navigation dialogue (give directions to 3 places)
- M34: "My Typical Day" paragraph (100-150 words)

**Action:**
- [ ] Create CEFR-aligned can-do rubrics for M10, M20, M34
- [ ] Add production tasks (monologue, paragraph writing)
- [ ] Add comprehensive mixed quizzes covering all prior modules
- [ ] Consider adding 10-15 more review vocabulary words

---

### 4. Verify IPA Consistency (M01-M20)

**Priority:** P1 (High)
**Effort:** Low

M01 correctly includes IPA for all vocabulary. Verify all modules maintain this standard.

**Expected format:**
```markdown
| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| мама | /ˈmɑmɑ/ | mom | noun | f | - |
```

**Action:**
- [ ] Audit M01-M20 vocabulary tables for IPA column
- [ ] Fix any modules missing IPA
- [ ] Ensure new M21-M34 include IPA

**Verification script:**
```bash
for i in {1..20}; do
  f=$(ls curriculum/l2-uk-en/a1/*$i-*.md 2>/dev/null | head -1)
  if [ -f "$f" ]; then
    echo -n "Module $i: "
    grep -c "^|.*|.*\/.*\/.*|" "$f" || echo "0 IPA entries"
  fi
done
```

---

### 5. Add Audio Placeholders

**Priority:** P2 (Medium)
**Effort:** Low

Modules 01-02 focus on pronunciation but have no audio component.

**Placeholder format:**
```markdown
> [!audio] Pronunciation Guide
>
> Audio file: `audio/a1/m01-cyrillic-letters.mp3`
> Status: Placeholder - to be recorded
```

**Action:**
- [ ] Add audio placeholders to M01-M02 (alphabet pronunciation)
- [ ] Add vocabulary pronunciation placeholders to all modules
- [ ] Create `audio/` directory structure

---

### 6. Consider Case Pacing Adjustment

**Priority:** P3 (Low)
**Effort:** High (restructure)

Cases are introduced rapidly in M11-16:
- M11: Accusative (inanimate)
- M12: Accusative (animate)
- M13: Locative
- M14: Possessives (not a case, but dense)
- M15: City navigation (applies Locative)
- M16: Genitive

**Options:**
1. **Accept current pacing** - Cases are introduced over 6 modules, which is reasonable
2. **Add vocabulary breathers** - Insert vocab-only modules between cases
3. **Split some modules** - Break M11-12 or M13-16 further

**Recommendation:** Accept current pacing for now. The progression is logical and the curriculum plan was carefully designed. Revisit if learner feedback indicates overload.

**Action:**
- [ ] No immediate action - monitor for learner feedback
- [ ] Consider adding 1 vocabulary module if A1.3 feels heavy

---

### 7. External Resource Integration

**Priority:** P3 (Low)
**Effort:** Low

Add curated external resources (YouTube, podcasts, websites) for supplementary learning.

**Placeholder format:**
```markdown
> [!resources] Learn More
>
> - YouTube: [Channel Name - Relevant Video](URL)
> - Podcast: [Ukrainian Lessons Podcast - Episode X](URL)
> - Website: [ukrainianlessons.com - Topic](URL)
```

**Action:**
- [ ] Await resource list from user
- [ ] Map resources to appropriate A1 modules
- [ ] Add resource boxes to modules

---

## Priority Matrix

| Priority | Items | Total Effort |
|----------|-------|--------------|
| **P0** | 0. State Standard gaps (vocative, свій), 1. Complete A1.3 (14 modules) | High |
| **P1** | 2. Production activities, 3. Checkpoint enrichment, 4. IPA verification | Medium |
| **P2** | 5. Audio placeholders | Low |
| **P3** | 6. Case pacing review, 7. External resources | Low |

---

## Implementation Phases

### Phase 1: Foundation (P0)
- [ ] Create M21-M34 following curriculum plan
- [ ] Apply all quality standards (8+ activities, immersion %, engagement boxes)
- [ ] Include production activities from the start

### Phase 2: Quality (P1)
- [ ] Verify IPA in M01-M20
- [ ] Add production activities to M01-M20
- [ ] Enrich checkpoint modules M10, M20, M34

### Phase 3: Enhancement (P2)
- [ ] Add audio placeholders
- [ ] Run full audit on all 34 modules

### Phase 4: Polish (P3)
- [ ] Add external resources when available
- [ ] Review case pacing based on feedback

---

## Success Criteria

A1 achieves **A+ rating** when:

- [x] All 34 modules implemented ✅
- [x] Controlled production activities (unjumble, anagram) + self-assessed writing in checkpoints ✅
- [x] Checkpoints have skill-based structure with Self-Check and toggleable solutions ✅
- [x] IPA present in all vocabulary tables ✅
- [x] External resources from authentic YouTube/podcast sources ✅
- [x] All modules pass audit (immersion, activity count, word count) ✅

**Status: A1 COMPLETE** (December 2024)

---

## Notes

- A1 completed with all 34 modules passing audit, MDX validation, and HTML validation
- New checkpoint format with skill-based structure and self-assessment
- True micro-write (AI-graded) deferred to B1+ - see [#174](https://github.com/krisztiankoos/learn-ukrainian/issues/174)

---

## Implementation Strategy

### Component Chain

When adding a curriculum improvement, keep these components in sync:

| Component | Purpose | Location |
|-----------|---------|----------|
| **Curriculum Plan** | WHAT to teach | `docs/l2-uk-en/A1-CURRICULUM-PLAN.md` |
| **Module Creation Prompts** | HOW to write modules | `claude_extensions/commands/module-create.md`, `docs/l2-uk-en/module-prompt.md` |
| **Richness Guidelines** | QUALITY standards | `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` |
| **Audit Config** | THRESHOLDS (min vocab, immersion %) | `scripts/audit/config.py` |
| **Audit Checks** | VERIFY compliance | `scripts/audit/checks/*.py` |
| **Existing Modules** | FIX based on audit | `curriculum/l2-uk-en/a1/` |
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

**Issues for this level:** #104-#108

### Vocabulary Workflow (Phased)

**GitHub Issue:** [#108](https://github.com/krisztiankoos/learn-ukrainian/issues/108) (Finalize vocabulary)

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
- "Поставте дієслово у правильну форму" — but what is "дієслово"?
- "Оберіть правильний відмінок" — but what is "відмінок"?

**Solution:** Each level must introduce grammatical vocabulary as part of the immersion progression:

| Level | Linguistic Terms to Teach |
|-------|--------------------------|
| A1 | іменник (noun), дієслово (verb), прикметник (adjective), він/вона/воно (gender), однина/множина (singular/plural) |
| A2 | відмінок (case), час (tense), вид (aspect), доконаний/недоконаний (perfective/imperfective) |
| B1 | дієприкметник (participle), дієприслівник (gerund), пасивний (passive), умовний (conditional) |

**Implementation:**
- Add linguistic terms to vocabulary sections BEFORE they appear in instructions
- First occurrence: provide English equivalent in parentheses
- Subsequent occurrences: Ukrainian only (true immersion)

Without this scaffolding, high immersion becomes confusion rather than natural learning.
