# Module Quality Standards

> **Single source of truth for module richness, activity requirements, and templates.**

---

## Quick Reference

<critical>


### Content Philosophy & Standards

> [!important] **Linguistic Purity & Source Authority**
>
> All content must adhere to strict linguistic standards:
> *   **No Surzhyk:** Zero tolerance.
> *   **No Transliteration:** Cyrillic only (except A1.1).
> *   **Active Syntax:** Avoid passive voice.
> *   **Source Hierarchy:** Verification via Goroh, Grinchenko, Antonenko-Davydovych.
>
> **Full Guidelines:** [`claude_extensions/quick-ref/philosophy.md`](claude_extensions/quick-ref/philosophy.md)


### Resource Section Placement

> [!important]
> **Standardized Module Structure:**
>
> All B1+ modules follow this layout:
> ```markdown
> ---
> YAML frontmatter (including optional `resources:` in YAML)
> ---
>
> # Title (H1 - from YAML title field)
>
> > Introduction hook (🎯 **Чому це важливо** or similar - optional)
>
> > [!resources] 🎧 External Resources
> > **Type:** [Title](url) — Description
>
> ## Diagnostic / Діагностика
> ```
>
> **Key Rules:**
> 1. H1 Title MUST exist immediately after YAML
> 2. Introduction hook (if present) comes BEFORE resources
> 3. Resources callout comes AFTER intro, BEFORE first `##` header
> 4. First content section is typically `## Diagnostic` or `## Діагностика`


### Content Requirements by Level (Instructional Core Only*)

| Metric | A1 | A2 | B1 | B2 | C1 | C2 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Module Range** | M01-34 | M01-50 | **M01-80** | **M01-135** | M01-115 | M01-80 |
| **Core Word Count** | **Graduated*** | **1000+** | **1500+** | **1750+** | **2000+** | **2000+** |
| **Immersion (% Ukr)** | **10-40%*** | **40-55%*** | **50-80%*** | **60-90%*** | **90-100%** | **98-100%** |
| **Min Vocab Words** | 20+ | 25+ | 20+/30+ | 20+/30+ | 25+ | 25+ |
| **Example Sentences** | 12+ | 18+ | 24+ | 24+ | 30+ | 32+ |
| **Engagement Boxes** | 3+ | 4+ | 5+ | 6+ | 7+ | 8+ |
| **Mini-Dialogues** | 2+ | 3+ | 4+ | 4+ | 5+ | 5+ |

*\*Instructional Core Definition: Counts ONLY Warm-up/Presentation (PPP); Diagnostic/Analysis/Deep Dive (TTT); or Introduction/Narrative/Analysis/Grammar in Context (CLIL). Excludes tables, practice drills, and activity instructions.*

> **A1 Core Word Count Graduation:**
> *   **M01-M05 (Phonetics):** **300 - 450 words**. Focus on high-quality English phonetic explanation & historical context.
> *   **M06-M10 (First Verbs):** **500 - 650 words**. Introduce simple Ukrainian narratives.
> *   **M11-M34 (Navigation):** **750+ words**. Full narrative standard.
>
> **LIT Track (Specialization) Target:**
> *   **Word Count:** **2500+ words**.
> *   **Rationale:** No gamified activities. Focus is on deep reading (Long-form articles, Literary Criticism, Biography).
> *   **Structure:** Essentially a university seminar reader.

> **Graduated Immersion (A1 Detail) — Tied to Learner Capability:**
> *   **M01-M05 (Cyrillic):** **10-15%** — Learner cannot read yet. Ukrainian = letters/words being taught. Heavy English for phonetics, alphabet explanation, historical context.
> *   **M06-M10 (First Words):** **15-25%** — Learner reads but lacks verbs. Ukrainian vocabulary examples, English explanations. No full sentences yet.
> *   **M11-M20 (First Sentences):** **25-35%** — SVO unlocked. Simple Ukrainian sentences and basic dialogues emerge. English for grammar theory.
> *   **M21-M30 (Consolidation):** **35-40%** — Short exchanges, mini-scenarios. **MAX 40% for A1.** English for complex explanations only.

> **Graduated Immersion (A2 Detail) — Phase-Based Progression:**
> *   **A2.1 (M01-20):** **40-45%** — Core case endings (dative, instrumental). Maximized scaffolding for complex grammar.
> *   **A2.2 (M21-40):** **45-50%** — Aspect basics, locative, more cases. Controlled comparison with increased Ukrainian.
> *   **A2.3 (M41-50):** **50-55%** — Pre-B1 runway. Narrative density increases, complex sentences introduced.

> **B1+ Immersion Philosophy — Ukrainian-First Approach:**
> At B1, students learn grammar **IN Ukrainian** — the way native speakers learn in school.
> - **All B1 modules (M01-80):** **90-95%** Ukrainian
> - Grammar explanations in Ukrainian with metalanguage (grammar terms as vocabulary)
> - No English translations except in vocabulary table
> - Engagement boxes, tips, warnings all in Ukrainian
>
> **Why this works:**
> - Immersion makes learning engaging (boring English theory killed motivation)
> - Grammar terminology (недоконаний вид, доконаний вид) becomes usable vocabulary
> - Students can understand Ukrainian grammar resources and discuss with native speakers

> **Immersion Implementation Guide (A2-C2):**
>
> | Level | Target | Write IN UKRAINIAN | Write IN ENGLISH |
> |-------|--------|-------------------|------------------|
> | **A2.1** (M01-20) | **40-45%** | Dialogues, examples, simple instructions | Grammar theory (cases), complex explanations |
> | **A2.2** (M21-40) | **45-50%** | Dialogues, examples, short narratives | Grammar theory (aspect), complex explanations |
> | **A2.3** (M41-50) | **50-55%** | Dialogues, narratives, simple explanations | Complex grammar only |
> | **B1** (M01-80) | **90-95%** | Grammar explanations, narratives, dialogues, examples, engagement boxes | Vocabulary table translations only |
> | **B2** (M01-125) | **95%** | All grammar, all content, all cultural material | Vocabulary table translations only |
> | **C1.1** (M01-20) | **90-100%** | All content except meta-analysis | Limited contrastive linguistics |
> | **C1.2-6** (M21-115) | **95-100%** | Everything | `🔗 Language Link` boxes only |
> | **C2** (M01-80) | **98-100%** | EVERYTHING | Strict <2% allowence for contrastive analysis |
>
> **B1 (90-95%) — Full Ukrainian Grammar Instruction:**
> *   ✅ UKRAINIAN: "Читав — це недоконаний вид. Він показує тривалу дію або процес."
> *   ✅ UKRAINIAN: "Прочитав — це доконаний вид. Він показує завершену дію з результатом."
> *   ✅ UKRAINIAN: All grammar explanations using Ukrainian metalanguage
> *   ✅ UKRAINIAN: All narratives, dialogues, engagement boxes, tips, warnings
> *   ✅ ENGLISH: Only the "Переклад" column in vocabulary tables
>
> **Metalanguage at B1:** Students learn grammar terminology as vocabulary:
> *   доконаний вид (perfective aspect), недоконаний вид (imperfective aspect)
> *   дієслово (verb), іменник (noun), прикметник (adjective), відмінок (case)
> *   підрядне речення (subordinate clause), підмет (subject), присудок (predicate)
>
> **B2 (95%) — Full Ukrainian Immersion:**
> *   ✅ UKRAINIAN: All grammar, all cultural content, all explanations
> *   ✅ UKRAINIAN: Advanced metalanguage (дієприслівник, пасивний стан, функціональний стиль)
> *   ✅ ENGLISH: Only the "Переклад" column in vocabulary tables
>
> **C1 (95%) — Near-total immersion:**
> *   ✅ UKRAINIAN: All grammar, all explanations, all cultural content
> *   ✅ ENGLISH: Only in dedicated `🔗 Language Link` boxes for cross-linguistic awareness
>
> **LIT Track (Specialization) — 95-100% Ukrainian:**
> *   ✅ UKRAINIAN: Everything. Context, analysis, glossaries (UA-UA).
> *   ⚠️ ALLOWED: Up to 5% Latin/Greek scholarly terms (e.g., "damnatio memoriae", "genius loci")
> *   ❌ ENGLISH: Forbidden. No Language Links. No translations.
>
> **C2 (95-100%) — Near-native experience:**
> *   ✅ UKRAINIAN: Everything — learner operates as near-native
> *   ⚠️ ALLOWED: Up to 5% Latin/Greek scholarly terms

### Ukrainian-Only Grammar Patterns (B1+)

**Why Ukrainian-only at B1+?** Students at this level should learn grammar the way native speakers do — in Ukrainian. English explanations were found to be "boring" and disengaging. Ukrainian metalanguage (grammar terms) becomes usable vocabulary.

**Pattern: Full Ukrainian grammar explanation**

```markdown
### Доконаний вид — Результат

Доконаний вид показує дію, яка завершена і має результат.

Коли використовувати доконаний вид:
- **Результат** — дія завершена, є підсумок
- **Одноразовість** — конкретна, окрема дія
- **Послідовність** — спочатку це, потім те

| Приклад | Контекст | Чому доконаний? |
|---------|----------|-----------------|
| Я **прочитав** книгу. | Результат | Книга прочитана |
| Він **написав** листа. | Завершення | Лист готовий |

> [!tip] Порада
> Якщо дія має чіткий кінець, який був досягнутий — це доконаний вид.
```

**Pattern: Ukrainian decision framework**

```markdown
> [!info] Як обрати вид?
>
> | Питання | Якщо ТАК → | Якщо НІ → |
> |---------|------------|-----------|
> | Це одноразова завершена подія? | Доконаний | Перевір далі |
> | Це регулярна/звичайна дія? | Недоконаний | Перевір далі |
> | Це тло для іншої дії? | Недоконаний | Доконаний |
```

**What stays Ukrainian:**
- All example sentences
- All dialogues and narratives
- All cultural context boxes (💡, 🎬, 🎭, 🌍)
- Activity content and instructions
- Simple grammar rules ("Недоконаний = процес")

**What goes English:**
- Conceptual explanations ("Why does aspect exist?")
- Decision frameworks and flowcharts
- English-Ukrainian contrasts (Language Link boxes)
- Metalinguistic analysis

### Activity Requirements by Level

| Level | Activities | Items/Activity | Types | Stage Sequencing |
|-------|------------|----------------|-------|------------------|
| A1 | 8+ | 12+ | 4+ | Recognition → Production (no stages needed) |
| A2 | 10+ | 12+ | 5+ | Recognition → Discrimination → Controlled → Production |
| B1 | 12+ | 14+ | 5+ | Full stage sequence |
| B2 | 14+ | 16+ | 5+ | Full stage sequence, heavier on production |
| C1 | 16+ | 18+ | 5+ | Production-heavy, subtle discrimination |
| C2 | 16+ | 18+ | 5+ | Production-heavy, native-level complexity |

### Mandatory Activity Mix by Level

| Activity Type | A1 | A2 | B1 | B2 | C1 | C2 |
|---------------|----|----|----|----|----|----|
| **fill-in** | 2+ | 2+ | 2+ | 3+ | 2+ | 2+ |
| **match-up** | 2+ | 1+ | 1+ | 1+ | 1+ | 1+ |
| **quiz** | 1+ | 1+ | 1+ | 1+ | 1+ | 1+ |
| **true-false** | 1+ | 1+ | 1+ | 1+ | — | — |
| **group-sort** | 1+ | 1+ | 1+ | 1+ | 1+ | 1+ |
| **anagram** | 2+ (M01-10 only) | ❌ | ❌ | ❌ | ❌ | ❌ |
| **unjumble** | 2+ (M11+ only) | 2+ | 2+ | 2+ | 2+ | 2+ |
| **error-correction** | ❌ | 1+ | 2+ | 2+ | 3+ | 3+ |
| **cloze** | ❌ | 1+ | 1+ | 1+ | 3+ | 3+ |
| **mark-the-words** | ❌ | 1+ | 1+ | 1+ | — | — |
| **dialogue-reorder** | ❌ | 1+ | 1+ | 1+ | 1+ | — |
| **select** | ❌ | opt | 1+ | 1+ | 1+ | 1+ |
| **translate** | ❌ | opt | 1+ | 1+ | 2+ | 2+ |

**Legend:** `2+` = minimum count, `opt` = optional, `❌` = not allowed, `—` = rarely used

**Note:** `observe-first` is a **pedagogical content pattern** (using `> [!observe]` callout inline), not an activity type. Use it before grammar explanations for inductive pattern discovery (recommended B1-B2).

### B1-B2 Grammar vs Vocabulary Activity Priorities

| Focus | Module Range | Priority Activities | Avoid | Rationale |
|-------|--------------|---------------------|-------|-----------|
| **B1-grammar** | M01-45 | error-correction, fill-in, unjumble, cloze | — | Aspect, motion verbs, complex sentences require controlled practice |
| **B1-vocab** | M46-80 | match-up, mark-the-words, translate, quiz | group-sort | Vocabulary acquisition needs recognition/translation, not categorization |
| **B2-grammar** | M01-40 | error-correction, fill-in, unjumble, cloze | — | Passive voice, participles, register require precision drilling |
| **B2-vocab** | M41-125 | match-up, mark-the-words, translate, quiz | group-sort | Phraseology/history vocabulary benefits from matching and translation |

**Grammar Module Focus:** Activities that develop grammatical accuracy through controlled practice and error awareness.

**Vocabulary Module Focus:** Activities that build word recognition and translation fluency. Avoid group-sort (cognitive overload when learning new topic vocabulary).

**C1-C2 Rationale:** At advanced levels, learners need more production practice (cloze ×3, translate ×2) and less basic recognition (mark-the-words removed). Error-correction remains high (×3) for metalinguistic awareness.

### Production Activity Requirements (B1+)

Each B1+ grammar module MUST include at least **2 production activities** to balance recognition-heavy drills.

#### Required Production Types (choose 2+):

**1. Guided Translation (`translate`)**
```markdown
## translate: Переклад з підказками
> Translate to Ukrainian using the target grammar.

1. I was reading all evening. (use: весь вечір)
   > [!answer] Я читав книгу весь вечір.
   > [!hint] Process = imperfective
```

**2. Sentence Transformation (`transform`)**
```markdown
## transform: Зміна виду
> Change the aspect and observe the meaning change.

1. Я читав книгу. (make result-focused)
   > [!answer] Я прочитав книгу.
   > [!explanation] Adding result focus requires perfective.
```

**3. Micro-Writing (`micro-write`)**
```markdown
## micro-write: Короткий текст
> Write 4-6 sentences about [topic] using both aspects.

**Prompt:** Describe your yesterday morning. Use at least 2 imperfective verbs (process) and 2 perfective verbs (completed actions).

**Model answer:**
Вчора вранці я прокинувся о сьомій (pf). Я снідав і дивився новини (impf, impf). Потім я поїхав на роботу (pf). Дорогою я слухав музику (impf).
```

**4. Dialogue Completion (`dialogue-complete`)**
```markdown
## dialogue-complete: Завершіть діалог
> Complete the dialogue using appropriate forms.

А: Що ти ___ (робити) вчора ввечері?
Б: Я ___ (читати) книгу. А потім ___ (подивитися) фільм.
А: І як, ___ (сподобатися)?
```

#### Activity Balance Check (B1-grammar)

| Category | Target | Activity Types |
|----------|--------|----------------|
| Recognition | 4-5 | quiz, match-up, true-false, mark-the-words |
| Controlled Production | 4-5 | fill-in, cloze, error-correction |
| **Free Production** | **2-4** | **translate, transform, micro-write, dialogue-complete** |
| Integrated | 2-3 | unjumble, dialogue-reorder |

**Audit check:** B1-grammar modules failing production balance will show warning in audit output.

### Activity Types Reference (13 Types)

| Activity | Level | Description |
|----------|-------|-------------|
| `quiz` | A1+ | Multiple choice questions |
| `match-up` | A1+ | Match pairs (left/right columns) |
| `fill-in` | A1+ | Gap fill with options |
| `true-false` | A1+ | True/false statements |
| `anagram` | A1 only | Letter unscrambling (phase out by A1.3) |
| `unjumble` | A1+ | Word reordering into sentences |
| `group-sort` | A1+ | Sort items into categories |
| `error-correction` | A2+ | Find and fix errors |
| `cloze` | A2+ | Passage with multiple dropdown blanks |
| `dialogue-reorder` | A2+ | Put dialogue lines in order |
| `mark-the-words` | A2+ | Click/tap words matching criteria |
| `translate` | A2+ | Select correct translation |
| `select` | A2+ | Multi-checkbox selection |

**Content Patterns (not activities):**
- `> [!observe]` - Observe-first pattern discovery callout (use inline before grammar explanations)

### Exercise Stage Sequencing (A2+)

For A2+ modules, sequence activities by pedagogical stage:

1. **🔍 Recognition** — mark-the-words (use `> [!observe]` callouts inline before grammar for pattern discovery)
2. **👂 Discrimination** — select, true-false with subtle distinctions
3. **✏️ Controlled Production** — fill-in, cloze, error-correction
4. **✍️ Free Production** — translate, dialogue-reorder

Add `[stage: xxx]` to activity headers for visual indicators.

### Spiral Review Pattern (B1+ Required)

Each module should include review items from previous module(s) to reinforce retention.

| Module Position | Review Requirements |
|-----------------|---------------------|
| M02-M04 | 3 items from M(n-1) |
| M05+ | 2 items from M(n-1), 1 item from M(n-3) |
| Checkpoints | 5+ items covering entire phase |

**Template:**

```markdown
## quiz: Повторення (М[XX-1])
> Quick review from the previous module.

1. [Question testing M[XX-1] content]
   - [x] correct
   - [ ] distractor
   - [ ] distractor
   > [Explanation referencing previous module]

2. [Question testing M[XX-1] content]
   ...

3. [Question testing M[XX-3] content, if M05+]
   ...
```

**Placement:** Put spiral review quiz as the **first activity** in the Activities section. This warms up learners with familiar content before new challenges.

### Sentence Complexity by Level

| Level | Fill-in Words | Unjumble Words | Clauses | Structure |
|-------|---------------|----------------|---------|-----------|
| A1 | 3-5 | 4-6 | 1 | Simple SVO |
| A2 | 6-8 | 8-10 | 1-2 | + Connectors (і, але, тому що) |
| B1 | 10-14 | 12-16 | 2-3 | + Conditionals, subordination |
| B2 | 12-16 | 14-18 | 3-4 | + Literary style, register |
| C1 | 14-18 | 16-20 | 4+ | + Academic, professional |
| C2 | 16-20 | 18-22 | 4+ | Native-level complexity |

### Time & Vocabulary Targets

| Level | Reading | Practice | Total | New Words/Module |
|-------|---------|----------|-------|------------------|
| A1 | 15 min | 45 min | 1h | 25-30 |
| A2 | 20 min | 45 min | 1h+ | 25-35 |
| B1 | 30 min | 60 min | 1.5h | 30-40 |
| B2 | 40 min | 80 min | 2h | 25-30 |
| C1 | 45 min | 90 min | 2h+ | 30-35 |
| C2 | 45 min | 90 min | 2h+ | 30-35 |

</critical>

---

## Module Types by Level

> **Module types determine audit thresholds.** Use the appropriate type in frontmatter `focus:` field.

### B1 Module Types

| Type | Modules | Words | Vocab | Immersion | Focus |
|------|---------|-------|-------|-----------|-------|
| `B1-grammar` | 01-45 (excl. checkpoints) | 1500+ | 25+ | 90-95% | Grammar acquisition: aspect, motion verbs, complex sentences |
| `B1-vocab` | 46-75 (excl. checkpoints) | 1500+ | 35+ | 90-95% | Thematic vocabulary: regions, professions, media |
| `B1-skills` | 76-79 | 1000+ | 15+ | 90-95% | Receptive skills, reading/listening integration |
| `B1-checkpoint` | 10, 20, 35, 45, 55, 65, 75 | 800+ | 10+ | 90%+ | Review & self-assessment with CEFR rubrics |
| `B1-capstone` | 80 | 1000+ | 10 | 90-95% | Final assessment with comprehensive rubric |

**Note:** All B1 modules use Ukrainian-first approach — grammar explained IN Ukrainian with metalanguage support.

### B2 Module Types

| Type | Modules | Words | Vocab | Immersion | Focus |
|------|---------|-------|-------|-----------|-------|
| `B2-grammar` | 01-40 | 1750+ | 25+ | 95% | Passive voice, participles, register, word formation |
| `B2-vocab` | 41-70 | 1750+ | 35+ | 95% | Phraseology: proverbs, idioms, synonyms |
| `B2-history` | 71-95 | 1400+ | 20+ | 95% | Ukrainian history narratives |
| `B2-biography` | 96-120 | 1400+ | 20+ | 95% | Biographical narratives (24 notable Ukrainians) |
| `B2-checkpoint` | 30, 40, 70, 95, 120 | 1000+ | 10+ | 95% | Phase review & assessment |
| `B2-capstone` | 121-135 | 1200+ | 10 | 95% | Research project & oral defense |

**Note:** B2 achieves full immersion — all grammar terminology and explanations in Ukrainian.

### C1 Module Types

| Type | Modules | Words | Vocab | Immersion | Focus |
|------|---------|-------|-------|-----------|-------|
| `C1-academic` | 01-20 | 1750+ | 24+ | 85-90% | Academic Ukrainian, morphology, syntax |
| `C1-professional` | 21-35 | 1600+ | 24+ | 90-95% | Professional & social register |
| `C1-stylistics` | 36-55 | 1600+ | 24+ | 90-95% | 5 functional styles, rhetoric, argumentation |
| `C1-folk` | 56-80 | 2000+ | 24+ | 95%+ | Folk culture, arts, dialects, Surzhyk |
| `C1-literature` | 81-115 | 2000+ | 24+ | 95%+ | Literary analysis: classics to contemporary |
| `C1-checkpoint` | 20, 35, 55, 80, 95, 115 | 1200+ | 15 | 90-95% | Phase review & CEFR self-assessment |
| `C1-capstone` | 111-112 | 1500+ | 15 | 95%+ | Research paper (2000+ words) & oral defense |

### C2 Module Types

| Type | Modules | Words | Vocab | Immersion | Focus |
|------|---------|-------|-------|-----------|-------|
| `C2-stylistic` | 01-20 | 1800+ | 25+ | 98%+ | 7 functional styles (incl. religious, epistolary) |
| `C2-literary` | 21-40 | 1600+ | 25+ | 98%+ | Literary mastery, creative writing, criticism |
| `C2-professional` | 41-60 | 1600+ | 25+ | 98%+ | Professional meta-skills (domain-agnostic) |
| `C2-checkpoint` | 20, 40, 60, 66 | 1400+ | 15 | 98%+ | Phase review & assessment |
| `C2-capstone` | 67-80 | 1400+ | 15-25 | 98%+ | Capstone project: 10,000-word paper OR literary work |

**Strategic 2% English at C2:** Only for comparative linguistics ("Unlike English...") or untranslatable scholarly terms.

---

## Philosophy

> **The curriculum is the goal. Vibe is just a tool.**

Modules should be **rich, engaging, and comprehensive**. One curriculum module may generate multiple Vibe lessons - this is expected and encouraged. The curriculum should never be constrained by platform limitations.

**Grammar is a tool for communication, not an end in itself.** Every grammar point should be taught through:
1. **Real-world context** — when would someone actually use this?
2. **Cultural anchoring** — how does this connect to Ukrainian life?
3. **Narrative examples** — mini-stories, not isolated sentences
4. **Practical dialogues** — show the grammar in natural conversation

---

## Showcasing Ukrainian Richness & Beauty

To surprise and impress students, highlighting the beautiful, melodic, and rich nature of the Ukrainian language is paramount. Modules must actively integrate authentic cultural elements, showcase phonetic nuances, and highlight idiomatic expressions.

### 1. Phonetics & Nuance (The Sound of Ukraine)
- **IPA for All New Vocabulary:** Every new word introduced in the vocabulary table MUST have its full IPA transcription, regardless of level. This ensures pronunciation accuracy from A1.
- **Key Sound Spotlights:** Explicitly highlight challenging or unique Ukrainian sounds (e.g., Ї, Щ, Г vs Ґ, Ь) with detailed articulation guidance.
- **Melody Highlights:** Point out how specific sounds or grammatical structures (e.g., iotated vowels, soft signs, sentence stress patterns) contribute to the language's melodic quality.

### 2. Audio Integration (The Voice of Ukraine)
- **Audio Policy:** Audio links are NO LONGER MANDATORY in the static markdown.
- **Generator Responsibility:** The build system will handle audio generation.
- **Vocab Tables:** You may include an "Interesting Note" column instead of audio links if relevant.

### 3. Richness & Phraseology (The Wisdom of Ukraine)
- **Proverbs, Idioms & Set Expressions:** From B1+, modules MUST organically integrate Ukrainian proverbs, idioms, and stable phraseological expressions. These should be explained in context, not just listed. Aim for 1-2 new phraseological units per module.
- **Word Etymology:** Where appropriate, provide brief, engaging insights into the origin or cultural significance of a word.

### 4. Culture, Folklore & History (The Heart of Ukraine)
- **Beyond Basic Facts:** Engagement boxes should go deeper than simple facts.
- **Folklore/Traditions Corner (New Box Type):** `> 🎭 **Folklore/Traditions Corner**` for myths, legends, folk customs, and traditions.
- **Historical Context in Narrative:** Weave historical context naturally into narratives, especially in history and literature modules.
- **Decolonization Lens:** As per previous guidelines, actively dismantle imperial myths and celebrate Ukrainian achievements.

### 5. Grammatical Elegance (The Logic of Ukraine)
- **Highlight "Why":** For complex grammar points (cases, aspect, motion verbs), actively explain the elegance and logical beauty of the Ukrainian system, using relatable analogies where possible.
- **Case System:** Describe cases not just as endings, but as tools for expressing nuance and relationships.
### 6. Decolonization & Patriotism (The Truth of Ukraine)
- **Bust Russian Myths:** Actively identify and dismantle common propaganda points.
    - *Example:* "Russian and Ukrainian are brotherly languages" -> **Truth:** Ukrainian is closer to Polish/Belarusian; Russian has significant Finno-Ugric/Turkic substrata.
    - *Example:* "Kyiv is the mother of Russian cities" -> **Truth:** Kyiv existed as a metropolis when Moscow was a swamp; Russia hijacked Kyivan Rus' history.
    - *Example:* "Lenin created Ukraine" -> **Truth:** Ukraine has a distinct statehood tradition dating back to Rus', the Cossack Hetmanate, and the UPR (1917).
- **Highlight Resistance:** When discussing language history, ALWAYS mention the Ems Ukaz (1876), Valuev Circular (1863), and the Executed Renaissance. Show that speaking Ukrainian was a revolutionary act.
- **Unapologetic Tone:** Celebrate Ukrainian heroes, inventors, and artists without looking for Russian validation. Use the "Prosecutor's Voice" — present facts that indict the imperial narrative.

---

## Linguistic Precision Standards (Grammar Truth)

> **Single Source of Truth** for strict grammatical definitions.
> **Scope vs. Method:**
> *   **The Scope (WHAT):** Defined by [`UKRAINIAN-STATE-STANDARD-2024`](UKRAINIAN-STATE-STANDARD-2024.txt). Modules must teach *at least* these competencies.
> *   **The Method (HOW):** Defined by *this document*. We use specific pedagogical models (e.g., "4 Families") to teach the Standard's requirements effectively.
> *   *Example:* Standard says "Know noun gender". Guidelines say "Teach Gender via 4-Family Model". Both are true.

### 1. Noun Declension Families (Відміни)

#### Family 1 (Declension I)
*   **Definition:** Nouns ending in **-А** or **-Я**.
*   **Gender Scope:**
    *   **Feminine:** vast majority (*Мама, Робота*).
    *   **Masculine:** names (*Микола, Ілля*).
    *   **Common:** dual-gender descriptors (*Сирота, Ненажера*).
*   **Groups:** Hard (*Мама*), Soft (*Земля*), Mixed (*Межа*).

#### Family 2 (Declension II)
*   **Definition:**
    *   **Masculine:** Zero ending (*Стіл*) or ending in **-О** (*Батько, Тато, Дніпро*).
    *   **Neuter:** Ending in **-О, -Е** (*Вікно, Море*) or **-Я** (but **only** those that do NOT gain suffixes -at/-yat/-en during declension) (*Життя, Весілля, Обличчя*).
*   **Key Distinction:** If a Neuter noun ends in -Я and keeps its stem simple (*Життя -> Життя*), it is Family 2.

#### Family 3 (Declension III) - "The Consonant Feminines"
*   **Definition:** **Feminine** nouns ending in a **Consonant**.
*   **Specific Endings:**
    1.  **Soft Sign (-Ь):** *Сіль, Осінь, Тінь, Любов, Кров*.
    2.  **Sibilants (Ж, Ч, Ш):** Hard consonants but historically soft class. Examples: *Ніч, Подорож, Розкіш, Річ*.
    3.  **Special:** The word *Мати* (Mother).
*   **Validation Rule:** If it ends in a consonant and is Feminine, it is Family 3. Do NOT say "Ends in Soft Sign" (that excludes *Ніч*).

#### Family 4 (Declension IV) - "The Suffix Gainers"
*   **Definition:** **Neuter** nouns ending in **-А** or **-Я** that **change their stem** during declension.
*   **Mechanism:** They gain suffixes **-ат-, -ят-, -ен-**.
*   **Examples:**
    *   *Ім'я* (Name) -> *Імені*.
    *   *Цуценя* (Puppy) -> *Цуценяти*.
    *   *Дівча* (Girl) -> *Дівчати*.
*   **Key Distinction:** Family 4 is defined by *behavior* (stem change), not just ending.

### 2. Verb Conjugation Groups (Дієвідміни)

#### Group I (E-Conjugation)
*   **Stem Ending:** Usually ends in a consonant after dropping -ти.
*   **Key Vowel:** **-Е-** (or -Є-).
*   **3rd Plural:** **-УТЬ / -ЮТЬ**.
*   **Examples:** *Чита-ти -> Чита-ють*, *Писа-ти -> Пиш-уть*.

#### Group II (I-Conjugation)
*   **Stem Ending:** Usually ends in -и, -і, -ї after lower vowel drop.
*   **Key Vowel:** **-И-** (or -Ї-).
*   **3rd Plural:** **-АТЬ / -ЯТЬ**.
*   **Examples:** *Говори-ти -> Говор-ять*, *Роби-ти -> Роб-лять*.

### 3. Common Falsehoods to Avoid

*   ❌ "All feminine nouns end in -a/-ya." (False: Family 3 exists).
*   ❌ "Niches (Ніч) ends in a soft sign." (False: Ends in hard sibilant 'ch').
*   ❌ "Neuters in -ya are always Family 4." (False: *Zhyttya* is Family 2).

---

## Activity Types (Full Reference)

> **Note:** See "Mandatory Activity Mix by Level" table in Quick Reference for exact counts.

| Type | A1 | A2 | B1 | B2 | C1 | C2 | Description |
|------|----|----|----|----|----|----|-------------|
| `quiz` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Multiple choice questions |
| `match-up` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Match pairs (Ukrainian ↔ English) |
| `group-sort` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Sort items into categories |
| `true-false` | ✓ | ✓ | ✓ | ✓ | opt | opt | Statement validation |
| `fill-in` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Gap completion with options |
| `unjumble` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Reorder words into sentence |
| `anagram` | M01-10 | ✗ | ✗ | ✗ | ✗ | ✗ | Letter unscrambling (Cyrillic scaffolding only) |
| `error-correction` | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | Find and fix errors |
| `cloze` | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | Passage with multiple dropdown blanks |
| `mark-the-words` | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | Click/tap words matching criteria |
| `dialogue-reorder` | ✗ | ✓ | ✓ | ✓ | ✓ | opt | Put dialogue lines in correct order |
| `select` | ✗ | opt | ✓ | ✓ | ✓ | ✓ | Multi-checkbox selection |
| `translate` | ✗ | opt | ✓ | ✓ | ✓ | ✓ | Select correct translation |

**Legend:** `✓` = required, `opt` = optional, `✗` = not allowed

**Note:** `observe-first` is a content pattern (`> [!observe]` callout), not an activity. Use inline before grammar explanations for inductive pattern discovery (recommended B1-B2).

### Activity Priority by Level

**A1 (Beginner):** Recognition → Production
- Primary: match-up, group-sort, quiz, true-false
- Secondary: fill-in, unjumble
- Special: anagram (M01-10 only for Cyrillic scaffolding)

**A2 (Elementary):** Introduce new activity types
- All A1 types + error-correction, cloze, mark-the-words, dialogue-reorder
- Optional: select, translate
- Error-correction: 1 obvious error per sentence

**B1 (Intermediate):** Full activity palette
- All 13 activity types available
- Use `> [!observe]` callouts inline before grammar explanations
- Production activities increase (unjumble ×2, error-correction ×2)

**B2 (Upper-Intermediate):** Production increases
- Fill-in ×3, unjumble ×2, error-correction ×2, cloze ×1
- Full activity palette available

**C1-C2 (Advanced/Mastery):** Production-heavy, context-focused
- Cloze ×3 (contextual grammar), error-correction ×3 (metalinguistic awareness)
- Translate ×2 (production with alternatives), fill-in ×2, unjumble ×2
- Mark-the-words rarely used (too basic at this level)

**Rationale:** At B1+, learners need to *produce* correct Ukrainian, not just recognize it. Error-correction builds metalinguistic awareness essential for self-correction.

### Error-Correction Progression

| Level | Errors per Sentence | Error Types |
|-------|---------------------|-------------|
| A2 | 1 obvious | Gender agreement, case endings, animate accusative |
| B1 | 1-2 | + Aspect errors, participles, word order |
| B2 | 2+ subtle | + Style errors, register mismatches, Russianisms |
| C1-C2 | 2+ nuanced | + Stylistic inconsistency, academic register |

---

## Complexity Standards by Activity Type

### quiz (Question & Option Complexity)

| Level | Question Length | Options | Distractors |
|-------|-----------------|---------|-------------|
| A1 | 5-10 words | 3-4 | Obviously wrong |
| A2 | 8-15 words | 4 | Plausible but clearly wrong |
| B1 | 12-20 words | 4 | Require careful reading |
| B2 | 15-25 words | 4 | Near-synonyms, subtle differences |
| C1 | 18-30 words | 4 | Nuanced, context-dependent |
| C2 | 20-35 words | 4 | Expert-level distinctions |

### match-up (Pair Complexity)

| Level | Pairs | Left Side | Right Side |
|-------|-------|-----------|------------|
| A1 | 8-10 | Single words | Single word translations |
| A2 | 10-12 | Words/short phrases | Translations/definitions |
| B1 | 12-14 | Phrases/idioms | Meanings/synonyms |
| B2 | 12-16 | Idioms/collocations | Nuanced equivalents |
| C1 | 14-18 | Register variants | Formal/informal pairs |
| C2 | 14-18 | Stylistic expressions | Literary/academic pairs |

### group-sort (Categorization Complexity)

| Level | Groups | Items | Category Type |
|-------|--------|-------|---------------|
| A1 | 2-3 | 8-12 | Concrete (gender, animate/inanimate) |
| A2 | 2-3 | 10-14 | Grammar (case, aspect, tense) |
| B1 | 3-4 | 12-16 | Abstract (register, style, meaning) |
| B2 | 3-4 | 14-18 | Nuanced (connotation, usage context) |
| C1 | 3-4 | 16-20 | Expert (stylistic register) |
| C2 | 3-4 | 16-20 | Native-level (dialectal, archaic) |

### true-false (Statement Complexity)

| Level | Statement Length | Complexity |
|-------|------------------|------------|
| A1 | 4-8 words | Obvious facts about grammar rules |
| A2 | 6-12 words | Grammar rules with exceptions |
| B1 | 10-18 words | Nuanced grammar, context-dependent |
| B2 | 14-22 words | Subtle distinctions, register rules |
| C1 | 16-25 words | Academic/literary conventions |
| C2 | 18-30 words | Expert-level linguistic facts |

### select (Word Selection Complexity)

| Level | Sentence Length | Options | Distractor Type |
|-------|-----------------|---------|-----------------|
| A1 | 4-6 words | 3-4 | Wrong gender/case |
| A2 | 6-10 words | 4 | Wrong case/aspect |
| B1 | 10-14 words | 4-5 | Aspect/mood confusion |
| B2 | 12-18 words | 4-5 | Register/style mismatch |
| C1 | 14-20 words | 4-5 | Near-synonyms, collocations |
| C2 | 16-22 words | 4-5 | Stylistic precision |

### error-correction (Error Complexity)

| Level | Errors | Sentence Length | Error Types |
|-------|--------|-----------------|-------------|
| A2 | 1 obvious | 6-10 words | Gender, case endings, agreement |
| B1 | 1-2 | 10-16 words | + Aspect, participles, word order |
| B2 | 2+ subtle | 14-20 words | + Style, register, Russianisms |
| C1 | 2+ nuanced | 16-24 words | + Academic register, collocations |
| C2 | 2+ expert | 18-28 words | + Stylistic inconsistency, archaisms |

### anagram (A1 Only)

| Modules | Word Length | Notes |
|---------|-------------|-------|
| A1 M01-10 | 4-8 letters | Cyrillic scaffolding |
| A1 M11-20 | 5-10 letters | Reduce usage |
| A1 M21-30 | — | Avoid, use unjumble instead |
| A2+ | — | NOT ALLOWED |

### cloze (A2+) - Passage with Dropdown Blanks

| Level | Passage Length | Blanks | Blank Spacing | Distractor Quality |
|-------|----------------|--------|---------------|-------------------|
| A2 | 3-5 sentences | 3-4 | Every 8-12 words | Obviously wrong options |
| B1 | 5-8 sentences | 4-6 | Every 6-10 words | Plausible but wrong |
| B2 | 8-12 sentences | 6-8 | Every 5-8 words | Near-synonyms |
| C1 | 10-15 sentences | 8-10 | Every 4-7 words | Register/style based |
| C2 | 12-18 sentences | 10-12 | Every 4-6 words | Native-level nuance |

**Usage:** Best for testing grammar in context (case endings, verb forms, aspect), coherence, and collocations.

### dialogue-reorder (A2+)

| Level | Lines | Speakers | Complexity |
|-------|-------|----------|------------|
| A2 | 4-6 | 2 | Simple greetings, basic exchanges |
| B1 | 6-8 | 2-3 | Topic negotiation, opinions |
| B2 | 8-10 | 2-3 | Argumentation, persuasion |
| C1 | 10-12 | 2-4 | Complex negotiation, formal registers |

**Usage:** Develops pragmatic competence, turn-taking, and conversation flow understanding.

### mark-the-words (A2+)

| Level | Sentence Length | Words to Mark | Criteria Type |
|-------|-----------------|---------------|---------------|
| A2 | 8-12 words | 2-4 | Single category (nouns, verbs, cases) |
| B1 | 12-18 words | 3-5 | Grammar class + case |
| B2 | 16-22 words | 4-6 | Subtle distinctions (aspect, register) |
| C1 | 18-25 words | 5-8 | Multiple criteria, stylistic features |
| C2 | 20-30 words | 6-10 | Expert-level categorization |

**Usage:** Recognition stage activity. Best for case identification, word class awareness, finding specific grammatical structures.

### select (Multi-Checkbox) (A2+)

| Level | Options | Correct Answers | Question Complexity |
|-------|---------|-----------------|---------------------|
| A2 | 4-5 | 2-3 | "Which are feminine nouns?" |
| B1 | 5-6 | 2-4 | "Which sentences are grammatically correct?" |
| B2 | 5-6 | 2-4 | "Which options express obligation?" |
| C1 | 5-7 | 2-4 | "Which are acceptable in formal register?" |
| C2 | 6-8 | 3-5 | "Which preserve the author's intent?" |

**Usage:** Tests ability to identify multiple valid answers. Good for cases, verb forms, stylistic variants.

### translate (A2+)

| Level | Source Length | Options | Alternative Count |
|-------|---------------|---------|-------------------|
| A2 | 4-8 words | 4 | 0-1 alternatives |
| B1 | 8-14 words | 4 | 1-2 alternatives |
| B2 | 12-18 words | 4 | 2-3 alternatives |
| C1 | 16-22 words | 4-5 | 2-4 alternatives |
| C2 | 18-28 words | 4-5 | 3-5 alternatives |

**Usage:** Production practice. Tests both accuracy and understanding of valid alternatives.

### Observe-First Content Pattern (B1-B2)

**Note:** This is a content callout (`> [!observe]`), not an activity type. Use inline before grammar explanations.

| Level | Examples | Pattern Type | Follow-up Activity |
|-------|----------|--------------|-------------------|
| B1 | 4-6 examples | Single pattern (endings, stress) | fill-in applying the pattern |
| B2 | 6-8 examples | Complex pattern (aspect pairs, motion) | cloze or translate |

**Usage:** Inductive learning before explicit rules. Place inline within lesson content, before grammar explanation.

**Format:**
```markdown
> [!observe] Look at these examples...
> - Я читаю книгу. (I read a book.)
> - Він бачить студента. (He sees the student.)
> What do you notice about the endings?
```

---

## Complexity Progression Principles

### A1: Foundation
- Simple SVO sentences
- Basic vocabulary, high-frequency words
- No subordinate clauses
- Example: `Це моя книга.` (3 words)

### A2: Expansion
- Add adjectives, adverbs, time expressions
- Simple connectors (і, але, тому що)
- Basic prepositional phrases
- Subordinate clauses with що, який, коли
- Example: `Я завжди читаю цікаві книги ввечері.` (6 words)

### B1: Integration
- Conditional sentences (якщо, якби)
- Reported speech
- Complex time expressions
- Adverbial participles (дієприслівники)
- Example: `Якби я знав про цю проблему раніше, я б обов'язково допоміг тобі її вирішити.` (14 words)

### B2: Sophistication
- Passive constructions
- Abstract vocabulary
- Nuanced connectors
- Stylistic variation
- Example: `Незважаючи на те, що проєкт був складним, команда успішно завершила його вчасно.` (12 words)

### C1: Advanced Fluency
- All registers (formal, academic, professional)
- Complex argumentation structures
- Implicit meaning and nuance
- Example: `Варто зазначити, що дане дослідження проводилось з урахуванням усіх методологічних вимог.` (10 words)

### C2: Mastery
- Full native-level complexity
- Literary and specialized language
- Subtle stylistic effects
- Example: `Незважаючи на численні застереження експертів, рішення було ухвалено одноголосно.` (8 words, but highly sophisticated)

---

## CEFR Can-Do Statements

### A1 (Breakthrough)
- Can understand and use familiar everyday expressions
- Can introduce themselves and others
- Can ask and answer simple questions about personal details

### A2 (Waystage)
- Can communicate in simple, routine tasks
- Can describe aspects of background, environment, and immediate needs
- Can handle short social exchanges

### B1 (Threshold)
- Can deal with most situations likely to arise while travelling
- Can enter unprepared into conversation on familiar topics
- Can produce simple connected text on familiar topics
- Can describe experiences, events, dreams, hopes and briefly give reasons

### B2 (Vantage)
- Can interact with a degree of fluency and spontaneity
- Can produce clear, detailed text on a wide range of subjects
- Can explain a viewpoint on a topical issue giving advantages and disadvantages

---

## Content Depth Requirements

### Vocabulary Policy: Active vs Passive

To ensure narratives are engaging and authentic (especially for History/Culture modules), we distinguish between two types of vocabulary:

1.  **Active Vocabulary (Target):** The ~25-40 specific words listed in the `Vocabulary` table.
    *   **Rule:** These MUST be drilled in activities.
    *   **Constraint:** Activities must ONLY test these words (plus prior module words).

2.  **Passive/Contextual Vocabulary:** Additional words used in the narrative to make the story flow or explain complex concepts.
    *   **Rule:** You ARE ALLOWED to use words outside the target list in the Narrative/Text sections to maintain richness and "Soul".
    *   **Constraint:** Do not test these in activities unless they are added to the table. Gloss difficult words if necessary.

### What Counts as "Content Words"

- ✅ Narrative paragraphs, explanations, cultural context
- ✅ Example sentences in flowing text
- ✅ Mini-dialogues and scenarios
- ✅ Engagement box text
- ❌ NOT vocabulary tables
- ❌ NOT grammar tables
- ❌ NOT activity instructions or answers

### A "Rich" Module Includes

- [ ] **Compelling introduction** (WHY, not "In this lesson we learn...")
- [ ] **Grammar tables surrounded by narrative** (no naked tables)
- [ ] **Mini-dialogues** showing grammar in real conversation
- [ ] **Usage patterns / Common mistakes** section
- [ ] **Multiple contextual examples** (not isolated words)
- [ ] **Phraseology Integration:** Use of proverbs, idioms, or set expressions (from B1+)
- [ ] **Engagement boxes** (varied types)
- [ ] **Cultural context** where relevant
- [ ] **Authentic materials** (real texts, media)
- [ ] **Production tasks** (speaking/writing) with **Model Answers** for self-correction
- [ ] **Self-assessment** checklist
- [ ] **Pronunciation guidance** (B2+ grammar modules)

### Red Flags for "Dry" Modules

- Tables with no surrounding paragraphs
- Introduction starts with "In this lesson we learn..."
- No mini-dialogues showing grammar in real conversation
- No "Common Mistakes" or "Usage Patterns" section
- Only ~150 words of narrative (rest is tables)

---

## Grammar-Focused Module Structure (TTT Approach)

**Pedagogy:** Test-Teach-Test (TTT) / Guided Discovery

Instead of: **Rule → Table → Exercises**

Use: **Context → Pattern Discovery → Practice → Real Application**

### Metacognition Elements (B1+ Required)

**A. "Why This Matters" box (after title, before Diagnostic):**

```markdown
> 🎯 **Чому це важливо**
>
> [2-3 sentences explaining real-world impact of this grammar point]
>
> Native speakers instantly notice wrong aspect choices. Mastering this distinction
> is what separates "textbook Ukrainian" from natural speech.
```

**B. "Self-Check" box (after Summary, before Словник):**

```markdown
> ✅ **Перевірте себе**
>
> Before moving on, can you:
> - [ ] [Key skill 1 from this module]?
> - [ ] [Key skill 2 from this module]?
> - [ ] [Key skill 3 from this module]?
>
> If you checked all boxes, proceed to the next module.
> If not, review the Analysis section and try the Practice activities again.
```

### Required Sections (A2+)

1. **Contextual Introduction (100+ words)**
   - Set up a real scenario where this grammar matters
   - Connect to cultural practices or daily life
   - Show WHY learners need this, not just WHAT it is

2. **Pattern Presentation with Narrative (80+ words per pattern)**
   - Brief table for reference
   - Paragraph explaining the pattern
   - Mini-examples in context
   - Engagement box connecting to culture/history

3. **Usage Patterns Section (150+ words)**
   - When to use vs. when NOT to use
   - Common mistakes and how to avoid them
   - Collocations and fixed expressions

4. **Mini-Dialogues (2-3 per module, 50+ words each)**
   - Show grammar in natural conversation
   - Vary scenarios (café, shop, home, work)
   - Highlight the grammar point with bold

5. **Cultural/Practical Connection (100+ words)**
   - How Ukrainians actually use this in life
   - Register notes (formal vs. informal)
   - Regional variations if relevant

---

## Vocabulary-Focused Module Structure (Narrative Arc)

**Pedagogy:** Content-Based Instruction (CBI) / Narrative-Driven

Instead of: **Table → Table → Table → Activities**

Use: **Story → Vocabulary-in-Context → Analysis → Retelling**

**Metacognition:** Vocabulary modules also include "Why This Matters" and "Self-Check" boxes (see Grammar-Focused section above for templates).

### Required Sections

1.  **Narrative Arc (Story-Driven) (150+ words)** — Vocabulary MUST be embedded in a compelling story or scenario.
2.  **Vocabulary Groups with Context (80+ words per group)** — Words in use, extracted from the story.
3. **Usage Patterns Section (150+ words)** — Collocations, what verbs go with what nouns
4. **Cultural/Real-World Connection (100+ words)** — How Ukrainians actually use these words
5. **Mini-Scenarios (150+ words)** — 2-3 short dialogues

### Minimum Content by Section

| Section | Min Words |
|---------|-----------|
| Thematic intro | 100 |
| Per vocab group | 80 |
| Usage patterns | 150 |
| Cultural notes | 100 |
| Mini-scenarios | 150 |
| **Total narrative** | **580+** (+ engagement boxes = 750+) |

---

## Engagement Boxes

### Required Types

| Box Type | Icon | Purpose |
|----------|------|---------|
| Did You Know? | 💡 | Fascinating facts |
| Myth Buster | 🔍 | Correct misconceptions |
| Pro Tip | ⚡ | Practical advice |
| Culture Corner | 🎭 | Traditions, customs |
| History Bite | 📜 | Historical context |
| Fun Fact | 🎯 | Memorable tidbits |
| Language Link | 🔗 | Connections to English |
| Real World | 🌍 | Modern relevance |
| Pop Culture Moment | 🎬 | Movies, music, games, memes |
| Folklore/Traditions Corner | 🎭 | Myths, legends, customs, traditions |

### Format

```markdown
> 💡 **Did You Know?**
>
> The Cyrillic alphabet was NOT invented by Russians! It was created in the
> 9th century in Bulgaria by followers of Saints Cyril and Methodius.
```

### Placement Guidelines

- At least 1-2 boxes per module section
- Place after introducing new concepts (reinforcement)
- Use to break up dense grammar explanations
- Connect abstract grammar to real cultural context
- Make learners want to share what they learned!

### Box Content Principles

1. **Surprising** - Challenge assumptions
2. **Memorable** - Stick in the mind
3. **Accurate** - Verified facts only
4. **Relevant** - Connected to the lesson content
5. **Shareable** - "I didn't know that!" factor

### Examples by Level

**A1 (Alphabet/Basics):**
- Origin of Cyrillic alphabet
- Ukrainian unique letters
- Why Ukrainian sounds different from Russian
- Famous Ukrainian words in English (steppe, borsch)
- 🎬 Pop culture: How movie/game characters would speak Ukrainian

**A2 (Grammar Expansion):**
- How Ukrainian cases compare to Latin/German
- Why aspect is "the soul of Slavic languages"
- Historical reasons for grammatical features
- 🎬 Pop culture: Famous quotes translated to Ukrainian

**B1-B2 (Intermediate):**
- Language politics and identity
- Regional dialects and their history
- Ukrainian literary tradition
- Famous polyglots who learned Ukrainian
- 🎬 Pop culture: Ukrainian music, films, memes

**C1+ (Advanced):**
- Linguistic research about Ukrainian
- Evolution of Ukrainian over centuries
- Influence of other languages
- Debates in modern Ukrainian linguistics
- 🎬 Pop culture: Subtitling challenges, dubbing culture

### Pop Culture References

**Good pop culture references:**
- Internationally known (Marvel, Star Wars, Harry Potter)
- Popular in Ukraine: Lord of the Rings, The Witcher, S.T.A.L.K.E.R. series
- Video games with Ukrainian connections (S.T.A.L.K.E.R., Metro series - both made by Ukrainian studios!)
- Easy to translate/explain
- Make a teaching point (grammar, pronunciation, culture)
- Self-aware humor (like the Groot example about sentence length)

**Ukrainian pop culture gold:**
- **Lord of the Rings** - "орки" (orcs) became wartime slang; Tolkien's languages resonate with Slavic speakers
- **The Witcher** - Slavic mythology, hugely popular; Netflix series has excellent Ukrainian dub
- **S.T.A.L.K.E.R.** - Made by GSC Game World (Kyiv); set in Chornobyl zone; iconic Ukrainian game
- **Metro 2033/Exodus** - Made by 4A Games (Kyiv); post-apocalyptic; Ukrainian voice acting
- **Cossacks** - Classic strategy game series by GSC Game World

**Ideas for pop culture boxes:**
- How would [character] say this in Ukrainian?
- Famous movie quotes in Ukrainian
- Ukrainian songs that teach grammar patterns
- Viral Ukrainian memes explained
- Video game localization quirks
- How Ukrainian dubbing differs from subtitles

**Format:**
```markdown
> 🎬 **Pop Culture Moment: [Reference]**
>
> [Interesting observation about Ukrainian through pop culture lens]
```

---

## A1 Sentence Examples by Module Type

**Modules 1-10 (Alphabet/Phonetics):**
```
Це банк. (This is a bank.)
Кава і чай. (Coffee and tea.)
Тут парк. (Here is a park.)
```

**Modules 11-20 (Basic Grammar):**
```
Це моя книга.
Я бачу студента.
Вона в школі.
Немає часу.
```

**Modules 21-30 (Practical Vocabulary):**
```
Я люблю каву.
Мій брат вдома.
У мене є сестра.
Вона працює тут.
```

## A2 Sentence Examples

```
Я читав книгу, і вона мені сподобалась.
Він хотів піти, але не мав часу.
Ми поїдемо завтра, тому що сьогодні дощ.
Вона працює в офісі, а він — вдома.
Я купив хліб і молоко в магазині.
```

## B1 Sentence Examples

```
Коли він прийшов додому, ми вже вечеряли.
Я думаю, що він прийде завтра на зустріч.
Якщо буде гарна погода, ми підемо на прогулянку.
Книга, яку я читаю, дуже цікава і корисна.
Хоча він був втомлений, він закінчив усю роботу.
```

## B2 Sentence Examples

```
Не зважаючи на те, що проєкт виявився значно складнішим, ніж передбачалося спочатку, команда, яка працювала над ним протягом двох років, досягла вражаючих результатів завдяки наполегливій праці.

Письменник, твори якого вже перекладено більш ніж тридцятьма мовами світу, народився в невеликому селі на Полтавщині, де провів усі роки свого дитинства.

Аналізуючи причини економічної кризи, експерти дійшли висновку, що головним чинником стала недостатня диверсифікація національної економіки, яка надмірно залежала від експорту сировини.
```

---

## Activity Templates by Level

### A1 Examples

#### fill-in (3-5 words per sentence)
```markdown
## fill-in: Possessive Pronouns

> Choose the correct possessive pronoun.

1. Це ___ книга.
   > [!answer] моя
   > [!options] мій | моя | моє | мої

2. ___ брат студент.
   > [!answer] Її
   > [!options] Його | Її | Їхній | Наш
```

#### match-up (8-10 pairs)
```markdown
## match-up: Family Vocabulary

| Left | Right |
|------|-------|
| мама | mother |
| тато | father |
| брат | brother |
| сестра | sister |
```

#### anagram (4-8 letters) - [Use INSTEAD of unjumble for A1]
```markdown
## anagram: Build the Word

1. о / л / к / о / м
   > [!answer] молоко
```

#### quiz
```markdown
## quiz: Gender and Cases

1. What gender is the noun "книга"?
   - [x] Feminine
   - [ ] Masculine
   - [ ] Neuter
   > Nouns ending in -а are typically feminine.
```

#### true-false
```markdown
## true-false: Grammar Rules

- [x] Feminine nouns typically end in -а or -я
  > Correct! Examples: книга, земля

- [ ] "Його" changes form for different genders
  > Incorrect. "Його" never changes - it's a frozen genitive form.
```

#### group-sort (2-3 categories)
```markdown
## group-sort: Noun Gender

> Sort these nouns by grammatical gender.

| Masculine | Feminine | Neuter |
|-----------|----------|--------|
| стіл | книга | вікно |
| брат | сестра | місто |
```

---

### A2 Examples

#### fill-in: Case Endings (6-8 words)
```markdown
## fill-in: Case Practice

1. Я дав книгу ___.
   > [!answer] другові
   > [!options] друг | друга | другові | другом

2. Ми говорили про ___.
   > [!answer] роботу
   > [!options] робота | роботу | роботи | роботою
```

#### fill-in: Verb Aspect
```markdown
## fill-in: Aspect Choices

1. Вчора я ___ цю книгу цілий день.
   > [!answer] читав
   > [!options] читав | прочитав | читаю | прочитаю

2. Нарешті він ___ роботу!
   > [!answer] зробив
   > [!options] робив | зробив | робить | зробить
```

#### match-up: Aspect Pairs (10-12 pairs)
```markdown
## match-up: Imperfective ↔ Perfective

| Imperfective | Perfective |
|--------------|------------|
| читати | прочитати |
| писати | написати |
| робити | зробити |
| говорити | сказати |
| брати | взяти |
```

#### unjumble (8-10 words)
```markdown
## unjumble: Compound Sentences

1. книгу / вчора / цікаву / Я / читав / дуже
   > [!answer] Я вчора читав дуже цікаву книгу.
   > (Yesterday I read a very interesting book.)

2. піти / хотів / але / Він / часу / не / мав
   > [!answer] Він хотів піти, але не мав часу.
   > (He wanted to go but didn't have time.)
```

#### error-correction (1 obvious error, 6-10 words)
```markdown
## error-correction: Find and Fix

> Each sentence has ONE obvious error. Find the incorrect word, then choose the correct form.

1. Я бачу студент у бібліотеці.
   > [!error] студент
   > [!answer] студента
   > [!options] студент | студента | студенту | студентом
   > [!explanation] Animate masculine accusative = genitive form

2. Вона читав книгу вчора.
   > [!error] читав
   > [!answer] читала
   > [!options] читав | читала | читало | читали
   > [!explanation] Past tense agrees with subject gender (feminine = -ла)
```

**A2 Error Types:**
- Gender agreement (adjective-noun, past tense-subject)
- Case endings (accusative, dative, locative, instrumental)
- Animate masculine accusative = genitive

---

### B1 Examples

#### fill-in: Agreement Chains (10-14 words)
```markdown
## fill-in: Full Agreement

1. ___ (Цей) ___ (новий) студентка вже ___ (прочитати, past) усі книги.
   > [!answer] Ця нова студентка вже прочитала усі книги.
   > [!options-1] Цей | Ця | Це | Ці
   > [!options-2] новий | нова | нове | нові
   > [!options-3] прочитав | прочитала | прочитало | прочитали
```

#### fill-in: Aspect in Context
```markdown
## fill-in: Aspect Choices in Context

1. Коли я ___ (входити/увійти) до кімнати, він ___ (читати/прочитати) газету.
   > [!answer] увійшов ... читав
   > Entry = single completed action (pf), reading = ongoing background (impf)
```

#### unjumble: Subordinate Clauses (12-16 words)
```markdown
## unjumble: Complex Sentences

1. прийшов / Коли / він / ми / додому / вже / вечеряли
   > [!answer] Коли він прийшов додому, ми вже вечеряли.
   > (When he came home, we were already having dinner.)

2. думаю / Я / що / завтра / він / на / прийде / зустріч
   > [!answer] Я думаю, що він прийде завтра на зустріч.
   > (I think that he will come to the meeting tomorrow.)
```

#### error-correction (1-2 errors, 10-16 words)
```markdown
## error-correction: Find and Fix

1. "Книга, який я читаю, цікава."
   > [!answer] Книга, якУ я читаю, цікава.
   > Error: Relative pronoun must agree with antecedent (feminine accusative)
```

---

### B2 Examples

#### fill-in: Literary Register (12-16 words)
```markdown
## fill-in: Literary Ukrainian

1. Не ___ (зважати) на те, що проєкт ___ (виявитися, past) значно ___ (складний, comparative), ніж ___ (передбачатися, past) спочатку, команда ___ (досягти, past) ___ (вражаючий) результатів.
   > [!answer] Не зважаючи на те, що проєкт виявився значно складнішим, ніж передбачалося спочатку, команда досягла вражаючих результатів.
```

#### fill-in: Stylistic Choices
```markdown
## fill-in: Register Selection

> Choose the most appropriate word for academic/formal writing.

1. Дослідники ___ важливі результати. (отримали / здобули / дістали)
   > [!answer] здобули
   > "Здобути" is more formal/academic than "отримати" or "дістати"
```

#### match-up: Near-Synonyms with Nuance
```markdown
## match-up: Semantic Nuances

| Word | Nuance/Usage |
|------|--------------|
| думати | neutral, general thinking |
| міркувати | deliberate, careful reasoning |
| гадати | suppose, assume |
| вважати | consider, hold opinion |
```

#### unjumble: Literary Sentences (14-18 words)
```markdown
## unjumble: Literary Ukrainian

1. сонця / Споглядаючи / древнім / захід / над / містом / він / глибокий / відчув / із / зв'язок / минулим
   > [!answer] Споглядаючи захід сонця над древнім містом, він відчув глибокий зв'язок із минулим.
```

#### error-correction: Subtle Style Errors (2+ errors, 14-20 words)
```markdown
## error-correction: Subtle Style Errors

1. "Згідно результатів дослідження, існує зв'язок..."
   > [!answer] Згідно З результатами дослідження...
   > Error: "Згідно" requires "з" + instrumental, not genitive

2. "Він є талановитим письменником."
   > [!answer] Він талановитий письменник. / Він — талановитий письменник.
   > Error: "є" as copula is a Russicism in such constructions
```

---

## Ukrainian Identity & Decolonization

### Philosophy

This curriculum takes a **decolonial approach** to teaching Ukrainian. For centuries, Russian imperial and Soviet narratives minimized, distorted, or erased Ukrainian language, history, and identity. Our role is to provide **accurate, factual information** that corrects misconceptions.

This is not about politics - it's about **historical accuracy** and **respect for Ukrainian identity**.

### Principles

1. **Ukrainian is a distinct language** - Not a "dialect of Russian," not "Little Russian," not derivative. Ukrainian has its own history, literature, and development path.

2. **Facts over narratives** - Present historically accurate information, even when it contradicts widely-held misconceptions. Cite sources when possible.

3. **Celebrate Ukrainian achievements** - Highlight Ukrainian contributions to world culture, science, literature, and history that have been overlooked or misattributed.

4. **Use proper Ukrainian** - Avoid Russianisms and Surzhyk in curriculum content. Teach standard Ukrainian vocabulary, not Russian calques.

5. **Name things correctly** - Use Ukrainian names for Ukrainian places (Kyiv not Kiev, Kharkiv not Kharkov, Odesa not Odessa).

### Common Misconceptions to Address

Use **🔍 Myth Buster** boxes when relevant:

| Misconception | Reality |
|---------------|---------|
| "Cyrillic is Russian" | Created in Bulgaria (9th c.); Ukraine adopted it independently |
| "Ukrainian is a dialect of Russian" | Separate East Slavic language with distinct development |
| "Kyivan Rus' was Russia" | Medieval state centered in Kyiv; "Russia" didn't exist yet |
| "Borsch is Russian" | Ukrainian dish; the word entered English from Ukrainian |
| "Holodomor was just a famine" | Deliberate genocide killing 4-10 million Ukrainians |
| "Ukraine means 'borderland'" | Contested etymology; Ukrainians reject this interpretation |
| "Russians and Ukrainians are one people" | Distinct nations with different languages, cultures, histories |

### Level-Appropriate Integration

| Level | Approach |
|-------|----------|
| **A1** | Factual corrections in engagement boxes (Cyrillic origins, word etymologies) |
| **A2** | Language comparisons, Ukrainian unique features, cultural facts |
| **B1** | Historical context, regional diversity, Ukrainian achievements |
| **B2** | Dedicated history modules, explicit myth-busting, literature |
| **C1-C2** | Critical analysis, propaganda recognition, academic discourse |

### Myth Buster Examples by Level

**A1 - Alphabet lesson:**
> 🔍 **Myth Buster**
>
> **Myth:** "Cyrillic is the Russian alphabet"
> **Fact:** Cyrillic was created in Bulgaria in the 9th century, over 100 years before "Russia" existed. Ukrainian Cyrillic has unique letters (Ї, Є, Ґ) that Russian doesn't have!

**A2 - Food vocabulary:**
> 🔍 **Myth Buster**
>
> **Myth:** "Borsch is a Russian dish"
> **Fact:** Borsch (борщ) is Ukrainian! The word entered English directly from Ukrainian. UNESCO recognized Ukrainian borsch culture as endangered heritage in 2022.

**B1 - History module:**
> 🔍 **Myth Buster**
>
> **Myth:** "Kyivan Rus' was an early Russian state"
> **Fact:** Kyivan Rus' (Київська Русь) was a medieval federation centered in Kyiv. The name "Russia" (Росія) appeared centuries later. Moscow didn't exist when Kyiv was already a major European capital.

### What This Is NOT

- **Not anti-Russian bigotry** - We distinguish between Russian government narratives and Russian people
- **Not political propaganda** - We present historical facts, not political opinions
- **Not one-sided** - We acknowledge complexity where it exists
- **Not aggressive** - Tone is educational and matter-of-fact, not polemical

### Vocabulary Choices

Always prefer standard Ukrainian over Russianisms:

| Use ✅ | Not ❌ | Why |
|--------|--------|-----|
| вибачте | ізвіняюсь | Russian calque |
| будь ласка | пожалуйста | Russian word |
| квиток | білет | Russian *билет* |
| гаразд | ладно | Russian word |
| файно/чудово | класно | Russian slang |
| мабуть | наверно | Russian word |
| відчиняти (doors) | відкривати | Russian usage pattern |

---

## Cultural Content

### Every Module Should Include

At minimum one of:
- **Cultural note** - Customs, traditions, history
- **Language tip** - Pragmatics, usage nuance
- **Fun fact** - Interesting cultural tidbit
- **Comparison** - Ukrainian vs English approach
- **Current relevance** - Modern Ukraine connection

### Cultural Sensitivity

- **Verify facts** with native speakers
- **Acknowledge diversity** within Ukraine
- **Avoid stereotypes** - Present nuanced view
- **Current events awareness** - Consider ongoing situation
- **Multiple perspectives** - Where relevant

---

## Engagement Techniques

### Variety in Activities

Each module should include **at least 3 different activity types**:

| Activity Type | Engagement Level | Best For |
|---------------|------------------|----------|
| Match-up | Medium | Vocabulary, associations |
| Quiz (MCQ) | Medium | Comprehension check |
| Gap-fill | Medium-High | Grammar practice |
| Sorting/Grouping | High | Categorization |
| Ordering/Sequencing | High | Narrative, process |
| Dialogue completion | High | Functional language |
| Translation (short) | Medium | Accuracy practice |
| Listening comprehension | High | Audio skills |
| Image labeling | High | Visual learners |
| Video comprehension | Very High | Engagement, culture |

### Gamification Elements

Consider including:
- **Points/scores** for activities
- **Streaks** for consecutive correct answers
- **Badges** for module completion
- **Leaderboards** (if platform supports)
- **Easter eggs** - hidden cultural content

### Story & Narrative

Where possible, create:
- **Recurring characters** across modules
- **Story arcs** that develop over levels
- **Real-world scenarios** learners can relate to
- **Cultural narratives** that teach while engaging

---

## Authentic Materials

### What Counts as Authentic

- Real news articles (adapted if needed)
- Actual social media posts (anonymized)
- Restaurant menus, signs, forms
- Song lyrics (with permission)
- Literary excerpts (public domain or licensed)
- Film/TV dialogue transcripts
- Podcast transcripts
- Interview recordings

### Adaptation Guidelines

When adapting authentic materials:
1. **Preserve authenticity** - Don't over-simplify
2. **Gloss difficult items** - Add vocabulary notes
3. **Provide context** - Cultural/situational background
4. **Progressive difficulty** - Match to level
5. **Attribute source** - Always credit original

---

## Media Integration

### Types

| Media Type | Usage | Permission Status |
|------------|-------|-------------------|
| Images | Illustrations, photos, diagrams | Track in MEDIA-SOURCES.md |
| Audio | Pronunciation, dialogues, listening | Record or license |
| Video | YouTube clips, documentaries | Requires permission |
| Maps | Historical, geographical | Create or license |
| Infographics | Grammar charts, timelines | Create internally |
| Songs | Music with lyrics | Requires license |
| Film clips | Cinema excerpts | Requires rights |

### Image Guidelines

- **Quality:** Minimum 800x600px for displays
- **Format:** WebP preferred, PNG for transparency
- **Alt text:** Always include for accessibility
- **Attribution:** Track in MEDIA-SOURCES.md
- **Cultural accuracy:** Verify with native speakers

### Audio Guidelines

- **Native speakers only** for pronunciation
- **Multiple voices:** Male/female, different ages
- **Regional variety:** Note accent/dialect used
- **Quality:** 44.1kHz, clear audio, no background noise
- **Duration:** Listening exercises 30s-3min optimal

### Video Guidelines

- **Ukrainian YouTube is rich** - many sources available
- **Short clips:** 1-5 minutes preferred for lessons
- **Subtitles:** Ukrainian subtitles when available
- **Context:** Brief introduction before video
- **Comprehension:** Questions/activities after viewing

### Video Integration Workflow

1. **Search Ukrainian YouTube** for topic
2. **Evaluate quality:** Audio clarity, content accuracy
3. **Check channel:** Reputable creators preferred
4. **Note timestamp:** Specific segment needed
5. **Add to sources tracking**

### Recommended YouTube Channel Types

| Type | Examples | Good For |
|------|----------|----------|
| News | Укрінформ, Радіо Свобода | Current events, listening |
| Educational | Простопросто, Цікава наука | Explanations, culture |
| History | Історична правда, Ukraїner | History modules |
| Music | Official artist channels | Songs, culture |
| Cooking | Ukrainian cooking channels | Vocabulary, culture |
| Travel | Ukraїner, travel vloggers | Geography, dialects |
| Language | Ukrainian teachers | Grammar explanations |

---

## Module-to-Vibe Mapping

> ⚠️ **STALE / NEEDS REWORK**
> This section is currently outdated and requires significant rework to align with the new "Theory-First" approach and data structure. Do not rely on these mapping rules until updated.

### One Module → Multiple Vibe Lessons

A single curriculum module can generate:

| Vibe Lesson | Content |
|-------------|---------|
| Lesson 1 | Theory + Basic practice |
| Lesson 2 | Vocabulary deep dive |
| Lesson 3 | Interactive activities |
| Lesson 4 | Production + Review |

### When to Split

**Split a module into multiple Vibe lessons when ANY apply:**

| Trigger | Threshold | Rationale |
|---------|-----------|-----------|
| Duration | > 60 min estimated | Learner fatigue, session limits |
| Vocabulary | > 25 words | Memory overload |
| Activities | > 5 activities | Too much in one session |
| Grammar points | > 2 major concepts | Cognitive overload |
| Content sections | > 4 distinct topics | Natural breakpoints exist |
| Engagement boxes | > 6 boxes | Information density |

### Splitting Approach

```
Module 01 (too long) → Split into:
├── Lesson 01a: Theory + first activity
├── Lesson 01b: Vocabulary + practice activities
└── Lesson 01c: Production + review
```

### Example Breakdown

**Module 201: Ancient Ukraine** could become:
1. **Vibe Lesson 201a:** Pre-history vocabulary + map activities
2. **Vibe Lesson 201b:** Scythian culture reading + comprehension
3. **Vibe Lesson 201c:** Founding of Kyiv narrative + listening
4. **Vibe Lesson 201d:** Production - describe ancient Ukraine
5. **Vibe Lesson 201e:** Review quiz + cultural discussion

**For now:** Start with 1:1 mapping. Mark heavy modules with:
```yaml
split_candidate: true
split_reason: "25+ vocabulary words, 6 activities"
```

We'll revisit after testing with real learners.

### Generator Adaptation

The generators (`generate-mdx.ts` for web, `generate_json.py` for Vibe) should:
1. Accept module markdown as input
2. Optionally split into multiple Vibe lessons
3. Maintain cross-references between lessons
4. Track which lessons belong to which module

---

## Quality Checklists

### Before Publishing Any Module

**Content Quality:**
- [ ] Grammar explanations are clear and accurate
- [ ] Examples are natural and useful
- [ ] Vocabulary is level-appropriate
- [ ] Activities are varied and engaging
- [ ] Cultural context provided

**Narrative Richness (CRITICAL):**
- [ ] Introduction has compelling WHY (not "In this lesson we learn...")
- [ ] Grammar tables surrounded by narrative (no naked tables)
- [ ] Mini-dialogues present and meet count for level
- [ ] Usage patterns / common mistakes section exists
- [ ] Content word count meets minimum
- [ ] Engagement boxes meet minimum

**Technical Quality:**
- [ ] Markdown renders correctly
- [ ] All links work
- [ ] Vocabulary table complete
- [ ] Activities function properly

### Grammar Module Checklist (A2+)

- [ ] Introduction explains WHY (not just "in this lesson we learn...")
- [ ] Each grammar table has surrounding narrative paragraphs
- [ ] Usage patterns explained (when to use, common mistakes)
- [ ] At least 2 mini-dialogues showing natural use
- [ ] Cultural connection (how Ukrainians actually use this)
- [ ] 4+ engagement boxes (varied types)
- [ ] Word count (excluding tables) reaches level target
- [ ] Examples are in context, not isolated words

### Vocabulary Module Checklist

- [ ] Introduction paragraph (not just "In this lesson we learn...")
- [ ] Each vocab group has contextual paragraph or dialogue
- [ ] Usage patterns explained (not just translated)
- [ ] At least 2 mini-dialogues showing natural use
- [ ] Cultural connection (how Ukrainians use these words)
- [ ] 4+ engagement boxes
- [ ] Word count (excluding tables) reaches 750+

---

## Anti-Patterns (What to Avoid)

| Problem | Example | Fix |
|---------|---------|-----|
| Too short | Only 5 examples for complex grammar | Add 12+ examples minimum |
| Too dense | 50 vocabulary words in one module | Split into multiple modules |
| Boring | Only gap-fill exercises | Mix 4+ activity types |
| Dry | Tables with no narrative | Add paragraphs around every table |
| Rule-dump | Rule → Table → Exercises | Context → Discovery → Practice |

---

## Pronunciation & Phonetics Guide (All Levels)

### When Required

Pronunciation guidance must be integrated actively across all modules where new sounds, challenging phonetic distinctions, or specific intonation patterns are introduced.

| Level | Focus Areas |
|-------|-------------|
| **A1** | IPA for all new vocabulary, key letter sounds (e.g., Ж, Щ, Ц, Г vs Ґ, Ь, И vs І), basic word stress. |
| **A2** | IPA for all new vocabulary, aspect-related stress shifts, challenging consonant clusters, basic intonation patterns for questions/statements. |
| **B1** | IPA for new vocabulary, stress changes in declension/conjugation, sentence rhythm, connected speech phenomena. |
| **B2+** | All above, plus stylistic intonation, regional accents (recognition), phrase stress, fine-tuning of articulation. |

### Required Components

1.  **IPA Transcriptions:** MUST be provided for *all new vocabulary* in the vocabulary table.
2.  **Key Sound Spotlights:** Dedicated sections or engagement boxes for challenging sounds (e.g., Г vs Ґ, Ь, И vs І), providing detailed articulation instructions (mouth position, tongue placement).
3.  **Stress Pattern Guidance:**
    *   For words with mobile stress (B1+), provide examples of stress shifts.
    *   Stress pattern tables for grammatical forms (e.g., passive participles).
4.  **Minimal Pairs:** For sounds that are easily confused, provide minimal pair examples (e.g., сім / сін).
5.  **Intonation Contours:** For sentence-level pronunciation, illustrate basic intonation patterns (e.g., for questions, exclamations, neutral statements).
6.  **Audio Integration (CRITICAL):** All spoken examples (words, phrases, dialogues) MUST have associated native speaker audio.

### Format Example (IPA for Vocabulary)

```markdown
# Vocabulary

| Word | IPA | English | POS | Gender | Note | Audio |
|------|-----|---------|-----|--------|------|-------|
| слово | /ˈslɔvɔ/ | word | noun | n | | [🔊](link_to_audio) |
```

### Format Example (Key Sound Spotlight)

```markdown
> 💡 **Key Sound Spotlight: Г vs Ґ**
> Ukrainian has two distinct 'G' sounds:
> - **Г (Hook):** A soft, breathy 'h' sound (like in 'ahoy'). Your throat barely vibrates.
> - **Ґ (Hook with Hat):** A hard, explosive 'g' sound (like in 'go'). Your throat vibrates strongly.
> Mispronouncing these can change meaning (e.g., Ганна vs Ґанна). Listen carefully and practice:
> [🔊](link_to_audio_g) (Ганна) vs [🔊](link_to_audio_g_hat) (Ґанна)
```

### Rationale

At all levels, accurate pronunciation is foundational. From A1, learners need clear guidance. At B2+, learners need to produce and perceive subtle phonetic and intonational distinctions for native-like fluency and effective communication across all registers.

---

## Grammar Module Example: BAD vs GOOD

### BAD (Rule-Dump Style)

```markdown
# Dative Case

The dative case shows indirect object.

| Noun | Nominative | Dative |
|------|------------|--------|
| мама | мама | мамі |
| друг | друг | другу |
| книга | книга | книзі |

## Exercises
1. Fill in the dative: Я даю ___ (мама).
```

### GOOD (Contextual Style)

```markdown
# Dative Case: The Art of Giving

In Ukrainian culture, giving matters. Whether it's a birthday gift, a cup of tea
to a guest, or advice to a friend — the ACT of giving is deeply woven into daily
life. And Ukrainian grammar has a special case just for recipients: the Dative.

The dative answers: **Кому?** (To whom?) — whenever something is given, told,
shown, or sent TO someone.

> 💡 **Did You Know?** Ukrainians traditionally give flowers in odd numbers
> (3, 5, 7...) for celebrations. Even numbers are only for funerals. So when
> you say "Я дарую мамі квіти" — make sure it's an odd bunch!

**Core Pattern:**

| Who receives? | Nominative | Dative | Example |
|---------------|------------|--------|---------|
| мама | мама | мам-і | Дарую мамі квіти. |
| друг | друг | друг-у | Кажу другу новину. |
| дитина | дитина | дитин-і | Читаю дитині казку. |

Notice the pattern: feminine nouns ending in -а get -і, masculine nouns get -у
(or -ові for people: другові, батькові).

**У реальному житті (In Real Life)**

You're at a birthday party in Lviv:

— Що ти подарував **Олені**?
— Я подарував **їй** книгу про Карпати.
— Вона любить гори?
— Так! Я завжди дарую **друзям** щось особливе.

Notice how the dative marks every recipient: Олені, їй, друзям.

**Common Dative Verbs:**
- **дарувати** — to give as a gift: Дарую мамі квіти.
- **казати** — to tell: Кажу другу правду.
- **показувати** — to show: Показую туристам місто.
- **допомагати** — to help: Допомагаю бабусі.
- **телефонувати** — to call: Телефоную батькам.

> 🎬 **Pop Culture Moment:** In the Ukrainian dub of "The Lord of the Rings",
> when Galadriel gives gifts to the Fellowship, every recipient is in dative:
> "Я даю тобі світло..." The grammar of giving!
```

---

## Vocabulary Module Example: BAD vs GOOD

### BAD (Table-Only Style)

```markdown
# Види спорту

| Спорт | English |
|-------|---------|
| футбол | football |
| баскетбол | basketball |

> 💡 Fact about sports
```

### GOOD (Contextual Style)

```markdown
# Види спорту / Types of Sports

Ukraine has a rich sporting culture. Football (футбол) is the most popular
team sport, with clubs like Dynamo Kyiv and Shakhtar Donetsk competing in
European championships. Basketball (баскетбол) has grown rapidly, especially
among young people in cities.

| Спорт | IPA | English |
|-------|-----|---------|
| футбол | /futˈbɔl/ | football |
| баскетбол | /baskɛtˈbɔl/ | basketball |

**У реальному житті (In Real Life)**

Imagine you're at a café in Kyiv with new Ukrainian friends. They ask about
your hobbies:

— Чим ти займаєшся у вільний час?
— Я граю у футбол щонеділі з друзями.
— О, класно! А де ви граєте?
— На стадіоні біля університету.

Notice how we use "грати в" (play) with ball sports...
```



---

## Implementation Checklist

### Per-Module Requirements

| Level | Modules | Key Features |
|-------|---------|--------------|
| A1 | 30 | Simple sentences, basic activities, anagram allowed |
| A2 | 50 | All cases, aspect, error-correction introduced |
| B1 | 80 | Conditionals, participles, full activity palette |
| B2 | 125 | Literary style, register variation, subtle errors |
| C1 | 115 | Academic discourse, specialized topics |
| C2 | 80 | Native-level complexity, professional specialization |

### 6. Fill-in Activity Standards (Strict)
- **Placeholders:** ALWAYS use `___` (three underscores) for the blank. Never use `......` or `(____)`.
- **No Hints:** NEVER put the hint in the sentence line (e.g., `(Bag)`). Hints belong in the `[!options]` block or as a `> [!hint]` callout if absolutely necessary.
- **Mandatory Answer Key:** ALL `fill-in` items MUST have a `> [!answer]` block. This is the source of truth for validation.
- **Mandatory Options:** For ALL levels (A1-C2), ALL `fill-in` activities MUST be accompanied by a `> [!options]` block listing the choices.
  ```markdown
  1. Це ___ (bag).
     > [!answer] сумку
     > [!options]
     > сумку, сумки, сумці
  ```

### 7. Anagram Activity Standards (Strict)
- **Separator:** MUST use **SPACES** to separate letters.
- **Forbidden:** Do NOT use slashes (`/`), commas, or hyphens.
- **Format:** `L E T T E R S`
  ```markdown
  1. К О Р О Б К А
     > [!answer] КОРОБКА
  ```

### 8. Quiz Activity Standards
- **Format:** Use standard Markdown checkbox list.
- **Alternative:** For simple options (e.g. A/B/C), use `> [!options]` block.
- **Example:**
  ```markdown
  1. Question?
     - [ ] Option A
     - [x] Correct Option B
     - [ ] Option C
     > [!explanation] Why B is correct.
  ```

### 2. Match-up (`match-up`)
- **Purpose**: Mapping synonyms, antonyms, translations, or logical pairs.
- **Rule**: STRICT 1-to-1 mapping. For Many-to-One (e.g. 5 numbers -> 1 Case), use `group-sort` instead.
- **Format**: `1. Left Item -> Right Item`
- **Example**:
  ```markdown
  ## match-up: Antonyms
  > Find the opposites.

  1. Big -> Small
  2. Hot -> Cold
  ```

### 3. Group Sort (`group-sort`)
- **Purpose**: Categorizing items into buckets. Best for Genders, Cases, conjugation groups.
- **Rule**: Use this for Many-to-One mappings.
- **Format**: `### Group Name` followed by bullet list.
- **Example**:
  ```markdown
  ## group-sort: Genders
  > Sort words by gender.

  ### Masculine
  - House
  - Dog

  ### Feminine
  - Cat
  - Mouse
  ```

### 8. Unjumble Activity Standards (Strict)
- **Separator:** MUST use **SLASHES** (`/`) to separate words/phrases.
- **Format:** `Word / Word / Word`
  ```markdown
  1. я / люблю / каву
     > [!answer] Я люблю каву.
  ```

### 9. Checkbox & Audio Standards (Strict)
- **Checkboxes:** MUST have a space inside the bracket: `- [ ]`. NEVER use `- []` (empty) or `- [v]` (check mark character).
- **Audio Links:** MUST follow the order: **Word** then **Icon**.
  - **Correct:** `**Стіл** [🔊](link)`
  - **Incorrect:** `[🔊](link) **Стіл**`

### 10. Cultural & Political Tone (The "Vibe" Check)
- **Sovereignty First:** Ukraine is a distinct, sovereign European nation. Avoid any framing that implies it is a "borderland" or "region".
  - **YES:** "Ukraine", "Kyiv", "In Ukraine".
  - **NO:** "The Ukraine", "Kiev", "In the Ukraine".
- **Myth Busting:** Actively dismantle misconceptions (e.g., "Ukrainian is a dialect of Russian"). Frame Ukrainian as the primary, ancient, and rich language it is.
- **De-Russification:** Avoid using Russian reference points unless explicitly contrasting False Friends. Do not assume the student knows Russian.

### Quality Standards

1. **Grammar Accuracy**: All Ukrainian must be grammatically correct
2. **CEFR Alignment**: Complexity matches level descriptors
3. **Variety**: Mix of recognition, production, and analysis activities
4. **Context**: Sentences should be meaningful, not random word combinations
5. **Progression**: Each level builds on previous knowledge
6. **Cultural Relevance**: Include Ukrainian cultural content where appropriate

---

## Iteration & Improvement

### Feedback Loops

After module deployment:
1. **Track completion rates** - Are learners finishing?
2. **Analyze activity results** - Where do they struggle?
3. **Collect user feedback** - What do they want more of?
4. **Native speaker review** - Periodic accuracy checks
5. **Update content** - Improve based on data

### Version Control

Modules should be versioned:
- `module-001-v1.0.md` - Initial release
- `module-001-v1.1.md` - Minor fixes
- `module-001-v2.0.md` - Major revision

Track changes in module metadata:
```yaml
version: 1.2
last_updated: 2025-11-30
changelog:
  - Fixed grammar error in example 3
  - Added video comprehension activity
  - Updated cultural note for current events
```

---

## Automated Pedagogical Checks

The audit script (`python3 scripts/audit_module.py`) runs 11 automated checks that detect pedagogical violations. Violations cause the module to FAIL.

### Grammar Constraint Checks

| Level | Cases Allowed | Cases Forbidden | Aspect | Participles | Subordinate Clauses | Max Sentence Words |
|-------|---------------|-----------------|--------|-------------|---------------------|--------------------|
| **A1** | Nom, Acc, Loc, Gen, Voc | Dative, Instrumental | Imperfective only | ❌ | ❌ | 10 |
| **A2** | All 7 cases | — | Both (introduced) | ❌ | Simple (що, який) | 15 |
| **B1** | All | — | Full mastery | ❌ | Yes | 25 |
| **B2** | All | — | Full | ✅ | Yes | 35 |
| **C1** | All | — | Full | ✅ | Yes | 50 |
| **C2** | All | — | Full | ✅ | Yes | No limit |

### Quality Assurance Checks

| Check | What It Detects | Threshold | Severity |
|-------|-----------------|-----------|----------|
| **Answer Position Bias** | Correct answers always in same position | >70% same position | WARNING |
| **Duplicate Content** | Copy-pasted sentences | 3+ identical sentences | WARNING |
| **Activity Variety** | Overuse of single activity type | >40% of activities | WARNING |
| **IPA Validation** | Invalid IPA symbols in vocabulary table | Any invalid symbol | WARNING |
| **Gender Agreement** | Adjective-noun gender mismatch | Any mismatch | WARNING |
| **Case Government** | Preposition + wrong case | Any error | WARNING |
| **Topic Consistency** | Content doesn't match title/objectives | <30% topic coverage | WARNING |
| **Vocabulary Violations** | Activity uses undefined words | Any undefined word | **FAIL** |
| **Activity Misuse** | match-up used for sorting/categorization | Sorting prompt or symmetric pairs | WARNING |
| **Level Restrictions** | Activity not allowed at level | e.g., anagram after A1 M10 | WARNING |
| **Focus Mismatch** | B1/B2 activities don't match grammar/vocab focus | <30% priority activities | WARNING |

### Activity Misuse Detection

The audit detects **match-up** activities that should be **group-sort**:

**Red flags for match-up misuse:**
- Prompt says "Which word needs/has/contains..." → Should be group-sort
- Prompt says "Sort by..." → Should be group-sort
- Pairs are "X vs variant-of-X" (e.g., word with feature vs without) → Should be group-sort
- No semantic relationship between pairs → Wrong activity type

**Example of BAD match-up (should be group-sort):**
```markdown
## match-up: Soft Sign
> Which word needs the soft sign?
| **Сіль** | **Стіл** |  ← No logical pairing relationship
| **День** | **Дон** |   ← Same word with/without feature = SORTING
```

**Correct approach - use group-sort:**
```markdown
## group-sort: Soft Sign Recognition
> Sort words by whether they contain the soft sign (ь).

### Has Soft Sign (ь)
- Сіль
- День
- Осінь

### No Soft Sign
- Стіл
- Сон
- Дон
```

### Activity Sequencing by Pedagogy

The audit validates that activity stages follow the correct pedagogical sequence:

**PPP (A1-A2):**
```
presentation → recognition → discrimination → controlled-production → free-production
```

**TTT (B1+):**
```
diagnostic → recognition → presentation → controlled-production → free-production
```

**CLIL/Narrative (B1-C2):**
```
pre-engagement → immersion → narrative → deep-dive → recognition → controlled-production → free-production
```

**How to fix:** Add `[stage: xxx]` to activity headers:
```markdown
## fill-in: Case Practice [stage: controlled-production]
## mark-the-words: Find Accusative [stage: recognition]
## translate: Express the Meaning [stage: free-production]
```

### Running the Audit

```bash
python3 scripts/audit_module.py curriculum/l2-uk-en/{level}/module-XX.md
```

The audit will output:
- Gate pass/fail status (Words, Activities, Density, etc.)
- Pedagogical violations with specific FIX suggestions
- Immersion percentage vs target

---

## Revision History

- v3.1 (2025-12): Added Automated Pedagogical Checks documentation.
- v3.0 (2025-12): Maximum Richness alignment with SKILL.md strict standards.
- v2.0 (2025-12): Consolidated from MODULE-RICHNESS-GUIDELINES.md + ACTIVITY-GUIDELINES.md
- v1.0 (2024-12): Initial comprehensive plan with CEFR alignment