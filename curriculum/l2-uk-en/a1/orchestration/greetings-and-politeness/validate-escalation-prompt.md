        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 5/3
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
Immersion    🇺🇦 16.0% (target 10-20% (M08))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [HEADING_LEVEL] Main section 'Vocabulary' uses H2 (##) but spec requires H1 (#)
     → FIX: Change '## Vocabulary' to '# Vocabulary' for top-level TOC compliance
  [FORBIDDEN_HEADER] Forbidden header '## Vocabulary' violates Clean MD standard (Issue #398)
     → FIX: Remove '## Vocabulary' header. This section is auto-injected from vocabulary/{slug}.yaml at build time. See docs/l2-uk-en/templates/ for correct pattern.


📋 TEMPLATE COMPLIANCE VIOLATIONS FOUND:
  🔴 [FORBIDDEN_HEADER] Forbidden header '## Vocabulary' violates Clean MD standard (Issue #398)
     → FIX: Remove '## Vocabulary' header. Template 'a1-module-template.md' specifies this section is auto-injected from YAML sidecars.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 3 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/greetings-and-politeness-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/greetings-and-politeness.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 1 Critical Template Violations

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/greetings-and-politeness-audit.log for details)

Running RAG word verification...
Verifying: greetings-and-politeness.md
  VESUM misses: 15 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 212549.19it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 73 | VESUM: 58 (79.5%) | RAG: 7 | Not found: 8
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/greetings-and-politeness-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

Prose-relevant failures:
  lesson: 1574/1200 (raw: 1695) | pedagogy: 2 violations
VESUM: 72/87 (83%) verified
⚠️ VESUM not found (11): Большакова, Загарійчук, Літвінова, Оксано, Петре, Пономарова, Софіє, Тарасе, Тетяно, Ірина
        ```

        ## Current Content of Affected Section(s)


## Ти і Ви (T-V distinction)

One of the most important social rules you'll learn in Ukrainian is knowing when to say **ти** and when to say **Ви**. Getting this right shows respect and cultural awareness.

**Ти** is singular and informal. Use it with:

- Friends and peers your age
- Family members (parents, siblings, cousins)
- Children
- Pets

**Ви** is either singular formal OR plural (any group of two or more). Use it with:

- Strangers — regardless of their age
- Teachers, professors, bosses
- Elders (anyone noticeably older than you)
- In shops, cafés, and official settings
- Any group of people, even close friends

> [!warning] **The Golden Rule**
> Always start with **Ви** until the other person suggests switching. The phrase **«Shall we switch to ти?»** signals that transition. Never make this switch yourself with someone older or in a position of authority — wait for them to offer.

This distinction is more strictly observed in Ukrainian culture than in many Western European languages. Using **ти** with a stranger or elder is considered rude — even if your intentions are perfectly friendly. Think of it this way: **Ви** is the respectful default, and **ти** is earned through closeness or invitation.

Notice how this affects your choice of greeting:

- **Привіт!** goes naturally with the informal register (**ти**)
- **Добрий день!** goes naturally with the formal register (**Ви**)

> [!culture] **Ви with a Capital В**
> When writing to one person formally, Ukrainians often capitalize **Ви**: «Як Ви?» This shows extra respect, especially in letters and messages.

## Ввічливість (Politeness)

You already know **дякую** (thank you). Now let's expand your politeness toolkit.

**Дякую** is your everyday «thank you.» You can make it stronger:

- **Дуже дякую!** — Thank you very much!
- **Щиро дякую!** — Thank you sincerely!

**Будь ласка** is a true magic word in Ukrainian — it means both «please» and «you're welcome»:

- When requesting something: **Каву, будь ласка.** (Coffee, please.)
- When responding to thanks: — **Дякую!** — **Будь ласка!** (— Thank you! — You're welcome!)

> [!tip] **Two Words, Always**
> Remember that **будь ласка** is always two separate words. Don't write them as one! The soft sign (ь) in **будь** is essential.

For saying sorry, you have two levels:

**Вибачте!** (formal) and **вибач!** (informal) mean «excuse me» or «sorry.» Use them to:

- Get someone's attention: **Вибачте, де метро?** (Excuse me, where is the metro?)
- Apologize for something small: **Вибачте!** (when you bump into someone)

**Перепрошую** is more formal and sincere — a genuine apology when you've truly inconvenienced someone. You might hear it in professional settings or from service staff.

Here are everyday situations where you'll use these expressions:

| Situation | What to say |
|---|---|
| Ordering coffee | **Каву, будь ласка!** |
| Bumping into someone | **Вибачте!** |
| Receiving a gift | **Дуже дякую!** |
| Holding a door for someone | **— Дякую! — Будь ласка!** |
| Arriving late to a meeting | **Перепрошую!** |

And when someone welcomes you somewhere, you might hear **welcome!** As in: **Welcome to Ukraine!**

## Звертання (Addressing People)

When you address someone directly in Ukrainian, the name changes form. This is called the vocative. For now, just memorize these as fixed phrases — you'll learn the full rules in a later module.

With family, you'll use:

- **Мамо!** (Mom!) — from мама
- **Тату!** (Dad!) — from тато
- **Бабусю!** (Grandma!) — from бабуся
- **Дідусю!** (Grandpa!) — from бабусь

With a friend: **Друже!** (Friend!) — from друг.

For formal address, Ukrainian uses **pane (Mr.)** and **pani (Ms.)**:

- **Добрий день, pane Petre!**
- **Добрий день, pani Oksano!**

Notice the pattern: most feminine names and titles end in **-о** when you address someone (Мамо, Оксано), while most masculine ones end in **-е or -у** (Друже, Тату, Петре).

> [!note] **Pani Stays Pani**
> The word **pani** itself doesn't change — only the name after it does: **пані Оксано**, **пані Іро**, **пані Тетяно**.

<!-- adapted from: Літвінова, Grade 6, §28; Пономарова, Grade 3, p.130 -->

## Знайомство (Introductions)

Meeting someone new? Here's everything you need.

To ask someone's name, you can ask «Who are you?» for now:

- **Who are you?** (formal, using Ви) — Хто ви?
- **Who are you?** (informal, using ти) — Хто ти?

To respond, just use **Я** (I) plus your name:

- **I am Olena.** — Я Олена.
- **I am Taras.** — Я Тарас.

After exchanging names, say:

- **Дуже приємно!** — Pleased to meet you! (literally «very pleasant»)

Here's how a formal introduction flows:

- **— Добрий день. Хто ви?**
- **— Я Ірина. А ви?**
- **— Я Андрій. Дуже приємно!**
- **— Дуже приємно!**

And an informal one between classmates:

- **— Привіт! Хто ти?**
- **— Я Марко. А ти?**
- **— Я Софія. Дуже приємно!**

> [!practice] **Try It Out**
> Imagine you're meeting your new Ukrainian neighbor. Practice saying aloud: **Добрий день! Я ___. Дуже приємно!** Fill in your own name.

## Діалоги (Dialogues)

Let's see all your new expressions working together in real situations. Pay attention to when people use **ти** vs **Ви**, and which greetings and farewells they choose.

> **(At the university / В університеті)**

A student meets a professor for the first time.

— Добрий день! My name is Taras.
— Добрий день, Тарасе. My name is Oksana Ivanivna.
— Дуже приємно, пані Оксано!
— Nice to meet you! Welcome!
— Щиро дякую! До побачення!
— До побачення!

Notice: Taras uses formal forms — **Добрий день**, **пані Оксано**, **До побачення**. This is a formal setting.

> **(On the street / На вулиці)**

Two old friends run into each other.

— Привіт, Софіє! Як справи?
— О, привіт, Марко! Добре, дякую. А ти?
— Теж добре!
— Goodbye!
— Goodbye! На все добре!

Notice: they use **Привіт**, **ти**, and **goodbye** — all informal, because they're friends.

> **(At a bakery / У пекарні)**

A customer gets the baker's attention politely.

— Вибачте! Хліб, будь ласка.
— Будь ласка!
— Дуже дякую!
— Будь ласка! На все добре!

Notice: the customer uses **Вибачте** (formal) to get attention, then **будь ласка** when ordering.

> **(After an evening event / Після зустрічі)**

A colleague thanks the host after a work dinner.

— Щиро дякую за вечір, пане Петре!
— Будь ласка, пані Оксано! Дуже приємно!
— До побачення!
— На все добре! Добраніч!

Notice: formal address (**пане Петре**, **пані Оксано**) plus **Добраніч** because it's evening.

<!-- adapted from: Большакова, Grade 1, p.64; Загарійчук, Grade 1, p.97 -->

## Підсумок — Summary

You've taken a big step forward! You can now greet people at any time of day — from a casual **привіт** with friends to a respectful **Добрий день** with strangers. You understand the crucial **ти/Ви** distinction that shapes every Ukrainian conversation. You can say **дякую**, **будь ласка**, and **вибачте** in the right moments. You know how to introduce yourself with **My name is...** and respond with **Дуже приємно!** And you can address people properly using **пане** and **пані**.

**Self-check — can you do these?**

1. Greet someone formally at 9 AM, 3 PM, and 8 PM?
2. Explain when to use **ти** and when to use **Ви**?
3. Say «please,» «thank you,» and «excuse me» in Ukrainian?
4. Introduce yourself and ask someone's name?

If you answered yes to all four — great work! You're ready for the next module, where you'll learn personal pronouns and the powerful little word **це**.

# Activities

## Vocabulary


        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/greetings-and-politeness.md`

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
