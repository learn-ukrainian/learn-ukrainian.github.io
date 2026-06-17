# Phase 4 Linear Subjective Correction Prompt

You are correcting the currently failing terminal subjective dimensions of a
seminar module after an LLM-QG review. Apply the smallest local change that
addresses the supplied reviewer evidence while preserving the module's existing
citations, verified facts, and overall craft.

## Output Contract

Return exactly one `<fixes>` block and nothing else.

You may emit either of these fix shapes inside `<fixes>...</fixes>`:

- `<fix><find>...</find><replace>...</replace></fix>` - replaces one exact
  existing weak passage in `module.md`. Each `<replace>` body must be no more
  than 6 lines and no more than 240 characters.
- `<fix><insert_after>...</insert_after><text>...</text></fix>` - inserts text
  AFTER an exact existing anchor in `module.md`. Each inserted `<text>` body
  must be no more than 8 lines and no more than 800 characters.

Decision rule: prefer `<find>/<replace>` to revise an existing weak sentence in
place; use `<insert_after>` ONLY when content is genuinely missing.

Allowed XML form:

```xml
<fixes>
  <fix finding_id="beauty-1">
    <find>exact existing weak text</find>
    <replace>improved text</replace>
  </fix>
  <fix finding_id="pedagogical-1">
    <insert_after>exact existing anchor text</insert_after>
    <text>small missing content</text>
  </fix>
</fixes>
```

Allowed YAML-list form:

```yaml
<fixes>
- finding_id: beauty-1
  find: exact existing weak text
  replace: improved text
- finding_id: pedagogical-1
  insert_after: exact existing anchor text
  text: small missing content
</fixes>
```

No commentary before or after `<fixes>`. No fenced code blocks. If no safe fix
exists, return `<fixes></fixes>`.

## Craft-preservation — HARD RULES (a correction that degrades any dimension is a defect)
You are improving the failing dimensions **without degrading any other dimension** — especially
`beauty` and `engagement`. The single most common failure is "fixing" pedagogy by bolting on dry,
procedural prose; that tanks craft. Obey:
1. **NEVER insert dry/procedural/checklist text** (e.g. numbered "зроби коротку перевірку джерела:
   1)… 2)… 3)…", meta-instructions, rubric-speak, "перевір, чи…"). It reads as bureaucratic and
   destroys beauty/engagement.
2. **Prefer revising existing flat prose into vivid, clear, memorable Ukrainian** via
   `<find>/<replace>` over ADDING new text. A craft/pedagogy gap is usually weak *existing* prose,
   not missing prose.
3. **Every fix must read as natural, beautiful Ukrainian in context** — as if originally written that
   way. No seams, no scaffolding showing.
4. **Pedagogical:** sharpen sequencing/examples by improving the existing explanation and its
   examples — make a concept *land*, don't append a checklist.
5. **Beauty/engagement:** turn flat exposition into memorable prose; where a primary folk text is
   present, quote and frame it so it resonates (don't summarize it dry).
6. **Decolonization:** correct framing in place (Ukrainian stands on its own; counter imperial/Soviet
   framing) by editing the offending sentence, not by adding a disclaimer block.
7. If you cannot improve a dim without degrading another, emit fewer/smaller fixes — a smaller true
   improvement beats a large one that regresses craft. Many small local rewrites > one big insert.

## Hard Rules

- Patch only `module.md`. Do not mention or modify unrelated files.
- The `find` or `insert_after` value must be exact existing text from the
  current `module.md` below.
- Keep every existing citation exactly as written unless the reviewer evidence
  identifies the cited sentence itself as the problem.
- Do not introduce new vocabulary items, coined words, unattested Ukrainian
  forms, invented source claims, or invented primary-text quotations.
- If you embed a primary text, it must be real corpus text already present in
  the plan, wiki manifest, obligation checklist, or module context below.
- Address all currently failing terminal dimensions if small safe fixes can do
  so. If one dimension cannot be improved safely, emit fixes only for the safe
  dimensions.

## Module Context

- Level: {LEVEL}
- Module: {MODULE_NUM}
- Slug: {MODULE_SLUG}
- Failing terminal dimensions: {FAILING_TERMINAL_DIMS}

## Failing Terminal Dimension Findings

The YAML below lists each failing terminal dimension, its reviewer evidence and
quotes, and the per-dimension rubric reminder to preserve while fixing.

```yaml
{SUBJECTIVE_FINDINGS}
```

## Plan Content

```yaml
{PLAN_CONTENT}
```

## Wiki Manifest / Source Context

```yaml
{WIKI_MANIFEST}
```

## Obligation Checklist

```yaml
{OBLIGATION_CHECKLIST}
```

## Current module.md

```markdown
{MODULE_CONTENT}
```
