# Prompt Engineering Best Practices

> **Scope:** How to write Gemini phase templates (`claude_extensions/phases/gemini/`).
> The phase-template rules are that Gemini contract.
> Added guidance covers [consequential prose reviews](#consequential-prose-reviews), UI and visual briefs, and [cross-model prompt practice](#cross-model-prompt-practice).
> Each added note applies to the model or provider it names, leaves the template contract in force, and does not establish the health of this repo's native CLIs.
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

### Consequential prose reviews

The checklist above is the Gemini output self-check. It compares one phase output with its own plan structure and word target.

When the artifact is consequential prose, also compare dates, quantities, names, and obligations across the plan, the brief, and the final report. For each contradiction, quote the conflicting text and give the source location in each document. Keep this comparison off the phase checklist above so that checklist stays short enough to run.

Source: [Getting the most out of Opus 5.5](https://claude.dev/blog/getting-the-most-out-of-opus-5-5/) (long-document check: numbers, dates, and names, each with its location).

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

Visual briefs and UI journeys are specified in [Visual references](#visual-references) and [UI journey briefs](#ui-journey-briefs). Those sections leave the DO / DO NOT rules above unchanged.

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
| --- | --- |
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
| --- | --- | --- |
| Wrong output format | No delimiter enforcement stated | Add delimiter enforcement notice |
| Gemini echoes old meta | Not told "do NOT copy" | Add explicit "rebuild from plan, not meta" rule |
| Oversized sections | No section size constraint | Add 25% word_target cap per section |
| Skipped validation | Checklist too long | Keep checklists to 6 items max |
| Missing FRICTION block | Not marked MANDATORY | Bold + MANDATORY in heading |
| Hallucinated quotes | No verification rule | "If unsure, mark [needs verification]" |

Prompt changes, evaluation calibration, Claude request compatibility, and observable proof: [Cross-model prompt practice](#cross-model-prompt-practice).

---

## Cross-model prompt practice

Use this section when changing a prompt, an evaluation, a Claude model request, or a UI brief. The Gemini phase-template contract above stays in force, including delimiter enforcement, friction reports, anti-gaming rules, and curriculum constraints. A controlled replay can retire one unearned prompt ritual. It is not a way to drop a curriculum or source-verification duty. Nothing here is a paid-evaluation order. A Claude API check is a compatibility check for that request shape.

### Causal instruction replay

Before changing a standing instruction, and before any broad removal of mandatory procedures, replay the same task, the same repository snapshot, and the same model with one instruction changed. Compare outcome quality, tool calls, tokens, runtime, and cost. Keep every other input fixed so the delta belongs to that instruction.

Source: [Maintaining software with the GPT-6 family](https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family) (replay one session prompt with a single AGENTS.md instruction unchanged, then removed or fixed; compare task quality, agent behavior, tool calls, tokens, runtime, and cost).

### Evaluation calibration

Independent held-out cases stay unseen by the edit under test. A held-out split alone does not show that the grader is stable, that the tasks represent the work, or that a gain exceeds noise. Before optimizing a prompt against an evaluation, check all of the following:

- Repeated grading of identical output. Grade the same output more than once and measure that noise against the improvement of interest. When the noise is larger than that improvement, the article's hillclimb check says so and suggests more repetitions or cases.
- Representative difficult cases. Sample the setting you actually care about, and include cases a person can say are hard before seeing which ones today's model misses. A set built only from one model's failures measures that model.
- Achievable headroom. The strongest configuration still has room to move. The same article's build-eval diagnostic warns when a baseline is already about 95%. A case that fails on every repeat is a tell to investigate task validity, model capability, grader correctness, and execution failure, including a timeout, an API error, a cut-off answer, or a harness error.
- Clean trial state. Start each trial clean. A leftover file or git history can hand the agent the answer.
- Uncertainty around measured improvements. State the noise around the score. Adopt a change only when the gain is larger than that uncertainty.

Source: [Automating eval design and hillclimbing](https://claude.dev/blog/automating-eval-design-and-hillclimbing/).

### Claude migration compatibility

When a Claude model id changes, check the request and response against the target model. These are compatibility checks for that API shape. They do not establish that this repo's native CLIs are broken.

- **Thinking settings.** Match the target model's accepted thinking field. On Sonnet 5.5, adaptive thinking is the default, `thinking: {"type": "disabled"}` returns 400, and upfront thinking is turned off with `thinking: {"type": "between_tools"}` at `high` effort or below. `xhigh` and `max` return 400 with `between_tools`. So do `display`, `budget_tokens`, and `block_binding`. Effort cannot change mid-conversation under `between_tools`; vary it per turn with adaptive thinking. Sonnet 5.5 effort is recalibrated against Sonnet 5, so the old level means a different amount of thinking. On Opus 5.5, thinking stays on: `disabled` and manual `enabled` return 400, so omit the `thinking` field and set depth with effort. On Haiku 5.5, manual `budget_tokens` thinking returns 400 and adaptive thinking is the default.
- **Forced tool choice.** `tool_choice` types `any` and `tool` return 400 on Sonnet 5.5, Opus 5.5, and Fable 5.1. Send `auto`. On Sonnet 5.5, mark the tool `strict: true`, set `additionalProperties: false` on every object, and say in the prompt when to call it. Opus 5.5 pairs `auto` with strict tool use. Fable 5.1 keeps `auto` and `none`, and uses strict tool use or structured outputs when the input must match a schema.
- **Typed response blocks.** Read each content block by its `type`. Sonnet 5.5 thinks by default, so a response can begin with a `thinking` block and `content[0].text` breaks. A note between tool calls that runs longer than a sentence or two comes back as a progress-update `thinking` block, empty at the default `display`. With adaptive thinking, set `thinking.display` to `"summarized"`, or to `"updates"` with the `thinking-display-updates-2026-08-18` beta header. With `between_tools`, that text comes back without `display`. On Haiku 5.5 a response can also begin with a `thinking` block, and its text is omitted unless `thinking.display` is `"summarized"`.
- **Preserved-thinking validity.** Replay a thinking block only where that model, conversation, and account still accept it. Sonnet 5.5 blocks are tied to the model and the conversation. Sonnet 5.5 reads Sonnet 5 blocks, and the Sonnet 5.5 guide says no other model reads Sonnet 5.5 blocks. The release notes add that a Sonnet 5.5 block is kept for the account that produced it, or a linked account. Another account drops the block and the request still succeeds. On Haiku 5.5, sending thinking blocks back after a change to `system`, `tools`, or earlier turns can return 400. On Fable 5.1, a block is preserved for that model or a newer one. For accounts created on or after 31 August 2026, replaying one after `system`, `tools`, or an earlier message changed returns 400. When a request compacts the conversation, thinking in the turns kept verbatim can stay valid on models that preserve thinking.
- **Advisor pairing.** A Sonnet 5.5 executor rejects Opus 4.8, Opus 4.7, and Sonnet 5 as advisors. Accepted advisors in that guide include Opus 5.5, Opus 5, and Sonnet 5.5. Advice comes back encrypted as an `advisor_redacted_result` block, so the caller cannot read the advice text.
- **Provider-specific tool versions.** Computer-use ids differ by provider. On the Claude API and Google Cloud, Sonnet 5.5 and Opus 5.5 accept `computer_toolset_20260801` and reject `computer_20251124`. Amazon Bedrock still accepts `computer_20251124` for those models. On Sonnet 5.5, the `fine-grained-tool-streaming-2025-05-14` beta header beside a toolset entry also returns 400. Set `eager_input_streaming: true` on the tool instead. Haiku 5.5 rejects `computer_20250124`. Use `computer_toolset_20260801` on the Claude API and Google Cloud, or `computer_20251124` on Amazon Bedrock.

Sources: [Building with Claude Sonnet 5.5](https://claude.dev/blog/building-with-claude-sonnet-5-5/) and the [Claude release notes](https://platform.claude.com/docs/en/release-notes/overview) (Sonnet 5.5, Opus 5.5, Haiku 5.5, and Fable 5.1 entries).

### Prompt migration audit

Run a model-specific audit when the seated model changes. Keep a requirement that has demonstrated value, including the Gemini contract and any check a replay still earns. Test a proposed removal with the [causal instruction replay](#causal-instruction-replay) before dropping it from the standing prompt.

Look for these four leftovers:

- Obsolete thinking requests. Delete "think carefully", "think step by step", and similar lines for Opus 5.5, which already thinks before every reply. The task-cost article says Opus 5.5 thinks more per turn than Opus 5 at the same effort level, most of all at `xhigh` and `max`, so measure again before keeping an Opus 5 level. Also drop a thinking parameter the target model now rejects (see the compatibility list above).
- Internal-reasoning extraction. Remove requests to reproduce the model's internal reasoning in the reply. On Opus 5.5 that request can be declined. Ask for the decision in a few sentences instead.
- Duplicate verification rituals. The Opus 5.5 task-cost audit removed a mandatory six-step procedure, a scratchpad rule, and a verify-twice rule that made the model write more and repeat tool calls. That article treats the benchmark as one example, not a saving to expect. A second check that has already earned its place stays until a replay says otherwise.
- Contradictory instructions. Remove rules that disagree with each other, including skill descriptions that contradict or that fire far outside the workflow they actually cover.

On GPT-6 Astra, also revisit standing skills and `AGENTS.md`: a recipe that is now tighter than the task, a demand to read the whole repo before every edit, and a boundary copied from an older model that stops work you still want done. Astra-specific cleanup stays on Astra prompts. It is not a reason to strip another model's checks.

Sources: [Getting the most out of Opus 5.5](https://claude.dev/blog/getting-the-most-out-of-opus-5-5/), [What a task costs on Opus 5.5](https://claude.dev/blog/what-a-task-costs-on-opus-5-5/), and [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).

### UI journey briefs

A local UI proof still needs a journey, because a screenshot can pass while the interaction fails. Give the brief all of the following:

- A reference image for the intended look or the reported bug.
- A repeatable starting state, such as a named scene or fixture, so the next run begins at the same point.
- The real user action. Loading the finished state does not replace the control the person uses.
- The observable resulting state: what changed for the user, recorded where the product exposes it.
- A screenshot where the picture helps, attached to that state rather than standing in for the action.

Source: [Building games with Astra](https://developers.openai.com/blog/how-to-build-games-with-astra) (named scenes, real-control journey tests, state inspection, and screenshots that do not replace the journey).

### Visual references

Supply the actual visual reference: the chart, screenshot, slide, or concept image. Name the unwanted patterns in concrete terms. A general instruction to avoid a generic look mostly swaps one default style for another. Choose a resolution that keeps the details a later check needs, and downscale when those details survive. On Sonnet 5.5 the high-resolution image tier runs to 2576 pixels on the long edge, and that guide says a 2000×1500 image costs about 2.5 times as many tokens as on Sonnet 4.6, Sonnet 4.5, or Haiku 4.5. That cost note is Sonnet 5.5 image input.

Sources: [Getting the most out of Opus 5.5](https://claude.dev/blog/getting-the-most-out-of-opus-5-5/) (attach the image; name the styles to leave out) and [Building with Claude Sonnet 5.5](https://claude.dev/blog/building-with-claude-sonnet-5-5/) (image-input size and cost).

### Performance proxies

A semantic check still has to pass. A deterministic counter becomes a regression gate only after two further checks: the proxy and the user-visible metric ran on matched inputs (the same path and the same starting conditions), and the counter's movement correlates with that user metric. Until both are shown, the threshold stays a lab number.

The claude.ai performance case study discarded a benchmark that was flaky or that did not correlate with user latency. Each sidebar shift scored about 0.008, inside a 0.1 "good" threshold, while the rows still popped in after load, so that threshold was not the gate. The replacement test matched the recording: a populated sidebar whose data was held until after first paint, graded by named region.

Source: [How we made claude.ai faster](https://claude.dev/blog/how-we-made-claude-ai-faster/).
