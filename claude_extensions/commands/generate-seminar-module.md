# Generate Seminar Module (Meta-Driven)

> **⚠️ ALWAYS use `.venv/bin/python` - NEVER use `python3` or `python` directly!**

Generates a high-quality "Seminar Style" module (e.g., B2-HIST, C1) strictly based on its Metadata YAML.
This command replaces the generic `/module-create` for advanced modules.

## Prerequisites

1.  **Meta YAML MUST exist**: `curriculum/l2-uk-en/{level}/meta/{slug}.yaml`
2.  **Vocab YAML MUST exist**: `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml`

## Usage

```
/generate-seminar-module [LEVEL] [SLUG]
```

**Example:**
```
/generate-seminar-module b2-hist scythians-sarmatians
```

## Workflow

### Step 1: Validation & Setup

1.  **Read Schema**: Read `schemas/meta-module.schema.json`.
2.  **Read Meta**: Read `curriculum/l2-uk-en/{LEVEL}/meta/{SLUG}.yaml`.
3.  **Read Vocab**: Read `curriculum/l2-uk-en/{LEVEL}/vocabulary/{SLUG}.yaml`.
4.  **Validate**:
    *   Ensure Meta YAML complies with the Schema.
    *   Ensure `pedagogy: seminar` is set (or warn if not).
    *   Ensure `content_outline` and `sources` are present.

### Step 2: Content Generation (Markdown)

**Goal**: Create `curriculum/l2-uk-en/{LEVEL}/{SLUG}.md`

1.  **Strict Outline Adherence**: Iterate through `content_outline` in the Meta YAML.
2.  **Richness**:
    *   Use **Sources** defined in Meta YAML for factual accuracy.
    *   Integrate **Vocabulary** from `vocabulary/{SLUG}.yaml` naturally.
    *   Add **Callouts**: `[!history-bite]`, `[!myth-buster]`, `[!quote]` as appropriate for the content.
3.  **Structure**:
    *   **H1**: `# Title` (From Meta)
    *   **H2**: `## Section Title` (From Outline)
    *   **Content**: Write required word count per section.
    *   **Footer**: Add `> [!resources]` block at the very end.

**Prompting Strategy**:
"You are a specialized textbook author. Write the content for module '{TITLE}' based strictly on the provided outline. Do not deviate from the section structure. Use the provided sources to ensure historical accuracy. Tone: {REGISTER}."

### Step 3: Activity Generation (YAML)

**Goal**: Create `curriculum/l2-uk-en/{LEVEL}/activities/{SLUG}.yaml`

1.  **Read Activity Hints**: Read `activity_hints` from Meta YAML.
2.  **Generate**: Create one activity for each hint.
    *   **Type**: Match the `type` field.
    *   **Focus**: Match the `focus` description.
    *   **Items**: Generate the requested number of items.
3.  **Format**: Ensure valid YAML output adhering to `docs/ACTIVITY-YAML-REFERENCE.md`.

### Step 4: Audit & Verification

1.  **Run Audit**:
    ```bash
    .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{LEVEL}/{SLUG}.md
    ```
2.  **Fix Violations**: Automatically fix any issues reported by the audit script.
3.  **Check Integrity**:
    *   Verify all sections from outline exist.
    *   Verify word count targets are met.

## Output

*   **Markdown**: `curriculum/l2-uk-en/{level}/{slug}.md`
*   **Activities**: `curriculum/l2-uk-en/{level}/activities/{slug}.yaml`
*   **Audit Report**: `(stdout)`

## Troubleshooting

*   **"Meta YAML not found"**: You must create the metadata file first.
*   **"Schema validation failed"**: Fix the YAML structure before generating.
*   **"Word count too low"**: The generator will be prompted to expand sections.
