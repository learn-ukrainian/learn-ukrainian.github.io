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
When you visit a medical professional in Ukraine, the interaction is usually direct and focused on the symptoms. A general practitioner, known as a **терапевт** (general practitioner), will often begin the consultation with a very standard, practical opening phrase: **Що у вас болить?** (What hurts you?). The cultural expectation is that you will answer this question directly by listing your physical symptoms or describing how you feel, rather than making small talk. There is no need to translate English phrases like "I am not feeling well today" before getting to the point. You simply state the problem. After receiving a diagnosis from the doctor, you will likely need to visit a pharmacy, called an **аптека** (pharmacy). There, you will speak with an **аптекар** (pharmacist) to purchase the necessary treatments, using polite requests to get exactly what you need.

> **Лікар:** Добрий день! Що у вас болить? *(Good day! What hurts?)*
> **Пацієнт:** У мене болить голова і горло. *(My head and throat hurt.)*
> **Лікар:** Давно? *(For a long time?)*
> **Пацієнт:** З учора. І в мене температура. *(Since yesterday. And I have a fever.)*
> **Лікар:** Ви кашляєте? *(Are you coughing?)*
> **Пацієнт:** Так, трохи. І в мене нежить. *(Yes, a little. And I have a runny nose.)*
> **Лікар:** Зрозуміло. Це застуда. Я випишу ліки. Відпочивайте! *(I understand. It is a cold. I will prescribe medicine. Rest!)*
> **Пацієнт:** Дякую, лікарю! *(Thank you, doctor!)*

In this dialogue, the patient clearly lists the problems: **болить голова і горло** (head and throat hurt), **температура** (fever), and **нежить** (runny nose). The doctor provides a clear diagnosis of **застуда** (a cold) and promises to help: **я випишу ліки** (I will prescribe medicine).

> **Пацієнт:** Добрий день! У мене болить голова. Дайте, будь ласка, таблетки. *(Good day! My head hurts. Give me pills, please.)*
> **Аптекар:** Від головного болю? *(For a headache?)*
> **Пацієнт:** Так. І від кашлю, будь ласка. *(Yes. And for a cough, please.)*
> **Аптекар:** Ось, будь ласка. Ще щось? *(Here you go. Anything else?)*
> **Пацієнт:** А є щось від нежитю? *(And is there anything for a runny nose?)*
> **Аптекар:** Так, ось краплі. *(Yes, here are drops.)*
> **Пацієнт:** Дякую! Скільки це коштує? *(Thank you! How much does it cost?)*

At the pharmacy, the patient uses the polite command **Дайте, будь ласка** (Give me, please) to request specific items. They ask for **таблетки від головного болю** (pills for a headache) and **краплі від нежитю** (drops for a runny nose). The interaction concludes with the essential practical question for any transaction: **Скільки це коштує?** (How much does it cost?).

<!-- INJECT_ACTIVITY: quiz-medical-responses -->

## Тіло (The Body)
To describe what hurts, you must first know the names of the fundamental parts of the body. In Ukrainian textbooks for early grades, these are taught simply as **частини тіла** (body parts). For common medical complaints, you need to recognize the most essential ones. The word for head is **голова** (head), which is a feminine noun. The throat is **горло** (throat), a neuter noun. The back is **спина** (back), another feminine noun. The stomach or abdomen is **живіт** (stomach), which is a masculine noun. Knowing the grammatical gender of each word is important because it dictates how adjectives will agree with them. For example, if you want to describe a sore back, the adjective must match the feminine gender of the noun, creating a phrase like **хвора спина** (sore back).

*   **голова** (head, f)
*   **горло** (throat, n)
*   **спина** (back, f)
*   **живіт** (stomach, m)

Beyond the torso and head, you must be able to name your limbs and sensory organs. The word for an arm or a hand is **рука** (hand/arm), a feminine noun. The word for a leg or a foot is **нога** (leg/foot), also feminine. For the face and head, an eye is **око** (eye, n), an ear is **вухо** (ear, n), a tooth is **зуб** (tooth, m), and a nose is **ніс** (nose, m). These vocabulary words will cover the vast majority of basic health issues you might experience.

:::note
In Ukrainian, **рука** refers to the entire limb from the shoulder all the way down to the fingertips, and **нога** refers to the entire limb from the hip down to the toes. Ukrainian does not strictly separate the hand from the arm or the foot from the leg in everyday speech as English does.
:::

*   **рука** (hand/arm, f)
*   **нога** (leg/foot, f)
*   **око** (eye, n)
*   **вухо** (ear, n)
*   **зуб** (tooth, m)
*   **ніс** (nose, m)

At the A1 level, your primary goal is to recognize these nouns so you can point to what hurts. However, you should also begin to notice how adjectives change their endings to match the gender of these body parts. You learned about adjective agreement in earlier modules, and it applies here perfectly. A masculine noun takes a masculine adjective, a feminine noun takes a feminine adjective, and a neuter noun takes a neuter adjective. For instance, you will see **великий ніс** (big nose — masculine), **велика рука** (big hand — feminine), and **велике око** (big eye — neuter). While you will mostly use these nouns with the verb for "hurts," recognizing these endings helps build your grammatical reflex.

*   **великий ніс** (big nose)
*   **велика рука** (big hand)
*   **велике око** (big eye)

<!-- INJECT_ACTIVITY: match-body-vocabulary -->

## У мене болить... (It Hurts...)
The most important structure for discussing health in Ukrainian is the magic phrase for expressing pain. You do not say "my head hurts" using a possessive pronoun. Instead, you use the fixed chunk **У мене болить** followed by the body part in the nominative case. Literally, this translates to "at me hurts," but it simply means "my [body part] hurts." You must memorize this as a complete pattern rather than analyzing the grammar behind it.

*   **У мене болить голова.** (I have a headache. / My head hurts.)
*   **У мене болить живіт.** (My stomach hurts.)
*   **У мене болить горло.** (My throat hurts.)
*   **У мене болить спина.** (My back hurts.)
*   **У мене болить зуб.** (I have a toothache. / My tooth hurts.)

:::caution
Never translate the English phrase "my head hurts" directly word-for-word into Ukrainian. A phrase like «Моя голова болить» sounds unnatural to a native speaker. Always use the impersonal construction **У мене болить голова**.
:::

If the pain is in a body part that comes in pairs or groups, the verb must change to match the plural subject. The singular verb **болить** (hurts) changes to the plural verb **болять** (hurt). This is a simple switch from an **-ить** ending to an **-ять** ending.

*   **У мене болять очі.** (My eyes hurt.)
*   **У мене болять вуха.** (My ears hurt.)
*   **У мене болять зуби.** (My teeth hurt.)
*   **У мене болять ноги.** (My legs hurt.)

Not all illnesses involve a specific localized pain. For general symptoms and respiratory issues, you use different phrases. If your body temperature is high, you use the noun **температура** (fever/temperature). For a cough, you use the masculine noun **кашель** (cough). For a runny nose, you use the masculine noun **нежить** (runny nose). To describe these states, you often use the same "I have" construction:

*   **У мене температура.** (I have a fever.)
*   **У мене кашель.** (I have a cough.)
*   **У мене нежить.** (I have a runny nose.)

:::tip
Remember that **нежить** (runny nose) is a masculine noun. This means its ending changes differently than feminine nouns, which is why you ask for drops **від нежитю**, not від нежиті.
:::

When you want to describe your overall physical state, you can use the adjective for sick, which must agree with your gender. A man says **Я хворий** (I am sick), and a woman says **Я хвора** (I am sick). Alternatively, you can use the impersonal phrase **Мені погано** (I feel bad) or **Мені холодно** (I am cold) to express general discomfort. These are excellent chunks to memorize for times when you cannot point to a specific pain but know you need help.

*   **Я хворий.** (I am sick. — masculine)
*   **Я хвора.** (I am sick. — feminine)
*   **Мені погано.** (I feel bad.)
*   **Мені холодно.** (I am cold.)

<!-- INJECT_ACTIVITY: fill-in-symptoms-logic -->
<!-- INJECT_ACTIVITY: fill-in-medical-chunks -->

## Summary
You can identify the ten core body parts: **голова** (head), **горло** (throat), **живіт** (stomach), **спина** (back), **рука** (arm/hand), **нога** (leg/foot), **око** (eye), **вухо** (ear), **зуб** (tooth), and **ніс** (nose). You also know the primary symptoms associated with common illnesses, such as **температура** (fever), **кашель** (cough), and **нежить** (runny nose). These words allow you to point to a problem and give it a name.

You have also learned the functional structures required to express pain and discomfort. The most critical magic phrase is **У мене болить** for singular body parts and **У мене болять** for plural ones. When you feel generally unwell, you can describe your state using the phrases **Мені погано** (I feel bad), **Мені холодно** (I am cold), or **Я хворий / Я хвора** (I am sick). Finally, when you visit the pharmacy, you know how to make a polite request using the phrase **Дайте таблетки від...** (Give me pills for...). You can ask for items **від головного болю** (for a headache), **від кашлю** (for a cough), or **від нежитю** (for a runny nose).

Here is a quick self-check to review what you have learned. Read the English prompt and try to form the Ukrainian response before looking at the model answer.

How do you tell a doctor that your throat hurts?
> [!model-answer]
> **У мене болить горло.**

How do you ask a pharmacist for headache pills?
> [!model-answer]
> **Дайте, будь ласка, таблетки від головного болю.**

How do you say "My eyes hurt and I have a fever"?
> [!model-answer]
> **У мене болять очі і є температура.**

How do you say "I am sick" if you are a woman?
> [!model-answer]
> **Я хвора.**

How do you tell someone that you feel bad?
> [!model-answer]
> **Мені погано.**
</generated_module_content>

**PIPELINE NOTE — Word count: 1547 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 1200 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
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
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
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

Verified: 71 words | Not found: 1 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ ить — NOT IN VESUM

All 71 other words are confirmed to exist in VESUM.

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
