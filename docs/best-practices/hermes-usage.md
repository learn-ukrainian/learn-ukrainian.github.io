# Hermes usage — moved out of git (OPSEC)

Machine-local harness documentation (configuration recipes, auth-pool state,
automation adoption plan, local source-tree references) is **not tracked in
this public repository** by operator policy (2026-07-05).

- **Local working copy (gitignored):** `docs/references/private/hermes-usage.md`
  — agents on the operator's machine read and update it there.
- **Generic lane routing** (which model/harness for which task) remains public
  in `agents_extensions/shared/rules/model-assignment.md` (served at
  `/api/rules`).
- If the private copy is missing on a fresh machine, re-derive it from the
  operator's private infra notes; do not reconstruct machine specifics in any
  tracked file, PR body, or issue.

Do not add hermes machine-local configuration, paths, probe recipes, or
adoption-status tables back to this file.
