## Phase 9: Final QA Review — the-living-verb-i

### Verification Method
- Read all 375 lines of prose, 525 lines of activities, 106 lines of vocabulary, 48 lines of meta
- Verified every IPA transcription against Ukrainian phonological rules
- Checked every conjugation form in both prose and activities
- Cross-referenced all vocabulary against plan hints
- Verified historical/cultural claims
- Scanned for Russianisms, Russian characters, scope violations, LLM artifacts

---

## Issues Found

### CRITICAL ISSUE 1: Missing "дієслово" terminology
**File:** `the-living-verb-i.md`, line 21
**Text:** `the **verb**. The word itself comes from **дія** [ˈdʲijɑ] (action) and **слово** [ˈslɔʋɔ] (word)`
**Problem:** The text etymologizes the Ukrainian word for "verb" (дія + слово = дієслово) without ever introducing the word **дієслово** itself. A student reads a brilliant etymology breakdown but never learns the actual term. This is like explaining "auto + mobile" without ever saying "automobile."

### CRITICAL ISSUE 2: Pedagogical trap — -ювати verbs contradict the "Master Key" rule
**File:** `the-living-verb-i.md`, lines 80-92 (rule) vs. line 250 (usage)
**Problem:** The "Master Key" rule taught is: *cut off -ти to get the stem, add endings.* But **працювати** (listed as core vocab on line 48) breaks this rule:
- Rule applied: працюва- + ю = **працюваю** (WRONG)
- Correct form: **працюю**

The module uses the correct form "Я працюю" in examples (line 250) but never explains why the rule doesn't apply literally. A diligent student who applies the "Master Key" will produce wrong forms. The "Примітка про «Писати»" (line 309) handles писати's irregularity — працювати deserves the same treatment.

### CRITICAL ISSUE 3: малювати undermines the "confidence builder"
**File:** `the-living-verb-i.md`, lines 347-351
**Text:** `like **малювати** [mɑlʲuˈʋɑtɪ] (to draw/paint)... You think: "Aha! I know you." **Я малюю.**`
**Problem:** малювати is ALSO a -ювати verb with the same stem-shortening trap as працювати. Using it to prove the "Master Key" works on new verbs is actively deceptive — a student applying the rule gets "малюваю" (wrong), not "малюю." Replace with a perfectly regular -ати verb like **співати** (to sing) → **Я співаю**, which genuinely validates the rule.

### MINOR ISSUE 4: Vocabulary file missing verbs used in activities
**File:** `vocabulary/the-living-verb-i.yaml`
**Problem:** Three verbs from plan `vocabulary_hints.recommended` appear in activities but are absent from the vocabulary file:
- **думати** — used in fill-in activity (item: "Я _____ про це" → думаю)
- **вивчати** — used in quiz activity ("Ми вивчаємо мову")
- **розуміти** — used in quiz activity ("Ви розумієте все")

Students practicing these in activities should be able to find them in the vocabulary reference.

### MINOR ISSUE 5: Vocabulary file contains малювати (to be replaced)
**File:** `vocabulary/the-living-verb-i.yaml`, lines 41-45
**Problem:** If малювати is removed from prose (Issue 3), it should be replaced in the vocabulary file with **співати** for consistency.

---

### Items Verified Clean

| Check | Result |
|-------|--------|
| Russianisms (кушати, получати, приймати участь, слідуючий) | CLEAN |
| Russian characters (ы, э, ё, ъ) | CLEAN |
| IPA tie bars on affricates (t͡ʃ, t͡s) | CLEAN — all present |
| IPA ʋ for В (not w) | CLEAN |
| IPA ɦ for Г (not g) | CLEAN |
| All 6 conjugation forms of читати | CORRECT |
| All 6 conjugation forms of писати | CORRECT (with с→ш noted) |
| All activity answers produce grammatical sentences | CORRECT |
| Activity YAML structure (bare list at root) | CORRECT |
| Fill-in: all answers exist in options | CORRECT |
| Anagram: scrambled letters match answer | CORRECT |
| Group-sort: items correctly categorized | CORRECT |
| True-false: all answers verified | CORRECT |
| Historical claim: Apostol 1574 Lviv | ACCURATE |
| Proverb: "Птицю пізнати по пір'ю..." | ACCURATE, authentic Ukrainian |
| Literacy rate claim | ACCURATE (~99.8% per UNESCO) |
| Plan content_outline: all sections present | ALL 4 SECTIONS COVERED |
| Plan objectives mapped to self-check questions | ALL 4 OBJECTIVES COVERED |
| Plan vocabulary_hints.required: all in prose | ALL 8 VERBS PRESENT |
| Grammar scope: no future tense, no perfective, no II conjugation teaching | CLEAN |
| Forward references: only "ignore for now" mentions | CLEAN |
| LLM artifacts / purple prose | CLEAN — voice is natural, tutor-like |
| Word count vs. 2000 target | EXCEEDS (estimated ~2800) |

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-i.md
---OLD---
the **verb**. The word itself comes from **дія** [ˈdʲijɑ] (action) and **слово** [ˈslɔʋɔ] (word). It is literally an "action word."
---NEW---
the **verb** — in Ukrainian, **дієслово** [dʲijɛˈslɔʋɔ]. The word comes from **дія** [ˈdʲijɑ] (action) and **слово** [ˈslɔʋɔ] (word). It is literally an "action word."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-i.md
---OLD---
It still follows the pattern of endings (-у/ю, -еш/єш, -е/є...), but just watch out for that **ш**. It makes the word easier to pronounce. Try saying "писаю" — the stress pattern is awkward. **Пишу** is crisper and clearer.

---

## Культурний контекст: Сила українського слова
---NEW---
It still follows the pattern of endings (-у/ю, -еш/єш, -е/є...), but just watch out for that **ш**. It makes the word easier to pronounce. Try saying "писаю" — the stress pattern is awkward. **Пишу** is crisper and clearer.

### Примітка про «Працювати»
The verb **працювати** (to work) has its own trick. If you cut off just **-ти**, you get **працюва-**. But **працюваю** is wrong! For verbs ending in **-ювати**, you cut off **-вати** to find the real stem.

**працювати** → remove **-вати** → **працю-**

*   **Я працюю.** (I work.)
*   **Ти працюєш.**
*   **Він працює.**
*   **Ми працюємо.**
*   **Ви працюєте.**
*   **Вони працюють.**

> [!tip]
> **Правило для -ювати:**
> See **-ювати** at the end? Remove **-вати**, not just **-ти**.
> **працю-** + **ю** = **працюю** ✓
> **працюва-** + **ю** = **працюваю** ✗

---

## Культурний контекст: Сила українського слова
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-i.md
---OLD---
When you encounter a new verb next week, like **малювати** [mɑlʲuˈʋɑtɪ] (to draw/paint), you don't need to panic. You look at it. You see the **-ати**.
You think: "Aha! I know you."
*   **Я малюю.** (I draw.)
*   **Ти малюєш.** (You draw.)
*   **Ми малюємо.** (We draw.)
---NEW---
When you encounter a new verb next week, like **співати** [spʲiˈʋɑtɪ] (to sing), you don't need to panic. You look at it. You see the **-ати**.
You think: "Aha! I know you."
*   **Я співаю.** (I sing.)
*   **Ти співаєш.** (You sing.)
*   **Ми співаємо.** (We sing.)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/the-living-verb-i.yaml
---OLD---
- ipa: '[mɑlʲuˈʋɑtɪ]'
  lemma: малювати
  notes: type 1 (-ювати → -юю); imperfective
  pos: verb
  translation: to draw; to paint
---NEW---
- ipa: '[spʲiˈʋɑtɪ]'
  lemma: співати
  notes: type 1 (-ати); imperfective
  pos: verb
  translation: to sing
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/the-living-verb-i.yaml
---OLD---
- ipa: '[t͡ʃɛˈkɑtɪ]'
  lemma: чекати
  notes: type 1 (-ати); imperfective
  pos: verb
  translation: to wait
- ipa: '[jɑ]'
---NEW---
- ipa: '[t͡ʃɛˈkɑtɪ]'
  lemma: чекати
  notes: type 1 (-ати); imperfective
  pos: verb
  translation: to wait
- ipa: '[ˈdumɑtɪ]'
  lemma: думати
  notes: type 1 (-ати); imperfective
  pos: verb
  translation: to think
- ipa: '[ʋɪu̯ˈt͡ʃɑtɪ]'
  lemma: вивчати
  notes: type 1 (-ати); imperfective
  pos: verb
  translation: to study
- ipa: '[rɔzuˈmʲitɪ]'
  lemma: розуміти
  notes: type 1 (-іти, I conjugation endings); imperfective
  pos: verb
  translation: to understand
- ipa: '[jɑ]'
===FIX_END===

---

## Review Summary

| Category | Finding |
|----------|---------|
| Critical issues | 3 (all fixable, fixes provided above) |
| Minor issues | 2 (vocab file gaps, fixes provided) |
| Ukrainian accuracy | No errors in grammar, morphology, or spelling |
| IPA accuracy | All transcriptions verified correct |
| Russianisms | None |
| Activity correctness | All 10 activities structurally valid, all answers correct |
| Plan compliance | Full — all sections, vocabulary, objectives covered |
| Historical claims | Accurate |
| LLM artifacts | None detected |
| Word count | Exceeds 2000 target |

The Green Team review identified the same 3 critical issues independently, which corroborates the findings. The module is genuinely strong — warm tone, excellent metaphors, correct Ukrainian throughout. The -ювати trap is the only real pedagogical danger, and the fixes above close it completely.

===VERDICT===
APPROVE
===END_VERDICT===