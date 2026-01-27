# A1 Modules 28-34 Creation Brief

**Agent:** Antigravity
**Task:** Create A1 modules 28-34 (7 modules)
**Parallel with:** Another agent creating M21-27

---

## Your Assignment

Create these 7 modules in `curriculum/l2-uk-en/a1/`:

| # | Filename | Topic |
|---|----------|-------|
| 28 | `28-description-adverbs.md` | Adverbs (manner & frequency) |
| 29 | `29-weather-and-nature.md` | Weather & impersonal constructions |
| 30 | `30-prepositions-iii.md` | Direction vs Location vs Origin |
| 31 | `31-body-and-health.md` | "Болить..." pattern |
| 32 | `32-my-family.md` | Family + **VOCATIVE CASE** (see below) |
| 33 | `33-holidays-and-traditions.md` | Dates, greetings |
| 34 | `34-checkpoint-final-review.md` | A1 Mastery assessment |

---

## CRITICAL: Read These First

Before writing ANY module:

```bash
# 1. Module specs (vocabulary lists, grammar scope)
docs/l2-uk-en/A1-CURRICULUM-PLAN.md    # Search for "Module 28", "Module 29", etc.

# 2. Format and grammar constraints
docs/l2-uk-en/module-prompt.md

# 3. Quality standards (activity counts, sentence complexity)
docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md

# 4. Example of existing A1 module format
curriculum/l2-uk-en/a1/20-checkpoint-navigation.md
```

---

## Special Requirement: Vocative Case in M32

**Ukrainian State Standard 2024 requires vocative basics at A1.**

Add this section to Module 32 (My Family):

```markdown
## Vocative Case (Кличний відмінок)

> [!observe] Pattern Discovery
>
> When calling someone directly, Ukrainian changes the word ending:
> - мама → мамо! (Mom!)
> - тато → тату! (Dad!)
> - друг → друже! (Friend!)

| Nominative | Vocative | Use |
|------------|----------|-----|
| мама | мамо | calling mom |
| тато | тату | calling dad |
| бабуся | бабусю | calling grandma |
| дідусь | дідусю | calling grandpa |
| Оксана | Оксано | calling Oksana |
| друг | друже | calling a friend (m) |
| сестра | сестро | calling sister |

> [!tip] When to Use
> Use vocative when directly addressing someone:
> - Мамо, де ти? (Mom, where are you?)
> - Тату, допоможи! (Dad, help!)
```

Add vocative forms to the vocabulary table for M32.

---

## Module Requirements (A1 Level)

### Structure

```markdown
---
module: [number]
title: [Title]
level: A1
phase: A1.3
---

# [Title]

> [!summary] Learning Goals
> - Goal 1
> - Goal 2

---

# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔwɔ/ | word | noun | n | - |

---

# Grammar

[Explanations with examples]

---

# Activities

[8+ activities]

---

# Summary

[Brief recap]
```

### Quality Standards

| Metric | A1 Requirement |
|--------|----------------|
| Activities | 8+ per module |
| Vocabulary | Use EXACTLY from curriculum plan |
| IPA | Required for all vocabulary |
| Immersion | 30-50% Ukrainian |
| Transliteration | First occurrence only (A1.3 rule) |
| Engagement boxes | 1-2 per module |
| Fill-in sentences | 4-6 words minimum |
| Unjumble sentences | 4-6 words minimum |

### Activity Types (use variety)

- `quiz` - Multiple choice
- `match-up` - Pair matching
- `fill-in` - Gap fill with dropdowns
- `true-false` - Statement validation
- `group-sort` - Category sorting
- `unjumble` - Word reordering

**NO anagrams in A1.3** (only allowed in M01-10)

---

## Vocabulary Rule

**Use EXACTLY the vocabulary from the curriculum plan. No additions, no substitutions.**

Find each module's vocabulary in `A1-CURRICULUM-PLAN.md` under:
```
**Vocabulary (N words):**
word1, word2, word3, ...
```

---

## After Creating Each Module

Run audit to verify:
```bash
python3 scripts/audit_module.py curriculum/l2-uk-en/a1/[filename].md
```

Fix any issues before moving to next module.

---

## Checkpoint Module (M34) Special Notes

M34 is a review/assessment module. It should include:

1. **Self-assessment rubric** with CEFR can-do statements
2. **Comprehensive review activities** covering all A1 content
3. **Production tasks:**
   - Self-introduction monologue prompt
   - "My typical day" paragraph prompt
   - Role-play scenarios (restaurant, doctor)
4. **Mixed grammar review** (all cases, tenses, verb forms)

Vocabulary for M34 is review selection (10 words) - focus on activities.

---

## Coordination

- Another agent is creating M21-27 in parallel
- Work independently - no dependencies between your modules
- After both are done, we'll run full audit and finalize vocabulary

---

## Commands Reference

```bash
# Generate MDX after creation
npm run generate l2-uk-en a1 28

# Generate JSON
npm run generate:json l2-uk-en a1 28

# Run audit
python3 scripts/audit_module.py curriculum/l2-uk-en/a1/28-description-adverbs.md
```

---

## Start

Begin with Module 28 (Adverbs). Read the curriculum plan section first, then create the module.
