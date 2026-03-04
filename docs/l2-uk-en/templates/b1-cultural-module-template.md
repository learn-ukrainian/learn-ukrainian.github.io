# B1 Cultural Module Template

**For:** B1 Phase 7 - Contemporary Ukraine (Modules 71-80)
**Examples:** M71 (Західна Україна), M75 (Українська музика), M76 (Українське кіно), M77 (Технології та стартапи)

---

## Quick Reference Checklist

Before submitting your cultural module, verify:

- [ ] **Word count:** 4000+ words per config.py
- [ ] **Vocabulary:** 25+ items in 5-column format with IPA (Слово | Вимова | English | PoS | Примітки)
- [ ] **Activities:** 8-10 activities (quality over quantity, comprehension-focused)
- [ ] **Activity items:** Quiz/match-up/fill-in 8+ items, cloze 12+ blanks
- [ ] **Reading passages:** 3+ authentic or semi-authentic texts (300-500 words each)
- [ ] **Sentence complexity:** Validated by audit (see `scripts/audit/config.py` for CEFR-aligned targets)
- [ ] **Engagement boxes:** 5+ (focus on real-world cultural references)
- [ ] **Immersion:** 90-100% Ukrainian
- [ ] **External resources:** Added to `docs/resources/external_resources.yaml` (NOT embedded in module)
- [ ] **Cultural accuracy:** All facts verified, no stereotypes
- [ ] **Regional balance:** Neutral presentation of all Ukrainian regions

<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст|Розминка
  - Історія та культура
  - Сучасність
  - Підсумок
  - Потрібно більше практики?
  pedagogy: CBI
  min_word_count: 4000
  required_callouts: []
  description: B1 cultural modules use CBI with regional focus
-->

---

## Key Cultural Module Characteristics

**Different from grammar/vocab modules:**

1. **Content-Driven, Not Grammar-Driven**
   - Grammar is incidental, not the focus
   - Cultural content is the subject matter
   - Reading comprehension is the primary skill

2. **Authentic Materials**
   - Real Ukrainian texts (adapted if needed)
   - News articles, blog posts, Wikipedia excerpts
   - Interviews, social media, cultural commentary

3. **Regional/Topical Focus**
   - M71-74: Ukrainian regions (West, East, South, Center)
   - M75-80: Cultural topics (Music, Cinema, Technology, Sports, Cuisine, Capstone)

4. **Vocabulary is Contextual**
   - Words for discussing the topic
   - Cultural terminology (genres, historical terms, regional names)
   - Less emphasis on grammar terminology

5. **Reading-Heavy Structure**
   - Multiple passages (3-5 per module)
   - Comprehension activities dominate
   - Less explicit instruction, more discovery

6. **Contemporary Focus**
   - Modern Ukraine (post-1991, especially 2010s-2020s)
   - Living culture, not just history
   - Real people, real achievements

---

## Cultural Module Structure (PPP Pedagogy)

### Frontmatter

```yaml
---
module: [number]
title: [Ukrainian title]
subtitle: [English subtitle]
level: B1
phase: B1.7
pedagogy: PPP
objectives:
  - Learner can discuss [topic] in Ukrainian
  - Learner can understand authentic texts about [topic]
  - Learner can use [topic]-specific vocabulary in context
word_target: 1500
vocab_target: 25 # Must match count in vocabulary/{slug}.yaml
immersion_target: 90-95%
---
```

**Why these objectives:** Cultural modules develop reading comprehension and topical discussion skills, not grammar mastery.

---

### Section 1: Вступ (Introduction) - 200-300 words

**Purpose:** Activate prior knowledge, preview the topic

**WHY:** Learners need context before diving into authentic texts.

**Structure:**

#### Opening Hook (50-100 words)

- Engaging question or statement about the topic
- Example: "Чи знаєте ви українських музикантів?" (M75)
- Example: "Західна Україна — це регіон з унікальною історією та культурою." (M71)

#### Overview (100-150 words)

- What the module covers
- Why this topic matters for Ukrainian cultural competence
- Preview of subtopics (e.g., for M71: Lviv, Zakarpattia, Halychyna)

#### Vocabulary Preview (50-100 words)

- Introduce 5-8 key terms with context
- Example: "У цьому модулі ви вивчите слова для обговорення української музики: **хіт**, **альбом**, **концерт**, **фестиваль**."

**Engagement Box (1):**

> 🌍 **Реальний світ:** [Cultural fact or connection to learner's experience]

---

### Section 2: Презентація (Presentation) - 600-800 words

**Purpose:** Present the cultural content through authentic reading passages

**WHY:** B1 learners need exposure to real Ukrainian discourse, not simplified textbook prose.

**Structure:**

#### Passage 1: Overview Text (200-300 words)

- Introduces the topic broadly
- Adapted from Wikipedia, cultural guides, or educational materials
- Example (M75): History of Ukrainian music from folk to contemporary

**Format:**

```markdown
#### [Passage Title]

[200-300 words of Ukrainian text]

**Comprehension Questions (3-4):**

1. [Question in Ukrainian]
2. [Question in Ukrainian]
3. [Question in Ukrainian]
```

**WHY comprehension questions:** Guides reading without breaking immersion.

#### Passage 2: Focused Subtopic (200-300 words)

- Zooms into a specific aspect
- Example (M71): Львів як культурна столиця
- Example (M76): Довженко and Ukrainian cinema's golden age

#### Passage 3: Contemporary Application (200-300 words)

- Modern examples, current events
- Example (M75): Eurovision 2022, contemporary Ukrainian bands
- Example (M77): Ukrainian IT sector and startups

**Engagement Boxes (2-3):**

> 💡 **Чи знали ви:** [Interesting cultural fact]
> 🎬 **Момент поп-культури:** [Reference to Ukrainian films, music, games]
> 🎯 **Цікавий факт:** [Memorable trivia]

**WHY 3 passages:** Provides variety, builds comprehensive understanding, maintains engagement.

---

### Section 3: Практика (Practice) - 400-600 words

**Purpose:** Consolidate understanding through varied activities

**WHY:** Cultural modules need reading comprehension and vocabulary practice, not grammar drills.

**Activities Order (8-10 total):**

#### Core Activities (Required - choose 6-7):

1. **quiz** (8+ items, 12-20 words each) — Reading comprehension, cultural knowledge
2. **true-false** (8+ items) — Fact verification from passages
3. **match-up** (8+ items) — Match people/places/terms to descriptions
4. **fill-in** (8+ items) — Vocabulary in cultural context
5. **cloze** (12+ blanks) — Extended passage completion
6. **unjumble** (6+ items, 12-16 words) — Sentences about cultural content
7. **translate** (6+ items) — Cultural phrases

#### Optional Activities (choose 1-3 to reach 8-10 total):

8. **group-sort** (12+ items) — Categorize regions/genres/time periods
9. **select** (6+ items) — Multiple correct answers (e.g., "Which are Western Ukrainian cities?")
10. **mark-the-words** (6+ target words) — Identify cultural terms
11. **error-correction** (6+ items) — Common misconceptions or mistakes

**WHY this order:** Reading comprehension first, then analytical tasks, finally production.

---

### Section 4: Продукція (Production) - 200-300 words

**Purpose:** Apply knowledge in communicative contexts

**Structure:**

#### Mini-Dialogues (3-4 dialogues, 6-8 turns each)

- Conversations about the cultural topic
- Example (M75): Discussing favorite Ukrainian bands
- Example (M71): Planning a trip to Western Ukraine

**Format:**

```markdown
#### Діалог 1: [Title]

**Олена:** [Turn 1 in Ukrainian]
**Тарас:** [Turn 2 in Ukrainian]
**Олена:** [Turn 3 in Ukrainian]
**Тарас:** [Turn 4 in Ukrainian]
...
```

**WHY dialogues:** Shows how cultural knowledge is used in real conversations.

#### Discussion Prompts (optional, 50-100 words)

- Open-ended questions for learner reflection
- Example: "Яка українська музика вам подобається? Чому?"
- Example: "Який український регіон ви хочете відвідати?"

**Engagement Box (1):**

> 🌍 **Реальний світ:** [How to use this knowledge when visiting Ukraine]

---

### Section 5: Підсумок (Summary) - 100-200 words

**Purpose:** Recap key cultural content and vocabulary

**Structure:**

#### What You've Learned (100-150 words)

- List main topics covered
- Example (M71): "Ви дізналися про Західну Україну: Львів, Закарпаття, Галичину..."
- Highlight key vocabulary (8-10 words)

#### Cultural Competence Reflection (50-100 words)

- How this knowledge helps with Ukrainian cultural fluency
- Connection to broader Ukrainian culture

**WHY:** Reinforces learning and builds metacognitive awareness.

---

### CRITICAL: Language Practice, Not Content Testing

<critical>

**Activities test LANGUAGE SKILLS, not cultural knowledge.**

The lesson teaches both Ukrainian AND cultural content. Activities practice only Ukrainian using the cultural content as context.

**✅ CORRECT:** "Згідно з текстом, як автор описує українську музичну сцену?" (requires reading Ukrainian)
**❌ WRONG:** "У якому році Kalush Orchestra виграли Євробачення?" (tests recall, not language)

**Key Test:** Can the learner answer without reading the Ukrainian text? If yes, rewrite.

| Component          | Purpose                                                                   |
| ------------------ | ------------------------------------------------------------------------- |
| **Lesson Content** | Teaches BOTH Ukrainian language AND cultural knowledge                    |
| **Activities**     | Practice ONLY Ukrainian language skills using cultural content as context |

**Activity Types and Their Language Focus:**

- **quiz**: Test reading comprehension — "Згідно з текстом, що автор виділяє як...?"
- **true-false**: Test comprehension of statements in the text — "У тексті зазначено, що..."
- **match-up**: Test vocabulary recognition — match Ukrainian terms to Ukrainian definitions
- **fill-in**: Test vocabulary/collocations — "Цей гурт \_\_\_\_ популярність після..."
- **cloze**: Test vocabulary in extended context
- **group-sort**: Test categorization using module vocabulary
- **select**: Test reading comprehension (multiple correct)
- **error-correction**: Test grammar, NOT cultural facts
- **unjumble**: Test word order and grammar

</critical>

---

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/b1-75-ukrainian-music.yaml`:**

```yaml
- type: quiz
  title: Українська музика (Reading Comprehension)
  instruction: Відповідайте на питання на основі прочитаного тексту.
  items:
    - question: Згідно з текстом, який гурт переміг на Євробаченні у 2022 році?
      options:
        - text: Kalush Orchestra
          correct: true
        - text: Go_A
          correct: false
```

---

### Section 6: Вправи (Activities)

**8-10 activities** (reduced from 12+, Jan 2026 - quality over quantity)

**Activity Mix for Cultural Modules:**

| Activity Type    | Count      | Priority | Purpose (LANGUAGE focus)                             |
| ---------------- | ---------- | -------- | ---------------------------------------------------- |
| quiz             | 8+ items   | HIGH     | Reading comprehension — "Згідно з текстом..."        |
| true-false       | 8+ items   | HIGH     | Comprehension of text statements                     |
| match-up         | 8+ items   | HIGH     | Vocabulary — Ukrainian terms ↔ Ukrainian definitions |
| fill-in          | 8+ items   | HIGH     | Vocabulary/collocations in context                   |
| cloze            | 12+ blanks | HIGH     | Vocabulary in extended passage                       |
| group-sort       | 12+ items  | MEDIUM   | Categorization using module vocabulary               |
| select           | 6+ items   | MEDIUM   | Multi-select reading comprehension                   |
| mark-the-words   | 6+ words   | MEDIUM   | Grammar recognition (verbs, nouns, etc.)             |
| unjumble         | 6+ items   | LOW      | Word order and grammar                               |
| error-correction | 6+ items   | LOW      | Grammar errors, NOT cultural mistakes                |
| translate        | 6+ items   | LOW      | Vocabulary in translation context                    |

**WHY this mix:** Cultural modules prioritize comprehension (quiz, true-false, match-up, cloze) over production (unjumble, error-correction).

**Note:** Choose 8-10 total activities focusing on core types (quiz, match-up, fill-in, cloze, translate).

---

### Section 7: Словник (Vocabulary)

**CRITICAL:** Vocabulary must be defined in `vocabulary/{slug}.yaml`. Do NOT embed a vocabulary table in Markdown.

**Example `vocabulary/b1-75-ukrainian-music.yaml`:**

```yaml
items:
  - lemma: захід
    ipa: /zɑxid/
    translation: west
    pos: ім. (ч.р.)
    gender: m
    note: напрямок або регіон
  - lemma: столиця
    ipa: /stolɪt͡sʲɑ/
    translation: capital
    pos: ім. (ж.р.)
    gender: f
    note: головне місто країни
```

**Requirements:**

- **25+ items** minimum
- **Thematic organization**
- **IPA pronunciation** for all entries
- **Contextual notes** in `note` field

**Vocabulary Categories for Cultural Modules:**

**Regional Modules (M71-74):**

- Region/direction names (захід, схід, південь, центр)
- Cities and geographical features (Львів, Одеса, Дніпро, Карпати)
- Historical/cultural terms (козацтво, спадщина, архітектура)
- Adjectives for description (мальовничий, історичний, багатонаціональний)

**Topical Modules (M75-80):**

- Domain-specific vocabulary (музика → хіт, альбом, концерт; кіно → фільм, режисер, кінострічка)
- Verbs for discussion (обговорювати, рекомендувати, впливати)
- Evaluative language (талановитий, популярний, видатний)

---

### Section 8: External Resources

> **⚠️ NOTE:** External resources are managed in `docs/resources/external_resources.yaml`, NOT in module markdown files. Do NOT add `[!resources]` blocks to modules.

**To add resources for a cultural module:**

1. Open `docs/resources/external_resources.yaml`
2. Add entries with the module ID:

```yaml
- module_id: b1-75
  url: 'https://www.eurovision.ua/'
  title: 'Євробачення - UA:PBC'
  type: website
  relevance: 5
  description: 'Official Ukrainian Eurovision site'

- module_id: b1-75
  url: 'https://uk.wikipedia.org/wiki/Українська_музика'
  title: 'Українська музика (Wikipedia)'
  type: article
  relevance: 4
```

**Resource types:** `website`, `article`, `video`, `podcast`, `book`, `music`

**WHY:** Centralized resources are easier to maintain, validate links, and update.

---

## Common Pitfalls to Avoid

### 1. **Oversimplified or Stereotypical Content**

**Problem:** "Ukrainians love borscht and wear vyshyvankas."
**Fix:** Focus on contemporary, diverse Ukraine. Real achievements, real complexity.

**Example:**

- ❌ Bad: "Всі українці люблять борщ." (Stereotypical)
- ✅ Good: "Українська кухня різноманітна: борщ, вареники, деруни, банош. Кожен регіон має свої страви." (Diverse, regional)

---

### 2. **Insufficient Authentic Materials**

**Problem:** Only constructed texts, no real Ukrainian sources.
**Fix:** Adapt real Ukrainian Wikipedia articles, news, blogs. Cite sources in Resources section.

**Example:**

- ❌ Bad: Made-up text about Ukrainian music with no real references
- ✅ Good: Adapted Wikipedia article on "Українська музика" with comprehension activities

---

### 3. **Missing Regional Balance**

**Problem:** Only focusing on Kyiv or Lviv, ignoring other regions.
**Fix:** For regional modules (M71-74), ensure neutral, balanced coverage. For topical modules (M75-80), include examples from various regions.

**Example (M75 - Music):**

- ✅ Include: Kyiv bands (Okean Elzy), Lviv bands (Tartak), Kharkiv bands, etc.
- ❌ Avoid: Only Kyiv-based artists

---

### 4. **Grammar-Heavy Approach**

**Problem:** Turning cultural module into grammar lesson.
**Fix:** Grammar is incidental. If a passage uses aspect, don't explain aspect—just use it naturally.

**Example:**

- ❌ Bad: "У цьому тексті ми бачимо доконаний вид..." (Grammar focus)
- ✅ Good: Just use perfective aspect naturally in cultural text without metalinguistic commentary

---

### 5. **Outdated Cultural Information**

**Problem:** Focusing on Soviet era or pre-2014 Ukraine exclusively.
**Fix:** Contemporary Ukraine (2010s-2020s) should dominate. Mention history for context, but focus on NOW.

**Example (M76 - Cinema):**

- ✅ Include: Dovzhenko (historical context) → contemporary Ukrainian films (Atlantis, Donbas, Tribe)
- ❌ Avoid: Only Soviet-era Ukrainian cinema

---

### 6. **Insufficient Reading Comprehension Activities**

**Problem:** Only 1-2 quiz questions after a 300-word passage.
**Fix:** 3-5 comprehension questions per passage, varied question types.

**Example:**

```markdown
#### Passage: Львів — культурна столиця України

[300 words about Lviv]

**Comprehension Questions:**

1. Коли Львів було засновано?
2. Які архітектурні стилі можна побачити у Львові?
3. Чому Львів називають "кавовою столицею України"?
4. Які фестивалі проводяться у Львові?
```

---

### 7. **No Resources Section**

**Problem:** No links to authentic Ukrainian materials.
**Fix:** Always include Resources section with 5-10 links to real Ukrainian websites, videos, articles.

---

### 8. **Quiz Questions Too Short or Too Simple**

**Problem:** "Де знаходиться Львів?" (6 words)
**Fix:** 12-20 words with context: "Львів знаходиться в західній Україні і є одним з найбільших культурних центрів країни. Де саме розташоване місто?"

**Example:**

- ❌ Bad: "Хто такий Довженко?" (3 words)
- ✅ Good: "Олександр Довженко був видатним українським режисером, який створив фільм 'Земля' у 1930 році. Чим він відомий у світовому кінематографі?" (18 words)

---

## Audit Validation Checklist

Before running the audit script, manually verify:

### Content Gates:

- [ ] **3+ reading passages** of 200-300 words each (authentic or adapted)
- [ ] **Comprehension questions** after each passage (3-5 questions)
- [ ] **Resources section** with 5+ links to authentic Ukrainian materials
- [ ] **Cultural accuracy** - all facts verified, sources cited
- [ ] **Contemporary focus** - post-1991 Ukraine, especially 2010s-2020s
- [ ] **Regional balance** - no region ignored or overrepresented

### Technical Gates:

- [ ] **Word count:** 4000+ words per config.py (run `.venv/bin/python scripts/audit_module.py`)
- [ ] **Vocabulary:** 25+ items in 5-column format with IPA
- [ ] **Activities:** 8-10 activities (quality over quantity)
- [ ] **Activity items:** Quiz/match-up/fill-in 8+ items each
- [ ] **Sentence complexity:** Validated by audit (see `scripts/audit/config.py` for CEFR-aligned targets)
- [ ] **Cloze passages:** 12+ blanks (check manually)
- [ ] **Engagement boxes:** 5+ boxes
- [ ] **Immersion:** 90-100% Ukrainian (audit script checks)

### Activity Mix:

- [ ] **High comprehension focus:** quiz (8+), true-false (8+), match-up (8+), cloze (12+)
- [ ] **Vocabulary practice:** fill-in (8+), group-sort (12+), select (6+)
- [ ] **Production:** unjumble (6+), error-correction (6+), translate (6+)

---

## Creator's Pre-Submission Checklist

### Phase 1: Research and Planning

- [ ] Read module specification in B1-CURRICULUM-PLAN.md
- [ ] Research authentic Ukrainian sources (Wikipedia, news, cultural sites)
- [ ] Identify 3-5 reading passages (adapt if needed, cite sources)
- [ ] Extract 25+ vocabulary items from passages
- [ ] Plan activity mix (prioritize comprehension activities)

### Phase 2: Content Creation

- [ ] Write Вступ (Introduction) with hook and overview
- [ ] Write Презентація with 3 reading passages (200-300 words each)
- [ ] Add comprehension questions after each passage
- [ ] Write Практика section overview (linking to activities)
- [ ] Write Продукція with 3-4 dialogues (6-8 turns each)
- [ ] Write Підсумок (Summary) with cultural reflection
- [ ] Create Resources section with 5-10 authentic links

### Phase 3: Activities

- [ ] Create 8-10 activities following cultural module priority mix (core: quiz, match-up, fill-in, cloze, translate)
- [ ] Verify sentence complexity (see config.py for targets)
- [ ] Sentence complexity validated by audit
- [ ] Verify cloze passage has 12+ blanks
- [ ] Verify all error-correction activities have all 4 callouts
- [ ] Verify all activities have correct item counts (see matrix)

### Phase 4: Vocabulary

- [ ] Create 5-column vocabulary table (Слово | Вимова | English | PoS | Примітки)
- [ ] Add IPA pronunciation for all 25+ words
- [ ] Organize thematically (not alphabetically)
- [ ] Add contextual notes in Примітки column

### Phase 5: Engagement

- [ ] Add 5+ engagement boxes (💡 Чи знали ви, 🌍 Реальний світ, 🎬 Поп-культура, 🎯 Цікавий факт)
- [ ] Verify cultural facts are accurate (cite sources mentally)
- [ ] Ensure contemporary focus (post-2014 Ukraine prominent)

### Phase 6: Audit

- [ ] Run `python3 scripts/audit_module.py curriculum/l2-uk-en/b1/[module-file].md`
- [ ] Fix any gate failures (word count, vocab count, activity counts)
- [ ] Sentence complexity validated by audit (config.py)
- [ ] Sentence complexity validated by audit (config.py)
- [ ] Manually verify cloze blank count (14+)
- [ ] Verify immersion percentage (90-95%)

### Phase 7: Final Review

- [ ] Read the entire module as a learner would
- [ ] Check for stereotypes or outdated information
- [ ] Verify regional balance (if applicable)
- [ ] Verify Resources section has working links
- [ ] Confirm all sources are Ukrainian (not Russian or other languages)

---

## Example Module Outline: M75 - Українська музика сьогодні

**Specification (from B1-CURRICULUM-PLAN.md):**

- **Topic:** Ukrainian music today
- **Vocabulary:** 25 words (музика, пісня, хіт, альбом, концерт, фестиваль, виконавець, гурт, сцена, etc.)
- **Cultural Content:** Eurovision, contemporary artists, music festivals

**Implementation:**

### Frontmatter

```yaml
---
module: 75
title: Українська музика сьогодні
subtitle: Contemporary Ukrainian Music
level: B1
phase: B1.7
pedagogy: PPP
objectives:
  - Learner can discuss Ukrainian music in context
  - Learner can understand authentic texts about Ukrainian artists and festivals
  - Learner can use music-related vocabulary to express preferences
  - Learner can compare Ukrainian music with their own musical culture
word_target: 1500
vocab_target: 25
immersion_target: 90-95%
---
```

### Section 1: Вступ (200 words)

"Чи знаєте ви українських музикантів? Україна має багату музичну традицію та яскраву сучасну музичну сцену..."

> 🎬 **Момент поп-культури:** Ukraine's Eurovision victories (Ruslana 2004, Jamala 2016, Kalush Orchestra 2022)

### Section 2: Презентація (700 words)

**Passage 1:** Історія української популярної музики (250 words)

- From Soviet era to independence
- Key milestones: Okean Elzy, VV, Skryabin

**Passage 2:** Євробачення та міжнародний успіх (250 words)

- Ukraine's Eurovision history
- Cultural impact of victories

**Passage 3:** Сучасна українська музична сцена (200 words)

- Contemporary bands and artists (Kalush Orchestra, Go_A, Onuka, The Hardkiss)
- Music festivals (Країна Мрій, Atlas Weekend, Фестиваль польської пісні)

> 💡 **Чи знали ви:** Jamala's "1944" was the first song about Crimean Tatar deportation to win Eurovision.
> 🌍 **Реальний світ:** Ukrainian music festivals attract 50,000+ attendees annually.

### Section 3: Практика (400 words)

- Activity overview linking to Activities section

### Section 4: Продукція (200 words)

**Dialogue 1:** Обговорення улюбленої української музики
**Dialogue 2:** Планування відвідування концерту
**Dialogue 3:** Розмова про Євробачення

### Section 5: Підсумок (100 words)

"Ви дізналися про сучасну українську музику: від Євробачення до музичних фестивалів. Тепер ви можете обговорювати українських виконавців та їхні досягнення."

### Section 6: Вправи (8-10 activities)

1. quiz: Українська музика (8 items, comprehension)
2. true-false: Факти про Євробачення (8 items)
3. match-up: Виконавці та пісні (8 items)
4. fill-in: Музична лексика (8 items)
5. cloze: Текст про Kalush Orchestra (12 blanks)
6. unjumble: Речення про музику (6 items)
7. translate: Музичні фрази (6 items)
8. group-sort: Жанри, виконавці, фестивалі (12 items) [optional]

### Section 7: Словник (25 words)

музика, пісня, хіт, альбом, концерт, фестиваль, виконавець, гурт, сцена, публіка, аплодисменти, співак, співачка, композитор, текст, мелодія, ритм, жанр, рок, поп, фолк, електронна музика, виступ, слава, успіх

### Section 8: External Resources

*Added to `docs/resources/external_resources.yaml` with `module_id: b1-75`:*

- Євробачення - UA:PBC (website)
- Ukrainian Music Wikipedia (article)
- Країна Мрій Festival (website)
- Atlas Weekend (website)
- YouTube channels: Kalush Orchestra, Go_A, Onuka (video)

---

## Notes for AI Agents

**When creating cultural modules:**

1. **Research first:** Read Ukrainian Wikipedia, news sites, cultural portals BEFORE writing.
2. **Cite mentally:** Know where each fact came from (even if not formally cited in the module).
3. **Verify dates and facts:** Ukrainian history is sensitive. Get it right.
4. **Avoid Russian sources:** Use Ukrainian-language sources only.
5. **Contemporary focus:** Ukraine today is dynamic, not frozen in Soviet past.
6. **Regional diversity:** Ukraine is not monolithic. Show variety.
7. **Real people, real achievements:** Name real Ukrainian artists, athletes, filmmakers, tech founders.
8. **Resources matter:** External resources in `docs/resources/external_resources.yaml` are mandatory—they bridge to authentic Ukrainian content.

**Activity creation for cultural modules:**

- Prioritize reading comprehension (quiz, true-false, match-up, cloze)
- Use authentic cultural content as CONTEXT for language practice
- Quiz questions should test READING COMPREHENSION, not cultural recall — always frame as "Згідно з текстом..."
- Error-correction should test GRAMMAR, not cultural misconceptions
- All activities must require reading the Ukrainian text to answer correctly

**Common mistakes to avoid:**

- ❌ Treating cultural modules like grammar modules (don't over-explain grammar)
- ❌ Using only constructed texts (use adapted authentic materials)
- ❌ Stereotyping (avoid "all Ukrainians..." statements)
- ❌ Ignoring contemporary Ukraine (don't focus only on history/folklore)
- ❌ Missing external resources (add to `docs/resources/external_resources.yaml`)

---

## Clean MD Architecture Note

### Activities, Vocabulary, and External Resources

**CRITICAL:** Do NOT add `## Activities`, `## Vocabulary`, or `## External Resources` headers to the Markdown file. These sections are automatically injected by the build system from the corresponding YAML sidecars:

- `activities/{slug}.yaml` → `## Activities` section
- `vocabulary/{slug}.yaml` → `## Vocabulary` section
- `docs/resources/external_resources.yaml` (filtered by `module_id`) → `## External Resources` section

The module structure follows **Clean MD architecture**: Markdown contains narrative content only, YAML sidecars contain structured data.

---

**End of B1 Cultural Module Template**

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
