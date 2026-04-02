<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 40: People Around Me (A1, A1.6 [Food and Shopping])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-040
level: A1
sequence: 40
slug: people-around-me
version: '1.2'
title: People Around Me
subtitle: Я бачу маму, знаю Олену — accusative for people
focus: grammar
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1200
objectives:
- Use accusative case for animate nouns (Я бачу маму, знаю Олену)
- Recognize that masculine animate accusative = genitive (бачу брата, друга)
- Distinguish animate vs inanimate accusative
- Talk about people in your daily life using accusative
dialogue_situations:
- setting: 'Showing wedding photos — identifying people: Бачиш маму (f→acc)? А тата
    (m→acc)? Знаєш Олену (f→acc)? Це мій дядько (m), а це тітка (f). Ось наречена
    (f) і наречений (m).'
  speakers:
  - Наречена
  - Друг
  motivation: 'Accusative animate: маму(f), тата(m), Олену(f), дядька(m)'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Who do you see? — Кого ти бачиш? — Я бачу маму і тата. — А хто це?
    — Це мій брат. Ти знаєш мого брата? — Ні, я не знаю твого брата. — Ходімо, я тебе
    познайомлю! Accusative animate: маму (f), тата (m), брата (m).'
  - 'Dialogue 2 — At work: — Ти знаєш нашу вчительку? — Так, я знаю Олену Петрівну.
    — А нового лікаря? — Ні, я ще не знаю лікаря. — Він дуже добрий. Я чекаю його
    зараз. Animate accusative with people around you.'
- section: Кого? (Whom?)
  words: 300
  points:
  - 'Accusative animate vs inanimate: Inanimate (M37): Я їм (що?) хліб. → no change
    for masculine. Animate (M40): Я бачу (кого?) брата. → masculine changes! The question
    word is the key: що? = inanimate (things) → masculine stays same. кого? = animate
    (people, animals) → masculine changes.'
  - 'Ukrainian school approach (Grade 4): ''Бачу кого? що?'' — two questions, two
    patterns. Кого? triggers the animate rule: masculine animate accusative = genitive
    form. брат → брата, друг → друга, тато → тата, лікар → лікаря. This is why animate
    accusative matters — it changes masculine nouns.'
- section: Знахідний відмінок — живе (Accusative Animate)
  words: 300
  points:
  - 'Feminine animate: same as inanimate (-а → -у, -я → -ю): мама → маму (Я бачу маму),
    сестра → сестру (Я знаю сестру), Олена → Олену (Я чекаю Олену), подруга → подругу
    (Я люблю подругу). No surprise — same ending as M37 (кава → каву).'
  - 'Masculine animate: accusative = genitive (THE new rule): брат → брата (Я бачу
    брата), друг → друга (Я знаю друга), тато → тата (Я люблю тата), лікар → лікаря
    (Я чекаю лікаря), вчитель → вчителя (Я знаю вчителя), сусід → сусіда (Я бачу сусіда).
    Pattern: masculine animate in accusative takes the genitive ending. Compare: Я
    бачу хліб (inanimate — no change) vs Я бачу брата (animate — changes).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Accusative summary — the full picture: | | Inanimate (що?) | Animate (кого?)
    | | Masculine | = nominative (хліб) | = genitive (брата) | | Feminine | -а → -у
    (каву) | -а → -у (маму) | | Neuter | = nominative (молоко) | (rare at A1) | Key
    verbs with animate accusative: бачити (to see), знати (to know), любити (to love),
    чекати (to wait for), шукати (to look for). Self-check: Я бачу ___ (мама → маму,
    брат → брата).'
vocabulary_hints:
  required:
  - бачити (to see)
  - знати (to know)
  - любити (to love)
  - чекати (to wait for)
  - шукати (to look for)
  - друг (friend, m)
  - подруга (friend, f)
  recommended:
  - сусід (neighbor, m)
  - колега (colleague, m/f)
  - викладач (lecturer, m)
  - вчитель (teacher, m)
  - лікар (doctor, m)
  - продавець (seller, m)
  - покупець (buyer, m)
activity_hints:
- type: fill-in
  focus: 'Я бачу ___ (nominative → accusative: мама → маму, брат → брата)'
  items:
  - Я бачу {маму|мама|мами}.
  - Я бачу {брата|брат|брату}.
  - Я знаю {Олену|Олена|Олени}.
  - Я знаю {друга|друг|другу}.
  - Я люблю {тата|тато|таті}.
  - Я чекаю {вчителя|вчитель|вчителю}.
  - Я шукаю {подругу|подруга|подруги}.
  - Я бачу {сусіда|сусід|сусіду}.
  - Я чекаю {лікаря|лікар|лікарю}.
  - Я знаю {сестру|сестра|сестри}.
- type: group-sort
  focus: 'Sort: animate (кого?) vs inanimate (що?) — changes vs stays same for masculine'
  groups:
  - name: Animate (кого?)
    items:
    - брата
    - маму
    - друга
    - лікаря
    - Олену
  - name: Inanimate (що?)
    items:
    - хліб
    - каву
    - воду
    - чай
    - борщ
- type: quiz
  focus: 'Choose correct: Я знаю (Олена / Олену / Олени)'
  items:
  - question: Я знаю ___.
    options:
    - Олену
    - Олена
    - Олени
  - question: Я бачу ___.
    options:
    - брата
    - брат
    - братом
  - question: Я люблю ___.
    options:
    - подругу
    - подруга
    - подруги
  - question: Я чекаю ___.
    options:
    - сусіда
    - сусід
    - сусідом
  - question: Я шукаю ___.
    options:
    - вчителя
    - вчитель
    - вчителю
  - question: Я знаю ___.
    options:
    - лікаря
    - лікар
    - лікарем
  - question: Я бачу ___.
    options:
    - колегу
    - колега
    - колеги
  - question: Я люблю ___.
    options:
    - тата
    - тато
    - татом
- type: fill-in
  focus: 'Complete: Я люблю ___, знаю ___, чекаю ___. (family/friends)'
  items:
  - — Кого ти {бачиш|бачити|бачить}?
  - — Я бачу {брата|брат|братом} і маму.
  - — Ти знаєш мого {друга|друг|другу} Тараса?
  - — Ні, я не {знаю|знає|знати} твого друга.
  - — А кого ти {чекаєш|чекати|чекає}?
  - — Я чекаю {лікаря|лікар|лікарем}.
connects_to:
- a1-041 (Checkpoint — Food and Shopping)
prerequisites:
- a1-039 (Shopping)
grammar:
- 'Accusative animate: feminine -а→-у (= inanimate), masculine = genitive'
- 'Animate vs inanimate distinction: кого? vs що?'
- 'Key pattern: masculine animate accusative = genitive (брат → брата)'
register: розмовний
references:
- title: ULP Season 1, Episode 33
  url: https://www.ukrainianlessons.com/episode33/
  notes: Accusative case — animate nouns.
- title: 'Grade 4 textbook: Знахідний відмінок (Заболотний)'
  notes: 'Ukrainian school approach: бачу кого? що? — animate accusative = genitive.'

</plan_content>

## Generated Content

<generated_module_content>
## Діало́ги (Dialogues)

A bride is showing wedding photos to a friend, pointing out family members and guests in the pictures.

> — **Нарече́на:** Диви́сь, це на́ше весі́лля! Ба́чиш ма́му? *(Look, this is our wedding! Do you see Mom?)*
> — **Друг:** Так, ба́чу маму. А хто це по́руч? *(Yes, I see Mom. And who is this next to her?)*
> — **Наречена:** Це та́то. Бачиш та́та? *(That's Dad. Do you see Dad?)*
> — **Друг:** Так, бачу тата! А хто це? *(Yes, I see Dad! And who is this?)*
> — **Наречена:** Це мій брат. Ти зна́єш мого бра́та? *(This is my brother. Do you know my brother?)*
> — **Друг:** Ні, я не зна́ю твого́ брата. *(No, I don't know your brother.)*
> — **Наречена:** Ході́мо, я тебе́ познайо́млю! *(Come on, I'll introduce you!)*

Notice the forms: **маму** (not ма́ма), **тата** (not тато), **брата** (not брат). Every time the bride says "do you see" or "do you know" someone, the person's name changes its ending.

Here is a second conversation — two colleagues at work:

> — **Марі́я:** Ти знаєш на́шу вчи́тельку? *(Do you know our teacher?)*
> — **Андрі́й:** Так, я знаю Оле́ну Петрі́вну. *(Yes, I know Olena Petrivna.)*
> — **Марія:** А ново́го лі́каря? *(And the new doctor?)*
> — **Андрій:** Ні, я ще не знаю лікаря. *(No, I don't know the doctor yet.)*
> — **Марія:** Він ду́же до́брий. Я чека́ю йо́го за́раз. *(He's very kind. I'm waiting for him now.)*
> — **Андрій:** До́бре, я теж чекаю Олену. *(OK, I'm also waiting for Olena.)*

Again: **вчительку** (not вчи́телька), **Олену** (not Оле́на), **лікаря** (not лі́кар). What do you notice? Every time someone talks about a person using **ба́чити** (to see), **зна́ти** (to know), or **чека́ти** (to wait for), the person's name or title changes form.

The pattern comes down to two question words: **що?** (what?) for things and **кого?** (whom?) for people. When you see or know a *person*, Ukrainian asks **кого?** — and that question triggers a special ending. This is the **знахі́дний відмі́нок** (accusative case) with animate nouns — **кого?**

## Кого? (Whom?)

When a verb takes a direct object, Ukrainian asks one of two questions. For things, you ask **що?** (what?). For people and animals, you ask **кого?** (whom?). The answer to each question follows a different pattern.

With **що?** (inanimate things), masculine nouns stay in their base form — no ending changes at all:

- Я їм **хліб** (що?) — I eat bread (хліб stays хліб)
- Я бачу **стіл** (що?) — I see the table (стіл stays стіл)
- Я п'ю **чай** (що?) — I drink tea (чай stays чай)

You already know this from Module 37 — inanimate masculine accusative equals nominative.

Now switch to **кого?** (animate — people). Watch what happens to the masculine nouns:

- Я бачу **брата** (кого?) — I see my brother (not брат!)
- Я знаю **дру́га** (кого?) — I know my friend (not друг!)
- Я чекаю **лікаря** (кого?) — I'm waiting for the doctor (not лікар!)

The contrast is stark. Compare side by side: **Я бачу хліб** — but **Я бачу брата**. **Я бачу стіл** — but **Я бачу тата**. Inanimate masculine = no change. Animate masculine = the ending changes.

This is exactly how Ukrainian schoolchildren learn it in Grade 4 (Заболо́тний): the verb **бачити** takes two questions — **кого?** for people and **що?** for things. **Кого?** triggers the animate rule: the masculine noun changes ending. **Що?** does not — masculine stays the same. The mnemonic is simple: **кого?** → the noun changes; **що?** → masculine stays.

Why does Ukrainian make this distinction? Ukrainian grammar separates all nouns into two categories: **живі́** (animate — living beings) and **неживі́** (inanimate — things). Animate nouns answer **кого?**; inanimate nouns answer **що?**. This is a deep grammatical logic — Ukrainian treats *seeing a person* differently from *seeing a thing*, not just in meaning, but in form. And the animate masculine accusative isn't random: it uses the same ending as the **родо́ви́й відмінок** (genitive case) you already learned. The accusative of **брат** is **брата** — exactly like **нема́ брата** (there is no brother). The next section shows this pattern in full.

<!-- INJECT_ACTIVITY: fill-in-animate-accusative -->

## Знахідний відмінок — живе́ (Accusative Animate)

Feminine animate nouns hold no surprises. They follow the exact same ending as inanimate feminine nouns: **-а → -у**, **-я → -ю**. You already know this from Module 37 (ка́ва → ка́ву). The same pattern applies to people:

- **мама** → **маму** (Я бачу маму) — I see Mom
- **сестра́** → **сестру́** (Я знаю сестру) — I know my sister
- **Олена** → **Олену** (Я чекаю Олену) — I'm waiting for Olena
- **по́друга** → **по́другу** (Я люблю́ подругу) — I love my friend
- **ті́тка** → **ті́тку** (Я бачу тітку) — I see my aunt
- **наречена** → **нарече́ну** (Я знаю наречену) — I know the bride

Compare: **кава → каву**, **мама → маму** — identical ending. Feminine animate accusative requires no new rule at all.

<!-- INJECT_ACTIVITY: fill-in-family-friends -->

Now the rule that matters most in this module. Masculine animate accusative equals genitive. The textbook (Карама́н, Grade 10) states it directly: *«Фо́рма знахі́дного відмі́нка однини́ чолові́чого ро́ду назв істо́т збігається з родо́ви́м однини.»* In plain terms: to form the accusative of a masculine animate noun, use its genitive form.

Here are six masculine animate nouns with their accusative (= genitive) forms:

- **брат** → **брата** (Я бачу брата) — I see my brother
- **друг** → **друга** (Я знаю друга) — I know my friend
- **тато** → **тата** (Я люблю тата) — I love Dad
- **лікар** → **лікаря** (Я чекаю лікаря) — I'm waiting for the doctor
- **вчи́тель** → **вчи́теля** (Я знаю вчителя) — I know the teacher
- **сусі́д** → **сусі́да** (Я бачу сусіда) — I see the neighbor

The connection to prior learning: **бачу брата** uses the same form as **нема брата** — the genitive ending you already know.

Now the critical contrast — animate versus inanimate masculine, side by side. **Що?** (inanimate) — no change: Я бачу **хліб**, Я бачу **стіл**, Я бачу **борщ**. **Кого?** (animate) — genitive form: Я бачу **брата**, Я бачу **тата**, Я бачу **друга**. The test you should apply every time: before writing the form, ask the question. **Кого?** → take the genitive form. **Що?** → leave masculine as is.

<!-- INJECT_ACTIVITY: group-sort-animate-inanimate -->

## Підсумок — Summary

The **знахідний відмінок** (accusative case) has two sub-patterns, determined by one question: **кого?** or **що?**

**Inanimate (що?):** Masculine stays the same — **хліб → хліб**, **стіл → стіл**. Feminine changes **-а → -у** — **кава → каву**, **вода́ → воду́**. Neuter stays the same — **молоко́ → молоко**.

**Animate (кого?):** Feminine still changes **-а → -у** — **мама → маму**, **Олена → Олену**. Masculine equals genitive — **брат → брата**, **лікар → лікаря**.

The single most important rule from this module: *Знахідний відмінок чоловічого роду живи́х істот = родовий відмінок.*

Five key verbs that take animate accusative at A1, each with a full example:

- **бачити** (to see) — Я бачу маму і тата.
- **знати** (to know) — Ти знаєш мого друга Тара́са?
- **люби́ти** (to love) — Я дуже люблю бабу́сю.
- **чекати** (to wait for) — Вона́ чека́є лікаря.
- **шука́ти** (to look for) — Ми шука́ємо на́шого сусіда.

Memorize these five verbs — they are the most common contexts where animate accusative appears in daily speech.

<!-- INJECT_ACTIVITY: quiz-accusative-animate -->

**Deterministic word count: 1242 words** (calculated by pipeline, do NOT estimate manually)

</generated_module_content>

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | DEDUCT for: motivational openers ("Numbers unlock the real Ukraine!"), meta-commentary ("Let us look at...", "Let us now explore..."), generic enthusiasm ("incredibly melodic", "hugely important"), telling instead of showing ("You now possess...", "You have unlocked..."), gamified language ("unlocked the ability"), corporate-speak ("precision and accuracy"), "The magic of...", any sentence that could apply to any language course unchanged. REWARD for: specific cultural details, natural dialogues, humor, concrete examples, teacher demonstrating rather than lecturing about how great the content is. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count outside target range, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count in range. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string must be an EXACT substring of the module content — copy-paste it
- Keep fixes minimal — change only what's wrong, preserve surrounding text
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 91 words | Not found: 37 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Андрі — NOT IN VESUM
  ✗ Андрій — NOT IN VESUM
  ✗ Діало — NOT IN VESUM
  ✗ Заболо — NOT IN VESUM
  ✗ Карама — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Оле — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Олену — NOT IN VESUM
  ✗ Петрі — NOT IN VESUM
  ✗ весі — NOT IN VESUM
  ✗ вну — NOT IN VESUM
  ✗ відмі — NOT IN VESUM
  ✗ дний — NOT IN VESUM
  ✗ дного — NOT IN VESUM
  ✗ дру — NOT IN VESUM
  ✗ знахі — NOT IN VESUM
  ✗ каря — NOT IN VESUM
  ✗ лля — NOT IN VESUM
  ✗ млю — NOT IN VESUM
  ✗ нка — NOT IN VESUM
  ✗ нок — NOT IN VESUM
  ✗ познайо — NOT IN VESUM
  ✗ рма — NOT IN VESUM
  ✗ родо — NOT IN VESUM
  ✗ руч — NOT IN VESUM
  ✗ тель — NOT IN VESUM
  ✗ телька — NOT IN VESUM
  ✗ тельку — NOT IN VESUM
  ✗ тка — NOT IN VESUM
  ✗ тку — NOT IN VESUM
  ✗ тний — NOT IN VESUM
  ✗ чити — NOT IN VESUM
  ✗ чиш — NOT IN VESUM
  ✗ шого — NOT IN VESUM
  ✗ ємо — NOT IN VESUM
  ✗ істо — NOT IN VESUM

All 91 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
