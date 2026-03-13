# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-065
level: A2
sequence: 65
slug: rental-accommodation
version: '2.0'
title: Rental Accommodation
subtitle: Finding an Apartment
focus: practical
pedagogy: PPP
phase: A2.6 [Practical]
word_target: 2000
objectives:
- Learner can understand rental ads
- Learner can ask about apartment details
- Learner can discuss lease terms
- Learner can talk about utilities and furniture
content_outline:
- section: Вступ (Introduction)
  words: 275
  points:
  - 'Overview of the Ukrainian rental market based on State Standard §3.2: emphasis on ''винаймання квартири'' (renting) versus
    ''приватний будинок'' (private house).'
  - 'Cultural hook: «Без посередників» (No middlemen) — explain why Ukrainians actively avoid real estate agents to save 50-100%
    commission fees; introduce collocations «комісія рієлтора», «послуги рієлтора».'
  - 'Cultural hook: «Перший і останній місяць» — explain the standard practice of paying the first month and a security deposit
    upfront in cash; distinction between «застава» and «депозит».'
- section: Презентація лексики (Vocabulary Presentation)
  words: 325
  points:
  - 'Core verbs: distinction between «здавати» (to rent out/give) and «знімати/орендувати» (to rent/take). Learner error fix:
    correct ''Я хочу здати квартиру'' (wrong for a tenant) to ''Я хочу зняти квартиру''.'
  - 'Distinction between housing types: clearly distinguish «кімната» (room in shared flat) from «однокімнатна квартира» (1-room
    apartment) to avoid English speakers'' confusion with ''studio''.'
  - 'Frequency focus: introduce high-frequency words «оренда», «квартира», and «власник» with collocations like «від власника»,
    «я власник».'
- section: 'Контекстне читання: Оголошення (Reading Context: Ads)'
  words: 325
  points:
  - Analysis of rental advertisements using vocabulary like «здається», «довгострокова оренда», «подобова оренда».
  - 'Cultural hook: «Євроремонт» (modern standards like plastic windows/laminate) vs «Радянський стан» (Soviet condition)
    — explain these as critical value markers in Ukrainian ads.'
  - 'Identifying features: «поверх» (floor), «площа» (area), and the register of abbreviations used in ads.'
- section: 'Діалог: Огляд квартири (Dialogue: Viewing the Apartment)'
  words: 400
  points:
  - 'Asking about features: use collocations «квартира з меблями», «без меблів», «техніка». Align with State Standard §3.2
    requirements for furniture and interior items.'
  - 'The #1 tenant question: drill the essential inquiry «А комунальні включені?» or «Скільки за комунальні?».'
  - 'Viewing etiquette and collocations: «огляд квартири», «дзвонити власникові», «коли можна подивитися?».'
- section: Комунальні послуги та умови (Utilities and Conditions)
  words: 275
  points:
  - 'Breakdown of «комунальні послуги»: газ, вода, електрика, опалення (heating). Explain the ''X грн + комунальні'' pricing
    model common in Ukraine.'
  - 'Learner error fix: drill the pattern ''плюс комунальні'' vs ''комунальні включені'' to prevent the assumption that rent
    covers everything.'
  - 'Utility management: introduce «лічильники» (meters) and «платити за комунальні».'
- section: Укладання договору (Signing the Agreement)
  words: 200
  points:
  - 'Legal vocabulary: «підписати договір оренди», «умови договору», «термін оренди».'
  - 'Financial terms: «страховий депозит» (security deposit), «повернути депозит», and the synonym «застава».'
- section: Практика та розповідь (Practice and Narrative)
  words: 200
  points:
  - 'Grammar focus: Learner error fix — Case confusion with Location (Locative) vs Motion (Accusative). Drill moving «в нову
    квартиру» (Acc) vs living «у новій квартирі» (Loc).'
  - 'Narrative production: a story about successfully finding an apartment «без посередників» and moving in, reinforcing the
    Accusative case for destination.'
vocabulary_hints:
  required:
  - оренда (rent) — довгострокова ~, подобова ~, вартість ~и, здати в ~у; High frequency
  - 'зняти (to rent/take) — ~ квартиру, ~ житло, ~ кімнату, ~ без посередників; Note: learner error to use ''здати'''
  - квартира (apartment) — однокімнатна ~, ~ з євроремонтом, огляд ~и, жити у ~і; High frequency
  - власник (owner) — від ~а, дзвонити ~у, я ~; Medium frequency
  - 'депозит (deposit) — страховий ~, повернути ~; Synonym: застава'
  - 'комунальні (utilities) — платити за ~, ~ включені, плюс ~, ~ послуги; Critical phrase: ''А комунальні?'''
  - договір (contract) — ~ оренди, підписати ~, умови ~у
  - меблі (furniture) — квартира з ~ями, без ~ів, нові ~; Standard §3.2
  recommended:
  - здається (for rent) — phrase used at the start of ads
  - кімната (room) — зняти ~у; distinguish from 1-room apartment
  - євроремонт (Euro-renovation) — modern standard renovation
  - радянський стан (Soviet condition) — old/unrenovated condition
  - рієлтор (realtor) — комісія ~а, без ~а, послуги ~а
  - застава (security deposit) — standard term for upfront security payment
  - посередник (middleman/agent) — без ~ів (very common search filter)
  - техніка (appliances) — побутова ~, квартира з ~ою
activity_hints:
- type: match-up
  focus: Rental vocabulary
  items: 25
- type: reading
  focus: Negotiate rental terms
  items: 10
connects_to:
- a2-66 (Scheduling Appointments)
- a2-51 (Home and Furniture)
prerequisites:
- a2-64 (Hotel Accommodation)
persona:
  voice: Encouraging Cultural Guide
  role: Landlord
grammar:
- Rental vocabulary (оренда, власник, орендар)
- Discussing utilities (комунальні послуги)
- Contract and lease terms
register: розмовний
immersion: 75-90% Ukrainian

```

**Level constraints quick-ref:**

```
# A2 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `2000`, `TARGET: 70-90% Ukrainian.
LANGUAGE ROLES:
- PRIMARY: Ukrainian for everything.
- ENGLISH: Only in vocabulary tables and one-line grammar notes where absolutely necessary.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English.
A2 register. Concrete everyday vocabulary. No literary language, no metaphors. Near-full Ukrainian immersion. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only. Full aspect pairs. No participles.`, ``, etc.

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

Research **Rental Accommodation** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Rental Accommodation

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
