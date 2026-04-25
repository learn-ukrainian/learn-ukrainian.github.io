# Human Evaluation Rubric — Ukrainian Curriculum Modules

> **Purpose:** A native-speaker rubric for rating a completed module on the
> same 9 dimensions the LLM reviewers use, so we can measure inter-rater
> reliability and catch subtle quality drift.
>
> **For:** the native reviewer, the native reviewer, and any native-speaker reviewer.
> **Time:** 20–30 minutes per module.
> **Output:** Fill in `docs/eval/evaluations/{reviewer}-{YYYY-MM-DD}-{level}-{slug}.yaml`
> using the template at the end of this file.

---

## How to use

1. Open the module at `https://learn-ukrainian.github.io/{level}/{slug}`
   (or read the source at `curriculum/l2-uk-en/{level}/{slug}.md`).
2. Read the lesson prose in full. Do the exercises.
3. Score each of the 9 dimensions below 0–10 using the rubric anchors.
4. For each dimension scoring below 9, cite **specific examples** from the
   module (a sentence, an exercise, a word) that anchor your score.
5. Fill in the YAML template and save it.
6. Submit as a PR or email to the maintainer.

**Scoring scale:**

- **10** = Native-level, could appear in a published textbook without edits
- **9** = Very good. Minor improvements possible but nothing that would
  confuse or mislead a learner
- **8** = Good. A few issues that should be fixed but none blocking
- **7** = Acceptable. Clear weaknesses a teacher would flag in review
- **6** = Below standard. Needs rewriting of at least one section
- **5 or below** = Failing. Should not be published as-is

You can score in whole numbers only (no half points). When in doubt between
two scores, take the lower.

---

## The 9 dimensions

### 1. Plan Adherence

Does the module match its plan YAML? Word target hit? Required sections
present? Stated objectives actually taught?

- **10** — All objectives met, all sections present, word target hit
  within ±5%
- **8** — All objectives met but one section is short or shallow
- **6** — An objective is missing or barely touched
- **0–4** — The module is about a different topic than the plan

### 2. Linguistic Accuracy

Is the Ukrainian grammatically correct? No Russianisms, no calques, no
Surzhyk, no non-existent word forms, no wrong stress marks, no case errors.

- **10** — Zero errors; every form is VESUM-verified
- **8** — One or two minor stylistic choices you'd change, no actual errors
- **6** — One genuine error (wrong case ending, wrong aspect, Russianism)
- **0–4** — Multiple errors, or any error that would teach the learner
  something wrong

### 3. Pedagogical Quality

Is this a good lesson? Does it build from simple to complex? Does it
explain WHY, not just WHAT? Would a teen/adult L2 learner understand it?

- **10** — Follows natural acquisition order, shows before tells, explains
  exceptions without overwhelming
- **8** — Solid lesson with a small structural issue (e.g. introduces two
  new concepts at once)
- **6** — Rule dumped on the learner without examples, or the examples
  don't illustrate the rule
- **0–4** — The lesson is confusing or actively misleading

### 4. Cultural Accuracy

Are the examples, contexts, and references culturally authentic Ukrainian?
No Western tropes pretending to be Ukrainian, no Russian-framed history,
no "post-Soviet" hedging.

- **10** — Every example feels like it comes from a real Ukrainian
  environment; decolonized framing throughout
- **8** — Culturally solid with one example that feels generic/Western
- **6** — Multiple examples read as translations from English or Russian
- **0–4** — The module is culturally inert or actively imports foreign
  framing

### 5. Vocabulary Coverage

Does the vocabulary section introduce the right words for the level? Are
they level-appropriate (A1 words in A1 modules)? Are the translations
accurate and contextual?

- **10** — All words at the right CEFR level, accurate contextual
  translations, no missing core words
- **8** — One or two words that feel slightly too advanced/basic; translations correct
- **6** — Multiple level mismatches, or a translation that is wrong in context
- **0–4** — Vocabulary is wrong or inappropriate

### 6. Exercise Quality

Do the exercises test language skill (not content recall)? Are they
well-calibrated for the level? Are the distractors in multiple-choice
questions plausible?

- **10** — Every exercise teaches something; no content-recall masquerading
  as a language test
- **8** — Mostly good, one exercise is too easy or too hard
- **6** — One exercise tests content recall instead of language skill
- **0–4** — Multiple broken exercises or exercises that would frustrate a
  learner into giving up

### 7. Dialogue Quality

Are the dialogues natural Ukrainian conversations? Do they reflect real
situations? Is the language register appropriate for the speakers?

- **10** — Every line sounds like something a real person would say
- **8** — Mostly natural with one stilted exchange
- **6** — Feels scripted or like an interrogation, but still teachable
- **0–4** — Unnatural, weird register, or impossible situations

### 8. Structural Integrity

Does the MDX render correctly? All 4 tabs present? Headings in order?
Tables formatted? No broken links?

- **10** — Renders perfectly on the site
- **8** — Small formatting issue (e.g. a hanging comma, a missing period)
- **6** — One broken link or malformed table
- **0–4** — The module does not render or is missing a tab

### 9. Engagement & Tone

Is the module engaging without being gimmicky? Does it read warmly
without condescension? Would a motivated adult enjoy reading it?

- **10** — Reads naturally, holds attention, never condescends
- **8** — Mostly engaging with one stretch that drags
- **6** — Dry or mechanical but not actively boring
- **0–4** — The module is tedious, condescending, or actively
  off-putting

---

## YAML output template

Save to `docs/eval/evaluations/{reviewer}-{YYYY-MM-DD}-{level}-{slug}.yaml`:

```yaml
reviewer: "the native reviewer"           # your name (or handle)
reviewer_role: "native teacher"  # native teacher / linguist / learner
evaluated_on: 2026-04-12      # ISO date
module:
  level: "a1"
  slug: "my-family"
  url: "https://learn-ukrainian.github.io/a1/my-family"

scores:
  plan_adherence: 9
  linguistic_accuracy: 10
  pedagogical_quality: 8
  cultural_accuracy: 9
  vocabulary_coverage: 10
  exercise_quality: 7
  dialogue_quality: 9
  structural_integrity: 10
  engagement_and_tone: 8

average: 8.9   # compute at the end

# For any dimension scoring below 9, cite examples:
notes:
  exercise_quality: |
    Exercise 3 (True/False) is too easy — a beginner would answer it
    without reading the text. Rewrite with harder distractors.
  engagement_and_tone: |
    The section on possessives drags in the middle. Could use one more
    concrete example (e.g. "Це моя бабуся, її звати Ольга.")

# Overall impression — one paragraph, plain language
overall: |
  Strong module. Grammatically perfect, well-structured, culturally
  authentic. The two weak points are one too-easy exercise and one
  draggy section in the middle. I'd publish this with those two fixes.

# Would you show this to your own students?
publishable: true  # true / with-edits / no
```

---

## What happens with your ratings

- Stored under `docs/eval/evaluations/` as the ground-truth dataset.
- `scripts/eval/human_eval_tracker.py` computes inter-rater reliability
  (human vs Claude vs Gemini review scores) over time.
- Modules you rate ≥9 become "golden reference" modules — used as
  regression anchors when we change prompts.
- Modules you rate ≤7 become fix candidates — the maintainer or a new
  pipeline pass will revisit them.

Your ratings are the most valuable data this project has. Thank you for
reviewing.
