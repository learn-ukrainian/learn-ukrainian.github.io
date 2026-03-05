---
name: content-review
description: Post-build module quality review. Checks plan adherence, linguistic accuracy, pedagogical quality, activities, vocabulary completeness, engagement.
argument-hint: <path-to-module.md | track slug>
---

# Content Review: $ARGUMENTS

## Parse Arguments

The user provides one of these argument patterns:

1. **Full path**: `curriculum/l2-uk-en/a1/the-cyrillic-code-i.md`
2. **Track + slug**: `a1 the-cyrillic-code-i`
3. **Track + sequence**: `a1 1`

Parse the arguments to locate the module's files:

- **Content markdown**: `curriculum/l2-uk-en/{track}/{slug}.md`
- **Activities YAML**: `curriculum/l2-uk-en/{track}/activities/{slug}.yaml`
- **Vocabulary YAML**: `curriculum/l2-uk-en/{track}/vocabulary/{slug}.yaml` (if it exists)
- **Meta YAML**: `curriculum/l2-uk-en/{track}/meta/{slug}.yaml`
- **Plan YAML**: `curriculum/l2-uk-en/plans/{track}/{slug}.yaml`

If a track + sequence is given, find the slug by reading plan files to match `sequence:`.

## Execute

Read and follow the full content review prompt at [content-review-prompt.md](content-review-prompt.md).

**Output path**: Save the review to `curriculum/l2-uk-en/{track}/audit/{slug}-content-review.md`

Reference issue #730.
