# Opening a PR

Prepare the update. Open the pull request only when the brief assigns that to this seat. A worker does not merge it.

1. Commits cite the issue. Each commit has the `X-Agent` trailer. One outcome per pull request.
2. The title names the user-visible change. The body leads with the outcome, then the checks and their results, then the residual and its owner.
3. One primary number in a performance body. Put the runs in the evidence (`../../benchmark-checklist/SKILL.md`).
4. Exact-head cross-family approval comes before the pull request is opened, including a draft, per `workflow.md`.
5. Do not add auto-merge labels. The driver enqueues after same-head green CI.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
