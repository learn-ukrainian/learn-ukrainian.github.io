# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-041
level: C1
sequence: 41
slug: skladnosuriadne-rechennia
version: '2.0'
title: Складносурядне речення
subtitle: Compound Sentences
content_outline:
- section: 'Вступ: просте vs складне речення'
  words: 500
  points:
  - 'Повторення структури простого речення: граматична основа, другорядні члени, однорідні члени'
  - 'Визначення складного речення: два або більше граматичних основ, типи складних речень (сурядне, підрядне, безсполучникове)'
  - 'Складносурядне vs складнопідрядне: рівноправний зв''язок (сурядність) проти підпорядкування (підрядність)'
- section: Єднальні сполучники
  words: 800
  points:
  - 'Сполучники і, та, й, також, ні...ні: правила вибору та стилістичні нюанси (і після приголосного, й після голосного, та
    як стилістичний варіант)'
  - 'Семантичні відношення: одночасність (І сонце світило, і вітер дмухав), послідовність (Він увійшов, і всі замовкли), наслідок
    (Почався дощ, і ми повернулися)'
  - 'Пунктуація: кома перед єднальним сполучником у складносурядному реченні, відсутність коми при спільному другорядному
    членові'
- section: Протиставні сполучники
  words: 800
  points:
  - 'Сполучники а, але, проте, зате, однак: семантичні відтінки кожного — а (зіставлення), але (протиставлення), проте/однак
    (допустовість), зате (компенсація)'
  - 'Стилістичний вибір між близькозначними сполучниками: але (нейтральне) vs проте (книжне) vs однак (офіційне) vs зате (розмовне)'
  - 'Позиція сполучника та інтонаційне оформлення: однак та проте можуть стояти не на початку другої частини'
- section: Розділові сполучники
  words: 600
  points:
  - 'Сполучники або, чи, то...то: альтернатива (Підеш ти, або піду я), роз''єднання (Чи дощ, чи сонце), чергування (То блискавка
    спалахне, то грім загуркотить)'
  - 'Стилістичні відмінності: або (нейтральне), чи (більш книжне, також для питань), то...то (експресивне чергування)'
  - 'Регістрова варіація: вживання розділових сполучників у різних функціональних стилях'
- section: Пунктуація у складносурядному реченні
  words: 700
  points:
  - 'Основне правило: кома перед сполучником, що з''єднує частини складносурядного речення'
  - 'Винятки: відсутність коми при спільному другорядному членові, спільному вставному слові, спільному підрядному реченні'
  - 'Тире замість коми: вживання тире для передачі раптовості, несподіваності, різкої зміни подій (Блискавка спалахнула —
    і все затихло)'
- section: 'Практика: конструювання та трансформація'
  words: 600
  points:
  - Побудова складносурядних речень із заданими сполучниками та семантичними відношеннями
  - 'Трансформація: перетворення простих речень на складносурядні та навпаки, заміна сполучників зі зміною значення'
  - 'Визначення семантики сполучника в контексті: єднальний, протиставний чи розділовий зв''язок'
focus: grammar
pedagogy: PPP
objectives:
- Classify compound sentence conjunctions by semantic type
- Apply punctuation rules for compound sentences including exceptions
- Select stylistically appropriate conjunctions for different registers
- Transform simple sentences into compound and vice versa
grammar:
- Compound sentence structure and conjunction types
- Coordinative conjunctions (єднальні, протиставні, розділові)
- Punctuation rules and exceptions for compound sentences
phase: C1.4 [Complex Sentences]
persona:
  voice: Senior Specialist
  role: Синтаксист-практик
word_target: 4000
vocabulary_hints:
  required:
  - складносурядне речення (compound sentence) — будова складносурядного речення, частини складносурядного речення; Core syntactic
    term
  - сполучник (conjunction) — сурядний сполучник, підрядний сполучник; Fundamental grammar concept
  - єднальний (copulative/additive) — єднальний сполучник, єднальний зв'язок; Conjunction subtype classification
  - протиставний (adversative) — протиставний сполучник, протиставне значення; Conjunction subtype classification
  - розділовий (disjunctive) — розділовий сполучник, розділові відношення; Conjunction subtype classification
  recommended:
  - рівноправний зв'язок (coordinate relation) — both clauses are syntactically equal
  - граматична основа (grammatical base) — підмет + присудок, core of each clause
  - сурядність (coordination) — syntactic equality between sentence parts
activity_hints:
- type: fill-in
  focus: selecting correct conjunction and punctuation
  items: 15
- type: error-correction
  focus: punctuation errors in compound sentences
  items: 15
- type: quiz
  focus: conjunction classification and semantic relations
  items: 15
- type: match-up
  focus: matching conjunctions to semantic relationships
  items: 10
prerequisites:
- checkpoint-movoznavstvo
connects_to:
- skladnopidriadne-oznachalne-zyasuvalne
register: літературний

```

**Level constraints quick-ref:**

```
# C1 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Full Ukrainian immersion. No English except technical terminology. Sentences max 35 words.`, etc.

## Grammar Scope

No grammar restrictions. Full literary Ukrainian. No sentence length limit.

## Immersion (100% Ukrainian)

Full Ukrainian immersion. All content — grammar explanations, narratives, dialogues,
cultural content, analyses, literary critiques, activity instructions, tips — in Ukrainian.

English ONLY in vocabulary table translations (YAML).

No Language Link boxes at C1 — students learned all grammar terminology by B1.

## Module Types

| Type | Modules | Focus |
|------|---------|-------|
| Academic | M01-19 | Academic foundation |
| Professional | M21-34 | Professional communication |
| Stylistics | M36-55 | Stylistics & sociolinguistics |
| Folk Culture | M56-85 | Folk culture & arts |
| Literature | M86-105 | Literary analysis |
| Checkpoint | M20,35,55,85,105,106 | Review + assessment |

> Biography content is in separate **BIO** track.

## Content-Heavy Modules (Folk/Literature M56+)

**Golden Rule:** "Can the learner answer without reading the Ukrainian text?"
- If YES → rewrite (tests content recall, not language)
- If NO → keep (tests Ukrainian comprehension)

Forbidden activity patterns: "У якому році...", "Хто був...", "Що символізує..." (without text reference)
Required patterns: "Згідно з текстом...", "У тексті модуля автор...", "Яку стилістичну функцію..."

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `C1` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Складносурядне речення** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Складносурядне речення

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
