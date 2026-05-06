# Codex dispatch brief — Bakeoff blocker: `{X}` literal in `linear-write.md`

> **Issue:** #1705 (already filed). Reference it in the commit and PR.
> **Branch base:** `origin/main`
> **Worktree:** `.worktrees/dispatch/codex/<issue>-prompt-template-render-guard/`
> **Branch name:** `codex/<issue>-prompt-template-render-guard`
> **Mode:** danger, --hard-timeout 2700 (45 min — mechanical work, no LLM dispatch)
> **Effort:** medium

## Goal

Unblock the bakeoff. The runtime guard
`scripts/build/prompt_builder.py:render_prompt` raises on any
`{TOKEN}`-shaped string in a phase template that isn't registered in
`PLACEHOLDERS` or `DOWNSTREAM_TOKENS`. Today
`scripts/build/phases/linear-write.md:34` contains the literal example
phrase

```
"I will produce ~{X}% Ukrainian and ~{100-X}% English in module.md."
```

`{X}` matches `TOKEN_RE = r"\{([A-Z][A-Z0-9_]*)\}"` and is not
registered, so every V7 writer phase invocation crashes with:

```
v7_build failed in phase writer: Unknown placeholder-shaped token
{X} in scripts/build/phases/linear-write.md.
```

(`{100-X}` does NOT match `TOKEN_RE` — leading digit fails the regex
— so only `{X}` triggers. But both should be addressed when fixing
the prose.)

## Three things to ship

### 1. Fix the prose (root cause)

Edit `scripts/build/phases/linear-write.md:34`. The intent is to show
the writer an internal-state phrase to instantiate with the actual
immersion percentage. The braces were aspirational ("fill in X here")
but read as template placeholders by the validator. Rewrite without
braces. Example replacement:

```
"I will produce ~X% Ukrainian and ~(100-X)% English in module.md."
```

Or use backticks/angle brackets — your call as long as no
`{TOKEN}` literal remains. Preserve the surrounding paragraph
meaning.

### 2. Hunt siblings

Grep every phase template under `scripts/build/phases/` for
`{[A-Z][A-Z0-9_]*}` literals that are NOT in
`prompt_builder.PLACEHOLDERS` and NOT in
`prompt_builder.DOWNSTREAM_TOKENS`. The set of registered names is in
`scripts/build/prompt_builder.py` (lines 12-83 today). Check both
`linear-write.md` and `linear-review-dim.md` and any other `.md` in
`scripts/build/phases/`. Fix every offender the same way (escape or
reword). If you find any, list each in the PR body so a reviewer can
spot-check.

### 3. Add CI prevention

Pure-runtime regex never caught this. Add a new test
(`tests/test_prompt_template_render.py`) that:

- Globs every `.md` under `scripts/build/phases/`
- Calls `prompt_builder.render_prompt(template_path)` on each
- Asserts no `RuntimeError` is raised
- Runs under the existing pytest suite (so it's part of CI's
  `Test (pytest)` check)

This is the structural invariant we want: every phase template is
renderable from a clean checkout, no per-template runtime crashes.

If `render_prompt` requires `NORTH_STAR`/`LESSON_CONTRACT` source
files to exist (it does — see lines 102-104), the test runs in the
real repo so those exist. No fixtures needed.

If a template legitimately needs a new downstream token, the test
will fail and the fix is to register the token in `DOWNSTREAM_TOKENS`
in the same PR. Don't suppress the test or skip templates.

## Issue body (file the issue first; reference number in PR title)

```markdown
## Symptom

`v7_build.py --writer claude-tools a1 my-morning` (and same for any
other writer) fails on the writer phase with:

\`\`\`
Unknown placeholder-shaped token {X} in scripts/build/phases/linear-write.md.
If this is a new Phase-0 placeholder, register it in PLACEHOLDERS.
If it's a downstream .format() variable, register it in DOWNSTREAM_TOKENS.
If it's a literal brace string, escape it.
\`\`\`

## Root cause

`scripts/build/phases/linear-write.md:34` contains the literal example
phrase `"I will produce ~{X}% Ukrainian and ~{100-X}% English"`. The
braces were intended as "fill in your value" placeholders for the
writer's internal monologue. The validator at
`scripts/build/prompt_builder.py:88-100` matches `{X}` against
`TOKEN_RE` and demands it be registered.

## Why CI didn't catch it

- `Lint Prompts` in CI checks markdown formatting, not template
  render-ability.
- No existing test calls `render_prompt` on every phase template.
- The validator only fires at runtime (during a real V7 build), and
  no V7 build had been attempted between the time `{X}` was added and
  the bakeoff today.

## Fix

1. Reword `linear-write.md:34` to remove `{X}` and `{100-X}` literals.
2. Sibling hunt: grep all `scripts/build/phases/*.md` for
   unregistered `{TOKEN}` literals; fix any others.
3. Prevention: add `tests/test_prompt_template_render.py` that calls
   `render_prompt` on every phase template, so this category of
   regression fails CI.

## Acceptance

- [ ] `v7_build.py a1 my-morning --writer claude-tools --dry-run`
      succeeds (already true — dry-run skips writer phase, but kept
      as smoke test)
- [ ] `v7_build.py a1 my-morning --writer claude-tools` reaches the
      writer phase without `RuntimeError` (won't run the writer in CI
      due to LLM cost, but the local test of `render_prompt` catches
      the failure mode)
- [ ] New test green: `pytest tests/test_prompt_template_render.py -v`
- [ ] CI green on the PR
- [ ] Reviewed by Gemini (cross-family per
      `docs/best-practices/agent-bridge.md`); `Reviewed-By` trailer
      on the commit message
```

## Worktree setup

`delegate.py dispatch --worktree ...` auto-creates the worktree from
`origin/main`. First action: verify base.

```bash
git log --oneline HEAD..origin/main  # must be empty
```

## Numbered execution steps

1. Verify worktree base clean (`git log --oneline HEAD..origin/main` empty). Issue #1705 is already filed; do not re-file.
2. Edit `scripts/build/phases/linear-write.md:34` per Section 1.
3. Run sibling-hunt grep: `grep -rEn '\{[A-Z][A-Z0-9_]*\}' scripts/build/phases/`. Cross-reference each match against `prompt_builder.PLACEHOLDERS` keys + `prompt_builder.DOWNSTREAM_TOKENS` set. Fix every unregistered match. List findings in the PR body.
4. Add `tests/test_prompt_template_render.py` per Section 3. Run `.venv/bin/pytest tests/test_prompt_template_render.py -v` — must pass before commit.
5. Smoke test the fix: `.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer claude-tools --dry-run` (still passes, sanity check).
6. `.venv/bin/ruff check scripts/build/ tests/`
7. Get review BEFORE commit — see "Review protocol" below.
8. Apply feedback or argue back in writing.
9. After review CLEAN: commit with `Reviewed-By: gemini-3.1-pro-preview (issue-1705-review)` trailer.
10. `git push -u origin codex/1705-prompt-template-render-guard`
11. `gh pr create --title "fix(prompts): escape literal {X} in linear-write.md + add render-guard test (#1705)"` with body listing the sibling-hunt findings + the new test rationale. DO NOT enable auto-merge.

## Review protocol (mandatory)

Before commit, get review from Gemini (cross-family — author is Codex,
reviewer is Gemini per project policy):

```bash
git add scripts/build/phases/linear-write.md tests/test_prompt_template_render.py
git diff --cached > /tmp/issue-1705-diff.txt
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
    "Adversarial review for issue #1705. Read /tmp/issue-1705-diff.txt. Focus: (1) does the rewording at linear-write.md:34 preserve the writer-prompt's pedagogical intent? (2) is the new render-guard test sufficient — does it catch every offender today? (3) any sibling templates I missed? Cite line numbers." \
    --task-id issue-1705-review --model gemini-3.1-pro-preview
```

Apply feedback. If you disagree with a finding, write a counter in the
PR body — don't silently ignore.

## Constraints

- **No edits on main**, no auto-merge.
- **No agent CLIs invoked** — this is mechanical text-replacement +
  pytest. Don't dispatch sub-agents.
- **No suppress/skip on the new test.** If a phase template
  legitimately needs a new placeholder, register it in `PLACEHOLDERS`
  or `DOWNSTREAM_TOKENS` in the same PR.
- **Do not modify** `prompt_builder.py` regex or the validator
  semantics. Don't relax the validator. The validator is correct;
  the templates were sloppy.

## Out of scope (do NOT include in this PR)

- Any change to V6 (V6 is legacy)
- Any change to `linear-write.md` content beyond the brace literals
  (don't restructure the prompt)
- Any change to the V7 prompts under PR #1696 (those are still in
  flight; rebase after this PR merges)
