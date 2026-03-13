# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-077
level: B1
sequence: 77
slug: business-basics
version: '2.0'
title: Основи бізнесу
subtitle: Business Basics
focus: vocabulary
pedagogy: PPP
phase: B1.6 [Vocabulary Expansion II]
word_target: 4000
objectives:
- Learner can use 30 business vocabulary words in context
- Learner can distinguish between similar business terms (компанія/фірма/підприємство)
- Learner can form natural collocations with business nouns
- Learner can discuss basic business topics fluently
content_outline:
- section: Вступ та історія (Introduction & History)
  words: 600
  points:
  - 'Historical ethical entrepreneurship: The Simirenko family legacy as sugar magnates who funded the 1860 edition of Taras
    Shevchenko''s ''Kobzar'' when state support failed.'
  - 'The Tereshchenko dynasty''s philanthropy: Establishing a model where 80% of profits went to hospitals and universities
    (KPI) under the motto ''Striving for public benefit''.'
  - Introduction to State Standard B1 competencies (§3.9, §3.12) regarding work, employment, and financial services as the
    foundation for modern professional life.
- section: Структури та формати бізнесу (Business Structures & Formats)
  words: 800
  points:
  - 'Distinguishing lexical nuances: ''компанія'' (general/IT context), ''фірма'' (smaller or more colloquial), and ''підприємство''
    (formal industrial or state-owned unit).'
  - 'Modern Ukrainian business landscape: Introduction of ''ФОП'' (Фізична особа-підприємець) as the standard legal format
    for small businesses and the thriving IT sector.'
  - 'Core vocabulary presentation: ''заснувати компанію'', ''власний бізнес'', ''державне підприємство'' with focus on correct
    register usage.'
- section: Професійна комунікація та етика (Professional Communication & Ethics)
  words: 1000
  points:
  - 'Learner Error Correction (Lexical Calques): Drill the distinction between ''скасувати'' (cancel/abolish, preferred formal
    register) and ''відмінити'' (also standard for cancelling, but ''скасувати'' is more common in business contexts).'
  - 'Register Awareness: ''Правильне рішення'' (correct/accurate) is the standard neutral form for business contexts;
    ''вірне рішення'' is also acceptable in modern Ukrainian but has a slightly informal nuance.'
  - 'Formal Correspondence Standards: Mandatory use of the Vocative case in address (e.g., ''Шановний Іване'', ''Пане директоре'')
    to avoid the common error of using the Nominative.'
  - 'Professional Time Expressions: Correcting the common ''на протязі року'' (which means in a draft/breeze) to the professional
    ''протягом року'' (during the year).'
- section: Офіційне працевлаштування та послуги (Official Employment & Services)
  words: 800
  points:
  - 'State Standard §3.9 Application: Vocabulary for official employment, contracts (''укласти угоду''), salary (''зарплатня''),
    and working hours (''обідня перерва'').'
  - 'State Standard §3.12 Services: Navigating interactions with banks, insurance companies (''страхова компанія''), and postal
    services in a business capacity.'
  - 'Emphasis on Active Agency: Promoting the natural Ukrainian preference for active constructions (''Ми підписали угоду'')
    over passive translations of ''The agreement was signed''.'
- section: Інвестиції, прибуток та підсумок (Investment, Profit & Summary)
  words: 800
  points:
  - 'Financial concepts: Discussion of ''чистий прибуток'' (net profit), ''податок на прибуток'' (income tax), and strategies
    for ''залучати інвестиції'' (attracting investment).'
  - 'Risk Management: Discussing ''збитки'' (losses) and ''вигідна угода'' (profitable deal) within the context of market
    strategy and ''маркетинг''.'
  - 'Final synthesis: Review of professional register expressions and the cultural values of ''ethical entrepreneurship''
    as a bridge to B2 Professional Track modules.'
vocabulary_hints:
  required:
  - компанія (company) — IT-компанія, страхова компанія, заснувати компанію; high frequency in modern sectors
  - підприємство (enterprise) — державне підприємство, промислове підприємство; formal/industrial unit
  - бізнес (business) — малий бізнес, вести бізнес, бізнес-план; general term for commercial activity
  - прибуток (profit) — чистий прибуток, отримувати прибуток, податок на прибуток; medium-high frequency
  - інвестиція (investment) — залучати інвестиції, іноземні інвестиції, повернення інвестицій
  - клієнт (client) — постійний клієнт, залучати клієнтів, обслуговування клієнтів; high frequency
  - продаж (sale) — відділ продажу, збільшити продажі; note the singular/plural usage in business
  - керувати (to manage) — керувати бізнесом, керувати відділом; requires Instrumental case
  recommended:
  - підприємець (entrepreneur) — приватний підприємець (ФОП), успішний підприємець; key cultural concept
  - маркетинг (marketing) — відділ маркетингу, стратегія маркетингу
  - постачальник (supplier) — надійний постачальник, змінити постачальника
  - збитки (losses) — зазнати збитків, покрити збитки; crucial for risk discussion
  - угода (agreement/deal) — укласти угоду, підписати угоду, вигідна угода; medium-high frequency
  - скасувати (to cancel) — скасувати зустріч, скасувати рейс; preferred in formal/business register (відмінити also standard)
  - правильний (correct) — правильне рішення, правильний вибір; standard neutral form for business
  - протягом (during) — протягом року, протягом тижня; professional time marker
activity_hints:
- type: match-up
  focus: Business noun phrases
  items: 25
- type: fill-in
  focus: Complete business sentences
  items: 20
- type: match-up
  focus: Match terms to definitions
  items: 15
- type: fill-in
  focus: Business scenarios
  items: 10
connects_to:
- b1-78 (Подорожі та географія)
prerequisites:
- b1-76 (Стосунки та зв'язки)
persona:
  voice: Senior Language & Culture Specialist
  role: Kyiv Entrepreneur
grammar:
- Business vocabulary collocations
- Professional register expressions
- Formal business communication patterns
register: розмовний

```

**Level constraints quick-ref:**

```
# B1 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Full Ukrainian immersion. Grammar explained IN Ukrainian. English only for disambiguation of false friends. Sentences max 30 words.`, etc.

## Grammar Scope

**Allowed:** All grammar constructions. Participles. Complex subordinate clauses.
Max 30 words per Ukrainian sentence. Max 4 clauses.

## Immersion Strategy (B1)

| Phase | Modules | Immersion | Notes |
|-------|---------|-----------|-------|
| B1.0 (Bridge) | M01-05 | Mixed | Teach grammar metalanguage; English scaffolding for abstract concepts |
| B1.1+ (Core) | M06-92 | **100%** | Full Ukrainian. English ONLY in vocabulary table translations |

**B1.0 Bridge modules:** English grammar term explanations allowed as transition from A2.

**B1.1+ Hard rule:** No English in prose, titles, callouts, or explanations.
No English in parentheses to clarify Ukrainian concepts:
- Wrong: **поки** — дія на тлі іншої дії (While she was cooking...)
- Right: **поки** — дія на тлі іншої дії, тобто одночасні процеси

## B1-Specific Writing Notes

- Content quality: equal treatment for all items in a category (same depth, same format)
- Example variety: mix standalone, table, inline, dialogue — no 5+ consecutive examples in same format
- Tables must have narrative context (2+ sentences before and after)
- Parallel sections use identical internal structure

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `B1` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Основи бізнесу** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

### Your RAG Tools

| Tool | When to use |
|------|-------------|
| `search_text` | Find how this topic is taught in Ukrainian textbooks |
| `verify_words` | Check vocabulary exists in VESUM dictionary |
| `query_grac` mode=`frequency` | Get word frequency data |
| `query_wikipedia` mode=`summary` | Quick fact-check for cultural hooks |

### Research Requirements

1. **State Standard Reference**: Look up the §section in `state-standard-2024-mapping.yaml`, then read ONLY that section from `UKRAINIAN-STATE-STANDARD-2024.txt`. Quote the relevant requirement.
2. **Vocabulary Frequency**: Use `query_grac` (mode=`frequency`) for key vocabulary items. Do NOT rely on memory alone.
3. **Cultural Hook**: Use `query_wikipedia` to find 1-2 verified cultural facts to anchor the lesson.
4. **Cross-References**: Note which modules this builds on and prepares for (check the plan's `connects_to` field).
5. **Common Errors**: Identify 2-3 common learner mistakes for this grammar point/topic.

### Decolonized Framing

When researching, frame Ukrainian independently — **never as a derivative or variant of Russian:**
- Describe Ukrainian features positively ("Ukrainian has...", "Ukrainian uses...")
- Do NOT use Russian as the baseline for comparisons ("Unlike Russian...", "Different from Russian...")
- If comparing language systems is useful, use non-Russian languages (Polish, Portuguese, etc.)
- Note how topics have been historically misframed by Russian/Soviet sources and provide the Ukrainian-centric perspective

### Research Output Cap
Keep research notes under **1500 words**. Focus on density: facts, dates, quotes, tables — not prose.

### Additional for Core B (B1.6+, B2, C1, C2, PRO)

- Domain-specific vocabulary collocations from professional glossaries (PRO tracks)
- Stylistic/dialectal features from academic sources (C2)
- Register distinctions (formal vs. informal usage)

## Downstream Audit Gates (Phase B content will be checked for)

Plan your outline knowing that Phase B content must pass these gates:
- **Word count**: minimum **4000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Russianisms**: ensure vocabulary_hints and examples avoid banned words (кушати→їсти, получати→отримувати)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Основи бізнесу

## State Standard Reference
§{section_number}: "{quoted requirement}"
Alignment: {how this module addresses the standard}

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| ...  | ...               | ...              |

## Cultural Hooks
1. {Verified fact with source}
2. {Verified fact with source}

## Common Learner Errors
1. {Error pattern} → {Correct form} — {Why it happens}
2. ...

## Cross-References
- Builds on: {module slugs}
- Prepares for: {module slugs}

## Multimedia Resources
(If you naturally encountered relevant Ukrainian-language YouTube videos or audio resources during your web research, note them here. Do NOT search specifically for videos — the discover phase handles that. Maximum 3 entries.)
- {Channel — Title — URL — 1-sentence relevance note}
- (none encountered)

## Notes for Content Writing
- {Any additional observations for Phase B}

===RESEARCH_END===
```

## Friction Report (MANDATORY)

After both output blocks, include:

```
===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | STATE_STANDARD_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT fabricate State Standard references — if you can't find the exact §, say so
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
