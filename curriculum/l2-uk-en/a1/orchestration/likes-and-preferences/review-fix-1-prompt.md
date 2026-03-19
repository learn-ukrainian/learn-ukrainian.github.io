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

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] VOCAB_NOT_IN_CONTENT** in `vocabulary`
  - Expected: Required word 'подобатися' must appear in content
  - Actual: Word not found (after stress-mark normalization)
  - Fix: Add 'подобатися' to an appropriate section in the content

- **[HIGH] VOCAB_NOT_IN_CONTENT** in `vocabulary`
  - Expected: Required word 'піти' must appear in content
  - Actual: Word not found (after stress-mark normalization)
  - Fix: Add 'піти' to an appropriate section in the content


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Entire module, Line 35, Section "Мені подобається (I like)", callout box, Lines 33-36, 66-69, 103-107, 134-139, 168-171, Module opening (line 1) and closing (lines 173-184), Multiple sections, throughout the module, Section "Мені подобається (I like)" (entire section, lines 1-36), Section "Мені подобається (I like)" (lines 1-36) and Section "Я люблю (I love)" (lines 38-69)

### Finding 1: CATASTROPHIC — Dative подобається construction completely missing from prose
**Location**: Section "Мені подобається (I like)" (entire section, lines 1-36)
**Problem**: The plan requires the Dative construction «Мені подобається + noun/infinitive» as the PRIMARY grammar point. The section is titled "Мені подобається" but the content teaches "Я люблю" instead. The word "подобається" appears zero times in the prose. The Dative pronoun paradigm (мені/тобі/йому/їй/нам/вам/їм) is never taught. This is the #1 learning objective and it is entirely absent.
**Required Fix**: Complete rewrite of section "Мені подобається (I like)" to teach the Dative construction with examples like "Мені подобається кава", "Тобі подобається музика?", and the full Dative pronoun table. Move люблю content to section "Я люблю (I love)".
**Severity**: HIGH

### Finding 2: CATASTROPHIC — Systematic wrong case (Nominative instead of Accusative) in 9+ sentences
**Location**: Multiple sections, throughout the module
**Problem**: Люблю and хочу are transitive verbs that take the Accusative case. Feminine nouns (кава→каву, музика→музику, вода→воду, книга→книгу) must change form. VESUM confirms каву (v_zna), музику (v_zna), воду (v_zna) as correct Accusative forms. Teaching Nominative after transitive verbs is actively harmful — learners would internalize incorrect grammar.
**Required Fix**: Replace all Nominative objects after люблю/хочу with correct Accusative forms. Note: some correct forms already exist in the conjugation table (line 19: 「Я люблю́ ка́ву.」, line 21: 「Він лю́бить му́зику.」) — the module contradicts itself.
**Severity**: HIGH

### Finding 3: HIGH — "В Україна" (line 35) — invalid Locative form
**Location**: Line 35, Section "Мені подобається (I like)", callout box
**Problem**: "В Україна" is Nominative. The Locative (Місцевий відмінок) required after "в" for location is "В Україні". VESUM confirms "Україні" as v_mis (Locative). Additionally, "кава" after "п'ють" should be "каву" (Accusative).
**Required Fix**: "В Україні люди часто п'ють чай або каву разом. Це гарна традиція."
**Severity**: HIGH

### Finding 4: HIGH — Sections 1 and 2 are nearly identical (both teach люблю)
**Location**: Section "Мені подобається (I like)" (lines 1-36) and Section "Я люблю (I love)" (lines 38-69)
**Problem**: Because section 1 teaches люблю instead of подобатися, both sections cover the same verb. Section 1 has a люблю conjugation table (lines 17-25), section 2 has another люблю conjugation table (lines 50-57). The content is redundant.
**Required Fix**: Section 1 must be rewritten to teach подобатися. Section 2 should then properly contrast люблю with подобатися as the plan requires.
**Severity**: HIGH

### Finding 5: HIGH — Required vocabulary words missing from prose
**Location**: Entire module
**Problem**: "подобатися" (required) never appears in prose. "піти" (required) never appears in prose. "улюблений" (recommended) never appears in prose. The vocabulary file lists all three, and the activities use подобатися extensively, but learners would never encounter these words before being tested on them.
**Required Fix**: Full rewrite needed — подобатися will naturally appear when section 1 is fixed. піти needs an example like "Я хочу піти" in section "Я хочу (I want)". улюблений should appear in at least one example.
**Severity**: HIGH

### Finding 6: MEDIUM — No welcome, no learning preview, no encouragement, no celebration
**Location**: Module opening (line 1) and closing (lines 173-184)
**Problem**: The module jumps straight into grammar with no warm greeting, no "Today you'll learn..." preview. The closing section "Підсумок" (line 173) says 「You can now confidently express your likes, loves, and desires.」 — but the learner was never taught подобатися, so this claim is false. No encouragement markers throughout.
**Required Fix**: Add a warm opening before section 1. Add encouragement at section transitions. Fix the Підсумок to accurately reflect what was actually taught.
**Severity**: HIGH

### Finding 7: MEDIUM — Callout boxes all use identical format
**Location**: Lines 33-36, 66-69, 103-107, 134-139, 168-171
**Problem**: All 5 callout boxes use `[!tip] 💡🎬🌍` with a bold title and Ukrainian examples followed by English translation in parentheses. No variety — no `[!did-you-know]`, `[!culture-note]`, or other types. This is repetitive LLM-pattern output.
**Required Fix**: Vary callout types. Use `[!culture-note]` for the Ukraine tea/coffee tradition, `[!did-you-know]` for interesting facts, `[!tip]` only for actual tips.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: CATASTROPHIC — Dative подобається construction completely missing from prose
- **Location**: Section "Мені подобається (I like)" (entire section, lines 1-36)
- **Problem**: The plan requires the Dative construction «Мені подобається + noun/infinitive» as the PRIMARY grammar point. The section is titled "Мені подобається" but the content teaches "Я люблю" instead. The word "подобається" appears zero times in the prose. The Dative pronoun paradigm (мені/тобі/йому/їй/нам/вам/їм) is never taught. This is the #1 learning objective and it is entirely absent.
- **Fix**: Complete rewrite of section "Мені подобається (I like)" to teach the Dative construction with examples like "Мені подобається кава", "Тобі подобається музика?", and the full Dative pronoun table. Move люблю content to section "Я люблю (I love)".

### Issue 2: CATASTROPHIC — Systematic wrong case (Nominative instead of Accusative) in 9+ sentences
- **Location**: Multiple sections, throughout the module
- **Original examples**:
  - Line 5: 「Я люблю́ ка́ва.」 → should be "Я люблю́ ка́ву."
  - Line 11: 「Я люблю́ му́зика і спорт.」 → should be "Я люблю́ му́зику і спорт."
  - Line 61: 「Я люблю́ ця кни́га.」 → should be "Я люблю́ цю кни́гу."
  - Line 68: 「Ми любимо музика.」 → should be "Ми любимо музику."
  - Line 100: 「Я люблю́ ка́ва.」 → should be "Я люблю́ ка́ву."
  - Line 105: 「Я хочу кава.」 → should be "Я хочу каву."
  - Line 117: 「Ти лю́биш му́зика?」 → should be "Ти лю́биш му́зику?"
  - Line 138: 「Я хочу вода.」 → should be "Я хочу воду."
- **Problem**: Люблю and хочу are transitive verbs that take the Accusative case. Feminine nouns (кава→каву, музика→музику, вода→воду, книга→книгу) must change form. VESUM confirms каву (v_zna), музику (v_zna), воду (v_zna) as correct Accusative forms. Teaching Nominative after transitive verbs is actively harmful — learners would internalize incorrect grammar.
- **Fix**: Replace all Nominative objects after люблю/хочу with correct Accusative forms. Note: some correct forms already exist in the conjugation table (line 19: 「Я люблю́ ка́ву.」, line 21: 「Він лю́бить му́зику.」) — the module contradicts itself.

### Issue 3: HIGH — "В Україна" (line 35) — invalid Locative form
- **Location**: Line 35, Section "Мені подобається (I like)", callout box
- **Original**: 「В Україна люди часто п'ють чай або кава разом. Це гарна традиція.」
- **Problem**: "В Україна" is Nominative. The Locative (Місцевий відмінок) required after "в" for location is "В Україні". VESUM confirms "Україні" as v_mis (Locative). Additionally, "кава" after "п'ють" should be "каву" (Accusative).
- **Fix**: "В Україні люди часто п'ють чай або каву разом. Це гарна традиція."

### Issue 4: HIGH — Sections 1 and 2 are nearly identical (both teach люблю)
- **Location**: Section "Мені подобається (I like)" (lines 1-36) and Section "Я люблю (I love)" (lines 38-69)
- **Problem**: Because section 1 teaches люблю instead of подобатися, both sections cover the same verb. Section 1 has a люблю conjugation table (lines 17-25), section 2 has another люблю conjugation table (lines 50-57). The content is redundant.
- **Fix**: Section 1 must be rewritten to teach подобатися. Section 2 should then properly contrast люблю with подобатися as the plan requires.

### Issue 5: HIGH — Required vocabulary words missing from prose
- **Location**: Entire module
- **Problem**: "подобатися" (required) never appears in prose. "піти" (required) never appears in prose. "улюблений" (recommended) never appears in prose. The vocabulary file lists all three, and the activities use подобатися extensively, but learners would never encounter these words before being tested on them.
- **Fix**: Full rewrite needed — подобатися will naturally appear when section 1 is fixed. піти needs an example like "Я хочу піти" in section "Я хочу (I want)". улюблений should appear in at least one example.

### Issue 6: MEDIUM — No welcome, no learning preview, no encouragement, no celebration
- **Location**: Module opening (line 1) and closing (lines 173-184)
- **Problem**: The module jumps straight into grammar with no warm greeting, no "Today you'll learn..." preview. The closing section "Підсумок" (line 173) says 「You can now confidently express your likes, loves, and desires.」 — but the learner was never taught подобатися, so this claim is false. No encouragement markers throughout.
- **Fix**: Add a warm opening before section 1. Add encouragement at section transitions. Fix the Підсумок to accurately reflect what was actually taught.

### Issue 7: MEDIUM — Callout boxes all use identical format
- **Location**: Lines 33-36, 66-69, 103-107, 134-139, 168-171
- **Problem**: All 5 callout boxes use `[!tip] 💡🎬🌍` with a bold title and Ukrainian examples followed by English translation in parentheses. No variety — no `[!did-you-know]`, `[!culture-note]`, or other types. This is repetitive LLM-pattern output.
- **Fix**: Vary callout types. Use `[!culture-note]` for the Ukraine tea/coffee tradition, `[!did-you-know]` for interesting facts, `[!tip]` only for actual tips.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 5 | 「Я люблю́ ка́ва.」 | Я люблю́ ка́ву. | Grammar (wrong case) |
| 11 | 「Я люблю́ му́зика і спорт.」 | Я люблю́ му́зику і спорт. | Grammar (wrong case) |
| 35 | 「В Україна люди часто п'ють чай або кава разом.」 | В Україні люди часто п'ють чай або каву разом. | Grammar (wrong Locative + wrong Accusative) |
| 61 | 「Я люблю́ ця кни́га.」 | Я люблю́ цю кни́гу. | Grammar (wrong case — both demonstrative and noun) |
| 68 | 「Ми любимо музика.」 | Ми любимо музику. | Grammar (wrong case) |
| 100 | 「Я люблю́ ка́ва.」 | Я люблю́ ка́ву. | Grammar (wrong case) |
| 105 | 「Я хочу кава.」 | Я хочу каву. | Grammar (wrong case) |
| 117 | 「Ти лю́биш му́зика?」 | Ти лю́биш му́зику? | Grammar (wrong case) |
| 138 | 「Я хочу вода.」 | Я хочу воду. | Grammar (wrong case) |

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 4.1)

### This module requires a FULL REBUILD, not incremental fixes.

The issues are too fundamental for FIND/REPLACE patches:
1. Section "Мені подобається (I like)" must be entirely rewritten to teach the Dative construction
2. 9+ sentences have wrong case forms scattered throughout
3. The pedagogical core (three-way contrast: подобається vs люблю vs хочу) doesn't exist
4. Missing vocabulary items (подобатися, піти, улюблений) need organic integration
5. Module needs welcome/preview/encouragement/celebration scaffolding

**Recommended action**: Rebuild via pipeline with explicit instruction to teach подобатися Dative construction in section 1, use Accusative case consistently after люблю/хочу, and include all required vocabulary.

### Projected Overall After Rebuild
With correct grammar, proper подобатися teaching, and beginner scaffolding:
```
Experience: 5→9, Language: 3→9, Pedagogy: 3→9, Activities: 6→9 (already good, just needs prose alignment),
Beginner Safety: 4→9, LLM: 6→8, Linguistic Accuracy: 2→9
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9 = (13.5+9.9+10.8+11.7+11.7+8.0+13.5)/8.9 = 79.1/8.9 = 8.9/10
```

---

## Audit Failures (from automated re-audit)

```
⚠️ HYDRATION NOTE: Outline sums to 1300, exceeding word_target 1200
--- STRICT GATES (Level A1) ---
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
⚠️  [PHANTOM_SECTION_REFERENCE] Review references 1 section(s) not found in content: 'Підсумок'. Verify section names match actual content headers.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/likes-and-preferences-audit.log for details)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/likes-and-preferences.md`

```markdown
## Мені подобається (I like)

When expressing that something appeals to you in Ukrainian, you can use the verb **люби́ти** (to like/love). This is a direct way to share your tastes. While some textbooks teach complex "to me is pleasing" structures, at this stage, we will focus on using straightforward verbs to express what you enjoy.

* **Я люблю́ ка́ва.** — I like coffee.
* **Я люблю́ чита́ти.** — I like to read.

Notice that you can follow the verb directly with an infinitive action, such as **чита́ти** (to read). This is extremely common when talking about your hobbies and daily routines.

> — Приві́т! Що ти лю́биш?
> — Я люблю́ му́зика і спорт. А ти?
> — Я люблю́ чита́ти і пи́ти чай.
> — Це гарно! Я теж люблю́ чай.

To say who likes something, you use the standard pronouns you already know:

| Pronoun | Meaning | Example | Meaning |
|---|---|---|---|
| я | I | **Я люблю́ ка́ву.** | I like coffee. |
| ти | you | **Ти лю́биш чай.** | You like tea. |
| він | he | **Він лю́бить му́зику.** | He likes music. |
| вона | she | **Вона́ лю́бить сніг.** | She likes snow. |
| ми | we | **Ми лю́бимо лі́то.** | We like summer. |
| ви | you (formal/pl) | **Ви лю́бите мі́сто.** | You like the city. |
| вони | they | **Вони́ лю́блять о́сінь.** | They like autumn. |

The verb **люби́ти** changes its ending to match the person who is liking something. Understanding these basic patterns helps you communicate your preferences clearly and naturally.

* **Я люблю́ ціка́вий фільм.** — I like an interesting film.
* **Я люблю́ ці кві́ти.** — I like these flowers.
* **Він лю́бить нові́ книжки́.** — He likes new books.

> [!tip] 💡🎬🌍
> **Цікаво знати!** (Interesting to know!)
> В Україна люди часто п'ють чай або кава разом. Це гарна традиція.
> (In Ukraine, people often drink tea or coffee together. This is a nice tradition.)

## Я люблю (I love)

While we often use **люби́ти** for general appeal, it is also used for stronger emotions. The verb **люби́ти** is used for active enjoyment or deep affection. This verb is incredibly useful for expressing strong positive feelings about food, activities, or people in your life. Do not be afraid to use it often!

The person is the active subject, and the thing loved takes a special object form (the Accusative). The grammatical subject is the person who is feeling the emotion. By mastering this verb, you can describe your world with much more passion and detail.

* **Я люблю́ чай.** — I love tea.
* **Я люблю́ спорт.** — I love sports.
* **Я люблю́ чита́ти.** — I love to read.

The verb belongs to the second conjugation group. Notice the spelling change in the first person singular form, where an extra letter appears to make pronunciation smoother:

| Pronoun | Verb Form |
|---|---|
| я | **люблю́** |
| ти | **лю́биш** |
| він/вона/воно | **лю́бить** |
| ми | **лю́бимо** |
| ви | **лю́бите** |
| вони | **лю́блять** |

There is an important difference in meaning depending on context. Sometimes **я люблю́** describes a general preference, and sometimes an active, ongoing attachment or habit.

* **Я люблю́ ця кни́га.** — I like this book.
* **Я люблю́ цей текст.** — I love this text.
* **Я люблю́ смачни́й борщ.** — I like tasty borscht.
* **Я люблю́ смачни́й борщ.** — I love tasty borscht.

> [!tip] 💡🎬🌍
> **Remember!**
> Я люблю спорт. Він любить читати. Ми любимо музика.
> (I love sports. He loves to read. We love music.)

## Я хочу (I want)

To express desire, use the verb **хоті́ти** (to want). This verb is irregular, meaning its endings follow a unique pattern. It is incredibly useful for everyday situations, such as ordering food at a restaurant or suggesting an activity to a friend. Learning this verb early will help you navigate many practical situations in Ukraine.

The most common way to use this verb is to follow it directly with an infinitive action. This lets you explain exactly what you intend to do next, making your communication much clearer and more efficient.

* **Я хо́чу ї́сти.** — I want to eat.
* **Я хо́чу спа́ти.** — I want to sleep.
* **Він хо́че чита́ти.** — He wants to read.

Here is the complete conjugation pattern for this irregular verb. Pay close attention to the vowel changes in the plural forms, as they shift noticeably:

| Pronoun | Verb Form |
|---|---|
| я | **хо́чу** |
| ти | **хо́чеш** |
| він/вона/воно | **хо́че** |
| ми | **хо́чемо** |
| ви | **хо́чете** |
| вони | **хо́чуть** |

You can also use this verb directly with an object. Just like with our active verb for love, the object takes a specific form to show it is being wanted. You will practice this form more later, but memorize these common examples for now so you can request things politely.

* **Я хо́чу сік.** — I want juice.
* **Я хо́чу квито́к.** — I want a ticket.
* **Вона́ хо́че чай.** — She wants tea.

Compare this directly with the verb we learned first. Preferences do not require this special object form when talking about simple things. This distinction is vital for sounding natural.

* **Я люблю́ ка́ва.** — I like coffee.
* **Я хо́чу чай.** — I want tea.

> [!tip] 💡🎬🌍
> **У кафе:** (At the cafe:)
> — Я хочу кава.
> — А я хочу чай і торт.
> (— I want coffee. — And I want tea and cake.)

## Порівняння (Comparing likes)

Once you can state your own preferences, the next step is asking others about theirs. Building dialogues about shared and different tastes is essential for making friends. You will find that Ukrainians are very hospitable and will frequently ask what you like or want. Showing interest in their answers is a great way to build rapport.

To turn statements into questions, simply use rising intonation or the question word **чи**. You can also ask directly about someone else using short question tags.

* **А ти?** — And you?
* **А ви?** — And you? (formal/plural)
* **Ти лю́биш му́зика?** — Do you like music?
* **Ти лю́биш чита́ти?** — Do you love to read?
* **Ви хо́чете ї́сти?** — Do you want to eat?

Let us look at a short dialogue building on these phrases. Notice how the speakers compare their tastes naturally, creating a flowing conversation:

> — **Приві́т! Ти лю́биш цей чай?**
> — **Так, смачни́й чай. А ти?**
> — **Я теж. Я дуже люблю́ чай.**

Understanding cultural context is helpful when discussing preferences. Ukrainians love to gather for meals and hot drinks, especially in the colder months. Finding out what people enjoy eating or doing in their free time naturally introduces new vocabulary you will see in upcoming modules. Being able to compare your likes with others will make these social interactions much more engaging and authentic.

* **Ми хо́чемо йти в кафе́.** — We want to go to a cafe.
* **Вони́ лю́блять смачни́й торт.** — They like tasty cake.
* **Я люблю́ чай.** — I love tea.
* **Це нудни́й фільм, я хо́чу спа́ти.** — This is a boring film, I want to sleep.

> [!tip] 💡🎬🌍
> **Діалог:** (Dialogue:)
> — Що ти хочеш?
> — Я хочу сік. А ти?
> — Я хочу вода.
> (— What do you want? — I want juice. And you? — I want water.)

## Практика (Practice)

Now it is time to practice choosing the correct construction. Depending on the context, you must decide whether to describe a like, an active love, or a direct desire.

Look at the following pattern examples to see how the choice changes the meaning slightly:

* **Я люблю́ суп.** — I like soup.
* **Я люблю́ суп.** — I love soup.
* **Я хо́чу суп.** — I want soup.

Consider the context carefully. If a friend asks you to watch a movie, but you have no interest, you might use an adjective to explain why you want to leave:

> — **Ти хо́чеш диви́тися фільм?**
> — **Ні, це нудни́й фільм. Я хо́чу спа́ти.**

Try to fill in the gaps mentally when you hear these conversations. Paying attention to context clues makes it easier:

> — **Що ти лю́биш?**
> — **Я люблю́ ________.**
> — **Що ти лю́биш?**
> — **Я люблю́ ________.**

Practice these forms daily. Discuss your preferences, from a tasty drink to an interesting book. 

* **Це ціка́вий текст.** — This is an interesting text.
* **Ця му́зика гарна.** — This music is beautiful.

> [!tip] 💡🎬🌍
> **Ваш вибір:** (Your choice:)
> Choose the correct word: хочу, люблю, любиш.
> (Choose the correct word: want, love/like, love/like (you).)

# Підсумок

You can now confidently express your likes, loves, and desires. You understand how to use direct verbs to share your tastes and feelings.

You have learned the standard pronoun forms, the conjugation pattern for showing affection, and the irregular forms for expressing wants. You can also ask others about their tastes and compare your preferences smoothly.

Test your knowledge with these questions:

1. How do you say "I like coffee"?
2. Which verb describes an active, ongoing attachment or habit?
3. What is the irregular first-person singular form for "to want"?
4. How do you ask "And you?" formally when discussing preferences?
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/likes-and-preferences.yaml`

```yaml
- type: quiz
  title: "Choose the Right Construction"
  instruction: "Select the correct way to express each meaning in Ukrainian."
  items:
    - question: "How do you say 'I like coffee' using the construction that means 'coffee appeals to me'?"
      options:
        - text: "Мені подобається кава"
          correct: true
        - text: "Я люблю кава"
          correct: false
        - text: "Я хочу кава"
          correct: false
        - text: "Мені хочу кава"
          correct: false
      explanation: "The Dative construction мені подобається means something appeals to me — it expresses liking."
    - question: "Which sentence correctly expresses 'He loves music'?"
      options:
        - text: "Він любить музику"
          correct: true
        - text: "Йому подобається музику"
          correct: false
        - text: "Він хоче музику"
          correct: false
        - text: "Він люблю музика"
          correct: false
      explanation: "Любити takes the Accusative (музику) and conjugates as любить for він."
    - question: "How do you say 'I want to eat'?"
      options:
        - text: "Я хочу їсти"
          correct: true
        - text: "Я люблю їсти"
          correct: false
        - text: "Мені подобається їсти"
          correct: false
        - text: "Я хочеш їсти"
          correct: false
      explanation: "Хочу + infinitive (їсти) expresses a desire to do something. Хочу is the я form."
    - question: "Which construction expresses an ongoing active enjoyment, not just a passive appeal?"
      options:
        - text: "Я люблю читати"
          correct: true
        - text: "Мені подобається читати"
          correct: false
        - text: "Я хочу читати"
          correct: false
        - text: "Читати люблю мені"
          correct: false
      explanation: "Люблю expresses active enjoyment or love. Подобається expresses passive appeal. Хочу expresses desire."
    - question: "How do you say 'She wants tea'?"
      options:
        - text: "Вона хоче чай"
          correct: true
        - text: "Вона любить чай"
          correct: false
        - text: "Їй подобається чай"
          correct: false
        - text: "Вона хочу чай"
          correct: false
      explanation: "Хотіти conjugates as хоче for вона. This expresses a desire, not a preference."
    - question: "Which sentence means 'We like summer' (summer appeals to us)?"
      options:
        - text: "Нам подобається літо"
          correct: true
        - text: "Ми подобається літо"
          correct: false
        - text: "Ми хочемо літо"
          correct: false
        - text: "Нам люблять літо"
          correct: false
      explanation: "The Dative construction uses нам (to us) + подобається. The pronoun must be in the Dative form."
    - question: "Someone says 'Мені подобається цей фільм.' What do they mean?"
      options:
        - text: "I like this film (it appeals to me)"
          correct: true
        - text: "I want this film"
          correct: false
        - text: "I love this film (actively)"
          correct: false
        - text: "This film is boring to me"
          correct: false
      explanation: "Мені подобається expresses that something appeals to you — a general liking."
    - question: "How do you say 'They love tasty borscht'?"
      options:
        - text: "Вони люблять смачний борщ"
          correct: true
        - text: "Їм подобається смачний борщ"
          correct: false
        - text: "Вони хочуть смачний борщ"
          correct: false
        - text: "Вони люблю смачний борщ"
          correct: false
      explanation: "Люблять is the вони form of любити. It expresses active love/enjoyment."
    - question: "Which is the correct Dative pronoun form for 'you' (informal) in 'You like music'?"
      options:
        - text: "Тобі подобається музика"
          correct: true
        - text: "Ти подобається музика"
          correct: false
        - text: "Тебе подобається музика"
          correct: false
        - text: "Тобі люблю музика"
          correct: false
      explanation: "Тобі is the Dative form of ти, used with подобається."
    - question: "What does 'Я хочу спати' mean?"
      options:
        - text: "I want to sleep"
          correct: true
        - text: "I like to sleep"
          correct: false
        - text: "I love sleeping"
          correct: false
        - text: "I am sleeping"
          correct: false
      explanation: "Хочу + infinitive (спати) means 'I want to sleep.'"

- type: fill-in
  title: "Complete the Preference Sentences"
  instruction: "Choose the correct word to complete each sentence."
  items:
    - sentence: "___ подобається кава."
      answer: "Мені"
      options: ["Мені", "Я", "Мене", "Моє"]
      explanation: "The Dative construction requires мені (to me), not я (I)."
    - sentence: "Він ___ музику."
      answer: "любить"
      options: ["любить", "люблю", "любиш", "люблять"]
      explanation: "Любить is the він/вона form of любити."
    - sentence: "Ми ___ читати."
      answer: "любимо"
      options: ["любимо", "люблю", "любить", "люблять"]
      explanation: "Любимо is the ми form of любити."
    - sentence: "Вона ___ їсти."
      answer: "хоче"
      options: ["хоче", "хочу", "хочеш", "хочуть"]
      explanation: "Хоче is the вона form of хотіти."
    - sentence: "___ подобається цей фільм."
      answer: "Їй"
      options: ["Їй", "Вона", "Її", "Йому"]
      explanation: "Їй is the Dative form of вона, used with подобається."
    - sentence: "Я ___ смачний борщ."
      answer: "люблю"
      options: ["люблю", "любить", "любиш", "любимо"]
      explanation: "Люблю is the я form of любити."
    - sentence: "Ви ___ пити чай?"
      answer: "хочете"
      options: ["хочете", "хочу", "хоче", "хочемо"]
      explanation: "Хочете is the ви form of хотіти."
    - sentence: "___ подобаються квіти."
      answer: "Нам"
      options: ["Нам", "Ми", "Нас", "Наш"]
      explanation: "Нам is the Dative form of ми. Подобаються is plural because квіти is plural."

- type: match-up
  title: "Match Construction to Meaning"
  instruction: "Match each Ukrainian sentence with its English meaning."
  pairs:
    - left: "Мені подобається кава"
      right: "Coffee appeals to me (I like coffee)"
    - left: "Я люблю каву"
      right: "I love coffee (active enjoyment)"
    - left: "Я хочу каву"
      right: "I want coffee (desire)"
    - left: "Тобі подобається музика?"
      right: "Do you like music? (does it appeal to you?)"
    - left: "Вони люблять читати"
      right: "They love to read"
    - left: "Він хоче спати"
      right: "He wants to sleep"
    - left: "Нам подобається літо"
      right: "We like summer (it appeals to us)"
    - left: "Вона хоче їсти"
      right: "She wants to eat"
    - left: "Їм подобається борщ"
      right: "They like borscht (it appeals to them)"
    - left: "Ми любимо спорт"
      right: "We love sports"

- type: unjumble
  title: "Put the Words in Order"
  instruction: "Arrange the words to form a correct Ukrainian sentence."
  items:
    - words: ["подобається", "Мені", "кава"]
      answer: "Мені подобається кава"
    - words: ["люблю", "Я", "читати"]
      answer: "Я люблю читати"
    - words: ["хоче", "Він", "спати"]
      answer: "Він хоче спати"
    - words: ["подобається", "Тобі", "музика"]
      answer: "Тобі подобається музика"
    - words: ["любить", "Вона", "чай"]
      answer: "Вона любить чай"
    - words: ["хочемо", "Ми", "їсти"]
      answer: "Ми хочемо їсти"

- type: true-false
  title: "True or False?"
  instruction: "Decide whether each statement about Ukrainian preference expressions is true or false."
  items:
    - statement: "In the construction 'Мені подобається кава,' the word мені means 'I.'"
      correct: false
      explanation: "Мені is the Dative form meaning 'to me.' The regular form for 'I' is я."
    - statement: "The verb хотіти (to want) is irregular — its forms are хочу, хочеш, хоче, хочемо, хочете, хочуть."
      correct: true
      explanation: "Хотіти is indeed irregular. Notice the vowel changes in the plural forms."
    - statement: "You can say 'Я люблю читати' to mean 'I love to read.'"
      correct: true
      explanation: "Люблю + infinitive is used to express love or enjoyment of an activity."
    - statement: "To say 'They like flowers,' you should say 'Їм подобається квіти.'"
      correct: false
      explanation: "Because квіти is plural, you need the plural form: Їм подобаються квіти."
    - statement: "'Подобається' expresses active, passionate love for something."
      correct: false
      explanation: "Подобається expresses passive appeal — something is pleasing to you. For active love, use люблю."
    - statement: "The Dative pronoun form for 'he' is йому — as in 'Йому подобається спорт.'"
      correct: true
      explanation: "Йому is the Dative form of він, used with подобається."
    - statement: "You can follow хочу directly with an infinitive, like 'Я хочу пити чай.'"
      correct: true
      explanation: "Хочу + infinitive is a common pattern for expressing desires."
    - statement: "The form 'люблять' is used with the pronoun ми."
      correct: false
      explanation: "Люблять is the вони form. The ми form is любимо."

- type: group-sort
  title: "Sort by Construction"
  instruction: "Sort these sentences into the correct category based on which construction they use."
  groups:
    - name: "Подобається (appeals to me)"
      items:
        - "Мені подобається кава"
        - "Тобі подобається музика"
        - "Їй подобається фільм"
        - "Нам подобається літо"
    - name: "Люблю (love/enjoy actively)"
      items:
        - "Я люблю читати"
        - "Він любить спорт"
        - "Вони люблять борщ"
        - "Ми любимо чай"
    - name: "Хочу (want/desire)"
      items:
        - "Я хочу їсти"
        - "Вона хоче спати"
        - "Ви хочете сік"
        - "Вони хочуть торт"
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/likes-and-preferences.yaml`

```yaml
items:
  - lemma: "подобатися"
    translation: "to like, to appeal"
    pos: "verb"
    aspect: "imperfective"
    notes: "Used in Dative construction: Мені подобається кава."
    usage: "Мені подобається музика."
  - lemma: "любити"
    translation: "to love, to enjoy"
    pos: "verb"
    aspect: "imperfective"
    notes: "II conjugation. Active enjoyment: Я люблю каву."
    usage: "Я люблю читати."
  - lemma: "хотіти"
    translation: "to want"
    pos: "verb"
    aspect: "imperfective"
    notes: "Irregular conjugation: хочу, хочеш, хоче, хочемо, хочете, хочуть."
    usage: "Я хочу їсти."
  - lemma: "кава"
    translation: "coffee"
    pos: "noun"
    gender: "f"
    usage: "Мені подобається кава."
  - lemma: "музика"
    translation: "music"
    pos: "noun"
    gender: "f"
    usage: "Тобі подобається музика?"
  - lemma: "читати"
    translation: "to read"
    pos: "verb"
    aspect: "imperfective"
    usage: "Я люблю читати."
  - lemma: "їсти"
    translation: "to eat"
    pos: "verb"
    aspect: "imperfective"
    usage: "Я хочу їсти."
  - lemma: "піти"
    translation: "to go (perfective)"
    pos: "verb"
    aspect: "perfective"
    notes: "Perfective infinitive used after хочу."
    usage: "Я хочу піти."
  - lemma: "спати"
    translation: "to sleep"
    pos: "verb"
    aspect: "imperfective"
    usage: "Він хоче спати."
  - lemma: "пити"
    translation: "to drink"
    pos: "verb"
    aspect: "imperfective"
    usage: "Я хочу пити чай."
  - lemma: "цікавий"
    translation: "interesting"
    pos: "adj"
    usage: "Це цікавий фільм."
  - lemma: "нудний"
    translation: "boring"
    pos: "adj"
    usage: "Це нудний фільм."
  - lemma: "смачний"
    translation: "tasty, delicious"
    pos: "adj"
    usage: "Я люблю смачний борщ."
  - lemma: "улюблений"
    translation: "favourite"
    pos: "adj"
    usage: "Це мій улюблений чай."
  - lemma: "чай"
    translation: "tea"
    pos: "noun"
    gender: "m"
    usage: "Мені подобається чай."
  - lemma: "борщ"
    translation: "borscht"
    pos: "noun"
    gender: "m"
    usage: "Я люблю смачний борщ."
  - lemma: "фільм"
    translation: "film, movie"
    pos: "noun"
    gender: "m"
    usage: "Мені подобається цей фільм."
  - lemma: "спорт"
    translation: "sport(s)"
    pos: "noun"
    gender: "m"
    usage: "Він любить спорт."
  - lemma: "сік"
    translation: "juice"
    pos: "noun"
    gender: "m"
    usage: "Я хочу сік."
  - lemma: "гарний"
    translation: "nice, beautiful, good"
    pos: "adj"
    usage: "Це гарна традиція."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/likes-and-preferences.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/likes-and-preferences.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/likes-and-preferences.yaml`

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
