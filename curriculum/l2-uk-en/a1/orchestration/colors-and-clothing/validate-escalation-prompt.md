        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        Auditing: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/colors-and-clothing.md
Mode: content-only (activities deferred)
Saving log to: curriculum/l2-uk-en/a1/audit/colors-and-clothing-audit.log


========================================
Error: No YAML frontmatter found (checked embedded and sidecar).

Critical Failures:
  • No YAML frontmatter found

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/colors-and-clothing-audit.log for details)

Running RAG word verification...
Verifying: colors-and-clothing.md
  VESUM misses: 3 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 48770.98it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 77 | VESUM: 74 (96.1%) | RAG: 2 | Not found: 1
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/colors-and-clothing-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

No status JSON produced by audit
VESUM: 74/77 (96%) verified
⚠️ VESUM not found (3): ий, штан, ій
        ```

        ## Current Content of Affected Section(s)


Here's how it works with different genders:

- **червоний светр** — red sweater (masculine: -ий)
- **червона сорочка** — red shirt (feminine: -а)
- **червоне плаття** — red dress (neuter: -е)

> [!tip]
> **Quick Gender Check**
>
> Look at the noun ending: **-а/-я** → feminine → color ends in **-а/-я**. Consonant → masculine → color ends in **-ий/-ій**. **-о/-е/-я** (neuter) → color ends in **-е/-є**. You already know these patterns from Module 11!

### Синій — The Odd One Out

Five of the six colors follow the hard-stem pattern (-ий/-а/-е/-і). But **синій** (blue) is a soft-stem adjective: **-ій/-я/-є/-і**. Notice the difference:

- Masculine: **жовтий**, Feminine: **жовта**, Neuter: **жовте**, Plural: **жовті** (hard stem)
- Masculine: **синій**, Feminine: **синя**, Neuter: **синє**, Plural: **сині** (soft stem)

The Ukrainian **прапор** (flag) gives you a perfect way to remember this. The flag has two stripes:

- **синє небо** — blue sky (neuter, soft: -є)
- **жовте поле** — yellow field (neuter, hard: -е)

Both are neuter nouns, but the endings on the colors differ: **синє** vs. **жовте**. That's how you know **синій** is special.

> [!warning]
> **Don't Mix Up Soft and Hard!**
>
> - ❌ ~~синя сорочка~~ ... wait, this IS correct! The feminine form is **синя**, while the masculine is **синій**.
> - ❌ ~~синьа сорочка~~ — no such form exists.
> - ✅ **синя сорочка** — blue shirt. Trust the pattern: **-ій → -я → -є → -і**.

### Незмінювані кольори — Invariable Loan Colors

Some color words borrowed from other languages never change their form. No matter the gender of the noun, these colors stay the same:

- **сукня бордо** — burgundy dress (F)
- **светр бордо** — burgundy sweater (M)
- **плаття бордо** — burgundy dress (N)

The same applies to **беж** (beige) and **хакі** (khaki). These loan colors follow the noun instead of coming before it. Don't add endings to them — that's a common beginner mistake.

---

## Одяг — Clothing Vocabulary

### П'ять основних речей — Five Core Items

Let's learn the essential clothing words. Each one has a gender, and that gender determines how you describe it with a color.

**Сорочка** (shirt, F) — the most culturally loaded clothing word in Ukrainian. A **вишита сорочка** (embroidered shirt) is the **вишиванка** you learned about above. In everyday life, **біла сорочка** (white shirt) is common formal wear.

**Штани** (pants) — always plural in Ukrainian. There is no singular form. You say **нові штани** (new pants), never ~~новий штан~~.

**Сукня** (dress, F) — the more elegant, formal word for a dress. You'll see it in descriptions of special occasions: **червона сукня** (red dress), **нова сукня** (new dress).

**Куртка** (jacket, F) — everyday outerwear. **Тепла куртка** (warm jacket), **чорна куртка** (black jacket).

**Светр** (sweater, M) — the masculine noun in the group. **Синій светр** (blue sweater), **зелений светр** (green sweater).

<!-- adapted from: Kravtsova, Grade 4, p.18 — штани etymology -->

### Описуємо одяг — Describing Clothing

You don't need verbs to describe clothing. Use the adjective + noun pattern you already know:

- **червона сукня** — a red dress
- **синій светр** — a blue sweater
- **білі штани** — white pants
- **чорна куртка** — a black jacket
- **зелена сорочка** — a green shirt

Now with all three genders side by side:

- **чорний светр** — black sweater (M: -ий)
- **чорна куртка** — black jacket (F: -а)
- **чорне плаття** — black dress (N: -е)

> [!practice]
> **Your Turn — Say It Out Loud!**
>
> Look around you. Pick one item of clothing you're wearing. What **колір** (color) is it? Try to say it in Ukrainian. For example: **Це біла сорочка.** or **Це сині штани.**

### Плаття vs. Сукня — Two Words for "Dress"

Ukrainian has two words for "dress." **Сукня** is the more elegant, literary choice. **Плаття** is the everyday, conversational word. Both are correct. The key difference for you as a learner: **сукня** is feminine (-а ending), while **плаття** is neuter (-е/-я ending). This affects which color form you use:

- **червона сукня** — red dress (F: -а)
- **червоне плаття** — red dress (N: -е)

Same item, different grammar!

### Pluralia Tantum — Always Plural

Some clothing words exist only in plural form. You've already met **штани** (pants). Two more:

**Джинси** (jeans) — always plural, just like **штани**:
- **сині джинси** — blue jeans
- **нові джинси** — new jeans

**Окуляри** (glasses) — also always plural:
- **великі окуляри** — big glasses
- **чорні окуляри** — black glasses

With these words, use the special pronoun **одні** (one pair of) instead of "один":

- ❌ ~~один штани~~ or ~~одна штани~~
- ✅ **одні штани** — one pair of pants
- ✅ **одні джинси** — one pair of jeans
- ✅ **одні окуляри** — one pair of glasses

The adjective always takes the plural form (-і): **сині джинси**, **чорні окуляри**, **білі штани**.

> [!note]
> **Pluralia tantum** means "plural only." English has these too — "pants," "jeans," "glasses" are always plural. Ukrainian works the same way here. The demonstrative is **ці** (these): **ці штани**, **ці джинси**, **ці окуляри**.

---

## Практичне застосування — Describing Outfits

### Описуємо людей — Describing What People Wear

You can describe someone's outfit using simple verb-free patterns. You already know **це** (this is) — combine it with a color and a clothing item:

- **Це червона сукня.** — This is a red dress.
- **Ці штани — сині.** — These pants are blue.
- **Мій светр — зелений.** — My sweater is green.
- **Це біла сорочка.** — This is a white shirt.
- **Ця куртка — чорна.** — This jacket is black.

Notice two patterns here. In the first pattern, the adjective comes before the noun: **червона сукня**. In the second pattern, the adjective comes after with a dash: **штани — сині**. Both are natural in Ukrainian.

> **(У крамниці / At a shop)**
>
> — Ця сорочка — біла.
> — А ця?
> — Ця сорочка — синя.
> — Гарна! А ці штани?
> — Ці штани — чорні.

> **(На вулиці / On the street)**
>
> — Це твоя куртка?
> — Так, це моя куртка. Вона зелена.
> — А мій светр — жовтий!

### Вишиванка за регіонами — Regional Styles

Different regions of Ukraine have distinctive **вишиванка** styles. You can describe them with what you've learned:

- **Це традиційна сорочка.** — This is a traditional shirt.
- **Ця вишиванка — червона й чорна.** — This vyshyvanka is red and black. (Central Ukraine: Poltava, Kyiv region)
- **Ця вишиванка — біла й синя.** — Wait — that's wrong! Let's fix it: **Ця вишиванка — біла й синя.** (Western Ukraine: Volyn, Zakarpattia)

The color must agree with **вишиванка** (feminine), not with the pattern itself. You're describing the shirt, so use feminine forms.

> [!challenge]
> **Загадка — Riddle**
>
> Here's a folk-style riddle using only colors and nouns — no verbs needed:
>
> A riddle: *«Червоне, але не сонце. Жовте, але не лимон. Синє, але не небо.»*
>
> (Red, but not the sun. Yellow, but not a lemon. Blue, but not the sky.)
>
> Can you guess? It's the Ukrainian **прапор** and a field of poppies! The point isn't the answer — it's that you can now read and understand color descriptions in Ukrainian. Great job!

---

## Підсумок — Summary

You've made real progress! Here's what you can now do:

You already know six colors — **білий**, **чорний**, **червоний**, **синій**, **зелений**, **жовтий** — and how their endings change for masculine, feminine, neuter, and plural nouns. You know five clothing items — **сорочка**, **штани**, **сукня**, **куртка**, **светр** — plus **плаття**, **джинси**, and **окуляри**. You understand that **синій** is a soft-stem adjective with different endings from the others. You can handle invariable loan colors like **бордо**, **беж**, and **хакі**. And you know that **штани**, **джинси**, and **окуляри** are always plural — paired with **одні**, not ~~один~~.

**Self-check — can you do these?**

1. Say "blue jeans" in Ukrainian with correct agreement.
2. What is the feminine form of **жовтий**?
3. Describe a black jacket: **Це _____ куртка.**
4. Why does **сукня бордо** have no ending on "бордо"?

If you can answer all four, you're ready for the next module on plurals. Don't worry if **синій** still feels tricky — you'll see it again and again. Take your time, and remember: every Ukrainian word you learn opens a window into a rich and beautiful culture.

**Want more practice?** Listen to Ukrainian Lessons Podcast Episode 25 for color pronunciation, or Episode 32 for clothing and shopping vocabulary.
> [!tip]
> **Check Your Stem!**
> Most colors end in **-ий**, but **синій** ends in **-ій**. This small difference means it uses **-я**, **-є**, and **-і** for other forms. Always check if the color is "hard" or "soft" before adding the ending!

> [!example]
> **Моя улюблена вишиванка (My Favorite Vyshyvanka)**
> - Це моя нова вишиванка. (This is my new vyshyvanka.)
> - Вона біла, червона й чорна. (It is white, red, and black.)
> - Цей одяг — мій улюблений! (I love this clothing very much!)

> [!cultural-note]
> **Кольори Прапора (Colors of the Flag)**
> The Ukrainian flag represents a blue sky (**синє небо**) over a yellow field of wheat (**жовте поле**). These two colors became the national symbol in 1848 and were officially restored in 1991 when Ukraine became independent.


        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/colors-and-clothing.md`

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
