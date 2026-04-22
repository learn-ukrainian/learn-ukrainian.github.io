# `--force` Audit — 2026-04-22

Scope:
- `claude_extensions/rules/*.md`
- `.claude/rules/*.md`
- `docs/best-practices/*.md`
- `.worktree-briefs/*.md`

Notes:
- `.claude/rules/` was not present in this worktree at audit time, so there were no mirror-only hits to classify there.
- `.worktree-briefs/` contained no `--force` hits.
- Total hits: 4

## Classification Summary

| Classification | Count |
| --- | ---: |
| LOAD-BEARING | 3 |
| DROP | 0 |
| FLAG_FOR_HUMAN | 1 |

## Classified Hits

| Path | Classification | Snippet | Rationale | Action |
| --- | --- | --- | --- | --- |
| `claude_extensions/rules/workflow.md` | LOAD-BEARING | `Which files would --force delete for this module?` | Refers to the real `force-preview` API endpoint that exists specifically to make forced rebuilds inspectable before execution. | Kept as-is. |
| `docs/best-practices/agent-cooperation.md` | LOAD-BEARING | `Which files would --force delete?` | Same preview endpoint as the workflow rule; removing the term would hide the safety affordance that documents forced rebuild impact. | Kept as-is. |
| `docs/best-practices/gitflow.md` | LOAD-BEARING | `git push --force` | This is a prohibited-command example in a danger list, not advice to run it. The exact flag spelling is necessary for the warning to be precise. | Kept as-is. |
| `docs/best-practices/agent-cooperation.md` | FLAG_FOR_HUMAN | `scripts/build_module_v5.py ... --force-phase ...` | `--force-phase` is an escalation path, but whether it is a justified recovery tool or an unsafe copy-paste default is a product/process decision. | Added inline `TODO(#1394)` comment for owner review. |

## Drop Cases

No DROP cases were found in the audited paths, so no `--force` usage was removed from these docs/rules files.
