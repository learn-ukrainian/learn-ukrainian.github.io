        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        Auditing: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/what-time-is-it.md
Mode: content-only (activities deferred)
Saving log to: curriculum/l2-uk-en/a1/audit/what-time-is-it-audit.log


========================================
Error: No YAML frontmatter found (checked embedded and sidecar).

Critical Failures:
  • No YAML frontmatter found

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/what-time-is-it-audit.log for details)

Running RAG word verification...
Verifying: what-time-is-it.md
  VESUM misses: 6 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 135737.99it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 121 | VESUM: 115 (95.0%) | RAG: 2 | Not found: 4
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/what-time-is-it-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

No status JSON produced by audit
VESUM: 115/121 (95%) verified
⚠️ VESUM not found (5): Загарійчук, Одесу, роботаю, роботаєш, Укрзалізниця
        ```

        ## Current Content of Affected Section(s)

        - **За́раз дру́га.** — It's two (o'clock).
- **За́раз деся́та.** — It's ten (o'clock).

### Adding Minutes: Telegraphic Style

The simplest way to say minutes is the "telegraphic style" — just say the hour number followed by the minutes. This is what you'll see on train schedules and phone screens:

- **во́сьма три́дцять** — 8:30
- **дев'я́та п'ятна́дцять** — 9:15
- **деся́та со́рок п'я́ть** — 10:45

This style is perfectly natural and widely used. At A1, this is all you need for minutes.

> [!tip] Pro Tip
> You may hear **пів** (half) in expressions like **пів на дев'я́ту** (half to the ninth = 8:30). Don't worry about this pattern yet — the telegraphic style will get you through any conversation.

Let's see a quick dialogue using times with minutes:

> **(Перо́н / Platform)**
>
> — О ко́трій по́їзд на Ки́їв?
> — О деся́тій три́дцять.
> — Дя́кую! А за́раз котра́ годи́на?
> — За́раз деся́та п'ятна́дцять.

You're doing great! Now let's move on to days and months.

## Дні та місяці (Days and Months)

### Days of the Week

Ukrainian has seven days — **дні ти́жня** (days of the week). Here they are, starting from Monday, as is standard in Ukraine:

| Day | Ukrainian | Gloss |
|-----|-----------|-------|
| Monday | понеді́лок | after Sunday (неділя) |
| Tuesday | вівто́рок | the second (day) |
| Wednesday | середа́ | the middle |
| Thursday | четве́р | the fourth |
| Friday | п'я́тниця | the fifth |
| Saturday | субо́та | rest day |
| Sunday | неді́ля | no-work day |

> [!warning] False Friend Alert
> **Неді́ля** means **Sunday**, NOT "week"! The word for "week" is **ти́ждень**. This trips up many learners, so remember: **неді́ля** = Sunday, **ти́ждень** = week.

To say "on Monday," "on Tuesday," etc., Ukrainian uses **у/в** + the day name. Treat these as fixed phrases — just memorize them as chunks:

- **у понеді́лок** — on Monday
- **у вівто́рок** — on Tuesday
- **у сере́ду** — on Wednesday
- **у четве́р** — on Thursday
- **у п'я́тницю** — on Friday
- **у субо́ту** — on Saturday
- **у неді́лю** — on Sunday

> [!note] Why Do the Endings Change?
> You might notice that **середа** becomes **у сере́ду**, and **субо́та** becomes **у субо́ту**. These are Accusative case forms — but don't worry about the grammar label right now. Just learn each "on + day" phrase as a unit. The pattern will make more sense when you study cases in detail later.

A conductor checking the schedule might say:

> **(Вокза́л / Station)**
>
> — Ко́ли по́їзд на Оде́су?
> — У понеді́лок і в середу.
> — А у п'я́тницю?
> — Ні, у п'я́тницю по́їзд не хо́дить.

### Months and Seasons

Ukrainian has twelve months — **двана́дцять мі́сяців**. Unlike English, months are always written in **lowercase** in Ukrainian. They group naturally into four seasons:

**Зима́ (Winter):**
- гру́день — December
- сі́чень — January
- лю́тий — February

**Весна́ (Spring):**
- бе́резень — March
- кві́тень — April
- тра́вень — May

**Лі́то (Summer):**
- че́рвень — June
- ли́пень — July
- се́рпень — August

**О́сінь (Autumn):**
- ве́ресень — September
- жо́втень — October
- листопа́д — November

> [!culture] Ukrainian Months Tell a Story
> Ukrainian month names come from nature, not Latin emperors. **Бе́резень** (March) comes from **бере́за** (birch tree) — birch sap starts flowing. **Ли́пень** (July) comes from **ли́па** (linden tree) — it blooms in summer. **Листопа́д** (November) literally means "leaf-fall." These names connect you to the Ukrainian landscape.

To say "in January," "in March," etc., use **у/в** + the Locative form of the month:

- **у сі́чні** — in January
- **у лю́тому** — in February
- **у бе́резні** — in March
- **у кві́тні** — in April
- **у тра́вні** — in May
- **у че́рвні** — in June
- **у ли́пні** — in July
- **у се́рпні** — in August
- **у ве́ресні** — in September
- **у жо́втні** — in October
- **у листопа́ді** — in November
- **у гру́дні** — in December

> [!tip] Lowercase Rule
> In English you write "January" with a capital letter. In Ukrainian, months and days of the week are always lowercase: **сі́чень**, **понеді́лок**. Only capitalize them at the start of a sentence.

Here's how months come up in conversation:

- **У сі́чні хо́лодно.** — It's cold in January.
- **У ли́пні те́пло.** — It's warm in July.
- **Но́вий рі́к — пе́рше сі́чня.** — New Year is January first.

## Практика та розклад (Practice and Schedule)

### 12-Hour vs. 24-Hour Format

Ukrainian uses two systems for telling time, depending on the situation:

**Official (24-hour)** — for train schedules, announcements, digital clocks:
- **чотирна́дцята годи́на** — 14:00 (2 PM)
- **двадця́та три́дцять** — 20:30 (8:30 PM)

**Colloquial (12-hour)** — for everyday conversation with friends and family:
- **дру́га годи́на дня** — 2 PM (second hour of the day)
- **во́сьма годи́на ве́чора** — 8 PM (eighth hour of the evening)

The day divides into four parts:

- **ра́нок** (morning) — roughly 6:00–12:00
- **де́нь** (day/afternoon) — roughly 12:00–18:00
- **ве́чір** (evening) — roughly 18:00–22:00
- **ніч** (night) — roughly 22:00–6:00

So in casual speech, you'd clarify which part of the day:

- **Дев'я́та ра́нку.** — 9 in the morning.
- **Тре́тя дня.** — 3 in the afternoon.
- **Сьо́ма ве́чора.** — 7 in the evening.

### Prepositions for Planning

Three prepositions help you build a schedule:

| Preposition | Meaning | Example |
|-------------|---------|---------|
| **о** | at | **о дев'я́тій** — at nine |
| **до** | until / before | **до п'я́тої** — until five |
| **пі́сля** | after | **пі́сля шо́стої** — after six |

Let's put it all together with a conductor's daily **ро́зклад** (schedule):

> **(Ро́зклад провідни́ці / Conductor's schedule)**
>
> — О ко́трій ти робо́таєш у понеді́лок?
> — Вра́нці, о во́сьмій.
> — А до ко́трої?
> — До п'я́тої ве́чора.
> — А у субо́ту?
> — У субо́ту я не робо́таю. Вихідни́й де́нь!

> [!practice] Your Turn!
> Try building your own schedule. Think about your week: **О ко́трій** do you wake up? What do you do **у понеді́лок**? **У субо́ту**? Use the patterns from this module to describe a typical day.

Let's see how all the pieces fit together — time, day, and month in one sentence:

- **По́їзд у понеді́лок о деся́тій.** — The train is on Monday at ten.
- **У ве́ресні шко́ла.** — School is in September.
- **Я робо́таю до п'я́тої.** — I work until five.

> [!note] Remember
> You don't need to be perfect. Ukrainians will understand you even if your endings aren't quite right. The important thing is to try. You already know numbers, and now you can use them with time — that's real progress!

# Підсумок
You've covered a lot of ground in this module. You can now:

- Ask for the time: **«Котра́ годи́на?»** and **«О ко́трій?»**
- Tell the hour using feminine ordinal numbers: **пе́рша, дру́га, тре́тя...**
- Add minutes in telegraphic style: **во́сьма три́дцять**
- Name all seven **дні ти́жня** and say "on Monday" — **у понеді́лок**
- Name all twelve **мі́сяці** and say "in January" — **у сі́чні**
- Use **о** (at), **до** (until), and **пі́сля** (after) for planning
- Distinguish official 24-hour time from colloquial 12-hour time

Self-check — can you answer these?

1. How do you politely ask a stranger for the time?
2. What's the difference between **«Котра́ годи́на?»** and **«О ко́трій?»**
3. How do you say "on Wednesday" and "in March" in Ukrainian?
4. Is it **«два годин»** or **«дру́га годи́на»** for "It's two o'clock"?

If you answered all four, you're ready to catch any train in Ukraine — **вча́сно**!

<!-- adapted from: Загарійчук, Grade 4, pp. 85–86, 117 -->

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/what-time-is-it.md`

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
