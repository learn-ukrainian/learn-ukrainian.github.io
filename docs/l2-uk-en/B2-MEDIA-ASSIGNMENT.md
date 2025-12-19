# B2 Media Content Assignment

**Status:** Needs External Resources Added
**Created:** 2025-12-14
**Updated:** 2025-12-16
**GitHub Issue:** #136

This document assigns media content to B2 modules.

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

**Current state:** 0/135 B2 modules have `> [!resources]` sections.

### Verified Resource Sites

| Site | Best For | Example URLs |
|------|----------|--------------|
| **ukrainianlessons.com** | Passive voice, register | `/passive-voice/`, `/register-formal/`, `/idioms/` |
| **ukrainiancourse.com** | Grammar tables | `/grammar-tables/` |
| **ukrainianlanguage.org.uk** | Academic lessons | `/read/unit15/` (passive), `/read/unit20/` (participles) |
| **speakua.com** | Blog articles | `/blog/` |
| **aspect.in.ua** | Verb aspect pairs | Homepage lookup tool |

### YouTube Channels for Learning Ukrainian

| Channel | Handle | Best For |
|---------|--------|----------|
| **Ukrainian Lessons** | `@UkrainianLessons` | Structured grammar, podcasts |
| **Let's Learn Ukrainian** | `@LetsLearnUkrainian` | Passive voice, complex grammar |
| **Ukrainian Language** | `@LearnUkrainianLanguage` | Grammar lessons |
| **Speak Ukrainian** | `@speakukrainian` | Comprehensive grammar |
| **Olga Reznikova** | `@OlgaReznikova` | Wide variety (233K subs) |

### Finding YouTube Videos with yt-dlp

```bash
# B2 topic searches
yt-dlp "ytsearch5:Ukrainian passive voice пасивний стан" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian participles дієприкметник" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian register formal official" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian idioms proverbs приказки" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian history Козаки Хмельницький" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian literature Шевченко Франко" --print "%(webpage_url)s" --skip-download
```

### Module Topics → Search Terms

| Phase | Modules | Topics | Search Terms |
|-------|---------|--------|--------------|
| B2.1 | M01-30 | Passive Voice, Participles, Register | `Ukrainian passive voice -но -то register formal official academic` |
| B2.1b | M31-40 | Numerals, Word Formation, Syntax | `Ukrainian numeral declension word formation suffixes` |
| B2.2 | M41-70 | Grammar Completion, Proverbs, Idioms, Synonyms | `Ukrainian aspect secondary imperfectivization idioms proverbs фразеологізми synonyms` |
| B2.3 | M71-95 | Ukrainian History | `Ukrainian history Kyivan Rus Козаки Хмельницький Голодомор` |
| B2.4 | M96-120 | Biographies | `Ukrainian Шевченко Франко Леся Українка biography` |
| B2.5 | M121-135 | Advanced Skills | `Ukrainian academic writing B2 advanced` |

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
>
> **Struggling with a skill?** Go back to:
> - Skill X → Module Y
> - Skill Z → Module W
```

**Live example:** [A1 Module 10](https://krisztiankoos.github.io/curricula-opus/docs/a1/module-10#need-more-practice)

**Icon conventions:**
| Icon | Type |
|------|------|
| 🎧 | Audio/Pronunciation guides |
| 🎙️ | Podcast episodes |
| 📖 | Grammar guides |
| 📚 | Reading resources |
| 🎬 | Video content |

**GitHub Issue:** [#170](https://github.com/krisztiankoos/curricula-opus/issues/170) - Standardize "Need More Practice?" section

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

### Content Types

| Type | Description | Primary Source |
|------|-------------|----------------|
| **Audio** | Pronunciation, dialogues, listening | Native speaker recordings |
| **Video** | Documentaries, interviews, culture | Ukrainer, Hromadske, UA:Pershyi |
| **Images** | Historical photos, art, diagrams | Wikimedia, museums |
| **Maps** | Historical territories, modern regions | Wikimedia, OpenStreetMap |
| **Text** | News, literature excerpts | Public domain, BBC Ukrainian |

### Phase-Specific Approach

| Phase | Primary Media | Secondary | Immersion |
|-------|--------------|-----------|-----------|
| B2.1 (M01-30) | Grammar diagrams, register examples | Audio dialogues | 65-70% |
| B2.1b (M31-40) | Tables, charts | Audio examples | 70-75% |
| B2.2 (M41-70) | Grammar charts, cultural images, idiom illustrations | Folk song clips | 75-80% |
| B2.3 (M71-95) | Historical maps, photos, portraits | Documentary clips | 80-85% |
| B2.4 (M96-120) | Biographical photos, artwork | Interview clips | 80-85% |
| B2.5 (M121-135) | Mixed per skill focus | Presentation examples | 85-90% |

---

## Video Sources

### YouTube Channels

| Channel | URL | Content Type | Status | B2 Use |
|---------|-----|--------------|--------|--------|
| Ukraїner | youtube.com/@ukrainernet | Documentary, culture, regions | ❓ TBD | B2.3-B2.4 history/biographies |
| Hromadske | youtube.com/@hromadske_ua | News, interviews, current events | ❓ TBD | B2.1 register examples |
| UA:Pershyi | youtube.com/@UAPershyi | National television | ❓ TBD | B2.3 historical programs |
| Радіо Свобода | youtube.com/@radiosvoboda | News, analysis, interviews | ❓ TBD | B2.1 media register |
| Liga.net | youtube.com/@liga_net | Political news, analysis | ❓ TBD | B2.1 politics vocabulary, M26 |
| Прямий | youtube.com/@PriamyiChannel | Political news, analysis | ❓ TBD | B2.1 politics vocabulary |
| Телеканал 1+1 | youtube.com/@1plus1 | Entertainment, documentary | ❓ TBD | B2.2 contemporary culture |
| ICTV | youtube.com/@ICTVchannel | News, factual programs | ❓ TBD | B2.1 news register |

#### History & Culture Channels

| Channel | URL | Content Type | Status | B2 Use |
|---------|-----|--------------|--------|--------|
| Комікс Історик | youtube.com/@komikistoryk | Animated history, culture | ❓ TBD | B2.3 M71-95 history modules |
| Реальна історія | youtube.com/@realnaistoriia | Historical analysis | ❓ TBD | B2.3 M71-95 history modules |
| **Історія мови** | youtube.com/@Istoria-Movy | Ukrainian language development | ❓ TBD | **PURE GOLD** B2.1-B2.3 |

**Note:** Історія мови is exceptionally valuable for B2 linguistic content - covers language history, dialectology, and standardization.

#### Literary & Arts Channels

| Channel | URL | Content Type | Status | B2 Use |
|---------|-----|--------------|--------|--------|
| Радіо Хартія (Zhadan) | youtube.com/@RadioKhartia | Literary discussions, culture | ❓ TBD | B2.4 M96-120 biographies |
| Жовті кеди | youtube.com/@ZhovtiKedy | Talk show, colloquial speech | ❓ TBD | B2.1 M24 colloquial register |

#### Science & Technology Channels

| Channel | URL | Content Type | Status | B2 Use |
|---------|-----|--------------|--------|--------|
| Alpha Centauri | youtube.com/@theACentauri | Space, astronomy | ❓ TBD | B2.5 M122-123 science/tech |
| Цікава наука | youtube.com/@... | Science education | ❓ TBD | B2.1 technical register |

#### Food & Lifestyle Channels

| Channel | URL | Content Type | Status | B2 Use |
|---------|-----|--------------|--------|--------|
| Klopotenko | youtube.com/@klopotenko | Ukrainian cuisine | ❓ TBD | B2.2 cultural context |

#### Animation & Film

| Channel | URL | Content Type | Status | B2 Use |
|---------|-----|--------------|--------|--------|
| Eneida (Animated) | youtube.com/watch?v=9m_z2XpuBk8 | Classic Ukrainian animation | ❓ TBD | B2.2 M22 literary register |

### Documentary Sources

| Source | Content | Status | Modules |
|--------|---------|--------|---------|
| Ukraїner Regional Series | All oblasts of Ukraine | ❓ TBD | B2.3 M71-95 |
| "Незвідані міста" (Ukraїner) | City explorations | ❓ TBD | B2.2 cultural modules |
| Національна рада з телебачення | Archive broadcasts | ❓ TBD | B2.3 historical modules |
| Довженко-Центр | Classic Ukrainian cinema | ❓ TBD | B2.4 cultural biographies |

---

## Audio Sources

### Pronunciation & Dialogues

| Type | Source | Status | Notes |
|------|--------|--------|-------|
| Register dialogues | Recording needed | 🎨 Planned | Formal/informal pairs |
| Business conversations | Recording needed | 🎨 Planned | Professional contexts |
| Academic lectures | University archives | ❓ TBD | B2.1 academic register |
| Medical dialogues | Recording needed | 🎨 Planned | B2.1 M20 medical register |

### Music for Cultural Context

| Song/Artist | Album/Source | Modules | Status | License |
|-------------|--------------|---------|--------|---------|
| Traditional folk songs | Folk archives | M45-46 proverbs | 🌐 PD | Traditional |
| Bandura recordings | Kobzar archives | M109 Skovoroda | ❓ TBD | Traditional |
| Kvitka Tsisyk | "Два кольори" | M108 | ❓ TBD | Commercial |
| Okean Elzy (excerpts) | Various | B2.5 culture | ❓ TBD | Commercial |

### Poetry Recitations

| Work | Reciter/Source | Modules | Status |
|------|----------------|---------|--------|
| Кобзар selections | Various recordings | M07, M110 | 🌐 PD |
| Лісова пісня | Theatre recordings | M99 | ❓ TBD |
| Lina Kostenko poems | Contemporary recordings | M107 | ❓ TBD |

---

## Image Sources

### Stock Photos (Free)

| Source | URL | License | Use Case |
|--------|-----|---------|----------|
| Unsplash | unsplash.com | 🔓 CC0 | Nature, animals, objects |
| Pexels | pexels.com | 🔓 CC0 | Lifestyle, Ukraine photos |
| Wikimedia Commons | commons.wikimedia.org | 🔓/🌐 | Historical, portraits |
| Pixabay | pixabay.com | 🔓 CC0 | General purpose |

### Museum & Archive Sources

| Institution | Collection | Content | Status | Modules |
|-------------|------------|---------|--------|---------|
| Національний художній музей | Art collection | Ukrainian paintings | ❓ TBD | M105-106 artists |
| Музей Шевченка | Shevchenko collection | Portraits, manuscripts | 🌐 PD | M110 |
| Львівський історичний музей | Historical artifacts | Cossack period | ❓ TBD | M76-79 |
| Національний музей історії | Historical photos | 20th century | ❓ TBD | M84-95 |
| Музей Голодомору | Memorial collection | Holodomor | ❓ TBD | M87 |
| Чорнобильський музей | Disaster documentation | Chornobyl | ❓ TBD | M91 |

### Portrait Gallery (Pre-1950 = Public Domain)

| Person | Source | Status | Module |
|--------|--------|--------|--------|
| Роксолана (Hurrem Sultan) | Wikimedia | 🌐 PD | M96 |
| Анна Ярославна | Wikimedia | 🌐 PD | M72 |
| Богдан Хмельницький | Wikimedia | 🌐 PD | M77, M113 |
| Іван Мазепа | Wikimedia | 🌐 PD | M79, M114 |
| Григорій Сковорода | Wikimedia | 🌐 PD | M109 |
| Тарас Шевченко | Wikimedia (self-portraits) | 🌐 PD | M83, M110 |
| Іван Франко | Wikimedia | 🌐 PD | M111 |
| Леся Українка | Wikimedia | 🌐 PD | M99 |
| Михайло Грушевський | Wikimedia | 🌐 PD | M85, M112 |
| Соломія Крушельницька | Wikimedia | 🌐 PD | M100 |
| Катерина Білокур | Wikimedia | 🌐 PD | M105 |
| Марія Примаченко | Museums | ❓ TBD | M106 |
| Василь Стус | Archives | ❓ TBD | M90, M116 |

---

## Historical Maps

| Map Description | Period | Source | Status | Module |
|-----------------|--------|--------|--------|--------|
| Трипільська культура | 5500-2750 BCE | Wikimedia | 🌐 PD | M71 |
| Київська Русь | 9th-13th c. | Wikimedia | 🌐 PD | M72 |
| Галицько-Волинське князівство | 13th-14th c. | Wikimedia | 🌐 PD | M73 |
| Велике князівство Литовське | 14th-16th c. | Wikimedia | 🌐 PD | M74 |
| Річ Посполита | 16th-18th c. | Wikimedia | 🌐 PD | M75 |
| Запорозька Січ | 15th-18th c. | Wikimedia | 🌐 PD | M76 |
| Козацька Гетьманщина | 1648-1764 | Wikimedia | 🌐 PD | M77-80 |
| Російська/Австрійська імперії | 18th-20th c. | Wikimedia | 🌐 PD | M81-82 |
| УНР/ЗУНР | 1918-1921 | Wikimedia | 🌐 PD | M85 |
| УРСР | 1922-1991 | Wikimedia | 🌐 PD | M86-90 |
| Сучасна Україна + окуповані | 2014-present | Self-created | 🎨 Planned | M95 |

---

## Text Sources

### Literature (Public Domain)

| Work | Author | Year | Status | Modules |
|------|--------|------|--------|---------|
| Кобзар | Шевченко | 1840 | 🌐 PD | M07, M22, M110 |
| Енеїда | Котляревський | 1798 | 🌐 PD | M22 (literary register) |
| Захар Беркут | Франко | 1883 | 🌐 PD | M22, M111 |
| Лісова пісня | Леся Українка | 1911 | 🌐 PD | M22, M99 |
| Intermezzo | Коцюбинський | 1908 | 🌐 PD | M22 (literary register) |
| Камінний хрест | Стефаник | 1900 | 🌐 PD | M22 (literary register) |
| Philosophy works | Сковорода | 1770s | 🌐 PD | M109 |

### News & Media Sources

| Source | Type | Status | Modules |
|--------|------|--------|---------|
| BBC Ukrainian | News excerpts | ❓ TBD | M23 media register |
| Українська правда | News analysis | ❓ TBD | M26 politics vocab |
| НВ (Новое время) | Long-form journalism | ❓ TBD | M28 economics |
| Zaxid.net | Regional news | ❓ TBD | B2.3 regional context |

### Official Document Sources

| Source | Content | Status | Modules |
|--------|---------|--------|---------|
| Zakon.rada.gov.ua | Legal texts | 🌐 PD | M19, M27 |
| Cabinet of Ministers | Government documents | 🌐 PD | M03, M17 |
| MOZ (Ministry of Health) | Medical guidelines | 🌐 PD | M20 |
| Правопис 2019 | Language standard | 🌐 PD | All grammar modules |

---

## Phase B2.1: Grammar & Register (M01-30)

### Media Requirements

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 01 | Passive Voice - Complete System | Grammar diagram (4 forms) | 🎨 Self-created | Planned |
| 02 | Past Passive Participles | Formation chart, audio examples | 🎨 Self-created | Planned |
| 03 | Impersonal -но/-то | Government document samples | zakon.rada.gov.ua | 🌐 PD |
| 04 | Reflexive -ся Passive | Scientific text excerpts | Wikipedia UA | 🔓 CC |
| 05 | 3rd Person Plural Passive | Colloquial dialogue audio | 🎨 Recording needed | Planned |
| 06 | Passive in Context | Register comparison chart | 🎨 Self-created | Planned |
| 07 | Active Participles I | Kobzar excerpt | Shevchenko | 🌐 PD |
| 08 | Active Participles II | Academic text excerpt | Wikipedia UA | 🔓 CC |
| 09 | Participles vs Clauses | Style comparison diagram | 🎨 Self-created | Planned |
| 10 | Adverbial Participles | Complex sentence diagrams | 🎨 Self-created | Planned |
| 11 | Multi-clause Sentences | Sentence structure diagrams | 🎨 Self-created | Planned |
| 12 | Parenthetical Expressions | BBC Ukrainian excerpts | BBC | ❓ TBD |
| 13 | Emphasis & Inversion | Kobzar examples | Shevchenko | 🌐 PD |
| 14 | Stylistic Connectors | Academic paper samples | Wikipedia UA | 🔓 CC |
| 15 | Register - Introduction | Register spectrum chart | 🎨 Self-created | Planned |
| 16 | Register - Formal/Informal | Dialogue audio pairs | 🎨 Recording needed | Planned |
| 17 | Register - Business | Business letter templates | Model documents | 🎨 Planned |
| 18 | Register - Academic | Academic paper excerpt | Wikipedia UA | 🔓 CC |
| 19 | Register - Official/Legal | Law excerpts | zakon.rada.gov.ua | 🌐 PD |
| 20 | Register - Medical | Medical dialogue sample | 🎨 Recording needed | Planned |
| 21 | Register - Technical | Wikipedia tech article | Wikipedia UA | 🔓 CC |
| 22 | Register - Literary | Kobzar, Франко excerpts | PD authors | 🌐 PD |
| 23 | Register - Media | Hromadske news clip | Hromadske | ❓ TBD |
| 24 | Register - Colloquial | Casual audio dialogue | 🎨 Recording needed | Planned |
| 25 | Register Practice | Cross-register samples | 🎨 Self-created | Planned |
| 26 | Politics & Government | Rada TV clip, parliament diagram | Rada TV | 🌐 PD |
| 27 | Law & Justice | Court terminology, legal diagram | Wikimedia | 🌐 PD |
| 28 | Economics & Business | Business news excerpt | NV/Ekonomichna Pravda | ❓ TBD |
| 29 | B2.1 Integration | Mixed register review | Various | Mixed |
| 30 | B2.1 Checkpoint | Assessment materials | 🎨 Self-created | Planned |

### Audio Needs (B2.1)

- [ ] Register dialogue pairs (formal/informal) - 10 pairs minimum
- [ ] Business conversation - 2-3 minute dialogue
- [ ] Academic lecture excerpt - 3-5 minutes
- [ ] Medical consultation - 2-3 minute dialogue
- [ ] Colloquial conversation samples - 5 short clips

---

## Phase B2.1b: Grammar Completion (M31-40)

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 31 | Numeral Declension I | Time/date tables, audio | 🎨 Self-created | Planned |
| 32 | Numeral Declension II | Compound number chart | 🎨 Self-created | Planned |
| 33 | Word Formation - Person | Suffix diagram | 🎨 Self-created | Planned |
| 34 | Word Formation - Abstract | Noun formation chart | 🎨 Self-created | Planned |
| 35 | Word Formation - Place | Ukraine place names map | OpenStreetMap | 🔓 CC |
| 36 | Word Formation - Adjective | Adjective formation tree | 🎨 Self-created | Planned |
| 37 | Word Formation - Adverb | Adverb derivation chart | 🎨 Self-created | Planned |
| 38 | One-member Sentences | Kobzar poetry examples | Shevchenko | 🌐 PD |
| 39 | Religious & Epistolary | Church text, letter samples | Historical | 🌐 PD |
| 40 | Advanced Pronouns + Check | Pronoun chart, assessment | 🎨 Self-created | Planned |

---

## Phase B2.2: Phraseology & Synonymy (M41-70)

### Advanced Grammar Completion (M41-44)

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 41 | Aspect Nuances I - Secondary Imperfectivization | Aspect transformation chart | 🎨 Self-created | Planned |
| 42 | Aspect Nuances II - Imperative & Infinitive | Imperative aspect diagram | 🎨 Self-created | Planned |
| 43 | Correlative Constructions (Співвідносні) | Correlative structure chart | 🎨 Self-created | Planned |
| 44 | Complex Syntax - Ellipsis & Parcelling | Sentence structure diagrams | 🎨 Self-created | Planned |

### Proverbs (M45-46)

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 45 | Proverbs I - Work, Wisdom & Character | Folk art illustrations | Prymachenko style | ❓ TBD |
| 46 | Proverbs II - Nature, Time & Caution | Nature photography | Unsplash/Pexels | 🔓 CC0 |

### Set Expressions (M47-48)

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 47 | Set Expressions I - Body & Animals | Body diagram, animal photos | 🎨 Self-created + Unsplash | Mixed |
| 48 | Set Expressions II - Objects & Abstract | Conceptual diagrams | 🎨 Self-created | Planned |

### Idioms (M49-54)

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 49 | Idioms - Body (Head/Face) | Face diagram with labels | 🎨 Self-created | Planned |
| 50 | Idioms - Body (Hands/Legs) | Body part diagram | 🎨 Self-created | Planned |
| 51 | Idioms - Body (Heart/Soul) | Conceptual art | 🎨 Self-created | Planned |
| 52 | Idioms - Animals I (Wolf, Dog, Horse) | Animal photos | Unsplash | 🔓 CC0 |
| 53 | Idioms - Animals II (Birds, Fish, Insects) | Animal photos | Unsplash | 🔓 CC0 |
| 54 | Idioms - Nature (Water, Fire, Earth, Wind) | Nature photography | Pexels | 🔓 CC0 |

### Synonyms (M55-66)

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 55 | Synonyms - Emotion | Emotion spectrum chart | 🎨 Self-created | Planned |
| 56 | Synonyms - Size | Size comparison diagram | 🎨 Self-created | Planned |
| 57 | Synonyms - Movement | Movement verbs diagram | 🎨 Self-created | Planned |
| 58 | Synonyms - Quality | Quality scale chart | 🎨 Self-created | Planned |
| 59 | Synonyms - Communication | Communication verbs network | 🎨 Self-created | Planned |
| 60 | Synonyms - Character | Character trait wheel | 🎨 Self-created | Planned |
| 61 | Synonyms - Time | Timeline diagram | 🎨 Self-created | Planned |
| 62 | Synonyms - Place | Location vocabulary map | 🎨 Self-created | Planned |
| 63 | Synonyms - Quantity | Quantity scale chart | 🎨 Self-created | Planned |
| 64 | Synonyms - Action | Action verb network | 🎨 Self-created | Planned |
| 65 | Synonyms - State | State vocabulary chart | 🎨 Self-created | Planned |
| 66 | Synonyms - Abstract | Concept map | 🎨 Self-created | Planned |

### Advanced Conjunctions & Integration (M67-70)

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 67 | Advanced Conjunctions I - Causal & Concessive | Sentence connector diagram | 🎨 Self-created | Planned |
| 68 | Advanced Conjunctions II - Temporal & Conditional | Clause relationship diagram | 🎨 Self-created | Planned |
| 69 | B2.2 Integration Practice | Mixed phraseology review | Various | Mixed |
| 70 | B2.2 Checkpoint | Assessment materials | 🎨 Self-created | Planned |

### Folk Culture Media (B2.2)

- [ ] Maria Prymachenko artwork - Contact National Art Museum
- [ ] Folk song audio clips - Ukrainian folk archives
- [ ] Vyshyvanka pattern photos - Wikimedia Commons (public domain patterns)
- [ ] Traditional Ukrainian nature photos - Unsplash/Pexels

---

## Phase B2.3: Ukrainian History (M71-95)

### Module Media Assignments

| # | Title | Required Media | Primary Source | Status |
|---|-------|----------------|----------------|--------|
| 71 | Kyivan Rus - Beginnings | Trypillia artifacts, early Kyiv | Wikimedia | 🌐 PD |
| 72 | Kyivan Rus - Golden Age | Saint Sophia mosaics, Volodymyr | Wikimedia | 🌐 PD |
| 73 | Galicia-Volhynia | Danylo Halytskyi, Lviv | Wikimedia | 🌐 PD |
| 74 | Grand Duchy of Lithuania | Territory map, Vitovt | Wikimedia | 🌐 PD |
| 75 | Polish-Lithuanian Commonwealth | Lublin Union painting | Wikimedia | 🌐 PD |
| 76 | Cossack Origins | Sich illustrations, Dmytro Vyshnevetsky | Wikimedia | 🌐 PD |
| 77 | Khmelnytsky Uprising | Khmelnytsky portrait, Zhovti Vody | Wikimedia | 🌐 PD |
| 78 | Pereiaslav Myths | Treaty document analysis | Historical archives | 🌐 PD |
| 79 | Hetmanate Period | Mazepa portrait, Baturyn | Wikimedia | 🌐 PD |
| 80 | Ruina & Division | Division map, Rozumovsky | Wikimedia | 🌐 PD |
| 81 | Russian Imperial Rule | Ems Ukaz, Valuev Circular | Historical archives | 🌐 PD |
| 82 | Austrian Galicia | Lviv historical photos, Franko | Wikimedia | 🌐 PD |
| 83 | National Revival | Shevchenko, Kostomarov, Kyrylo-Mefodiy | Wikimedia | 🌐 PD |
| 84 | WWI & Revolution | WWI photos, Petliura | Wikimedia | 🌐 PD |
| 85 | UNR & ZUNR | Hrushevsky, proclamation photos | Wikimedia | 🌐 PD |
| 86 | Soviet 1920s | Ukrainization posters, Skrypnyk | Wikimedia | 🌐 PD |
| 87 | Holodomor | Memorial photos, survivor testimonies | Holodomor Museum | ❓ TBD |
| 88 | WWII | Occupation map, Babyn Yar, UPA | Wikimedia | 🌐 PD |
| 89 | Soviet Post-War | Industrial photos, Dnipro dams | Wikimedia | 🌐 PD |
| 90 | Dissidents & Sixties | Stus, Chornovil, Symonenko photos | Archives | ❓ TBD |
| 91 | Chornobyl | Disaster photos, exclusion zone | Wikimedia | 🌐 PD |
| 92 | Independence 1991 | Referendum photos, declaration | National archives | 🌐 PD |
| 93 | Orange Revolution | Maidan 2004 photos | Wikimedia | 🔓 CC |
| 94 | Euromaidan | Maidan 2013-14 photos, video | Ukrainer/Hromadske | ❓ TBD |
| 95 | Russia's War | Current conflict maps, images | News sources | ❓ TBD |

### Video Sources (B2.3 History)

| Source | Content | Status | Priority |
|--------|---------|--------|----------|
| Ukraїner "Історії" | Regional history documentaries | ❓ TBD | HIGH |
| Hromadske | Euromaidan coverage, interviews | ❓ TBD | HIGH |
| UA:Pershyi | Historical documentaries | ❓ TBD | MEDIUM |
| Інститут національної пам'яті | Educational videos | ❓ TBD | HIGH |
| Музей Голодомору | Survivor testimonies | ❓ TBD | HIGH |

---

## Phase B2.4: Biographies (M96-120)

### Women (M96-108)

| # | Person | Era | Required Media | Source | Status |
|---|--------|-----|----------------|--------|--------|
| 96 | Роксолана | 16th c. | Ottoman portraits, Süleymaniye | Wikimedia | 🌐 PD |
| 97 | Ганна Барвінок | 19th c. | Portrait, book covers | Wikimedia | 🌐 PD |
| 98 | Софія Окуневська | 19th c. | Portrait, medical context | Archives | ❓ TBD |
| 99 | Леся Українка | 19th-20th c. | Portrait, Crimea photos | Wikimedia | 🌐 PD |
| 100 | Соломія Крушельницька | 19th-20th c. | Performance photos | Wikimedia | 🌐 PD |
| 101 | Ольга Басараб | 20th c. | Portrait, UVO context | Archives | ❓ TBD |
| 102 | Берта Рапопорт | 20th c. | Ship captain photos | Archives | ❓ TBD |
| 103 | Олена Степанів | 20th c. | Military portrait, USS context | Wikimedia | 🌐 PD |
| 104 | Віра Холодна | 20th c. | Silent film stills | Wikimedia | 🌐 PD |
| 105 | Катерина Білокур | 20th c. | Artwork samples | National Art Museum | ❓ TBD |
| 106 | Марія Примаченко | 20th c. | Artwork samples | National Art Museum | ❓ TBD |
| 107 | Ліна Костенко | Contemporary | Portrait, book covers | Contemporary | ❓ TBD |
| 108 | Квітка Цісик | Contemporary | Performance photos, album art | Estate | ❓ TBD |

### Men (M109-119)

| # | Person | Era | Required Media | Source | Status |
|---|--------|-----|----------------|--------|--------|
| 109 | Григорій Сковорода | 18th c. | Portrait, philosophical works | Wikimedia | 🌐 PD |
| 110 | Тарас Шевченко | 19th c. | Self-portraits, Kobzar pages | Wikimedia | 🌐 PD |
| 111 | Іван Франко | 19th-20th c. | Portrait, Lviv photos | Wikimedia | 🌐 PD |
| 112 | Михайло Грушевський | 19th-20th c. | Portrait, Tsentralna Rada | Wikimedia | 🌐 PD |
| 113 | Богдан Хмельницький | 17th c. | Historical portraits, battle scenes | Wikimedia | 🌐 PD |
| 114 | Іван Мазепа | 17th-18th c. | Portrait, Baturyn ruins | Wikimedia | 🌐 PD |
| 115 | Микола Хвильовий | 20th c. | Portrait, publications | Archives | ❓ TBD |
| 116 | Василь Стус | 20th c. | Portrait, prison context | Archives | ❓ TBD |
| 117 | В'ячеслав Чорновіл | 20th c. | Political photos | Archives | ❓ TBD |
| 118 | Леонід Каденюк | Contemporary | Astronaut photos | Space agencies | ❓ TBD |
| 119 | Валерій Залужний | Contemporary | Military photos | News sources | ❓ TBD |
| 120 | B2.4 Checkpoint | — | Assessment materials | 🎨 Self-created | Planned |

### Audio/Video for Biographies

| Person | Media Type | Source | Status |
|--------|------------|--------|--------|
| Леся Українка | Poetry recitation | Ukrainian recordings | ❓ TBD |
| Соломія Крушельницька | Opera excerpts | Historical recordings | 🌐 PD |
| Квітка Цісик | Song recordings | Albums | ❓ TBD |
| Ліна Костенко | Poetry recitation | Contemporary | ❓ TBD |
| Василь Стус | Poetry recitation | Archives | ❓ TBD |

---

## Phase B2.5: Advanced Skills & Capstone (M121-135)

| # | Title | Required Media | Source | Status |
|---|-------|----------------|--------|--------|
| 121 | Medicine Advanced | Medical diagrams, anatomy | 🎨 Self-created | Planned |
| 122 | Technology & AI | Tech diagrams, screenshots | 🎨 Self-created | Planned |
| 123 | Science & Research | Scientific method diagram | 🎨 Self-created | Planned |
| 124 | Arts & Literature | Literary timeline | 🎨 Self-created | Planned |
| 125 | Psychology & Mind | Psychology concepts | 🎨 Self-created | Planned |
| 126 | Ukrainian Mentality | Cultural comparison chart | 🎨 Self-created | Planned |
| 127 | Diaspora | World map with communities | 🎨 Self-created | Planned |
| 128 | Religion in Ukraine | Religious map, architecture photos | Wikimedia | 🔓 CC |
| 129 | Academic Writing | Essay structure diagram | 🎨 Self-created | Planned |
| 130 | Text Analysis | Analysis template | 🎨 Self-created | Planned |
| 131 | Capstone: Project | Research guide | 🎨 Self-created | Planned |
| 132 | Capstone: Presentation | Presentation template | 🎨 Self-created | Planned |
| 133 | B2 Review I | Review materials | Various | Mixed |
| 134 | B2 Review II | Review materials | Various | Mixed |
| 135 | B2 Final Exam | Exam materials | 🎨 Self-created | Planned |

---

## Permission Request Tracker

### High Priority Requests (Before B2.3 begins)

| Organization | Content | Contact | Status | Priority |
|--------------|---------|---------|--------|----------|
| Ukraїner | Documentary clips (all phases) | youtube.com/@Ukrainer | ❓ TBD | CRITICAL |
| Hromadske | News footage, Euromaidan | youtube.com/@hromadske | ❓ TBD | HIGH |
| Музей Голодомору | Memorial photos, testimonies | holodomor.org.ua | ❓ TBD | HIGH |
| Національний художній музей | Prymachenko, Bilokur artwork | namu.kiev.ua | ❓ TBD | HIGH |
| Інститут національної пам'яті | Historical educational content | memory.gov.ua | ❓ TBD | HIGH |

### Medium Priority (Before B2.4 begins)

| Organization | Content | Contact | Status |
|--------------|---------|---------|--------|
| Квітка Цісик estate | Song excerpts, photos | Via publisher | ❓ TBD |
| Lina Kostenko | Poetry permission, photo | Via publisher | ❓ TBD |
| NASA/Space agencies | Kadeniuk photos | Public relations | ❓ TBD |
| Contemporary news sources | M95 current events | Various | ❓ TBD |

### Permission Request Templates

See `docs/l2-uk-en/MEDIA-SOURCES.md` for:
- Email templates for permission requests
- Attribution format requirements
- Response tracking

---

## Self-Created Content Needs

### Diagrams & Charts (Phase Priority)

**B2.1 (Grammar/Register):**
1. Passive voice 4-form diagram
2. Register spectrum chart (7 registers)
3. Sentence structure diagrams (complex/compound)
4. Participle formation charts

**B2.2 (Phraseology):**
1. Body idiom diagrams (head, hands, heart)
2. Synonym network charts (12 topics)
3. Proverb category charts

**B2.3 (History):**
1. Historical timeline (3500 BCE - present)
2. Territory evolution maps (10 periods)
3. Key figure relationship diagrams

**B2.4 (Biographies):**
1. Biography timeline templates
2. Achievement infographics
3. Context maps (per person)

### Audio Recordings Needed

| Type | Quantity | Duration | Priority |
|------|----------|----------|----------|
| Register dialogue pairs | 10 pairs | 1-2 min each | HIGH |
| Business conversations | 5 | 2-3 min each | HIGH |
| Medical consultations | 3 | 2-3 min each | MEDIUM |
| Colloquial speech samples | 10 | 30-60 sec each | MEDIUM |
| Poetry recitations | 10 poems | 1-3 min each | HIGH |

### Maps to Create

1. Modern Ukraine with occupation lines (updated regularly)
2. Ukrainian diaspora world map
3. Religious distribution map of Ukraine
4. Regional identity/dialect map

---

## Quality Standards

### Image Requirements
- Minimum resolution: 1200x800 pixels
- Format: PNG or JPG
- Alt text required for accessibility
- Caption with source attribution

### Audio Requirements
- Format: MP3, 128kbps minimum
- Native speaker recordings
- Clear pronunciation
- Duration: 30 seconds - 3 minutes per clip

### Video Requirements
- Format: MP4 or embedded YouTube
- Maximum duration: 5 minutes per clip
- Subtitles available (or transcription provided)
- Educational use permissions confirmed

---

## Attribution Format

When approved with attribution requirement:

```markdown
**Source:** [Title](URL) by [Creator/Organization]
Used with permission / CC BY-SA 4.0 / Public Domain
```

### Module Attribution Tracker

| Module | Media Item | Attribution Required | Status |
|--------|------------|---------------------|--------|
| M07 | Kobzar excerpt | Taras Shevchenko, Public Domain | 🌐 |
| M109 | Skovoroda portrait | Wikimedia Commons, Public Domain | 🌐 |
| M72 | St. Sophia mosaics | Wikimedia Commons, CC BY-SA | 🔓 |
| ... | ... | ... | ... |

---

## Notes

1. **Public Domain priority**: Use Wikimedia Commons and public domain sources first
2. **Historical photos**: Most pre-1950 Ukrainian photos are public domain
3. **Contemporary content**: Requires explicit permission from authors/organizations
4. **Maps**: Create custom maps for modern/sensitive topics (occupation lines)
5. **Audio**: Native speaker recordings are critical - budget for professional recording
6. **Ukrainer priority**: Contact early - they have the best regional/cultural content
7. **Museum collections**: Educational use often permitted - contact in advance

---

## Related Documents

- `docs/l2-uk-en/MEDIA-SOURCES.md` - Source tracking & templates
- `docs/l2-uk-en/B2-CURRICULUM-PLAN.md` - Module specifications
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Quality standards
- `docs/l2-uk-en/B2-IMPROVEMENT-PLAN.md` - Development priorities
