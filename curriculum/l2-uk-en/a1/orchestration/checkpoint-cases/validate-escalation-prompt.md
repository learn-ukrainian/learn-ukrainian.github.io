        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        Auditing: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/checkpoint-cases.md
Mode: content-only (activities deferred)
Saving log to: curriculum/l2-uk-en/a1/audit/checkpoint-cases-audit.log


========================================
Error: No YAML frontmatter found (checked embedded and sidecar).

Critical Failures:
  • No YAML frontmatter found

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/checkpoint-cases-audit.log for details)

Running RAG word verification...
Verifying: checkpoint-cases.md
  VESUM misses: 1 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 415277.62it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 79 | VESUM: 78 (98.7%) | RAG: 0 | Not found: 1
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/checkpoint-cases-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

Prose-relevant failures:
  meta: Missing '## Activities' header OR activities sidecar
VESUM: 78/79 (99%) verified
⚠️ VESUM not found (1): н
        ```

        ## Current Content of Affected Section(s)

        <!-- SCOPE
Covers: Review and synthesis of Accusative case (a1-025, a1-026), Locative case (a1-013), Genitive with немає (a1-031), prepositions of place (a1-033), adjective case forms (a1-033), pronoun declension
Not covered:
  - New grammar or vocabulary
  - Direction and origin (куди/звідки expanded) → direction-and-origin
-->

# Checkpoint: Cases

> **Чому це важливо?**
>
> You've reached a milestone. Over the last several modules, you've learned three Ukrainian cases — Accusative, Locative, and Genitive — plus prepositions, adjective agreement, and pronoun forms. That's a lot of moving parts. This checkpoint brings them all together so you can see how they work as a system, spot any gaps, and feel confident before moving forward.

## Огляд (Overview)

This checkpoint follows a TTT structure — Test, Teach, Test. You'll check your skills with the Accusative, Locative, and Genitive cases, review how prepositions pair with specific cases, and practice adjective and pronoun agreement in oblique forms.

The goal here isn't to re-learn everything from scratch. You already know these pieces individually. Now it's time to combine them in real situations — ordering at a café, asking for directions, describing what's missing. Think of this as a practice run before Phase A1.4 introduces past and future tenses, where you'll need your case skills working smoothly.

Three question words will guide you through this checkpoint:

- **Де?** — Where is something? (Locative)
- **Куди?** — Where to? (Accusative)
- **Звідки?** — Where from? (Genitive)

If you can answer these three questions correctly in Ukrainian, you're in excellent shape. Let's find out.

## Навичка 1: Відмінки (Skill 1: Cases)

You've met three oblique cases so far. Here's a quick reminder of when each one fires, followed by a fresh scenario that tests all three together.

**Accusative** answers **Кого? Що?** — it marks the direct object. For inanimate nouns, masculine and neuter Accusative looks identical to Nominative. Feminine nouns shift: **-а → -у**, **-я → -ю**. For animate masculine nouns, Accusative equals Genitive.

- **Я бачу парк.** — I see a/the park. (inanimate masc. = Nominative)
- **Я бачу нову книгу.** — I see a new book. (feminine: книга → книгу)
- **Я бачу студента.** — I see a/the student. (animate masc. = Genitive)

**Locative** answers **Де?** — it marks location. It always appears after a preposition (**в/у** or **на**).

- **Книга на столі.** — The book is on the table.
- **Ми у великому місті.** — We are in a big city.

**Genitive** with **немає** answers **Чого? Кого немає?** — it marks absence.

- **Немає кави.** — There is no coffee.
- **Немає часу.** — There is no time.
- **Немає його.** — He isn't here. (lit. "there is no him")

> [!tip] **The question-word trick**
> Not sure which case to use? Ask the question. **Що ти бачиш?** → Accusative. **Де ти?** → Locative. **Чого немає?** → Genitive. The question always tells you the case.

Now try combining them. Imagine you're in a café:

> **— Де кафе?** — Where is the café?
> **— Кафе у маленькому місті.** — The café is in a small town.
> **— Я бачу маленьке кафе.** — I see a small café.
> **— Немає вільного столу.** — There's no free table.

That short exchange used all three cases. **У маленькому місті** is Locative (location), **маленьке кафе** is Accusative (direct object of бачу), and **вільного столу** is Genitive (after немає).

## Навичка 2: Прийменники (Skill 2: Prepositions)

Prepositions and cases form a system — each preposition demands a specific case. Here's the key contrast you've learned.

**Direction (Куди?) → Accusative:**

- **Я йду в парк.** — I'm going to the park.
- **Вона їде на роботу.** — She's going to work.

**Location (Де?) → Locative:**

- **Я в парку.** — I'm in the park.
- **Вона на роботі.** — She's at work.

Notice the pattern: the preposition stays the same (**в/у**, **на**), but the case changes depending on whether you mean direction or location. **Куди ти йдеш?** — Accusative. **Де ти?** — Locative.

Three more Accusative prepositions round out your toolkit:

| Preposition | Meaning | Example |
|---|---|---|
| **за** | for, in (time) | **Дякую за каву.** — Thanks for the coffee. |
| **через** | through, because of | **Йду через парк.** — I'm walking through the park. |
| **про** | about | **Книга про місто.** — A book about the city. |

> [!warning] **Don't confuse direction and location**
> **Куди ти йдеш? — Я йду в кафе.** (Accusative — movement toward)
> **Де ти? — Я в кафе.** (Locative — already there)
> Same preposition **в**, different case. The question word is your guide.

Think of preposition + case as a fixed pair. When you hear **через**, expect Accusative. When you hear **де**, expect Locative. Building these automatic associations is the key skill at this stage.

## Навичка 3: Узгодження (Skill 3: Agreement)

Cases don't just change nouns — adjectives and pronouns must follow along. This is agreement, and it's where everything clicks together.

**Adjectives in Accusative and Locative:**

| Form | Masculine | Feminine | Neuter |
|---|---|---|---|
| Nom. | **новий** парк | **нова** книга | **нове** місто |
| Acc. | **новий** парк | **нову** книгу | **нове** місто |
| Loc. | у **новому** парку | у **новій** книзі | у **новому** місті |

The same patterns work for **великий**, **красивий**, and **маленький**:

- **Я бачу красиву вулицю.** — I see a beautiful street. (Acc. fem.)
- **Ми у маленькому кафе.** — We're in a small café. (Loc. neut.)
- **Він у великому місті.** — He's in a big city. (Loc. masc.)

**Pronoun declension** follows its own pattern. Here are the forms you've learned:

| Case | я | ти | він |
|---|---|---|---|
| Nom. | я | ти | він |
| Acc./Gen. | **мене** | **тебе** | **його** |
| Loc. | на мені | на тобі | на ньому |

> [!did-you-know] **The н-prefix sound trick**
> When **його** follows a preposition, it gains an **н-** at the front: **у нього**, **від нього**, **для нього**. This happens because Ukrainian likes a consonant between a preposition and a vowel — it just sounds better. Think of it as a pronunciation shortcut, not a grammar rule. Compare: **Я бачу його** (no preposition, no н-) vs. **У нього є кава** (preposition → add н-).

Agreement chains combine everything. Watch how one noun pulls its adjective and context into the same case:

- **Я бачу нову велику книгу.** — I see a new big book. (both adjectives in Acc. fem.)
- **Ми у новій красивій кімнаті.** — We're in a new beautiful room. (both in Loc. fem.)

When you can build chains like these without hesitating, your case system is working.

## Інтеграційне завдання (Integration Task)

Time to put it all together. Here's a navigation scenario that uses all three cases, prepositions, and agreement. Read through the dialogue, then check the analysis below.

> **— Вибачте, де нова зупинка?** — Excuse me, where's the new stop?
> **— Walk через великий парк.** — Walk through the big park.
> **— Куди потім?** — Where to after that?
> **— На красиву вулицю.** — To the beautiful street.
> **— А звідки ви?** — And where are you from?
> **— Я з маленького міста.** — I'm from a small town.
> **— Немає кафе тут?** — There's no café here?
> **— Немає. Але є у мене карта.** — No. But I have a map.

Let's trace the cases: **нова зупинка** — Nominative (subject of **де**). **Через великий парк** — Accusative after **через**. **На красиву вулицю** — Accusative (direction). **З маленького міста** — Genitive (origin). **Немає кафе** — Genitive (absence). **У мене** — the pronoun **я** in a possessive construction.

> [!culture] **Navigating Ukrainian cities**
> In real life, Ukrainians use the **де/куди** contrast constantly when giving directions. **Де зупинка?** asks where the stop IS. **Куди йде автобус?** asks where the bus is GOING. English uses «where» for both — Ukrainian splits them. Mastering this distinction makes you sound natural on the streets of Kyiv or Lviv.

**Self-assessment:** Which of the three cases felt hardest in that dialogue? If Accusative feminine endings tripped you up, revisit the adjective agreement table above. If Genitive after **немає** felt uncertain, practice with more nouns: **немає хліба**, **немає молока**, **немає тебе**. If the **н-prefix** on pronouns surprised you, remember: preposition + **його/її/їх** → add **н-**.

---

# Підсумок

You've just reviewed the entire A1.3 case system in one module — Accusative for objects and direction, Locative for location, Genitive for absence, prepositions that pair with each case, and agreement across adjectives and pronouns. These aren't separate topics anymore — they're one connected system.

Before moving on to Phase A1.4, check yourself with these questions:

1. **Де книга?** (Where is the book?) — Which case does the answer use? (Locative: **Книга на столі.**)
2. **Куди ти йдеш?** (Where are you going?) — Which case does the answer use? (Accusative: **Я йду в парк.**)
3. **Чого немає?** (What is missing?) — Which case does the answer use? (Genitive: **Немає кави.**)
4. What happens to **його** after a preposition? (It becomes **нього**: **у нього**.)

If you answered all four confidently — congratulations, you're ready. If any felt shaky, revisit that skill section above. Cases are the backbone of Ukrainian grammar, and you've just proven you can handle them.

---

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/checkpoint-cases.md`

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
