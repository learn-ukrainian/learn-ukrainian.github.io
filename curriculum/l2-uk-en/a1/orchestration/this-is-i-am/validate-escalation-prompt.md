        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        Engagement   ✅ 9/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Lint         ✅ Clean Format
Pedagogy     ❌ 2 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    🇺🇦 18.6% (target 10-20% (M09))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [INFO] Dative case used at A1: 'Особові' (taught formally at A2)
     → FIX: No action needed — incidental dative exposure is acceptable.
  [HEADING_LEVEL] Main section 'Vocabulary' uses H2 (##) but spec requires H1 (#)
     → FIX: Change '## Vocabulary' to '# Vocabulary' for top-level TOC compliance
  [FORBIDDEN_HEADER] Forbidden header '## Vocabulary' violates Clean MD standard (Issue #398)
     → FIX: Remove '## Vocabulary' header. This section is auto-injected from vocabulary/{slug}.yaml at build time. See docs/l2-uk-en/templates/ for correct pattern.


📋 TEMPLATE COMPLIANCE VIOLATIONS FOUND:
  🔴 [DUPLICATE_SYNONYMOUS_HEADERS] Multiple headers contain 'Presentation': Граматика: Секрет нульової зв'язки (Grammar: The Zero Copula Secret), Презентація: Особові займенники (Presentation: Personal Pronouns)
     → FIX: RENAME one header to NOT contain 'Presentation'. Example: 'Агіографічна спадщина' → 'Житійна творчість' (removes the duplicate word).
  🔴 [FORBIDDEN_HEADER] Forbidden header '## Vocabulary' violates Clean MD standard (Issue #398)
     → FIX: Remove '## Vocabulary' header. Template 'a1-module-template.md' specifies this section is auto-injected from YAML sidecars.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
   → 5 violations (moderate)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/this-is-i-am-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/this-is-i-am.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 2 Critical Template Violations

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/this-is-i-am-audit.log for details)

Running RAG word verification...
Verifying: this-is-i-am.md
  VESUM misses: 8 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 116724.60it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 71 | VESUM: 63 (88.7%) | RAG: 6 | Not found: 2
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/this-is-i-am-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

Prose-relevant failures:
  lesson: 1863/1200 (raw: 2302) | pedagogy: 2 violations
VESUM: 65/73 (89%) verified
⚠️ VESUM not found (4): Захарійчук, Кравцова, Сара, Ірина
        ```

        ## Current Content of Affected Section(s)


> [!example] **Pronouns in Action**
> Let's see how pronouns replace names in a simple story:
> - **Це Тарас.** (This is Taras.) → **Він тут.** (He is here.)
> - **Це книга.** (This is a book.) → **Вона там.** (It is there.)
> - **Це вікно.** (This is a window.) → **Воно ось.** (It is here.)
> - **Тарас і я.** (Taras and I.) → **Ми друзі.** (We are friends.)
> - **Оксана і Тарас.** (Oksana and Taras.) → **Вони там.** (They are there.)

## Граматика: Секрет нульової зв'язки (Grammar: The Zero Copula Secret)

Here's the big surprise of this module. In English, you need the verb "to be" in every identity sentence:

- I **am** a student.
- She **is** a teacher.
- He **is** Ukrainian.

In Ukrainian, that little verb simply disappears. Ukrainian drops "to be" in the present tense. Linguists call this the "zero copula" — a fancy name for "no linking verb." Look:

| English | Ukrainian | What's missing? |
|---------|-----------|-----------------|
| I **am** a student. | **Я Ø студент.** | am |
| She **is** a teacher. | **Вона Ø вчителька.** | is |
| He **is** Ukrainian. | **Він Ø українець.** | is |
| We **are** friends. | **Ми Ø друзі.** | are |

The **Ø** symbol shows where English would put "am/is/are" — but Ukrainian leaves it empty. Subject goes straight to the predicate. That's it!

Here are more examples of this efficient pattern:

- **Я студент.** — I am a student. (male speaker)
- **Я студентка.** — I am a student. (female speaker)
- **Він вчитель.** — He is a teacher.
- **Вона українка.** — She is Ukrainian.
- **Ти студент?** — Are you a student?
- **Ви вчителька?** — Are you (formal) a teacher?
- **Вони друзі.** — They are friends.
- **Ми тут.** — We are here.

> [!tip] **The Pattern**
> **Pronoun + Noun = Complete sentence.**
> No "am," no "is," no "are." Just two words and you're done.

> [!myth-buster] **"Is it a sentence?"**
> Yes! Even without a verb, **«Я студент»** is a perfect, grammatically complete sentence in Ukrainian. In fact, adding a verb would make it sound strange!

> **(At a conference / На конференції)**
>
> — Хто ви?
>
> — Я Оксана. Я вчителька. А ви?
>
> — Я Тарас. Я студент.
>
> — Дуже приємно!
>
> — Дуже приємно!

### The Phantom «є» — A Common Trap

Does Ukrainian have a word for "is"? Yes — **є**. But in modern spoken Ukrainian, **є** is almost never used in identity sentences. Saying *«Я є студент»* sounds archaic, like saying "I doth be a student" in English. It's technically correct but sounds very stiff.

> [!warning] **Learner Error: The Phantom "Is"**
> Your English brain will want to insert **є** into every sentence. Resist the urge!
> - ❌ *Я є студент.* — sounds strange and unnatural
> - ✅ **Я студент.** — natural and correct
> - ❌ *Вона є вчителька.* — awkward
> - ✅ **Вона вчителька.** — perfect

In identity statements (saying who someone is or what something is), drop the verb. Just pronoun + noun.

### Nationality and Role Pairs

Ukrainian has different forms for masculine and feminine roles and nationalities. You already know about grammatical gender from Module 7. Now you'll use it with pronouns:

- **Він українець.** / **Вона українка.** — He / She is Ukrainian.
- **Він студент.** / **Вона студентка.** — He / She is a student.
- **Він вчитель.** / **Вона вчителька.** — He / She is a teacher.

A masculine speaker says **Я українець**, a feminine speaker says **Я українка**. Always match the form to the person you're describing!

## Робота над помилками та практика (Error Correction and Practice)

### The «It» Trap

In English, you call everything that isn't a person "it" — the table, the book, the car. Ukrainian doesn't work this way! Remember from Module 7: every noun has a grammatical gender. When you replace a noun with a pronoun, you must match the gender:

- **Стіл** (table) is masculine → **він**
- **Книга** (book) is feminine → **вона**
- **Молоко** (milk) is neuter → **воно**

So when someone asks **Що це?** and you point to a table, say **Це стіл. Він тут.** — never *Воно тут*! This is one of the biggest mental shifts for English speakers.

> [!note] **When to Use «воно»**
> Use **воно** only for neuter nouns: **молоко**, **місто** (city), **вікно** (window), **море** (sea). Don't use **воно** for people — that's rude!

### Drill: Replacing Nouns with Pronouns

Practice replacing each noun with the correct pronoun. Remember the gender!

- **Це Іван.** → **Він студент.**
- **Це Оксана.** → **Вона вчителька.**
- **Це книга.** → **Вона тут.**
- **Це дім.** → **Він там.**
- **Це молоко.** → **Воно тут.**
- **Це сіль.** → **Вона там.**

### Transformation Practice

Now combine **це** identification with pronoun sentences:

- **Це Тарас. Він українець.**
- **Це Марія. Вона студентка.**
- **Це хліб. Він там.**
- **Ось книга. Вона тут.**

The word **ось** (here, over here) works like **це** but draws extra attention — like pointing and saying "right here!" or "look!"

> **(In a room / У кімнаті)**
>
> — Що це?
>
> — Це книга. Вона тут.
>
> — А що там?
>
> — Там стіл. Він там.
>
> — А хто це?
>
> — Це Марія. Вона студентка.

## Продакшн: Хто я і Хто ви? (Production: Who am I and Who are you?)

You now have everything you need for your first real self-introduction in Ukrainian. Let's put it all together!

### Patterns for Intro

- **Мене звати ______.** (My name is...)
- **Я студент / студентка.** (I am a student.)
- **Я українець / українка.** (I am Ukrainian. — or your nationality)

> **(At a university / В університеті)**
>
> — Добрий день! Мене звати Тарас. Я студент. Я українець. А ви?
>
> — Добрий день! Мене звати Сара. Я студентка.
>
> — Дуже приємно!
>
> — Дуже приємно!
>
> **(At a café / У кафе)**
>
> — Привіт! Я Марія. А ти хто?
>
> — Привіт! Я Іван. Я студент.
>
> — Ти українець?
>
> — Так, я українець. А ти?
>
> — Я українка!

Notice the difference? The first dialogue uses **ви** — a formal meeting at university. The second uses **ти** — chatting with a peer at a café. You're already applying the **Ви Safety Net**!

### Identifying Others

You can also introduce other people:

- **Ось Тарас. Він студент.**
- **Ось Оксана. Вона вчителька.**
- **Вони тут. Ми друзі.**

The simple structure **Subject + Noun** (no verb!) is the foundation of your A1 communication. You'll use it hundreds of times from here on.

# Activities

## Vocabulary

## Підсумок — Summary

You've just unlocked one of the most important structures in Ukrainian. Here's what you can now do:

- **Identify** people and things: **Це Ірина. Це книга.**
- **Ask** who or what: **Хто це? Що це?**
- **Introduce yourself**: **Мене звати... Я студент.**
- **Use all 8 pronouns**: **я, ти, він, вона, воно, ми, ви, вони**
- **Form sentences without "to be"**: **Я українець. Вона вчителька.**
- **Choose the right register**: **ви** for strangers, **ти** for friends

The zero copula is your new superpower. English speakers need three words ("I am a student"), but you need just two: **Я студент.** Clean, simple, powerful. Great work — you're well on your way!

### Self-Check Questions

1. How do you say "This is a book" in Ukrainian? (Answer: **Це книга.**)
2. Which pronoun replaces a masculine noun like **стіл**? (Answer: **він**)
3. Should you use **ти** or **ви** when meeting a teacher for the first time? (Answer: **ви**)
4. Is *«Я є студент»* correct in modern Ukrainian? (Answer: No — say **Я студент** without **є**.)


        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/this-is-i-am.md`

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
