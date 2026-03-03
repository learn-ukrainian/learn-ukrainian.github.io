<!-- content-hash: c6827c22174c -->
# Factual Review (Pass 1)

## Factual Verification Summary

**Total claims checked:** 13
**Confirmed [Tier 1]:** 3
**Discrepancies [Tier 1]:** 1
**Unverified:** 9
**Factual Alignment Score:** 8/10

## Confirmed Claims

1. **Vowels vs Consonants distinction**: The module correctly introduces "Голосні — Vowels" and "Приголосні — Consonants" as the two primary categories of sounds.
   - **Module says:** "## Голосні — Vowels", "## Приголосні — Consonants"
   - **Reference says:** "ЗВУКИ. ГОЛОСНІ І ПРИГОЛОСНІ Ти вимовляєш різні звуки: голосні і приголосні."
   - **Source:** [1-klas-bukvar-bolshakova-2018-1_s0023]

2. **Letter И and its phonetic realization**: The module correctly links the Cyrillic letter И to its phonetic sound representation.
   - **Module says:** "Літера И ... makes the sound [и]" (implied by context focusing on the sound it makes)
   - **Reference says:** "Бачу И, и. Чую [и]."
   - **Source:** [1-klas-bukvar-zaharijchuk-2025-1_s0042]

3. **Vocabulary validity**: The module utilizes 20 Ukrainian vocabulary terms, all of which are valid.
   - **Module says:** Uses words like "мама", "кіно", "вода", "банан", "рука", etc.
   - **Reference says:** "VESUM coverage: 78/78 (100.0%) All words verified ✅ — no morphological issues detected."
   - **Source:** VESUM Dictionary Verification

## Discrepancies

### Discrepancy 1: Hard vs Soft Vowels Classification
- **Module says:** "Літера И (The Hard Vowel)", "Літера І (The Soft Vowel)", and "distinction between the hard И and the soft І"
- **Reference says:** "ГОЛОСНІ ЗВУКИ: наголошені, ненаголошені" and "ПРИГОЛОСНІ ЗВУКИ: дзвінкі, глухі, тверді, м'які"
- **Source:** [2-klas-ukrmova-vashulenko-2019-1_s0001]
- **Severity:** HIGH
- **Suggested fix:** Remove the terminology calling vowels "hard" or "soft". In Ukrainian phonetics, consonants are hard or soft (тверді, м'які), while vowels are stressed or unstressed. Rename the headers to "The Deep Vowel" and "The Bright Vowel" (or similar), and clarify that И/І often indicate the hardness/softness of the preceding consonant.

## Unverified Claims

1. "The letter К... sounds exactly like [English 'K']."
2. "The letter Р... sounds entirely different. It is a trilled or rolled 'r'."
3. "The letter Б... representing the 'b' sound."
4. "The letter В... makes a 'v' sound, or sometimes a 'w' sound."
5. "The letter Д... makes a clear, solid 'd' sound."
6. "The letter О... unstressed О maintains phonetic purity."
7. "The dotted І... is frequently used in art, literature, and branding as a proud symbol of Ukrainian linguistic identity."
8. "The letter И... rarely appears at the very beginning of a native Ukrainian word."
9. "Рим (Rome) uses the deep, relaxed И. Рі́вне (Rivne) uses the sharp, smiling І." (While the vocabulary and overarching phonetic concepts are correct, the explicit minimal pair logic isn't documented in the provided Tier 1 RAG chunks).

## Verdict

**Status:** FAIL

---

# Language Review (Pass 2)

**Reviewed-By:** gemini-2.5-pro (RAG-grounded)

**Status:** FAIL
**Overall Score:** 7.1/10

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Content is structured well but introduces jarring, inappropriate vocabulary (`міна` - explosive) as beginner reading practice. |
| 2 | Language | 9/10 | <8 | The Ukrainian examples are natural, though the English instructional text relies somewhat heavily on AI-style transitions. |
| 3 | Pedagogy | 6/10 | <7 | Fails due to a fundamentally incorrect definition of a "minimal pair" and testing vocabulary that was never taught. |
| 4 | Activities | 6/10 | <7 | Fails due to colonial framing in a quiz explanation ("Unlike Russian...") and including completely untaught words in the image-to-letter activity. |
| 5 | Beginner Safety | 8/10 | <7 | Including words like "mine / explosive" in the very first reading exercises undermines a welcoming beginner environment (Would I Continue? 4/5). |
| 6 | LLM Fingerprint | 7/10 | <7 | Formulaic structure and repetitive AI rhetoric: "This is a milestone," "Knowledge requires reinforcement." |
| 7 | Linguistic Accuracy | 6/10 | <9 | The claim that "Рим" and "Рівне" are a minimal pair is linguistically false. They differ in multiple phonemes and syllables. |

**Weighted Overall:** (8*1.5 + 9*1.1 + 6*1.2 + 6*1.3 + 8*1.3 + 7*1.0 + 6*1.5) / 8.9 = **7.1/10**

## Critical Issues Found

### Issue 1: False Minimal Pair (Linguistic Accuracy & Pedagogy)
**Location**: Section `Важливий контраст — The Crucial Contrast: И versus І`
**Problem**: The text states: `Let us look at a famous minimal pair to understand this contrast. Рим (Rome) ... Рі́вне (Rivne)`. This is factually incorrect. A minimal pair must differ by exactly one phonological element. "Рим" [rɪm] and "Рівне" [rʲivnɛ] differ in their vowels, the palatalization of the initial consonant, their final consonants, and the number of syllables.
**Fix**: Replace the false minimal pair with a true minimal pair using letters the student actually knows, such as `дим` (smoke) and `дім` (house).

### Issue 2: Colonial Framing in Activities (Rule Violation)
**Location**: `activities/the-cyrillic-code-ii.yaml`, Quiz item 4
**Problem**: The explanation for unstressed "О" states: `Unlike Russian, the Ukrainian unstressed О maintains a pure o sound.` This violates the strict anti-colonial framing rule that forbids defining Ukrainian via Russian's absence.
**Fix**: Remove the reference to Russian. Explain the Ukrainian phonetic rule on its own terms.

### Issue 3: Testing Untaught Words (Activities & Pedagogy)
**Location**: `activities/the-cyrillic-code-ii.yaml`, `image-to-letter` activity
**Problem**: The activity asks the user to match emojis (🚀, 🦃, 🥒) to the first letter of their Ukrainian words (`ракета`, `індик`, `огірок`). However, these words were never introduced in the module text. An A1 beginner cannot complete this without guessing or relying on external knowledge.
**Fix**: Replace the untaught emojis/words with vocabulary explicitly taught in the module, such as `мама` (👩), `молоко` (🥛), or `рука` (🖐️).

### Issue 4: Inappropriate Vocabulary for Beginners (Beginner Safety)
**Location**: Section `Перевірка — Self-Check Reading List` and Vocabulary
**Problem**: The list of "high-frequency words" includes `Мі́на (mine / explosive)`. This is a jarring and potentially distressing word choice for a safe, welcoming beginner module, especially when many neutral alternatives with the same known letters exist.
**Fix**: Replace `Мі́на` and `Ді́рка` with neutral, genuinely high-frequency beginner words that use known letters, such as `сік` (juice) or `ліс` (forest).

## Ukrainian Language Issues

- The contrast between `Си́ла` and `Сі́ло` is provided for И/І, but `Сіло` (it sat down) is a somewhat awkward verb form to use as a primary comparative example for absolute beginners compared to basic nouns. A cleaner noun pair like `дим/дім` is much more pedagogically sound and serves dual purposes.

## Fix Plan to Reach 9/10

1. **Fix Minimal Pair**: Replace the "Рим / Рівне" comparison with the actual minimal pair "дим / дім" in the "Важливий контраст" section.
2. **Remove Colonial Framing**: Edit the quiz explanation in the activities YAML to remove the phrase "Unlike Russian,".
3. **Align Activities with Content**: In the `image-to-letter` activity, replace `ракета`, `індик`, and `огірок` with words actually taught in the lesson (`молоко`, `рука`, `мама`).
4. **Swap Inappropriate Vocab**: Replace `Мі́на` and `Ді́рка` in the reading list and vocabulary YAML with neutral vocabulary like `Ліс` and `Сік`. Add `Дим` to the vocabulary list to support the new minimal pair.
5. **Trim AI Rhetoric**: Remove filler sentences like "This is a milestone." and "Knowledge requires reinforcement."

## Verification Summary

- Checked A1 progression and immersion targets (5.5% is within the 5-15% target).
- Scanned for Russianisms and Anglicisms (none found in the Ukrainian text).
- Verified vocabulary alignment between module content and activities (found untaught words tested in activities).
- Checked for colonial framing (found explicitly in the activities quiz explanation).
- Assessed pedagogical accuracy of phonetic explanations (found completely incorrect minimal pair).

## Verdict

**Status:** FAIL
**Rationale:** The module fails due to a linguistically incorrect definition of a minimal pair, an explicit violation of the colonial framing rule in the activities file, and testing learners on vocabulary that was never introduced.