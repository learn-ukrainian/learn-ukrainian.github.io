# Lesson Schema YAML — Phase 3 design (#1584)

> **Status:** DESIGN DRAFT v2 — 3-agent review thread
> `911722b35b3d4cb7abe19059a1ba1044` ran 2 rounds; both Codex + Gemini
> ended `[DISAGREE]` with the explicit framing "design shape is
> correct, sign off after these specific fixes." All 7 findings
> applied in v2. Conditional sign-off stands; if morning user wants a
> formal `[AGREE]` round on the v2 fixes, re-run `ab discuss
> architecture` with the v2 doc.
>
> **Authority:** Phase 0 docs (`docs/north-star.md`,
> `docs/lesson-contract.md`). This design specifies HOW the lesson
> contract becomes machine-consumable; it does NOT amend the contract.
>
> **Sub-issue:** #1584 (under EPIC #1577).

---

## What this design defines

Two coupled artifacts:

1. **`docs/lesson-schema.yaml`** — per-Starlight-component prop schema.
   One YAML entry per component. Source of truth for what data each
   component consumes. Both the writer prompt (when generating
   `activities.yaml`, `vocabulary.yaml`, etc.) and Python QG (when
   validating writer output before MDX assembly) read this schema.

2. **`scripts/build/prompt_builder.py`** — substitution mechanism that
   fills `{NORTH_STAR}` and `{LESSON_CONTRACT}` placeholders in any
   prompt template. The placeholders were added in Phase 0
   (`scripts/build/phases/v6-write.md` v2.6.0); this is the code that
   makes them functional.

## Why YAML for the schema

The lesson contract enumerates components and tabs. The schema fills
in WHAT DATA each component takes. Two consumers need this:

- **Writer prompt** at build time — needs to know "to emit a `quiz`
  activity, produce a YAML object with these keys, these types, this
  validation." Templating into the prompt as a YAML block is direct.
- **Python QG** at validation time — loads the schema, walks the
  writer's `activities.yaml`, validates each entry against its type's
  schema. Standard YAML schema validation pattern.

TypeScript types in the component files are the runtime truth, but
TS is not consumable by Python without parsing TS itself. YAML is the
lowest-common-denominator format both layers parse natively.

The YAML schema is GENERATED from the TS interfaces by a build step,
not hand-maintained — a single source of truth (the `.tsx` interface)
prevents drift. See §4 below.

## §1 Schema format

One YAML document. Top-level: `components:` map keyed by component
name. Each value: a record with `tab`, `level_scope`, `props`, and
`example`.

### Format spec

```yaml
schema_version: "1.0"
generator_version: "1.0.0"      # bumped when generator output changes shape
generated_from:                 # deterministic provenance — content hashes, not timestamps
  components_dir: starlight/src/components/{*.tsx, *.astro}
  components_sha256: <hex>      # hash of every input .tsx/.astro file's content concatenated by sorted path
  config_tables_sha256: <hex>   # hash of scripts/pipeline/config_tables.py at generation time
  lesson_contract_sha256: <hex> # hash of docs/lesson-contract.md at generation time

components:
  <ComponentName>:
    tab: lesson | vocabulary | activities | resources
    level_scope: [a1, a2, b1, ...]   # GENERATED ENFORCEMENT DATA derived from ACTIVITY_CONFIGS — NOT the policy authority. The authority is scripts/pipeline/config_tables.py + docs/best-practices/activity-pedagogy.md (matrix doc derived from the config).
    activity_type: <string> | null   # for activity components, the `type` string in activities.yaml; null for prose components
    placement: inline | workbook | both | n/a   # for activity components only
    props:
      required:
        - name: <prop_name>
          type: string | number | boolean | string[] | object | <ref>
          description: <short>
          ukrainian_text: true | false | maybe
            # if true, Python QG applies the module's tab-aware Ukrainian-language policy
            # (per Lesson Contract §4.6 + IMMERSION_POLICIES band rule for the module's level)
            # if maybe, preserve source-language text and skip Ukrainian-only enforcement
            # unless the source itself is Ukrainian (used by SourceBox.quote where source
            # language varies)
            # if false, never apply the Ukrainian-language policy to this prop
      optional:
        - name: <prop_name>
          type: <type>
          default: <value>
          description: <short>
    nested_types:    # for props whose type is a complex object
      <TypeName>:
        - name: <field_name>
          type: <type>
          description: <short>
    example:    # canonical example used in writer prompt + tests
      <yaml block matching the schema>
    deprecated: true | false   # default false; if true, writer must not emit
    deprecation_reason: <string> | null
```

### Metadata source — JSDoc tags on TS interfaces

The TS interface alone does NOT carry the metadata the schema needs
(`description`, `ukrainian_text`, `example`). Per Codex F1: TS gives
us shape; JSDoc gives us QG semantics. The generator parses JSDoc
tags on every prop:

```typescript
interface QuizQuestionItem {
  /**
   * @schemaDescription The prompt text shown to the learner.
   * @ukrainianText true
   */
  question: string;
  /**
   * @schemaDescription Array of 2-5 options.
   */
  options: QuizOption[];
}

interface QuizOption {
  /**
   * @ukrainianText true
   */
  text: string;
  correct: boolean;  // no JSDoc → ukrainian_text: false (default)
}
```

Recognized tags:
- `@schemaDescription <text>` — populates `description`
- `@ukrainianText true|false|maybe` — populates `ukrainian_text`
- `@schemaExample <yaml-fragment>` — optional override for the
  per-prop example (default examples come from the worked-example
  set in §2)
- `@deprecated <reason>` — marks the component (or prop) deprecated

**Where JSDoc must be added (Phase 3 implementation work):**
Every prop on every Tab 2 / Tab 3 component in MVP scope (the 19
components listed in Lesson Contract §3.4.a + the 3 Tab-2 components
in §3.3 + Tab-1 narrative components in §3.2 that are inline-renderable
via INJECT_ACTIVITY). Tab-1 prose components (RuleBox, DialogueBox,
YouTubeVideo) get JSDoc on their props too. Total: ~25 component
files get JSDoc additions in Phase 3.

**Components OUT of MVP scope:** still get JSDoc tags on a
best-effort basis but are not in the regeneration drift gate (their
`level_scope` excludes A1/A2/B1).

## §2 Five worked examples

Real prop signatures pulled from the current `.tsx` files. These five
exercise every shape pattern (scalar, array, nested object,
optional-with-default, polymorphic, JSX children).

### `Quiz`

```yaml
Quiz:
  tab: activities
  level_scope: [a1, a2, b1, b2, c1, c2, hist, bio, istorio, lit, b2-pro, c1-pro, oes, ruth]
  activity_type: quiz
  placement: both
  props:
    required:
      - name: questions
        type: QuizQuestionItem[]
        description: Array of question items
    optional:
      - name: instruction
        type: string
        description: Header instruction shown above the question set
        ukrainian_text: true   # at B1+ this MUST be Ukrainian
      - name: isUkrainian
        type: boolean
        default: false
        description: UI flag for Ukrainian rendering
  nested_types:
    QuizQuestionItem:
      - name: question
        type: string
        description: The prompt text
        ukrainian_text: true
      - name: options
        type: QuizOption[]
        description: 2-5 options
    QuizOption:
      - name: text
        type: string
        ukrainian_text: true
      - name: correct
        type: boolean
  example:
    instruction: "Оберіть правильну відповідь"
    questions:
      - question: "Що означає «привіт»?"
        options:
          - text: "Hi"
            correct: true
          - text: "Goodbye"
            correct: false
```

### `FillIn`

```yaml
FillIn:
  tab: activities
  level_scope: [a1, a2, b1, b2, c1, c2, hist, bio, istorio, lit, b2-pro, c1-pro, oes, ruth]
  activity_type: fill-in
  placement: both
  props:
    required:
      - name: items
        type: FillInItem[]
    optional:
      - name: instruction
        type: string
        ukrainian_text: true
      - name: isUkrainian
        type: boolean
        default: false
  nested_types:
    FillInItem:
      - name: sentence
        type: string
        description: Sentence with ____ marker for the blank
        ukrainian_text: true
      - name: answer
        type: string
        ukrainian_text: true
      - name: options
        type: string[]
        description: Optional multiple-choice options; if empty the field is free-input
  example:
    instruction: "Доповніть речення"
    items:
      - sentence: "Я ____ українську мову."
        answer: "вивчаю"
        options: ["вивчаю", "вивчати", "вивчав"]
```

### `VocabCard`

```yaml
VocabCard:
  tab: vocabulary
  level_scope: [a1, a2, b1, b2, c1, c2, hist, bio, istorio, lit, b2-pro, c1-pro, oes, ruth]
  activity_type: null
  placement: n/a
  props:
    required:
      - name: words
        type: VocabEntry[]
    optional:
      - name: title
        type: string
        ukrainian_text: true
      - name: isUkrainian
        type: boolean
        default: false
  nested_types:
    VocabEntry:
      - name: word
        type: string
        description: The Ukrainian lemma (VESUM-verified)
        ukrainian_text: true
      - name: emoji
        type: string
        default: null
      - name: image_url
        type: string
        default: null
      - name: pronunciation_video
        type: string
        default: null
      - name: examples
        type: string[]
        description: Example sentences using the word; minimum 1
        ukrainian_text: true
      - name: category
        type: string
        default: null
      - name: question
        type: string
        default: null
        ukrainian_text: true
  example:
    title: "Словник модуля"
    words:
      - word: "вивчати"
        examples:
          - "Я вивчаю українську мову."
          - "Тарас вивчає історію."
        category: "verb"
```

### `RuleBox`

```yaml
RuleBox:
  tab: lesson
  level_scope: [a1, a2, b1, b2, c1, c2, hist, bio, istorio, lit, b2-pro, c1-pro, oes, ruth]
  activity_type: null
  placement: n/a
  props:
    required:
      - name: title
        type: string
        ukrainian_text: true
      - name: children
        type: jsx
        description: Body content (markdown / MDX inside the box)
    optional:
      - name: icon
        type: string
        default: "📐"
        description: Emoji or icon character
  example: |
    <RuleBox title="Голосні звуки">
    Ukrainian has 6 vowel sounds: [а], [о], [у], [е], [и], [і].
    Letters Я, Ю, Є, Ї are *iotated* — they spell two sounds.
    </RuleBox>
```

### `SourceBox`

```yaml
SourceBox:
  tab: resources
  level_scope: [a1, a2, b1, b2, c1, c2, hist, bio, istorio, lit, b2-pro, c1-pro, oes, ruth]
  activity_type: null
  placement: n/a
  props:
    required:
      - name: title
        type: string
        description: Source title (English titles preserved verbatim per Lesson Contract §3.5)
      - name: quote
        type: string
        description: Quoted excerpt
        ukrainian_text: maybe   # Ukrainian iff source is Ukrainian; otherwise verbatim source language
      - name: citation
        type: string
        description: Author + page + URL
    optional:
      - name: children
        type: jsx
        description: Curator's note (Ukrainian at B1+ per Lesson Contract §3.5)
        ukrainian_text: true
  example: |
    <SourceBox
      title="Заболотний, Українська мова, 5 клас"
      quote="Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо."
      citation="Заболотний 2018, p. 83"
    >
    Класичне формулювання різниці між звуком і літерою.
    </SourceBox>
```

## §3 Schema generation pipeline

`docs/lesson-schema.yaml` is GENERATED from three machine-readable
sources, not hand-maintained. The pipeline:

1. **Source-walk** every lesson-scope component file. Discovery uses
   `rglob("*.tsx")` and `rglob("*.astro")` to catch nested files
   (e.g. future `components/<group>/*.tsx`). The exclusion list comes
   from Lesson Contract §3.1: skip `Footer.astro`, `Head.astro`,
   `Header.astro`, `PageTitle.astro`, `Sidebar.astro`, `Home.tsx`,
   `LevelLanding.tsx`, `LiveStatus.tsx`, `ActivityHelp.tsx`,
   `ActivityPlaceholder.tsx`, `utils.tsx`. Exclusion is policy-based,
   not directory-based — a future `overrides/`-nested lesson-scope
   component would still be included.
2. **Parse the `interface XxxProps` declaration + JSDoc** from each
   component using a small Node.js tool (~50 lines using the
   `typescript` compiler API, which is already a project dep) that
   emits JSON. JSDoc tags (`@schemaDescription`, `@ukrainianText`,
   `@schemaExample`, `@deprecated`) carry the QG metadata that TS
   interfaces alone don't express.
3. **Import `ACTIVITY_CONFIGS`, `INLINE_ONLY_TYPES`,
   `WORKBOOK_ONLY_TYPES`, `FORBIDDEN_ACTIVITY_TYPES`** from
   `scripts/pipeline/config_tables.py` — this is the policy authority
   for activity placement and level allowlists. The schema's
   `level_scope`, `activity_type`, and `placement` fields are
   GENERATED from this config; they are enforcement convenience for
   downstream Python QG, NOT the policy source of truth.
4. **Cross-reference `docs/lesson-contract.md`** for tab assignment
   only (the policy authority for which tab each component lives in).
5. **Emit `docs/lesson-schema.yaml`** with deterministic provenance:
   `generator_version` (semver bumped when generator output changes
   shape), plus `*_sha256` content hashes of every input source. NO
   wall-clock `generated_at` — that would make the file change every
   regeneration even when no input did, breaking the drift gate.

The generation script lives at `scripts/build/generate_lesson_schema.py`.
A pre-commit hook (preferred per Q2 consensus) regenerates the schema
on any change to a component file, `config_tables.py`, or
`lesson-contract.md`; if the output drifts from the committed schema,
the commit fails. CI runs the same check as a backstop.

**Hand-edits forbidden.** All changes to `docs/lesson-schema.yaml`
must come through the generator. This prevents the schema-vs-component
drift that would otherwise quietly accumulate.

## §4 Substitution mechanism

`scripts/build/prompt_builder.py`:

```python
"""Fill {NORTH_STAR} and {LESSON_CONTRACT} placeholders in any
prompt template, and validate that no unknown Phase-0-style token
sneaks through (a typo guard).

Source of truth: docs/north-star.md, docs/lesson-contract.md (Phase 0).
"""
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NORTH_STAR_PATH = PROJECT_ROOT / "docs" / "north-star.md"
LESSON_CONTRACT_PATH = PROJECT_ROOT / "docs" / "lesson-contract.md"

# Phase-0-style placeholders this module substitutes. Phase 4+ may
# add more keys; all must register here.
PLACEHOLDERS = {
    "{NORTH_STAR}": NORTH_STAR_PATH,
    "{LESSON_CONTRACT}": LESSON_CONTRACT_PATH,
}

# Downstream-substituted tokens (.format(**ctx) sites). NOT Phase-0
# concerns; this list exists only so the typo guard knows to skip
# them. Keep in sync with v6_build.py / linear_pipeline.py.
DOWNSTREAM_TOKENS = frozenset({
    "LEVEL", "MODULE_NUM", "TOPIC_TITLE", "PHASE", "WORD_TARGET",
    "WORD_CEILING", "SUMMARY_HEADING", "IMMERSION_RULE",
    "IMMERSION_TARGET_SHORT", "LEVEL_CONSTRAINTS", "CONTRACT_YAML",
    "PRE_VERIFIED_FACTS", "SECTION_WIKI_EXCERPTS",
    "GOLDEN_DIALOGUE_ANCHORS", "EXACT_SECTION_TITLES",
    "CANONICAL_ANCHORS", "DIALOGUE_SITUATIONS",
    "PEDAGOGICAL_CONSTRAINTS", "VOCABULARY_HINTS",
    "PRONUNCIATION_VIDEOS", "GOLDEN_FRAGMENT",
    "VOCABULARY_CHECKLIST",
})

# Pattern for a Phase-0-style token: {ALL_CAPS_WITH_UNDERSCORES}
TOKEN_RE = re.compile(r"\{([A-Z][A-Z0-9_]*)\}")


def render_prompt(template_path: Path) -> str:
    """Load the template, substitute every Phase 0 placeholder, return
    the rendered prompt text. Fails on:
    - Missing Phase 0 source file
    - Known placeholder still present after substitution
    - Unknown placeholder-shaped token (typo guard)
    """
    text = template_path.read_text(encoding="utf-8")

    # Typo guard — scan BEFORE substitution so we see what was
    # actually authored, not what survived replacement.
    for match in TOKEN_RE.finditer(text):
        token = match.group(1)
        if (
            f"{{{token}}}" not in PLACEHOLDERS
            and token not in DOWNSTREAM_TOKENS
        ):
            raise RuntimeError(
                f"Unknown placeholder-shaped token {{{token}}} in "
                f"{template_path}. If this is a new Phase-0 placeholder, "
                f"register it in PLACEHOLDERS. If it's a downstream "
                f".format() variable, register it in DOWNSTREAM_TOKENS. "
                f"If it's a literal brace string, escape it."
            )

    # Substitute Phase 0 placeholders.
    for placeholder, source in PLACEHOLDERS.items():
        if not source.exists():
            raise FileNotFoundError(
                f"Phase 0 source missing for {placeholder}: {source}"
            )
        text = text.replace(placeholder, source.read_text(encoding="utf-8"))

    # Belt-and-suspenders: known placeholder must not survive.
    for placeholder in PLACEHOLDERS:
        if placeholder in text:
            raise RuntimeError(
                f"Unfilled placeholder remains after substitution: "
                f"{placeholder} in {template_path}"
            )
    return text
```

The function is called by every prompt-loading site in the pipeline
(writer, reviewer, activities-author, plan-reviewer). Each existing
caller — typically `Path(...).read_text()` — replaces with
`render_prompt(...)`.

### Why this design choice

- **Plain string substitution, not Jinja2.** Phase 0 placeholders are
  document-level injections, not per-build variable substitution. The
  per-build variables (`{LEVEL}`, `{MODULE_NUM}`, `{IMMERSION_RULE}`,
  `{CONTRACT_YAML}`, etc.) already use `.format(**ctx)` downstream;
  this layer runs FIRST and produces a template string those later
  substitutions still operate on. Two-stage substitution; clean
  separation of concerns.
- **Fail-loud on missing files.** If the user moves or deletes
  `docs/north-star.md`, every build fails with a clear error, not a
  prompt that silently lost its preamble.
- **Fail-loud on UNKNOWN placeholder-shaped tokens.** A typo like
  `{NORHT_STAR}` matches the pattern, isn't in either registry,
  fires the typo guard. (Per Codex F4 minor: the prior version only
  checked known keys and would NOT catch this typo.)
- **Fail-loud on unfilled known placeholders.** Belt-and-suspenders
  even though the typo guard runs first.
- **Downstream-token registry is explicit, not inferred.** The
  generator can't statically know what `.format(**ctx)` keys
  v6_build.py uses — they're hardcoded in `DOWNSTREAM_TOKENS` and
  drift with v6_build.py changes. This is acceptable maintenance
  overhead because the registry change is one-line per new token,
  caught by the typo guard if forgotten.

## §5 Test strategy

### `tests/test_prompt_substitution.py`

```python
import pytest
from pathlib import Path
from build.prompt_builder import render_prompt, PLACEHOLDERS

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "scripts/build/phases"

@pytest.mark.parametrize("template", list(PROMPTS_DIR.glob("v6-*.md")))
def test_no_unfilled_placeholders(template):
    """Every prompt template renders without leaving an unfilled
    Phase 0 placeholder."""
    rendered = render_prompt(template)
    for placeholder in PLACEHOLDERS:
        assert placeholder not in rendered, (
            f"Template {template.name} still has {placeholder} after render"
        )

def test_north_star_loaded():
    """North Star content actually appears in v6-write.md after
    substitution (regression guard against an empty NORTH_STAR file)."""
    rendered = render_prompt(PROMPTS_DIR / "v6-write.md")
    assert "WHO — the learner" in rendered
    assert "B1 onwards is uniformly 100 % Ukrainian" in rendered

def test_lesson_contract_loaded():
    rendered = render_prompt(PROMPTS_DIR / "v6-write.md")
    assert "Tab 3 — Вправи" in rendered
    assert "deprecated; subsumed by `mark-the-words`" in rendered
```

### `tests/test_lesson_schema.py`

```python
import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "docs/lesson-schema.yaml"
COMPONENTS_DIR = PROJECT_ROOT / "starlight/src/components"

EXCLUSIONS = {  # Lesson Contract §3.1 framing + utility (out of lesson scope)
    "utils",
    # Site overrides
    "Footer", "Head", "Header", "PageTitle", "Sidebar",
    # Framing
    "Home", "LevelLanding", "LiveStatus",
    "ActivityHelp", "ActivityPlaceholder",
}


def test_every_lesson_scope_component_has_schema():
    """Every lesson-scope .tsx / .astro component has a schema entry.
    Discovery uses rglob to catch nested directories. Exclusion is
    policy-based (Lesson Contract §3.1) not directory-based.
    Any new component added without a schema entry fails this test;
    any orphan schema entry without a backing component fails too."""
    schema = yaml.safe_load(SCHEMA_PATH.read_text())
    declared = set(schema["components"].keys())
    actual = set()
    for ext in ("*.tsx", "*.astro"):
        for f in COMPONENTS_DIR.rglob(ext):    # recursive — catches overrides/, future nesting
            if f.stem not in EXCLUSIONS:
                actual.add(f.stem)
    assert declared == actual, (
        f"missing from schema: {actual - declared}; "
        f"orphan in schema: {declared - actual}"
    )

def test_schema_loadable():
    yaml.safe_load(SCHEMA_PATH.read_text())  # raises if malformed

def test_activity_components_match_pedagogy_matrix():
    """Every activity component's level_scope matches the matrix in
    docs/best-practices/activity-pedagogy.md."""
    # ... cross-reference against the matrix table
```

## §6 Workflow doc (`docs/best-practices/lesson-schema.md`)

Brief workflow for future contributors:

> When you add or modify a Starlight component:
>
> 1. Edit the `.tsx` interface as needed.
> 2. Run `.venv/bin/python scripts/build/generate_lesson_schema.py`.
> 3. Verify the generated `docs/lesson-schema.yaml` diff is what you
>    expect.
> 4. If your change adds a new component, also add it to
>    `docs/lesson-contract.md` §3 (which tab, which level scope).
> 5. If your change adds a new activity type, also add it to
>    `docs/best-practices/activity-pedagogy.md` §3 matrix and
>    `scripts/pipeline/config_tables.py` `ACTIVITY_CONFIGS`.
> 6. Run `.venv/bin/pytest tests/test_lesson_schema.py
>    tests/test_prompt_substitution.py`.
> 7. Commit the component edit + the regenerated schema in the same
>    commit.

## §7 Resolved design decisions (panel-confirmed)

3-agent review thread `911722b35b3d4cb7abe19059a1ba1044` produced
unanimous answers on all 5 open questions (both Codex + Gemini
explicitly aligned, even where they ended `[DISAGREE]` on the v1
draft pending the v2 fixes folded above):

**D1 — TS-AST parser:** Small Node.js tool using the `typescript`
compiler API, ~50 lines, with JSDoc tag parsing for QG metadata.
Node is already a project dep; avoids native build dependencies.

**D2 — Drift gate:** Pre-commit hook (preferred for fail-fast local
detection) with CI as backstop. **Conditional on deterministic
output** — the schema's provenance must be content-hash-based, not
wall-clock timestamp, or the hook fires on every regeneration.
Phase 3 implementation MUST land deterministic provenance before
the hook is wired.

**D3 — `ukrainian_text: maybe`** is canonical (§1). Used for fields
where source language varies (e.g. `SourceBox.quote`). Avoids
forking prop shapes for niche cases.

**D4 — Placeholders:** Single `PLACEHOLDERS` dict in
`prompt_builder.py` for now. Add a `DOWNSTREAM_TOKENS` registry
alongside (per the v2 typo guard, §4) so unknown tokens fail loudly.
Refactor to a separate registry only when ≥10 placeholders exist.

**D5 — `level_scope` enforcement vs authority:** `level_scope` IS
the field Python QG checks against (single enforcement target,
no duplication). It is GENERATED from `ACTIVITY_CONFIGS` and is
NOT the policy authority — that role belongs to
`scripts/pipeline/config_tables.py` + `docs/best-practices/activity-pedagogy.md`
(the matrix doc). Schema regeneration on `config_tables.py` change
is part of the drift gate.

## §8 Implementation plan after sign-off

1. Codex implements `scripts/build/generate_lesson_schema.py` (the
   TS-AST → YAML pipeline)
2. Codex runs it once to emit `docs/lesson-schema.yaml`
3. Codex implements `scripts/build/prompt_builder.py` + tests
4. Codex implements `docs/best-practices/lesson-schema.md` workflow doc
5. Codex opens PR; orchestrator reviews + merges
6. After merge: every existing prompt-loading site in the pipeline
   gets switched to `render_prompt(...)` (separate PR by Codex)

Estimated implementation time: 1.5 days for Codex (matches Phase 3's
3-day budget with margin).

## §9 Scope of the schema

**In scope:** every lesson-scope writer-emittable component. That is
the union of:
- Tab 1 prose components per Lesson Contract §3.2 (RuleBox, DialogueBox,
  YouTubeVideo, plus the higher-level components flagged out-of-MVP
  but still in the repo)
- Tab 2 vocab components per Lesson Contract §3.3 (FlashcardDeck,
  VocabCard, PhraseTable)
- Tab 3 activity components per Lesson Contract §3.4 (the 19 in MVP
  scope per §3.4.a + the 11 out-of-MVP per §3.4.b — the deprecated
  Classify/Select per §3.4.c are flagged `deprecated: true` in the
  schema)
- Tab 4 resource components per Lesson Contract §3.5 (SourceBox,
  YouTubeVideo)

That set is computed deterministically as `(every .tsx ∪ every
.astro) − §3.1 EXCLUSIONS`. The `EXCLUSIONS` constant in §5
matches Lesson Contract §3.1 exactly.

**Out of scope (NOT in the schema):**
- Site framing components (Home, LevelLanding, LiveStatus,
  ActivityHelp, ActivityPlaceholder, utils + the 5 site overrides) —
  Lesson Contract §3.1
- Wiki packet schema (Phase 5)
- Per-band per-level immersion-rule injection (Phase 4 pipeline work)
- Site dictionary schema (#1581 EPIC, separate)
- Generator script per-component prop schemas — they're MECHANICALLY
  filled by the generator at implementation time; only 5 worked
  examples here for design clarity
