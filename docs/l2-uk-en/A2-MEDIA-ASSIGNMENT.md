# A2 Media Content Assignment

**Status:** Updated
**Created:** 2025-12-14
**Updated:** 2025-12-16
**Modules:** 57

This document assigns media content requirements to all 57 A2 modules.

**📚 See also:** [MEDIA-SOURCES.md](./MEDIA-SOURCES.md) for complete channel list, permission tracking, and licensing information.

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

## ⚠️ IMPORTANT: URL Verification Required

**The URLs in the "External Resources by Module" section are PATTERNS, not verified links.**

Before embedding resources into modules, you MUST:
1. Search for actual content on the topic
2. Verify the URL exists and is relevant
3. Use the verified resource sites below

See **Issue #170** for the standardization task.

---

## 📋 Standard Format for Module Resources

Every module MUST have a "Need More Practice?" section **before `## Activities`**.

**Location in module:**
```
## Summary
...

---

## Need More Practice?    <-- HERE

> [!resources] External Resources
> ...

---

## Activities
```

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

**Live example:** [A1 Module 10](https://krisztiankoos.github.io/learn-ukrainian/docs/a1/module-10#need-more-practice)

**Icon conventions:**
| Icon | Type |
|------|------|
| 🎧 | Audio/Alphabet guides |
| 🎙️ | Podcast episodes |
| 📖 | Grammar guides |
| 🔊 | Pronunciation tools |
| 📝 | Vocabulary lists |

---

### Verified Resource Sites

| Site | Best For | Example Verified URLs |
|------|----------|----------------------|
| **ukrainianlessons.com** | Podcasts, grammar | `/intro-cases/`, `/perfective-verbs/`, `/episode51/`, `/prepositions-cases/` |
| **ukrainiancourse.com** | Grammar tables | `/grammar-tables/nouns-in-the-dative-case/`, `/grammar-tables/adjectives-in-the-dative-case/` |
| **talkukrainian.com** | Cases, adjectives | `/grammatical-cases/`, `/adjectives-degrees-comparison/` |
| **ukrainianlanguage.org.uk** | Academic lessons | `/read/unit08/page8-4.htm` (aspect), `/read/unit09/page9-5.htm` (comparison) |
| **speakua.com** | Blog articles | `/blog/perfective-and-imperfective-verbs` |
| **opentext.ku.edu/dobraforma** | University textbook | `/chapter/26-1-introduction-to-verbal-aspect-prefixed-perfective-verbs/` |
| **aspect.in.ua** | Verb aspect | Homepage has aspect pair lookup |

### YouTube Channels

| Channel | Handle | Best For |
|---------|--------|----------|
| **Ukrainian Lessons** | `@UkrainianLessons` | Podcast companion, structured grammar |
| **Let's Learn Ukrainian** | `@LetsLearnUkrainian` | Grammar deep dives, case explanations |
| **Ukrainian Language** | `@LearnUkrainianLanguage` | Beginner lessons, verb tenses |
| **Speak Ukrainian** | `@speakukrainian` | Cases, comprehensive lessons |
| **Olga Reznikova** | `@OlgaReznikova` | 233K subs, wide variety |
| **Ukrainian Learner** | — | Worksheets, case practice |
| **Easy Ukrainian** | `@EasyUkrainian` | Street interviews with subtitles |

### Finding YouTube Videos with yt-dlp

Use `yt-dlp` CLI to search YouTube and get real URLs:

```bash
# Search for 5 videos on a topic
yt-dlp "ytsearch5:Ukrainian dative case lesson" --print "%(title)s | %(channel)s | %(webpage_url)s" --skip-download

# Examples:
yt-dlp "ytsearch5:Ukrainian instrumental case" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian verb aspect perfective" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian comparatives adjectives" --print "%(webpage_url)s" --skip-download
```

**Verified videos found:**

| Topic | Video | Channel | URL |
|-------|-------|---------|-----|
| Dative | All about Dative Case | Let's Learn Ukrainian | youtube.com/watch?v=Cm0Ay7NEOlw |
| Dative | Dative case in Ukrainian | Speak Ukrainian | youtube.com/watch?v=ATeU7iwuyLU |
| Instrumental | All About Instrumental Case | Let's Learn Ukrainian | youtube.com/watch?v=7q87c9T2QeA |
| Instrumental | Instrumental case | Speak Ukrainian | youtube.com/watch?v=lmPHpt2DGos |
| Aspect | Perfective and Imperfective | Let's Learn Ukrainian | youtube.com/watch?v=YnWlncQJg8o |
| Aspect | 50 Verb Pairs | Let's Learn Ukrainian | youtube.com/watch?v=iK4uNlozmFE |

### How to Search (Web)

```bash
# Google site search examples:
site:ukrainianlessons.com dative case
site:talkukrainian.com instrumental
site:ukrainiancourse.com grammar tables
```

---

## Permission Status Legend

| Status | Symbol | Meaning |
|--------|--------|---------|
| Pending | ⏳ | Permission request sent, awaiting response |
| Approved | ✅ | Permission granted |
| Linked | ✅ | External resource linked |
| Public Domain | 🌐 | No permission needed |
| Creative Commons | 🔓 | Free to use with attribution |
| Self-Created | 🎨 | Created by curriculum team |
| TBD | ❓ | Not yet assigned |

---

## Media Strategy Overview

### A2 Media Principles

1. **Continuation from A1**: Maintain familiar hooks (S.T.A.L.K.E.R., Witcher references)
2. **External Resources**: Ukrainian Lessons remains primary partner
3. **Reduced Pop Culture**: Shift toward real-world practical scenarios
4. **Food & Culture Focus**: Klopotenko for cuisine vocabulary
5. **Transliteration**: First-occurrence only in vocabulary tables
6. **Practical Scenarios**: Post office, doctor, shopping, restaurant

### Content Types by Phase

| Phase | Modules | Primary Media | Immersion |
|-------|---------|--------------|-----------|
| A2.1 Cases | M01-11 | Case charts, Ukrainian Lessons | 40-45% |
| A2.2 Aspect | M12-16 | Aspect diagrams, verb pair tables | 45-50% |
| A2.3 Comparison | M17-24 | Shopping scenarios, comparison charts | 45-50% |
| A2.4 Complex Sentences | M25-34 | Story texts, conjunctions charts | 50% |
| A2.5 Word Formation | M35-43 | Prefix/suffix diagrams, root trees | 50-55% |
| A2.6 Vocabulary | M44-55 | Thematic photos, real-world scenarios | 55% |
| A2.7 Review | M56-57 | Comprehensive review materials | 55% |

---

## YouTube Channel Assignments

### Primary Resource Partner

| Channel | URL | Modules | Content Type |
|---------|-----|---------|--------------|
| Ukrainian Lessons | youtube.com/@ukrainianlessons | All A2 | Grammar, vocabulary |

### Cultural & Thematic Channels

| Channel | URL | Modules | Content Type | Status |
|---------|-----|---------|--------------|--------|
| Євген Клопотенко | youtube.com/@klopotenko | M44 Food | Ukrainian cuisine | ❓ TBD |
| Ukraїner | youtube.com/@ukrainernet | M46 Nature | Regional culture | ❓ TBD |

---

## External Resources by Module (⚠️ PATTERNS - VERIFY BEFORE USE)

### Topic → Resource Mapping

Use this table to identify WHAT to search for, then find the actual URL.

| Module | Topic | Resource Type | Search Terms |
|--------|-------|--------------|-------------|
| M01 | Dative Pronouns | Grammar Guide | `Ukrainian dative case pronouns` |
| M02 | Dative Nouns | Grammar Chart | `Ukrainian dative nouns endings` |
| M03 | Dative Verbs | Verbs Guide | `Ukrainian verbs dative case` |
| M04 | Instrumental | Grammar Guide | `Ukrainian instrumental case` |
| M05 | Tools/Transport | Vocabulary | `Ukrainian transport vocabulary` |
| M06 | Professions | Grammar | `Ukrainian professions instrumental` |
| M07 | Prepositions | Grammar | `Ukrainian prepositions cases` ✅ ukrainianlessons.com/prepositions-cases/ |
| M08 | Logical Prep | Grammar | `Ukrainian prepositions meaning` |
| M09 | All Cases | 7 Cases Chart | `Ukrainian cases overview` ✅ ukrainianlessons.com/intro-cases/ |
| M10 | Post Office | Podcast FMU | `Ukrainian post office vocabulary` |
| M11 | Cases Review | Review | `Ukrainian 7 cases review` |
| M12 | Aspect Intro | Grammar | `Ukrainian verb aspect` ✅ ukrainianlessons.com/verb-aspect-in-ukrainian-differences/ |
| M13 | Past Aspect | Grammar | `Ukrainian past tense aspect` |
| M14 | Future Aspect | Grammar | `Ukrainian future tense` ✅ ukrainianlessons.com/ukrainian-tenses/ |
| M15 | Aspect Pairs | Grammar | `Ukrainian perfective imperfective pairs` ✅ ukrainianlessons.com/perfective-verbs/ |
| M16 | Aspect Mastery | Grammar | `Ukrainian aspect practice` |
| M17 | свій Possessive | Grammar | `Ukrainian свій possessive` |
| M18 | Comparison | Grammar | `Ukrainian comparative adjectives` ✅ talkukrainian.com/adjectives-degrees-comparison/ |
| M19 | Superlatives | Grammar | `Ukrainian superlatives най-` |
| M20 | Preferences | Vocabulary | `Ukrainian preferences vocabulary` |
| M21 | Numerals | Grammar | `Ukrainian numbers nouns` ✅ ukrainianlessons.com/nouns-after-numbers/ |
| M22 | Conditional | Grammar | `Ukrainian conditional mood якби` |
| M23 | Shopping | Podcast FMU | `Ukrainian shopping dialogue` |
| M24 | A2.3 Checkpoint | Review | `Ukrainian A2 grammar review` |
| M25 | Past Narration | Grammar | `Ukrainian storytelling past tense` |
| M26 | Causal | Grammar | `Ukrainian conjunctions бо тому що` ✅ ukrainianlessons.com/ukrainian-conjunctions-guide/ |
| M27 | Reported Speech | Grammar | `Ukrainian reported speech` |
| M28 | Opinion Clauses | Grammar | `Ukrainian що clauses думати` |
| M29 | Emotion Clauses | Grammar | `Ukrainian emotion expressions` |
| M30 | Purpose Clauses | Grammar | `Ukrainian щоб purpose` |
| M31 | Relative Clauses | Grammar | `Ukrainian який relative pronouns` |
| M32 | Time Clauses | Grammar | `Ukrainian коли поки temporal` |
| M33 | Doctor Visit | Podcast FMU | `Ukrainian doctor vocabulary` ✅ ukrainianlessons.com/something-hurts/ |
| M34 | A2.4 Checkpoint | Review | `Ukrainian complex sentences review` |
| M35 | Motion Prefixes | Grammar | `Ukrainian verb prefixes motion` ✅ ukrainianlessons.com/ukrainian-verb-prefixes/ |
| M36 | Advanced Motion | Grammar | `Ukrainian motion verbs йти їхати` |
| M37 | Action Prefixes | Grammar | `Ukrainian verb prefixes meaning` |
| M38 | Noun Suffixes | Word Formation | `Ukrainian noun suffixes -ість -ння` |
| M39 | Adj Suffixes | Word Formation | `Ukrainian adjective suffixes` |
| M40 | Root Families | Word Formation | `Ukrainian word families roots` |
| M41 | Root Families II | Word Formation | `Ukrainian word formation patterns` |
| M42 | WF Mastery | Word Formation | `Ukrainian word formation` |
| M43 | WF Checkpoint | Review | `Ukrainian word formation review` |
| M44 | Food Vocabulary | Vocabulary | `Ukrainian food vocabulary` |
| M45 | Home Vocabulary | Vocabulary | `Ukrainian home furniture vocabulary` |
| M46 | Nature | Vocabulary | `Ukrainian nature weather vocabulary` |
| M47 | Emotions | Vocabulary | `Ukrainian emotions personality` |
| M48 | Work | Vocabulary | `Ukrainian professions work vocabulary` |
| M49 | Technology | Vocabulary | `Ukrainian technology vocabulary` |
| M50 | Hobbies | Vocabulary | `Ukrainian hobbies leisure vocabulary` |
| M51 | Education | Vocabulary | `Ukrainian education school vocabulary` |
| M52 | Shopping | Vocabulary | `Ukrainian shopping services vocabulary` |
| M53 | Sports | Vocabulary | `Ukrainian sports fitness vocabulary` |
| M54 | Health | Vocabulary | `Ukrainian health body vocabulary` |
| M55 | Vocab Checkpoint | Review | `Ukrainian A2 vocabulary review` |
| M56 | Grammar Review | Review | `Ukrainian A2 grammar comprehensive` |
| M57 | Final Review | Review | `Ukrainian A2 skills review` |

---

## Verified Resources by Module (3-4 per module)

### A2.1: Cases (M01-11)

**M01: Dative I — Pronouns**
- 🎥 [All About Dative Case](https://www.youtube.com/watch?v=Cm0Ay7NEOlw) — Let's Learn Ukrainian
- 📖 [Ukrainian Personal Pronouns](https://www.ukrainianlessons.com/ukrainian-personal-pronouns/)
- 📝 [Dative Case Grammar](https://www.ukrainiancourse.com/grammar-tables/nouns-in-the-dative-case/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

**M02: Dative II — Nouns**
- 🎥 [Dative Case Practice](https://www.youtube.com/watch?v=Cm0Ay7NEOlw) — Let's Learn Ukrainian
- 📖 [Nouns in Dative Case](https://www.ukrainiancourse.com/grammar-tables/nouns-in-the-dative-case/)
- 📝 [Dative Case Guide](https://www.ukrainianlessons.com/intro-cases/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

**M03: Dative Verbs**
- 🎥 [Dative Case Usage](https://www.youtube.com/watch?v=Cm0Ay7NEOlw) — Let's Learn Ukrainian
- 📖 [Ukrainian Verbs](https://www.ukrainianlessons.com/verbs/)
- 📝 [Dative with Verbs](https://www.ukrainianlessons.com/intro-cases/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

**M04: Instrumental I**
- 🎥 [Instrumental Case Explained](https://www.youtube.com/watch?v=lmPHpt2DGos) — Speak Ukrainian
- 📖 [Instrumental Case Guide](https://www.talkukrainian.com/instrumental-case/)
- 📝 [Instrumental Usage](https://www.speakua.com/blog/instrumental-case-ukrainian)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

**M05: Instrumental II — Tools & Transport**
- 🎥 [Instrumental with Examples](https://www.youtube.com/watch?v=lmPHpt2DGos) — Speak Ukrainian
- 📖 [Transport Vocabulary](https://www.ukrainianlessons.com/vocabulary/)
- 📝 [Instrumental Case](https://www.ukrainiancourse.com/grammar-tables/nouns-in-the-instrumental-case/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

**M06: Being and Becoming — Professions**
- 🎥 [Instrumental Case](https://www.youtube.com/watch?v=lmPHpt2DGos) — Speak Ukrainian
- 📖 [Professions Vocabulary](https://www.ukrainianlessons.com/vocabulary/)
- 📝 [Instrumental with Professions](https://www.ukrainianlanguage.org.uk/read/unit07/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

**M07: Preposition Master**
- 🎥 [Prepositions Guide](https://www.youtube.com/@SpeakUkrainian) — Speak Ukrainian
- 📖 [Prepositions with Cases](https://www.ukrainianlessons.com/prepositions-cases/)
- 📝 [Cases Overview](https://www.ukrainianlessons.com/intro-cases/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

**M08-11: Logical Prepositions, All Cases, Post Office, Checkpoint**
- 🎥 [All 7 Cases](https://www.youtube.com/@LetsLearnUkrainian) — Let's Learn Ukrainian
- 📖 [Cases Introduction](https://www.ukrainianlessons.com/intro-cases/)
- 📝 [Cases Chart](https://www.ukrainianlessons.com/ukrainian-cases-chart/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

### A2.2: Aspect (M12-16)

**M12: Aspect Introduction**
- 🎥 [Perfective vs Imperfective](https://www.youtube.com/watch?v=YnWlncQJg8o) — Let's Learn Ukrainian
- 📖 [Verb Aspect Guide](https://www.ukrainianlessons.com/verb-aspect-in-ukrainian-differences/)
- 📝 [Aspect Overview](https://www.ukrainianlessons.com/perfective-verbs/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

**M13-16: Past Aspect, Future Aspect, Aspect Pairs, Mastery**
- 🎥 [50 Verb Pairs](https://www.youtube.com/watch?v=iK4uNlozmFE) — Let's Learn Ukrainian
- 📖 [Perfective Verbs](https://www.ukrainianlessons.com/perfective-verbs/)
- 📝 [Aspect Differences](https://www.ukrainianlessons.com/verb-aspect-in-ukrainian-differences/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

### A2.3: Comparison & Conditional (M17-24)

**M17-19: Possessive свій, Comparatives, Superlatives**
- 🎥 [Comparative Adjectives](https://www.youtube.com/@LetsLearnUkrainian) — Let's Learn Ukrainian
- 📖 [Degrees of Comparison](https://www.talkukrainian.com/adjectives-degrees-comparison/)
- 📝 [Adjectives Guide](https://www.ukrainianlessons.com/vocabulary-adjectives/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

**M20-24: Preferences, Numerals, Conditional, Shopping, Checkpoint**
- 🎥 [Numbers with Nouns](https://www.youtube.com/@LetsLearnUkrainian) — Let's Learn Ukrainian
- 📖 [Nouns After Numbers](https://www.ukrainianlessons.com/nouns-after-numbers/)
- 📝 [Numbers Guide](https://www.ukrainianlessons.com/numbers/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

### A2.4: Complex Sentences (M25-34)

**M25-32: Narration, Conjunctions, Clauses**
- 🎥 [Complex Sentences](https://www.youtube.com/@LetsLearnUkrainian) — Let's Learn Ukrainian
- 📖 [Conjunctions Guide](https://www.ukrainianlessons.com/ukrainian-conjunctions-guide/)
- 📝 [Complex Sentences](https://www.ukrainianlessons.com/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

**M33: At the Doctor's**
- 🎥 [Health Vocabulary](https://www.youtube.com/@SpeakUkrainian) — Speak Ukrainian
- 📖 [Something Hurts](https://www.ukrainianlessons.com/something-hurts/)
- 📝 [Body Vocabulary](https://www.ukrainianlessons.com/vocabulary-body/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

### A2.5: Word Formation (M35-43)

**M35-37: Motion & Action Prefixes**
- 🎥 [Verb Prefixes](https://www.youtube.com/@LetsLearnUkrainian) — Let's Learn Ukrainian
- 📖 [Ukrainian Verb Prefixes](https://www.ukrainianlessons.com/ukrainian-verb-prefixes/)
- 📝 [Motion Verbs](https://www.ukrainianlessons.com/verbs/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

**M38-43: Suffixes, Roots, Word Formation**
- 🎥 [Word Formation](https://www.youtube.com/@LetsLearnUkrainian) — Let's Learn Ukrainian
- 📖 [Vocabulary Building](https://www.ukrainianlessons.com/vocabulary/)
- 📝 [Grammar Guide](https://www.ukrainianlessons.com/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

### A2.6: Vocabulary Expansion (M44-55)

**M44: Food & Cooking**
- 🎥 [Food Vocabulary](https://www.youtube.com/@SpeakUkrainian) — Speak Ukrainian
- 📖 [Ukrainian Food](https://www.ukrainianlessons.com/ukrainian-food/)
- 📝 [Cooking Vocabulary](https://www.ukrainianlessons.com/vocabulary/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

**M45-55: Thematic Vocabulary & Checkpoint**
- 🎥 [Vocabulary Lessons](https://www.youtube.com/@SpeakUkrainian) — Speak Ukrainian
- 📖 [Vocabulary Guide](https://www.ukrainianlessons.com/vocabulary/)
- 📝 [Thematic Lists](https://www.ukrainianlessons.com/)
- 🎙️ [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/podcast/)

### A2.7: Final Review (M56-57)

**M56-57: Grammar & Final Review**
- 🎥 [A2 Complete](https://www.youtube.com/@LetsLearnUkrainian) — Let's Learn Ukrainian
- 📖 [Ukrainian Resources](https://www.ukrainianlessons.com/ukrainian-language-resources/)
- 📝 [Grammar Overview](https://www.ukrainianlessons.com/)
- 🎙️ [Top Episodes](https://www.ukrainianlessons.com/episodes-for-ukrainian-language-beginners/)

---

## Other External Resources

| Module | Source | Resource | Status |
|--------|--------|----------|--------|
| All | Forvo | Pronunciation | ✅ Linked |
| M44 | Klopotenko | Cooking videos | ❓ TBD |

---

## Pop Culture References (Reduced from A1)

### S.T.A.L.K.E.R. (Continuation)

| Module | Context | Grammar Connection | Status |
|--------|---------|-------------------|--------|
| M05 | Transport in the Zone | Instrumental (їхати автобусом) | 🌐 Reference |
| M07 | Zone navigation | Preposition + case practice | 🌐 Reference |
| M35 | "Я виходжу зі Зони" | Motion prefixes (ви-, в-) | 🌐 Reference |

### The Witcher (Continuation)

| Module | Context | Grammar Connection | Status |
|--------|---------|-------------------|--------|
| M06 | "Він став відьмаком" | Instrumental with стати | 🌐 Reference |
| M18 | "Сильніший монстр" | Comparison forms | 🌐 Reference |

### Metro Series (New for A2)

| Module | Context | Grammar Connection | Status |
|--------|---------|-------------------|--------|
| M05 | "Я їду метро" | Instrumental transport | 🌐 Reference |
| M12 | "Він виживав" vs "Він вижив" | Aspect introduction | 🌐 Reference |

---

## Thematic Media Assignments

### Phase A2.1: Cases (M01-11)

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 01 | Dative I — Pronouns | Pronoun chart | 🎨 Self-created | ❓ TBD |
| 02 | Dative II — Nouns | Ending chart | 🎨 Self-created | ❓ TBD |
| 03 | Dative Verbs | Verb list diagram | 🎨 Self-created | ❓ TBD |
| 04 | Instrumental I | з + Instrumental chart | 🎨 Self-created | ❓ TBD |
| 05 | Instrumental II | Transport/tool illustrations | Pexels | 🔓 CC |
| 06 | Being and Becoming | Profession photos | Unsplash | 🔓 CC |
| 07 | Preposition Master | Full preposition table | 🎨 Self-created | ❓ TBD |
| 08 | Logical Prepositions | Abstract concept diagram | 🎨 Self-created | ❓ TBD |
| 09 | All Cases Practice | 7-case summary chart | 🎨 Self-created | ❓ TBD |
| 10 | Post Office & Bank | Service vocabulary | 🎨 Self-created | ❓ TBD |
| 11 | Checkpoint: Cases | Assessment materials | 🎨 Self-created | ❓ TBD |

### Phase A2.2: Aspect (M12-16)

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 12 | Aspect Introduction | Aspect timeline diagram | 🎨 Self-created | ❓ TBD |
| 13 | The Completed Past | Process vs result diagram | 🎨 Self-created | ❓ TBD |
| 14 | Future Plans | Future forms comparison | 🎨 Self-created | ❓ TBD |
| 15 | Aspect Pairs Deep Dive | Pair vocabulary table | 🎨 Self-created | ❓ TBD |
| 16 | Aspect Mastery | Comprehensive aspect chart | 🎨 Self-created | ❓ TBD |

### Phase A2.3: Comparison & Conditional (M17-24)

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 17 | Possessive свій | свій vs його/її diagram | 🎨 Self-created | ❓ TBD |
| 18 | Bigger, Better, Stronger | Comparative forms chart | 🎨 Self-created | ❓ TBD |
| 19 | The Best, The Worst | Superlative forms chart | 🎨 Self-created | ❓ TBD |
| 20 | Preferences & Choices | Preference expressions | 🎨 Self-created | ❓ TBD |
| 21 | Numerals & Nouns | Number + case chart | 🎨 Self-created | ❓ TBD |
| 22 | If I Were... | Conditional diagram | 🎨 Self-created | ❓ TBD |
| 23 | Smart Shopping | Shopping scenario photos | Pexels | 🔓 CC |
| 24 | Checkpoint | Assessment materials | 🎨 Self-created | ❓ TBD |

### Phase A2.4: Complex Sentences (M25-34)

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 25 | Telling Stories | Narrative structure diagram | 🎨 Self-created | ❓ TBD |
| 26 | Because and Although | Causal conjunction chart | 🎨 Self-created | ❓ TBD |
| 27 | She Said That... | Reported speech diagram | 🎨 Self-created | ❓ TBD |
| 28 | I Think That... | Opinion clause examples | 🎨 Self-created | ❓ TBD |
| 29 | I Feel Like... | Emotion expressions chart | 🎨 Self-created | ❓ TBD |
| 30 | In Order To... | Purpose clause diagram | 🎨 Self-created | ❓ TBD |
| 31 | Which One? | Relative pronoun chart | 🎨 Self-created | ❓ TBD |
| 32 | When & While | Temporal conjunction diagram | 🎨 Self-created | ❓ TBD |
| 33 | At the Doctor's | Medical dialogue audio | 🎨 Recording needed | ❓ TBD |
| 34 | Checkpoint 3 | Assessment materials | 🎨 Self-created | ❓ TBD |

### Phase A2.5: Word Formation (M35-43)

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 35 | Motion Verb Prefixes | Prefix meaning chart (в-, ви-, за-) | 🎨 Self-created | ❓ TBD |
| 36 | Advanced Motion Prefixes | Extended prefix chart | 🎨 Self-created | ❓ TBD |
| 37 | Action Verb Prefixes | Non-motion prefix chart | 🎨 Self-created | ❓ TBD |
| 38 | Noun Suffixes | Suffix tree diagram | 🎨 Self-created | ❓ TBD |
| 39 | Adjective Suffixes | Adj suffix patterns | 🎨 Self-created | ❓ TBD |
| 40 | Root Families I | Root tree visualization | 🎨 Self-created | ❓ TBD |
| 41 | Root Families II | Extended root trees | 🎨 Self-created | ❓ TBD |
| 42 | Word Formation Mastery | Comprehensive WF chart | 🎨 Self-created | ❓ TBD |
| 43 | Checkpoint: Word Formation | Assessment materials | 🎨 Self-created | ❓ TBD |

### Phase A2.6: Vocabulary Expansion (M44-55)

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 44 | Food & Cooking | Klopotenko recipes | Klopotenko | ❓ TBD |
| 45 | Home & Furniture | Home illustrations | Pexels | 🔓 CC |
| 46 | Nature & Weather | Nature photos | Unsplash | 🔓 CC |
| 47 | Emotions & Personality | Emotion illustrations | 🎨 Self-created | ❓ TBD |
| 48 | Work & Professions | Workplace photos | Pexels | 🔓 CC |
| 49 | Technology & Media | Tech illustrations | Pexels | 🔓 CC |
| 50 | Hobbies & Leisure | Activity photos | Pexels | 🔓 CC |
| 51 | Education & Learning | University photos | Pexels | 🔓 CC |
| 52 | Shopping & Services | Store photos | Pexels | 🔓 CC |
| 53 | Sports & Fitness | Sports photos | Unsplash | 🔓 CC |
| 54 | Health & Body | Body diagram | 🎨 Self-created | ❓ TBD |
| 55 | Checkpoint: Vocabulary | Assessment materials | 🎨 Self-created | ❓ TBD |

### Phase A2.7: Review & Mastery (M56-57)

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 56 | A2 Grammar Review | Comprehensive grammar charts | 🎨 Self-created | ❓ TBD |
| 57 | A2 Final Review | All skills review materials | 🎨 Self-created | ❓ TBD |

---

## Audio Content Needs

### Dialogue Recordings (Priority)

| Type | Modules | Duration | Priority |
|------|---------|----------|----------|
| Post office scenario | M10 | 2-3 min | HIGH |
| Doctor visit | M33 | 3-4 min | HIGH |
| Shopping dialogue | M23, M52 | 2-3 min | HIGH |
| Restaurant ordering | M44 | 2-3 min | MEDIUM |
| Job interview | M48 | 3-4 min | MEDIUM |

---

## Music References

### Folk Songs (Continued from A1)

| Song | Module | Grammar Connection | Status |
|------|--------|-------------------|--------|
| Ой, у гаю при Дунаю | M04 | Instrumental (з друзями) | 🌐 PD |
| Їхав козак за Дунай | M35 | Motion verb prefixes | 🌐 PD |

---

## Self-Created Content Summary

### Grammar Diagrams Needed

| Diagram | Modules | Priority |
|---------|---------|----------|
| 7-Case Summary | M09, M11 | HIGH |
| Dative Endings | M01-03 | HIGH |
| Instrumental Endings | M04-06 | HIGH |
| Preposition + Case Table | M07-08 | HIGH |
| Aspect Timeline | M12-16 | HIGH |
| Motion Prefix Chart | M35-36 | HIGH |
| Word Formation Trees | M38-42 | HIGH |
| Conjunction Overview | M26-32 | MEDIUM |

---

## Quality Standards

### Image Requirements
- Minimum resolution: 800x600 pixels
- Format: PNG or JPG
- Alt text required for accessibility

### Audio Requirements
- Format: MP3, 128kbps minimum
- Native speaker recordings
- Clear pronunciation
- Duration: 30 seconds - 3 minutes per clip

### External Link Requirements
- All links verified working
- Ukrainian Lessons primary resource
- Links to free content only
- Educational purpose only

---

## Phase Summary

### A2.1 (M01-11): Cases
- **Pop Culture**: S.T.A.L.K.E.R. (2 refs), Witcher (1 ref)
- **External Resources**: Ukrainian Lessons (11 links)
- **Self-Created**: Case charts, ending tables
- **Audio**: Post office dialogue

### A2.2 (M12-16): Aspect
- **Pop Culture**: Metro (1 ref)
- **External Resources**: Ukrainian Lessons (5 links)
- **Self-Created**: Aspect diagrams, verb pair tables

### A2.3 (M17-24): Comparison & Conditional
- **Pop Culture**: Witcher (1 ref)
- **External Resources**: Ukrainian Lessons (8 links)
- **Real-World**: Shopping scenarios
- **Audio**: Shopping dialogue

### A2.4 (M25-34): Complex Sentences
- **External Resources**: Ukrainian Lessons (10 links)
- **Self-Created**: Conjunction charts, clause diagrams
- **Audio**: Doctor visit dialogue

### A2.5 (M35-43): Word Formation
- **Pop Culture**: S.T.A.L.K.E.R. (1 ref)
- **External Resources**: Ukrainian Lessons (9 links)
- **Self-Created**: Prefix/suffix charts, root trees

### A2.6 (M44-55): Vocabulary Expansion
- **External Resources**: Ukrainian Lessons (12 links), Klopotenko (1 module)
- **Photos**: Pexels, Unsplash (CC licensed)
- **Real-World**: Thematic scenarios

### A2.7 (M56-57): Review
- **External Resources**: Ukrainian Lessons (2 links)
- **Self-Created**: Comprehensive review charts

---

## Notes

1. **Reduced Pop Culture**: A2 shifts focus from games to practical scenarios
2. **Klopotenko Integration**: Food vocabulary module uses his content
3. **Audio Priority**: Service dialogues (post office, doctor, shopping) are critical
4. **Word Formation**: New phase with extensive diagram needs
5. **Transliteration**: First-occurrence only in vocabulary tables
6. **External Resources**: Ukrainian Lessons remains primary, verify all URLs before embedding

---

## Related Documents

- `docs/l2-uk-en/MEDIA-SOURCES.md` - Source tracking
- `docs/l2-uk-en/A2-CURRICULUM-PLAN.md` - Module specifications
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Quality standards
- `docs/l2-uk-en/A1-MEDIA-ASSIGNMENT.md` - A1 reference (predecessor)
