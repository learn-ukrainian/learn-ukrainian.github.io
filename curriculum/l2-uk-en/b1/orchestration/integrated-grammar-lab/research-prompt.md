# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-054
level: B1
sequence: 54
slug: integrated-grammar-lab
version: '2.0'
title: Інтегрована граматична лабораторія
subtitle: Integrated Grammar Lab - B1.4 Synthesis
focus: grammar
pedagogy: TTT
phase: B1.6 [Participles and Advanced Grammar]
word_target: 4000
objectives:
- Learner can combine B1.4 grammar constructions in coherent texts
- Learner can distinguish between styles and registers
- Learner can edit texts for appropriate style
- Learner can flexibly switch between constructions
content_outline:
- section: 'Вступний тест: Стилістична діагностика (Initial Test: Stylistic Diagnostics)'
  words: 400
  points:
  - 'State Standard 2024 Alignment (§4.5.1): Diagnostic check on the learner''s ability to distinguish between official and
    unofficial registers.'
  - 'Initial register check: Identifying stylistic inconsistencies, such as using high-style words (''здійснити'') in casual
    contexts.'
- section: 'Пояснення: Синтез і стилістична гнучкість (Explanation: Synthesis and Stylistic Flexibility)'
  words: 600
  points:
  - 'Cultural hook: The struggle against ''kantseliaryt'' (bureaucratese) and the historical preference for active voice over
    passive constructions (e.g., ''ми розглядаємо'' vs ''питання розглядається'').'
  - 'The power of synonymy: How Ukrainian synonymic rows (e.g., ''обрій'', ''небокрай'', ''горизонт'') allow for precise calibration
    of speech registers from poetic to scientific.'
- section: 'Сценарій 1: Офіційно-діловий звіт (Scenario 1: Official Business Report)'
  words: 700
  points:
  - 'Formal register mastery: Prioritizing active agency (''Комісія ухвалила'') over the passive ambiguity often found in
    Soviet-era bureaucratic styles.'
  - 'Grammar integration: Synthesizing complex numerals and collective nouns within the framework of a formal report or proposal.'
- section: 'Сценарій 2: Неофіційна сімейна розмова (Scenario 2: Informal Family Conversation)'
  words: 700
  points:
  - 'Informal register nuances: Utilizing diminutives and rich synonyms for emotional depth without slipping into register
    mismatch (avoiding ''даний'' or ''здійснити'').'
  - 'Synthesis of diminutives and pronouns: Building natural-sounding dialogue that reflects authentic family interactions.'
- section: 'Сценарій 3: Новини та медіа (Scenario 3: News and Media)'
  words: 600
  points:
  - 'News register syntax: Implementing ellipsis and concise sentence structure for brevity and impact in headlines and bulletins
    (one-member sentences covered in dedicated module b1-51).'
  - 'Synthesizing B1.6 features: Combining aspectual nuances with the concise syntax required for modern Ukrainian journalism.'
- section: 'Практика: Лабораторія редагування (Practice: Editing Laboratory)'
  words: 600
  points:
  - 'Register transformation task: Transforming a single content item (e.g., ''Я запізнився'') into three styles: an official
    note, a friend message, and a news headline.'
  - 'Error correction drill: Identifying and fixing passive voice overuse (Learner Error: ''Книга читається учнем'' -> ''Учень
    читає книгу'') and impersonal sentence confusion.'
- section: Діалоги та текстотворення (Dialogues and Text Production)
  words: 300
  points:
  - 'Register switching exercise: Rapidly adapting tone and vocabulary in a multi-stage dialogue involving different social
    hierarchies.'
  - 'Advanced synthesis: Integrating numerals, aspect, and stylistic flexibility into coherent, paragraph-length text production.'
- section: 'Підсумок: Потрібно більше практики? (Summary: Need More Practice?)'
  words: 100
  points:
  - Final reflection on stylistic appropriateness and communicative effectiveness across B1.4 scenarios.
  - Review of core collocations for professional and social integration.
vocabulary_hints:
  required:
  - інтеграція (integration) — інтеграція в суспільство, інтеграція зусиль; середня частота, медіа/науковий контекст
  - синтез (synthesis) — синтез мистецтв, аналіз і синтез; низька частота, науковий стиль
  - стиль (style) — офіційно-діловий стиль, розмовний стиль, художній стиль; висока частота
  - регістр (register) — високий/низький регістр, перемикання регістрів; лінгвістичний термін
  - редагування (editing) — літературне редагування, редагування тексту, внести правки; середня частота
  - гнучкість (flexibility) — стилістична гнучкість, гнучкість мислення
  - перемикання (switching) — перемикання кодів/регістрів
  - зв'язність (coherence) — зв'язність тексту
  recommended:
  - послідовність (consistency) — логічна послідовність
  - доречність (appropriateness) — доречність використання, доречність стилю
  - текстотворення (text production) — навички текстотворення
  - аудиторія (audience) — цільова аудиторія
  - канцелярит (bureaucratese) — боротьба з канцеляритом; культурно значущий термін для критики бюрократичної мови
  - актив (active voice) — перевага активних конструкцій над пасивними
activity_hints:
- type: error-correction
  focus: Revise texts for style
  items: 20
- type: fill-in
  focus: Create multi-feature paragraphs
  items: 15
- type: error-correction
  focus: Fix style inconsistencies
  items: 15
- type: quiz
  focus: Choose appropriate form
  items: 20
connects_to:
- b1-55 (Checkpoint Advanced Grammar)
prerequisites:
- b1-53 (Numerals Collectives Fractions)
persona:
  voice: Senior Language & Culture Specialist
  role: Linguistic Researcher
grammar:
- 'Синтез: дієприкметники + пасив + демінутиви + числівники'
- Стилістична гнучкість (stylistic flexibility)
- Перемикання регістрів (register switching)
- Боротьба з канцеляритом (anti-bureaucratese)
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

Research **Інтегрована граматична лабораторія** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Інтегрована граматична лабораторія

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
