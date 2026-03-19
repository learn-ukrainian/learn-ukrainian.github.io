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



**NOTE: 8 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥30 items
  - Actual: Activity has 8 items
  - Fix: Add 22 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥30 items
  - Actual: Activity has 6 items
  - Fix: Add 24 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 10 items
  - Fix: Add 10 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 8 items
  - Fix: Add 7 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 6 items
  - Fix: Add 9 more items to 'fill-in' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Line 124: 「# Підсумок」, Lines 110-112 in section "Продукування та культурний контекст (Production and Cultural Context)", Section "Вступ: Тріада гостинності (Introduction: The Triad of Hospitality)", line 5, and section "Продукування та культурний контекст (Production and Cultural Context)", line 112, Whole module

### Finding 1: Zero Engagement Boxes (AUDIT GATE FAILURE)
**Location**: Whole module
**Problem**: The module contains zero `> [!tip]`, `> [!example]`, `> [!cultural-note]`, `> [!did-you-know]` or similar callout boxes. The audit requires minimum 1 for A1. Richness is 57% (threshold 60%) — engagement boxes are the missing dimension. The blockquotes at lines 33-35 and 40-42 are plain `>` blockquotes, not Obsidian-style callouts.
**Required Fix**: Add at least 2 callout boxes: one `> [!tip]` for the "golden rule" about и vowels (near line 26), and one `> [!cultural-note]` for the hospitality triad (near line 5 or lines 119-122). Also add one `> [!example]` with a mini-dialogue using the hospitality verbs.
**Severity**: HIGH

### Finding 2: Підсумок Uses H1 Instead of H2
**Location**: Line 124: 「# Підсумок」
**Problem**: All other sections use `##` (H2). The summary uses `#` (H1), breaking the document structure hierarchy. The plan doesn't list Підсумок as a separate section, and it shouldn't outrank the main H2 sections.
**Required Fix**: Change `# Підсумок` to `## Підсумок`.
**Severity**: HIGH

### Finding 3: пити Silently Grouped with 2nd Conjugation
**Location**: Section "Вступ: Тріада гостинності (Introduction: The Triad of Hospitality)", line 5, and section "Продукування та культурний контекст (Production and Cultural Context)", line 112
**Problem**: The module introduces пити as part of the Hospitality Triad alongside 2nd conjugation verbs (їсти, говорити) but never warns that пити is actually 1st conjugation (п'ю, п'єш, п'є — uses є, not и). VESUM confirms: п'ю, п'єш, п'є, п'ємо, п'єте, п'ють — all 1st conjugation forms. A learner following this module would reasonably try to conjugate *я пию, *ти пиїш — nonexistent forms. The builder notes identify this friction but the content doesn't address it.
**Required Fix**: Add an explicit warning box near line 112 or in section "Презентація: Моделі та мутації (Presentation: Paradigms and Mutations)": "Despite ending in -ити, пити is actually a First Conjugation verb: п'ю, п'єш, п'є. Don't be fooled by the infinitive ending!"
**Severity**: HIGH

### Finding 4: No Encouragement or Emotional Safety Markers
**Location**: Whole module
**Problem**: Zero explicit encouragement phrases ("Great!", "You've got this!", "Don't worry"), zero "don't worry" moments, and zero "You can now..." validation markers. The Beginner Safety rubric requires ≥3 encouragement phrases, ≥2 "don't worry" moments, and ≥2 validation markers. The closest the module gets is "Are you ready to join the table?" (line 9), which is inviting but not encouraging.
**Required Fix**: Add at minimum: (1) one encouragement phrase after the first table (line 25-26), (2) one "don't worry" moment near the mutation section (line 29), (3) "You can now..." celebration in Підсумок.
**Severity**: HIGH

### Finding 5: Immersion Below Target Band
**Location**: Whole module
**Problem**: Audit shows 8.3% immersion. Module 16 falls in the "Modules 11-20: 25-45% Ukrainian" band. At 8.3%, the module is far below the minimum 25% target. Most Ukrainian appears only in bold vocabulary words and tables, with almost all prose in English.
**Required Fix**: Add Ukrainian mini-dialogues or Reading Practice blocks after sections "Презентація: Моделі та мутації (Presentation: Paradigms and Mutations)" and "Продукування та культурний контекст (Production and Cultural Context)". Example: a short dialogue of a guest arriving at a Ukrainian home using the hospitality triad verbs. This would boost immersion while reinforcing the cultural theme.
**Severity**: HIGH

### Finding 6: D.0 Morphological Violations — Collocations with Untaught Cases
**Location**: Lines 110-112 in section "Продукування та культурний контекст (Production and Cultural Context)"
**Problem**: D.0 flags instrumental and accusative forms not taught until M25. These are standard collocations presented as fixed phrases, which is pedagogically defensible at A1. However, the module doesn't signal these as "learn as a chunk" — a learner might try to analyze the case ending.
**Required Fix**: PARTIALLY DISMISS. Add a brief note: "Learn these as fixed phrases for now — we'll explore the grammar behind the word endings in a later module." This addresses the D.0 flag without removing essential collocations.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Zero Engagement Boxes (AUDIT GATE FAILURE)
- **Location**: Whole module
- **Problem**: The module contains zero `> [!tip]`, `> [!example]`, `> [!cultural-note]`, `> [!did-you-know]` or similar callout boxes. The audit requires minimum 1 for A1. Richness is 57% (threshold 60%) — engagement boxes are the missing dimension. The blockquotes at lines 33-35 and 40-42 are plain `>` blockquotes, not Obsidian-style callouts.
- **Fix**: Add at least 2 callout boxes: one `> [!tip]` for the "golden rule" about и vowels (near line 26), and one `> [!cultural-note]` for the hospitality triad (near line 5 or lines 119-122). Also add one `> [!example]` with a mini-dialogue using the hospitality verbs.

### Issue 2: Підсумок Uses H1 Instead of H2
- **Location**: Line 124: 「# Підсумок」
- **Problem**: All other sections use `##` (H2). The summary uses `#` (H1), breaking the document structure hierarchy. The plan doesn't list Підсумок as a separate section, and it shouldn't outrank the main H2 sections.
- **Fix**: Change `# Підсумок` to `## Підсумок`.

### Issue 3: пити Silently Grouped with 2nd Conjugation
- **Location**: Section "Вступ: Тріада гостинності (Introduction: The Triad of Hospitality)", line 5, and section "Продукування та культурний контекст (Production and Cultural Context)", line 112
- **Problem**: The module introduces пити as part of the Hospitality Triad alongside 2nd conjugation verbs (їсти, говорити) but never warns that пити is actually 1st conjugation (п'ю, п'єш, п'є — uses є, not и). VESUM confirms: п'ю, п'єш, п'є, п'ємо, п'єте, п'ють — all 1st conjugation forms. A learner following this module would reasonably try to conjugate *я пию, *ти пиїш — nonexistent forms. The builder notes identify this friction but the content doesn't address it.
- **Fix**: Add an explicit warning box near line 112 or in section "Презентація: Моделі та мутації (Presentation: Paradigms and Mutations)": "Despite ending in -ити, пити is actually a First Conjugation verb: п'ю, п'єш, п'є. Don't be fooled by the infinitive ending!"

### Issue 4: No Encouragement or Emotional Safety Markers
- **Location**: Whole module
- **Problem**: Zero explicit encouragement phrases ("Great!", "You've got this!", "Don't worry"), zero "don't worry" moments, and zero "You can now..." validation markers. The Beginner Safety rubric requires ≥3 encouragement phrases, ≥2 "don't worry" moments, and ≥2 validation markers. The closest the module gets is "Are you ready to join the table?" (line 9), which is inviting but not encouraging.
- **Fix**: Add at minimum: (1) one encouragement phrase after the first table (line 25-26), (2) one "don't worry" moment near the mutation section (line 29), (3) "You can now..." celebration in Підсумок.

### Issue 5: Immersion Below Target Band
- **Location**: Whole module
- **Problem**: Audit shows 8.3% immersion. Module 16 falls in the "Modules 11-20: 25-45% Ukrainian" band. At 8.3%, the module is far below the minimum 25% target. Most Ukrainian appears only in bold vocabulary words and tables, with almost all prose in English.
- **Fix**: Add Ukrainian mini-dialogues or Reading Practice blocks after sections "Презентація: Моделі та мутації (Presentation: Paradigms and Mutations)" and "Продукування та культурний контекст (Production and Cultural Context)". Example: a short dialogue of a guest arriving at a Ukrainian home using the hospitality triad verbs. This would boost immersion while reinforcing the cultural theme.

### Issue 6: D.0 Morphological Violations — Collocations with Untaught Cases
- **Location**: Lines 110-112 in section "Продукування та культурний контекст (Production and Cultural Context)"
- **Original**: 「говорити українською」(instrumental), 「любити природу」(accusative), 「пити каву」(accusative)
- **Problem**: D.0 flags instrumental and accusative forms not taught until M25. These are standard collocations presented as fixed phrases, which is pedagogically defensible at A1. However, the module doesn't signal these as "learn as a chunk" — a learner might try to analyze the case ending.
- **Fix**: PARTIALLY DISMISS. Add a brief note: "Learn these as fixed phrases for now — we'll explore the grammar behind the word endings in a later module." This addresses the D.0 flag without removing essential collocations.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 56 | 「*я їджу* or *я їстю*」 | N/A — correctly marked as errors | Error example (OK) |
| 73 | 「*ти робеш*」 | N/A — correctly marked as error | Error example (OK) |
| 77-79 | 「*ти бачеш*」「*він ходе*」「*ми просемо*」 | N/A — correctly marked as errors | Error examples (OK) |
| 112 | пити treated as 2nd conjugation by context | Add explicit 1st conjugation warning | Misclassification by omission |

All error examples are correctly marked with italics (*) as incorrect forms — this is good pedagogy. No Russianisms detected. No calques detected.

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 7.7)

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Add 2-3 `> [!tip]`, `> [!cultural-note]`, `> [!example]` callout boxes — solves engagement=0 audit gate
2. Line 124: Change `# Підсумок` to `## Підсумок`
3. Add "You can now..." celebration in Підсумок
4. Add a mini-dialogue in Ukrainian using hospitality verbs (boosts immersion + engagement + experience)

**Expected score after fix:** 9/10

### Beginner Safety: 7/10 → 9/10
**What to fix:**
1. Add ≥3 encouragement phrases (after table at line 25, after mutation section ~line 42, after practice section ~line 87)
2. Add ≥1 "don't worry" moment near mutations (~line 29: "Don't worry — this pattern is very consistent once you see it a few times")
3. Add "You can now..." validation in Підсумок

**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Add explicit пити warning — this verb is 1st conjugation (п'ю, п'єш), not 2nd, despite -ити ending. Place near the Hospitality Triad introduction or as a `> [!tip]` callout.
2. Add "learn as fixed phrases" note for collocations at lines 109-112

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 8×1.1 + 8×1.2 + 8×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 8.8 + 9.6 + 10.4 + 11.7 + 8.0 + 13.5) / 8.9
= 75.5 / 8.9 = 8.5/10
```

To reach 9.0+, Pedagogy and Activities would also need polish (add inline practice earlier, add a sentence-building activity), but the immediate priority is the 3 failing dimensions above.

---

## Audit Failures (from automated re-audit)

```
Практика: Помилки та автоматизація (Practice: Errors and Automation)     321 /  300  ✅ (+21)
> Conjugate Second Conjugation Verbs: 8 items (min 6)
📚 IMMERSION TOO LOW (9.4% vs 15-25% target)
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 1 violations
Immersion    ❌ 9.4% LOW (target 15-25% (M16))
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
→ 1 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/the-living-verb-ii-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `бачеш` (source: prose)
  ❌ `дж` (source: prose)
  ❌ `ити` (source: prose)
  ❌ `просемо` (source: prose)
  ❌ `робеш` (source: prose)
  ❌ `їджу` (source: prose)
  ❌ `їстю` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-living-verb-ii.md`

```markdown
## Вступ: Тріада гостинності (Introduction: The Triad of Hospitality)

Welcome back to the world of verbs! In our previous module, you learned the First Conjugation—the largest family of verbs in Ukrainian. Today, we are exploring the second pillar of Ukrainian verbal action: the Second Conjugation. These verbs, which typically end in **-ити** or **-іти**, are essential for expressing ongoing, habitual, and continuous actions. They form the backbone of many daily routines and interactions.

Before we look at the grammar, let's look at why these verbs matter culturally. Ukrainian culture places a massive emphasis on hospitality. When you visit a Ukrainian home, you will immediately encounter the «Triad of Hospitality». This consists of three core actions: **їсти** (to eat), **пити** (to drink), and **говорити** (to speak). True connection is built through sharing a meal, pouring a warm drink, and having a long, meaningful conversation. These aren't just vocabulary words; they are the literal foundation of social interaction. You cannot truly experience Ukrainian culture without them.

To use these verbs correctly, we need a quick concept check. Remember from our earlier discussions that Ukrainian verbs focus heavily on the process of an action. When you say you are doing something right now, or you do it regularly, you are using the imperfective aspect. We are focusing purely on the «doing», not the «completing». So, when a host asks if you want to eat or drink, they are inviting you into the ongoing process of sharing time together. It is an invitation to stay, sit, and belong.

Are you ready to join the table? Let's see how these essential verbs work in action. Once you master them, you will unlock a new level of fluency.

> [!tip] Golden Rule of Conjugation
> First Conjugation → **е/є** in endings (читаєш, знаєш). Second Conjugation → **и/і** in endings (говориш, робиш). When in doubt, check the vowel!

## Презентація: Моделі та мутації (Presentation: Paradigms and Mutations)

Let's look at the mechanics of the Second Conjugation. The key to recognizing these verbs is the vowel in their endings. While the First Conjugation relies heavily on **е** or **є**, the Second Conjugation is built around **и** and **і**.

Here is the standard pattern for a regular **-ити** verb like **говорити** (to speak), placed side-by-side with a First Conjugation verb like **читати** (to read) for comparison. Notice the critical vowel difference in the endings.

| First Conjugation | Second Conjugation |
| :--- | :--- |
| **я читаю** (I read) | **я говорю** (I speak) |
| **ти читаєш** (you read) | **ти говориш** (you speak) |
| **він читає** (he reads) | **він говорить** (he speaks) |
| **ми читаємо** (we read) | **ми говоримо** (we speak) |
| **ви читаєте** (you read) | **ви говорите** (you speak) |
| **вони читають** (they read) | **вони говорять** (they speak) |

You can clearly see that **ти говориш** uses **и**, while **ти читаєш** uses **є**. This pattern is remarkably consistent. Great work spotting the pattern — you're already thinking like a Ukrainian grammarian!

**Consonant Mutations in the «Я» Form**
Second conjugation verbs have a unique quirk: the final consonant of the stem often changes, but *only* in the **я** (I) form. Don't worry — this is a natural phonetic adjustment to make the word easier to say, and the pattern is very consistent once you see it a few times. 

For example, look at the State Standard model verb **сидіти** (to sit). The letter **д** mutates into **дж**.

> **Mutation Pattern: д → дж**
> **сидіти** → **я сиджу** (I sit)
> **ходити** → **я ходжу** (I walk)

**The Labial L**
Some verbs have stems ending in a labial consonant—letters formed with your lips, like **б**, **п**, **в**, **м**, or **ф**. When you try to add the **ю** ending for the **я** form, your lips need a phonetic buffer. So, Ukrainian inserts a «helper» **л**. It is not just an arbitrary rule; it is a physical aid to separate the labial consonant from the **ю** sound.

> **Mutation Pattern: Labial + л**
> **робити** → **я роблю** (I do)
> **любити** → **я люблю** (I love)

**The Irregularity of Їсти**
The most important hospitality verb, **їсти** (to eat), is highly irregular. It does not follow the standard patterns, and you simply must memorize its forms. 

| The Verb **їсти** (to eat) |
| :--- |
| **я їм** |
| **ти їси** |
| **він їсть** |
| **ми їмо** |
| **ви їсте** |
| **вони їдять** |

A very common learner error is trying to apply regular endings, resulting in incorrect forms like *я їджу* or *я їстю*. Always stick to the correct **я їм**. 

**To See vs. To Watch**
Finally, be careful to maintain the distinction between **бачити** (to see) and **дивитися** (to watch). **Бачити** describes the physical faculty of sight, the result of having your eyes open. 

*   **я бачу** (I see)
*   **ти бачиш** (you see)

If you are intentionally directing your eyes at something for a period of time, like a movie, you use **дивитися**. Keep them distinct to prevent semantic confusion in your early sentence building!

## Практика: Помилки та автоматизація (Practice: Errors and Automation)

Now it is time to build your muscle memory. The Second Conjugation is highly regular once you learn the endings, but it requires practice to prevent old habits from interfering. The more you drill these patterns, the more automatic they become.

**Preventing Conjugation Mixing**
The most frequent mistake learners make is Conjugation Mixing. Because verbs like **говорити** and **читати** both end in **-ти** in their dictionary form, it is tempting to mix their endings. You might accidentally apply First Conjugation vowels to a Second Conjugation verb. 

For example, a learner might say *ти робеш*. This is entirely incorrect! Remember the golden rule: Second Conjugation uses **и**. The correct form is **ти робиш**. 

Let's identify and correct the habit of applying the wrong vowels:

*   Incorrect: *ти бачеш* → Correct: **ти бачиш** (you see)
*   Incorrect: *він ходе* → Correct: **він ходить** (he walks)
*   Incorrect: *ми просемо* → Correct: **ми просимо** (we ask)

**Mutation Mastery**
The consonant mutations in the **я** form also require focused drilling. If you forget the mutation, you will produce forms that sound very strange to native speakers. We need intensive drills to eliminate these omission errors.

*   **ходити** (to walk): Always say **я ходжу**.
*   **сидіти** (to sit): Always say **я сиджу**.
*   **платити** (to pay): Always say **я плачу**.
*   **просити** (to ask): Always say **я прошу**.

**Sorting and Categorizing**
To build structural intuition for vowel patterns in endings, try a sorting exercise. Categorize verbs mentally as you learn them. Ask yourself: does this verb take **е/є** or **и/і**? 

*   Group 1 (First Conjugation, **е/є**): **знати**, **думати**, **грати**.
*   Group 2 (Second Conjugation, **и/і**): **говорити**, **робити**, **вчити**.

By organizing verbs into these mental buckets, your brain will automatically select the right vowel for the ending. Let's practice with the verb **стояти** (to stand). Though it looks a bit unusual, it mostly follows the Second Conjugation pattern. 

| The Verb **стояти** (to stand) |
| :--- |
| **я стою** (I stand) |
| **ти стоїш** (you stand) |
| **вони стоять** (they stand) |

## Продукування та культурний контекст (Production and Cultural Context)

You are now ready to start using these verbs in real-world contexts. These high-frequency action words are perfect for describing your daily routines and personal interests. 

Here are some common collocations that you can start using immediately. Learn these as fixed phrases for now — we'll explore the grammar behind the word endings in a later module:

*   **робити домашнє завдання** (to do homework)
*   **говорити українською** (to speak Ukrainian)
*   **любити природу** (to love nature)
*   **пити каву** (to drink coffee)

> [!tip] Watch Out: пити Is a Rebel!
> Despite ending in **-ити**, the verb **пити** (to drink) is actually a **First Conjugation** verb: **п'ю**, **п'єш**, **п'є**, **п'ємо**, **п'єте**, **п'ють**. Notice the **є** vowel — that's the First Conjugation marker. Don't try to conjugate it like говорити!

**Deep Culture: The Etymology of Любити**
Let's take a closer look at the verb **любити** (to love). In English, «love» is a very broad concept. But the Ukrainian word has deep historical roots. It comes from the ancient Proto-Indo-European root *\*lewdh-*, which is the exact same root shared with the word **люди** (people) and **людство** (humanity). 

This etymology illustrates how love is intrinsically linked to community belonging. In the Ukrainian mindset, to love is, quite literally, to be drawn toward people. This makes **любити** a profoundly social and human-centric verb, reminding us that connection is at the heart of the culture. 

**The Social Ethics of Hospitality**
Let's return to our Hospitality Triad: **їсти**, **пити**, and **говорити**. When you are a guest in Ukraine, these verbs carry significant social weight. A host will almost certainly offer you food and drink as a primary gesture of welcome. 

If you say **я не їм** (I am not eating) or flatly refuse a dish, you must be aware that this can sometimes be perceived as a rejection of the host's goodwill. Food is synonymous with care. Refusing the meal can accidentally signal that you are refusing the care itself. Of course, you do not have to eat everything on the table! But participating in the process—taking a small bite, sharing a drink, and engaging warmly in conversation—shows deep respect for the host's effort and solidifies your place at the table.

> [!cultural-note] A Ukrainian Kitchen Scene
> — Сідай! Їж! (Sit down! Eat!)
> — Дякую! Я їм. Смачно! (Thank you! I'm eating. Delicious!)
> — Пий чай! (Drink tea!)
> — Дякую, п'ю. (Thank you, I'm drinking.)
> — Говори! Як справи? (Talk! How are things?)

## Підсумок
Fantastic work — you've come a long way! You have now mastered the two major verb families in Ukrainian. The Second Conjugation, with its characteristic **и** and **і** vowels, powers some of the most important words in the language, especially the Triad of Hospitality: **їсти**, **пити**, and **говорити**. 

Remember to watch out for consonant mutations in the **я** form, like **я ходжу** and **я люблю**. Keep your vowels straight to avoid conjugation mixing, and never use *я їджу* when you mean **я їм**! 

**You can now:**
- Conjugate Second Conjugation verbs (-ити) in present tense
- Spot and apply consonant mutations in the я-form (ходжу, роблю, прошу)
- Use the Hospitality Triad (їсти, пити, говорити) in real conversations
- Tell First and Second Conjugation apart by their vowel patterns

You are fully equipped to describe your daily actions, express your preferences, and participate graciously in a traditional Ukrainian gathering. Молодець! 🎉

**Self-Check Questions:**
1. What is the characteristic vowel of the Second Conjugation for the «ти» (you) form?
2. Why do we insert the letter «л» in the «я» form of verbs like **робити** and **любити**?
3. What is the correct «я» form of the highly irregular verb **їсти**?
4. How might refusing to eat (**не їсти**) be perceived by a Ukrainian host?
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-living-verb-ii.yaml`

```yaml
- type: fill-in
  title: "Conjugate Second Conjugation Verbs"
  instruction: "Choose the correct verb form to complete each sentence."
  items:
    - sentence: "Я ___ українською."
      answer: "говорю"
      options: ["говорю", "говориш", "говорить", "говоримо"]
      explanation: "The я-form of говорити is говорю."
    - sentence: "Ти ___ домашнє завдання."
      answer: "робиш"
      options: ["робиш", "роблю", "робить", "робимо"]
      explanation: "The ти-form of робити uses the ending -иш."
    - sentence: "Він ___ каву."
      answer: "любить"
      options: ["любить", "люблю", "любиш", "любимо"]
      explanation: "The він-form of любити is любить — ending -ить."
    - sentence: "Ми ___ в парк."
      answer: "ходимо"
      options: ["ходимо", "ходжу", "ходиш", "ходить"]
      explanation: "The ми-form of ходити is ходимо — ending -имо."
    - sentence: "Вони ___ правду."
      answer: "говорять"
      options: ["говорять", "говорю", "говориш", "говоримо"]
      explanation: "The вони-form of говорити is говорять — ending -ять."
    - sentence: "Ви ___ книгу."
      answer: "бачите"
      options: ["бачите", "бачу", "бачиш", "бачить"]
      explanation: "The ви-form of бачити is бачите — ending -ите."
    - sentence: "Ти ___ мову."
      answer: "вчиш"
      options: ["вчиш", "вчу", "вчить", "вчимо"]
      explanation: "The ти-form of вчити is вчиш — ending -иш."
    - sentence: "Вона ___ допомоги."
      answer: "просить"
      options: ["просить", "прошу", "просиш", "просимо"]
      explanation: "The вона-form of просити is просить — ending -ить."

- type: match-up
  title: "Match Verbs to Their Я-Forms"
  instruction: "Match each verb infinitive on the left to its correct я-form on the right. Pay attention to consonant mutations!"
  pairs:
    - left: "говорити"
      right: "говорю"
    - left: "робити"
      right: "роблю"
    - left: "любити"
      right: "люблю"
    - left: "ходити"
      right: "ходжу"
    - left: "сидіти"
      right: "сиджу"
    - left: "просити"
      right: "прошу"
    - left: "платити"
      right: "плачу"
    - left: "бачити"
      right: "бачу"
    - left: "стояти"
      right: "стою"
    - left: "їсти"
      right: "їм"

- type: fill-in
  title: "Complete with the Correct Я-Form"
  instruction: "Each sentence uses я. Choose the correct я-form — watch out for consonant mutations!"
  items:
    - sentence: "Я ___ домашнє завдання."
      answer: "роблю"
      options: ["роблю", "робиш", "робить", "робимо"]
      explanation: "Робити has a labial mutation in the я-form: б + л → роблю."
    - sentence: "Я ___ природу."
      answer: "люблю"
      options: ["люблю", "любиш", "любить", "любимо"]
      explanation: "Любити has a labial mutation in the я-form: б + л → люблю."
    - sentence: "Я ___ в парк."
      answer: "ходжу"
      options: ["ходжу", "ходиш", "ходить", "ходимо"]
      explanation: "Ходити has a consonant mutation in the я-form: д → дж → ходжу."
    - sentence: "Я тут ___."
      answer: "сиджу"
      options: ["сиджу", "сидиш", "сидить", "сидимо"]
      explanation: "Сидіти has a consonant mutation in the я-form: д → дж → сиджу."
    - sentence: "Я ___ допомоги."
      answer: "прошу"
      options: ["прошу", "просиш", "просить", "просимо"]
      explanation: "Просити has a consonant mutation in the я-form: с → ш → прошу."
    - sentence: "Я ___ за каву."
      answer: "плачу"
      options: ["плачу", "платиш", "платить", "платимо"]
      explanation: "Платити has a consonant mutation in the я-form: т → ч → плачу."

- type: group-sort
  title: "Sort Verbs by Conjugation"
  instruction: "Sort these verbs into two groups. First Conjugation verbs use е/є in their endings. Second Conjugation verbs use и/і."
  groups:
    - name: "First Conjugation (е/є)"
      items:
        - "читати"
        - "знати"
        - "думати"
        - "грати"
    - name: "Second Conjugation (и/і)"
      items:
        - "говорити"
        - "робити"
        - "бачити"
        - "любити"
        - "ходити"
        - "сидіти"
        - "просити"
        - "платити"

- type: quiz
  title: "Second Conjugation Knowledge Check"
  instruction: "Choose the correct answer."
  items:
    - question: "What is the correct ти-form of говорити?"
      options:
        - text: "говориш"
          correct: true
        - text: "говорю"
          correct: false
        - text: "говорять"
          correct: false
        - text: "говоримо"
          correct: false
      explanation: "The ти-form uses the ending -иш for Second Conjugation: говориш."
    - question: "What is the correct я-form of робити?"
      options:
        - text: "роблю"
          correct: true
        - text: "робиш"
          correct: false
        - text: "робить"
          correct: false
        - text: "робимо"
          correct: false
      explanation: "Робити has a labial mutation (б + л) in the я-form: роблю."
    - question: "Which of these is the correct я-form of їсти?"
      options:
        - text: "їм"
          correct: true
        - text: "їсти"
          correct: false
        - text: "їдять"
          correct: false
        - text: "їсте"
          correct: false
      explanation: "Їсти is highly irregular. The correct я-form is simply їм."
    - question: "What is the correct вони-form of любити?"
      options:
        - text: "люблять"
          correct: true
        - text: "любиш"
          correct: false
        - text: "люблю"
          correct: false
        - text: "любимо"
          correct: false
      explanation: "The вони-form of любити is люблять — ending -ять with labial mutation."
    - question: "What is the correct ми-form of бачити?"
      options:
        - text: "бачимо"
          correct: true
        - text: "бачу"
          correct: false
        - text: "бачиш"
          correct: false
        - text: "бачить"
          correct: false
      explanation: "The ми-form uses the ending -имо for Second Conjugation: бачимо."
    - question: "What is the correct я-form of просити?"
      options:
        - text: "прошу"
          correct: true
        - text: "просиш"
          correct: false
        - text: "просить"
          correct: false
        - text: "просимо"
          correct: false
      explanation: "Просити has a consonant mutation (с → ш) in the я-form: прошу."

- type: true-false
  title: "True or False?"
  instruction: "Decide whether each statement about Ukrainian verbs is true or false."
  items:
    - statement: "Second Conjugation verbs use the vowel и in their endings, for example ти говориш."
      correct: true
      explanation: "Correct! Second Conjugation uses и/і (говориш, робиш), while First Conjugation uses е/є (читаєш, знаєш)."
    - statement: "The correct я-form of робити is роблю, with an inserted л."
      correct: true
      explanation: "Correct! The labial consonant б needs the helper л before ю: роблю."
    - statement: "The verb їсти follows regular Second Conjugation patterns."
      correct: false
      explanation: "Їсти is highly irregular. Its forms (їм, їси, їсть, їмо, їсте, їдять) do not follow standard patterns."
    - statement: "In the я-form of ходити, the letter д changes to дж, giving ходжу."
      correct: true
      explanation: "Correct! This is the д → дж consonant mutation that only occurs in the я-form."
    - statement: "First Conjugation verbs like читати use the vowel и in their endings."
      correct: false
      explanation: "First Conjugation uses е/є in its endings: ти читаєш, він читає, ми читаємо."
    - statement: "Бачити means 'to watch' in Ukrainian."
      correct: false
      explanation: "Бачити means 'to see' (the physical faculty of sight). 'To watch' is дивитися."
    - statement: "The letter л is inserted in люблю to separate the labial consonant б from the sound ю."
      correct: true
      explanation: "Correct! Labial consonants (б, п, в, м, ф) need the helper л before ю as a phonetic buffer."
    - statement: "The three verbs of the Ukrainian Hospitality Triad are їсти, пити, and говорити."
      correct: true
      explanation: "Correct! Eating, drinking, and speaking are the foundations of Ukrainian hospitality."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-living-verb-ii.yaml`

```yaml
items:
  - lemma: "говорити"
    translation: "to speak"
    pos: "verb"
    aspect: "imperfective"
    usage: "говорити українською, говорити правду"
    notes: "Second Conjugation. Part of the Hospitality Triad. Top 100 frequency."
  - lemma: "робити"
    translation: "to do, to make"
    pos: "verb"
    aspect: "imperfective"
    usage: "робити домашнє завдання, робити покупки"
    notes: "Second Conjugation. Labial mutation in я-form: роблю. Top 50 frequency."
  - lemma: "бачити"
    translation: "to see"
    pos: "verb"
    aspect: "imperfective"
    usage: "я бачу, радий бачити"
    notes: "Second Conjugation. Describes the faculty of sight (result), not intentional watching."
  - lemma: "любити"
    translation: "to love"
    pos: "verb"
    aspect: "imperfective"
    usage: "любити природу, любити читати"
    notes: "Second Conjugation. Labial mutation: люблю. Shares PIE root with люди (people)."
  - lemma: "їсти"
    translation: "to eat"
    pos: "verb"
    aspect: "imperfective"
    usage: "хотіти їсти, смачно їсти"
    notes: "Highly irregular: їм, їси, їсть, їмо, їсте, їдять. Part of Hospitality Triad."
  - lemma: "пити"
    translation: "to drink"
    pos: "verb"
    aspect: "imperfective"
    usage: "пити каву, пити воду"
    notes: "Irregular: п'ю, п'єш, п'є. Part of Hospitality Triad."
  - lemma: "ходити"
    translation: "to walk, to go (on foot)"
    pos: "verb"
    aspect: "imperfective"
    usage: "ходити в парк, ходити до школи"
    notes: "Second Conjugation. Consonant mutation д → дж in я-form: ходжу."
  - lemma: "просити"
    translation: "to ask, to request"
    pos: "verb"
    aspect: "imperfective"
    usage: "просити допомоги"
    notes: "Second Conjugation. Consonant mutation с → ш in я-form: прошу."
  - lemma: "сидіти"
    translation: "to sit"
    pos: "verb"
    aspect: "imperfective"
    usage: "сидіти вдома, сидіти тихо"
    notes: "Second Conjugation. State Standard model verb for д → дж mutation: сиджу."
  - lemma: "стояти"
    translation: "to stand"
    pos: "verb"
    aspect: "imperfective"
    usage: "стояти в черзі"
    notes: "Second Conjugation. Я-form: стою. Вони-form: стоять."
  - lemma: "платити"
    translation: "to pay"
    pos: "verb"
    aspect: "imperfective"
    usage: "платити за каву"
    notes: "Second Conjugation. Consonant mutation т → ч in я-form: плачу."
  - lemma: "вчити"
    translation: "to teach, to learn/study"
    pos: "verb"
    aspect: "imperfective"
    usage: "вчити мову, вчити слова"
    notes: "Second Conjugation. Я-form: вчу."
  - lemma: "читати"
    translation: "to read"
    pos: "verb"
    aspect: "imperfective"
    usage: "читати книгу"
    notes: "First Conjugation — used as contrast: читаєш (е/є) vs говориш (и/і)."
  - lemma: "знати"
    translation: "to know"
    pos: "verb"
    aspect: "imperfective"
    usage: "знати мову"
    notes: "First Conjugation. Used in sorting exercises for conjugation contrast."
  - lemma: "думати"
    translation: "to think"
    pos: "verb"
    aspect: "imperfective"
    usage: "думати про щось"
    notes: "First Conjugation. Used in sorting exercises for conjugation contrast."
  - lemma: "грати"
    translation: "to play"
    pos: "verb"
    aspect: "imperfective"
    usage: "грати в гру"
    notes: "First Conjugation. Used in sorting exercises for conjugation contrast."
  - lemma: "дивитися"
    translation: "to watch, to look at"
    pos: "verb"
    aspect: "imperfective"
    usage: "дивитися фільм"
    notes: "Contrast with бачити (to see). Дивитися = intentional watching over time."
  - lemma: "кава"
    translation: "coffee"
    pos: "noun"
    gender: "f"
    usage: "пити каву"
    notes: "High-frequency noun used in hospitality contexts."
  - lemma: "вода"
    translation: "water"
    pos: "noun"
    gender: "f"
    usage: "пити воду"
    notes: "Basic noun for drink-related collocations."
  - lemma: "природа"
    translation: "nature"
    pos: "noun"
    gender: "f"
    usage: "любити природу"
    notes: "Used in collocation with любити for production practice."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-living-verb-ii.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-living-verb-ii.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-living-verb-ii.yaml`

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
