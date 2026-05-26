# Bio Track Gap Audit — Russia-Oppressed Ukrainian Patriots

> **🔒 VERSION-LOCKED for Epic #2309**
>
> This doc is the immutable SSOT for the bio-track expansion epic. Any scope change requires a *new* audit doc (e.g. `bio-track-gap-audit-2026-Qx.md`), not in-place edits to this one. Sub-issue work references this document by URL + commit SHA.
>
> Version: `1.0-2026-05-26`
> Lock SHA: see [`docs/audits/bio-track-gap-audit-2026-05-26.lock.md`](bio-track-gap-audit-2026-05-26.lock.md)
> Companion docs:
> - [`docs/audits/bio-decolonization-checklist.md`](bio-decolonization-checklist.md) — Phase 5 Q1 reviewer checklist
> - `docs/best-practices/bio-research-source-tiers.md` — ships via #2312
> - `docs/best-practices/bio-naming-canonical.md` — ships via #2313 (with slug appendix)
> - `docs/best-practices/politically-charged-bios.md` — ships via #2311 (gates Tier 4)
> - `docs/templates/bio-research-dossier-template.md` — ships via #2314

**Date:** 2026-05-26
**Author:** Claude (orchestrator), with Gemini-3.1-pro-preview + Codex review
**Scope rule:** Any Ukrainian patriot oppressed by Russia (imperial / Soviet / Russian Federation) — writers, poets, artists, composers, scientists, clergy, military, journalists, dissidents.
**Current bio coverage:** 180 modules in `curriculum/l2-uk-en/plans/bio/`.
**Proposed additions:** 130 modules.
**Flagged (need user-by-user judgment):** 3.
**Removed from preliminary draft:** 6.

---

## Why this audit exists

User-noticed gap: Павло Тичина, Олександр Олесь, and Євген Гуцало all have LIT modules but no bio. Root cause traced (see "Cause" below) — the bio seed used an implicit "executable-biography" selection heuristic that filtered out (a) survivors-via-capitulation (Тичина), (b) emigré-survivors (Олесь, Винниченко, Багряний), (c) figures whose oppression was non-executive (Сосюра's 1951 attack, Антоненко-Давидович's 23-year camp survival), and (d) entire categories never cross-checked (UGCC martyrology, OUN/UNR military, Helsinki Group, RF-era war-killed).

Three-way review was conducted: Claude (proposal), Gemini-3.1-pro-preview (canon completeness against UA school grades 8–11 + martyrology lists), Codex (adversarial — challenge politicization risk, false-positive oppression mechanisms, framing).

---

## Cause: why these gaps existed

1. **Implicit heuristic, never documented.** The original `c1-bio` seed (Feb 2026 rename to `bio` in commit `74c33b6180`) covered the dramatically-executed cohort (Хвильовий, Зеров, Куліш М., Підмогильний, Курбас, Косинка, Антонич, Филипович) but consistently missed *survivors-under-pressure*. Тичина wrote «Партія веде» and lived; Олесь emigrated. Neither tripped the seed's selection filter.
2. **PR #894 was a LIT-gap audit, not a bio-gap audit.** Gemini-triaged 10 textbook authors missing from LIT; 5 got promoted to BIO based on "remarkable life," not on "exists in LIT but not BIO."
3. **No `lit/* − bio/*` diff exists.** Гуцало landed in `plans/lit/yevhen-hutsalo-shistdesiatnyky.yaml` (PR #894) but no audit caught that he also needed BIO.
4. **No documented inclusion criterion** for bio in `docs/best-practices/track-architecture.md`. The criterion lived in the seeders' heads.

**Process fixes proposed** (separate issues, not part of this audit):
- (i) Add `scripts/audit/bio_lit_cross_reference.py` — every author in ≥1 `plans/lit/*.yaml` must have a `plans/bio/*.yaml` or be on a documented exclusion list.
- (ii) Document the bio inclusion criterion in `docs/best-practices/track-architecture.md`.
- (iii) Establish a quarterly war-killed-writer audit drawing from PEN Ukraine + Ukrainian Institute lists.

---

## Final consolidated list (130 additions)

Legend: ✓ = wiki-verified in this audit (mcp__sources__query_wikipedia). (G) = Gemini-added. (C) = Codex-added. (K) = User-found.

### A. Розстріляне Відродження — completion (12)

| Name | Mechanism |
|---|---|
| Михайль Семенко ✓ | Shot 24 Oct 1937, NKVD Kyiv. UA-futurism founder. |
| Володимир Свідзінський ✓ | Killed by NKVD during 1941 retreat (burned in barn). |
| Михайло Драй-Хмара ✓ | Neoclassicist «ґроно п'ятірне», died Kolyma 1939. |
| Микола Вороний ✓ | Symbolist, shot 1938. |
| Михайло Яловий (C) | VAPLITE first president, shot 1937. |
| Григорій Епік (C) | VAPLITE, shot 1937. |
| Валер'ян Поліщук (C) | Constructivist poet, shot 1937. |
| Олекса Влизько (C) | Shot 1934. |
| Марко Вороний (C) | Микола Вороний's son, shot 1937. |
| Мирослав Ірчан (C) | "Західна Україна" group, shot 1937. |
| Антін Крушельницький (C) | "Західна Україна" patriarch, shot with sons 1937. |
| Софія Налепинська-Бойчук (C) | Михайло Бойчук's wife, boychukist, shot 1937. |

### B. Pre-Soviet imperial-era oppressed (6)

| Name | Mechanism |
|---|---|
| Павло Грабовський (C) | Народовольці, ~20y Siberian exile, died Tobolsk 1902. |
| Микола Костомаров (C) | Cyril-Methodius Brotherhood, exile to Saratov. Author of "Книги буття українського народу." |
| Іван Карпенко-Карий (C) | Imperial surveillance, exile. Theatre of corypheus. |
| Панас Мирний (C) | Imperial censorship of «Хіба ревуть воли...». |
| Іван Манжура ✓ (RAG) | Expelled from Kharkiv gymnasium "за непокору", expelled from Vet Institute as "неблагонадійний", banned from higher ed, tsarist censorship redacted ref to «запорожець»/«козак»/«Січ» from his work, two major collections rejected, died destitute 1893 buried as unknown. |
| Леонід Глібов (RAG) | Fabulist; Valuev decree 1863 shut down his journal «Черниговскій листокъ», suspended from teaching for sympathy with Шевченко's circle. Direct Imperial-Russia censorship. |

(Marginal: **Яків Щоголів** 1824–1898 — Russian critic Бєлінський's hatchet-job made him burn his work and go silent for years. Indirect cultural oppression rather than executive. **Осип Турянський** 1880–1933 — Galician, primarily Habsburg-Polish context; lean SKIP per scope.)

### C. Émigré-survival patriots (26)

⚠️ **Major category surfaced via RAG sweep on 2026-05-26 (2nd pass).** First-pass audit missed the entire émigré tradition. 11-klas Borzenko textbook devotes the «Під чужим небом» / «Еміграційна література» unit to these poets/prosators as the canonical post-Революція literary stream parallel to «Розстріляне відродження».

**C.1. First-wave individual émigrés (Революція 1917–22)** (5)

| Name | Mechanism |
|---|---|
| Олександр Олесь ✓ (K) | Emigrated 1919, died occupied Prague 1944. Father of Олег Ольжич. |
| Володимир Винниченко | UNR Directorate head, fled, died France 1951. «Чорна Пантера», «Сонячна машина». |
| Іван Багряний ✓ | 16y NKVD prisons/camps → DP → UNRada head. «Тигролови», «Сад Гетсиманський». |
| Тодось Осьмачка | NKVD-induced breakdown, emigrated. «План до двору». |
| Василь Королів-Старий (RAG) | UNR diplomat, writer, emigrated to Prague, died occupied Prague 1943. Literary fairy tales now in Grade 5 textbook. |

**C.2. Празька школа (Prague School), interwar 1923–39** (6)

Already in bio from this cluster: Олег Ольжич ✓, Олена Теліга ✓, Юрій Липа ✓.

| Name | Mechanism |
|---|---|
| Євген Маланюк ✓ (RAG) | UNR Army сотник, «Імператор залізних строф», Prague School flagship poet, 11-klas chapter subject «Український Одіссей». |
| Юрій Клен / Освальд Бургардт (RAG) | 5th poet of «ґроно п'ятірне» neoclassicists alongside Зеров/Драй-Хмара/Рильський/Филипович; emigrated 1931, died 1947. |
| Юрій Дараган (RAG) | Prague School founder, історіософські мотиви — Дажбог, варяги, дикий степ. |
| Наталя Лівицька-Холодна (RAG) | Прага → New York. OUN-aligned. |
| Леонід Мосендз (RAG) | Прага → Switzerland. «Останній пророк». |
| Оксана Лятуринська (RAG) | Sculptor + poet, Прага → USA. |

**C.3. МУР / DP-camp / postwar Munich (1945–50)** (6)

| Name | Mechanism |
|---|---|
| Василь Барка ✓ (RAG) | DP → USA. «Жовтий князь» — canonical Holodomor novel. |
| Віктор Домонтович / В. Петров (RAG) | Intelligence-officer scholar-writer, complex biography, «Доктор Серафікус», «Без ґрунту». |
| Ігор Костецький (RAG) | МУР theorist, modernist. |
| Докія Гуменна ✓ (RAG) | "Слово"/"Плуг" → DP → USA. Foundational woman writer of diaspora; archaeology + early Ukraine. |
| Юрій Косач (RAG) | Лесі Українки's nephew, novelist, complex postwar trajectory. |
| Михайло Орест (RAG) | Микола Зеров's brother, neoclassicist émigré poet. |

**C.4. Нью-Йоркська група (NY Group), postwar US** (5)

| Name | Mechanism |
|---|---|
| Богдан Бойчук (RAG) | NY Group founder, modernist poet. |
| Юрій Тарнавський (RAG) | NY Group, experimentalist. |
| Емма Андієвська (RAG) | Surrealist poet+painter, Munich. |
| Богдан Рубчак (RAG) | NY Group poet+critic. |
| Віра Вовк (RAG) | Brazil-based scholar+poet. |

**C.5. Diaspora institution-builders / scholars** (4)

| Name | Mechanism |
|---|---|
| Омелян Пріцак ✓ (RAG) | Founded Harvard Ukrainian Research Institute (HURI), 1973; Институт сходознавства in Kyiv post-1991. |
| Дмитро Чижевський ✓ (RAG) | Philosopher, literary scholar, slavist; Heidelberg → US universities. Foundational «Історія української літератури». |
| Юрій Лавриненко (RAG) | Compiled the canonical 1959 Paris antology «Розстріляне відродження» — the work that named the era. |
| Олекса Воропай (RAG) | Folklorist in diaspora, «Звичаї нашого народу» (London 1958), foundational ethnographic compendium under Soviet ban. |

(Already in bio: Юрій Шевельов ✓ george-shevelov.yaml.)

### D. Survived but censored / coerced + camp-returnees (8)

| Name | Mechanism |
|---|---|
| Павло Тичина ✓ (K) | Coerced/co-opted post-1933, capitulation arc. Bio is the right place to teach «трагічний злам». |
| Максим Рильський ✓ (C, K-prompted) | Київ Парнас neoclassicist; arrested 1931, ~6mo Lukyanivska prison; capitulated via «Знак терезів» 1932; post-Stalin used Soviet-laureate status to rehabilitate Зеров/Драй-Хмара and shelter шістдесятники. Already in 2 LIT modules. |
| Володимир Сосюра ✓ | UNR Гайдамацький полк → «Любіть Україну» 1944 → 1951 Pravda attack «Об идеологических извращениях». |
| Юрій Яновський | Censored Soviet laureate, attacked 1948 for «Жива вода». RECLASSIFIED from A per reviewer consensus. |
| Остап Вишня (C) | 10y Solovki camps (1934–43), survived, returned. |
| Микола Бажан ✓ (RAG) | VAPLITE survivor; Soviet poet-laureate path; in 1958 co-signed «В ім'я людини» Ukrainian-language defense with Рильський (Pravda). Same complex pattern as Тичина/Рильський — capitulation + later defensive agency. |
| Зінаїда Тулуб (RAG) | Author of «Людолови» (Cossack-era historical novel); arrested 1937, exiled to Karaganda, returned 1956 to write «В степу безкраїм за Уралом». |
| Олександр Ковінька (RAG) | Camp-returnee writer, satirist of Soviet absurdity. |

### E. Шістдесятники + Helsinki Group dissidents (29 in E.1, +3 in E.2 = 32) — full coverage per user direction

| Name | Mechanism |
|---|---|
| Євген Гуцало ✓ (K) | шістдесятники prose, «Ментальність орди». |
| Микола Руденко ✓ | UHG founder, political prisoner. |
| Іван Світличний | Critic, nerve center of шістдесятники lit-circle, 7y camps + exile. |
| Григір Тютюнник | Suicide 1980 after KGB persecution. |
| Іван Драч | шістдесятник poet (note: later compromised — content warning). |
| Микола Вінграновський | шістдесятник, Довженко's student. |
| Опанас Заливаха | Dissident artist, 5y camps. |
| Стефанія Шабатура | Tapestry artist, 8y camps. |
| Борис Антоненко-Давидович ✓ | ~23y camps (1935→1957), returned defiant. |
| Юрій Бадзьо ✓ | «Право жити», 7y camps + 5y exile. |
| Олекса Тихий | UHG co-founder, died Perm-36 camp 1984. |
| Василь Голобородько (C) | шістдесятник, banned 20+ years. |
| Сергій Параджанов (G) | «Тіні забутих предків» Ukrainian; jailed 1973–77, 1982. |
| Валерій Марченко (G+C) | Journalist, died in Gulag 1984. |
| Юрій Литвин (G) | Poet, died in Gulag 1984. |
| Леонід Плющ (C) | Mathematician, special-psych-hospital, exiled. |
| Ніна Строката (C) | Microbiologist, UHG, camps. |
| Ігор Калинець (C) | Poet, camps + exile. |
| Ірина Калинець (C) | Poet, camps. |
| Надія Світлична (C) | UHG, Іван's sister. |
| Святослав Караванський (C) | 32y in camps + exile. |
| Михайло Горинь (C) | Camps, UHG. |
| Богдан Горинь (C) | Михайло's brother, camps. |
| Оксана Мешко (C) | UHG matriarch, exile at 79. |
| Юрій Шухевич (C) | Roman Шухевич's son, ~40y total camps. |
| Данило Шумук (C) | 42y in camps (Polish + 2× Soviet). |
| Іван Кандиба (C) | UHG founder, camps. |
| Василь Овсієнко (C) | UHG, camps. |
| Валентин Мороз (C) | Camps. |

### E.2 — шістдесятники visual + theater (added via RAG sweep)

| Name | Mechanism |
|---|---|
| Лесь Танюк (RAG) | Theater director, founded «Клуб творчої молоді» in Kyiv 1960 — the шістдесятники hub. |
| Віктор Зарецький (RAG) | Painter, Алла Горська's husband; targeted post-1970 murder of Горська. |
| Веніамін Кушнір (RAG) | шістдесятники painter. |

(Block E total: 32. Full coverage per user direction 2026-05-26.)

### F. War-killed / RF-captured post-2014 (12)

| Name | Mechanism |
|---|---|
| Василь Сліпак (C) | Opera baritone, KIA Donbas 2016. |
| Олександр Мацієвський (C) | "Слава Україні" execution by RF, 2023. |
| Володимир Рибак (C) | Horlivka deputy, killed 2014. |
| Макс Левін (C) | Photojournalist, killed by RF 2022. |
| Ірина Цибух «Чека» (C) | Medic, KIA 2024. |
| Вікторія Рощина (C) | Journalist, died in RF captivity 2024. |
| Станіслав Асєєв (C) | Writer, DNR torture-captivity «Світлий шлях». |
| Владислав Єсипенко (C) | RFE/RL journalist, RF captivity. |
| Геннадій Афанасьєв ✓ (C) | Sentsov-case co-defendant, RF prisoner 2014–16, Hero of Ukraine. ZSU servicemember. |
| Віктор Гурняк ✓ (C) | Photojournalist + 24th "Айдар" batt., KIA 2014, Hero of Ukraine. |
| Гліб Бабіч ✓ (C) | Poet, killed near Ізюм 2022. |
| Ігор Козловський ✓ (C) | Religious-studies scholar (NAS), 2y DNR captivity, PEN UA. |

(Existing in bio: Кривцов, Вакуленко, Амеліна, Руф. With these 12, total war-block = 16.)

### G. OUN/UPA/UNR military leadership (9) — ⚠️ all require content-warning framing

| Name | Mechanism | Content warning |
|---|---|---|
| Степан Бандера ✓ (K) | Polish prisons → Sachsenhausen → KGB assassination Munich 1959. | HIGH |
| Ярослав Стецько ✓ | Co-author 30 Jun 1941 Akt, Sachsenhausen 1942–44. | HIGH |
| Андрій Мельник | OUN(m) leader, German camps, emigrated. | MED |
| Дмитро Клячківський «Клим Савур» | UPA-North commander, killed by NKVD 1945. | HIGH (Volhynia 1943 record) |
| Юрій Тютюнник ✓ | UNR general, Зимовий похід, lured to USSR, shot Moscow 1930. | normal |
| Августин Волошин (C) | Carpatho-Ukraine president, kidnapped NKVD 1945, died Moscow prison. | normal |
| Лев Ребет (C) | OUN ideologue, KGB-assassinated by Stashynsky 1957 (before Bandera). | MED |
| Катерина Зарицька (C) | UPA underground, 30y camps. | normal |
| Петро Федун-Полтава (C) | UPA chief ideologue. | MED |

### H. Scholars / scientists oppressed (4)

| Name | Mechanism |
|---|---|
| Михайло Кравчук ✓ | Mathematician, founder of UA math terminology, died Kolyma 1942. Taught Корольов. |
| Степан Рудницький (C) | Geographer (foundational «Україна — наш рідний край»), shot Sandarmokh 1937. |
| Дмитро Яворницький (C) | Cossack historian («Історія запорізьких козаків»), censored, died 1940. |
| Катерина Грушевська (C) | Folklorist, Михайло's daughter, exiled, died Magadan 1943. |

### I. Visual artists + composers oppressed (8)

| Name | Mechanism |
|---|---|
| Василь Барвінський (C) | Composer, 10y Gulag, scores destroyed by Soviet authorities. |
| Олександр Кошиць | UNR Republican Capella conductor (Щедрик→world), emigré. |
| Василь Кричевський | Designed UNR trident, emigré. |
| Іван Гончар | Folk-art collector, KGB harassment, museum suppressed. |
| Іван Падалка (C) | Boychukist, shot 1937. |
| Василь Седляр (C) | Boychukist, shot 1937. |
| Ніл Хасевич (G) | UPA visual artist (banknote designer), killed by MGB 1952. |
| Данило Щербаківський (C) | Ethnographer, suicide-protest 1927 over UAN museum purges. |

### J. Religious martyrs — UGCC + UAOC (11)

| Name | Mechanism |
|---|---|
| Василь Липківський (K) | UAOC Metropolitan, UAOC founder, shot 1937. |
| Микола Чарнецький ✓ | UGCC bishop, 11y camps, beatified martyr. |
| Василь Величковський ✓ (C) | UGCC bishop, redemptorist, beatified новомученик. |
| Йосафат Коциловський (G+C) | UGCC bishop of Peremyshl, died Soviet prison 1947. |
| Григорій Хомишин (G+C) | UGCC bishop of Stanislaviv, died Lubyanka 1945–47. |
| Микита Будка (C) | UGCC bishop, died Karaganda 1949. |
| Климентій Шептицький (C) | Andrey Шептицький's brother, UGCC, died Vladimir prison 1951. |
| Іван Зятик (C) | UGCC Redemptorist, died camp 1952. |
| Зиновій Ковалик (C) | UGCC Redemptorist, executed 1941. |
| Теодор Ромжа (G) | Mukachevo eparch, assassinated by MGB 1947. |
| Петро Вергун (C) | UGCC apostolic visitator, died camp 1957. |

### K. Crimean-Tatar Ukrainian patriots, RF-oppressed (2)

| Name | Mechanism |
|---|---|
| Мустафа Джемілєв (C) | Lifelong Crimean Tatar leader, 15y Soviet camps, RF-banned. |
| Наріман Джелял (C) | Mejlis deputy, RF-jailed since 2021. |

⚠️ **Follow-up audit needed**: zero Crimean-Tatar figures currently in bio. With Джемілєв + Джелял in, the next pass should cover Crimean-Tatar artists, writers, and historical figures separately. File as a sibling issue.

---

## Removed from preliminary draft (reviewer consensus)

1. **Тимко Бойчук** — died of TB 1922, not repression. Replaced by Падалка + Седляр + Налепинська-Бойчук.
2. **Георгій Гонгадзе** — murder mechanism was Kuchma-era domestic Ukrainian state, not Russia-specific. Out of scope.
3. **Мирослав-Іван Любачівський** — exile/survival, not martyr. Replaced by Теодор Ромжа.
4. **Богдан Лепкий** — Polish/Austrian context primary; weak Russia-oppression fit.
5. **Андрій Малишко, Левко Ревуцький** — too integrated into Soviet establishment.
6. **Олекса Новаківський, Олена Кульчицька** — Habsburg/Polish-era primarily; weak Russia-oppression fit.

## Flagged for user-by-user decision (3)

| Name | Issue | Reviewer recommendation |
|---|---|---|
| Аркадій Любченко | VAPLITE secretary, but 1941–44 occupation-era publication record | Include only with explicit honest framing of WWII occupation context |
| Улас Самчук | «Волинь» trilogy is great UA prose, but newspaper editorship under German occupation | Same — include with content warning |
| Кирило Стеценко | Composer (UNR-era choral music), but direct oppression mechanism is thin | Lean keep on cultural-significance grounds; alternative is to absorb into a UNR-era-composers seminar |

---

## Content-warning framework (politically-charged bios)

**User decision:** encode per-bio in YAML front-matter.

### Schema addition for `plans/bio/*.yaml`

```yaml
content_warning:
  level: HIGH | MED | normal
  required_framing:
    - "anti-imperial-resistance"        # primary frame
    - "specific-russian-persecution"    # what Russia specifically did
    - "contested-ideology"              # acknowledge OUN's interwar fascist-adjacent ideology where applicable
    - "civilian-harm-record"            # Volhynia 1943 etc. not erased
    - "polish-jewish-perspectives"      # referenced honestly
    - "multiple-ukrainian-views"        # not single hagiographic memory
    - "no-hagiography"                  # pedagogical posture
  applies_to_modules: [bio-N]
  reference: docs/best-practices/politically-charged-bios.md  # NEW DOC — write this alongside Bandera bio
```

### Bios that get `content_warning` (initial set)

**HIGH:** Бандера, Стецько, Клячківський.
**MED:** Мельник, Ребет, Федун-Полтава, Драч (post-Soviet political evolution), Шухевич (already in bio — retrofit), Донцов (already in bio — retrofit), Петлюра (already in bio — retrofit, lighter touch).

⚠️ **Retrofit task:** the framework must be applied retroactively to the 4 already-in-bio politically-charged figures (Шухевич, Донцов, Петлюра, Коновалець). File as a sibling cleanup.

---

## Build order recommendation

Priority tiers for writing the 88 bios. Build top-down. Each tier is ~20–25 modules; spread across 3 dispatch batches per tier (avoid #M-9 fan-out cap).

**Tier 1a — Розстріляне Відродження + survived-but-broken (core Soviet-purge narrative):**
- Block A (12 Розстріляне Відродження additions)
- Block D (8 survived/censored + returnees) — Тичина, Рильський, Сосюра, Яновський, Вишня, Бажан, Тулуб, Ковінька
- Total: 20

**Tier 1b — Émigré tradition (Празька → МУР → NY Group → scholars):**
- Block C (24) — single coherent unit; Маланюк/Барка/Клен/Домонтович/Гуменна as flagship names
- Best dispatched as 4 sub-batches: Празька (6), МУР (6), NY Group (5), scholars (3), plus the 4 first-wave individuals already in
- Total: 24

**Tier 2 — Imperial era + scholars + artists + religious + Crimean Tatar:**
- Block B (5 imperial-era, incl. Манжура)
- Block H (4 scholars/scientists)
- Block I (8 visual+composer)
- Block J (11 religious martyrs)
- Block K (2 Crimean Tatar)
- Total: 30

**Tier 3 — шістдесятники deep dive:**
- Block E (32 dissidents + artists + theater)

**Tier 4 — Politically charged (require content-warning framework + best-practices doc shipped FIRST):**
- Block G (9 OUN/UPA/UNR military) — block Tier 4 on writing `docs/best-practices/politically-charged-bios.md` first
- Includes retrofit pass on 4 existing bios

**Tier 5 — War-killed (process item, continuous):**
- Block F (12 post-2014 victims; ongoing curation thereafter)

---

## Sibling issues to file

1. **`scripts/audit/bio_lit_cross_reference.py`** — every author in `plans/lit/*.yaml` must have a `plans/bio/*.yaml` or sit on documented exclusion list. Prevents this category of gap recurring.
2. **`docs/best-practices/track-architecture.md`** — document the bio inclusion criterion explicitly.
3. **`docs/best-practices/politically-charged-bios.md`** — write the 7-point framing rule + retrofit checklist. BLOCKING for Tier 4.
4. **Crimean-Tatar bio coverage audit** — sibling pass; currently zero CT figures in bio beyond the 2 added here.
5. **War-killed continuous-curation process** — quarterly intake from PEN Ukraine + Ukrainian Institute lists.

---

## Reviewer credits

- **Gemini-3.1-pro-preview** — canon completeness, school-textbook cross-check, removal recommendations (Лепкий, Любачівський, Тимко Бойчук, Гонгадзе scope-correction).
- **Codex** — adversarial depth, ~50 additional names (Розстріляне Відродження inner cohort, Helsinki Group full roster, RF-era war-killed list, UGCC martyrology depth), reclassification proposals, factual fixes (Драй-Хмара died Kolyma not shot, Свідзінський mechanism = burned in barn during retreat not standard execution, Чарнецький died-from-effects not shot).
- **Claude (orchestrator)** — initial proposal, scope rule clarification, three-way synthesis, build-order prioritization.

Source briefs and raw responses: `/tmp/bio-gap-review/` (brief.md, gemini-response.md, codex-response in message #1085).

---

## Status

- ✅ List finalized at **127** (4th-pass total).
- ⏳ Awaiting user sign-off to begin Tier 1a writing.
- ⏳ Sibling issues 1–5 not yet filed.

## Audit history

- **2026-05-26 1st pass:** Claude consolidated 88 names from 3-way review (Claude + Gemini + Codex).
- **2026-05-26 2nd pass:** User flagged Рильський missing; re-checked Codex's full original ADD list against the consolidated file; recovered 6 dropped names (5 from Codex's lists, 1 from chain-of-prompting). Total 94.
- **2026-05-26 3rd pass:** User asked "we have those textbooks in RAG no? why OCR?" — switched from grep-on-OCR to `mcp__sources__search_text`. RAG sweep surfaced the entire missed émigré-literature tradition: Празька школа (6), МУР/DP-Munich (6), Нью-Йоркська група (5), diaspora institution-scholars (3), plus Бажан/Тулуб/Ковінька (capitulator/returnee pattern), Танюк/Зарецький/Кушнір (шістдесятники visual/theater), Манжура (imperial-era censorship). Total 121 + Величковський/Афанасьєв/Гурняк/Бабіч/Козловський retro-recovered = 127.
- **2026-05-26 4th pass:** Gemini textbook-mining background dispatch returned 86-author canonical roster from 6 grades (5–11). Result: VALIDATED the 127 against textbook canon; surfaced 4 minor candidates for further consideration (Воропай, Королів-Старий, Турянський, Глібов) and confirmed Гаспринський + Умеров belong in the planned Crimean-Tatar coverage sibling audit.

## Methodology lessons learned

1. **First pass missed the émigré tradition entirely.** The bio seed's "executable biography" filter excluded survivors-via-exile just as it excluded survivors-via-capitulation. Two structurally identical gaps.
2. **Compression without trace is a hallucination class.** When I trimmed Codex's 50+ names to "what I thought was canonical," I silently dropped 6 names. The fix: every dropped name needs a documented reason, not a vibe-based cut.
3. **OCR-on-PDF should never be the primary tool when a RAG corpus exists.** ~30 min of grep-on-shredded-OCR yielded 4 author names; one `search_text` query yielded 26 in a single sweep. Memory rule update candidate: prefer indexed RAG over file-system grep on any corpus we have ingested.
