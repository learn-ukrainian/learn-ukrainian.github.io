# A2 Module Template

> **Level:** A2 (Elementary)
> **Pedagogy:** PPP (Presentation-Practice-Production)
> **Focus:** All 7 cases, aspect introduction, comparison, complex sentences
> **Immersion:** Graduated (M01-15: 40-50%, M16-35: 50-65%, M36-58: 65-80%)

<!--
TEMPLATE_METADATA:
  required_sections:
  - Introduction|Вступ
  - Presentation|Grammar|Focus|Презентація|Граматика|Теорія
  - Practice|Exercises|Activity|Практика|Вправи
  - Summary|Підсумок
  - Need More Practice?
  optional_sections:
  - Діалоги
  - Культурна нотатка
  forbidden_headers:
  - Activities
  - Vocabulary
  - External Resources
  - Вправи
  - Словник
  pedagogy: PPP
  min_word_count: 2000
  required_callouts: []
  description: A2 uses PPP pedagogy with bilingual structure and focus on all 7 cases
-->

---

## Template Checklist

Before submitting, verify:

- [ ] Metadata sidecar complete in `meta/{slug}.yaml`
- [ ] Word count meets target (3000+ words per config.py)
- [ ] NO transliteration in body text
- [ ] 10+ activities with 8+ items each in `activities/{slug}.yaml`
- [ ] 4+ unique activity types including error-correction
- [ ] 4+ engagement boxes
- [ ] Bilingual structure (English intro + Ukrainian Вступ)
- [ ] Vocabulary items enriched with IPA in `vocabulary/{slug}.yaml`
- [ ] Mandatory headers (Summary, External Resources, Activities, Vocabulary) present at end of MD
- [ ] All activity answers are correct

---

## Metadata Sidecar

**CRITICAL:** Do NOT include frontmatter in the Markdown file. Use `curriculum/l2-uk-en/a2/meta/{slug}.yaml`.

See [METADATA_YAML_SCHEMA.md](../../docs/dev/METADATA_YAML_SCHEMA.md) for details.

---

## Naturalness Quality Checklist

**Run this check during Stage 4 (Review & Fix) on prose activities.**

Before finalizing the module, verify prose activities (cloze, fill-in, unjumble with 5+ sentences) achieve:

- [ ] **Subject consistency** - Clear subjects maintained throughout passages
- [ ] **Discourse markers** - At least 2-3 connectors per 10-sentence passage (а, але, потім, тому, також, спочатку, нарешті)
- [ ] **Topic coherence** - All sentences contribute to unified narrative/theme, no random topic jumps
- [ ] **No template repetition** - Varied sentence structures across activities within the module
- [ ] **Moderate intensifiers** - Maximum 2-3 "дуже" per module, 0-1 "надзвичайно/справжній"
- [ ] **No double superlatives** - Use one precise descriptor instead of redundant pairs (e.g., "найкращий" NOT "найкращий та найвидатніший")
- [ ] **Natural transitions** - Avoid robotic "і це", "тому що... тому" patterns

**Target score:** 8/10 for content modules, 7/10 for checkpoints

**Red flags (score < target):**
- Same sentence template repeated across multiple activities
- Disconnected factoid lists without discourse markers
- Excessive intensifiers or double superlatives
- Robotic, mechanical transitions

**See:** `claude_extensions/phases/stage-4-review-fix.md` Section 9 for detailed naturalness criteria.

**For batch scanning:** Use `/scan-naturalness {level} {start} {end}` to scan completed modules.

---

## Module Structure

### # {Ukrainian Title}

Main title in Ukrainian (matching topic).

### ## Introduction

English introduction (100-150 words):

- Context for what's being learned
- Connection to previous knowledge
- Overview of module content
- Why this grammar/vocab matters

### ## Вступ

Ukrainian introduction (100-150 words):

- Same content as English intro but in Ukrainian
- Appropriate for A2 level complexity
- Maximum 15 words per sentence
- Use vocabulary learner already knows

### ## Presentation

Core lesson content with bilingual approach:

#### ### {English Section Title}

Concept explanation in English:

- Clear grammar rules
- Comparison tables
- 4-6 example sentences

```markdown
| Називний | Давальний | Приклад         |
| -------- | --------- | --------------- |
| я        | мені      | Дай мені книгу. |
```

#### ### {Ukrainian Section Title}

Same concept reinforced in Ukrainian:

- Simpler explanation
- More examples
- Pattern highlighting

> 💡 **Did You Know?**
>
> {Cultural or linguistic insight}

### ## Practice

Guided practice section:

- Transformation exercises
- Pattern completion
- Guided dialogues

### ## Dialogues

2-3 mini-dialogues demonstrating grammar in context:

```markdown
**А:** Тобі подобається кава?
**Б:** Так, мені дуже подобається кава!
```

---

## Mandatory Sections (At End of File)

Every A2 module MUST end with these four sections. The content is injected automatically from YAML sidecars during the build, but the headers MUST be present in the Markdown for structural validation.

### ## Summary

(or `## Підсумок`)

Brief recap in Ukrainian (75-100 words):

- Key grammar points
- Most important vocabulary
- Encouragement

---

## Content Structure Note

### Vocabulary, Activities & External Resources

**CRITICAL:** Do NOT add `## Vocabulary`, `## Activities`, or `## External Resources` headers. These sections are injected automatically from:

- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`
- `docs/resources/external_resources.yaml`

The build system (`generate_mdx.py`) will inject these sections at build time.

---

## A2 Constraints

### Grammar Allowed (Building on A1)

- All 7 cases (Dative and Instrumental introduced)
- Aspect pairs (introduction)
- Comparison (вищий ступінь)
- Simple subordinate clauses
- Past tense
- Future tense (imperfective)

### Grammar Introduced at A2

- Dative case (давальний)
- Instrumental case (орудний)
- Perfective aspect basics
- Subordinate clauses with що, бо

### Sentence Complexity

- Maximum 15 words per sentence
- Up to 2 clauses
- Simple coordination (і, а, але)
- Simple subordination (що, бо)

---

## A2 Phases and Immersion

| Phase | Modules | Immersion Target | Focus                             |
| ----- | ------- | ---------------- | --------------------------------- |
| A2.1  | 01-15   | 40-50%           | Dative, Instrumental introduction |
| A2.2  | 16-35   | 50-65%           | Aspect pairs, consolidation       |
| A2.3  | 36-58   | 65-80%           | Pre-B1 Runway, integration        |

---

## Quality Targets

| Metric           | Target |
| ---------------- | ------ |
| Words            | 3000+  |
| Activities       | 10+    |
| Items/activity   | 8+     |
| Unique types     | 4+     |
| Engagement boxes | 4+     |
| Vocabulary       | 20+    |
| Dialogues        | 2+     |

---

## Error-Correction Format (Critical)

A2 introduces error-correction. **All 4 callouts are required:**

```markdown
## error-correction: Find the Mistake

1. Я даю книга тобі.
   > [!error] книга
   > [!answer] книгу
   > [!options] книга | книгу | книги | книзі
   > [!explanation] Direct object requires accusative case: книга → книгу
```

---

## Example Module Skeleton

```markdown
# Давальний відмінок I — Займенники

## Introduction

{English introduction...}

## Вступ

{Ukrainian introduction...}

## Presentation

### Why the Dative Case Matters

{...}

### Займенники в давальному відмінку

{...}

> 💡 **Did You Know?**
> {...}

## Practice

{...}

## Dialogues

**А:** Тобі подобається ця книга?
**Б:** Так, мені дуже подобається!

# Підсумок

{Ukrainian recap...}

---

## Самооцінка (Optional)

Checklist for learners...
```

> [!NOTE]
> **Standardized Sections**: The headers for `Activities`, `External Resources`, and `Vocabulary` are **NOT** required in the Markdown source file for A2+. The build system injects them automatically from the corresponding sidecars.
