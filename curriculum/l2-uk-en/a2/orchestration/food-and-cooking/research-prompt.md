# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-050
level: A2
sequence: 50
slug: food-and-cooking
version: '2.0'
title: Food and Cooking
subtitle: In the Kitchen
focus: vocabulary
pedagogy: PPP
phase: A2.5 [Vocabulary Expansion]
word_target: 2000
objectives:
- Learner can follow a simple recipe in Ukrainian
- Learner can describe cooking methods
- Learner can use kitchen vocabulary
- Learner can give instructions using the imperative
content_outline:
- section: Вступ (Introduction)
  words: 300
  points:
  - 'The core principle of Ukrainian hospitality: «Чим хата багата, тим і рада» (What the house is rich in, it is glad to
    offer); explanation of offering guests everything available, starting with bread and salt (хліб-сіль).'
  - 'Overview of the module objectives aligned with State Standard §3.10: identifying kitchen equipment (посуд), cooking methods
    (способи приготування), and traditional dishes.'
  - Introduction to Borshch as UNESCO Intangible Cultural Heritage; the concept that it is more than a soup, but a defining
    cultural process involving specific steps like 'засмажка'.
- section: 'Лексика: Кухня та приготування (Vocabulary: Kitchen and Cooking)'
  words: 475
  points:
  - 'High-frequency kitchen equipment based on research: каструля (pot), сковорода (pan), духовка (oven), ніж (knife); collocations:
    велика каструля, розігріта сковорода, гаряча духовка.'
  - 'Core cooking verbs and their nuances: варити (to boil/cook in liquid), смажити (to fry), пекти (to bake), різати (to
    cut); collocations: варити борщ, смажити м''ясо, пекти хліб, різати овочі.'
  - 'Vocabulary nuance note: distinguishing ''варити'' (specific to liquids/boiling) from the general ''готувати'' (to prepare);
    instruction that one does not ''варити'' a sandwich or salad.'
  - 'Tastes and contrasts: солодкий (sweet) and солоний (salty); using the versatility of varenyky fillings (cherry vs. potato)
    to illustrate the contrast.'
- section: 'Граматика: Орудний відмінок та Наказовий спосіб (Grammar: Instrumental Case and Imperative Mood)'
  words: 500
  points:
  - 'Grammar focus §4.2.2.5: Instrumental case for tools and instruments. Critical correction of common learner error: using
    the preposition ''з'' for tools (e.g., *ріжу з ножем). Correct form: різати ножем (Instrumental ONLY).'
  - 'Comparative table of Nominative vs. Instrumental for all three genders to prevent case ending confusion: ніж -> ножем
    (masc), ложка -> ложкою (fem), масло -> маслом (neut).'
  - 'Distinguishing ''Instrumental for tools'' (NO preposition) from ''Instrumental for accompaniment'' (WITH preposition
    ''з''/''із''): різати ножем vs. чай із лимоном or вареники зі сметаною.'
  - 'Imperative mood for recipes and instructions (§4.2.3.2). Target 2nd person singular forms: наріж (cut), додай (add),
    звари (boil), перемішай (mix).'
- section: 'Культура: Традиційні страви (Culture: Traditional Dishes)'
  words: 425
  points:
  - 'Deep dive into Borshch culture: the ''засмажка'' process (sautéing beets, carrots, and onions) and the diversity of family
    recipes. Reflection on why every recipe is considered ''authentic''.'
  - 'Varenyky versatility: main dishes (potato, cabbage, meat) vs. desserts (cherries, cottage cheese). The ritual of making
    varenyky as a family activity.'
  - Table etiquette and hospitality phrases in the context of a Ukrainian home; the role of the host as someone who 'is glad'
    to share food.
- section: Практика та Підсумок (Practice and Summary)
  words: 300
  points:
  - 'Dialogue practice: cooking with a grandmother. Contextual use of kitchen vocabulary, instrumental case for tools, and
    imperative mood for following instructions.'
  - Step-by-step recipe construction using sequence markers (спочатку, потім, наприкінці) and imperative verbs (наріж овочі,
    поклади у каструлю).
  - Summary of key §3.10 competencies and a final grammar check on the instrument/accompaniment distinction in the Instrumental
    case.
vocabulary_hints:
  required:
  - 'варити (to boil/cook) — high frequency core verb; specifically for liquids; collocations: варити борщ, варити суп, варити
    каву'
  - 'смажити (to fry) — high frequency; collocations: смажити м''ясо, смажити рибу, смажити картоплю'
  - 'пекти (to bake) — med-high frequency; collocations: пекти пиріг, пекти торт, пекти хліб, пекти печиво'
  - 'різати (to cut) — high frequency; collocations: різати ножем (pure Instrumental), різати овочі, дрібно різати'
  - 'каструля (pot) — household high frequency; usage: велика каструля, у каструлі'
  - 'сковорода (pan) — household high frequency; usage: на сковороді, розігріта сковорода'
  - 'духовка (oven) — household med frequency; usage: у духовці, гаряча духовка'
  - 'рецепт (recipe) — usage: слідувати рецепту, простий рецепт'
  recommended:
  - 'додавати (to add) — core recipe verb; usage: додавати сіль, додавати цукор'
  - 'змішувати (to mix) — usage: змішувати інгредієнти'
  - 'солодкий (sweet) — high frequency; collocations: солодкий чай, солодкі вареники'
  - 'солоний (salty) — high frequency; collocations: солоний огірок, солона страва'
  - 'інгредієнт (ingredient) — usage: свіжі інгредієнти, список інгредієнтів'
  - 'страва (dish) — usage: національна страва, смачна страва'
activity_hints:
- type: match-up
  focus: Kitchen and cooking words
  items: 12
- type: cloze
  focus: Complete cooking instructions
  items: 12
- type: quiz
  focus: Food and cooking vocabulary
  items: 8
- type: unjumble
  focus: Cooking sentences
  items: 8
- type: error-correction
  focus: Kitchen mistakes
  items: 6
- type: group-sort
  focus: Kitchen categories
  items: 16
- type: true-false
  focus: Kitchen facts
  items: 12
- type: translate
  focus: Food words
  items: 8
connects_to:
- a2-51 (Home and Furniture)
prerequisites:
- 'a2-49 (Checkpoint: Word Formation)'
- a1-18 (Food and Shopping)
persona:
  voice: Encouraging Cultural Guide
  role: Hospitable Host
grammar:
- Imperative in recipes (наріж, звари)
- Instrumental for tools (ножем, ложкою)
- Cooking verbs and sequences
register: розмовний
immersion: 60-75% Ukrainian

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

Research **Food and Cooking** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Food and Cooking

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
