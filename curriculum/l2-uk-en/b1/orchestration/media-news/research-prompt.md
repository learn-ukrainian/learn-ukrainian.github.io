# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-070
level: B1
sequence: 70
slug: media-news
version: '2.0'
title: Медіа та новини
subtitle: Media and News
focus: vocabulary
pedagogy: PPP
phase: B1.5 [Vocabulary Expansion I]
word_target: 4000
objectives:
- Learner can use 30 media and journalism vocabulary words in context
- Learner can distinguish between types of media content
- Learner can form natural collocations with media vocabulary
- Learner can discuss news and current events fluently
content_outline:
- section: Вступ (Introduction)
  words: 600
  points:
  - 'Overview of the Ukrainian media landscape aligned with State Standard §3.4: press, radio, television, and internet as
    informational leisure.'
  - 'Historical cultural hook: The 1924 Kharkiv radio launch with the iconic phrase «Алло, алло, алло! Говорить Харків!» marking
    the start of broadcasting.'
  - 'Modern context: The 2017 creation of Suspilne (Public Broadcasting) as a reform toward independent, non-oligarchic media
    in Ukraine.'
- section: 'Презентація: Джерела та Формати (Presentation: Sources and Formats)'
  words: 1000
  points:
  - 'Categorization of media: traditional (газети, ТБ) vs. digital (Telegram-канали, подкасти) reflecting modern Ukrainian
    reality.'
  - 'Professional vocabulary: roles in the editorial office (редакція), including specialized journalists (військовий/спортивний
    журналіст) and investigative reporting.'
  - 'Concept introduction: «медіаграмотність» (media literacy) and the importance of identifying reliable sources (джерела
    інформації).'
- section: Лексика та Культура мовлення (Vocabulary and Speech Culture)
  words: 1100
  points:
  - 'Collocation mastery: forming natural pairs with «новини» (свіжі, термінові) and «стаття» (аналітична, автор статті).'
  - 'Learner error correction: drill to distinguish between «транслювати» (to broadcast) and «перекладати» (to translate)
    to avoid semantic confusion.'
  - 'Language purity drill: identifying and replacing Russianisms like «приймати участь» (use «брати участь») and «піднімати
    питання» (use «порушувати питання»).'
  - 'Grammar focus: mastering the case government of «повідомляти» — Accusative for the fact (повідомити новину) vs. Dative
    for the person (повідомити друзям).'
- section: 'Практика: Аналіз та Дискусія (Practice: Analysis and Discussion)'
  words: 800
  points:
  - 'Register differentiation: analyzing formal news reports (passive constructions, formal lexis) vs. informal blog/podcast
    discussion styles.'
  - 'Reading activity: scanning a news feed (стрічка новин) for key events and practicing fact-checking terminology.'
  - 'Discussion: media consumption habits as part of leisure (дозвілля) and the role of ZMI (ЗМІ) in modern society.'
- section: Підсумок (Summary)
  words: 500
  points:
  - Review of high-frequency media terminology (ЗМІ, редакція, висвітлювати, оприлюднювати) and their typical collocations.
  - 'Final synthesis: forming opinions on news items using B1-level reporting verbs and corrected phrases.'
vocabulary_hints:
  required:
  - новини (news) — свіжі/останні/термінові новини, стрічка новин, випуск новин; high frequency media term
  - стаття (article) — аналітична/наукова стаття, автор статті, публікувати статтю; essential for press analysis
  - журналіст (journalist) — військовий/спортивний журналіст, журналістське розслідування, працювати журналістом
  - ЗМІ (media) — засоби масової інформації; high frequency formal term for mass media
  - 'повідомляти (to report) — grammar: + Accusative (fact/news), + Dative (person/audience); also «повідомляти про» + Acc'
  - висвітлювати (to cover/highlight) — висвітлювати події, висвітлювати проблему; key journalistic verb
  - телебачення (television) — дивитися телебачення, працювати на телебаченні
  - газета (newspaper) — читати газету, свіжий номер газети
  - репортаж (report) — вести репортаж з місця подій, цікавий репортаж
  recommended:
  - редакція (editorial office) — працювати в редакції, редакційна політика; professional setting
  - 'трансляція (broadcast) — пряма трансляція, вести трансляцію; note: do not confuse with translation'
  - подкаст (podcast) — слухати подкаст, автор подкасту; modern digital news source
  - медіаграмотність (media literacy) — навички медіаграмотності; critical B1 concept
  - оприлюднювати (to publish/release) — оприлюднювати інформацію, оприлюднювати результати; formal register
  - 'брати участь (to participate) — drill: use instead of Russianism «приймати участь»'
  - 'порушувати питання (to raise an issue) — drill: use instead of Russianism «піднімати питання»'
activity_hints:
- type: match-up
  focus: Media noun phrases
  items: 25
- type: fill-in
  focus: Complete media sentences
  items: 20
- type: match-up
  focus: Match media terms
  items: 15
- type: quiz
  focus: Discuss current events
  items: 10
connects_to:
- b1-71 (Суспільство та політика)
prerequisites:
- b1-69 (Опис змін)
persona:
  voice: Senior Language & Culture Specialist
  role: Investigative Journalist
grammar:
- Media vocabulary collocations
- Journalistic expressions
- Reporting verb patterns
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

Research **Медіа та новини** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Медіа та новини

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
