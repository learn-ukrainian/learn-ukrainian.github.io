# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-045
level: A2
sequence: 45
slug: adjective-suffixes-types
version: '2.0'
title: Adjective Suffixes — Types
subtitle: Materials and Origins
focus: grammar
pedagogy: PPP
phase: A2.3
word_target: 2000
objectives:
- Learner can describe what things are made of
- Learner can describe origin and nationality
- Learner can form abstract adjectives
- Learner can classify adjectives by meaning
- Learner can handle consonant mutations in origin suffixes
sources:
- name: Ukrainian State Standard 2024 - Adjective Morphology
  url: https://mon.gov.ua/
  type: reference
  notes: Standards for material and origin adjective suffixes at A2
- name: Ukrainian Word Formation - Consonant Changes
  url: https://uk.wikipedia.org/wiki/Чергування_приголосних_при_творенні_прикметників
  type: reference
  notes: Rules for mutations like k->ts, h->z when adding -sk-
content_outline:
- section: Вступ (Introduction)
  words: 300
  points:
  - 'From Nouns to Identity: The magic of the material bridge — introduce core suffixes -ськ- and -н- aligned with State Standard
    §4.2.1.2 requirements for A2 communicative intentions (describing objects and origins)'
  - 'Why ''wooden'' is more than a word: Use the high-frequency example «дерев''яний» to illustrate the concept; connect to
    the theme of traditional craftsmanship and collocations like «дерев''яний стіл», «дерев''яний будинок», and «дерев''яна
    ложка»'
- section: 'Презентація: Матеріали та походження (Presentation: Materials and Origins)'
  words: 550
  points:
  - 'The Materialist Logic: Heuristic for choosing suffixes — use -ян- for natural or traditional materials (вовняний, дерев''яний,
    скляний) vs -ов- for standard/processed materials (металевий, пластиковий, дубовий)'
  - 'The Geography of Suffixes: -Ськ- and its many faces — focus on high-frequency city adjectives: київський (київський торт,
    київський князь), львівський (львівська кава, львівський сирник); introduce cultural context of Київська Русь and львівська
    ґвара'
  - 'The ''Big Three'' Consonant Mutations: Crossing the bridge from Prague to Odesa — focus on A2-appropriate mutations:
    к/ч/ц -> цьк, г/ж/з -> зьк, х/ш/с -> ськ; use the mnemonic anchor: Прага -> Празький to prevent common mutation failures'
  - 'Suffix Selection Heuristics: Managing -ов- vs -ев- — explain dependency on hard/soft stems and stress (e.g., hard stem
    ''дуб'' -> дубовий vs soft stem ''поле'' -> польовий); highlight «домашній» as a very high-frequency soft-suffix example'
- section: 'Культурний контекст: Традиційні вироби (Cultural Context: Traditional Crafts)'
  words: 400
  points:
  - 'Яворівська забавка (Yavoriv Toy): A wooden hook — explain the use of «осика» (aspen) in traditional wooden toys from
    the Lviv region, believed to drive away evil and decorated with «вербівка» patterns'
  - 'Гуцульський ліжник (Hutsul Lizhnyk): The warmth of wool — describe the heavy woolen blanket made of «овеча вовна» (sheep''s
    wool), famous for its therapeutic ''biting'' texture and role in weddings and ceremonies'
- section: Практика та аналіз помилок (Practice and Error Analysis)
  words: 475
  points:
  - 'Material conversion drills: Focus on converting nouns to adjectives with correct suffix choices — скло -> скляний (скляна
    пляшка), залізо -> залізний (залізні двері), вовна -> вовняний'
  - 'City-to-Adjective mutation challenge: Targeted drills on the ''Big Three'' patterns; focus on preventing the common error
    of simply adding -ськ- without mutation (e.g., correct *Празький* vs error *Прагський*)'
  - 'Stress and Stem Sensitivity: Drills contrasting hard and soft stems for -ов-/-ев- selection (дубовий vs польовий) to
    minimize stress-dependent confusion'
- section: Діалог та продукція (Dialogue and Production)
  words: 275
  points:
  - 'At the handicraft fair: Discussing wooden toys and woolen shawls — production task using materials vocabulary to describe
    artisanal items (яворівська забавка, гуцульський ліжник)'
  - 'Identity and Origins: Describing one''s home and city using -ськ- and -н- adjectives — describing ''домашній затишок''
    (home comfort) and local landmarks with origin suffixes'
vocabulary_hints:
  required:
  - дерев'яний (wooden) — дерев'яний стіл, дерев'яний будинок, дерев'яна ложка; High frequency
  - скляний (glass adj.) — скляна пляшка, скляний посуд, скляні двері; Medium frequency
  - залізний (iron adj.) — залізні двері, залізний характер (idiom), залізниця (noun); High frequency
  - київський (Kyiv adj.) — київський торт, київський князь, Київська Русь; High frequency
  - львівський (Lviv adj.) — львівська кава, львівський сирник, львівська ґвара; High frequency
  - домашній (home/domestic) — домашнє завдання, домашня тварина, домашній затишок; Very High frequency
  - вовняний (woolen) — вовняний светр, вовняна ковдра, вовняні шкарпетки; Medium frequency
  recommended:
  - осика (aspen) — traditional wood for Yavoriv toys, believed to drive away evil
  - ліжник (lizhnyk) — Hutsul woven blanket made of sheep's wool, famous for therapeutic 'biting' texture
  - овеча вовна (sheep's wool) — the raw material for traditional Ukrainian textiles
  - яворівська забавка (Yavoriv toy) — traditional wooden toy decorated with willow branch patterns
persona:
  voice: Encouraging Cultural Guide
  role: Art Gallery Curator
module_type: grammar
immersion: 60-75% Ukrainian
prerequisites:
- adjective-suffixes-qualities
connects_to:
- root-families-i
grammar:
- Вступ
- Матеріали та походження
- Традиційні вироби
register: розмовний
activity_hints:
- type: quiz
  focus: Identify correct forms
  items: 10
- type: fill-in
  focus: Complete with correct grammar
  items: 8
- type: match-up
  focus: Match forms to categories
  items: 10
- type: error-correction
  focus: Find and fix errors
  items: 6
- type: group-sort
  focus: Classify by grammatical feature
  items: 8
- type: essay-response
  focus: Write using target structures

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

Research **Adjective Suffixes — Types** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Adjective Suffixes — Types

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
