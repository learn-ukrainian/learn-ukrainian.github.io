# Phase 4 Linear Pedagogical Correction Prompt

You are correcting the `pedagogical` dimension of a seminar module after an
LLM-QG review. Apply the smallest additive change that addresses the supplied
review finding while preserving every existing sentence.

## Output Contract

Return exactly one `<fixes>` block and nothing else.

You may emit ONLY this fix shape inside `<fixes>...</fixes>`:

- `<fix><insert_after>...</insert_after><text>...</text></fix>` - inserts
  AFTER an existing anchor in `module.md`.

Allowed XML form:

```xml
<fixes>
  <fix finding_id="pedagogical-1">
    <insert_after>exact existing anchor text</insert_after>
    <text>small inserted pedagogical scaffold</text>
  </fix>
</fixes>
```

Allowed YAML-list form:

```yaml
<fixes>
- finding_id: pedagogical-1
  insert_after: exact existing anchor text
  text: small inserted pedagogical scaffold
</fixes>
```

No commentary before or after `<fixes>`. No fenced code blocks. If no safe
insert exists, return `<fixes></fixes>`.

## Hard Rules

- Use `insert_after` ONLY. Never emit `find`, `replace`, deletion, or any
  instruction that rewrites existing prose.
- The `insert_after` value must be exact existing anchor text from the current
  `module.md` below.
- Keep every existing citation exactly as written.
- Do not introduce new vocabulary items, coined words, or unattested
  Ukrainian forms.
- If you embed a primary text, it must be real corpus text already present in
  the plan, wiki manifest, obligation checklist, or module context below.
  Never invent quotes or paraphrase a quote as if it were primary text.
- Each inserted `text` body must be narrowly pedagogical: no more than 8 lines
  and no more than 800 characters.
- Patch only `module.md`. Do not mention or modify unrelated files.

## Allowed Additive Moves

Choose the smallest move that addresses the finding:

- surface or embed the primary text the module teaches,
- insert a self-check or reflection prompt,
- insert a worked example or inline activity scaffold,
- insert a short "why this matters" clarifying note.

## Module Context

- Level: {LEVEL}
- Module: {MODULE_NUM}
- Slug: {MODULE_SLUG}

## Pedagogical Findings

```yaml
{PEDAGOGICAL_FINDINGS}
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
