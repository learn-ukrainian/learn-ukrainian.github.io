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



**NOTE: 10 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥25 items
  - Actual: Activity has 10 items
  - Fix: Add 15 more items to 'fill-in' activity

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
  - Actual: Activity has 10 items
  - Fix: Add 10 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 6 items
  - Fix: Add 14 more items to 'fill-in' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Activities YAML lines 19, 56, 89, Activities YAML, all three activities, Entire module, Entire module — all sections, Line 102, Line 67 / Section "Практика (Practice)", Lines 14, 23, 24, 93, 94 / Sections "Вступ (Introduction)", "Презентація (Presentation)", "Займенники у родовому (Pronouns in Genitive)"

### Finding 1: Wrong Stress on мене (HIGH — Linguistic Accuracy)
**Location**: Lines 14, 23, 24, 93, 94 / Sections "Вступ (Introduction)", "Презентація (Presentation)", "Займенники у родовому (Pronouns in Genitive)"
**Problem**: The stress dictionary confirms мене́ (stress on second syllable) is the correct form. ме́не with stress on first syllable is wrong. This is a pronoun learners will use constantly — teaching wrong stress is critical.
**Required Fix**: Replace all occurrences of ме́не with мене́
**Severity**: HIGH

### Finding 2: VESUM-Failed Distractor цукра in Activities (HIGH — Activities)
**Location**: Activities YAML lines 19, 56, 89
**Problem**: цукра is NOT a valid Ukrainian word form (confirmed by VESUM: NOT FOUND). Students should not practice choosing between options where one distractor is a non-existent form. This fails the ACTIVITY_VESUM_FAIL gate.
**Required Fix**: Replace цукра with цукрі (locative, valid form) or цукру (duplicate — better: цукрові as dative alternative)
**Severity**: HIGH

### Finding 3: Activity Item Shortfall vs Plan (HIGH — Activities)
**Location**: Activities YAML, all three activities
**Problem**: Only 24 of 51 planned activity items were delivered (47%). This is a massive shortfall that undermines the drilling purpose of the module. The plan specifies high item counts precisely because genitive endings require extensive drilling.
**Required Fix**: Rebuild activities with full item counts per plan specification (25, 20, 6)
**Severity**: HIGH

### Finding 4: Zero Engagement Boxes (MEDIUM — Experience Quality)
**Location**: Entire module — all sections
**Problem**: The module has 0 callout boxes (`[!tip]`, `[!example]`, `[!cultural-note]`, etc.). Audit requires minimum 1 for A1. Callout boxes provide visual variety, quick wins, and encouragement moments crucial for beginners.
**Required Fix**: Add at minimum: 1× `[!tip]` in section "Презентація (Presentation)" about the -а/-у semantic split, 1× `[!cultural-note]` in section "Культурний контекст (Cultural Context)" around the proverb
**Severity**: HIGH

### Finding 5: Register Mismatch in Café Dialogue (MEDIUM — Language)
**Location**: Line 67 / Section "Практика (Practice)"
**Problem**: In Ukrainian service contexts (café, restaurant), a server would naturally say 「Що бажа́єте?」 not 「Що ви хо́чете?」. The A1 calibration explicitly flags this as an Anglicism. "Що ви хочете?" sounds blunt/rude from a server in Ukrainian culture.
**Required Fix**: Change to 「Що бажа́єте?」 with a brief note that this is the polite service form
**Severity**: HIGH

### Finding 6: Підсумок Uses H1 Instead of H2 (LOW — Experience Quality)
**Location**: Line 102
**Problem**: All other sections use H2 (`##`). The summary uses H1, breaking the heading hierarchy. This will cause rendering issues in the Starlight site.
**Required Fix**: Change to `## Підсумок`
**Severity**: HIGH

### Finding 7: Low Immersion (11.5% vs 30-55% target) (MEDIUM — Pedagogy)
**Location**: Entire module
**Problem**: Module 31 falls in the A1 band 21+ which targets 30-55% Ukrainian immersion. At 11.5%, the module is far under. The English prose is clear and warm, but there are opportunities for more Ukrainian text — additional example sentences, a reading practice block, or Ukrainian-only mini-dialogues.
**Required Fix**: Add a Reading Practice block (5-8 Ukrainian sentences) after section "Практика (Practice)" and expand Ukrainian examples in sections "Презентація (Presentation)" and "Займенники у родовому (Pronouns in Genitive)"
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Wrong Stress on мене (HIGH — Linguistic Accuracy)
- **Location**: Lines 14, 23, 24, 93, 94 / Sections "Вступ (Introduction)", "Презентація (Presentation)", "Займенники у родовому (Pronouns in Genitive)"
- **Original**: 「ме́не」 (5 occurrences)
- **Problem**: The stress dictionary confirms мене́ (stress on second syllable) is the correct form. ме́не with stress on first syllable is wrong. This is a pronoun learners will use constantly — teaching wrong stress is critical.
- **Fix**: Replace all occurrences of ме́не with мене́

### Issue 2: VESUM-Failed Distractor цукра in Activities (HIGH — Activities)
- **Location**: Activities YAML lines 19, 56, 89
- **Original**: `options: ["цукор", "цукру", "цукром", "цукра"]`
- **Problem**: цукра is NOT a valid Ukrainian word form (confirmed by VESUM: NOT FOUND). Students should not practice choosing between options where one distractor is a non-existent form. This fails the ACTIVITY_VESUM_FAIL gate.
- **Fix**: Replace цукра with цукрі (locative, valid form) or цукру (duplicate — better: цукрові as dative alternative)

### Issue 3: Activity Item Shortfall vs Plan (HIGH — Activities)
- **Location**: Activities YAML, all three activities
- **Original**: Activity 1 has 10 items (plan: 25), Activity 2 has 8 items (plan: 20)
- **Problem**: Only 24 of 51 planned activity items were delivered (47%). This is a massive shortfall that undermines the drilling purpose of the module. The plan specifies high item counts precisely because genitive endings require extensive drilling.
- **Fix**: Rebuild activities with full item counts per plan specification (25, 20, 6)

### Issue 4: Zero Engagement Boxes (MEDIUM — Experience Quality)
- **Location**: Entire module — all sections
- **Problem**: The module has 0 callout boxes (`[!tip]`, `[!example]`, `[!cultural-note]`, etc.). Audit requires minimum 1 for A1. Callout boxes provide visual variety, quick wins, and encouragement moments crucial for beginners.
- **Fix**: Add at minimum: 1× `[!tip]` in section "Презентація (Presentation)" about the -а/-у semantic split, 1× `[!cultural-note]` in section "Культурний контекст (Cultural Context)" around the proverb

### Issue 5: Register Mismatch in Café Dialogue (MEDIUM — Language)
- **Location**: Line 67 / Section "Практика (Practice)"
- **Original**: 「До́брий день! Що ви хо́чете?」
- **Problem**: In Ukrainian service contexts (café, restaurant), a server would naturally say 「Що бажа́єте?」 not 「Що ви хо́чете?」. The A1 calibration explicitly flags this as an Anglicism. "Що ви хочете?" sounds blunt/rude from a server in Ukrainian culture.
- **Fix**: Change to 「Що бажа́єте?」 with a brief note that this is the polite service form

### Issue 6: Підсумок Uses H1 Instead of H2 (LOW — Experience Quality)
- **Location**: Line 102
- **Original**: `# Підсумок`
- **Problem**: All other sections use H2 (`##`). The summary uses H1, breaking the heading hierarchy. This will cause rendering issues in the Starlight site.
- **Fix**: Change to `## Підсумок`

### Issue 7: Low Immersion (11.5% vs 30-55% target) (MEDIUM — Pedagogy)
- **Location**: Entire module
- **Problem**: Module 31 falls in the A1 band 21+ which targets 30-55% Ukrainian immersion. At 11.5%, the module is far under. The English prose is clear and warm, but there are opportunities for more Ukrainian text — additional example sentences, a reading practice block, or Ukrainian-only mini-dialogues.
- **Fix**: Add a Reading Practice block (5-8 Ukrainian sentences) after section "Практика (Practice)" and expand Ukrainian examples in sections "Презентація (Presentation)" and "Займенники у родовому (Pronouns in Genitive)"

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 14 | 「У ме́не нема́є квитка́.」 | 「У мене́ нема́є квитка́.」 | Stress error |
| 23 | 「У ме́не нема́є ча́су.」 | 「У мене́ нема́є ча́су.」 | Stress error |
| 24 | 「У ме́не нема́є гроше́й.」 | 「У мене́ нема́є гроше́й.」 | Stress error |
| 93 | 「ме́не」 | 「мене́」 | Stress error |
| 94 | 「Без ме́не.」 | 「Без мене́.」 | Stress error |
| 67 | 「Що ви хо́чете?」 | 「Що бажа́єте?」 | Register/Anglicism |

### D.0 Pre-Screen Disposition

1. **[STRESS_MISMATCH] ме́не → мене́**: CONFIRMED — wrong stress, 5 occurrences
2. **[STRESS_UNKNOWN] гроше́й**: DISMISSED — VESUM confirms грошей is valid gen.pl. of гроші; stress on е́й is standard
3. **[STRESS_UNKNOWN] гро́ші**: DISMISSED — standard nominative plural stress
4. **[STRESS_UNKNOWN] телефо́на**: DISMISSED — VESUM confirms телефона is valid gen.sg.; stress on о́ is standard
5. **[STRESS_MISMATCH] його́ → йо́го**: DISMISSED — його́ (stress on second syllable) is the standard genitive of він per SUM and VESUM. The suggestion йо́го appears incorrect.
6. **[STRESS_UNKNOWN] ньо́го**: DISMISSED — valid prepositional variant of його, stress is standard
7. **[STRESS_UNKNOWN] її́**: DISMISSED — valid genitive of вона, stress is standard
8. **[LOW_ENGAGEMENT]**: CONFIRMED — 0 engagement boxes, minimum 1 required
9. **[ACTIVITY_VESUM_FAIL] цукра**: CONFIRMED — цукра is NOT a valid Ukrainian word form

---

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Activities: 6/10 → 8/10
**What to fix:**
1. Rebuild Activity 1 to have 25 items per plan (currently 10)
2. Rebuild Activity 2 to have 20 items per plan (currently 8)
3. Replace цукра distractor with valid form (цукрові or цукрів) in all 3 activity files
4. Consider adding a match-up or quiz activity type for variety (plan only specifies fill-in, but variety aids learning)

**Expected score after fix:** 8/10

### Language: 7/10 → 9/10
**What to fix:**
1. Fix all 5 occurrences of ме́не → мене́ (lines 14, 23, 24, 93, 94)
2. Change 「Що ви хо́чете?」 → 「Що бажа́єте?」 on line 67

**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Same stress fixes as Language above
2. Fix цукра distractor in activities

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add 2 callout boxes: `[!tip]` in section "Презентація (Presentation)" and `[!cultural-note]` in section "Культурний контекст (Cultural Context)"
2. Fix `# Підсумок` → `## Підсумок` on line 102

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add a Reading Practice block (5-8 Ukrainian sentences) after section "Практика (Practice)" to boost immersion from 11.5% toward 30%
2. Add more Ukrainian examples in section "Займенники у родовому (Pronouns in Genitive)" (currently only 3 examples for 8 pronoun forms)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 8×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 10.4 + 10.4 + 8.0 + 13.5) / 8.9
= 76.5 / 8.9 = 8.6/10
```

---

## Audit Failures (from automated re-audit)

```
⚠️ HYDRATION NOTE: Outline sums to 1325, exceeding word_target 1200
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 1 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 1 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/the-genitive-i-absence-audit.log for details)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `н` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-genitive-i-absence.md`

```markdown
## Вступ (Introduction)

Welcome to a major milestone in your Ukrainian journey! So far, we have focused a lot on what exists. You know how to say that something is present or available using the word **«є»**. For instance, you can point out that a city has a café or that you have a ticket. But what happens when you need to express that something is missing? This is a very common situation in real life, especially when you are out shopping or ordering food in a restaurant. You need a way to talk about absence.

In English, we often rely on the simple word "not" or "no" to handle all kinds of negation. We say "I am not a student" and we also say "I do not have a ticket". Because English handles this so simply, English speakers often make a common learner error in Ukrainian. They try to use the basic negative word **«не»** for everything. But Ukrainian makes a very logical and strict distinction between these two types of negation.

If you want to negate a state, a quality, or an identity, you use **«не»**.
- **Я не студе́нт.** — I am not a student.
- **Він не до́брий.** — He is not kind.

However, when you want to declare the absence, non-existence, or lack of an object, you cannot use **«не»**. Instead, you must use the special word **«нема́є»**. This word literally means "there is no" or "it does not exist".

- **Тут нема́є кафе́.** — There is no café here.
- **У мене́ нема́є квитка́.** — I do not have a ticket.

Learning to instinctively choose **«нема́є»** when talking about missing items is your first big step. Once you master this, navigating stores and restaurants becomes much easier!

## Презентація (Presentation)

Now that you understand when to use **«нема́є»**, we need to talk about what happens to the noun that follows it. In Ukrainian, the word **«нема́є»** acts like a grammatical magnet that always attracts the Genitive case. This is a foundational rule of the language. Whenever you say that something is absent, the missing object must change its ending.

Let us look at some ready-made, high-frequency phrases you will hear constantly. These are excellent examples of the Genitive case triggered by absence.
- **У мене́ нема́є ча́су.** — I have no time.
- **У мене́ нема́є гроше́й.** — I have no money.

Notice the word for money, **гро́ші**. It is always plural in Ukrainian. Its Genitive plural form is **гроше́й**. You do not need to memorize the entire plural system yet; just learn **«нема́є гроше́й»** as an essential set phrase for your financial vocabulary.

Another powerful trigger for the Genitive case is the preposition **«без»** (without). Since "without" also implies the absence of something, it naturally requires the exact same case. This is extremely useful when ordering food or drinks. <!-- adapted from: Українська мова, Grade 4 -->
- **Ка́ва без цу́кру, будь ла́ска.** — Coffee without sugar, please.
- **Вода́ без га́зу.** — Water without gas (still water).
- **Ї́хати без квитка́.** — To ride without a ticket.

You might have noticed that masculine nouns take different endings. Why does **квито́к** become **квитка́**, while **цу́кор** becomes **цу́кру**? This is not random! Masculine nouns follow a logical split based on their meaning.

Concrete, physical objects that you can easily count or touch usually take the **«-а»** or **«-я»** ending.
- **хліб** → **нема́є хлі́ба**
- **ключ** → **нема́є ключа́**
- **квито́к** → **нема́є квитка́**

Abstract concepts, substances, and uncountable liquids usually take the **«-у»** or **«-ю»** ending.
- **час** → **нема́є ча́су**
- **цу́кор** → **нема́є цу́кру**
- **газ** → **нема́є га́зу**

Sometimes, a single word can take either ending depending on its meaning! The word **телефо́н** is a fantastic example of this semantic split. When dealing with the word **телефо́н**, you choose the ending based on your exact meaning:
- **нема́є телефо́на** — I do not have a physical phone device.
- **нема́є телефо́ну** — I do not have the phone number.

> [!tip]
> **The -а/-у Split Shortcut**: Can you touch it or count it? Use **-а/-я** (хлі́ба, квитка́). Is it a substance, feeling, or abstract idea? Use **-у/-ю** (ча́су, цу́кру). When in doubt, think: "Can I put this in a bag?"

## Практика (Practice)

Let us put this theory into active practice. As an English speaker, your brain is not used to changing the endings of nouns just because something is missing. The most typical mistake beginners make is Case Neglect. This happens when a learner correctly remembers to use **«нема́є»**, but forgets to change the noun, leaving it in the basic dictionary form (the Nominative case). We want to train your brain to anticipate the Genitive case every single time you hear or say **«нема́є»** or **«без»**.

Read these minimal pairs aloud. Feel the shift from existence to absence, and notice how the ending changes immediately.
- **Є квито́к.** — **Нема́є квитка́.**
- **Є ключ.** — **Нема́є ключа́.**
- **Є час.** — **Нема́є ча́су.**
- **Є вода́.** — **Вода́ без га́зу.**

Let us visualize these transformations. We already looked at masculine nouns, but what about feminine nouns? Feminine words ending in **«-а»** generally change to **«-и»**. Words ending in **«-я»** change to **«-і»**. Let us see this pattern in action with some essential vocabulary. <!-- adapted from: Avramenko, Grade 6 -->
- **вода́** → **во́ди** (water)
- **пробле́ма** → **пробле́ми** (problem)

Now, imagine you are stepping into a lively Ukrainian café. You want to order a hot drink, but you have specific preferences. This is a perfect real-world scenario to practice the preposition **«без»** alongside the Genitive case. Neuter nouns like **молоко́** follow a simple rule: the ending **«-о»** becomes **«-а»**. Read this short roleplay dialogue out loud to practice ordering.

> — **До́брий день! Що бажа́єте?** (Good afternoon! What would you like?)
> — **До́брий день. Ка́ву без цу́кру та без молока́, будь ла́ска.** (Good afternoon. Coffee without sugar and without milk, please.)
> — **А вода́?** (And water?)
> — **Вода́ без га́зу.** (Water without gas.)
> — **На жаль, хлі́ба нема́є.** (Unfortunately, there is no bread.)

In this dialogue, the server politely informs the customer about an absent item. Using **«нема́є»** allows for a soft, polite delivery rather than a blunt "No." Note that the server uses **«Що бажа́єте?»** — this is the standard polite service form in Ukrainian, much more natural than the direct **«Що ви хо́чете?»**. Practice these phrases until they feel completely natural in your mouth!

### Практика читання (Reading Practice)

Read the following short text entirely in Ukrainian. Do not try to translate word-by-word — focus on recognizing the genitive patterns you have just learned.

> У Мари́ни нема́є ча́су. Вона́ йде в магази́н, але́ там нема́є хлі́ба. На жаль, молока́ тако́ж нема́є. Мари́на п'є ка́ву без цу́кру та без молока́. Її́ дру́г Андрі́й тако́ж тут. У ньо́го нема́є гроше́й, але́ є квито́к. Мари́на ка́же: «Нема́є пробле́м! Я без гроше́й, він без ча́су — ми до́бра кома́нда!»

Now read it once more, this time aloud. Pay attention to how the noun endings change after **«нема́є»** and **«без»**: хлі́ба, молока́, цу́кру, гроше́й, ча́су. Every one of these is in the Genitive case.

## Культурний контекст (Cultural Context)

Language is deeply intertwined with culture, and the way Ukrainians express absence reveals a lot about their communication style. One of the most ubiquitous phrases you will encounter in Ukraine is **«Нема́є пробле́м!»** (No problems!). The word **пробле́ма** changes to its Genitive plural form, **пробле́м**. You will hear this phrase used as a marker of hospitality, flexibility, and a generally easygoing attitude. Whether you ask for a special modification to your café order, or request help with directions in the city, the cheerful response **«Нема́є пробле́м!»** immediately sets a warm tone.

Furthermore, Ukrainians often use **«нема́є»** as a tool for polite refusal. In many situations, saying a direct, flat "No" can sound overly harsh or unaccommodating. If a store is out of a certain product, a shopkeeper will rarely just say **«Ні»**. Instead, they will soften the blow by framing it around the absence of the item.
- **На жаль, квиткі́в нема́є.** — Unfortunately, there are no tickets.

This subtle shift moves the blame from the speaker to the circumstances. It is a highly polite and professional way to navigate customer service.

We can also see this grammar structure enshrined in traditional wisdom. Let us look at a famous piece of cultural code, a proverb that perfectly illustrates both grammatical triggers we learned today. <!-- adapted from: Hlazova, Grade 10 -->
- **Нема́є ди́му без вогню́.** — There is no smoke without fire.

This famous proverb uses both **«нема́є»** and **«без»** in the exact same sentence, proving how deeply ingrained the Genitive case is when expressing absence. It is the perfect sentence to memorize!

> [!cultural-note]
> In Ukrainian shops and cafés, you will rarely hear a flat **«Ні»** (No). Instead, staff soften the refusal: **«На жаль, нема́є»** (Unfortunately, there isn't any). This small shift moves the blame to circumstances, not the person — a hallmark of Ukrainian hospitality.

## Займенники у родовому (Pronouns in Genitive)

Finally, let us explore how personal pronouns behave when they are missing. The great news is that the Genitive forms of personal pronouns are completely identical to the Accusative forms you already know! This means you have one less thing to memorize.

Here are the Genitive pronouns: **мене́**, **тебе́**, **його́** / **ньо́го**, **її́** / **не́ї**, **нас**, **вас**, **їх** / **них**.
- **Без мене́.** — Without me.
- **Від тебе́.** — From you.
- **Для на́с.** — For us.
- **Без ва́с.** — Without you (plural/formal).

There is one special phonetic rule you must remember. When third-person pronouns directly follow a preposition (like **«без»** or **«від»**), they gain a prothetic consonant at the beginning for smoother pronunciation: **його́** becomes **ньо́го**, **її́** becomes **не́ї**, and **їх** becomes **них**.
- **У ньо́го нема́є ча́су.** — He has no time.
- **Без не́ї.** — Without her.
- **Я тут без них.** — I am here without them.

## Підсумок
You have done an amazing job navigating the Genitive case for absence! Let us review the key takeaways from this module. You learned that when we talk about something that does not exist or is missing, we use **«нема́є»** instead of the simple **«не»**. You discovered that both **«нема́є»** and the preposition **«без»** force the following noun into the Genitive case. For masculine nouns, we use **«-а»** / **«-я»** for concrete objects and **«-у»** / **«-ю»** for abstract substances. Finally, you saw how pronouns adapt to prepositions by adding a prothetic consonant to third-person pronouns after prepositions (**ньо́го**, **не́ї**, **них**).

Take a moment to test your knowledge with these self-check questions:
1. What is the grammatical difference in usage between **«не»** and **«нема́є»**?
2. Which case must always follow the preposition **«без»**?
3. Why does the word **квито́к** take an **«-а»** ending (**квитка́**), but **час** takes a **«-у»** ending (**ча́су**)?
4. How do you say "without her" in Ukrainian, and what special consonant is added?

Keep up the fantastic work!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-genitive-i-absence.yaml`

```yaml
- type: fill-in
  title: "Change Nouns to Genitive"
  instruction: "Choose the correct genitive form of the noun to complete each phrase."
  items:
    - sentence: "Немає ___. (хліб)"
      answer: "хліба"
      options: ["хліб", "хліба", "хлібом", "хлібі"]
      explanation: "Хліб is a concrete object, so it takes the -а ending in genitive: хліба."
    - sentence: "Немає ___. (час)"
      answer: "часу"
      options: ["час", "часу", "часом", "часі"]
      explanation: "Час is an abstract concept, so it takes the -у ending in genitive: часу."
    - sentence: "Немає ___. (квиток)"
      answer: "квитка"
      options: ["квиток", "квитка", "квитком", "квитку"]
      explanation: "Квиток is a concrete object, so it takes the -а ending in genitive: квитка."
    - sentence: "Немає ___. (цукор)"
      answer: "цукру"
      options: ["цукор", "цукру", "цукром", "цукрові"]
      explanation: "Цукор is an uncountable substance, so it takes the -у ending in genitive: цукру."
    - sentence: "Немає ___. (ключ)"
      answer: "ключа"
      options: ["ключ", "ключа", "ключем", "ключу"]
      explanation: "Ключ is a concrete object, so it takes the -а ending in genitive: ключа."
    - sentence: "Немає ___. (газ)"
      answer: "газу"
      options: ["газ", "газу", "газом", "газі"]
      explanation: "Газ is a substance, so it takes the -у ending in genitive: газу."
    - sentence: "Немає ___. (молоко)"
      answer: "молока"
      options: ["молоко", "молока", "молоком", "молоку"]
      explanation: "Neuter nouns change -о to -а in the genitive: молоко becomes молока."
    - sentence: "Немає ___. (вода)"
      answer: "води"
      options: ["вода", "води", "водою", "воді"]
      explanation: "Feminine nouns ending in -а change to -и in the genitive: вода becomes води."
    - sentence: "Немає ___. (проблема)"
      answer: "проблеми"
      options: ["проблема", "проблеми", "проблемою", "проблемі"]
      explanation: "Feminine nouns ending in -а change to -и in the genitive: проблема becomes проблеми."
    - sentence: "Немає ___. (телефон — the device)"
      answer: "телефона"
      options: ["телефон", "телефона", "телефону", "телефоном"]
      explanation: "When talking about a physical phone device, телефон takes -а: телефона."
    - sentence: "Немає ___. (телефон — the number)"
      answer: "телефону"
      options: ["телефон", "телефона", "телефону", "телефоном"]
      explanation: "When talking about a phone number (abstract), телефон takes -у: телефону."
    - sentence: "Немає ___. (дим)"
      answer: "диму"
      options: ["дим", "диму", "димом", "димі"]
      explanation: "Дим is a substance, so it takes the -у ending in genitive: диму."
    - sentence: "Немає ___. (вогонь)"
      answer: "вогню"
      options: ["вогонь", "вогню", "вогнем", "вогні"]
      explanation: "Вогонь is an abstract/natural force, so it takes the -ю ending in genitive: вогню."
    - sentence: "Немає ___. (кава)"
      answer: "кави"
      options: ["кава", "кави", "кавою", "каві"]
      explanation: "Feminine nouns ending in -а change to -и in the genitive: кава becomes кави."
    - sentence: "Без ___. (хліб)"
      answer: "хліба"
      options: ["хліб", "хліба", "хлібом", "хлібі"]
      explanation: "After без, use the genitive. Хліб (concrete) takes -а: хліба."
    - sentence: "Без ___. (молоко)"
      answer: "молока"
      options: ["молоко", "молока", "молоком", "молоку"]
      explanation: "After без, neuter nouns change -о to -а in the genitive: молоко becomes молока."
    - sentence: "Без ___. (вода)"
      answer: "води"
      options: ["вода", "води", "водою", "воді"]
      explanation: "After без, feminine nouns ending in -а change to -и: вода becomes води."
    - sentence: "Немає ___. (квиток)"
      answer: "квитка"
      options: ["квитку", "квитка", "квитком", "квиток"]
      explanation: "Квиток is a concrete object, so it takes the -а ending in genitive: квитка."
    - sentence: "Без ___. (газ)"
      answer: "газу"
      options: ["газ", "газу", "газом", "газі"]
      explanation: "After без, газ (substance) takes the -у ending: газу."
    - sentence: "Немає ___. (цукор)"
      answer: "цукру"
      options: ["цукру", "цукор", "цукром", "цукрові"]
      explanation: "Цукор is a substance, so it takes the -у ending in genitive: цукру."
    - sentence: "Без ___. (ключ)"
      answer: "ключа"
      options: ["ключ", "ключа", "ключем", "ключу"]
      explanation: "After без, ключ (concrete object) takes the -а ending: ключа."
    - sentence: "Немає ___. (проблема — plural)"
      answer: "проблем"
      options: ["проблеми", "проблем", "проблемами", "проблемах"]
      explanation: "Feminine nouns in genitive plural lose the ending entirely: проблема → проблем."
    - sentence: "Без ___. (час)"
      answer: "часу"
      options: ["час", "часу", "часом", "часі"]
      explanation: "After без, час (abstract) takes the -у ending: часу."
    - sentence: "Без ___. (проблема)"
      answer: "проблеми"
      options: ["проблема", "проблеми", "проблемою", "проблемі"]
      explanation: "After без, feminine nouns ending in -а change to -и: проблема becomes проблеми."
    - sentence: "Немає ___. (гроші — plural)"
      answer: "грошей"
      options: ["гроші", "грошей", "грошима", "грошах"]
      explanation: "Гроші is always plural. Its genitive plural form is грошей."

- type: fill-in
  title: "Complete the Sentence with Genitive"
  instruction: "Choose the correct word to complete each sentence about things that are missing."
  items:
    - sentence: "У мене немає ___."
      answer: "часу"
      options: ["час", "часу", "часом", "часі"]
      explanation: "After немає, use the genitive case. Час (abstract) becomes часу."
    - sentence: "Кава без ___, будь ласка."
      answer: "цукру"
      options: ["цукор", "цукру", "цукром", "цукрові"]
      explanation: "After без, use the genitive case. Цукор (substance) becomes цукру."
    - sentence: "Вода без ___."
      answer: "газу"
      options: ["газ", "газу", "газом", "газі"]
      explanation: "After без, use the genitive case. Газ (substance) becomes газу."
    - sentence: "На жаль, ___ немає."
      answer: "хліба"
      options: ["хліб", "хліба", "хлібом", "хлібі"]
      explanation: "After немає, use the genitive case. Хліб (concrete) becomes хліба."
    - sentence: "У мене немає ___."
      answer: "грошей"
      options: ["гроші", "грошей", "грошима", "грошах"]
      explanation: "Гроші is always plural. Its genitive plural form is грошей."
    - sentence: "Кава без ___, будь ласка."
      answer: "молока"
      options: ["молоко", "молока", "молоком", "молоку"]
      explanation: "After без, use the genitive case. Молоко (neuter) becomes молока."
    - sentence: "На жаль, ___ немає."
      answer: "квитка"
      options: ["квиток", "квитка", "квитком", "квитку"]
      explanation: "After немає, use the genitive case. Квиток (concrete) becomes квитка."
    - sentence: "У нього немає ___."
      answer: "ключа"
      options: ["ключ", "ключа", "ключем", "ключу"]
      explanation: "After немає, use the genitive case. Ключ (concrete) becomes ключа."
    - sentence: "Немає ___ без вогню."
      answer: "диму"
      options: ["дим", "диму", "димом", "димі"]
      explanation: "After немає, use the genitive case. Дим (substance) becomes диму."
    - sentence: "У неї немає ___."
      answer: "кави"
      options: ["кава", "кави", "кавою", "каві"]
      explanation: "After немає, use the genitive case. Кава (feminine) becomes кави."
    - sentence: "У мене немає ___."
      answer: "телефона"
      options: ["телефон", "телефона", "телефону", "телефоном"]
      explanation: "After немає, use the genitive case. Телефон (device, concrete) becomes телефона."
    - sentence: "Чай без ___, будь ласка."
      answer: "цукру"
      options: ["цукор", "цукру", "цукром", "цукрові"]
      explanation: "After без, use the genitive case. Цукор (substance) becomes цукру."
    - sentence: "Немає ___ — магазин зачинений."
      answer: "хліба"
      options: ["хліб", "хліба", "хлібом", "хлібі"]
      explanation: "After немає, use the genitive case. Хліб (concrete) becomes хліба."
    - sentence: "Без ___, будь ласка."
      answer: "газу"
      options: ["газ", "газу", "газом", "газі"]
      explanation: "After без, use the genitive case. Газ (substance) becomes газу."
    - sentence: "На жаль, ___ немає."
      answer: "води"
      options: ["вода", "води", "водою", "воді"]
      explanation: "After немає, use the genitive case. Вода (feminine) becomes води."
    - sentence: "Без ___ нікуди!"
      answer: "квитка"
      options: ["квиток", "квитка", "квитком", "квитку"]
      explanation: "After без, use the genitive case. Квиток (concrete) becomes квитка."
    - sentence: "У них немає ___."
      answer: "проблем"
      options: ["проблеми", "проблем", "проблемами", "проблемах"]
      explanation: "After немає, use the genitive plural. Проблеми (pl.) becomes проблем."
    - sentence: "У вас немає ___?"
      answer: "молока"
      options: ["молоко", "молока", "молоком", "молоку"]
      explanation: "After немає, use the genitive case. Молоко (neuter) becomes молока."
    - sentence: "Кава без ___ та без цукру."
      answer: "молока"
      options: ["молоко", "молока", "молоком", "молоку"]
      explanation: "After без, use the genitive case. Молоко (neuter) becomes молока."
    - sentence: "Без ___ немає диму."
      answer: "вогню"
      options: ["вогонь", "вогню", "вогнем", "вогні"]
      explanation: "After без, use the genitive case. Вогонь (natural force) becomes вогню."

- type: fill-in
  title: "I Don't Have... Conversations"
  instruction: "Imagine you are at a shop or restaurant. Choose the correct form to complete your reply."
  items:
    - sentence: "— Ви хочете чай з цукром? — Ні, без ___."
      answer: "цукру"
      options: ["цукор", "цукру", "цукром", "цукрові"]
      explanation: "After без, use the genitive. Цукор (substance) becomes цукру."
    - sentence: "— Дайте квиток, будь ласка. — На жаль, у мене немає ___."
      answer: "квитка"
      options: ["квиток", "квитка", "квитком", "квитку"]
      explanation: "After немає, use the genitive. Квиток (concrete) becomes квитка."
    - sentence: "— Ви хочете воду з газом? — Ні, без ___."
      answer: "газу"
      options: ["газ", "газу", "газом", "газі"]
      explanation: "After без, use the genitive. Газ (substance) becomes газу."
    - sentence: "— У вас є час? — Ні, у мене немає ___."
      answer: "часу"
      options: ["час", "часу", "часом", "часі"]
      explanation: "After немає, use the genitive. Час (abstract) becomes часу."
    - sentence: "— Дайте хліб, будь ласка. — На жаль, ___ немає."
      answer: "хліба"
      options: ["хліб", "хліба", "хлібом", "хлібі"]
      explanation: "After немає, use the genitive. Хліб (concrete) becomes хліба."
    - sentence: "— Кава з молоком? — Ні, без ___."
      answer: "молока"
      options: ["молоко", "молока", "молоком", "молоку"]
      explanation: "After без, use the genitive. Молоко (neuter) becomes молока."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-genitive-i-absence.yaml`

```yaml
items:
  - lemma: "немає"
    translation: "there is no, there are no"
    pos: "particle"
    notes: "Used to express absence or non-existence. Always triggers genitive case."
    usage: "У мене немає часу."
  - lemma: "без"
    translation: "without"
    pos: "preposition"
    notes: "Always followed by the genitive case."
    usage: "Кава без цукру."
  - lemma: "час"
    translation: "time"
    pos: "noun"
    gender: "m"
    notes: "Genitive: часу (abstract noun, takes -у ending)."
    usage: "У мене немає часу."
  - lemma: "гроші"
    translation: "money"
    pos: "noun"
    notes: "Always plural. Genitive plural: грошей."
    usage: "У мене немає грошей."
  - lemma: "молоко"
    translation: "milk"
    pos: "noun"
    gender: "n"
    notes: "Genitive: молока (neuter -о becomes -а)."
    usage: "Кава без молока."
  - lemma: "цукор"
    translation: "sugar"
    pos: "noun"
    gender: "m"
    notes: "Genitive: цукру (uncountable substance, takes -у ending)."
    usage: "Кава без цукру."
  - lemma: "вода"
    translation: "water"
    pos: "noun"
    gender: "f"
    notes: "Genitive: води (feminine -а becomes -и)."
    usage: "Вода без газу."
  - lemma: "хліб"
    translation: "bread"
    pos: "noun"
    gender: "m"
    notes: "Genitive: хліба (concrete object, takes -а ending)."
    usage: "Немає хліба."
  - lemma: "проблема"
    translation: "problem"
    pos: "noun"
    gender: "f"
    notes: "Genitive singular: проблеми. Genitive plural: проблем."
    usage: "Немає проблем!"
  - lemma: "квиток"
    translation: "ticket"
    pos: "noun"
    gender: "m"
    notes: "Genitive: квитка (concrete object, takes -а ending)."
    usage: "Немає квитка."
  - lemma: "ключ"
    translation: "key"
    pos: "noun"
    gender: "m"
    notes: "Genitive: ключа (concrete object, takes -а ending)."
    usage: "Немає ключа."
  - lemma: "телефон"
    translation: "phone; phone number"
    pos: "noun"
    gender: "m"
    notes: "Genitive: телефона (device, -а) or телефону (number, -у). Semantic split."
    usage: "Немає телефона."
  - lemma: "газ"
    translation: "gas, sparkling (in drinks)"
    pos: "noun"
    gender: "m"
    notes: "Genitive: газу (substance, takes -у ending)."
    usage: "Вода без газу."
  - lemma: "від"
    translation: "from"
    pos: "preposition"
    notes: "Requires genitive case. Від тебе — from you."
    usage: "Від тебе."
  - lemma: "на жаль"
    translation: "unfortunately"
    pos: "adverb"
    notes: "Used to soften refusals or bad news."
    usage: "На жаль, хліба немає."
  - lemma: "дим"
    translation: "smoke"
    pos: "noun"
    gender: "m"
    notes: "Genitive: диму. Used in the proverb: Немає диму без вогню."
    usage: "Немає диму без вогню."
  - lemma: "вогонь"
    translation: "fire"
    pos: "noun"
    gender: "m"
    notes: "Genitive: вогню. Used in the proverb about smoke and fire."
    usage: "Немає диму без вогню."
  - lemma: "кава"
    translation: "coffee"
    pos: "noun"
    gender: "f"
    notes: "Common in ordering phrases with без."
    usage: "Кава без цукру та без молока."
  - lemma: "будь ласка"
    translation: "please"
    pos: "particle"
    notes: "Essential polite phrase for ordering and requests."
    usage: "Каву без цукру, будь ласка."
  - lemma: "є"
    translation: "there is, there are; is"
    pos: "verb"
    notes: "Contrast with немає. Є = existence, немає = absence."
    usage: "Є квиток. — Немає квитка."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-genitive-i-absence.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-genitive-i-absence.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-genitive-i-absence.yaml`

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
