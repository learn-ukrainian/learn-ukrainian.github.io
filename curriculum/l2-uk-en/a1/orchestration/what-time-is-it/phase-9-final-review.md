Good. Vocabulary files are definitively bare lists with IPA. Now I have all the evidence. Let me compile my adversarial review.

---

## Adversarial QA Review: what-time-is-it (a1-23)

### Issues Found

**Issue 1 (CRITICAL — Pedagogical Contradiction): "Третя десята" uses ordinal for minutes**

Location: `what-time-is-it.md` line 97

The module explicitly teaches the telegraphic format as `[Година (ordinal)] + [Хвилина (cardinal number)]`. All examples in "The Minutes" section follow this: **Десята двадцять**, **П'ята тридцять**, etc. But then line 97 says **Зараз третя десята.** — using the ordinal "десята" (tenth) for the minutes instead of cardinal "десять" (ten). This directly contradicts the rule taught two paragraphs earlier and would confuse learners, since "десята" also means "10 o'clock."

**Issue 2 (HIGH — IPA Error): Wrong stress on "вечеряти"**

Location: `what-time-is-it.md` line 295

Given: `` — stress on second syllable (чe).
Correct: `` — вечеря́ти has stress on -ря-.

**Issue 3 (HIGH — IPA Error): Wrong stress on "Укрзалізниця"**

Location: `what-time-is-it.md` line 20

Given: `` — stress on -ні-.
Correct: `` — Укрзалі́зниця (from залі́зниця) has stress on -лі-.

**Issue 4 (MEDIUM — Euphony Violation): "й їм" phonetic clash**

Location: `what-time-is-it.md` line 323

`Я п'ю каву й їм круасан.` — the combination `й їм` creates a [j]+[ji] clash. Standard euphony prefers `та` or `і` before `ї`.

**Issue 5 (MEDIUM — Inconsistency): Missing IPA for two time examples**

Location: `what-time-is-it.md` lines 85–86

The first four time examples have IPA transcriptions; the last two (`Одинадцята десять`, `Дванадцята п'ятдесят`) do not. Inconsistent for beginners needing pronunciation of longer numerals.

**Issue 6 (HIGH — Format Deviation): Vocabulary file uses `items:` wrapper instead of bare list**

Location: `vocabulary/what-time-is-it.yaml`

All other vocabulary files in the project use a bare list at root. This file wraps entries under `items:`, breaking format consistency. Additionally, all 20 entries are missing `ipa` fields (mandatory per project convention), and the file uses a non-standard `example` field instead of `notes`.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/what-time-is-it.md
---OLD---
**Укрзалізниця**
---NEW---
**Укрзалізниця**
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/what-time-is-it.md
---OLD---
*   11:10 — **Одинадцята десять**
*   12:50 — **Дванадцята п'ятдесят**
---NEW---
*   11:10 — **Одинадцята десять**
*   12:50 — **Дванадцята п'ятдесят**
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/what-time-is-it.md
---OLD---
*   **Зараз третя десята.** (It is 3:10 now.)
---NEW---
*   **Зараз третя десять.** (It is 3:10 now.)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/what-time-is-it.md
---OLD---
*   **вечеряти** — to have dinner
---NEW---
*   **вечеряти** — to have dinner
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/what-time-is-it.md
---OLD---
Я п'ю каву й їм круасан.
---NEW---
Я п'ю каву та їм круасан.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/what-time-is-it.yaml
---OLD---
items:
  - lemma: "година"
    translation: "hour"
    pos: "noun"
    gender: "f"
    example: "Котра година?"
  - lemma: "хвилина"
    translation: "minute"
    pos: "noun"
    gender: "f"
    example: "Зачекайте одну хвилину."
  - lemma: "день"
    translation: "day"
    pos: "noun"
    gender: "m"
    example: "Сьогодні гарний день."
  - lemma: "тиждень"
    translation: "week"
    pos: "noun"
    gender: "m"
    example: "Я працюю весь тиждень."
  - lemma: "місяць"
    translation: "month"
    pos: "noun"
    gender: "m"
    example: "У році дванадцять місяців."
  - lemma: "рік"
    translation: "year"
    pos: "noun"
    gender: "m"
    example: "З Новим роком!"
  - lemma: "ранок"
    translation: "morning"
    pos: "noun"
    gender: "m"
    example: "Доброго ранку."
  - lemma: "вечір"
    translation: "evening"
    pos: "noun"
    gender: "m"
    example: "Доброго вечора."
  - lemma: "зараз"
    translation: "now"
    pos: "adverb"
    example: "Я зараз зайнятий."
  - lemma: "о котрій"
    translation: "at what time"
    pos: "phrase"
    example: "О котрій ти прийдеш?"
  - lemma: "понеділок"
    translation: "Monday"
    pos: "noun"
    gender: "m"
  - lemma: "вівторок"
    translation: "Tuesday"
    pos: "noun"
    gender: "m"
  - lemma: "середа"
    translation: "Wednesday"
    pos: "noun"
    gender: "f"
  - lemma: "четвер"
    translation: "Thursday"
    pos: "noun"
    gender: "m"
  - lemma: "п'ятниця"
    translation: "Friday"
    pos: "noun"
    gender: "f"
  - lemma: "субота"
    translation: "Saturday"
    pos: "noun"
    gender: "f"
  - lemma: "неділя"
    translation: "Sunday"
    pos: "noun"
    gender: "f"
  - lemma: "сьогодні"
    translation: "today"
    pos: "adverb"
  - lemma: "завтра"
    translation: "tomorrow"
    pos: "adverb"
  - lemma: "пізно"
    translation: "late"
    pos: "adverb"
---NEW---
- ipa: ''
  lemma: година
  notes: f; Котра година? О першій годині
  pos: noun
  translation: hour
- ipa: ''
  lemma: хвилина
  notes: f; за п'ять хвилин, одна хвилина
  pos: noun
  translation: minute
- ipa: '[dɛnʲ]'
  lemma: день
  notes: m; добрий день, робочий день
  pos: noun
  translation: day
- ipa: ''
  lemma: тиждень
  notes: m; на цьому тижні (Loc), наступного тижня (Gen)
  pos: noun
  translation: week
- ipa: ''
  lemma: місяць
  notes: m; у цьому місяці (Loc)
  pos: noun
  translation: month
- ipa: '[rʲik]'
  lemma: рік
  notes: m; новий рік, цього року (Gen)
  pos: noun
  translation: year
- ipa: ''
  lemma: ранок
  notes: m; доброго ранку, о восьмій ранку
  pos: noun
  translation: morning
- ipa: ''
  lemma: вечір
  notes: m; добрий вечір, о сьомій вечора
  pos: noun
  translation: evening
- ipa: ''
  lemma: зараз
  notes: Зараз третя десять.
  pos: adverb
  translation: now
- ipa: ''
  lemma: о котрій
  notes: О котрій ти прийдеш?
  pos: phrase
  translation: at what time
- ipa: ''
  lemma: понеділок
  notes: m; у понеділок (Acc)
  pos: noun
  translation: Monday
- ipa: ''
  lemma: вівторок
  notes: m; у вівторок (Acc)
  pos: noun
  translation: Tuesday
- ipa: ''
  lemma: середа
  notes: f; у середу (Acc)
  pos: noun
  translation: Wednesday
- ipa: ''
  lemma: четвер
  notes: m; у четвер (Acc)
  pos: noun
  translation: Thursday
- ipa: ''
  lemma: п'ятниця
  notes: f; у п'ятницю (Acc)
  pos: noun
  translation: Friday
- ipa: ''
  lemma: субота
  notes: f; у суботу (Acc)
  pos: noun
  translation: Saturday
- ipa: ''
  lemma: неділя
  notes: f; у неділю (Acc)
  pos: noun
  translation: Sunday
- ipa: ''
  lemma: сьогодні
  pos: adverb
  translation: today
- ipa: ''
  lemma: завтра
  pos: adverb
  translation: tomorrow
- ipa: ''
  lemma: пізно
  pos: adverb
  translation: late
- ipa: ''
  lemma: вчасно
  notes: бути вчасно, прийти вчасно
  pos: adverb
  translation: on time
- ipa: ''
  lemma: рано
  notes: Ще рано.
  pos: adverb
  translation: early
===FIX_END===

---

### Summary

| # | Severity | Issue | Fixed? |
|---|----------|-------|--------|
| 1 | CRITICAL | "третя десята" — ordinal used for minutes, contradicts module's own cardinal rule | Yes |
| 2 | HIGH | IPA stress on "вечеряти" on wrong syllable (чe instead of ря) | Yes |
| 3 | HIGH | IPA stress on "Укрзалізниця" on wrong syllable (ні instead of лі) | Yes |
| 4 | MEDIUM | Euphony violation: "й їм" creates j+ji clash | Yes |
| 5 | MEDIUM | Missing IPA for two time examples (inconsistency) | Yes |
| 6 | HIGH | Vocabulary file: wrong format (`items:` wrapper), missing all IPA, non-standard fields | Yes |

**No Russianisms, no Russian characters, no factual errors, no broken activities detected.** All unjumble word arrays verified against their answers (all 24 items match). All fill-in answers produce grammatical sentences. Plan compliance is good — all content_outline sections present, all objectives mapped to self-check questions.

The module is strong overall. The critical find is Issue 1 — "третя десята" is a pedagogical trap that would teach learners to use ordinals for minutes, directly contradicting the module's own stated rule. After these fixes, the module is clean.

===VERDICT===
APPROVE
===END_VERDICT===