# Phase 4: module-lesson-qa

Validate lesson content before locking.

> **Architecture v2.0:** Plans are immutable source of truth. Meta is mutable build config.
>
> - **Plan** (`plans/{level}/{slug}.yaml`): content_outline, word_target, objectives, vocabulary_hints
> - **Meta** (`{level}/meta/{slug}.yaml`): naturalness score, build timestamps

## Usage

```
/module-lesson-qa {level} {module_num}
```

## Input

- `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` (IMMUTABLE - content_outline, word_target, vocabulary_hints)
- `curriculum/l2-uk-en/{level}/meta/{slug}.yaml` (MUTABLE - naturalness, build config)
- `curriculum/l2-uk-en/{level}/{slug}.md` (from Phase 3)

## Validation Checks

### 0. Script Validation (Mechanical Checks)

**Run automated validation first to catch basic errors:**

```bash
.venv/bin/python scripts/audit_module.py --phase=lesson-qa curriculum/l2-uk-en/{level}/{slug}.md
```

This script verifies:

- YAML frontmatter syntax is valid
- Markdown structure is parseable
- No broken formatting
- File encoding is UTF-8

**If script fails:** Fix mechanical errors before proceeding to manual checks.

**Note:** Script validation is mechanical only. Quality checks (1-18) require human/LLM judgment.

---

### 1. Template Compliance

**Before detailed checks, verify module follows correct template structure.**

**Read the appropriate template for this module type:**

- **A1:** `docs/l2-uk-en/templates/a1-module-template.md`
- **A2:** `docs/l2-uk-en/templates/a2-module-template.md`
- **B1 M01-05 (Metalanguage):** `docs/l2-uk-en/templates/b1-metalanguage-module-template.md`
- **B1 M06-51 (Grammar):** `docs/l2-uk-en/templates/b1-grammar-module-template.md`
- **B1 M52-71 (Vocabulary):** `docs/l2-uk-en/templates/b1-vocab-module-template.md`
- **B1 M72-81 (Cultural):** `docs/l2-uk-en/templates/b1-cultural-module-template.md`
- **B1 M82-86 (Integration):** `docs/l2-uk-en/templates/b1-integration-module-template.md`
- **B1 Checkpoints:** `docs/l2-uk-en/templates/b1-checkpoint-module-template.md`
- **B2 core:** `docs/l2-uk-en/templates/b2-grammar-module-template.md` (or cultural/vocab based on focus)
- **B2-HIST:** `docs/l2-uk-en/templates/ai/b2-history-module-template.md`
- **B2-PRO:** `docs/l2-uk-en/templates/ai/b2-pro-module-template.md`
- **C1-BIO:** `docs/l2-uk-en/templates/ai/c1-biography-module-template.md`
- **C1-HIST:** `docs/l2-uk-en/templates/ai/c1-history-module-template.md`
- **C1-PRO:** `docs/l2-uk-en/templates/ai/c1-pro-module-template.md`
- **LIT:** `docs/l2-uk-en/templates/ai/lit-module-template.md`

**Verify:**

- [ ] Module structure matches template sections
- [ ] Section headers follow template naming
- [ ] Content follows pedagogy pattern from template

**If structure doesn't match template:** FAIL - may require Phase 1 rewind to fix meta.yaml structure.

### 2. File Structure

**Required components:**

```markdown
---
{ YAML frontmatter }
---

<!-- SCOPE
{scope comment}
-->

# {Title}

{Content sections}

---

# Підсумок

{Summary}

---
```

All these MUST exist:

- [ ] YAML frontmatter present and valid
- [ ] SCOPE comment present
- [ ] H1 title matches meta.title
- [ ] Підсумок section present

### 3. Word Count Accuracy

**CRITICAL:** This is the primary validation.

> **📖 READ THIS FIRST: Section Flexibility**
>
> Section word targets are FLEXIBLE guidance, not strict limits.
> See: `docs/SUBSECTION-FLEXIBILITY-GUIDE.md`
>
> **Quick examples:**
>
> - Section A: 1200/600 (+600 over) + Section B: 400/600 (-200 under) = Redistribute 200 words from A to B
> - Total: 3500/4000 (under) = Must expand with new content (can't just redistribute)
> - Total: 4100/4000 (over) + some sections under = Redistribute only (no expansion needed)

**Priority hierarchy:**

1. **Total word count** ≥ word_target (MOST IMPORTANT)
2. Individual sections within ±10% tolerance (flexible guidance)

**Section word counts are FLEXIBLE:**

- You can redistribute words between sections
- One section can be 20% over if another is 5% under
- As long as total ≥ word_target and no section >10% under

1. **Count words in each section:**
   - Extract content between H2 headers
   - Exclude YAML, SCOPE comment, Підсумок
   - Count actual prose words

2. **Compare to plan targets:**

   ```
   For each section in plan.content_outline:
     actual = count_words(section_content)
     target = plan.content_outline[i].words
     tolerance = ±10% of target

     if actual < (target * 0.9):
       WARNING: Section "{section}" under target (but can redistribute)

     if actual > (target * 1.1):
       NOTE: Section "{section}" over target (content depth - OK)
   ```

3. **Check total:**

   ```
   total_actual = sum(all_section_word_counts)
   total_target = plan.word_target
   tolerance = ±5% of target

   if total_actual < (target * 0.95):
     FAIL: Total word count below minimum
   ```

**Fix strategy for section mismatches:**

If total is met but some sections are >10% under:

- **Option A:** Expand under-target sections with new content
- **Option B:** Redistribute content from over-target sections
- **Option C:** Combination of both

Example:

```
Section A: 1200 / 600 (+600 words over)
Section B: 400 / 600 (-200 words under)
Total: 4000 / 4000 ✅

Fix: Move ~200 words from Section A to Section B
Result: Both sections balanced, total unchanged
```

**Why 10% per section but 5% total?**

- Individual sections can vary slightly
- Variations should balance out
- Overall target must be tight

### 4. Content Outline Coverage

All sections from `plan.content_outline` MUST be present as H2 headers:

```
For each section in plan.content_outline:
  if section.section not found as H2 in markdown:
    FAIL: Missing section "{section.section}"
```

**Exception:** Empty sections with 0 words in plan can be skipped.

### 5. Engagement Boxes

Count callout blocks matching pattern `> [!type]`:

**Minimum by level:**

- A1: 3+
- A2: 4+
- B1: 5+
- B2: 6+
- C1: 7+
- C2: 8+

**Valid types:** tip, history-bite, myth-buster, culture, quote, warning

```
count = number of "> [!{type}]" blocks
if count < level_minimum:
  FAIL: Engagement boxes below minimum
```

### 6. Example Sentences

Count sentences matching pattern `_Приклад:_ «{text}»`:

**Minimum by level:**

- A1: 12+
- A2: 18+
- B1: 24+
- B2: 24+
- C1: 30+
- C2: 32+

```
count = number of "_Приклад:_" occurrences
if count < level_minimum:
  FAIL: Example sentences below minimum
```

### 7. Mini-Dialogues

**For grammar/vocab modules (focus != history/cultural):**

Count dialogue blocks matching pattern `**Діалог:**`:

**Minimum by level:**

- A1: 2+
- A2: 3+
- B1: 4+
- B2: 4+
- C1: 5+
- C2: 5+

```
if meta.focus in [grammar, vocabulary]:
  count = number of "**Діалог:**" blocks
  if count < level_minimum:
    FAIL: Mini-dialogues below minimum
```

**For history/cultural modules:** Skip this check (dialogues not required).

### 8. Required Vocabulary

All vocabulary from `plan.vocabulary_hints.required` MUST appear in content:

```
For each word in plan.vocabulary_hints.required:
  if word not found in markdown content:
    FAIL: Required vocabulary "{word}" not used
```

**Note:** Check Ukrainian word only (before parentheses with translation).

### 9. Vocabulary Level Appropriateness

**All vocabulary in content must be within the level's allowed scope.**

**Process:**

1. **Read module plan:**

   ```
   curriculum/l2-uk-en/plans/{level}/{slug}.yaml
   ```

2. **Extract all Ukrainian words** from lesson content (excluding proper nouns)

3. **Check against cumulative vocabulary:**
   - For A1: Only A1 vocabulary allowed
   - For A2: A1 + A2 vocabulary allowed
   - For B1: A1 + A2 + B1 vocabulary allowed
   - For B2-HIST: A1 + A2 + B1 + B2 core + B2-HIST vocabulary allowed
   - etc.

4. **Flag out-of-scope words:**
   ```
   For each word in content:
     if word not in cumulative_allowed_vocabulary:
       if word not in plan.vocabulary_hints (required + recommended):
         WARNING: Out-of-scope vocabulary "{word}" (too advanced for {level})
   ```

**Special cases:**

- Words in `plan.vocabulary_hints.recommended` are allowed even if not in cumulative list (pre-teaching)
- Proper nouns (names, places) are exempt
- International cognates are exempt at all levels

**If 5+ out-of-scope words found:** FAIL - vocabulary level too advanced for this module.

### 10. Forbidden Content

Content MUST NOT contain:

- [ ] Activities/exercises (go in Phase 5)
- [ ] Vocabulary tables (go in Phase 7)
- [ ] Practice recommendations section (auto-generated)

**Red flags:**

- Headers like "Activities", "Вправи", "Vocabulary", "Словник"
- YAML table blocks in vocabulary format
- "Потрібно більше практики?" section (should not be in Phase 3 output)

### 11. Immersion Percentage (B1+ only)

**For B1+ modules (100% Ukrainian):**

Count non-Ukrainian words (excluding proper nouns, code examples):

```
ukrainian_words = count words in Cyrillic
total_words = total word count
immersion = (ukrainian_words / total_words) * 100

if level >= B1 and immersion < 95%:
  WARNING: Immersion below 95% ({immersion}%)
```

**For A1-A2:** Verify graduated immersion matches phase targets.

### 12. YAML Frontmatter Match

Frontmatter MUST match meta.yaml:

```yaml
Required fields that must match:
  - module == meta.module
  - title == meta.title
  - subtitle == meta.subtitle
  - version == meta.version
  - phase == meta.phase
  - pedagogy == meta.pedagogy
  - focus == meta.focus
  - duration == meta.duration
  - transliteration == meta.transliteration
```

If `register` present in meta, must be in frontmatter.

### 13. Primary Sources (History modules only)

**For history/cultural modules with seminar pedagogy:**

Minimum 2 primary source excerpts in `[!quote]` callouts:

```
if meta.pedagogy == "seminar" and meta.focus in [history, cultural]:
  quote_count = count of "> [!quote]" blocks
  if quote_count < 2:
    FAIL: Less than 2 primary sources
```

### 14. Factual Accuracy (History/Cultural Modules)

**For history, cultural, biography modules - verify all factual claims.**

**Using your knowledge base, check:**

1. **Historical dates and events:**
   - Birth/death dates correct
   - Event dates accurate
   - Chronology logical

2. **Names and spellings:**
   - Historical figures spelled correctly in Ukrainian
   - Place names use correct Ukrainian forms (not Russian)
   - Titles and positions accurate

3. **Historical facts:**
   - Events described accurately
   - Cause-effect relationships correct
   - No anachronisms

4. **Literary/cultural attributions:**
   - Works correctly attributed to authors
   - Dates of publication/creation correct
   - Cultural movements accurately described

**Process:**

```
For each factual claim in content:
  Verify against your knowledge base

  If uncertain:
    FLAG for user verification

  If definitively wrong:
    FAIL: Factual error - "{claim}" should be "{correction}"
```

**Examples of factual errors to catch:**

| Error                            | Correction                   |
| -------------------------------- | ---------------------------- |
| Нечуй-Левицький народився 1845   | народився 1838               |
| Київська Русь заснована 988 року | хрещення 988, держава раніше |
| Шевченко написав "Кобзар" 1860   | перше видання 1840           |

**For core modules (grammar/vocab):** Skip this check unless cultural references are present.

**If factual errors found:** FAIL with specific corrections.

### 15. Primary Ukrainian Language Correctness

**MANDATORY check using your Ukrainian language knowledge:**

Extract 3-5 sample passages from main content and validate:

```
For each sample passage:
  - Grammar correctness (case endings, verb aspects, word order)
  - No obvious Surzhyk (приймати участь → брати участь)
  - No English calques (робити сенс → мати сенс)
  - Natural Ukrainian syntax
```

**Common errors to check:**

| ❌ Wrong        | ✅ Correct   | Issue              |
| --------------- | ------------ | ------------------ |
| приймати участь | брати участь | Russicism          |
| самий кращий    | найкращий    | Superlative calque |
| на протязі      | протягом     | Russicism          |
| робити сенс     | мати сенс    | English calque     |

**If grammar errors found:** FAIL with specific corrections needed.

**Optional:** If Gemini MCP validator available, use it for additional validation.

### 16. Linguistic Purity (CRITICAL)

**ZERO TOLERANCE checks - any violation is FAIL:**

1. **NO Russian Characters:**

   ```bash
   # Search for forbidden characters
   grep -n '[ёъыэ]' {slug}.md
   ```

   If any found: FAIL immediately
   - **ё** → Ukrainian uses **є** or **йо**
   - **ъ** → Not used in Ukrainian
   - **ы** → Ukrainian uses **и**
   - **э** → Ukrainian uses **е**

2. **NO Russian Phonetic Comparisons:**

   Forbidden patterns:
   - "Ukrainian И is like Russian Ы"
   - "similar to Russian..."
   - Any cross-references to Russian phonology

   If found: FAIL - Remove all Russian comparisons

3. **NO AI Contamination:**

   Search for English fragments in Ukrainian text:
   - "wait", "actually", "let me", "note that"

   If found: FAIL - Pure Ukrainian only

4. **Verify Against LINGUISTIC-PURITY-GUIDE.md:**

   Check suspect words against:

   ```
   docs/l2-uk-en/LINGUISTIC-PURITY-GUIDE.md
   ```

**This check is BLOCKING - module cannot proceed if any violations found.**

### 17. Content Richness Quality (B1+ CRITICAL)

**For B1+ modules only.** This evaluates whether content is ALIVE or DEAD.

**Skip for A1-A2** (different standards apply).

For each major content section, evaluate:

#### 14a. Engagement Quality

**DRY (textbook voice - FAIL):**

```markdown
Доконаний вид показує завершену дію.
Недоконаний вид показує незавершену дію.
Дивіться таблицю нижче.
```

**RICH (conversational - PASS):**

```markdown
Уявіть: ви читаєте книгу весь вечір — це процес, недоконаний вид.
Але ось ви закрили книгу — готово! Результат. Доконаний вид.

Це як різниця між «я йшов додому» (може, ще йду) і «я прийшов» (точка, фініш).
```

#### 14b. Variety Check

Count unique sentence starters in each section:

```
If >50% of sentences start the same way → FAIL as REPETITIVE
```

❌ DRY pattern:

```markdown
Доконаний вид означає...
Доконаний вид використовується...
Доконаний вид показує...
```

✅ RICH pattern:

```markdown
Коли дія завершена — це доконаний вид.
Українці кажуть «я прочитав книгу», бо книга закінчена.
А якщо ще читаю? Тоді «читаю» — без результату.
```

#### 14c. Emotional Hooks

Each major section needs at least ONE of:

- [ ] Metaphor or analogy ("як фальшива нота", "як різниця між X і Y")
- [ ] Real-world scenario ("уявіть: ви на співбесіді...")
- [ ] Cultural connection ("українці кажуть так, бо...")
- [ ] Surprise or contrast ("але тут є сюрприз!")
- [ ] Question to reader ("а що якщо...? чому так?")

**If no hooks:** Flag as TEXTBOOK_VOICE (requires enrichment).

#### 14d. Cultural Depth (B1+)

Each module should include:

- [ ] At least 1 named Ukrainian place (Львів, Карпати, Дніпро)
- [ ] At least 1 cultural reference (traditional, historical, contemporary)
- [ ] Real-world context showing WHY this matters

❌ Generic: "Людина купує хліб у магазині."
✅ Specific: "Оксана купує паляницю на Бесарабському ринку в Києві."

**If all examples are generic:** Flag as NO_CULTURAL_ANCHOR.

#### 14e. Proverbs & Idioms (B1+ Grammar Modules)

**For grammar modules:** Should include 1-2 proverbs/idioms that:

- Naturally demonstrate the grammar point
- Are woven into content (not just listed)
- Have cultural context explained

Example for aspect:

```markdown
Українці кажуть: «Не кажи гоп, поки не перескочиш».
Зверніть увагу: **перескочиш** — доконаний вид.
Чому? Бо йдеться про результат: перестрибнув чи ні.
```

**For history/cultural modules:** Proverbs optional but cultural depth mandatory.

#### 14f. Richness Score (B1+ only)

For each section, score:

| Criterion       | 0 (FAIL)            | 1 (WARN)         | 2 (PASS)                  |
| --------------- | ------------------- | ---------------- | ------------------------- |
| Engagement      | Textbook voice      | Some personality | Conversational, memorable |
| Variety         | Repetitive starters | Mixed            | Varied, rhythmic          |
| Hooks           | None                | 1-2              | 3+ per section            |
| Cultural depth  | Generic examples    | Some specifics   | Rich, placed content      |
| Proverbs/idioms | None                | 1 (forced)       | 1-2 (natural)             |

**Scoring:**

- **Total 0-4:** ❌ FAIL - Section needs REWRITE
- **Total 5-7:** ⚠️ WARNING - Section needs ENRICHMENT
- **Total 8-10:** ✅ PASS

**If average score across all sections < 6:** FAIL module for enrichment.

#### 14g. Quick Dryness Flags

Flag content if ANY of these are true:

| Flag                  | Pattern                                                   | Action |
| --------------------- | --------------------------------------------------------- | ------ |
| TEXTBOOK_VOICE        | No questions, metaphors, or emotional hooks in 300+ words | WARN   |
| REPETITIVE            | Same sentence structure >5 times in section               | FAIL   |
| GENERIC_EXAMPLES      | No named people, places, or specific scenarios            | WARN   |
| LIST_DUMP             | Explanation is just a list without narrative flow         | WARN   |
| NO_CULTURAL_ANCHOR    | Grammar taught without Ukrainian cultural context         | WARN   |
| ENGAGEMENT_BOX_FILLER | 💡 boxes just restate what was already said               | WARN   |

**If 2+ flags in same section:** Section needs REWRITE, not just fix.

**This check applies to B1+ only.** For A1-A2, focus on structural checks (1-11).

### 18. Naturalness Check (MANDATORY - Agent Evaluated)

**CRITICAL:** Naturalness is NEVER skipped - every module with Ukrainian text requires evaluation.

> **🤖 Agent Evaluation:** You (Claude/Gemini) evaluate naturalness directly during this QA phase.
> There is no automated script for this - it's YOUR responsibility to analyze the prose.
> The audit script only checks if a score exists in meta.yaml; YOU provide the actual evaluation.

#### 15.1 Extract ALL Ukrainian Text

Evaluate ALL Ukrainian prose content:

- Main lesson content (all paragraphs)
- Engagement box content
- Example sentences
- Mini-dialogues
- Summary section

**Note:** Don't evaluate YAML frontmatter or SCOPE comments.

#### 15.2 Analyze Naturalness

**Switch to Ukrainian language mode.** Score prose 1-10 based on:

1. **Subject consistency** - Are subjects maintained throughout passages?
2. **Discourse markers** - Presence of connectors (а, але, потім, тому, також, спочатку, нарешті)
3. **Topic coherence** - Do passages maintain unified topics or jump randomly?
4. **Redundancy** - Are there repetitive patterns or disconnected sentences?

**Red flags (score < 8/10):**

| Issue                         | Example                                                  |
| ----------------------------- | -------------------------------------------------------- |
| **Template repetition**       | Same sentence structure repeated across sections         |
| **Excessive intensifiers**    | "дуже" used 5+ times, "надзвичайно/справжній" overused   |
| **Double superlatives**       | "найвидатніший та найвідоміший" (semantically redundant) |
| **Missing discourse markers** | List of disconnected factoids with no connectors         |
| **Robotic transitions**       | "і це допомагає...", "тому що... тому" (mechanical)      |

#### 15.3 Scoring Standards

| Module Type                         | Target Score | Threshold   |
| ----------------------------------- | ------------ | ----------- |
| **Content modules (grammar/vocab)** | 8/10         | FAIL if < 8 |
| **History/cultural modules**        | 8/10         | FAIL if < 8 |
| **Checkpoints**                     | 7/10         | FAIL if < 7 |

**Calculate average score across all prose sections.**

#### 15.4 Update Meta File (MANDATORY)

After evaluating, **ALWAYS update the meta file:**

```yaml
# curriculum/l2-uk-en/{level}/meta/{slug}.yaml

# ADD THIS SECTION:
naturalness:
  score: 9 # Your evaluated score (1-10)
  status: PASS # PASS if score >= threshold, else FAIL
```

**Status values:**

- `PASS` - Score meets threshold
- `FAIL` - Score below threshold (module needs enrichment)

**This update is MANDATORY - module-lesson-qa cannot pass without it.**

#### 15.5 Fix Flagged Issues

If score < threshold:

1. Identify specific red flags
2. Apply fixes:
   - **Template repetition:** Vary sentence structures
   - **Excessive intensifiers:** Remove 50% of "дуже", eliminate "надзвичайно" unless essential
   - **Double superlatives:** Replace with single precise descriptor
   - **Missing discourse markers:** Add 2-3 connectors per 10-sentence passage
   - **Robotic transitions:** Simplify mechanical constructions

3. Re-score after fixes
4. Update meta file with new score

**Module cannot be locked until naturalness score passes and meta is updated.**

---

## Fix Strategy

**Based on violation count and severity, determine the appropriate fix approach:**

### Minor Violations (≤3 issues)

**Apply targeted fixes:**

- Missing vocabulary → Add to content where contextually appropriate
- Wrong syntax in markdown → Correct the specific line
- Missing engagement box → Add one in relevant section
- Spelling/grammar error → Fix it directly
- Out-of-scope vocabulary → Replace with level-appropriate word

**Action:** Edit specific sections, re-run validation.

### Major Violations (>3 issues in same section)

**Rebuild the affected section:**

- Content section failing richness → Rewrite entire section with more engagement
- Multiple naturalness red flags in section → Regenerate section from scratch
- Grammar violations throughout section → Rewrite affected paragraphs
- Factual errors + poor structure → Rebuild section with correct facts

**Action:** Regenerate entire section, re-run validation.

### Catastrophic (>10 violations OR structural issues)

**Requires Phase Rewind:**

- Frontmatter doesn't match meta → Phase 1 rewind (meta.yaml needs fixing)
- Wrong pedagogy structure → Plan update needed (plan.content_outline needs restructuring)
- Vocabulary fundamentally wrong → Plan update needed (vocabulary_hints need correction)
- Word count targets impossible to meet → Plan update needed (plan.word_target needs adjustment)
- Missing required sections → Plan update needed (content_outline incomplete)

**Note:** Plan changes require human approval - agents cannot modify plan files.

**Action:** Output "PHASE UNLOCK REQUIRED" with specific reason, halt validation.

---

## LLM Self-Validation Logging (MANDATORY)

<critical>

**SKEPTICAL VALIDATION - NOT A RUBBER STAMP**

You are the last line of defense. Be aggressive in finding errors.

**After completing all 18 validation checks, you MUST create a detailed validation log.**

</critical>

### Logging Format

**Create file:** `curriculum/l2-uk-en/{level}/review/{slug}-llm-review.md`

**Template:**

````markdown
# LLM Self-Validation: {slug}

**Validated by:** Claude Sonnet 4.5 | **Date:** {YYYY-MM-DD}
**Module:** {level}-{num} | **Focus:** {focus} | **Pedagogy:** {pedagogy}

---

## Validation Summary

**Overall Result:** ✅ PASS / ❌ FAIL
**Total Checks:** 18
**Checks Passed:** {N}
**Checks Failed:** {N}
**Warnings:** {N}

---

## Detailed Check Results

### 1. Template Compliance

**Status:** ✅/❌
**Evidence:** Template `{template_name}` loaded and compared. Structure matches/differs in: {details}

### 2. File Structure

**Status:** ✅/❌
**Evidence:** All required components present: frontmatter ✓, SCOPE ✓, title ✓, Підсумок ✓

### 3. Word Count Accuracy

**Status:** ✅/❌
**Total:** {actual}/{target} ({percentage}%)
**Section breakdown:**

- {Section 1}: {count}/{target} words ({percentage}%)
- {Section 2}: {count}/{target} words ({percentage}%)
  ...
  **Violations:** {list any sections outside ±10% or "None"}

### 4. Content Outline Coverage

**Status:** ✅/❌
**Expected sections:** {N}
**Found sections:** {N}
**Missing:** {list or "None"}

### 5. Engagement Boxes

**Status:** ✅/❌
**Count:** {actual} (minimum: {min})
**Types found:** {list types}

### 6. Example Sentences

**Status:** ✅/❌
**Count:** {actual} (minimum: {min})
**Sampled:** "{first example}" ... "{last example}"

### 7. Mini-Dialogues

**Status:** ✅/❌/N/A
**Count:** {actual} (minimum: {min})
**Reason if N/A:** {history/cultural module}

### 8. Required Vocabulary

**Status:** ✅/❌
**Required terms:** {N}
**All found:** Yes/No
**Missing:** {list or "None"}

### 9. Vocabulary Level Appropriateness

**Status:** ✅/❌/⚠️
**Level:** {level}
**Out-of-scope words found:** {N}
**Details:** {list words that are too advanced, or "All vocabulary appropriate for level"}

### 10. Forbidden Content

**Status:** ✅/❌
**Activities found:** No/Yes {details}
**Vocabulary tables found:** No/Yes {details}
**Practice recommendations found:** No/Yes {details}

### 11. Immersion Percentage

**Status:** ✅/❌/N/A
**Percentage:** {percentage}% (target: {target}%)
**Non-Ukrainian words:** {count}

### 12. YAML Frontmatter Match

**Status:** ✅/❌
**All fields match meta.yaml:** Yes/No
**Mismatches:** {list or "None"}

### 13. Primary Sources

**Status:** ✅/❌/N/A
**Count:** {actual} (minimum: 2 for seminar modules)
**Sources:** {list quote callout titles or "N/A for non-seminar"}

### 14. Factual Accuracy

**Status:** ✅/❌/N/A
**Checked:** {N} factual claims
**Errors found:** {list specific errors with corrections, or "None"}
**Uncertain claims flagged:** {list or "None"}

### 15. Primary Ukrainian Language Correctness

**Status:** ✅/❌
**Passages sampled:** {N}
**Grammar errors:** {list specific errors, or "None found"}
**Russicisms:** {list or "None found"}
**English calques:** {list or "None found"}

### 16. Linguistic Purity

**Status:** ✅/❌
**Russian characters (ё,ъ,ы,э):** Found {N} / None
**Russian phonetic comparisons:** Found {N} / None
**AI contamination:** Found {N} English fragments / None
**LINGUISTIC-PURITY-GUIDE.md checked:** Yes

### 17. Content Richness Quality (B1+ only)

**Status:** ✅/❌/⚠️/N/A
**Average richness score:** {score}/10
**Section scores:**

- {Section 1}: Engagement {score}, Variety {score}, Hooks {score}, Cultural {score}, Proverbs {score} = {total}/10
- {Section 2}: ...
  **Dryness flags:** {list flags or "None"}
  **Sections needing rewrite:** {list or "None"}

### 18. Naturalness Check

**Status:** ✅/❌
**Score:** {score}/10 (threshold: {8 or 7}/10)
**Prose passages evaluated:** {N}
**Red flags:** {list specific issues or "None"}
**Meta file updated:** Yes with score={score}, status={PASS/FAIL}

---

## Issues Found

{MUST list specific issues with line numbers/section names, or explicitly state:}
**None found after checking {N} items across 18 validation categories.**

---

## Fixes Applied

{If any fixes were needed during validation, list them with before/after:}

**Example:**

1. **Section "Ранні роки"** - Removed Russicism "на протязі" → replaced with "протягом"
2. **Naturalness** - Added discourse markers "також", "проте" to improve flow in Section 3
3. **Word count** - Section "Військовий лідер" was 810 words (target: 900), added 90 words of detail

{Or if no fixes needed:}
**None needed - module passed all checks on first validation.**

---

## Naturalness Meta Update

```yaml
naturalness:
  score: { score }
  status: { PASS/FAIL }
```
````

**Meta file path:** `curriculum/l2-uk-en/{level}/meta/{slug}.yaml`
**Update applied:** Yes / No (if FAIL, will be applied after fixes)

---

## Recommendation

**PASS:** Module meets all quality standards. Ready to lock and proceed to Phase 5 (module-act).

**FAIL:** Module has {N} violations. Apply {minor/major/catastrophic} fix strategy and re-run validation.

**PHASE REWIND:** Meta.yaml needs correction for: {specific reason}. Unlock Phase 1, fix meta, re-run module-meta-qa, then regenerate lesson.

---

**Validation completed:** {timestamp}

```

### Evidence Requirements

**CRITICAL:** Generic statements like "all checks passed" are NOT acceptable.

For each check, you MUST provide:

1. **Specific counts** (e.g., "Found 15 engagement boxes")
2. **Examples** (e.g., "Sampled naturalness in Section 3: '{quote 10 words}'")
3. **Line numbers** for errors (e.g., "Line 47: Found Russian character 'ё'")
4. **Before/after** for fixes (e.g., "Changed 'на протязі' → 'протягом'")

**If you write "No issues found", you MUST also state:**
- "After checking {N} items"
- "Across {N} sections"
- "In {N} passages sampled"

**This detailed log is MANDATORY for audit trail and quality tracking.**

---

## Output

### On PASS

```

LESSON-QA: PASS

✓ File structure complete
✓ Word count: {total}/{target} ({percentage}%) - within tolerance

- Section 1: {count}/{target} words
- Section 2: {count}/{target} words
- ...
  ✓ Content outline: All {N} sections present
  ✓ Engagement boxes: {count} (min: {level_min})
  ✓ Example sentences: {count} (min: {level_min})
  ✓ Mini-dialogues: {count} (min: {level_min}) [if applicable]
  ✓ Required vocabulary: All {N} terms used
  ✓ No forbidden content
  ✓ Immersion: {percentage}% [if B1+]
  ✓ Frontmatter matches meta
  ✓ Primary sources: {count} [if history module]
  ✓ Ukrainian grammar: No errors found
  ✓ Linguistic purity: PASS (no Russian chars, no AI contamination)
  ✓ Content richness: {Average score {score}/10 | SKIPPED (A1-A2)}
  ✓ Naturalness: {score}/10 - PASS (meta updated)

META UPDATED: naturalness.score = {score}, naturalness.status = PASS
VALIDATION LOG: curriculum/l2-uk-en/{level}/review/{slug}-llm-review.md

LESSON LOCKED. Proceed to: /module-act {level} {module_num}

```

### On FAIL

```

LESSON-QA: FAIL

Violations:

1. [CHECK_NAME]: {specific issue}
2. [CHECK_NAME]: {specific issue}
   ...

VALIDATION LOG: curriculum/l2-uk-en/{level}/review/{slug}-llm-review.md
See detailed log for evidence and fix recommendations.

Apply {MINOR/MAJOR} fix strategy.
Fix {slug}.md and re-run: /module-lesson-qa {level} {module_num}

```

### On PHASE REWIND

If violations require meta.yaml changes:

```

PHASE UNLOCK REQUIRED: {reason}

Meta.yaml needs adjustment. Examples:

- Word targets too low for content requirements
- Missing sections in content_outline
- Vocabulary_hints missing essential terms

Fix meta.yaml, re-run /module-meta-qa, then regenerate lesson.

```

---

## Validation Helper Functions

### Count Words in Section

```

Extract text between:
Start: ## {section_name}
End: Next ## or ---

Remove:

- Markdown formatting (\*_, _, \_, etc.)
- Callout markers (> [!type])
- Links ([text](url) → text)
- Code blocks

Count remaining words

```

### Extract Engagement Boxes

```

Pattern: ^>\s\*\[!(\w+)\]
Capture group 1 = type (tip, history-bite, etc.)

```

### Extract Examples

```

Pattern: _Приклад:_\s\*«([^»]+)»
Count occurrences

```

### Extract Dialogues

```

Pattern: \*\*Діалог:\*\*
Count occurrences

```

---

## Implementation Notes

1. **Word counting:** Use same algorithm as Phase 3 generation for consistency
2. **Tolerance levels:** Strict on total (±5%), lenient on sections (±10%)
3. **Quality checks are MANDATORY:** Linguistic purity, content richness (B1+), and naturalness are BLOCKING
4. **Meta file update required:** Naturalness score MUST be written to meta.yaml before module can be locked
5. **Fast fail:** Check structure first, then word count, then quality (most expensive)
6. **Detailed output:** Show which sections are over/under target, which quality checks failed

---

## Next Phase

On PASS, output is LOCKED. User proceeds to Phase 5 (module-act).

## Examples

### Example 1: PASS - B2-HIST Lesson QA

**Input:** `trypillian-civilization.md` and `meta/trypillian-civilization.yaml`

**Output:**
```

LESSON-QA: PASS

✓ File structure complete
✓ Word count: 2700/2500 (108%) - within tolerance

- Вступ: 500/500 words
- Читання: 2000/2000 words
- Підсумок: 200/200 words (not counted in target)
  ✓ Content outline: All 3 sections present
  ✓ Engagement boxes: 6 (min: 6 for B2)
  ✓ Example sentences: 28 (min: 24 for B2)
  ✓ Mini-dialogues: N/A (history module)
  ✓ Required vocabulary: All 20 terms used
  ✓ No forbidden content
  ✓ Immersion: 99% (target: 98-100% for B2)
  ✓ Frontmatter matches meta
  ✓ Primary sources: 3 (min: 2 for seminar)
  ✓ Ukrainian grammar: No errors found
  ✓ Linguistic purity: PASS (no Russian chars, no AI contamination)
  ✓ Content richness: 9/10 (B1+)
  ✓ Naturalness: 9/10 - PASS (meta updated)

META UPDATED: naturalness.score = 9, naturalness.status = PASS
VALIDATION LOG: curriculum/l2-uk-en/b2-hist/review/trypillian-civilization-llm-review.md

LESSON LOCKED. Proceed to: /module-act b2-hist 1

```

### Example 2: FAIL - Word Count Issues

**Input:** Module with sections over/under target

**Output:**
```

LESSON-QA: FAIL

Violations:

1. Word count accuracy: Total 3100/4000 (77.5%) - below 95% tolerance
2. Content outline coverage: Section "Читання" 1200/2000 words (60%) - below 90% tolerance
3. Example sentences: 15 (minimum: 24 for B2)

VALIDATION LOG: curriculum/l2-uk-en/{level}/review/{slug}-llm-review.md
See detailed log for evidence and fix recommendations.

Apply MINOR fix strategy.
Fix {slug}.md and re-run: /module-lesson-qa {level} {module_num}

```

### Example 3: FAIL - Naturalness Below Threshold

**Input:** B1 grammar module with robotic prose

**Output:**
```

LESSON-QA: FAIL

Violations:

1. Naturalness Check: 6/10 (threshold: 8/10 for B1+) - Multiple red flags: template repetition, missing discourse markers, robotic transitions

VALIDATION LOG: curriculum/l2-uk-en/{level}/review/{slug}-llm-review.md

Apply MAJOR fix strategy.
Fix {slug}.md and re-run: /module-lesson-qa {level} {module_num}

```

---

On FAIL, user fixes lesson content and re-runs this phase.

On PHASE REWIND, unlock meta.yaml and restart from Phase 1.
```
