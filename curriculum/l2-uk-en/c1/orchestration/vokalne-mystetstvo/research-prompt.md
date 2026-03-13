# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-096
level: C1
sequence: 96
slug: vokalne-mystetstvo
version: '2.0'
title: Вокальне мистецтво
subtitle: Vocal Art
content_outline:
- section: 'Вступ: Голос як дзеркало душі (Introduction: Voice as a Mirror of the Soul)'
  words: 500
  points:
  - Поняття «кордоцентризму» (сердечності) як філософської основи української музичної культури
  - Огляд багатоголосої традиції від козацьких дум до сучасних хорових полотен
  - 'Естетичний опис вокалу: використання епітетів (оксамитовий, проникливий, дзвінкий) та метафор (тепла атмосфера) згідно
    з вимогами С1 (§4.4.3)'
- section: Хорова спадщина та «Золотий вік» (Choral Heritage and the 'Golden Age')
  words: 900
  points:
  - 'Тріумвірат «Золотого віку»: духовний вимір творчості Максима Березовського, Артема Веделя та Дмитра Бортнянського'
  - 'Національна капела «ДУМКА»: історія абревіатури (Державна українська мандрівна капела, 1919) та її просвітницька місія'
  - 'Сучасні хорові інституції: Капела Ревуцького та розвиток чоловічого хорового співу'
- section: 'Камерно-вокальний жанр: Романс (Chamber Vocal Genre: Art Song/Romance)'
  words: 800
  points:
  - 'Еволюція українського романсу: від засновника Миколи Лисенка та Якова Степового до сучасних інтерпретацій'
  - Аналіз взаємодії поетичного слова та музичної тканини в класичному романсі
  - 'Лексичний фокус: професійна термінологія для опису виконання (діапазон, тембр, колоратура, мелізматика)'
- section: Етно-хаос та фольк-ф’южн (Ethno-Chaos and Folk Fusion)
  words: 900
  points:
  - 'Гурт «ДахаБраха»: філософія стилю «етно-хаос» та глобальний прорив (NPR Tiny Desk Concert)'
  - 'Електронний фольклор: ONUKA — поєднання архаїчних інструментів та сучасного саунду'
  - 'Традиційна мелізматика в сучасному контексті: як автентичний спів стає частиною світової музичної сцени'
- section: Аналіз та вокальна школа (Analysis and Vocal School)
  words: 900
  points:
  - 'Типові помилки: розмежування значень «голос» (voice) та «голосування» (vote); правильне вживання «виконувати партію»
    замість калькованого «грати»'
  - 'Робота над стилістичним багатством: заміна примітивних оцінок (гарний, добрий) на професійні дескриптори (насичений,
    віртуозний)'
  - 'Творче завдання: написання есе-критики про розвиток української вокальної школи та її міжнародне значення'
focus: fine-arts
pedagogy: CBI
objectives:
- Learner explores the rich tradition of Ukrainian choral music.
- Learner can explain the genre of art song (romance) in Ukraine.
- Learner can discuss contemporary vocal fusion projects.
grammar:
- Professional music terminology
- Descriptive aesthetics
phase: C1.7 [Fine Arts & High Culture]
persona:
  voice: Senior Specialist
  role: Оперний критик
word_target: 4000
vocabulary_hints:
  required:
  - тембр (timbre) — оксамитовий тембр, унікальний тембр; висока частотність у мистецькому дискурсі
  - діапазон (range) — широкий діапазон, голосовий діапазон; опис вокальних можливостей
  - акапела (a cappella) — співати акапела, акапельний спів; ключовий термін хорової традиції
  - колоратура (coloratura) — колоратурне сопрано, віртуозна колоратура; технічна складність вокалу
  - мелізматика (melismatics) — багата мелізматика, народна мелізматика; орнаментика співу
  - капела (chapel/choir) — хорова капела, Національна капела «Думка»; інституційне позначення колективу
  - виконувати (to perform) — виконувати партію, виконувати романс; вживання замість помилкового «грати» щодо вокалу
  - проникливий (penetrating/soulful) — проникливий спів, проникливе виконання; естетичний епітет С1
  recommended:
  - оксамитовий (velvety) — оксамитовий голос; метафоричний епітет для опису тембру
  - кордоцентризм (cordocentrism) — музичний кордоцентризм; філософський термін для опису «сердечності» культури
  - етно-хаос (ethno-chaos) — стиль етно-хаос; самоназва жанру гурту «ДахаБраха»
  - просвітницька місія (enlightenment mission) — виконувати просвітницьку місію; контекст історії капели «ДУМКА»
prerequisites:
- operne-mystetstvo
connects_to:
- obrazotvorche-mystetstvo-1
register: літературний
activity_hints:
- type: quiz
  focus: Art terminology comprehension
  items: 12
- type: match-up
  focus: Match Хорова спадщина та «Золотий вік» examples to categories
  items: 12
- type: fill-in
  focus: Complete descriptions of artistic works
  items: 10
- type: group-sort
  focus: Classify by Романс
  items: 10
- type: reading
  focus: Analyze arts-related text
  items: 4
- type: essay-response
  focus: Write critical analysis of artistic work

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

Research **Вокальне мистецтво** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Вокальне мистецтво

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
