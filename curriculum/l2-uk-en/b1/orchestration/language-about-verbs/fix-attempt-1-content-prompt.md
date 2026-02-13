# Phase Fix-Content: Content-Only Fixes

> **You are Gemini, executing a targeted content fix.**
> **Your ONLY task: Fix the CONTENT file based on audit errors below.**
> **Do NOT output activities or vocabulary — only the fixed content.**

## Your Input

Read these files from disk:

**Current content** (the file you are fixing):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/language-about-verbs.md
```

**Plan file** (source of truth for scope):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/b1/language-about-verbs.yaml
```

**Research notes** (reference for factual accuracy):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/research/language-about-verbs-research.md
```

## Audit Errors to Fix

The following audit errors were found in the content. Fix ALL of them:

### Fix 1: Break 4 long sentences (max 25 words for B1)

These sentences exceed the 25-word limit and MUST be split into shorter sentences:

**Sentence A** (~27 words, in section "Вступ"):
"На рівні В1, коли ви починаєте працювати зі складнішими граматичними структурами, такими як система виду дієслова чи його часові форми, здатність розуміти пояснення українською мовою стає критично важливою."
→ Split into 2 shorter sentences.

**Sentence B** (~26 words, in section "Додаткові дієслівні терміни"):
"Ці терміни дозволяють детальніше аналізувати структуру речення та розуміти, хто є виконавцем дії, а хто її об'єктом, а також який характер має сама дія – реальний, бажаний чи умовний."
→ Split into 2 shorter sentences.

**Sentence C** (~32 words, in "Підсумок"):
"Ми детально розглянули ключові терміни, такі як вид, час, спосіб та стан дієслова, навчилися розрізняти доконаний та недоконаний вид, а також розуміти концепції дії, процесу та результату, які є визначальними для правильного вживання дієслів."
→ Split into 2-3 shorter sentences.

**Sentence D** (~31 words, in "Підсумок"):
"Опанування цієї граматичної метамови є критично важливим для будь-якого студента рівня В1, оскільки це дозволяє не тільки пасивно сприймати інформацію, але й активно аналізувати її, формулювати питання та самостійно шукати відповіді в українськомовних джерелах."
→ Split into 2 shorter sentences.

### Fix 2: Add 2 cultural callouts (richness: cultural = 0, need 2)

The audit found 0 cultural callouts. Add EXACTLY 2 using the `[!cultural]` format.

**Cultural callout 1** — Add to the section "Вид дієслова: Доконаний та недоконаний":
A cultural callout about how the aspectual system reflects Ukrainian ways of perceiving action and time. Something like "Дієслівний вид у мові та культурі" — how aspect reflects whether Ukrainians foreground the process or result of an action.

**Cultural callout 2** — Add to the section "Форми дієслова: Складна та синтетична":
A cultural callout about how verb form richness in Ukrainian reflects a deep linguistic tradition. Reference Ukrainian grammarians or the tradition of Ukrainian grammar codification.

Use this exact format:
```
> [!cultural] **Title**
> Content text here. Keep it 2-4 sentences. Must relate to Ukrainian culture, history, or identity.
```

### Fix 3: Add 1 more table (richness: tables = 1, need 2)

Currently there is only 1 table (in "Концепції дії"). Add 1 more table to a different section.

**Suggested location**: Section "Часи дієслова: Теперішній, минулий, майбутній"

Create a table comparing the three tenses with columns: Час | Визначення | Приклад | Зв'язок з видом

Wrap the table with 2+ sentences of context before and after it (narrative wrapping rule).

## Rules

1. **Apply EVERY fix** — all 4 long sentences must be broken, both cultural callouts added, 1 table added
2. **Scope your changes** — only change what this Fix Plan specifies. Leave unflagged sections untouched.
3. **Preserve structure** — keep the same H2/H3 headings
4. **Preserve voice** — do not change the writing style of unflagged content
5. **Preserve immersion** — this is a 75% immersion bridge module. English equivalents appear in parentheses on first introduction only.
6. **Do NOT change word count dramatically** — the module already meets its 3000-word target. Your fixes should add ~50-100 words (callouts + table), not hundreds.

## Output Format

**CRITICAL: Output the COMPLETE fixed content between these delimiter lines.**

===CONTENT_START===
(complete fixed content markdown — ALL of it, not just changed parts)
===CONTENT_END===

**After the content, report what you changed:**

===CHANGES_START===
## Applied Fixes

1. Section "{name}": {what changed} — {which audit error}

## Fixes NOT Applied (explain why)

- {If any fix was unclear or contradictory, explain here}
===CHANGES_END===

===FRICTION_START===
**Phase**: Phase 4: Fix Content
**Step**: Breaking long sentences, adding cultural callouts and table
**Friction Type**: {type or NONE}
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {or "N/A"}
===FRICTION_END===

## Boundaries

- Do NOT output activities or vocabulary sections
- Do NOT rewrite sections that aren't flagged
- Do NOT remove any existing content
- Do NOT change the module's pedagogical approach or structure
- If you cannot apply a fix, explain why in "Fixes NOT Applied"
