# C1 Biography Module Template

**Purpose:** Reference template for C1 biography modules (M36-100: 65 Ukrainian Historical & Cultural Figures)

**Based on:** `c1-module-template.md` — inherits all C1 quality standards

**Related Issue:** [#306](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/306)

---

## ⚠️ BEFORE WRITING: Research First!

**CRITICAL:** Biographical content requires verified facts. Do NOT generate biographies from memory—this leads to hallucination (wrong dates, invented quotes, fictional events).

### Research Strategy

**Step 1: Use WebSearch for Initial Research**
```
WebSearch: "[Figure name] Ukrainian Wikipedia"
WebSearch: "[Figure name] Encyclopedia of Modern Ukraine"
WebSearch: "[Figure name] біографія"
```

**Step 2: Verify with WebFetch**
After finding URLs, use WebFetch to extract content:
```
WebFetch: https://uk.wikipedia.org/wiki/[Figure_name]
WebFetch: https://esu.com.ua/article-[id]
```

**Step 3: Find Primary Sources**
For quotes, letters, speeches:
```
WebSearch: "[Figure name] листи" OR "[Figure name] промови"
WebSearch: "[Figure name] цитати site:uk.wikiquote.org"
```

### Key Resources by Domain (Prioritize .gov.ua and academic)

| Domain | Primary Resources (SAFE) | Secondary |
|--------|--------------------------|-----------|
| **Literature** | esu.com.ua, litopys.org.ua, ukrlib.com.ua | — |
| **Politics/Military** | memory.gov.ua, history.org.ua, esu.com.ua | — |
| **Science/Academia** | nas.gov.ua, esu.com.ua | — |
| **Arts/Culture** | esu.com.ua, namu.kiev.ua | — |
| **Religious figures** | risu.ua, esu.com.ua | — |
| **Contemporary** | ukrinform.ua, president.gov.ua | — |

> ⚠️ **Wikipedia Warning:** Ukrainian Wikipedia (uk.wikipedia.org) is a contested space subject to information warfare. **ALWAYS verify Wikipedia claims against .gov.ua or academic sources.** Prefer ЕСУ (esu.com.ua) for biographical facts.

### Primary Academic Sources (PRIORITIZE THESE)

| Source | URL | Coverage |
|--------|-----|----------|
| **Енциклопедія Сучасної України (ЕСУ)** | [esu.com.ua](https://esu.com.ua) | 81,000+ peer-reviewed articles |
| **Institute of National Memory** | [memory.gov.ua](https://memory.gov.ua) | 20th century, dissidents, Holodomor |
| **Institute of History NANU** | [history.org.ua](https://history.org.ua) | Academic historical research |
| **National Library of Ukraine** | [nbuv.gov.ua](https://nbuv.gov.ua) | Dissertations, academic works |

### Reference Works (Use, Don't Copy!)

| Source | Use For |
|--------|---------|
| ЕСУ biographical articles | Verified dates, achievements, context |
| Поліщук О. "Творці української нації" (2024) | Decolonization perspective on key figures |
| UINP biographical databases | Dissidents, Executed Renaissance, Holodomor witnesses |

**⚠️ ANTI-PLAGIARISM RULES:**
1. **SYNTHESIZE, don't copy** — use encyclopedias for facts, write original narrative
2. **Quote properly** — if using figure's own words, use `> [!quote]` with attribution
3. **Add language learning value** — encyclopedias inform, we teach Ukrainian through biography
4. **Decolonize** — even ЕСУ may have Soviet-era remnants in older articles

### Anti-Hallucination Rules

1. **NEVER invent birth/death dates** — verify from ЕСУ or .gov.ua sources
2. **NEVER generate quotes from memory** — find actual documented quotes in academic sources
3. **NEVER invent family members, teachers, or associates** — verify names in ЕСУ
4. **PREFER ЕСУ over Wikipedia** — [esu.com.ua](https://esu.com.ua) is peer-reviewed by NANU scholars
5. **When in doubt, mark as [NEEDS VERIFICATION]** — flag for review

### URL Verification (MANDATORY)

Before using any external URL in reading activities:
1. Use WebFetch to confirm the page exists
2. Verify the page is about the correct person (common name collisions!)
3. Check the page contains substantial biographical content

> 💡 **Tip:** [Енциклопедія Сучасної України](https://esu.com.ua) (ЕСУ) is the authoritative source — 81,000+ peer-reviewed articles from NANU and NTSh scholars. **Avoid relying solely on Wikipedia** due to information warfare concerns.

---

<!--
TEMPLATE_METADATA:
  required_sections:
  - Життєпис
  - Внесок
  - Останні роки|Сучасний етап
  - Спадщина|Вплив
  - Підсумок
  - Потрібно більше практики?
  pedagogy: Immersion
  min_word_count: 4000
  required_callouts: []
  description: C1 biography modules focus on cultural figures
-->

---

## Quick Reference Checklist

Before submitting a C1 biography module, verify all items from `c1-module-template.md` PLUS:

### Biography-Specific Requirements
- [ ] **CBI pedagogy:** Content-Based Instruction (vocabulary through narrative)
- [ ] **Extended narrative:** 800-1000 word biographical account
- [ ] **Primary sources (≥2):** Include quotes, letters, or speeches from the figure using `[!quote]` callouts
- [ ] **Reading tasks (2-3):** External reading assignments with linguistic analysis questions
- [ ] **Essay activity:** `essay-response` activity in YAML (250-400 words per config.py) — NO essay section in markdown
- [ ] **Activity count:** 4-9 seminar-style activities (must include reading + essay-response + critical-analysis per config.py)
- [ ] **Historical context:** Place figure in their era's political/cultural context
- [ ] **Legacy section:** Connect to modern Ukraine
- [ ] **Gender/era balance:** Follow curriculum diversity requirements
- [ ] **Decolonization lens:** Ukrainian perspective, not Russian imperial framing
- [ ] **NO DIALOGS:** Biography modules are READING-CENTRIC. Do NOT include conversational dialogs—focus on narrative, primary sources, and analysis. Fictional dialogs with historical figures are inappropriate.


---

## Naturalness Quality Checklist

**Run this check during Stage 4 (Review & Fix) on prose activities.**

Before finalizing the module, verify prose activities (cloze, fill-in, unjumble with 5+ sentences) achieve:

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

## Module Structure (Biography-Specific)

### 1. Frontmatter

```yaml
---
module: c1-XX
title: "[Figure Name]: [Ukrainian Title]"
phase: "C1.3 [Biographies]"
pedagogy: "CBI"  # Content-Based Instruction
register: "публіцистичний"  # Biographical narrative style
tags:
  - biography
  - [era: pre-modern, cossack, imperial, revolutionary, soviet, independence]
  - [domain: literature, politics, science, arts, military, religion]
grammar:
  - "Historical narrative tenses"
  - "Quoted speech conventions"
vocabulary_focus:
  - "Domain-specific terminology"
  - "Historical vocabulary"
---
```

### 2. Biography Content Structure

#### Section 1: Hook & Context — 300-400 words

```markdown
# [Figure Name]: [Descriptive Title]

> 🎯 **Чому це важливо?**
>
> [2-3 sentences explaining figure's significance]
> [Why modern Ukrainians remember this person]
> [What learners will understand by studying this figure]

## Вступ

[Compelling opening — a dramatic moment, famous quote, or surprising fact about the figure]

[Set the historical context: When did they live? What was Ukraine like then? What challenges did they face?]

> 💡 **Чи знали ви?**
>
> [Surprising or lesser-known fact about the figure]
```

#### Section 2: Біографія (Main Narrative) — 800-1000 words

```markdown
## Біографія

### Ранні роки

[200-250 words about birth, childhood, education, formative experiences]

**Ключові дати:**
| Рік | Подія |
|-----|-------|
| [Year] | [Event] |
| [Year] | [Event] |

### Шлях до [визнання/влади/творчості]

[300-350 words about rise to prominence, key achievements, turning points]

> 📜 **Первинне джерело**
>
> [Quote from the figure's letters, speeches, or writings — 50-100 words]
> *— Джерело: [Attribution]*

### Головні досягнення

[250-300 words about major contributions, works, or actions]

**[Figure's domain]-specific achievements:**
1. [Achievement 1]
2. [Achievement 2]
3. [Achievement 3]

### Останні роки (якщо постать померла) / Сучасний етап (якщо постать жива)

[200-250 words about later life/death OR current activities and role today]

### Спадщина (якщо постать померла) / Вплив (якщо постать жива)

[200-250 words about impact on culture and history]

> 🌍 **Сучасна Україна**
>
> [How this figure is remembered today — monuments, street names, cultural references]
```

#### Section 3: Історичний контекст — 300-400 words

```markdown
## Історичний контекст

### [Era Name]: Україна у [period]

[Describe the political, cultural, and social context of the figure's life]

**Ключові контекстуальні фактори:**
- **Політика:** [Political situation]
- **Культура:** [Cultural movements]
- **Мова:** [Language situation — Russification, national revival, etc.]

### Вплив на сучасників

[How the figure influenced contemporaries and was perceived in their time]

> ⚠️ **Деколонізація**
>
> [Challenge Russian/Soviet historiographical myths about this figure if applicable]
> [Provide Ukrainian perspective based on primary sources]
```

#### Section 4: Порівняльний аналіз — 300-400 words

```markdown
## Порівняльний аналіз

### [Figure] vs. [Contemporary or Contrasting Figure]

| Аспект | [Figure 1] | [Figure 2] |
|--------|------------|------------|
| Епоха | [Era] | [Era] |
| Домен | [Domain] | [Domain] |
| Підхід | [Approach] | [Approach] |
| Спадщина | [Legacy] | [Legacy] |

**Аналіз:**
[200-250 words comparing the two figures' contributions, approaches, or legacies]

### Критичне мислення

**Питання для роздуму:**
1. Чому ця постать важлива для української ідентичності?
2. Як би її життя відрізнялося в інших обставинах?
3. Які уроки можна винести з її досвіду?
```

---

## Reading Tasks (External Assignments)

Biography modules should include **2-3 external reading tasks** for deeper engagement with primary sources and scholarly biographies.

```yaml
# In activities/{slug}.yaml

- type: reading
  id: c1-XX-reading-01
  title: "Первинні джерела: Листи/Промови/Твори"
  resource:
    type: primary_source
    url: "https://..."
    title: "[Figure Name]: [Document Title]"
  tasks:
    - "Який регістр використовує автор у цьому документі? Наведіть приклади."
    - "Знайдіть три приклади емоційно забарвленої лексики"
    - "Порівняйте мову автора з сучасною українською. Які слова застаріли?"

- type: reading
  id: c1-XX-reading-02
  title: "Науковий біографічний нарис"
  resource:
    type: article
    url: "https://..."
    title: "[Ukrainian historian's biography]"
  tasks:
    - "Як автор використовує біографічну лексику (відіграти роль, творча спадщина)?"
    - "Знайдіть приклади академічного регістру в тексті"
    - "Порівняйте інтерпретацію історика з аналізом у модулі"
```

**Note:** Questions focus on LINGUISTIC analysis, not biographical interpretation.

---

## Essay Activities (In YAML Only)

**CRITICAL:** Essay activities are defined ONLY in `activities/{slug}.yaml` as `type: essay-response`.

**DO NOT include `## Есе` sections in markdown.** This was a legacy pattern that caused:
- Content redundancy (essay prompt + model answer duplicated)
- Word count inflation (~700 words added to content)
- QA confusion (auditing both locations)

**Per config.py, C1-biography essay-response requirements:**
- **Word count:** 250-400 words (student response length)
- **Required:** Every module must have essay-response + critical-analysis activities

**Essay activity in YAML:**
```yaml
- type: essay-response
  id: c1-XX-essay-01
  title: 'Есе: Порівняльний аналіз'
  prompt: |
    Напишіть порівняльне есе (250-400 слів): "[Figure 1] та [Figure 2]"

    Вимоги:
    - Використайте лексику та граматику модуля
    - Порівняйте підходи, досягнення, спадщину двох постатей
    - Використайте цитати з первинних джерел
  rubric:
    - criterion: Мовна якість
      weight: 40
      description: Граматика, біографічна лексика, складність речень
    - criterion: Використання матеріалу
      weight: 30
      description: Цитування джерел, лексика модуля
    - criterion: Порівняльний аналіз
      weight: 20
      description: Логічне порівняння постатей
    - criterion: Структура
      weight: 10
      description: Організація, зв'язність
```

---

## Biography-Specific Activities

### CRITICAL: Language Practice, Not Biographical Recall

<critical>

**These are LANGUAGE lessons that use biography as context, NOT biography tests taught in Ukrainian.**

**The Golden Rule:** "Can the learner answer this without reading the Ukrainian text?"
- **If YES** → Rewrite (tests biographical recall, not language)
- **If NO** → Keep (tests Ukrainian comprehension)

### Examples: GOOD vs BAD Activities

**❌ BAD (Tests Biographical Facts):**
```markdown
1. Шевченко народився в [___] році.
   > [!answer] 1814
```
Problem: Tests dates. No language learning.

**❌ BAD (Tests Factual Recall):**
```markdown
1. Хто викупив Шевченка з кріпацтва?
   - [x] Група митців та меценатів
```
Problem: Tests biographical knowledge from memory.

**✅ GOOD (Tests Ukrainian Collocations):**
```markdown
1. Згідно з текстом, Шевченко [___] визначну роль у розвитку української літератури.
   > [!answer] відіграв
   > [!options] відіграв | зробив | мав | дав
```
Why GOOD: Tests fixed collocation (відіграти роль), requires reading Ukrainian text.

**✅ GOOD (Tests Reading Comprehension):**
```markdown
1. Як автор характеризує вплив цієї постаті на українську культуру?
   - [x] Автор підкреслює революційний характер її творчості
```
Why GOOD: Requires understanding how the MODULE describes the figure's influence.

**Key phrases to use:**
- "Згідно з текстом..."
- "Як автор характеризує..."
- "Який внесок автор виділяє..."

**Never ask:**
- "У якому році народився/померла..." (tests dates)
- "Де навчався/жила..." (tests facts)
- "Хто був..." (tests biographical knowledge)

</critical>

---

### Activity Mix for Biography Modules (per config.py)

**Total: 4-9 activities** (seminar-style, quality over quantity)

**REQUIRED activity types:**
- `reading` - External reading assignments with linguistic analysis
- `essay-response` - 250-400 word essay (in YAML only, NO model answer in markdown)
- `critical-analysis` - Deep analytical questions

**OPTIONAL activity types:**
- `comparative-study` - Cross-figure or cross-era comparisons
- `authorial-intent` - Analysis of the figure's own writings
- `quiz` - ONLY for conceptual questions (NOT factual recall)

**FORBIDDEN activity types (per config.py):**
- match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/c1-XX-biography.yaml`:**

```yaml
- type: reading
  id: c1-XX-reading-01
  title: 'Аналіз первинного джерела'
  resource:
    type: primary_source
    url: 'https://...'
    title: 'Лист/Промова/Твір'
  tasks:
    - 'Який регістр використовує автор? Наведіть приклади.'
    - 'Знайдіть три приклади емоційно забарвленої лексики'

- type: essay-response
  id: c1-XX-essay-01
  title: 'Есе: Порівняльний аналіз'
  prompt: |
    Напишіть порівняльне есе (250-400 слів)...
  rubric:
    - criterion: Мовна якість
      weight: 40

- type: critical-analysis
  id: c1-XX-analysis-01
  title: 'Критичний аналіз спадщини'
  questions:
    - 'Як сучасна українська культура оцінює внесок цієї постаті?'
    - 'Які аспекти діяльності залишаються дискусійними?'
```

---

## Seminar-Style Activity Examples

**Per config.py, C1-BIO modules use ONLY seminar-style activities.** Traditional drill activities (fill-in, match-up, error-correction, group-sort, etc.) are FORBIDDEN.

### 1. Reading Activity

```yaml
- type: reading
  id: c1-bio-XX-reading-01
  title: 'Аналіз первинного джерела'
  resource:
    type: primary_source
    url: 'https://...'
    title: 'Лист/Промова постаті'
  tasks:
    - 'Який регістр використовує автор? Наведіть приклади.'
    - 'Знайдіть три приклади емоційно забарвленої лексики'
    - 'Порівняйте мову автора з сучасною українською'
```

### 2. Essay-Response Activity

```yaml
- type: essay-response
  id: c1-bio-XX-essay-01
  title: 'Есе: Порівняльний аналіз'
  prompt: |
    Напишіть порівняльне есе (250-400 слів):
    "[Figure 1] та [Figure 2]: Порівняльний аналіз внеску"

    Вимоги:
    - Використайте лексику модуля
    - Наведіть цитати з первинних джерел
  rubric:
    - criterion: Мовна якість
      weight: 40
      description: Граматика, біографічна лексика, складність речень
    - criterion: Використання матеріалу
      weight: 30
      description: Цитування джерел, лексика модуля
```

### 3. Critical-Analysis Activity

```yaml
- type: critical-analysis
  id: c1-bio-XX-analysis-01
  title: 'Критичний аналіз спадщини'
  questions:
    - 'Як сучасна українська культура оцінює внесок цієї постаті?'
    - 'Які аспекти діяльності залишаються дискусійними?'
    - 'Як деколонізаційний підхід змінює оцінку цієї постаті?'
```

### 4. Comparative-Study Activity (Optional)

```yaml
- type: comparative-study
  id: c1-bio-XX-compare-01
  title: 'Порівняльний аналіз'
  figures:
    - '[Figure 1]'
    - '[Figure 2]'
  aspects:
    - 'Епоха та контекст'
    - 'Основний внесок'
    - 'Сучасне значення'
```

### 5. Quiz (Conceptual Only)

**Quiz is allowed but ONLY for conceptual questions, NOT factual recall:**

```yaml
- type: quiz
  id: c1-bio-XX-quiz-01
  title: 'Концептуальний аналіз'
  items:
    - question: 'Згідно з текстом, як автор характеризує вплив цієї постаті?'
      options:
        - text: 'Автор підкреслює революційний характер її творчості'
          correct: true
        - text: 'Автор оцінює її як консервативну фігуру'
          correct: false
      explanation: 'У тексті автор наголошує на...'
```

---

## Engagement Boxes for Biography Modules

```markdown
> 💡 **Чи знали ви?**
>
> [Surprising fact about the figure]

> 📜 **Первинне джерело**
>
> [Quote from letters, speeches, or works]

> 🏛️ **Історичний контекст**
>
> [Background information about the era]

> ⚠️ **Деколонізація**
>
> [Challenge Russian/Soviet myths]

> 🌍 **Сучасна Україна**
>
> [How figure is remembered today]

> 📚 **Рекомендоване читання**
>
> [Ukrainian-language sources for further study]
```

---

---

## Content Structure Note

### Vocabulary & Activities
**CRITICAL:** Do NOT add `## Vocabulary` or `## Activities` headers. These sections are injected automatically from:
- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`

The build system will inject these sections at build time.
**Example `vocabulary/c1-XX-biography.yaml`:**

```yaml
items:
- lemma: постать
  ipa: /pɔˈstɑtʲ/
  translation: figure/personality
  pos: noun
  gender: f
  note: історична постать
- lemma: спадщина
  ipa: /spɑˈdʃt͡ʃɪnɑ/
  translation: legacy/heritage
  pos: noun
  gender: f
  note: інтелектуальна спадщина
```

**Why YAML sidecar:**
- Validates schema automatically
- Ensures consistent formatting
- Enables programmatic processing
- Audit validates this exact format for C1+

---

## Module Breakdown: C1.3 Biographies

### Era Distribution (65 modules)

| Era | Modules | Count | Focus |
|-----|---------|-------|-------|
| Pre-modern | M36-45 | 10 | Kyivan Rus, medieval figures |
| Cossack era | M46-55 | 10 | Hetmans, Sich leaders, diplomats |
| Imperial era | M56-70 | 15 | Writers, artists, activists under Russian rule |
| Revolutionary | M71-78 | 8 | UNR, Sich Riflemen, early Soviet |
| Soviet era | M79-88 | 10 | Dissidents, executed renaissance, WWII |
| Independence | M89-100 | 12 | Contemporary figures, Maidan, war heroes |

### Gender Balance Requirement

- **Target:** Minimum 30% women (20+ modules)
- **Domains:** Literature, arts, science, politics, military, activism
- **Era representation:** Women from each major era

---

## Decolonization Guidelines

### Required Perspective Corrections

| Figure | Colonial Myth | Ukrainian Reality |
|--------|---------------|-------------------|
| Shevchenko | "Russian poet" | Ukrainian poet persecuted by Russian Empire |
| Mazepa | "Traitor" | Defender of Ukrainian autonomy |
| Hrushevsky | "Nationalist" | Historian documenting Ukrainian statehood |
| UPA figures | "Nazis" | Independence fighters in complex WWII context |

### Language Sensitivity

- Use "Московське царство" before 1721
- Use "Російська імперія" for 1721-1917
- Avoid Soviet-era designations ("Malorossiya", "Little Russia")
- Emphasize Ukrainian agency, not victimhood

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/c1-module-template.md`
- **C1 Curriculum Plan:** `docs/l2-uk-en/C1-CURRICULUM-PLAN.md` (M36-100 specifications)
- **B2 History Template:** `docs/l2-uk-en/templates/b2-history-module-template.md`

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
