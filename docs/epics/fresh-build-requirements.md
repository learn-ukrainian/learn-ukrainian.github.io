# Fresh lesson-based build — requirements

> Sub-epic [#8397](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8397), parent #7994.
> Source: operator direction, 2026-09-21. Status: **draft for operator correction**. Once the
> operator accepts it, this file is the frozen input for the plan schema, the arcs, the plans and
> the build prompts. A later change to a requirement is made here first, then downstream.

## 1. What changes and what does not

**Changes.** `--upgrade` (preserve and expand an old module) is abandoned for A1–B2: it was
expensive and it misled — upgraded Module 1 shipped with a plan that said "first 7 letters" while
the content taught 33. "Curriculum upgrade" now means an **upgraded build engine** that creates
modules fresh from new plans. The largest visible change is the layout: a module is a sequence of
lessons.

**Does not change.** The methodology: decolonized pedagogy, Ukrainian State Standard 2024,
textbook and corpus grounding, VESUM and stress verification, student-aware immersion derived from
ULP, cross-family review, word targets as minimums, every audit gate passing.

## 2. Requirements

Each requirement has an id so plans, prompts, gates and reviews can cite it.

### Layout

- **R-01 Lessons.** A module is split into lessons of roughly one hour of learner time each.
- **R-02 No lesson cap.** A module has as many lessons as its content needs. Nobody pads a module
  to reach a count or squeezes one to stay under a count.
- **R-03 Recap close.** The last lesson of a module is a learner recap of *that* module. It is not a
  "Textbook Check", not a school-system explainer and not another presentation-practice-production
  cycle.
- **R-04 Targets per lesson.** Word targets are set per lesson and remain minimums.
- **R-05 Previous edition stays.** The earlier edition remains reachable (`/a1-v1/` today).

### Plans

- **R-06 Plan is the spine.** A module plan contains `lessons[]`. Each lesson states its job, its
  inventory (letters or sounds, grammar, vocabulary), its activities and its videos. The writer
  follows the plan; the writer does not invent the lesson structure.
- **R-07 Title equals job.** If a plan's title or subtitle disagrees with what its lessons teach,
  the plan is fixed before anything is written.
- **R-08 Plans are built with the sources MCP.** Teaching points, examples and sequencing are
  taken from pedagogy and knowledge that exists in our corpus (school textbooks, ULP, the
  dictionaries, the style guide, the State Standard), and each plan records where each point came
  from. Every Ukrainian word form, stress and morphological fact in a plan is tool-verified, never
  recalled from memory.
- **R-09 Full arc first.** A level's arc (module order, one-sentence job per module, progression of
  letters, grammar and vocabulary) is written and reviewed before its module plans.

### Build engine

- **R-10 Create, never upgrade.** The engine builds from the plan, the wiki and the MCP.
- **R-11 No context poisoning.** Old builds and old plans are never given to the writer or to the
  engine. The arc author may mine old plans for textbook citations only, and re-verifies each one
  through the MCP before using it.
- **R-12 No hand edits.** `module.md` and its siblings are produced by the engine. A defect is fixed
  in the plan, prompt, gate or code that caused it.
- **R-13 Fast tools.** The sources MCP must support heavy batch use: many words per call, compact
  responses, one "word card" call for morphology + stress + level + meaning (#8398). VESUM alone is
  not enough; ULIF data and the Atlas dictionary are part of the evidence base.

### Language and immersion

- **R-14 A1 immerses gradually.** English scaffolding in A1 is by design and recedes lesson by
  lesson, student-aware: the learner has completed every lesson before this one.
- **R-15 A2 is Ukrainian.** A2 is fully Ukrainian with occasional English support. From A2 the
  English share is never raised.
- **R-16 Simple Ukrainian.** In A1 and A2 the Ukrainian itself is very simple and fits the level of
  the learner that the specific lesson is aimed at — vocabulary and grammar the learner has met, plus
  what this lesson introduces.

### Learner experience

- **R-17 Exercise-rich.** Lessons carry many activities, inline and in the workbook tab.
- **R-18 Video.** A lesson includes YouTube video where a suitable one exists; the plan names it.
  No video is invented or guessed; a lesson without a suitable video simply has none.
- **R-19 Engaging activities.** Activities must be pleasant to use. **Quiz** and
  **find-and-fix-the-error** are the models. Today's **true-false** and **fill-in-the-blank** are
  the examples of a dull experience. Whether each is redesigned or retired is decided by a
  cross-family design discussion, because it changes `docs/best-practices/activity-pedagogy.md`,
  the activity schemas and the site components.

### Scope and order

- **R-20 Levels.** A1 first, then A2, B1, B2, using the same schema, engine and workflow.
- **R-21 Wiki and workflow.** Plans, the wiki and the build workflow are all improved as part of
  this work, not only the prompts.

## 3. Roles

Design and planning sit with the curriculum-upgrade driver seat. Other fleet agents implement from
the driver's briefs. Ukrainian language questions are settled by the sanctioned language lanes.
Every review of record is cross-family at the exact head.

## 4. Open questions for the operator

The operator said some things were probably left unsaid. These are the gaps the driver can see;
each has a proposed default that applies unless corrected.

| # | Question | Proposed default |
| --- | --- | --- |
| Q1 | What counts toward "one hour" — reading, videos, inline activities, workbook? | All learner time in the lesson page, workbook included. The plan estimates it; a gate checks the word and activity minimums, not a clock. |
| Q2 | Does each lesson keep the four tabs (Урок · Словник · Вправи · Ресурси)? | Yes, per lesson; the module landing aggregates. |
| Q3 | Is the learner state tracked per lesson rather than per module? | Yes — "has completed lessons 1..n−1" at lesson grain, including vocabulary met. |
| Q4 | May the new arc rename, split, merge or reorder the 55 A1 modules? | Yes, where the arc review agrees; slugs of published `/a1-v1/` pages do not change. |
| Q5 | Checkpoint modules: keep them, and do they follow the same lesson layout? | Keep; a checkpoint is lessons of mixed review and a self-check, no new material. |
| Q6 | Which video sources are acceptable? | Channels already in the corpus first (ULP and the others in `data/external_articles/`); anything else needs a recorded reason. Link rot is checked by a gate. |
| Q7 | Should vocabulary cards link to the Atlas dictionary entry for the word? | Yes once the Atlas entry exists; until then the card stands alone. |
| Q8 | Should lessons feed spaced review (practice decks) across lessons and modules? | Yes as a later child; the plan schema reserves the field now. |
| Q9 | Audio: is recorded or synthesized pronunciation in scope for A1? | Out of scope here; videos carry pronunciation. Revisit after A1. |
| Q10 | What does "better wiki" mean concretely? | One wiki packet per module that the plan cites, regenerated from the corpus with the same verification rules as plans. To be specified in its own child. |
| Q11 | When A2 is rebuilt, is the current A2 archived like A1 (`/a2-v1/`)? | Yes, same pattern. |

## 5. What "done" means for this document

The operator has read it, corrected it, and the corrected version is merged. Requirements added
later get the next free id; ids are never reused.
