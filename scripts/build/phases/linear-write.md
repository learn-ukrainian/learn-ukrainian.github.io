{NORTH_STAR}

{LESSON_CONTRACT}

# Phase 4 Linear Writer Prompt

Write the A1 module using the plan and contract below. Produce exactly four
authoring artifacts: `module.md`, `activities.yaml`, `vocabulary.yaml`, and
`resources.yaml`.

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
    "title": "..."
  }
]
```

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

`module.md` itself stays Markdown. Only the three structured-data blocks move
to JSON. The pipeline serializes those parsed JSON values to YAML for storage.
Use `json` fences only for these three structured artifacts; do not fence prose
inside `module.md`.

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

- **No English meta-narration.** Do not write phrases like "Welcome to the
  start of our journey", "In this section we will learn", "Now that you have
  seen these verbs", "Let's now look at", "Before we move on", or any
  variant. They burn English words and miss the immersion target. Open each
  prose section directly with the grammar point in Ukrainian, with a
  Ukrainian dialogue line, or with the example itself.
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

## Activity Component Props (mandatory)

Each activity object in `activities.yaml` MUST carry the props for its
declared `type` exactly as specified below. The build's `component_props`
gate compares these against `docs/lesson-schema.yaml` and fails the build
on any missing required prop. Do not invent prop names; do not borrow a
prop name from a different activity type (for example, `fill-in` requires
`items: FillInItem[]` — do not substitute `passage:`).

```
{COMPONENT_PROPS_SCHEMA}
```

For nested array item types (e.g. `FillInItem[]`), include the listed
fields on every item. For numeric arrays like `correct_order: number[]`,
indices are zero-based.

## Plan

```yaml
{PLAN_CONTENT}
```

## Knowledge Packet

{KNOWLEDGE_PACKET}
