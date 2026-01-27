# B2 History Module Template

**Purpose:** Reference template for B2 Ukrainian history modules (M71-131: Origins to Present, Decolonization Focus)

**Based on:** `b2-module-template.md` — inherits all B2 quality standards

**Related Issues:** [#305](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/305), [#332](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/332)

> **Note:** Synthesis modules (M83, M107, M119, M125, M131) use `b2-synthesis-module-template.md` instead.

---

## ⚠️ BEFORE WRITING: Research First!

**CRITICAL:** Historical content requires verified facts. Do NOT generate historical content from memory—this leads to hallucination.

### Research Strategy

**Step 1: Use WebSearch for Initial Research**
```
WebSearch: "[Historical topic] Ukrainian Wikipedia"
WebSearch: "[Historical topic] Encyclopedia of Modern Ukraine"
WebSearch: "[Historical event/figure] Інститут історії України"
```

**Step 2: Verify with WebFetch**
After finding URLs, use WebFetch to extract content:
```
WebFetch: https://uk.wikipedia.org/wiki/[Topic]
WebFetch: https://esu.com.ua/article-[id]
```

**Step 3: Cross-Reference Sources**
- Ukrainian Wikipedia (uk.wikipedia.org) — good starting point
- Encyclopedia of Modern Ukraine (esu.com.ua) — authoritative
- Institute of History of Ukraine (history.org.ua) — academic
- Litopys.org.ua — primary sources

### Key Resources by Era (Prioritize .gov.ua and academic)

| Era | Primary Resources (SAFE) |
|-----|--------------------------|
| **Ancient/Medieval** | history.org.ua, esu.com.ua, litopys.org.ua |
| **Cossack** | litopys.org.ua (chronicles), esu.com.ua |
| **Imperial** | esu.com.ua, history.org.ua |
| **Soviet/20th c.** | memory.gov.ua, uinp.gov.ua, esu.com.ua |
| **Independence** | ukrinform.ua, president.gov.ua |

> ⚠️ **Wikipedia Warning:** Ukrainian Wikipedia (uk.wikipedia.org) is a contested space subject to Russian information warfare. **ALWAYS verify Wikipedia claims against .gov.ua or academic sources.** Prefer ЕСУ (esu.com.ua) and Institute of History (history.org.ua) for historical facts.

### Anti-Hallucination Rules

1. **NEVER invent dates, names, or events** — always verify
2. **NEVER generate primary source quotes from memory** — find real sources
3. **If you cannot find a source, use WebSearch** — do not guess
4. **When in doubt, mark as [NEEDS VERIFICATION]** — flag for review

### Reference Textbooks (Use, Don't Copy!)

This curriculum aligns with Ukrainian school textbooks:

| Source | Use For |
|--------|---------|
| Хлібовська Г.М. et al. "Історія України 7-11 класи" (2017-2025) | Factual framework, chronology |
| Бурнейко І.О. "Історія України 9 клас" (2017) | 19th-20th century events |
| Поліщук О. "Творці української нації" (2024) | Biographical details, decolonization |

**⚠️ ANTI-PLAGIARISM RULES:**
1. **SYNTHESIZE, don't copy** — use textbooks for facts, write in your own words
2. **Cite properly** — if quoting directly, use `> [!quote]` with attribution
3. **Add value** — our modules must include decolonization perspective textbooks may lack
4. **Transform for language learning** — textbooks teach history, we teach Ukrainian through history

> 💡 **Tip:** Use `WebSearch: "[topic] site:history.org.ua"` or `site:esu.com.ua` to search within trusted academic sources. **Avoid relying solely on Wikipedia** due to information warfare.

---

<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст|Розминка
  - Читання
  - Первинні джерела
  - Деколонізаційний погляд
  - Підсумок
  - Потрібно більше практики?
  optional_sections:
  - Діалоги
  forbidden_headers:
  - Activities
  - Vocabulary
  - External Resources
  - Вправи
  - Словник
  - Зовнішні ресурси
  pedagogy: CBI
  min_word_count: 4000
  required_callouts:
  - myth-buster
  - history-bite
  - quote
  description: History modules use Content-Based Instruction with mandatory decolonization
    content
-->

---

## Quick Reference Checklist

Before submitting a B2 history module, verify all items from `b2-module-template.md` PLUS:

### History-Specific Requirements

- [ ] **CBI pedagogy:** Content-Based Instruction with Narrative Arc (NOT TTT)
- [ ] **Extended narrative:** 500+ word historical account (main text)
- [ ] **Decolonization lens:** Ukraine-centric perspective, not Russian imperial framing
- [ ] **Primary sources (≥2):** MANDATORY — include at least 2 excerpts from historical documents using `[!quote]` callout format
- [ ] **Reading tasks (2-3):** External reading assignments with linguistic analysis questions
- [ ] **Essay activity:** `essay-response` activity in YAML (150-250 words per config.py) — NO essay section in markdown
- [ ] **Activity count:** 3-10 seminar-style activities (must include reading + essay-response per config.py)
- [ ] **Vocabulary in context:** Historical terms embedded in narrative, not listed
- [ ] **Engagement boxes:** Historical context, myth-busting, modern relevance
- [ ] **NO DIALOGS:** History modules are READING-CENTRIC. Do NOT include conversational dialogs — they waste space and distract from historical content. Use primary source excerpts instead.

---

## Naturalness Quality Checklist

**Run this check during Stage 4 (Review & Fix) on prose content.**

Before finalizing the module, verify all narrative prose and essay prompts achieve:

- [ ] **Subject consistency** - Clear subjects maintained throughout passages
- [ ] **Discourse markers** - At least 2-3 connectors per 10-sentence passage (а, але, потім, тому, також, спочатку, нарешті)
- [ ] **Topic coherence** - All sentences contribute to unified narrative/theme, no random topic jumps
- [ ] **No template repetition** - Varied sentence structures across activities within the module
- [ ] **Moderate intensifiers** - Maximum 2-3 "дуже" per module, 0-1 "надзвичайно/справжній"
- [ ] **No double superlatives** - Use one precise descriptor instead of redundant pairs (e.g., "найкращий" NOT "найкращий та найвидатніший")
- [ ] **Natural transitions** - Avoid robotic "і це", "тому що... тому" patterns

**Target score:** 8/10 for content modules, 7/10 for checkpoints

**Red flags (score < target):**
- Same sentence template repeated across multiple activities
- Disconnected factoid lists without discourse markers
- Excessive intensifiers or double superlatives
- Robotic, mechanical transitions

**See:** `claude_extensions/stages/stage-4-review-fix.md` Section 9 for detailed naturalness criteria.

**For batch scanning:** Use `/scan-naturalness {level} {start} {end}` to scan completed modules.

---

## Module Structure (History-Specific)

### 1. Frontmatter

```yaml
---
module: b2-XX
title: 'Ukrainian Title — Historical Period/Event'
phase: 'B2.3 [Ukrainian History]'
pedagogy: 'CBI' # Content-Based Instruction
register: 'публіцистичний' # Historical narrative style
tags:
  - history
  - [era: medieval, cossack, imperial, soviet, independence]
  - [topic: specific-event-or-period]
grammar:
  - 'Historical narrative tenses'
  - 'Passive voice in historical writing'
vocabulary_focus:
  - 'Historical terminology'
  - 'Political/military vocabulary'
---
```

### 2. Narrative Arc Structure

#### Section 1: Hook — 200-300 words

```markdown
# [Historical Topic Title]

> 🎯 **Чому це важливо?**
>
> [Connect historical event to modern Ukrainian identity]
> [Explain relevance to language learner]
> [Frame the decolonization perspective]

## Вступ

[Compelling opening that draws reader in — a dramatic moment, a key figure's words, or a surprising fact]

[Set the historical context: When? Where? Who? What was at stake?]

> 💡 **Чи знали ви?**
>
> [Surprising fact that challenges common misconceptions]
```

#### Section 2: Historical Narrative — 800-1000 words

```markdown
## [Historical Event/Period Name]

### Контекст

[200-300 words of background: political situation, key players, tensions]

### Основні події

[400-500 words of main narrative with embedded vocabulary]

**Key vocabulary should appear naturally in the narrative:**

> Гетьман Богдан Хмельницький **очолив** козацьке повстання проти польського панування. Запорозька Січ стала центром **спротиву**. Козаки **здобули** низку перемог, що **підірвали** владу Речі Посполитої.

### Наслідки

[200-300 words on consequences and legacy]

> 🌍 **Сучасна перспектива**
>
> [How this historical event is viewed today in Ukraine]
> [Contrast with Russian/Soviet historiography if relevant]
```

#### Section 3: Primary Sources — 200-300 words

```markdown
## Первинні джерела

### Документ 1: [Source Title]

**Контекст:** [Brief context about the document]

> [Excerpt from primary source in Ukrainian — 100-200 words]
> _— Джерело: [Attribution]_

**Лінгвістичний аналіз:**

<critical>
**FOCUS ON LANGUAGE, NOT CONTENT INTERPRETATION**

Questions must analyze LINGUISTIC features, not historical meaning.
</critical>

**✅ GOOD (Linguistic Analysis):**

- Який регістр використовує автор? Наведіть приклади.
- Знайдіть три приклади пасивного стану. Чому автор їх використовує?
- Порівняйте лексику цього тексту з лексикою модуля. Які слова застаріли?
- Які синтаксичні конструкції характерні для офіційного стилю?

**❌ BAD (Content Interpretation):**

- Що автор думає про Московське царство? ← Tests interpretation
- Чому Хмельницький прийняв це рішення? ← Tests historical knowledge

### Документ 2: [Contrasting Source]

[If applicable, provide contrasting perspective for LINGUISTIC comparison]
```

#### Section 4: Decolonization Focus — 200-300 words

```markdown
## Деколонізаційний погляд

### Міфи та реальність

**Міф:** [Common misconception from Russian/Soviet historiography]

**Реальність:** [Ukrainian perspective based on primary sources and modern scholarship]

> ⚠️ **Деколонізація**
>
> [Explain why the Russian/Soviet narrative is problematic]
> [Cite Ukrainian historians or primary sources]

### Сучасна Україна

[Connect historical event to modern Ukrainian identity and independence movement]
```

---

## Reading Tasks (External Assignments)

History modules should include **2-3 external reading tasks** for deeper engagement with authentic Ukrainian historical texts.

```yaml
# In activities/{slug}.yaml

- type: reading
  id: b2-75-reading-01
  title: 'Аналіз первинного джерела'
  resource:
    type: primary_source
    url: 'https://...'
    title: 'Універсал Богдана Хмельницького'
  tasks:
    - 'Знайдіть у тексті три приклади офіційного регістру'
    - 'Які дієслова використовує автор для опису своїх дій?'
    - 'Порівняйте синтаксис цього документа із сучасною публіцистикою'

- type: reading
  id: b2-75-reading-02
  title: 'Сучасний історичний аналіз'
  resource:
    type: article
    url: 'https://...'
    title: "[Ukrainian historian's article]"
  tasks:
    - 'Як автор описує деколонізаційний підхід до цього періоду?'
    - 'Знайдіть приклади академічного регістру в тексті'
    - 'Порівняйте мову історика з мовою первинного джерела'
```

**Note:** Questions focus on LINGUISTIC analysis, not historical interpretation.

---

## Essay Activities (In YAML Only)

**CRITICAL:** Essay activities are defined ONLY in `activities/{slug}.yaml` as `type: essay-response`.

**DO NOT include `## Есе` sections in markdown.** This was a legacy pattern that caused:
- Content redundancy (essay prompt + model answer duplicated)
- Word count inflation (~700 words added to content)
- QA confusion (auditing both locations)

**Per config.py, B2-history essay-response requirements:**
- **Word count:** 150-250 words (student response length)
- **Required:** Every module must have an essay-response activity

**Essay activity in YAML:**
```yaml
- type: essay-response
  id: b2-XX-essay-01
  title: 'Есе: Деколонізаційний аналіз'
  prompt: |
    Напишіть есе (150-250 слів) на тему: "[Topic]"

    Вимоги:
    - Використайте лексику модуля
    - Застосуйте деколонізаційний підхід
    - Наведіть приклади з первинних джерел
  rubric:
    - criterion: Мовна якість
      weight: 40
      description: Граматика, лексика, складність речень
    - criterion: Використання матеріалу
      weight: 30
      description: Цитування джерел, лексика модуля
    - criterion: Структура
      weight: 20
      description: Логічна організація, зв'язність
    - criterion: Деколонізаційний підхід
      weight: 10
      description: Критичний аналіз імперських наративів
```

---

## History-Specific Activities

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

### Seminar-Style Activities (Required)

*Note: B2-HIST is a seminar track. All activities must be implemented in YAML using seminar-style types only.*

**Required activity types:**
1. **Reading (`reading`):** External reading assignments with linguistic analysis questions — analyze primary sources, academic articles
2. **Essay Response (`essay-response`):** Extended writing (150-250 words) with rubric — every module must include one

**Recommended activity types:**
3. **Critical Analysis (`critical-analysis`):** Deep analysis of texts, sources, or historiographical approaches
4. **Comparative Study (`comparative-study`):** Compare perspectives, sources, or interpretations
5. **Authorial Intent (`authorial-intent`):** Analyze author's purpose, bias, and rhetorical strategies in primary sources
6. **True/False (`true-false`):** LIMITED use — only for verifying reading comprehension, not grammar drills

**❌ NOT PERMITTED in B2-HIST:**
- Grammar drills: quiz, fill-in, cloze, match-up, error-correction, unjumble, mark-the-words, group-sort, select, translate
- These activity types are for language-focused modules, not history seminars

---

## Engagement Boxes for History Modules

```markdown
> 🏛️ **Історичний контекст**
>
> [Background information that helps understand the period]

> ⚠️ **Деколонізація**
>
> [Challenge Russian/Soviet historiographical myths]

> 📜 **Первинне джерело**
>
> [Quote from historical document with translation notes]

> 🌍 **Сучасна Україна**
>
> [Connect to post-2014 or post-2022 context]

> 💡 **Чи знали ви?**
>
> [Surprising historical fact]

> 🗺️ **Географічний контекст**
>
> [Explain historical geography — borders, regions, place names]
```

---

---

## Content Structure Note

### Vocabulary & Activities

**CRITICAL:** Do NOT add `## Vocabulary` or `## Activities` headers. These sections are injected automatically from:

- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`

The build system will inject these sections at build time.

**History vocabulary notes:**

- Include political/military terminology
- Include historiographical terms (джерело, свідчення, інтерпретація)
- Include fixed collocations common in historical writing
- Note decolonization-relevant terms (гноблення, колонізація, русифікація)

---

## Example Module Outline: M75 (Cossack Era)

```markdown
# Козацька ера: Хмельниччина

> 🎯 **Чому це важливо?**
> Козацька революція 1648-1657 років — це початок модерної української державності...

## Вступ

[Hook with dramatic opening — perhaps Хмельницький's words]

## Хмельниччина: Повстання та війна

### Контекст [Polish-Lithuanian oppression]

### Основні події [Uprising, battles, negotiations]

### Наслідки [Hetmanate, Pereyaslav]

## Первинні джерела

### Універсал Богдана Хмельницького

### Свідчення іноземних дипломатів

## Деколонізаційний погляд

### Міфи про "возз'єднання"

### Сучасна українська історіографія

# Підсумок

# Словник [defined in vocabulary/{slug}.yaml]

# Активності [defined in activities/{slug}.yaml, 3-10 seminar-style]
# (must include reading + essay-response per config.py)
```

---

## Decolonization Content Guidelines

### Required Myth-Busting

**For each major historical period, address:**

| Period   | Common Myth                   | Ukrainian Reality                                               |
| -------- | ----------------------------- | --------------------------------------------------------------- |
| Medieval | Kyivan Rus = "Ancient Russia" | Rus was a multi-ethnic state; "Russia" is a later appropriation |
| Cossack  | Pereyaslav = "reunification"  | Military alliance, not submission; broken by Moscow             |
| Imperial | "Little Russians"             | Colonial term; Ukrainians had distinct identity and language    |
| Soviet   | "Brotherly nations"           | Russification, Holodomor, cultural suppression                  |
| Modern   | "One people"                  | Independent nation with separate history, language, culture     |

### Decolonization Vocabulary

| Term                   | Usage                                                    |
| ---------------------- | -------------------------------------------------------- |
| Московське царство     | Use instead of "Росія" for pre-1721 period               |
| Російська імперія      | Use for 1721-1917 period                                 |
| Русифікація            | Describe policies suppressing Ukrainian language/culture |
| Колоніальний наратив   | Label Russian/Soviet historiographical distortions       |
| Українська державність | Emphasize continuous tradition of statehood              |

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/b2-module-template.md`
- **Synthesis template:** `docs/l2-uk-en/templates/b2-synthesis-module-template.md` (for M83, M107, M119, M125, M131)
- **B2 Curriculum Plan:** `docs/l2-uk-en/B2-CURRICULUM-PLAN.md` (M71-131 history progression)
- **Restructure proposal:** `docs/l2-uk-en/B2-HISTORY-RESTRUCTURE-PROPOSAL.md`
- **Gemini expansion:** `docs/l2-uk-en/B2-GEMINI-EXPANSION-PROPOSAL.md` (detailed module specs)
- **Decolonization guidelines:** Referenced in curriculum plan

---

**Last Updated:** 2026-01-27
**Template Version:** 1.3

**Changelog:**

- v1.3 (2026-01-27): Converted to seminar-style activities only — removed grammar drill recommendations (quiz, fill-in, cloze, match-up, error-correction, unjumble, mark-the-words, group-sort, select, translate); now requires reading, essay-response, critical-analysis, comparative-study, authorial-intent
- v1.2 (2025-12-29): Updated module range M71-131, added reference to synthesis template
- v1.1 (2025-12-29): Added NO DIALOGS rule, made primary sources mandatory (≥2)
