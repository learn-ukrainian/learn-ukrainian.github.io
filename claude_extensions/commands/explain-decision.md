#!/bin/bash
# explain-decision - Explain curriculum design decisions
#
# Usage:
#   /explain-decision [topic]
#
# Examples:
#   /explain-decision b1-aspect-sequencing
#   /explain-decision why-motion-verbs-after-aspect
#   /explain-decision checkpoint-placement
#
# Purpose:
#   Educational tool to help you understand the "why" behind curriculum decisions.
#   Learn pedagogy, not just follow instructions.

```yaml
---
name: explain-decision
description: Explain curriculum design decisions and pedagogical rationale
version: '1.0'
category: learning
model: sonnet
---
```

---

## Purpose

**Help you learn curriculum design by explaining decisions.**

Not just "what to do" but "why it's done this way."

---

## Usage

### General Explanations

```
/explain-decision [topic]
```

**Examples:**
- `/explain-decision aspect-teaching-sequence`
- `/explain-decision b1-checkpoint-frequency`
- `/explain-decision vocabulary-selection-criteria`
- `/explain-decision activity-type-distribution`

### Module-Specific

```
/explain-decision module [LEVEL] [NUM]
```

**Examples:**
- `/explain-decision module b1 9` - Why is M9 structured this way?
- `/explain-decision module b2-hist 15` - Pedagogical rationale for M15

### Decision Comparison

```
/explain-decision compare [option1] vs [option2]
```

**Examples:**
- `/explain-decision compare aspect-first vs motion-first`
- `/explain-decision compare 3000-words vs 2000-words`

---

## What I Explain

### Pedagogical Rationale

**For module structure:**
- Why this section order?
- Why these subsections?
- Why this word count target?
- Why these prerequisite modules?

**For sequencing:**
- Why aspect before motion verbs?
- Why this grammar at B1 vs B2?
- Why checkpoints here?
- Why this module count per phase?

### Design Trade-offs

**Decisions involve trade-offs. I'll explain:**
- What we prioritized (and why)
- What we compromised (and why)
- Alternative approaches considered
- Why this approach for Ukrainian specifically

### Historical Context

**Why things are designed this way:**
- What didn't work in previous versions
- Lessons from curriculum failures
- Best practices from language pedagogy
- Ukrainian-specific considerations

### CEFR Alignment

**Why at this level:**
- CEFR descriptor mapping
- Complexity appropriate for proficiency
- Progression logic (A1→C2)
- Assessment alignment

---

## Example Explanations

### Example 1: Aspect Sequencing

**Question:** Why teach aspect at B1, not A2?

**Explanation:**

**CEFR Rationale:**
- A2: "Can use simple structures" (CEFR)
- B1: "Can handle main tenses" and "explain viewpoints" (CEFR)
- Aspect = viewpoint on action (perfective = completed, imperfective = ongoing)
- This is B1-level linguistic abstraction

**Pedagogical Rationale:**
- A2 students need concrete, immediate usage
- Aspect requires metalinguistic awareness ("How do I view this action?")
- B1 students ready for system thinking, not just phrase collection

**Ukrainian-Specific:**
- Aspect is core to Ukrainian (not optional like English articles)
- Must be taught systematically (not just memorized pairs)
- B1 is when students transition from phrases → productive language

**Alternative Considered:**
- Early aspect (A2): Too abstract, students get confused
- Late aspect (B2): Too late, bad habits formed

**Decision:** B1 is optimal for systematic aspect teaching.

---

### Example 2: Checkpoint Frequency

**Question:** Why checkpoints every 10-15 modules, not more often?

**Explanation:**

**Pedagogical Rationale:**
- Checkpoints test integration, not single concepts
- Need 10-15 modules to have enough material to integrate
- Too frequent = constant testing stress
- Too rare = losing track of progress

**Resource Consideration:**
- Each checkpoint = significant time investment
- Must balance assessment with new learning
- Students need "breathing room" to practice

**CEFR Alignment:**
- CEFR describes proficiency in bands (A1, A2.1, A2.2, B1.1, etc.)
- Checkpoints align with sub-band transitions
- Natural assessment points

**Data-Driven:**
- Research shows optimal testing frequency = 8-12 hours of instruction
- Our modules ≈ 45-60 min each
- 10 modules ≈ 10 hours ≈ optimal checkpoint timing

---

### Example 3: Activity Type Distribution

**Question:** Why more fill-in-blanks at A1, but more essay-response at B2?

**Explanation:**

**Cognitive Load:**
- A1: Limited working memory available for L2
- Fill-in: Controlled output, reduces cognitive load
- Essay: Open-ended, requires full productive capacity

**Proficiency Development:**
- A1: Guided practice → accuracy first
- B2: Autonomous production → fluency + complexity

**CEFR Descriptors:**
- A1: "Can complete simple forms" (fill-in appropriate)
- B2: "Can write clear detailed text" (essay appropriate)

**Assessment Validity:**
- Fill-in tests: Recognition + basic production
- Essay tests: Complex production + coherence

---

## How to Use for Learning

### When Designing New Modules

**Before building:**
```
/explain-decision why-is-module-X-structured-this-way

Then ask yourself:
- Does my new module follow same principles?
- Are there unique considerations for this topic?
- Should I diverge from the pattern (and why)?
```

### When Questioning Decisions

**If something seems wrong:**
```
/explain-decision why-[the-thing-that-seems-wrong]

Understanding the rationale helps you either:
- Agree with the decision (now that you understand it)
- Propose a better alternative (with informed reasoning)
```

### When Planning Strategy

**For big decisions:**
```
/explain-decision compare [approach-A] vs [approach-B]

Understand trade-offs before committing.
```

---

## Output Format

**I will provide:**

1. **Direct Answer** (2-3 sentences)
2. **Pedagogical Rationale** (why this works for learning)
3. **CEFR Alignment** (how it maps to proficiency)
4. **Trade-offs** (what we gain vs. what we compromise)
5. **Alternatives Considered** (what else we could do)
6. **Ukrainian-Specific Factors** (if applicable)
7. **Recommendations** (how to apply this thinking)

---

## Learning Outcomes

**By using this tool, you will:**

- ✅ Understand pedagogical principles (not just follow recipes)
- ✅ Make informed decisions for new content
- ✅ Identify when to follow patterns vs. when to diverge
- ✅ Explain curriculum design to others
- ✅ Improve curriculum over time with solid rationale

**This is not just for executing tasks - it's for becoming a better curriculum designer.**

---

## Notes

**This is a learning tool, not a decision-making tool.**

- I explain decisions, I don't make them for you
- You still decide what to do
- But now you understand why each approach works (or doesn't)

**Ask anything you want to understand:**
- "Why is X before Y?"
- "Why this word count?"
- "Why these activities?"
- "Why at this level?"

**No question is too simple.** Understanding fundamentals makes you better at this work.
