---
date: 2026-10-22
status: accepted
scope: agent rules
review_by: 2026-11-22
expires: 2026-11-22
---

# Decision: Rule lifecycle

## Context and decision

Rules need a traceable reason to exist and a regular review without growing
the instructions every seat loads. Keep a small per-rule record, use four tiers,
and review changes through existing PRs and tests. This document records the
design only. It does not rewrite rules or populate the records.

## Per-rule record

Keep a sibling file, `agents_extensions/shared/rules/core-lifecycle.yaml`, beside
`core-manifest.yaml`. This leaves the manifest's existing ID-to-anchor schema
unchanged. Key one record by each distinct anchor in the manifest, including
curriculum anchors, rather than duplicating records for IDs sharing an anchor.
Retain the record when a rule moves out of core, using the same anchor.

Each record has four fields:

- `origin`: an operator order, incident, or decision ID. Mark an untraced origin
  `unknown` for the CTO to resolve, rather than inventing provenance.
- `tier`: `PROTECTED`, `core`, `task_scoped`, or `tool_enforced`.
- `enforcement`: `kind` is `text`, `checklist`, or `tool`. For `tool`, also name
  the existing guard or CI check in `name`.
- `review_by`: the next review date in `YYYY-MM-DD` format.

This is manually maintained YAML. No new loader or validator is part of this
decision. Protection takes precedence over placement or enforcement method.

## Tiers and protection

| Tier | Content and treatment |
| --- | --- |
| `PROTECTED` | Ukrainian source of truth in core P5; mission, decolonization, anti-Russian-propaganda stance, and immersion policy in P9; curriculum non-negotiables in `core-curriculum.md` and `non-negotiable-rules.md`; OPSEC in P8. Only the operator may change these rules. Low citation counts never make them removal candidates. |
| `core` | Invariants every seat needs that a tool does not yet enforce. Keep these in the always-loaded core. |
| `task_scoped` | Procedures needed for a particular task or phase. Load these on demand through the existing selector. |
| `tool_enforced` | Rules enforced by an existing guard or CI check. Once that enforcement covers the obligation, core keeps a one-line pointer to the tool and the detailed procedure moves out of core. |

A protected rule remains `PROTECTED` even when a tool enforces it. Neither a
review date nor a tier change grants permission to weaken or remove protection.

## Adding or changing a rule

Include this four-line change record in the PR body:

```text
Problem and evidence: <failure or conflict, with a source>
Replaces or extends: <existing rule anchor, or none with a reason>
Tier: <PROTECTED, core, task_scoped, or tool_enforced>
Enforcement plan: <text, checklist, or existing tool name and coverage>
```

Core additions must be true invariants that are not yet enforceable by a tool.
If an addition would exceed the existing byte budget, the second line names
the rule moving down to the task-scoped or tool-enforced tier in the same PR.
Update the affected lifecycle records and retain the existing approval gates.

## Monthly review

The CTO spends about 30 minutes each month reviewing mistakes-ledger items
with `ML-` IDs in `lu-driver-state`, review findings, and lane escalations about
conflicting text. The first review is due on 2026-11-22.

Record merges of overlapping rules, demotions to task-scoped or tool-enforced
tiers, and removal proposals in one short report in `docs/decisions/` or the
tracker. Update origins and review dates for the rules examined. Protected
rules stay outside the removal-candidate list.

A non-protected rule is a removal candidate only when the preceding 90 days
contain neither a citation nor an incident. Missing history does not prove
absence. The CTO proposes removal with evidence; the operator must approve
before removal. Review dates trigger review, not automatic deletion or expiry
of a rule's protection.

## Budget and scope

Keep the existing byte ceiling in `tests/test_rules_core_loading.py` as the CI
backstop. It limits the share of context used by core and forces replacement
when adding rules. A measured basis for that ceiling is deferred to C-0719.

Non-goals are rewriting rule text, changing `core.md`, adding services, and
adding automation beyond existing tests. The existing decision check reads
`docs/decisions/decisions.yaml`; it does not validate Markdown front matter.
The review date above is explicit for the CTO's monthly review.
