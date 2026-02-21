Now I have everything I need. Here is my deep adversarial review.

---

## Adversarial QA Review: taking-transport (a1-40)

### Issues Found

**ISSUE 1 — HIGH: Unjumble words arrays missing terminal punctuation**
File: `activities/taking-transport.yaml`, all 6 unjumble items (lines 177-188)

Every answer string includes terminal punctuation (`.` or `?`) but the words arrays do not include these tokens. The learner cannot reconstruct the answer from the available words.
- Item 1: answer `Я їду на роботу автобусом.` — no `.` in words
- Item 2: answer `Наступна станція — Університет.` — no `.` in words
- Item 3: answer `Мені треба зробити пересадку.` — no `.` in words
- Item 4: answer `Обережно, двері зараз зачиняються.` — no `.` in words
- Item 5: answer `Як доїхати до вокзалу?` — no `?` in words
- Item 6: answer `Не забудьте завалідувати квиток.` — no `.` in words

**ISSUE 2 — HIGH: Vocabulary file uses `items:` wrapper instead of bare list**
File: `vocabulary/taking-transport.yaml`, line 1

All other A1 vocabulary files (around-the-city, the-living-verb-i, the-gender-code, etc.) use bare list format. This file wraps entries in `items:`, which is non-standard for the project.

**ISSUE 3 — HIGH: Activity tests untaught word "Контролер"**
File: `activities/taking-transport.yaml`, lines 36-37

The match-up activity includes "Контролер" → "Людина, яка перевіряє квитки". However, "контролер" never appears in the lesson prose and is absent from the vocabulary file. The plan's vocabulary_hints do not list it. Testing a word never taught is a pedagogical trap for A1 learners.

**ISSUE 4 — MODERATE: Non-standard IPA notation for пересісти**
File: `taking-transport.md`, line 166

`[pɛrɛˈs⁽ʲ⁾istɪ]` — The superscript parenthetical `⁽ʲ⁾` is non-standard IPA. Should be `[pɛrɛˈsʲistɪ]` (с before і is unambiguously palatalized).

**ISSUE 5 — MODERATE: Heading hierarchy broken**
File: `taking-transport.md`, line 317

`# Підсумок` is H1, but all other content sections are H2. Only the module title (line 9, `# Taking Transport`) should be H1. This should be `## Підсумок`.

**ISSUE 6 — MODERATE: Missing recommended vocabulary entries**
File: `vocabulary/taking-transport.yaml`

The plan's `vocabulary_hints.recommended` includes "проїзд" (core social collocation) and "прокомпостувати" (with IPA requirement). Both are used heavily in the prose and activities but are absent from the vocabulary file. "Завалідувати" (the modern replacement taught in prose) is also absent.

**ISSUE 7 — MINOR: Quiz sentence "Вона вже швидко зайшла"**
File: `activities/taking-transport.yaml`, line 303

"Вже" and "швидко" together is stylistically clunky. "Вже" (already) implies completed action; "швидко" (quickly) is redundant alongside it in this context. Simplify to "Вона швидко зайшла."

**ISSUE 8 — MINOR: Unverifiable cultural claim (Mykola Petrenko)**
File: `taking-transport.md`, lines 130-132

The claim that Kyiv Metro announcements were voiced by "Mykola Petrenko" who "passed away in 2016" is unverifiable and may be LLM confabulation. The iconic metro voice is real, but the specific name/date cannot be confirmed. Recommend softening to avoid presenting uncertain facts.

**ISSUE 9 — MINOR: Match-up "де стає автобус"**
File: `activities/taking-transport.yaml`, line 27

"Місце, де стає автобус або тролейбус" — "стає" (stands/becomes) is less clear than "зупиняється" (stops) for A1 learners defining what a bus stop is.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/taking-transport.yaml
---OLD---
    - words: ['на', 'роботу', 'їду', 'автобусом', 'Я']
      answer: 'Я їду на роботу автобусом.'
    - words: ['Наступна', 'станція', '—', 'Університет']
      answer: 'Наступна станція — Університет.'
    - words: ['треба', 'пересадку', 'зробити', 'Мені']
      answer: 'Мені треба зробити пересадку.'
    - words: ['Обережно,', 'двері', 'зараз', 'зачиняються']
      answer: 'Обережно, двері зараз зачиняються.'
    - words: ['доїхати', 'Як', 'до', 'вокзалу']
      answer: 'Як доїхати до вокзалу?'
    - words: ['квиток', 'завалідувати', 'Не', 'забудьте']
      answer: 'Не забудьте завалідувати квиток.'
---NEW---
    - words: ['на', 'роботу', 'їду', 'автобусом', 'Я', '.']
      answer: 'Я їду на роботу автобусом.'
    - words: ['Наступна', 'станція', '—', 'Університет', '.']
      answer: 'Наступна станція — Університет.'
    - words: ['треба', 'пересадку', 'зробити', 'Мені', '.']
      answer: 'Мені треба зробити пересадку.'
    - words: ['Обережно,', 'двері', 'зараз', 'зачиняються', '.']
      answer: 'Обережно, двері зараз зачиняються.'
    - words: ['доїхати', 'Як', 'до', 'вокзалу', '?']
      answer: 'Як доїхати до вокзалу?'
    - words: ['квиток', 'завалідувати', 'Не', 'забудьте', '.']
      answer: 'Не забудьте завалідувати квиток.'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/taking-transport.yaml
---OLD---
    - left: 'Контролер'
      right: 'Людина, яка перевіряє квитки'
---NEW---
    - left: 'Пасажир'
      right: 'Людина, яка їде в транспорті'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/taking-transport.yaml
---OLD---
      right: 'Місце, де стає автобус або тролейбус'
---NEW---
      right: 'Місце, де зупиняється автобус або тролейбус'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/taking-transport.yaml
---OLD---
    - question: 'Вона вже швидко зайшла _____ (вагон).'
---NEW---
    - question: 'Вона швидко зайшла _____ (вагон).'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/taking-transport.md
---OLD---
**Пересісти на...** [pɛrɛˈs⁽ʲ⁾istɪ nɑ] — To change to... / To transfer to...
---NEW---
**Пересісти на...** [pɛrɛˈsʲistɪ nɑ] — To change to... / To transfer to...
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/taking-transport.md
---OLD---
# Підсумок
---NEW---
## Підсумок
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/taking-transport.md
---OLD---
> For decades, the announcements in the Kyiv Metro were voiced by Mykola Petrenko. His deep, calm, baritone voice became a symbol of Kyiv. Even during the most chaotic rush hour, his voice remained a calm constant. Although he passed away in 2016, his recordings are still legendary, though newer lines now feature different voices.
---NEW---
> For decades, the deep, calm baritone of the Kyiv Metro announcements became a symbol of the city. Even during the most chaotic rush hour, that voice remained a constant. The older recordings are still legendary, though newer lines now feature different voices.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/taking-transport.yaml
---OLD---
items:
  - lemma: 'зупинка'
    translation: 'stop (bus/tram)'
    pos: 'noun'
    gender: 'f'
    usage: 'автобусна зупинка'
  - lemma: 'метро'
    translation: 'metro / subway'
    pos: 'noun'
    gender: 'n'
    notes: 'indeclinable noun'
  - lemma: 'трамвай'
    translation: 'tram'
    pos: 'noun'
    gender: 'm'
  - lemma: 'тролейбус'
    translation: 'trolleybus'
    pos: 'noun'
    gender: 'm'
  - lemma: 'автобус'
    translation: 'bus'
    pos: 'noun'
    gender: 'm'
  - lemma: 'маршрутка'
    translation: 'minibus taxi'
    pos: 'noun'
    gender: 'f'
    notes: 'short for маршрутне таксі'
  - lemma: 'таксі'
    translation: 'taxi'
    pos: 'noun'
    gender: 'n'
    notes: 'indeclinable noun'
  - lemma: 'поїзд'
    translation: 'train'
    pos: 'noun'
    gender: 'm'
  - lemma: 'маршрут'
    translation: 'route'
    pos: 'noun'
    gender: 'm'
  - lemma: 'станція'
    translation: 'station (metro/train)'
    pos: 'noun'
    gender: 'f'
  - lemma: 'пересадка'
    translation: 'transfer'
    pos: 'noun'
    gender: 'f'
    usage: 'робити пересадку'
  - lemma: 'виходити'
    translation: 'to exit / get off'
    pos: 'verb'
    aspect: 'imp'
    usage: 'Ви виходите на наступній?'
  - lemma: 'заходити'
    translation: 'to enter / get on'
    pos: 'verb'
    aspect: 'imp'
  - lemma: 'їхати'
    translation: 'to go (by vehicle)'
    pos: 'verb'
    aspect: 'imp'
  - lemma: 'іти'
    translation: 'to go (on foot)'
    pos: 'verb'
    aspect: 'imp'
  - lemma: 'квиток'
    translation: 'ticket'
    pos: 'noun'
    gender: 'm'
  - lemma: 'проїзний'
    translation: 'travel pass'
    pos: 'noun'
    gender: 'm'
  - lemma: 'валідатор'
    translation: 'validator'
    pos: 'noun'
    gender: 'm'
  - lemma: 'водій'
    translation: 'driver'
    pos: 'noun'
    gender: 'm'
  - lemma: 'пасажир'
    translation: 'passenger'
    pos: 'noun'
    gender: 'm'
  - lemma: 'ескалатор'
    translation: 'escalator'
    pos: 'noun'
    gender: 'm'
  - lemma: 'вхід'
    translation: 'entrance'
    pos: 'noun'
    gender: 'm'
  - lemma: 'вихід'
    translation: 'exit'
    pos: 'noun'
    gender: 'm'
---NEW---
- lemma: 'зупинка'
  translation: 'stop (bus/tram)'
  pos: 'noun'
  gender: 'f'
  usage: 'автобусна зупинка'
- lemma: 'метро'
  translation: 'metro / subway'
  pos: 'noun'
  gender: 'n'
  notes: 'indeclinable noun'
- lemma: 'трамвай'
  translation: 'tram'
  pos: 'noun'
  gender: 'm'
- lemma: 'тролейбус'
  translation: 'trolleybus'
  pos: 'noun'
  gender: 'm'
- lemma: 'автобус'
  translation: 'bus'
  pos: 'noun'
  gender: 'm'
- lemma: 'маршрутка'
  translation: 'minibus taxi'
  pos: 'noun'
  gender: 'f'
  notes: 'short for маршрутне таксі'
- lemma: 'таксі'
  translation: 'taxi'
  pos: 'noun'
  gender: 'n'
  notes: 'indeclinable noun'
- lemma: 'поїзд'
  translation: 'train'
  pos: 'noun'
  gender: 'm'
- lemma: 'маршрут'
  translation: 'route'
  pos: 'noun'
  gender: 'm'
- lemma: 'станція'
  translation: 'station (metro/train)'
  pos: 'noun'
  gender: 'f'
- lemma: 'пересадка'
  translation: 'transfer'
  pos: 'noun'
  gender: 'f'
  usage: 'робити пересадку'
- lemma: 'проїзд'
  translation: 'fare / passage'
  pos: 'noun'
  gender: 'm'
  usage: 'передайте за проїзд'
- lemma: 'виходити'
  translation: 'to exit / get off'
  pos: 'verb'
  aspect: 'imp'
  usage: 'Ви виходите на наступній?'
- lemma: 'заходити'
  translation: 'to enter / get on'
  pos: 'verb'
  aspect: 'imp'
- lemma: 'їхати'
  translation: 'to go (by vehicle)'
  pos: 'verb'
  aspect: 'imp'
- lemma: 'іти'
  translation: 'to go (on foot)'
  pos: 'verb'
  aspect: 'imp'
- lemma: 'квиток'
  translation: 'ticket'
  pos: 'noun'
  gender: 'm'
- lemma: 'проїзний'
  translation: 'travel pass'
  pos: 'noun'
  gender: 'm'
- lemma: 'валідатор'
  translation: 'validator'
  pos: 'noun'
  gender: 'm'
- lemma: 'завалідувати'
  translation: 'to validate (ticket/payment)'
  pos: 'verb'
  aspect: 'perf'
  usage: 'завалідувати квиток'
- lemma: 'прокомпостувати'
  ipa: '[prɔkɔmpɔstuˈʋɑtɪ]'
  translation: 'to validate (old style, punch ticket)'
  pos: 'verb'
  aspect: 'perf'
  notes: 'legacy term; older generation usage'
- lemma: 'водій'
  translation: 'driver'
  pos: 'noun'
  gender: 'm'
- lemma: 'пасажир'
  translation: 'passenger'
  pos: 'noun'
  gender: 'm'
- lemma: 'ескалатор'
  translation: 'escalator'
  pos: 'noun'
  gender: 'm'
- lemma: 'вхід'
  translation: 'entrance'
  pos: 'noun'
  gender: 'm'
- lemma: 'вихід'
  translation: 'exit'
  pos: 'noun'
  gender: 'm'
===FIX_END===

---

## Review Summary

| Category | Finding |
|----------|---------|
| **Russianisms** | CLEAN — no кушати/получати/слідуючий found |
| **Russian characters** | CLEAN — no ы/э/ё/ъ |
| **IPA** | 1 fix (non-standard palatalization notation) |
| **Grammar/case agreement** | CLEAN in prose; all Ukrainian sentences verified |
| **Unjumble integrity** | 6/6 items missing terminal punctuation (FIXED) |
| **Fill-in grammar** | CLEAN — all answers produce grammatical sentences |
| **Activity-vocabulary alignment** | 1 untaught word in match-up (FIXED) |
| **Vocab file format** | Non-standard `items:` wrapper (FIXED to bare list) |
| **Plan compliance** | All 4 meta sections present; required vocabulary covered; 2 recommended vocab entries added |
| **Factual accuracy** | Arsenalna depth correct; Kyiv Digital correct; 1 unverifiable cultural claim softened |
| **LLM artifacts** | Minimal — no purple prose, no "tapestry of" patterns |
| **Heading structure** | H1/H2 inconsistency (FIXED) |

**Strengths**: The module is genuinely excellent — culturally rich marshrutka scenarios, clear іти/їхати distinction, well-scaffolded Locative/Accusative grammar. The Green Team's Issue 1 (contradiction about метро case) has already been resolved in the current text — both the warning box and the Instrumental section consistently teach "на метро." Activities are diverse (11 activity blocks, ~88 items total) and pedagogically sound.

**Post-fix assessment**: All high and moderate issues resolved. Remaining minor items (направо → праворуч is a project-wide pattern, not isolated here) are cosmetic.

===VERDICT===
APPROVE
===END_VERDICT===