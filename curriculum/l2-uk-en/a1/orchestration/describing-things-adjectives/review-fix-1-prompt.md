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

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥25 items
  - Actual: Activity has 8 items
  - Fix: Add 17 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥25 items
  - Actual: Activity has 8 items
  - Fix: Add 17 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥25 items
  - Actual: Activity has 6 items
  - Fix: Add 19 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 6 items
  - Fix: Add 14 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 10 items
  - Fix: Add 5 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥8 items
  - Actual: Activity has 6 items
  - Fix: Add 2 more items to 'fill-in' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Line 43, section "Презентація: Тверда група (Presentation: Hard Stem Adjectives)", Line 94, section "Практика та Культурний контекст (Practice and Cultural Context)", Lines 29-32 and 67-70 (both presentation sections), Multiple, Section "Вступ: Світ прикметників (Introduction: The World of Adjectives)", Whole module

### Finding 1: ZERO Engagement Boxes (AUDIT GATE FAILURE)
**Location**: Whole module
**Problem**: The module contains 0 callout boxes (`> [!tip]`, `> [!example]`, `> [!cultural-note]`, `> [!did-you-know]`, etc.). The audit requires minimum 1 for A1, and the richness gate shows `engagement: 0/2`. This is the primary reason for AUDIT FAIL status.
**Required Fix**: Add at minimum 2 engagement callout boxes:
**Severity**: HIGH

### Finding 2: IPA-Banned Brackets on Line 43
**Location**: Line 43, section "Презентація: Тверда група (Presentation: Hard Stem Adjectives)"
**Problem**: The `[is]` notation triggers the IPA scanner (D.0 items #1-2). While contextually it means "omitted verb," square brackets are banned project-wide for IPA reasons.
**Required Fix**: Replace `[is]` with `(is)` or rephrase as "(The book — beautiful)" or use em-dash: "The book — beautiful"
**Severity**: HIGH

### Finding 3: Awkward Ukrainian on Line 94
**Location**: Line 94, section "Практика та Культурний контекст (Practice and Cultural Context)"
**Problem**: "Вона зелена Мавка" is grammatically strange — it reads as "She [is] green Mavka" which is an unnatural predicate + bare proper noun construction. In natural Ukrainian, this would be "Вона — зелена Мавка" (with a dash acting as copula) or simply "Зелена Мавка" as a noun phrase.
**Required Fix**: Change to `Вона — зелена Мавка.` or restructure as `Це зелена Мавка.`
**Severity**: HIGH

### Finding 4: No Grammar Paradigm Tables
**Location**: Lines 29-32 and 67-70 (both presentation sections)
**Problem**: The plan specifies "visual scaffolding with color-coded gender markers." The content uses emoji bullet lists, which are less scannable than actual markdown tables. For A1 beginners, clean paradigm tables are the standard presentation in Ukrainian textbooks (Grades 3-4).
**Required Fix**: Convert the bullet-list paradigms into proper markdown tables with gender headers.
**Severity**: HIGH

### Finding 5: Missing рідний Discovery Hook
**Location**: Section "Вступ: Світ прикметників (Introduction: The World of Adjectives)"
**Problem**: The research notes specifically recommend the Vashulenko Grade 3 рідний paradigm (рідний край / рідна мова / рідне слово / рідні люди) as a discovery warm-up — "Students see the pattern before the rule is stated." This textbook-grounded technique is absent. The content jumps from question words directly to Софійський собор without a pattern-discovery moment.
**Required Fix**: Add a short discovery exercise between the Який/Яка/Яке/Які introduction and the Софійський собор hook, presenting the рідний paradigm and asking learners to spot the pattern.
**Severity**: HIGH

### Finding 6: Linguistic Accuracy — AUTO-FAIL (score 8 < threshold 9)
**Location**: Multiple
**Problem**: The Linguistic Accuracy dimension scores 8/10 which is below the auto-fail threshold of 9. The issues are: (a) "[is]" bracket notation, (b) "Вона зелена Мавка" unnaturalness, (c) the word "синий" appearing in prose without clear error marking (asterisk prefix like *синий would be conventional). While "синий" is used pedagogically to show a common error, it should be typographically distinguished more clearly.
**Required Fix**: Fix items (a), (b), and mark "синий" with an asterisk prefix (*синий) to follow linguistic convention for erroneous forms.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: ZERO Engagement Boxes (AUDIT GATE FAILURE)
- **Location**: Whole module
- **Problem**: The module contains 0 callout boxes (`> [!tip]`, `> [!example]`, `> [!cultural-note]`, `> [!did-you-know]`, etc.). The audit requires minimum 1 for A1, and the richness gate shows `engagement: 0/2`. This is the primary reason for AUDIT FAIL status.
- **Fix**: Add at minimum 2 engagement callout boxes:
  1. A `> [!tip]` after line 34 about the gender mismatch rule (mnemonic aid)
  2. A `> [!cultural-note]` after line 15 about Софійський собор
  3. A `> [!did-you-know]` in section "Презентація 2: М'яка група та Специфіка" about the Kyiv Metro

### Issue 2: IPA-Banned Brackets on Line 43
- **Location**: Line 43, section "Презентація: Тверда група (Presentation: Hard Stem Adjectives)"
- **Original**: 「«Книга **гарна**» (The book [is] beautiful). «Дім **новий**» (The house [is] new).」
- **Problem**: The `[is]` notation triggers the IPA scanner (D.0 items #1-2). While contextually it means "omitted verb," square brackets are banned project-wide for IPA reasons.
- **Fix**: Replace `[is]` with `(is)` or rephrase as "(The book — beautiful)" or use em-dash: "The book — beautiful"

### Issue 3: Awkward Ukrainian on Line 94
- **Location**: Line 94, section "Практика та Культурний контекст (Practice and Cultural Context)"
- **Original**: 「Вона **зелена** Мавка. (She is a green Mavka, tied to nature.)」
- **Problem**: "Вона зелена Мавка" is grammatically strange — it reads as "She [is] green Mavka" which is an unnatural predicate + bare proper noun construction. In natural Ukrainian, this would be "Вона — зелена Мавка" (with a dash acting as copula) or simply "Зелена Мавка" as a noun phrase.
- **Fix**: Change to `Вона — зелена Мавка.` or restructure as `Це зелена Мавка.`

### Issue 4: No Grammar Paradigm Tables
- **Location**: Lines 29-32 and 67-70 (both presentation sections)
- **Problem**: The plan specifies "visual scaffolding with color-coded gender markers." The content uses emoji bullet lists, which are less scannable than actual markdown tables. For A1 beginners, clean paradigm tables are the standard presentation in Ukrainian textbooks (Grades 3-4).
- **Fix**: Convert the bullet-list paradigms into proper markdown tables with gender headers.

### Issue 5: Missing рідний Discovery Hook
- **Location**: Section "Вступ: Світ прикметників (Introduction: The World of Adjectives)"
- **Problem**: The research notes specifically recommend the Vashulenko Grade 3 рідний paradigm (рідний край / рідна мова / рідне слово / рідні люди) as a discovery warm-up — "Students see the pattern before the rule is stated." This textbook-grounded technique is absent. The content jumps from question words directly to Софійський собор without a pattern-discovery moment.
- **Fix**: Add a short discovery exercise between the Який/Яка/Яке/Які introduction and the Софійський собор hook, presenting the рідний paradigm and asking learners to spot the pattern.

### Issue 6: Linguistic Accuracy — AUTO-FAIL (score 8 < threshold 9)
- **Location**: Multiple
- **Problem**: The Linguistic Accuracy dimension scores 8/10 which is below the auto-fail threshold of 9. The issues are: (a) "[is]" bracket notation, (b) "Вона зелена Мавка" unnaturalness, (c) the word "синий" appearing in prose without clear error marking (asterisk prefix like *синий would be conventional). While "синий" is used pedagogically to show a common error, it should be typographically distinguished more clearly.
- **Fix**: Fix items (a), (b), and mark "синий" with an asterisk prefix (*синий) to follow linguistic convention for erroneous forms.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 43 | 「(The book [is] beautiful)」 | (The book _(is)_ beautiful) | IPA-banned notation |
| 72 | 「«**синий**»」 | «***синий**» or prefix with asterisk | Error form not marked conventionally |
| 94 | 「Вона **зелена** Мавка.」 | Вона — зелена Мавка. | Missing dash copula |

---

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Engagement Boxes: Add 2-3 callout boxes

**What to fix:**
1. After line 15 (Софійський собор): Add `> [!cultural-note]` about the cathedral's UNESCO status and significance
2. After line 34 (gender mismatch): Add `> [!tip]` with a mnemonic for remembering gender agreement
3. After line 66 (Kyiv Metro): Add `> [!did-you-know]` about the Metro line colors

**Expected impact:** Engagement 0→2+, richness gap closed, Experience Quality 8→9

### Linguistic Accuracy: Fix bracket notation + naturalness

**What to fix:**
1. Line 43: Change `[is]` to `_(is)_` or parenthetical
2. Line 94: Add dash — `Вона — зелена Мавка.`
3. Line 72: Mark error form with asterisk prefix

**Expected impact:** Linguistic Accuracy 8→9

### LLM Fingerprint: Vary section openings

**What to fix:**
1. Line 118: Replace 「You have successfully unlocked the power of description in Ukrainian!」with something specific: "You can now describe a нова квартира, an old Софійський собор, and a синє море — all with the right endings."
2. Vary at least one section opening — e.g., section "Презентація 2: М'яка група та Специфіка" could open with the Kyiv Metro hook instead of the generic "While most adjectives are hard..."

**Expected impact:** LLM Fingerprint 7→8

### Pedagogy: Add рідний discovery exercise

**What to fix:**
1. In section "Вступ: Світ прикметників", after line 13 (Які?), add the рідний paradigm discovery exercise from research notes.

**Expected impact:** Pedagogy 8→9

### Projected Overall After Fixes
```
Experience: 9×1.5 = 13.5
Language: 8×1.1 = 8.8
Pedagogy: 9×1.2 = 10.8
Activities: 8×1.3 = 10.4
Beginner Safety: 9×1.3 = 11.7
LLM Fingerprint: 8×1.0 = 8.0
Linguistic Accuracy: 9×1.5 = 13.5
Total: 76.7 / 8.9 = 8.6/10
```

---

## Audit Failures (from automated re-audit)

```
⚠️  Outline compliance: 2 errors, 2 warnings
❌ [MISSING_OUTLINE_SECTION] Section 'Вступ: Світ прикметників — Introduction: The World of Adjectives' defined in outline but not found in markdown.
❌ [MISSING_OUTLINE_SECTION] Section 'Презентація: Тверда група — Presentation: Hard Stem Adjectives' defined in outline but not found in markdown.
⚠️ [EXTRA_SECTION_IN_MARKDOWN] Section 'Вступ: Світ прикметників (Introduction: The World of Adjectives)' found in markdown but not in outline.
✨ Purity violations found: 1
❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (100% overlap): "You cannot use a masculine adjective with a feminine noun.". Shares significant keywords with sentence at index 21.
--- STRICT GATES (Level A1) ---
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 1 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• 2 Outline Compliance Errors
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/describing-things-adjectives-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: 2 Outline Compliance Errors
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `ий` (source: prose)
  ❌ `синий` (source: prose)
  ❌ `ій` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/describing-things-adjectives.md`

```markdown
<!-- adapted from: Vashulenko, Grade 3; Kravtsova, Grade 3-4; Avramenko, Grade 5 -->

## Вступ: Світ прикметників (Introduction: The World of Adjectives)

Welcome back! So far, you have learned how to name the world around you using nouns like **місто** (city), **дім** (house), and **кава** (coffee). You also know how to point to things using words like **цей** (this) and **той** (that). But what if you want to describe these things? What if the coffee is tasty, the house is big, or the city is ancient?

To do this, we need adjectives. In Ukrainian, adjectives are incredibly expressive and musical. They help us paint a vivid picture of the world.

> [!tip] 🔑 **The Golden Rule of Ukrainian Adjectives**
> In Ukrainian, adjectives must always **agree** with the noun they describe — in gender and number. Think of it like a dance: the noun leads, and the adjective follows its steps perfectly. 

Let's do a quick warm-up. Look around your room. If you wanted to describe the things you see, you would ask questions. In English, we simply ask "What kind of...?" But in Ukrainian, our questions change depending on the gender of the object:
*   **Який?** (What kind of? — Masculine)
*   **Яка?** (What kind of? — Feminine)
*   **Яке?** (What kind of? — Neuter)
*   **Які?** (What kind of? — Plural)

These questions are the master keys to describing everything in Ukrainian. But before we learn the rules, let's see if you can spot the pattern yourself. Look at these four phrases:

*   **рідний край** (native land)
*   **рідна мова** (native language)
*   **рідне слово** (native word)
*   **рідні люди** (native people)

What stays the same? What changes? You probably noticed that **рідн-** is always there — only the ending changes! That is the secret of Ukrainian adjectives: one root, different endings for different genders. You just discovered the rule before we even taught it!

> [!cultural-note] 🏛️ **Софійський собор — St. Sophia's Cathedral**
> If you visit Kyiv, you cannot miss **Софійський собор** — the historical heart of the city and a UNESCO World Heritage Site. We can describe it using two essential adjectives: it is **старий** (ancient) and **великий** (grand). Without adjectives, it is just a cathedral. With adjectives, it becomes an ancient and grand masterpiece. 

To use adjectives correctly, we must build on a foundation you already know: The Gender Code. In Ukrainian, every noun belongs to one of three genders: masculine, feminine, or neuter. 
*   **Стіл** (table) is a masculine noun.
*   **Кімната** (room) is a feminine noun.
*   **Вікно** (window) is a neuter noun.

Adjectives in Ukrainian are like mirrors: they reflect the gender of the noun they describe. The adjective agrees with the noun perfectly. You cannot use a masculine adjective with a feminine noun. They must match! Let's explore exactly how this beautiful agreement works.

## Презентація: Тверда група (Presentation: Hard Stem Adjectives)

In Ukrainian, most adjectives belong to the "Hard Stem" group. This simply means that the core part of the word ends in a hard consonant. For this group, the endings follow a very consistent and melodic pattern. Let's look at one of the most useful adjectives in the language: **новий** (new), alongside **гарний** (beautiful, nice).

Here is the secret formula for Hard Stem adjectives. We can visualize this with color codes to help your memory:
*   🟦 **Masculine (-ий)**: **новий дім** (new house), **гарний день** (beautiful day).
*   🟥 **Feminine (-а)**: **нова хата** (new house/cottage), **гарна кімната** (beautiful room).
*   🟨 **Neuter (-е)**: **нове місто** (new city), **гарне фото** (beautiful photo).
*   🟩 **Plural (-і)**: **нові двері** (new doors), **гарні речі** (beautiful things).

Notice how the ending changes? The dictionary form of an adjective is always the masculine form (**новий**, **гарний**). A very common error for English speakers is to take this dictionary form and use it for everything. You might be tempted to say «**новий** машина» (new car). However, because **машина** is feminine, using the masculine **новий** is like trying to fit a square peg into a round hole. It feels unnatural to a Ukrainian ear. The correct phrase is **нова машина**.

Let's practice correcting this gender mismatch with some common pairs. Compare the masculine and feminine forms:
*   **новий стіл** (new table) vs. **нова шафа** (new wardrobe)
*   **старий ліс** (old forest) vs. **стара школа** (old school)
*   **гарний кіт** (beautiful cat) vs. **гарна собака** (beautiful dog)

Where do we place these adjectives? Just like in English, adjectives usually go right before the noun. This is called the attributive position. For example, «Це **гарна** книга» (This is a beautiful book). 

But you can also place the adjective after the noun to make a statement, known as the predicative position. In English, we use the verb "to be" (The book is beautiful). In Ukrainian, in the present tense, we use the zero copula construction. We simply drop the verb "is" and put the noun and adjective together: «Книга **гарна**» (The book _(is)_ beautiful). «Дім **новий**» (The house _(is)_ new). Notice that the adjective ending remains exactly the same. The gender agreement is unbroken!

Now that you know the rules, let's expand your descriptive toolkit with some high-frequency opposites. Learning pairs is the fastest way to grow your vocabulary:
*   **великий** (big) / **малий** (small)
    *   «Це **велике** місто.» (This is a big city.)
    *   «Це **мале** село.» (This is a small village.)
*   **добрий** (good, kind) / **поганий** (bad)
    *   «Він **добрий** студент.» (He is a good student.)
    *   «Це **погана** кава.» (This is bad coffee.)
*   **дорогий** (expensive) / **дешевий** (cheap)
    *   «Це **дорогий** диван.» (This is an expensive sofa.)
    *   «Це **дешева** кава.» (This is cheap coffee.)
*   **смачний** (tasty)
    *   «Це **смачний** суп.» (This is a tasty soup.)
    *   «Це **смачна** риба.» (This is tasty fish.)
*   **цікавий** (interesting)
    *   «Це **цікавий** факт.» (This is an interesting fact.)
    *   «Це **цікаве** фото.» (This is an interesting photo.)

## Презентація 2: М'яка група та Специфіка (Presentation 2: Soft Stem and Nuances)

While most adjectives are hard, a special group of adjectives belongs to the "Soft Stem" group. Their endings are slightly different because the stem of the word ends in a soft consonant. The most famous example of a soft stem adjective is **синій** (blue). 

If you travel to Kyiv, a fantastic way to remember this is by riding the Kyiv Metro. The Metro has different lines, and the famous Blue Line is called **синя лінія** (blue line).

> [!did-you-know] 🚇 **Kyiv Metro Color Code**
> The Kyiv Metro has three lines. The Blue Line (**синя лінія**) is a soft stem adjective, while the Red Line (**червона лінія**) is a hard stem adjective. Real-world Ukrainian, right on your phone's map!

Let's look at the endings for the soft stem group:
*   🟦 **Masculine (-ій)**: **синій диван** (blue sofa), **синій телефон** (blue phone).
*   🟥 **Feminine (-я)**: **синя лампа** (blue lamp), **синя річ** (blue thing).
*   🟨 **Neuter (-є)**: **синє море** (blue sea), **синє небо** (blue sky).
*   🟩 **Plural (-і)**: **сині двері** (blue doors), **сині лампи** (blue lamps).

Because English speakers often rely on English phonetics, there is a strong tendency to misspell soft masculine adjectives. You might hear the word "siniy" and want to write «**синий**», using the hard **и** letter. This is a common error! Remember that the Ukrainian spelling for the soft masculine ending requires the letter **і** followed by **й**. It must be written as **синій**. 

Another soft stem detail involves the color red. While **синій** is soft, the color red, **червоний**, is actually a hard stem adjective! 
*   **червоний мак** (red poppy)
*   **червона шапка** (red hat)
*   **червоне яблуко** (red apple)

There is one wonderful piece of good news that makes plural adjectives very easy. Plural consistency! Whether the original noun was masculine, feminine, or neuter in its singular form, the plural adjective ending is always **-і**. You never have to worry about gender once you are talking about multiple things. 
*   **гарний день** (m) becomes **гарні дні** (beautiful days)
*   **гарна дівчина** (f) becomes **гарні дівчата** (beautiful girls)
*   **нове вікно** (n) becomes **нові вікна** (new windows)

Do not make the mistake of using singular feminine endings for plural nouns just because they look similar in English or other languages. It is never «гарна дні». It is always **гарні**!

## Практика та Культурний контекст (Practice and Cultural Context)

To really master these adjectives, let's step into two different worlds: the magical realm of Ukrainian folklore, and the practical world of an apartment hunt.

First, let's meet a legendary figure from Ukrainian culture. **Мавка** (Mavka) is a beautiful forest spirit from Lesya Ukrainka's famous poetic play "Forest Song" (Лісова пісня). Mavka is the soul of the forest. How would we describe her using our new feminine adjectives?
*   Вона **молода**. (She is young.)
*   Вона дуже **гарна**. (She is very beautiful.)
*   Вона **цікава**. (She is interesting.)
*   Вона — зелена Мавка. (She is a green Mavka, tied to nature.)

Notice how every single adjective perfectly matches her feminine gender, ending in **-а**. This repetition is the rhythm of the Ukrainian language.

Now, let's switch gears. Imagine you are a real estate agent in Lviv or Kyiv. You want to show a client an apartment and describe the rooms. This is where your vocabulary becomes extremely useful. Let's roleplay describing a property using what you know:
*   «Це **нова** квартира.» (This is a new apartment.)
*   «Тут **великий** будинок.» (Here is a big house.)
*   «Там **мала** кімната.» (There is a small room.)
*   «Ось **дорогий** диван.» (Here is an expensive sofa.)
*   «Це **гарне** ліжко.» (This is a beautiful bed.)
*   «Тут **нові** двері.» (Here are new doors.)

As an agent, you must switch rapidly between feminine (квартира, кімната), masculine (будинок, диван), neuter (ліжко), and plural (двері). Practice this aloud. Point to objects in your own home and describe them!

Let's look at a final synthesis of our question-and-answer pattern. Memorize this chart, and you will be ready for any description:
*   **Який?** (Masculine) → **новий**, **гарний**, **синій**. 
*   **Яка?** (Feminine) → **нова**, **гарна**, **синя**.
*   **Яке?** (Neuter) → **нове**, **гарне**, **синє**.
*   **Які?** (Plural) → **нові**, **гарні**, **сині**.

Mastering these questions is your stepping stone. Soon, you will use this exact same pattern to learn all the colors of the rainbow and describe the clothes you wear!

## Підсумок — Summary

You did it! You can now describe a **нова квартира**, an ancient **Софійський собор**, and a **синє море** — all with the right endings. The key rule: adjectives must always agree with their noun in gender and number. 

Here are the key takeaways from this module:
*   **Hard Stem Adjectives** end in **-ий**, **-а**, **-е**, **-і** (e.g., **новий**, **нова**, **нове**, **нові**).
*   **Soft Stem Adjectives** end in **-ій**, **-я**, **-є**, **-і** (e.g., **синій**, **синя**, **синє**, **сині**).
*   **Gender Agreement** is non-negotiable. You cannot use a masculine adjective with a feminine noun.
*   **Plural Adjectives** always end in **-і**, regardless of the noun's original gender.

**Self-Check Questions:**
1. What question do you ask to find a masculine adjective? What about a feminine one?
2. If the noun is **місто** (city), which form of the adjective **старий** do you use? 
3. True or False: The adjective **синій** (blue) is a hard stem adjective.
4. What is the plural form of the adjective **великий**?

Keep practicing by describing the objects around you. Your world is about to become much more colorful!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/describing-things-adjectives.yaml`

```yaml
- type: fill-in
  title: "Change the Adjective Gender"
  instruction: "The adjective is given in masculine form. Choose the correct form to match the noun's gender."
  items:
    - sentence: "Це ___ книга. (новий)"
      answer: "нова"
      options: ["нова", "нове", "нові", "новий"]
      explanation: "Книга is feminine, so новий becomes нова (-а ending)."
    - sentence: "Це ___ місто. (старий)"
      answer: "старе"
      options: ["стара", "старе", "старі", "старий"]
      explanation: "Місто is neuter, so старий becomes старе (-е ending)."
    - sentence: "Це ___ кімната. (великий)"
      answer: "велика"
      options: ["велике", "великі", "велика", "великий"]
      explanation: "Кімната is feminine, so великий becomes велика (-а ending)."
    - sentence: "Це ___ вікно. (гарний)"
      answer: "гарне"
      options: ["гарна", "гарне", "гарні", "гарний"]
      explanation: "Вікно is neuter, so гарний becomes гарне (-е ending)."
    - sentence: "Це ___ двері. (новий)"
      answer: "нові"
      options: ["нова", "нове", "нові", "новий"]
      explanation: "Двері is plural, so новий becomes нові (-і ending)."
    - sentence: "Це ___ школа. (добрий)"
      answer: "добра"
      options: ["добре", "добра", "добрі", "добрий"]
      explanation: "Школа is feminine, so добрий becomes добра (-а ending)."
    - sentence: "Це ___ село. (малий)"
      answer: "мале"
      options: ["мала", "малі", "мале", "малий"]
      explanation: "Село is neuter, so малий becomes мале (-е ending)."
    - sentence: "Це ___ лампа. (синій)"
      answer: "синя"
      options: ["синя", "синє", "сині", "синій"]
      explanation: "Лампа is feminine. Синій is soft stem, so it becomes синя (-я ending)."

- type: fill-in
  title: "Complete with the Correct Adjective Form"
  instruction: "Choose the adjective form that correctly matches the noun in each sentence."
  items:
    - sentence: "Це ___ дім."
      answer: "великий"
      options: ["великий", "велика", "велике", "великі"]
      explanation: "Дім is masculine, so we use великий (-ий ending)."
    - sentence: "Це ___ кава."
      answer: "смачна"
      options: ["смачний", "смачна", "смачне", "смачні"]
      explanation: "Кава is feminine, so we use смачна (-а ending)."
    - sentence: "Це ___ фото."
      answer: "цікаве"
      options: ["цікавий", "цікава", "цікаве", "цікаві"]
      explanation: "Фото is neuter, so we use цікаве (-е ending)."
    - sentence: "Це ___ машина."
      answer: "нова"
      options: ["новий", "нова", "нове", "нові"]
      explanation: "Машина is feminine, so we use нова (-а ending)."
    - sentence: "Це ___ диван."
      answer: "дорогий"
      options: ["дорогий", "дорога", "дороге", "дорогі"]
      explanation: "Диван is masculine, so we use дорогий (-ий ending)."
    - sentence: "Це ___ море."
      answer: "синє"
      options: ["синій", "синя", "синє", "сині"]
      explanation: "Море is neuter. Синій is soft stem, so the neuter form is синє (-є ending)."
    - sentence: "Це ___ погода."
      answer: "погана"
      options: ["поганий", "погана", "погане", "погані"]
      explanation: "Погода is feminine, so we use погана (-а ending)."
    - sentence: "Це ___ суп."
      answer: "смачний"
      options: ["смачний", "смачна", "смачне", "смачні"]
      explanation: "Суп is masculine, so we use смачний (-ий ending)."

- type: match-up
  title: "Match the Adjective to the Noun"
  instruction: "Match each adjective form to the noun it correctly agrees with."
  pairs:
    - left: "новий"
      right: "дім"
    - left: "нова"
      right: "квартира"
    - left: "нове"
      right: "місто"
    - left: "гарна"
      right: "книга"
    - left: "великий"
      right: "будинок"
    - left: "мале"
      right: "село"
    - left: "старі"
      right: "двері"
    - left: "синя"
      right: "лампа"
    - left: "червоне"
      right: "яблуко"
    - left: "дешева"
      right: "кава"

- type: fill-in
  title: "Describe What You See"
  instruction: "You are a real estate agent showing an apartment. Choose the correct adjective form to complete each description."
  items:
    - sentence: "Тут ___ кімната."
      answer: "мала"
      options: ["малий", "мала", "мале", "малі"]
      explanation: "Кімната is feminine, so малий becomes мала."
    - sentence: "Ось ___ диван."
      answer: "старий"
      options: ["старий", "стара", "старе", "старі"]
      explanation: "Диван is masculine, so we use старий."
    - sentence: "Це ___ ліжко."
      answer: "нове"
      options: ["новий", "нова", "нове", "нові"]
      explanation: "Ліжко is neuter, so новий becomes нове."
    - sentence: "Там ___ стіл."
      answer: "великий"
      options: ["великий", "велика", "велике", "великі"]
      explanation: "Стіл is masculine, so we use великий."
    - sentence: "Це ___ квартира."
      answer: "дорога"
      options: ["дорогий", "дорога", "дороге", "дорогі"]
      explanation: "Квартира is feminine, so дорогий becomes дорога."
    - sentence: "Тут ___ вікно."
      answer: "гарне"
      options: ["гарний", "гарна", "гарне", "гарні"]
      explanation: "Вікно is neuter, so гарний becomes гарне."

- type: true-false
  title: "True or False? Adjective Agreement Rules"
  instruction: "Decide whether each statement about Ukrainian adjectives is true or false."
  items:
    - statement: "Hard stem masculine adjectives end in -ий (e.g., новий, старий)."
      correct: true
      explanation: "Correct! Hard stem masculine adjectives use the -ий ending."
    - statement: "The adjective синій (blue) is a hard stem adjective."
      correct: false
      explanation: "Синій is a soft stem adjective. Notice the -ій ending, not -ий."
    - statement: "Feminine adjectives always end in -а for hard stems (e.g., нова, стара)."
      correct: true
      explanation: "Correct! Hard stem feminine adjectives use the -а ending."
    - statement: "You can use the masculine form новий with a feminine noun like книга."
      correct: false
      explanation: "The adjective must agree in gender. Книга is feminine, so you must say нова книга."
    - statement: "Plural adjectives always end in -і, regardless of the noun's gender."
      correct: true
      explanation: "Correct! Whether the noun is masculine, feminine, or neuter, the plural adjective ending is always -і."
    - statement: "The word червоний (red) is a soft stem adjective."
      correct: false
      explanation: "Червоний is a hard stem adjective, despite being a color word. It uses -ий, not -ій."
    - statement: "In the sentence Книга гарна, the adjective comes after the noun."
      correct: true
      explanation: "Correct! This is the predicative position. The adjective still agrees in gender."
    - statement: "Soft stem feminine adjectives end in -а (e.g., синя uses -а)."
      correct: false
      explanation: "Soft stem feminine adjectives end in -я (e.g., синя), not -а."

- type: group-sort
  title: "Sort Adjectives by Type"
  instruction: "Sort these adjective forms into Hard Stem or Soft Stem groups."
  groups:
    - name: "Hard Stem"
      items:
        - "новий"
        - "гарна"
        - "старе"
        - "великий"
        - "червона"
        - "дешевий"
    - name: "Soft Stem"
      items:
        - "синій"
        - "синя"
        - "синє"
        - "сині"

- type: quiz
  title: "Check Your Understanding"
  instruction: "Choose the correct answer for each question about Ukrainian adjectives."
  items:
    - question: "Which question word do you use to describe a masculine noun?"
      options:
        - text: "Який?"
          correct: true
        - text: "Яка?"
          correct: false
        - text: "Яке?"
          correct: false
        - text: "Які?"
          correct: false
      explanation: "Який? is the question word for masculine nouns (e.g., Який дім? — What kind of house?)."
    - question: "What is the correct feminine form of великий?"
      options:
        - text: "велике"
          correct: false
        - text: "великі"
          correct: false
        - text: "велика"
          correct: true
        - text: "великий"
          correct: false
      explanation: "Feminine hard stem adjectives end in -а, so великий becomes велика."
    - question: "What is the neuter form of the soft stem adjective синій?"
      options:
        - text: "синя"
          correct: false
        - text: "синє"
          correct: true
        - text: "сині"
          correct: false
        - text: "синій"
          correct: false
      explanation: "Soft stem neuter adjectives end in -є, so синій becomes синє."
    - question: "Which phrase has a gender agreement error?"
      options:
        - text: "новий дім"
          correct: false
        - text: "нова книга"
          correct: false
        - text: "новий машина"
          correct: true
        - text: "нове місто"
          correct: false
      explanation: "Машина is feminine, so it needs the feminine form нова, not the masculine новий."
    - question: "What ending do ALL plural adjectives share, regardless of gender?"
      options:
        - text: "-а"
          correct: false
        - text: "-е"
          correct: false
        - text: "-ий"
          correct: false
        - text: "-і"
          correct: true
      explanation: "All plural adjectives end in -і (нові, гарні, сині), no matter the original gender."
    - question: "Which pair are antonyms (opposites)?"
      options:
        - text: "новий / гарний"
          correct: false
        - text: "великий / малий"
          correct: true
        - text: "старий / поганий"
          correct: false
        - text: "добрий / цікавий"
          correct: false
      explanation: "Великий (big) and малий (small) are antonyms."

- type: unjumble
  title: "Put the Words in Order"
  instruction: "Arrange the words to form a correct Ukrainian sentence."
  items:
    - words: ["книга", "Це", "нова"]
      answer: "Це нова книга"
    - words: ["великий", "дім", "Це"]
      answer: "Це великий дім"
    - words: ["мале", "Це", "село"]
      answer: "Це мале село"
    - words: ["гарна", "Це", "кімната"]
      answer: "Це гарна кімната"
    - words: ["дорогий", "Це", "диван"]
      answer: "Це дорогий диван"
    - words: ["синє", "Це", "море"]
      answer: "Це синє море"
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/describing-things-adjectives.yaml`

```yaml
items:
  - lemma: "новий"
    translation: "new"
    pos: "adjective"
    notes: "Hard stem. Forms: нова (f), нове (n), нові (pl)."
    usage: "Це новий дім."
  - lemma: "старий"
    translation: "old, ancient"
    pos: "adjective"
    notes: "Hard stem. Forms: стара (f), старе (n), старі (pl)."
    usage: "Це старий будинок."
  - lemma: "гарний"
    translation: "beautiful, nice"
    pos: "adjective"
    notes: "Hard stem. Forms: гарна (f), гарне (n), гарні (pl)."
    usage: "Це гарна книга."
  - lemma: "великий"
    translation: "big, grand"
    pos: "adjective"
    notes: "Hard stem. Forms: велика (f), велике (n), великі (pl)."
    usage: "Це велике місто."
  - lemma: "малий"
    translation: "small"
    pos: "adjective"
    notes: "Hard stem. Forms: мала (f), мале (n), малі (pl)."
    usage: "Це мале село."
  - lemma: "добрий"
    translation: "good, kind"
    pos: "adjective"
    notes: "Hard stem. Forms: добра (f), добре (n), добрі (pl)."
    usage: "Він добрий студент."
  - lemma: "поганий"
    translation: "bad"
    pos: "adjective"
    notes: "Hard stem. Forms: погана (f), погане (n), погані (pl)."
    usage: "Це погана погода."
  - lemma: "цікавий"
    translation: "interesting"
    pos: "adjective"
    notes: "Hard stem. Forms: цікава (f), цікаве (n), цікаві (pl)."
    usage: "Це цікавий факт."
  - lemma: "синій"
    translation: "blue"
    pos: "adjective"
    notes: "Soft stem. Forms: синя (f), синє (n), сині (pl)."
    usage: "Це синє море."
  - lemma: "червоний"
    translation: "red"
    pos: "adjective"
    notes: "Hard stem (not soft, despite being a color). Forms: червона (f), червоне (n), червоні (pl)."
    usage: "Це червоне яблуко."
  - lemma: "молодий"
    translation: "young"
    pos: "adjective"
    notes: "Hard stem. Forms: молода (f), молоде (n), молоді (pl)."
    usage: "Вона молода."
  - lemma: "дорогий"
    translation: "expensive"
    pos: "adjective"
    notes: "Hard stem. Forms: дорога (f), дороге (n), дорогі (pl)."
    usage: "Це дорогий диван."
  - lemma: "дешевий"
    translation: "cheap"
    pos: "adjective"
    notes: "Hard stem. Forms: дешева (f), дешеве (n), дешеві (pl)."
    usage: "Це дешева кава."
  - lemma: "смачний"
    translation: "tasty"
    pos: "adjective"
    notes: "Hard stem. Forms: смачна (f), смачне (n), смачні (pl)."
    usage: "Це смачний суп."
  - lemma: "зелений"
    translation: "green"
    pos: "adjective"
    notes: "Hard stem. Forms: зелена (f), зелене (n), зелені (pl)."
    usage: "Зелена Мавка."
  - lemma: "який"
    translation: "what kind of (m)"
    pos: "adjective"
    notes: "Question word for adjectives. Forms: яка (f), яке (n), які (pl)."
    usage: "Який дім?"
  - lemma: "квартира"
    translation: "apartment"
    pos: "noun"
    gender: "f"
    usage: "Це нова квартира."
  - lemma: "будинок"
    translation: "building, house"
    pos: "noun"
    gender: "m"
    usage: "Тут великий будинок."
  - lemma: "кімната"
    translation: "room"
    pos: "noun"
    gender: "f"
    usage: "Там мала кімната."
  - lemma: "ліжко"
    translation: "bed"
    pos: "noun"
    gender: "n"
    usage: "Це гарне ліжко."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/describing-things-adjectives.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/describing-things-adjectives.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/describing-things-adjectives.yaml`

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
