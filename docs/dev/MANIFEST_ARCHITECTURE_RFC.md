# RFC: Manifest-Driven Curriculum Architecture

**Status:** 📋 PROPOSAL
**Goal:** Decouple curriculum logic (ordering, numbering) from physical storage (filenames, folders) to enable "Renumber-Free" restructuring.

## The Problem

Currently, the curriculum structure is tightly coupled to the filesystem:
1.  **Ordering:** Defined by `01-`, `02-` prefixes in filenames.
2.  **Discovery:** Scripts iterate specific folders (`a1`, `b2`) and glob `*.md`.
3.  **Fragility:** Inserting a module at #5 requires renaming #6 through #100.
4.  **Link Rot:** Renaming a file breaks all internal links (`[Link](05-old-name.md)`).

## The Solution: Manifest-Driven Architecture

### 1. The Manifest (`curriculum.yaml`)

A single source of truth defining the *logical* structure of the course.

```yaml
curriculum:
  version: "2.0"
  tracks:
    core:
      title: "Core Path"
      levels:
        - id: "a1"
          title: "A1: Survivor"
          modules:
            - slug: "alphabet-intro"
              path: "a1/alphabet-intro.md"  # Physical path (no number)
              uuid: "a1-001"                # Stable ID for database/analytics
            - slug: "basic-greetings"
              path: "a1/basic-greetings.md"
        - id: "b2"
          modules:
            - slug: "future-perfect"
              path: "b2/future-perfect.md"
            # NOTE: History modules moved out, but files can stay or move
            
    b2-hist:
      title: "Ukrainian History"
      modules:
        - slug: "kyivan-rus"
          path: "b2-hist/kyivan-rus.md" # or even keep in b2/ if we want
```

### 2. Physical Storage (The "Repository")

Files are stored in "buckets" or tracks, but **filenames do not contain numbers**.

*   `curriculum/l2-uk-en/a1/alphabet-intro.md`
*   `curriculum/l2-uk-en/a1/basic-greetings.md`
*   `curriculum/l2-uk-en/b2/kyivan-rus.md`

**Benefit:**
*   To reorder: Change lines in `curriculum.yaml`.
*   To insert: Add line in `curriculum.yaml`.
*   To move track: Move line in `curriculum.yaml`.

### 3. Stable Linking Strategy

Links must survive reordering.

**New Syntax Proposal:**
*   Use the `slug` as the anchor.
*   Format: `[Link Text](@module/kyivan-rus)` or `[Link Text](slug:kyivan-rus)`
*   **Preprocessor:** The build script (MDX Generator) replaces `slug:kyivan-rus` with the actual calculated relative path (e.g., `../b2-hist/module-01.mdx`) based on the *current* manifest order.

### 4. Migration Plan (Incremental)

**Phase 1: The Manifest (Parallel Run)**
1.  Generate `curriculum.yaml` from current filesystem.
2.  Update `generate_mdx.py` to *optionally* read from manifest if present.
3.  Validate that Manifest-generated output matches Filesystem-generated output.

**Phase 2: The Decoupling**
1.  **Stop Renaming:** New modules get semantic names only (`a1/restaurant-scenario.md`), no numbers.
2.  **Update Manifest:** Add new modules to `curriculum.yaml`.
3.  **Pipeline Switch:** Switch default pipeline to read Manifest.

**Phase 3: Cleanup**
1.  Batch rename all existing files to remove `01-` prefixes.
2.  Update all internal links to use `slug:` syntax (via script).

## Immediate Next Steps (Pre-Reorganization)

1.  Create `scripts/generate_manifest.py` to snapshot current state.
2.  Draft `curriculum.yaml`.
3.  This allows us to implement the Reorganization (RFC #409) purely by editing the YAML file, avoiding the "renumbering hell".
