        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        Auditing: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/demonstratives-this-that.md
Mode: content-only (activities deferred)
Saving log to: curriculum/l2-uk-en/a1/audit/demonstratives-this-that-audit.log


========================================
Error: No YAML frontmatter found (checked embedded and sidecar).

Critical Failures:
  • No YAML frontmatter found

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/demonstratives-this-that-audit.log for details)

Running RAG word verification...
Verifying: demonstratives-this-that.md
  VESUM misses: 1 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 37172.56it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 85 | VESUM: 84 (98.8%) | RAG: 1 | Not found: 0
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/demonstratives-this-that-rag-audit.md
✅ RAG verification: all words verified

No status JSON produced by audit
VESUM: 84/85 (99%) verified
        ```

        ## Current Content of Affected Section(s)

        Notice how this mirrors what you already know:

| | Possessive | Demonstrative |
|--|-----------|---------------|
| Masculine | мій | цей |
| Feminine | моя | ця |
| Neuter | моє | це |

The agreement rule is the same — look at the noun's gender, then pick the matching form. You've done this before with adjectives and possessives, so you're already ahead!

- **Цей стілець** новий. — This chair is new.
- **Ця вулиця** гарна. — This street is nice.
- **Це озеро** велике. — This lake is big.
- **Цей будинок** старий. — This building is old.
- **Ця дівчина** — студентка. — This girl is a student.

[!tip] **Gender shortcut**
If you remember the gender of a noun from its ending, you already know which demonstrative to use: consonant ending → **цей**, -а/-я ending → **ця**, -о/-е ending → **це**.

### The Two Lives of Це

Here's a critical distinction. You've been using **це** since your very first modules — in sentences like **Це кіт** (This is a cat). That **це** is a copula — it means "this is." But now you're meeting **це** as a demonstrative pronoun modifying a neuter noun.

Compare these two sentences carefully:

- **Це кафе.** — This is a café. (What is it? → It's a café.)
- **Це кафе** гарне. — This café is nice. (Which café? → This one.)

In the first sentence, **це** stands alone — it's the subject, pointing at something and identifying it. In the second, **це** sits before **кафе** and describes which café you mean — it's working as a demonstrative, and the sentence continues with an adjective.

Here's how to tell them apart:

- **Це** + noun + period = copula ("This is a...")
- **Це** + noun + continues = demonstrative ("This particular...")

> **(У кафе / At a café)**
>
> — Це кафе?
> — Так, це кафе. Це кафе дуже гарне!
> — А це місто велике?
> — Так. Це місто — Львів.

[!warning] **Common mistake**
Don't use **це** for all genders! English speakers often say *це хлопець* instead of **цей хлопець**, because English "this" never changes. Always check the noun's gender first.

## Ці (These)

When a noun is plural, all three gender forms collapse into one: **ці** (these). No matter whether the singular was **цей**, **ця**, or **це** — the plural is always **ці**.

| Singular | Plural |
|----------|--------|
| **цей** стілець (this chair) | **ці** стільці (these chairs) |
| **ця** книга (this book) | **ці** книги (these books) |
| **це** місто (this city) | **ці** міста (these cities) |

This is actually good news — one form for all plurals! Here are some examples:

- **Ці** студенти говорять добре. — These students speak well.
- **Ці** будинки нові. — These buildings are new.
- **Ці** вулиці гарні. — These streets are nice.
- **Ці** озера великі. — These lakes are big.

[!warning] **Watch out for number mismatch**
A common beginner error is using a singular demonstrative with a plural noun: *цей книги* instead of **ці книги**. Your strategy: if you see -и, -і, or -а on the noun (plural endings), you need **ці** — no exceptions.

Think of it this way: singular nouns get a gender-specific form (**цей/ця/це**), but plural nouns all share one form (**ці**). Simple!

## Той/та/те/ті (That/Those)

Now let's look across the room. When something is farther away, Ukrainian uses a separate set of demonstratives: **той/та/те/ті** (that/those).

The gender agreement works exactly the same way:

| Gender | That | Example |
|--------|------|---------|
| Masculine | **той** | **той будинок** — that building |
| Feminine | **та** | **та вулиця** — that street |
| Neuter | **те** | **те озеро** — that lake |
| Plural | **ті** | **ті люди** — those people |

- **Той** стілець старий. — That chair is old.
- **Та** дівчина — моя подруга. — That girl is my friend.
- **Те** місто далеко. — That city is far.
- **Ті** книги цікаві. — Those books are interesting.
- **Той** хлопець — студент. — That guy is a student.

Here's the full picture — both sets side by side:

| | This (close) | That (far) |
|--|-------------|------------|
| Masculine | **цей** | **той** |
| Feminine | **ця** | **та** |
| Neuter | **це** | **те** |
| Plural | **ці** | **ті** |

[!note] **Pattern recognition**
Notice how the "that" forms are shorter and simpler: **той, та, те, ті** — all start with **т** and are just one syllable. The "this" forms **цей, ця, це, ці** all start with **ц**. This makes them easy to keep apart.

### The Double Life of Та

Here's something tricky. The word **та** has two completely different jobs in Ukrainian:

1. **та** = "that" (feminine demonstrative) — **Та дівчина** гарна.
2. **та** = "and" (conjunction, like **і**) — Хлопець **та** дівчина.

Sometimes both appear in the same sentence:

- **Та** дівчина **та** її подруга тут. — That girl and her friend are here.

The first **та** means "that" (it comes before a noun and describes it). The second **та** means "and" (it connects two things). Context makes it clear — if **та** sits right before a noun and acts like "which one?", it's a demonstrative. If it connects two nouns or phrases, it's a conjunction.

[!tip] **Quick test for та**
Can you replace **та** with **і** (and)? If yes, it's a conjunction. If no, it's a demonstrative.
- Та дівчина → *і дівчина*? No → demonstrative ✓
- Дівчина та хлопець → дівчина і хлопець? Yes → conjunction ✓

## Цей vs Той у контексті (This vs That in context)

The core difference between **цей** and **той** is distance — physical or conversational.

### Spatial Distance

When you're pointing at things, **цей** means "here, close to me" and **той** means "over there, farther away." Imagine you're at a market:

> **(На ринку / At the market)**
>
> — Я хочу **цей** торт. *(pointing at the one nearby)*
> — **Цей** торт? Він дуже смачний!
> — А **той** торт великий? *(pointing at one farther away)*
> — **Той**? Так, він великий і дорогий.

> **(У кімнаті / In the room)**
>
> — **Цей** стілець зручний.
> — А **той** стілець?
> — **Той** старий, але добрий.
> — Я люблю **цю** кімнату!

In each case, **цей/ця/це** refers to what's near the speaker, and **той/та/те** refers to what's farther away. This is natural and intuitive — just like pointing and saying "this one... no, that one!"

### Conversational Distance

Beyond physical space, **цей** and **той** also work for conversational reference. When you just mentioned something, use **цей** (this, the one I just said). When referring back to something mentioned earlier, use **той** (that, the one from before):

- Я бачу **такий** великий будинок! **Цей** будинок новий. — I see such a big building! This building is new. *(just mentioned)*
- Ми говорили про **інший** будинок. **Той** будинок старий. — We were talking about a different building. That building is old. *(mentioned earlier)*

[!practice] **Try it yourself**
Look around the room you're in right now. Pick three objects and describe each one: **цей/ця/це ___** for things within arm's reach, and **той/та/те ___** for things across the room. Say each phrase out loud — your Ukrainian is becoming more natural with **кожний** новий крок (every new step)!

## Практика (Practice)

Time to put everything together! You've learned eight demonstrative forms and the key distinctions between them. Let's practice.

### Gender Agreement Drill

Choose the correct demonstrative for each noun:

- ___ книга (this) → **ця** книга (feminine)
- ___ будинок (that) → **той** будинок (masculine)
- ___ озеро (this) → **це** озеро (neuter)
- ___ стільці (these) → **ці** стільці (plural)
- ___ вулиця (that) → **та** вулиця (feminine)
- ___ торт (this) → **цей** торт (masculine)

### Proximity Contrast

Pair up items by distance:

- **Цей** стілець новий, а **той** стілець старий.
- **Ця** книга цікава, а **та** книга нудна.
- **Це** кафе гарне, а **те** кафе маленьке.
- **Ці** будинки нові, а **ті** будинки старі.

[!challenge] **Spot the demonstrative!**
Read this mini-text and identify each demonstrative — is it "this/these" or "that/those"?

Цей хлопець — мій друг. Він любить ці книги. Та дівчина — його подруга. Вона сама читає ті книги. Це місто гарне!

*(Answer: цей = this, ці = these, та = that, ті = those, це = this)*

# Підсумок
Great work! You can now point out anything in Ukrainian — near or far, singular or plural. Here's what you've mastered:

- **Цей/ця/це** for "this" (matching gender) and **ці** for "these"
- **Той/та/те** for "that" (matching gender) and **ті** for "those"
- The difference between **це** as a copula ("This is...") and **це** as a demonstrative ("This thing...")
- How to tell **та** the demonstrative from **та** the conjunction
- Using proximity to choose between **цей** and **той**

**Self-check — can you do these?**

1. Your friend points at a building far away and asks what it is. How do you say "That building is old"?
2. You're holding a book. How do you say "This book is interesting"?
3. Someone says **«Та дівчина та її подруга»** — which **та** means "that" and which means "and"?
4. You see several nice streets. How do you say "These streets are nice"?

*(Answers: 1. Той будинок старий. 2. Ця книга цікава. 3. First та = "that," second та = "and." 4. Ці вулиці гарні.)*

You're ready for the next module, where you'll learn numbers and money — and you'll use **ці** and **ті** to point at the things you're counting! Keep going — you're doing wonderfully.

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/demonstratives-this-that.md`

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
