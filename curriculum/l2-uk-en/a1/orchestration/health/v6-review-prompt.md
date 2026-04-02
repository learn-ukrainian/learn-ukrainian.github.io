<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 53: Health (A1, A1.8 [Past, Future, Graduation])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-053
level: A1
sequence: 53
slug: health
version: '1.2'
title: Health
subtitle: У мене болить голова — body parts and symptoms
focus: vocabulary
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Name basic body parts in Ukrainian (голова, рука, нога, живіт, горло, спина)
- Describe symptoms using "У мене болить..." as a chunk
- Tell a doctor or pharmacist what hurts
- Use basic health vocabulary in practical situations
dialogue_situations:
- setting: 'At the doctor''s office — describing symptoms: У мене болить голова (f,
    head). Болить горло (n, throat). Болить живіт (m, stomach). Нежить (m, runny nose).
    Кашель (m, cough). Температура (f, fever).'
  speakers:
  - Пацієнт
  - Лікар
  motivation: 'Body parts: голова(f), горло(n), живіт(m), температура(f)'
content_outline:
- section: Dialogues
  words: 300
  points:
  - 'Dialogue 1 — At the doctor''s: — Що у вас болить? — У мене болить голова і горло.
    — Давно? — З учора. І в мене температура. — Ви кашляєте? — Так, трохи. І в мене
    нежить. — Зрозуміло. Це застуда. Я випишу ліки. Відпочивайте! — Дякую, лікарю!
    Doctor visit: symptoms + basic diagnosis.'
  - 'Dialogue 2 — At the pharmacy: — Добрий день! У мене болить голова. Дайте, будь
    ласка, таблетки. — Від головного болю? — Так. І від кашлю, будь ласка. — Ось,
    будь ласка. Ще щось? — А є щось від нежиті? — Так, ось краплі. — Дякую! Скільки
    це коштує? Pharmacy: asking for medicine using known polite forms.'
- section: Тіло (The Body)
  words: 300
  points:
  - 'Essential body parts (Grade 1-2 textbooks: частини тіла): голова (head, f), горло
    (throat, n), спина (back, f), живіт (stomach, m), рука (hand/arm, f), нога (leg/foot,
    f), око (eye, n), вухо (ear, n), зуб (tooth, m), ніс (nose, m). Note: рука = whole
    arm including hand. нога = whole leg including foot. These are the most useful
    for A1 — not an anatomy lesson.'
  - 'Body part gender matters for adjectives (review from M09): велике око (big eye
    — neuter), великий ніс (big nose — masc), велика рука (big hand — fem). But at
    A1, focus on recognition — you''ll use these mainly with болить.'
- section: У мене болить... (It Hurts...)
  words: 300
  points:
  - 'The magic phrase: У мене болить + body part. У мене болить голова. (I have a
    headache. — literally ''at me hurts head'') У мене болить живіт. (My stomach hurts.)
    У мене болить горло. (My throat hurts.) У мене болить спина. (My back hurts.)
    У мене болить зуб. (I have a toothache.) Learn this as a CHUNK — don''t analyze
    the grammar (that''s dative, A2+).'
  - 'Common symptoms (as chunks): У мене температура. (I have a fever.) У мене кашель.
    (I have a cough.) У мене нежить. (I have a runny nose.) Мені холодно. (I''m cold.)
    Мені погано. (I feel bad.) Я хворий/хвора. (I''m sick. — masc/fem) Note: ''У мене
    болять зуби'' (teeth hurt — plural form болять). Just recognize it.'
- section: Summary
  words: 300
  points:
  - 'Health toolkit: Body parts: голова, горло, живіт, спина, рука, нога, око, вухо,
    зуб, ніс. Symptoms: У мене болить [body part]. У мене температура/кашель/нежить.
    State: Я хворий/хвора. Мені погано. At the doctor: Що у вас болить? — У мене болить...
    At the pharmacy: Дайте таблетки від [symptom], будь ласка. від головного болю
    (for headache), від кашлю (for cough), від нежиті (for runny nose). Self-check:
    How do you say ''My throat hurts and I have a fever''?'
vocabulary_hints:
  required:
  - голова (head, f)
  - горло (throat, n)
  - живіт (stomach, m)
  - рука (hand/arm, f)
  - нога (leg/foot, f)
  - болить (hurts — chunk: у мене болить)
  - лікар (doctor, m)
  - аптека (pharmacy, f)
  recommended:
  - спина (back, f)
  - око (eye, n)
  - вухо (ear, n)
  - зуб (tooth, m)
  - ніс (nose, m)
  - температура (fever/temperature, f)
  - кашель (cough, m)
  - нежить (runny nose, f)
  - таблетка (pill, f)
  - хворий (sick, adj)
activity_hints:
- type: match-up
  focus: Match body parts to their English translations.
  items:
  - голова == head
  - живіт == stomach
  - горло == throat
  - спина == back
  - рука == hand/arm
  - нога == leg/foot
  - зуб == tooth
  - око == eye
- type: fill-in
  focus: Complete the sentence with the correct symptom or body part.
  items:
  - У мене болить {голова|рука|нога}. Я хочу спати.
  - У мене болить {живіт|вухо|око}. Я не хочу їсти.
  - У мене болить {горло|спина|ніс} і є температура. Я не можу говорити.
  - У мене {кашель|нежить|зуб}, я постійно кашляю.
  - У мене болить {зуб|голова|нога}, мені потрібен стоматолог.
  - Я {хворий|лікар|аптека}. У мене болить голова і спина.
- type: quiz
  focus: Choose the logical response to the health problem.
  items:
  - question: У мене болить голова.
    options:
    - Ось таблетки від головного болю.
    - Ось краплі від нежиті.
    - Випийте сироп від кашлю.
  - question: У мене сильний кашель.
    options:
    - Вам потрібні таблетки від кашлю.
    - Ось краплі для носа.
    - У мене болить зуб.
  - question: Що у вас болить?
    options:
    - У мене болить горло.
    - Я лікар.
    - Де аптека?
  - question: Добрий день. Дайте, будь ласка, щось від нежиті.
    options:
    - Ось краплі, будь ласка.
    - У мене болить спина.
    - Це таблетки від головного болю.
- type: fill-in
  focus: At the pharmacy or doctor - using target chunks.
  items:
  - Дайте, {будь ласка|добрий день|дякую}, таблетки від головного болю.
  - Що у вас {болить|хворий|лікар}?
  - У мене {температура|аптека|лікар} і болить горло.
  - Мені {погано|хворий|добре}. Викличте лікаря!
  - Де тут найближча {аптека|голова|спина}? Мені потрібні ліки.
connects_to:
- a1-054 (Emergencies)
prerequisites:
- a1-052 (My Story)
grammar:
- У мене болить + body part (impersonal chunk — no grammar analysis)
- Body part gender for adjective agreement (recognition only)
- Я хворий/хвора (gender agreement in short adjectives)
register: розмовний
references:
- title: State Standard 2024, §3
  notes: 'Thematic area: health (здоров''я) — body parts, symptoms, doctor visits.'
- title: 'Grade 1-2 textbook: Частини тіла'
  notes: Body parts vocabulary with pictures.

</plan_content>

## Generated Content

<generated_module_content>
## Dialogues

Оле́нка wakes up feeling terrible — her head is pounding and her throat is on fire. Time to visit the **лі́кар** (doctor).

> — **Лікар:** До́брий день! Що у вас боли́ть? *(Good day! What hurts?)*
> — **Паціє́нтка:** У мене́ болить голова́ і го́рло. *(My head and throat hurt.)*
> — **Лікар:** Давно́? *(For long?)*
> — **Пацієнтка:** З учо́ра. І в мене температу́ра. *(Since yesterday. And I have a fever.)*
> — **Лікар:** Ви ка́шляєте? *(Are you coughing?)*
> — **Пацієнтка:** Так, тро́хи. І в мене не́жить. *(Yes, a little. And I have a runny nose.)*
> — **Лікар:** Зрозумі́ло. Це засту́да. *(Understood. It's a cold.)*
> — **Пацієнтка:** Що мені́ роби́ти? *(What should I do?)*
> — **Лікар:** Я ви́пишу лі́ки. Відпочива́йте! *(I'll prescribe medicine. Rest!)*
> — **Пацієнтка:** Дякую, лі́карю! *(Thank you, doctor!)*

With her prescription in hand, Оленка walks to the **апте́ка** (pharmacy) next door.

> — **Оленка:** Добрий день! У мене болить голова. Да́йте, будь ла́ска, табле́тки. *(Good day! My head hurts. Give me pills, please.)*
> — **Фармаце́вт:** Про́ти головно́го бо́лю? *(For a headache?)*
> — **Оленка:** Так. І проти ка́шлю, будь ласка. *(Yes. And for a cough, please.)*
> — **Фармацевт:** Ось, будь ласка. Ще щось? *(Here you go. Anything else?)*
> — **Оленка:** А є щось проти не́житю? *(Do you have something for a runny nose?)*
> — **Фармацевт:** Так, ось кра́плі. *(Yes, here are drops.)*
> — **Оленка:** Дякую! Скі́льки це ко́шту́є? *(Thanks! How much does this cost?)*
> — **Фармацевт:** Сто два́дцять гри́вень. *(One hundred twenty hryvnias.)*
> — **Оленка:** Будь ласка. *(Here you go.)*

Notice three key chunks from these dialogues. First: **У мене болить...** (I have a pain in...) — the essential phrase for telling anyone what hurts. Second: **Дайте, будь ласка...** (Give me... please) — the polite request form you already know from shopping modules. Third: **проти головного болю** (for a headache), **проти кашлю** (for a cough), **проти нежитю** (for a runny nose) — these are how you ask for specific medicine. You don't need to analyse the grammar behind these yet — that comes at A2. For now, treat them as ready-made chunks.

## Ті́ло (The Body)

Here are the ten body parts you need at A1. Each one has a grammatical gender — this matters for adjective agreement, but right now your main job is simply learning the words:

- **голова** (head, f)
- **горло** (throat, n)
- **спи́на** (back, f)
- **живі́т** (stomach, m)
- **рука́** (hand/arm, f)
- **нога́** (leg/foot, f)
- **о́ко** (eye, n)
- **ву́хо** (ear, n)
- **зуб** (tooth, m)
- **ніс** (nose, m)

Two important notes: **рука** covers the entire arm including the hand — Ukrainian doesn't split them at A1. The same goes for **нога**, which means the whole leg including the foot. If you stub your toe or twist your ankle, it's still **нога**.

Why do genders matter here? Because adjectives must agree: **вели́ке око** (big eye — neuter), **вели́кий ніс** (big nose — masculine), **вели́ка рука** (big hand — feminine). But at this stage, you'll mostly use these words in the chunk **У мене болить...**, where gender doesn't change anything. Memorise the words first — full adjective agreement practice comes at A2.

<!-- INJECT_ACTIVITY: match-body-parts -->

Imagine Миха́йлик is drawing a person and labelling the parts: «Ось **голова**!» *(Here's the head!)* He draws two arms: «А це **рука** і **рука**.» *(And this is an arm and an arm.)* Then the legs: «Це **нога**.» *(This is a leg.)* He adds a face: «Ось **ніс**, **око** і **вухо**.» *(Here's the nose, eye, and ear.)* He points to the middle: «А тут **живіт**!» *(And here's the stomach!)* Finally he writes across the back: «І **спина**!» *(And the back!)* Simple labelling like this — pointing and naming — is exactly how Ukrainian Grade 1 textbooks introduce body parts.

A few pronunciation tips for tricky words. **Горло** — the «г» is a voiced sound, softer than English "g." Think of a gentle vibration in the throat, not a hard stop. **Живіт** — the «ж» sounds like the "s" in English "measure" or "pleasure." **Вухо** starts with two distinct sounds: «в» then «у» — don't blend them into an English "w." When in doubt about stress or exact pronunciation, check the словни́к tab where every word has audio.

## У мене болить... (It Hurts...)

The single most useful health phrase in Ukrainian is **У мене болить** + a body part. Learn it as one chunk — a ready-made sentence starter. Here are the five core combinations:

1. **У мене болить голова.** (My head hurts.)
2. **У мене болить живіт.** (My stomach hurts.)
3. **У мене болить горло.** (My throat hurts.)
4. **У мене болить спина.** (My back hurts.)
5. **У мене болить зуб.** (My tooth hurts.)

The literal structure is "at me hurts head" — the grammar behind this pattern is something you'll study properly at A2. For now, just memorise the pattern: **У мене болить** + whatever hurts.

When more than one thing hurts — or when the body part is naturally plural — **болить** changes to **боля́ть**:

- **У мене болять зу́би.** (My teeth hurt.)
- **У мене болять но́ги.** (My legs hurt.)
- **У мене болять о́чі.** (My eyes hurt.)

You don't need to produce these forms yet. Just recognise them when you hear a doctor or friend say **болять** — it means multiple things hurt.

<!-- INJECT_ACTIVITY: fill-in-symptoms -->

Beyond **болить**, there are several common symptom chunks. Each one is a complete statement you can use as-is:

- **У мене температура.** (I have a fever. — literally "I have temperature")
- **У мене ка́шель.** (I have a cough.)
- **У мене нежить.** (I have a runny nose.)
- **Мені хо́лодно.** (I'm cold.)
- **Мені пога́но.** (I feel unwell.)
- **Я хво́рий.** (I'm sick. — if you're male)
- **Я хво́ра.** (I'm sick. — if you're female)

Notice that **У мене температура** doesn't use **болить** — the fever doesn't "hurt," it "is with you." And **Мені погано** uses a different grammatical form (**мені**) — again, just learn it as a chunk for now.

At the doctor or pharmacy, combine these chunks naturally. A sick person might say: **У мене болить горло і є температура.** (My throat hurts and I have a fever.) Or: **Я хвора. У мене кашель і нежить.** (I'm sick. I have a cough and a runny nose.) You already have enough vocabulary to describe a full set of symptoms — real Ukrainian you'd use on day one in Kyiv.

<!-- INJECT_ACTIVITY: fill-in-pharmacy -->

## Summary

Here is your complete health toolkit from this module.

**Body parts:**
**голова**, **горло**, **живіт**, **спина**, **рука**, **нога**, **око**, **вухо**, **зуб**, **ніс**

**Symptom chunks:**
- **У мене болить** [body part].
- **У мене температура / кашель / нежить.**
- **Мені погано.**
- **Я хворий / хвора.**

Two real situations where you'll use all of this:

**At the doctor (у лі́каря):**
- Doctor asks: **Що у вас болить?** → You answer: **У мене болить...**

**At the pharmacy (в апте́ці):**
- **Дайте, будь ласка, таблетки проти головного болю.** (Give me pills for a headache, please.)
- **Дайте краплі проти нежитю.** (Give me drops for a runny nose.)
- **Дайте сиро́п проти кашлю.** (Give me syrup for a cough.)

<!-- INJECT_ACTIVITY: quiz-health-response -->

Test yourself with these three questions:

- How do you say "My throat hurts and I have a fever"? → **У мене болить горло і є температура.**
- You're at the pharmacy. You need something for a cough. What do you say? → **Дайте, будь ласка, щось проти кашлю.**
- How do you say "I feel unwell"? → **Мені погано.**

If you got all three, you're ready for real-world health situations.

Looking ahead: module 54 (Emergencies) builds directly on this vocabulary. You'll learn phrases like **ви́клик швидко́ї** (calling an ambulance), describe urgent situations, and use past-tense forms from module 52. The chunk **У мене болить...** will reappear constantly across future modules — it's one of those patterns that, once learned, never stops being useful.

<!-- INJECT_ACTIVITY: fill-in-pharmacy-doctor -->

**Deterministic word count: 1338 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 73 words | Not found: 32 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Зрозумі — NOT IN VESUM
  ✗ Миха — NOT IN VESUM
  ✗ Оле — NOT IN VESUM
  ✗ Паціє — NOT IN VESUM
  ✗ Скі — NOT IN VESUM
  ✗ Фармаце — NOT IN VESUM
  ✗ апте — NOT IN VESUM
  ✗ боля — NOT IN VESUM
  ✗ вень — NOT IN VESUM
  ✗ дцять — NOT IN VESUM
  ✗ засту — NOT IN VESUM
  ✗ йлик — NOT IN VESUM
  ✗ йте — NOT IN VESUM
  ✗ карю — NOT IN VESUM
  ✗ каря — NOT IN VESUM
  ✗ кра — NOT IN VESUM
  ✗ лодно — NOT IN VESUM
  ✗ льки — NOT IN VESUM
  ✗ нка — NOT IN VESUM
  ✗ нтка — NOT IN VESUM
  ✗ пога — NOT IN VESUM
  ✗ рло — NOT IN VESUM
  ✗ словни — NOT IN VESUM
  ✗ табле — NOT IN VESUM
  ✗ температу — NOT IN VESUM
  ✗ тки — NOT IN VESUM
  ✗ тро — NOT IN VESUM
  ✗ учо — NOT IN VESUM
  ✗ хво — NOT IN VESUM
  ✗ шель — NOT IN VESUM
  ✗ шляєте — NOT IN VESUM
  ✗ шту — NOT IN VESUM

All 73 other words are confirmed to exist in VESUM.

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
