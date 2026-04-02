<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 34: Where From? (A1, A1.5 [Places])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-034
level: A1
sequence: 34
slug: where-from
version: '1.2'
title: Where From?
subtitle: Звідки ти? Я з України — origins and directions
focus: communication
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Ask and answer Звідки? (Where from?) using з/із + country/city
- Name Ukrainian cities and common countries
- Complete the location trio: Де? / Куди? / Звідки?
- Talk about origins, nationality, and travel history
dialogue_situations:
- setting: 'International student mixer at a Kyiv university — sharing origins: Я
    з Канади, Вона з Японії, Він з Німеччини. Also: З якого міста? З Торонто, з Токіо,
    з Берліна.'
  speakers:
  - Кілька студентів (group)
  motivation: 'Звідки? + з: Канада(f), Японія(f), Німеччина(f), Торонто(n)'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Meeting someone (extending M05, ULP Ep4): — Звідки ти? — Я з України,
    з Києва. А ти? — Я з Канади, із Торонто. — Давно тут? — Ні, я приїхав місяць тому.
    Звідки? pattern with countries and cities.'
  - 'Dialogue 2 — Coming from somewhere: — Звідки ти йдеш? — Я йду з роботи. — А Олена?
    — Вона йде зі школи. — Куди вона йде? — Додому. Direction FROM (з + genitive chunk)
    vs TO (в/на + accusative).'
- section: Звідки? (Where From?)
  words: 300
  points:
  - 'Three direction questions complete: Де ти? — В Україні. (locative — where you
    ARE) Куди ти їдеш? — В Україну. (accusative — where you''re GOING) Звідки ти?
    — З України. (genitive — where you''re FROM) At A1: learn з + country/city as
    chunks. Genitive grammar = A2.'
  - 'Pattern: з/із/зі + genitive (memorized forms): з України, з Києва, зі Львова,
    з Одеси, з Харкова. з Канади, зі США (зі Штатів), з Англії, з Німеччини, з Польщі.
    з роботи, зі школи, з магазину, з банку. Note: euphony rules from M28 apply: з/із/зі.'
- section: Країни і міста (Countries and Cities)
  words: 300
  points:
  - 'Ukrainian cities: Київ (Kyiv), Львів (Lviv), Одеса (Odesa), Харків (Kharkiv),
    Дніпро (Dnipro), Запоріжжя (Zaporizhzhia). Countries (common for learners): Україна,
    Канада, США, Англія, Німеччина, Польща, Франція, Італія, Японія.'
  - 'Nationality and language links: Я з України → Я українець/українка → Я говорю
    українською. Review from M05: Мене звати..., Я з..., Я говорю... New: Я живу в
    Києві, але я зі Львова. (current location vs origin)'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Three location questions: Де? → в/на + locative (В Україні) Куди? → в/на + accusative
    (В Україну) Звідки? → з/із/зі + genitive chunk (З України) Self-check: Where are
    you from? Where do you live now? Where are you going after this lesson?'
vocabulary_hints:
  required:
  - звідки (where from)
  - з/із/зі (from — + genitive chunk)
  - Україна (Ukraine)
  - Київ (Kyiv)
  - Львів (Lviv)
  - Канада (Canada)
  recommended:
  - Одеса (Odesa)
  - Харків (Kharkiv)
  - США (USA)
  - Англія (England)
  - Німеччина (Germany)
  - Польща (Poland)
  - додому (home — direction)
activity_hints:
- type: fill-in
  focus: Answer Звідки? using з/із/зі + memorized genitive chunks
  items: 8
  blanks:
  - Звідки ти? — Я {з України}.
  - Вона {з Канади}.
  - Ми {з Києва}, а ви?
  - Джон {зі США}.
  - Мій друг {з Німеччини}.
  - Я {зі Львова}.
  - Вони {з Англії}.
  - Олена {з Одеси}.
- type: group-sort
  focus: Categorize phrases into Де? (Locative), Куди? (Accusative), Звідки? (Genitive)
  items: 9
  groups:
  - name: Де? (Where?)
    items:
    - в Україні
    - в Києві
    - на роботі
  - name: Куди? (Where to?)
    items:
    - в Україну
    - в Київ
    - на роботу
  - name: Звідки? (Where from?)
    items:
    - з України
    - з Києва
    - з роботи
- type: quiz
  focus: Choose correct preposition (в/на/з) for location/direction
  items: 8
  questions:
  - Я йду... роботи. (з / на / в)
  - Вона йде... школу. (в / на / зі)
  - Ми зараз... Україні. (в / з / на)
  - Я їду... Канаду. (в / з / на)
  - Він... Німеччини. (з / в / на)
  - Вони... Львові. (у / зі / на)
  - Я йду... магазину. (з / в / на)
  - Олена... школи. (зі / в / на)
- type: fill-in
  focus: Contrast current location (в/на) and origin (з/із)
  items: 6
  blanks:
  - Я живу {в Києві}, але я {зі Львова}.
  - Вона живе {в Канаді}, але вона {з України}.
  - Ми зараз {в Англії}, але ми {з Польщі}.
  - Він живе {в Одесі}, але він {з Харкова}.
  - Я {з Німеччини}, але зараз я {в Україні}.
  - Ти {зі США}, але живеш {у Києві}.
connects_to:
- a1-035 (Checkpoint — Places)
prerequisites:
- a1-033 (Around the City)
grammar:
- Звідки? + з/із/зі + genitive (memorized chunks)
- 'Location trio: Де? (M.в.) / Куди? (Зн.в.) / Звідки? (Р.в. chunk)'
- Country/city names in three case forms
register: розмовний
references:
- title: ULP Season 1, Episode 4
  url: https://www.ukrainianlessons.com/episode4/
  notes: Where are you from? — nationalities and countries.

</plan_content>

## Generated Content

<generated_module_content>
## Діало́ги (Dialogues)

It's the first week of the semester, and students from all over the world are meeting at a Kyiv university. Everyone wants to know the same thing: **Звідки ти?** (Where are you from?) Here's how that conversation sounds in Ukrainian — using **з** (from) plus a country or city name.

### Діало́г 1 — На зу́стрічі студе́нтів (At a student mixer)

> — **Тарас:** Приві́т! Ме́не зва́ти Тарас. Звідки ти? *(Hi! My name is Taras. Where are you from?)*
> — **Лена:** Я з Украї́ни, з Ки́єва. А ти? *(I'm from Ukraine, from Kyiv. And you?)*
> — **Тарас:** Я з Кана́ди, із Торо́нто. *(I'm from Canada, from Toronto.)*
> — **Лена:** Давно́ тут? *(Been here long?)*
> — **Тарас:** Ні, я приї́хав мі́сяць тому́. А ти, Кенджі? *(No, I arrived a month ago. And you, Kenji?)*
> — **Кенджі:** Я з Япо́нії, з То́кіо. *(I'm from Japan, from Tokyo.)*
> — **Тарас:** Як ціка́во! *(How interesting!)*

:::tip
**Я приїхав** (I arrived) — memorize this as a ready-made chunk. The full verb **приїхати** belongs to A2. For now, just use **я приїхав** (masculine) or **я приїхала** (feminine) when you need to say "I arrived."
:::

Notice how Dialogue 1 uses **з** (from) with both countries and cities. The same question — **Звідки ти?** — works for both. When Lena answers **Я з України, з Києва**, she's layering: country first, then city. Think of it as zooming in: "from Ukraine, from Kyiv." Taras does the same: **Я з Канади, із Торонто** — from Canada, from Toronto.

### Діалог 2 — На ву́лиці (On the street)

> — **Оксана:** Звідки ти йдеш? *(Where are you coming from?)*
> — **Микола:** Я йду з робо́ти. А ти? *(I'm coming from work. And you?)*
> — **Оксана:** Я зі шко́ли. Куди́ ти за́раз? *(From school. Where are you headed now?)*
> — **Микола:** Додо́му. А Оле́на де? *(Home. And where's Olena?)*
> — **Оксана:** Вона́ ще в магази́ні. Але́ ско́ро йде з магази́ну додому. *(She's still at the store. But she's heading home from the store soon.)*
> — **Микола:** До́бре. Бува́й! *(Okay. Bye!)*

:::note
**з роботи** = from work | **зі школи** = from school | **додому** = homeward (direction)
:::

Look at what both dialogues share. **Звідки?** always triggers **з/із/зі** plus a place name: **з Японії** (from Japan), **з роботи** (from work), **зі школи** (from school). But notice two different uses: (1) **Звідки ти?** asks about your origin or nationality — **Я з Японії**; (2) **Звідки ти йдеш?** asks where you're physically coming from right now — **з роботи**, **зі школи**. Both use the same preposition family. Up next: the full direction trio **Де?–Куди?–Звідки?** — the three questions every Ukrainian speaker uses constantly.

<!-- INJECT_ACTIVITY: fill-in-zvidky -->

## Звідки? (Where From?)

You already know two of the three essential location questions. **Де ти?** (Where are you?) appeared in M05. **Куди ти ї́деш?** (Where are you going?) came in M33. Now the trio is complete with **Звідки ти?** (Where are you from?). Here's the whole system — one country, three different forms, three different questions:

- **Де ти?** — **В Украї́ні.** (locative — where you ARE right now)
- **Куди ти їдеш?** — **В Украї́ну.** (accusative — direction TO)
- **Звідки ти?** — **З України.** (genitive chunk — origin FROM)

See how **Україна** changes shape each time? **В Україні**, **В Україну**, **З України** — three different endings for three different situations. Native speakers switch between them automatically. We learn the pattern now and the full grammar of these endings (**відмінки**) in A2.

### З / із / зі — the euphony rule

Remember the euphony patterns from M28? The preposition **з** (from) follows the same logic. It has three forms to keep Ukrainian sounding smooth:

**With Ukrainian cities:**
- **з Києва**, **з Одеси**, **з Харкова**, **з Дніпра**
- **зі Львова** — **зі** before the лв- cluster

**With countries:**
- **з Канади**, **з Англії**, **з Польщі**, **з Фра́нції**, **з Японії**, **з Німеччини**
- **зі США** / **зі Шта́тів** — **зі** before the шт- cluster

**With everyday places:**
- **з роботи**, **з магазину**, **з банку**, **з парку**
- **зі школи** — **зі** before шк-

The pattern: **з** before most consonants and vowels; **із** between awkward consonant clusters; **зі** before combinations starting with з-, с-, ш-. At A1, don't calculate — just recognize the pattern and memorize the fixed phrases from the lists above.

### Memorize as chunks

Treat **з** + place as sealed units, the same way you learned **в Україні** as a single phrase back in M30. English speakers don't think "in + Ukraine" as separate words — they say "in Ukraine" as one chunk. Do the same here. **Я з України**, **з Києва**, **з роботи** — three set phrases to know by heart. Why does **Київ** become **Києва** and **Україна** become **України**? Those are genitive case endings — full A2 grammar. For now, recognize and reproduce the forms from this module's vocabulary. If you can say **Я з Києва** without hesitating, you're doing it right.

<!-- INJECT_ACTIVITY: group-sort-location-trio -->

## Краї́ни і міста́ (Countries and Cities)

### Украї́нські міста (Ukrainian cities)

Here are six major Ukrainian cities with their **з**-forms — the shape they take after **Звідки?**:

| Мі́сто (City) | Звідки? (From where?) |
|---|---|
| **Київ** (Kyiv) | **з Києва** |
| **Львів** (Lviv) | **зі Львова** |
| **Одеса** (Odesa) | **з Одеси** |
| **Харків** (Kharkiv) | **з Харкова** |
| **Дніпро** (Dnipro) | **з Дніпра** |
| **Запоріжжя** (Zaporizhzhia) | **із Запоріжжя** |

Ukrainian city names carry history. **Київ** takes its name from Кий, a legendary Polanian prince. **Львів** is named for Prince Лев Дани́лович — Lev, son of Danylo. When you say **зі Львова**, you're using a form shaped by centuries of Ukrainian language. Notice **зі Львова** specifically — the **зі** form prevents an awkward зл- consonant cluster.

### Країни (Countries)

Countries follow the same pattern. Here are the ones you'll use most often:

**Nearby:** **Польща** → **з Польщі** | **Угорщина** (Hungary) → **з Уго́рщини** | **Румунія** (Romania) → **з Руму́нії**

**Further away:** **Канада** → **з Канади** | **США** → **зі США** (**зі Штатів**) | **Англія** (England) → **з Англії** | **Німеччина** (Germany) → **з Німеччини** | **Франція** (France) → **з Франції** | **Японія** (Japan) → **з Японії** | **Італія** (Italy) → **з Іта́лії**

One important note: these are Ukrainian names, not transliterations of English. Germany is **Німеччина** (not "Герма́нія"). Japan is **Японія**. Canada is **Канада** (not "Кенада"). Always use the Ukrainian forms.

### Націона́льність і мо́ва (Nationality and language)

Back in M05, you learned to introduce yourself. Now extend that chain with origin:

- **Я з України** → **Я украї́нець** (m) / **українка** (f) → **Я говорю́ украї́нською.**
- **Я з Польщі** → **Я поляк** (m) / **полька** (f) → **Я говорю по́льською.**

And here's a new contrast — where you live now versus where you're originally from:

- **Я живу́ в Ки́єві, але я зі Львова.** (I live in Kyiv, but I'm from Lviv.)
- **Вона живе́ в Кана́ді, але вона з України.** (She lives in Canada, but she's from Ukraine.)

The pattern: **живу в** [place — locative] + **але я з** [place — genitive chunk]. This is how diaspora Ukrainians talk about themselves every day.

<!-- INJECT_ACTIVITY: quiz-prepositions -->

<!-- INJECT_ACTIVITY: fill-in-location-vs-origin -->

## Підсумок — Summary

You now have all three direction questions that Ukrainian speakers use constantly. Here's the complete trio — three questions, three preposition families, three memorized chunk sets:

| Пита́ння (Question) | Прийме́нник (Preposition) | Приклад (Example) | Meaning |
|---|---|---|---|
| **Де?** | в/на + locative chunk | **В Україні. У Києві. На робо́ті.** | where you ARE |
| **Куди?** | в/на + accusative chunk | **В Україну. У Київ. На робо́ту.** | where you're GOING |
| **Звідки?** | з/із/зі + genitive chunk | **З України. З Києва. З роботи.** | where you're FROM |

Why does **Київ** become **Києва** in one column and **Києві** in another? Those are different case endings — the genitive and locative. Full case grammar arrives in A2. For now: recognize the pattern, memorize the fixed forms from this module. You already have all three direction questions. Use them.

### Переві́р себе́ (Self-check)

Answer these three questions out loud in Ukrainian. Switch the prepositions correctly for each:

- **Звідки ти?** (З яко́ї країни? З яко́го міста?)
- **Де ти зараз?** (В яко́му мі́сті? В які́й краї́ні?)
- **Куди ти йдеш пі́сля цього́ уро́ку?** (Додому? На роботу? В магази́н?)

If you can answer all three — switching smoothly between **з/із/зі**, **в/на**, and **в/на** — the **Де?/Куди?/Звідки?** trio is yours.

**Deterministic word count: 1374 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 65 words | Not found: 79 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іта — NOT IN VESUM
  ✗ Італія — NOT IN VESUM
  ✗ Англія — NOT IN VESUM
  ✗ Англії — NOT IN VESUM
  ✗ Дани — NOT IN VESUM
  ✗ Дніпра — NOT IN VESUM
  ✗ Дніпро — NOT IN VESUM
  ✗ Додо — NOT IN VESUM
  ✗ Діало — NOT IN VESUM
  ✗ Запоріжжя — NOT IN VESUM
  ✗ Кана — NOT IN VESUM
  ✗ Канада — NOT IN VESUM
  ✗ Канади — NOT IN VESUM
  ✗ Кенада — NOT IN VESUM
  ✗ Кенджі — NOT IN VESUM
  ✗ Києва — NOT IN VESUM
  ✗ Лена — NOT IN VESUM
  ✗ Львова — NOT IN VESUM
  ✗ Львів — NOT IN VESUM
  ✗ Микола — NOT IN VESUM
  ✗ Націона — NOT IN VESUM
  ✗ Німеччина — NOT IN VESUM
  ✗ Німеччини — NOT IN VESUM
  ✗ Одеса — NOT IN VESUM
  ✗ Одеси — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM
  ✗ Оле — NOT IN VESUM
  ✗ Переві — NOT IN VESUM
  ✗ Польща — NOT IN VESUM
  ✗ Польщі — NOT IN VESUM
  ✗ Приві — NOT IN VESUM
  ✗ Руму — NOT IN VESUM
  ✗ Румунія — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Торонто — NOT IN VESUM
  ✗ Уго — NOT IN VESUM
  ✗ Угорщина — NOT IN VESUM
  ✗ Украї — NOT IN VESUM
  ✗ Фра — NOT IN VESUM
  ✗ Франція — NOT IN VESUM
  ✗ Харкова — NOT IN VESUM
  ✗ Харків — NOT IN VESUM
  ✗ Шта — NOT IN VESUM
  ✗ Япо — NOT IN VESUM
  ✗ Японія — NOT IN VESUM
  ✗ Японії — NOT IN VESUM
  ✗ деш — NOT IN VESUM
  ✗ зва — NOT IN VESUM
  ✗ кіо — NOT IN VESUM
  ✗ лович — NOT IN VESUM

All 65 other words are confirmed to exist in VESUM.

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
