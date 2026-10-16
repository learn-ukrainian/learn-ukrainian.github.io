# Authoring a skill

1. Edit the canonical skill under `agents_extensions/shared/skills/<name>/SKILL.md`. Do not hand-edit a deployed copy.
2. Frontmatter needs `name` and `description`. `name` matches the directory. Link every reference the skill cites, and make sure the file exists.
3. Keep one home per fact. Point at `drive-epic`, `local-code-review`, and `workflow.md` instead of restating them.
4. Run `scripts/lint/lint_agent_skills.py` with the project interpreter. The driver deploys with `npm run agents:deploy` after review and merge. This playbook does not deploy.
5. Open a pull request only when the brief allows it.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
