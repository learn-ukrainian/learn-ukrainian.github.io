# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-039
level: A2
sequence: 39
slug: health-and-body
version: '2.0'
title: Health and Body
subtitle: Body Parts, Symptoms, Doctor Visits & Folk Remedies
focus: vocabulary
pedagogy: PPP
phase: A2.3
word_target: 2000
objectives:
- Learner can name major body parts and their plurals
- Learner can use the боліти construction correctly (singular and plural)
- Learner can describe symptoms and illnesses
- Learner can express physical states using Dative (Мені погано/добре)
- Learner can navigate a doctor consultation in formal register
- Learner can understand diagnosis, prescriptions, and sick leave
- Learner can discuss folk remedies and healthy lifestyle
sources:
- name: Ukrainian State Standard 2024 - Health and Hygiene
  url: https://mon.gov.ua/
  type: reference
  notes: Standards for describing physical conditions, health communication at A2 (§3.12, §4.2.2.3, §4.2.3.2)
content_outline:
- section: Моє тіло (My Body)
  words: 300
  points:
  - 'Core body parts vocabulary: голова, рука, нога, живіт, спина, горло, зуб, серце, око, вухо. Gender of each noun explicitly
    marked (голова-f, живіт-m, серце-n).'
  - 'Irregular plurals as A2 grammar point: око→очі, вухо→вуха, рука→руки. Adjective agreement drill: червоне горло, хворий
    зуб, ліва рука.'
  - 'Internal organs briefly: серце (heart), шлунок (stomach), легені (lungs) — passive recognition, not active production.'
  - 'Cultural idiom: «Від щирого серця» (from the bottom of my heart) — anatomical terms in everyday expressions.'
- section: У мене болить... (It Hurts...)
  words: 375
  points:
  - 'Primary grammar: «У мене болить» + Nominative (singular) vs «У мене болять» + Nominative (plural). Drill: болить зуб
    / болять зуби, болить око / болять очі.'
  - 'Learner error prevention: block the English transfer «Я болю голову» — боліти is intransitive; the body part is the grammatical
    subject.'
  - 'Dative states (§4.2.2.3): «Мені погано/добре/нудно/холодно/жарко/запаморочилось». Correct the common error «Я погано»
    → «Мені погано».'
  - 'Distinction: боліти (specific pain, intransitive) vs хворіти на + Accusative (to be sick with a disease: «хворіти на
    грип»). Never «я болю грип».'
  - 'Register note: literary standard «У мене болить...» vs poetic/emotional «Мені болить за Україну» — dative reserved for
    emotional pain.'
- section: Симптоми та хвороби (Symptoms and Illnesses)
  words: 275
  points:
  - 'Symptom vocabulary: температура (висока/низька), кашель (сухий/вологий), нежить, біль (гострий/тупий), слабкість, запаморочення.'
  - 'Common illnesses: застуда, грип, алергія, ангіна. False friend alert: «ангіна» = tonsillitis (NOT angina pectoris / heart
    attack = серцевий напад).'
  - 'Reporting to doctor or friend: «У мене кашель / нежить / висока температура», «Мене нудить», «Я хворію на грип».'
  - 'Measurement: «міряти температуру» (take temperature), «вимірювати тиск» (measure blood pressure).'
- section: У лікаря (At the Doctor)
  words: 450
  points:
  - 'Appointment booking: «записатися на прийом» via phone or online; the «сімейний лікар» (family doctor) + «декларація»
    system explained briefly.'
  - 'Institutional clarity: «поліклініка» (outpatient — where you go for checkups) vs «лікарня» (hospital — inpatient). Fix
    the error «я йду в лікарню» for a routine visit → «я йду в поліклініку» / «я йду до лікаря».'
  - 'Cultural note: «бахіли» (blue plastic shoe covers) — mandatory in clinics. Entering in street shoes is a social faux
    pas.'
  - 'Doctor consultation: «Що вас турбує?», «Де болить?», «Як давно?» — formal Ви register mandatory with medical staff.'
  - 'Examination imperatives (§4.2.3.2): «Дихайте / Не дихайте», «Відкрийте рот», «Покажіть язик», «Роздягніться до пояса».
    Imperative Ви-forms.'
  - 'Diagnosis and prescription: «поставити діагноз», «виписати рецепт», «приймати ліки двічі на день», «до/після їжі».'
  - 'Sick leave: «взяти лікарняний» / «бути на лікарняному» — bureaucratic necessity; tests: «здати аналізи» (blood/urine
    tests).'
  - 'Emergency: «Викличте швидку!» (Call an ambulance! — 103); distinguishing emergency (швидка допомога) from house call
    (викликати лікаря додому).'
- section: Народна мудрість і здоровий спосіб життя (Folk Wisdom and Healthy Living)
  words: 325
  points:
  - 'Cultural hook: «У здоровому тілі — здоровий дух» — health as a primary value and smalltalk topic in Ukrainian culture.'
  - 'Folk remedies (taught ONCE, thoroughly): чай з малиною (universal cold remedy — every household has raspberry jam), калина
    (viburnum — cultural symbol with healing properties), мед з молоком (honey with milk for sore throat), чай з ромашки/м''яти
    (herbal teas). Textbook connection: Grade 1 Zaharijchuk — звіробій «лікує сто хвороб».'
  - 'Загартовування (hardening/toughening): Grade 3 Savchenko — the boy who skis and does not get sick while the witch catches
    cold. «Я загартований! Я на лижах бігаю».'
  - 'Healthy lifestyle vocabulary: «робити зарядку» (morning exercise), «правильне харчування» (proper nutrition), «здоровий
    сон» (healthy sleep). Advice construction: «варто/треба» + infinitive: «Варто більше відпочивати».'
  - 'Proverb: «Здоров''я — найбільше багатство» (Health is the greatest wealth).'
- section: 'Практика: Від симптому до одужання (Practice: From Symptom to Recovery)'
  words: 275
  points:
  - 'Full narrative: A learner feels the first symptoms (кашель, температура) → calls the clinic (записатися на прийом) →
    puts on бахіли → doctor examines (Дихайте! Покажіть!) → receives діагноз (застуда) → gets рецепт → buys ліки → recovers
    with бабусина калина. Transition to next module: «Купіть ці ліки в аптеці» → at-the-pharmacy.'
  - 'Cultural parallel: Тетяна Майданович «Телефонна розмова» — the granddaughter calling sick grandma, offering bees instead
    of injections. Humor as a teaching tool.'
  - 'Role-play: Calling a friend to report being sick (informal register) vs calling the clinic (formal register). Synthesis
    of all section constructions.'
vocabulary_hints:
  required:
  - 'голова (head) — f; collocations: болить голова, головний біль, крутиться голова'
  - 'рука (arm/hand) — f; collocations: права/ліва рука, зламати руку'
  - 'нога (leg/foot) — f; collocations: болять ноги, зламати ногу'
  - 'живіт (stomach/belly) — m; usage: болить живіт'
  - 'горло (throat) — n; collocations: червоне горло, болить горло'
  - 'спина (back) — f; collocations: болить спина, біль у спині'
  - 'зуб (tooth) — m; collocations: болить зуб, зубний біль'
  - 'серце (heart) — n; idiom: від щирого серця; medical: боліти в серці'
  - 'боліти (to hurt) — impersonal: у мене болить + Nom (sg) / болять + Nom (pl); intransitive — the body part is the subject'
  - хворіти на (to be sick with) — хворіти на грип/застуду; never «я болю грип»
  - 'температура (fever/temperature) — collocations: висока температура, міряти температуру'
  - 'кашель (cough) — m; collocations: сильний кашель, сухий кашель'
  - 'лікар (doctor) — collocations: сімейний лікар, записатися до лікаря, викликати лікаря'
  - поліклініка (outpatient clinic) — where you go for non-emergencies; ≠ лікарня (hospital)
  - 'рецепт (prescription) — виписати рецепт; learner error: ≠ чек (receipt)'
  - записатися на прийом (to make an appointment) — high frequency medical phrase
  recommended:
  - око/очі (eye/eyes) — irregular plural; болять очі
  - вухо/вуха (ear/ears) — irregular plural; болить вухо
  - нежить (runny nose) — m; мати нежить, засоби від нежитю
  - застуда (cold) — f; лікувати застуду, застудитися
  - грип (flu) — m; хворіти на грип
  - діагноз (diagnosis) — поставити діагноз, підтвердити діагноз
  - лікарняний (sick leave certificate) — взяти лікарняний, бути на лікарняному
  - аналіз (test) — здати аналізи, аналіз крові
  - калина (viburnum) — чай з калиною; traditional folk remedy
  - малина (raspberry) — чай з малиною; universal cold remedy
  - швидка допомога (ambulance) — Викличте швидку! (103)
  - бахіли (shoe covers) — mandatory in clinics; cultural etiquette
  - здоровий (healthy) — здоровий спосіб життя, у здоровому тілі
  - 'варто (it is worth) — advice: варто відпочивати, варто піти до лікаря'
  - алергія (allergy) — алергія на + Acc; алергічна реакція
  - 'ангіна (tonsillitis) — false friend: ≠ angina pectoris (серцевий напад)'
activity_hints:
- type: match-up
  focus: Body parts vocabulary and symptoms
  items: 25
- type: fill-in
  focus: боліти/болять construction (singular vs plural agreement)
  items: 15
- type: fill-in
  focus: State expressions with Dative (Мені погано/добре/холодно)
  items: 10
- type: quiz
  focus: Doctor consultation — formal register and imperatives
  items: 12
- type: fill-in
  focus: Medical vocabulary (рецепт, діагноз, прийом, аналізи)
  items: 10
persona:
  voice: Encouraging Cultural Guide
  role: School Nurse
grammar:
- body parts (gender, irregular plurals, adjective agreement)
- impersonal pain construction (у мене болить/болять + Nom)
- state expressions with Dative (Мені погано/добре/холодно)
- хворіти на + Accusative vs боліти (intransitive)
- medical imperatives in Ви-form (Дихайте!, Покажіть!)
- advice structures (треба/варто + infinitive)
register: розмовний
module_type: vocabulary
immersion: 60-75% Ukrainian
prerequisites:
- time-clauses
connects_to:
- checkpoint

```

**Level constraints quick-ref:**

```
# A2 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `2000`, `TARGET: 55-75% Ukrainian.
LANGUAGE ROLES:
- PRIMARY: Ukrainian for all content — dialogues, examples, section intros, cultural context.
- ENGLISH: Only for abstract grammar concepts that need explicit explanation.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English. Dialogues, examples, section intros all stay Ukrainian-only.
A2 register. Concrete everyday vocabulary. No literary language, no metaphors. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only. Aspect pairs introduced. No participles.`, ``, etc.

## Grammar Scope

**Allowed:** All 7 cases. Simple subordinate clauses (який/що/коли). Aspect pairs introduced.
Max 15 words per Ukrainian sentence. Max 2 clauses per sentence.

**Forbidden:** Participles. Complex subordinate clauses.

## Immersion Strategy (A2)

A2 uses graduated immersion (50-90%) across three bands:

| Band | Modules | Target | English used for |
|------|---------|--------|-----------------|
| Core grammar | M01-20 | 45-65% | Grammar theory (cases, aspect) |
| Applied grammar | M21-50 | 55-75% | Abstract concepts only |
| Consolidation | M51-70 | 70-90% | Vocabulary tables only |

**Critical rule:** NEVER mix languages within a sentence at A2.
Each sentence is 100% Ukrainian OR 100% English.
Ukrainian paragraph first, then English translation paragraph below if needed.

## A2-Specific Writing Notes

- No Latin transliteration — stress marks (´) only
- No IPA or phonetic brackets
- Register: A2 only. Concrete everyday vocabulary (їсти, ходити, купувати)
- No literary/poetic language, no abstract nouns (почуття, відчуття, стан, сутність)
- No metaphors or figurative speech
- Grammar terms in Ukrainian introduced where relevant (відмінок, називний, etc.)

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `A2` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Health and Body** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

### Your RAG Tools

| Tool | When to use |
|------|-------------|
| `search_text` | Find how this topic is taught in Ukrainian textbooks |
| `verify_words` | Check vocabulary exists in VESUM dictionary |
| `query_grac` mode=`frequency` | Get word frequency data |
| `query_wikipedia` mode=`summary` | Quick fact-check for cultural hooks |

### Research Requirements

1. **State Standard Reference**: Look up the §section in `state-standard-2024-mapping.yaml`, then read ONLY that section from `UKRAINIAN-STATE-STANDARD-2024.txt`. Quote the relevant requirement.
2. **Vocabulary Frequency**: Use `query_grac` (mode=`frequency`) for key vocabulary items. Do NOT rely on memory alone.
3. **Cultural Hook**: Use `query_wikipedia` to find 1-2 verified cultural facts to anchor the lesson.
4. **Cross-References**: Note which modules this builds on and prepares for (check the plan's `connects_to` field).
5. **Common Errors**: Identify 2-3 common learner mistakes for this grammar point/topic.

### Decolonized Framing

When researching, frame Ukrainian independently — **never as a derivative or variant of Russian:**
- Describe Ukrainian features positively ("Ukrainian has...", "Ukrainian uses...")
- Do NOT use Russian as the baseline for comparisons ("Unlike Russian...", "Different from Russian...")
- If comparing language systems is useful, use non-Russian languages (Polish, Portuguese, etc.)
- Note how topics have been historically misframed by Russian/Soviet sources and provide the Ukrainian-centric perspective

### Research Output Cap
Keep research notes under **1500 words**. Focus on density: facts, dates, quotes, tables — not prose.

### Additional for Core B (B1.6+, B2, C1, C2, PRO)

- Domain-specific vocabulary collocations from professional glossaries (PRO tracks)
- Stylistic/dialectal features from academic sources (C2)
- Register distinctions (formal vs. informal usage)

## Downstream Audit Gates (Phase B content will be checked for)

Plan your outline knowing that Phase B content must pass these gates:
- **Word count**: minimum **2000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Russianisms**: ensure vocabulary_hints and examples avoid banned words (кушати→їсти, получати→отримувати)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Health and Body

## State Standard Reference
§{section_number}: "{quoted requirement}"
Alignment: {how this module addresses the standard}

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| ...  | ...               | ...              |

## Cultural Hooks
1. {Verified fact with source}
2. {Verified fact with source}

## Common Learner Errors
1. {Error pattern} → {Correct form} — {Why it happens}
2. ...

## Cross-References
- Builds on: {module slugs}
- Prepares for: {module slugs}

## Multimedia Resources
(If you naturally encountered relevant Ukrainian-language YouTube videos or audio resources during your web research, note them here. Do NOT search specifically for videos — the discover phase handles that. Maximum 3 entries.)
- {Channel — Title — URL — 1-sentence relevance note}
- (none encountered)

## Notes for Content Writing
- {Any additional observations for Phase B}

===RESEARCH_END===
```

## Friction Report (MANDATORY)

After both output blocks, include:

```
===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | STATE_STANDARD_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT fabricate State Standard references — if you can't find the exact §, say so
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
