# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> The review already applied some fixes. You handle what's still failing.
> You have **Edit** and **Grep** tools — fix files directly.

---

## Ukrainian Alphabet Reference (use when editing letter/sound content)

When fixing content about the Ukrainian alphabet, vowels, or consonants, use these EXACT classifications:
- **10 vowel letters (голосні)**: А, О, У, Е, И, І, Я, Ю, Є, Ї (6 base + 4 iotated)
- **22 consonant letters (приголосні)**: Б, В, Г, Ґ, Д, Ж, З, Й, К, Л, М, Н, П, Р, С, Т, Ф, Х, Ц, Ч, Ш, Щ
- **1 modifier**: Ь (soft sign)
- Common confusions: В is a CONSONANT, І is a VOWEL, Й is a CONSONANT

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original, not less.
- **PRESERVE the author's intent.** If a paragraph explains something poorly, rewrite it to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your rewrite should read like the original author wrote it on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information that cannot be salvaged). This should be rare.

---

## Fix Plan (from Phase D.1 review)



**NOTE: 12 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥30 items
  - Actual: Activity has 12 items
  - Fix: Add 18 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥30 items
  - Actual: Activity has 10 items
  - Fix: Add 20 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:quiz`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 10 items
  - Fix: Add 10 more items to 'quiz' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 8 items
  - Fix: Add 7 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 12 items
  - Fix: Add 8 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 10 items
  - Fix: Add 10 more items to 'match-up' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Entire module — all 5 sections, Line 45 (only mention), Section "Практичні вправи (Practice Exercises)", Line 78, Section "Культурний код та підсумок (Cultural Code and Summary)", Line 80, Section "Культурний код та підсумок (Cultural Code and Summary)", Lines 11, 27, 38, 40, 45, 52, 60, 68, 78, 82

### Finding 1: Zero Engagement Boxes (Audit Gate Failure)
**Location**: Entire module — all 5 sections
**Problem**: The module contains zero callout boxes (`> [!tip]`, `> [!example]`, `> [!cultural-note]`, `> [!did-you-know]`). The audit requires minimum 1 for A1, and the richness gate requires 2. This is a blocking audit failure.
**Required Fix**: Add at minimum 2 engagement callouts. Recommended placements:
**Severity**: HIGH

### Finding 2: Fabricated Compound "сонце-життя"
**Location**: Line 80, Section "Культурний код та підсумок (Cultural Code and Summary)"
**Problem**: "сонце-життя" is NOT a standard Ukrainian compound expression. VESUM returns NOT FOUND. The research notes mention "земля-мати" as a cultural hook but never mention "сонце-життя." This appears to be an LLM fabrication presented as authentic Ukrainian cultural language. "Земля-мати" is real; "сонце-життя" is not.
**Required Fix**: Replace with an actual Ukrainian expression, e.g., "ясне сонце" (bright sun) or "сонце — джерело життя" (sun is the source of life), or simply remove the fabricated compound and discuss сонце's neuter gender using the existing cultural hook from the introduction.
**Severity**: HIGH

### Finding 3: LLM Voice — "Let us" x10+
**Location**: Lines 11, 27, 38, 40, 45, 52, 60, 68, 78, 82
**Problem**: "Let us" appears 10+ times throughout the module. This is extremely formal and a strong LLM fingerprint. Real English tutors use "Let's" in conversational instruction. The formality creates a cold, robotic feel that fails the beginner warmth test.
**Required Fix**: Replace all "Let us" with "Let's" throughout the module.
**Severity**: HIGH

### Finding 4: Missing Warmth & Encouragement (Beginner Safety Failure)
**Location**: Entire module — all 5 sections
**Problem**: Zero encouragement phrases ("Great!", "You've got this!", "Don't worry"). No welcome greeting (no "Привіт!"). No "don't worry, this is normal" moment. No celebration at the end — line 89 just says 「Keep practicing your color codes and observing the endings of every new word you meet.」 which is flat and perfunctory. The "Would I Continue?" test fails on 3/5 criteria.
**Required Fix**: Add (1) a warm opening like "Привіт! Welcome to..." in section "Вступ (Introduction)", (2) at least 2 encouragement moments mid-module (after the first practice set, after S.T.A.L.K.E.R. section), (3) a celebration closing in section "Культурний код та підсумок (Cultural Code and Summary)" that says "You can now identify the gender of most Ukrainian nouns!"
**Severity**: HIGH

### Finding 5: Plan Objective Unmet — 4 Declension Families
**Location**: Line 45 (only mention), Section "Практичні вправи (Practice Exercises)"
**Problem**: Plan objective 2 states "Learner can categorize nouns into 4 declension families." The content only mentions "Family 4" in passing. Families 1-3 are never named. The learner cannot meet this objective from the content provided.
**Required Fix**: Add a brief overview table or callout in section "Презентація правил (Presentation of Rules)" that names all 4 declension families with one example each, even at recognition level. This could double as one of the missing engagement boxes.
**Severity**: HIGH

### Finding 6: Unsourced "95% Predictability Rule"
**Location**: Line 78, Section "Культурний код та підсумок (Cultural Code and Summary)"
**Problem**: The "95%" statistic is presented as fact but has no source. The research notes don't mention this figure. While gender IS largely predictable from endings, the specific "95%" claim is unverifiable and may be fabricated.
**Required Fix**: Change to "For most words, the ending reliably predicts the gender" — remove the unsourced statistic.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Zero Engagement Boxes (Audit Gate Failure)
- **Location**: Entire module — all 5 sections
- **Problem**: The module contains zero callout boxes (`> [!tip]`, `> [!example]`, `> [!cultural-note]`, `> [!did-you-know]`). The audit requires minimum 1 for A1, and the richness gate requires 2. This is a blocking audit failure.
- **Fix**: Add at minimum 2 engagement callouts. Recommended placements:
  1. After line 7 in section "Вступ (Introduction)": `> [!tip]` with the color-code mnemonic as a visual reference table (Blue=M, Red=F, Yellow=N)
  2. After line 43 in section "Практичні вправи (Practice Exercises)": `> [!did-you-know]` about the день/ніч pair being commonly used in greetings

### Issue 2: Fabricated Compound "сонце-життя"
- **Location**: Line 80, Section "Культурний код та підсумок (Cultural Code and Summary)"
- **Original**: 「We say сонце-життя (sun-life) because the neuter ending places the sun in a universal, balanced role.」
- **Problem**: "сонце-життя" is NOT a standard Ukrainian compound expression. VESUM returns NOT FOUND. The research notes mention "земля-мати" as a cultural hook but never mention "сонце-життя." This appears to be an LLM fabrication presented as authentic Ukrainian cultural language. "Земля-мати" is real; "сонце-життя" is not.
- **Fix**: Replace with an actual Ukrainian expression, e.g., "ясне сонце" (bright sun) or "сонце — джерело життя" (sun is the source of life), or simply remove the fabricated compound and discuss сонце's neuter gender using the existing cultural hook from the introduction.

### Issue 3: LLM Voice — "Let us" x10+
- **Location**: Lines 11, 27, 38, 40, 45, 52, 60, 68, 78, 82
- **Original**: 「Let us start with Masculine nouns.」 (line 11), 「Let us look at the case of тато」 (line 38), etc.
- **Problem**: "Let us" appears 10+ times throughout the module. This is extremely formal and a strong LLM fingerprint. Real English tutors use "Let's" in conversational instruction. The formality creates a cold, robotic feel that fails the beginner warmth test.
- **Fix**: Replace all "Let us" with "Let's" throughout the module.

### Issue 4: Missing Warmth & Encouragement (Beginner Safety Failure)
- **Location**: Entire module — all 5 sections
- **Problem**: Zero encouragement phrases ("Great!", "You've got this!", "Don't worry"). No welcome greeting (no "Привіт!"). No "don't worry, this is normal" moment. No celebration at the end — line 89 just says 「Keep practicing your color codes and observing the endings of every new word you meet.」 which is flat and perfunctory. The "Would I Continue?" test fails on 3/5 criteria.
- **Fix**: Add (1) a warm opening like "Привіт! Welcome to..." in section "Вступ (Introduction)", (2) at least 2 encouragement moments mid-module (after the first practice set, after S.T.A.L.K.E.R. section), (3) a celebration closing in section "Культурний код та підсумок (Cultural Code and Summary)" that says "You can now identify the gender of most Ukrainian nouns!"

### Issue 5: Plan Objective Unmet — 4 Declension Families
- **Location**: Line 45 (only mention), Section "Практичні вправи (Practice Exercises)"
- **Original**: 「Explaining why ім'я is Neuter despite ending in -я requires knowing that it belongs to a special historical group called Family 4.」
- **Problem**: Plan objective 2 states "Learner can categorize nouns into 4 declension families." The content only mentions "Family 4" in passing. Families 1-3 are never named. The learner cannot meet this objective from the content provided.
- **Fix**: Add a brief overview table or callout in section "Презентація правил (Presentation of Rules)" that names all 4 declension families with one example each, even at recognition level. This could double as one of the missing engagement boxes.

### Issue 6: Unsourced "95% Predictability Rule"
- **Location**: Line 78, Section "Культурний код та підсумок (Cultural Code and Summary)"
- **Original**: 「For most words, you have a 95% predictability rule.」
- **Problem**: The "95%" statistic is presented as fact but has no source. The research notes don't mention this figure. While gender IS largely predictable from endings, the specific "95%" claim is unverifiable and may be fabricated.
- **Fix**: Change to "For most words, the ending reliably predicts the gender" — remove the unsourced statistic.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 80 | 「сонце-життя」 | ясне сонце / remove compound | Fabricated compound |

Note: All other Ukrainian in the module is grammatically correct. Gender assignments, adjective agreement, pronoun forms (мій/моя/моє), and example sentences all verify clean.

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 7.0)

### Experience Quality: 6/10 → 9/10
**What to fix:**
1. Add 2+ engagement callout boxes (> [!tip], > [!did-you-know]) — one in section "Вступ (Introduction)" with color-code table, one in section "Практичні вправи (Practice Exercises)"
2. Replace all "Let us" → "Let's" (10+ instances)
3. Add warm opening greeting in section "Вступ (Introduction)"
4. Add celebration closing in section "Культурний код та підсумок (Cultural Code and Summary)"
5. Add 2-3 encouragement phrases throughout

**Expected score after fix:** 9/10

### Beginner Safety: 6/10 → 9/10
**What to fix:**
1. Add "Привіт!" welcome at opening
2. Add "Don't worry" moment after introducing soft sign exceptions (line 40)
3. Add "Great job!" after the pronoun drill (after line 64)
4. Replace flat ending (line 89) with "You can now identify gender for most Ukrainian nouns! That's a real superpower."
5. Break section "Практичні вправи (Practice Exercises)" into smaller visual chunks

**Expected score after fix:** 9/10

### LLM Fingerprint: 6/10 → 9/10
**What to fix:**
1. Replace all 10+ "Let us" with "Let's"
2. Vary section openings — not every section should start with "Let us [verb]"
3. Remove 「The secret to the Ukrainian gender code lies right at the end of the word.」 and replace with direct instruction ("Gender in Ukrainian is easy to spot — just look at the ending.")
4. Vary example formatting — use a table for one set, inline for another, dialogue for a third

**Expected score after fix:** 9/10

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Add declension families overview (even brief) to meet plan objective 2
2. Remove or replace fabricated "сонце-життя" compound
3. Replace "95% predictability rule" with unquantified statement
4. Add the color-code mnemonic as an actual visual table (currently described in words only)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 7×1.3 + 9×1.3 + 9×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 9.1 + 11.7 + 9.0 + 13.5) / 8.9
= 77.5 / 8.9
= 8.7/10
```

Note: Activities kept at 7 because item counts are below plan hints (4 activities vs suggested ~85 items). A rebuild of activities would be needed to push higher, but this is outside the content fix scope.

---

## Audit Failures (from automated re-audit)

```
❌ Structure check failed: Missing '## Summary'
✨ Purity violations found: 1
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'it is...'.
--- STRICT GATES (Level A1) ---
Structure    ❌ Missing '## Summary'
📚 PEDAGOGICAL VIOLATIONS FOUND:
[ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'it is...'.
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
→ 1 violations (minor)
→ Structure issue: Missing '## Summary'
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Structure: Missing '## Summary'
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/the-gender-code-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Structure: Missing '## Summary'
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `земля-мати` (source: prose)
  ❌ `сонце-життя` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md`

```markdown
## Вступ (Introduction)

Привіт! Welcome to one of the most important building blocks of Ukrainian. Today, you'll unlock the three-gender system. In Ukrainian, every single noun belongs to one of three categories: Masculine, Feminine, or Neuter. This isn't just about people — everyday objects, abstract concepts, and places all have a grammatical gender too. Don't worry — there's a simple trick for predicting it, and you'll pick it up fast.

In Ukrainian folklore, the natural world reflects this system in beautiful ways. Take the word **сонце** (sun), for example. In Romance languages like French or Spanish, the sun is typically masculine. However, the Ukrainian sun is neuter. It is viewed as an impartial, gentle life-giver rather than a gendered deity. This neuter perspective helps establish the idea that grammatical gender goes beyond biological sex.

To make predicting gender easier, we'll use a color-code system. Here's your cheat sheet:

> [!tip] Gender Color Codes
> 🔵 **Masculine** — ends in a hard consonant (стіл, хліб, дім)
> 🔴 **Feminine** — ends in **-а** or **-я** (книга, школа, земля)
> 🟡 **Neuter** — ends in **-о** or **-е** (вікно, місто, море)

Keep these color codes in mind throughout the module. By assigning a visual tag to every new vocabulary word, your brain will build a mental dictionary that makes grammatical agreement feel natural.

## Презентація правил (Presentation of Rules)

Gender in Ukrainian is easy to spot — just look at the last letter. Let's start with Masculine nouns. These words typically end in a hard consonant. Great examples include **стіл** (table), **хліб** (bread), and **дім** (house). When you see a word finishing with a consonant, your first instinct should be that it is masculine.

Next, we have Feminine nouns. These words almost always end in the vowels **-а** or **-я**. You already know many of these words. For instance, **книга** (book), **школа** (school), and **земля** (earth) are all feminine. Finally, there are Neuter nouns. These words usually end in the vowels **-о** or **-е**. Words like **вікно** (window), **місто** (city), and **море** (sea) fit perfectly into this category. 

To practice this categorization, we will use three essential diagnostic tools: the possessive pronouns **мій** (my masculine), **моя** (my feminine), and **моє** (my neuter). This is how we confirm gender agreement and identity.

*   **мій** **стіл** (my table)
*   **моя** **книга** (my book)
*   **моє** **вікно** (my window)

Notice the syntactic agreement. The gender of the noun dictates the form of adjectives and pronouns you use with it. If you add an adjective, it must match the noun's gender.

*   **великий** **стіл** (large table)
*   **цікава** **книга** (interesting book)
*   **чисте** **вікно** (clean window)

Now let's see this in action with a family dialogue. This shows the difference between natural and grammatical gender.

> **Хто** **це**? (Who is this?)
> **Це** **мій** **брат**. **Він** **добрий**. (This is my brother. He is kind.)
> **А** **це** **хто**? (And who is this?)
> **Це** **моя** **сестра**. **Вона** **добра**. (This is my sister. She is kind.)

The word **брат** (brother) ends in a consonant and is biologically male, so it is masculine. The word **сестра** (sister) ends in **-а** and is biologically female, making it feminine. However, we also have **мама** (mom) and **тато** (dad). Both are high-frequency family words, but we must look closely at their endings and their natural gender in the next section. Other family members follow similar predictable rules, but we will focus on these core relationships first.

## Практичні вправи (Practice Exercises)

Great — you've got the basic rules down! Now let's look at a few important exceptions. Don't worry, there aren't many. The first is the natural gender override. Let's look at **тато** (dad). Based on the rule you just learned, a word ending in **-о** should be neuter. However, biological sex always overrides the vowel ending. Because a dad is biologically male, the word **тато** is Masculine. You must say **мій** **тато** (my dad), never the neuter form. Let us contrast this with the word **місто** (city). A city has no biological sex, so the **-о** ending correctly makes it Neuter. You would say **моє** **місто** (my city).

Next up: the soft sign ambiguity. Some words end in **-ь**, and there's no simple rule to predict their gender — you just have to memorize them. But here's the good news: there aren't many at A1 level. Let's practice with a high-frequency pair: **день** (day) versus **ніч** (night).

> [!did-you-know] Greetings Lock In Gender
> You already use these words in everyday greetings: **Добрий день!** (Good day! — masculine) and **Добра ніч!** (Good night! — feminine). The adjective ending changes with gender — that's agreement in action! The word **день** is Masculine, while **ніч** is Feminine. A great strategy for memorizing these essential soft exceptions is to learn them with their matching adjectives.

*   **гарний** **день** (good day)
*   **добра** **ніч** (good night)

Another interesting challenge is the "name" trap. Let's look at the word **ім'я** (name). Explaining why **ім'я** is Neuter despite ending in **-я** requires knowing that it belongs to a special historical group called Family 4. To avoid common learner confusion, you must contrast it with a regular Feminine word like **земля**. While **земля** uses **моя**, the word **ім'я** requires the neuter pronoun.

*   **моя** **рідна** **земля** (my native land)
*   **моє** **повне** **ім'я** (my full name)

For additional practice, let us look at the word **серце** (heart). It ends in **-е**, so it is Neuter. We say **добре** **серце** (good heart) or **моє** **серце** (my heart).

Let's finish this section with a categorization drill. You're doing great! Look at these high-frequency nouns and sort them into their respective gender buckets.

*   **чоловік** (man) — ends in a consonant, biological male: Masculine.
*   **жінка** (woman) — ends in **-а**, biological female: Feminine.
*   **місто** (city) — ends in **-о**, inanimate object: Neuter.

## Самостійна робота (Independent Work/Production)

Time for some independent practice! A common mistake for English speakers is the "it" trap. In English, you use "it" for any inanimate object. In Ukrainian, you must use the pronoun that matches the grammatical gender of the word. Let us do a targeted drill to stop learners from using neuter **воно** for all objects. Remember the rule: if the object is masculine, use **він**. If it is feminine, use **вона**. If it is neuter, use **воно**. Reinforcing this is crucial.

*   **Де** **стіл**? **Він** **тут**. (Where is the table? It is here.)
*   **Де** **книга**? **Вона** **там**. (Where is the book? It is there.)
*   **Де** **вікно**? **Воно** **тут**. (Where is the window? It is here.)

Next, let us map gender to modern contexts using S.T.A.L.K.E.R. vocabulary. The popular game provides excellent classification anchors. Look at the word **артефакт** (artifact). It ends in a hard consonant, making it Masculine. Now consider the word **зона** (zone). It ends in **-а**, so it is Feminine. Finally, look at **укриття** (shelter). It ends in **-я** and is an abstract structure, falling into the Neuter category. Use these gaming terms as memory anchors to lock in the rules. When you explore a virtual landscape, every object you pick up or location you discover follows these exact same grammar rules.

Let us try applying agreement by creating simple descriptive phrases for personal items and nature terms. Use the pronouns **мій**, **моя**, or **моє** along with basic adjectives like **новий** (new), **цікавий** (interesting), or **великий** (large).

*   **Це** **мій** **новий** **дім**. (This is my new house.)
*   **Це** **моя** **цікава** **книга**. (This is my interesting book.)
*   **Це** **моє** **велике** **море**. (This is my large sea.)

Look around your room. Try to point at an object, guess its gender based on the ending, and add the correct possessive pronoun. What about a dog? The word **собака** (dog) ends in **-а**, making it grammatically Feminine, so we say **моя** **собака** (my dog), even though you might hear colloquial variations. Stick to the grammatical feminine form for now to keep your foundation strong.

## Культурний код та підсумок (Cultural Code and Summary)

You have now unlocked the core mechanism of Ukrainian nouns. Let us do a quick summary of gender prediction from endings. For most words, the ending reliably predicts the gender. Hard consonants usually signal Masculine words. The vowels **-а** or **-я** usually signal Feminine words. The vowels **-о** or **-е** usually signal Neuter words. Always remember the reinforcement of the soft sign and natural gender exceptions. Words like **тато** rely on biology, and words like **день** or **ніч** must simply be memorized.

This system is not just grammar; it is a cultural reflection. Gendered language shapes the Ukrainian worldview through the personification of nature. We say **земля-мати** (mother earth) because the feminine ending naturally associates the land with a nurturing female figure. The neuter **сонце** (sun) — **ясне сонце** — sits in a balanced, universal role, neither masculine nor feminine. 

Let us do a final competency check. Identify the gender for these core identity vocabulary words based on everything you have learned.

*   **ім'я** (Neuter exception)
*   **тато** (Masculine override)
*   **мама** (Feminine)
*   **місто** (Neuter)

You can now identify the gender of most Ukrainian nouns just by looking at their ending — that's a real superpower! Keep practicing your color codes 🔵🔴🟡 and observing the endings of every new word you meet. You've earned it — чудово! (wonderful!)
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-gender-code.yaml`

```yaml
- type: match-up
  title: "Match the Noun to Its Gender"
  instruction: "Match each Ukrainian noun to its grammatical gender based on the ending rules you learned."
  pairs:
    - left: "стіл"
      right: "Masculine"
    - left: "хліб"
      right: "Masculine"
    - left: "дім"
      right: "Masculine"
    - left: "брат"
      right: "Masculine"
    - left: "книга"
      right: "Feminine"
    - left: "школа"
      right: "Feminine"
    - left: "земля"
      right: "Feminine"
    - left: "сестра"
      right: "Feminine"
    - left: "вікно"
      right: "Neuter"
    - left: "місто"
      right: "Neuter"
    - left: "море"
      right: "Neuter"
    - left: "сонце"
      right: "Neuter"

- type: quiz
  title: "Identify the Gender"
  instruction: "Choose the correct gender for each Ukrainian noun."
  items:
    - question: "What is the gender of the word серце (heart)?"
      options:
        - text: "Masculine"
          correct: false
        - text: "Feminine"
          correct: false
        - text: "Neuter"
          correct: true
        - text: "No gender"
          correct: false
      explanation: "Серце ends in -е, which signals Neuter gender."
    - question: "What is the gender of the word тато (dad)?"
      options:
        - text: "Masculine"
          correct: true
        - text: "Feminine"
          correct: false
        - text: "Neuter"
          correct: false
        - text: "No gender"
          correct: false
      explanation: "Тато ends in -о, which normally signals Neuter, but biological sex overrides the ending. Dad is male, so тато is Masculine."
    - question: "What is the gender of the word собака (dog)?"
      options:
        - text: "Masculine"
          correct: false
        - text: "Feminine"
          correct: true
        - text: "Neuter"
          correct: false
        - text: "No gender"
          correct: false
      explanation: "Собака ends in -а, which signals Feminine gender. The grammatical ending determines gender here."
    - question: "What is the gender of the word день (day)?"
      options:
        - text: "Masculine"
          correct: true
        - text: "Feminine"
          correct: false
        - text: "Neuter"
          correct: false
        - text: "No gender"
          correct: false
      explanation: "День ends in a soft sign (-ь) and must be memorized as Masculine."
    - question: "What is the gender of the word ніч (night)?"
      options:
        - text: "Masculine"
          correct: false
        - text: "Feminine"
          correct: true
        - text: "Neuter"
          correct: false
        - text: "No gender"
          correct: false
      explanation: "Ніч ends in a soft consonant and must be memorized as Feminine."
    - question: "What is the gender of the word зона (zone)?"
      options:
        - text: "Masculine"
          correct: false
        - text: "Feminine"
          correct: true
        - text: "Neuter"
          correct: false
        - text: "No gender"
          correct: false
      explanation: "Зона ends in -а, which signals Feminine gender."
    - question: "What is the gender of the word артефакт (artifact)?"
      options:
        - text: "Masculine"
          correct: true
        - text: "Feminine"
          correct: false
        - text: "Neuter"
          correct: false
        - text: "No gender"
          correct: false
      explanation: "Артефакт ends in a hard consonant, which signals Masculine gender."
    - question: "What is the gender of the word укриття (shelter)?"
      options:
        - text: "Masculine"
          correct: false
        - text: "Feminine"
          correct: false
        - text: "Neuter"
          correct: true
        - text: "No gender"
          correct: false
      explanation: "Укриття is Neuter. Despite ending in -я, it belongs to a special neuter group, similar to ім'я."
    - question: "Which ending usually signals a Feminine noun?"
      options:
        - text: "A hard consonant"
          correct: false
        - text: "-о or -е"
          correct: false
        - text: "-а or -я"
          correct: true
        - text: "-ий or -ій"
          correct: false
      explanation: "Feminine nouns typically end in -а or -я, like книга, сестра, земля."
    - question: "Which possessive pronoun do you use with a Neuter noun?"
      options:
        - text: "мій"
          correct: false
        - text: "моя"
          correct: false
        - text: "моє"
          correct: true
        - text: "мої"
          correct: false
      explanation: "Neuter nouns use моє, for example: моє вікно, моє місто."

- type: fill-in
  title: "Choose the Correct Possessive Pronoun"
  instruction: "Fill in the blank with the correct form of 'my' (мій, моя, or моє) to match the noun's gender."
  items:
    - sentence: "Це ___ стіл."
      answer: "мій"
      options: ["мій", "моя", "моє", "мої"]
      explanation: "Стіл is Masculine, so we use мій."
    - sentence: "Це ___ книга."
      answer: "моя"
      options: ["мій", "моя", "моє", "мої"]
      explanation: "Книга is Feminine, so we use моя."
    - sentence: "Це ___ вікно."
      answer: "моє"
      options: ["мій", "моя", "моє", "мої"]
      explanation: "Вікно is Neuter, so we use моє."
    - sentence: "Це ___ тато."
      answer: "мій"
      options: ["мій", "моя", "моє", "мої"]
      explanation: "Тато is Masculine (biological sex overrides the -о ending), so we use мій."
    - sentence: "Це ___ мама."
      answer: "моя"
      options: ["мій", "моя", "моє", "мої"]
      explanation: "Мама is Feminine, so we use моя."
    - sentence: "Це ___ місто."
      answer: "моє"
      options: ["мій", "моя", "моє", "мої"]
      explanation: "Місто is Neuter, so we use моє."
    - sentence: "Це ___ дім."
      answer: "мій"
      options: ["мій", "моя", "моє", "мої"]
      explanation: "Дім is Masculine (ends in a consonant), so we use мій."
    - sentence: "Це ___ сестра."
      answer: "моя"
      options: ["мій", "моя", "моє", "мої"]
      explanation: "Сестра is Feminine (ends in -а), so we use моя."

- type: match-up
  title: "Match the Noun to Its Possessive Pronoun"
  instruction: "Match each noun to the correct form of 'my' based on its gender."
  pairs:
    - left: "брат"
      right: "мій"
    - left: "мама"
      right: "моя"
    - left: "серце"
      right: "моє"
    - left: "хліб"
      right: "мій"
    - left: "земля"
      right: "моя"
    - left: "море"
      right: "моє"
    - left: "чоловік"
      right: "мій"
    - left: "жінка"
      right: "моя"
    - left: "сонце"
      right: "моє"
    - left: "собака"
      right: "моя"
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-gender-code.yaml`

```yaml
items:
  - lemma: "брат"
    translation: "brother"
    pos: "noun"
    gender: "m"
    usage: "старший брат (older brother)"
  - lemma: "сестра"
    translation: "sister"
    pos: "noun"
    gender: "f"
    usage: "молодша сестра (younger sister)"
  - lemma: "мама"
    translation: "mother, mom"
    pos: "noun"
    gender: "f"
    usage: "моя мама (my mom)"
  - lemma: "тато"
    translation: "father, dad"
    pos: "noun"
    gender: "m"
    notes: "Natural gender overrides the -о ending. Masculine, not Neuter."
    usage: "мій тато (my dad)"
  - lemma: "дім"
    translation: "house, home"
    pos: "noun"
    gender: "m"
    usage: "новий дім (new house)"
  - lemma: "вікно"
    translation: "window"
    pos: "noun"
    gender: "n"
    usage: "чисте вікно (clean window)"
  - lemma: "книга"
    translation: "book"
    pos: "noun"
    gender: "f"
    usage: "цікава книга (interesting book)"
  - lemma: "місто"
    translation: "city"
    pos: "noun"
    gender: "n"
    usage: "велике місто (big city)"
  - lemma: "стіл"
    translation: "table"
    pos: "noun"
    gender: "m"
    usage: "великий стіл (large table)"
  - lemma: "море"
    translation: "sea"
    pos: "noun"
    gender: "n"
    usage: "синє море (blue sea)"
  - lemma: "ніч"
    translation: "night"
    pos: "noun"
    gender: "f"
    notes: "Soft sign exception — must be memorized as Feminine."
    usage: "добра ніч (good night)"
  - lemma: "день"
    translation: "day"
    pos: "noun"
    gender: "m"
    notes: "Soft sign exception — must be memorized as Masculine."
    usage: "гарний день (good day)"
  - lemma: "земля"
    translation: "earth, land"
    pos: "noun"
    gender: "f"
    usage: "рідна земля (native land)"
  - lemma: "серце"
    translation: "heart"
    pos: "noun"
    gender: "n"
    usage: "добре серце (good heart)"
  - lemma: "сонце"
    translation: "sun"
    pos: "noun"
    gender: "n"
    notes: "Cultural hook — neuter life-giver in Ukrainian folklore."
    usage: "ясне сонце (bright sun)"
  - lemma: "собака"
    translation: "dog"
    pos: "noun"
    gender: "f"
    notes: "Grammatically Feminine despite colloquial masculine usage."
    usage: "моя собака (my dog)"
  - lemma: "ім'я"
    translation: "name"
    pos: "noun"
    gender: "n"
    notes: "Neuter exception (Family 4) — despite ending in -я."
    usage: "моє повне ім'я (my full name)"
  - lemma: "артефакт"
    translation: "artifact"
    pos: "noun"
    gender: "m"
    notes: "S.T.A.L.K.E.R. vocabulary hook."
    usage: "цікавий артефакт (interesting artifact)"
  - lemma: "зона"
    translation: "zone"
    pos: "noun"
    gender: "f"
    notes: "S.T.A.L.K.E.R. vocabulary hook."
    usage: "небезпечна зона (dangerous zone)"
  - lemma: "укриття"
    translation: "shelter"
    pos: "noun"
    gender: "n"
    notes: "S.T.A.L.K.E.R. vocabulary hook. Neuter despite -я ending."
    usage: "надійне укриття (reliable shelter)"
```

---

## Instructions

1. For each issue in the Fix Plan or audit failures, use **Grep** to verify the exact text exists in the file
2. Use the **Edit** tool to fix each issue directly in the file
3. Only fix issues documented above — no silent extra changes
4. Prioritize: audit gate failures first, then review issues

---

## How to Fix

Use the Edit tool for each fix. The workflow for each issue:

1. **Grep** the file to confirm the text exists and is unique
2. **Edit** the file: provide `old_string` (exact text from file) and `new_string` (corrected text)
3. Move to next issue

File paths:
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-gender-code.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-gender-code.yaml`

## Fix Rules

- Only fix issues documented in the Fix Plan or audit failures above
- You MAY add new activities or modify existing ones if the Fix Plan explicitly requests it
- Do NOT add new prose sections or vocabulary items unless the Fix Plan explicitly requests it
- Maximum **20 edits** total (prioritize the most impactful fixes)
- If nothing needs fixing, state that clearly

---

## Friction Report (MANDATORY)

After all fixes, output:

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: {what you were doing when friction occurred, or "Full Phase D.2"}
**Friction Type**: NONE | EDIT_FAILED | TEXT_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done in Phase D.1
- Do NOT output ===REVIEW_START=== blocks
- Do NOT output FIND/REPLACE blocks — use the Edit tool instead
- You MAY add/modify activities if the Fix Plan requests it
- Do NOT make cosmetic changes beyond what the review flagged
