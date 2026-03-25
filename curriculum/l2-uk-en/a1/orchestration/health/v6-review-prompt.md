# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 53: Health (A1, A1.8 [Past, Future, Graduation])
**Writer:** Gemini Pro
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

Feeling unwell in a new language can be stressful, but learning a few essential phrases helps you navigate a visit to the clinic or the pharmacy with confidence. When you need medical help in Ukraine, you will usually speak with a **лікар** (doctor) or visit an **аптека** (pharmacy) to ask for medicine. 

A typical conversation at the doctor's office involves directly naming your symptoms. The doctor will want to know exactly what is bothering you and how long you have been experiencing the problem. Notice how the patient answers these questions clearly and concisely.

<div class="dialogue">


**Лікар:** Що у вас болить? *(What hurts you?)*


**Пацієнт:** У мене болить голова і горло. *(My head and throat hurt.)*


**Лікар:** Давно? *(For a long time?)*


**Пацієнт:** З учора. І в мене температура. *(Since yesterday. And I have a fever.)*


**Лікар:** Ви кашляєте? *(Are you coughing?)*


**Пацієнт:** Так, трохи. І в мене нежить. *(Yes, a little. And I have a runny nose.)*


**Лікар:** Зрозуміло. Це застуда. Я випишу ліки. Відпочивайте! *(I see. This is a cold. I will prescribe medicine. Rest!)*


**Пацієнт:** Дякую, лікарю! *(Thank you, doctor!)*


</div>

In this dialogue, the doctor asks the most important medical question you will ever hear in a clinic: **Що у вас болить?** (What hurts you?). The patient answers by listing their symptoms using the simple, fixed phrase **У мене болить...** (My... hurts) followed by the specific body parts. The doctor also asks about other common symptoms like coughing, to which the patient adds that they have a fever (**температура**) and a runny nose (**нежить**). This leads to a straightforward diagnosis of a cold (**застуда**).

If you already know what you need, you can bypass the clinic and go straight to an **аптека** (pharmacy). Polite requests are your best tool in this situation, as the pharmacist can guide you to the correct over-the-counter medicine.

<div class="dialogue">


**Фармацевт:** Добрий день! *(Good day!)*


**Клієнт:** Добрий день! У мене болить голова. Дайте, будь ласка, таблетки. *(Good day! My head hurts. Give me pills, please.)*


**Фармацевт:** Від головного болю? *(For a headache?)*


**Клієнт:** Так. І від кашлю, будь ласка. *(Yes. And for a cough, please.)*


**Фармацевт:** Ось, будь ласка. Ще щось? *(Here you go. Anything else?)*


**Клієнт:** А є щось від нежиті? *(And is there anything for a runny nose?)*


**Фармацевт:** Так, ось краплі. *(Yes, here are drops.)*


**Клієнт:** Дякую! Скільки це коштує? *(Thank you! How much does this cost?)*


</div>

The customer clearly explains their problem using the phrase **У мене болить голова** and then makes a polite request using **Дайте, будь ласка...** (Give me, please...). They also ask for medicine tailored to specific symptoms like **кашель** (cough) and **нежить** (runny nose). The pharmacist confirms the type of pain, asking if the pills are **від головного болю** (for a headache), and provides the necessary items.

:::fill-in
title: "Знайди потрібне слово (At the pharmacy or doctor)"
---
- sentence: "Дайте, {будь ласка|добрий день|дякую}, таблетки від головного болю."
- sentence: "Що у вас {болить|хворий|лікар}?"
- sentence: "У мене {температура|аптека|лікар} і болить горло."
- sentence: "Мені {погано|хворий|добре}. Викличте лікаря!"
- sentence: "Де тут найближча {аптека|голова|спина}? Мені потрібні ліки."
:::

## Тіло (The Body)

To explain what is bothering you to a medical professional, you first need to know how to name the parts of your body. In Ukrainian textbooks for primary school, this fundamental vocabulary is often introduced as **частини тіла** (body parts). For practical, everyday communication, you only need the most essential terms to point to where it hurts. You do not need to memorize complex medical terminology.

These are the core body parts you will use most frequently, along with their grammatical gender. Recognizing the gender becomes important when you describe the body part with an adjective.

*   **голова** (head) — feminine
*   **горло** (throat) — neuter
*   **спина** (back) — feminine
*   **живіт** (stomach) — masculine
*   **рука** (hand/arm) — feminine
*   **нога** (leg/foot) — feminine
*   **око** (eye) — neuter
*   **вухо** (ear) — neuter
*   **зуб** (tooth) — masculine
*   **ніс** (nose) — masculine

The Ukrainian language often uses a single word to describe a larger limb or extremity. For example, **рука** refers to the entire arm, including the hand itself. Whether you hurt your finger, your wrist, or your shoulder, you can state that your **рука** hurts, and the medical professional will know where to look. Similarly, **нога** means the entire leg, all the way down to the foot. This makes describing your injuries much simpler, as you do not need separate words for toes, ankles, or knees at this stage.

Because Ukrainian nouns belong to a specific gender—masculine, feminine, or neuter—any adjective you use to describe them must change its ending to match the noun. 

*   **великий ніс** (big nose) — **ніс** is masculine, so the adjective takes the masculine form **великий**.
*   **велика рука** (big hand) — **рука** is feminine, so the adjective takes the feminine form **велика**.
*   **велике око** (big eye) — **око** is neuter, so the adjective takes the neuter form **велике**.
*   **великий живіт** (big stomach) — **живіт** is masculine, so the adjective remains **великий**.

When visiting a clinic or talking about a basic illness, you will mostly use these nouns entirely on their own without adding adjectives. Focusing on recognizing these core body parts prepares you to combine them seamlessly with the phrase for "it hurts."

:::match-up
title: "Утвори пару (Match the body parts)"
---
- left: "голова"
  right: "head"
- left: "живіт"
  right: "stomach"
- left: "горло"
  right: "throat"
- left: "спина"
  right: "back"
- left: "рука"
  right: "hand/arm"
- left: "нога"
  right: "leg/foot"
- left: "зуб"
  right: "tooth"
- left: "око"
  right: "eye"
:::

## У мене болить... (It Hurts...)

With the basic body parts memorized, you can build the single most important phrase for any medical situation. In Ukrainian, describing pain requires a fixed, impersonal construction that translates literally to "at me hurts." You do not use the verb "to have" to talk about pain.

The magic phrase is **у мене болить** followed by the body part in its basic dictionary form. This phrase should be learned as a complete chunk, without analyzing the underlying grammar. You simply attach the noun to the end of the phrase.

*   **У мене болить голова.** (I have a headache.)
*   **У мене болить живіт.** (My stomach hurts.)
*   **У мене болить горло.** (My throat hurts.)
*   **У мене болить спина.** (My back hurts.)
*   **У мене болить зуб.** (I have a toothache.)

The verb **болить** (hurts) remains exactly the same in all of these examples. Whether the pain is located in a masculine noun like **живіт** or a feminine noun like **голова**, the introductory phrase **у мене болить** does not change its form. However, if multiple parts of your body hurt at the same time, the verb shifts to its plural form, which is **болять**. For instance, **у мене болять зуби** means "my teeth hurt." At this level, your primary focus should be on recognizing this plural form when you hear it spoken by someone else. 

Beyond localized pain, you might also experience general symptoms associated with a cold or the flu. You can describe these physical conditions using the exact same **у мене** (at me) construction.

*   **У мене температура.** (I have a fever.)
*   **У мене кашель.** (I have a cough.)
*   **У мене нежить.** (I have a runny nose.)

To describe your overall physical state, there are a few simple and effective phrases. If you feel chilled or shivery, you say **мені холодно** (I am cold). If you simply feel unwell or nauseous, you state **мені погано** (I feel bad). You can also declare directly that you are sick by using an adjective. Because it is an adjective, you must ensure that it matches your own gender.

*   **Я хворий.** (I am sick. — spoken by a man)
*   **Я хвора.** (I am sick. — spoken by a woman)
*   **Він хворий.** (He is sick.)
*   **Вона хвора.** (She is sick.)

Combining **у мене болить** with specific symptoms allows you to clearly explain exactly what is wrong when speaking to a doctor, ensuring you receive the proper care.

:::fill-in
title: "Обери правильне слово (Complete the symptom)"
---
- sentence: "У мене болить {голова|рука|нога}. Я хочу спати."
- sentence: "У мене болить {живіт|вухо|око}. Я не хочу їсти."
- sentence: "У мене болить {горло|спина|ніс} і є температура. Я не можу говорити."
- sentence: "У мене {кашель|нежить|зуб}, я постійно кашляю."
- sentence: "У мене болить {зуб|голова|нога}, мені потрібен стоматолог."
- sentence: "Я {хворий|лікар|аптека}. У мене болить голова і спина."
:::

## Summary

Being able to communicate your symptoms clearly is one of the most practical skills you can learn. The health toolkit you have built covers the most essential medical situations. 

You now know the vocabulary for your core body parts. Your head is **голова**, your throat is **горло**, your back is **спина**, and your stomach is **живіт**. The word **рука** refers to your entire arm and hand, while **нога** refers to your whole leg and foot. You also learned **око** (eye), **вухо** (ear), **зуб** (tooth), and **ніс** (nose). 

The most critical phrase for describing pain is **у мене болить**. Adding any body part to this phrase forms a complete and natural Ukrainian sentence. 

*   **У мене болить спина.** (My back hurts.)
*   **У мене болить вухо.** (My ear hurts.)

General illnesses follow a similar pattern. You report a fever by saying **у мене температура**, a cough by saying **у мене кашель**, and a runny nose by saying **у мене нежить**. To describe your overall condition, you state **мені погано** (I feel bad) or specify that you are unwell by saying **я хворий** if you are a man, or **я хвора** if you are a woman.

At the doctor's office, the physician will typically ask **Що у вас болить?** (What hurts you?). You respond directly with your symptoms. At the pharmacy, you request medication using the polite phrase **дайте, будь ласка** (give me, please) followed by the type of medicine.

*   **Дайте таблетки від головного болю, будь ласка.** (Give me pills for a headache, please.)
*   **Дайте таблетки від кашлю, будь ласка.** (Give me pills for a cough, please.)
*   **Дайте краплі від нежиті, будь ласка.** (Give me drops for a runny nose, please.)

:::quiz
title: "Обери логічну відповідь (Choose the logical response)"
---
- q: "У мене болить голова."
  o: ["Ось таблетки від головного болю.", "Ось краплі від нежиті.", "Випийте сироп від кашлю."]
  a: 0
- q: "У мене сильний кашель."
  o: ["Вам потрібні таблетки від кашлю.", "Ось краплі для носа.", "У мене болить зуб."]
  a: 0
- q: "Що у вас болить?"
  o: ["У мене болить горло.", "Я лікар.", "Де аптека?"]
  a: 0
- q: "Добрий день. Дайте, будь ласка, щось від нежиті."
  o: ["Ось краплі, будь ласка.", "У мене болить спина.", "Це таблетки від головного болю."]
  a: 0
:::

**Deterministic word count: 1536 words** (calculated by pipeline, do NOT estimate manually)

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

List every exercise block (`:::quiz`, `:::fill-in`, `:::match-up`, `:::group-sort`, `:::true-false`). These are filled exercises — a deterministic tool converted placeholders to real content.

For each exercise, check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?
- Are there enough items per exercise? (check against plan's `activity_hints`)

Also check: Are there enough exercises total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercises are generated by a deterministic tool from the writer's placeholders. If the exercise LOGIC is wrong (e.g., matching unrelated items), flag it — the tool's input data needs fixing. If the exercise FORMAT looks unusual, that is expected (the tool uses a specific DSL syntax).

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | Every content_outline point covered? Section word budgets respected (±10%)? All plan references used? |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | PPP (Present→Practice→Produce) applied? Textbook pedagogy used (Большакова, Захарійчук)? Grammar scope respected (no A2 in A1)? |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | Placeholders specific enough? Test the right skills? Placed after relevant teaching? Match plan's activity_hints? Sufficient items? |
| 6 | **Engagement & tone** | 10% | Interesting for teens/adults? Authoritative but warm (like a skilled teacher)? No LLM filler ("Good news!", "Don't panic!", "Fun fact!")? Cultural hooks? |
| 7 | **Structural integrity** | 5% | All H2 headings from plan present? Word count in range? No duplicate sections? No meta-commentary? Clean markdown? |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | Dialogues natural and culturally appropriate? Real situations, real responses? Speaker roles clear? Not stilted or textbook-robotic? |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Critical = module cannot ship. Major = quality below standard. Minor = polish item.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero critical findings, at most minor issues |
| **REVISE** | Has major findings but no criticals — fixable without rewrite |
| **REJECT** | Has any critical finding — fundamental problems requiring rewrite |

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

Verified: 101 words | Not found: 0 words

All 101 other words are confirmed to exist in VESUM.

</vesum_verification>