        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
             Продукція: Комунікативні сценарії (Production: Communicative Scenarios)                    249 /  250  ✅ (-1)
     З'єднуємо речення (Joining Sentences)                                                      333 /  200  ✅ (+133)
     Культурний контекст та ALF (Cultural Context and ALF)                                      161 /  125  ✅ (+36)
     ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
     TOTAL                                                                                     1613 / 1400  ✅ (+213)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2001/1200 (raw: 2133)
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
Research     ✅ Content aligned with research
Immersion    🇺🇦 22.6% (target 15-25% (M18))

📋 TEMPLATE COMPLIANCE VIOLATIONS FOUND:
  🔴 [DUPLICATE_SYNONYMOUS_HEADERS] Multiple headers contain 'Introduction': Культурний контекст та ALF (Cultural Context and ALF), Вступ: Основи заперечення та інтонації (Introduction: Basics of Negation and Intonation)
     → FIX: RENAME one header to NOT contain 'Introduction'. Example: 'Агіографічна спадщина' → 'Житійна творчість' (removes the duplicate word).


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 1 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/questions-and-negation-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/questions-and-negation.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 1 Critical Template Violations

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/questions-and-negation-audit.log for details)

Running RAG word verification...
Verifying: questions-and-negation.md
  VESUM misses: 3 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 25811.10it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 122 | VESUM: 119 (97.5%) | RAG: 1 | Not found: 2
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/questions-and-negation-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

VESUM: 136/139 (98%) verified
⚠️ VESUM not found (3): Львова, Оля, Шо
        ```

        ## Current Content of Affected Section(s)


### Question Words

Ukrainian has a clear set of question words. Here are the ones you need at A1, aligned with State Standard §4.3.1:

- **Що?** — What? → **Що це?** — What is this? **Що ти робиш?** — What are you doing?
- **Хто?** — Who? → **Хто це?** — Who is this? **Хто там?** — Who's there?
- **Де?** — Where? → **Де ти?** — Where are you? **Де туалет?** — Where is the toilet?
- **Коли?** — When? → **Коли сніданок?** — When is breakfast?
- **Куди?** — Where to? → **Куди ви їдете?** — Where are you going?
- **Звідки?** — Where from? → **Звідки ти?** — Where are you from?
- **Чому?** — Why? → **Чому ти тут?** — Why are you here?
- **Як?** — How? → **Як справи?** — How are things?
- **Скільки?** — How much/many? → **Скільки це коштує?** — How much does it cost?

> [!note] **Що vs Шо**
> The standard form is **що**. In spoken Ukrainian, you'll hear **шо** everywhere — it's completely natural and not "wrong," just informal. Use **що** in writing and formal situations, but don't be surprised when you hear **шо** on the street.

### Answering: Так vs Ні

When someone asks a **чи**-question, answer with **так** (yes) or **ні** (no). You can add a full sentence after:

- **Чи ти знаєш?** — **Так, я знаю.** / **Ні, я не знаю.**
- **Чи це молоко?** — **Так, це молоко.** / **Ні, це не молоко.**
- **Чи він вдома?** — **Так, він вдома.** / **Ні, він не вдома.**

Notice the pattern for negative answers: **Ні** + subject + **не** + verb (or noun).

## Практика: Тренування заперечень та запитань (Practice: Drilling Negation and Questions)

### Sentence Transformations

The core skill in this module is transforming sentences between three forms. Watch how each one moves through statement → negative → question:

- **Ти знаєш.** → **Ти не знаєш.** → **Чи ти знаєш?**
- **Він говорить.** → **Він не говорить.** → **Чи він говорить?**
- **Вона тут.** → **Вона не тут.** → **Чи вона тут?**
- **Це молоко.** → **Це не молоко.** → **Чи це молоко?**
- **Вони ходять.** → **Вони не ходять.** → **Чи вони ходять?**

> [!practice] **Your Turn: The Three-Step Drill**
> Pick any statement you know — like **Я студент** or **Він робить** — and practice all three forms out loud. Notice how your voice changes for each version. This drill is the fastest way to build the habit.

### The English-Transfer Trap

Here are common mistakes you might make — and how to fix them:

- ❌ *Do ти знаєш?* → ✅ **Чи ти знаєш?** (or just **Ти знаєш?** ↗)
- ❌ *Я є не студент.* → ✅ **Я не студент.**
- ❌ *Не він тут.* → ✅ **Він не тут.**

Remember: **не** goes directly before the word it negates — usually the verb, but sometimes a noun or adjective. Never put **не** at the start of the sentence.

### Question Word Matching

Pair each question word with the right situation:

- Someone knocks on the door → **Хто там?**
- You don't recognize an object → **Що це?**
- You're looking for something → **Де...?**
- You need a direction → **Куди...?**
- You want to know someone's origin → **Звідки ти?**
- You're asking about a price → **Скільки це коштує?**

## Продукція: Комунікативні сценарії (Production: Communicative Scenarios)

### The Café Scenario

> **(Кафе / Café)**
>
> — Добрий день! Де кава?
> — Ось кава, будь ласка.
> — Скільки це коштує?
> — Одна гривня.
> — Чи є цукор?
> — Так, ось цукор.
> — А чай? Чи є чай?
> — Так, є. Чай і кава.
> — Дякую!

<!-- adapted from: common communicative scenarios, Grade 3 -->

This short exchange uses three question types you've learned: **де** (location), **скільки** (price), and **чи** (yes/no availability). These are the questions you'll use most in real-life situations.

### Roleplay: The Investigative Journalist

> **(Інтерв'ю / Interview)**
>
> — Привіт! Хто ти?
> — Я студентка. Мене звати Оля.
> — Звідки ти?
> — Я зі Львова.
> — Що ти робиш тут?
> — Я тут читаю.
> — Чому?
> — Це цікава книга!

Try this yourself. Use your question word checklist — **хто, що, де, звідки, як, коли, чому** — to interview a partner, a friend, or even yourself out loud. The goal is to use every question word at least once.

### Negative Responses and Frequency

Frequency words add nuance to your sentences. Here are the key ones you need:

- **завжди** — always → **Я завжди тут.** — I'm always here.
- **часто** — often → **Я часто ходжу в парк.** — I often go to the park.
- **іноді** — sometimes → **Іноді я читаю.** — Sometimes I read.
- **ніколи** — never → **Я ніколи не...** — I never...

> [!warning] **Double Negation Is REQUIRED**
> In English, "I never eat" has one negative. In Ukrainian, you need TWO: **Я ніколи не їм.** Literally "I never not eat." This is not a mistake — it's a strict grammar rule. **Ніколи** always requires **не** before the verb.

Practice these double negations:

- **Я ніколи не сплю.** — I never sleep.
- **Він ніколи не сидить.** — He never sits.
- **Вони ніколи не ходять.** — They never walk.

## З'єднуємо речення (Joining Sentences)

You can already make statements, questions, and negations. Now let's connect your sentences with simple conjunctions — this is a big step toward sounding natural.

### І/Й (and), А (and/but), Але (but)

- **і** (after consonants) / **й** (after vowels) — connects similar ideas:
  - **Я студент, і він студент.** — I am a student, and he is a student.
  - **Вона тут, й він тут.** — She's here, and he's here.

- **а** — shows a mild contrast (softer than **але**):
  - **Я тут, а він там.** — I am here, and he is there.
  - **Вона говорить, а він слухає.** — She speaks, and he listens.

- **але** — a strong "but":
  - **Я читаю, але не часто.** — I read, but not often.
  - **Він тут, але вона не тут.** — He's here, but she's not here.

### Словник у реченнях (Vocabulary in Sentences)

Here is how we use our new words in simple sentences. Pay attention to the stress marks (´):

- **Що** (що́) це за кни́га? — **Що** там лежи́ть? (What kind of book is this? What is lying there?)
- **Хто** (хто́) це прийшо́в? — **Хто** там сту́кає? (Who is this that came? Who is there knocking?)
- **Де** (де́) мо́я ка́ва? — **Де** ви за́раз? (Where is my coffee? Where are you now?)
- **Коли́** (коли́) бу́де обі́д? — **Коли́** твій сніда́нок? (When will be lunch? When is your breakfast?)
- **Куди́** (куди́) ви сьогодні йдете́? — **Куди́** він іде́ за́раз? (Where are you going today? Where is he going now?)
- **Зві́дки** (зві́дки) ви приї́хали? — **Зві́дки** він ро́дом? (Where did you come from? Where is he from?)
- **Чому́** (чому́) ти сього́дні тут? — **Чому́** він там сиди́ть? (Why are you here today? Why is he sitting there?)
- **Бо** (бо́) це ду́же ціка́во. (Because it is very interesting.)
- **Тому́ що** (тому́ що) я за́раз студе́нт. (Because I am a student now.)
- Чи ви хо́чете пи́ти ка́ву? — **Ні** (ні́), ду́же дя́кую. (Do you want to drink coffee? No, thank you very much.)

Notice how **ні** stands alone as "no" in a response.











## Культурний контекст та ALF (Cultural Context and ALF)

### Register: When to Use Чи

Context matters. In formal situations — speaking with a teacher, a doctor, or an elder — **чи** shows respect: **Чи ви розумієте?** With friends and family, skip it and use intonation: **Ти розумієш?** ↗ Both are grammatically correct. The difference is about politeness and register, not right or wrong.

### The ALF Quote

Ukrainians love this line from the dubbed TV show ALF:

> **«Ти не спиш? Ти просто не працюєш!»**
> — You don't sleep? You just don't work!

This simple phrase packs two negations (**не спиш**, **не працюєш**), a rhetorical question with rising intonation, and a punchline that showcases Ukrainian humor. It's a perfect example of how **не** works naturally in conversation.

> [!culture] **Хто там?**
> The phrase **Хто там?** (Who's there?) is deeply embedded in Ukrainian daily life. When someone knocks on your door, this is what you say — always. You'll hear it in movies, jokes, and every apartment building in Ukraine. It's one of those phrases that instantly marks you as comfortable with the language.

# Підсумок

You've covered a lot of ground in this module. Here's what you can now do:

- **Ask yes/no questions** using **чи** or rising intonation ↗
- **Use nine question words** — **що, хто, де, коли, куди, звідки, чому, як, скільки** — to ask about anything
- **Negate any statement** with **не** directly before the verb
- **Give full negative answers**: **Ні, я не знаю.**
- **Use frequency adverbs** — **завжди, часто, іноді, ніколи** — with double negation where required
- **Connect sentences** with **і/й, а, але, бо, тому що**

### Self-Check

1. How do you turn **Ти говориш** into a yes/no question two different ways?
2. What's the difference between **ні** and **не**?
3. How do you say "I never eat fish" in Ukrainian? (Hint: you need two negatives!)
4. Which conjunction means "because" in casual speech — **бо** or **тому що**?

You're building real sentences now — questions, negations, even compound sentences with conjunctions. That's a huge step. Keep practicing these patterns, and they'll feel natural before you know it.


        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/questions-and-negation.md`

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
