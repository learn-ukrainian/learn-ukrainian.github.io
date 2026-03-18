        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
             Множина прикметників (Adjective plurals)                202 /  250  ⚠️ (-48)
     Винятки та особливості (Exceptions and special cases)     0 /  175  ❌ (-175)
     Практика (Practice)                                     220 /  250  ⚠️ (-30)
     ──────────────────────────────────────────────────────────────────────────────
     TOTAL                                                  1116 / 1200  ❌ (-84)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 1510/1200 (raw: 1939)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 4/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ⚠️ Refresh recommended: Research has 2+ cultural hooks but content has no cultural section
Immersion    🇺🇦 15.6% (target 10-20% (M13))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [METALANGUAGE] Metalanguage terms used but not in vocabulary: множина
     → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 1 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/plurals-and-alternation-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/plurals-and-alternation.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 1 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/plurals-and-alternation-audit.log for details)

Running RAG word verification...
Verifying: plurals-and-alternation.md
  VESUM misses: 2 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 36230.67it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 94 | VESUM: 92 (97.9%) | RAG: 1 | Not found: 1
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/plurals-and-alternation-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

VESUM: 166/177 (94%) verified
⚠️ VESUM not found (11): Вашуленко, дітині, кіти, ножицю, ножиця, ножиціі, ніжі, пічі, стіли, хлопце
        ```

        ## Current Content of Affected Section(s)


Some nouns don't just change their ending — they also change a vowel INSIDE the stem. This is called alternation, and it's one of Ukrainian's neatest features.

### The Fleeting **і**

The most common alternation is **і → о** or **і → е**. Watch carefully:

- **кіт** → **коти́** (cat → cats) — і becomes о
- **стіл** → **столи́** (table → tables) — і becomes о
- **ніж** → **ножі́** (knife → knives) — і becomes о
- **піч** → **печі́** (oven → ovens) — і becomes е

Why does this happen? In the singular, the syllable is closed (it ends in a consonant: **кіт**). The vowel **і** appears in these closed syllables. When you add a plural ending, the syllable opens up (**ко-ти**), and the **і** reverts to its original **о** or **е**. Linguists call this the "fleeting **і**" — it appears and disappears depending on the word's shape.

You don't need to memorize the linguistics — just know that short masculine nouns with **і** in the stem often change that vowel in the plural.

> [!tip] Pattern Spotter
> See **і** in the last syllable of a short masculine noun like **кіт**, **стіл**, **ніж**, or **дім**? There's a good chance it will alternate in the plural. Watch for it!

### Consonant Alternation Preview

Ukrainian also has consonant changes where **к → ц**, **г → з**, and **х → с** before the ending **-і**:

- **рука́** → **у руці** (hand → in the hand)
- **нога́** → **на нозі** (foot → on the foot)

These examples are NOT plurals — they're forms you'll meet later in the locative case. This is just a quick preview so the pattern won't surprise you when it returns. For now, simply notice that consonants can change too — not only vowels.

### Your Strategy

When you encounter a new word with **і** in its stem, ask yourself: does this **і** alternate? Here's your checklist:

- Is it a short masculine noun? (one syllable, like **кіт**, **стіл**)
- Does the **і** sit in the last syllable?

If yes to both, the **і** will likely change to **о** or **е** in the plural. With practice, you'll spot these instantly.

## Множина прикметників (Adjective plurals)

Here's genuinely great news. You already learned that adjectives have different endings for masculine, feminine, and neuter nouns. In the plural, all three genders collapse into ONE form. One ending instead of three — this is going to make your life easier.

### Hard-Stem Adjectives

The plural ending is **-і** for all genders:

- **нови́й** (m) → **нові́**
- **нова́** (f) → **нові́**
- **нове́** (n) → **нові́**
- **вели́кий** (m) → **вели́кі**
- **вели́ка** (f) → **вели́кі**
- **вели́ке** (n) → **вели́кі**
- **стари́й** (m) → **старі́**
- **стара́** (f) → **старі́**
- **старе́** (n) → **старі́**

### Soft-Stem Adjectives

The same pattern, just with a soft variant:

- **си́ній** (m) → **си́ні**
- **си́ня** (f) → **си́ні**
- **си́нє** (n) → **си́ні**

### Agreement in Action

The adjective MUST match the noun in number. Plural noun = plural adjective:

- **Це нові́ кни́ги.** (These are new books.)
- **Це вели́кі мі́ста.** (These are big cities.)
- **Це молоді студе́нти.** (These are young students.)
- **Ті вели́кі буди́нки старі́.** (Those big buildings are old.)
- **Це до́брі лю́ди.** (These are good people.)
- **Це мале́нькі ді́ти.** (These are small children.)

> [!practice] Try It Yourself
> Take any adjective you know — **гарний**, **цікавий**, **дорогий** — and change the ending to **-і**. Pair it with a plural noun. You've just built a Ukrainian noun phrase!

## Винятки та особливості — Exceptions and Special Cases

### Uncountable Nouns

Some nouns refer to things you can't count individually. They exist only in the singular — they have no plural form:

- **молоко́** (milk)
- **цу́кор** (sugar)
- **вода́** (water, in the general sense)
- **пові́тря** (air)

You already know **молоко** and **цукор** from earlier modules. Now you understand why they never get plural endings — you simply can't count milk or sugar as individual items.

### Plural-Only Nouns

Other nouns exist ONLY in the plural. They have no singular form at all:

- **гроші** (money) — always plural
- **две́рі** (door/doors) — always plural
- **но́жиці** (scissors) — always plural
- **окуля́ри** (glasses/eyeglasses) — always plural

You already know **двері** and **окуляри**. Now you understand why they always look plural — because they ARE always plural. Even when talking about one door or one pair of scissors, Ukrainian uses the plural form.

> [!warning] Don't Fight It
> Don't try to make these words singular. In everyday Ukrainian, **гроші** is always plural. **Ножиці** is always plural. Just accept them as they are — you do the same in English with "scissors" and "glasses."

<!-- adapted from: Вашуленко, Grade 3, p. 116 -->

### Stress Shifts

Some nouns change their stress in the plural. You learned about stress mobility earlier — here it is in action:

- **рука́** → **ру́ки** (hand → hands)
- **сестра́** → **сестри́** (sister → sisters)
- **нога́** → **но́ги** (leg → legs)

This is perfectly normal in Ukrainian. Your ear will adjust as you hear more plural forms.

## Практика (Practice)

### Plural Formation

Look at each singular noun and form the plural. Check the gender, apply the right ending, and watch for alternation:

- **студе́нт** → ? → **студе́нти** ✓
- **кни́га** → ? → **кни́ги** ✓
- **мі́сто** → ? → **мі́ста** ✓
- **кіт** → ? → **коти́** ✓ (alternation!)
- **мо́ре** → ? → **мо́ря** ✓
- **стіл** → ? → **столи́** ✓ (alternation!)

### Matching Singulars to Plurals

Can you match each singular to its correct plural? Some are regular, some are not:

| Singular | Plural |
|----------|--------|
| дити́на | ді́ти |
| люди́на | лю́ди |
| о́ко | о́чі |
| кіт | коти́ |
| кни́га | кни́ги |
| ніж | ножі́ |

### Dialogues

> **(At the Market / На ри́нку)**
>
> — Де я́блука?
> — Ось я́блука. Вели́кі я́блука!
> — А де кни́ги?
> — Кни́ги там. Нові́ кни́ги!

<!-- adapted from: Вашуленко, Grade 3 -->

> **(At Home / Вдо́ма)**
>
> — Де ді́ти?
> — Ді́ти тут.
> — А коти́?
> — Коти́ там. Руді́ коти́!

### Reading Plural Phrases

Practice reading these sentences aloud:

- **Це нові́ кни́ги.** — These are new books.
- **Де вели́кі мі́ста?** — Where are the big cities?
- **Ось молоді студе́нти.** — Here are the young students.
- **Це до́брі лю́ди.** — These are good people.
- **Де мале́нькі ді́ти?** — Where are the small children?
- **Це руді́ коти́.** — These are ginger cats.
- **Ось старі́ кни́ги.** — Here are the old books.
- **Це си́ні о́чі.** — These are blue eyes.

> [!challenge] Market Challenge
> A vendor shows you items. Name the plural: **яблуко** → ? **книга** → ? **ніж** → ? **окуляри** → ? (careful — that last one is already plural!)

## Вправи (Activities)

<!-- activities: sidecar -->

Now that you've learned the rules, it's time to put them into action! Use the activities below to practice forming plurals, matching singulars to their plural forms, and identifying those tricky irregulars. Remember to watch for vowel alternation in words like **кіт** and **стіл**. Good luck!

## Словник (Vocabulary)

<!-- vocabulary: sidecar -->

## Підсумок — Summary

You've unlocked a major piece of Ukrainian grammar. Here's what you can now do:

You can form plurals for all three genders: masculine nouns add **-и/-і** (**студе́нт → студе́нти**), feminine nouns swap **-а** for **-и** (**кни́га → кни́ги**), and neuter nouns swap **-о** for **-а** (**мі́сто → мі́ста**). You know that some common words have irregular plurals: **ді́ти**, **лю́ди**, **о́чі**. You can spot the "fleeting **і**" — when **і** changes to **о** or **е** in the plural (**кіт → коти́**, **стіл → столи́**). You understand uncountable nouns (**молоко́**, **цу́кор**) and plural-only nouns (**гроші**, **две́рі**, **но́жиці**). And best of all, adjective plurals are simple — just **-і** for all genders (**нові́**, **вели́кі**, **си́ні**).

### Self-Check

1. What is the plural of **місто**?
2. Why does **кіт** become **коти** and not **кіти**?
3. What is the plural form of **новий**?
4. Name two plural-only nouns.

If you answered all four, you're ready for the checkpoint ahead. You've come so far — keep it up!

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/plurals-and-alternation.md`

        ## Instructions

        1. Fix ONLY the violations listed above
        2. For euphony (в/у, і/й): apply Ukrainian euphony rules strictly
        3. Do NOT add or remove content — only fix the specific violations
        4. Preserve all markdown formatting, headers, and structure

        ## Output Format (MANDATORY)

        Output ONLY the fixed section(s) between delimiters:

        ```
        ===SECTION_FIX_START===
        ## {section title}
        {fixed section content}
        ===SECTION_FIX_END===
        ```

        If multiple sections need fixing, output each in its own delimiter block.
        Do NOT output anything else — no explanations, no commentary.
