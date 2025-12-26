# Review Content Quality

Evaluate module content for educational quality, coherence, and pedagogical soundness.

## Usage

```
/review-content [LEVEL]                    # Review all modules in level
/review-content [LEVEL] [MODULE_NUM]       # Review single module
/review-content [LEVEL] [START-END]        # Review range of modules
```

## Arguments

- `$ARGUMENTS` - One of:
  - `a1` - Review all A1 modules (1-34)
  - `a1 15` - Review module 15 only
  - `a1 10-20` - Review modules 10 through 20
  - `b2 1-10` - Review B2 modules 1 through 10

## Instructions

Parse arguments: $ARGUMENTS

**Step 1: Determine Scope**
- If only LEVEL provided: Review ALL modules in that level
- If LEVEL + NUMBER: Review single module
- If LEVEL + RANGE (e.g., "10-20"): Review that range
- Find all matching files in `curriculum/l2-uk-en/{level}/`

**Step 2: For Each Module**

### Extract Content
1. Read the module file
2. Extract lesson content (everything BEFORE `## Activities`)
   - Include: Summary, all instructional sections, examples, engagement boxes
   - Exclude: Frontmatter, Activities, Vocabulary, Self-Assessment
3. Extract metadata (title, level, module number, topic)

### Evaluate Quality

**Step 0: Template Compliance Check**

Before scoring, verify the module follows the appropriate template:

**Template Selection by Level and Type:**
- **B1 M01-05 (Metalanguage):** `docs/l2-uk-en/templates/b1-metalanguage-module-template.md`
- **B1 M06-51 (Grammar):** `docs/l2-uk-en/templates/b1-grammar-module-template.md`
- **B1 Checkpoints (M15, M25, M34, M41, M51 — grammar phases only):** `docs/l2-uk-en/templates/b1-checkpoint-module-template.md`
- **B1 M52-71 (Vocabulary):** `docs/l2-uk-en/templates/b1-vocab-module-template.md`
- **B1 M72-81 (Cultural):** `docs/l2-uk-en/templates/b1-cultural-module-template.md`
- **B1 M82-86 (Integration):** `docs/l2-uk-en/templates/b1-integration-module-template.md`
- **B2:** `docs/l2-uk-en/templates/b2-module-template.md`
- **C1:** `docs/l2-uk-en/templates/c1-module-template.md`
- **C2:** `docs/l2-uk-en/templates/c2-module-template.md`
- **LIT:** `docs/l2-uk-en/templates/lit-module-template.md`

**Use Module Architect Skills for Focus-Area Review:**

| Module Type | Skill | Review Focus |
|-------------|-------|--------------|
| Grammar (B1-B2) | `grammar-module-architect` | TTT pedagogy, aspect/motion verb teaching |
| Vocabulary (B1) | `vocab-module-architect` | Collocations, synonymy, register |
| Cultural (B1-C1) | `cultural-module-architect` | Authentic materials, regional balance |
| History/Biography (B2-C1) | `history-module-architect` | Decolonization, primary sources |
| Integration (B1-B2) | `integration-module-architect` | Skill coverage, no new content |
| Checkpoint (All) | `checkpoint` | All skill groups tested, 16+ activities |
| Literature (LIT) | `literature-module-architect` | 100% immersion, essays not drills |

**Also use `grammar-check` skill** to verify Ukrainian grammar complies with Ukrainian State Standard 2024.

**Verify:**
- [ ] Module structure matches template sections
- [ ] Word count meets template minimum (core prose only, excludes vocabulary/activities/tables)
- [ ] Activity count and types match template requirements
- [ ] Vocabulary count meets template specification
- [ ] Pedagogy (PPP/TTT/TBL/CBI) matches template
- [ ] Focus-area requirements from architect skill met

**If template compliance fails, flag as ❌ REWRITE regardless of other scores.**

Score each criterion 1-5:

**1. Coherence**
- Logical organization and flow
- Clear transitions between sections
- Progressive difficulty (simple → complex)
- Consistent terminology

**2. Relevance**
- Content matches module title
- Examples relate to topic
- Grammar focus appropriate for level
- Vocabulary used matches topic

**3. Educational Value**
- Clear, sufficient explanations
- Varied, meaningful examples
- Inductive discovery patterns (observe-first)
- Follows stated pedagogy (PPP/TBL)
- Engagement boxes add value (not filler)

**4. Language Quality**
- Clear, professional writing
- No excessive repetition (same structure ≥5 times = flag)
- Grammatically correct Ukrainian
- Grammatically correct English explanations
- Consistent terminology
- **No Russisms/Surzhik:** Strictly standard Ukrainian (e.g., use 'так' not 'да', 'будь ласка' not 'пожалуйста', 'звичайно' not 'канешно'). Flag any non-standard usage.

**5. Pedagogical Correctness**
- **Sequence:** Does it teach A before B? (e.g., specific letters before reading words)
- **Scaffolding:** clear step-by-step instructions?
- **Cognitive Load:** Is it too much at once?
- **Accuracy:** Are grammar rules explained correctly?

**6. Natural Immersion (Mixed Language Check)**
- **Natural Flow:** Mixing must feel intentional (e.g., "In Ukrainian, we say **так** for yes"), NOT forced.
- **Syntactic Integrity:** Do NOT break English syntax just to insert a Ukrainian word (e.g., "The **хлопець** goes to the **школа**" -> BAD).
- **No "Denglish":** Sentences should generally be fully English (explanation) or fully Ukrainian (example), with specific exceptions for target vocabulary insertion in clear contexts.
- **Contextual Clarity:** Does the mix help or confuse?
- **Exception:** Checkpoint modules (assessments) are exempt from strict immersion flow checks.

**7. Word Salad Check**
Flag if ANY true:
- Same sentence pattern repeated 5+ times
- Generic filler without substance
- Contradictory explanations
- Examples unrelated to explanations
- Clear auto-generation artifacts

**8. Activity Quality** (Critical Check)

Review ALL activities in the module for:

**8a. Structural Integrity**
- No duplicate items (same question appears twice)
- No mixed activity types (e.g., `[!error]` syntax inside a `fill-in` activity)
- Correct callout format for activity type (see `docs/ACTIVITY-MARKDOWN-REFERENCE.md`)
- Item count matches level requirements

**8b. Answer Validity**
- **Single-answer activities:** Only ONE correct answer exists linguistically
  - Flag: "читати → прочитати" when "почитати" is also valid perfective
  - Flag: Fill-in where multiple grammatical options work
- **Multi-answer activities (`select`):** All valid answers are included
- **Error-correction:** The "error" is genuinely wrong, not just stylistic

**8c. Linguistic Accuracy**
- Ukrainian spelling is correct
- Grammar forms are correct (case endings, verb conjugations)
- Distractors are plausible but genuinely wrong (not trick questions)
- No Russisms in options or answers

**8d. Pedagogical Alignment**
- Activity tests what was TAUGHT in this module (not future content)
- Difficulty matches level (A1 activities shouldn't require case knowledge untaught)
- Activity type suits the learning goal:
  - Grammar → fill-in, error-correction, unjumble
  - Vocabulary → match-up, quiz, translate
  - Comprehension → true-false, select, cloze
- Clear, unambiguous instructions

**8e. External Resources**
- YouTube videos are relevant to module topic
- URLs are valid and accessible
- Resources match level (A1 shouldn't link C1 content)
- No duplicate resources across modules without reason
- Blog/article links are from reputable Ukrainian learning sources

**Activity Red Flags (Auto-fail):**
- ❌ **Spoiler Hints:** The hint gives away the answer (e.g., `Answer: cat`, `Hint: It is a c_t`).
- ❌ **Nonsense Options:** Distractors are illogical or obviously wrong without linguistic knowledge (e.g., `Select: Apple`, Options: `Apple`, `Car`, `Moon`, `Sock` - too easy).
- ❌ Multiple valid answers but only one accepted
- ❌ Wrong activity type syntax mixed in
- ❌ Grammatically incorrect "correct" answer
- ❌ Testing untaught material
- ❌ Duplicate items in same activity
- ❌ Broken/unrelated external resources

**9. Red Flags (Auto-fail)**
Flag if:
- **Forced Mixing:** "I want to **їсти** the **яблуко**." (Syntactic breakage)
- **Undefined Terms:** Using concepts not yet taught.
- **False Friends:** Using high-level grammar (cases) in A1 without explanation.
- **Russianisms/Surzhik:** Any detection of mixed Ukrainian-Russian forms (unless explicitly teaching *about* Surzhik).

**10. Content Richness Quality (B1+ Critical)**

This is not about counts. This is about whether the content is ALIVE or DEAD.

**10a. Engagement Quality**

❌ **DRY (robot wrote this):**
```markdown
Доконаний вид показує завершену дію.
Недоконаний вид показує незавершену дію.
Дивіться таблицю нижче.
```

✅ **RICH (learner will remember this):**
```markdown
Уявіть: ви читаєте книгу весь вечір — це процес, недоконаний вид.
Але ось ви закрили книгу — готово! Результат. Доконаний вид.

Це як різниця між «я йшов додому» (може, ще йду) і «я прийшов» (точка, фініш).

💡 **Чому це важливо?**
Українці чують цю різницю одразу. Неправильний вид —
і речення звучить... дивно. Як фальшива нота в пісні.
```

**10b. Variety Check**

Count unique sentence starters in each section. If >50% of sentences start the same way, flag as DRY.

❌ DRY pattern:
```markdown
Доконаний вид означає...
Доконаний вид використовується...
Доконаний вид показує...
Доконаний вид має...
```

✅ RICH pattern:
```markdown
Коли дія завершена — це доконаний вид.
Українці кажуть «я прочитав книгу», бо книга закінчена.
А якщо ще читаю? Тоді «читаю» — без результату.
Порівняйте: «він писав лист» vs «він написав лист».
```

**10c. Emotional Hooks**

Each major section needs at least one of:
- Metaphor or analogy (як фальшива нота, як різниця між X і Y)
- Real-world scenario (уявіть: ви на співбесіді...)
- Cultural connection (українці кажуть так, бо...)
- Surprise or contrast (але тут є сюрприз!)
- Question to reader (а що якщо...? чому так?)

❌ No hooks = textbook voice = learner falls asleep
✅ Has hooks = conversation voice = learner stays engaged

**10d. Cultural Depth (B1+)**

Each module should include:
- [ ] At least 1 named Ukrainian place (Львів, Карпати, Дніпро)
- [ ] At least 1 cultural reference (traditional, historical, or contemporary)
- [ ] Real-world context showing WHY this grammar/vocab matters

❌ Generic: "Людина купує хліб у магазині."
✅ Specific: "Оксана купує паляницю на Бесарабському ринку в Києві."

**10e. Proverbs & Idioms (B1+ Grammar Modules)**

Each grammar module should include 1-2 proverbs or idioms that:
- Naturally demonstrate the grammar point
- Are woven into content, not just listed
- Have cultural context explained

Example for aspect:
```markdown
Українці кажуть: «Не кажи гоп, поки не перескочиш».
Зверніть увагу: **перескочиш** — доконаний вид.
Чому? Бо йдеться про результат: перестрибнув чи ні.
```

**10f. Richness Score Calculation**

For each section, score:

| Criterion | 0 | 1 | 2 |
|-----------|---|---|---|
| Engagement | Textbook voice | Some personality | Conversational, memorable |
| Variety | Repetitive starters | Mixed | Varied, rhythmic |
| Hooks | None | 1-2 | 3+ per section |
| Cultural depth | Generic examples | Some specifics | Rich, placed content |
| Proverbs/idioms | None | 1 (forced) | 1-2 (natural) |

**Total 0-4:** ❌ REWRITE section
**Total 5-7:** ⚠️ ENRICH section
**Total 8-10:** ✅ PASS

**10g. Dryness Flags**

Flag content as DRY if ANY of these are true:

| Flag | Pattern | Excluded Module Types |
|------|---------|----------------------|
| TEXTBOOK_VOICE | No questions, metaphors, or emotional hooks in 300+ words | — |
| REPETITIVE | Same sentence structure >5 times in section | — |
| GENERIC_EXAMPLES | No named people, places, or specific scenarios | — |
| LIST_DUMP | Explanation is just a list without narrative flow | — |
| NO_CULTURAL_ANCHOR | Grammar taught without Ukrainian cultural context | — |
| ENGAGEMENT_BOX_FILLER | 💡 boxes just restate what was already said | — |
| WALL_OF_TEXT | >500 words without engagement box, example block, or dialogue | History, Biography, Literature modules |

**If 2+ dryness flags: Section needs REWRITE, not just fix.**

**Note:** A1/A2 modules focus on scaffolding (Cyrillic, basic grammar). Richness scoring applies primarily to B1+ where full immersion enables engaging content.

**Step 3: Generate Summary Report**

For each module, output:

```
## Module {num}: {title}

**Template:** {template_name} | **Compliance:** ✅ PASS / ❌ FAIL
**Scores:** Coherence {X}/5 | Relevance {X}/5 | Educational {X}/5 | Language {X}/5 | Pedagogy {X}/5 | Immersion {X}/5 | Activities {X}/5 | Richness {X}/5 | **Overall {X}/5**
**Status:** ✅ PASS / ⚠️ NEEDS WORK / ❌ REWRITE

{If not PASS, list 2-3 main issues}
```

**Step 4: Apply Safe Fixes**

For each module with action items, categorize fixes:

**Safe Fixes (Auto-apply):**
- Remove leftover editing notes/meta-commentary
- Fix typos and repetition errors
- Delete redundant paragraphs (exact duplicates)
- Remove factually incorrect statements
- Clean up formatting artifacts

**Risky Fixes (Report only):**
- Structural changes
- Rewriting sections for clarity
- Changing word count significantly
- Subjective improvements

For safe fixes:
1. Apply the fix to the module file
2. Run `python3 scripts/audit_module.py {file_path}` to verify still passes
3. If audit fails, revert the fix
4. Mark fix status in review: ✅ FIXED or ❌ SKIPPED

**Step 5: Save Review Files**

For each module, save detailed review to:
`curriculum/l2-uk-en/{level}/review/{module_number}-{slug}-review.md`

Example: `curriculum/l2-uk-en/a1/review/03-the-gender-code-review.md`

**Step 6: Generate Final Summary**

After reviewing all modules in scope:

```
# Content Quality Summary

**Level:** {level}
**Modules Reviewed:** {count}
**Date:** {today}

---

## Overview

| Status | Count | Modules |
|--------|-------|---------|
| ✅ PASS (≥4/5) | {count} | {list} |
| ⚠️ NEEDS WORK (3/5) | {count} | {list} |
| ❌ REWRITE (<3/5) | {count} | {list} |

---

## Module Reports

{Full report for each module}

---

## Detailed Module: {module_number} - {title}

**Overall Score:** {X}/5 {stars}
**Template:** {template_name} | **Compliance:** ✅ PASS / ❌ FAIL

### Scores Breakdown
- Template Compliance: ✅ PASS / ❌ FAIL {reason}
- Coherence: {X}/5 {reason}
- Relevance: {X}/5 {reason}
- Educational: {X}/5 {reason}
- Language: {X}/5 {reason}
- Pedagogy: {X}/5 {reason}
- Immersion: {X}/5 {reason}
- Activities: {X}/5 {reason}
- Richness: {X}/5 {reason} (B1+ only, N/A for A1/A2)
- Word Salad: ❌ No / ⚠️ Yes
- Dryness Flags: {list any triggered flags}

### Strengths
- {strength 1}
- {strength 2}
- {strength 3}

### Issues
- **[Category]** {specific issue with line/example}
- **[Category]** {specific issue with line/example}

### Examples
{Quote 1-2 specific problematic or exemplary passages}

> "{quoted text}"
- Issue: {what's wrong}
- Fix: {how to fix}

### Recommendation
{✅ PASS / ⚠️ NEEDS IMPROVEMENT / ❌ REWRITE}

### Action Items
1. {specific, actionable fix} [SAFE/RISKY]
   - ✅ FIXED / ❌ SKIPPED / ⏳ MANUAL (if risky)
2. {specific, actionable fix} [SAFE/RISKY]
   - ✅ FIXED / ❌ SKIPPED / ⏳ MANUAL (if risky)
3. {specific, actionable fix} [SAFE/RISKY]
   - ✅ FIXED / ❌ SKIPPED / ⏳ MANUAL (if risky)

---

{Repeat for each module}

---

## Priority Fixes

### Critical (Must Fix)
{List modules with score < 3 or word salad}

### Important (Should Fix)
{List modules with score = 3}

### Optional (Nice to Have)
{List modules with score = 4 but minor issues}

---

## Patterns Across Level

### Common Strengths
- {pattern seen in multiple modules}
- {pattern seen in multiple modules}

### Common Issues
- {pattern seen in multiple modules}
- {pattern seen in multiple modules}

### Recommendations
1. {level-wide improvement suggestion}
2. {level-wide improvement suggestion}
3. {level-wide improvement suggestion}
```

## Scoring Scale

| Score | Rating | Meaning |
|-------|--------|---------|
| 5 | Excellent | No issues, exemplary quality |
| 4 | Good | Minor issues, overall strong |
| 3 | Acceptable | Several issues, needs improvement |
| 2 | Poor | Major issues, requires significant rework |
| 1 | Critical | Fundamental flaws, complete rewrite |

## Example Usage

```bash
# Review all A1 modules
/review-content a1

# Review single module
/review-content a2 19

# Review range
/review-content b1 1-10

# Review checkpoint modules in A1
/review-content a1 10 20 34
```

## Performance Notes

- **Single module:** ~30 seconds
- **10 modules:** ~5 minutes
- **Full level (34 modules):** ~15 minutes
- **Full level (80 modules):** ~40 minutes

For large batches, the command will show progress:
```
Reviewing A1...
[1/34] Module 01... ✅ PASS (4.5/5)
[2/34] Module 02... ⚠️ NEEDS WORK (3/5)
...
```

## What Gets Checked

✅ **Checked:**
- Lesson content (instructional text)
- Examples and explanations
- Engagement boxes
- Topic consistency
- Language quality
- Pedagogical approach
- **Activities** (structural integrity, answer validity, linguistic accuracy)
- **External resources** (relevance, accessibility)

❌ **Not Checked:**
- Vocabulary tables (separate audit)
- Frontmatter metadata
- Self-assessment sections

## Important Notes

1. **Focus on teaching quality**, not just format
2. **Be specific** - quote actual problematic text
3. **Provide actionable fixes** - not vague suggestions
4. **Score honestly** - don't inflate for "effort"
5. **Check both languages** - Ukrainian examples AND English explanations
6. **Context matters** - what's good at A1 may be weak at C1
7. **Auto-fix safe issues** - apply safe fixes, run audit, verify pass
8. **Save to review/ folder** - don't append to gemini/ folder anymore

## Red Flags (Auto-fail)

These trigger automatic REWRITE recommendation:
- ❌ **Template compliance failure:** Module doesn't follow appropriate template structure
- ❌ Word salad detected
- ❌ Overall score < 2/5
- ❌ Teaching wrong grammar for level
- ❌ Examples completely unrelated to topic
- ❌ No actual teaching content (just filler)
- ❌ Contradictory explanations
- ❌ **Unnatural Language Mixing:** (e.g., "The **чоловiк** is walking" -> BAD. "The word for man is **чоловік**" -> GOOD).
- ❌ **Pedagogical Leaps:** Testing material that wasn't taught.
- ❌ **Activity Structural Errors:** Duplicate items, mixed syntax, broken format
- ❌ **Multiple Valid Answers:** Activity accepts only one answer when others are linguistically valid
- ❌ **Incorrect "Correct" Answer:** The marked answer is grammatically wrong
- ❌ **Unrelated Resources:** YouTube/blog links don't match module topic
- ❌ **Dry Content (B1+):** 2+ dryness flags triggered (textbook voice, no cultural anchors, generic examples)

## Common Activity Issues (Examples)

### Issue 1: Multiple Valid Answers
```markdown
## fill-in: Transform to Perfective
1. читати → [___]
   > [!answer] прочитати
   > [!options] прочитати | читати | почитати
```
**Problem:** "почитати" is ALSO a valid perfective (means "to read for a while"). Activity wrongly treats it as incorrect.
**Fix:** Rephrase to "Give the COMPLETIVE perfective" or add note "result-focused form".

### Issue 2: Mixed Activity Syntax
```markdown
## fill-in: Transform to Perfective
7. говорити | ___ (suppletive pair)
   > [!error] suppletive pair
   > [!answer] сказати
   > [!explanation] Говорити/сказати use different roots.
```
**Problem:** `[!error]` and `[!explanation]` are error-correction syntax, not fill-in syntax.
**Fix:** Use only `[!answer]` and `[!options]` for fill-in activities.

### Issue 3: Duplicate Items
```markdown
7. розуміти → [___]
8. готувати → [___]
7. розуміти → [___]  ← DUPLICATE
8. готувати → [___]  ← DUPLICATE
```
**Problem:** Items 7-8 appear twice (copy-paste error).
**Fix:** Remove duplicates.

### Issue 4: Unrelated External Resources
```markdown
> [!resources]
> - [Cat Videos Compilation](https://youtube.com/...)  ← UNRELATED
```
**Problem:** Resource has nothing to do with Ukrainian learning.
**Fix:** Replace with relevant Ukrainian learning content or remove.
