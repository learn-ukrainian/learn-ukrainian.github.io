Now I have everything I need. Let me compile the full adversarial review.

---

## Phase 9: Final QA Review — tomorrow-future-tense

### Issues Found

**Issue 1: Vocabulary YAML — Wrong Root Structure**
- **File**: `vocabulary/tomorrow-future-tense.yaml`, line 1
- **Current**: File uses `items:` dictionary wrapper
- **Problem**: All other A1 vocabulary files (`the-living-verb-i.yaml`, `the-gender-code.yaml`, etc.) use a bare list at root. This file is structurally inconsistent. Scripts that expect bare-list format will break or need special-casing.
- **Fix**: Convert to bare list format matching project standard.

**Issue 2: IPA — вихідні wrong stress placement**
- **File**: `tomorrow-future-tense.md`, line 204
- **Current**: `[ʋɪˈxidnʲi]` (stress on second syllable)
- **Problem**: Standard stress is вихідні́ — final syllable. Correct IPA: `[ʋɪxidˈnʲi]`.

**Issue 3: IPA — збирається inconsistent affricate notation**
- **File**: `tomorrow-future-tense.md`, line 100
- **Current**: `[zbɪˈrɑjetʲsʲa]` — breaks `-ться` into separate `[tʲsʲ]`
- **Problem**: Module uses tie bars for all other affricates (t͡ʃ, t͡s). Ukrainian `-ться` is phonetically an affricate [t͡sʲː]. The transcription is internally inconsistent.
- **Fix**: `[zbɪˈrɑjet͡sʲːa]`

**Issue 4: IPA — спати missing stress marker**
- **File**: `tomorrow-future-tense.md`, line 275
- **Current**: `[spɑtɪ]`
- **Problem**: All other IPA transcriptions in the module include stress markers. This one is missing. Stress: спа́ти → `[ˈspɑtɪ]`.

**Issue 5: IPA — снідати missing stress marker**
- **File**: `tomorrow-future-tense.md`, line 275
- **Current**: `[sʲnʲidɑtɪ]`
- **Problem**: Missing stress marker. Stress: сніда́ти → `[sʲnʲiˈdɑtɪ]`.

**Issue 6: Pedagogical — Dialogue 2 uses untaught grammar (present-for-future)**
- **File**: `tomorrow-future-tense.md`, line 251
- **Current**: `«Так! **Наступного тижня** я їду додому, до батьків.»`
- **Problem**: Module teaches exclusively `буду + infinitive` as the future tense formula. Using `їду` (present tense with future meaning) is natural Ukrainian but untaught at this point. Breaks "Safe Harbor" — learners who just memorized the formula will be confused by an alternative they haven't been taught.
- **Fix**: Restructure to use compound future.

**Issue 7: Untranslated Ukrainian sentence at A1 level**
- **File**: `tomorrow-future-tense.md`, line 27
- **Current**: `Українська мова — це музика. Слухайте і говоріть.`
- **Problem**: An A1 learner at module 22 has not been taught imperative forms (слухайте, говоріть). This sentence appears without any English translation, violating the module's own scaffolding pattern.

**Issue 8: Truncated proverb — plan compliance gap**
- **File**: `tomorrow-future-tense.md`, line 110
- **Current**: `"Don't say 'hop'!" («Не кажи 'гоп'!»)`
- **Problem**: The plan requires the full proverb: «Не кажи 'гоп', поки не перескочиш». Truncating it loses the meaning. The cultural hook is weaker without the punchline.

**Issue 9: Naturalness — "друзі будуть дзвонити"**
- **File**: `tomorrow-future-tense.md`, line 279
- **Current**: `Увечері мої друзі **будуть дзвонити**.`
- **Problem**: "Будуть дзвонити" emphasizes the ongoing process of ringing/calling, which reads oddly as a lead-in to "ми будемо вечеряти разом". The narrative flow (friends calling → dinner together) is disjointed.
- **Fix**: `Увечері я **буду** з друзями.` — cleaner, stays within taught grammar.

**Issue 10: Activity — "листа" uses untaught Genitive case**
- **File**: `activities/tomorrow-future-tense.yaml`, line 42
- **Current**: `'Ви ___ писати листа?'`
- **Problem**: "Лист" (letter) is masculine inanimate — Accusative = Nominative = "лист". "Листа" is Genitive form. While "писати листа" (Genitive object) exists in Ukrainian, this module teaches Genitive only for time expressions (наступного тижня). Using Genitive for direct objects introduces an untaught pattern. Safer: "лист" (Accusative).

**Informational (no fix needed):**
- Plan calls for a synthetic future FYI mention (працюватиму) which is absent. The meta explicitly defers this to A2. Module follows meta correctly — this is a plan/meta discrepancy, not a content deficiency.
- Three items in the "Наступного" fill-in activity use present-for-future verbs (їдемо, працюємо, їду). These are vocabulary drills testing case form only, not tense. Acceptable simplification at A1.
- "Потім" in group-sort classified as "Future" — it can also appear in past sequences, but this simplification is pedagogically justified for the lesson context.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
You need only one small helper word — **буду** [ˈbudu] (I will be). You simply add it to the word you already know — and just like that, you are speaking about the future. Українська мова — це музика. Слухайте і говоріть.
---NEW---
You need only one small helper word — **буду** [ˈbudu] (I will be). You simply add it to the word you already know — and just like that, you are speaking about the future. Українська мова — це музика. Слухайте і говоріть. (The Ukrainian language is music. Listen and speak.)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
*   Він **збирається** [zbɪˈrɑjetʲsʲa] працювати. (He is going to work.)
---NEW---
*   Він **збирається** [zbɪˈrɑjet͡sʲːa] працювати. (He is going to work.)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
> In Ukrainian culture, people often speak carefully about big plans. There is a famous proverb about not boasting about success until the job is done. Ukrainians say: "Don't say 'hop'!" («Не кажи 'гоп'!»). So Ukrainians might say "I plan..." or "I hope..." instead of a firm "I will do!".
---NEW---
> In Ukrainian culture, people often speak carefully about big plans. There is a famous proverb about not boasting about success until the job is done. Ukrainians say: «Не кажи 'гоп', поки не перескочиш!» — "Don't say 'hop' until you've jumped over!" In other words, do not celebrate before you finish. So Ukrainians might say "I plan..." or "I hope..." instead of a firm "I will do!".
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
*   **вихідні** [ʋɪˈxidnʲi] — weekend (literally: exit days)
---NEW---
*   **вихідні** [ʋɪxidˈnʲi] — weekend (literally: exit days)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
**Ірина:** Так! **Наступного тижня** я їду додому, до батьків.
---NEW---
**Ірина:** Так! **Наступного тижня** я **буду** вдома, у батьків.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
*Зауважте (Note):* Maksym uses "буду працювати" because it is a long process. Iryna uses "будемо гуляти" to describe how they will spend time.
---NEW---
*Зауважте (Note):* Maksym uses "буду працювати" because it is a long process. Iryna uses "буду вдома" to describe where she will be, and "будемо гуляти" to describe how they will spend time.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
Завтра буде чудовий день. Вранці я **буду спати** [spɑtɪ] довго. Потім я **буду снідати** [sʲnʲidɑtɪ] в кафе.
---NEW---
Завтра буде чудовий день. Вранці я **буду спати** [ˈspɑtɪ] довго. Потім я **буду снідати** [sʲnʲiˈdɑtɪ] в кафе.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/tomorrow-future-tense.md
---OLD---
Увечері мої друзі **будуть дзвонити**. Ми **будемо вечеряти** разом у ресторані.
---NEW---
Увечері я **буду** з друзями. Ми **будемо вечеряти** разом у ресторані.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/tomorrow-future-tense.yaml
---OLD---
    - sentence: 'Ви ___ писати листа?'
---NEW---
    - sentence: 'Ви ___ писати лист?'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/tomorrow-future-tense.yaml
---OLD---
items:
  - lemma: 'завтра'
    translation: 'tomorrow'
    pos: 'adverb'
    example: 'Завтра я буду вдома.'
  - lemma: 'післязавтра'
    translation: 'the day after tomorrow'
    pos: 'adverb'
  - lemma: 'буду'
    translation: 'I will'
    pos: 'verb'
    notes: 'Future form of "бути" for "I" (Я)'
  - lemma: 'бути'
    translation: 'to be'
    pos: 'verb'
  - lemma: 'наступний'
    translation: 'next'
    pos: 'adjective'
    example: 'Наступного тижня.'
  - lemma: 'план'
    translation: 'plan'
    pos: 'noun'
    gender: 'm'
  - lemma: 'хотіти'
    translation: 'to want'
    pos: 'verb'
    usage: 'Я хочу + infinitive'
  - lemma: 'збиратися'
    translation: 'to be going to / to intend'
    pos: 'verb'
    notes: 'Reflexive verb'
  - lemma: 'незабаром'
    translation: 'soon / before long'
    pos: 'adverb'
  - lemma: 'скоро'
    translation: 'soon'
    pos: 'adverb'
  - lemma: 'потім'
    translation: 'then / afterwards'
    pos: 'adverb'
  - lemma: 'пізніше'
    translation: 'later'
    pos: 'adverb'
  - lemma: 'тиждень'
    translation: 'week'
    pos: 'noun'
    gender: 'm'
  - lemma: 'рік'
    translation: 'year'
    pos: 'noun'
    gender: 'm'
  - lemma: 'сподіватися'
    translation: 'to hope'
    pos: 'verb'
  - lemma: 'мріяти'
    translation: 'to dream'
    pos: 'verb'
  - lemma: 'планувати'
    translation: 'to plan'
    pos: 'verb'
  - lemma: 'обіцяти'
    translation: 'to promise'
    pos: 'verb'
  - lemma: 'вихідні'
    translation: 'weekend'
    pos: 'noun'
    notes: 'Plural only'
  - lemma: 'відпустка'
    translation: 'vacation / leave'
    pos: 'noun'
    gender: 'f'
  - lemma: 'канікули'
    translation: 'holidays / break'
    pos: 'noun'
    notes: 'Plural only (school/university)'
---NEW---
- lemma: 'завтра'
  translation: 'tomorrow'
  pos: 'adverb'
  example: 'Завтра я буду вдома.'
- lemma: 'післязавтра'
  translation: 'the day after tomorrow'
  pos: 'adverb'
- lemma: 'буду'
  translation: 'I will'
  pos: 'verb'
  notes: 'Future form of "бути" for "I" (Я)'
- lemma: 'бути'
  translation: 'to be'
  pos: 'verb'
- lemma: 'наступний'
  translation: 'next'
  pos: 'adjective'
  example: 'Наступного тижня.'
- lemma: 'план'
  translation: 'plan'
  pos: 'noun'
  gender: 'm'
- lemma: 'хотіти'
  translation: 'to want'
  pos: 'verb'
  usage: 'Я хочу + infinitive'
- lemma: 'збиратися'
  translation: 'to be going to / to intend'
  pos: 'verb'
  notes: 'Reflexive verb'
- lemma: 'незабаром'
  translation: 'soon / before long'
  pos: 'adverb'
- lemma: 'скоро'
  translation: 'soon'
  pos: 'adverb'
- lemma: 'потім'
  translation: 'then / afterwards'
  pos: 'adverb'
- lemma: 'пізніше'
  translation: 'later'
  pos: 'adverb'
- lemma: 'тиждень'
  translation: 'week'
  pos: 'noun'
  gender: 'm'
- lemma: 'рік'
  translation: 'year'
  pos: 'noun'
  gender: 'm'
- lemma: 'сподіватися'
  translation: 'to hope'
  pos: 'verb'
- lemma: 'мріяти'
  translation: 'to dream'
  pos: 'verb'
- lemma: 'планувати'
  translation: 'to plan'
  pos: 'verb'
- lemma: 'обіцяти'
  translation: 'to promise'
  pos: 'verb'
- lemma: 'вихідні'
  translation: 'weekend'
  pos: 'noun'
  notes: 'Plural only'
- lemma: 'відпустка'
  translation: 'vacation / leave'
  pos: 'noun'
  gender: 'f'
- lemma: 'канікули'
  translation: 'holidays / break'
  pos: 'noun'
  notes: 'Plural only (school/university)'
===FIX_END===

---

### Review Summary

| Category | Issues | Fixed |
|----------|--------|-------|
| IPA accuracy | 4 (wrong stress, missing markers, inconsistent affricate) | 4 |
| Pedagogical safety | 2 (present-for-future in dialogue, untaught Genitive in activity) | 2 |
| Naturalness | 1 ("друзі будуть дзвонити") | 1 |
| Plan compliance | 1 (truncated proverb) | 1 |
| A1 scaffolding | 1 (untranslated Ukrainian) | 1 |
| File structure | 1 (vocab YAML wrapper) | 1 |
| **Total** | **10** | **10** |

**Russianisms**: CLEAN
**Russian characters (ы, э, ё, ъ)**: CLEAN
**Gender/case agreement**: CLEAN
**Activity mechanics**: All unjumble word arrays verified complete. All fill-in answers produce grammatical sentences.
**Factual claims**: Carpathians geography accurate. Proverb authentic (now complete).

===VERDICT===
APPROVE
===END_VERDICT===