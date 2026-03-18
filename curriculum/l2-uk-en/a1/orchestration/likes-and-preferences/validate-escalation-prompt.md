        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
           FIX: Expand English grammar theory sections
   FIX: Learner can't read Cyrillic yet - needs more English scaffolding

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 1757/1200 (raw: 1943)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 5/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ✅ 9/10 (High)
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 25.4% HIGH (target 15-25% (M19))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [INFO] Dative case used at A1: 'Вам' (taught formally at A2)
     → FIX: No action needed — incidental dative exposure is acceptable.
  [INFO] Dative case used at A1: 'вам' (taught formally at A2)
     → FIX: No action needed — incidental dative exposure is acceptable.
  [INFO] Dative case used at A1: 'вам' (taught formally at A2)
     → FIX: No action needed — incidental dative exposure is acceptable.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 3 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/likes-and-preferences-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/likes-and-preferences.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/likes-and-preferences-audit.log for details)

Running RAG word verification...
Verifying: likes-and-preferences.md
  VESUM misses: 2 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 35757.07it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 103 | VESUM: 101 (98.1%) | RAG: 0 | Not found: 2
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/likes-and-preferences-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

Prose-relevant failures:
  lesson: 1757/1200 (raw: 1943) | immersion: 25.4% HIGH (target 15-25% (M19))
VESUM: 101/103 (98%) verified
⚠️ VESUM not found (2): бл, ться
        ```

        ## Current Content of Affected Section(s)

        > [!tip] **Quick Win**
> You can already say what is pleasing! Just pick a word you know and put it before **подобається**: **Чай подобається.** — Tea is pleasing. Try it with any noun you've learned!

Now, what happens when more than one thing is pleasing? The verb changes to match:

- Кава подобає**ться**. — Coffee is pleasing. *(one thing)*
- Квіти подобаю**ться**. — Flowers are pleasing. *(many things)*

Notice the difference: **подобається** (singular) vs **подобаються** (plural). The verb agrees with what is liked.

You can also use this construction with verbs in the infinitive form — to say an action is pleasing:

- Читати подобається. — Reading is pleasing.
- Гуляти подобається? — Is walking pleasing?
- Співати подобається. — Singing is pleasing.

> [!warning] **Common Mistake**
> English speakers often try to say ~~"Я подобаюся кава"~~ — mapping "I like coffee" word for word. This is wrong! In Ukrainian, YOU are in the Dative case (which means "to me"), and the COFFEE is the subject: **Мені подобається кава.**

<!-- adapted from: Vashulenko, Grade 3, p.5 — "Що я люблю" theme -->

## Я люблю (I love)

While **подобається** describes something that appeals to you, **люблю** is stronger and more personal. It means "I love" or "I really enjoy." And unlike **подобається**, here YOU are the subject — just like in English.

The verb **любити** belongs to the Second Conjugation. Here is the full present-tense pattern:

| Person | Singular | Plural |
|--------|----------|--------|
| 1st | я **люблю** | ми **любимо** |
| 2nd | ти **любиш** | ви **любите** |
| 3rd | він/вона **любить** | вони **люблять** |

Notice how the first person singular (**люблю**) and third person plural (**люблять**) both have **-бл-** instead of **-б-**. This is a consonant change you've seen before with Second Conjugation verbs.

After **люблю**, the object takes the Accusative form. You'll study Accusative case formally in a later module. For inanimate masculine objects, the form looks exactly like the Nominative:

- Я люблю чай. — I love tea. *(чай)*
- Він любить борщ. — He loves borshch. *(борщ)*
- Ми любимо парк. — We love the park. *(парк)*
- Вони люблять торт. — They love cake. *(торт)*

You can also use **любити** with infinitives, just like **подобається**:

- Я люблю читати. — I love reading.
- Вона любить співати. — She loves singing.
- Ми любимо гуляти. — We love walking.

> [!note] **подобається vs люблю — What's the Difference?**
> Think of it this way: **подобається** is about a reaction — something appeals to you. **Люблю** is about a feeling — you actively love or enjoy something.
>
> - Цей парк подобається. — This park is appealing. *(reaction)*
> - Я люблю цей парк. — I love this park. *(feeling)*
>
> Both are natural. Use **подобається** when you discover something pleasant. Use **люблю** for things you know you love.

## Я хочу (I want)

The verb **хотіти** (to want) is one of the most useful verbs in Ukrainian. It's also irregular — its conjugation doesn't follow the standard First or Second Conjugation patterns neatly. The good news? It's very common, so you'll memorize it quickly through use.

| Person | Singular | Plural |
|--------|----------|--------|
| 1st | я **хочу** | ми **хочемо** |
| 2nd | ти **хочеш** | ви **хочете** |
| 3rd | він/вона **хоче** | вони **хочуть** |

You can use **хочу** in two ways. First, with an infinitive — to say what you want **to do**:

- Я хочу їсти. — I want to eat.
- Я хочу піти. — I want to go.
- Вона хоче читати. — She wants to read.
- Ми хочемо гуляти. — We want to walk.

Second, with a noun — to say what you want **to have**. Just like with **любити**, the noun takes the Accusative form:

- Я хочу каву. — I want coffee.
- Ти хочеш чай? — Do you want tea?
- Він хоче борщ. — He wants borshch.
- Вони хочуть квиток. — They want a ticket.

> [!tip] **Three Constructions, Three Patterns**
> Here's your cheat sheet:
>
> | Construction | Structure | Example |
> |-------------|-----------|---------|
> | подобається | Dative + подобається + Nominative/infinitive | Мені подобається кава. |
> | люблю | Subject + люблю + Accusative/infinitive | Я люблю каву. |
> | хочу | Subject + хочу + Accusative/infinitive | Я хочу каву. |
>
> Notice: with **люблю** and **хочу**, YOU are the subject. With **подобається**, the THING you like is the subject.

How is **хочу** different from the other two? It's about desire or intention, not preference:

- Мені подобається кава. — I like coffee. *(general preference)*
- Я люблю каву. — I love coffee. *(strong, lasting feeling)*
- Я хочу каву. — I want coffee. *(right now, please!)*

> **(Кафе / Café)**
>
> — Привіт! Ви хочете каву?
> — Так, я хочу каву. Дякую!
> — А торт? Тобі подобається торт?
> — Так, дуже! Я люблю торт.
> — Добре! Смачний торт і кава.

## Порівняння (Comparing likes)

Now you have three powerful tools for talking about preferences. Let's use them in conversations! When you want to ask someone about their preferences, here are the key questions:

- Тобі подобається музика? — Do you like music?
- Ти любиш читати? — Do you love reading?
- Ви хочете каву? — Do you want coffee?
- А ти? — And you? *(informal)*
- А вам? — And you? *(formal)*

These questions are your gateway to real conversations. Let's see them in action:

> **(Парк / Park)**
>
> — Мені подобається цей парк. А тобі?
> — Так, мені також подобається. Тут дуже гарно.
> — Ти любиш гуляти?
> — Так, я люблю гуляти. А ти?
> — Я також! Мені подобається гуляти разом.

> **(Школа / School)**
>
> — Тобі подобається ця книга?
> — Ні, вона нудна. Я люблю цікаві книги.
> — А який фільм тобі подобається?
> — Мені подобаються цікаві фільми.

Notice how **цікавий** (interesting) and **нудний** (boring) help you express opinions. And the word **найкращий** (best) is perfect for talking about top preferences:

- Моя найкраща книга — це... — My best book is...
- Мій найкращий колір — синій. — My best colour is blue.
- Яка твоя найкраща музика? — What is your best music?

> [!culture] **What Ukrainians Love**
> Ukrainians love to share food and drinks with friends and family. A host will often ask **«Ви хочете чай чи каву?»** (Do you want tea or coffee?) rather than just asking what you like in general. **Борщ**, **вареники**, and **чай** are everyday favourites. Ukrainian culture is warm and hospitable. The Ukrainian proverb says: **«На колір і смак товариш не всяк»** — roughly, "Tastes differ" or "To each their own." This means everyone has their own unique taste and style. In Ukraine, people value these personal differences in food, music, and art.

Here's a longer dialogue that puts everything together:

> **(Дім / Home)**
>
> — Що ти любиш робити?
> — Я люблю читати і слухати музику.
> — Цікаво! А яка музика тобі подобається?
> — Мені подобається українська музика. А тобі?
> — Мені також! Я хочу слухати разом!
> — Добре! Ходімо!

## Практика (Practice)

Let's practise choosing the right construction. Remember:

- **Подобається** — something appeals to you (Dative + подобається)
- **Люблю** — you love or enjoy something (Subject + люблю)
- **Хочу** — you want something right now (Subject + хочу)

Try filling in the blanks in these mini-conversations:

- — ___ подобається кава? — Так, ___ подобається.  *(Answer: Тобі... мені)*
- — Ти ___ читати? — Так, я ___ читати.  *(Answer: любиш... люблю)*
- — Ви ___ чай? — Так, ми ___ чай.  *(Answer: хочете... хочемо)*

> [!practice] **Your Turn**
> Think about your own preferences. Can you say three things you like using each construction?
>
> 1. Мені подобається ___. *(something that appeals to you)*
> 2. Я люблю ___. *(something you love)*
> 3. Я хочу ___. *(something you want right now)*
>
> Now try asking a friend: **А тобі? Що ти любиш?**

Here's one final dialogue to bring it all together:

> **(Кафе / Café)**
>
> — Добрий день! Що ви хочете?
> — Я хочу каву, будь ласка. А ти?
> — Мені подобається чай. Я хочу чай.
> — Ви хочете торт? Він дуже смачний!
> — Так! Ми любимо смачний торт!

# Підсумок
Great job! You've learned three essential ways to talk about your preferences in Ukrainian. Let's celebrate what you can now do:

You can say what appeals to you with **мені подобається** — using the Dative construction where the thing you like is the subject. You can express love and enjoyment with **я люблю** — where you are the subject and the object takes the Accusative form. And you can express what you want right now with **я хочу** — followed by an infinitive or an Accusative noun.

You've also learned all seven Dative pronoun forms (**мені, тобі, йому, їй, нам, вам, їм**), how to use adjectives like **цікавий**, **нудний**, **смачний**, and **найкращий** to express opinions, and how to ask others about their preferences with **А тобі? Ти любиш...? Ви хочете...?**

**Self-check — can you do these?**

1. Say "I like music" using **подобається**.
2. Say "She loves coffee" using **любити**.
3. Say "We want to walk" using **хотіти**.
4. Ask someone "Do you like this book?" using **подобається**.

If you can do all four, you're ready to move on to the next module, where you'll learn about possessive pronouns — **mine**, **yours**, and more!

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/likes-and-preferences.md`

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
