# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: folk-024
level: FOLK
sequence: 24
slug: narodni-anekdoty
version: '2.0'
title: 'Народні анекдоти та небилиці: Сміхова культура'
subtitle: 'Folk Anecdotes and Tall Tales: Laughter Culture'
focus: Folk humor, tall tales, comedic worldview, carnival inversion
phase: FOLK.5
word_target: 5000
content_outline:
- section: Вступ
  points:
  - Laughter culture (сміхова культура) as essential folk worldview
  - Анекдот vs небилиця — joke vs tall tale
  words: 750
- section: Народний анекдот
  points:
  - Social types as targets — пан, піп, москаль, циган
  - Punchline structure, brevity, stereotyping as social commentary
  words: 900
- section: Небилиці та нісенітниці
  points:
  - The world upside down — fish climbing trees, dead men dancing
  - Carnival logic — inversion of natural order for comic effect
  words: 850
- section: Сміх як зброя
  points:
  - Humor against oppression — laughing at the powerful
  - Москаль in folk humor — the imperial soldier mocked
  words: 850
- section: Текстовий аналіз
  points:
  - Close reading of selected anecdotes and tall tales
  - Colloquial language, dialectalisms, performance markers
  words: 850
- section: Підсумок
  points:
  - Folk humor as resistance and resilience
  - Vocabulary table
  words: 800
vocabulary_hints:
- анекдот
- небилиця
- нісенітниця
- сміхова культура
- карнавал
- пародія
- сатира
- дотепність
activity_hints:
- type: reading
  focus: Folk humor text analysis
  items: 1
- type: vocabulary
  focus: Humor and narrative terminology
  items: 1
- type: quiz
  focus: Humor types and social targets
  items: 1
persona:
  voice: Senior Folklorist
  role: Humor Studies Scholar
connects_to:
- zahadky
- prykazky-ta-pryslivia
objectives:
- Аналізувати народні анекдоти як інструмент соціальної критики
- Розуміти карнавальну логіку небилиць і нісенітниць
- Демонструвати вміння інтерпретувати сміхову культуру як форму спротиву

```

**Level constraints quick-ref:**

```
# FOLK Quick Reference — Українська усна літературна традиція

> **Track Type:** Oral Literature / Folklore Studies
> **Period:** Pre-Christian era → XVIII century
> **Modules:** 27
> **Immersion:** 100% Ukrainian

---

## Phases Overview

| Phase | Modules | Name | Focus |
|-------|---------|------|-------|
| FOLK.1 | 01-07 | Обрядова поезія | Ritual songs: колядки, веснянки, русальні, купальські, обжинкові, весільні, голосіння |
| FOLK.2 | 08-14 | Казки, легенди, балади | Fairy tales (чарівні, про тварин, побутові), legends, ballads, chumak songs |
| FOLK.3 | 15-18 | Епос | Heroic tradition: билини київського циклу, богатирі |
| FOLK.4 | 19-23 | Думи та кобзарство | Cossack dumas (невільницькі, лицарські, побутові), kobzar tradition |
| FOLK.5 | 24-27 | Малі жанри | Proverbs, riddles, folk humor, family lyrics, kolomyiky |

---

## Key Concepts

- **Oral ≠ primitive**: The duma tradition is as sophisticated as any written epic
- **Authorless**: These are collective creations — no individual author to credit
- **Living tradition**: Many forms survive in modern ritual (weddings, Christmas)
- **Decolonization**: Imperial scholarship classified Ukrainian folklore as "Little Russian" — it is an independent European tradition

## Primary Scholarly Sources

- **Грушевський** — «Історія української літератури» (Том 1: фольклор, Том 4: думи)
- **Крип'якевич** — «Історія української культури» (обрядова поезія)
- **Чижевський** — «Історія української літератури» (oral tradition sections)

## Key Vocabulary Domains

- Ritual/calendar: колядка, щедрівка, веснянка, купальська, обжинкова
- Fairy tale: казка, чарівний, тотемізм, ініціація, архетип
- Epic: билина, богатир, дума, речитатив, кобзар, лірник
- Performance: лебійська мова, цех, бандура, кобза, ліра
- Micro-genres: приказка, прислів'я, загадка, коломийка, небилиця

## Decolonization Angle

- Билини — claimed by Russia as "Russian epic." Hrushevsky proved their Kyivan origin.
- Думи — uniquely Ukrainian genre with NO parallel in Russian tradition.
- Кобзарство — systematically destroyed by Soviet regime (1930s purges of blind kobzars).
- Народна пісня — was the vehicle that preserved Ukrainian language during centuries of oppression.

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `FOLK` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Народні анекдоти та небилиці: Сміхова культура** for the **FOLK** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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
- **Word count**: minimum **1200** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Russianisms**: ensure vocabulary_hints and examples avoid banned words (кушати→їсти, получати→отримувати)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Народні анекдоти та небилиці: Сміхова культура

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
