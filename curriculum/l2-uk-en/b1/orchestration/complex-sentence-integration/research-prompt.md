# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-041
level: B1
sequence: 41
slug: complex-sentence-integration
version: '2.0'
title: Інтеграція складних речень
subtitle: Complex Sentence Integration
focus: grammar
pedagogy: TTT
phase: B1.3b [Complex Sentences]
word_target: 4000
objectives:
- Learner can combine причинові, часові, умовні clauses
- Learner can build multi-clause sentences
- Learner can choose appropriate connectors for context
- Learner can manage complex sentence structure
content_outline:
- section: Діагностика та вступ (Diagnostic Test & Introduction)
  words: 600
  points:
  - 'Діагностичне тестування: використання простих речень там, де доцільніші складні речення; самооцінка навичок поєднання
    частин речення.'
  - 'Вправа на розрізнення регістрів: вживання сполучників «бо» (розмовний) та «тому що» (офіційний/нейтральний) у діалогах.'
- section: Граматичні основи та типи зв'язку (Grammatical Foundations & Types of Connection)
  words: 1000
  points:
  - 'Державний стандарт §4.4.3: типи складносурядних речень (єднальні, протиставні, розділові) та складнопідрядних речень.'
  - 'Аналіз типової помилки: плутанина між сполучниками «і» (додавання) та «а» (протиставлення), спричинена впливом англійського
    «and».'
  - 'Класифікація підрядних частин: причини (тому що, бо), умови (якщо), мети (щоб) та допустові (хоча/хоч).'
- section: Культура, ритм та пунктуація (Culture, Rhythm & Punctuation)
  words: 800
  points:
  - 'Культурний гачок: «Правило трьох» в українських народних казках як модель для побудови багатокомпонентних речень (послідовний
    та паралельний зв''язок).'
  - 'Мелодійний синтаксис: ритміка та музикальність довгих речень; використання сполучників для створення плинності тексту
    («співоча мова»).'
  - 'Правила пунктуації: структурний характер коми перед «що», «який», «коли»; розбір помилок, пов''язаних із пропуском розділових
    знаків.'
- section: Практичне застосування та стилістика (Practical Application & Stylistics)
  words: 900
  points:
  - 'Побудова складних структур: поєднання сурядності та підрядності в одному реченні; керування структурою багатокомпонентних
    речень.'
  - 'Усунення помилок: правильне вживання відносного займенника «який» замість незмінного сполучника «що» у відповідних відмінках
    та родах.'
  - 'Стилістичні правки: вибір між короткими та довгими реченнями для досягнення бажаного ефекту в тексті.'
- section: Творча майстерня редактора (Creative Editor's Workshop)
  words: 700
  points:
  - 'Рольова гра «Редактор роману»: редагування тексту для покращення стилю та чіткості викладу думок через складні речення.'
  - 'Сценарії багаторівневого діалогу: вибір відповідних конекторів залежно від контексту (регістр) та мети висловлювання.'
  - 'Підсумковий огляд: закріплення навичок інтеграції складних речень у мовлення.'
vocabulary_hints:
  required:
  - інтеграція (integration) — інтеграція в текст; процес поєднання
  - складний (complex) — складне речення; складна структура
  - сурядний (coordinating) — сурядний зв'язок; рівноправні частини
  - підрядний (subordinating) — підрядний зв'язок; головна та залежна частини
  - багатокомпонентний (multi-component) — речення з трьома і більше частинами
  - структура (structure) — структура речення; ритмічна структура
  - кома (comma) — обов'язкова перед «що», «який», «коли»; структурна пунктуація
  - розділовий знак (punctuation mark) — знаки для чіткості стилю
  - а (and/but) — протиставлення (не ..., а ...); а також (and also); висока частотність
  - але (but) — протиставлення; часто вживається у парі з «хоча»; high frequency
  - щоб (in order to/that) — мета; для того, щоб; хочу, щоб...; high frequency
  - бо (because) — причина; розмовний стиль; не прийшов, бо захворів
  - тому що (because) — причина; нейтральний або офіційний стиль; тому що це важливо
  recommended:
  - вкладений (nested) — вкладені підрядні частини
  - паралельний (parallel) — паралельна підрядність
  - зрозумілість (clarity) — зрозумілість викладу думок
  - стиль (style) — художній стиль; розмовний стиль
  - хоча (although) — допустове значення; хоча було пізно; хоча він знав
  - якщо (if) — умова; якщо буде час; якщо ти не проти; висока частотність
  - який (which/who) — відносний займенник; книга, яку я читаю; узгодження у роді та відмінку
  - що (that) — сполучник; незмінна форма; він каже, що...
activity_hints:
- type: error-correction
  focus: Build multi-clause sentences
  items: 25
- type: error-correction
  focus: Fix complex sentence errors
  items: 20
- type: fill-in
  focus: Complete integrated sentences
  items: 15
- type: fill-in
  focus: Write complex paragraphs
  items: 10
connects_to:
- 'b1-42 (Непряма мова: твердження)'
prerequisites:
- b1-40 (Часові підрядні речення)
persona:
  voice: Senior Language & Culture Specialist
  role: Novel Editor
grammar:
- Combining multiple clause types
- Coordination and subordination together
- Multi-clause sentence management
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

Research **Інтеграція складних речень** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Інтеграція складних речень

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
