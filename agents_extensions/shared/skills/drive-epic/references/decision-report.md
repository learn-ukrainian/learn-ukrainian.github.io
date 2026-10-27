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

## Sources

Every source cited above, with its link or path.
