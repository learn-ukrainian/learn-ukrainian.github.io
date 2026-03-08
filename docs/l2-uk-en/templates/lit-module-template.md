# LIT Module Template

**Purpose:** Reference template for creating LIT modules (LIT-001-030: Ukrainian Literature & Classics specialization track)

**Based on:** Existing LIT-001 and LIT-005 modules, LIT Curriculum Plan

**Prerequisite:** C1 Core (Strict)

**Related Curriculum Plan:** `docs/l2-uk-en/LIT-CURRICULUM-PLAN.md`

<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст|Розминка
  - Текст і аналіз
  - Обговорення
  - Підсумок
  - Потрібно більше практики?
  pedagogy: Seminar
  min_word_count: 5000
  required_callouts: []
  description: LIT modules use graduate-level seminar approach with literary analysis
-->

---

## ⚠️ CRITICAL: LIT Track vs C1 Literature

**This template is ONLY for LIT track modules (LIT-001 to LIT-030).**

C1 core curriculum has its own literature modules (C1.6 Phase: M146-160) which use:

- Template: `c1-literature-module-template.md`
- Location: `curriculum/l2-uk-en/c1/`
- Different pedagogy (C1 language mastery, not graduate seminar)

**If you're creating C1 literature modules, STOP. Use the C1 template instead.**

---

## ⚠️ BEFORE WRITING: Check Reference Modules!

**CRITICAL:** Before creating any new LIT module, consult the archived reference modules for research material:

📂 **Location:** `curriculum/l2-uk-en/lit/reference/`

**Available reference modules:**

- `module-LIT-001.md` - Kotliarevsky biography (~54k words)
- `module-LIT-002.md` - Eneida Part I (~52k words)
- `module-LIT-003.md` - Eneida vocabulary analysis (~49k words)
- `module-LIT-004.md` - Eneida military terms (~47k words)
- `module-LIT-005.md` - Natalka Poltavka (~48k words)
- `module-LIT-006.md` - Kvitka-Osnovianenko (~51k words)

**Use these for:**

1. ✅ **Historical facts** - Pre-researched biographical details, dates, events
2. ✅ **Vocabulary lists** - Literary and historical terms already compiled
3. ✅ **Essay topics** - Analytical questions and model answers
4. ✅ **Engagement box ideas** - Interesting facts and cultural insights
5. ✅ **Reading recommendations** - Primary sources and scholarly articles
6. ✅ **Content inspiration** - Structure, tone, analytical depth

**DO NOT copy-paste verbatim** - use as research reference and adapt to this template structure.

---

## 🆘 SYNTHESIS GUIDE: What if there is NO reference module?

If you are compelled to create a module from scratch (e.g., Kvitka-Osnovianenko modules 07-10) without a direct 50k-word reference source:

### 1. The "Bulk Content" Strategy (Crucial for Word Count)

- **Problem:** It is extremely difficult to generate 5000+ words of *pure analysis* from scratch without hallucinating.
- **Solution:** You MUST include large blocks of the **original public domain text** (from UkrLib) directly in the `Reading Hall` or `Analysis` sections.
- **Quantity:** Include at least **3-4 full pages (1000-1500 words)** of the original text as indented blockquotes (`> text`) or within the `🏛️ Читальна Зала` section.
- **Format:** Present these as "Key Excerpts for Analysis" and intersperse them with your philological commentary.

### 2. Strict Transliteration/Latin Prohibition

- The audit script has **ZERO TOLERANCE** for Latin characters in LIT modules.
- **Forbidden:** `(Diminutives)`, `(Sehnsucht)`, `(humility)`, `(Innapyt)`.
- **Allowed:** ONLY specialized linguistic terms if absolutely necessary (e.g., `*cor*` in Latin), but better to avoid entirely.
- **Check:** Run `grep -P "[a-zA-Z]"` before submitting.

## 🏗️ YAML Architecture (Required)

<critical>
**ESSAY CONTAMINATION PREVENTION:**

Even though LIT modules are analytical, ALL specific Essay Prompts and complete Model Answers MUST reside in `activities/{slug}.yaml`.

- **DO NOT** include `## Есе` or `## Аналітичний практикум` headers in the Markdown.
- The Markdown should contain the **Lecture Prose** (the analysis itself), but the **Tasks** based on that analysis go in YAML.
</critical>

LIT modules now follow a **multi-file architecture**.

| Component      | Location                     | Description                                        |
| -------------- | ---------------------------- | -------------------------------------------------- |
| **Metadata**   | `lit/meta/{slug}.yaml`       | Title, subtitle, tags, objectives, focus.          |
| **Vocabulary** | `lit/vocabulary/{slug}.yaml` | 3-column items (lemma, translation, notes).        |
| **Activities** | `lit/activities/{slug}.yaml` | Essays, debates, and structured **reading** tasks. |
| **Lesson**     | `lit/{slug}.md`              | **CLEAN** narrative (lecture) only.                |

---

### 3. Header Hierarchy (Markdown)

- **H1 (`#`)**: ONLY for the Module Title (`# Ukrainian Title`).
- **H2 (`##`)**: For lesson sections (`## Частина I: ...`).
- **PROHIBITED**: DO NOT include `# Словник`, `# 🏛️ Читальна Зала`, or `# ✍️ Аналітичний Практикум` in the Markdown file. These are injected automatically from YAML.

---

## Quick Reference Checklist

Before submitting a LIT module, verify:

### File Structure

- [ ] **Clean Markdown:** Main file has NO frontmatter, NO vocabulary table, and NO activity lists.
- [ ] **Meta Sidecar:** Created in `meta/` with correct `focus: literature`.
- [ ] **Vocab Sidecar:** Created in `vocabulary/` with 30-40 items.
- [ ] **Activities Sidecar:** Created in `activities/` containing essays and reading tasks.

### Content Requirements

- [ ] **Word count:** 5000+ words (core prose narrative).
- [ ] **Reading Hall (YAML):** Structured as `type: reading` activities with tasks and links.
- [ ] **Analytical Workshop (YAML):** Structured as `type: essay` or `type: debate`.

### Essay Requirements

- [ ] **Analytical essays:** 1-2 essay prompts (300-500 words each)
- [ ] **Model answers:** ALL essay prompts include complete model answers
- [ ] **Critical thinking:** Essays require analysis, comparison, argumentation

### Reading Resources

- [ ] **External links:** UkrLib or other Ukrainian literary resources
- [ ] **Primary texts:** Links to full original works
- [ ] **Secondary sources:** Critical/scholarly resources

### Immersion & Quality

- [ ] **Immersion:** 100% Ukrainian (English ONLY in MDX description field)
- [ ] **Academic rigor:** University-level literary criticism
- [ ] **Cultural accuracy:** Historical facts verified, no anachronisms
- [ ] **No traditional activities:** LIT modules are content-based, not activity-based

---

## What Makes LIT Different from C1/C2

| Aspect         | C1/C2 Core                  | LIT Track                        |
| -------------- | --------------------------- | -------------------------------- |
| **Philosophy** | General language mastery    | Literary/cultural specialization |
| **Word count** | 2000-2200+                  | 5000+ (core analysis + excerpts) |
| **Vocabulary** | 35-40 general               | 30-40 literary/historical        |
| **Structure**  | Grammar/vocab/activities    | Pure content + essays            |
| **Activities** | 14-16 interactive           | 0 traditional (essay-based only) |
| **Focus**      | Language skills             | Philological analysis            |
| **Texts**      | Excerpts (500-1000 words)   | Full works (external links)      |
| **Pedagogy**   | TTT/CBI/Creative Production | Academic seminar style           |

**Key shift:** LIT is a **graduate-level literature seminar**, not a language course. It assumes C1 mastery and focuses on cultural/historical depth.

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

**See:** `claude_extensions/phases/stage-4-review-fix.md` Section 9 for detailed naturalness criteria.

**For batch scanning:** Use `/scan-naturalness {level} {start} {end}` to scan completed modules.

---

## Module Structure Template

### 1. Frontmatter (MDX)

```yaml
---
sidebar_position: X # Sequential number (1-30)
sidebar_label: '0X. Short Ukrainian Title'
title: 'Full Ukrainian Title'
description: 'LIT-00X: English description for metadata'
---
```

**Notes:**

- `sidebar_position`: Sequential order in LIT track (1-30)
- `sidebar_label`: Brief Ukrainian title for navigation
- `title`: Full Ukrainian module title
- `description`: English metadata for SEO/cataloging only

---

### 2. Module Title and Identity Box

```markdown
# Ukrainian Title

> 🇺🇦 **Ідентичність:** (or **Цитата:** or **Чому це важливо:**)
>
> [2-3 sentences IN UKRAINIAN establishing the cultural/historical significance]
> [Quote from the author, or statement about national importance]
> [Connect to Ukrainian identity, literary tradition, or cultural memory]
```

**Example (Author Biography module):**

```markdown
# Молодий Шевченко

> 🇺🇦 **Ідентичність:**
> Тарас Шевченко — це не просто поет. Це символ України. Його доля — кріпак, що став генієм — втілює весь трагізм і велич нації. Без Шевченка немає української ідентичності. Він перетворив приватне страждання на національний епос.
```

**Example (Literary Work module):**

```markdown
# Заповіт

> 🇺🇦 **Цитата:**
> "Як умру, то поховайте / Мене на могилі, / Серед степу широкого, / На Вкраїні милій..."
>
> Ці рядки знає кожен українець. Це наш національний "гімн смерті" — заповіт поета, що став заповітом нації.
```

---

### 3. Підсумок Section

```markdown
# Підсумок

[150-200 word overview IN UKRAINIAN explaining:]

- What this module covers (author/work/period/theme)
- Why it matters to Ukrainian literature/culture
- What students will learn (historical context, literary analysis, cultural significance)
- How it connects to previous/next modules in the LIT track
```

**Example:**

```markdown
# Підсумок

Цей модуль присвячений аналізу "Заповіту" Тараса Шевченка — найвідомішого вірша української літератури. Ми розглянемо не тільки текст, а й його місце в національній культурі. Ви дізнаєтесь, чому ці 14 рядків стали політичним маніфестом, як імперська цензура намагалася їх заборонити, і чому "Заповіт" звучить на кожній важливій події (від весіль до похорон). Ми проведемо граматичний аналіз тексту, розкриємо символіку образів (могила, степ, Дніпро, кайдани), і обговоримо, чому цей вірш — це національна ідея у концентрованій формі.
```

---

### 4. Content Sections (Частини I-XX)

**Structure:** 15-20 themed sections, 5000+ words total

```markdown
# Частина I: [Section Title] 📖/🕯️/👤/🎭 (optional emoji)

[300-500 words of deep analysis]

## 1. Subsection Title

[Historical/biographical/analytical content]

**Key points:**

- Point 1
- Point 2
- Point 3

## 2. Subsection Title

[Continue analysis]

:::note **Historical Parallel** (or **Linguistic Insight**, **Cultural Context**, etc.)
[Engagement box content IN UKRAINIAN]
:::

---

# Частина II: [Section Title]

[Continue with next major theme]

[...]
```

**Section Types (Mix as appropriate):**

1. **Biographical Sections** (Author modules):
   - Early life, education, formative experiences
   - Professional career, key relationships
   - Political involvement, controversies
   - Legacy, influence on later writers

2. **Literary Analysis Sections** (Work modules):
   - Plot summary and structure
   - Stylistic devices (metaphor, irony, symbolism)
   - Themes and motifs
   - Language and register analysis
   - Historical/cultural context of creation

3. **Historical Context Sections**:
   - Political situation (e.g., Ruin period, Imperial censorship)
   - Social conditions (e.g., serfdom, class structure)
   - Literary movements (e.g., Romanticism, Realism)
   - Cultural influences (European, Russian, Polish)

4. **Cultural Significance Sections**:
   - Reception history (how work was received)
   - Influence on Ukrainian identity
   - Modern interpretations
   - Place in canon

---

### 5. Engagement Boxes (6-8 boxes throughout content)

**LIT Engagement Box Types:**

```markdown
> [!important] **Psychological Insight** (or **Didactic Moment**, **Key Concept**, etc.)
>
> [Academic insight IN UKRAINIAN about psychology, pedagogy, or key idea]

> [!cultural] **Спадщина у Бронзі** (or **Культурний Контекст**, **Національна Пам'ять**, etc.)
>
> [Cultural/historical significance IN UKRAINIAN]

> [!warning] **Myth Buster**
>
> **Міф:** [Common misconception]
> **Правда:** [Historical truth with evidence]

> [!note] **Historical Parallel** (or **Літературна Паралель**, **Факт Біографії**, etc.)
>
> [Comparative or contextual information IN UKRAINIAN]

> [!tip] **Лінгвістичний Нюанс** (or **Стилістична Особливість**, **Термінологія**, etc.)
>
> [Language/style analysis IN UKRAINIAN]

> [!model-answer] **Модель Тези** (Used in essay section)
>
> - **[Argument 1]:** [Explanation]
> - **[Argument 2]:** [Explanation]
> - **Висновок:** [Conclusion]
```

**Critical:** ALL engagement boxes in Ukrainian. Use to:

- Break up long prose sections
- Highlight key insights
- Provide comparative context
- Debunk myths
- Offer linguistic analysis

---

### 6. Vocabulary Section (Словник)

**CRITICAL:** Vocabulary must be defined in `vocabulary/{slug}.yaml`. Do NOT embed a vocabulary table in Markdown.

**Example `vocabulary/lit-001-kotliarevsky.yaml`:**

```yaml
items:
  - lemma: травестія
    translation: travesty (genre)
    note: комічне наслідування
  - lemma: бурлеск
    translation: burlesque
    note: стиль грубого комізму
```

**Vocabulary Types:**

- **Literary terms:** Genre, style, device names (травестія, метафора, іронія)
- **Historical terms:** Political/social concepts (Гетьманщина, кріпацтво, Руїна)
- **Cultural terms:** Traditional practices, beliefs (весільний обряд, рушники)
- **Author vocabulary:** Unique words/phrases from the literary work
- **Archaic/dialectal:** Old forms, regional variants

---

### 7. Reading Resources (Читальна Зала)

**CRITICAL:** Reading tasks must be defined in `activities/{slug}.yaml` as `type: reading`.

<critical>

**Required fields:**
- `id:` - REQUIRED unique identifier for linking to analytical activities (e.g., `reading-bio`, `reading-poem`)
- `title:` - Display title
- Either `text:` (inline) OR `resource:` (external URL) - NOT both
- `tasks:` - Array of reading comprehension questions

**URL Verification (MANDATORY):**
Before using any external URL, you MUST verify it points to the correct content:
1. Open the URL in a browser
2. Confirm the page is about the intended author/work
3. Check the page title contains the author's name

Common UkrLib author IDs (verify before using):
- Котляревський: tid=1672
- Шевченко: tid=57
- Куліш: tid=1621
- Нечуй-Левицький: tid=1646
- Франко: tid=71

> ⚠️ **Source Verification:** When using Ukrainian Wikipedia (uk.wikipedia.org), cross-reference key claims against UkrLib or academic sources where possible.

</critical>

**Format 1: External Resource (for biographies, full texts)**

```yaml
- type: reading
  id: reading-bio                    # REQUIRED for linking
  title: Біографія Котляревського
  resource:
    type: Biography
    url: https://www.ukrlib.com.ua/bio/printit.php?tid=1672  # VERIFY this URL!
    title: Іван Котляревський. Життя і творчість
  tasks:
    - Знайдіть паралелі між життям автора і сюжетом "Енеїди".
    - Як вплинула військова служба на творчість?
```

**Format 2: Inline Primary Source (for poems, short excerpts)**

```yaml
- type: reading
  id: reading-testament              # REQUIRED for linking
  title: 'Джерело: Заповіт'
  source: 'Тарас Шевченко (1845)'    # Attribution (author, year)
  text: |
    Як умру, то поховайте
    Мене на могилі,
    Серед степу широкого,
    На Вкраїні милій...
  tasks:
    - Які географічні образи використовує поет?
    - Яка роль імперативу в тексті?
```

**Linking to Analytical Activities:**

```yaml
# Reading defines the id
- type: reading
  id: reading-bio          # ← This ID
  ...

# Essay/analysis references it
- type: essay-response
  source_reading: reading-bio  # ← Must match the reading id
  ...
```

**Resource Types:**

- **Primary texts:** Full literary works (UkrLib links)
- **Biographies:** Author life stories
- **Critical essays:** Scholarly analysis
- **Historical documents:** Letters, diaries, manifestos
- **Modern interpretations:** Contemporary critical perspectives

---

### 8. Analytical Essays (Аналітичний Практикум)

**CRITICAL:** Essays must be defined in `activities/{slug}.yaml` as `type: essay-response`.

**Example `activities/lit-001-kotliarevsky.yaml`:**

```yaml
- type: essay-response
  title: Роль особистості
  prompt: "Існує думка, що поява 'Енеїди' була випадковістю. Проаналізуйте роль автора."
  model_answer: "Поява Котляревського — це щасливий 'генетичний збій'..."
```

**Essay Requirements:**

- **1-2 essays per module** (minimum 1)
- **300-500 words** each
- **Model answers required** for all essay prompts
- **Critical thinking:** Analysis, comparison, argumentation
- **Academic tone:** University-level literary criticism

---

### 9. Source-Evaluation Activity

**Use for analyzing literary criticism, historical reception, and scholarly interpretations:**

```yaml
- type: source-evaluation
  title: "Оцінка джерела: Критична стаття/Рецензія/Маніфест"
  instruction: "Застосуйте метод критичного аналізу до цього літературознавчого джерела."
  source_text: |
    [Excerpt from literary criticism, contemporary review, or manifesto — 100-200 words]
  source_metadata:
    author: "[Critic/writer name]"
    date: "[Year of publication]"
    type: "[criticism/review/manifesto/memoir]"
    context: "[Literary movement, political context, relationship to author]"
  evaluation_criteria:
    - authorship
    - date_and_context
    - intended_audience
    - purpose_and_bias
    - omissions
  guiding_questions:
    - "Яку літературну позицію представляє критик?"
    - "Як історичний контекст впливає на оцінку?"
    - "Які естетичні критерії використовує автор?"
    - "Що ця критика замовчує або применшує?"
  model_evaluation: |
    **1. Авторство:** [Who wrote it, their literary circle]
    **2. Контекст:** [When written, literary debates of the era]
    **3. Естетична позиція:** [What values the critic promotes]
    **4. Упередження:** [Ideological, aesthetic, personal biases]
    **5. Історична цінність:** [What this source reveals about reception history]
```

### 10. Debate Activity

**Use for contested interpretations of literary works and authors' legacies:**

```yaml
- type: debate
  title: "Дискусія: [Contested Literary Question]"
  instruction: "Проаналізуйте конкуруючі інтерпретації та сформулюйте власну позицію."
  debate_question: "[The contested question about interpretation or legacy]"
  historical_context: |
    [Background on the literary controversy — 50-100 words]
  positions:
    - name: "[Position 1 — e.g., Народницька інтерпретація]"
      proponents: "[Critics, scholars who hold this view]"
      argument: "[Core interpretive argument]"
      evidence:
        - "[Textual evidence]"
        - "[Historical evidence]"
      weaknesses:
        - "[Limitation of this reading]"
    - name: "[Position 2 — e.g., Модерністська інтерпретація]"
      proponents: "[Who holds this view]"
      argument: "[Core argument]"
      evidence:
        - "[Evidence]"
      weaknesses:
        - "[Critique]"
    - name: "[Position 3 — e.g., Радянська інтерпретація]"
      proponents: "[Soviet critics]"
      argument: "[Their reading]"
      evidence:
        - "[Their claimed evidence]"
      weaknesses:
        - "[Why this is problematic — decolonization perspective]"
  analysis_tasks:
    - "Які текстуальні докази підтримують кожну позицію?"
    - "Як ідеологія критика впливає на інтерпретацію?"
    - "Як сучасна українська перспектива змінює читання?"
    - "Яку позицію ви вважаєте найбільш переконливою? Чому?"
  model_analysis: |
    [Balanced evaluation of interpretive positions, demonstrating philological
    rigor and awareness of how critical schools shape readings. Graduate-level
    analysis should engage with reception history and decolonization.]
```

**Example contested questions for LIT track:**
- "Котляревський: бурлеск чи національний маніфест?"
- "Чи 'Енеїда' — пародія чи епос?"
- "Шевченко: романтик, реаліст, чи модерніст avant la lettre?"
- "Як читати колоніальну травму в класичних текстах?"

---

## LIT-Specific Pedagogical Notes

### 1. No Traditional Activities

**LIT modules do NOT include:**

- Quiz, fill-in, match-up, true-false, etc.
- Interactive exercises typical of A1-C2 core

**Why:**

- LIT is a **graduate-level seminar**, not a language drill
- Focus is on **reading and analysis**, not skill practice
- Students already have C1 mastery (prerequisite)

**Instead, LIT uses:**

- Deep reading of primary texts (external links)
- Analytical essay writing (300-500 words)
- Critical discussion prompts

### 2. Academic Rigor

**LIT modules assume:**

- **C1+ language proficiency** (students read university-level Ukrainian)
- **Literary/historical knowledge** (students understand literary terms, Ukrainian history)
- **Critical thinking skills** (students can analyze, compare, argue)

**Content should:**

- Provide philological analysis (style, language, devices)
- Contextualize historically/culturally
- Challenge students intellectually
- Avoid oversimplification

### 3. 100% Ukrainian Immersion

**English appears ONLY in:**

- MDX frontmatter `description` field (for metadata/SEO)

**Everything else is Ukrainian:**

- All content sections
- Engagement boxes
- Vocabulary definitions
- Essay prompts and model answers
- Reading resource annotations

**No exceptions.** LIT is a specialization track for advanced learners who have already mastered Ukrainian.

### 4. External Reading (Mandatory)

**Every LIT module MUST include:**

- Links to full primary texts (UkrLib or equivalent)
- Links to biographical/critical sources
- Guidance on what to focus on while reading

**Students are expected to:**

- Read full literary works (not just excerpts)
- Engage with external scholarly sources
- Synthesize information from multiple sources

### 5. Cultural Sensitivity

**When writing about Ukrainian literature:**

- **Decolonize narratives:** Avoid Russian Imperial/Soviet perspectives
- **Center Ukrainian experience:** Focus on Ukrainian cultural autonomy
- **Acknowledge trauma:** Recognize historical oppression (Russification, censorship, executions)
- **Celebrate resilience:** Show how literature resisted erasure

**Example:**

- ❌ "Ukrainian developed from Russian influence"
- ✅ "Ukrainian resisted Russian imperial suppression"

### 6. Complexity Scaling (C1/C2 Core → LIT)

| Feature    | C1 Core                  | C2 Core                   | LIT Track                     |
| ---------- | ------------------------ | ------------------------- | ----------------------------- |
| Word count | 2000+                    | 2200+                     | 5000+ (core + excerpts)       |
| Vocabulary | 35+ general              | 40+ general               | 30-40 literary/historical     |
| Activities | 12+ interactive          | 3-9 (seminar)             | 3-9 (essays only)             |
| Essays     | 1 (400+ words)           | 1-2 (various)             | 1-2 (300-500 words)           |
| Texts      | Excerpts (500-800 words) | Excerpts (600-1000 words) | Full works (external)         |
| Focus      | Language mastery         | Creative production       | Philological analysis         |

---

## Module Type Breakdown (LIT.1-LIT.5)

### Phase LIT.1: Kotliarevsky (M001-005)

**Focus:** Burlesque & folk origins, birth of modern Ukrainian literature

| Module  | Type             | Content Focus                                              |
| ------- | ---------------- | ---------------------------------------------------------- |
| LIT-001 | Biography        | Kotliarevsky's life, historical context (Ruin period)      |
| LIT-002 | Literary Work    | *Eneida* Part I - burlesque style, Trojan-Cossack parallel |
| LIT-003 | Vocabulary Study | Food/feast vocabulary from *Eneida*                        |
| LIT-004 | Vocabulary Study | Military/war vocabulary from *Eneida*                      |
| LIT-005 | Literary Work    | *Natalka Poltavka* - sentimentalism, theater               |

**Word count:** 5000+ per module

### Phase LIT.2: Kvitka-Osnovianenko (M006-010)

**Focus:** Sentimentalism, prose development, ethnography

**Word count:** 5000+ per module

### Phase LIT.3: Taras Shevchenko (M011-020)

**Focus:** Romanticism, synthesis of folk and Church Slavonic, modern standard

**Word count:** 5000+ per module (10 modules - major author)

### Phase LIT.4: Kulish & Kostomarov (M021-025)

**Focus:** Europeanism, historical novels, language reform

**Word count:** 5000+ per module

### Phase LIT.5: Nechuy-Levytsky (M026-030)

**Focus:** Realism, village life, conversational language

**Word count:** 5000+ per module

---

## Common Pitfalls to Avoid

### ❌ DON'T:

- **Don't add traditional activities** — LIT is essay-based, not drill-based
- **Don't oversimplify** — This is graduate-level content
- **Don't use English explanations** — 100% Ukrainian immersion (except MDX description)
- **Don't skip model answers** — Every essay prompt needs a complete model
- **Don't ignore historical context** — Literature exists in history
- **Don't romanticize oppression** — Acknowledge trauma honestly

### ✅ DO:

- **Provide deep philological analysis** — Style, language, devices
- **Contextualize historically/culturally** — Politics, society, movements
- **Include external reading links** — UkrLib, scholarly sources
- **Write model answers for essays** — Show students how to argue
- **Use engagement boxes liberally** — Break up long prose, highlight insights
- **Maintain academic rigor** — This is university-level study

---

## Pre-Submission Checklist

### Content

- [ ] 5000+ words before vocabulary/resources
- [ ] 30-40 vocabulary items in 3-column format
- [ ] 15-20 content sections (Частини I-XX)
- [ ] Biographical/historical/analytical depth
- [ ] 6-8 engagement boxes (all in Ukrainian)
- [ ] Academic rigor throughout

### Essays

- [ ] 1-2 analytical essay prompts (300-500 words)
- [ ] Model answers for ALL essay prompts
- [ ] Critical thinking questions provided
- [ ] Academic tone maintained

### Resources

- [ ] UkrLib or equivalent links to primary texts
- [ ] Links to biographical/critical sources
- [ ] Reading guidance provided (what to focus on)

### Immersion & Quality

- [ ] 100% Ukrainian (English only in MDX description)
- [ ] University-level literary criticism
- [ ] Historical accuracy verified
- [ ] Cultural sensitivity maintained
- [ ] No traditional activities included

---

## Related Documentation

- **LIT Curriculum Plan:** `docs/l2-uk-en/LIT-CURRICULUM-PLAN.md`
- **C1 Module Template:** `docs/l2-uk-en/templates/c1-module-template.md` (for comparison)
- **C2 Module Template:** `docs/l2-uk-en/templates/c2-module-template.md` (for comparison)
- **Module Richness Guidelines:** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- **Ukrainian State Standard 2024:** `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt`

---

## Example Module References

**Existing LIT modules (for structural reference):**

- `docusaurus/docs/lit/module-01.mdx` — LIT-001: Котляревський (Biography)
- `docusaurus/docs/lit/module-05.mdx` — LIT-005: Наталка Полтавка (Literary Work)

---

## Clean MD Architecture Note

### Activities, Vocabulary, and External Resources

**CRITICAL:** Do NOT add `## Activities`, `## Vocabulary`, or `## External Resources` headers to the Markdown file. These sections are automatically injected by the build system from the corresponding YAML sidecars:

- `activities/{slug}.yaml` → `## Activities` section
- `vocabulary/{slug}.yaml` → `## Vocabulary` section
- `docs/resources/external_resources.yaml` (filtered by `module_id`) → `## External Resources` section

The module structure follows **Clean MD architecture**: Markdown contains narrative content only, YAML sidecars contain structured data.

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
**Maintainer:** Claude (The Content Developer)
