# Pause safely

1. Finish the current atomic step or back it out. Start nothing new.
2. Do not open a pull request or push merely to pause.
3. If the brief tells you to commit, make one commit that says the work is incomplete and whether the tree is broken. Otherwise leave the diff uncommitted and say so.
4. Write the handoff where the seat's handoff rules require: intent, what is verified, the next step, and the key paths. No secrets.
5. The complementary resume path is [session pickup](session-pickup.md).

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
