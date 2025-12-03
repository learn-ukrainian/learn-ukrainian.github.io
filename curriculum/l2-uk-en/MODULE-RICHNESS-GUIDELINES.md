# Module Richness Guidelines

## Philosophy

> **The curriculum is the goal. Vibe is just a tool.**

Modules should be **rich, engaging, and comprehensive**. One curriculum module may generate multiple Vibe lessons - this is expected and encouraged. The curriculum should never be constrained by platform limitations.

---

## Module Length & Depth

### Minimum Content Requirements

| Level | Min Duration | Min Vocabulary | Activity Count | Items per Activity | Depth Expectation |
|-------|--------------|----------------|----------------|-------------------|-------------------|
| A1 | 30 min | 15 words | 6 | 10 | Foundation building |
| A2 | 35 min | 20 words | 8 | 10 | Skill expansion |
| A2+ | 40 min | 22 words | 10 | 15 | Transition to B1 |
| B1 | 40 min | 25 words | 12 | 20 | Complex integration |
| B2 | 45 min | 30 words | 14 | 20 | Professional depth |
| C1 | 50 min | 30 words | 14 | 20 | Near-native richness |
| Tracks | 45-60 min | 35 words | 14 | 20 | Domain expertise |

### Activity Type Priority

When adding activities to a module, prioritize in this order:

1. **quiz** - Multiple choice comprehension
2. **match-up** - Vocabulary associations
3. **group-sort** - Categorization skills
4. **true-false** - Statement validation
5. **select** - Word selection
6. **order** - Sequence building
7. **fill-in** - Gap completion (sentence complexity applies)
8. **unjumble** - Word ordering (sentence complexity applies)

**Rationale:** fill-in and unjumble are highest cognitive load activities. Build comprehension with lower-load activities first, then challenge with production tasks.

---

## CEFR Sentence Complexity Standards

Activity sentences must follow CEFR complexity progression:

| Level | Fill-in Words | Unjumble Words | Sentence Structure Examples |
|-------|---------------|----------------|----------------------------|
| A1 | 3-5 | 4-6 | Simple isolated phrases: `Я читаю книгу.` |
| A2 | 6-8 | 8-10 | Simple sentences + connectors: `Я завжди даю мамі квіти на свято.` |
| A2+ | 8-10 | 10-12 | Subordinate clauses begin: `Він каже, що хоче допомогти своїй сестрі.` |
| B1 | 10-14 | 12-16 | Complex sentences, conditionals: `Якби я мав більше часу, я б допоміг тобі з роботою.` |
| B2 | 12-16 | 14-18 | Sophisticated structures, passive: `Було вирішено, що проєкт буде завершено до кінця місяця.` |

### Complexity Progression Principles

1. **A1 (Modules 1-30)**: Foundation
   - Simple SVO sentences
   - Basic vocabulary, high-frequency words
   - No subordinate clauses
   - Example: `Це моя книга.` (3 words)

2. **A2 (Modules 31-60)**: Expansion
   - Add adjectives, adverbs, time expressions
   - Simple connectors (і, але, тому що)
   - Basic prepositional phrases
   - Example: `Я завжди читаю цікаві книги ввечері.` (6 words)

3. **A2+ (Modules 61-80)**: Transition
   - Subordinate clauses with що, який, коли
   - More complex verb forms
   - Multiple modifiers
   - Example: `Дівчина, яка працює в цьому офісі, дуже добре говорить англійською.` (10 words)

4. **B1 (Modules 81-140)**: Integration
   - Conditional sentences (якщо, якби)
   - Reported speech
   - Complex time expressions
   - Example: `Якби я знав про цю проблему раніше, я б обов'язково допоміг тобі її вирішити.` (14 words)

5. **B2 (Modules 141-190)**: Sophistication
   - Passive constructions
   - Abstract vocabulary
   - Nuanced connectors
   - Example: `Незважаючи на те, що проєкт був складним, команда успішно завершила його вчасно.` (12 words)

### Content Depth Indicators

A "rich" module includes:

- [ ] **Theory section** with clear explanations
- [ ] **Multiple examples** (not just 1-2)
- [ ] **Authentic materials** (real texts, media)
- [ ] **Cultural context** where relevant
- [ ] **Common mistakes** section (Типові помилки)
- [ ] **Practice activities** (varied types)
- [ ] **Production tasks** (speaking/writing)
- [ ] **Self-assessment** checklist
- [ ] **Pronunciation guidance** (B2+ grammar modules)

---

## Module-to-Vibe Mapping

### One Module → Multiple Vibe Lessons

A single curriculum module can generate:

| Vibe Lesson | Content |
|-------------|---------|
| Lesson 1 | Theory + Basic practice |
| Lesson 2 | Vocabulary deep dive |
| Lesson 3 | Interactive activities |
| Lesson 4 | Production + Review |

### When to Split: Decision Criteria

**Split a module into multiple Vibe lessons when ANY of these apply:**

| Trigger | Threshold | Rationale |
|---------|-----------|-----------|
| Duration | > 45 min estimated | Learner fatigue, session limits |
| Vocabulary | > 25 words | Memory overload |
| Activities | > 5 activities | Too much in one session |
| Grammar points | > 2 major concepts | Cognitive overload |
| Content sections | > 4 distinct topics | Natural breakpoints exist |
| Engagement boxes | > 6 boxes | Information density |

**How to decide:**

1. **After writing module** - Review against thresholds above
2. **Natural breakpoints** - Look for clear topic transitions
3. **Learner testing** - If completion rates drop, consider splitting
4. **Platform feedback** - Vibe may have session length recommendations

**Splitting approach:**

```
Module 01 (too long) → Split into:
├── Lesson 01a: Theory + first activity
├── Lesson 01b: Vocabulary + practice activities
└── Lesson 01c: Production + review
```

**For now:** Start with 1:1 mapping. Mark modules that feel "heavy" with a note:
```yaml
split_candidate: true
split_reason: "25+ vocabulary words, 6 activities"
```

We'll revisit after testing with real learners.

### Example Breakdown

**Module 201: Ancient Ukraine**

Could become:
1. **Vibe Lesson 201a:** Pre-history vocabulary + map activities
2. **Vibe Lesson 201b:** Scythian culture reading + comprehension
3. **Vibe Lesson 201c:** Founding of Kyiv narrative + listening
4. **Vibe Lesson 201d:** Production - describe ancient Ukraine
5. **Vibe Lesson 201e:** Review quiz + cultural discussion

### Generator Adaptation

The generator (`scripts/generate.ts`) should:
1. Accept module markdown as input
2. Optionally split into multiple Vibe lessons
3. Maintain cross-references between lessons
4. Track which lessons belong to which module

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

## Media Integration

### Types of Media

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

---

## Video Integration Workflow

### Finding Videos

1. **Search Ukrainian YouTube** for topic
2. **Evaluate quality:** Audio clarity, content accuracy
3. **Check channel:** Reputable creators preferred
4. **Note timestamp:** Specific segment needed
5. **Add to sources tracking**

### Recommended Channel Types

| Type | Examples | Good For |
|------|----------|----------|
| News | Укрінформ, Радіо Свобода | Current events, listening |
| Educational | Простопросто, Цікава наука | Explanations, culture |
| History | Історична правда, Ukraїner | History modules |
| Music | Official artist channels | Songs, culture |
| Cooking | Ukrainian cooking channels | Vocabulary, culture |
| Travel | Ukraїner, travel vloggers | Geography, dialects |
| Language | Ukrainian teachers | Grammar explanations |

### Permission Request Template

```
Subject: Content Usage Request - Educational Curriculum

Dear [Channel Name],

I am developing an open educational curriculum for Ukrainian language learners. I would like to request permission to include clips from your video "[Video Title]" in our learning materials.

Proposed usage:
- Educational, non-commercial curriculum
- Short clip (approximately X minutes)
- Full attribution and link to original
- Used in [Module/Topic description]

Benefits:
- Exposure to language learners worldwide
- Proper attribution driving traffic to your channel
- Supporting Ukrainian language education

Please let me know if you would grant permission for this use, and any conditions you may have.

Thank you for your consideration.

Best regards,
[Name]
[Project]
```

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

## Interesting Context & Engagement Boxes

### Required: Every Module Must Include At Least One

Modules should include **contextual boxes** that make learning memorable and engaging:

| Box Type | Icon | Purpose | Example |
|----------|------|---------|---------|
| Did You Know? | 💡 | Fascinating facts | "Ukrainian has 7 cases, but English lost them 500 years ago!" |
| Myth Buster | 🔍 | Correct misconceptions | "Cyrillic isn't Russian - it was created in Bulgaria!" |
| Pro Tip | ⚡ | Practical advice | "Ukrainians rarely use the formal 'Ви' with family" |
| Culture Corner | 🎭 | Traditions, customs | "Why Ukrainians say 'на Україні' is controversial" |
| History Bite | 📜 | Historical context | "The letter Ї exists only in Ukrainian - no other Slavic language has it" |
| Fun Fact | 🎯 | Memorable tidbits | "The word 'Козак' (Cossack) means 'free man'" |
| Language Link | 🔗 | Connections to English | "'Borsch' entered English from Ukrainian, not Russian" |
| Real World | 🌍 | Modern relevance | "These words appear daily in Ukrainian news" |

### Box Format in Markdown

```markdown
> 💡 **Did You Know?**
>
> The Cyrillic alphabet was NOT invented by Russians! It was created in the
> 9th century in Bulgaria by followers of Saints Cyril and Methodius. Russia
> adopted it centuries later. Ukrainian Cyrillic has unique letters (Ї, Є, Ґ)
> that don't exist in Russian!
```

### Placement Guidelines

- **At least 1-2 boxes** per module section
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

**A2 (Grammar Expansion):**
- How Ukrainian cases compare to Latin/German
- Why aspect is "the soul of Slavic languages"
- Historical reasons for grammatical features

**B1-B2 (Intermediate):**
- Language politics and identity
- Regional dialects and their history
- Ukrainian literary tradition
- Famous polyglots who learned Ukrainian

**C1+ (Advanced):**
- Linguistic research about Ukrainian
- Evolution of Ukrainian over centuries
- Influence of other languages
- Debates in modern Ukrainian linguistics

---

## Pronunciation Guidance (B2+ Grammar Modules)

### When Required

Grammar modules at B2+ level that introduce new grammatical forms must include pronunciation guidance:

| Grammar Type | Pronunciation Elements |
|--------------|----------------------|
| Passive forms | -ий vs -о endings, stress patterns |
| Participles | Stress shifts, consonant changes |
| Complex verb forms | Aspect-related stress |
| Formal registers | Intonation patterns |

### Required Components

1. **IPA transcriptions** for key examples
2. **Stress pattern tables** showing where stress falls
3. **Minimal pairs** for forms that sound similar (e.g., написаний vs написано)
4. **Intonation contours** for sentence-level pronunciation

### Format Example

```markdown
# Вимова [grammatical form]

## Наголос

| Форма | IPA | Наголос |
|-------|-----|---------|
| написа́ний | /nɐpɪˈsɑnɪj/ | на -са- |
| напи́сано | /nɐpɪˈsɑno/ | на -са- |

## Мінімальні пари

| Форма 1 | IPA | Форма 2 | IPA |
|---------|-----|---------|-----|
| -ий | /ɪj/ | -о | /o/ |

## Інтонація

| Контекст | Інтонаційний контур |
|----------|---------------------|
| Нейтральний | → ↘ |
| Офіційний | ↗ ↘ |
```

### Rationale

At B2+, learners need to:
- **Produce** accurate pronunciation, not just recognize
- **Distinguish** similar forms by sound
- **Match** register through intonation
- **Self-correct** using stress patterns

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

## Quality Checklist

Before publishing any module:

### Content Quality
- [ ] Grammar explanations are clear and accurate
- [ ] Examples are natural and useful
- [ ] Vocabulary is level-appropriate
- [ ] Activities are varied and engaging
- [ ] Authentic materials included where possible
- [ ] Cultural context provided

### Media Quality
- [ ] All images are high quality
- [ ] Audio is clear and native-speaker produced
- [ ] Videos are educational and appropriate
- [ ] All media sources documented
- [ ] Permissions obtained or pending

### Engagement Quality
- [ ] Module is not text-heavy (balanced with activities)
- [ ] Visual elements break up text
- [ ] Progression from easier to harder
- [ ] Production opportunity included
- [ ] Self-assessment at end

### Technical Quality
- [ ] Markdown renders correctly
- [ ] All links work
- [ ] Vocabulary table complete
- [ ] Activities function properly
- [ ] Can generate valid Vibe lesson(s)

---

## Anti-Patterns (What to Avoid)

### Too Short / Superficial
- Only 5 examples for a complex grammar point
- Single activity type
- No authentic materials
- No cultural context

### Too Dense / Overwhelming
- 50 vocabulary words in one module
- Wall of text with no activities
- No breaks between sections
- Advanced content for lower levels

### Boring / Unengaging
- Only gap-fill exercises
- No visual elements
- Dry, textbook-style presentation
- No real-world connection

### Inaccurate / Misleading
- Grammar mistakes
- Outdated cultural information
- Stereotypical content
- Unverified claims

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
