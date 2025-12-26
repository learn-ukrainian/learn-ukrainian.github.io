# Stage 4: Review & Fix Loop

Review the module, fix violations, repeat until PASS.

## Input

- **Module file**: Complete module from Stages 1-3
- **Level**: Determines constraints and expectations

## Process

```
┌─────────────────────────────────────────────────┐
│                 REVIEW MODULE                   │
│         Run audit, check all constraints        │
└─────────────────────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │    VIOLATIONS?        │
            └───────────────────────┘
                   │         │
                   │ NO      │ YES
                   ▼         ▼
        ┌─────────────┐   ┌─────────────────────────┐
        │   PASS!     │   │  COUNT VIOLATIONS       │
        │ Output JSON │   │  ≤3 = FIX               │
        │ & MDX       │   │  >3 = REBUILD SECTION   │
        └─────────────┘   └─────────────────────────┘
                                    │
                                    ▼
                          ┌─────────────────────┐
                          │   APPLY FIX or      │
                          │   REBUILD SECTION   │
                          └─────────────────────┘
                                    │
                                    ▼
                              (loop back to REVIEW)
```

## Review Checklist

### 1. Template Compliance
- [ ] **Read the appropriate template** for this module type:
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
- [ ] Module structure matches template sections
- [ ] Word count meets template minimum
- [ ] Activity count and types match template requirements
- [ ] Vocabulary count meets template specification

### 2. Structural Audit
- [ ] Frontmatter complete (module, title, pedagogy, objectives)
- [ ] All required sections present
- [ ] Vocabulary table at end

### 3. Grammar Constraints
- [ ] Only uses grammar allowed at this level
- [ ] See `{LEVEL}-CURRICULUM-PLAN.md` Каталог В

### 4. Vocabulary Constraints
- [ ] Vocabulary table present with required columns
- [ ] IPA present for all vocabulary (A1-B1)
- [ ] Uses vocabulary from curriculum plan
- **Note:** Cross-module vocab validation deferred to `npm run vocab:rebuild`

### 5. Activity Constraints
- [ ] Count meets minimum (8-16+ by level)
- [ ] Items per activity meets minimum (12-18+ by level)
- [ ] Type variety (4-5+ types)
- [ ] Correct syntax (fill-in `___`, unjumble ` / `, etc.)
- [ ] All answers correct

### 6. Richness Constraints (Counts)

**CRITICAL: Read `docs/RICHNESS-SCORING-GUIDE.md` for scoring details and fix templates.**

- [ ] Word count meets target
- [ ] Example sentences meet minimum
- [ ] Engagement boxes meet minimum
- [ ] Mini-dialogues present

When richness fails, check the audit report for **Dryness Flags** and use the exact fix templates from the guide.

### 7. Content Richness Quality (B1+ Critical)

**This is not about counts. This is about whether the content is ALIVE or DEAD.**

Check each section for these quality indicators:

#### 7a. Engagement Quality

**DRY (robot wrote this):**
```markdown
Доконаний вид показує завершену дію.
Недоконаний вид показує незавершену дію.
Дивіться таблицю нижче.
```

**RICH (learner will remember this):**
```markdown
Уявіть: ви читаєте книгу весь вечір — це процес, недоконаний вид.
Але ось ви закрили книгу — готово! Результат. Доконаний вид.

Це як різниця між «я йшов додому» (може, ще йду) і «я прийшов» (точка, фініш).

💡 **Чому це важливо?**
Українці чують цю різницю одразу. Неправильний вид —
і речення звучить... дивно. Як фальшива нота в пісні.
```

#### 7b. Variety Check

**Count unique sentence starters in each section.** If >50% of sentences start the same way, flag as DRY.

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

#### 7c. Emotional Hooks

**Each major section needs at least one of:**
- Metaphor or analogy (як фальшива нота, як різниця між X і Y)
- Real-world scenario (уявіть: ви на співбесіді...)
- Cultural connection (українці кажуть так, бо...)
- Surprise or contrast (але тут є сюрприз!)
- Question to reader (а що якщо...? чому так?)

❌ No hooks = textbook voice = learner falls asleep

✅ Has hooks = conversation voice = learner stays engaged

#### 7d. Cultural Depth (B1+)

**Each module should include:**
- [ ] At least 1 named Ukrainian place (Львів, Карпати, Дніпро)
- [ ] At least 1 cultural reference (traditional, historical, or contemporary)
- [ ] Real-world context showing WHY this grammar/vocab matters

❌ Generic: "Людина купує хліб у магазині."
✅ Specific: "Оксана купує паляницю на Бесарабському ринку в Києві."

#### 7e. Proverbs & Idioms (B1+)

**Each grammar module should include 1-2 proverbs or idioms that:**
- Naturally demonstrate the grammar point
- Are woven into content, not just listed
- Have cultural context explained

Example for aspect:
```markdown
Українці кажуть: «Не кажи гоп, поки не перескочиш».
Зверніть увагу: **перескочиш** — доконаний вид.
Чому? Бо йдеться про результат: перестрибнув чи ні.
```

#### 7f. Richness Score Calculation

For each section, mentally score:

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

#### 7g. Quick Dryness Flags

Flag content as DRY if ANY of these are true:

| Flag | Pattern |
|------|---------|
| TEXTBOOK_VOICE | No questions, metaphors, or emotional hooks in 300+ words |
| REPETITIVE | Same sentence structure >5 times in section |
| GENERIC_EXAMPLES | No named people, places, or specific scenarios |
| LIST_DUMP | Explanation is just a list without narrative flow |
| NO_CULTURAL_ANCHOR | Grammar taught without Ukrainian cultural context |
| ENGAGEMENT_BOX_FILLER | 💡 boxes just restate what was already said |

**If 2+ flags: Section needs REWRITE, not just fix.**

### 8. Linguistic Purity
- [ ] No Surzhyk or "Ghost Words" (Verify spelling is Ukrainian, not Russian). See LINGUISTIC-PURITY-GUIDE.md
- [ ] No AI contamination ("wait", "actually", "let me")
- [ ] Correct Ukrainian spelling and grammar
- [ ] **NO Russian Characters**: Search for `ё`, `ъ`, `ы`, `э` (Forbidden).
- [ ] **NO Russian Phonetics**: No comparisons like "Ukrainian И is like Russian Ы".

## Fix Strategy

### Minor Violations (≤3 issues)
Apply targeted fixes:
- Missing vocabulary → Add to table
- Wrong syntax → Correct the specific line
- Missing engagement box → Add one
- Spelling error → Fix it

### Major Violations (>3 issues in same section)
Rebuild the section:
- Content section failing → Rewrite entire section
- Multiple activity failures → Delete all activities, recreate
- Grammar violations throughout → Rewrite affected paragraphs

### Catastrophic (>10 violations OR structural issues)
Rebuild from Stage 1:
- Frontmatter wrong → Start over
- Wrong pedagogy structure → Start over
- Vocabulary fundamentally wrong → Start over

## Running the Audit

```bash
.venv/bin/python scripts/audit_module.py {file_path}
```

Audit output categories:
- **FAIL**: Must fix (grammar, vocabulary, syntax)
- **WARN**: Should fix (richness, variety)
- **INFO**: Optional improvement

## Iteration Limit

Maximum 3 fix iterations per stage. If still failing after 3:
1. Report the persistent issues
2. Ask user for guidance
3. Consider rebuilding from earlier stage

## Output on PASS

When audit passes, run the full pipeline:

```bash
# Full pipeline: lint → generate MDX → validate MDX → validate HTML
npm run pipeline l2-uk-en {level} {module_num}

# Also generate JSON for Vibe app
npm run generate:json l2-uk-en {level} {module_num}
```

The pipeline validates:
1. **Lint**: MD format compliance
2. **Generate**: Creates MDX for Docusaurus
3. **Validate MDX**: Ensures no content loss during conversion
4. **Validate HTML**: Headless browser check for rendering errors

**Note:** HTML validation requires dev server running (`cd docusaurus && npm start`)

Report:
- Final audit score
- Pipeline status (PASS/FAIL)
- MDX file location
- JSON file location
- "MODULE APPROVED"
