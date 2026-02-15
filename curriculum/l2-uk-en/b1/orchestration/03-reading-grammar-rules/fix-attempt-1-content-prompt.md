# Fix: Content Expansion (Attempt 1)

> **You are Gemini, fixing content from Phase 2 that failed audit.**
> **Your ONLY task: Expand the content to meet word count and richness requirements.**

## Files to Read

Read the current content file:
```
curriculum/l2-uk-en/b1/03-reading-grammar-rules.md
```

Read the meta for section budgets:
```
curriculum/l2-uk-en/b1/meta/03-reading-grammar-rules.yaml
```

Read the plan for vocabulary constraints:
```
curriculum/l2-uk-en/plans/b1/reading-grammar-rules.yaml
```

## Audit Failures

The content failed on these gates:

### 1. Word Count: 3076/4000 (-924 words)

Section deficits:
| Section | Current | Target | Deficit |
|---------|---------|--------|---------|
| Дієслова для виконання вправ | 265 | 392 | -127 |
| Аналітична термінологія | 265 | 392 | -127 |
| Термінологія стилю та регістру | 263 | 392 | -129 |
| Терміни словотвору | 208 | 313 | -105 |
| Практика: Аналіз правил | 199 | 428 | -229 |
| Діалоги: Обговорення правил | 346 | 588 | -242 |
| Підсумок | 180 | 295 | -115 |

### 2. Richness: 73% (needs ≥95%)

Missing elements:
- **NO_DIALOGUE**: Add at least 4 mini-dialogues (the Діалоги section exists but needs expansion)
- **NO_TABLES**: Add at least 2 comparison/paradigm tables
- **LOW_CULTURAL_ANCHOR**: Add 2+ cultural anchors (Smotrytsky, Ohiienko)

## Your Task

**Rewrite the ENTIRE content file** with these fixes applied. Keep the same H2/H3 structure, keep all existing good content, but EXPAND every deficient section.

### Expansion Strategy

For each deficient section:
1. **Add H3 subsections** where concepts are compressed — each term/concept needs its own 80-100 word block
2. **Add example sentences** (2+ per concept, in varied formats)
3. **Add comparison tables** for pattern groups
4. **Add mini-dialogues** in the Діалоги section (need 6 dialogues, ~100 words each)
5. **Add callout boxes** ([!tip], [!warning], [!culture], [!observe]) to boost engagement

### Specific Expansions Required

**Дієслова для виконання вправ (+127 words):**
- Each verb group (вибору, структурування, творчі) needs its own H3 with 80+ words
- Add a table showing verb → typical context

**Аналітична термінологія (+127 words):**
- Each term (контекст, маркер, частота, аспектуальна пара) needs its own paragraph
- Add [!tip] about using these terms

**Термінологія стилю та регістру (+129 words):**
- Add Ohiienko cultural hook as [!culture] box
- Expand розмовна vs літературна comparison with table

**Терміни словотвору (+105 words):**
- Each morpheme type (корінь, префікс, суфікс, основа, закінчення) needs examples
- Add visual morpheme breakdown

**Практика: Аналіз правил (+229 words):**
- Add 2-3 authentic grammar rule excerpts for students to decode
- Add step-by-step analysis walkthrough

**Діалоги: Обговорення правил (+242 words):**
- Must have 6 distinct mini-dialogues
- Each dialogue: 80-100 words, realistic student/teacher or student/student setting
- Cover different module topics (instruction verbs, style, word formation)

**Підсумок (+115 words):**
- Add 4-6 self-check questions (Перевірте себе)
- Add brief metalanguage glossary recap

### Language Rules (SAME as Phase 2)

- 80% Ukrainian, English only in tip/note callouts
- No English inside Ukrainian sentences
- No Russianisms (кушати→їсти, приймати участь→брати участь)
- Ukrainian angular quotes «...» (not straight quotes)
- Only vocabulary from plan's vocabulary_hints

## Output Format

> **Content outside delimiters is discarded by extraction.**

Return the COMPLETE expanded content:

```
===CONTENT_START===
{entire module content, not just the changed parts}
===CONTENT_END===
```

After the content:

```
===WORD_COUNTS===
Section "name": {count} words
...
Total: {total} words (target: 4000)
===WORD_COUNTS===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Phase 4 Fix: Content Expansion
**Step**: {what you were doing}
**Friction Type**: NONE | ...
**Raw Error**: {error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT change the H2 structure (section names must match meta exactly)
- Do NOT add new vocabulary not in the plan
- Do NOT generate activities
- Do NOT remove existing good content — only ADD to it
- Do NOT use straight quotes "..." — always «...»
