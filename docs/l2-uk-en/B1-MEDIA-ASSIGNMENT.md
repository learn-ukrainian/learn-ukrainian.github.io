# B1 Media Content Assignment

**Status:** Needs External Resources Added
**Created:** 2024-12-14
**Updated:** 2025-12-16
**Modules:** 80 (5 created, 75 planned)

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

**Current state:** 0/80 B1 modules have `> [!resources]` sections.

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

| Phase | Immersion Target | Media Approach |
|-------|------------------|----------------|
| B1.1-2 | 45-55% | English explanations, Ukrainian examples/media |
| B1.3-4 | 55-60% | Mixed explanations, more Ukrainian media |
| B1.5-6 | 60-65% | Ukrainian media dominant, English support |
| B1.7-8 | 65-70% | Full Ukrainian immersion in media |

---

## Phase B1.1: Aspect Mastery (M01-10)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 01 | Aspect: The Complete System | Aspect choice flowchart | 🎨 Self-created | Planned |
| 02 | Aspect in Past: Single vs Repeated | Time marker infographic | 🎨 Self-created | Planned |
| 03 | Aspect in Past: Result vs Process | Result/process comparison | 🎨 Self-created | Planned |
| 04 | Aspect in Future | Three future forms chart | 🎨 Self-created | Planned |
| 05 | Aspect in Negation | Negation rules diagram | 🎨 Self-created | Planned |
| 06 | Aspect in Imperatives | Imperative aspect guide | 🎨 Self-created | Planned |
| 07 | Aspect Pairs: Essential 40 | Aspect pair flashcard deck | 🎨 Self-created | Planned |
| 08 | Робочий тиждень: Aspect in Action | Work scenario illustrations | 🎨 Self-created | Planned |
| 09 | Aspect Integration Practice | Mixed practice materials | 🎨 Self-created | Planned |
| 10 | Checkpoint: Aspect Mastery | Diagnostic quiz materials | 🎨 Self-created | Planned |

### External Resources (B1.1)

#### YouTube Videos

| Module | Video Title | URL | Channel | Status |
|--------|-------------|-----|---------|--------|
| M01 | Perfective and Imperfective: Verb Aspects in Ukrainian | https://www.youtube.com/watch?v=YnWlncQJg8o | Let's Learn Ukrainian | ✅ Found |
| M01 | PERFECTIVE VERBS vs IMPERFECTIVE VERBS - PART 1 | https://www.youtube.com/watch?v=v-SuEb_0WYM | Ukrainian grammar | ✅ Found |
| M02 | The Past Imperfective tense in Ukrainian # 39 | https://www.youtube.com/watch?v=PK-108GsZF4 | Ukrainian Language | ✅ Found |
| M02 | The Past Perfective tense in Ukrainian # 43 | https://www.youtube.com/watch?v=WfGlonPphFQ | Ukrainian Language | ✅ Found |
| M03 | Learn 50 important Ukrainian Verb Pairs | https://www.youtube.com/watch?v=iK4uNlozmFE | Let's Learn Ukrainian | ✅ Found |
| M04 | FUTURE TENSE IN UKRAINIAN LANGUAGE | https://www.youtube.com/watch?v=VJmihxvTLww | Speak Ukrainian | ✅ Found |
| M04 | Verb Conjugation: Future Tense #Ukrainian | https://www.youtube.com/watch?v=7oBqLYAYnw4 | Let's Learn Ukrainian | ✅ Found |
| M04 | The Future tense # 107 | https://www.youtube.com/watch?v=oXM7CrIta2E | Ukrainian Language | ✅ Found |
| M05 | Рекомендації – Asking for advice + aspect | https://www.youtube.com/watch?v=POUzGxu9OxU | Ukrainian Lessons | ✅ Found |
| M01-05 | 🇺🇦 Most Useful Ukrainian Verbs for Beginners | https://www.youtube.com/watch?v=xa-_fedNU6U | Ukrainian Language | ✅ Found |

#### Grammar Guides

| Module | Resource | URL | Status |
|--------|----------|-----|-----------|
| M01-06 | Ukrainian Lessons: Aspect | https://ukrainianlessons.com/aspect/ | ✅ Linked |
| M04 | Ukrainian Lessons: Future Tense | https://ukrainianlessons.com/grammar-future/ | ✅ Linked |
| M01-05 | Ukrainian Lessons: Verb Pairs | https://ukrainianlessons.com/verbs/ | ✅ Linked |

---

## Phase B1.2: Motion Verbs with Prefixes (M11-20)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 11 | Motion Verbs: The Full System | 14 motion pairs table | 🎨 Self-created | Planned |
| 12 | Motion: Coming & Going | при-/ви-/в- prefix diagram | 🎨 Self-created | Planned |
| 13 | Motion: Passing & Crossing | пере-/про-/об- diagram | 🎨 Self-created | Planned |
| 14 | Motion: Starting & Returning | по-/за-/роз- diagram | 🎨 Self-created | Planned |
| 15 | Motion: Approaching & Departing | під-/від-/до- diagram | 🎨 Self-created | Planned |
| 16 | Motion: Figurative Uses | Idiom illustrations | 🎨 Self-created | Planned |
| 17 | Motion: Full Prefix Integration | Complete prefix chart | 🎨 Self-created | Planned |
| 18 | Motion Patterns in Other Verbs | Prefix transfer examples | 🎨 Self-created | Planned |
| 19 | Motion: Practice & Integration | City map navigation | 🎨 Self-created | Planned |
| 20 | Checkpoint: Motion Verbs | Motion verb assessment | 🎨 Self-created | Planned |

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
| **M11: Motion Verbs - The Full System** | • [Verbs of Motion: Unidirectional, Multidirectional](https://www.youtube.com/watch?v=Bs7EJFMsAJY)<br>• [Verbs of motion: ЙТИ, ХОДИТИ vs ЇХАТИ ЇЗДИТИ](https://www.youtube.com/watch?v=BHURRyliZHo) | Comprehensive overview of the motion verb system |
| **M12-15: Motion with Prefixes** | • [Їздити VS Їхати/ Йти VS Ходити](https://www.youtube.com/watch?v=T6YwFExsRVc) | Reinforces base pairs before adding prefixes |
| **M16-18: Practice & Integration** | • [Let's practise the verbs of motion with me](https://www.youtube.com/watch?v=yS3MwBod5nM)<br>• [Practise with me the main verbs of motion](https://www.youtube.com/watch?v=iFvvfEayiLE) | Practice-focused videos for integration modules |

#### Grammar Guides

| Module | Resource | URL | Status |
|--------|----------|-----|--------|\n| M11 | Ukrainian Lessons: Motion Verbs | ukrainianlessons.com/motion-verbs/ | ✅ Linked |
| M12-15 | Ukrainian Lessons: Prefixes | ukrainianlessons.com/prefixes/ | ✅ Linked |
| M19 | Kyiv Metro Map | kyivmetro.ua | 🌐 Reference |

---

## Phase B1.3: Complex Sentences (M21-35)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 21 | Relative Clauses: який Review | який declension table | 🎨 Self-created | Planned |
| 22 | Relative Clauses: де, куди, звідки | Place relative diagram | 🎨 Self-created | Planned |
| 23 | Relative Clauses: коли, що | Time/fact relative examples | 🎨 Self-created | Planned |
| 24 | Purpose: щоб + Infinitive | Purpose clause diagram | 🎨 Self-created | Planned |
| 25 | Purpose: щоб + Past Form | Subject switch diagram | 🎨 Self-created | Planned |
| 26 | Conditionals: Real (якщо) | Real conditional flowchart | 🎨 Self-created | Planned |
| 27 | Conditionals: Unreal (якби) | Unreal conditional chart | 🎨 Self-created | Planned |
| 28 | Conditionals: Mixed & Complex | Complex conditional examples | 🎨 Self-created | Planned |
| 29 | Concessive Clauses | хоча/незважаючи examples | 🎨 Self-created | Planned |
| 30 | Causal & Result Clauses | Cause/effect diagram | 🎨 Self-created | Planned |
| 31 | Temporal Clauses Deep Dive | Temporal connector chart | 🎨 Self-created | Planned |
| 32 | Complex Sentence Integration & One-Member Sentences | Sentence analysis examples | 🎨 Self-created | Planned |
| 33 | Reported Statements | Direct → indirect diagram | 🎨 Self-created | Planned |
| 34 | Reported Questions & Commands | Reporting structure chart | 🎨 Self-created | Planned |
| 35 | Checkpoint: Complex Sentences | Complex sentence assessment | 🎨 Self-created | Planned |

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
| **M26-27: Conditionals (якщо/якби)** | • [Якби я мала крила орлині - Українська народна пісня](https://www.youtube.com/watch?v=4HOw1znM7Sc) | Folk song with multiple якби (if I had) examples for authentic conditional usage |

*Note: For M21-25 and M28-35, rely on Ukrainian Lessons grammar guides below, as no Ukrainian-language instructional videos were found.*

#### Grammar Guides

| Module | Resource | URL | Status |
|--------|----------|-----|--------|
| M21-23 | Ukrainian Lessons: Relative Clauses | ukrainianlessons.com/relative-clauses/ | ✅ Linked |
| M26-27 | Ukrainian Lessons: Conditionals | ukrainianlessons.com/conditionals/ | ✅ Linked |
| M33-34 | Ukrainian Lessons: Reported Speech | ukrainianlessons.com/reported-speech/ | ✅ Linked |

---

## Phase B1.4: Advanced Grammar (M36-45)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 36 | Adverbial Participles: Imperfective | -ючи/-ачи formation chart | 🎨 Self-created | Planned |
| 37 | Adverbial Participles: Perfective | -вши/-ши formation chart | 🎨 Self-created | Planned |
| 38 | Active Participles & Phrases | Literary excerpt with participles | 🌐 PD Literature | Planned |
| 39 | Past Passive Participles I | -ний/-тий formation table | 🎨 Self-created | Planned |
| 40 | Past Passive Participles II | -но/-то usage examples | 🎨 Self-created | Planned |
| 41 | Passive Constructions | Passive voice comparison | 🎨 Self-created | Planned |
| 42 | Diminutives: Master Class | Diminutive suffix chart | 🎨 Self-created | Planned |
| 43 | Numerals: Collectives & Fractions | Numeral forms table | 🎨 Self-created | Planned |
| 44 | Integrated Grammar Lab | Grammar integration practice | 🎨 Self-created | Planned |
| 45 | Checkpoint: Advanced Grammar | Advanced grammar assessment | 🎨 Self-created | Planned |

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
| **M36-37: Adverbial Participles** | • [ULP 3-107 У барі + Дієприслівник](https://www.youtube.com/watch?v=S3GgY9Fa8uk)<br>• [Learning Ukrainian with Odarka. Lesson 57. Adverbial Participle](https://www.youtube.com/watch?v=SRKqRpPzXnE) | Comprehensive coverage of дієприслівник formation and usage |
| **M39-41: Passive Participles & Constructions** | • [How to form and use passive voice in Ukrainian](https://www.youtube.com/watch?v=txDI2JzODFo)<br>• [Practice with me the passive voice](https://www.youtube.com/watch?v=zsSqBE-iaNM)<br>• [Мене попросили, запитали, запросили - Passive Voice practice](https://www.youtube.com/watch?v=khJ6GLWoYZ4) | Theory + practice for passive constructions with -но/-то |

### Literary Excerpts (B1.4)

| Module | Text | Author | Purpose | Status |
|--------|------|--------|---------|--------|
| M38 | Short story excerpt | Коцюбинський | Participle examples | 🌐 PD |
| M43 | Folk tale excerpt | Traditional | Diminutive examples | 🌐 PD |

---

## Phase B1.5: Vocabulary Expansion I (M46-55)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 46 | Abstract Concepts I: Ideas | Concept map visual | 🎨 Self-created | Planned |
| 47 | Abstract Concepts II: Processes | Process vocabulary infographic | 🎨 Self-created | Planned |
| 48 | Expressing Opinions | Opinion expression scale | 🎨 Self-created | Planned |
| 49 | Agreement & Disagreement | Discussion phrases chart | 🎨 Self-created | Planned |
| 50 | Discourse Markers I | Basic connectors table | 🎨 Self-created | Planned |
| 51 | Discourse Markers II | Advanced connectors chart | 🎨 Self-created | Planned |
| 52 | Describing Changes | Trend vocabulary with graphs | 🎨 Self-created | Planned |
| 53 | Media & News | News article example | Hromadske | ❓ TBD |
| 54 | Society & Politics | Political vocabulary infographic | 🎨 Self-created | Planned |
| 55 | Checkpoint: Vocabulary I | Vocabulary assessment | 🎨 Self-created | Planned |

### External Resources (B1.5)

#### YouTube Videos

*Note: No Ukrainian-language instructional videos found for abstract vocabulary or discourse markers. Search results returned only English grammar lessons and unrelated content. This phase will rely on authentic content (news, podcasts, reading materials) rather than instructional videos.*

#### News & Media Sources

| Module | Resource | URL | Status |
|--------|----------|-----|--------|
| M53 | Hromadske News | youtube.com/@hromadske_ua | ❓ TBD |
| M53 | Liga.net | youtube.com/@liga_net | ❓ TBD |
| M54 | Верховна Рада official | rada.gov.ua | 🌐 Reference |

---

## Phase B1.6: Vocabulary Expansion II (M56-65)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 56 | Environment & Ecology | Environmental infographic | 🎨 Self-created | Planned |
| 57 | Health & Wellness | Health vocabulary visual | 🎨 Self-created | Planned |
| 58 | Emotions: Deep Dive | Emotion wheel in Ukrainian | 🎨 Self-created | Planned |
| 59 | Relationships | Relationship vocabulary map | 🎨 Self-created | Planned |
| 60 | Business Basics | Business scenario illustrations | 🎨 Self-created | Planned |
| 61 | Travel & Geography | Ukraine travel map | 🎨 Self-created | Planned |
| 62 | Synonymy I: Thinking Verbs | Thinking verb distinctions | 🎨 Self-created | Planned |
| 63 | Synonymy II: Speaking Verbs | Speaking verb chart | 🎨 Self-created | Planned |
| 64 | Collocations & Expressions | Collocation practice cards | 🎨 Self-created | Planned |
| 65 | Checkpoint: Vocabulary II | Vocabulary assessment | 🎨 Self-created | Planned |

---

## Phase B1.7: Contemporary Ukraine (M66-75)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 66 | Українські регіони: Захід | Ukraїner Western Ukraine | Ukraїner | ❓ TBD |
| 67 | Українські регіони: Схід | Ukraїner Eastern Ukraine | Ukraїner | ❓ TBD |
| 68 | Українські регіони: Південь | Ukraїner Southern Ukraine | Ukraїner | ❓ TBD |
| 69 | Українські регіони: Центр | Ukraїner Central Ukraine | Ukraїner | ❓ TBD |
| 70 | Українська музика сьогодні | Contemporary music clips | Various | ❓ TBD |
| 71 | Українське кіно та серіали | Film clips/trailers | Various | ❓ TBD |
| 72 | Технології та стартапи | Tech industry content | Various | ❓ TBD |
| 73 | Спорт в Україні | Sports highlights | Various | ❓ TBD |
| 74 | Українська кухня | Klopotenko recipe videos | Klopotenko | ❓ TBD |
| 75 | Checkpoint: Contemporary Ukraine | Cultural assessment | 🎨 Self-created | Planned |

### YouTube Channel Integration (B1.7)

| Module | Channel | Content Type | Status |
|--------|---------|--------------|--------|
| M66-69 | Ukraїner | Regional documentaries | ❓ TBD |
| M66-69 | Комікс Історик | Regional history | ❓ TBD |
| M66-69 | Реальна історія | Historical context | ❓ TBD |
| M70 | Various artists | Music videos | ❓ TBD |
| M71 | Film studios | Trailers, clips | ❓ TBD |
| M72 | Tech channels | IT industry content | ❓ TBD |
| M74 | Klopotenko | Cooking tutorials | ❓ TBD |

### Ukraїner Content Mapping

| Module | Region | Potential Videos | Notes |
|--------|--------|------------------|-------|
| M66 | Western | Lviv, Закарпаття, Буковина | Habsburg heritage, multicultural |
| M67 | Eastern | Харків, Слобожанщина | Industrial, academic heritage |
| M68 | Southern | Одеса, Херсон, Чорне море | Port cities, agriculture |
| M69 | Central | Київ, Полтава, Черкаси | Historical heart, Cossack heritage |

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
| **M66: Українські регіони - Захід** | • [Волинь. Україна з неба](https://www.youtube.com/watch?v=yE61lOcmuHs)<br>• [Німці України. Хто вони?](https://www.youtube.com/watch?v=OarTBeBi1DI) | Western Ukraine regional content, multicultural heritage |
| **M67: Українські регіони - Схід** | • [Сіверськодонецьк — це Україна. Хоробрі міста](https://www.youtube.com/watch?v=exyLdpF8JZA) | Eastern Ukraine, resilience during war |
| **M68: Українські регіони - Південь** | • [Болгари України. Хто вони?](https://www.youtube.com/watch?v=Oi-t55SYdq8) | Southern Ukraine, ethnic diversity |
| **M69: Українські регіони - Центр** | • [Полтавщина. Україна з неба](https://www.youtube.com/watch?v=sX1xttuglKE) | Central Ukraine, Cossack heritage |
| **M70-71: Сучасна Україна** | • [Що таке українська мова?](https://www.youtube.com/watch?v=nqReOxAjuWg)<br>• [Чим для вас є Україна?](https://www.youtube.com/watch?v=x75Me7dLRj4)<br>• [Віталій Портников: «Розвивати українське»](https://www.youtube.com/watch?v=cslHRvAe3oA) | Contemporary Ukrainian identity, language, culture |
| **M72-74: Культура і суспільство** | • [Україна з неба](https://www.youtube.com/watch?v=vb0ZWc70gOk) | Overview of Ukraine's diversity and beauty |

---

## Phase B1.8: Skills & Integration (M76-80)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 76 | Новини: як читати | Authentic news articles | Various | ❓ TBD |
| 77 | Інтерв'ю та подкасти | Podcast excerpts | Various | ❓ TBD |
| 78 | B1 Grammar Integration | Grammar review materials | 🎨 Self-created | Planned |
| 79 | B1 Vocabulary Integration | Vocabulary review materials | 🎨 Self-created | Planned |
| 80 | B1 Capstone | Final assessment materials | 🎨 Self-created | Planned |

### Podcast Integration (B1.8)

| Module | Podcast | Content Type | Status |
|--------|---------|--------------|--------|
| M77 | Ukrainian Lessons Podcast | Learning content | ✅ Linked |
| M77 | Радіо Хартія (Zhadan) | Cultural/literary | ❓ TBD |
| M76-77 | Hromadske interviews | News/current affairs | ❓ TBD |

### News Sources (B1.8)

| Module | Source | Type | Status |
|--------|--------|------|--------|
| M76 | Hromadske | Video news | ❓ TBD |
| M76 | Liga.net | Political news | ❓ TBD |
| M76 | Ukraїner | Documentary | ❓ TBD |

---

## Pop Culture References

### Film References

| Module | Film/Series | Context | Status |
|--------|-------------|---------|--------|
| M71 | Тіні забутих предків (1965) | Classic Ukrainian cinema | 🌐 PD |
| M71 | Кіборги (2017) | Contemporary war drama | ❓ TBD |
| M71 | Слуга народу | Political comedy series | ❓ TBD |

### Music References

| Module | Artist/Song | Context | Status |
|--------|-------------|---------|--------|
| M70 | Eurovision winners | Contemporary pop | 🌐 Reference |
| M70 | Океан Ельзи | Rock music culture | 🌐 Reference |
| M70 | DakhaBrakha | Folk/world music | 🌐 Reference |
| M70 | Kalush Orchestra | Eurovision 2022 | 🌐 Reference |

### Literature References

| Module | Work | Author | Status |
|--------|------|--------|--------|
| M38 | Short stories | Коцюбинський | 🌐 PD |
| M43 | Folk tales | Traditional | 🌐 PD |
| M69 | Poetry excerpts | Шевченко | 🌐 PD |

---

## Language & History Content

### Історія мови Channel Integration

| Module | Topic | Potential Video | Status |
|--------|-------|-----------------|--------|
| M66 | Western dialects | Галицьке наріччя | ❓ TBD |
| M67 | Eastern dialects | Слобожанське наріччя | ❓ TBD |
| M69 | Language standardization | Історія літературної мови | ❓ TBD |

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
