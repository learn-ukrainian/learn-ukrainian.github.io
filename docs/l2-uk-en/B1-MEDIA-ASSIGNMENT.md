# B1 Media Content Assignment

**Status:** Needs External Resources Added
**Created:** 2024-12-14
**Updated:** 2025-12-21
**Modules:** 85 (including 5 metalanguage bridge modules)

---

## 🚨 MANDATORY: NO RUSSIAN CONTENT

> [!CAUTION]
> **ZERO TOLERANCE FOR RUSSIAN CONTENT**
>
> Russia is committing genocide against Ukraine. Every day Russian forces bomb Ukrainian cities, murder civilians, kidnap children, and commit war crimes. In this context, mixing Russian content with Ukrainian language learning is **completely unacceptable**.
>
> **STRICTLY FORBIDDEN:**
> - ❌ NO videos comparing Ukrainian to Russian
> - ❌ NO "Can Russians understand Ukrainian?" content
> - ❌ NO Russian-language learning resources
> - ❌ NO videos from Russian channels/creators
> - ❌ NO content that frames Ukrainian as a "dialect" or "variant" of Russian
> - ❌ NO content normalizing Russia or Russian culture
>
> **REQUIRED:**
> - ✅ ONLY pure Ukrainian content from Ukrainian creators
> - ✅ Ukrainian channels: Ukrainian Lessons, Speak Ukrainian, Let's Learn Ukrainian
> - ✅ Content that celebrates Ukrainian identity and independence
> - ✅ Myth-buster boxes that debunk Russian propaganda (with "Prosecutor's Voice")
>
> **Before adding ANY YouTube video:**
> 1. Check the channel - is it Ukrainian-owned?
> 2. Check the title - any Russian references or comparisons?
> 3. Check the content - does it treat Ukrainian as its own language?
>
> **If in doubt, DO NOT USE THE VIDEO.**

---

## ⚠️ IMPORTANT: External Resources Not Yet Added

**Current state:** 0/85 B1 modules have `> [!resources]` sections.

See **Issue #170** for the standardization task.

---

## 📋 Standard Format for Module Resources

Every module MUST have a "Need More Practice?" section **before `## Activities`**.

**Standard format:**
```markdown
## Need More Practice?

> [!resources] External Resources
>
> **Topic Links:**
> - 🎧 [Resource Title](URL) — Brief description
> - 🎙️ [Podcast Episode](URL) — Brief description
> - 📖 [Grammar Guide](URL) — Brief description
>
> **Review Previous Modules:**
> - Topic X → Module Y
> - Topic Z → Module W
```

**Live example:** [A1 Module 10](https://krisztiankoos.github.io/curricula-opus/docs/a1/module-10#need-more-practice)

**Icon conventions:**
| Icon | Type |
|------|------|
| 🎧 | Audio guides |
| 🎙️ | Podcast episodes |
| 📖 | Grammar guides |
| 🔊 | Pronunciation tools |
| 📝 | Vocabulary lists |

---

### Verified Resource Sites

| Site | Best For | Example URLs |
|------|----------|--------------|
| **ukrainianlessons.com** | Aspect, motion verbs | `/verb-aspect-in-ukrainian-differences/`, `/perfective-verbs/`, `/ukrainian-verb-prefixes/` |
| **ukrainiancourse.com** | Grammar tables | `/grammar-tables/` |
| **ukrainianlanguage.org.uk** | Academic lessons | `/read/unit08/` (aspect), `/read/unit11/` (motion) |
| **speakua.com** | Blog articles | `/blog/perfective-and-imperfective-verbs` |
| **aspect.in.ua** | Verb aspect pairs | Homepage lookup tool |

### YouTube Channels

| Channel | Handle | Best For |
|---------|--------|----------|
| **Ukrainian Lessons** | `@UkrainianLessons` | Structured grammar, podcasts |
| **Let's Learn Ukrainian** | `@LetsLearnUkrainian` | Aspect, motion verbs deep dives |
| **Ukrainian Language** | `@LearnUkrainianLanguage` | Grammar lessons |
| **Speak Ukrainian** | `@speakukrainian` | Comprehensive grammar |
| **Olga Reznikova** | `@OlgaReznikova` | Wide variety (233K subs) |
| **All-Ukrainian School Online** | `@ukrainian-online-school` | School curriculum (History, Literature) |

### Finding YouTube Videos with yt-dlp

```bash
# B1 topic searches
yt-dlp "ytsearch5:Ukrainian verb aspect perfective imperfective" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian motion verbs prefixes йти їхати" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian participles дієприслівник" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian passive voice пасивний стан" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian complex sentences складні речення" --print "%(webpage_url)s" --skip-download
```

### Module Topics → Search Terms (B1.1-B1.2)

| Phase | Modules | Topics | Search Terms |
|-------|---------|--------|--------------|
| B1.1 | M01-10 | Aspect Mastery | `Ukrainian verb aspect perfective imperfective system` |
| B1.2 | M11-20 | Motion Verbs | `Ukrainian motion verbs prefixes йти ходити` |
| B1.3 | M21-35 | Complex Sentences | `Ukrainian relative clauses щоб якщо якби` |
| B1.4 | M36-45 | Participles/Passive | `Ukrainian дієприслівник passive -но -то` |
| B1.5-6 | M46-65 | Vocabulary | `Ukrainian abstract vocabulary discourse markers` |
| B1.7-8 | M66-80 | Culture/Review | `Ukrainian contemporary culture B1 review` |

---

## Permission Status Legend

| Status | Symbol | Meaning |
|--------|--------|---------|
| Pending | ⏳ | Permission request sent, awaiting response |
| Approved | ✅ | Permission granted |
| Denied | ❌ | Permission denied, find alternative |
| Public Domain | 🌐 | No permission needed |
| Creative Commons | 🔓 | Free to use with attribution |
| Licensed | 💰 | Paid license obtained |
| Self-Created | 🎨 | Created by curriculum team |
| TBD | ❓ | Not yet contacted |

---

## B1 Media Strategy Overview

### B1 Media Principles

1. **Authentic Content Integration**: Transition from pedagogical to authentic Ukrainian media
2. **Regional Immersion**: Heavy use of Ukraїner and regional documentaries
3. **Language History**: Історія мови channel for metalinguistic content
4. **News Literacy**: Real news sources for reading/listening practice
5. **Cultural Depth**: Contemporary music, film, and tech content
6. **Reduced External Links**: More self-created content, targeted external resources

### Content Sources by Phase

| Phase | Primary Sources |
|-------|-----------------|
| B1.1 Aspect (M01-10) | Ukrainian Lessons grammar, self-created timelines |
| B1.2 Motion (M11-20) | Self-created diagrams, city maps |
| B1.3 Complex Sentences (M21-35) | Authentic texts with complex structures |
| B1.4 Advanced Grammar (M36-45) | Literary excerpts, grammar charts |
| B1.5-6 Vocabulary (M46-65) | News articles, business content |
| B1.7 Contemporary Ukraine (M66-75) | Ukraїner, Klopotenko, music/film content |
| B1.8 Skills (M76-80) | Hromadske, Liga.net, podcasts |

### Immersion Level

| Phase | Modules | Immersion Target | Media Approach |
|-------|---------|------------------|----------------|
| B1.0 | M01-05 | No limit | Metalanguage bridge — teach grammar terminology |
| B1.1-2 | M06-25 | 90-95% | Full Ukrainian immersion |
| B1.3-4 | M26-50 | 90-95% | Full Ukrainian immersion |
| B1.5-6 | M51-70 | 90-95% | Full Ukrainian immersion |
| B1.7-8 | M71-85 | 90-95% | Full Ukrainian immersion |

---

## Phase B1.0: Metalanguage Bridge (M01-05)

### Purpose
Teach grammar terminology in Ukrainian so students can understand grammar explanations from M06 onwards. These modules have NO immersion limit.

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 01 | Як говорити про граматику | Parts of speech flashcards | 🎨 Self-created | Planned |
| 02 | Мова про дієслова | Aspect terminology chart | 🎨 Self-created | Planned |
| 03 | Читаємо граматичні правила | Grammar instruction patterns | 🎨 Self-created | Planned |
| 04 | Структура речення | Sentence structure diagram | 🎨 Self-created | Planned |
| 05 | Готові до занурення | Metalanguage quiz materials | 🎨 Self-created | Planned |

### External Resources (B1.0)

| Module | Resource | Type | Status |
|--------|----------|------|--------|
| M01-05 | Grammar terminology reference | 📖 Guide | Planned |

---

## Phase B1.1: Aspect Mastery (M06-15)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 06 | Aspect: The Complete System | Aspect choice flowchart | 🎨 Self-created | Planned |
| 07 | Aspect in Past: Single vs Repeated | Time marker infographic | 🎨 Self-created | Planned |
| 08 | Aspect in Past: Result vs Process | Result/process comparison | 🎨 Self-created | Planned |
| 09 | Aspect in Future | Three future forms chart | 🎨 Self-created | Planned |
| 10 | Aspect in Negation | Negation rules diagram | 🎨 Self-created | Planned |
| 11 | Aspect in Imperatives | Imperative aspect guide | 🎨 Self-created | Planned |
| 12 | Aspect Pairs: Essential 40 | Aspect pair flashcard deck | 🎨 Self-created | Planned |
| 13 | Робочий тиждень: Aspect in Action | Work scenario illustrations | 🎨 Self-created | Planned |
| 14 | Aspect Integration Practice | Mixed practice materials | 🎨 Self-created | Planned |
| 15 | Checkpoint: Aspect Mastery | Diagnostic quiz materials | 🎨 Self-created | Planned |

### External Resources (B1.1)

#### YouTube Videos

| Module | Video Title | URL | Channel | Status |
|--------|-------------|-----|---------|--------|
| M06 | Perfective and Imperfective: Verb Aspects in Ukrainian | https://www.youtube.com/watch?v=YnWlncQJg8o | Let's Learn Ukrainian | ✅ Found |
| M06 | PERFECTIVE VERBS vs IMPERFECTIVE VERBS - PART 1 | https://www.youtube.com/watch?v=v-SuEb_0WYM | Ukrainian grammar | ✅ Found |
| M07 | The Past Imperfective tense in Ukrainian # 39 | https://www.youtube.com/watch?v=PK-108GsZF4 | Ukrainian Language | ✅ Found |
| M07 | The Past Perfective tense in Ukrainian # 43 | https://www.youtube.com/watch?v=WfGlonPphFQ | Ukrainian Language | ✅ Found |
| M08 | Learn 50 important Ukrainian Verb Pairs | https://www.youtube.com/watch?v=iK4uNlozmFE | Let's Learn Ukrainian | ✅ Found |
| M09 | FUTURE TENSE IN UKRAINIAN LANGUAGE | https://www.youtube.com/watch?v=VJmihxvTLww | Speak Ukrainian | ✅ Found |
| M09 | Verb Conjugation: Future Tense #Ukrainian | https://www.youtube.com/watch?v=7oBqLYAYnw4 | Let's Learn Ukrainian | ✅ Found |
| M09 | The Future tense # 107 | https://www.youtube.com/watch?v=oXM7CrIta2E | Ukrainian Language | ✅ Found |
| M10 | Рекомендації – Asking for advice + aspect | https://www.youtube.com/watch?v=POUzGxu9OxU | Ukrainian Lessons | ✅ Found |
| M06-10 | 🇺🇦 Most Useful Ukrainian Verbs for Beginners | https://www.youtube.com/watch?v=xa-_fedNU6U | Ukrainian Language | ✅ Found |

#### Grammar Guides

| Module | Resource | URL | Status |
|--------|----------|-----|-----------|
| M06-11 | Ukrainian Lessons: Aspect | https://ukrainianlessons.com/aspect/ | ✅ Linked |
| M09 | Ukrainian Lessons: Future Tense | https://ukrainianlessons.com/grammar-future/ | ✅ Linked |
| M06-10 | Ukrainian Lessons: Verb Pairs | https://ukrainianlessons.com/verbs/ | ✅ Linked |

---

## Phase B1.2: Motion Verbs with Prefixes (M16-25)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 16 | Motion Verbs: The Full System | 14 motion pairs table | 🎨 Self-created | Planned |
| 17 | Motion: Coming & Going | при-/ви-/в- prefix diagram | 🎨 Self-created | Planned |
| 18 | Motion: Passing & Crossing | пере-/про-/об- diagram | 🎨 Self-created | Planned |
| 19 | Motion: Starting & Returning | по-/за-/роз- diagram | 🎨 Self-created | Planned |
| 20 | Motion: Approaching & Departing | під-/від-/до- diagram | 🎨 Self-created | Planned |
| 21 | Motion: Figurative Uses | Idiom illustrations | 🎨 Self-created | Planned |
| 22 | Motion: Full Prefix Integration | Complete prefix chart | 🎨 Self-created | Planned |
| 23 | Motion Patterns in Other Verbs | Prefix transfer examples | 🎨 Self-created | Planned |
| 24 | Motion: Practice & Integration | City map navigation | 🎨 Self-created | Planned |
| 25 | Checkpoint: Motion Verbs | Motion verb assessment | 🎨 Self-created | Planned |

### External Resources (B1.2)

#### YouTube Videos

| Title | URL | Channel | Status |
|-------|-----|---------|--------|
| Verbs of Motion: Unidirectional, Multidirectional \| Perfective, Imperfective \|Conjugation #Ukrainian | https://www.youtube.com/watch?v=Bs7EJFMsAJY | Let's Learn Ukrainian | ✅ Found |
| Verbs of motion: ЙТИ, ХОДИТИ vs ЇХАТИ ЇЗДИТИ | https://www.youtube.com/watch?v=BHURRyliZHo | Ukrainian grammar | ✅ Found |
| Їздити VS Їхати/ Йти VS Ходити in Ukrainian | https://www.youtube.com/watch?v=T6YwFExsRVc | Ukrainian grammar | ✅ Found |
| Let's practise the verbs of motion with me | https://www.youtube.com/watch?v=yS3MwBod5nM | Ukrainian grammar | ✅ Found |
| Practise with me the main verbs of motion in Ukrainian | https://www.youtube.com/watch?v=iFvvfEayiLE | Ukrainian grammar | ✅ Found |

#### Module-Specific Video Assignments

**When creating these modules, add these videos to the `> [!resources]` section:**

| Module | Recommended Videos | Rationale |
|--------|-------------------|-----------|
| **M16: Motion Verbs - The Full System** | • [Verbs of Motion: Unidirectional, Multidirectional](https://www.youtube.com/watch?v=Bs7EJFMsAJY)<br>• [Verbs of motion: ЙТИ, ХОДИТИ vs ЇХАТИ ЇЗДИТИ](https://www.youtube.com/watch?v=BHURRyliZHo) | Comprehensive overview of the motion verb system |
| **M17-20: Motion with Prefixes** | • [Їздити VS Їхати/ Йти VS Ходити](https://www.youtube.com/watch?v=T6YwFExsRVc) | Reinforces base pairs before adding prefixes |
| **M21-23: Practice & Integration** | • [Let's practise the verbs of motion with me](https://www.youtube.com/watch?v=yS3MwBod5nM)<br>• [Practise with me the main verbs of motion](https://www.youtube.com/watch?v=iFvvfEayiLE) | Practice-focused videos for integration modules |

#### Grammar Guides

| Module | Resource | URL | Status |
|--------|----------|-----|--------|
| M16 | Ukrainian Lessons: Motion Verbs | ukrainianlessons.com/motion-verbs/ | ✅ Linked |
| M17-20 | Ukrainian Lessons: Prefixes | ukrainianlessons.com/prefixes/ | ✅ Linked |
| M24 | Kyiv Metro Map | kyivmetro.ua | 🌐 Reference |

**Note:** B1 modules already have verified YouTube videos and Ukrainian Lessons URLs listed in the "External Resources" sections above (B1.1-B1.8). Each phase includes 3-4 verified resources per module including YouTube videos from Let's Learn Ukrainian, Speak Ukrainian, Ukrainian grammar channels, and Ukraїner for regional content.

---

## Phase B1.3: Complex Sentences (M26-40)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 26 | Relative Clauses: який Review | який declension table | 🎨 Self-created | Planned |
| 27 | Relative Clauses: де, куди, звідки | Place relative diagram | 🎨 Self-created | Planned |
| 28 | Relative Clauses: коли, що | Time/fact relative examples | 🎨 Self-created | Planned |
| 29 | Purpose: щоб + Infinitive | Purpose clause diagram | 🎨 Self-created | Planned |
| 30 | Purpose: щоб + Past Form | Subject switch diagram | 🎨 Self-created | Planned |
| 31 | Conditionals: Real (якщо) | Real conditional flowchart | 🎨 Self-created | Planned |
| 32 | Conditionals: Unreal (якби) | Unreal conditional chart | 🎨 Self-created | Planned |
| 33 | Conditionals: Mixed & Complex | Complex conditional examples | 🎨 Self-created | Planned |
| 34 | Concessive Clauses | хоча/незважаючи examples | 🎨 Self-created | Planned |
| 35 | Causal & Result Clauses | Cause/effect diagram | 🎨 Self-created | Planned |
| 36 | Temporal Clauses Deep Dive | Temporal connector chart | 🎨 Self-created | Planned |
| 37 | Complex Sentence Integration & One-Member Sentences | Sentence analysis examples | 🎨 Self-created | Planned |
| 38 | Reported Statements | Direct → indirect diagram | 🎨 Self-created | Planned |
| 39 | Reported Questions & Commands | Reporting structure chart | 🎨 Self-created | Planned |
| 40 | Checkpoint: Complex Sentences | Complex sentence assessment | 🎨 Self-created | Planned |

### External Resources (B1.3)

#### YouTube Videos

*Note: Limited Ukrainian-language grammar videos found for complex sentences. Most results were English lessons or news clips. Consider creating custom content.*

| Title | URL | Channel | Status |
|-------|-----|---------|--------|
| Якби я мала крила орлині, якби я вміла літати - Українська народна пісня | https://www.youtube.com/watch?v=4HOw1znM7Sc | Tatiana Pluhatar | ✅ Found (якби examples in folk song) |

#### Module-Specific Video Assignments

**When creating these modules, add this video to the `> [!resources]` section:**

| Module | Recommended Videos | Rationale |
|--------|-------------------|-----------|
| **M31-32: Conditionals (якщо/якби)** | • [Якби я мала крила орлині - Українська народна пісня](https://www.youtube.com/watch?v=4HOw1znM7Sc) | Folk song with multiple якби (if I had) examples for authentic conditional usage |

*Note: For M26-30 and M33-40, rely on Ukrainian Lessons grammar guides below, as no Ukrainian-language instructional videos were found.*

#### Grammar Guides

| Module | Resource | URL | Status |
|--------|----------|-----|--------|
| M26-28 | Ukrainian Lessons: Relative Clauses | ukrainianlessons.com/relative-clauses/ | ✅ Linked |
| M31-32 | Ukrainian Lessons: Conditionals | ukrainianlessons.com/conditionals/ | ✅ Linked |
| M38-39 | Ukrainian Lessons: Reported Speech | ukrainianlessons.com/reported-speech/ | ✅ Linked |

---

## Phase B1.4: Advanced Grammar (M41-50)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 41 | Adverbial Participles: Imperfective | -ючи/-ачи formation chart | 🎨 Self-created | Planned |
| 42 | Adverbial Participles: Perfective | -вши/-ши formation chart | 🎨 Self-created | Planned |
| 43 | Active Participles & Phrases | Literary excerpt with participles | 🌐 PD Literature | Planned |
| 44 | Past Passive Participles I | -ний/-тий formation table | 🎨 Self-created | Planned |
| 45 | Past Passive Participles II | -но/-то usage examples | 🎨 Self-created | Planned |
| 46 | Passive Constructions | Passive voice comparison | 🎨 Self-created | Planned |
| 47 | Diminutives: Master Class | Diminutive suffix chart | 🎨 Self-created | Planned |
| 48 | Numerals: Collectives & Fractions | Numeral forms table | 🎨 Self-created | Planned |
| 49 | Integrated Grammar Lab | Grammar integration practice | 🎨 Self-created | Planned |
| 50 | Checkpoint: Advanced Grammar | Advanced grammar assessment | 🎨 Self-created | Planned |

### External Resources (B1.4)

#### YouTube Videos

| Title | URL | Channel | Status |
|-------|-----|---------|--------|
| ULP 3-107 У барі – At the bar in Ukraine + Дієприслівник – Adverbial participle in Ukrainian | https://www.youtube.com/watch?v=S3GgY9Fa8uk | Ukrainian Lessons | ✅ Found |
| Learning Ukrainian with Odarka. Lesson 57. Adverbial Participle | https://www.youtube.com/watch?v=SRKqRpPzXnE | Learning Ukrainian with Odarka | ✅ Found |
| How to form and use passive voice in Ukrainian | https://www.youtube.com/watch?v=txDI2JzODFo | Ukrainian grammar | ✅ Found |
| Practice with me the passive voice | https://www.youtube.com/watch?v=zsSqBE-iaNM | Ukrainian grammar | ✅ Found |
| 🤯 Мене попросили, запитали, запросили!?Vocabulary + Passive Voice practice 🗣️ A2-B1 | https://www.youtube.com/watch?v=khJ6GLWoYZ4 | bazikschool | ✅ Found |

#### Module-Specific Video Assignments

**When creating these modules, add these videos to the `> [!resources]` section:**

| Module | Recommended Videos | Rationale |
|--------|-------------------|-----------|
| **M41-42: Adverbial Participles** | • [ULP 3-107 У барі + Дієприслівник](https://www.youtube.com/watch?v=S3GgY9Fa8uk)<br>• [Learning Ukrainian with Odarka. Lesson 57. Adverbial Participle](https://www.youtube.com/watch?v=SRKqRpPzXnE) | Comprehensive coverage of дієприслівник formation and usage |
| **M44-46: Passive Participles & Constructions** | • [How to form and use passive voice in Ukrainian](https://www.youtube.com/watch?v=txDI2JzODFo)<br>• [Practice with me the passive voice](https://www.youtube.com/watch?v=zsSqBE-iaNM)<br>• [Мене попросили, запитали, запросили - Passive Voice practice](https://www.youtube.com/watch?v=khJ6GLWoYZ4) | Theory + practice for passive constructions with -но/-то |

### Literary Excerpts (B1.4)

| Module | Text | Author | Purpose | Status |
|--------|------|--------|---------|--------|
| M43 | Short story excerpt | Коцюбинський | Participle examples | 🌐 PD |
| M47 | Folk tale excerpt | Traditional | Diminutive examples | 🌐 PD |

---

## Phase B1.5: Vocabulary Expansion I (M51-60)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 51 | Abstract Concepts I: Ideas | Concept map visual | 🎨 Self-created | Planned |
| 52 | Abstract Concepts II: Processes | Process vocabulary infographic | 🎨 Self-created | Planned |
| 53 | Expressing Opinions | Opinion expression scale | 🎨 Self-created | Planned |
| 54 | Agreement & Disagreement | Discussion phrases chart | 🎨 Self-created | Planned |
| 55 | Discourse Markers I | Basic connectors table | 🎨 Self-created | Planned |
| 56 | Discourse Markers II | Advanced connectors chart | 🎨 Self-created | Planned |
| 57 | Describing Changes | Trend vocabulary with graphs | 🎨 Self-created | Planned |
| 58 | Media & News | News article example | Hromadske | ❓ TBD |
| 59 | Society & Politics | Political vocabulary infographic | 🎨 Self-created | Planned |
| 60 | Checkpoint: Vocabulary I | Vocabulary assessment | 🎨 Self-created | Planned |

### External Resources (B1.5)

#### YouTube Videos

*Note: No Ukrainian-language instructional videos found for abstract vocabulary or discourse markers. Search results returned only English grammar lessons and unrelated content. This phase will rely on authentic content (news, podcasts, reading materials) rather than instructional videos.*

#### News & Media Sources

| Module | Resource | URL | Status |
|--------|----------|-----|--------|
| M58 | Hromadske News | youtube.com/@hromadske_ua | ❓ TBD |
| M58 | Liga.net | youtube.com/@liga_net | ❓ TBD |
| M59 | Верховна Рада official | rada.gov.ua | 🌐 Reference |

---

## Phase B1.6: Vocabulary Expansion II (M61-70)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 61 | Environment & Ecology | Environmental infographic | 🎨 Self-created | Planned |
| 62 | Health & Wellness | Health vocabulary visual | 🎨 Self-created | Planned |
| 63 | Emotions: Deep Dive | Emotion wheel in Ukrainian | 🎨 Self-created | Planned |
| 64 | Relationships | Relationship vocabulary map | 🎨 Self-created | Planned |
| 65 | Business Basics | Business scenario illustrations | 🎨 Self-created | Planned |
| 66 | Travel & Geography | Ukraine travel map | 🎨 Self-created | Planned |
| 67 | Synonymy I: Thinking Verbs | Thinking verb distinctions | 🎨 Self-created | Planned |
| 68 | Synonymy II: Speaking Verbs | Speaking verb chart | 🎨 Self-created | Planned |
| 69 | Collocations & Expressions | Collocation practice cards | 🎨 Self-created | Planned |
| 70 | Checkpoint: Vocabulary II | Vocabulary assessment | 🎨 Self-created | Planned |

---

## Phase B1.7: Contemporary Ukraine (M71-80)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 71 | Українські регіони: Захід | Ukraїner Western Ukraine | Ukraїner | ❓ TBD |
| 72 | Українські регіони: Схід | Ukraїner Eastern Ukraine | Ukraїner | ❓ TBD |
| 73 | Українські регіони: Південь | Ukraїner Southern Ukraine | Ukraїner | ❓ TBD |
| 74 | Українські регіони: Центр | Ukraїner Central Ukraine | Ukraїner | ❓ TBD |
| 75 | Українська музика сьогодні | Contemporary music clips | Various | ❓ TBD |
| 76 | Українське кіно та серіали | Film clips/trailers | Various | ❓ TBD |
| 77 | Технології та стартапи | Tech industry content | Various | ❓ TBD |
| 78 | Спорт в Україні | Sports highlights | Various | ❓ TBD |
| 79 | Українська кухня | Klopotenko recipe videos | Klopotenko | ❓ TBD |
| 80 | Checkpoint: Contemporary Ukraine | Cultural assessment | 🎨 Self-created | Planned |

### YouTube Channel Integration (B1.7)

| Module | Channel | Content Type | Status |
|--------|---------|--------------|--------|
| M71-74 | Ukraїner | Regional documentaries | ❓ TBD |
| M71-74 | Комікс Історик | Regional history | ❓ TBD |
| M71-74 | Реальна історія | Historical context | ❓ TBD |
| M75 | Various artists | Music videos | ❓ TBD |
| M76 | Film studios | Trailers, clips | ❓ TBD |
| M77 | Tech channels | IT industry content | ❓ TBD |
| M79 | Klopotenko | Cooking tutorials | ❓ TBD |

### Ukraїner Content Mapping

| Module | Region | Potential Videos | Notes |
|--------|--------|------------------|-------|
| M71 | Western | Lviv, Закарпаття, Буковина | Habsburg heritage, multicultural |
| M72 | Eastern | Харків, Слобожанщина | Industrial, academic heritage |
| M73 | Southern | Одеса, Херсон, Чорне море | Port cities, agriculture |
| M74 | Central | Київ, Полтава, Черкаси | Historical heart, Cossack heritage |

### External Resources (B1.7)

#### YouTube Videos - Ukraїner Channel

| Title | URL | Channel | Status |
|-------|-----|---------|--------|
| Що таке українська мова? • Ukraïner | https://www.youtube.com/watch?v=nqReOxAjuWg | Ukraїner | ✅ Found |
| Німці України. Хто вони? · Ukraїner | https://www.youtube.com/watch?v=OarTBeBi1DI | Ukraїner | ✅ Found |
| Болгари України. Хто вони? · Ukraїner | https://www.youtube.com/watch?v=Oi-t55SYdq8 | Ukraїner | ✅ Found |
| Волинь. Україна з неба · Ukraїner | https://www.youtube.com/watch?v=yE61lOcmuHs | Ukraїner | ✅ Found |
| Полтавщина. Україна з неба · Eкспедиція Ukraїner | https://www.youtube.com/watch?v=sX1xttuglKE | Ukraїner | ✅ Found |
| Україна з неба • Ukraïner | https://www.youtube.com/watch?v=vb0ZWc70gOk | Ukraїner | ✅ Found |
| Чим для вас є Україна? • Ukraïner | https://www.youtube.com/watch?v=x75Me7dLRj4 | Ukraїner | ✅ Found |
| Сіверськодонецьк — це Україна. Хоробрі міста • Ukraїner | https://www.youtube.com/watch?v=exyLdpF8JZA | Ukraїner | ✅ Found |
| Віталій Портников: «Розвивати українське, а не боротися з російським» • Ukraїner Q | https://www.youtube.com/watch?v=cslHRvAe3oA | Ukraїner Q | ✅ Found |

#### Module-Specific Video Assignments

**When creating these modules, add these videos to the `> [!resources]` section:**

| Module | Recommended Videos | Rationale |
|--------|-------------------|-----------|
| **M71: Українські регіони - Захід** | • [Волинь. Україна з неба](https://www.youtube.com/watch?v=yE61lOcmuHs)<br>• [Німці України. Хто вони?](https://www.youtube.com/watch?v=OarTBeBi1DI) | Western Ukraine regional content, multicultural heritage |
| **M72: Українські регіони - Схід** | • [Сіверськодонецьк — це Україна. Хоробрі міста](https://www.youtube.com/watch?v=exyLdpF8JZA) | Eastern Ukraine, resilience during war |
| **M73: Українські регіони - Південь** | • [Болгари України. Хто вони?](https://www.youtube.com/watch?v=Oi-t55SYdq8) | Southern Ukraine, ethnic diversity |
| **M74: Українські регіони - Центр** | • [Полтавщина. Україна з неба](https://www.youtube.com/watch?v=sX1xttuglKE) | Central Ukraine, Cossack heritage |
| **M75-76: Сучасна Україна** | • [Що таке українська мова?](https://www.youtube.com/watch?v=nqReOxAjuWg)<br>• [Чим для вас є Україна?](https://www.youtube.com/watch?v=x75Me7dLRj4)<br>• [Віталій Портников: «Розвивати українське»](https://www.youtube.com/watch?v=cslHRvAe3oA) | Contemporary Ukrainian identity, language, culture |
| **M77-79: Культура і суспільство** | • [Україна з неба](https://www.youtube.com/watch?v=vb0ZWc70gOk) | Overview of Ukraine's diversity and beauty |

---

## Phase B1.8: Skills & Integration (M81-85)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 81 | Новини: як читати | Authentic news articles | Various | ❓ TBD |
| 82 | Інтерв'ю та подкасти | Podcast excerpts | Various | ❓ TBD |
| 83 | B1 Grammar Integration | Grammar review materials | 🎨 Self-created | Planned |
| 84 | B1 Vocabulary Integration | Vocabulary review materials | 🎨 Self-created | Planned |
| 85 | B1 Capstone | Final assessment materials | 🎨 Self-created | Planned |

### Podcast Integration (B1.8)

| Module | Podcast | Content Type | Status |
|--------|---------|--------------|--------|
| M82 | Ukrainian Lessons Podcast | Learning content | ✅ Linked |
| M82 | Радіо Хартія (Zhadan) | Cultural/literary | ❓ TBD |
| M81-82 | Hromadske interviews | News/current affairs | ❓ TBD |

### News Sources (B1.8)

| Module | Source | Type | Status |
|--------|--------|------|--------|
| M81 | Hromadske | Video news | ❓ TBD |
| M81 | Liga.net | Political news | ❓ TBD |
| M81 | Ukraїner | Documentary | ❓ TBD |

---

## Pop Culture References

### Film References

| Module | Film/Series | Context | Status |
|--------|-------------|---------|--------|
| M76 | Тіні забутих предків (1965) | Classic Ukrainian cinema | 🌐 PD |
| M76 | Кіборги (2017) | Contemporary war drama | ❓ TBD |
| M76 | Слуга народу | Political comedy series | ❓ TBD |

### Music References

| Module | Artist/Song | Context | Status |
|--------|-------------|---------|--------|
| M75 | Eurovision winners | Contemporary pop | 🌐 Reference |
| M75 | Океан Ельзи | Rock music culture | 🌐 Reference |
| M75 | DakhaBrakha | Folk/world music | 🌐 Reference |
| M75 | Kalush Orchestra | Eurovision 2022 | 🌐 Reference |

### Literature References

| Module | Work | Author | Status |
|--------|------|--------|--------|
| M43 | Short stories | Коцюбинський | 🌐 PD |
| M47 | Folk tales | Traditional | 🌐 PD |
| M74 | Poetry excerpts | Шевченко | 🌐 PD |

---

## Language & History Content

### Історія мови Channel Integration

| Module | Topic | Potential Video | Status |
|--------|-------|-----------------|--------|
| M71 | Western dialects | Галицьке наріччя | ❓ TBD |
| M72 | Eastern dialects | Слобожанське наріччя | ❓ TBD |
| M74 | Language standardization | Історія літературної мови | ❓ TBD |

**Note:** Історія мови (youtube.com/@Istoria-Movy) is marked as "PURE GOLD" for B1-C1 content on Ukrainian language development and dialectology.

This document assigns media content to B1 modules.

**📚 See also:** [MEDIA-SOURCES.md](./MEDIA-SOURCES.md) for complete channel list, permission tracking, and licensing information.

---

## Ukrainian Lessons Resources

### Full Module Mapping

| Module | Resource | Topic |
|--------|----------|-------|
| M01-06 | Grammar: Aspect | Aspect selection and usage |
| M07 | Verbs | Aspect pairs list |
| M11-15 | Motion Verbs | Motion verb system |
| M21-23 | Grammar | Relative clauses |
| M24-25 | Grammar | Purpose clauses |
| M26-27 | Grammar | Conditional mood |
| M33-34 | Grammar | Reported speech |
| M36-37 | Grammar | Participles |
| M77 | Podcast | Listening practice |

---

## Self-Created Content Requirements

### Grammar Aids

| Type | Modules | Description |
|------|---------|-------------|
| Aspect flowcharts | M01-10 | Decision trees for aspect selection |
| Prefix diagrams | M11-20 | Visual prefix meaning system |
| Clause charts | M21-35 | Complex sentence structure guides |
| Participle tables | M36-41 | Formation and usage charts |

### Cultural Content

| Type | Modules | Description |
|------|---------|-------------|
| Regional maps | M66-69 | Ukraine regions with characteristics |
| Cultural infographics | M70-74 | Contemporary Ukraine topics |
| Assessment materials | Checkpoints | Diagnostic and review quizzes |

---

## Phase-by-Phase Summary

### B1.1-2 (M01-20): Grammar Foundation

| Media Type | Usage |
|------------|-------|
| Self-created | Grammar charts, diagrams, flowcharts |
| External | Ukrainian Lessons grammar references |
| Pop culture | Minimal (grammar focus) |

### B1.3-4 (M21-45): Complex Grammar

| Media Type | Usage |
|------------|-------|
| Self-created | Complex sentence guides, participle tables |
| Literary | PD excerpts (Коцюбинський, folk tales) |
| External | Ukrainian Lessons advanced grammar |

### B1.5-6 (M46-65): Vocabulary Expansion

| Media Type | Usage |
|------------|-------|
| Self-created | Vocabulary infographics, concept maps |
| News | Hromadske, Liga.net for media vocabulary |
| External | Authentic texts for reading practice |

### B1.7-8 (M66-80): Contemporary Ukraine

| Media Type | Usage |
|------------|-------|
| Ukraїner | Regional documentaries |
| Klopotenko | Cooking content |
| Music/Film | Contemporary Ukrainian culture |
| News/Podcasts | Listening comprehension practice |
| Історія мови | Language history content |

---

## Notes

1. **Immersion Progression**: Media shifts from pedagogical to authentic across B1
2. **Regional Focus**: M66-69 heavily rely on Ukraїner documentaries
3. **Cultural Integration**: M70-74 introduce contemporary Ukrainian culture
4. **Skills Focus**: M76-80 emphasize authentic media comprehension
5. **Self-Created Preference**: Grammar modules primarily use self-created content
6. **Permission Status**: Most video content requires permission outreach

---

## Related Documents

- `docs/l2-uk-en/MEDIA-SOURCES.md` - Source tracking
- `docs/l2-uk-en/B1-CURRICULUM-PLAN.md` - Module specifications
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Quality standards
- `docs/l2-uk-en/A2-MEDIA-ASSIGNMENT.md` - Previous level reference
