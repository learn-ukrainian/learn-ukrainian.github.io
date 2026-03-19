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
- Only modify these sections: Activities YAML, line 356-359 (fill-in item 5), Entire module — all 5 sections, Richness gaps: engagement 0/2, examples 4/8, video_embeds 0/2, Vocabulary YAML (`my-world-objects.yaml`) — only 20 items, Whole module — sections "Вступ (Introduction)" through "Продукція та підсумок (Production and Summary)"

### Finding 1: Zero Engagement Boxes (AUDIT GATE FAIL)
**Location**: Entire module — all 5 sections
**Problem**: The module has zero callout boxes (`> [!tip]`, `> [!example]`, `> [!cultural-note]`, etc.). The audit requires minimum 1 for A1, and the richness gate shows engagement: 0/2. This is the primary reason for FAIL audit status.
**Required Fix**: Add at least 2 callout boxes:
**Severity**: HIGH

### Finding 2: Grammar Scope Creep — Locative Case in Activity
**Location**: Activities YAML, line 356-359 (fill-in item 5)
**Problem**: The locative case form "квартирі" (в квартирі) has not been taught at Module 10. This requires knowledge of locative endings, which is beyond A1.1 scope. The plan specifies nominative-only Ukrainian.
**Required Fix**: Replace with a nominative-case identification pattern consistent with the module's scope: `'Що це? — Це ___.'` with answer "квартира" and options from dwelling vocabulary.
**Severity**: HIGH

### Finding 3: Vocabulary YAML Missing 8 Words Used in Activities
**Location**: Vocabulary YAML (`my-world-objects.yaml`) — only 20 items
**Problem**: The following words appear in activities (match-up) but are absent from the vocabulary sidecar: річ, хата, ніж, ложка, блюдо, диван, крісло, Покуття. This causes vocab/activity misalignment.
**Required Fix**: Add at least the nouns that appear in both prose AND activities to the vocabulary YAML: хата, ніж, ложка, блюдо, диван, крісло, річ.
**Severity**: HIGH

### Finding 4: Low Immersion (7.8% vs 15-35% target)
**Location**: Whole module — sections "Вступ (Introduction)" through "Продукція та підсумок (Production and Summary)"
**Problem**: Module 10 falls in the 11-20 band (target 25-45% Ukrainian). At 7.8%, immersion is critically low. The content is almost entirely English prose with only isolated bolded Ukrainian words.
**Required Fix**: Add 2-3 short Ukrainian example dialogues using blockquote format (as research notes suggest): e.g., «Що це? — Це книга. — Ця книга? — Так, ця книга.» in section "Практика (Practice)". Add more Ukrainian mini-sentences throughout section "Презентація (Presentation)".
**Severity**: HIGH

### Finding 5: Richness Below Threshold (54% vs 60%)
**Location**: Richness gaps: engagement 0/2, examples 4/8, video_embeds 0/2
**Problem**: The module lacks visual engagement variety. No tables for the gender paradigm (the Near/Far demonstrative grid cries out for a summary table). No callout boxes. Few standalone example blocks.
**Required Fix**: Add a demonstrative paradigm summary table in section "Презентація (Presentation)" after line 37. Add example blocks in section "Практика (Practice)". Engagement boxes addressed in Issue 1.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Zero Engagement Boxes (AUDIT GATE FAIL)
- **Location**: Entire module — all 5 sections
- **Problem**: The module has zero callout boxes (`> [!tip]`, `> [!example]`, `> [!cultural-note]`, etc.). The audit requires minimum 1 for A1, and the richness gate shows engagement: 0/2. This is the primary reason for FAIL audit status.
- **Fix**: Add at least 2 callout boxes:
  1. A `> [!tip]` in section "Презентація (Presentation)" after the identification vs specification explanation (after line 19) with a mnemonic summary
  2. A `> [!cultural-note]` wrapping the Покуття content in section "Культурний контекст (Cultural Insight)" (line 58)

### Issue 2: Grammar Scope Creep — Locative Case in Activity
- **Location**: Activities YAML, line 356-359 (fill-in item 5)
- **Original**: `'Де ти живеш? — Я живу в ___.'` with answer "квартирі"
- **Problem**: The locative case form "квартирі" (в квартирі) has not been taught at Module 10. This requires knowledge of locative endings, which is beyond A1.1 scope. The plan specifies nominative-only Ukrainian.
- **Fix**: Replace with a nominative-case identification pattern consistent with the module's scope: `'Що це? — Це ___.'` with answer "квартира" and options from dwelling vocabulary.

### Issue 3: Vocabulary YAML Missing 8 Words Used in Activities
- **Location**: Vocabulary YAML (`my-world-objects.yaml`) — only 20 items
- **Problem**: The following words appear in activities (match-up) but are absent from the vocabulary sidecar: річ, хата, ніж, ложка, блюдо, диван, крісло, Покуття. This causes vocab/activity misalignment.
- **Fix**: Add at least the nouns that appear in both prose AND activities to the vocabulary YAML: хата, ніж, ложка, блюдо, диван, крісло, річ.

### Issue 4: Low Immersion (7.8% vs 15-35% target)
- **Location**: Whole module — sections "Вступ (Introduction)" through "Продукція та підсумок (Production and Summary)"
- **Problem**: Module 10 falls in the 11-20 band (target 25-45% Ukrainian). At 7.8%, immersion is critically low. The content is almost entirely English prose with only isolated bolded Ukrainian words.
- **Fix**: Add 2-3 short Ukrainian example dialogues using blockquote format (as research notes suggest): e.g., «Що це? — Це книга. — Ця книга? — Так, ця книга.» in section "Практика (Practice)". Add more Ukrainian mini-sentences throughout section "Презентація (Presentation)".

### Issue 5: Richness Below Threshold (54% vs 60%)
- **Location**: Richness gaps: engagement 0/2, examples 4/8, video_embeds 0/2
- **Problem**: The module lacks visual engagement variety. No tables for the gender paradigm (the Near/Far demonstrative grid cries out for a summary table). No callout boxes. Few standalone example blocks.
- **Fix**: Add a demonstrative paradigm summary table in section "Презентація (Presentation)" after line 37. Add example blocks in section "Практика (Practice)". Engagement boxes addressed in Issue 1.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Activities L356 | Де ти живеш? — Я живу в ___. (answer: квартирі) | Що це? — Це ___. (answer: квартира) | Scope creep (locative case) |

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 7.9)

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Add `> [!tip]` callout in section "Презентація (Presentation)" after the identification/specification explanation (after line 19) summarizing the key distinction
2. Add `> [!cultural-note]` callout wrapping Покуття content in section "Культурний контекст (Cultural Insight)" (line 58)
3. Add a demonstrative paradigm table in section "Презентація (Presentation)" (after line 34) showing цей/ця/це/ці and той/та/те/ті in a clean grid

**Expected score after fix:** 9/10

### Activities: 7/10 → 9/10
**What to fix:**
1. Replace locative-case activity item (line 356) with nominative-case pattern
2. Add missing vocabulary items to YAML (хата, ніж, ложка, блюдо, диван, крісло, річ)

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add 2-3 Ukrainian mini-dialogues using blockquote format in section "Практика (Practice)" to raise immersion from 7.8% toward 15%+
2. Add a Ukrainian example dialogue in section "Презентація (Presentation)" after the near/far explanation

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 5: Tone down "profoundly special place in people's hearts" → "special place in Ukrainian culture"
2. Line 58: Replace "incredibly important concept" → "important tradition"
3. Line 67: Replace "enthusiastically navigating" → "walking through"

**Expected score after fix:** 9/10

### Projected Overall After Fixes
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 10.4 + 8.0 + 13.5) / 8.9
= 77.8 / 8.9 = **8.7/10**

---

## Audit Failures (from automated re-audit)

```
❌ Structure check failed: Missing '## Summary'
✨ Purity violations found: 1
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'no, it's...'.
✨ Prose quality violations found: 1
❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (8 occurrences): (This table), (This table), (That phone) — breaks immersion target
--- STRICT GATES (Level A1) ---
Structure    ❌ Missing '## Summary'
📚 PEDAGOGICAL VIOLATIONS FOUND:
[ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'no, it's...'.
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
→ 2 violations (minor)
→ Structure issue: Missing '## Summary'
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Structure: Missing '## Summary'
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/my-world-objects-audit.log for details)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Structure: Missing '## Summary'
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-world-objects.md`

```markdown
## Вступ (Introduction)

Welcome to the next exciting step in your Ukrainian language journey! By now, you already know that every noun in Ukrainian belongs to a specific gender family (**masculine**, **feminine**, or **neuter**), which we learned to recognize in our very first modules. You also know how to point things out using the simple word **це** (this is) for basic identification. Let's build upon that strong grammatical foundation and explore the beautiful spaces where we live.

In Ukrainian culture, the concept of home — **дім** — holds a special place. There is a famous proverb that captures this feeling: «В гостях добре, а вдома краще» (East or West, home is best). It reminds us that no matter where we go, returning to our own **дім** brings the greatest comfort. This proverb is the perfect anchor for our home-centric vocabulary today.

To talk about the objects inside our homes properly, we need to master a new skill: demonstrative specification. According to the State Standard for Ukrainian as a Second Language (§4.2.2), at this level, you need to know exactly how to use the specific words for "this" (**цей**, **ця**, **це**, **ці**) and "that" (**той**, **та**, **те**, **ті**) in their correct gendered and plural forms. This will allow you not just to say "This is a room," but to specifically point out "this room" or "that room." Let's dive in!

## Презентація (Presentation)

Imagine you are walking through a beautiful, spacious house. When you want to talk about objects around you, distance matters immensely. In Ukrainian, we use one specific set of words for objects that are "Near" (imagine small hand-touching icons for things you could reach out and touch) and another set of words for objects that are "Far" (imagine finger-pointing icons for things you would point at from across the room).

For "Near" objects, we use the various forms of **цей** (this). For "Far" objects, we use the forms of **той** (that).

Wait, didn't we already learn the word **це** for "this"? Yes, we did! But there is a significant hurdle here for English speakers: Identification versus Specification.

When you walk into a room and simply identify an object, you say: «Це стіл.» (This is a table.) This is Identification. We are just stating what the object is.

When you want to specify a particular table, perhaps to say it is yours or it is new, you say: «Цей стіл» (This table). This is Specification. English uses the word "this" for both situations, but Ukrainian uses two distinct grammatical structures! We can explain this using English metalanguage: one structure is for pure identification, and the other is for exact specification.

> [!tip] **Identification vs. Specification — the key difference**
> - **Це стіл.** = "This **is** a table." (You're identifying what something is.)
> - **Цей стіл.** = "**This** table." (You're specifying which table you mean.)
> English uses "this" for both. Ukrainian doesn't — and that's actually a superpower once you get it!

Let's look closely at how the specifying words must perfectly match the gender of the noun.

If the noun is masculine, like **стіл** (table), **стілець** (chair), or **телефон** (phone), we must use the masculine demonstrative forms: **цей** (near) or **той** (far).
- «Цей стіл» (This table)
- «Той телефон» (That phone)

If the noun is feminine, like **книга** (book), **кімната** (room), **лампа** (lamp), or **шафа** (wardrobe), we must use the feminine demonstrative forms: **ця** (near) or **та** (far).
- «Ця кімната» (This room)
- «Та шафа» (That wardrobe)

If the noun is neuter, like **вікно** (window) or **ліжко** (bed), we use the neuter demonstrative forms: **це** (near) or **те** (far). Notice that the neuter "this" is the exact same word **це** that we use for general identification!
- «Це ліжко» (This bed)
- «Те вікно» (That window)

What about plurals? For multiple objects, we introduce the plural forms: **ці** (these) and **ті** (those). For example, «Ці речі» (These things). You must pay special emphasis to inherently plural nouns like **двері** (door). In Ukrainian, a door is always plural! So, you must always say «ці двері» (these doors) or «ті двері» (those doors). Never try to make it singular.

Here is a summary of all the demonstrative forms:

| | Masculine | Feminine | Neuter | Plural |
|---|---|---|---|---|
| **Near (this/these)** | цей | ця | це | ці |
| **Far (that/those)** | той | та | те | ті |

To help you remember, listen for the rhyming sound association between the demonstrative endings and the noun endings. For feminine nouns ending in -а, the demonstrative also ends in an "a" sound: **цЯ книгА**, **цЯ лампА**. For neuter nouns ending in -о, the demonstrative ends in an "e/o" sound: **цЕ вікнО**, **цЕ ліжкО**. For masculine nouns ending in a consonant, the demonstrative ends in a consonant: **цЕЙ стіл**. Let this natural rhythm guide you to prevent any mismatch!

## Практика (Practice)

Let's practice what we just learned to build your confidence. A very common learner error for English speakers is to completely forget gender agreement and just use the masculine form for everything, resulting in mistakes like *цей книга* (wrong!). Because English has no grammatical gender for objects, our brains naturally default to one word.

Let's correct this habit right now through a quick Drill: Gender Matching. Listen carefully to the phonological reinforcement of the feminine "-а" ending using minimal pairs and repetition. The correct phrase is **ця книга** (this book). Can you hear how the "a" sounds beautifully echo each other at the end of both words?
- Is it *цей кімната*? No, it's **ця кімната**!
- Is it *це лампа*? No, it's **ця лампа**!
- Is it *цей шафа*? No, it's **ця шафа**!

To make this vocabulary even easier to master, let's look at household categorization. We can group kitchen objects and furniture by their grammatical gender to help them stick in your memory.

First, let's group kitchen objects: A **ніж** (knife) is masculine, so we say **цей ніж**. A **ложка** (spoon) is feminine, so we say **ця ложка**. A **блюдо** (dish) is neuter, so we say **це блюдо**.

Next, let's group furniture: A **диван** (sofa) is masculine, so we confidently say **цей диван**. A **шафа** (wardrobe) is feminine, so we say **ця шафа**. A **крісло** (armchair) is neuter, so we say **це крісло**. Practice saying these aloud to truly feel the rhythm of the gender agreement.

Finally, what about distinguishing near versus far? If you ever experience proximity confusion between near and far objects during identification tasks, just use the proximity mnemonic: "T" is for "There/That". The Ukrainian words starting with "T" (**той**, **та**, **те**, **ті**) always mean "There" or "That". The words starting with "Ц" (**цей**, **ця**, **це**, **ці**) always mean "Close" (this/these). So, when you point to a distant chair, the "T" reminds you to say **той стілець** (that chair), not **цей стілець**.

## Культурний контекст (Cultural Insight)

> [!cultural-note] **Покуття — The Heart of a Ukrainian Home**
> The **Покуття** (Pokuttia, or Red Corner) is an important tradition in the Ukrainian home. This space serves as a spiritual focal point in the main living area, typically arranged diagonally opposite the stove. Families traditionally displayed religious icons here, draped in beautifully embroidered cloths called *rushnyky*. Even in modern city apartments, many Ukrainian families maintain a decorative corner echoing this tradition.

When describing where they actually live, Ukrainians make lexical distinctions in dwelling that English simply translates broadly as "house" or "home." You should know these three key words:
- A **хата** is a traditional rural cottage. It carries a high cultural resonance, instantly evoking warm images of white-washed walls, thatched roofs, and the traditional center of village life.
- A **квартира** is a modern urban apartment. This is the practical word for what most city-dwellers live in today.
- A **дім** is the general concept of a house or a home. It is an affective, emotional term that embodies the true feeling of belonging.

## Продукція та підсумок (Production and Summary)

Now, it is your turn to step into a new role for our Persona Task: 'Interior Designer'. Imagine you are walking through a living space with a new client. You need to point out various objects to them to discuss the design. Stand up, walk around your own room, pointing to distant and near objects, and practice specifying them with the correct gender-matched demonstratives.

Look closely at the items near you. Say aloud: «Цей стіл. Ця лампа. Це вікно.»

Now point across the room to distant objects. Say aloud: «Той телефон. Та шафа. Те ліжко.»

Let's finish with a thorough review of the State Standard §4.2.2 competencies. Can you now perform a self-assessment on matching demonstrative gender and number with 40 household and everyday objects? Can you consistently pair the feminine **ця** with **книга**, the masculine **цей** with **стілець**, the neuter **це** with **вікно**, and remember that **двері** inherently takes the plural **ці** or **ті**?

If you can confidently describe your space using these demonstrative tools, you are officially ready for the next exciting module!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/my-world-objects.yaml`

```yaml
- type: match-up
  title: "Label Room Objects"
  instruction: "Match each Ukrainian household word to its English meaning."
  pairs:
    - left: "стіл"
      right: "table"
    - left: "книга"
      right: "book"
    - left: "телефон"
      right: "phone"
    - left: "кімната"
      right: "room"
    - left: "стілець"
      right: "chair"
    - left: "ліжко"
      right: "bed"
    - left: "лампа"
      right: "lamp"
    - left: "вікно"
      right: "window"
    - left: "шафа"
      right: "wardrobe"
    - left: "двері"
      right: "door"
    - left: "ніж"
      right: "knife"
    - left: "ложка"
      right: "spoon"
    - left: "блюдо"
      right: "dish"
    - left: "диван"
      right: "sofa"
    - left: "крісло"
      right: "armchair"
    - left: "хата"
      right: "traditional cottage"
    - left: "квартира"
      right: "apartment"
    - left: "дім"
      right: "house / home"
    - left: "річ"
      right: "thing"
    - left: "Покуття"
      right: "Red Corner (sacred space)"

- type: quiz
  title: "Match the Demonstrative to the Gender"
  instruction: "Choose the correct demonstrative pronoun for each noun."
  items:
    - question: "Which demonstrative means 'this' for the masculine noun стіл (table)?"
      options:
        - text: "цей"
          correct: true
        - text: "ця"
          correct: false
        - text: "це"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Стіл is masculine, so we use the masculine form цей."
    - question: "Which demonstrative means 'this' for the feminine noun книга (book)?"
      options:
        - text: "ця"
          correct: true
        - text: "цей"
          correct: false
        - text: "це"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Книга is feminine, so we use the feminine form ця."
    - question: "Which demonstrative means 'this' for the neuter noun вікно (window)?"
      options:
        - text: "це"
          correct: true
        - text: "цей"
          correct: false
        - text: "ця"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Вікно is neuter, so we use the neuter form це."
    - question: "Which demonstrative means 'that' for the masculine noun телефон (phone)?"
      options:
        - text: "той"
          correct: true
        - text: "та"
          correct: false
        - text: "те"
          correct: false
        - text: "ті"
          correct: false
      explanation: "Телефон is masculine, so we use the masculine form той."
    - question: "Which demonstrative means 'that' for the feminine noun шафа (wardrobe)?"
      options:
        - text: "та"
          correct: true
        - text: "той"
          correct: false
        - text: "те"
          correct: false
        - text: "ті"
          correct: false
      explanation: "Шафа is feminine, so we use the feminine form та."
    - question: "Which demonstrative means 'that' for the neuter noun ліжко (bed)?"
      options:
        - text: "те"
          correct: true
        - text: "той"
          correct: false
        - text: "та"
          correct: false
        - text: "ті"
          correct: false
      explanation: "Ліжко is neuter, so we use the neuter form те."
    - question: "Which demonstrative means 'these' for the plural noun двері (door)?"
      options:
        - text: "ці"
          correct: true
        - text: "цей"
          correct: false
        - text: "ця"
          correct: false
        - text: "це"
          correct: false
      explanation: "Двері is always plural in Ukrainian, so we use the plural form ці."
    - question: "Which demonstrative means 'those' for the plural noun речі (things)?"
      options:
        - text: "ті"
          correct: true
        - text: "той"
          correct: false
        - text: "та"
          correct: false
        - text: "те"
          correct: false
      explanation: "Речі is plural, so we use the plural form ті."
    - question: "Which demonstrative means 'this' for the feminine noun лампа (lamp)?"
      options:
        - text: "ця"
          correct: true
        - text: "цей"
          correct: false
        - text: "це"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Лампа is feminine (ends in -а), so we use ця."
    - question: "Which demonstrative means 'this' for the masculine noun диван (sofa)?"
      options:
        - text: "цей"
          correct: true
        - text: "ця"
          correct: false
        - text: "це"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Диван is masculine (ends in a consonant), so we use цей."
    - question: "Which demonstrative means 'this' for the neuter noun крісло (armchair)?"
      options:
        - text: "це"
          correct: true
        - text: "цей"
          correct: false
        - text: "ця"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Крісло is neuter (ends in -о), so we use це."
    - question: "Which demonstrative means 'that' for the feminine noun кімната (room)?"
      options:
        - text: "та"
          correct: true
        - text: "той"
          correct: false
        - text: "те"
          correct: false
        - text: "ті"
          correct: false
      explanation: "Кімната is feminine (ends in -а), so we use та."
    - question: "Which demonstrative means 'this' for the masculine noun ніж (knife)?"
      options:
        - text: "цей"
          correct: true
        - text: "ця"
          correct: false
        - text: "це"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Ніж is masculine (ends in a consonant), so we use цей."
    - question: "Which demonstrative means 'this' for the feminine noun ложка (spoon)?"
      options:
        - text: "ця"
          correct: true
        - text: "цей"
          correct: false
        - text: "це"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Ложка is feminine (ends in -а), so we use ця."
    - question: "Which demonstrative means 'this' for the neuter noun блюдо (dish)?"
      options:
        - text: "це"
          correct: true
        - text: "цей"
          correct: false
        - text: "ця"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Блюдо is neuter (ends in -о), so we use це."
    - question: "Which demonstrative means 'that' for the masculine noun стілець (chair)?"
      options:
        - text: "той"
          correct: true
        - text: "та"
          correct: false
        - text: "те"
          correct: false
        - text: "ті"
          correct: false
      explanation: "Стілець is masculine (ends in a consonant), so we use той."
    - question: "Which demonstrative means 'this' for the feminine noun хата (cottage)?"
      options:
        - text: "ця"
          correct: true
        - text: "цей"
          correct: false
        - text: "це"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Хата is feminine (ends in -а), so we use ця."
    - question: "Which demonstrative means 'this' for the feminine noun квартира (apartment)?"
      options:
        - text: "ця"
          correct: true
        - text: "цей"
          correct: false
        - text: "це"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Квартира is feminine (ends in -а), so we use ця."
    - question: "Which demonstrative means 'this' for the masculine noun дім (home)?"
      options:
        - text: "цей"
          correct: true
        - text: "ця"
          correct: false
        - text: "це"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Дім is masculine (ends in a consonant), so we use цей."
    - question: "What is the key difference between Це стіл and Цей стіл?"
      options:
        - text: "Це стіл identifies (This is a table), Цей стіл specifies (This table)"
          correct: true
        - text: "They mean exactly the same thing"
          correct: false
        - text: "Це стіл is formal, Цей стіл is informal"
          correct: false
        - text: "Це стіл is plural, Цей стіл is singular"
          correct: false
      explanation: "Це стіл is identification (This is a table). Цей стіл is specification (This table) — a key distinction in Ukrainian."

- type: fill-in
  title: "Complete with the Correct Demonstrative"
  instruction: "Fill in the blank with the correct form of 'this' (цей, ця, це, ці)."
  items:
    - sentence: "___ стіл."
      answer: "Цей"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Стіл is masculine, so we use цей."
    - sentence: "___ книга."
      answer: "Ця"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Книга is feminine (ends in -а), so we use ця."
    - sentence: "___ вікно."
      answer: "Це"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Вікно is neuter (ends in -о), so we use це."
    - sentence: "___ двері."
      answer: "Ці"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Двері is always plural, so we use ці."
    - sentence: "___ лампа."
      answer: "Ця"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Лампа is feminine (ends in -а), so we use ця."
    - sentence: "___ телефон."
      answer: "Цей"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Телефон is masculine (ends in a consonant), so we use цей."
    - sentence: "___ ліжко."
      answer: "Це"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Ліжко is neuter (ends in -о), so we use це."
    - sentence: "___ шафа."
      answer: "Ця"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Шафа is feminine (ends in -а), so we use ця."
    - sentence: "___ диван."
      answer: "Цей"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Диван is masculine (ends in a consonant), so we use цей."
    - sentence: "___ крісло."
      answer: "Це"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Крісло is neuter (ends in -о), so we use це."
    - sentence: "___ кімната."
      answer: "Ця"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Кімната is feminine (ends in -а), so we use ця."
    - sentence: "___ стілець."
      answer: "Цей"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Стілець is masculine (ends in a consonant), so we use цей."
    - sentence: "___ ніж."
      answer: "Цей"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Ніж is masculine (ends in a consonant), so we use цей."
    - sentence: "___ ложка."
      answer: "Ця"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Ложка is feminine (ends in -а), so we use ця."
    - sentence: "___ блюдо."
      answer: "Це"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Блюдо is neuter (ends in -о), so we use це."

- type: fill-in
  title: "Що це? Conversations"
  instruction: "Complete each mini-conversation with the correct Ukrainian word."
  items:
    - sentence: 'Що це? — Це ___.'
      answer: "стіл"
      options: ["стіл", "стілець", "диван", "ніж"]
      explanation: "Стіл means table."
    - sentence: 'Що це? — Це ___.'
      answer: "книга"
      options: ["книга", "лампа", "шафа", "ложка"]
      explanation: "Книга means book."
    - sentence: 'Що це? — Це ___.'
      answer: "вікно"
      options: ["вікно", "ліжко", "крісло", "блюдо"]
      explanation: "Вікно means window."
    - sentence: 'Що це? — Це ___.'
      answer: "телефон"
      options: ["телефон", "диван", "стілець", "дім"]
      explanation: "Телефон means phone."
    - sentence: 'Що це? — Це ___.'
      answer: "квартира"
      options: ["квартира", "кімната", "хата", "шафа"]
      explanation: "Квартира means apartment."
    - sentence: 'Що це? — Це ___.'
      answer: "диван"
      options: ["диван", "стіл", "ніж", "телефон"]
      explanation: "Диван means sofa."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/my-world-objects.yaml`

```yaml
items:
  - lemma: "цей"
    translation: "this (masculine)"
    pos: "pronoun"
    gender: "m"
    usage: "цей стіл, цей диван"
  - lemma: "ця"
    translation: "this (feminine)"
    pos: "pronoun"
    gender: "f"
    notes: "Feminine form of цей"
    usage: "ця книга, ця лампа"
  - lemma: "це"
    translation: "this (neuter) / this is"
    pos: "pronoun"
    gender: "n"
    notes: "Also used for identification: Це стіл (This is a table)"
    usage: "це вікно, це ліжко"
  - lemma: "ці"
    translation: "these (plural)"
    pos: "pronoun"
    notes: "Plural form of цей/ця/це"
    usage: "ці двері, ці речі"
  - lemma: "той"
    translation: "that (masculine)"
    pos: "pronoun"
    gender: "m"
    usage: "той телефон, той стілець"
  - lemma: "та"
    translation: "that (feminine)"
    pos: "pronoun"
    gender: "f"
    usage: "та шафа, та кімната"
  - lemma: "те"
    translation: "that (neuter)"
    pos: "pronoun"
    gender: "n"
    usage: "те вікно, те ліжко"
  - lemma: "ті"
    translation: "those (plural)"
    pos: "pronoun"
    notes: "Plural form of той/та/те"
    usage: "ті двері, ті речі"
  - lemma: "стіл"
    translation: "table"
    pos: "noun"
    gender: "m"
    usage: "цей стіл, обідній стіл"
  - lemma: "книга"
    translation: "book"
    pos: "noun"
    gender: "f"
    usage: "ця книга, цікава книга"
  - lemma: "телефон"
    translation: "phone"
    pos: "noun"
    gender: "m"
    usage: "мій телефон, мобільний телефон"
  - lemma: "кімната"
    translation: "room"
    pos: "noun"
    gender: "f"
    usage: "ця кімната, велика кімната"
  - lemma: "стілець"
    translation: "chair"
    pos: "noun"
    gender: "m"
    usage: "зручний стілець, той стілець"
  - lemma: "ліжко"
    translation: "bed"
    pos: "noun"
    gender: "n"
    usage: "це ліжко, велике ліжко"
  - lemma: "лампа"
    translation: "lamp"
    pos: "noun"
    gender: "f"
    usage: "ця лампа, настільна лампа"
  - lemma: "вікно"
    translation: "window"
    pos: "noun"
    gender: "n"
    usage: "це вікно, біля вікна"
  - lemma: "шафа"
    translation: "wardrobe"
    pos: "noun"
    gender: "f"
    usage: "ця шафа, книжкова шафа"
  - lemma: "двері"
    translation: "door"
    pos: "noun"
    notes: "Always plural in Ukrainian (ці двері, not *ця двері)"
    usage: "ці двері, вхідні двері"
  - lemma: "дім"
    translation: "house, home"
    pos: "noun"
    gender: "m"
    usage: "цей дім, великий дім"
  - lemma: "квартира"
    translation: "apartment"
    pos: "noun"
    gender: "f"
    usage: "ця квартира, моя квартира"
  - lemma: "хата"
    translation: "traditional cottage"
    pos: "noun"
    gender: "f"
    usage: "ця хата, стара хата"
  - lemma: "ніж"
    translation: "knife"
    pos: "noun"
    gender: "m"
    usage: "цей ніж, гострий ніж"
  - lemma: "ложка"
    translation: "spoon"
    pos: "noun"
    gender: "f"
    usage: "ця ложка, срібна ложка"
  - lemma: "блюдо"
    translation: "dish"
    pos: "noun"
    gender: "n"
    usage: "це блюдо, велике блюдо"
  - lemma: "диван"
    translation: "sofa"
    pos: "noun"
    gender: "m"
    usage: "цей диван, зручний диван"
  - lemma: "крісло"
    translation: "armchair"
    pos: "noun"
    gender: "n"
    usage: "це крісло, м'яке крісло"
  - lemma: "річ"
    translation: "thing"
    pos: "noun"
    gender: "f"
    usage: "ця річ, ці речі"
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-world-objects.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/my-world-objects.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/my-world-objects.yaml`

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
