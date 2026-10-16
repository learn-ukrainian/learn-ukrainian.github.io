# Worktree cleanup

Reclaim dispatcher worktrees only through the documented common reaper in `agents_extensions/shared/rules/workflow.md`. This playbook does not delete simulators, and it does not run `git worktree remove --force` or `rm -rf`.

1. Identify the task id and whether GitHub shows the pull request merged.
2. Run the common reaper in its default dry-run. Read the receipt.
3. Apply only when the receipt says the tree is safe. A SKIPPED receipt is not a deletion. Record it and its owner.
4. Do not touch the primary checkout, another lane's live tree, or a worktree with unpushed work you have not inspected.

There is no second deletion path.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
