# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-024
level: C1
sequence: 24
slug: digital-communication
version: '2.0'
title: Цифрова комунікація
subtitle: 'Introduction: Registers and Channels of Digital Communication'
content_outline:
- section: 'Вступ: Регістри та канали цифрової комунікації (Introduction: Registers and Channels of Digital Communication)'
  words: 500
  points:
  - Аналіз офіційно-ділового та епістолярного стилів у цифровому середовищі згідно з Державним стандартом §4.4.1.1.
  - Критерії вибору каналу комунікації (email vs месенджер) залежно від терміновості та формальності запиту.
  - 'Культурний гачок: концепція «тихої години» в українському бізнес-середовищі та етика спілкування в позаробочий час.'
- section: 'Мистецтво ділового листування: Етикет та структура (Art of Business Correspondence: Etiquette and Structure)'
  words: 800
  points:
  - 'Культурна особливість: обов''язкове використання кличного відмінка у звертаннях (напр. «Шановний пане Андрію») як ознака
    С1-рівня.'
  - 'Табу в українському етикеті: виправлення помилкової кальки «Доброго часу доби» на нормативні часові вітання (Добрий день/вечір).'
  - 'Елементи структурування тексту за стандартом §4.4.4: вживання вставних слів «по-перше», «отже», «насамкінець» для логіки
    викладу.'
  - Важливість теми листа (Subject line) та правила оформлення підпису (Signature) згідно з нормами Chamber.ua.
- section: Специфіка спілкування в месенджерах та робочих чатах (Specifics of Communication in Messengers and Work Chats)
  words: 700
  points:
  - 'Етикет корпоративних чатів: баланс між лаконічністю та ввічливістю, використання емодзі в українському бізнес-контексті.'
  - 'Термінологічна чистота: пріоритетне вживання слова «покликання» замість розмовного русизму «силка».'
  - 'Learner error: надмірне вживання великої літери «Ви» у груповому листуванні (правило вживання малої літери для множини).'
- section: Відеоконференції та цифрова етика (Video Conferences and Digital Ethics)
  words: 700
  points:
  - 'Мовленнєвий етикет онлайн-зустрічей: підключення, представлення учасників та модерація обговорення.'
  - 'Професійний жаргон: доречне використання термінів «затегати», «м’ют», «шерінг екрана» як елементів ІТ-культури.'
  - Застосування безособових конструкцій для пом'якшення тону в конфліктних ситуаціях або при наданні негативного фідбеку.
- section: Корекція типових помилок та кальок (Correction of Common Errors and Calques)
  words: 700
  points:
  - Розрізнення «питання» (problem/issue) та «запитання» (question) — виправлення англійської кальки «Я маю питання» на «У
    мене є запитання».
  - 'Норми оформлення вкладень (attachments): супровідний текст та правила іменування файлів.'
  - Аналіз помилок, пов'язаних з ігноруванням повідомлень та неправильним використанням копій (CC/BCC).
- section: 'Практикум: Трансформація стилів та написання (Workshop: Style Transformation and Writing)'
  words: 600
  points:
  - Трансформація неформального запиту з месенджера в офіційний електронний лист з дотриманням усіх структурних елементів.
  - 'Написання тематичних листів: запит інформації, подяка партнеру та лист-вибачення за технічну затримку.'
  - Критичний аналіз прикладів реального листування на відповідність нормам українського цифрового етикету.
vocabulary_hints:
  required:
  - електронний лист (email) — написати, надіслати, отримати, переслати лист; найвища частотність у бізнесі
  - тема листа (subject line) — обов’язковий елемент для ідентифікації змісту та терміновості
  - звертання (salutation) — вимагає вживання кличного відмінка (пане, добродію)
  - підпис (signature) — містить посаду, контактні дані та покликання на сайт компанії
  - вкладення (attachment) — додати вкладення, завантажити файл у вкладенні; офіційний термін
  - копія (CC) — поставити колегу в копію для інформування
  - прихована копія (BCC) — для масових розсилок, щоб приховати адреси отримувачів
  - месенджер (messenger) — корпоративний месенджер, робочий чат, спілкування в месенджерах
  - відеоконференція (video conference) — підключитися до відеоконференції, посилання на зустріч
  - покликання (link) — активне покликання, перейти за покликанням; нормативний замінник слова «силка»
  recommended:
  - запитання (question) — те, що ставлять (у мене є запитання); часто плутають з «питанням» (problem)
  - вставні слова (fillers/linkers) — по-перше, отже, насамкінець; для структурування тексту за стандартом §4.4.4
  - безособові конструкції (impersonal constructions) — напр. «було вирішено», «погоджено» для дипломатичного тону
  - 'затегати (to tag) — професійний жаргон: позначити когось у повідомленні чату'
  - м’ют (mute) — стан вимкненого мікрофона (бути на м’юті)
  - шерінг екрана (screen sharing) — демонстрація робочого столу під час відеодзвінка
  - онлайн-етикет (online etiquette) — негласні правила спілкування в цифрову епоху
  - автовідповідь (auto-reply) — налаштування повідомлення про відсутність на робочому місці
activity_hints:
- type: essay-response
  focus: Write formal email on given topic
- type: quiz
  focus: Digital communication etiquette
  items: 15+
- type: match-up
  focus: Informal message → formal email
  items: 12+
- type: error-correction
  focus: Fix email mistakes
  items: 12+
- type: cloze
  focus: Email templates completion
  items: 10+
- type: group-sort
  focus: Formal vs informal digital language
  items: 12+
focus: communication
pedagogy: PPP
prerequisites:
- c1-23 (Business Etiquette)
- Academic writing skills
connects_to:
- c1-25 (Political System)
- c1-36 (Професійні сценарії)
- c1-20 (Контрольна точка — Академічна база)
module_type: skills
sources:
- name: Ukrainian Digital Etiquette
  url: https://mon.gov.ua/
  type: reference
  notes: Guidelines for professional digital communication
- name: Business Email Standards
  url: https://chamber.ua/
  type: secondary
  notes: Ukrainian business correspondence norms
immersion: 100% Ukrainian
phase: C1.2 [Professional Communication]
objectives:
- Learner can use appropriate language for Етикет та структура
- Learner can produce professional texts in the domain of Цифрова комунікація
- Learner can evaluate and correct register in Регістри та канали цифрової комунікації contexts
persona:
  voice: Senior Specialist
  role: SMM-стратег
word_target: 4000
grammar:
- Регістри та канали цифрової комунікації
- Етикет та структура
- Специфіка спілкування в месенджерах та робочих чатах
- Відеоконференції та цифрова етика
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

Research **Цифрова комунікація** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Цифрова комунікація

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
