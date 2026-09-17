---
type: Reference
title: Documentation Authority and Lifecycle Contract
description: Reference guide to repository authority classes, lifecycle states, conflict resolution, and citation hierarchy.
tags: [docs-authority, lifecycle, conflict-resolution, adr-013, contract]
---

# Documentation Authority and Lifecycle Contract

> [!NOTE]
> OpenWiki is a non-authoritative locator. The binding authority contract is defined in [`docs/architecture/docs-authority-lifecycle.md`](file:///home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot/docs/architecture/docs-authority-lifecycle.md) and frozen under [ADR-013](file:///home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot/docs/architecture/adr/adr-013-docs-knowledge-openwiki.md).

## Authority Classes and Precedence

The repository formalizes which artifact owns each category of fact. Higher authority overrides lower layers only for the fact types it specifically owns.

| Class | Canonical Location | Permitted Overrides |
|---|---|---|
| **Behavioral truth** | Code + tests (`scripts/`, `site/`, `tests/`) | Overrides prose or documentation that contradicts observed runtime execution |
| **Config-as-policy** | `scripts/config.py`, `scripts/config/*.yaml` | Overrides stale curated documentation restating the same knobs |
| **Binding rules** | `agents_extensions/shared/rules/`, `contracts/` | Overrides deployed harness copies (`.claude/`, `.codex/`, `.gemini/`) |
| **Deployed rule copies** | `.claude/`, `.codex/`, `.agent/`, `.gemini/` | Generated mirrors only; cannot establish policy or override sources |
| **Curated docs** | Tracked `docs/**` (with frontmatter lifecycles) | Guides humans/agents; cannot override code, config, or binding rules |
| **Architecture ADRs** | Permanent records in `docs/architecture/adr/` | Overrides prior ADRs only via explicit supersession |
| **Planning state** | GitHub issue/epic bodies (SSOT) | GitHub state wins over stale markdown plans |
| **Live ops / leases** | Monitor API (`/api/session/*`), live session streams | Live runtime only; **never** durable documentation fact |
| **OpenWiki** | `openwiki/**` | **Nothing** — locator and citation only; killable layer |

---

## Conflict-Resolution Procedure

When two repository artifacts disagree on a fact, agents and tooling must execute this deterministic procedure:

1. **Classify the fact type:** Determine whether the conflict involves runtime behavior, config parameters, binding agent rules, pedagogical intent, planning state, or live operations.
2. **Apply the authority table:** The class assigned ownership wins for that fact type.
3. **Decide by evidence of staleness if ownership is tied:**
   - Prefer the artifact with a newer verified git commit, passing live test, or explicit supersession link.
   - Prefer tool-backed code/config reads over narrative prose.
   - Prefer `/api/rules` / `agents_extensions/` over deployed rule mirrors when they drift.
4. **Record the disposition:** Note the conflict resolution in the PR description, issue comment, or decision card.
5. **OpenWiki never breaks ties:** OpenWiki is strictly forbidden from acting as an authority or tie-breaker.

---

## Worked Example: Immersion Policy Conflict

- **Scenario:** A curated documentation guide claims A1 lessons must maintain 70% Ukrainian text, whereas [`scripts/config.py`](file:///home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot/scripts/config.py) defines `TRACK_CONFIG["a1"]["immersion_range"] = [0.10, 0.50]`.
- **Resolution:** Config-as-policy wins. The executable configuration in `scripts/config.py` and operator contract item 9 govern runtime lesson building. The documentation is stale for that fact type.
- **OpenWiki Citation:** OpenWiki must cite `scripts/config.py` and the operator contract path, rather than repeating the obsolete documentation claim.

---

## Lifecycle States & Maintenance Rules

Curated documentation files use frontmatter status tags:
- `draft` → `active` → `superseded` → `archive`.

### Large Documentation Moves (>20 Files)
Per FBL-011, documentation moves touching more than 20 files must ship as a dedicated move PR without mixing code or behavioral changes. Breadcrumb stubs should be preserved for high-traffic paths to prevent breaking historical GitHub links.
