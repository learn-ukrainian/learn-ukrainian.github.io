        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        Auditing: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/checkpoint-sentences.md
Mode: content-only (activities deferred)
Saving log to: curriculum/l2-uk-en/a1/audit/checkpoint-sentences-audit.log


========================================
Error: No YAML frontmatter found (checked embedded and sidecar).

Critical Failures:
  • No YAML frontmatter found

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/checkpoint-sentences-audit.log for details)

Running RAG word verification...
Verifying: checkpoint-sentences.md
  VESUM misses: 13 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 261056.27it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 106 | VESUM: 93 (87.7%) | RAG: 2 | Not found: 11
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/checkpoint-sentences-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

No status JSON produced by audit
VESUM: 93/106 (88%) verified
⚠️ VESUM not found (12): говорюють, ете, еш, имо, ите, ити, ить, иш, Києва, сь
        ```

        ## Current Content of Affected Section(s)

        <!-- SCOPE
Covers: Review and synthesis of A1.2 modules — The Living Verb I & II, Questions & Negation, Likes & Preferences, Mine & Yours, Demonstratives, What Time Is It
Not covered:
  - New grammar or vocabulary
  - Accusative case → the-accusative-i
-->

# Checkpoint: Sentences

> **Чому це важливо?**
>
> You've built real skills over the last nine modules. You can conjugate verbs, ask questions, say what you like, and point things out with possessives and demonstratives. That's a lot of Ukrainian! This checkpoint brings everything together — not as a test, but as a chance to see how far you've come before we move into cases.

## Огляд (Overview)

This checkpoint consolidates the four core skills of A1.2: verb conjugation, question formation, expressing preferences, and using possessive and demonstrative pronouns. Think of it as a tune-up before the next phase — A1.3, where you'll start working with the accusative case.

The approach is practical. Instead of re-reading rules, you'll work through real communicative tasks — the kind of things you'd actually do in Ukrainian. Ordering coffee, describing your things, asking where someone is from. Each section gives you a quick reminder, then throws you into a new scenario that combines what you know.

If something feels shaky, that's useful information. Better to spot a gap now than to discover it mid-conversation in Kyiv. There are no wrong answers here — only honest self-assessment.

By the end, you'll know exactly which skills are solid and which need another look. Ready? Let's go.

## Навичка 1: Дієслова (Skill 1: Verbs)

You've been conjugating verbs since «The Living Verb» modules. Here's a quick refresher on the two conjugation patterns, then a new scenario to put them to work.

**I conjugation** verbs like **читати** and **писати** follow the **-у/-еш/-е/-емо/-ете/-уть** pattern. **II conjugation** verbs like **говорити** follow **-ю/-иш/-ить/-имо/-ите/-ять**. The key difference shows up in the endings — especially in the third person plural.

| | **читати** (I) | **говорити** (II) |
|---|---|---|
| я | чита́ю | говорю́ |
| ти | чита́єш | гово́риш |
| він/вона | чита́є | гово́рить |
| ми | чита́ємо | гово́римо |
| ви | чита́єте | гово́рите |
| вони | чита́ють | говоря́ть |

Notice the third person plural: **читають** (-ють) vs. **говорять** (-ять). This is where learners mix up the patterns most often. If you catch yourself writing **говорюють** — stop. That's a I-conjugation ending on a II-conjugation verb.

Watch for consonant mutations too. **Писати** looks like a regular I-conjugation verb, but the stem shifts: **я пишу**, **ти пишеш**, **він пише**. The **с → ш** change happens only in conjugated forms, not in the infinitive.

> [!warning] **Common trap: 3rd person plural**
> Beginners often default to I-conjugation endings for everything. Remember: if the infinitive ends in **-ити/-іти**, it's almost always II conjugation → **-ять** (not **-ють**) in the third person plural.

Now try this scenario. Imagine you're describing what people do at a library:

- **Я читаю книгу.** — I'm reading a book.
- **Ти пишеш лист.** — You're writing a letter.
- **Вона говорить тихо.** — She speaks quietly.
- **Вони читають і пишуть.** — They read and write.

Reflexive verbs like **подобатися** and **називатися** add **-ся** (after a consonant) or **-сь** (after a vowel) to the conjugated form. You already know **подобається** — the **-ся** attaches directly to the third person singular ending.

> **Називатися** works the same way:
> - **Я називаюся Олег.** — My name is Oleh.
> - **Вона називається «Кобзар».** — It's called «Kobzar».

## Навичка 2: Питання та заперечення (Skill 2: Questions & Negation)

You've got five question words in your toolkit: **хто** (who), **що** (what), **де** (where), **куди** (where to), and **звідки** (from where). Each one opens a different door.

The pair **де** vs. **куди** trips up English speakers because English uses «where» for both. In Ukrainian, **де** asks about a static location, and **куди** asks about direction of movement:

- **Де ти?** — Where are you? (location)
- **Куди ти йдеш?** — Where are you going? (direction)
- **Звідки ти?** — Where are you from? (origin)

For yes/no questions, Ukrainian uses the particle **чи** at the start of the sentence, or simply rising intonation:

- **Чи ти читаєш?** — Are you reading?
- **Ти читаєш?** — Are you reading? (intonation only)

Negation is straightforward — put **не** directly before the verb:

- **Я не говорю англійською.** — I don't speak English.
- **Він не хоче каву.** — He doesn't want coffee.

> [!tip] **Connecting with «бо» and «тому що»**
> Both mean «because.» Use **бо** in casual speech — it's shorter and more colloquial. **Тому що** is slightly more formal. Either way, the reason clause follows:
> - **Я не читаю, бо я пишу.** — I'm not reading because I'm writing.
> - **Він не йде, тому що він хоче каву.** — He's not going because he wants coffee.

Now combine questions and negation in a mini-dialogue:

> **— Що ти хочеш?** — What do you want?
> **— Я не хочу каву. Я хочу чай.** — I don't want coffee. I want tea.
> **— Куди ти йдеш?** — Where are you going?
> **— Я йду в кафе, бо хочу їсти.** — I'm going to a café because I want to eat.

## Навичка 3: Уподобання та присвійні (Skill 3: Preferences & Possessives)

You have three ways to express what you like in Ukrainian. Each construction works differently:

1. **Мені подобається** + nominative (Dative construction — the thing liked is the subject)
2. **Я люблю** + accusative (direct object construction)
3. **Я хочу** + infinitive or accusative (desire/want)

The biggest confusion is between #1 and #2. With **подобатися**, YOU are in the dative case and the thing you like is the grammatical subject. With **люблю**, YOU are the subject:

- **Мені подобається ця книга.** — I like this book. (lit. «This book is pleasing to me.»)
- **Я люблю цю книгу.** — I love this book.
- **Я хочу читати цю книгу.** — I want to read this book.

Now let's layer in possessives and demonstratives. Remember, they must agree in gender and number with the noun:

| | Masculine | Feminine | Neuter | Plural |
|---|---|---|---|---|
| my | **мій** | **моя** | **моє** | **мої** |
| your | **твій** | **твоя** | **твоє** | **твої** |
| this | **цей** | **ця** | **це** | **ці** |
| that | **той** | **та** | **те** | **ті** |

Combine them naturally:

- **Це мій телефон.** — This is my phone.
- **Мені подобається твоя книга.** — I like your book.
- **Цей торт смачний!** — This cake is tasty!
- **Той будинок великий.** — That building is big.
- **Я хочу ці книги.** — I want these books.

> [!did-you-know] **Gender shortcuts**
> Most nouns ending in a consonant are masculine (**мій друг**, **цей стілець**). Most ending in **-а/-я** are feminine (**моя книга**, **та вулиця**). Most ending in **-о/-е** are neuter (**моє місце**, **це молоко**). These patterns hold for the vast majority of A1 vocabulary.

## Інтеграційне завдання (Integration Task)

Time to put everything together. Here's a café scene that uses all four skills — conjugation, questions, preferences, and possessives/demonstratives. Read through it, then check yourself against the skill notes below.

> **— Привіт! Де твій друг?** — Hi! Where's your friend?
> **— Він не йде, бо він пише лист.** — He's not coming because he's writing a letter.
> **— Що ти хочеш?** — What do you want?
> **— Я хочу каву. Мені подобається ця кава тут.** — I want coffee. I like the coffee here.
> **— А хто це?** — And who is that?
> **— Це моя подруга. Вона говорить українською.** — This is my (female) friend. She speaks Ukrainian.
> **— Звідки вона?** — Where is she from?
> **— Вона з Києва. Їй подобається цей торт.** — She's from Kyiv. She likes this cake.

What skills did you just see?

- **Conjugation**: пише (I conj.), йде (I conj.), хочу (irregular), говорить (II conj.), подобається (reflexive)
- **Questions**: Де? Що? Хто? Звідки? — four different question words
- **Negation + cause**: не йде, бо він пише
- **Preferences**: Я хочу каву; Мені подобається ця кава; Їй подобається цей торт
- **Possessives & demonstratives**: твій друг, моя подруга, ця кава, цей торт

> [!culture] **Café culture in Ukraine**
> Since 2022, Ukrainian has become the dominant language in cafés across Kyiv and other major cities. Ordering in Ukrainian — even with beginner-level phrases like **Я хочу каву** — is welcomed and appreciated. Your A1.2 skills are genuinely enough to navigate a real café interaction.

### Ready for A1.3?

Ask yourself these questions honestly:

1. Can you conjugate **читати**, **писати**, and **говорити** in all six persons without checking a table?
2. Do you know when to use **де** vs. **куди** vs. **звідки**?
3. Can you build a sentence with **мені подобається** without accidentally making yourself the subject?
4. Do your possessives and demonstratives match the gender of the noun?

If you answered yes to all four — congratulations, you're ready for the accusative case. If one or two feel wobbly, revisit the relevant module before moving on. There's no rush. Solid foundations make everything that comes next easier.

---

# Підсумок

You've reviewed the four pillars of A1.2: verb conjugation (I and II patterns), question formation with **хто/що/де/куди/звідки**, preference constructions (**подобається/люблю/хочу**), and possessive and demonstrative pronouns with gender agreement. These skills don't just sit side by side — they combine in every real conversation.

**Self-check:**

1. **Вони ... українською.** (говорять чи говорюють?) — They speak Ukrainian. → **говорять** (II conjugation)
2. **... ти йдеш?** (Де чи Куди?) — Where are you going? → **Куди** (direction)
3. **Мені подобається ... книга.** (цей чи ця?) — I like this book. → **ця** (feminine)
4. **Я не читаю, ... я пишу.** (бо чи де?) — I'm not reading because I'm writing. → **бо** (because)

If these felt easy — you're ready. Next stop: the accusative case in A1.3.

---

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/checkpoint-sentences.md`

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
