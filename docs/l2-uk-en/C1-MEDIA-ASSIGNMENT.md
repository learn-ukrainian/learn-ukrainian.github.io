# C1 Media Content Assignment

**Status:** Needs External Resources Added
**Created:** 2024-12-14
**Updated:** 2025-12-16
**GitHub Issue:** TBD

This document assigns media content to C1 modules.

**📚 See also:** [MEDIA-SOURCES.md](./MEDIA-SOURCES.md) for complete channel list, permission tracking, and licensing information.

---

## ⚠️ IMPORTANT: External Resources Not Yet Added

**Current state:** 0/115 C1 modules have `> [!resources]` sections.

### Verified Resource Sites

| Site | Best For | Example URLs |
|------|----------|--------------|
| **ukrainianlessons.com** | Academic style, advanced grammar | `/academic-writing/`, `/advanced-grammar/` |
| **ukrainiancourse.com** | Grammar reference tables | `/grammar-tables/` |
| **ukrainianlanguage.org.uk** | Academic lessons | `/read/advanced/` |
| **speakua.com** | Blog articles | `/blog/` |

### YouTube Channels for Learning Ukrainian

| Channel | Handle | Best For |
|---------|--------|----------|
| **Ukrainian Lessons** | `@UkrainianLessons` | Structured grammar, podcasts |
| **Let's Learn Ukrainian** | `@LetsLearnUkrainian` | Advanced grammar deep dives |
| **Ukrainian Language** | `@LearnUkrainianLanguage` | Grammar lessons |
| **Speak Ukrainian** | `@speakukrainian` | Comprehensive grammar |
| **Olga Reznikova** | `@OlgaReznikova` | Wide variety (233K subs) |

### Finding YouTube Videos with yt-dlp

```bash
# C1 topic searches
yt-dlp "ytsearch5:Ukrainian academic writing science" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian dialects dialectology" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian stylistics register formal" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian literature Шевченко analysis" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian folk music kobzar bandura" --print "%(webpage_url)s" --skip-download
yt-dlp "ytsearch5:Ukrainian irony sarcasm humor Вишня" --print "%(webpage_url)s" --skip-download
```

### Module Topics → Search Terms

| Phase | Modules | Topics | Search Terms |
|-------|---------|--------|--------------|
| C1.1 | M01-20 | Academic Foundation | `Ukrainian academic writing thesis citation research` |
| C1.2 | M21-35 | Professional Context | `Ukrainian CV resume business dialects Surzhyk` |
| C1.3 | M36-55 | Stylistics & Rhetoric | `Ukrainian metaphor irony euphemism archaic verb forms` |
| C1.4 | M56-80 | Folk Culture & Arts | `Ukrainian kobzar bandura pysanka вишиванка folk` |
| C1.5 | M81-95 | Literature I - Classics | `Ukrainian literature Шевченко Франко Леся Українка` |
| C1.6 | M96-115 | Literature II - Modern | `Ukrainian literature Костенко Стус Андрухович Жадан` |

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

## Media Strategy Overview

### Content Types

| Type | Description | Primary Source |
|------|-------------|----------------|
| **Audio** | Academic lectures, poetry recitations, interviews | Native speaker recordings |
| **Video** | Documentaries, lectures, literary analysis | Ukrainer, Hromadske, UA:Pershyi |
| **Images** | Historical photos, art, literary portraits | Wikimedia, museums |
| **Maps** | Regional/dialect maps, historical | Wikimedia, self-created |
| **Text** | Literary excerpts, academic papers, news | Public domain, permissions |

### Phase-Specific Approach

| Phase | Primary Media | Secondary | Immersion |
|-------|--------------|-----------|-----------|
| C1.1 (M01-20) | Academic paper samples, lecture excerpts | Grammar diagrams | 90-95% |
| C1.2 (M21-35) | Business documents, news clips, dialect samples | Professional templates | 90-95% |
| C1.3 (M36-55) | Literary excerpts, satire archives, archaic texts | Register examples | 95% |
| C1.4 (M56-80) | Folk music, dance video, craft demonstrations | Ukrainer documentaries | 95% |
| C1.5 (M81-95) | Literary portraits, film clips, audiobooks | Poetry recitations | 95% |
| C1.6 (M96-115) | Author interviews, contemporary media, war literature | Capstone examples | 95% |

---

## Video Sources

### YouTube Channels

| Channel | URL | Content Type | Status | C1 Use |
|---------|-----|--------------|--------|--------|
| Ukraїner | youtube.com/@ukrainernet | Documentary, culture, regions | ❓ TBD | C1.4 folk culture, C1.2 regions |
| Hromadske | youtube.com/@hromadske_ua | News, interviews | ❓ TBD | C1.2 media landscape |
| Liga.net | youtube.com/@liga_net | Political news, analysis | ❓ TBD | C1.2 M25 political system |

#### History & Linguistics Channels

| Channel | URL | Content Type | Status | C1 Use |
|---------|-----|--------------|--------|--------|
| **Історія мови** | youtube.com/@Istoria-Movy | Ukrainian language development | ❓ TBD | **PURE GOLD** C1.1-C1.3 linguistics |
| Комікс Історик | youtube.com/@komikistoryk | Animated history, culture | ❓ TBD | C1.4-C1.5 historical context |
| Реальна історія | youtube.com/@realnaistoriia | Historical analysis | ❓ TBD | C1.5 literary history |

**Note:** Історія мови is exceptionally valuable for C1 linguistic content - covers dialectology, language history, standardization debates, and orthography evolution.

#### Literary & Arts Channels

| Channel | URL | Content Type | Status | C1 Use |
|---------|-----|--------------|--------|--------|
| Радіо Хартія (Zhadan) | youtube.com/@RadioKhartia | Literary discussions, culture | ❓ TBD | **C1.6 M106** Жадан module |
| Жовті кеди | youtube.com/@ZhovtiKedy | Talk show, colloquial speech | ❓ TBD | C1.3 M53 slang/youth language |

#### Science & Education Channels

| Channel | URL | Content Type | Status | C1 Use |
|---------|-----|--------------|--------|--------|
| Alpha Centauri | youtube.com/@theACentauri | Space, astronomy | ❓ TBD | C1.1 academic Ukrainian |
| All-Ukrainian School Online | youtube.com/@ukrainian-online-school | School curriculum | ❓ TBD | C1.1 academic context |

#### Food & Lifestyle Channels

| Channel | URL | Content Type | Status | C1 Use |
|---------|-----|--------------|--------|--------|
| Klopotenko | youtube.com/@klopotenko | Ukrainian cuisine | ❓ TBD | C1.4 folk culture context |

#### Animation & Film

| Channel | URL | Content Type | Status | C1 Use |
|---------|-----|--------------|--------|--------|
| Eneida (Animated) | youtube.com/watch?v=9m_z2XpuBk8 | Classic Ukrainian animation | ❓ TBD | C1.5 M82 Котляревський |

---

## Phase C1.1: Academic Foundation (M01-20)

### Media Requirements

| # | Title | Required Media | Source |
|---|-------|----------------|--------|
| 01 | B2 Review & Bridge to C1 | B2 grammar summary diagrams | Self-created |
| 02 | Academic Style Markers | ДСТУ samples, academic paper excerpts | Wikipedia UA |
| 03 | Research Verbs | Academic article excerpts | Наукова періодика |
| 04 | Analysis Vocabulary | Analysis framework diagrams | Self-created |
| 05 | Logical Connectors | Connector chart, sentence examples | Self-created |
| 06 | Hedging & Modality | Certainty scale diagram | Self-created |
| 07 | Citation & Reference | ДСТУ citation format guide | Official standards |
| 08 | Essay Structure | Essay structure diagram, model essays | Self-created |
| 09 | Thesis Development | Thesis examples from dissertations | University archives |
| 10 | Counterarguments | Debate video excerpts | Rada TV (PD) |
| 11 | Summary & Paraphrase | Paraphrase comparison examples | Self-created |
| 12 | Genre - Research Article (Наукова стаття) | Journal article samples | Наукова періодика |
| 13 | Genre - Abstract (Реферат) | Abstract samples, conference materials | University archives |
| 14 | Genre - Literature Review (Огляд літератури) | Literature review excerpts | University archives |
| 15 | Oral Presentations (Доповідь) | TEDxKyiv clips, presentation examples | TEDx (with permission) |
| 16 | Advanced Punctuation | Правопис 2019 examples | Official standards |
| 17 | Irregular Verbs Complete | Verb conjugation charts | Self-created |
| 18 | C1.1 Practice I - Essay Writing | Model essay with annotations | Self-created |
| 19 | C1.1 Practice II - Article Critique | Article critique example | Self-created |
| 20 | C1.1 Checkpoint | Assessment materials | Self-created |

### Audio Needs (C1.1)
- [ ] Academic lecture excerpts (university recordings)
- [ ] Conference presentation samples
- [ ] Dissertation defense audio
- [ ] Academic discussion examples

---

## Phase C1.2: Professional & Social Context (M21-35)

### Media Requirements

| # | Title | Required Media | Source |
|---|-------|----------------|--------|
| 21 | CV & Resume Writing | CV templates, professional examples | Work.ua samples |
| 22 | Interview Language | Interview audio samples | Recording needed |
| 23 | Business Etiquette | Business culture video clips | Ukrainer |
| 24 | Digital Communication | Email templates, formal correspondence | Self-created |
| 25 | Political System | Parliament diagram, Rada video clips | Rada TV (PD) |
| 26 | Media Landscape | Media landscape infographic | Self-created |
| 27 | Global Context - EU & NATO | EU integration timeline, maps | Wikimedia |
| 28 | Dialects Overview | Dialect map, audio samples by region | Linguistic archives |
| 29 | Surzhyk | Surzhyk examples, linguistic analysis | Academic sources |
| 30 | Language Policy | Law 2019 excerpts, infographic | Official documents |
| 31 | Diaspora Ukrainian | Diaspora map, heritage speaker audio | Diaspora organizations |
| 32 | C1.2 Practice I - Professional Scenarios | Professional scenario materials | Self-created |
| 33 | C1.2 Practice II - Case Studies | Case study documents | Self-created |
| 34 | C1.2 Review | Review materials | Self-created |
| 35 | C1.2 Checkpoint | Assessment materials | Self-created |

### Audio Needs (C1.2)
- [ ] Dialect audio samples (all regions)
- [ ] Business interview recordings
- [ ] News broadcast excerpts
- [ ] Diaspora speaker samples

### Video Sources (C1.2)

| Source | Content | Permission Status |
|--------|---------|-------------------|
| Ukrainer | Business/culture documentaries | TBD |
| Hromadske | Political analysis | TBD |
| Rada TV | Parliament sessions | Public domain |
| Радіо Свобода | News analysis | TBD |

---

## Phase C1.3: Advanced Stylistics & Rhetoric (M36-55)

### Media Requirements

| # | Title | Required Media | Source |
|---|-------|----------------|--------|
| 36 | Metaphor & Simile | Poetry excerpts with analysis | Kobzar (PD) |
| 37 | Irony & Sarcasm | Literary irony examples | Vyshnia (PD) |
| 38 | Hyperbole & Litotes | Literary examples | Franko, Ukrainka (PD) |
| 39 | Euphemism & Taboo | Linguistic analysis samples | Academic sources |
| 40 | Rhetorical Questions | Speech excerpts | Historical archives |
| 41 | Degrees of Certainty | Certainty scale diagram | Self-created |
| 42 | Politeness Strategies | Dialogue examples by register | Self-created |
| 43 | Indirectness | Film dialogue excerpts | Ukrainian cinema |
| 44 | Ukrainian Humor Traditions | Ostap Vyshnia excerpts | Vyshnia (PD) |
| 45 | Wordplay & Puns | Literary pun examples | Various (PD) |
| 46 | Anecdotes & Jokes | Folk humor collections | Folklore archives |
| 47 | Archaic Verb Forms | Old Ukrainian text samples | Historical archives |
| 48 | Literary Syntax | Shevchenko, Franko syntax analysis | Kobzar (PD) |
| 49 | Church Slavonicisms | Liturgical text samples | Religious archives |
| 50 | Archaic Pronouns | Historical document excerpts | Archives |
| 51 | High Formal Register | Legal document samples | Zakon.rada.gov.ua |
| 52 | Intimate Register | Literature dialogue excerpts | Ukrainian prose (PD) |
| 53 | Slang & Youth Language | Contemporary media samples | Social media (fair use) |
| 54 | C1.3 Review | Stylistics summary materials | Self-created |
| 55 | C1.3 Checkpoint | Assessment materials | Self-created |

### Literary Text Sources (C1.3)

| Author | Work | Status | Notes |
|--------|------|--------|-------|
| Остап Вишня | Усмішки | 🌐 PD | Public domain |
| Тарас Шевченко | Кобзар | 🌐 PD | Public domain |
| Іван Франко | Selected works | 🌐 PD | Public domain |
| Леся Українка | Poetry/Drama | 🌐 PD | Public domain |

---

## Phase C1.4: Folk Culture & Arts (M56-80)

### Media Requirements

| # | Title | Required Media | Source |
|---|-------|----------------|--------|
| 56 | Кобзарі та бандура | Kobzar documentary clips, bandura audio | Ukrainer |
| 57 | Обрядові пісні | Ritual song recordings | Folk archives |
| 58 | Колискові та думи | Duma performance video, lullaby audio | Folk archives |
| 59 | Гопак і козачок | Virsky ensemble video | Virsky (permission) |
| 60 | Регіональні танці | Regional dance video clips | Ukrainer |
| 61 | Писанки | Pysanka creation video, symbol chart | Ukrainer, museums |
| 62 | Вишиванка | Regional embroidery patterns, video | Ukrainer, museums |
| 63 | Гончарство та різьбярство | Opishne pottery video, Hutsul carving | Ukrainer |
| 64 | Народна міфологія | Folk creature illustrations | Wikimedia, self-created |
| 65 | Народна медицина | Herb illustrations, folk remedy texts | Botanical sources |
| 66 | Козацькі легенди | Cossack illustrations, legend texts | Wikimedia (PD) |
| 67 | Казки та притчі | Folktale audiobook excerpts | Folk archives |
| 68 | Зимові обряди | Christmas/New Year video clips | Ukrainer |
| 69 | Весна та літо | Kupala celebration video | Ukrainer |
| 70 | Хрестини та весілля | Traditional wedding video | Ukrainer |
| 71 | Поминальні обряди | Memorial tradition documentation | Ethnographic sources |
| 72 | Галичина | Galicia documentary clips | Ukrainer |
| 73 | Слобожанщина | Slobozhanshchyna documentary | Ukrainer |
| 74 | Полісся | Polissia documentary clips | Ukrainer |
| 75 | Поділля та Волинь | Central regions documentary | Ukrainer |
| 76 | Класичні композитори | Lysenko, Skoryk audio excerpts | Classical recordings |
| 77 | Сучасна музика | Contemporary Ukrainian music clips | Music labels (permission) |
| 78 | Українське кіно | Dovzhenko clips, modern film excerpts | Film archives |
| 79 | Спортивні герої | Sports highlights, athlete photos | News archives |
| 80 | C1.4 Checkpoint | Assessment materials | Self-created |

### Video Sources (C1.4)

| Source | Content | Permission Status |
|--------|---------|-------------------|
| Ukrainer | Regional documentaries (all regions) | TBD - HIGH PRIORITY |
| Музей Гончара | Folk craft demonstrations | TBD |
| Virsky Ensemble | Dance performances | TBD |
| Dovzhenko Centre | Classic Ukrainian cinema | TBD |

### Audio Sources (C1.4)

| Source | Content | Permission Status |
|--------|---------|-------------------|
| Folk music archives | Traditional songs | TBD |
| Kobzar recordings | Bandura performances | TBD |
| Opera recordings | Lysenko operas | Historical (PD) |

---

## Phase C1.5: Literature I - Classics (M81-95)

### Media Requirements

| # | Title | Required Media | Source |
|---|-------|----------------|--------|
| 81 | Історія української літератури | Literature timeline infographic | Self-created |
| 82 | Котляревський: Енеїда | Eneida text excerpts, illustrations | Wikimedia (PD) |
| 83 | Шевченко: Життя | Shevchenko portraits, biography video | Wikimedia (PD), Ukrainer |
| 84 | Шевченко: Поезія | Kobzar audiobook excerpts | Audio recordings |
| 85 | Шевченко: Спадщина | Monument photos worldwide | Wikimedia |
| 86 | Франко: Життя і поезія | Franko portraits, Lviv photos | Wikimedia (PD) |
| 87 | Франко: Проза | Zakhar Berkut text, film clips | Wikimedia (PD), Film (2019) |
| 88 | Леся Українка: Поезія | Poetry audio recordings, portraits | Wikimedia (PD) |
| 89 | Леся Українка: Драма | Лісова пісня theatre clips, Mavka film | Theatre archives, Mavka (2023) |
| 90 | Вовчок та Мирний | Author portraits, text excerpts | Wikimedia (PD) |
| 91 | Коцюбинський | Shadows of Forgotten Ancestors film | Paradjanov (1965) |
| 92 | Літературознавча термінологія | Literary terms diagram | Self-created |
| 93 | Аналіз поезії | Poetry analysis template, examples | Self-created |
| 94 | C1.5 Review | Literature review materials | Self-created |
| 95 | C1.5 Checkpoint | Assessment materials | Self-created |

### Portrait Gallery (C1.5)

| Person | Source | Status |
|--------|--------|--------|
| Котляревський | Wikimedia | 🌐 PD |
| Шевченко | Wikimedia (self-portraits) | 🌐 PD |
| Франко | Wikimedia | 🌐 PD |
| Леся Українка | Wikimedia | 🌐 PD |
| Марко Вовчок | Wikimedia | 🌐 PD |
| Панас Мирний | Wikimedia | 🌐 PD |
| Коцюбинський | Wikimedia | 🌐 PD |

### Film Sources (C1.5)

| Film | Director | Year | Permission Status |
|------|----------|------|-------------------|
| Тіні забутих предків | Параджанов | 1965 | Educational use |
| Мавка | Дерунова | 2023 | TBD - commercial |
| Захар Беркут | Сейтаблаєв | 2019 | TBD - commercial |

---

## Phase C1.6: Literature II - Modern & Capstone (M96-115)

### Media Requirements

| # | Title | Required Media | Source |
|---|-------|----------------|--------|
| 96 | Модернізм | Modernist artwork, text excerpts | Wikimedia (PD) |
| 97 | Розстріляне відродження | Executed Renaissance photos, excerpts | Archives |
| 98 | Тичина та Рильський | Poet portraits, poetry audio | Wikimedia (PD) |
| 99 | Радянський період | Sixties generation photos | Archives |
| 100 | Ліна Костенко | Portrait, poetry audio | Contemporary |
| 101 | Василь Стус | Prison photos, poetry audio | Archives |
| 102 | Діаспорна література | Diaspora author photos | Archives |
| 103 | Незалежність | 1990s literary scene photos | Archives |
| 104 | Андрухович | Author photo, interview clips | Contemporary (permission) |
| 105 | Забужко | Author photo, lecture clips | Contemporary (permission) |
| 106 | Жадан | Author photo, poetry/music clips | Contemporary (permission) |
| 107 | Воєнна література | War poetry collections, author photos | Contemporary |
| 108 | Літературна критика | Review writing templates | Self-created |
| 109 | C1.6 Review | Modern lit review materials | Self-created |
| 110 | C1.6 Integration | Essay integration examples | Self-created |
| 111 | Капстон: Проєкт | Research paper guide, model paper | Self-created |
| 112 | Капстон: Захист | Defense presentation model | Self-created |
| 113 | C1 Фінал: Читання | Reading exam practice materials | Self-created |
| 114 | C1 Фінал: Письмо | Writing exam practice materials | Self-created |
| 115 | C1 РІВЕНЬ ЗАВЕРШЕНО | Certification materials | Self-created |

### Contemporary Author Permissions (C1.6)

| Author | Content Needed | Contact | Status |
|--------|---------------|---------|--------|
| Ліна Костенко | Poetry excerpts, photo | Publisher | TBD |
| Юрій Андрухович | Interview clips, photo | Agent | TBD |
| Оксана Забужко | Lecture clips, photo | Publisher | TBD |
| Сергій Жадан | Music/poetry clips, photo | Agent | TBD |

---

## Permission Request Tracker

### High Priority Requests

| Date | Organization | Content | Status |
|------|--------------|---------|--------|
| TBD | Ukrainer | Documentary clips (all regions) | Not started |
| TBD | Hromadske | News/political footage | Not started |
| TBD | Virsky Ensemble | Dance performance clips | Not started |
| TBD | Dovzhenko Centre | Classic cinema clips | Not started |
| TBD | Contemporary authors | Interview/lecture clips | Not started |

### Permission Templates

See `docs/l2-uk-en/MEDIA-SOURCES.md` for request templates.

---

## Self-Created Content Needs

### Diagrams & Charts (Priority)

1. Academic structure diagrams (M01-20)
2. Essay/thesis templates (M08-09)
3. Literary timeline (M81)
4. Certainty scale chart (M41)
5. Register comparison charts (C1.3)
6. Regional map for dialects (M28)

### Audio Recordings Needed

1. Academic lecture samples
2. Dialect audio samples (all regions)
3. Poetry recitations (Shevchenko, Franko, Ukrainka)
4. Interview samples for listening exercises

### Maps to Create

1. Ukrainian dialect map with audio points
2. Diaspora communities world map
3. Regional folk traditions map

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
- Duration: 30 seconds - 5 minutes per clip

### Video Requirements

- Format: MP4 or embedded YouTube
- Maximum duration: 10 minutes per clip (C1 allows longer)
- Subtitles required
- Educational use permissions

---

## Notes

1. **Public Domain priority**: Use Wikimedia Commons and public domain sources first
2. **Classical literature**: All 19th century authors are public domain
3. **Contemporary content**: Requires explicit permission from authors/publishers
4. **Ukrainer**: Primary source for cultural/regional documentaries - prioritize permission request
5. **Audio**: Academic and literary recordings are critical - budget for professional recordings
6. **95% Ukrainian**: All media must support C1 immersion level

---

## Related Documents

- `docs/l2-uk-en/MEDIA-SOURCES.md` - Source tracking
- `docs/l2-uk-en/C1-CURRICULUM-PLAN.md` - Module specifications
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Quality standards
