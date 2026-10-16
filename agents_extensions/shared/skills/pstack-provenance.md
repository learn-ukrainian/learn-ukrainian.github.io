# Ported skill provenance

Issue #10874 vendors public pstack skill text at revision
`cdb3c41c9f2f6d41f050e3dc25e15e325493d499`
(default-branch head of `cursor/plugins`, read 2026-10-16).
The previous pin from #10040 Item G was
`ccb5507cec1546dc88135c1139c811e6c59115ba`.

Diff against the previous pin: 88 files changed, 6 added, 0 removed (170 files at the new pin).

## Added

- `pstack/docs/harness/claude-code.md`
- `pstack/plugin.json`
- `pstack/skills/in-your-own-words/SKILL.md`
- `pstack/skills/ketchup/SKILL.md`
- `pstack/skills/poteto-mode/scripts/check-plan.test.ts`
- `pstack/skills/sharpen/SKILL.md`

## Removed

- None.

## Already-ported skills

These three entrypoints were not rewritten.

- `correct`: upstream reworded one sentence so a test that still passes when behavior breaks should be fixed or deleted. That conflicts with this repository's rule against weakening or deleting tests. The existing skill already requires a failing-then-passing behavior check.
- `blast-radius`: no upstream diff.
- `benchmark-checklist`: editorial compression of the same seven questions. The existing skill already states them. The removed companion link is now the standalone `principle-explain-the-number` skill.
- `principle-prove-it-works`: no upstream diff. It was previously incorporated into the three entrypoints and is now also a standalone skill.

No hook files exist at this pin. Subagent definitions, installers, plugin manifests, and executable scripts are security-class below and are not enabled. Nothing was added to a marketplace, a plugin setting, or a settings hook.

## Disposition

Every file under `pstack/` at the pinned revision.

| Path | Disposition | Reason |
| --- | --- | --- |
| `pstack/.cursor-plugin/plugin.json` | security-class | Plugin manifest. Registers agents. Not added to any marketplace or settings file. |
| `pstack/.gitignore` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/LICENSE` | adopted | MIT notice recorded in this file. Not copied as a separate skill. |
| `pstack/README.md` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/agents/comment-sicko.md` | security-class | Subagent definition. Listed, not enabled. |
| `pstack/agents/poteto-agent.md` | security-class | Subagent definition. Listed, not enabled. |
| `pstack/assets/logo.png` | skipped | Binary brand asset. Not skill text. |
| `pstack/automations/benny/FOR_AGENTS.md` | skipped | Benny automation. model-assignment forbids vendoring Benny. |
| `pstack/automations/benny/README.md` | skipped | Benny automation. model-assignment forbids vendoring Benny. |
| `pstack/automations/benny/skills/reproduce-and-fix-issues/SKILL.md` | skipped | Benny automation. model-assignment forbids vendoring Benny. |
| `pstack/automations/benny/skills/reproduce-and-fix-issues/references/control-adapter.md` | skipped | Benny automation. model-assignment forbids vendoring Benny. |
| `pstack/automations/benny/skills/reproduce-and-fix-issues/references/feature-map.example.md` | skipped | Benny automation. model-assignment forbids vendoring Benny. |
| `pstack/automations/benny/skills/reproduce-and-fix-issues/references/verify-existing-fix.md` | skipped | Benny automation. model-assignment forbids vendoring Benny. |
| `pstack/automations/benny/skills/setup-benny/SKILL.md` | security-class | Installer for Benny. Model-assignment forbids vendoring Benny. Not enabled. |
| `pstack/automations/benny/skills/triage-issue-reports/SKILL.md` | skipped | Benny automation. model-assignment forbids vendoring Benny. |
| `pstack/automations/benny/skills/triage-issue-reports/references/routing.example.md` | skipped | Benny automation. model-assignment forbids vendoring Benny. |
| `pstack/automations/benny/templates/configuration.example.yaml` | skipped | Benny automation. model-assignment forbids vendoring Benny. |
| `pstack/automations/benny/templates/reproduce-automation-prompt.md` | skipped | Benny automation. model-assignment forbids vendoring Benny. |
| `pstack/automations/benny/templates/triage-automation-prompt.md` | skipped | Benny automation. model-assignment forbids vendoring Benny. |
| `pstack/docs/guide/01-setup.md` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/02-poteto-mode.md` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/03-understand.md` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/04-design.md` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/05-build-and-clean.md` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/06-verify-and-ship.md` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/07-overnight.md` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/08-principles.md` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/09-make-it-yours.md` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/10-recipes-and-pitfalls.md` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/README.md` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/images/design.jpg` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/images/overnight.jpg` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/images/recipes.jpg` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/images/router.jpg` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/images/understanding.jpg` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/guide/images/verification.jpg` | skipped | Product readme, ignore file, or onboarding guide. Not a skill or playbook. |
| `pstack/docs/harness/claude-code.md` | security-class | Harness installer notes that would generate and enable the plugin. Not vendored. |
| `pstack/plugin.json` | security-class | Plugin manifest. Registers agents. Not added to any marketplace or settings file. |
| `pstack/skills/architect/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/architect/references/design-red-flags.md` | adopted | Adapted reference. No host paths and no executable script. |
| `pstack/skills/architect/references/rationale-template.md` | adopted | Adapted reference. No host paths and no executable script. |
| `pstack/skills/architect/references/runner-prompt.md` | security-class | Subagent prompt payload. Method, where kept, is in the parent skill. Not enabled. |
| `pstack/skills/arena/SKILL.md` | skipped | N-implementation arena. model-assignment forbids vendoring it. |
| `pstack/skills/automate-me/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/benchmark-checklist/SKILL.md` | adopted | Already ported under #10040. Upstream delta is not material. See the note above. |
| `pstack/skills/blast-radius/SKILL.md` | adopted | Already ported under #10040. Upstream delta is not material. See the note above. |
| `pstack/skills/bro/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/correct/SKILL.md` | adopted | Already ported under #10040. Upstream delta is not material. See the note above. |
| `pstack/skills/create-verification-skill/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/create-verification-skill/references/feature-map-example/README.md` | skipped | Sample application. The feature-map shape is described in the skill. |
| `pstack/skills/create-verification-skill/references/feature-map-example/create-note.md` | skipped | Sample application. The feature-map shape is described in the skill. |
| `pstack/skills/create-verification-skill/references/feature-map-example/search.md` | skipped | Sample application. The feature-map shape is described in the skill. |
| `pstack/skills/figure-it-out/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/how/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/how/references/explainer-prompt.md` | security-class | Subagent prompt payload. Method, where kept, is in the parent skill. Not enabled. |
| `pstack/skills/how/references/explorer-prompt.md` | security-class | Subagent prompt payload. Method, where kept, is in the parent skill. Not enabled. |
| `pstack/skills/in-your-own-words/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/interrogate/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/interrogate/references/code-quality-review.md` | skipped | Checklist folded into interrogate/SKILL.md. Formal review stays local-code-review. |
| `pstack/skills/interrogate/references/lead-judgment.md` | security-class | Subagent prompt payload. Method, where kept, is in the parent skill. Not enabled. |
| `pstack/skills/interrogate/references/reviewer-prompt.md` | security-class | Subagent prompt payload. Method, where kept, is in the parent skill. Not enabled. |
| `pstack/skills/interrogate/references/rubric.md` | skipped | Checklist folded into interrogate/SKILL.md. |
| `pstack/skills/ketchup/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/maintain-verification-skill/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/make-bot-ui/SKILL.md` | skipped | Webhook sender-key handoff and tailnet hosting. Operator-only host access. Not vendored. |
| `pstack/skills/no-comments/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/poteto-help/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/poteto-help/references/prompting.md` | skipped | Upstream onboarding recipes. The index of our skills is poteto-help/SKILL.md. |
| `pstack/skills/poteto-help/references/recipes.md` | skipped | Upstream onboarding recipes. The index of our skills is poteto-help/SKILL.md. |
| `pstack/skills/poteto-mode/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/poteto-mode/playbooks/authoring-a-skill.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/autonomous-run.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/autopilot-full.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/autopilot-stack.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/babysit.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/bug-fix.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/eval.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/feature.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/hillclimb.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/investigation.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/multi-phase-plan.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/opening-a-pr.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/orchestrate.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/pause-safely.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/perf-issue.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/prototype.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/refactoring.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/runtime-forensics.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/session-pickup.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/shipping.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/trace-forensics.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/visual-parity.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/playbooks/worktree-cleanup.md` | adopted | Adapted playbook. Orchestration replaced by drive-epic, local-code-review, and worker-brief boundaries. |
| `pstack/skills/poteto-mode/references/bugbot-triage.md` | skipped | Cursor Bugbot product procedure. Not our review gate. |
| `pstack/skills/poteto-mode/scripts/bootstrap.ts` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/bun.lock` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/check-plan.mjs` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/check-plan.test.ts` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/orch/orch.test.ts` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/orch/orch.ts` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/orch/store.ts` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/package.json` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/watch-pr/cli.test.ts` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/watch-pr/cli.ts` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/watch-pr/fakes.test-helper.ts` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/watch-pr/github.test.ts` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/watch-pr/github.ts` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/watch-pr/policy.test.ts` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/watch-pr/policy.ts` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/watch-pr/render.ts` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/watch-pr/tsconfig.json` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/watch-pr/types.compile.ts` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/watch-pr/types.ts` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/watch-pr/watch-pr` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/poteto-mode/scripts/worktree-audit.sh` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/principle-attack-the-premise/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-boundary-discipline/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-build-the-lever/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-encode-lessons-in-structure/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-exhaust-the-design-space/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-experience-first/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-explain-the-number/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-fix-root-causes/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-foundational-thinking/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-guard-the-context-window/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-laziness-protocol/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-make-operations-idempotent/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-minimize-reader-load/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-model-the-domain/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-never-block-on-the-human/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-outcome-oriented-execution/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-prove-it-works/SKILL.md` | adopted | Previously folded into the three entrypoints. Now also a standalone skill. Upstream text at this pin matches the previous pin. |
| `pstack/skills/principle-redesign-from-first-principles/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-separate-before-serializing-shared-state/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-sequence-verifiable-units/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-subtract-before-you-add/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-test-behavior-not-implementation/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/principle-type-system-discipline/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/recall/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/reflect/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/reflect/references/divergent-reviewer.md` | security-class | Subagent prompt payload. Method, where kept, is in the parent skill. Not enabled. |
| `pstack/skills/reflect/references/judgment-reviewer.md` | security-class | Subagent prompt payload. Method, where kept, is in the parent skill. Not enabled. |
| `pstack/skills/reflect/references/synthesizer.md` | security-class | Subagent prompt payload. Method, where kept, is in the parent skill. Not enabled. |
| `pstack/skills/reflect/references/tooling-reviewer.md` | security-class | Subagent prompt payload. Method, where kept, is in the parent skill. Not enabled. |
| `pstack/skills/setup-pstack/SKILL.md` | security-class | Installer. Writes an always-applied model rule. Not vendored. |
| `pstack/skills/sharpen/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/show-me-your-work/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/show-me-your-work/references/decision-log-template.tsv` | adopted | Adapted reference. No host paths and no executable script. |
| `pstack/skills/show-me-your-work/scripts/log.sh` | security-class | Executable script or package. Not vendored and not run. |
| `pstack/skills/swarm/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/tdd/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/teach/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/technical-writing/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/typescript-best-practices/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/typescript-best-practices/references/patterns.md` | adopted | Adapted reference. No host paths and no executable script. |
| `pstack/skills/unslop/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/why/SKILL.md` | adopted | Adapted skill text. Model-neutral. No hooks, subagents, or session scripts. |
| `pstack/skills/why/references/epistemics.md` | skipped | Method folded into why/SKILL.md. Product MCP routing was not vendored. |
| `pstack/skills/why/references/investigator-prompt.md` | security-class | Subagent prompt payload. Method, where kept, is in the parent skill. Not enabled. |
| `pstack/skills/why/references/source-playbook.md` | skipped | Method folded into why/SKILL.md. Product MCP routing was not vendored. |
| `pstack/skills/why/references/sources/code-archaeology.md` | skipped | In-repo git archaeology is folded into why/SKILL.md. The source note is not vendored separately. |
| `pstack/skills/why/references/sources/databricks.md` | skipped | Third-party product query notes. Repository git method is in why/SKILL.md. |
| `pstack/skills/why/references/sources/datadog.md` | skipped | Third-party product query notes. Repository git method is in why/SKILL.md. |
| `pstack/skills/why/references/sources/incident-postmortem.md` | skipped | In-repo revert and incident-commit signals are folded into why/SKILL.md. The external postmortem note is not vendored. |
| `pstack/skills/why/references/sources/linear.md` | skipped | Third-party product query notes. Repository git method is in why/SKILL.md. |
| `pstack/skills/why/references/sources/notion.md` | skipped | Third-party product query notes. Repository git method is in why/SKILL.md. |
| `pstack/skills/why/references/sources/sentry.md` | skipped | Third-party product query notes. Repository git method is in why/SKILL.md. |
| `pstack/skills/why/references/sources/slack.md` | skipped | Third-party product query notes. Repository git method is in why/SKILL.md. |
| `pstack/skills/why/references/synthesizer-prompt.md` | security-class | Subagent prompt payload. Method, where kept, is in the parent skill. Not enabled. |

Counts: 79 adopted, 51 skipped, 40 security-class, 170 files.

## Upstream license notice

From [pstack/LICENSE](https://github.com/cursor/plugins/blob/cdb3c41c9f2f6d41f050e3dc25e15e325493d499/pstack/LICENSE):

MIT License

Copyright (c) 2026 Lauren Tan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
