# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-025
level: C1
sequence: 25
slug: political-system
version: '2.0'
title: Політична система України
subtitle: 'Introduction: State System and Constitution'
content_outline:
- section: 'Вступ: Державний устрій та Конституція (Introduction: State System and Constitution)'
  words: 600
  points:
  - 'Огляд внутрішньої політики згідно з державним стандартом (§3.8): поняття державного устрою, територіальної цілісності
    та конституційних засад України.'
  - 'Cultural Hook: Конституція Пилипа Орлика (1710) — розгляд історичної тяглості українського державотворення та закладення
    основ поділу влади.'
  - 'Конституція України (1996): аналіз структури документа та процедури внесення змін у контексті демократичних реформ.'
- section: Законодавча влада та Парламентаризм (Legislative Power and Parliamentarism)
  words: 1000
  points:
  - 'Верховна Рада України: структура парламенту, роль народних депутатів, робота фракцій та комітетів.'
  - 'Cultural Hook: Поняття ''монобільшості'' (2019) — аналіз унікального політичного прецеденту в історії незалежної України
    та його наслідків для законодавчого процесу.'
  - 'Законодавчий процес: етапи від реєстрації законопроєкту до його ухвалення ''в цілому'' та підписання президентом.'
  - 'Learner Error: Стилістична диференціація між ''ухвалювати закон'' (офіційний стандарт) та розмовним ''приймати закон''.'
- section: Виконавча влада та інститут президентства (Executive Power and the Institution of Presidency)
  words: 900
  points:
  - 'Президент України: правовий статус гаранта Конституції, повноваження у сфері національної безпеки та зовнішньої політики.'
  - 'Кабінет Міністрів України: формування урядової коаліції, призначення міністрів та механізм відставки уряду.'
  - 'Взаємодія між гілками влади: система стримувань і противаг, право вето президента та процедура імпічменту.'
- section: Судова система та Децентралізація (Judicial System and Decentralization)
  words: 800
  points:
  - 'Структура судової влади: роль Конституційного Суду та Верховного Суду у забезпеченні верховенства права.'
  - 'Реформа децентралізації: створення об''єднаних територіальних громад (ОТГ) як ключовий етап модернізації управління на
    місцях.'
  - 'Місцеве самоврядування: повноваження громад, місцеві вибори та питання фінансової децентралізації.'
- section: Практичний аналіз та мовна компетенція (Practical Analysis and Language Competency)
  words: 700
  points:
  - 'Аналіз політичного дискурсу: робота з новинами про державні реформи, виокремлення ключових меседжів урядових програм.'
  - 'Learner Error Drill: Конструкція ''голосувати за кандидата'' (Знахідний відмінок) — виправлення типових кальок з іноземних
    мов.'
  - 'Термінологічна точність: розмежування значень ''обирати'' (на виборну посаду) та ''вибирати'' (загальний вибір), а також
    використання офіційної колоквіалістики.'
vocabulary_hints:
  required:
  - 'конституція (constitution) — ухвалити конституцію, гарант конституції, конституційні права; частотність: висока (офіц.-діл.)'
  - 'президент (president) — повноваження президента, інавгурація президента, указ президента; частотність: висока'
  - 'парламент (parliament) — розпустити парламент, скликання парламенту, парламентська більшість; частотність: середня'
  - 'уряд (government) — сформувати уряд, відставка уряду, урядова програма; частотність: висока'
  - 'законопроєкт (bill) — зареєструвати законопроєкт, ветувати законопроєкт, розгляд законопроєкту; частотність: висока'
  - 'депутат (deputy) — народний депутат, депутатська недоторканність, депутатський запит; частотність: висока'
  - децентралізація (decentralization) — реформа децентралізації, фінансова децентралізація; актуальний термін реформ
  - 'вибори (elections) — чергові вибори, виборча дільниця, результати виборів; частотність: висока'
  - 'голосування (voting) — таємне голосування, процедура голосування; частотність: середня'
  - 'міністр (minister) — профільний міністр, кабінет міністрів; частотність: висока'
  recommended:
  - коаліція (coalition) — правляча коаліція, розпад коаліції, коаліційна угода; ключовий термін парламентаризму
  - фракція (faction) — парламентська фракція, голова фракції; вживається у контексті партійної структури
  - ОТГ (United Territorial Community) — об'єднана територіальна громада; ключовий термін реформи децентралізації
  - ухвалювати (to adopt/pass) — ухвалювати закон; стилістично вища норма ніж 'приймати'
  - обирати (to elect) — обирати президента/депутата; вживається для посад та процедур
  - імпічмент (impeachment) — процедура імпічменту; правовий термін
  - 'вето (veto) — накласти вето, подолати вето; частотність: середня'
  - референдум (referendum) — загальнонаціональний референдум; засіб прямої демократії
activity_hints:
- type: quiz
  focus: Political system structure
  items: 15+
- type: match-up
  focus: Institution → function
  items: 15+
- type: fill-in
  focus: Political news sentences
  items: 12+
- type: cloze
  focus: Constitutional terminology
  items: 10+
- type: group-sort
  focus: Powers by branch of government
  items: 12+
- type: true-false
  focus: Ukrainian political system facts
  items: 12+
focus: domain
pedagogy: CBI
prerequisites:
- c1-24 (Digital Communication)
- B2 politics vocabulary
connects_to:
- c1-26 (Media Landscape)
- c1-27 (Global Context)
- c1-20 (Контрольна точка — Академічна база)
module_type: cultural
sources:
- name: Конституція України
  url: https://zakon.rada.gov.ua/
  type: primary
  notes: Constitutional framework of Ukraine
- name: Верховна Рада України
  url: https://rada.gov.ua/
  type: reference
  notes: Official parliamentary information
immersion: 100% Ukrainian
phase: C1.2 [Professional Communication]
objectives:
- Learner can use appropriate language for Законодавча влада та Парламентаризм
- Learner can produce professional texts in the domain of Політична система України
- Learner can evaluate and correct register in Державний устрій та Конституція contexts
persona:
  voice: Senior Specialist
  role: Політичний оглядач
word_target: 4000
grammar:
- Державний устрій та Конституція
- Законодавча влада та Парламентаризм
- Виконавча влада та інститут президентства
- Судова система та Децентралізація
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

Research **Політична система України** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Політична система України

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
