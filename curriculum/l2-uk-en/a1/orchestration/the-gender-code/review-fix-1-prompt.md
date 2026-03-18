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



**NOTE: 7 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥30 items
  - Actual: Activity has 8 items
  - Fix: Add 22 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥30 items
  - Actual: Activity has 8 items
  - Fix: Add 22 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:quiz`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'quiz' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 8 items
  - Fix: Add 7 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'match-up' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Entire module; plan objective #2: "Learner can categorize nouns into 4 declension families", Line 86, Section "Культурний код та підсумок (Cultural Code and Summary)", Only 「[!tip] The Golden Rule of Practice」 on line 49, Section openings, Vocabulary file (`the-gender-code.yaml`), Whole module

### Finding 1: Fabricated Ukrainian Expression — "со́нце-життя́"
**Location**: Line 86, Section "Культурний код та підсумок (Cultural Code and Summary)"
**Problem**: "Земля-мати" (Mother Earth) is a well-established Ukrainian expression. "Сонце-життя" is NOT a standard Ukrainian compound noun or cultural concept. RAG textbook search returned no matches. VESUM does not list it. This appears to be an LLM fabrication presented as a real cultural expression. The plan itself lists it (line 63: "сонце-життя"), so this is a plan-inherited error, but the content should not present fabricated expressions as cultural facts.
**Required Fix**: Replace with a real Ukrainian expression or reframe. E.g., refer to "ясне сонце" (bright sun) or "красне сонечко" (dear little sun) — both genuine folk expressions. Or simply drop the parallel and keep only земля-мати.
**Severity**: HIGH

### Finding 2: Missing Plan Objective — 4 Declension Families
**Location**: Entire module; plan objective #2: "Learner can categorize nouns into 4 declension families"
**Problem**: The content only mentions "Family 4" once in passing (line 47: 「belongs to a special historical group (Family 4)」). There is no systematic presentation of what the 4 declension families are, how they differ, or how to categorize nouns into them. This is a plan objective that is entirely unmet.
**Required Fix**: Add a brief overview table or callout box in section "Презентація правил (Presentation of Rules)" that previews the 4 families at recognition level (not full detail). E.g., a `[!did-you-know]` box explaining the 4 families exist and that learners will explore them more in later modules.
**Severity**: MEDIUM

### Finding 3: Low Immersion (8.5% vs 15-35% target)
**Location**: Whole module
**Problem**: Module 7 falls in the 6-10 band, targeting 15-35% Ukrainian. At 8.5%, the immersion is well below minimum. Most Ukrainian appears only as bolded inline words with immediate English translations.
**Required Fix**: Add 2-3 short Ukrainian reading practice blocks after key sections. E.g., after section "Практичні вправи (Practice Exercises)", add a 3-4 sentence block: "Це мій стіл. Стіл великий. А це моя книга. Книга цікава." These simple, repetitive sentences increase immersion without overwhelming the learner.
**Severity**: MEDIUM

### Finding 4: Only 1 Engagement Box (need ≥2)
**Location**: Only 「[!tip] The Golden Rule of Practice」 on line 49
**Problem**: Audit reports engagement: 1/2. The module needs at least 2 engagement callout boxes. There are no `[!did-you-know]`, `[!culture]`, or `[!fun-fact]` boxes.
**Required Fix**: Add a `[!did-you-know]` box. Natural candidate: a box in section "Культурний код та підсумок (Cultural Code and Summary)" about the cultural significance of земля-мати in Ukrainian folklore, or a box in section "Вступ (Introduction)" noting that Ukrainian has 3 genders while English lost its gender system centuries ago.
**Severity**: MEDIUM

### Finding 5: Vocabulary YAML Missing Prose Words
**Location**: Vocabulary file (`the-gender-code.yaml`)
**Problem**: хліб (line 15), кімната (line 17), чоловік (line 53), жінка (line 54) all appear as teaching examples in the prose and/or activities but are absent from the vocabulary YAML. хліб is used in pattern recognition examples and the group-sort activity. кімната is used in the pattern recognition and match-up activity. чоловік and жінка are used in the categorization drill.
**Required Fix**: Add all 4 words to the vocabulary YAML as supplementary items.
**Severity**: LOW

### Finding 6: LLM Structural Monotony — "Let's..." Openings
**Location**: Section openings
**Problem**: 3 sections begin with "Let's..." variants: "Let's start with a beautiful cultural hook" (line 7, section "Вступ (Introduction)"), "Now, let's look at how we can actually predict" (line 13, section "Презентація правил (Presentation of Rules)"), "Let's dive into some practical exercises" (line 40, section "Практичні вправи (Practice Exercises)"). This is a structural monotony pattern.
**Required Fix**: Vary section openings. E.g., section "Практичні вправи (Practice Exercises)" could open with "Time to put those rules to the test!" instead.
**Severity**: LOW

---

## Critical Issues Found

### Issue 1: Fabricated Ukrainian Expression — "со́нце-життя́"
- **Location**: Line 86, Section "Культурний код та підсумок (Cultural Code and Summary)"
- **Original**: 「We say **со́нце-життя́** (Sun-Life) because the neuter sun is an impartial, balancing force for all living things.」
- **Problem**: "Земля-мати" (Mother Earth) is a well-established Ukrainian expression. "Сонце-життя" is NOT a standard Ukrainian compound noun or cultural concept. RAG textbook search returned no matches. VESUM does not list it. This appears to be an LLM fabrication presented as a real cultural expression. The plan itself lists it (line 63: "сонце-життя"), so this is a plan-inherited error, but the content should not present fabricated expressions as cultural facts.
- **Fix**: Replace with a real Ukrainian expression or reframe. E.g., refer to "ясне сонце" (bright sun) or "красне сонечко" (dear little sun) — both genuine folk expressions. Or simply drop the parallel and keep only земля-мати.
- **Severity**: HIGH

### Issue 2: Missing Plan Objective — 4 Declension Families
- **Location**: Entire module; plan objective #2: "Learner can categorize nouns into 4 declension families"
- **Problem**: The content only mentions "Family 4" once in passing (line 47: 「belongs to a special historical group (Family 4)」). There is no systematic presentation of what the 4 declension families are, how they differ, or how to categorize nouns into them. This is a plan objective that is entirely unmet.
- **Fix**: Add a brief overview table or callout box in section "Презентація правил (Presentation of Rules)" that previews the 4 families at recognition level (not full detail). E.g., a `[!did-you-know]` box explaining the 4 families exist and that learners will explore them more in later modules.
- **Severity**: MEDIUM

### Issue 3: Low Immersion (8.5% vs 15-35% target)
- **Location**: Whole module
- **Problem**: Module 7 falls in the 6-10 band, targeting 15-35% Ukrainian. At 8.5%, the immersion is well below minimum. Most Ukrainian appears only as bolded inline words with immediate English translations.
- **Fix**: Add 2-3 short Ukrainian reading practice blocks after key sections. E.g., after section "Практичні вправи (Practice Exercises)", add a 3-4 sentence block: "Це мій стіл. Стіл великий. А це моя книга. Книга цікава." These simple, repetitive sentences increase immersion without overwhelming the learner.
- **Severity**: MEDIUM

### Issue 4: Only 1 Engagement Box (need ≥2)
- **Location**: Only 「[!tip] The Golden Rule of Practice」 on line 49
- **Problem**: Audit reports engagement: 1/2. The module needs at least 2 engagement callout boxes. There are no `[!did-you-know]`, `[!culture]`, or `[!fun-fact]` boxes.
- **Fix**: Add a `[!did-you-know]` box. Natural candidate: a box in section "Культурний код та підсумок (Cultural Code and Summary)" about the cultural significance of земля-мати in Ukrainian folklore, or a box in section "Вступ (Introduction)" noting that Ukrainian has 3 genders while English lost its gender system centuries ago.
- **Severity**: MEDIUM

### Issue 5: Vocabulary YAML Missing Prose Words
- **Location**: Vocabulary file (`the-gender-code.yaml`)
- **Problem**: хліб (line 15), кімната (line 17), чоловік (line 53), жінка (line 54) all appear as teaching examples in the prose and/or activities but are absent from the vocabulary YAML. хліб is used in pattern recognition examples and the group-sort activity. кімната is used in the pattern recognition and match-up activity. чоловік and жінка are used in the categorization drill.
- **Fix**: Add all 4 words to the vocabulary YAML as supplementary items.
- **Severity**: LOW

### Issue 6: LLM Structural Monotony — "Let's..." Openings
- **Location**: Section openings
- **Problem**: 3 sections begin with "Let's..." variants: "Let's start with a beautiful cultural hook" (line 7, section "Вступ (Introduction)"), "Now, let's look at how we can actually predict" (line 13, section "Презентація правил (Presentation of Rules)"), "Let's dive into some practical exercises" (line 40, section "Практичні вправи (Practice Exercises)"). This is a structural monotony pattern.
- **Fix**: Vary section openings. E.g., section "Практичні вправи (Practice Exercises)" could open with "Time to put those rules to the test!" instead.
- **Severity**: LOW

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 86 | 「со́нце-життя́」 | Remove or replace with "красне сонечко" | Fabricated compound |
| 84 | "memorised" | "memorized" | Spelling inconsistency (British/American) |

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 8.2)

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Line 5: Replace 「This system is the heartbeat of the language」 with a simpler statement like "This system is the foundation of the language" — removes stacked metaphor
2. Line 86: Remove the fabricated 「со́нце-життя́」 and replace with genuine folk reference or simply expand земля-мати discussion
3. Vary section openings — change at least 1 of the 3 "Let's..." openings

**Expected score after fix:** 8/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 84: "memorised" → "memorized" for consistency
2. Line 86: Remove fabricated "сонце-життя" — this is a language accuracy issue when presenting Ukrainian cultural concepts

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add a brief declension families preview (callout box) in section "Презентація правил (Presentation of Rules)" to address the missing plan objective
2. Add 1 engagement box (e.g., `[!did-you-know]`) to meet richness gate

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add a second engagement callout box (fixes richness gate)
2. Add 2-3 short Ukrainian reading practice blocks (fixes immersion gap)

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Add a quiz or fill-in activity that tests він/вона/воно pronoun assignment for objects (matching the "It Trap" teaching in section "Самостійна робота (Independent Work/Production)")

**Expected score after fix:** 9/10

### Projected Overall After Fixes
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9 = (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 8.0 + 13.5) / 8.9 = 79.1 / 8.9 = **8.9/10**

---

## Audit Failures (from automated re-audit)

```
❌ Structure check failed: Missing '## Summary'
✨ Purity violations found: 1
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'it goes...'.
--- STRICT GATES (Level A1) ---
Structure    ❌ Missing '## Summary'
Pedagogy     ❌ 1 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
[ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'it goes...'.
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 35/100)
→ 4 violations (moderate)
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

Welcome to a fascinating new dimension of the Ukrainian language! You are doing incredibly well on your journey, and today we are unlocking one of the most fundamental concepts: the three-gender system. In Ukrainian, absolutely every noun has a specific gender: Masculine, Feminine, or Neuter. 

For English speakers, it is crucial to remember that grammatical gender is not about biology or people. It is simply a linguistic category, a way of organizing words into three distinct buckets. Every object, idea, or feeling falls into one of these categories. A table, a thought, and a house all have a gender. This system is the foundation of the language, and once you learn the basic patterns, everything else—like adjectives and pronouns—will naturally click into place.

Let's start with a beautiful cultural hook: the Ukrainian sun. In many Romance languages, the sun is masculine (like *el sol* in Spanish or *le soleil* in French). But the Ukrainian **со́нце** (sun) is neuter. In Ukrainian folklore, the sun is not a gendered deity or a harsh warrior; it is an impartial, gentle life-giver. This perfectly captures the essence of the neuter gender—it is balanced, neutral, and essential.

To help you remember, we are going to use a simple Visual Mnemonic Framework. Imagine three colors for our three buckets. Think of Blue for Masculine (words that feel "solid" and end in a hard consonant). Think of Red for Feminine (words that feel "open" and end with an -a sound). And think of Yellow for Neuter (words that feel "round" and balanced, ending in an -o or -e). Keep these colors in your mind, and categorizing words will become second nature!

## Презентація правил (Presentation of Rules)

Now, let's look at how we can actually predict a word's gender just by looking at its ending. The great news is that Ukrainian gender is highly predictable. About 95% of the time, the last letter of the word tells you exactly which bucket it belongs in. Let's break down this Pattern Recognition.

For the Masculine gender (our Blue bucket), look for words that end in a consonant. These words have a strong, firm stop at the end. Great examples are **стіл** (table), **хліб** (bread), and **дім** (house). 

For the Feminine gender (our Red bucket), look for the open, airy sounds of -а or -я at the end. You will see this everywhere: **кни́га** (book), **кімна́та** (room), and **земля́** (earth). 

For the Neuter gender (our Yellow bucket), look for the soft, rounded vowels -о or -е. Classic examples include **вікно́** (window), **мі́сто** (city), and **мо́ре** (sea). 

To test our words, we use a diagnostic tool: possessive pronouns. In English, we say "my" for everything. In Ukrainian, "my" changes to match the noun. We use **мій** for Masculine, **моя́** for Feminine, and **моє́** for Neuter. This is the absolute best way to check gender agreement and identity. 

This Syntactic Agreement means that gender also dictates the form of adjectives. If the noun is masculine, the adjective must match. Here are some examples:

> [!tip] The Four Families
> Ukrainian nouns are grouped into 4 declension families based on gender and ending. Family 1 = most masculine nouns (стіл, брат). Family 2 = most feminine nouns ending in -а/-я (книга, земля). Family 3 = feminine nouns ending in a soft sign (ніч). Family 4 = neuter nouns ending in -я with a special plural (ім'я → імена). You do not need to memorize these yet — just know they exist!
* **вели́кий стіл** (big table) — Masculine
* **ціка́ва кни́га** (interesting book) — Feminine
* **чи́сте вікно́** (clean window) — Neuter

Let's see this in action with high-frequency family vocabulary. Sometimes, natural biology aligns perfectly with grammatical rules. 

> **Вдо́ма (At home)**
> — Хто це?
> — Це мій **брат**. А це моя́ **сестра́**.
> — А де **ма́ма** і **та́то**?
> — **Ма́ма** тут, і **та́то** тут.

Notice how **сестра́** (sister) and **ма́ма** (mother) end in -а, making them feminine (**моя́**). Meanwhile, **брат** (brother) ends in a consonant, making it masculine (**мій**). But what about **та́то** (father)? It ends in -o, which usually means neuter! We'll explore this fascinating trap in the next section. You are doing great—take a breath, and let's keep going!

## Практичні вправи (Practice Exercises)

Time to put those rules to the test! As we noted, rules have exceptions, and these exceptions are usually tied to deep, natural logic. The most common Natural Gender Override Trap is the word **та́то** (father). By the strict grammatical rule, ending in -o should place it in the Neuter (Yellow) bucket. However, biological sex always overrides the written ending. Because a father is a man, **та́то** is Masculine. Therefore, we say **мій та́то**, never ~~моє тато~~. Contrast this with the word **мі́сто** (city), which is a true neuter word because it is an inanimate object: **моє́ мі́сто**. 

Next, we encounter the Soft Sign Ambiguity. Words ending in the soft sign (ь) can be either Masculine or Feminine, and there is no simple rule—you just have to memorize them as you learn them. Let's look at a critical, high-frequency minimal pair:
* **день** (day) is Masculine. We say: гарний **день** (good day).
* **ніч** (night) is Feminine. We say: добра **ніч** (good night).
The best strategy for memorizing these essential 'soft' exceptions is to learn them in pairs. When you learn **день**, immediately pair it with **ніч** and remember their different genders.

Another tricky exception is the 'Name' Trap. The word **ім'я́** (name) ends in -я. Normally, -я means Feminine, just like **земля́** (earth). However, **ім'я́** belongs to a special historical group (Family 4) and is actually Neuter! This causes common learner confusion. To avoid this, always learn the pronoun with it: **моє́ ім'я́** (my name), contrasting with **моя́ земля́** (my earth).

> [!tip] The Golden Rule of Practice
> Whenever you learn a new noun, always say it out loud with its matching "my" pronoun. Don't just learn **соба́ка** (dog); learn **моя́ соба́ка**. Don't just learn **серце** (heart); learn **моє́ се́рце**. This builds muscle memory!

Let's do a quick categorization drill with high-frequency nouns. Imagine you have our three colored buckets:
* **чолові́к** (man) ends in a consonant (к). It goes in the Blue bucket: Masculine (**мій чолові́к**).
* **жі́нка** (woman) ends in -а. It goes in the Red bucket: Feminine (**моя́ жі́нка**).
* **мі́сто** (city) ends in -о. It goes in the Yellow bucket: Neuter (**моє́ мі́сто**).

You are doing wonderfully. Grasping these concepts takes time, but you are building a rock-solid foundation for everything that follows!

## Самостійна робота (Independent Work/Production)

Now it is time for you to take the wheel. We need to tackle one of the most common habits for English speakers: The "It" Trap. In English, if an object isn't a person or a pet, we call it "it". But in Ukrainian, objects have true genders, which means we must use gendered pronouns for them!

If you are talking about a table (**стіл**, Masculine), you cannot use a neuter pronoun. You must use **він** (he). 
If you are talking about a book (**кни́га**, Feminine), you must use **вона́** (she). 
Only true neuter words like **вікно́** (window) take the neuter pronoun **воно́** (it).
Targeted drill: Stop using **воно́** for everything! A house (**дім**) is **він**. The earth (**земля́**) is **вона́**.

Let's make this more fun by mapping gender to modern contexts. If you are familiar with the famous Ukrainian video game franchise S.T.A.L.K.E.R., you can use its iconic vocabulary as classification anchors for our three buckets:
* **Артефа́кт** (Artifact) — Ends in a hard consonant (т). It is Masculine. (**Він** / **мій артефа́кт**).
* **Зо́на** (Zone) — Ends in -а. It is Feminine. (**Вона́** / **моя́ зо́на**).
* **Укриття́** (Shelter) — Ends in -я but follows the special neuter pattern. It is Neuter. (**Воно́** / **моє́ укриття́**).

Now, let's practice applying agreement by creating simple descriptive phrases for personal items and nature terms. Combine **мій / моя́ / моє́** with a basic adjective and a noun:
* **мій нови́й дім** (my new house)
* **моя́ ціка́ва кни́га** (my interesting book)
* **моє́ вели́ке мі́сто** (my big city)
* **мій ста́рший брат** (my older brother)
* **моя́ моло́дша сестра́** (my younger sister)

Try walking around your own room right now. Point to a table and say **мій стіл**. Point to a window and say **моє́ вікно́**. The more you actively connect the physical objects to their grammatical gender, the faster your brain will absorb the "Gender Code."

## Культурний код та підсумок (Cultural Code and Summary)

You have successfully unlocked the Gender Code! Let's summarize the key principles that will guide you forward. First, remember the 95% predictability rule: consonant endings mean Masculine, -а/-я endings mean Feminine, and -о/-е endings mean Neuter. Second, be aware of the "Soft Sign" exceptions, like **день** (M) and **ніч** (F), which must be memorized. Third, never forget that Natural Gender always wins—a biological male like **та́то** is Masculine, despite the -o ending. 

Understanding gender is not just about grammar; it reflects the Ukrainian worldview. Consider the personification of nature. We say **земля́-ма́ти** (Mother Earth) because the land is feminine, nurturing, and deeply connected to the concept of motherhood. The neuter **со́нце** is an impartial life-giver — in folk songs it is "красне сонечко" (dear little sun), a balanced force that does not take sides. The language breathes personality into the world around us.

> [!did-you-know] Grammatical Gender as a Window
> English once had three genders too! Old English had masculine, feminine, and neuter — just like modern Ukrainian. Over centuries, English lost this system. Ukrainian kept it, and it gives every noun a distinct personality. When you learn **мій стіл** and **моя́ кни́га**, you are tapping into a thousand-year-old tradition that English speakers left behind.

To finish, let's do a Final Competency Check. Can you confidently identify the gender for these core identity words?
1. **ім'я́** (name) — Did you say Neuter? Correct! It is an exception.
2. **та́то** (father) — Did you say Masculine? Excellent! Natural gender overrides the -o.
3. **ма́ма** (mother) — Feminine, ending in -а.
4. **мі́сто** (city) — Neuter, ending in -о.

You have mastered a huge milestone today. Take pride in your progress — you are building the foundation for everything that comes next. Keep up the fantastic work!

> **Читаймо! (Let's read!)**
> Це мій стіл. Стіл вели́кий. А це моя́ кни́га. Кни́га ціка́ва. Де моє́ вікно́? Вікно́ тут. А де мій брат? Брат тут. І моя́ сестра́ тут. Це моє́ мі́сто. Мі́сто вели́ке!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-gender-code.yaml`

```yaml
- type: match-up
  title: Match Nouns to Their Meanings
  instruction: Match each Ukrainian noun to its English translation. Pay attention
    to the word endings — they reveal the gender!
  pairs:
  - left: стіл
    right: table
  - left: книга
    right: book
  - left: вікно
    right: window
  - left: море
    right: sea
  - left: земля
    right: earth
  - left: сонце
    right: sun
  - left: хліб
    right: bread
  - left: кімната
    right: room
- type: quiz
  title: Identify the Gender
  instruction: Choose the correct gender for each Ukrainian noun.
  items:
  - question: What gender is стіл (table)?
    options:
    - text: Masculine
      correct: true
    - text: Feminine
      correct: false
    - text: Neuter
      correct: false
    - text: No gender
      correct: false
    explanation: Стіл ends in a consonant (л), which is the main pattern for Masculine
      nouns.
  - question: What gender is книга (book)?
    options:
    - text: Masculine
      correct: false
    - text: Feminine
      correct: true
    - text: Neuter
      correct: false
    - text: No gender
      correct: false
    explanation: Книга ends in -а, which is the main pattern for Feminine nouns.
  - question: What gender is вікно (window)?
    options:
    - text: Masculine
      correct: false
    - text: Feminine
      correct: false
    - text: Neuter
      correct: true
    - text: No gender
      correct: false
    explanation: Вікно ends in -о, which is the main pattern for Neuter nouns.
  - question: What gender is тато (father)?
    options:
    - text: Masculine
      correct: true
    - text: Feminine
      correct: false
    - text: Neuter
      correct: false
    - text: No gender
      correct: false
    explanation: Тато ends in -о, which normally means Neuter. But natural gender
      always wins — a father is male, so тато is Masculine.
  - question: What gender is ніч (night)?
    options:
    - text: Masculine
      correct: false
    - text: Feminine
      correct: true
    - text: Neuter
      correct: false
    - text: No gender
      correct: false
    explanation: Ніч ends in a soft sign (ь). Words ending in ь can be Masculine or
      Feminine — ніч is Feminine and must be memorized.
  - question: What gender is день (day)?
    options:
    - text: Masculine
      correct: true
    - text: Feminine
      correct: false
    - text: Neuter
      correct: false
    - text: No gender
      correct: false
    explanation: День ends in a soft sign (ь). Unlike ніч (Feminine), день is Masculine
      — learn them as a pair to remember the difference.
  - question: What gender is ім'я (name)?
    options:
    - text: Masculine
      correct: false
    - text: Feminine
      correct: false
    - text: Neuter
      correct: true
    - text: No gender
      correct: false
    explanation: Ім'я ends in -я, which normally means Feminine. But ім'я belongs
      to a special historical group and is actually Neuter — моє ім'я.
  - question: Which possessive pronoun goes with море (sea)?
    options:
    - text: моє
      correct: true
    - text: мій
      correct: false
    - text: моя
      correct: false
    - text: мої
      correct: false
    explanation: Море ends in -е, making it Neuter. Neuter nouns take the possessive
      моє.
- type: fill-in
  title: Choose the Correct Possessive
  instruction: Fill in the blank with the correct form of 'my' in Ukrainian.
  items:
  - sentence: Це ___ стіл.
    answer: мій
    options:
    - мій
    - моя
    - моє
    - мої
    explanation: Стіл is Masculine (ends in consonant), so it takes мій.
  - sentence: Це ___ книга.
    answer: моя
    options:
    - мій
    - моя
    - моє
    - мої
    explanation: Книга is Feminine (ends in -а), so it takes моя.
  - sentence: Це ___ вікно.
    answer: моє
    options:
    - мій
    - моя
    - моє
    - мої
    explanation: Вікно is Neuter (ends in -о), so it takes моє.
  - sentence: Де ___ брат?
    answer: мій
    options:
    - мій
    - моя
    - моє
    - мої
    explanation: Брат is Masculine (ends in consonant), so it takes мій.
  - sentence: Це ___ сестра.
    answer: моя
    options:
    - мій
    - моя
    - моє
    - мої
    explanation: Сестра is Feminine (ends in -а), so it takes моя.
  - sentence: Це ___ місто.
    answer: моє
    options:
    - мій
    - моя
    - моє
    - мої
    explanation: Місто is Neuter (ends in -о), so it takes моє.
  - sentence: Це ___ дім.
    answer: мій
    options:
    - мій
    - моя
    - моє
    - мої
    explanation: Дім is Masculine (ends in consonant), so it takes мій.
  - sentence: Це ___ тато.
    answer: мій
    options:
    - мій
    - моя
    - моє
    - мої
    explanation: Тато ends in -о, but natural gender wins — a father is male, so тато
      is Masculine and takes мій.
- type: match-up
  title: Match the Descriptive Phrase
  instruction: Match each Ukrainian phrase to its English meaning. Notice how the
    adjective ending changes to match the noun's gender.
  pairs:
  - left: великий стіл
    right: big table
  - left: цікава книга
    right: interesting book
  - left: чисте вікно
    right: clean window
  - left: синє море
    right: blue sea
  - left: добра ніч
    right: good night
  - left: гарний день
    right: good day
  - left: моя сестра
    right: my sister
  - left: мій брат
    right: my brother
- type: group-sort
  title: Sort Nouns by Gender
  instruction: Place each noun into the correct gender bucket.
  groups:
  - name: Masculine (мій)
    items:
    - стіл
    - хліб
    - дім
    - брат
    - день
  - name: Feminine (моя)
    items:
    - книга
    - кімната
    - земля
    - сестра
    - ніч
  - name: Neuter (моє)
    items:
    - вікно
    - місто
    - море
    - сонце
    - серце
- type: true-false
  title: True or False?
  instruction: Decide whether each statement about Ukrainian gender is true or false.
  items:
  - statement: Ukrainian nouns ending in a consonant are usually Masculine.
    correct: true
    explanation: Correct! Consonant endings are the main pattern for Masculine nouns,
      like стіл, хліб, дім.
  - statement: Ukrainian nouns ending in -а or -я are usually Neuter.
    correct: false
    explanation: 'Nouns ending in -а or -я are usually Feminine, not Neuter. Examples:
      книга, земля, сестра.'
  - statement: The word тато (father) is Neuter because it ends in -о.
    correct: false
    explanation: Тато ends in -о, but natural gender always wins. A father is male,
      so тато is Masculine.
  - statement: The correct form is "мій брат" because брат is Masculine.
    correct: true
    explanation: Брат ends in a consonant and refers to a male person — it is Masculine
      and takes мій.
  - statement: All nouns ending in a soft sign (ь) are Feminine.
    correct: false
    explanation: Not all! День (day) ends in ь but is Masculine. Ніч (night) ends
      in ь and is Feminine. You must memorize these.
  - statement: The word ім'я (name) is Feminine because it ends in -я.
    correct: false
    explanation: Ім'я looks Feminine because of the -я ending, but it belongs to a
      special group and is actually Neuter — моє ім'я.
  - statement: In Ukrainian, you say він (he) when talking about a table because стіл
      is Masculine.
    correct: true
    explanation: Correct! Unlike English where objects are 'it', Ukrainian uses gendered
      pronouns. Стіл is Masculine, so it is він.
  - statement: The possessive моє is used with Neuter nouns like вікно and місто.
    correct: true
    explanation: Correct! Вікно and місто both end in -о (Neuter), so they take the
      possessive моє.
- type: anagram
  title: Unscramble the Noun
  instruction: Rearrange the letters to form the correct Ukrainian noun from this
    lesson.
  items:
  - scrambled: т а р б
    answer: брат
  - scrambled: а г к и н
    answer: книга
  - scrambled: н о к в і
    answer: вікно
  - scrambled: о т с і м
    answer: місто
  - scrambled: л я з м е
    answer: земля
  - scrambled: е ц р с е
    answer: серце
  - scrambled: е ц н о с
    answer: сонце
  - scrambled: а р т с е с
    answer: сестра
- type: unjumble
  title: Put the Words in Order
  instruction: Arrange the words to form a correct Ukrainian sentence.
  items:
  - words:
    - стіл
    - Це
    - мій
    answer: Це мій стіл
  - words:
    - книга
    - моя
    - Це
    answer: Це моя книга
  - words:
    - моє
    - Це
    - вікно
    answer: Це моє вікно
  - words:
    - мій
    - Це
    - брат
    answer: Це мій брат
  - words:
    - Це
    - сестра
    - моя
    answer: Це моя сестра
  - words:
    - тато
    - мій
    - Це
    answer: Це мій тато

```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-gender-code.yaml`

```yaml
items:
  - lemma: "брат"
    translation: "brother"
    pos: "noun"
    gender: "m"
    usage: "старший брат (older brother)"
    example: "Це мій брат."
  - lemma: "сестра"
    translation: "sister"
    pos: "noun"
    gender: "f"
    usage: "молодша сестра (younger sister)"
    example: "Це моя сестра."
  - lemma: "мама"
    translation: "mother, mom"
    pos: "noun"
    gender: "f"
    usage: "люба мама (dear mom)"
    example: "Мама тут."
  - lemma: "тато"
    translation: "father, dad"
    pos: "noun"
    gender: "m"
    notes: "Natural gender overrides the -о ending. Masculine, not Neuter."
    example: "Це мій тато."
  - lemma: "дім"
    translation: "house, home"
    pos: "noun"
    gender: "m"
    usage: "новий дім (new house)"
    example: "Це мій дім."
  - lemma: "вікно"
    translation: "window"
    pos: "noun"
    gender: "n"
    usage: "чисте вікно (clean window)"
    example: "Це моє вікно."
  - lemma: "книга"
    translation: "book"
    pos: "noun"
    gender: "f"
    usage: "цікава книга (interesting book)"
    example: "Це моя книга."
  - lemma: "місто"
    translation: "city"
    pos: "noun"
    gender: "n"
    usage: "велике місто (big city)"
    example: "Це моє місто."
  - lemma: "стіл"
    translation: "table"
    pos: "noun"
    gender: "m"
    usage: "великий стіл (big table)"
    example: "Це мій стіл."
  - lemma: "море"
    translation: "sea"
    pos: "noun"
    gender: "n"
    usage: "синє море (blue sea)"
    example: "Це моє море."
  - lemma: "ніч"
    translation: "night"
    pos: "noun"
    gender: "f"
    notes: "Feminine soft-sign exception. Memorize as a pair with день."
    example: "Добра ніч!"
  - lemma: "день"
    translation: "day"
    pos: "noun"
    gender: "m"
    notes: "Masculine soft-sign exception. Memorize as a pair with ніч."
    example: "Гарний день!"
  - lemma: "земля"
    translation: "earth, land"
    pos: "noun"
    gender: "f"
    usage: "рідна земля (native land)"
    example: "Це моя земля."
  - lemma: "серце"
    translation: "heart"
    pos: "noun"
    gender: "n"
    usage: "добре серце (kind heart)"
    example: "Це моє серце."
  - lemma: "сонце"
    translation: "sun"
    pos: "noun"
    gender: "n"
    notes: "Neuter — an impartial life-giver in Ukrainian folklore."
    example: "Сонце тут."
  - lemma: "собака"
    translation: "dog"
    pos: "noun"
    gender: "f"
    notes: "Feminine despite some colloquial masculine usage."
    example: "Це моя собака."
  - lemma: "ім'я"
    translation: "name"
    pos: "noun"
    gender: "n"
    notes: "Neuter exception (Family 4) despite the -я ending."
    example: "Це моє ім'я."
  - lemma: "артефакт"
    translation: "artifact"
    pos: "noun"
    gender: "m"
    notes: "S.T.A.L.K.E.R. cultural hook — consonant ending, Masculine."
    example: "Це мій артефакт."
  - lemma: "зона"
    translation: "zone"
    pos: "noun"
    gender: "f"
    notes: "S.T.A.L.K.E.R. cultural hook — ends in -а, Feminine."
    example: "Це моя зона."
  - lemma: "укриття"
    translation: "shelter"
    pos: "noun"
    gender: "n"
    notes: "S.T.A.L.K.E.R. cultural hook — Neuter despite -я ending."
    example: "Це моє укриття."
  - lemma: "хліб"
    translation: "bread"
    pos: "noun"
    gender: "m"
    usage: "свіжий хліб (fresh bread)"
    example: "Це мій хліб."
  - lemma: "кімната"
    translation: "room"
    pos: "noun"
    gender: "f"
    usage: "велика кімната (big room)"
    example: "Це моя кімната."
  - lemma: "чоловік"
    translation: "man, husband"
    pos: "noun"
    gender: "m"
    usage: "мій чоловік (my man/husband)"
    example: "Це мій чоловік."
  - lemma: "жінка"
    translation: "woman, wife"
    pos: "noun"
    gender: "f"
    usage: "моя жінка (my woman/wife)"
    example: "Це моя жінка."
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
