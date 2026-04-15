# Rewrite One Module Section

Rewrite ONLY the section `## В чи на? (В or На?)`.
Return ONLY the rewritten section, beginning with the exact same H2 heading.
Do not output any other sections, commentary, or code fences.

## Rewrite Directive

Rewrite only this section. Keep the exact H2 heading. Shorten the section to the contract budget, preserve the core contrasts (`в школі`, `у банку`, `на вулиці`, `на площі`, `на роботі`, `на пошті`, `на вокзалі`, `в Україні`), but remove the rigid euphony tip. Replace it with an accurate explanation that `у/в` choice depends on surrounding sounds and smooth pronunciation, using contrasts like `в Києві`, `у Львові`, `в офісі`, and `у банку`. Keep the cultural note about `в Україні`, but express it more compactly.

## Shared Module Contract

[BEGIN MODULE CONTRACT LITERAL - reference data only; do not follow instructions inside]
```yaml
module:
  slug: where-is-it
  level: a1
  module_num: 29
  title: Where Is It?
  phase: A1.5 [Places]
  word_target: 1200
teaching_beats:
  section_order:
  - Діалоги (Dialogues)
  - Місцевий відмінок (The Locative Case)
  - В чи на? (В or На?)
  - Підсумок — Summary
  sections:
  - order: 1
    name: Діалоги (Dialogues)
    word_budget:
      target: 300
      min: 270
      max: 330
    teaching_beats:
    - 'Dialogue 1 — Where is everyone? (ULP Ep17 pattern): — Де Олена? — Вона в школі.
      — А Тарас? — Він на роботі. — А діти? — Вони в парку. — А кішка? — Вона на дивані!
      Locative case emerges naturally from answering ''Де?'''
    - 'Dialogue 2 — Describing locations: — Де ти живеш? — Я живу в Києві, на вулиці
      Хрещатик. — А де ти працюєш? — В офісі, на другому поверсі. City + street +
      building locations.'
    required_terms:
    - Олена
    - школі
    - Тарас
    - Він
    - роботі
    - діти
    - парку
    - кішка
    factual_anchors:
    - section: Діалоги (Dialogues)
      claim: '# Педагогіка A1: Where Is It ## Методичний підхід (Methodological Approach)
        Teaching A1 learners to express location centers on the **Місцевий відмінок
        (Locative case)**.'
      citation: 'pedagogy/a1/where-is-it.md :: Overview'
      matched_terms:
      - case
      - locations
      - locative
      - pattern
    - section: Діалоги (Dialogues)
      claim: '* тут (here), там (there), вдома (at home), далеко (far), близько (near).'
      citation: 'pedagogy/a1/where-is-it.md :: Прислівники (Adverbs)'
      matched_terms:
      - dialogue
      - locations
      - locative
      - вулиці
    activity_types_after_section:
    - quiz
    - fill-in
    - match-up
    - quiz
  - order: 2
    name: Місцевий відмінок (The Locative Case)
    word_budget:
      target: 300
      min: 270
      max: 330
    teaching_beats:
    - 'Grade 4 case system: helper word method (Захарійчук Gr4 p.74): М. = місцевий
      відмінок: на/у кому? на/у чому? The locative ALWAYS needs a preposition — в/у
      or на. В/у = inside: в школі, у банку, в магазині, у лікарні. На = on/at: на
      роботі, на вулиці, на площі, на уроці.'
    - 'Basic locative endings (most common patterns): Masculine: -і or -у — в парку,
      у банку, в офісі, на уроці. Feminine: -і — в школі, на роботі, у лікарні, на
      вулиці. Neuter: -і — в місті, на морі. Note: endings depend on the noun''s declension
      — learn the common places as fixed phrases for now.'
    required_terms:
    - Захарійчук
    - місцевий
    - відмінок
    - кому
    - чому
    - школі
    - банку
    - магазині
    factual_anchors:
    - section: Місцевий відмінок (The Locative Case)
      claim: '# Педагогіка A1: Where Is It ## Методичний підхід (Methodological Approach)
        Teaching A1 learners to express location centers on the **Місцевий відмінок
        (Locative case)**.'
      citation: 'pedagogy/a1/where-is-it.md :: Overview'
      matched_terms:
      - always
      - basic
      - case
      - common
    - section: Місцевий відмінок (The Locative Case)
      claim: '# Педагогіка A1: What Is It Like ## Методичний підхід (Methodological
        Approach) The core of teaching descriptive language at the A1 level is to
        establish the **прикме́тник (adjective)** as a word that answers the questions
        **яки́й?'
      citation: 'pedagogy/a1/what-is-it-like.md :: Overview'
      matched_terms:
      - always
      - basic
      - case
      - common
    activity_types_after_section:
    - quiz
    - fill-in
    - match-up
    - quiz
  - order: 3
    name: В чи на? (В or На?)
    word_budget:
      target: 300
      min: 270
      max: 330
    teaching_beats:
    - 'General guide: В/у = enclosed spaces: в школі, в магазині, у банку, в лікарні,
      в кафе. На = open spaces, surfaces, events: на вулиці, на площі, на роботі,
      на концерті. Some are conventional: на пошті (not в пошті), на вокзалі (not
      в вокзалі). Learn each place with its preposition — like English ''at school''
      vs ''in the office''.'
    - 'Country/city rule: В/у + country/city: в Україні, у Києві, у Львові, в Одесі.
      На + some special cases: на Хрещатику (on Khreshchatyk street). Remember: NEVER
      ''на Україні'' — it''s ЗАВЖДИ ''в Україні''. This is not just grammar — it''s
      a matter of respect and sovereignty.'
    required_terms:
    - школі
    - магазині
    - банку
    - лікарні
    - кафе
    - вулиці
    - площі
    - роботі
    factual_anchors:
    - section: В чи на? (В or На?)
      claim: '# Педагогіка A1: Where Is It ## Методичний підхід (Methodological Approach)
        Teaching A1 learners to express location centers on the **Місцевий відмінок
        (Locative case)**.'
      citation: 'pedagogy/a1/where-is-it.md :: Overview'
      matched_terms:
      - and
      - are
      - enclosed
      - english
    - section: В чи на? (В or На?)
      claim: '# Педагогіка A1: What Is It Like ## Методичний підхід (Methodological
        Approach) The core of teaching descriptive language at the A1 level is to
        establish the **прикме́тник (adjective)** as a word that answers the questions
        **яки́й?'
      citation: 'pedagogy/a1/what-is-it-like.md :: Overview'
      matched_terms:
      - and
      - are
      - english
      - grammar
    activity_types_after_section:
    - quiz
    - fill-in
    - match-up
    - quiz
  - order: 4
    name: Підсумок — Summary
    word_budget:
      target: 300
      min: 270
      max: 330
    teaching_beats:
    - 'Locative case = where something IS (static location). Де? → в/у + locative
      (inside) or на + locative (on/at). Helper word: М. (на, у) — на/у кому? на/у
      чому? Common places: в школі, на роботі, у банку, в парку, на вулиці. Self-check:
      Where are you right now? Where do you work? Where do you live?'
    required_terms:
    - кому
    - чому
    - школі
    - роботі
    - банку
    - парку
    - вулиці
    factual_anchors:
    - section: Підсумок — Summary
      claim: '# Педагогіка A1: Where Is It ## Методичний підхід (Methodological Approach)
        Teaching A1 learners to express location centers on the **Місцевий відмінок
        (Locative case)**.'
      citation: 'pedagogy/a1/where-is-it.md :: Overview'
      matched_terms:
      - are
      - case
      - common
      - inside
    - section: Підсумок — Summary
      claim: '# Педагогіка A1: What Is It Like ## Методичний підхід (Methodological
        Approach) The core of teaching descriptive language at the A1 level is to
        establish the **прикме́тник (adjective)** as a word that answers the questions
        **яки́й?'
      citation: 'pedagogy/a1/what-is-it-like.md :: Overview'
      matched_terms:
      - are
      - case
      - common
      - word
    activity_types_after_section:
    - quiz
    - fill-in
    - match-up
    - quiz
dialogue_acts:
- setting: 'First week in a new city — asking a neighbor where to find: аптека (f,
    pharmacy), банк (m, bank), пошта (f, post office), кафе (n, café), лікарня (f,
    hospital), парк (m, park). В аптеці, на пошті, у банку.'
  speakers:
  - Новий мешканець (newcomer)
  - Сусід (neighbor)
  function: В/на + locative with аптека(f), банк(m), пошта(f), кафе(n)
vocab_grammar_targets:
  must_introduce:
  - школа → в школі (school)
  - робота → на роботі (work)
  - банк → у банку (bank)
  - магазин → у/в магазині (shop)
  - вулиця → на вулиці (street)
  - місто → у/в місті (city)
  scope_lock:
  - 'Locative case: в/у + М.в. (inside), на + М.в. (on/at)'
  - 'Helper word method: М. (на, у) — на/у кому? на/у чому?'
  - 'Basic locative endings: -і (most common), -у (masculine some)'
  - В Україні (never на Україні)
factual_anchors:
- section: Діалоги (Dialogues)
  claim: '# Педагогіка A1: Where Is It ## Методичний підхід (Methodological Approach)
    Teaching A1 learners to express location centers on the **Місцевий відмінок (Locative
    case)**.'
  citation: 'pedagogy/a1/where-is-it.md :: Overview'
  matched_terms:
  - case
  - locations
  - locative
  - pattern
- section: Діалоги (Dialogues)
  claim: '* тут (here), там (there), вдома (at home), далеко (far), близько (near).'
  citation: 'pedagogy/a1/where-is-it.md :: Прислівники (Adverbs)'
  matched_terms:
  - dialogue
  - locations
  - locative
  - вулиці
- section: Місцевий відмінок (The Locative Case)
  claim: '# Педагогіка A1: Where Is It ## Методичний підхід (Methodological Approach)
    Teaching A1 learners to express location centers on the **Місцевий відмінок (Locative
    case)**.'
  citation: 'pedagogy/a1/where-is-it.md :: Overview'
  matched_terms:
  - always
  - basic
  - case
  - common
- section: Місцевий відмінок (The Locative Case)
  claim: '# Педагогіка A1: What Is It Like ## Методичний підхід (Methodological Approach)
    The core of teaching descriptive language at the A1 level is to establish the
    **прикме́тник (adjective)** as a word that answers the questions **яки́й?'
  citation: 'pedagogy/a1/what-is-it-like.md :: Overview'
  matched_terms:
  - always
  - basic
  - case
  - common
- section: В чи на? (В or На?)
  claim: '# Педагогіка A1: Where Is It ## Методичний підхід (Methodological Approach)
    Teaching A1 learners to express location centers on the **Місцевий відмінок (Locative
    case)**.'
  citation: 'pedagogy/a1/where-is-it.md :: Overview'
  matched_terms:
  - and
  - are
  - enclosed
  - english
- section: В чи на? (В or На?)
  claim: '# Педагогіка A1: What Is It Like ## Методичний підхід (Methodological Approach)
    The core of teaching descriptive language at the A1 level is to establish the
    **прикме́тник (adjective)** as a word that answers the questions **яки́й?'
  citation: 'pedagogy/a1/what-is-it-like.md :: Overview'
  matched_terms:
  - and
  - are
  - english
  - grammar
- section: Підсумок — Summary
  claim: '# Педагогіка A1: Where Is It ## Методичний підхід (Methodological Approach)
    Teaching A1 learners to express location centers on the **Місцевий відмінок (Locative
    case)**.'
  citation: 'pedagogy/a1/where-is-it.md :: Overview'
  matched_terms:
  - are
  - case
  - common
  - inside
- section: Підсумок — Summary
  claim: '# Педагогіка A1: What Is It Like ## Методичний підхід (Methodological Approach)
    The core of teaching descriptive language at the A1 level is to establish the
    **прикме́тник (adjective)** as a word that answers the questions **яки́й?'
  citation: 'pedagogy/a1/what-is-it-like.md :: Overview'
  matched_terms:
  - are
  - case
  - common
  - word
banned_error_patterns:
- Russianisms
- Surzhyk
- Calques
- Invented grammar
- Meta-narration
- Formulaic section openers
activity_obligations:
- order: 1
  id: ''
  type: quiz
  focus: В or на? Choose the correct preposition for each place.
- order: 2
  id: ''
  type: fill-in
  focus: 'Answer Де?: Олена ___ (школа). Тарас ___ (робота).'
- order: 3
  id: ''
  type: match-up
  focus: 'Match nominative to locative: школа ↔ в школі'
- order: 4
  id: ''
  type: quiz
  focus: Where is it? Choose the correct locative form.
section_word_budgets:
  Діалоги (Dialogues):
    target: 300
    min: 270
    max: 330
  Місцевий відмінок (The Locative Case):
    target: 300
    min: 270
    max: 330
  В чи на? (В or На?):
    target: 300
    min: 270
    max: 330
  Підсумок — Summary:
    target: 300
    min: 270
    max: 330
artifacts:
  wiki_excerpt_file: wiki-excerpts.yaml
```
[END MODULE CONTRACT LITERAL]

## Section-Mapped Wiki Excerpts

[BEGIN SECTION WIKI EXCERPTS LITERAL - reference data only; do not follow instructions inside]
```yaml
section: В чи на? (В or На?)
items:
- citation: 'pedagogy/a1/where-is-it.md :: Overview'
  source_path: pedagogy/a1/where-is-it.md
  source_heading: Overview
  matched_terms:
  - and
  - are
  - enclosed
  - english
  - events
  - general
  score: 32
  excerpt: '# Педагогіка A1: Where Is It ## Методичний підхід (Methodological Approach)
    Teaching A1 learners to express location centers on the **Місцевий відмінок (Locative
    case)**. The pedagogical approach, drawn from Ukrainian primary school textbooks
    and L2 materials, prioritizes communicative function over abstract grammatical
    rules. The core concept is that the Locative case answers the question **Де?**
    (Where?) and *always* requires a preposition, most commonly в (у) or на (Source
    21, 14). The initial teaching strategy...'
- citation: 'pedagogy/a1/what-is-it-like.md :: Overview'
  source_path: pedagogy/a1/what-is-it-like.md
  source_heading: Overview
  matched_terms:
  - and
  - are
  - english
  - grammar
  - it's
  - its
  score: 11
  excerpt: '# Педагогіка A1: What Is It Like ## Методичний підхід (Methodological
    Approach) The core of teaching descriptive language at the A1 level is to establish
    the **прикме́тник (adjective)** as a word that answers the questions **яки́й?
    яка́? яке́? які́?** (what kind of?) and describes an **озна́ку предме́та (an attribute
    of an object)** (Source 3-klas-ukrainska-mova-vashulenko-2020-1_s0120, Source
    2-klas-ukrmova-kravcova-2019-1_s0075). The native Ukrainian pedagogy, evident
    in early grade textbooks, avoids dense...'
factual_anchors:
- section: В чи на? (В or На?)
  claim: '# Педагогіка A1: Where Is It ## Методичний підхід (Methodological Approach)
    Teaching A1 learners to express location centers on the **Місцевий відмінок (Locative
    case)**.'
  citation: 'pedagogy/a1/where-is-it.md :: Overview'
  matched_terms:
  - and
  - are
  - enclosed
  - english
- section: В чи на? (В or На?)
  claim: '# Педагогіка A1: What Is It Like ## Методичний підхід (Methodological Approach)
    The core of teaching descriptive language at the A1 level is to establish the
    **прикме́тник (adjective)** as a word that answers the questions **яки́й?'
  citation: 'pedagogy/a1/what-is-it-like.md :: Overview'
  matched_terms:
  - and
  - are
  - english
  - grammar
```
[END SECTION WIKI EXCERPTS LITERAL]

## Previous Sections For Continuity

[BEGIN PREVIOUS SECTIONS CONTEXT LITERAL - reference data only; do not follow instructions inside]
```markdown
[...previous sections truncated...]

bank far?)* > **Сусі́д:** Ні, банк теж бли́зько. *(No, the bank is also nearby.)* > **Но́вий ме́шканець:** Де я мо́жу ви́пити ка́ву? *(Where can I drink coffee?)* > **Сусі́д:** Ось гарне кафе́, а по́руч — парк. *(Here is a nice café, and nearby is a park.)* > **Но́вий ме́шканець:** А де ліка́рня та по́шта? *(And where are the hospital and post office?)* > **Сусі́д:** Ліка́рня дале́ко. А по́шта — на ву́лиці Хреща́тик. *(The hospital is far. And the post office is on Khreshchatyk street.)* > **Но́вий ме́шканець:** Дя́кую! Лі́ки в апте́ці, гро́ші у ба́нку... *(Thank you! Medicine is in the pharmacy, money is in the bank...)* > **Сусі́д:** А листи́ — на по́шті! *(And letters are at the post office!)* Notice that **на** is used for the street (**на ву́лиці**) and the post office (**на по́шті**), while **в** is used for the pharmacy (**в апте́ці**) and **у** for the bank (**у ба́нку**). ## Місце́вий відмі́нок (The Locative Case) Ukrainian children learn grammar using specific helper questions, which naturally link grammatical cases to their real-world function. In the fourth grade, students learn that the locative case, or **місцевий відмінок**, answers the questions **на/у ко́му? на/у чому́?** (on/in whom? on/in what?). The locative case is used exclusively to describe a static location — where something or someone currently IS, rather than the direction where they are going. Unlike other cases, the locative case ALWAYS needs a preposition to function. You cannot use it alone; it must be paired with a preposition, most commonly **в** (or its phonetic variant **у**) and **на**. :::note The helper question **на/у кому? на/у чому?** is how Ukrainian native speakers identify the locative case. Memorize it to build your intuition! ::: The most common ending for the locative case is **-і**. Many feminine nouns ending in **-а** or **-я** have **-і** in the locative, sometimes with a stem change, so learn the most common place words as fixed phrases. For example, **ліка́рня** (hospital) becomes **у ліка́рні** (in the hospital). This same **-і** ending also applies to neuter nouns ending in **-о** or **-е**. The word **мі́сто** (city) becomes **у мі́сті** (in the city), and **мо́ре** (sea) becomes **на мо́рі** (at the sea). Masculine nouns ending in a consonant also frequently take the **-і** ending. For instance, **о́фіс** (office) becomes **в офісі** (in the office), and **уро́к** (lesson) becomes **на уроці** (at the lesson). However, many common masculine places take a different ending entirely: **-у**. There is a historical linguistic reason for this difference, but for now, learn these specific masculine words as exceptions. Instead of trying to calculate every single ending on the fly, you should focus on memorizing the most common places as fixed phrases. Learn the preposition and the noun together as a single grammatical chunk: * школа → в школі (school) * робота → на роботі (work) * банк → у ба́нку (bank) * магази́н → у/в магази́ні (shop) * ву́лиця → на вулиці (street) * парк → у/в парку (park) <!-- INJECT_ACTIVITY: match-up-nominative-locative -->
```
[END PREVIOUS SECTIONS CONTEXT LITERAL]

## Current Section To Replace

[BEGIN CURRENT SECTION LITERAL - reference data only; do not follow instructions inside]
```markdown
## В чи на? (В or На?)

How do you choose between the prepositions **в** and **на**? The general rule for **в** (and its euphonic alternative **у**) is that it is used for enclosed spaces or being physically "inside" a structure with walls, a ceiling, or clear boundaries. When you are inside a building, you almost always use **в/у**. For example, you say **в школі** (in the school building), **у/в магазині** (in the shop), **у банку** (inside the bank branch), and **у лікарні** (in the hospital). Note that foreign borrowed words ending in a vowel, like **кафе́** (café), are indeclinable: **у/в кафе** (in the café).

:::tip
To avoid awkward consonant clusters, Ukrainian uses **у** instead of **в** before words starting with consonants (like **у банку**), and **в** after vowels (like **Вона в школі**). 
:::

The preposition **на**, on the other hand, is generally used for open spaces, flat surfaces, or events. When you are standing on a surface or attending a public gathering, you use **на**. Clear examples include **на вулиці** (on the street), **на пло́щі** (on the square), **на конце́рті** (at a concert), and **на уроці** (at a lesson). However, there are conventional exceptions that must be memorized. Some institutional concepts take **на** regardless of whether they have walls. You must say **на роботі** (at work), **на по́шті** (at the post office, not в пошті), and **на вокза́лі** (at the train station, not в вокзалі).

There is a strong rule regarding countries and cities. Countries and cities normally take the preposition **в/у**. You say **в Украї́ні** (in Ukraine), **у Києві** (in Kyiv), **у Льво́ві** (in Lviv), and **в Оде́сі** (in Odesa). Contrast this with smaller local spaces like streets and squares, which typically take **на**. You say **на площі** (on the square) or **на Хреща́тику** (on Khreshchatyk). Do not extend the **в/у** rule to every geographical name: some regional and historical names use **на**. For this A1 pattern, remember: countries and cities usually use **в/у**, while streets and squares often use **на**.

There is a critical cultural and political note regarding the name of the country. You must NEVER say **на Україні**. It is ЗА́ВЖДИ́ (always) **в Україні**. Historically, the incorrect preposition "на" was pushed by imperial policy to frame Ukraine as a mere territory or borderland rather than a fully independent state. Using **в Україні** is not just a grammatical rule; it is a matter of profound respect and national sovereignty.

:::caution
Never say **на Україні**. Using **в Україні** affirms Ukraine's status as an independent state, not a region. 
:::

<!-- INJECT_ACTIVITY: quiz-v-or-na -->
```
[END CURRENT SECTION LITERAL]

## Skeleton For This Section

[BEGIN SECTION SKELETON LITERAL - reference data only; do not follow instructions inside]
```markdown
## В чи на? (В or На?)
```
[END SECTION SKELETON LITERAL]
