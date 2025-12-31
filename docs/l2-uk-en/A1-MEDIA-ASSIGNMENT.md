# A1 Media Content Assignment

**Status:** Needs External Resources Added
**Created:** 2025-12-14
**Updated:** 2025-12-16
**Modules:** 34

This document assigns media content to A1 modules.

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

## ⚠️ IMPORTANT: External Resources Not Yet Added

**Current state:** 1/34 A1 modules have `> [!resources]` sections.

Pop culture references are documented below, but actual external URLs need to be found and embedded.

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

### Verified Resource Sites

| Site | Best For | Example URLs |
|------|----------|--------------|
| **ukrainianlessons.com** | Grammar, alphabet | `/ukrainian-alphabet/`, `/intro-cases/`, `/prepositions-cases/` |
| **ukrainiancourse.com** | Grammar tables | `/grammar-tables/`, `/free-ukrainian-courses/` |
| **talkukrainian.com** | Cases, vocabulary | `/grammatical-cases/`, `/ukrainian-alphabet/` |
| **ukrainianlanguage.org.uk** | Academic lessons | `/read/unit01/` through `/read/unit10/` |

### YouTube Channels

| Channel | Handle | Best For |
|---------|--------|----------|
| **Ukrainian Lessons** | `@UkrainianLessons` | Structured grammar, podcast companion |
| **Let's Learn Ukrainian** | `@LetsLearnUkrainian` | Grammar deep dives, case explanations |
| **Ukrainian Language** | `@LearnUkrainianLanguage` | Beginner lessons |
| **Speak Ukrainian** | `@speakukrainian` | Cases, comprehensive lessons |
| **Olga Reznikova** | `@OlgaReznikova` | Wide variety (233K subs) |

### Finding YouTube Videos with yt-dlp

```bash
# Install
brew install yt-dlp

# Search for A1 topics
yt-dlp "ytsearch5:Ukrainian alphabet Cyrillic lesson" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian nominative case" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian accusative case" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian genitive case" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian locative case" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian verb conjugation beginners" --print "%(webpage_url)s" --skip-download
```

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

## Media Strategy Overview

### A1 Media Principles

1. **Pop Culture Hooks**: Use familiar games/media to engage learners
2. **External Resources**: Link to quality free resources (Ukrainian Lessons)
3. **Real-World Context**: Ground grammar in practical scenarios
4. **Cultural Immersion**: Introduce Ukrainian songs, traditions, food
5. **Transliteration Support**: Full transliteration in M01-10, phased out by M21+

### Content Types Used

| Type | Description | Primary Source |
|------|-------------|----------------|
| **Pop Culture** | Games, movies, TV references | S.T.A.L.K.E.R., Witcher, Harry Potter |
| **Music** | Folk songs, popular songs | Traditional, "Червона рута" |
| **External Links** | Learning resources | ukrainianlessons.com |
| **Real-World** | Cities, metro, food, shopping | Kyiv, Lviv descriptions |
| **Cultural** | Holidays, traditions, family | Ukrainian customs |

---

## Pop Culture References by Module

### S.T.A.L.K.E.R. (GSC Game World, Kyiv)

| Module | Context | Grammar Connection | Status |
|--------|---------|-------------------|--------|
| M01 | Cyrillic decoding (сталкер) | False friends recognition | 🌐 Reference |
| M03 | Location names (Прип'ять, місто, будинок) | Noun gender endings | 🌐 Reference |
| M09 | Тушонка (canned food) scavenging | Food vocabulary | 🌐 Reference |
| M10 | Food items (ковбаса, хліб, консерви) | Checkpoint review | 🌐 Reference |
| M11 | "Я бачу аномалію!" | Accusative case (-а → -у) | 🌐 Reference |
| M13 | "Я в Зоні", "на складі" | Locative case | 🌐 Reference |
| M15 | Chornobyl Exclusion Zone navigation | City/directions vocab | 🌐 Reference |
| M17 | Counting artifacts (три артефакти) | Numbers with nouns | 🌐 Reference |
| M18 | "Я хочу консерви та хліб!" | Shopping vocabulary | 🌐 Reference |

### The Witcher (Netflix Ukrainian Dub)

| Module | Context | Grammar Connection | Status |
|--------|---------|-------------------|--------|
| M02 | "Відьмак" — soft sign usage | Ь softening Д | 🌐 Reference |
| M05 | "Цей меч", "Та книга" | Demonstrative agreement | 🌐 Reference |
| M08 | "Я хочу їсти" | Irregular verb хотіти + їсти | 🌐 Reference |
| M12 | "Я шукаю когось" | Animate accusative | 🌐 Reference |

### Harry Potter (Ukrainian Dub)

| Module | Context | Grammar Connection | Status |
|--------|---------|-------------------|--------|
| M08 | "Я хочу їсти" (Ron) | Two irregular verbs together | 🌐 Reference |

### Ukrainian Cinema

| Module | Film | Context | Status |
|--------|------|---------|--------|
| M27 | Тіні забутих предків (1965) | Colors in storytelling | 🌐 PD |

---

## Music References by Module

### Traditional Folk Songs

| Module | Song | Context | Status |
|--------|------|---------|--------|
| M06 | "Гуляла дівчина бережком" | Class I verbs in folk songs | 🌐 PD |
| M14 | Коломийки (folk songs) | Possessives "моя мила", "наша Україна" | 🌐 PD |
| M28 | "Пісня козака" | Adverbs "вранці рано" | 🌐 PD |
| M29 | "Ой у лузі червона калина" | Nature vocabulary | 🌐 PD |
| M29 | "Місяць на небі" | Nature vocabulary | 🌐 PD |

### Popular Songs

| Module | Song | Context | Status |
|--------|------|---------|--------|
| M21 | "Червона рута" | Past tense "Я знайшов її колись..." | 🌐 Reference |
| M22 | "Все буде добре" | Future tense anthem | 🌐 Reference |

---

## External Resources by Module

### Ukrainian Lessons (ukrainianlessons.com)

| Module | Resource Type | Topic | URL Pattern |
|--------|--------------|-------|-------------|
| M01 | YouTube | Ukrainian Alphabet | ukrainianlessons.com/ukrainian-alphabet/ |
| M02 | YouTube Channel | Beginner videos | youtube.com/@ukrainianlessons |
| M02 | Podcast | Season 1 for beginners | ukrainianlessons.com/thepodcast/ |
| M03 | Grammar Guide | Noun Genders | ukrainianlessons.com/noun-genders-in-ukrainian/ |
| M03 | Video | How to Know Noun Gender | ukrainianlessons.com/video-noun-gender/ |
| M04 | Pronouns | Personal Pronouns | ukrainianlessons.com/personal-pronouns/ |
| M04 | Podcast | ULP 1-03 Introductions | ukrainianlessons.com/episode3/ |
| M05 | Grammar | ЦЕЙ and ТОЙ | ukrainianlessons.com/pronouns-this-that/ |
| M06 | Grammar Chart | Verb Tenses | ukrainianlessons.com/ukrainian-tenses/ |
| M06 | Podcast | ULP 1-22 First Conjugation | ukrainianlessons.com/episode22/ |
| M07 | Question Words | Питальні слова | ukrainianlessons.com/question-words/ |
| M07 | Negation | Double Negation | ukrainianlessons.com/negation-in-ukrainian/ |
| M08 | Podcast | ULP 1-24 Second Conjugation | ukrainianlessons.com/episode24/ |
| M09 | Food Guide | 40+ Ukrainian Dishes | ukrainianlessons.com/ukrainian-food/ |
| M09 | Podcast | ULP 1-12 Ordering Food | ukrainianlessons.com/episode12/ |
| M10 | Alphabet Review | All 33 letters | ukrainianlessons.com/ukrainian-alphabet/ |
| M10 | Podcast | Top 10 for Beginners | ukrainianlessons.com/episodes-for-ukrainian-language-beginners/ |
| M11 | Grammar Guide | Accusative Case | ukrainianlessons.com/accusativecase/ |
| M11 | Cases Overview | Introduction to Cases | ukrainianlessons.com/intro-cases/ |
| M12 | Pronouns | Personal Pronouns Declension | ukrainianlessons.com/ukrainian-personal-pronouns/ |
| M13 | Podcast | ULP 2-66 Locative | ukrainianlessons.com/episode66/ |
| M14 | Grammar Guide | Possessive Pronouns | ukrainianlessons.com/grammar-possessive-pronouns/ |
| M15 | Vocabulary | Around Town | ukrainianlessons.com/vocabulary-town/ |
| M15 | Directions | Navigation Vocab | ukrainianlessons.com/vocabulary-directions/ |
| M16 | Grammar Guide | 10 Uses of Genitive | ukrainianlessons.com/genitive-case/ |
| M17 | Numbers | Numbers in Ukrainian | ukrainianlessons.com/numbers/ |
| M18 | Shopping | FMU 1-18 | ukrainianlessons.com/fmu18/ |
| M19 | Podcast | FMU 1-11 Order Coffee | ukrainianlessons.com/fmu11/ |
| M20 | Cases Chart | All 7 Cases | ukrainianlessons.com/ukrainian-cases-chart/ |
| M21 | Grammar Guide | Past Tense | ukrainianlessons.com/grammar-past-tense/ |
| M22 | Grammar Guide | Future Tense | ukrainianlessons.com/grammar-future/ |
| M23 | Time | Котра година? | ukrainianlessons.com/grammar-time/ |
| M24 | Verbs | 500+ Ukrainian Verbs | ukrainianlessons.com/verbs/ |
| M26 | Adjectives | Common Adjectives | ukrainianlessons.com/vocabulary-adjectives/ |
| M27 | Colors | Colors in Ukrainian | ukrainianlessons.com/vocabulary-colors/ |
| M28 | Grammar | Adjectives and Adverbs | ukrainianlessons.com/adjectives-and-adverbs/ |
| M29 | Weather | Яка погода? | ukrainianlessons.com/weather-vocabulary/ |
| M30 | Prepositions | Location vs Destination | ukrainianlessons.com/location-destination-prepositions/ |
| M31 | Body Parts | Body Vocabulary | ukrainianlessons.com/vocabulary-body/ |
| M32 | Family | Сім'я | ukrainianlessons.com/vocabulary-family/ |
| M33 | Holidays | Greetings for Every Occasion | ukrainianlessons.com/greetings/ |
| M34 | Hub | 100 Links for Learning | ukrainianlessons.com/ukrainian-language-resources/ |

### Other External Resources

| Module | Source | Resource | Status |
|--------|--------|----------|--------|
| M01 | Talk Ukrainian | Alphabet with Audio | talkukrainian.com/ukrainian-alphabet/ |
| M01 | Forvo | Ukrainian Dictionary | forvo.com/languages/uk/ |

---

## Real-World Context by Module

### Kyiv Metro System

| Module | Content | Status |
|--------|---------|--------|
| M15 | Three metro lines (Red M1, Blue M2, Green M3) | 🎨 Self-created |
| M15 | Gendered announcements (female = toward center) | 🎨 Self-created |
| M15 | Deepest stations (100+ meters underground) | 🎨 Self-created |
| M20 | Arsenalna escalator (5 minutes, deepest in world) | 🎨 Self-created |

### Ukrainian Cities

| Module | City | Content | Status |
|--------|------|---------|--------|
| M01 | Kyiv | Metro stations, street signs, shops | 🎨 Self-created |
| M10 | Kyiv | Capital description, metro, parks, cafes | 🎨 Self-created |
| M15 | Lviv | UNESCO historic center, narrow streets | 🎨 Self-created |
| M15 | Kyiv, Kharkiv, Dnipro | Only cities with metro | 🎨 Self-created |

### Ukrainian Currency

| Module | Content | Status |
|--------|---------|--------|
| M17 | Hryvnia (гривня) system | 🎨 Self-created |
| M20 | Ticket prices (8 hryvnias) | 🎨 Self-created |

---

## Cultural Content by Module

### Food & Cuisine

| Module | Content | Status |
|--------|---------|--------|
| M09 | Ukrainian food categories (vegetables, fruits, meat, dairy) | 🎨 Self-created |
| M09 | Тушонка (canned meat) - Soviet-era staple | 🎨 Self-created |
| M10 | Вареники, ковбаса, хліб | 🎨 Self-created |
| M18 | Market shopping, магазин vocabulary | 🎨 Self-created |
| M19 | Café culture, coffee ordering | 🎨 Self-created |

### Holidays & Traditions

| Module | Content | Status |
|--------|---------|--------|
| M33 | Різдво (Christmas) - January 7 | 🎨 Self-created |
| M33 | Великдень (Easter) traditions | 🎨 Self-created |
| M33 | День Незалежності (Independence Day) - August 24 | 🎨 Self-created |
| M33 | Birthday traditions (Многая літа!) | 🎨 Self-created |

### Family & Social

| Module | Content | Status |
|--------|---------|--------|
| M32 | Ukrainian family structure | 🎨 Self-created |
| M14 | Possessives in folk culture ("наша Україна") | 🎨 Self-created |

---

## Phase-by-Phase Summary

### A1.1 (M01-10): First Contact

| Media Type | Usage |
|------------|-------|
| Pop Culture | S.T.A.L.K.E.R. (4 refs), Witcher (3 refs), Harry Potter (1 ref) |
| External Resources | Ukrainian Lessons (10+ links) |
| Real-World | Kyiv, metro, basic locations |
| Music | Folk songs introduction |

### A1.2 (M11-20): Navigation

| Media Type | Usage |
|------------|-------|
| Pop Culture | S.T.A.L.K.E.R. (4 refs), Witcher (1 ref) |
| External Resources | Ukrainian Lessons (15+ links) |
| Real-World | Kyiv metro detail, Lviv, shopping, café |
| Cultural | Food, shopping customs |

### A1.3 (M21-34): Daily Life

| Media Type | Usage |
|------------|-------|
| Pop Culture | Ukrainian cinema (Тіні забутих предків) |
| Music | Червона рута, Все буде добре, folk songs |
| External Resources | Ukrainian Lessons (20+ links) |
| Real-World | Time, weather, family, holidays |
| Cultural | Traditions, holidays, family structure |

---

## Video/Audio Content Used

### Referenced Films

| Film | Year | Director | Module | Status |
|------|------|----------|--------|--------|
| Тіні забутих предків | 1965 | Параджанов | M27 | 🌐 PD |
| The Witcher (Netflix) | 2019-2024 | Various | M02, M05, M08, M12 | Reference only |
| Harry Potter series | 2001-2011 | Various | M08 | Reference only |

### Referenced Games

| Game | Developer | Year | Modules | Status |
|------|-----------|------|---------|--------|
| S.T.A.L.K.E.R. series | GSC Game World (Kyiv) | 2007-2024 | M01, M03, M09-11, M13, M15, M17-18 | Reference only |
| The Witcher 3 | CD Projekt Red | 2015 | M02, M05, M12 | Reference only |

### Audio References (Songs)

| Song | Type | Module | Status |
|------|------|--------|--------|
| Червона рута | Popular | M21 | 🌐 Reference |
| Все буде добре | Popular | M22 | 🌐 Reference |
| Гуляла дівчина бережком | Folk | M06 | 🌐 PD |
| Ой у лузі червона калина | Folk | M29 | 🌐 PD |
| Місяць на небі | Folk | M29 | 🌐 PD |
| Пісня козака | Folk | M28 | 🌐 PD |
| Коломийки (genre) | Folk | M14 | 🌐 PD |

---

## Self-Created Content Summary

### Grammar Aids

| Type | Modules | Description |
|------|---------|-------------|
| Cyrillic charts | M01-02 | True Friends, False Friends tables |
| Gender endings | M03 | -а/-я (f), consonant (m), -о/-е (n) |
| Verb conjugation | M06-08 | Class I and II patterns |
| Case tables | M11-16 | Accusative, Locative, Genitive |
| Time expressions | M21-23 | Past, Future, Clock time |

### Cultural Content

| Type | Modules | Description |
|------|---------|-------------|
| Metro system | M15, M20 | Kyiv metro lines, announcements |
| City descriptions | M10, M15, M20 | Kyiv, Lviv characteristics |
| Food vocabulary | M09, M18-19 | Ukrainian cuisine categories |
| Holiday calendar | M33 | Ukrainian celebrations |

---

## Quality Standards Applied

### Image Requirements (when used)
- Minimum resolution: 800x600 pixels (A1 lower requirement)
- Format: PNG or JPG
- Alt text required for accessibility

### Audio Requirements (when used)
- Format: MP3, 128kbps minimum
- Native speaker recordings
- Clear pronunciation for beginners
- Duration: 15-60 seconds per clip

### External Link Requirements
- All links verified working
- Ukrainian Lessons as primary resource partner
- Links to free content only
- Educational purpose only

---

## Notes

1. **Pop Culture Strategy**: S.T.A.L.K.E.R. and Witcher references serve as engagement hooks for gamer demographic
2. **External Resources**: Ukrainian Lessons (Anna Ohoiko) is the primary recommended resource
3. **Self-Created Preference**: Most A1 content is self-created rather than requiring permissions
4. **Music References**: Songs are referenced for cultural context, not embedded
5. **Transliteration**: Full in M01-10, vocabulary-only in M11-20, first-occurrence in M21-34

---

## Related Documents

- `docs/l2-uk-en/MEDIA-SOURCES.md` - Source tracking
- `docs/l2-uk-en/A1-CURRICULUM-PLAN.md` - Module specifications
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Quality standards
