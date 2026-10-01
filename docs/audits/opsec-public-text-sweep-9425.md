# Audit Report: OPSEC Public Text Sweep (#9425)

- **Date:** 2026-10-01
- **Task / Issue:** [#9425](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/9425) (`[infra][opsec] Sweep agent-facing docs and rules for operational detail in public text`)
- **Parent Stream Epic:** #5703 (`[epic] DevOps Stream`)
- **Driver:** Gemini (`gemini/opsec-9425-sweep`)
- **Reviewer of Record:** Pending exact-head CF review (Claude Opus 5.5)
- **Status:** In Progress / Verification (Pre-Merge Review)

---

## 1. Executive Summary & Scope (AC-01)

This audit implements the operational security hardening required under issue #9425: systematically sweeping all public agent-facing documentation, rules, and runbooks to remove concrete operational details, infrastructure specifics, hosting topologies, and internal forge postures while strictly preserving the functional authority, requirements, and safety guarantees of every rule.

### Scanned Denominator
- **Denominator Size:** 375 tracked files (354 Markdown files and 21 YAML files) across three core directories:
  - `agents_extensions/shared/` (shared rules, agent personas, skills, references)
  - `docs/runbooks/` (operational procedures, maintenance runbooks)
  - `docs/best-practices/` (workflow, gitflow, and quality standards)
- **Selection Criteria:** All public-facing documentation and agent context files that define execution behavior, repository configuration, infrastructure topology, and operational protocol.

---

## 2. Categorization of Findings

Findings identified across the denominator were grouped into four distinct operational security categories:

### Category A: Merge Automation & Retired Pipeline Labels
- **Description:** Mentions of internal pipeline labels (`automerge-ok`), workflow files (`auto-arm-merge.yml`), or automated merge permissions that disclose automation tooling topology or could lead agents to attempt self-labeling or unauthorized bypass.
- **Action Taken:** Replaced pipeline-specific label strings with neutral contract-level invariants requiring independent cross-family exact-head review and green CI checks prior to merge. Corrected local pre-tool merge guard documentation in `gitflow.md` to reflect exact tool behavior without asserting review verification in tooling.

### Category B: Repository Protection & Forge Posture Disclosures
- **Description:** Concrete descriptions of GitHub plan limitations (e.g. private repo 403 API responses on branch protection), signed commit status ("off today"), organizational public/private status, or forge ruleset implementation gaps.
- **Action Taken:** Rephrased from organizational/forge vulnerability descriptions into neutral, universal technical standards and invariant merge guard requirements.

### Category C: Storage Topology, Host Paths & Service Counts
- **Description:** Explicit internal SMB share names (`UkrainianData`), cloud drive folder paths, absolute local host paths (`/home/ops/...`), backup repository remotes (`rclone:lu-gdrive:...`), loopback listener process counts, and systemd service dropin counts.
- **Action Taken:** Generalized to neutral architecture terms ("primary bulk storage mirror", "cloud storage fallback", relative repo paths, generic backup remote placeholders, and standard service/timer dropin guards) while retaining strict local filesystem requirements for SQLite.

### Category D: Private Tracker Citations
- **Description:** Explicit cross-references to private security issue tracker IDs (e.g., `#622`, `#667`) in public files.
- **Action Taken:** Replaced private issue citations with corresponding public issue numbers or neutral authorization scopes. Extended `scripts/audit/lint_opsec_leaks.py` with automated detection for Category D private tracker patterns in public agent docs and rules.

---

## 3. Inventory of Neutralized Files & Changes (AC-02)

The following table documents each file modified in this sweep, the operational detail neutralized, and how rule meaning was preserved:

| File Path | Category | Neutralized Operational Detail | Invariant / Meaning Preserved |
| :--- | :--- | :--- | :--- |
| `agents_extensions/shared/agents/curriculum-track-orchestrator.md` | Cat A | Retired `automerge-ok` pipeline label and auto-arm references. | Preserved strict lane model requirement: driver lands own PRs only after independent cross-family review + blocking CI. Restored `#7450` citation. |
| `agents_extensions/shared/rules/critical-rules.md` | Cat A, Cat B | Neutralized `automerge-ok` pipeline wording (§8.5), ruleset non-existence disclosure (§8.1), and forge protection/org status disclosure (§8.6). Restored concrete cancellation instruction (item 2). | Preserved non-negotiable invariant that auto-merge and `--auto` cannot substitute for review/CI gates; preserved supply-chain controls and serialization requirements without forge posture disclosures. |
| `agents_extensions/shared/rules/workflow.md` | Cat A | Retired `auto-arm-merge.yml` and `automerge-ok` references. | Retained invariant that dispatched agents never self-enable auto-merge or bypass blocking CI checks. |
| `agents_extensions/shared/rules/storage-topology.md` | Cat C | Removed explicit Windows NTFS share name `UkrainianData`, Google Drive path, `/Volumes/UkrainianData` mount path, and platform-specific cache/maintenance wording. | Retained all storage topology invariants: active DBs must remain strictly local; bulk roots require marker validation; network paths for SQLite remain strictly refused. |
| `agents_extensions/shared/skills/drive-ukrainian-dataset-epic/references/legacy-v4-contract.md` | Cat D | Removed private tracker citation `#622`. | Retained prohibition on restarting legacy V4 row generation. |
| `docs/best-practices/gitflow.md` | Cat B, Cat A | Neutralized GitHub UI settings list, signed commit status ("off today"), private repo 403 API response disclosures, and corrected pre-tool merge guard checks. | Preserved all 8 required branch invariants for `main` and accurately documented local pre-tool merge guards (draft, check states, branch protection inspection). |
| `docs/runbooks/agent-seat-onboarding.md` | Cat D | Replaced private tracker citation `#667` with public authorization under `#6943`. | Retained full agent seat onboarding authorization scope. |
| `docs/runbooks/atlas-job-protocol.md` | Cat C | Neutralized explicit hosting provider references. | Retained atlas job execution protocol and failure isolation. |
| `docs/runbooks/clear-stale-git-lock.md` | Cat C | Removed absolute local host path `/home/ops/learn-ukrainian/.venv/bin/python`. | Retained exact command invocation using standard `.venv/bin/python`. |
| `docs/runbooks/storage-topology.md` | Cat C | Neutralized NTFS share name (`Get-SmbShare -Name UkrainianData` -> `Get-SmbShare`), Drive path, listener counts, systemd dropin numbers, and Mac/Finder cache reclaim phrasing. | Retained full storage topology layout, migration window steps, and exit status 78 guard behavior. |
| `docs/runbooks/teacher-curated-seed-rebuild.md` | Cat C | Neutralized concrete cloud drive recovery and curriculum paths (`/absolute/path/to/My Drive/Projects/...`). | Retained teacher-curated seed rebuild workflow using generic path placeholders. |
| `docs/runbooks/data-backup.md` | Cat C | Neutralized concrete restic backup remote and path (`rclone:lu-gdrive:Projects/learn-ukrainian-restic`). | Retained backup initialization and execution procedures using generic remote placeholder. |
| `scripts/audit/lint_opsec_leaks.py` | Tooling | Added Category D private tracker pattern detection (`\b(?:private\|infra-private)\s*#[0-9]+\b`) for public documentation and agent rule paths. | Automates enforcement so private tracker citations in public text are blocked in pre-push and CI. |
| `tests/test_opsec_linter.py` | Tooling | Added unit tests verifying Category D private tracker citation detection in public agent docs and rules. | Verified via pytest (19/19 passing). |
| `tests/test_agent_seat_onboarding_docs.py` | Hygiene | Updated test assertion to match neutralized public citation `#6943`. | Fully passing (41/41 tests pass). |

---

## 4. Verification Evidence

1. **OPSEC Leak Linter:**
   - Command: `.venv/bin/python scripts/audit/lint_opsec_leaks.py origin/main...HEAD`
   - Result: 0 leaks detected across all touched files.
2. **Onboarding & Operator Contract Verification:**
   - Command: `.venv/bin/python -m pytest tests/test_agent_seat_onboarding_docs.py tests/test_opsec_linter.py tests/test_operator_contract_wiring.py`
   - Result: 73 passed.
3. **Storage Topology Resolver Verification:**
   - Command: `.venv/bin/python -m pytest tests/test_storage_resolver.py`
   - Result: All hermetic storage tests pass.
4. **Agent Deploy Preflight:**
   - Command: `npm run agents:deploy -- --dry-run`
   - Result: Preflight clean. Actual synchronization will be executed post-merge as required by the terminal goal.

---

## 5. Recorded Residuals & Ownership

Per the issue's residual policy, items outside documentation/rules scope or belonging to split workstreams are recorded with their owner:

1. **Public Python Code Constant `SMB_SHARE_NAME`:**
   - **Path:** `scripts/storage/topology.py:27`
   - **Category:** Category C (Storage Share Names)
   - **Description:** `SMB_SHARE_NAME = "UkrainianData"` is defined as a code constant consumed by storage topology candidates and PowerShell maintenance scripts. Code refactoring is outside the Markdown/YAML documentation sweep scope of #9425 (per non-goals).
   - **Owner:** Infra Driver / Storage Maintainer.

2. **External Scanner Boundary Normalization Gap:**
   - **Issue:** Tracked under public issue [#9447](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/9447)
   - **Category:** Category D (Scanner Boundary Normalization)
   - **Description:** Normalization of publisher text scanning boundaries in the external publisher proxy.
   - **Owner:** Infra Driver.
