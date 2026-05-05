{NORTH_STAR}

{LESSON_CONTRACT}

# Phase 4 Linear Writer Prompt

Write the A1 module using the plan and contract below. Produce exactly four
authoring artifacts: `module.md`, `activities.yaml`, `vocabulary.yaml`, and
`resources.yaml`.

## Reasoning checklist (do this BEFORE drafting — #1673)

Before producing any output, work through these four reasoning steps. If the
model you are running supports extended thinking (Claude, Gemini, GPT-5.5),
use the thinking facility for these steps; the output below does not change
shape, but every section you write must be the result of having reasoned
through these explicitly. Skipping this is the writer-discipline-gate failure
mode that bit Phase 4 round 3.5.

1. **Word budget per section.** Read the Contract YAML below. For each
   contracted section, decide how many of the {WORD_TARGET} words go where.
   Sections with more contract items need more budget. Verify your
   allocation sums to {WORD_TARGET}±5%. Sections that drift more than ±10%
   from their share are a contract violation.

2. **Required plan-vocab terms.** Enumerate the lemmas the Plan requires
   (vocabulary list, plan.required_terms, contract.required_vocabulary).
   For each term, decide which section it appears in and what concrete
   sentence grounds it. A required term that appears in zero sections is a
   contract violation; a required term that appears only as a translation
   gloss without a Ukrainian sentence is also insufficient.

3. **Register check.** Re-read the Immersion Rule above. State internally:
   "I will produce ~X% Ukrainian and ~(100-X)% English in module.md." If
   your draft starts drifting (English bridge sentences expanding, Ukrainian
   examples shrinking), STOP and rebudget — do not push through.

4. **Teaching sequence.** Re-read the Knowledge Packet below. Each citation
   [S1], [S2], etc. is a fact you will teach or anchor on. Decide the
   sequence: which fact comes first, which builds on which, which sections
   carry which facts. A fact in the packet that maps to no section means
   either the section needs that fact or the packet was over-fetched —
   surface either by emitting a `<!-- VERIFY: packet fact [Sn] not used -->`
   marker.

Only after this reasoning is complete, emit the four fenced blocks below.

Return only these four fenced blocks, in this exact order. Do not add prose
before, between, or after the blocks.

```markdown file=module.md
...
```

```json file=activities.yaml
[
  {
    "id": "act-1",
    "type": "fill-in",
    "instruction": "Complete each sentence with the best word.",
    "items": [
      {
        "sentence": "Я ____ о сьомій.",
        "answer": "прокидаюся",
        "options": ["прокидаюся", "сплю", "йду"]
      }
    ]
  }
]
```

Each activity object MUST carry the props for its declared `type` exactly as
laid out in the "Activity Component Props" section below. The example above
is a valid `fill-in`; do not strip the `items` array down to `id/type/title`
just because the example looks shorter that way.

```json file=vocabulary.yaml
[
  {
    "lemma": "прокидатися",
    "translation": "to wake up",
    "pos": "verb",
    "usage": "Я прокидаюся о сьомій."
  }
]
```

```json file=resources.yaml
[
  {
    "title": "Караман Grade 10, p.176",
    "notes": "Зворотні дієслова: суфікс -ся означає дію, спрямовану на себе."
  }
]
```

## Output format (strict)

Emit `activities.yaml`, `vocabulary.yaml`, and `resources.yaml` as separate
fenced JSON code blocks labeled with the language `json`. Exactly one JSON
block per structured artifact. Do not include trailing commas. Do not include
comments. Do not mix YAML or prose into JSON blocks. The pipeline uses
`json.loads` and fails the build on any parse error.

Inside the `module.md` artifact, do NOT use triple backticks (```) for ANY
purpose — no fenced code, no fenced quote, no fenced text. Use plain paragraphs,
lists, or tables instead. Triple backticks inside the artifact will be parsed as
a closing fence and break the artifact boundary. Single backticks for inline code
spans (e.g., `verify_words`) are fine — only triple backticks are forbidden.

## Module Context

- Level: {LEVEL}
- Module: {MODULE_NUM}
- Slug: {MODULE_SLUG}
- Topic: {TOPIC_TITLE}
- Phase: {PHASE}
- Word target: {WORD_TARGET}

## Immersion Rule

{IMMERSION_RULE}

## Contract YAML

```yaml
{CONTRACT_YAML}
```

## Tone and immersion (mandatory)

The prose of `module.md` is for a learner who is encountering Ukrainian, not
for a teacher narrating their own lesson plan. Hold to this register:

- **No English meta-narration.** Do not write transitional or instructional
  framing phrases. Specifically forbidden, with no exceptions:
  - "Welcome to the start of our journey"
  - "In this section we will learn"
  - "Now that you have seen these verbs"
  - "Let's now look at"
  - "Before we move on"
  - "Note that…", "Notice that…", "Observe that…", "Observe how…"
  - "Pay attention to…", "Remember that…", "It is important to…"
  - Any English sentence that opens with a teacher-facing transition verb
    ("Let's…", "We will…", "You should now…")
  Open each prose section directly with the grammar point in Ukrainian,
  with a Ukrainian dialogue line, with the example itself, or with a
  one-sentence English statement of the grammar fact (no warm-up).
- **English is for translation, gloss, and short scaffolds, never for
  framing.** Treat English as a footnote that supports a Ukrainian sentence,
  not as a frame around it.
- **Honor the immersion ratio in the "Immersion Rule" section above.** It
  is not a target to approach asymptotically; over-writing in English is
  the single biggest failure mode of this prompt. Write less English, not
  more Ukrainian.
- **Section length is bounded by the contract YAML.** If you find yourself
  expanding an English bridge sentence, cut it instead. Word budgets are
  authoritative.

## Activity Types

Allowed: {ALLOWED_ACTIVITY_TYPES}

Forbidden: {FORBIDDEN_ACTIVITY_TYPES}

Inline allowed: {INLINE_ALLOWED_TYPES}

Workbook allowed: {WORKBOOK_ALLOWED_TYPES}

Activity count target: {ACTIVITY_COUNT_TARGET}

Vocabulary count target: {VOCAB_COUNT_TARGET}

## Activity Authoring Fields (mandatory)

Each activity object in `activities.yaml` MUST use the authoring field names
listed below for its declared `type`. These are the JSON/YAML fields consumed
by `scripts/yaml_activities.py` and checked by the writer parser. They are not
React component prop names.

Do not invent prop names. Do not borrow a prop name from a different activity
type. In particular, for `quiz`, `select`, and `translate`, use the authoring
field `items`; do NOT use the React/component prop name `questions`.

```
{COMPONENT_PROPS_SCHEMA}
```

For item-bearing types, include a non-empty `items` array. For numeric arrays
like `correct_order`, indices are zero-based.

## Plan

```yaml
{PLAN_CONTENT}
```

## Knowledge Packet

{KNOWLEDGE_PACKET}
