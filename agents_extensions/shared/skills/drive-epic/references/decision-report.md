# Decision report template

Use it when the CTO publishes a proposal that needs designated or panel approval (as a
published page), and when a driver writes the brief for a new multi-PR outcome. Operator
template, C-2834. Keep each section to what changes the reader's decision; every claim cites
a command, file:line, run ID, SHA or tracker item, or says NOT CHECKED with its command.

## How it was made

Who drafted independently (model, family, harness), what each draft proposed, and how the
panel compared them. Name the drafts that lost and why.

## What it is and how it composes

The outcome in one paragraph, then the parts and how they fit the existing skills, rules,
tools and data. Name the owner of each part and the paths it touches.

## What keeps it safe

Pre-mortem: assume it failed and list why. Each credible cause becomes a check, a stop
condition or a sequencing change; name which.

## One source per procedure

Each procedure it defines lives in exactly one file. List the files it supersedes and the
pointers that replace their copies, so no stale duplicate survives.

## Rollout, timing and proof of use

The order of PRs, what lands first and why, the deploy step, and the proof that agents use
it (an attributed fetch, a run, a receipt), not only that it merged.

## Panel decisions

Each decision with who approved it. Designated approval is Opus 5.5 and Sol 6.1, the
non-author completing an advisor's proposal (operator-expectations.md item 12); panel voices
such as Muse advise and never replace it, and the author's family never approves its own
proposal. A disagreement goes to the operator. The operator is informed; approved work does
not wait on the operator. Operator-only items (core.md P6) wait for the operator while
independent work continues; list each as a residual with a workaround and the command output
that shows it is operator-only.

## Council: optional independent panel

Use it for a consequential design decision, when the operator asks for a second opinion
("council"), or for a named unresolved risk on a critical PR. Not for routine PRs.

- **Members:** live eligible routes only: Opus via Claude, Sol via Codex, Grok via Cursor
  (`model-assignment.md`). Muse may add advice but never replaces designated approval
  (operator-expectations.md item 12). AGY read-only dispatch runs inside the dispatcher's
  bubblewrap boundary (C-3027) and is refused only on a host that cannot start it. Grok is
  out of Ukrainian-content questions. An unavailable member is reported, never substituted,
  and the panel is then not called complete.
- **Read-only** comes from the harness (`dispatch.py --mode read-only`), not from prompt wording.
- **Freeze before dispatch:** the question, context, roles and stop condition. Panel rounds
  count against the same `review-loop` budget as any review
  ([policy](../../review-loop/references/policy.md)); never "until all members are satisfied".
- **Findings and score:** every panelist returns written findings plus `SCORE n/10` with a
  one-line rationale, against this rubric: 10 = no findings; 7-9 = only P2/P3; 4-6 = an open
  P1; 1-3 = a P0 or the wrong approach. A score never gates a merge: the verdict and the
  findings do.
- **Output:** evidence, dissent, scores, dispositions and owners go in this report and the
  durable task record. For a PR panel, record each round in a rounds table in the PR body
  (round, member, verdict, score, key finding).
- **On a PR** the panel shares the `review-loop` budget and ledger; `review-loop` keeps the
  single exact-head review of record, so the panel adds no second review path. Designated
  approval and `full-send` are unchanged.
  Before a panel round, bring the head up to date as `review-loop` step 0 says.

Learned from tstack's `council` skill (MIT, Theo Browne); the text is our own.

## Sources

Every source cited above, with its link or path.
