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



**NOTE: 6 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥30 items
  - Actual: Activity has 6 items
  - Fix: Add 24 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥30 items
  - Actual: Activity has 8 items
  - Fix: Add 22 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 6 items
  - Fix: Add 14 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥10 items
  - Actual: Activity has 8 items
  - Fix: Add 2 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥10 items
  - Actual: Activity has 6 items
  - Fix: Add 4 more items to 'fill-in' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Entire module — all sections, Line 3 and Line 92, Line 84, Section "Практичне застосування — Describing Outfits", Section "Презентація кольорів та граматика узгодження (Colors & Grammar of Agreement)", after line 32, Sections "Презентація кольорів та граматика узгодження (Colors & Grammar of Agreement)" (line 15), "Одяг — Clothing Vocabulary" (line 50 "Let's describe"), "Практичне застосування — Describing Outfits" (line 64)

### Finding 1: Zero Engagement Boxes (AUDIT GATE FAILURE)
**Location**: Entire module — all sections
**Problem**: The module contains zero callout boxes (`[!tip]`, `[!cultural-note]`, `[!did-you-know]`, `[!example]`, etc.). The audit requires minimum 1 for A1, and the richness gate shows `engagement: 0/2`. This is a FAIL condition. The cultural content in section "Вступ та культурний контекст (Introduction & Cultural Context)" (вишиванка symbolism, калина meaning) would be perfect in `[!culture]` or `[!did-you-know]` boxes. The soft-stem синій explanation in section "Презентація кольорів та граматика узгодження (Colors & Grammar of Agreement)" would benefit from a `[!tip]` box.
**Required Fix**: Add at least 2 engagement callout boxes:
**Severity**: HIGH

### Finding 2: LLM Filler Phrases — "language journey" (×2)
**Location**: Line 3 and Line 92
**Problem**: "As you continue your language journey" is an explicit LLM cliché pattern listed in the calibration. It appears twice — once in the opening and once in the closing.
**Required Fix**: Line 3: Replace with specific, module-oriented preview: "In this module, you'll learn to name colors and describe clothing — and you'll discover why Ukrainians see colors as much more than decoration." Line 92: Replace with "You can now look at any outfit and describe it in Ukrainian — colors, clothing, and all."
**Severity**: HIGH

### Finding 3: Structural Monotony — "Let's..." Openings
**Location**: Sections "Презентація кольорів та граматика узгодження (Colors & Grammar of Agreement)" (line 15), "Одяг — Clothing Vocabulary" (line 50 "Let's describe"), "Практичне застосування — Describing Outfits" (line 64)
**Problem**: Three H2 sections open with "Let's..." creating structural monotony (LLM Fingerprint ≤ 7 trigger).
**Required Fix**: Vary section openings. E.g., Line 64 could start: "Time to put everything together! You can describe..."
**Severity**: HIGH

### Finding 4: English-Ukrainian Mismatch on Line 84
**Location**: Line 84, Section "Практичне застосування — Describing Outfits"
**Problem**: The English says "beautifully embroidered" but the Ukrainian phrase is just 「біла сорочка」 (white shirt) — not "beautifully embroidered white shirt" (гарно вишита біла сорочка). This misleads learners about what the Ukrainian actually says. If the intended meaning is a вишиванка, it should say so.
**Required Fix**: Change to "with a **біла вишиванка** (white embroidered shirt)" or remove "beautifully embroidered" from the English.
**Severity**: HIGH

### Finding 5: Missed Pedagogical Hook — Ukrainian Flag Mnemonic
**Location**: Section "Презентація кольорів та граматика узгодження (Colors & Grammar of Agreement)", after line 32
**Problem**: The research notes identify the Ukrainian flag (синє небо + жовте поле) as "the cleanest mnemonic" for the hard/soft distinction. This excellent discovery exercise is absent from the content. It would naturally surface the question: "Why does синє look different from жовте?"
**Required Fix**: Add a `[!tip]` or `[!did-you-know]` box after line 32 using the flag mnemonic.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Zero Engagement Boxes (AUDIT GATE FAILURE)
- **Location**: Entire module — all sections
- **Problem**: The module contains zero callout boxes (`[!tip]`, `[!cultural-note]`, `[!did-you-know]`, `[!example]`, etc.). The audit requires minimum 1 for A1, and the richness gate shows `engagement: 0/2`. This is a FAIL condition. The cultural content in section "Вступ та культурний контекст (Introduction & Cultural Context)" (вишиванка symbolism, калина meaning) would be perfect in `[!culture]` or `[!did-you-know]` boxes. The soft-stem синій explanation in section "Презентація кольорів та граматика узгодження (Colors & Grammar of Agreement)" would benefit from a `[!tip]` box.
- **Fix**: Add at least 2 engagement callout boxes:
  1. A `[!culture]` box around the вишиванка protective-circle explanation (line 9)
  2. A `[!tip]` box for the синій soft-stem exception (line 32)

### Issue 2: LLM Filler Phrases — "language journey" (×2)
- **Location**: Line 3 and Line 92
- **Original (Line 3)**: 「As you continue your language journey, learning to describe what you and others are wearing is a big step.」
- **Original (Line 92)**: 「Being able to describe the world around you is a major milestone in your language journey.」
- **Problem**: "As you continue your language journey" is an explicit LLM cliché pattern listed in the calibration. It appears twice — once in the opening and once in the closing.
- **Fix**: Line 3: Replace with specific, module-oriented preview: "In this module, you'll learn to name colors and describe clothing — and you'll discover why Ukrainians see colors as much more than decoration." Line 92: Replace with "You can now look at any outfit and describe it in Ukrainian — colors, clothing, and all."

### Issue 3: Structural Monotony — "Let's..." Openings
- **Location**: Sections "Презентація кольорів та граматика узгодження (Colors & Grammar of Agreement)" (line 15), "Одяг — Clothing Vocabulary" (line 50 "Let's describe"), "Практичне застосування — Describing Outfits" (line 64)
- **Problem**: Three H2 sections open with "Let's..." creating structural monotony (LLM Fingerprint ≤ 7 trigger).
- **Fix**: Vary section openings. E.g., Line 64 could start: "Time to put everything together! You can describe..."

### Issue 4: English-Ukrainian Mismatch on Line 84
- **Location**: Line 84, Section "Практичне застосування — Describing Outfits"
- **Original**: 「A modern Ukrainian might pair **сині джинси** (blue jeans) with a beautifully embroidered **біла сорочка** (white shirt).」
- **Problem**: The English says "beautifully embroidered" but the Ukrainian phrase is just 「біла сорочка」 (white shirt) — not "beautifully embroidered white shirt" (гарно вишита біла сорочка). This misleads learners about what the Ukrainian actually says. If the intended meaning is a вишиванка, it should say so.
- **Fix**: Change to "with a **біла вишиванка** (white embroidered shirt)" or remove "beautifully embroidered" from the English.

### Issue 5: Missed Pedagogical Hook — Ukrainian Flag Mnemonic
- **Location**: Section "Презентація кольорів та граматика узгодження (Colors & Grammar of Agreement)", after line 32
- **Problem**: The research notes identify the Ukrainian flag (синє небо + жовте поле) as "the cleanest mnemonic" for the hard/soft distinction. This excellent discovery exercise is absent from the content. It would naturally surface the question: "Why does синє look different from жовте?"
- **Fix**: Add a `[!tip]` or `[!did-you-know]` box after line 32 using the flag mnemonic.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 84 | English "beautifully embroidered" + Ukrainian 「біла сорочка」 | Either 「біла вишиванка」 or drop "embroidered" from English | Translation mismatch |

**D.0 Pre-Screen Dismissals:**
- Agreement errors (items 1-8): ALL FALSE POSITIVES. The scanner matched words on the same line that belong to different phrases. E.g., line 28 has 「**червоний светр** (masculine) vs **червона сорочка** (feminine)」 — "червона" and "светр" are in separate pairs. Line 25 «червоний сорочка» is an intentional error example. All agreement in actual adj+noun pairs is correct.
- LOW_ENGAGEMENT (item 9): CONFIRMED — 0 engagement boxes, needs at least 1.

**VESUM Flag Dismissals:**
- `ий`, `ій`: grammatical suffixes discussed in prose, not standalone words.
- `синьа`: intentionally shown as incorrect form in activity explanation line 122.
- `штан`: intentionally cited as non-existent singular on line 56: 「You cannot have just one «штан» or one «джинс»!」

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 8.5)

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add 2+ engagement callout boxes: `[!culture]` for вишиванка symbolism, `[!tip]` for синій soft endings.
2. This also fixes the richness gate (engagement: 0/2 → 2/2).

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 3: Remove "As you continue your language journey" — replace with module-specific preview.
2. Line 92: Remove "major milestone in your language journey" — replace with concrete "You can now..." statement.
3. Line 84: Fix English-Ukrainian mismatch — either change Ukrainian to 「біла вишиванка」 or remove "beautifully embroidered" from English.

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Vary section openings — change at least 1 of the 3 "Let's..." starts to a different pattern.
2. Fixes from Language dimension (removing "language journey" ×2) also help here.

**Expected score after fix:** 8/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 8.0 + 13.5) / 8.9
= 79.1 / 8.9 = 8.9/10
```

---

## Audit Failures (from automated re-audit)

```
⚠️  Outline compliance: 0 errors, 1 warnings
⚠️ [EXTRA_SECTION_IN_MARKDOWN] Section 'Підсумок — Summary' found in markdown but not in outline.
--- STRICT GATES (Level A1) ---
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
⚠️  [SCORE_DRIFT_OUTLIER] Review mean score (8.4) is a 2σ outlier above track average (7.2 ± 0.4). This may indicate rubber-stamping. Re-examine scores critically.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/colors-and-clothing-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `ий` (source: prose)
  ❌ `штан` (source: prose)
  ❌ `ій` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/colors-and-clothing.md`

```markdown
## Вступ та культурний контекст (Introduction & Cultural Context)

Welcome! In this module, you'll learn to name colors, describe clothing, and match adjective endings — and you'll discover why Ukrainians see colors as much more than decoration. In Ukrainian culture, colors hold deep symbolic meaning, especially in our rich folk traditions.

Let's start with the symbolism of colors. In traditional Ukrainian art, poetry, and song, **червоний** (red) is the color of life, love, and vibrant energy. You will often see it connected to the **червона калина** (red viburnum), a beloved national symbol. In contrast, **чорний** (black) is not a color of sadness. Instead, it serves as a symbol of the fertile earth and ancient wisdom. We see this reflected in everyday phrases like **чорний хліб** (black bread). Meanwhile, **білий** (white) stands as a clear sign of purity and light.

In many ancient songs, **чорний** and **червоний** are described as two threads weaving the destiny of a person. The colors act as a visual language, speaking volumes before a single word is even spoken.

This beautiful color code comes alive in the traditional embroidered shirt, the **вишиванка**. For centuries, the **вишиванка** has been more than just a beautiful garment. It acts as a powerful talisman or amulet. The intricate embroidery on the collar and cuffs serves a specific function: it creates a protective circle around the person wearing it. This concept of "closing" the vulnerable energy zones of the body through patterns and colors is a key part of our heritage. A classic **вишиванка** often combines **червоний** and **чорний** on a **білий** background, creating a perfect balance of life, earth, and purity.

> [!culture] **Вишиванка — більше ніж сорочка**
> The **вишиванка** is not just fashion — it is one of the most powerful cultural symbols in Ukraine. Ukrainians wear вишиванки on national holidays, at weddings, and at important life events. Every region of Ukraine has its own distinctive embroidery patterns and color combinations. When you learn to describe a вишиванка's colors, you are reading a visual language that stretches back centuries.

Understanding this cultural context makes learning Ukrainian colors so much more meaningful. When you learn to say **червоний**, you are not just learning a vocabulary word; you are connecting with centuries of poetry and tradition.

## Презентація кольорів та граматика узгодження (Colors & Grammar of Agreement)

Let’s explore the basic colors according to the Ukrainian State Standard. Here are the essential colors you need to know:
- **білий** (white)
- **чорний** (black)
- **червоний** (red)
- **синій** (blue)
- **зелений** (green)
- **жовтий** (yellow)

Notice how almost all of these color words end in **-ий**. This is the standard ending for masculine adjectives in the dictionary form. As we learned in our previous module about describing things, Ukrainian adjectives must match the noun they describe in gender (masculine, feminine, or neuter). This is called gender agreement.

Let's practice the endings **-ий** (masculine), **-а** (feminine), and **-е** (neuter). A very common mistake for English speakers is to use the masculine dictionary form for everything, resulting in phrases like «червоний сорочка» (red shirt). But since **сорочка** is feminine, we must change the adjective!

Let’s look at some contrastive pairs to fix this:
- **червоний светр** (masculine) vs **червона сорочка** (feminine)
- **чорний кіт** (masculine) vs **чорна кава** (feminine)
- **білий дім** (masculine) vs **біле місто** (neuter)

Pay special attention to **синій** (blue). While most colors belong to the "hard group" and take **-ий** / **-а** / **-е**, the color **синій** belongs to the "soft group". This means its endings are slightly different to keep the soft sound: **-ій** for masculine, **-я** for feminine, and **-є** for neuter. For example, think of the sky and the sun: the sky is **синє небо** (neuter), while the sun is **жовте сонце** (neuter). We do not say «синьо небо» because the stem is soft!

> [!tip] **The Flag Trick — Hard vs. Soft at a Glance**
> Look at the Ukrainian flag: **синє небо** (blue sky) on top, **жовте поле** (yellow field) on the bottom. Both are neuter — but notice: **синє** ends in **-є** (soft group), while **жовте** ends in **-е** (hard group). The flag is your best mnemonic for the hard/soft difference!

Finally, you should know that Ukrainian has a few borrowed color words that never change their endings, no matter what gender the noun is. These invariable colors include **бордо** (burgundy), **беж** (beige), and **хакі** (khaki). So, you can safely say **сукня бордо** (burgundy dress) or **куртка хакі** (khaki jacket) without worrying about matching the endings at all. These borrowed words are very handy when you are out shopping!

## Одяг — Clothing Vocabulary

Now that we have our colors ready, let's learn the essential vocabulary for the topic of clothing, or **одяг**. You will use the word **одяг** whenever you talk about apparel in general. Whether you are packing a suitcase or going shopping, knowing the specific names for your **одяг** is essential. Remember that the word **одяг** itself is masculine, so you could say **новий одяг** (new clothing).

Here are the most common items you will wear:
- **сорочка** (shirt) – feminine
- **штани** (pants) – plural
- **сукня** (dress) – feminine
- **плаття** (dress) – neuter
- **куртка** (jacket) – feminine
- **светр** (sweater) – masculine

You might notice that we have two words for a dress: **сукня** and **плаття**. What is the stylistic difference between these synonyms? The word **сукня** is often used for a more elegant or formal garment, like a **дорога сукня** (expensive dress). On the other hand, **плаття** is a more general conversational term, like a **нове плаття** (new dress).

Let’s describe clothing using our adjective and noun combinations. Remember, we don't need any verbs right now. We can just pair the color and the item to build great descriptive phrases. Let's do some gender agreement practice with our clothing vocabulary:
- For a masculine noun: **чорний светр** (black sweater), **синій светр** (blue sweater)
- For a feminine noun: **чорна куртка** (black jacket), **червона сукня** (red dress)
- For a neuter noun: **чорне плаття** (black dress), **біле плаття** (white dress)
- For a plural noun: **білі штани** (white pants)

Now, let's look closer at a special category of words known as *pluralia tantum*. These are words that only exist in the plural form, just like in English. In Ukrainian, **штани** (pants), **джинси** (jeans), and **окуляри** (glasses) belong to this group. You cannot have just one «штан» or one «джинс»!

Because these words are always plural, any adjective describing them must also take the plural ending **-і**. So, instead of trying to figure out if they are masculine or feminine, you simply use the plural form for all of them: **сині джинси** (blue jeans), **великі окуляри** (big glasses), or **нові штани** (new pants). 

If you want to point to these items, you use the plural demonstrative pronoun **ці** (these): **ці штани** (these pants) or **ці джинси** (these jeans). And if you need to count them, you cannot use the standard word for "one". Instead, you must use the special plural form **одні**, as in **одні штани** (one pair of pants) or **одні джинси** (one pair of jeans). This is a great trick to sound very natural in Ukrainian!

## Практичне застосування — Describing Outfits

Time to put everything together! You can describe what other people are wearing using simple, verb-free patterns. By combining the demonstrative pronoun **це** (this is) with your adjectives and nouns, you can build complete thoughts.

Here are some great verb-free patterns to describe outfits:
- **Це червона сукня.** (This is a red dress.)
- **Це біла сорочка.** (This is a white shirt.)
- **Ці штани — сині.** (These pants are blue.)
- **Мій светр — зелений.** (My sweater is green.)

Try practicing combining colors with clothing items and paying attention to gender agreement. If you see a friend wearing a beautiful jacket or looking at new denim, you can point and use these phrases:
- **Це гарна куртка.** (This is a beautiful jacket.)
- **Ці джинси — нові.** (These jeans are new.)

Let's also look at the cultural context of clothing in Ukraine today. Traditional clothing still influences the everyday style of Ukrainians. The colors of a **вишиванка** often vary by region. Some regions prefer bright geometric patterns, while others use subtle, intricate designs. When you describe these beautiful garments, you can use your new adjectives:
- **Це традиційна сорочка.** (This is a traditional shirt.)
- **Ця вишиванка — червона й чорна.** (This embroidered shirt is red and black.)

When you walk through a Ukrainian market, you can practice these phrases in your head. Look around and describe what you see:
- **Ця куртка — жовта.** (This jacket is yellow.)
- **Ця сукня — дуже гарна.** (This dress is very beautiful.)

Even in modern cities like Kyiv or Lviv, you will see a mix of contemporary fashion and traditional elements. A modern Ukrainian might pair **сині джинси** (blue jeans) with a **біла вишиванка** (white embroidered shirt). You now have all the tools you need to look at these outfits and describe them accurately and naturally. Keep practicing these verb-free combinations, and soon, matching the endings will feel completely automatic!

## Підсумок — Summary

You have done a fantastic job learning how to describe colors and clothing in Ukrainian! In this module, we explored the deep cultural symbolism behind colors like **червоний** and **чорний**, especially when looking at the traditional **вишиванка**. 

We also practiced matching our color adjectives with masculine, feminine, and neuter nouns. Remember the contrast: **чорний светр** vs **чорна куртка**. We discovered that **синій** uses soft endings, and we learned that plural-only words like **штани**, **джинси**, and **окуляри** always take the plural adjective ending **-і**. Finally, we used simple verb-free sentences to describe complete outfits without needing complicated grammar.

Take your time to review these concepts. You can now look at any outfit and describe it in Ukrainian — colors, clothing items, and all the right endings.

**Self-Check Questions:**
1. How do you say "red shirt" in Ukrainian, ensuring the adjective matches the feminine noun?
2. Which color word takes soft endings like **-я** and **-є** instead of the usual **-а** and **-е**?
3. What is the difference in style between **сукня** and **плаття**?
4. How do you describe "blue jeans", remembering that the word for jeans is always plural?
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/colors-and-clothing.yaml`

```yaml
- type: match-up
  title: "Match Colors to Their English Meanings"
  instruction: "Match each Ukrainian color word to its English translation."
  pairs:
    - left: "білий"
      right: "white"
    - left: "чорний"
      right: "black"
    - left: "червоний"
      right: "red"
    - left: "синій"
      right: "blue"
    - left: "зелений"
      right: "green"
    - left: "жовтий"
      right: "yellow"

- type: match-up
  title: "Match Colors to Clothing Items"
  instruction: "Match each color-clothing phrase to its English meaning."
  pairs:
    - left: "червона сукня"
      right: "red dress"
    - left: "чорний светр"
      right: "black sweater"
    - left: "біла сорочка"
      right: "white shirt"
    - left: "сині джинси"
      right: "blue jeans"
    - left: "зелена куртка"
      right: "green jacket"
    - left: "жовте плаття"
      right: "yellow dress"
    - left: "білі штани"
      right: "white pants"
    - left: "чорна кава"
      right: "black coffee"

- type: fill-in
  title: "Describe the Outfit"
  instruction: "Choose the correct color form to complete each sentence. Pay attention to gender agreement!"
  items:
    - sentence: "Це ___ сукня."
      answer: "червона"
      options: ["червоний", "червона", "червоне", "червоні"]
      explanation: "Сукня is feminine, so the adjective takes the feminine ending -а."
    - sentence: "Це ___ светр."
      answer: "чорний"
      options: ["чорний", "чорна", "чорне", "чорні"]
      explanation: "Светр is masculine, so the adjective keeps the masculine ending -ий."
    - sentence: "Це ___ плаття."
      answer: "біле"
      options: ["білий", "біла", "біле", "білі"]
      explanation: "Плаття is neuter, so the adjective takes the neuter ending -е."
    - sentence: "Ці штани — ___."
      answer: "сині"
      options: ["синій", "синя", "синє", "сині"]
      explanation: "Штани is plural, so the adjective takes the plural ending -і."
    - sentence: "Це ___ куртка."
      answer: "зелена"
      options: ["зелений", "зелена", "зелене", "зелені"]
      explanation: "Куртка is feminine, so the adjective takes the feminine ending -а."
    - sentence: "Це ___ сорочка."
      answer: "нова"
      options: ["новий", "нова", "нове", "нові"]
      explanation: "Сорочка is feminine, so the adjective takes the feminine ending -а."
    - sentence: "Це ___ небо."
      answer: "синє"
      options: ["синій", "синя", "синє", "сині"]
      explanation: "Небо is neuter, and синій is a soft adjective, so the neuter form is синє."
    - sentence: "Це ___ сонце."
      answer: "жовте"
      options: ["жовтий", "жовта", "жовте", "жовті"]
      explanation: "Сонце is neuter, so the adjective takes the neuter ending -е."

- type: fill-in
  title: "Shopping for Clothes"
  instruction: "Choose the correct word to complete each phrase you might use while shopping."
  items:
    - sentence: "Це гарна ___."
      answer: "куртка"
      options: ["куртка", "светр", "штани", "одяг"]
      explanation: "Гарна is feminine, so it must match a feminine noun — куртка."
    - sentence: "Ці джинси — ___."
      answer: "нові"
      options: ["новий", "нова", "нове", "нові"]
      explanation: "Джинси is plural, so the adjective takes the plural ending -і."
    - sentence: "Це дорога ___."
      answer: "сукня"
      options: ["сукня", "светр", "плаття", "штани"]
      explanation: "Дорога is feminine, so it matches the feminine noun сукня."
    - sentence: "Мій ___ — зелений."
      answer: "светр"
      options: ["светр", "куртка", "сукня", "штани"]
      explanation: "Мій and зелений are masculine forms, so they match the masculine noun светр."
    - sentence: "Це ___ одяг."
      answer: "новий"
      options: ["новий", "нова", "нове", "нові"]
      explanation: "Одяг is masculine, so the adjective takes the masculine ending -ий."
    - sentence: "Ця вишиванка — ___ й чорна."
      answer: "червона"
      options: ["червоний", "червона", "червоне", "червоні"]
      explanation: "Вишиванка is feminine, so the adjective takes the feminine ending -а."

- type: group-sort
  title: "Sort by Gender"
  instruction: "Sort these clothing and color words by the gender of the noun."
  groups:
    - name: "Masculine"
      items: ["светр", "одяг", "хліб", "дім"]
    - name: "Feminine"
      items: ["сорочка", "сукня", "куртка", "кава"]
    - name: "Neuter"
      items: ["плаття", "місто", "небо", "сонце"]

- type: true-false
  title: "True or False?"
  instruction: "Decide if each statement about Ukrainian colors and clothing is true or false."
  items:
    - statement: "The Ukrainian word синій uses different endings from most other colors because it belongs to the soft group."
      correct: true
      explanation: "Синій is a soft adjective, so its feminine form is синя and neuter is синє, not синьа/синьо."
    - statement: "Штани can be used in a singular form to mean one pant leg."
      correct: false
      explanation: "Штани is pluralia tantum — it only exists in the plural form, just like English pants."
    - statement: "The word червоний can describe a masculine noun without changing its ending."
      correct: true
      explanation: "Червоний is already in the masculine form, which is the dictionary form for adjectives."
    - statement: "To say white dress (neuter), you should say біла плаття."
      correct: false
      explanation: "Плаття is neuter, so you need the neuter form — біле плаття."
    - statement: "The color word бордо changes its ending to match the gender of the noun."
      correct: false
      explanation: "Бордо is a borrowed word and never changes — сукня бордо, светр бордо."
    - statement: "In Ukrainian culture, the color чорний symbolizes sadness and mourning."
      correct: false
      explanation: "In Ukrainian tradition, чорний symbolizes fertile earth and ancient wisdom, not sadness."
    - statement: "The plural adjective ending for colors is -і, as in білі штани."
      correct: true
      explanation: "All adjectives in the plural take the ending -і, regardless of the noun's gender."
    - statement: "Сукня and плаття both mean dress, but сукня is more formal and elegant."
      correct: true
      explanation: "Сукня is used for more elegant or formal garments, while плаття is a general conversational term."

- type: quiz
  title: "Colors and Clothing Knowledge Check"
  instruction: "Choose the correct answer."
  items:
    - question: "Which color is associated with life, love, and the калина in Ukrainian culture?"
      explanation: "Червоний is the color of life, love, and energy, closely connected to the червона калина symbol."
      options:
        - text: "червоний"
          correct: true
        - text: "чорний"
          correct: false
        - text: "білий"
          correct: false
        - text: "жовтий"
          correct: false
    - question: "What is the correct feminine form of the color зелений?"
      explanation: "Feminine adjectives take the ending -а, so зелений becomes зелена."
      options:
        - text: "зелена"
          correct: true
        - text: "зелене"
          correct: false
        - text: "зеленій"
          correct: false
        - text: "зелені"
          correct: false
    - question: "Which word means jacket in Ukrainian?"
      explanation: "Куртка is the Ukrainian word for jacket."
      options:
        - text: "куртка"
          correct: true
        - text: "сорочка"
          correct: false
        - text: "сукня"
          correct: false
        - text: "светр"
          correct: false
    - question: "What is special about words like штани, джинси, and окуляри?"
      explanation: "These are pluralia tantum — words that only exist in the plural form."
      options:
        - text: "They only exist in plural form"
          correct: true
        - text: "They are always masculine"
          correct: false
        - text: "They never take adjectives"
          correct: false
        - text: "They are borrowed words"
          correct: false
    - question: "How do you say blue jeans in Ukrainian?"
      explanation: "Джинси is plural, and синій in plural form is сині, so it is сині джинси."
      options:
        - text: "сині джинси"
          correct: true
        - text: "синій джинси"
          correct: false
        - text: "синя джинси"
          correct: false
        - text: "синє джинси"
          correct: false
    - question: "What is the neuter form of the color синій?"
      explanation: "Синій is a soft adjective, so its neuter form is синє, not синьо."
      options:
        - text: "синє"
          correct: true
        - text: "синьо"
          correct: false
        - text: "сине"
          correct: false
        - text: "синя"
          correct: false

- type: unjumble
  title: "Put the Words in Order"
  instruction: "Arrange the words to form a correct Ukrainian sentence."
  items:
    - words: ["сукня", "Це", "червона"]
      answer: "Це червона сукня"
    - words: ["сорочка", "біла", "Це"]
      answer: "Це біла сорочка"
    - words: ["зелений", "светр", "Мій"]
      answer: "Мій светр зелений"
    - words: ["нове", "плаття", "Це"]
      answer: "Це нове плаття"
    - words: ["куртка", "гарна", "Це"]
      answer: "Це гарна куртка"
    - words: ["сині", "штани", "Ці"]
      answer: "Ці штани сині"
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/colors-and-clothing.yaml`

```yaml
items:
  - lemma: "білий"
    translation: "white"
    pos: "adjective"
    notes: "Symbol of purity and light in Ukrainian tradition"
    usage: "біла сорочка, білий сніг"
  - lemma: "чорний"
    translation: "black"
    pos: "adjective"
    notes: "Symbol of fertile earth and ancient wisdom, not sadness"
    usage: "чорний хліб, чорна кава"
  - lemma: "червоний"
    translation: "red"
    pos: "adjective"
    notes: "Symbol of life, love, and energy; linked to червона калина"
    usage: "червона сукня, червона калина"
  - lemma: "синій"
    translation: "blue"
    pos: "adjective"
    notes: "Soft-group adjective; feminine синя, neuter синє"
    usage: "сині джинси, синій светр"
  - lemma: "зелений"
    translation: "green"
    pos: "adjective"
    usage: "зелена трава, зелений колір"
  - lemma: "жовтий"
    translation: "yellow"
    pos: "adjective"
    usage: "жовте сонце, жовтий лимон"
  - lemma: "сорочка"
    translation: "shirt"
    pos: "noun"
    gender: "f"
    notes: "The basis of the traditional вишиванка"
    usage: "біла сорочка, вишита сорочка"
  - lemma: "штани"
    translation: "pants"
    pos: "noun"
    notes: "Pluralia tantum — always plural; adjectives take -і ending"
    usage: "білі штани, нові штани"
  - lemma: "сукня"
    translation: "dress (formal/elegant)"
    pos: "noun"
    gender: "f"
    notes: "More formal than плаття"
    usage: "червона сукня, дорога сукня"
  - lemma: "куртка"
    translation: "jacket"
    pos: "noun"
    gender: "f"
    usage: "тепла куртка, зелена куртка"
  - lemma: "светр"
    translation: "sweater"
    pos: "noun"
    gender: "m"
    usage: "чорний светр, синій светр"
  - lemma: "плаття"
    translation: "dress (general/conversational)"
    pos: "noun"
    gender: "n"
    notes: "More casual synonym of сукня"
    usage: "нове плаття, біле плаття"
  - lemma: "джинси"
    translation: "jeans"
    pos: "noun"
    notes: "Pluralia tantum — always plural"
    usage: "сині джинси, нові джинси"
  - lemma: "окуляри"
    translation: "glasses"
    pos: "noun"
    notes: "Pluralia tantum — always plural"
    usage: "великі окуляри"
  - lemma: "одяг"
    translation: "clothing, apparel"
    pos: "noun"
    gender: "m"
    usage: "новий одяг"
  - lemma: "вишиванка"
    translation: "traditional Ukrainian embroidered shirt"
    pos: "noun"
    gender: "f"
    notes: "Cultural talisman; embroidery serves as protective symbols"
    usage: "червона й чорна вишиванка"
  - lemma: "калина"
    translation: "viburnum (guelder rose)"
    pos: "noun"
    gender: "f"
    notes: "National symbol of Ukraine; червона калина"
  - lemma: "гарний"
    translation: "beautiful, nice"
    pos: "adjective"
    usage: "гарна куртка, гарна сукня"
  - lemma: "новий"
    translation: "new"
    pos: "adjective"
    usage: "нове плаття, нові штани"
  - lemma: "дорогий"
    translation: "expensive, dear"
    pos: "adjective"
    usage: "дорога сукня"
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/colors-and-clothing.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/colors-and-clothing.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/colors-and-clothing.yaml`

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
