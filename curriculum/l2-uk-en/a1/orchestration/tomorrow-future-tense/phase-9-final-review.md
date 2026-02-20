Now I have everything I need for a thorough adversarial review. Let me compile the findings.

---

## Phase 9: Final QA Review — tomorrow-future-tense

### Issues Found

#### CRITICAL: IPA — [e] systematically used for Ukrainian и (should be [ɪ])

Ukrainian и = [ɪ] (near-close near-front vowel). Ukrainian е = [e]. Using [e] for и would make a learner pronounce "четати" instead of "читати".

1. **Line 17**: `[ja t͡ʃeˈtɑlɑ]` for "читала" — should be `[ja t͡ʃɪˈtɑlɑ]`
2. **Line 44**: `[t͡ʃeˈtɑtɪ]` for "читати" — should be `[t͡ʃɪˈtɑtɪ]`
3. **Line 71**: `[ʋidpɔt͡ʃeˈʋɑtɪ]` for "відпочивати" — should be `[ʋidpɔt͡ʃɪˈʋɑtɪ]`

#### CRITICAL: Synthetic perfective future forms used in content that explicitly excludes them

The SCOPE comment says "Not covered: Synthetic future forms (-му, -меш) → A2 / Perfective future (прочитаю) → A2". Yet four sentences use exactly these forms without explanation:

1. **Line 169**: `побачимося` — perfective synthetic future of побачитися
2. **Line 180**: `зателефоную` — perfective synthetic future of зателефонувати
3. **Line 181**: `поговоримо` — perfective synthetic future of поговорити
4. **Line 275**: `замовлю` — perfective synthetic future of замовити

A learner who just learned "only use буду + infinitive" will be confused by forms that violate the rule they just memorized.

#### MODERATE: Reflexive verb conjugation — bolding error (line 104)

Current: `(збираю**ся**, збирає**шся**, збираєть**ся**)`

Problems:
- 2nd form "збирає**шся**" — bolding "шся" wrongly includes the personal ending "ш" as part of the reflexive marker
- 3rd form "збираєть**ся**" — misleading morpheme boundary (should show -ться as the 3rd person reflexive suffix)

Correct: `(збираю**ся**, збираєш**ся**, збирає**ться**)` — consistently showing -ся for 1st/2nd person, -ться for 3rd person.

#### MODERATE: LLM artifacts

1. **Line 27**: "Voila!" — French exclamation in a Ukrainian textbook
2. **Line 38**: "Here is your golden key to the future" — grandiose
3. **Line 134**: "### Magic of the word 'Next'" — AI pattern header
4. **Line 293**: "Now you are masters of time" — purple prose
5. **Line 299**: "Magic time words" — repeats "magic" pattern

#### MODERATE: Excessive metalanguage for A1 (lines 135–140)

Using grammar terms "Genitive of Time", "Nominative", "Genitive" with labels is too abstract for A1. The same concept can be taught as a pattern ("when saying *when*, change the ending to -ого") without the linguistic terminology.

#### MODERATE: IPA stress on вихідні (line 204)

`[ʋɪxidˈnʲi]` places stress on the final syllable. Вихідні has stress on the second syllable: [ʋɪˈxidnʲi].

#### MINOR: Activity uses out-of-scope synthetic future (activities line 287)

`'Це станеться ___ тижня.'` — "станеться" is perfective synthetic future, out of scope. Learner fills in "наступного" but encounters an unexplained verb form.

#### MINOR: Plan compliance gap — missing collocations

Plan requires "завтра вранці, завтра ввечері" collocations. Neither appears in the content. Noting for awareness; not fixing in QA gate.

#### MINOR: Plan compliance gap — missing synthetic future FYI

Plan says "Синтетичний майбутній (-му, -меш, -ме) — згадка — limit to brief FYI". Neither meta nor content includes this. Plan→meta gap.

#### CLEAN: No Russianisms, no Russian characters, no calques, cultural claims accurate, unjumble words/answers aligned, fill-in answers grammatical.

---

Now applying fixes:

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
**я читала** [ja t͡ʃeˈtɑlɑ] (I read)
---NEW---
**я читала** [ja t͡ʃɪˈtɑlɑ] (I read)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
the verb **читати** [t͡ʃeˈtɑtɪ] (to read):
---NEW---
the verb **читати** [t͡ʃɪˈtɑtɪ] (to read):
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
**Вони будуть відпочивати** [ʋidpɔt͡ʃeˈʋɑtɪ].
---NEW---
**Вони будуть відпочивати** [ʋidpɔt͡ʃɪˈʋɑtɪ].
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
You simply add it to the word you already know. Voila! You are speaking about the future.
---NEW---
You simply add it to the word you already know — and just like that, you are speaking about the future.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
Here is your golden key to the future:
---NEW---
Here is the formula:
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
(збираю**ся**, збирає**шся**, збираєть**ся**)
---NEW---
(збираю**ся**, збираєш**ся**, збирає**ться**)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
### Magic of the word "Next"
---NEW---
### The Word "Next" (Наступний)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
How do we say "next week" or "next year"? We use the word **наступний** [nɑˈstupnɪi̯] (next). But here is a small secret. When we say *when exactly* something happens, we change the ending. This is called **Genitive of Time**.

Look at this change:

*   Наступн**ий** тиждень (Nominative: Next week is coming) → **НаступнОГО тижня** (Genitive: **On** next week / Next week something happens).
*   Наступн**ий** рік (Nominative: Next year is good) → **НаступнОГО року** (Genitive: **In** the next year).
---NEW---
How do we say "next week" or "next year"? We use the word **наступний** [nɑˈstupnɪi̯] (next). But here is an important trick. When we say *when exactly* something happens, we change the ending to **-ого**.

Look at this pattern:

*   Наступн**ий** тиждень (Next week — as a thing) → **НаступнОГО тижня** (Next week — as a *time*, when something happens).
*   Наступн**ий** рік (Next year — as a thing) → **НаступнОГО року** (Next year — as a *time*).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
*   Ми **незабаром** побачимося. (We will see each other soon.)
---NEW---
*   Ми **незабаром** будемо разом. (We will be together soon.)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
*   Я зателефоную **пізніше**. (I will call later.)
*   Ми поговоримо **потім**. (We will talk then.)
---NEW---
*   Я буду телефонувати **пізніше**. (I will call later.)
*   Ми будемо говорити **потім**. (We will talk then.)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
**вихідні** [ʋɪxidˈnʲi]
---NEW---
**вихідні** [ʋɪˈxidnʲi]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
Потім я **буду снідати** [sʲnʲidɑtɪ] в кафе. Я замовлю каву і круасан.
---NEW---
Потім я **буду снідати** [sʲnʲidɑtɪ] в кафе. Я буду пити каву і їсти круасан.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
Вітаємо! Congratulations! Now you are masters of time. You can not only tell about what was, but also create a picture of what will be. The future is in your hands (and on your tongue!).
---NEW---
Вітаємо! Congratulations! Now you can speak about the past *and* the future. You are building sentences in three tenses — and that is a real achievement.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
4.  Magic time words: **завтра**, **скоро**, **наступного тижня**.
---NEW---
4.  Time words: **завтра**, **скоро**, **наступного тижня**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/tomorrow-future-tense.yaml
---OLD---
    - sentence: 'Це станеться ___ тижня.'
      answer: 'наступного'
      options: ['наступного', 'наступний', 'наступна', 'наступні']
---NEW---
    - sentence: 'Це буде ___ тижня.'
      answer: 'наступного'
      options: ['наступного', 'наступний', 'наступна', 'наступні']
===FIX_END===

---

### Remaining Issues (not fixed, noted for awareness)

1. **Plan compliance**: Missing "завтра вранці, завтра ввечері" collocations and "у понеділок, у січні" time expressions from plan. These are plan→meta gaps — the meta doesn't request them either, so the builder followed meta correctly.

2. **Plan compliance**: Missing synthetic future (-му, -меш) brief FYI mention. Plan requests it, meta omits it. Requires meta fix, not content fix.

3. **Perfective verbs with хочу/збиратися**: Lines 89, 212, 241, 256, 265 use perfective infinitives (поїхати, купити, піти) with хочу/збиратися. This is grammatically correct Ukrainian — perfective after хочу is natural. However, since the learner hasn't been taught aspect at all, encountering both verb types without explanation adds cognitive load. Not fixing because: (a) it's natural Ukrainian, (b) the warning is specifically about буду + perfective, (c) replacing all perfective verbs would make dialogue examples unnatural.

4. **Vocabulary YAML format**: Uses `items:` dictionary wrapper instead of bare list (compare with this-is-i-am.yaml which uses bare list). Audit passes, so parser handles both formats. Not fixing to avoid breaking parsing.

===VERDICT===
APPROVE
===END_VERDICT===