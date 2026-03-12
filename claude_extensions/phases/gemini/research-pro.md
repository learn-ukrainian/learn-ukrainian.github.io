# Phase A: Research + Meta (Professional Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the professional topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
{PLAN_CONTENT}
```

---

## PART 1: Professional Research

Research **{TOPIC_TITLE}** for the **{TRACK}** professional track. Produce structured research notes that will drive authentic, professionally accurate content in Phase B.

### Research Requirements

1. **Sources**: Find 3+ Ukrainian-language professional/official sources. Priority order:
   - `zakon.rada.gov.ua` — Ukrainian legislation and legal norms
   - `dstu.ua`, `kharkiv.dstu.ua` — ДСТУ standards for professional language
   - `business.diia.gov.ua`, `msp.gov.ua` — official business guidance
   - Ukrainian professional publications, industry associations, university resources
   - Russian-language sources are PROHIBITED.

2. **Terminology Inventory**: Build a table of 8+ key professional terms for this topic:
   - Ukrainian standard form (as per ДСТУ/official norms)
   - Common Russified/non-standard variant used in practice (if exists)
   - English equivalent
   - Usage context (formal written / spoken / legal / technical)

3. **Language Norms**: Identify relevant ДСТУ standards or official language guidelines that apply to this professional domain. Note specific rules (e.g. ДСТУ 4163:2020 for business documents).

4. **Authentic Examples**: Collect 3+ short authentic Ukrainian professional text fragments:
   - Email phrases, document clauses, meeting formulas, report templates, etc.
   - Must be sourced from real Ukrainian professional practice (not invented)
   - Ukrainian only — no Russian examples

5. **Common Errors**: Identify 5+ language mistakes Ukrainian speakers make in this professional context:
   - Russianisms carried over from Soviet-era professional language
   - Calques from Russian professional terminology
   - Register mismatches (using colloquial forms in formal contexts)
   - With correct Ukrainian alternative for each error

6. **Engagement Hooks**: Identify 4+ hooks mapped to specific content sections:
   - `[!pro-tip]` — Professional insider tips
   - `[!language-note]` — Ukrainian vs Russified form, with explanation
   - `[!example]` — Authentic workplace example
   - `[!common-error]` — Frequent mistake with correction
   - `[!context]` — Professional/cultural context

7. **Section-Mapped Notes**: Structure your notes with headings that match the `content_outline` sections from the plan. This makes Phase B content writing mechanical.

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: {TOPIC_TITLE}

## Використані джерела
1. [Source name](URL) — brief description
2. ...
3. ...

## Термінологічна база

| Українська (норма) | Русизм/ненорма | English | Контекст вживання |
|--------------------|---------------|---------|-------------------|
| ...                | ...           | ...     | ...               |

## Мовні норми та стандарти
- ДСТУ / official norm reference: ...
- Key rule 1: ...
- Key rule 2: ...

## Аутентичні приклади
1. [Context]: «Ukrainian professional text fragment»
2. ...
3. ...

## Типові помилки
1. ❌ [wrong form] → ✅ [correct form] — explanation
2. ...
3. ...
4. ...
5. ...

## Engagement Hooks (mapped to sections)
- Section "{section_name}": [!hook_type] — description
- ...

## Відеоресурси
(Якщо під час дослідження ви натрапили на релевантні відеоматеріали — навчальні відео, вебінари, офіційні відеоінструкції з DIIA чи урядових сайтів — зазначте їх тут. НЕ шукайте відео спеціально — це робить фаза discover. Максимум 3 записи.)
- {Канал — Назва — URL — Короткий опис релевантності}
- (нічого не знайдено)

## Section-Mapped Research Notes

### {Section 1 from content_outline}
Key terminology, authentic examples, norms for this section...

### {Section 2 from content_outline}
...

===RESEARCH_END===
```

## Friction Report (MANDATORY)

After the research output block, include:

```
===FRICTION_START===
**Phase**: Phase A: Research + Meta (Professional)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | SOURCE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT skip any section from the plan's content_outline
- Do NOT use Russian-language sources
- Do NOT invent professional examples — source them from real Ukrainian practice
- Do NOT use invented ДСТУ numbers — only cite standards you can verify
- Do NOT request skills, delegate to Claude, or skip this phase
