# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> The review already applied some fixes. You handle what's still failing.
> All file contents are provided below — produce FIND/REPLACE pairs directly.

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original, not less.
- **PRESERVE the author's intent.** If a paragraph explains something poorly, rewrite it to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your rewrite should read like the original author wrote it on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information that cannot be salvaged). This should be rare.

---

## Fix Plan (from Phase D.1 review)

## Critical Issues Found

### Issue 1: Factual Overstatement (Minor)
- **Location**: Line 269 / Section "Практика"
- **Original**: 「одна мебля」 (used as example of impossible form)
- **Problem**: The module states "You cannot say 'one furniture' (*одна мебля*)". However, VESUM confirms that `мебля` exists as an archaic noun form (`noun:inanim:f:v_naz:arch`). The claim is overly absolute. While `мебля` is archaic and not standard in modern speech, saying it "cannot" be said is inaccurate.
- **Fix**: Soften to "In modern Ukrainian, *мебля* is archaic — you will almost always hear the plural **меблі**." or "The singular form *мебля* is archaic and rarely used today."

### Issue 2: Untranslated Vocabulary in Dialogue
- **Location**: Line 305 / Section "Практика"
- **Original**: 「Я хо́чу купи́ти цей сті́л.」 (dialogue with "Продавець" as speaker label)
- **Problem**: The word **Продавець** (seller/salesperson) appears as a dialogue speaker label without translation or glossing. This word is NOT in the vocabulary list. At A1, untranslated words outside the taught vocabulary can cause confusion.
- **Fix**: Add an inline gloss: **Продавець (Salesperson):** or add it to the vocabulary list.

### Issue 3: Richness Gaps (Audit-Blocking)
- **Location**: Module-wide
- **Problem**: The automated richness audit shows 74% (threshold 95%) with gaps: `engagement: 4/5`, `cultural: 1/3`, `dialogues: 0/4`. The actual content CONTAINS 3 `[!culture]` callouts and 5 dialogues, but the scanner doesn't detect them — likely a markup format mismatch. The module needs to conform to the expected markup patterns for the scanner to count these elements.
- **Fix**: (1) Ensure dialogues use whatever format the scanner expects (check scanner regex). (2) Verify why only 1 of 3 `[!culture]` boxes is counted. (3) Add 1 more `[!engagement]` interactive prompt (e.g., before the reading passages in section "Практика").

### Issue 4: Learning Objectives Arrive Late
- **Location**: Lines 17-28 / Section "Вступ"
- **Problem**: The first ~400 words of the introduction discuss culture, recap prior modules, and explain demonstratives conceptually before the learner knows what they'll learn today. The explicit preview ("we will learn how to form and use the gendered forms...") doesn't arrive until line 26-28. At A1, the "Today you'll learn..." moment should come within the first 2-3 sentences.
- **Fix**: Add a brief learning preview after the first paragraph: "By the end of this lesson, you'll be able to point at objects around you and say 'this table' or 'that window' with perfect grammatical agreement."

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 269 | 「одна мебля」 (claimed impossible) | Acknowledge as archaic, not impossible | Factual |
| 305 | Продавець (unglossed) | Продавець (Salesperson) | Missing gloss |

---

## Fix Plan to Reach 9.0/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Lines 17-19: Move a brief learning objective preview ("Today you'll learn to point at objects near and far using gender-matched demonstratives") to immediately after the opening welcome sentence, before the proverb discussion.
2. Consider whether the two reading passages (L168-184, L191-200) could be consolidated. Both test the same skills.

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add an `[!engagement]` interactive prompt before the reading passage in section "Практика" (around L166) to break up the dense practice material.
2. Ensure dialogue markup matches scanner expectations to resolve the `dialogues: 0/4` richness gap.

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Differentiate quizzes 3 and 4 — consider converting one to a different format (e.g., make quiz 4 a "drag-and-drop" or add sentence context to the far-demonstrative items so they feel distinct from the near-demonstrative quiz).
2. Add English gloss for Продавець in dialogue activity items if referenced.

**Expected score after fix:** 9/10

### Richness Gaps (Audit-Blocking)
**What to fix:**
1. `dialogues: 0/4` — The 5 existing dialogues need to match scanner format. Check what pattern the richness scanner uses and reformat accordingly.
2. `cultural: 1/3` — 3 `[!culture]` boxes exist; verify scanner regex and fix any format issue preventing detection.
3. `engagement: 4/5` — Add 1 more interactive engagement element (e.g., an `[!engagement]` callout with a self-check question between the two reading passages in section "Практика").

**Expected richness after fix:** ≥95%

### Projected Overall After Fixes
```
Experience: 9×1.5 = 13.5
Language: 9×1.1 = 9.9
Pedagogy: 9×1.2 = 10.8
Activities: 9×1.3 = 11.7
Beginner Safety: 9×1.3 = 11.7
LLM Fingerprint: 9×1.0 = 9.0
Linguistic Accuracy: 9×1.5 = 13.5
Total: 80.1 / 8.9 = 9.0/10
```

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
failing gates:
lesson: 4782/3300 (raw: 5045) | pedagogy: 1 violations
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/my-world-objects-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
```

---

## File Contents

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-world-objects.md`

```markdown
<!-- SCOPE
Covers: Demonstrative pronouns (цей/той), gender agreement with household objects, distinguishing near vs far objects, cultural concepts of home.
Not covered:
  - Complex plural noun declensions → a1-12
  - Prepositional case for locations (in the room, on the table) → a1-15
Related: a1-03 (Gender), a1-09 (This Is, I Am)
-->

# My World: Objects

> **Чому це важливо?**
>
> Your home is your most personal environment, filled with objects you interact with daily. Moving from simply naming these objects to specifically pointing them out—distinguishing "this book" from "that table"—is a big step forward in what you can say. Mastering demonstratives allows you to navigate and organize your physical space in Ukrainian with precision and natural fluency.

## Вступ

Welcome back. Today, we are going to step into your personal space. Our environment is filled with objects that matter to us. We pick them up, we point at them from across the room, and we organize our daily lives around them. Being able to talk about these objects smoothly is one of the most practical skills you can develop. 

In Ukrainian culture, the home is a profound and deeply respected space. There is a beautiful and famous proverb that captures this feeling perfectly: **«В гостя́х до́бре, а вдо́ма кра́ще»**. It is the cultural equivalent of the English phrase "East or West, home is best." This phrase anchors our lesson today. We are going to learn how to interact linguistically with the home and the foundational objects inside it. 

Do you remember when we discussed that every single object in Ukrainian has a grammatical gender? We learned this in our earlier modules. A table is masculine, a book is feminine, and a window is neuter. At the time, you might have wondered why this classification was necessary. Today, you will see exactly why grammatical gender is the master key that unlocks the language. You cannot effectively point to an object in Ukrainian without knowing its gender.

> [!context] **The Power of Pointing**
> Pointing is one of the most fundamental human communicative acts. Before we even learn to speak complex sentences as children, we point. In language, we "point" using words called demonstrative pronouns. They ground our speech in physical reality, connecting our thoughts directly to the environment around us.

We are focusing on a very specific grammatical skill today, one that is highly emphasized in Ukrainian educational standards. We are going to master demonstrative pronouns. In simple terms, these are the words we use to point at things: "this" and "that." In English, you can simply say "this table" or "this book" without ever changing the word "this." The English demonstrative is static. Ukrainian, however, requires harmony. The word for "this" must dynamically adapt to match the grammatical gender of the object it describes.

This means we will learn how to form and use the gendered forms of the words for "this" (**цей**, **ця**, **це**) and "that" (**той**, **та**, **те**), as well as their plural forms (**ці**, **ті**). This might seem like a lot of new words for a relatively simple concept, but please do not worry. As your tutor, I will guide you through the logical, rhythmic patterns that make these words easy to remember. We will see how these demonstratives rhyme and dance with the nouns they modify. By the end of this lesson, pointing to objects in your room will feel natural, structured, and inherently Ukrainian.

## Презентація

Let's build our understanding of how to point at objects step by step. We will start by clearing up a common point of confusion, then we will learn how to talk about objects we can touch, and finally, we will learn how to talk about objects across the room.

### The "Це" vs "Цей" Hurdle: Identification vs Specification

Let's clear up the most common hurdle right away. You already know the word **це**. You use it to identify something for the first time. 

*   **Це сті́л.**
*   **Це кни́га.**
*   **Це вікно́.**

Notice how **це** stays exactly the same in every single sentence, no matter what object follows it? In these sentences, **це** acts as the invariant subject of the sentence. You are simply declaring what the object is to someone who might not know. We call this grammatical function *identification*.

However, what happens when you want to describe a specific object rather than just name it? You no longer want to say "This is a table." You want to say "This table is big," or you just want to point and say "This table." This is called *specification*. When you specify, the word for "this" acts as an adjective. It attaches itself directly to the noun, and in Ukrainian, adjectives must perfectly match the gender of their nouns.

This is where the invariant **це** changes its shape to match the world around it. For a masculine noun, "this" becomes **цей**.

*   **Цей сті́л...**
*   **Ця кни́га...**

Understanding the profound difference between the unchanging **це** in "This is..." and the gender-matching demonstrative in "This table..." is a major milestone in learning Ukrainian. It is the shift from just naming the world to actively interacting with it.

> [!warning] **The English Trap**
> Because English uses "this" for both identification ("This is a book") and specification ("This book is heavy"), English speakers naturally want to use **це** for everything. Always ask yourself: am I naming the object for the first time, or am I pointing at a specific one?

### Pointing to Near Objects (Цей, Ця, Це, Ці)

When an object is close to you—close enough to touch with your hand—you use the "near" demonstratives. Let's look at how these adapt to the three genders and the plural form.

**Masculine: Цей**
For masculine nouns, which typically end in a hard or soft consonant, we use the word **цей**. It sounds somewhat like the English word "say," but starting with a sharp "ts" sound. You use this when holding or touching a masculine object.

*   **Цей сті́л.** Це мій стіл. Він великий. Цей стіл тут. 
*   **Цей телефо́н.** Це мій телефон.
*   **Цей ні́ж.** Це ніж. Я маю ніж.

If you are holding your smartphone, you would say **цей телефо́н**. It is in your personal space, and because the word ends in a consonant (н), it demands the masculine **цей**.

**Feminine: Ця**
For feminine nouns, which usually end in the vowels **-а** or **-я**, we use the word **ця**. It sounds like "tsya." This is perhaps the most satisfying demonstrative to use because it creates an immediate, audible rhyme with the noun it modifies.

*   **Ця кни́га.** Це гарна книга. Я читаю.
*   **Ця кімна́та.** Це моя кімната.
*   **Ця ша́фа.** Це велика шафа.

When you are standing inside your bedroom, you refer to it as **ця кімна́та**. The matching "a" sounds at the end of both words create a sense of linguistic completion.

**Neuter: Це**
Neuter nouns generally end in **-о** or **-е**. The demonstrative word matching a neuter noun is **це**. It sounds like "tseh." Yes, this is the exact same spelling and pronunciation as the identification word we discussed earlier, but here it acts specifically as a neuter adjective modifying a neuter noun.

*   **Це вікно́.** Це чисте вікно. Воно тут.
*   **Це лі́жко.** Це зручне ліжко. Я сплю тут.
*   **Це крі́сло.** Це старе крісло.

If you are sitting on your bed, you are sitting on **це лі́жко**. Again, notice the visual and auditory alignment: the mid vowels "e" and "o" complement each other smoothly.

**Plural: Ці**
For plural objects—when you have more than one item in your immediate vicinity—we use the word **ці**. It sounds like "tsee." The plural form simplifies things considerably. In the plural, grammatical gender distinctions are neutralized. Whether you have multiple masculine tables, feminine books, or neuter windows, the word is always **ці**.

*   **Ці ре́чі.** Це мої речі. Вони лежать тут.
*   **Ці книжки́.** Це нові книжки.
*   **Ці столи́.** Це великі столи. Вони стоять тут.

> [!fun-fact] **How Many Genders?**
> Ukrainian has three grammatical genders, which is common among Slavic languages. But not all languages agree on the number! German also has three (der, die, das), French has two (le, la), and Finnish has none at all. The Ukrainian system may feel unfamiliar at first, but once you learn to "hear" the vowel patterns at the end of nouns, choosing the right demonstrative becomes almost automatic.

### Pointing to Far Objects (Той, Та, Те, Ті)

What if the object is across the room? You can no longer touch it. You have to point with your finger. For distant objects, we shift away from the "near" group and use the "far" group. 

> [!tip] **The "T" Mnemonic**
> There is a wonderful and highly effective memory trick for the "far" demonstratives: they all start with the letter **Т**. Think of the English words "**T**hat" and "**T**here." They also start with T! When you point over *there* at *that* distant object, you must use the Ukrainian **Т** words.

The endings of these distant demonstratives follow the exact same logical vowel pattern as the "near" words we just learned. 

**Masculine: Той**
If a masculine object is far away, we use **той**.
*   **Той сті́л.** Той стіл стоїть там. Він далеко.
*   **Той телефо́н.** Той телефон лежить там.

**Feminine: Та**
If a feminine object is out of reach, we use **та**.
*   **Та ла́мпа.** Та лампа дуже красива. Вона далеко.
*   **Та ша́фа.** Та шафа велика. Вона стоїть там.

**Neuter: Те**
For a distant neuter object, we use **те**.
*   **Те вікно́.** Те вікно брудне. Воно далеко.
*   **Те лі́жко.** Те ліжко нове. Там спить гість.

**Plural: Ті**
For multiple distant objects of any gender, we use **ті**.
*   **Ті ре́чі.** Ті речі лежать там.
*   **Ті столи́.** Ті столи дуже старі. Вони там.

Take a moment to compare them directly. You can physically feel the difference in distance. **Ця кімна́та** refers to this room you are standing in right now, while **та кімна́та** refers to that room down the hall. **Цей телефо́н** is the phone currently in your hand, whereas **той телефо́н** is the one you left on the desk across the office. 

### Special Plurals: The Door Exception

Here's a quirk that surprises many learners: the Ukrainian word for "door" is always plural. Let's look at why.

In English, a door is conceptualized as a singular object. You walk up to it and say "this door." In Ukrainian, the word for door is **две́рі**. This word is inherently plural. It belongs to a category of nouns that have no singular form at all. Grammatically, you cannot have "one door"; you always have a set of "doors," likely referring historically to the two panels that made up traditional entrances.

Because **две́рі** is grammatically plural at all times, it must always take the plural demonstrative pronoun, regardless of how many physical doors you are actually looking at.

*   **Ці две́рі.** Ці двері відкриті.
*   **Ті две́рі.** Ті двері закриті.

If you are standing right next to the entrance of your home, ready to open it, you say **ці две́рі**. If you are pointing at the emergency exit at the far end of a long corridor, you say **ті две́рі**. Grammatically, you cannot use the singular **ця** or **та** with it. Remembering this small but critical detail will instantly make your Ukrainian sound much more authentic.

### The Poetic Rhythm of Gender Agreement

Let's take a step back and notice the patterns in Ukrainian grammar. The system of matching demonstrative endings to noun endings is not an arbitrary set of academic rules designed to make learning difficult. It is a characteristic feature of the language's structure that creates physical, acoustic rhythm. 

When you match the gender correctly, the sentence physically sounds better to the ear. It creates a linguistic harmony. Look at the feminine pair: **ця** - **книга**. Both end with wide, open vowels (я - а). Now look at the neuter pair: **це** - **вікно**. The endings complement each other — the front е of **це** pairs with the back, rounded о of **вікно**. 

This harmony means that the language actively helps you speak it correctly. As you practice, your ear will become tuned to these frequencies. Eventually, if you accidentally pair a masculine demonstrative with a feminine noun, it will physically sound "wrong" or "off-balance" to you, long before you consciously remember the grammar rule. Embrace this rhythm.

### Demonstrative Paradigm Summary

Here is the complete demonstrative paradigm at a glance:

| Gender | Near (this) | Far (that) |
|---|---|---|
| Masculine (він) | **цей** | **той** |
| Feminine (вона) | **ця** | **та** |
| Neuter (воно) | **це** | **те** |
| Plural (вони) | **ці** | **ті** |

> [!tip] **Pattern**
> Near demonstratives start with **Ц-**, far demonstratives start with **Т-**. The vowel ending always matches the gender: **-ей** (masc.), **-я/-а** (fem.), **-е** (neut.), **-і** (plural).
 

## Практика

Read the following passages slowly. Try to identify every demonstrative pronoun and its gender. After each passage, answer the comprehension questions.

**Читання:**
Де ти? Я тут. Це моя кімната. Вона велика і чиста. 
Що це? Це стіл. Це новий стіл. Цей стіл тут.
Що там? Це шафа. Це стара шафа. Та шафа там.
Цей стіл тут. Та шафа там. Це вікно чисте. Ті двері відкриті. 
Де ніж? Цей ніж тут. Він гострий. Де блюдо? Це блюдо там.
Я маю телефон. Де мій телефон? Цей телефон тут. Той телефон там.
Я люблю мій дім. Тут зручно. Тут тепло. Тут добре.
Ці речі мої. Ті речі твої. 
Ці нові столи мої. Ті старі столи твої.
Ця книга моя. Та велика книга твоя.
Це чисте вікно моє. Те вікно твоє.
Тут є цей новий диван. Там є те старе крісло.
Я сиджу тут. Ти сидиш там. 
Я маю цей стіл і цей диван.
Ти маєш той стіл і те крісло.
Мій дім тут. Твій дім там.

> **Comprehension Questions:**
> 1. Which demonstrative does the speaker use for **стіл** — and why that form?
> 2. Is **та шафа** near or far from the speaker? How do you know?
> 3. Find two plural demonstratives in the text. What nouns do they modify?

**Читання 1:**

Read slowly. Circle every demonstrative pronoun you find. What gender is each one?

Це кафе. Тут стоїть цей стілець. Він зручний. Та полиця далеко. Ці чашки тут. Цей чайник гарячий. Ця кава гаряча. Ця тарілка чиста. Те дзеркало велике. Я люблю це кафе. Тут тепло і добре. Ці меблі нові. Ті картини красиві.

> **Comprehension Questions:**
> 1. Is **цей стілець** near or far from the speaker?
> 2. What gender is **та полиця**, and how can you tell from the demonstrative?
> 3. How many different demonstrative forms appear in this passage? Can you find a plural one?


Now that we understand the theory and the elegant logic behind demonstratives, it is time to actively practice. We need to train your brain to quickly match proximity (near/far) with gender (masculine/feminine/neuter/plural).

### The Gender Matching Drill

One of the most persistent errors for learners transitioning from English to Ukrainian is saying things like "цей книга". Let's examine why this happens and how to fix it permanently. 

English relies entirely on word order, so the brain simply grabs the first word it learned for "this" (**цей**) and pastes it onto every noun, regardless of gender. To fix this, we must build a new mental habit: we must look at the ending of the noun *before* we choose our demonstrative. 

Let's do a targeted drill to correct this reflex. Look at how the mismatched, incorrect pairs are transformed into correct, harmonious Ukrainian phrases:

*   INCORRECT: *цей кімната* 
    *   CORRECT: **ця кімна́та** — The noun ends in -а, demanding the feminine form.
*   INCORRECT: *це телефон* (when trying to specify "this phone")
    *   CORRECT: **цей телефо́н** — The noun ends in a consonant, demanding the masculine form.
*   INCORRECT: *ця вікно*
    *   CORRECT: **це вікно́** — The noun ends in -о, demanding the neuter form.
*   INCORRECT: *цей двері*
    *   CORRECT: **ці две́рі** — The noun is strictly plural, demanding the plural form.

Your mental checklist should always be: 
1. How far away is it? (Determines Ц- or Т- base)
2. What is the last letter of the object? (Determines the gender ending)
3. Combine them to create the perfect match.

> Don't worry if this seems like a lot of new words. You already know the key to sorting them — just look at the last letter of the noun!

### Sorting the Room: Kitchen and Furniture

Let's apply this checklist to some new household vocabulary. We will organize these objects by their grammatical gender using the "near" demonstratives, pretending they are all right in front of us. 

First, let's look at objects you would find in a kitchen (**ку́хня**):
*   **Цей ні́ж.** Де ніж? Цей ніж лежить тут. — The word ends in a hard consonant (ж), so it is masculine.
*   **Цей чайни́к.** Цей чайник гарячий. — Ends in a consonant (к), masculine.
*   **Ця ло́жка** — The word ends in -а, so it is feminine.
*   **Ця ча́шка.** Ця чашка біла. — Ends in -а, feminine.
*   **Ця тарі́лка.** Ця тарілка чиста. — Ends in -а, feminine.
*   **Це блю́до** — The word ends in -о, so it is neuter.

Now, let's step into the living room and look at the furniture (**ме́блі**):
*   **Цей дива́н** — Ends in a consonant (н), masculine.
*   **Цей годи́нник.** Цей годинник старий. — Ends in a consonant (к), masculine.
*   **Цей сті́лець.** Цей стілець зручний. — Ends in a consonant (ць), masculine.
*   **Ця ша́фа.** Це велика шафа. — Ends in -а, feminine.
*   **Ця поли́ця.** Ця полиця нова. — Ends in -я, feminine.
*   **Ця карти́на.** Ця картина гарна. — Ends in -а, feminine.
*   **Це крі́сло.** Це старе крісло. — Ends in -о, neuter.
*   **Це дзе́ркало.** Це чисте дзеркало. — Ends in -о, neuter.

And in the bedroom (**спа́льня**):
*   **Цей кили́м.** Цей килим м'який. — Ends in a consonant (м), masculine.
*   **Ця поду́шка.** Ця подушка зручна. — Ends in -а, feminine.
*   **Ця ко́вдра.** Ця ковдра тепла. — Ends in -а, feminine.

And in the bathroom (**ва́нна кімна́та**):
*   **Це ми́ло.** Це нове мило. Воно біле. — Ends in -о, neuter.
*   **Цей рушни́к.** Цей рушник чистий. Він мій. — Ends in a consonant (к), masculine.
*   **Ця ва́нна.** Ця ванна велика. Вона біла. — Ends in -а, feminine.

And some useful items you see every day:
*   **Ця ва́за.** Ця ваза гарна. Вона моя. — Ends in -а, feminine.
*   **Цей холоди́льник.** Цей холодильник новий. Він великий. — Ends in a consonant (к), masculine.
*   **Ця пли́та.** Ця плита гаряча. Вона нова. — Ends in -а, feminine.

By physically visualizing these objects and consciously applying the matching demonstrative, you are wiring the grammar directly into your spatial memory. When you sit on a sofa, mentally tell yourself **цей дива́н**. When you open a wardrobe, think **ця ша́фа**. 

> [!did-you-know] **Меблі — Another Pluralia Tantum Noun**
> The Ukrainian word for furniture is **ме́блі**, and just like **две́рі**, it only exists in the plural form. You cannot say "one furniture" (*одна мебля*) any more than you can say "one scissors" in English. So if you want to point at the furniture in your room, you always use the plural demonstrative: **ці ме́блі** (this furniture, near) or **ті ме́блі** (that furniture, far).

> [!try-it] **Room Scan Challenge**
> Before reading the scenarios below, try this yourself: Pick any object within arm's reach and say its name with the correct "near" demonstrative (Цей? Ця? Це?). Now point to an object across the room and say it with the "far" demonstrative (Той? Та? Те?). Did you match the gender correctly?

### Near or Far? The Proximity Challenge

Let's put distance into the mix. In real life, we constantly shift our perspective between what we are holding and what we are looking at across the room. Read the following scenarios and visualize the space.

**Scenario 1: Working at your desk.**
You are sitting down to study. You touch the wooden surface in front of you and say: **«Цей сті́л мій. Він великий. Цей стіл новий і зручний.»** Then, you look up and point to the glass on the opposite wall: **«Те вікно́ там. Воно чисте. Те вікно велике.»** You seamlessly shifted from a near-masculine to a far-neuter.

**Scenario 2: Relaxing in the evening.**
You are curled up reading. You hold the novel in your hands and say: **«Ця кни́га цікава. Вона нова. Ця книга моя.»** However, it is getting dark, so you point to the light fixture in the corner of the room: **«Та ла́мпа далеко. Вона красива. Та лампа стара.»** Here, you shifted from a near-feminine to a far-feminine.

**Scenario 3: In the kitchen.**
You are in the kitchen. You pat the fridge beside you: **«Цей холоди́льник новий. Він великий.»** You point at the stove across the room: **«Та пли́та там. Вона гаряча.»** You grab the towel from the counter: **«Цей рушни́к чистий. Він мій.»**

Practicing these contrasting pairs builds remarkable agility in your speaking. It forces you to process both space and grammar simultaneously.

> [!fact] **Pluralia Tantum Nouns**
> Words like **две́рі** that only exist in the plural form are called *pluralia tantum* nouns in linguistics. English has them too—think of words like "scissors," "pants," or "glasses." You can't have one "pant." Ukrainian just applies this logic to different objects, like doors!

### Mini-Dialogues in Context

To truly cement these concepts, let's look at how Ukrainian speakers use these demonstratives in everyday, natural conversations. Read these mini-dialogues and pay attention to how the speakers confirm or clarify which object they are discussing.

**Dialogue 1: Looking for a lost item**
*   **Олена:** **Де мій телефо́н?**
*   **Андрій:** **Цей телефо́н?**
*   **Олена:** **Ні, не цей. Той телефо́н.**
*   **Андрій:** **Той стари́й?**
*   **Олена:** **Так, той стари́й.**

**Dialogue 2: Furniture shopping**
*   **Максим:** **Я хо́чу купи́ти цей сті́л.**
*   **Продавець:** **Цей сті́л? Він га́рний. А та ша́фа?**
*   **Максим:** **Ні, та ша́фа завели́ка. А це крі́сло?**
*   **Продавець:** **Це крі́сло зру́чне.**

**Dialogue 3: Dealing with the exception**
*   **Марія:** **Будь ла́ска, зачини́ ті две́рі.**
*   **Іван:** **Ці две́рі?**
*   **Марія:** **Ні, не ці. Ті две́рі, там.**
*   **Іван:** **А, ті. До́бре.**

**Dialogue 4: Describing the room**
*   **Катерина:** **Ця кімна́та га́рна.**
*   **Олег:** **Так, і це вікно́ вели́ке.**
*   **Катерина:** **А той дива́н зру́чний?**
*   **Олег:** **Ду́же зру́чний! А ця ла́мпа нова́?**
*   **Катерина:** **Так, ця ла́мпа нова́.**

**Dialogue 5: In the kitchen**
*   **Тетяна:** **Де мій ніж?**
*   **Петро:** **Цей ніж?**
*   **Тетяна:** **Так, цей. А де ця ло́жка?**
*   **Петро:** **Та ло́жка? Вона́ там.**
*   **Тетяна:** **Ні, ця ло́жка тут. Та — там.**

Notice how the demonstratives do all the heavy lifting in these conversations. They clarify intent, confirm location, and prevent misunderstandings, all while maintaining perfect grammatical harmony with the nouns.

## Культурний контекст

Ukrainian homes have their own vocabulary and cultural rules. To truly understand the objects of the Ukrainian home, we must explore the cultural concepts that organize it.

### The Heart of the Space: Покуття (Pokuttia)

If you step into a traditional Ukrainian home, the space is not organized randomly. It is oriented around a specific, spiritually significant focal point known as the **поку́ття**. 

Historically, the **поку́ття** was located diagonally opposite the large, masonry stove (**піч**). It was the most honored place in the house, decorated with intricately embroidered towels (**рушники́**) draped over religious icons. 

> [!culture] **The Піч — Soul of the Ukrainian Home**
> The traditional masonry stove (**піч**) was not just for cooking. It heated the entire house, served as a sleeping platform for the elderly, and was used to dry herbs and clothes. In folk belief, the **піч** was a protective boundary — a house spirit (**домови́к**) was thought to live behind or inside it. Even today, the expression **«танцювати від печі»** (to dance from the stove) means "to start from the basics."

This spatial organization dictated how people moved and spoke within the room. When a guest entered a traditional home, they would not immediately look at the host. They would first look to the **поку́ття**, remove their hat, and perhaps bow or say a brief blessing, paying respect to the spiritual center of the household before greeting the physical inhabitants. 

While modern apartments in Kyiv or Lviv may not have a traditional stove, the cultural memory of the **поку́ття** remains. Many Ukrainian families still designate a specific high shelf or corner for icons and **рушники́**. Understanding this helps you realize that in Ukrainian culture, physical space and the objects within it are deeply mapped with cultural respect and orientation.

> [!culture] **The Power of the Threshold**
> In Ukrainian tradition, the threshold of the door (**порі́г**) is a boundary between the safe, known world of the home and the unpredictable outside world. This is why many Ukrainians will refuse to shake hands or hand objects directly across a threshold—you must either invite the person inside or step outside to complete the exchange!

> [!culture] **Рушники — More Than Towels**
> The embroidered cloths called **рушники́** that decorate the **поку́ття** are not ordinary towels. Each **рушни́к** carries symbolic patterns — red thread for life and love, black for eternity. They are used in weddings (the couple stands on one), in greeting honored guests (bread and salt are presented on one), and in funerals. A **рушни́к** is a thread connecting generations.

### Дім, Хата, Квартира: Where Do We Live?

When we talk about where we live, Ukrainians use three distinct words that carry very different emotional and physical meanings. Understanding the nuance between them is crucial for sounding culturally authentic.

The first word is **ха́та**. This word refers to the traditional, physical rural dwelling. Historically, a **хата** was a whitewashed building with a thatched roof, surrounded by a garden. Today, it still generally refers to a private house in a village or the countryside. It represents ancestral heritage. You will frequently hear it in folklore and proverbs.

The second word is **кварти́ра**. This is the physical reality for the vast majority of modern Ukrainians living in urban centers. It is a functional, modern space in a multi-story building. If you ask a friend in the city where they live, they will give you the address of their **кварти́ра**. 

The third, and most important word, is **ді́м**. This word is not just about architecture; it is an emotional anchor. It represents the concept of belonging, safety, and family. Regardless of whether you physically reside in a rural **хата** or a modern urban **квартира**, the place where you truly belong is your **дім**. 

When Ukrainians use the proverb we learned at the beginning of the lesson, **«В гостя́х до́бре, а вдо́ма кра́ще»**, they are invoking this powerful, emotional connection. They are not saying the physical architecture of their apartment is superior; they are expressing that the emotional sanctuary of their **дім** is irreplaceable.

## Продукція та підсумок

You have learned the theory, practiced the grammar, and explored the cultural context. Before we move to your final task, here is a quick-reference card you can return to at any time:

| | Near (close to you) | Far (across the room) |
|---|---|---|
| **Masculine** (consonant ending) | **цей** стіл | **той** стіл |
| **Feminine** (-а / -я ending) | **ця** книга | **та** книга |
| **Neuter** (-о / -е ending) | **це** вікно | **те** вікно |
| **Plural** | **ці** двері | **ті** двері |

Now, it is time to turn this knowledge into active, spoken Ukrainian. You've already mastered the patterns — now let's put them into action.

### Your Turn: The Interior Designer Persona

For your final task, we are going to step into a roleplay scenario. I want you to adopt the persona of an Interior Designer who is analyzing a living space. 

Please stand up in the center of the room you are currently in. Look around you. You are going to catalog the objects in this space for your design project.

**Step 1: The Near Objects**
Walk up to three different objects in your room. Physically touch each one. As you touch it, confidently state what it is, using the correct gendered demonstrative for a near object. 
Say aloud:
*   "**Цей...**" (for a masculine object, like a table or phone)
*   "**Ця...**" (for a feminine object, like a book or lamp)
*   "**Це...**" (for a neuter object, like a window or bed)

**Step 2: The Far Objects**
Now, walk to the wall and lean against it. Point your finger across the room to three completely different objects. They must be out of your physical reach. As you point, state what they are, using the correct "far" demonstratives.
Say aloud:
*   "**Той...**" (for a distant masculine object)
*   "**Та...**" (for a distant feminine object)
*   "**Те...**" (for a distant neuter object)

If you can smoothly transition between touching (near) and pointing (far) while maintaining perfect grammatical harmony with the nouns, you have successfully internalized the core objective of this lesson. You are no longer just naming things; you are actively organizing your world in Ukrainian.

---

# Підсумок

In this module, we have taken a major step forward in your ability to communicate naturally. We moved beyond simply identifying objects with the invariant **це** and learned how to specifically point to them using gender-matched demonstratives ("This table"). We discovered that near objects use the **цей/ця/це/ці** family, while far objects rely on the "T" mnemonic family: **той/та/те/ті**. We explored the rhythmic, poetic nature of Ukrainian vowel harmony, and we learned how deeply the concept of **дім** resonates within Ukrainian culture.

**Перевірте себе:**
1. What is the fundamental grammatical difference between using **це** in the sentence **«Це стіл»** versus using **цей** in the phrase **«Цей стіл»**?
2. Which specific consonant sound connects all the demonstrative pronouns used for objects that are far away from you?
3. How do you correctly say "this room" and "that room," and why do you use those specific endings?
4. Why is it grammatically incorrect to say **ця двері**, and what must you say instead?
5. Explain the emotional and conceptual difference between a **квартира** and a **дім** in modern Ukrainian life.

---
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/my-world-objects.yaml`

```yaml
- groups:
  - items:
    - стіл
    - стілець
    - диван
    - телефон
    - чайник
    - годинник
    - килим
    - рушник
    - холодильник
    name: Він (Masculine)
  - items:
    - шафа
    - книга
    - кімната
    - лампа
    - чашка
    - тарілка
    - полиця
    - подушка
    - ковдра
    - картина
    - ванна
    - ваза
    - плита
    name: Вона (Feminine)
  - items:
    - вікно
    - ліжко
    - крісло
    - блюдо
    - дзеркало
    - мило
    name: Воно (Neuter)
  instruction: Sort the words into the correct gender category (Він, Вона, Воно).
  title: 'Сортування: Чоловічий, Жіночий, Середній'
  type: group-sort
- instruction: Match the Ukrainian words with their English translations.
  pairs:
  - left: стіл
    right: table
  - left: стілець
    right: chair
  - left: крісло
    right: armchair
  - left: ліжко
    right: bed
  - left: шафа
    right: wardrobe
  - left: вікно
    right: window
  - left: кімната
    right: room
  - left: диван
    right: sofa
  - left: чайник
    right: kettle
  - left: чашка
    right: cup
  - left: тарілка
    right: plate
  - left: дзеркало
    right: mirror
  - left: килим
    right: carpet
  - left: подушка
    right: pillow
  - left: рушник
    right: towel
  - left: ваза
    right: vase
  - left: холодильник
    right: refrigerator
  - left: плита
    right: stove
  - left: мило
    right: soap
  - left: ванна
    right: bathtub
  title: 'Словниковий запас: Меблі та предмети'
  type: match-up
- instruction: Choose the correct form of 'This' (цей, ця, це) for each object.
  items:
  - explanation: Стіл is masculine (він), so we use Цей.
    options:
    - correct: true
      text: Цей
    - correct: false
      text: Ця
    - correct: false
      text: Це
    - correct: false
      text: Ці
    question: ___ стіл тут. Він дуже великий.
  - explanation: Книга is feminine (вона), so we use Ця.
    options:
    - correct: true
      text: Ця
    - correct: false
      text: Цей
    - correct: false
      text: Це
    - correct: false
      text: Ці
    question: ___ книга тут. Вона дуже цікава.
  - explanation: Вікно is neuter (воно), so we use Це.
    options:
    - correct: true
      text: Це
    - correct: false
      text: Цей
    - correct: false
      text: Ця
    - correct: false
      text: Ці
    question: ___ вікно тут. Воно дуже чисте.
  - explanation: Телефон is masculine (він), so we use Цей.
    options:
    - correct: true
      text: Цей
    - correct: false
      text: Ця
    - correct: false
      text: Це
    - correct: false
      text: Ці
    question: ___ телефон тут. Він дуже новий.
  - explanation: Шафа is feminine (вона), so we use Ця.
    options:
    - correct: true
      text: Ця
    - correct: false
      text: Цей
    - correct: false
      text: Це
    - correct: false
      text: Ці
    question: ___ шафа тут. Вона дуже стара.
  - explanation: Ліжко is neuter (воно), so we use Це.
    options:
    - correct: true
      text: Це
    - correct: false
      text: Цей
    - correct: false
      text: Ця
    - correct: false
      text: Ці
    question: ___ ліжко тут. Воно дуже зручне.
  - explanation: Стілець is masculine (він), so we use Цей.
    options:
    - correct: true
      text: Цей
    - correct: false
      text: Ця
    - correct: false
      text: Це
    - correct: false
      text: Ці
    question: ___ стілець тут. Він дуже гарний.
  - explanation: Лампа is feminine (вона), so we use Ця.
    options:
    - correct: true
      text: Ця
    - correct: false
      text: Цей
    - correct: false
      text: Це
    - correct: false
      text: Ці
    question: ___ лампа тут. Вона дуже красива.
  - explanation: Крісло is neuter (воно), so we use Це.
    options:
    - correct: true
      text: Це
    - correct: false
      text: Цей
    - correct: false
      text: Ця
    - correct: false
      text: Ці
    question: ___ крісло тут. Воно дуже старе.
  - explanation: Диван is masculine (він), so we use Цей.
    options:
    - correct: true
      text: Цей
    - correct: false
      text: Ця
    - correct: false
      text: Це
    - correct: false
      text: Ці
    question: ___ диван тут. Він дуже великий.
  title: 'Вибір займенника: Близько (Near)'
  type: quiz
- instruction: Choose the correct form of 'That' (той, та, те) for each object.
  items:
  - explanation: Стіл is masculine, so we use Той.
    options:
    - correct: true
      text: Той
    - correct: false
      text: Та
    - correct: false
      text: Те
    - correct: false
      text: Ті
    question: ___ стіл там. Він дуже великий.
  - explanation: Лампа is feminine, so we use Та.
    options:
    - correct: true
      text: Та
    - correct: false
      text: Той
    - correct: false
      text: Те
    - correct: false
      text: Ті
    question: ___ лампа там. Вона дуже красива.
  - explanation: Вікно is neuter, so we use Те.
    options:
    - correct: true
      text: Те
    - correct: false
      text: Той
    - correct: false
      text: Та
    - correct: false
      text: Ті
    question: ___ вікно там. Воно дуже чисте.
  - explanation: Диван is masculine, so we use Той.
    options:
    - correct: true
      text: Той
    - correct: false
      text: Та
    - correct: false
      text: Те
    - correct: false
      text: Ті
    question: ___ диван там. Він дуже великий.
  - explanation: Кімната is feminine, so we use Та.
    options:
    - correct: true
      text: Та
    - correct: false
      text: Той
    - correct: false
      text: Те
    - correct: false
      text: Ті
    question: ___ кімната там. Вона дуже велика.
  - explanation: Крісло is neuter, so we use Те.
    options:
    - correct: true
      text: Те
    - correct: false
      text: Той
    - correct: false
      text: Та
    - correct: false
      text: Ті
    question: ___ крісло там. Воно дуже старе.
  - explanation: Телефон is masculine, so we use Той.
    options:
    - correct: true
      text: Той
    - correct: false
      text: Та
    - correct: false
      text: Те
    - correct: false
      text: Ті
    question: ___ телефон там. Він дуже новий.
  - explanation: Ліжко is neuter, so we use Те.
    options:
    - correct: true
      text: Те
    - correct: false
      text: Той
    - correct: false
      text: Та
    - correct: false
      text: Ті
    question: ___ ліжко там. Воно дуже зручне.
  - explanation: Шафа is feminine, so we use Та.
    options:
    - correct: true
      text: Та
    - correct: false
      text: Той
    - correct: false
      text: Те
    - correct: false
      text: Ті
    question: ___ шафа там. Вона дуже стара.
  - explanation: Двері is plural, so we use Ті.
    options:
    - correct: true
      text: Ті
    - correct: false
      text: Той
    - correct: false
      text: Та
    - correct: false
      text: Те
    question: ___ двері там. Вони дуже великі.
  title: 'Вибір займенника: Далеко (Far)'
  type: quiz
- instruction: Fill in the blank with the correct demonstrative pronoun (Цей, Ця,
    Це, Той, Та, Те).
  items:
  - answer: Цей
    explanation: Стіл is masculine and near.
    options:
    - Цей
    - Ця
    - Це
    - Той
    sentence: ___ (This) стіл великий.
  - answer: Те
    explanation: Вікно is neuter and far.
    options:
    - Те
    - Той
    - Та
    - Це
    sentence: ___ (That) вікно чисте.
  - answer: Ця
    explanation: Лампа is feminine and near.
    options:
    - Ця
    - Цей
    - Це
    - Та
    sentence: ___ (This) лампа нова.
  - answer: Та
    explanation: Книга is feminine and far.
    options:
    - Та
    - Той
    - Те
    - Ця
    sentence: ___ (That) книга стара.
  - answer: Це
    explanation: Ліжко is neuter and near.
    options:
    - Це
    - Те
    - Ця
    - Цей
    sentence: ___ (This) ліжко зручне.
  - answer: Той
    explanation: Телефон is masculine and far.
    options:
    - Той
    - Та
    - Те
    - Цей
    sentence: ___ (That) телефон мій.
  - answer: Та
    explanation: Шафа is feminine and far.
    options:
    - Та
    - Той
    - Те
    - Ця
    sentence: ___ (That) шафа велика.
  - answer: Цей
    explanation: Стілець is masculine and near.
    options:
    - Цей
    - Ця
    - Це
    - Той
    sentence: ___ (This) стілець зручний.
  - answer: Те
    explanation: Крісло is neuter and far.
    options:
    - Те
    - Той
    - Та
    - Це
    sentence: ___ (That) крісло старе.
  - answer: Цей
    explanation: Диван is masculine and near.
    options:
    - Цей
    - Ця
    - Це
    - Той
    sentence: ___ (This) диван новий.
  title: Вставте пропущене слово
  type: fill-in
- instruction: Rearrange the letters to find the furniture word.
  items:
  - answer: стіл
    scrambled: л і с т
  - answer: шафа
    scrambled: ф а ш а
  - answer: вікно
    scrambled: к н о в і
  - answer: книга
    scrambled: г и к н а
  - answer: лампа
    scrambled: п а л м а
  - answer: диван
    scrambled: в а н д и
  - answer: стілець
    scrambled: ц і л е с т ь
  - answer: телефон
    scrambled: ф е н о л е т
  - answer: крісло
    scrambled: с л о к р і
  - answer: ліжко
    scrambled: к о ж л і
  - answer: рушник
    scrambled: н и к ш р у
  - answer: ваза
    scrambled: з а в а
  - answer: мило
    scrambled: л о м и
  title: Розшифруйте слова
  type: anagram
- groups:
  - items:
    - цей стіл
    - ця книга
    - це вікно
    - ці двері
    - цей телефон
    - ця лампа
    name: Близько (Near)
  - items:
    - той стіл
    - та книга
    - те вікно
    - ті двері
    - той телефон
    - та лампа
    name: Далеко (Far)
  instruction: Sort the phrases into 'Near' (This) or 'Far' (That).
  title: 'Сортування: Близько чи Далеко?'
  type: group-sort
- instruction: Match the Ukrainian phrases with their English meanings.
  pairs:
  - left: Цей стілець
    right: This chair
  - left: Той стілець
    right: That chair
  - left: Ця лампа
    right: This lamp
  - left: Та лампа
    right: That lamp
  - left: Це вікно
    right: This window
  - left: Те вікно
    right: That window
  - left: Цей диван
    right: This sofa
  - left: Той диван
    right: That sofa
  - left: Ця кімната
    right: This room
  - left: Та кімната
    right: That room
  - left: Це ліжко
    right: This bed
  - left: Те ліжко
    right: That bed
  title: Переклад фраз
  type: match-up
- instruction: Choose the correct form of 'This' based on the context (Is it 'This
    is a...' or 'This specific...').
  items:
  - answer: Це
    explanation: 'Identification: ''This is a table'' always uses Це.'
    options:
    - Це
    - Цей
    - Ця
    - Той
    sentence: ___ (This is) стіл.
  - answer: Цей
    explanation: 'Specification: ''This table'' requires agreement (masculine).'
    options:
    - Цей
    - Це
    - Ця
    - Той
    sentence: ___ (This) стіл новий.
  - answer: Це
    explanation: 'Identification: ''This is a book'' always uses Це.'
    options:
    - Це
    - Ця
    - Цей
    - Та
    sentence: ___ (This is) книга.
  - answer: Ця
    explanation: 'Specification: ''This book'' requires agreement (feminine).'
    options:
    - Ця
    - Це
    - Цей
    - Та
    sentence: ___ (This) книга цікава.
  - answer: Це
    explanation: 'Identification: ''This is a window'' uses Це.'
    options:
    - Це
    - Цей
    - Ця
    - Те
    sentence: ___ (This is) вікно.
  - answer: Це
    explanation: 'Specification: ''This window'' (neuter) also uses Це.'
    options:
    - Це
    - Цей
    - Ця
    - Те
    sentence: ___ (This) вікно велике.
  - answer: Це
    explanation: 'Identification: ''This is a phone'' uses Це.'
    options:
    - Це
    - Цей
    - Ця
    - Той
    sentence: ___ (This is) телефон.
  - answer: Цей
    explanation: 'Specification: ''This phone'' (masculine) uses Цей.'
    options:
    - Цей
    - Це
    - Ця
    - Той
    sentence: ___ (This) телефон старий.
  - answer: Це
    explanation: 'Identification: ''This is a wardrobe'' uses Це.'
    options:
    - Це
    - Ця
    - Цей
    - Та
    sentence: ___ (This is) шафа.
  - answer: Ця
    explanation: 'Specification: ''This wardrobe'' (feminine) uses Ця.'
    options:
    - Ця
    - Це
    - Цей
    - Та
    sentence: ___ (This) шафа нова.
  title: Ідентифікація чи Специфікація?
  type: fill-in
- instruction: Complete each mini-dialogue by filling in the correct demonstrative
    pronoun.
  items:
  - answer: Цей
    explanation: Телефон is masculine and near the speaker.
    options:
    - Цей
    - Ця
    - Той
    - Та
    sentence: 'Де мій телефон? — ___ телефон?'
  - answer: Той
    explanation: Стіл is masculine and far from the speaker (там).
    options:
    - Той
    - Цей
    - Та
    - Те
    sentence: 'Який стіл? — ___ стіл, там.'
  - answer: Ця
    explanation: Книга is feminine and near the speaker (тут).
    options:
    - Ця
    - Цей
    - Та
    - Це
    sentence: 'Де моя книга? — ___ книга тут.'
  - answer: Ті
    explanation: Двері is always plural. The speaker points far (там).
    options:
    - Ті
    - Ці
    - Та
    - Той
    sentence: 'Які двері? — ___ двері, там.'
  - answer: Це
    explanation: Вікно is neuter and near the speaker (тут).
    options:
    - Це
    - Цей
    - Ця
    - Те
    sentence: 'Яке вікно? — ___ вікно тут.'
  - answer: Та
    explanation: Шафа is feminine and far from the speaker (там).
    options:
    - Та
    - Ця
    - Той
    - Те
    sentence: 'Яка шафа? — ___ шафа, там.'
  title: 'Діалоги: вставте займенник'
  type: fill-in

```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/my-world-objects.yaml`

```yaml
- lemma: цей
  notes: Used for masculine nouns near the speaker
  pos: pronoun
  translation: this (masc.)
- lemma: ця
  notes: Used for feminine nouns near the speaker
  pos: pronoun
  translation: this (fem.)
- lemma: це
  notes: Used for neuter nouns near speaker OR general identification (This is...)
  pos: pronoun
  translation: this (neut.) / this is
- lemma: ці
  notes: Plural form for near objects
  pos: pronoun
  translation: these
- lemma: той
  notes: Used for masculine nouns far from the speaker
  pos: pronoun
  translation: that (masc.)
- lemma: та
  notes: Used for feminine nouns far from the speaker
  pos: pronoun
  translation: that (fem.)
- lemma: те
  notes: Used for neuter nouns far from the speaker
  pos: pronoun
  translation: that (neut.)
- lemma: ті
  notes: Plural form for far objects
  pos: pronoun
  translation: those
- lemma: стіл
  notes: Masculine
  pos: noun
  translation: table
- lemma: стілець
  notes: Masculine
  pos: noun
  translation: chair
- lemma: диван
  notes: Masculine
  pos: noun
  translation: sofa
- lemma: телефон
  notes: Masculine
  pos: noun
  translation: phone
- lemma: шафа
  notes: Feminine
  pos: noun
  translation: wardrobe
- lemma: книга
  notes: Feminine
  pos: noun
  translation: book
- lemma: кімната
  notes: Feminine
  pos: noun
  translation: room
- lemma: лампа
  notes: Feminine
  pos: noun
  translation: lamp
- lemma: вікно
  notes: Neuter
  pos: noun
  translation: window
- lemma: ліжко
  notes: Neuter
  pos: noun
  translation: bed
- lemma: крісло
  notes: Neuter
  pos: noun
  translation: armchair
- lemma: двері
  notes: Always plural in Ukrainian
  pos: noun
  translation: door / doors
- lemma: ніж
  notes: Masculine
  pos: noun
  translation: knife
- lemma: ложка
  notes: Feminine
  pos: noun
  translation: spoon
- lemma: блюдо
  notes: Neuter
  pos: noun
  translation: dish
- lemma: чайник
  notes: Masculine
  pos: noun
  translation: kettle
- lemma: чашка
  notes: Feminine
  pos: noun
  translation: cup
- lemma: тарілка
  notes: Feminine
  pos: noun
  translation: plate
- lemma: годинник
  notes: Masculine
  pos: noun
  translation: clock
- lemma: полиця
  notes: Feminine
  pos: noun
  translation: shelf
- lemma: картина
  notes: Feminine
  pos: noun
  translation: picture / painting
- lemma: дзеркало
  notes: Neuter
  pos: noun
  translation: mirror
- lemma: килим
  notes: Masculine
  pos: noun
  translation: carpet / rug
- lemma: подушка
  notes: Feminine
  pos: noun
  translation: pillow
- lemma: ковдра
  notes: Feminine
  pos: noun
  translation: blanket
- lemma: мило
  notes: Neuter
  pos: noun
  translation: soap
- lemma: рушник
  notes: Masculine
  pos: noun
  translation: towel
- lemma: ванна
  notes: Feminine
  pos: noun
  translation: bathtub
- lemma: ваза
  notes: Feminine
  pos: noun
  translation: vase
- lemma: холодильник
  notes: Masculine
  pos: noun
  translation: refrigerator
- lemma: плита
  notes: Feminine
  pos: noun
  translation: stove


```

---

## Instructions

1. For each issue in the Fix Plan or audit failures, find the exact text in the file contents above
2. Produce a FIND/REPLACE pair with verbatim FIND text copied exactly from above
3. Only fix issues documented above — no silent extra changes
4. Prioritize: audit gate failures first, then review issues

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===SECTION_FIX_START===
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-world-objects.md
---
FIND:
exact text to replace (full sentence or paragraph, verbatim from the file contents above)
REPLACE:
corrected replacement text
---
FIND:
next problematic text
REPLACE:
corrected replacement
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/my-world-objects.yaml
---
FIND:
exact activity text to replace
REPLACE:
corrected activity text
---
===SECTION_FIX_END===
```

## Fix Rules

- **FIND text must be verbatim** — copy from the file contents above exactly
- Only fix issues documented in the Fix Plan or audit failures above
- You MAY add new activities or modify existing ones if the Fix Plan explicitly requests it
- To ADD a new YAML item, FIND the last existing item in the list, REPLACE it with that same item followed by your new item. Preserve exact YAML indentation.
- Do NOT add new prose sections or vocabulary items unless the Fix Plan explicitly requests it
- Maximum **20 FIND/REPLACE pairs** total (prioritize the most impactful fixes)
- Each FILE: line starts a new sub-block for that file
- If nothing needs fixing, output:
  ```
  ===SECTION_FIX_START===
  ===SECTION_FIX_END===
  ```

---

## Friction Report (MANDATORY)

After the fix block, include:

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: {what you were doing when friction occurred, or "Full Phase D.2"}
**Friction Type**: NONE | FIND_TEXT_MISMATCH | FILE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done in Phase D.1
- Do NOT output ===REVIEW_START=== blocks
- Do NOT modify files directly — only output fix blocks
- You MAY add/modify activities if the Fix Plan requests it (use FIND/REPLACE on the YAML file)
- Do NOT make cosmetic changes beyond what the review flagged
