# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-063
level: A2
sequence: 63
slug: at-the-pharmacy
version: '2.0'
title: At the Pharmacy
subtitle: Buying Medicine
focus: practical
pedagogy: PPP
phase: A2.6 [Practical]
word_target: 2000
objectives:
- Learner can ask for medicine by symptoms
- Learner can understand dosage instructions
- Learner can read medicine labels
- Learner can discuss side effects
content_outline:
- section: 'Вступ: Українські аптеки (Introduction: Ukrainian Pharmacies)'
  words: 275
  points:
  - 'Cultural hook: Identifying a «чергова аптека» (duty pharmacy) open 24/7, marked by the iconic green cross; explaining
    the infrastructure of Ukrainian pharmacies.'
  - 'Prescription system: The transition to «е-рецепт» (electronic prescription via SMS) since 2022 for antibiotics; distinguishing
    between «безрецептурні ліки» (OTC) and prescription-only meds.'
  - 'Learner error: Clarifying that «ліки» is pluralia tantum (always plural); correcting the common mistake of treating it
    as singular (e.g., «Ці ліки», not «Це ліки»).'
  - 'Vocabulary note: «ліки» is the preferred standard Ukrainian form (pluralia tantum); «лікарство» is also in VESUM as standard
    Ukrainian (not a Russicism) but «ліки» is more common and stylistically preferred.'
- section: 'Пошук ліків: Симптоми та запити (Asking for Medicine: Symptoms and Requests)'
  words: 500
  points:
  - 'Grammar drill: Using «від» + Genitive case for ailments (State Standard §4.2.2.2); correcting the error of using «для»
    (e.g., «ліки від кашлю» vs incorrect «ліки для кашлю»).'
  - 'Cultural hook: Ukrainian preference for «фітотерапія» (herbal remedies); discussing common natural treatments like tea
    with «калина» (viburnum) or herbal syrups.'
  - 'Functional language: Key phrases for describing symptoms such as «У мене болить...» and «Мені потрібно щось від...» for
    specific conditions like cold («застуда») or headache («біль голови»).'
  - 'Vocabulary expansion: Categorizing common OTC meds: «жарознижувальні» (antipyretics), «знеболювальні» (painkillers),
    and «таблетки для розсмоктування» (lozenges).'
- section: Інструкції та етикетки (Instructions and Labels)
  words: 425
  points:
  - 'Standard vs Colloquial usage: Defining the formal «приймати ліки» used in labels versus the colloquial «пити таблетки»
    found in daily speech.'
  - 'Reading labels: Identifying key terms on packaging: «дозування» (dosage), «застосування» (application), and «протипоказання»
    (contraindications).'
  - 'Grammar in context: Understanding instructions using the Imperative mood (State Standard §4.2.3.2) found on medicine
    leaflets.'
  - 'Warning signs: Recognizing storage instructions like «зберігати в недоступному для дітей місці» and expiry dates.'
- section: Дозування та побічні ефекти (Dosage and Side Effects)
  words: 475
  points:
  - 'Precision in dosage: Phrases for frequency such as «раз на день», «двічі на добу», and the specific construction «приймати
    по одній таблетці».'
  - 'Meal-related instructions: Differentiating between «до їди» (before meals), «під час їди» (during meals), and «після
    їди» (after meals).'
  - 'Side effects and allergies: Essential vocabulary for «побічні ефекти» and «алергія»; discussing interactions with other
    substances.'
  - 'Medical forms: Vocabulary for different delivery methods: «капсула» (capsule), «сироп» (syrup), «мазь» (ointment), and
    «краплі» (drops).'
- section: 'Практика: Діалог в аптеці (Practice: Pharmacy Dialogue)'
  words: 325
  points:
  - 'Roleplay: Buying medicine for a cold using the «від + Genitive» construction and asking about side effects.'
  - 'Authenticity check: A scenario where the learner asks for antibiotics and the pharmacist explains the requirement for
    an «е-рецепт».'
  - 'Consultation: Asking the pharmacist («фармацевт») for a recommendation between a synthetic drug and a herbal alternative.'
vocabulary_hints:
  required:
  - 'аптека (pharmacy) — collocations: чергова аптека (24/7), купити в аптеці; high frequency'
  - 'ліки (medicine) — always plural! «лікарство» is also standard but «ліки» preferred; collocations: ліки від застуди, приймати ліки'
  - 'таблетка (pill) — collocations: таблетка від голови, приймати по одній таблетці, таблетки для розсмоктування'
  - 'рецепт (prescription) — collocations: електронний рецепт (е-рецепт), ліки за рецептом, виписати рецепт'
  - 'біль (pain) — use with ''від'' for medicine: таблетки від болю; note gender (masculine)'
  - 'кашель (cough) — collocations: сироп від кашлю, ліки від кашлю'
  - 'температура (fever) — collocations: жарознижувальні (antipyretics), висока температура'
  - приймати (to take) — standard medical verb for dosage; distinguish from colloquial 'пити'
  recommended:
  - 'сироп (syrup) — collocation: сироп від кашлю'
  - 'мазь (ointment) — usage: наносити мазь (to apply ointment)'
  - дозування (dosage) — note the suffix -ння
  - побічний ефект (side effect) — high frequency in warnings
  - протипоказання (contraindication) — technical term for labels
  - 'алергія (allergy) — usage: алергія на (allergy to + Acc)'
  - фармацевт (pharmacist) — the professional at the counter
  - застосування (application/usage) — formal term on packaging
activity_hints:
- type: match-up
  focus: Pharmacy vocabulary
  items: 25
- type: fill-in
  focus: Complete medicine instructions
  items: 15
connects_to:
- a2-64 (Hotel Accommodation)
prerequisites:
- a2-39 (Health and Body)
persona:
  voice: Encouraging Cultural Guide
  role: Experienced Pharmacist
grammar:
- Asking for specific medicine by symptoms
- Understanding dosage instructions
- Side effects and warnings vocabulary
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

Research **At the Pharmacy** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: At the Pharmacy

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
