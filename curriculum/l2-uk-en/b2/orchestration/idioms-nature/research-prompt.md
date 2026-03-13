# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-062
level: B2
sequence: 62
slug: idioms-nature
version: '2.0'
title: 'Фразеологізми: Природа (Вода, Вогонь, Земля, Вітер)'
subtitle: 'Nature Idioms in Ukrainian'
focus: phraseology
pedagogy: CBI
phase: B2.6
word_target: 4000
objectives:
- Вивчити 8 фундаментальних фразеологізмів про чотири стихії
- Розуміти значення метафор випробування, ризику та правди
- Вміти використовувати природні образи для опису складних життєвих ситуацій
content_outline:
- section: 'Вступ: Чотири стихії в українському світогляді (Introduction: Four elements in the Ukrainian worldview)'
  words: 600
  points:
  - 'Standard §4.4.1.2: Introduction to the metaphorical reimagining of nature (rains go, sun sets) as a base for idiomatic
    thinking.'
  - 'Cultural Hook: Elements as spiritual entities; the sacredness of Earth (''Земля-годувальниця'') and the cleansing vs
    destructive power of Water.'
  - 'Myth-buster: Discussing ''Не плюй у криницю'' (Don''t spit in the well) as a cultural anchor for respect towards natural
    elements.'
- section: 'Вода та вогонь: Випробування та терпіння (Water and Fire: Trials and patience)'
  words: 900
  points:
  - 'Analyzing ''Пройти вогонь і воду'' (and ''і мідні труби''): The tactile image of complete initiation and life experience.'
  - 'Visual imagery of ''Вода камінь точить'' (Standard §2.2): Practical use of idioms to express persistence and long-term
    effort.'
  - 'Learner error drill: Instrumental case in ''Гратися з вогнем'' vs Accusative in ''Підливати масла у вогонь'' to prevent
    case confusion after nature verbs.'
  - 'Tactile comparison: ''Носити воду решетом'' (carrying water in a sieve) vs ''Товкти воду в ступі'' as visual metaphors
    for futility.'
- section: 'Земля та вітер: Сором, дух та відповідальність (Earth and Wind: Shame, spirit, and responsibility)'
  words: 900
  points:
  - 'Learner error: Distinguishing between Perfective ''провалитися крізь землю'' (the resultative wish to disappear) and
    Imperfective ''провалюватися'' (process).'
  - 'Register shift: Introducing ''Як земля носить'' as a high-frequency emotional expression for indignation (alternative
    to the literal ''Земля тримає'').'
  - 'Moral metaphors: ''Вітер у голові'' (character trait) vs ''Кидати слова на вітер'' (lack of responsibility in communication).'
  - 'Cultural Hook: Wind as the carrier of spirits; explaining ''Звідки вітер віє'' as a tool for identifying the source of
    hidden trouble or influence.'
- section: Лінгвістичний аналіз та типові пастки (Linguistic analysis and typical traps)
  words: 800
  points:
  - 'Translation trap: Comparison of ''To beat the air'' (Eng) vs ''Носити воду решетом'' (Ukr) to highlight specific cultural
    imagery.'
  - 'Stylistic analysis (Standard §4.4.1.2): Identifying why these idioms fit conversational and publicistic styles but are
    avoided in official-business register.'
  - 'Structural variations: Discussing how ''Підливати масла у вогонь'' can vary (у багаття) while maintaining its core semantic
    impact.'
- section: 'Практика: Карпатський провідник та публіцистика (Practice: Carpathian Guide and publicism)'
  words: 800
  points:
  - 'Production task (Persona): Writing a narrative as a ''Carpathian Guide'' using elements to describe a difficult journey
    through life.'
  - 'Standard §2.2: Simulating a social or political critique using ''кидати слова на вітер'' to demonstrate idiomatic competence
    in public speaking.'
  - 'Cross-reference: Connecting element-based idioms to M45-46 (Proverbs) to see how folk wisdom shapes modern figurative
    language.'
vocabulary_hints:
  required:
  - фразеологізм (idiom) — вживати фразеологізм, влучний фразеологізм; core term for B2
  - вираз (expression) — стійкий вираз, розмовний вираз; used for both literal and figurative phrases
  - значення (meaning) — переносне значення (figurative), буквальне значення (literal); crucial for idiom analysis
  - контекст (context) — залежно від контексту, вирвати з контексту; Standard §2.2 requirement
  - Пройти вогонь і воду (to go through fire and water) — description of a very experienced person; high frequency
  recommended:
  - переносне значення (figurative meaning) — key for understanding the transition from nature to human traits
  - стилістичне забарвлення (stylistic coloring) — identifying the conversational vs. publicistic register of idioms
  - вода камінь точить (patience wears away a stone) — proverb/idiom denoting patience; visual imagery
  - провалитися крізь землю (to sink into the ground) — expressing extreme shame; use in perfective aspect
  - кидати слова на вітер (to throw words to the wind) — denoting lack of responsibility; publicistic use
  - звідки вітер віє (which way the wind blows) — discovering the source of influence or trouble
activity_hints:
- type: reading
  focus: Контекстне використання
  items: 4
- type: fill-in
  focus: Практичне застосування
  items: 10
- type: true-false
  focus: Розуміння значень
  items: 8
persona:
  voice: Professional Language Coach
  role: Carpathian Guide (Карпатський провідник)
grammar:
- Fixed expressions
- Idiom structure and variation
register: varies
prerequisites:
- idioms-animals
connects_to:
- neologisms-borrowings

```

**Level constraints quick-ref:**

```
# B2 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Full Ukrainian immersion. No English except technical terminology. Sentences max 35 words.`, etc.

## Grammar Scope

**Allowed:** Full grammar including adverbial participles.
Max 35 words per Ukrainian sentence. Max 6 clauses.

## Immersion (100% Ukrainian)

All content in Ukrainian. English ONLY in vocabulary table translations (YAML).
B2 learners have internalized all grammar terminology from B1 — no English scaffolding needed.

## Module Types

| Type | Modules | Pedagogy | Structure |
|------|---------|----------|-----------|
| Grammar | M01-40 | TTT | Діагностика → Аналіз → Поглиблення → Практика → Підсумок |
| Phraseology | M41-70 | CBI | Вступ → Наратив → Аналіз → Граматика в контексті → Підсумок |
| Integration | M71-83 | CBI | Same as phraseology |
| Communication | M85-93 | CBI | Same as phraseology |
| Checkpoint | M10,30,40,70,84 | — | Review + assessment |

> History content is in separate **HIST** track.

## B2-Specific Writing Notes

- No language mixing — every sentence fully Ukrainian or fully English (English only in vocab YAML)
- Fill-in blanks use `___` format (no brackets)
- Error-correction items: the `error` field marks the wrong word, `answer` is the correct replacement

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `B2` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Фразеологізми: Природа (Вода, Вогонь, Земля, Вітер)** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Фразеологізми: Природа (Вода, Вогонь, Земля, Вітер)

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
