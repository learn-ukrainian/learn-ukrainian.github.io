# B1 Metalanguage Module Template

**Purpose:** Reference template for creating B1.0 Bridge modules (M01-05: Metalanguage Bridge)

**Based on:** M01 (Як говорити про граматику), M05 (Готові до занурення) which achieved ✅ PASS on audit gates

**Related Issue:** [#298](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/298)


<!--
TEMPLATE_METADATA:
  required_sections:
  - Presentation|Introduction|Вступ|Презентація|Діагностика
  - Parts of Speech|Seven Cases|Термінологія|Частини мови|Відмінки|Basic Sentence Terms|Aspect Terms|Tense Terms|Aspect|Вид|Tense|Час|Verb Forms|Negation|Explanation Patterns|Instruction Patterns|Word Formation|Analytical Terms|Style|Пояснювальні|Інструкції|Словотвір|Аналітична|Стиль|Аналіз|Поглиблення
  - Practice|Mini-Dialogues|Практика|Міні-діалоги
  optional_sections:
  - Warm-up|Розминка
  - Summary|Підсумок
  - Need More Practice?
  pedagogy: PPP
  min_word_count: 1200
  required_callouts: []
  description: B1 metalanguage bridge modules teach grammar terminology bilingually (M01-M05 cover different terminology areas)
-->

---

## What Makes Metalanguage Modules Different

**Unique Function:** B1.0 modules are the **bridge from English-medium to Ukrainian-medium instruction**. They teach grammar terminology IN Ukrainian so learners can understand grammar explanations from M06 onward.

**Key Differences from B1 Grammar Modules:**

| Aspect | Metalanguage (M01-05) | Grammar (M06-85) |
|--------|----------------------|------------------|
| **Immersion** | Flexible (no strict %) | 90-100% Ukrainian |
| **Goal** | Teach terminology | Teach grammar concepts |
| **Scaffolding** | Bilingual tables, explicit translations | Minimal English (vocab only) |
| **Pedagogy** | PPP (terminology acquisition) | TTT (concept discovery) |
| **Content** | Terms + usage examples | Grammar rules + practice |
| **English** | Allowed in explanations | Vocabulary translations only |

**Bridge Function:**
- **A2 ends at:** 50-55% immersion, English explanations
- **B1.0 (M01-05):** Flexible immersion, teaches Ukrainian grammar terms
- **B1.1+ (M06-85):** 90-95% immersion, uses Ukrainian grammar terms

---

## Quick Reference Checklist

Before submitting a B1 metalanguage module, verify:

### Content Requirements
- [ ] **Word count:** 1200+ words (core prose: explanations, examples, engagement boxes — excludes vocabulary section, activities section, tables)
- [ ] **Vocabulary:** 25-45 items in 5-column format (Слово | Вимова | Переклад | ЧМ | Примітка)
- [ ] **Terminology coverage:** All target terms introduced with Ukrainian + English
- [ ] **Usage examples:** Each term shown in context (sample sentences)
- [ ] **Bilingual scaffolding:** Tables with Ukrainian terms + English translations

### Activity Requirements
- [ ] **Activities:** 10-12 minimum (fewer than grammar modules, focus on terminology)
- [ ] **Activity density:**
  - Quiz: 8+ items (testing terminology knowledge)
  - Match-up: 8+ pairs (Ukrainian terms ↔ English)
  - Fill-in: 8+ items (terminology in context)
  - Group-sort: 10+ items (categorizing terms)
  - Unjumble: 6+ items (sentences using terminology)
  - Translate: 6+ items (grammar explanations Ukrainian ↔ English)
- [ ] **Engagement boxes:** 4-5 boxes (Did You Know, Real World, etc.)

### Immersion & Quality
- [ ] **Immersion:** Flexible (bilingual scaffolding allowed)
- [ ] **Pedagogy:** PPP (Presentation-Practice-Production)
- [ ] **No violations:** Check for pedagogical red flags
- [ ] **Bridge function:** Clear preparation for M06+ full immersion

---

## Module Structure Template

### 1. Frontmatter (YAML)

```yaml
---
module: b1-0X  # M01-05 only
title: "Ukrainian Title"
subtitle: "English subtitle explaining terminology focus"
version: "1.0"
phase: "B1.0 Bridge"  # Always "B1.0 Bridge" for M01-05
pedagogy: "PPP"  # Presentation-Practice-Production (terminology acquisition)
duration: 75  # minutes
transliteration: none  # No transliteration at B1
tags:
  - grammar
  - metalanguage
  - terminology
  - bridge  # Always include "bridge" tag
grammar:
  - "Main terminology category (e.g., Parts of speech names)"
  - "Secondary terminology (e.g., Case names)"
objectives:
  - "Learner can identify [X] using Ukrainian terminology"
  - "Learner can name [Y] in Ukrainian"
  - "Learner can understand [Z] when reading Ukrainian grammar"
vocabulary_count: 25  # Must match count in vocabulary/{slug}.yaml
---
```

**Why these fields:**
- `phase: "B1.0 Bridge"`: Identifies module as metalanguage bridge (not B1.1 Aspect, etc.)
- `pedagogy: "PPP"`: Terminology requires explicit presentation, not discovery
- `tags`: Always include `bridge` and `metalanguage`
- `vocabulary_count`: Higher than grammar modules (25-45) due to terminology density

---

### 2. Module Title and Motivation Box

```markdown
# Ukrainian Title

> 🎯 **Why This Module Matters**
>
> [Explain WHY learning Ukrainian grammar terminology matters]
> [Connect to B1+ full immersion: "From M06 onward, grammar will be explained IN Ukrainian"]
> [Show real-world benefit: reading Ukrainian grammar books, talking with natives]
```

**Example from M01:**
```markdown
# Як говорити про граматику

> 🎯 **Why This Module Matters**
>
> You're at B1 now. From this point forward, you'll encounter grammar explanations written *in Ukrainian* — in textbooks, online resources, and conversations with native speakers. To understand these resources, you need to know what Ukrainians call the parts of speech, the cases, and other grammar concepts. This module gives you that vocabulary. By the end, you'll be able to read a Ukrainian grammar explanation and understand what it's talking about.
```

**Why this works:**
- Establishes the **bridge function** explicitly
- Motivates terminology learning (real-world utility)
- Sets expectations ("From M06 onward...")

---

### 3. Content Sections (1200+ words total)

**Structure for PPP pedagogy:**

#### Section 1: Presentation (Введення)
- Introduce the terminology domain
- Explain why Ukrainians learn this too
- Contextualize the terms (etymology, usage)
- 150-200 words

```markdown
## Presentation

### The Challenge of Learning Grammar in a New Language

[Narrative hook: Why grammar terminology in Ukrainian matters]

Think about how you learned grammar in school. Someone taught you terms like "noun," "verb," "adjective." Now imagine picking up a Ukrainian grammar book. You open it and see: *"Іменник стоїть у родовому відмінку після прийменника..."*

If you don't know that **іменник** means "noun," **родовий відмінок** means "genitive case," and **прийменник** means "preposition," you're lost. This module solves that problem.

### Why Ukrainians Learn This Too

[Explain that Ukrainian schoolchildren learn these terms]
[Show that learners already understand the concepts, just need new words]
```

**Why this works:**
- Frames terminology as **access to resources**, not arbitrary memorization
- Reduces anxiety (you already know the concepts!)
- Shows cultural connection (Ukrainian schoolchildren learn this too)

#### Section 2: Terminology Tables (700-800 words)
- Present all terms in **bilingual tables**
- Organize by category (content words vs. function words, etc.)
- Include Ukrainian term, English equivalent, examples
- Add etymological notes (e.g., "дієслово = action-word")

**CRITICAL:** Use bilingual tables for terminology. This is NOT a violation of immersion—it's the bridge.

```markdown
## The Parts of Speech: Частини мови

Ukrainian has ten parts of speech. At B1, you need to recognize all of them by their Ukrainian names.

### Content Words (Самостійні частини мови)

These are the words that carry meaning:

| Термін | English | Example |
|--------|---------|---------|
| **іменник** | noun | книга, стіл, Київ |
| **дієслово** | verb | читати, писати, бігти |
| **прикметник** | adjective | гарний, великий, синій |
| **прислівник** | adverb | швидко, добре, тут |
| **займенник** | pronoun | я, ти, він, вона |
| **числівник** | numeral | один, два, перший |

[Add explanatory paragraphs showing terms in context]

Notice how each Ukrainian term describes what the word category does. The іменник comes from "ім'я" — it names things. The прикметник comes from "прикмета" — it describes characteristics.

### Function Words (Службові частини мови)

| Термін | English | Example |
|--------|---------|---------|
| **прийменник** | preposition | в, на, до, з |
| **сполучник** | conjunction | і, але, бо, що |
| **частка** | particle | не, ні, хай, би |
| **вигук** | interjection | ой, ах, гей |

[Explain function words' role in sentence structure]
```

**Why this works:**
- Tables make terminology scannable and memorable
- Examples show terms in authentic context
- Etymology notes create memory hooks
- Bilingual format scaffolds understanding

#### Section 3: Usage in Context (200-300 words)
- Show how these terms appear in Ukrainian grammar explanations
- Provide sample Ukrainian grammar text with terminology highlighted
- Demonstrate comprehension

```markdown
## How This Works in Practice

When you read a Ukrainian grammar resource, you'll encounter sentences like:

> *"Дієслово 'читати' — недоконаного виду. Воно використовується, коли дія триває або повторюється."*

Now you understand:
- **Дієслово** = verb
- **Недоконаний вид** = imperfective aspect
- **Дія** = action
- **Триває** = continues
- **Повторюється** = repeats

You can now read Ukrainian grammar independently!
```

**Why this works:**
- Shows real-world application
- Tests comprehension in authentic context
- Builds confidence for M06+ immersion

#### Section 4: Engagement Boxes (4-5 boxes)
- 💡 **Did You Know** — Interesting linguistic facts
- 🌍 **Real World** — How natives use these terms
- 🎯 **Fun Fact** — Memorable trivia about terminology

```markdown
> 💡 **Did You Know?**
>
> Ukrainian grammar terminology comes largely from Church Slavonic and Latin traditions. The word **відмінок** literally means "change" or "variation" — because the word *changes* form depending on its role in the sentence.

> 🌍 **Real World: Grammar Discussions**
>
> When Ukrainians discuss language on forums or social media, they use these terms freely. You might see: "Тут треба вжити дієслово доконаного виду" (Here you need to use a perfective verb). Without knowing **дієслово** and **вид**, you'd miss the point entirely.
```

---

### 4. Vocabulary Section (Словник)

**CRITICAL:** Vocabulary must be defined in `vocabulary/{slug}.yaml`. Do NOT embed a vocabulary table in Markdown.

**Example `vocabulary/b1-01-grammar.yaml`:**

```yaml
items:
- lemma: іменник
  ipa: /iˈmɛnːɪk/
  translation: noun
  pos: noun
  note: from "ім'я" (name)
- lemma: дієслово
  ipa: /dijɛˈslɔwɔ/
  translation: verb
  pos: noun
  note: literally "action-word"
```

---

### 5. Activities Section (Активності)

**Activity Mix for Metalanguage Modules:**

#### Must-Have Activities:
1. **quiz** (8+ items) — Test terminology knowledge
2. **match-up** (8+ pairs) — Match Ukrainian terms ↔ English equivalents
3. **fill-in** (8+ items) — Use terminology in context
4. **group-sort** (10+ items) — Categorize terms (e.g., content words vs. function words)
5. **translate** (6+ items) — Translate grammar explanations Ukrainian ↔ English

#### Recommended Activities:
6. **unjumble** (6+ items) — Sentences using terminology
7. **true-false** (8+ items) — Statements about grammar concepts
8. **error-correction** (6+ items) — Fix misused terminology

**Total:** 10-12 activities (fewer than grammar modules, but focused on terminology mastery)

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/b1-01-grammar.yaml`:**

```yaml
- type: quiz
  title: Тест на термінологію
  items:
    - question: Яка частина мови слово "книга"?
      options:
        - text: іменник
          correct: true
        - text: дієслово
          correct: false

- type: match-up
  title: З'єднайте терміни
  pairs:
    - left: іменник
      right: noun
    - left: дієслово
      right: verb
```

---

### 6. Pedagogical Notes

**What Makes Metalanguage Modules Effective:**

1. **Bilingual Scaffolding Is NOT a Weakness**
   - Terminology acquisition requires explicit translation
   - Tables make terms scannable and memorable
   - English scaffolding here ENABLES Ukrainian-only explanations in M06+

2. **Etymology Creates Memory Hooks**
   - Show that "дієслово" = "дія" (action) + "слово" (word)
   - Show that "відмінок" = "change" (word form changes)
   - Learners remember terms better with meaningful connections

3. **Real-World Context Motivates Learning**
   - Show sample Ukrainian grammar texts
   - Reference online forums where natives use these terms
   - Connect to next modules ("In M06, you'll see...")

4. **PPP Works for Terminology**
   - **Presentation:** Introduce terms in tables
   - **Practice:** Activities test recognition and usage
   - **Production:** Read Ukrainian grammar texts independently

---

## Common Pitfalls to Avoid

### ❌ DON'T:
- **Don't apologize for bilingual scaffolding** — It's pedagogically necessary
- **Don't skip etymology** — Memory hooks matter for 40+ terms
- **Don't present terms without examples** — Context aids retention
- **Don't forget the bridge function** — Every module should reference M06+ immersion
- **Don't overload one module** — Spread terms across M01-05
- **Don't use activities that require grammar knowledge** — These modules teach terms, not grammar

### ✅ DO:
- **Use bilingual tables generously** — Make terms scannable
- **Show terms in authentic Ukrainian grammar texts** — Build confidence
- **Reference Ukrainian schoolchildren** — Reduces anxiety ("natives learn this too!")
- **Connect to previous A2 knowledge** — Learners already know concepts, just need Ukrainian words
- **Prepare for M06+ immersion explicitly** — "After M05, all grammar will be in Ukrainian"
- **Use translation activities** — They're perfect for metalanguage modules

---

## Module-Specific Guidance

### M01: Parts of Speech + Cases
- Focus: 10 parts of speech + 7 cases
- Vocabulary: ~25 terms
- Tables: Parts of speech (content vs. function), case names + questions

### M02: Verb Terminology
- Focus: Aspect, tense, mood, negation, verb forms
- Vocabulary: ~30 terms
- Tables: Aspect types, tenses, moods, negation patterns

### M03: Grammar Explanation Patterns
- Focus: How Ukrainian grammar books explain concepts
- Vocabulary: ~35 terms
- Tables: Explanation verbs, instruction verbs, analytical terms

### M04: Sentence Structure
- Focus: Sentence elements, sentence types, punctuation
- Vocabulary: ~30 terms
- Tables: Sentence elements, simple vs. complex sentences

### M05: Integration Checkpoint
- Focus: Review of M01-04, comprehension test
- Vocabulary: ~44 terms (comprehensive review)
- Activity: Read Ukrainian grammar text, answer questions

---

## Pre-Submission Checklist

### Content
- [ ] 1200+ words before activities
- [ ] 25-45 vocabulary items in 5-column format
- [ ] All target terminology introduced with Ukrainian + English
- [ ] Bilingual tables for all term categories
- [ ] Etymology notes for key terms
- [ ] Sample Ukrainian grammar text showing terms in context

### Activities
- [ ] 10-12 activities minimum
- [ ] quiz (8+ items)
- [ ] match-up (8+ pairs)
- [ ] fill-in (8+ items)
- [ ] group-sort (10+ items)
- [ ] translate (6+ items)
- [ ] Activity items test terminology, not grammar concepts

### Immersion & Quality
- [ ] Flexible immersion (bilingual scaffolding allowed)
- [ ] PPP pedagogy (Presentation-Practice-Production)
- [ ] Bridge function clearly stated ("After M05, full Ukrainian immersion")
- [ ] Real-world context shown (Ukrainian grammar texts, native usage)
- [ ] 4-5 engagement boxes
- [ ] No pedagogical violations

### Audit
- [ ] Module passes `python3 scripts/audit_module.py`
- [ ] Vocabulary count matches frontmatter
- [ ] All activities formatted correctly
- [ ] Immersion check passes (flexible for M01-05)

---

## Example Modules

**Reference these existing modules:**
- **M01:** Parts of speech + cases — `curriculum/l2-uk-en/b1/01-how-to-talk-about-grammar.md`
- **M05:** Integration checkpoint — `curriculum/l2-uk-en/b1/05-ready-for-immersion.md`

Both modules achieved ✅ PASS on all audit gates.

---

## Related Documentation

- **B1 Curriculum Plan:** `docs/l2-uk-en/B1-CURRICULUM-PLAN.md`
- **B1 Improvement Plan:** `docs/l2-uk-en/B1-IMPROVEMENT-PLAN.md`
- **B1 Grammar Template:** `docs/l2-uk-en/templates/b1-grammar-module-template.md`
- **Module Richness Guidelines:** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- **Activity Markdown Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

## Clean MD Architecture Note

### Activities, Vocabulary, and External Resources

**CRITICAL:** Do NOT add `## Activities`, `## Vocabulary`, or `## External Resources` headers to the Markdown file. These sections are automatically injected by the build system from the corresponding YAML sidecars:

- `activities/{slug}.yaml` → `## Activities` section
- `vocabulary/{slug}.yaml` → `## Vocabulary` section
- `docs/resources/external_resources.yaml` (filtered by `module_id`) → `## External Resources` section

The module structure follows **Clean MD architecture**: Markdown contains narrative content only, YAML sidecars contain structured data.

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
**Maintainer:** Claude (The Content Developer)
