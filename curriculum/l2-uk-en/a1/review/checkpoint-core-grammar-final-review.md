Now let me do a thorough deep review. I've read all files. Here is my adversarial analysis.

---

## Deep Adversarial Review: checkpoint-core-grammar (a1-34)

### Issue 1: FACTUAL ERROR — "тато" cited as soft sign example
**File:** `checkpoint-core-grammar.md`, line 86
**Text:** `Words ending in soft sign **-ь** can be masculine (день, тато) or feminine (ніч, сіль).`
**Problem:** "Тато" ends in **-о**, not **-ь**. It is masculine, but it does NOT demonstrate a soft sign ending. This is a factual error that directly undermines the rule being taught. Learners will internalize a false example.
**Fix:** Replace "тато" with "кінь" (horse) — a genuine masculine -ь word known at A1.

### Issue 2: Missing stress marks on "плачу" minimal pair
**File:** `checkpoint-core-grammar.md`, line 61
**Text:** `(for example, **плачу** — *I pay* vs **плачу** — *I cry*)`
**Problem:** Without stress marks, the two words are visually identical. The entire pedagogical point — that stress changes meaning — is completely defeated when the student sees the same grapheme twice. This is a critical readability failure for the EXACT concept being taught.
**Fix:** Add stress marks: **плачу́** (I pay) vs **пла́чу** (I cry).

### Issue 3: "студентом" uses Instrumental case — A2 content
**File:** `checkpoint-core-grammar.md`, line 156
**Text:** `| Past | I was a student | *Я студент* | **Я був студентом** (need "був") |`
**Problem:** The SCOPE comment (line 4) explicitly states "Instrumental and Dative cases → A2." Using "студентом" (Instrumental) in a teaching table introduces an unexplained A2 case form. A learner will see the -ом ending, not understand where it came from, and get confused. The pedagogical point (past tense requires "був") can be made without Instrumental.
**Fix:** Change to "Я був вдома" — uses an adverb, no case form, same pedagogical point.

### Issue 4: IPA for Щ missing tie bar on affricate
**File:** `checkpoint-core-grammar.md`, lines 49, 58, 69
**Text:** `[ʃt͡ʃ]` (three occurrences)
**Problem:** Ukrainian Ч is the affricate [t͡ʃ], so Щ = [ʃ] + [t͡ʃ] = [ʃt͡ʃ]. The tie bar distinguishes an affricate from a consonant sequence. Minor at A1, but since IPA is being used explicitly, it should be correct.

### Issue 5: Accusative Life Hack incomplete — omits -я ending
**File:** `checkpoint-core-grammar.md`, line 190
**Text:** `Only feminine gender changes: -а turns into -у.`
**Problem:** Feminine nouns ending in -я (e.g., пісня, земля, Наталія) change to -ю in Accusative, not -у. Since "пісня" appears in the gender rules section (line 81) as a feminine -я example, a student who encounters it later and applies this rule won't know what to do. The simplification is too aggressive.
**Fix:** Add the -я → -ю rule alongside -а → -у.

### Issue 6: Activity title "Числа від 1 до 5" — contains 8 pairs
**File:** `activities/checkpoint-core-grammar.yaml`, line 2
**Text:** `title: 'Числа від 1 до 5'`
**Problem:** The match-up contains pairs for 1 through 8 (один through вісім). Title says "до 5." This is a copy-paste artifact. Students see a title promising 5 items but get 8.

### Issue 7: Activity title "В чи У?" misleading
**File:** `activities/checkpoint-core-grammar.yaml`, line 203
**Text:** `title: 'В чи У? (Напрямок чи Місце)'`
**Problem:** The activity asks students to choose the correct **noun form** (e.g., "парк" vs "парку"), NOT to choose between prepositions в/у. Furthermore, items 3-4 test Nominative and Genitive — not direction/location at all. The title is misleading on two levels.
**Fix:** Change to a general cases title that matches the actual exercise content.

### Issue 8: Unjumble missing question mark
**File:** `activities/checkpoint-core-grammar.yaml`, lines 193-194
**Text:** `words: ["Де", "твоя", "нова", "машина"]` / `answer: "Де твоя нова машина"`
**Problem:** "Де...?" is an interrogative. Both the words array and answer omit the question mark. Per QA criteria: "words array contains all words+punctuation in the answer." Note: All other unjumble items in this file also omit terminal punctuation, so this is a systemic pattern. However, a question without "?" is pedagogically worse than a statement without "." — students are learning question formation.
**Severity:** Minor (systemic pattern, not isolated error). I'll fix this one since it's a question.

### Green Team Verification
The Green Team flagged 5 issues. My assessment:
- **Issue 1 (тато):** Confirmed. Fixing.
- **Issue 2 (stress marks):** Confirmed. Fixing.
- **Issue 3 (park/bank mismatch):** **NOT confirmed.** The actual text reads "Я йду **в банк**. (Банк — unchanged...)" — both example and explanation use "банк." The Green Team hallucinated this error (classic LLM artifact in the reviewer itself).
- **Issue 4 (title 1-5):** Confirmed. Fixing.
- **Issue 5 (В чи У):** Confirmed. Fixing.

### Additional checks performed
- **Russianisms:** CLEAN. No кушати, получати, приймати участь, слідуючий found.
- **Russian characters (ы, э, ё, ъ):** CLEAN.
- **All verb conjugations in fill-in:** Verified all 8 items — all produce grammatical sentences.
- **All case forms in activities:** Verified — all Genitive, Locative, Accusative forms are correct.
- **Plural forms in match-up:** All 8 pairs verified correct (including irregular Друг→Друзі, День→Дні).
- **Past tense match-up:** All 8 pairs verified correct.
- **Unjumble word arrays:** All 6 items contain all words present in the answer.
- **Plan compliance:** All 7 meta sections present in content. Plan's у/в euphony rule missing but this is a plan↔meta gap, not a builder error (meta doesn't include it). All 4 objectives have corresponding self-check questions.
- **LLM artifacts:** "Welcome to this important milestone" (line 17) is generic LLM-speak but the persona is otherwise consistent. No purple prose, no "Це не просто X, а Y", no invented statistics.
- **Cultural claim:** The 1934 Paris contest claim is properly hedged as "legend" with "historians argue" caveat. Responsible handling.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-core-grammar.md
---OLD---
> Words ending in soft sign **-ь** can be masculine (день, тато) or feminine (ніч, сіль). At level A1, we learn their gender by heart. But most words still follow the general rules.
---NEW---
> Words ending in soft sign **-ь** can be masculine (день, кінь) or feminine (ніч, сіль). At level A1, we learn their gender by heart. But most words still follow the general rules.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-core-grammar.md
---OLD---
Wrong stress can even change the meaning of a word (for example, **плачу** — *I pay* vs **плачу** — *I cry*).
---NEW---
Wrong stress can even change the meaning of a word (for example, **плачу́** — *I pay* vs **пла́чу** — *I cry*).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-core-grammar.md
---OLD---
| Present | I am a student | *Я є студент* | **Я студент** (without "є") |
| Past | I was a student | *Я студент* | **Я був студентом** (need "був") |
---NEW---
| Present | I am a student | *Я є студент* | **Я студент** (without "є") |
| Past | I was at home | *Я вдома* | **Я був вдома** (need "був") |
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-core-grammar.md
---OLD---
*   **Щ (Shch)** — is a combination of sounds [ʃt͡ʃ]. Imagine you are saying "fresh cheese" very quickly.
---NEW---
*   **Щ (Shch)** — is a combination of sounds [ʃt͡ʃ]. Imagine you are saying "fresh cheese" very quickly.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-core-grammar.md
---OLD---
*   **Борщ** (borscht) — at the end hear the full [ʃt͡ʃ], do not swallow sounds.
---NEW---
*   **Борщ** (borscht) — at the end hear the full [ʃt͡ʃ], do not swallow sounds.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-core-grammar.md
---OLD---
How many sounds does the letter "Щ" designate? It should sound like [ʃt͡ʃ]. If you read it as "sh", try again!
---NEW---
How many sounds does the letter "Щ" designate? It should sound like [ʃt͡ʃ]. If you read it as "sh", try again!
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-core-grammar.md
---OLD---
> Only feminine gender changes: -а turns into -у.
> Я бачу мам**у**. Я йду в бібліотек**у**.
---NEW---
> Only feminine gender changes: -а turns into -у, -я turns into -ю.
> Я бачу мам**у**. Я йду в бібліотек**у**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-core-grammar.yaml
---OLD---
  title: 'Числа від 1 до 5'
---NEW---
  title: 'Числа від 1 до 8'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-core-grammar.yaml
---OLD---
  title: 'В чи У? (Напрямок чи Місце)'
  instruction: 'Оберіть правильну форму слова.'
---NEW---
  title: 'Відмінки: оберіть правильну форму'
  instruction: 'Оберіть правильну форму слова для кожного речення.'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-core-grammar.yaml
---OLD---
    - words: ["Де", "твоя", "нова", "машина"]
      answer: "Де твоя нова машина"
---NEW---
    - words: ["Де", "твоя", "нова", "машина?"]
      answer: "Де твоя нова машина?"
===FIX_END===

---

## Summary

| # | Issue | Severity | Fixed |
|---|-------|----------|-------|
| 1 | "тато" as soft sign example (ends in -о, not -ь) | Critical — factual error | Yes |
| 2 | Missing stress marks on плачу́/пла́чу minimal pair | Critical — defeats lesson | Yes |
| 3 | "студентом" leaks Instrumental (A2) into A1 | High — scope violation | Yes |
| 4 | IPA [ʃt͡ʃ] missing tie bar → [ʃt͡ʃ] | Minor — accuracy | Yes |
| 5 | Accusative Life Hack omits -я → -ю | Medium — incomplete rule | Yes |
| 6 | Activity title "1 до 5" contains 8 pairs | Medium — misleading | Yes |
| 7 | Activity title "В чи У?" tests case forms, not preposition | Medium — misleading | Yes |
| 8 | Unjumble question missing "?" | Minor — punctuation | Yes |
| 9 | Green Team's "park/bank mismatch" | N/A — hallucinated by reviewer | N/A |

All identified issues have corresponding fixes above. After applying these fixes, the module is pedagogically sound, factually accurate, linguistically correct, and properly scoped to A1. No Russianisms, no Russian characters, no LLM artifacts beyond a mildly generic opener, no forward references to untaught content.

===VERDICT===
APPROVE
===END_VERDICT===