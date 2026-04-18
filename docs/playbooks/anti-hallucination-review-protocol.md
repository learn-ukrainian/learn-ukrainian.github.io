# Playbook — Universal anti-hallucination review protocol + verifier

> Portable implementation prompt. Drop into any agent (Claude / Codex / Gemini)
> in any project. The agent reads this file and builds the system described.
>
> **First-touched in:** learn-ukrainian #1331 (2026-04-19) — also applies in
> kubedojo. If the agent is invoked in a project where it has already been
> built, it should detect that and decline rather than rebuild.

## When to use this

Use when:
- The project routinely uses LLM cross-agent code review (Codex reviews Claude's code, Gemini reviews Codex's, etc.)
- A reviewer has hallucinated findings — claimed code is missing when it
  exists, invented file:line references, or misquoted the diff
- The cost of those hallucinations is significant (rebuttal, re-verification,
  wasted reviewer rounds)

Do NOT use when:
- The project has only one agent doing reviews and no record of hallucinations
- The reviewer dispatch layer doesn't exist yet (the protocol needs a seam to
  hook into) — the agent should respond `Blocked — no reviewer dispatcher
  exists to wrap` and stop

## The prompt to give the agent

Copy from `## DROP-IN PROMPT` below to the end. Adjust the four
project-specific items in the `## Pre-flight: project-specific adaptations`
section before dispatching, then hand the rest verbatim to the agent.

---

## Pre-flight: project-specific adaptations

Before dispatching, fill in these four items for the target project:

1. **Reviewer dispatch seam** — where prompts are assembled before being sent
   to an agent. (e.g. `scripts/ai_agent_bridge/_prompts.py`,
   `bridge/dispatcher.py`, etc.)
2. **Channel/multi-agent post seam** (if any) — where multi-round agent
   conversations get their pinned context.
3. **Branch/PR model** — does the project use PRs (verifier uses `--pr N` and
   `gh pr view`), or does it commit on `main` and track work via GH issues
   (verifier uses `--issue N` and `gh issue view`)?
4. **Lint + test commands** — `.venv/bin/ruff check` and `pytest`, or
   `npm run lint` and `npm test`, etc.

If any of these don't exist yet in the project, the agent should respond
`Blocked — <which item is missing>` rather than try to invent the seam.

---

## DROP-IN PROMPT

# Build: universal anti-hallucination review protocol + verifier

## Why
LLM code reviewers hallucinate — they claim code is missing when it exists in
lines outside the diff, or they invent file:line references. Each hallucination
costs ~15 min of rebuttal/re-verification. This tool makes the review protocol
reviewer-agnostic (any agent follows the same rules and produces the same output
schema), and adds a passive post-hoc verifier so any orchestrator — not just a
specific agent — can run the loop autonomously.

## Deliverables (one PR or one commit, depending on project gitflow)

### 1. `docs/review-protocol.md` — canonical source

Single source of truth for the review contract. Must contain:

- **Five hallucination guards:**
  1. **DIFF vs FILE distinction** — lines not in the diff still exist in the
     file. A "missing X" claim must prove absence in the FILE, not the DIFF.
  2. **Mandatory FINDING format** (see schema below).
  3. **"Missing" claims require proof of absence** — verbatim grep miss or
     quoted file line, not "I don't see it in the diff."
  4. **No invented line numbers** — every `file:line` must resolve to a real
     line on the branch at review time.
  5. **Self-check before submitting** — "could the code I think is missing
     actually exist at a line I haven't read?"

- **Mandatory per-finding schema:**

  ```
  FINDING:
  FILE:LINE: <path>:<n>
  CURRENT CODE (verbatim from branch):
  ```
  <copy-paste from file>
  ```
  WHY WRONG:
  <one paragraph>
  FIX:
  <patch or instruction>
  SEVERITY: {blocker | major | minor | nit}
  ```

  Findings without all fields are DISCARDED by the verifier.

- **"Universal review loop" section** — step-by-step of how any orchestrator
  (human or agent) dispatches a reviewer with `--review`, pipes output through
  the verifier, and decides next step from the verifier's structured output.

### 2. `--review` flag on every reviewer-dispatch CLI path — parity across all agents

Today only some agent-specific dispatchers inject review context. Bring all
paths to parity. The single seam is the project's prompt-assembly layer
(identified in pre-flight). All `ask-*` / `dispatch-*` / channel-post commands
get a `--review` flag.

Wiring requirements:

- When `--review` is set, the prompt builder prepends the contents of
  `docs/review-protocol.md` verbatim (read at call time — no duplication, no
  caching of stale text).
- The protocol body sits BEFORE any per-channel / per-project context, so it
  cannot be silently overridden.
- One small helper (e.g. `def review_protocol_prefix() -> str`) loads the doc
  and is called from each builder. **Do NOT copy the protocol text into
  multiple files.**

### 3. `scripts/verify_review.py` — standalone, reviewer-agnostic

CLI:
```
verify_review.py [--pr N | --issue N | --from-stdin] [--branch REF] [--post-comment]
```

Use `--pr` if the project uses pull requests, `--issue` if it tracks work on
issues with main-branch commits.

Flow:

1. Read review text from stdin OR fetch the latest PR/issue comment via `gh`.
2. Parse every FINDING block with a stable regex: header `^FINDING:`, body
   continues until next `^FINDING:` or EOF.
3. For each finding, read `<path>` from the branch (`git show <branch>:<path>`
   or filesystem if `--branch` omitted). Normalize whitespace (collapse runs of
   spaces, strip per-line edge whitespace, strip backticks/triple-backticks).
   Check whether the normalized `CURRENT CODE` block is a contiguous substring
   of the normalized file.
4. Emit per-finding outcome to stdout as JSON Lines:
   `{ "finding_id": N, "file": ..., "line": ..., "outcome": "verified" |
   "line_mismatch" | "quote_missing", "evidence": ... }`.
5. If `--post-comment`, append a structured summary as a PR/issue comment via
   `gh`.
6. Exit 0 when no `quote_missing`; exit 1 otherwise. `line_mismatch` alone
   does NOT fail the run (whitespace normalization is fuzzy on line numbers;
   presence is what matters).

**Constraints (non-negotiable):**

- Passive / warn-only. Never auto-block merge. Never auto-re-dispatch in a
  loop.
- Deterministic text normalization only — **no fuzzy matching, no AST, no
  edit distance.** Those would silently turn bad claims into false passes.
- `gh` and `git` calls go through ONE shell-out helper that's stub-friendly
  for tests.

### 4. Tests for the verifier

Cases:

- Finding with quote at claimed line → `verified`
- Finding with quote at different line → `line_mismatch`
- Finding with quote absent from file → `quote_missing`
- Mixed review with all three outcomes → single run, correct per-finding
  emission
- Malformed FINDING (missing fields) → discarded with reason
- No external network: stub the `gh`/`git` shell-out helper.

## LOC budget (hard cap, calibrated for ~mid-size projects)

≤ 200 LOC of net-new code total (the protocol doc itself is not counted):

- Verifier: ≤ 80 LOC
- Builder helper + per-builder `--review` threading: ≤ 30 LOC each
- argparse wiring per CLI command: ≤ 20 LOC total

If a section pushes over budget, the design is wrong — stop and report
rather than expanding. Larger infra: scale the budget proportionally but
keep the verifier under ~150 LOC. If the verifier balloons, you've added
fuzzy matching by accident.

## Out of scope (do NOT do)

- Auto-retry loops on `quote_missing`. (Future issue, gated on data from
  manual use.)
- AST/semantic verification. Whitespace-normalized substring match only.
- Modifying any existing review documentation beyond a one-line pointer to
  the new protocol doc.
- Adding new MCP tools, API endpoints, or services.
- Promoting any existing review-related script into the protocol — the
  protocol is the doc; existing reviewers continue to work, they just gain
  `--review` as a switch.
- Changing existing channel-context mechanisms. The `--review` prefix sits
  ABOVE channel context; it doesn't replace it.

## Workflow

Use the project's gitflow:
- PR-based projects: branch + worktree + tests + lint + commit + push + open PR
- Main-commit projects: tests + lint + one commit on main referencing the
  tracking issue

Run the project's lint + test commands before committing.

## Response format (strict)

End your final commit message / PR description / issue comment with EXACTLY
ONE of:

- `Done — commit <sha>, tests pass, LOC <n>/200.`
- `PR <url> opened, tests pass, LOC <n>/200.`
- `Blocked — <one-line specific reason>`

No "what I would do" meta-replies. No multi-paragraph status updates.

---

## Notes for the orchestrator (you, dispatching this)

- If the project isn't Python, adjust file extensions and lint/test commands
  before handing off.
- The ≤200 LOC cap is calibrated for this kind of project. For larger infra,
  scale proportionally — but the verifier should never need fuzzy matching;
  if it does, you've gone off-spec.
- If you see `Blocked — no reviewer dispatcher exists to wrap`, do NOT push
  the agent to invent one. That's a separate, larger piece of work.
- Track instances of this playbook being used in: project's GH issues with a
  consistent label (e.g. `meta:review-protocol`) so you can see the rollout
  across repos.
