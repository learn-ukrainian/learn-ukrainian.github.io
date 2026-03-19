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

- **[HIGH] VOCAB_NOT_IN_CONTENT** in `vocabulary`
  - Expected: Required word 'займатися' must appear in content
  - Actual: Word not found (after stress-mark normalization)
  - Fix: Add 'займатися' to an appropriate section in the content

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥25 items
  - Actual: Activity has 15 items
  - Fix: Add 10 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥25 items
  - Actual: Activity has 6 items
  - Fix: Add 19 more items to 'fill-in' activity

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
- Only modify these sections: Activities YAML, Activity 2, items at lines 154-169, Entire module, Entire module — Section "Практика та застосування (Practice and Application)" is the most natural fit, Line 76, Section "Презентація: Форми та відмінювання (Presentation: Forms and Conjugation)", Lines 147, 153 in Section "Практика та застосування (Practice and Application)", Section "Презентація: Форми та відмінювання (Presentation: Forms and Conjugation)", subsection "Morphological Note" (lines 59-68)

### Finding 1: Activity Design Flaw — Broken Suffix Fill-In Items (HIGH)
**Location**: Activities YAML, Activity 2, items at lines 154-169
**Problem**: Activity 2 is titled "Choose the Correct Suffix: -ся or -сь" but three items don't work with this paradigm:
**Required Fix**: Remove these 3 items entirely and replace with stems that cleanly take -ся or -сь (e.g., "Ми сміємо___." → "сь", "Ти одягаєш___." → "ся", "Вони займають___." → "ся").
**Severity**: HIGH

### Finding 2: Colonial Framing in [!tip] Box (HIGH)
**Location**: Line 76, Section "Презентація: Форми та відмінювання (Presentation: Forms and Conjugation)"
**Problem**: This defines Ukrainian pronunciation through contrast with Russian. The block is a [!tip], not a [!myth-buster] or [!decolonization] block. Per review protocol, this is colonial framing — Ukrainian features must be presented on their own terms.
**Required Fix**: Remove the Russian comparison entirely. Present the [ц'а] pronunciation as an intrinsic feature of Ukrainian: "This long, soft sound is a hallmark of authentic Ukrainian pronunciation. Practice making it soft and drawn out — it's one of the beautiful sounds that defines the melody of Ukrainian."
**Severity**: HIGH

### Finding 3: Missing Plan Point — Past Tense Forms (MEDIUM)
**Location**: Section "Презентація: Форми та відмінювання (Presentation: Forms and Conjugation)", subsection "Morphological Note" (lines 59-68)
**Problem**: Plan explicitly requires: "Mention past tense forms per Standard examples (сміявся, сміялася, сміялося, сміялися) to show the suffix persists across tenses." The content only shows present tense forms of сміятися. This is a direct plan violation.
**Required Fix**: Add a brief note after line 67 showing past tense forms in a small table or list: сміявся, сміялася, сміялося, сміялися — with a note that past tense will be taught at M36, this is just pattern recognition.
**Severity**: HIGH

### Finding 4: Incomplete Transitive Sentences (MEDIUM)
**Location**: Lines 147, 153 in Section "Практика та застосування (Practice and Application)"
**Problem**: Transitive verbs мити and одягати require objects in Ukrainian. "Я мию." and "Мама одягає." sound truncated and unnatural. The plan itself says "мити тарілку" — the object was in the plan but dropped in content.
**Required Fix**: Change to "**Я мию тарілку.** (I wash a plate.)" and "**Мама одягає дитину.** (Mom dresses the child.)" — consistent with the plan's "мити тарілку" phrasing.
**Severity**: HIGH

### Finding 5: No Yoga Instructor Persona Integration (MEDIUM)
**Location**: Entire module — Section "Практика та застосування (Practice and Application)" is the most natural fit
**Problem**: Plan specifies `persona: { voice: Patient Supportive Tutor, role: Yoga Instructor }`. Research notes explicitly suggest "A yoga class also works well — займатися йогою, розминатися (warm up), розслаблятися (relax)." Zero yoga references appear in the module. The persona is completely absent.
**Required Fix**: Add a yoga-themed example cluster in Section "Практика та застосування (Practice and Application)", e.g., a short dialogue at a yoga class using займатися йогою, розминатися, розслаблятися.
**Severity**: HIGH

### Finding 6: Low Immersion & Missing Engagement Elements (LOW-MEDIUM)
**Location**: Entire module
**Problem**: Immersion at 12.3% is below the 15-25% audit target and well below the 25-45% band for A1 modules 11-20. Only 1 engagement box ([!tip] at line 70) vs. 2 required. Zero video embeds vs. 2 richness target. Research notes found a relevant YouTube video (ULP Ep 109) that is not embedded.
**Required Fix**: Add at least 1 more engagement callout (e.g., a [!did-you-know] about Ukrainian morning routines using the proverb from research notes: "Хто рано встає, тому Бог дає"). Embed the ULP video. Both will also boost immersion.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Activity Design Flaw — Broken Suffix Fill-In Items (HIGH)
- **Location**: Activities YAML, Activity 2, items at lines 154-169
- **Original (line 154)**: `"Він сміє___."` with answer `"ся"` and (line 162): `"Ти сміє___."` with answer `"шся"` and (line 166): `"Вона вмиває___."` with answer `"ся"`
- **Problem**: Activity 2 is titled "Choose the Correct Suffix: -ся or -сь" but three items don't work with this paradigm:
  - "Він сміє" + "ся" = "смієся" — NOT a valid form. Correct is "сміється" (with -ть-).
  - "Вона вмиває" + "ся" = "вмиваєся" — NOT a valid form. Correct is "вмивається" (with -ть-).
  - "Ти сміє" + "шся" = "смієшся" — orthographically works, but "шся" is NOT a suffix choice between -ся/-сь. The "ш" is a conjugation ending, not part of the reflexive suffix. This answer is categorically wrong for an activity about suffix selection.
- **Fix**: Remove these 3 items entirely and replace with stems that cleanly take -ся or -сь (e.g., "Ми сміємо___." → "сь", "Ти одягаєш___." → "ся", "Вони займають___." → "ся").

### Issue 2: Colonial Framing in [!tip] Box (HIGH)
- **Location**: Line 76, Section "Презентація: Форми та відмінювання (Presentation: Forms and Conjugation)"
- **Original**: 「In Russian, a similar spelling is pronounced as a hard, short sound. By mastering this long, soft sound, you are embracing the true melody of Ukrainian and distinguishing your pronunciation.」
- **Problem**: This defines Ukrainian pronunciation through contrast with Russian. The block is a [!tip], not a [!myth-buster] or [!decolonization] block. Per review protocol, this is colonial framing — Ukrainian features must be presented on their own terms.
- **Fix**: Remove the Russian comparison entirely. Present the [ц'а] pronunciation as an intrinsic feature of Ukrainian: "This long, soft sound is a hallmark of authentic Ukrainian pronunciation. Practice making it soft and drawn out — it's one of the beautiful sounds that defines the melody of Ukrainian."

### Issue 3: Missing Plan Point — Past Tense Forms (MEDIUM)
- **Location**: Section "Презентація: Форми та відмінювання (Presentation: Forms and Conjugation)", subsection "Morphological Note" (lines 59-68)
- **Problem**: Plan explicitly requires: "Mention past tense forms per Standard examples (сміявся, сміялася, сміялося, сміялися) to show the suffix persists across tenses." The content only shows present tense forms of сміятися. This is a direct plan violation.
- **Fix**: Add a brief note after line 67 showing past tense forms in a small table or list: сміявся, сміялася, сміялося, сміялися — with a note that past tense will be taught at M36, this is just pattern recognition.

### Issue 4: Incomplete Transitive Sentences (MEDIUM)
- **Location**: Lines 147, 153 in Section "Практика та застосування (Practice and Application)"
- **Original**: 「**Я мию.** (I wash something.)」 and 「**Мама одягає.** (Mom dresses someone.)」
- **Problem**: Transitive verbs мити and одягати require objects in Ukrainian. "Я мию." and "Мама одягає." sound truncated and unnatural. The plan itself says "мити тарілку" — the object was in the plan but dropped in content.
- **Fix**: Change to "**Я мию тарілку.** (I wash a plate.)" and "**Мама одягає дитину.** (Mom dresses the child.)" — consistent with the plan's "мити тарілку" phrasing.

### Issue 5: No Yoga Instructor Persona Integration (MEDIUM)
- **Location**: Entire module — Section "Практика та застосування (Practice and Application)" is the most natural fit
- **Problem**: Plan specifies `persona: { voice: Patient Supportive Tutor, role: Yoga Instructor }`. Research notes explicitly suggest "A yoga class also works well — займатися йогою, розминатися (warm up), розслаблятися (relax)." Zero yoga references appear in the module. The persona is completely absent.
- **Fix**: Add a yoga-themed example cluster in Section "Практика та застосування (Practice and Application)", e.g., a short dialogue at a yoga class using займатися йогою, розминатися, розслаблятися.

### Issue 6: Low Immersion & Missing Engagement Elements (LOW-MEDIUM)
- **Location**: Entire module
- **Problem**: Immersion at 12.3% is below the 15-25% audit target and well below the 25-45% band for A1 modules 11-20. Only 1 engagement box ([!tip] at line 70) vs. 2 required. Zero video embeds vs. 2 richness target. Research notes found a relevant YouTube video (ULP Ep 109) that is not embedded.
- **Fix**: Add at least 1 more engagement callout (e.g., a [!did-you-know] about Ukrainian morning routines using the proverb from research notes: "Хто рано встає, тому Бог дає"). Embed the ULP video. Both will also boost immersion.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 147 | 「**Я мию.** (I wash something.)」 | 「**Я мию тарілку.** (I wash a plate.)」 | Grammar — missing object |
| 153 | 「**Мама одягає.** (Mom dresses someone.)」 | 「**Мама одягає дитину.** (Mom dresses the child.)」 | Grammar — missing object |
| 174 | 「**Вона вчиться грати.** (She studies playing.)」 | 「**Вона вчиться грати на гітарі.** (She is learning to play guitar.)」 | Naturalness — incomplete thought |
| Act.154 | "Він сміє___." answer: "ся" | Remove item — "смієся" is invalid | Activity error |
| Act.162 | "Ти сміє___." answer: "шся" | Replace with "Ти одягаєш___." answer: "ся" | Activity error |
| Act.166 | "Вона вмиває___." answer: "ся" | Replace with "Вони займають___." answer: "ся" | Activity error |

---

## Fix Plan to Reach 9.0/10

### Language: 7/10 → 9/10
**What to fix:**
1. Line 76: Remove Russian comparison from [!tip] box — present [ц'а] as intrinsic Ukrainian feature
2. Line 147: Change 「**Я мию.**」 → 「**Я мию тарілку.**」
3. Line 153: Change 「**Мама одягає.**」 → 「**Мама одягає дитину.**」

**Expected score after fix:** 9/10

### Activities: 6/10 → 9/10
**What to fix:**
1. Remove/replace 3 broken items in Activity 2 (lines 154, 162-165, 166-169 in YAML): replace with stems that cleanly take -ся or -сь
2. Remove "шся" as an answer option entirely — it's not a suffix

**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Fix Activity 2 broken items (same as above)
2. Line 147, 153: Add objects to transitive sentences
3. Line 174: Expand 「**Вона вчиться грати.**」 to include instrument

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add past tense forms (сміявся, сміялася, сміялося, сміялися) to Section "Презентація: Форми та відмінювання (Presentation: Forms and Conjugation)" subsection "Morphological Note"
2. Replace "bound morpheme" with simpler phrasing in Section "Вступ: Дзеркало дії (Introduction: Mirroring Action)"
3. Integrate yoga instructor persona into Section "Практика та застосування (Practice and Application)"

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add 1+ engagement callout (e.g., [!did-you-know] with morning routine proverb from research)
2. Embed ULP Ep 109 video
3. Add 1-2 encouragement beats in middle sections

**Expected score after fix:** 9/10

### Projected Overall After Fixes
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9 = (13.5 + 9.9 + 10.8 + 11.7 + 10.4 + 8.0 + 13.5) / 8.9 = 77.8 / 8.9 = **8.7/10**

---

## Audit Failures (from automated re-audit)

```
> Conjugate Reflexive Verbs: 25 items (min 6)
--- STRICT GATES (Level A1) ---
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
⚠️  [PHANTOM_SECTION_REFERENCE] Review references 2 section(s) not found in content: 'Morphological Note', 'Morphological Note'. Verify section names match actual content headers.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/reflexive-verbs-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `сь` (source: prose)
  ❌ `ться` (source: prose)
  ❌ `Хрещатик` (source: prose)
  ❌ `ш` (source: prose)
  ❌ `ю` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/reflexive-verbs.md`

```markdown
## Вступ: Дзеркало дії (Introduction: Mirroring Action)

Welcome back! You have already mastered the basics of how Ukrainian verbs live and breathe. You know how to talk about actions you do, like reading (**читати**) or writing (**писати**). But what happens when the action you are doing is directed right back at you? What if *you* are both the one doing the action and the one receiving it?

Imagine looking into a mirror. When you wash a plate, the action goes from you to the plate. But when you wash your face, the action reflects back onto you. In Ukrainian, we use a special «mirror» attached to the end of the verb to show this reflection. This mirror is the suffix **-ся** (or **-сь**). 

We call these *reflexive verbs*. They are incredibly common in Ukrainian because they describe our daily routines, our interactions, and our feelings. 

Let’s take a look at where this little mirror comes from. The suffix **-ся** is actually a shortened, glued-on version of the word for "self". Historically, it was a separate word. Over time, it merged with the verb to become a permanent part of it—a small piece that cannot stand alone but carries important meaning. It signals that the action stays with the agent.

### The «Apology» Logic

Understanding this «self» meaning helps explain a very important cultural and linguistic rule in Ukrainian regarding saying you are sorry. You might hear some people say **«Вибачаюсь»** when they bump into someone. But let's look at the mirror! Since **-ся** means «myself», saying **«Вибачаюсь»** literally means «I excuse myself» or «I forgive myself». That implies self-forgiveness, which is not very polite!

The correct, standard Ukrainian way to apologize is to ask the *other* person for forgiveness using the imperative form: **«Вибачте»** (Excuse me / Forgive me). You are asking them to excuse you, rather than excusing yourself.

### A Common Learner Error: The «Myself» Redundancy

Because English uses pronouns like «myself» or «yourself», a very common mistake for English speakers is to try and translate this directly. 

For example, a learner might say:
* **Я мию** + the word for "myself". (I wash myself.)

While a Ukrainian speaker would understand you, it sounds unnatural and redundant, like saying «I wash myself myself». Instead, you simply use the reflexive verb. The «myself» is already built-in!
* **Я миюся.** (I wash myself.)

By mastering this suffix, you will instantly sound much more natural and fluent. Let's learn how to use it!
<!-- adapted from: Ukrainian Lessons Podcast, Ep 109 -->

## Презентація: Форми та відмінювання (Presentation: Forms and Conjugation)

Now that you know what the mirror does, let's learn how to attach it to your verbs. The reflexive suffix has two forms: **-ся** and **-сь**. Choosing which one to use is entirely based on euphony—the beautiful, flowing sound of the Ukrainian language.

### The Phonetic Rule: Consonants vs. Vowels

The rule is simple and depends on the sound that comes immediately *before* the suffix:
* Use **-ся** after consonants.
  * **Він миється** — He washes himself. (Ends in a consonant 'т', so we add **-ся**).
* Use **-сь** after vowels.
  * **Я миюсь** — I wash myself. (Ends in a vowel 'ю', so we add **-сь**).

*Note: In modern spoken Ukrainian, you will often hear people use **-ся** after vowels as well (e.g., **я миюся**). Both are absolutely correct and accepted in the literary standard, but using **-сь** after vowels makes your speech flow a bit faster and is very common. For our practice, we will show you both, but pay attention to the vowel/consonant rhythm!*

### Conjugating in the Present Tense

Let's look at how this works in practice with a high-frequency verb you will use every day: **дивитися** (to watch, to look). This aligns perfectly with the Ukrainian State Standard §4.2.4.1 for present tense conjugation patterns.

Notice that we first conjugate the verb normally (like a standard Second Conjugation verb), and then we attach our mirror (**-ся** or **-сь**) to the very end.

* **Я дивлюся** / **дивлюсь** (I watch/look)
* **Ти дивишся** (You watch/look - singular)
* **Він / вона / воно дивиться** (He/she/it watches/looks)
* **Ми дивимося** / **дивимось** (We watch/look)
* **Ви дивитеся** / **дивитесь** (You watch/look - plural/formal)
* **Вони дивляться** (They watch/look)

See how the suffix just tags along? It doesn't change the base conjugation of the verb; it just attaches to the end of whatever form you need.

### Morphological Note: The Mirror Persists

To show you that this suffix persists across all forms, let's take a quick peek at the conjugation of the verb **сміятися** (to laugh), exactly as shown in standard textbook examples:

* **Ти смієшся** — You laugh (consonant 'ш' + ся)
* **Вона сміється** — She laughs (soft sound + ся)
* **Ми сміємося** — We laugh (vowel 'о' + ся, or сміємось)
* **Вони сміються** — They laugh (soft sound + ся)

The suffix is loyal; it stays with the verb in every form!

And this pattern extends to the past tense as well! You will learn the past tense later (at M36), but take a quick look at how the mirror stays put:

* **сміявся** — he laughed (masculine)
* **сміялася** — she laughed (feminine)
* **сміялося** — it laughed (neuter)
* **сміялися** — they laughed (plural)

See? The suffix persists in every form, present or past!

> [!tip] Shibboleth Pronunciation: The Secret of soft "tsya"
> 
> Here is a crucial pronunciation secret that will instantly make you sound like a native Ukrainian speaker. Pay close attention to the **-ться** ending in the «він/вона/воно» and «вони» forms (like **дивиться** and **дивляться**).
> 
> When you see the letters **-ться**, you do NOT pronounce them as «t-s-ya». Instead, they merge into a single, long, soft sound: a long, soft «tsya». 
> 
> This specific pronunciation is a critical phonetic marker of Ukrainian identity. This long, soft sound is a hallmark of authentic Ukrainian speech — it's one of the beautiful sounds that defines the melody of the language. By mastering it, you are embracing the true sound of Ukrainian.
> 
> * **Він дивиться** is pronounced with a long, soft tsya at the end.
> * **Вони дивляться** is pronounced with a long, soft tsya at the end.
> 
> Take a moment to practice this out loud. It should feel soft and drawn out!
<!-- adapted from: Grade 10, Сторінка 176 -->

## Семантичні групи (Semantic Groups)

Reflexive verbs in Ukrainian aren't just for washing yourself. The **-ся** suffix is quite versatile and creates several distinct «flavors» of meaning. Let's break them down into three main semantic groups.

### Type 1: True Reflexive (Actions on Oneself)

This is the classic mirror group. The subject performs an action directly upon themselves. These verbs are essential for describing your daily routine.

* **вмиватися** (to wash one's face/oneself)
  * **вмиватися швидко** (to wash oneself quickly)
  * **вмиватися вранці** (to wash oneself in the morning)
* **одягатися** (to dress oneself)
  * **одягатися тепло** (to dress warmly)
  * **швидко одягатися** (to dress quickly)
  * **одягатися стильно** (to dress stylishly)
* **голитися** (to shave oneself)

Notice that in English, you often drop the «oneself» (e.g., «I am dressing»). In Ukrainian, the **-ся** is mandatory!

### Type 2: Reciprocal (Actions Between Two or More People)

Sometimes the mirror reflects between two people. In this group, the **-ся** suffix means «each other» or «one another». It implies a mutual action.

* **знайомитися** (to get acquainted with each other)
* **зустрічатися** (to meet each other / to date)
* **вітатися** (to greet each other)
* **цілуватися** (to kiss each other)

When you use these verbs, it's understood that it's a two-way street. You aren't just greeting a wall; you and the other person are greeting each other.

### Type 3: Lexicalized (Always Reflexive)

Some verbs have worn their mirror for so long that they cannot exist without it. They are always reflexive, even if the action doesn't logically seem to reflect back on the subject.

* **сміятися** (to laugh)
* **подобатися** (to like / to be pleasing)
* **цікавитися** (to be interested in)

**A Note on "Laughing at":**
If you want to say you are laughing *at* something, Ukrainian uses specific prepositions with the verb **сміятися**. You will learn the case rules for these later:
* **сміятися** + preposition **з** (laughing at/about someone/something) – This is the most standard, neutral way to express finding something funny.
* **сміятися** + preposition **над** (laughing at someone/something) – This often carries a nuance of mocking, ridiculing, or laughing from a position of superiority.

### Agent Confusion: «To Name» vs. «To Be Called»

A very common point of confusion for learners is the difference between identifying something and being identified. We must explicitly contrast these two forms:

* **називати** (to name something/someone) – You are giving a name to an object or a person. 
* **називатися** (to be called / to identify as) – This is the reflexive form, used to state what something's name is.

This is a high-frequency verb for identification. When you want to know the name of an object or a street, you use the reflexive form!
* **Як це називається?** (What is this called?)
* **Вулиця називається Хрещатик.** (The street is called Khreshchatyk.)

## Практика та застосування (Practice and Application)

Now that you understand the theory, let's put these verbs to work. The best way to master the **-ся** suffix is to actively contrast it with its non-reflexive counterparts and then use it in context.

### Transitive vs. Reflexive Contrast

Let's drill the difference between an action directed outward (transitive) and an action directed inward (reflexive). Seeing them side-by-side solidifies the mirror concept.

* **мити** (to wash something) vs. **митися** (to wash oneself)
  * **Я мию тарілку.** (I wash a plate.)
  * **Я миюся.** (I wash myself.)
* **зупиняти** (to stop something/someone) vs. **зупинятися** (to stop oneself / to come to a halt)
  * **Він зупиняє автобус.** (He stops the bus.)
  * **Він зупиняється.** (He stops.)
* **одягати** (to dress someone, like a child) vs. **одягатися** (to dress oneself)
  * **Мама одягає дитину.** (Mom dresses the child.)
  * **Дитина одягається.** (The child dresses themselves.)

### Daily Routine Integration

Reflexive verbs are the backbone of talking about your day. Let's look at how they integrate into sentences you will use all the time, preparing you for when we discuss daily routines more deeply.

* **Я вмиваюся вранці.** (I wash my face in the morning.)
* **Вони вчаться.** (They study.)
* **Ми повертаємося додому пізно.** (We return home late.)
* **Ти займаєшся?** (Are you exercising?)

Notice how verbs like **вчитися** (to study/learn) and **повертатися** (to return) naturally take the reflexive suffix when describing your own ongoing actions or routines.

### Conjugation Drills: High-Frequency Verbs

Let's focus on two incredibly common verbs to ensure you have automaticity in the present tense. Read these aloud, paying attention to the suffix!

**вчитися** (to study):
* **Я вчуся добре.** (I study well.)
* **Де ти вчишся?** (Where do you study?)
* **Вона вчиться грати.** (She studies playing.)
* **Ми вчимося.** (We study.)
* **Ви вчитеся.** (You study.)
* **Вони вчаться.** (They study.)

**дивитися** (to watch/look):
* **Я дивлюся телевізор.** (I watch TV.)
* **Чому ти дивишся?** (Why are you looking?)
* **Він дивиться у вікно.** (He looks into the window.)
* **Ми дивимося кіно.** (We are watching a movie.)

### Social Interaction Dialogues

Finally, let's look at how reciprocal reflexive verbs work in short social interactions. Building confidence with these will help you make friends!

**Dialogue 1: Getting Acquainted**
* **— Привіт! Час знайомитися. Я — Максим.** (Hi! Time to get acquainted. I am Maksym.)
* **— Привіт! Дуже приємно.** (Hi! Very nice to meet you.)

**Dialogue 2: Greeting**
* **— Чому вони не вітаються?** (Why aren't they greeting each other?)
* **— Вони не знають один одного.** (They don't know each other.)

Practice using these verbs every day, and soon the mirror of Ukrainian verbs will feel perfectly natural to you!

# Підсумок
You’ve taken a huge step forward in your Ukrainian journey! You now understand that the **-ся** (or **-сь**) suffix acts like a mirror, reflecting an action back onto the subject, showing mutual action, or simply being an inseparable part of certain verbs. You’ve learned the phonetic rules for choosing between **-ся** and **-сь**, mastered the present tense conjugation of key verbs like **дивитися** and **вчитися**, and discovered the beautiful, soft pronunciation of the **-ться** ending. Most importantly, you know how to talk about your daily routine and social interactions much more naturally.

**Self-Check Questions:**
1. What word is the suffix **-ся** historically derived from, and what does it mean?
2. When should you use the **-сь** form instead of the **-ся** form according to the phonetic rule?
3. How is the ending **-ться** (as in **дивиться**) pronounced in standard Ukrainian?
4. What is the difference in meaning between **мити** and **митися**?
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/reflexive-verbs.yaml`

```yaml
- type: fill-in
  title: "Conjugate Reflexive Verbs"
  instruction: "Choose the correct conjugated form of the reflexive verb to complete the sentence."
  items:
    - sentence: "Я ___ телевізор щовечора."
      answer: "дивлюся"
      options: ["дивлюся", "дивишся", "дивиться", "дивляться"]
      explanation: "The subject is я (I), so we use the first person singular form дивлюся."
    - sentence: "Ти ___ добре в школі."
      answer: "вчишся"
      options: ["вчуся", "вчишся", "вчиться", "вчаться"]
      explanation: "The subject is ти (you), so we use the second person singular form вчишся."
    - sentence: "Вона ___ голосно."
      answer: "сміється"
      options: ["сміюся", "сміється", "сміються", "сміємося"]
      explanation: "The subject is вона (she), so we use the third person singular form сміється."
    - sentence: "Ми ___ додому пізно."
      answer: "повертаємося"
      options: ["повертаюся", "повертаєшся", "повертаємося", "повертаються"]
      explanation: "The subject is ми (we), so we use the first person plural form повертаємося."
    - sentence: "Вони ___ спортом."
      answer: "займаються"
      options: ["займаюся", "займаєшся", "займається", "займаються"]
      explanation: "The subject is вони (they), so we use the third person plural form займаються."
    - sentence: "Він ___ вранці."
      answer: "вмивається"
      options: ["вмиваюся", "вмивається", "вмиваємося", "вмиваються"]
      explanation: "The subject is він (he), so we use the third person singular form вмивається."
    - sentence: "Я ___ швидко."
      answer: "одягаюся"
      options: ["одягаюся", "одягаєшся", "одягається", "одягаються"]
      explanation: "The subject is я (I), so we use the first person singular form одягаюся."
    - sentence: "Ти ___ йогою?"
      answer: "займаєшся"
      options: ["займаюся", "займаєшся", "займається", "займаються"]
      explanation: "The subject is ти (you), so we use the second person singular form займаєшся."
    - sentence: "Вони ___ кіно."
      answer: "дивляться"
      options: ["дивлюся", "дивиться", "дивимося", "дивляться"]
      explanation: "The subject is вони (they), so we use the third person plural form дивляться."
    - sentence: "Він ___ у вікно."
      answer: "дивиться"
      options: ["дивлюся", "дивишся", "дивиться", "дивляться"]
      explanation: "The subject is він (he), so we use the third person singular form дивиться."
    - sentence: "Ви ___ в школі?"
      answer: "вчитеся"
      options: ["вчуся", "вчишся", "вчитеся", "вчаться"]
      explanation: "The subject is ви (you, plural/formal), so we use the second person plural form вчитеся."
    - sentence: "Ми ___ кіно."
      answer: "дивимося"
      options: ["дивлюся", "дивишся", "дивимося", "дивляться"]
      explanation: "The subject is ми (we), so we use the first person plural form дивимося."
    - sentence: "Я ___ голосно."
      answer: "сміюся"
      options: ["сміюся", "сміється", "сміються", "сміємося"]
      explanation: "The subject is я (I), so we use the first person singular form сміюся."
    - sentence: "Вона ___ добре."
      answer: "вчиться"
      options: ["вчуся", "вчишся", "вчиться", "вчаться"]
      explanation: "The subject is вона (she), so we use the third person singular form вчиться."
    - sentence: "Ти ___ вранці?"
      answer: "вмиваєшся"
      options: ["вмиваюся", "вмиваєшся", "вмивається", "вмиваються"]
      explanation: "The subject is ти (you), so we use the second person singular form вмиваєшся."
    - sentence: "Вони ___ додому."
      answer: "повертаються"
      options: ["повертаюся", "повертається", "повертаємося", "повертаються"]
      explanation: "The subject is вони (they), so we use the third person plural form повертаються."
    - sentence: "Він ___ вранці."
      answer: "голиться"
      options: ["голюся", "голишся", "голиться", "голяться"]
      explanation: "The subject is він (he), so we use the third person singular form голиться."
    - sentence: "Я ___ музикою."
      answer: "цікавлюся"
      options: ["цікавлюся", "цікавишся", "цікавиться", "цікавляться"]
      explanation: "The subject is я (I), so we use the first person singular form цікавлюся."
    - sentence: "Ми ___ спортом."
      answer: "займаємося"
      options: ["займаюся", "займаєшся", "займаємося", "займаються"]
      explanation: "The subject is ми (we), so we use the first person plural form займаємося."
    - sentence: "Вона ___ тепло."
      answer: "одягається"
      options: ["одягаюся", "одягаєшся", "одягається", "одягаються"]
      explanation: "The subject is вона (she), so we use the third person singular form одягається."
    - sentence: "Ви ___ телевізор?"
      answer: "дивитеся"
      options: ["дивлюся", "дивишся", "дивитеся", "дивляться"]
      explanation: "The subject is ви (you, plural/formal), so we use the second person plural form дивитеся."
    - sentence: "Ти ___ стильно."
      answer: "одягаєшся"
      options: ["одягаюся", "одягаєшся", "одягається", "одягаємося"]
      explanation: "The subject is ти (you), so we use the second person singular form одягаєшся."
    - sentence: "Вони ___ голосно."
      answer: "сміються"
      options: ["сміюся", "сміється", "сміємося", "сміються"]
      explanation: "The subject is вони (they), so we use the third person plural form сміються."
    - sentence: "Він ___ додому пізно."
      answer: "повертається"
      options: ["повертаюся", "повертаєшся", "повертається", "повертаються"]
      explanation: "The subject is він (he), so we use the third person singular form повертається."
    - sentence: "Ми ___ вранці."
      answer: "вмиваємося"
      options: ["вмиваюся", "вмиваєшся", "вмиваємося", "вмиваються"]
      explanation: "The subject is ми (we), so we use the first person plural form вмиваємося."

- type: fill-in
  title: "Choose the Correct Suffix: -ся or -сь"
  instruction: "Select the correct reflexive suffix. Use -сь after vowels, -ся after consonants."
  items:
    - sentence: "Я дивлю___."
      answer: "сь"
      options: ["ся", "сь", "се", "си"]
      explanation: "Дивлю ends in the vowel ю, so we use the shorter form -сь."
    - sentence: "Він дивить___."
      answer: "ся"
      options: ["ся", "сь", "се", "си"]
      explanation: "Дивить ends in a soft consonant, so we use -ся."
    - sentence: "Ми вчимо___."
      answer: "сь"
      options: ["ся", "сь", "се", "си"]
      explanation: "Вчимо ends in the vowel о, so we use -сь."
    - sentence: "Вони дивлять___."
      answer: "ся"
      options: ["ся", "сь", "се", "си"]
      explanation: "Дивлять ends in a soft consonant, so we use -ся."
    - sentence: "Ти дивиш___."
      answer: "ся"
      options: ["ся", "сь", "се", "си"]
      explanation: "Дивиш ends in the consonant ш, so we use -ся."
    - sentence: "Я мию___."
      answer: "сь"
      options: ["ся", "сь", "се", "си"]
      explanation: "Мию ends in the vowel ю, so we use -сь."
    - sentence: "Я вчу___."
      answer: "сь"
      options: ["ся", "сь", "се", "си"]
      explanation: "Вчу ends in the vowel у, so we use -сь."
    - sentence: "Ти вчиш___."
      answer: "ся"
      options: ["ся", "сь", "се", "си"]
      explanation: "Вчиш ends in the consonant ш, so we use -ся."
    - sentence: "Я одягаю___."
      answer: "сь"
      options: ["ся", "сь", "се", "си"]
      explanation: "Одягаю ends in the vowel ю, so we use -сь."
    - sentence: "Ви дивите___."
      answer: "сь"
      options: ["ся", "сь", "се", "си"]
      explanation: "Дивите ends in the vowel е, so we use -сь."
    - sentence: "Ми повертаємо___."
      answer: "сь"
      options: ["ся", "сь", "се", "си"]
      explanation: "Повертаємо ends in the vowel о, so we use -сь."
    - sentence: "Ти одягаєш___."
      answer: "ся"
      options: ["ся", "сь", "се", "си"]
      explanation: "Одягаєш ends in the consonant ш, so we use -ся."
    - sentence: "Я займаю___."
      answer: "сь"
      options: ["ся", "сь", "се", "си"]
      explanation: "Займаю ends in the vowel ю, so we use -сь."
    - sentence: "Ми сміємо___."
      answer: "сь"
      options: ["ся", "сь", "се", "си"]
      explanation: "Сміємо ends in the vowel о, so we use -сь."
    - sentence: "Вони займають___."
      answer: "ся"
      options: ["ся", "сь", "се", "си"]
      explanation: "Займають ends in the consonant т, so we use -ся."

- type: match-up
  title: "Transitive and Reflexive Verb Pairs"
  instruction: "Match each transitive verb (action directed outward) with its reflexive counterpart (action directed back at oneself)."
  pairs:
    - left: "мити (to wash something)"
      right: "митися (to wash oneself)"
    - left: "одягати (to dress someone)"
      right: "одягатися (to dress oneself)"
    - left: "зупиняти (to stop something)"
      right: "зупинятися (to stop oneself)"
    - left: "називати (to name something)"
      right: "називатися (to be called)"
    - left: "вчити (to teach)"
      right: "вчитися (to study)"
    - left: "дивити (to show / to amaze)"
      right: "дивитися (to watch / to look)"
    - left: "вмивати (to wash someone's face)"
      right: "вмиватися (to wash one's face)"
    - left: "повертати (to turn something)"
      right: "повертатися (to return)"
    - left: "зустрічати (to meet someone)"
      right: "зустрічатися (to meet each other)"
    - left: "вітати (to greet someone)"
      right: "вітатися (to greet each other)"
    - left: "знайомити (to introduce someone)"
      right: "знайомитися (to get acquainted)"
    - left: "цікавити (to interest someone)"
      right: "цікавитися (to be interested in)"

- type: fill-in
  title: "Daily Routine Conversations"
  instruction: "Complete each sentence with the correct reflexive verb from the options."
  items:
    - sentence: "Я ___ вранці холодною водою."
      answer: "вмиваюся"
      options: ["вмиваюся", "вмивається", "миюся", "дивлюся"]
      explanation: "Вмиватися means to wash one's face. First person singular: вмиваюся."
    - sentence: "Дитина ___ тепло."
      answer: "одягається"
      options: ["одягаюся", "одягається", "одягаються", "одягаємося"]
      explanation: "The subject is дитина (child), third person singular: одягається."
    - sentence: "Як це ___?"
      answer: "називається"
      options: ["називаюся", "називається", "називаються", "називаємося"]
      explanation: "Називатися means to be called. Third person singular for це: називається."
    - sentence: "Ми ___ в школі."
      answer: "вчимося"
      options: ["вчуся", "вчишся", "вчимося", "вчаться"]
      explanation: "The subject is ми (we), so we use the first person plural form вчимося."
    - sentence: "Ти ___ стильно."
      answer: "одягаєшся"
      options: ["одягаюся", "одягаєшся", "одягається", "одягаються"]
      explanation: "The subject is ти (you), so we use the second person singular form одягаєшся."
    - sentence: "Вони ___ додому пізно."
      answer: "повертаються"
      options: ["повертаюся", "повертається", "повертаємося", "повертаються"]
      explanation: "The subject is вони (they), so we use the third person plural form повертаються."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/reflexive-verbs.yaml`

```yaml
items:
  - lemma: "дивитися"
    translation: "to watch, to look"
    pos: "verb"
    aspect: "imperfective"
    usage: "дивитися телевізор, дивитися у вікно"
    notes: "High-frequency reflexive verb. Second conjugation."
  - lemma: "сміятися"
    translation: "to laugh"
    pos: "verb"
    aspect: "imperfective"
    notes: "Lexicalized reflexive — always has -ся. сміятися з (laughing at) vs сміятися над (mocking)."
  - lemma: "вмиватися"
    translation: "to wash oneself, to wash one's face"
    pos: "verb"
    aspect: "imperfective"
    usage: "вмиватися вранці, вмиватися холодною водою"
    notes: "True reflexive — daily routine verb."
  - lemma: "одягатися"
    translation: "to dress oneself, to get dressed"
    pos: "verb"
    aspect: "imperfective"
    usage: "одягатися тепло, одягатися стильно"
    notes: "True reflexive. Compare with одягати (to dress someone else)."
  - lemma: "називатися"
    translation: "to be called, to be named"
    pos: "verb"
    aspect: "imperfective"
    usage: "Як це називається?"
    notes: "High-frequency identification verb. Compare with називати (to name something)."
  - lemma: "вчитися"
    translation: "to study, to learn"
    pos: "verb"
    aspect: "imperfective"
    usage: "вчитися в школі, вчитися добре"
    notes: "High-frequency. Compare with вчити (to teach / to memorize)."
  - lemma: "займатися"
    translation: "to do, to engage in, to exercise"
    pos: "verb"
    aspect: "imperfective"
    usage: "займатися спортом, займатися йогою"
    notes: "Takes Instrumental case for the activity."
  - lemma: "повертатися"
    translation: "to return, to come back"
    pos: "verb"
    aspect: "imperfective"
    usage: "повертатися додому, повертатися з роботи"
    notes: "High-frequency motion verb."
  - lemma: "голитися"
    translation: "to shave (oneself)"
    pos: "verb"
    aspect: "imperfective"
    notes: "True reflexive — daily routine context."
  - lemma: "зупинятися"
    translation: "to stop (oneself), to come to a halt"
    pos: "verb"
    aspect: "imperfective"
    usage: "Автобус зупиняється."
    notes: "Compare with зупиняти (to stop something/someone)."
  - lemma: "знайомитися"
    translation: "to get acquainted, to meet"
    pos: "verb"
    aspect: "imperfective"
    usage: "Час знайомитися."
    notes: "Reciprocal reflexive — implies mutual action."
  - lemma: "цікавитися"
    translation: "to be interested in"
    pos: "verb"
    aspect: "imperfective"
    notes: "Lexicalized reflexive. Takes Instrumental case."
  - lemma: "подобатися"
    translation: "to like, to be pleasing"
    pos: "verb"
    aspect: "imperfective"
    notes: "Lexicalized reflexive — always has -ся. The thing liked is the subject."
  - lemma: "митися"
    translation: "to wash oneself"
    pos: "verb"
    aspect: "imperfective"
    usage: "Я миюся."
    notes: "True reflexive. Compare with мити (to wash something)."
  - lemma: "зустрічатися"
    translation: "to meet each other, to date"
    pos: "verb"
    aspect: "imperfective"
    notes: "Reciprocal reflexive — mutual action between people."
  - lemma: "вітатися"
    translation: "to greet each other"
    pos: "verb"
    aspect: "imperfective"
    notes: "Reciprocal reflexive."
  - lemma: "цілуватися"
    translation: "to kiss each other"
    pos: "verb"
    aspect: "imperfective"
    notes: "Reciprocal reflexive."
  - lemma: "мити"
    translation: "to wash (something)"
    pos: "verb"
    aspect: "imperfective"
    notes: "Transitive counterpart to митися."
  - lemma: "одягати"
    translation: "to dress (someone else)"
    pos: "verb"
    aspect: "imperfective"
    usage: "Мама одягає дитину."
    notes: "Transitive counterpart to одягатися."
  - lemma: "називати"
    translation: "to name, to call (something)"
    pos: "verb"
    aspect: "imperfective"
    notes: "Transitive counterpart to називатися."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/reflexive-verbs.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/reflexive-verbs.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/reflexive-verbs.yaml`

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
