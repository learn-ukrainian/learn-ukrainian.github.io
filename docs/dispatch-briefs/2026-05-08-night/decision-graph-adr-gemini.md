# Dispatch brief: Draft "Decision Graph view" ADR (kubedojo Action C)

> **Tracking doc:** `docs/session-state/2026-05-07-kubedojo-paradigm-followups.md` Action C
> **Output:** new file `docs/decisions/pending/2026-05-09-decision-graph-view.md` (PROPOSED status, awaiting user signoff)
> **Agent:** Gemini (substantial drafting + design rationale)
> **Worktree:** mandatory

## Worktree instructions (mandatory)

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent gemini --mode danger --worktree --base origin/main \
    --task-id gemini-decision-graph-adr \
    --prompt-file docs/dispatch-briefs/2026-05-08-night/decision-graph-adr-gemini.md
```

Lands in `.worktrees/dispatch/gemini/gemini-decision-graph-adr`.

## Context

The kubedojo team (sister project) compared their dashboard to ours and pitched inverting `channels.html` from chat-primary to **Decision Graph**-primary, with chat as a toggle. They also offered to upstream their D3 (Decision Graph) PR after they implement it in their own repo.

3-way agent review (Codex + Gemini, 2026-05-07) converged on a **modified version**:

- **Decision Graph as a TOGGLE** that auto-engages when a thread has ≥2 distinct `agent_family` responses with `[AGREE]`/`[OPTION]`/`[OBJECT]`/`[DEFER]` markers. Chat stays primary.
- **Outline-first matrix layout** (rows=rounds, cols=agent_family, cell=marker + first-line summary, click→side drawer with full body) — because round bodies average 2367 chars, max 8349 chars; body-first grid would be unreadable.
- **Separate ADR**, not Strand-6 fold into the existing pending Multi-UI ADR. Codex's threshold rule applies (changes primary IA + marker semantics).

Codex's verifiable data (from `channel_messages` snapshot 2026-05-07):

| Channel | Marker threads | Total threads | % |
|---|---:|---:|---:|
| `architecture` | 32 | 39 | 82% |
| `pipeline` | 2 | 11 | 18% |
| `reviews` | 19 | 83 | 23% |

This data justifies the toggle (NOT inversion) — for ~75-80% of channel traffic, Decision Graph view would be wrong.

## What to write

A new ADR file at `docs/decisions/pending/2026-05-09-decision-graph-view.md` answering Q1-Q6 with explicit rationale. Status: **PROPOSED**. The user will review and either flip to ACCEPTED or send REVISE.

## Required ADR structure (match conventions)

Read `docs/decisions/pending/README.md` and look at `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md` for style. Required sections:

- Frontmatter (status: PROPOSED, date, authors, supersedes, blocks/blocked-by)
- Context (the kubedojo pitch + our data + why this matters now)
- Decision (the toggle-not-inversion summary in 3-5 bullet points)
- Q1-Q6 with rationale per question (see below)
- Implementation notes (what changes, what doesn't)
- Cross-agent review (placeholder for Codex + Claude review markers, post-draft)
- Open questions (anything genuinely unresolved that user must decide)
- Supersedes/Refines relationships to other ADRs

## The 6 questions to answer

### Q1 — When does Decision Graph view auto-engage?

Three sub-questions:
- Marker-density threshold (e.g. ≥2 marker-tagged messages? ≥3? per thread or per round?)
- Participant-count threshold (≥2 agent families? ≥3?)
- Manual toggle override behavior (always available? only on threads that meet auto-criteria?)

**Recommended starting point** (refine if you have a better idea): auto-engage when thread has ≥2 messages from distinct `agent_family` with markers in `{[AGREE], [OPTION], [OBJECT], [DEFER]}`. Manual toggle always available regardless.

### Q2 — Layout

Confirm or refine Codex's "outline-first matrix":
- Rows = rounds (1..N)
- Columns = agent_family (claude / gemini / codex / ... + a "human" column for `from_agent='human'` posts)
- Cell content: marker chip + first-line summary (truncated to ~80 chars)
- Click cell → side drawer with full message body
- Empty cells (agent didn't respond in that round): visible empty state

Justify with the body-size data above.

### Q3 — Marker parsing semantics

- What counts as `[AGREE]`/`[OPTION]`/`[OBJECT]`/`[DEFER]`?
- Case-sensitive match? (Recommend case-insensitive for human postability)
- Position requirement: anywhere in body, end-of-body, or top-of-body?
- Multiple markers per message? (e.g. `[OPTION] [DEFER]` — recommend last-wins or all-counted)
- What about adjacent variants like `[AGREED]`, `[OBJECT - X]`, etc?

Read `docs/best-practices/agent-cooperation.md` "Multi-Agent Deliberation" section to ground this in our existing protocol.

### Q4 — Convergence detection

When is a thread "decided"? Options:
- All distinct agent_families `[AGREE]` in same round
- Stricter: all `[AGREE]` in latest round AND at least one round has had `[OPTION]`/`[OBJECT]` (i.e. real deliberation happened)
- Looser: any single `[AGREE]` after at least one `[OPTION]`

This matters for closing-out indicator + Decision Card auto-link suggestion.

### Q5 — Side drawer UX

- Single-message vs full-thread transcript? (Probably full-thread filtered to that agent_family for that round)
- Modal (interrupts page) vs pinnable rail (persists alongside graph)?
- Rendering: same markdown render as channels.html main view?
- Quote/reply/copy actions?

Decide and explain.

### Q6 — Decision provenance

- Does Decision Graph link out to ADR file when one exists?
- Use what relationship — issue references? Manual decision-id linking? Auto-detect from `[ACCEPTED]` markers?
- Hooks into D4 (decision-lineage backlink scanner, #1785) — once D4 lands, Decision Graph reads its lineage records to surface "this thread became ADR-NNN" badges.

This question pairs the ADR with #1785 implementation work.

## Numbered execution steps

1. `git worktree add` — handled by delegate runner via `--worktree --base origin/main`.
2. Read `docs/decisions/pending/README.md` for ADR conventions.
3. Read `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md` for style and structure precedent.
4. Read `docs/best-practices/agent-cooperation.md` "Multi-Agent Deliberation" section for marker semantics grounding.
5. Read `docs/session-state/2026-05-07-kubedojo-paradigm-followups.md` Action C in full (you have the summary above).
6. Draft the ADR at `docs/decisions/pending/2026-05-09-decision-graph-view.md`. Status: **PROPOSED**.
7. **Length target:** 800-1500 lines of markdown including code/data fences. Substantive but not bloated. Each Q gets ~100-200 lines.
8. **Cite data** for every design decision: marker-density numbers, body-size numbers, thread density. Don't make claims you can't ground.
9. **Identify open questions** — anything you genuinely couldn't decide alone — in a final "Open questions for user" section. The user will resolve those before flipping to ACCEPTED.
10. Update `docs/decisions/INDEX.md` if the project's convention requires a new entry there.
11. Commit: `docs(adr): draft decision-graph-view ADR (PROPOSED, kubedojo Action C)`
12. `git push -u origin gemini-decision-graph-adr`
13. `gh pr create` with title + body summary + link to the kubedojo follow-ups doc + "PROPOSED — awaiting user signoff to ACCEPTED".
14. **Do NOT auto-merge.** PR stays open for user review.

## Out of scope

- No implementation code — this is a design document.
- No `channels.html` UI changes.
- No ADR-008 or Multi-UI ADR modifications (those are separately tracked).
- Don't propose a backend schema change unless you genuinely cannot answer a Q without one (in which case, flag it in Open questions).

## Constraint reminders

- Status must stay **PROPOSED**. Only the user can flip it.
- This is a **separate ADR**, not a fold into the pending Multi-UI ADR (Codex's threshold rule applied — see kubedojo doc Action C).
- Decision Graph is paradigm-correct as a **TOGGLE**, not as a primary inversion. Don't drift back to inversion-primary even if a Q seems to invite it.
