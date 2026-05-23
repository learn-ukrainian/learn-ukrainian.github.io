# Renderer-logic audit findings (F3 carry-over from 2026-05-23)

Date: 2026-05-23
Author: claude-orchestrator (inline, during validation build wait)
Trigger: handoff §"Behavioral lessons" 4 + F7 carry-over — qwen3.7-max flagged that the PR-C strip plan audited template TEXT but not LOGIC; quick grep of `render_writer_prompt` for duplicate-placeholder injections could surface free wins beyond `{KNOWLEDGE_PACKET}` dedup.

## Method

1. Read substitution chain: `render_writer_prompt` → `render_phase_prompt` → `render_prompt` (Phase-0 PLACEHOLDERS = `{NORTH_STAR}` / `{LESSON_CONTRACT}` source-file inlines) + naive `str.replace` over all DOWNSTREAM_TOKENS.
2. Count token occurrences in `scripts/build/phases/linear-write.md` (the claude-tools default).
3. Cross-reference each multi-occurrence token with its position context (content slot vs prose reference).

## Findings

### Bug — silent duplicate expansion of `{COMPONENT_PROPS_SCHEMA}` (and 3 sibling list tokens) in prose paragraph

`scripts/build/phases/linear-write.md:103`:

```
Writer-facing activity authority is inline below: `{ALLOWED_ACTIVITY_TYPES}`, `{INLINE_ALLOWED_TYPES}`, `{WORKBOOK_ALLOWED_TYPES}`, `{COMPONENT_PROPS_SCHEMA}`. Full React component mapping lives in `docs/best-practices/writer-prompt-appendix.md`; canonical contract lives in `docs/lesson-contract.md`.
```

Intent: prose pointer ("these tokens appear inline later — see below"). The backticks tell a human reader "these are token names, not content."

Actual behavior: `render_phase_prompt` does naive `text.replace(f"{{{key}}}", str(value))` for every DOWNSTREAM_TOKEN. Backticks are invisible to the substitution. Each of those four token references silently expands at line 103, then expands AGAIN at the real content slot:

- `{ALLOWED_ACTIVITY_TYPES}` content slot: elsewhere in template
- `{INLINE_ALLOWED_TYPES}` content slot: elsewhere
- `{WORKBOOK_ALLOWED_TYPES}` content slot: elsewhere
- `{COMPONENT_PROPS_SCHEMA}` content slot: line 394 inside ```` ``` ```` code-fence — the intended payload position.

### Cost estimate

- `{COMPONENT_PROPS_SCHEMA}`: ~1–2KB per A1 module (sorted authoring-field spec × allowed types). Extra expansion at L103 = **~1–2KB wasted prompt bytes**.
- `{ALLOWED_ACTIVITY_TYPES}` / `{INLINE_ALLOWED_TYPES}` / `{WORKBOOK_ALLOWED_TYPES}`: short comma lists, ~50–100 bytes each. ~200–400 bytes total.
- `{LEVEL}` × 8 backticked occurrences (L233, L243, L256, L266, L309, L314, L318, L319): `"a1"` = 2 bytes each, ~16 bytes total. **Negligible — leave as-is.**

Realistic save: **~1.5–2.5KB rendered prompt size**, from 120KB → ~118KB.

### Why it matters more than the byte count

The writer reads "Writer-facing activity authority is inline below: [HERE A FULL SCHEMA DUMP, mid-prose-paragraph], [HERE A LIST OF TYPES], ..." instead of "see below for [name]". This is a model-confusion risk — having the full schema mid-paragraph during the "where are things" prose and then AGAIN in the labelled code-fence creates ambiguity about whether the lesson-contract section IS the schema. This is exactly the bug class flagged in the 2026-05-23 PR-sequence handoff (behavioral lesson #5 — `{ALLCAPS_NAME}` in prose body of template-substituted docs).

The current PR-C salvage caught the case where the unresolved-token CHECK would fail (`{COMPONENT_PROPS_SCHEMA}` literal text rendered into reviewer-prompt → unfilled-placeholder check failed). It did NOT catch the case where the token IS in DOWNSTREAM_TOKENS and silently expands.

## Fix

Option A — minimal (recommended): edit line 103 to drop curly braces on the prose references:

```diff
-Writer-facing activity authority is inline below: `{ALLOWED_ACTIVITY_TYPES}`, `{INLINE_ALLOWED_TYPES}`, `{WORKBOOK_ALLOWED_TYPES}`, `{COMPONENT_PROPS_SCHEMA}`. Full React component mapping ...
+Writer-facing activity authority is inline below: `ALLOWED_ACTIVITY_TYPES`, `INLINE_ALLOWED_TYPES`, `WORKBOOK_ALLOWED_TYPES`, `COMPONENT_PROPS_SCHEMA`. Full React component mapping ...
```

Token regex `\{([A-Z][A-Z0-9_]*)\}` requires braces — so backticked bare names are NOT touched by the substitution pass, and the prose meaning is preserved verbatim.

Option B — defense in depth: extend `render_phase_prompt` to detect "token appears inside a backtick-bounded span" and skip those occurrences. Higher complexity, broader blast radius, and doesn't fix the underlying authoring footgun (writers should not write `{ALLCAPS}` in prose at all).

Pre-commit lint would be the structural fix — see carry-over F7-2026-05-23 in the same handoff.

## Validation that this is safe to ship as a separate PR

- Substitution chain unchanged.
- DOWNSTREAM_TOKENS set unchanged.
- The four affected tokens still appear at their dedicated content slots; only the duplicate prose-occurrence inlines are removed.
- No tests assert on prompt body byte-equality at L103 — the strip-plan tests assert on presence of named sections, which is unaffected.
- Behavior change is "rendered writer prompt drops ~2KB" — measurable via `scripts/audit/check_writer_prompt_size.py` rerun.

## Recommended sequencing

After the in-flight a1/my-morning validation build resolves and the post-validation steps complete (promote or diagnose), open as small follow-up PR. Estimated 1-line code change + 1 regression test asserting `linear-write.md` contains no `{[A-Z]...}` token inside backticks except inside a literal code fence.

Filed as a NEW follow-up (call it `F9-2026-05-23` for the next handoff) since it's not covered by the existing F-series.
