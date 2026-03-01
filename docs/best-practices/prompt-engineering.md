# Prompt Engineering Best Practices

> **Scope:** How to write Gemini phase templates (`claude_extensions/phases/gemini/`).
> For what information to include in prompts, see `context-engineering.md`.

---

## Core Principle

Phase templates are contracts. Gemini must know exactly what to produce, in what format, under what constraints. Ambiguity → wrong output → wasted call.

---

## Template Structure

Every phase template must have these sections in order:

1. **Identity line** — who Gemini is, what phase this is, ONE task only
2. **Input** — what files to read (explicit paths via placeholders)
3. **Task** — what to do (ordered, specific)
4. **Rules** — constraints (DO/DO NOT)
5. **Output format** — exact delimiters, exact structure
6. **Validation checklist** — self-check before outputting
7. **Friction report** — MANDATORY, always last

---

## Delimiter Enforcement

All structured output MUST use `===TAG_START===` / `===TAG_END===` delimiters.

```
===RESEARCH_START===
...content...
===RESEARCH_END===

===META_OUTLINE_START===
...content...
===META_OUTLINE_END===
```

**Why:** Content outside delimiters is automatically discarded by the extraction pipeline. Never rely on prose position.

**Rules:**
- One tag pair per output type
- Tags must be on their own line, no surrounding whitespace
- Always tell Gemini: `> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.`

---

## Validation Checklists

End every output block with a checklist Gemini must complete before outputting:

```markdown
### Validation checklist (complete before outputting):

- [ ] All section names are Ukrainian
- [ ] Section names match plan structure
- [ ] Each section has `words` and `points`
- [ ] Sum of all `words` ≈ {WORD_TARGET}
- [ ] No section has fewer than 200 words
```

**Why:** Forces Gemini to self-review. Reduces malformed output significantly.

---

## Friction Reports

Every template must request a friction report as the final output block:

```
===FRICTION_START===
**Phase**: Phase X: Description
**Step**: {what you were doing, or "Full phase"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | SOURCE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {script/design issue, or "N/A"}
===FRICTION_END===
```

**Why:** Surfaces invisible failures. Gemini often silently truncates or skips — friction reports expose this.

---

## Boundary Rules (DO NOT)

Always include explicit DO NOT rules at the end. Gemini fills gaps with hallucinations. Close every gap:

```markdown
## Boundaries

- Do NOT write lesson content — only research notes and meta outline
- Do NOT generate activities or vocabulary
- Do NOT use Russian-language sources
- Do NOT fabricate quotes or dates — if unsure, mark as "[needs verification]"
- Do NOT reference persona names or voice instructions
- Do NOT request skills, delegate to Claude, or skip this phase
```

**Pattern:** `Do NOT [action] — [consequence or alternative]`

---

## Identity Line

Always open with a clear identity statement:

```markdown
> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **This is a combined Phase 0 + Phase 1. Your ONLY task: Research the topic AND produce the meta outline in one pass.**
```

Key elements:
- Name the phase explicitly
- State the ONE task (not a list of goals)
- Use bold for the task statement

---

## Placeholder Conventions

Templates use `{PLACEHOLDER_NAME}` for runtime injection via `placeholders.yaml`. Standard placeholders:

| Placeholder | Content |
|-------------|---------|
| `{PLAN_PATH}` | Path to module plan YAML |
| `{META_PATH}` | Path to meta YAML |
| `{RESEARCH_PATH}` | Path to research markdown |
| `{CONTENT_PATH}` | Path to lesson markdown |
| `{WORD_TARGET}` | Integer word count target |
| `{TOPIC_TITLE}` | Human-readable module title |
| `{TRACK}` | Track identifier (bio, hist, etc.) |

**Rule:** Never hardcode paths. Always use placeholders.

---

## Anti-Gaming Rules (for Review Phases)

Phase D (review + fix) must include explicit anti-gaming enforcement:

```markdown
- Review scores DO NOT affect pipeline pass/fail — only content gates do
- "Ensuring a high score" language → IMMEDIATE REJECTION
- You are a skeptic. Find real problems. That is your only purpose.
- NEVER rubber-stamp: no all-10s with no issues, no empty issues sections
```

**Why:** Without this, LLMs inflate self-review scores. The incentive must be removed architecturally AND stated explicitly. See `audit-standards.md` for the detection layer.

---

## Combining Phases (v3 Pattern)

When combining multiple phases into one call (Phase A = research + meta):

1. Use `## PART 1:` / `## PART 2:` headings
2. Each part has its own output delimiter block
3. Keep part boundaries explicit — Gemini must complete Part 1 before Part 2
4. State dependencies: "After completing research, rebuild the outline using your notes"

---

## Template Deployment

Templates live in `claude_extensions/phases/gemini/`. After editing:

```bash
npm run claude:deploy
```

This syncs to `.claude/`, `.agent/`, `.gemini/` — **never edit those directly**.

---

## Common Failures and Fixes

| Failure | Root Cause | Fix |
|---------|-----------|-----|
| Wrong output format | No delimiter enforcement stated | Add delimiter enforcement notice |
| Gemini echoes old meta | Not told "do NOT copy" | Add explicit "rebuild from plan, not meta" rule |
| Oversized sections | No section size constraint | Add 25% word_target cap per section |
| Skipped validation | Checklist too long | Keep checklists to 6 items max |
| Missing FRICTION block | Not marked MANDATORY | Bold + MANDATORY in heading |
| Hallucinated quotes | No verification rule | "If unsure, mark [needs verification]" |
