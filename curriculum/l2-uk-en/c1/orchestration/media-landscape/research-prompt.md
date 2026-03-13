# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-026
level: C1
sequence: 26
slug: media-landscape
version: '2.0'
title: 'Медіаландшафт: Як не потонути в інформації'
subtitle: 'Introduction: The Role of Media in Modern Society'
content_outline:
- section: 'Вступ: Роль медіа в сучасному суспільстві (Introduction: The Role of Media in Modern Society)'
  words: 450
  points:
  - 'Огляд українського медіаландшафту згідно з державним стандартом §3.20: вплив ЗМІ на суспільну думку.'
  - Поняття інформаційної гігієни та медіаграмотності як ключових компетенцій рівня C1.
  - 'Learner error: Узгодження слова «медіа» — виправлення кальки з англійської (медіа повідомляють/інформують) та вживання
    ЗМІ як множини.'
- section: Структура власності та типи медіа (Ownership Structure and Media Types)
  words: 650
  points:
  - 'Державні vs Суспільні медіа: роз''яснення різниці між «державним» та «суспільним» (Suspilne) мовленням для уникнення
    типових помилок.'
  - 'Приватні та олігархічні медіа: аналіз впливу власників на редакційну політику та виникнення політичної упередженості.'
  - 'Cultural Hook: Феномен телемарафону «Єдині новини» під час повномасштабного вторгнення — дискусія про централізацію vs
    свободу слова.'
- section: Журналістські стандарти та медіаграмотність (Journalistic Standards and Media Literacy)
  words: 750
  points:
  - 'Базові професійні стандарти: баланс думок, достовірність, відокремлення фактів від коментарів та повнота інформації.'
  - 'Оцінка джерел: робота з першоджерелами, верифікованими та сумнівними джерелами інформації (§4.4.1.1 — публіцистичний
    стиль).'
  - Виявлення прихованої та явної упередженості в текстах новинних видань та соціальних мережах.
- section: Протидія дезінформації та маніпуляціям (Countering Disinformation and Manipulation)
  words: 800
  points:
  - 'Cultural Hook: Роль StopFake як одного з перших у світі центрів фактчекінгу, заснованого в Україні для боротьби з пропагандою.'
  - 'Методи пропаганди та маніпуляції свідомістю: емоційна лексика, клікбейтні заголовки та викривлення контексту.'
  - 'Learner error: Розрізнення синонімів «фейковий» (для новин/акаунтів) та «фальшивий» (для грошей/документів) — дрилі на
    контекстуальне вживання.'
- section: Критичний аналіз медіатекстів (Critical Analysis of Media Texts)
  words: 800
  points:
  - 'Практичний аналіз новинних статей за структурою тексту (§4.4.4): заголовки, ліди, бекграунд та цитування.'
  - 'Верифікація інформації: алгоритм перевірки достовірності новини перед поширенням (фактчекінг).'
  - Порівняльний аналіз висвітлення однієї події різними медіа-ресурсами для виявлення маніпулятивних прийомів.
- section: Свобода слова в умовах війни (Freedom of Speech in Wartime Conditions)
  words: 550
  points:
  - 'Права та безпека журналістів у зонах конфлікту: виклики для професійної діяльності та цензура.'
  - 'Баланс між національною безпекою та правом на інформацію: міжнародні стандарти та український досвід.'
  - 'Підсумкова дискусія: як медіаграмотність допомагає зберігати критичне мислення в умовах інформаційної війни.'
vocabulary_hints:
  required:
  - ЗМІ (mass media) — засоби масової інформації; вживається як множина (ЗМІ повідомили); high-frequency.
  - джерело (source) — першоджерело, сумнівне джерело, верифіковане джерело; посилатися на джерело.
  - упередженість (bias) — явна/прихована упередженість, політична упередженість; уникнути упередженості.
  - дезінформація (disinformation) — поширювати дезінформацію, кампанія з дезінформації, боротьба з дезінформацією.
  - маніпуляція (manipulation) — маніпуляція свідомістю, медійна маніпуляція, піддаватися маніпуляції.
  - достовірність (reliability) — перевірка достовірності, сумніватися в достовірності; mid-frequency academic.
  - фейковий (fake) — фейкова новина, фейковий акаунт; не плутати з «фальшивий» (fake/forged objects).
  - фактчекінг (fact-checking) — інструменти фактчекінгу, займатися фактчекінгом; modern media terminology.
  - суспільне мовлення (public broadcasting) — незалежне від держави медіа; ключове для українського контексту.
  - свобода слова (freedom of speech) — загроза свободі слова, обмеження свободи слова в умовах війни.
  recommended:
  - інформаційна гігієна (information hygiene) — дотримання правил споживання інформації; high-frequency context.
  - олігархічні медіа (oligarch-owned media) — медіа, що належать великому бізнесу; політичний контекст.
  - баланс думок (balance of opinions) — журналістський стандарт, що передбачає висвітлення різних точок зору.
  - клікбейт (clickbait) — маніпулятивний заголовок для залучення уваги; лексика соцмереж.
  - верифікація (verification) — процес перевірки даних на відповідність дійсності.
  - першоджерело (primary source) — оригінальний документ або пряме свідчення події.
activity_hints:
- type: quiz
  focus: Media literacy concepts
  items: 15+
- type: group-sort
  focus: Media types by reliability
  items: 12+
- type: match-up
  focus: Propaganda technique → example
  items: 12+
- type: cloze
  focus: Media analysis vocabulary
  items: 10+
- type: true-false
  focus: Identify bias indicators
  items: 12+
- type: essay-response
  focus: Analyze news article for bias
focus: domain
pedagogy: CBI
prerequisites:
- c1-25 (Political System)
- Critical thinking skills
connects_to:
- c1-27 (Global Context)
- c1-37 (Практичні кейси)
- c1-20 (Контрольна точка — Академічна база)
module_type: cultural
sources:
- name: Інститут масової інформації
  url: https://imi.org.ua/
  type: reference
  notes: Media monitoring and analysis
- name: StopFake
  url: https://www.stopfake.org/
  type: secondary
  notes: Fact-checking resources
immersion: 100% Ukrainian
phase: C1.2 [Professional Communication]
objectives:
- Learner can use appropriate language for Структура власності та типи медіа
- Learner can produce professional texts in the domain of Медіаландшафт: Як не потонути в інформації
- Learner can evaluate and correct register in Роль медіа в сучасному суспільстві contexts
persona:
  voice: Senior Specialist
  role: Медіа-експерт
word_target: 4000
grammar:
- Роль медіа в сучасному суспільстві
- Структура власності та типи медіа
- Журналістські стандарти та медіаграмотність
- Протидія дезінформації та маніпуляціям
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

Research **Медіаландшафт: Як не потонути в інформації** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Медіаландшафт: Як не потонути в інформації

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
