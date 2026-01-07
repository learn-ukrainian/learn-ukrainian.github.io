# B1 Checkpoint Module Template

**Purpose:** Reference template for B1 grammar checkpoint modules (M15, M25, M34, M41, M51)

**Based on:** `b1-grammar-module-template.md` — inherits all B1 quality standards

**Related Issue:** [#305](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/305)

---

## Quick Reference Checklist

Before submitting a B1 checkpoint module, verify all items from `b1-grammar-module-template.md` PLUS:

### Checkpoint-Specific Requirements
- [ ] **TTT pedagogy:** Test-Teach-Test structure (comprehensive review)
- [ ] **Word count:** 1200+ words (review content, not new teaching)
- [ ] **Vocabulary:** 30-40 items (review vocabulary from ALL modules in phase)
- [ ] **Activities:** 16+ comprehensive testing activities
- [ ] **Integration:** Complete review of ALL modules in the phase
- [ ] **Self-assessment:** "Чи можете ви..." checklist at end
- [ ] **Immersion:** 100% Ukrainian (English only in vocabulary translations)
- [ ] **No new content:** Checkpoints ONLY review and test existing knowledge

---

## B1 Checkpoint Modules (Grammar Phases Only)

| Checkpoint | Phase | Modules Covered | Focus |
|------------|-------|-----------------|-------|
| M15 | B1.1 | M06-14 | Aspect Mastery |
| M25 | B1.2 | M16-24 | Motion Verbs with Prefixes |
| M34 | B1.3a | M26-33 | Complex Sentences Part 1 (Relatives, Purpose, Conditionals) |
| M41 | B1.3b | M35-40 | Complex Sentences Part 2 (Concessive, Temporal, Reported) |
| M51 | B1.4 | M42-50 | Advanced Grammar (Participles, Passive, Diminutives, Numerals) |

**Note:** B1.5-B1.8 (Vocabulary, Cultural, Integration phases) do NOT have checkpoints. They use content modules instead.

---

## Required Skill Groups (Per Checkpoint)

Each checkpoint tests specific **skill groups** — concrete abilities learners must demonstrate. Activities should target these skills directly.

### M15: Aspect Mastery Checkpoint

| Skill Group | Source | What Learner Can Do |
|-------------|--------|---------------------|
| Aspect in Past | M06-07 | Choose correct aspect for completed vs ongoing actions |
| Aspect in Future | M08-09 | Distinguish буду + infinitive vs perfective future |
| Aspect in Negation | M10 | Use imperfective for general negation, perfective for specific |
| Aspect in Imperatives | M11 | Choose polite (impf) vs urgent (pf) commands |
| Aspect in Infinitives | M12 | Match aspect to context (intention vs general) |
| Verb Pair Formation | M13 | Form aspect pairs: читати/прочитати pattern |
| Integrated Aspect | M14 | Apply all aspect rules in extended text |

### M25: Motion Verbs Checkpoint

| Skill Group | Source | What Learner Can Do |
|-------------|--------|---------------------|
| Unprefixed Motion | M16-17 | Use йти/ходити, їхати/їздити correctly |
| Directional Prefixes | M18-19 | Add в-/ви-, при-/від- for direction |
| Path Prefixes | M20-21 | Use пере-, об-, до- for path type |
| Abstract Motion | M22 | Understand figurative motion (час іде, думки летять) |
| Motion + Aspect | M23 | Combine motion verbs with aspectual meaning |
| Integrated Motion | M24 | Apply all motion patterns in narrative |

### M34: Complex Sentences I Checkpoint

| Skill Group | Source | What Learner Can Do |
|-------------|--------|---------------------|
| Relative який | M26 | Use який in all cases with correct agreement |
| Relative де/куди/звідки | M27 | Form place-based relative clauses |
| Relative коли/що | M28 | Form time and general relative clauses |
| Purpose щоб + Infinitive | M29 | Express purpose with infinitive |
| Purpose щоб + Past | M30 | Express purpose with different subjects |
| Real Conditionals | M31 | Form якщо clauses with correct tense |
| Unreal Conditionals | M32 | Form якби clauses with past tense |
| Mixed Conditionals | M33 | Combine condition types in complex sentences |

### M41: Complex Sentences II Checkpoint

| Skill Group | Source | What Learner Can Do |
|-------------|--------|---------------------|
| Concessive Clauses | M35 | Use хоча, незважаючи на те що |
| Causal Clauses | M36 | Use тому що, оскільки, бо |
| Temporal Clauses | M37 | Use коли, поки, після того як |
| Integrated Clauses | M38 | Combine clause types in extended text |
| Reported Statements | M39 | Transform direct speech to indirect |
| Reported Questions | M40 | Transform questions to indirect form |

### M51: Advanced Grammar Checkpoint

| Skill Group | Source | What Learner Can Do |
|-------------|--------|---------------------|
| Adverbial Participles Impf | M42 | Form and use -ючи/-ачи (simultaneous) |
| Adverbial Participles Pf | M43 | Form and use -вши/-ши (prior action) |
| Active Participles | M44 | Recognize and avoid bureaucratic forms |
| Passive Participles Full | M45 | Form -ний/-тий with agreement |
| Passive Participles Short | M46 | Form -но/-то impersonal passives |
| Passive Constructions | M47 | Use all passive types appropriately |
| Diminutives | M48 | Form and understand diminutive nuance |
| Collective Numerals | M49 | Use двоє, троє; fractions |
| Integrated Grammar | M50 | Apply all advanced forms in context |

---

## Module Structure (Checkpoint-Specific)

### 1. Frontmatter

```yaml
---
module: b1-XX
title: "Контрольна точка: [Phase Title]"
phase: "B1.X [Phase Name] Checkpoint"
pedagogy: "TTT"  # ALWAYS TTT for checkpoints
tags:
  - checkpoint
  - integration
  - [phase-specific-tag]
grammar:
  - "Integration of M[start]-M[end]"
  - "Comprehensive review and testing"
objectives:
  - "Learner can demonstrate mastery of [phase topic]"
  - "Learner can integrate knowledge from M[start]-M[end]"
  - "Learner can self-assess readiness for next phase"
vocabulary_count: 35  # Must match count in vocabulary/{slug}.yaml
---
```

### 2. Checkpoint Content Structure (Skill-Based)

**IMPORTANT:** Checkpoints use a **skill-based structure** as defined in `CHECKPOINT-DESIGN-GUIDE.md`.
Each skill from the phase gets its own section with Model → Practice → Self-Check.

#### Opening Section

```markdown
# [Phase] Контрольна точка

> 🎯 **Чому це важливо?**
>
> [Explain in Ukrainian this is a checkpoint — no new content]
> [Describe what phase is being assessed]
> [Set expectation for comprehensive review]
> [Preview what comes after mastering this checkpoint]

---

## Огляд

Ця контрольна точка перевіряє навички з модулів [XX]-[YY]:

- **Навичка 1:** [Skill description from skill table]
- **Навичка 2:** [Skill description from skill table]
- **Навичка 3:** [Skill description from skill table]
[Continue for all skills in phase]
```

#### Skill Sections (Repeat for EACH skill group)

```markdown
---

## Skill 1: [Skill Name in Ukrainian]

### Model:

> [Annotated example text showing the skill in use]
> [Bold key forms: **прочитав**, **читав**]

**Зверніть увагу:**
- [Pattern 1 explanation]
- [Pattern 2 explanation]

### Practice:

[Scaffolded activity - fill-in, complete, or choose]

1. [Practice item 1]
2. [Practice item 2]
[5-8 practice items]

> [!solution] Перевірити
> 1. **[answer]** ([explanation])
> 2. **[answer]** ([explanation])

### Self-Check:

- ☐ [Criterion 1 - can I do X?]
- ☐ [Criterion 2 - do I understand Y?]
- ☐ [Criterion 3 - can I apply Z?]

> 💡 **Чи знали ви?**
>
> [Interesting fact about this skill in Ukrainian]
```

#### Integration Challenge Section

```markdown
---

## Інтеграційне завдання

Прочитайте цей текст і дайте відповіді на запитання:

> *[200+ word Ukrainian text using ALL skills from the phase]*

**Запитання:**

1. [Question testing Skill 1]
2. [Question testing Skill 2]
3. [Question testing integration of skills]

> [!solution] Відповіді
> 1. [Answer with explanation]
> 2. [Answer with explanation]
> 3. [Answer with explanation]
```

#### Summary Section

```markdown
---

# Підсумок

**Що ви навчилися:**

| Навичка | Ключовий патерн | Приклад |
|---------|-----------------|---------|
| Skill 1 | [Pattern] | [Example] |
| Skill 2 | [Pattern] | [Example] |
| Skill 3 | [Pattern] | [Example] |

**Далі:**

[Preview of next phase with specific modules]

> ✅ **Самоперевірка**
>
> Чи можете ви:
> - [ ] [Self-assessment criterion 1 — Skill 1]?
> - [ ] [Self-assessment criterion 2 — Skill 2]?
> - [ ] [Self-assessment criterion 3 — integration]?
>
> Якщо ви відповіли "так" на всі питання — ви готові до [Next Phase]!
```

---

## Checkpoint-Specific Activities

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/b1-15-checkpoint.yaml`:**

```yaml
- type: quiz
  title: Аспект у минулому часі (M06-07)
  instruction: Перевірте ваше розуміння аспекту в минулому часі.
  items:
    - question: Я вчора _____ книгу.
      options:
        - text: читав
          correct: true
        - text: прочитав
          correct: false
```

---

### Skill-Based Activity Design

**CRITICAL:** Each activity must target specific skill groups from the checkpoint's skill table. Do NOT create generic activities.

**Example: M15 Aspect Checkpoint**

```markdown
## quiz: Аспект у минулому часі (M06-07)
> Перевірте ваше розуміння аспекту в минулому часі.

[10-14 questions ONLY testing past tense aspect choices]

---

## quiz: Аспект у наказовому способі (M11)
> Оберіть правильну форму наказу.

[10-14 questions ONLY testing imperative aspect]

---

## fill-in: Інтегроване застосування аспекту (M06-14)
> Заповніть пропуски, застосовуючи всі правила аспекту.

[Extended passage testing ALL aspect skills in context]
```

### Comprehensive Testing (16+ activities required)

Checkpoints must test ALL skill groups from the phase:

**Core Testing Activities (Skill-Targeted):**
1. **quiz** (2-3 activities, 10-14 items each) — One quiz per skill group cluster
2. **match-up** (2 activities, 14+ items) — Term-definition, concept-example
3. **fill-in** (2 activities, 12-14 items) — Contextual application of specific skills
4. **group-sort** (1-2 activities, 14-18 items) — Categorization by skill group

**Integration Activities:**
5. **error-correction** (2 activities, 10-12 items) — Common mistakes across phase
6. **cloze** (1 activity, 16+ blanks) — Extended passage integrating all concepts
7. **unjumble** (1 activity, 10+ items) — Sentence formation with phase structures

**Production Activities:**
8. **Writing task with Model Answer** (1 activity, 100+ words)

---

### Quiz Structure for Checkpoints

```markdown
## quiz: Комплексний тест — [Module X Topic]

[10-14 questions testing ONLY Module X concepts, 15-25 words each]

---

## quiz: Комплексний тест — [Module Y Topic]

[10-14 questions testing ONLY Module Y concepts]

---

## quiz: Інтеграція всіх модулів

[12+ questions testing INTEGRATION across all modules]
```

---

## Vocabulary Section for Checkpoints

**CRITICAL:** Vocabulary must be defined in `vocabulary/{slug}.yaml`. Do NOT embed a vocabulary table in Markdown.

**Example `vocabulary/b1-15-checkpoint.yaml`:**

```yaml
items:
- lemma: читати
  ipa: /t͡ʃɪˈtɑtɪ/
  translation: to read
  pos: дієсл.
  note: з модуля 06
```

---

## Common Pitfalls to Avoid

### 1. **Introducing New Content**
- ❌ Problem: Teaching new grammar or vocabulary in checkpoint
- ✅ Solution: Checkpoints ONLY review and test. All content must come from prior modules.

### 2. **Insufficient Module Coverage**
- ❌ Problem: Testing only 2-3 modules out of 8-module phase
- ✅ Solution: Create dedicated quiz for EACH major concept + integration quiz

### 3. **English in Content**
- ❌ Problem: English explanations or instructions
- ✅ Solution: 100% Ukrainian immersion (English only in vocabulary translations)

### 4. **No Model Answers**
- ❌ Problem: Writing tasks without examples
- ✅ Solution: Every writing task includes complete model answer

### 5. **Too Few Activities**
- ❌ Problem: 12 activities (same as regular modules)
- ✅ Solution: 16+ activities for comprehensive testing

### 6. **Missing Self-Assessment**
- ❌ Problem: No "Чи можете ви..." checklist
- ✅ Solution: Include specific criteria tied to each module in the phase

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/b1-grammar-module-template.md`
- **B1 Curriculum Plan:** `docs/l2-uk-en/B1-CURRICULUM-PLAN.md`
- **B2 Checkpoint Template:** `docs/l2-uk-en/templates/b2-checkpoint-module-template.md`
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

**Last Updated:** 2025-12-25
**Template Version:** 1.0
