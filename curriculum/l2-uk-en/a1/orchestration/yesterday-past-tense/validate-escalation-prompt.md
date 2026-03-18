        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        Auditing: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/yesterday-past-tense.md
Mode: content-only (activities deferred)
Saving log to: curriculum/l2-uk-en/a1/audit/yesterday-past-tense-audit.log


========================================
Error: No YAML frontmatter found (checked embedded and sidecar).

Critical Failures:
  • No YAML frontmatter found

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/yesterday-past-tense-audit.log for details)

Running RAG word verification...
Verifying: yesterday-past-tense.md
  VESUM misses: 12 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 411206.27it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 117 | VESUM: 105 (89.7%) | RAG: 6 | Not found: 6
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/yesterday-past-tense-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

No status JSON produced by audit
VESUM: 105/117 (90%) verified
⚠️ VESUM not found (11): Захарійчук, ЗУНР, Кравцова, лася, ли, ло, Львові, Федоров, ї, їст
        ```

        ## Current Content of Affected Section(s)

        - **Іван Федоров надрукував «Апостол» у Львові.**

That word **надрукував** is past tense. By the end of this module, you'll be forming past tense verbs yourself and telling stories about **вчора** (yesterday).

### Time expressions for the past

Before diving into verb forms, you need the time words that signal past events. Ukrainian uses the adjective **минулий** (last, past) in the genitive case — and importantly, *without* any preposition:

- **вчора** — yesterday
- **вчора зранку** — yesterday morning
- **вчора ввечері** — yesterday evening
- **минулого тижня** — last week
- **минулого місяця** — last month
- **раніше** — earlier, before

> [!warning] No preposition needed!
> English says "last week," and some learners want to add **в**: ~~в минулому тижні~~. The correct form is simply **минулого тижня** — genitive case, no preposition. The same pattern works for **минулого місяця** (last month).

With just **вчора** and a few past tense verbs, you can talk about your whole day. Let's learn how to form those verbs!

## Основи минулого часу (Grammar: Past Tense Formation)

Great news — Ukrainian past tense is simpler than present tense! In the present, you conjugate for six persons (я, ти, він, ми, ви, вони). In the past, you only match **gender** and **number**. No person endings at all.

### The formula

Take the infinitive, remove **-ти**, and add one of four endings:

| | Ending | **читати** | **робити** |
|---|---|---|---|
| він (he) | **-в** | читав | робив |
| вона (she) | **-ла** | читала | робила |
| воно (it) | **-ло** | читало | робило |
| вони (they) | **-ли** | читали | робили |

Four endings — that's it! Here are more examples with verbs you know:

- **пити** → він **пив**, вона **пила**, вони **пили**
- **спати** → він **спав**, вона **спала**, вони **спали**
- **працювати** → він **працював**, вона **працювала**

> [!tip] Quick pattern
> **Masculine** ends in **-в** (after the stem vowel).
> **Feminine** always **-ла**. **Neuter** always **-ло**. **Plural** always **-ли**.
> Just change the vowel before **-л** — easy!

### Gender agreement matters

Here's the biggest difference from English: your past tense form depends on YOUR gender. In English, "I worked" is the same for everyone. In Ukrainian:

- A man says: **Я працював у офісі.**
- A woman says: **Я працювала у офісі.**

The same applies when talking to someone using **ти**:

- To a man: **Ти читав книгу?**
- To a woman: **Ти читала книгу?**

> [!warning] Common mistake
> If you're a woman, don't say ~~Я писав~~. The correct form is **Я писала**. Always match the verb ending to the speaker's gender when using **я** or **ти**.

### Don't add бути!

English speakers sometimes want to translate "I was working" by adding **бути** (to be) before the verb. Don't do this!

- ✅ **Я працював.** — I was working. / I worked.
- ❌ ~~Я був працював.~~ — This is wrong!

Ukrainian imperfective past covers both English simple past ("I worked") and past progressive ("I was working"). One form does the work of two — that's a win for you!

The verb **бути** does have its own past tense forms, and they're very useful on their own:

- він **був** / вона **була** / воно **було** / вони **були**

Use these to say where you were or how something was:

- **Я був удома.** — I was at home. (man speaking)
- **Я була на роботі.** — I was at work. (woman speaking)
- **Було цікаво!** — It was interesting!

## Складні випадки та практика (Irregular Verbs and Practice)

Most verbs follow the pattern you just learned. But a few very common verbs have irregular past forms. Don't worry — there are only a handful, and you'll memorize them quickly with practice.

### Їсти (to eat) — irregular root

The verb **їсти** doesn't follow the regular pattern. Instead of ~~їстив~~, the root changes completely:

- він **їв** / вона **їла** / воно **їло** / вони **їли**

The root shortens from **їст-** to **ї-**, but the endings stay the same! Examples in context:

- **Він їв яблуко.** — He ate an apple.
- **Вона їла кашу зранку.** — She ate porridge in the morning.
- **Ми їли обід у ресторані.** — We ate lunch at a restaurant.

### Йти (to go) — suppletive forms

The verb **йти** (to go on foot, one direction) has completely different past tense forms:

- він **ішов** / вона **ішла** / вони **ішли**

Compare this with **ходити** (to go regularly, or there and back):

- він **ходив** / вона **ходила** / вони **ходили**

For now, remember this simple distinction:
- **ішов/ішла** = was going somewhere (one trip)
- **ходив/ходила** = went somewhere (and came back)

- **Він ішов додому.** — He was going home.
- **Вона ходила в магазин.** — She went to the store.

### Practice: masculine vs. feminine

Let's drill the gender pairs. Notice the pattern:

- він **пив** / вона **пила**
- він **дивився** / вона **дивилася**
- він **ішов** / вона **ішла**
- він **був** / вона **була**
- він **спав** / вона **спала**

Notice that **дивитися** keeps its reflexive particle **-ся** in the past tense: **дивився** (he watched), **дивилася** (she watched). The particle stays attached — it just shifts from **-ся** to **-лася** in the feminine form.

> [!culture] Two February 15ths
> February 15 is a remarkable date in Ukrainian history. In 1574, Ivan Fedorov printed the first book in Lviv. And in 1919, the Western Ukrainian People's Republic (ЗУНР) passed a law making Ukrainian the state language: **ЗУНР прийняла закон про державну мову.** Two past tense sentences — two turning points in Ukrainian culture.

Now let's see past tense in a real conversation:

> **(У кафе / At a café)**
>
> — Привіт! Що ти робив вчора?
> — Hello! What did you do yesterday?
>
> — Вчора я читав книгу вдома.
> — Yesterday I read a book at home.
>
> — А я ходила в музей. Було цікаво!
> — And I went to the museum. It was interesting!
>
> — Ти їла там?
> — Did you eat there?
>
> — Ні, я пила тільки каву.
> — No, I only drank coffee.

> **(На роботі / At work)**
>
> — Що ти робила ввечері?
> — What did you do in the evening?
>
> — Я дивилася серіал. А ти?
> — I watched a TV series. And you?
>
> — Я спав. Я був дуже дужий.
> — I slept. I was very tired.

## Підсумок: Мій день (Summary and Production)

You've made great progress! You can now describe your entire yesterday. Here's a sample:

- **Вчора зранку я пив каву.** — Yesterday morning I drank coffee.
- **Я ходив на роботу.** — I went to work.
- **Я працював у офісі.** — I worked in the office.
- **Ввечері я дивився фільм.** — In the evening I watched a movie.

> [!practice] Your turn!
> Try building your own story about yesterday. Use these question-and-answer patterns:
> - **Що ти робив/робила вчора?** — What did you do yesterday?
> - **Де ти був/була?** — Where were you?
> - **Що ти їв/їла?** — What did you eat?

### Quick reference: gender endings

Remember — match the verb to the subject's gender:

| Subject | -в | -ла | -ло | -ли |
|---|---|---|---|---|
| він / я (♂) | **був** | — | — | — |
| вона / я (♀) | — | **була** | — | — |
| воно | — | — | **було** | — |
| вони / ми | — | — | — | **були** |

### Self-check

Before moving on, make sure you can:

1. Form the past tense of any regular verb (remove **-ти**, add **-в/-ла/-ло/-ли**)
2. Choose the correct gender ending for **я** and **ти** based on the speaker's gender
3. Use **був/була/було/були** to say where you were
4. Handle irregular forms: **їв/їла** and **ішов/ішла**
5. Use time expressions **вчора**, **минулого тижня**, **раніше** — without adding a preposition

> [!tip] Ukrainian proverb
> **Що було, те минуло.** — What was, has passed. A perfect summary of the past tense — and great folk wisdom!

You can now talk about yesterday, last week, and even events from centuries ago. In the next module, you'll learn how to talk about **tomorrow** — the future tense!

<!-- adapted from: Кравцова 2021, Grade 4, p.111; Захарійчук, Grade 4, p.147 -->

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/yesterday-past-tense.md`

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
