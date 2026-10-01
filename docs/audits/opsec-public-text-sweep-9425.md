# Audit Report: OPSEC Public Text Sweep (#9425)

- **Date:** 2026-10-01
- **Task / Issue:** [#9425](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/9425) (`[infra][opsec] Sweep agent-facing docs and rules for operational detail in public text`)
- **Parent Stream Epic:** #5703 (`[epic] DevOps Stream`)
- **Driver:** Gemini (`gemini/opsec-9425-sweep`)
- **Reviewer of Record:** `claude-opus-5-5` (independent cross-family review)
- **Status:** Complete (AC-01 and AC-02 verified)

---

## 1. Executive Summary & Scope (AC-01)

This audit implements the security hardening required under issue #9425: systematically sweeping all public agent-facing documentation, rules, and runbooks to remove concrete operational details, infrastructure specifics, hosting topologies, and internal forge postures while strictly preserving the functional authority, requirements, and safety guarantees of every rule.

### Scanned Denominator
- **Denominator Size:** 375 markdown files across three core directories:
  - `agents_extensions/shared/` (shared rules, agent personas, skills, references)
  - `docs/runbooks/` (operational procedures, maintenance runbooks)
  - `docs/best-practices/` (workflow, gitflow, and quality standards)
- **Selection Criteria:** All public-facing documentation and agent context files that define execution behavior, repository configuration, infrastructure topology, and operational protocol.

---

## 2. Categorization of Findings

Findings identified across the denominator were grouped into four distinct operational security categories:

### Category A: Merge Automation & Retired Pipeline Labels
- **Description:** Mentions of internal pipeline labels (`automerge-ok`), workflow files (`auto-arm-merge.yml`), or automated merge permissions that disclose automation tooling topology or could lead agents to attempt self-labeling or unauthorized bypass.
- **Action Taken:** Replaced pipeline-specific label strings with neutral contract-level invariants requiring independent cross-family exact-head review and green CI checks prior to merge.

### Category B: Repository Protection & Forge Posture Disclosures
- **Description:** Concrete descriptions of GitHub plan limitations (e.g. private repo 403 API responses on branch protection), signed commit status ("off today"), organizational public/private status, or forge ruleset implementation gaps.
- **Action Taken:** Rephrased from organizational/forge vulnerability descriptions into neutral, universal technical standards and invariant merge guard requirements.

### Category C: Storage Topology, Host Paths & Service Counts
- **Description:** Explicit internal SMB share names (`UkrainianData`), cloud drive folder paths, absolute local host paths (`/home/ops/...`), loopback listener process counts, and systemd service dropin counts.
- **Action Taken:** Generalized to neutral architecture terms ("primary bulk storage mirror", "cloud storage fallback", relative repo paths, and standard service/timer dropin guards) while retaining strict local filesystem requirements for SQLite.

### Category D: Private Tracker Citations
- **Description:** Explicit cross-references to private security issue tracker IDs (e.g., `#622`, `#667`) in public files.
- **Action Taken:** Replaced private issue citations with corresponding public issue numbers or neutral authorization scopes.

---

## 3. Inventory of Neutralized Files & Changes (AC-02)

The following table documents each file modified in this sweep, the operational detail neutralized, and how rule meaning was preserved:

| File Path | Category | Neutralized Operational Detail | Invariant / Meaning Preserved |
| :--- | :--- | :--- | :--- |
| `agents_extensions/shared/agents/curriculum-track-orchestrator.md` | Cat A | Retired `automerge-ok` pipeline label and auto-arm references. | Preserved strict lane model requirement: driver lands own PRs only after independent cross-family review + blocking CI. Restored `#7450` citation. |
| `agents_extensions/shared/rules/critical-rules.md` | Cat A, Cat B | Neutralized `automerge-ok` pipeline wording (§8.5), ruleset non-existence disclosure (§8.1), and forge protection/org status disclosure (§8.6). | Preserved non-negotiable invariant that auto-merge and `--auto` cannot substitute for review/CI gates; preserved supply-chain controls and serialization requirements without forge posture disclosures. |
| `agents_extensions/shared/rules/workflow.md` | Cat A | Retired `auto-arm-merge.yml` and `automerge-ok` references. | Retained invariant that dispatched agents never self-enable auto-merge or bypass blocking CI checks. |
| `agents_extensions/shared/rules/storage-topology.md` | Cat C | Removed explicit Windows NTFS share name `UkrainianData`, Google Drive path, and `/Volumes/UkrainianData` mount path. | Retained all storage topology invariants: active DBs must remain strictly local; bulk roots require marker validation; network paths for SQLite remain strictly refused. |
| `agents_extensions/shared/skills/drive-ukrainian-dataset-epic/references/legacy-v4-contract.md` | Cat D | Removed private tracker citation `#622`. | Retained prohibition on restarting legacy V4 row generation. |
| `docs/best-practices/gitflow.md` | Cat B | Neutralized GitHub UI settings list, signed commit status ("off today"), and private repo 403 API response disclosures. | Preserved all 8 required branch invariants for `main` and explained deterministic local pre-tool merge guards without disclosing account or plan status. |
| `docs/runbooks/agent-seat-onboarding.md` | Cat D | Replaced private tracker citation `#667` with public authorization under `#6943`. | Retained full agent seat onboarding authorization scope. |
| `docs/runbooks/atlas-job-protocol.md` | Cat C | Neutralized explicit hosting provider references. | Retained atlas job execution protocol and failure isolation. |
| `docs/runbooks/clear-stale-git-lock.md` | Cat C | Removed absolute local host path `/home/ops/learn-ukrainian/.venv/bin/python`. | Retained exact command invocation using standard `.venv/bin/python`. |
| `docs/runbooks/storage-topology.md` | Cat C | Neutralized NTFS share name, Drive path, listener counts (4), and systemd dropin numbers (12). | Retained full storage topology layout, migration window steps, and exit status 78 guard behavior. |
| `tests/test_agent_seat_onboarding_docs.py` | Hygiene | Updated test assertion to match neutralized public citation `#6943`. | Fully passing (41/41 tests pass). |

---

## 4. Verification Evidence

1. **OPSEC Leak Linter:**
   - Command: `.venv/bin/python scripts/audit/lint_opsec_leaks.py origin/main...HEAD`
   - Result: 0 leaks detected across all touched files.
2. **Onboarding & Operator Contract Verification:**
   - Command: `.venv/bin/python -m pytest tests/test_agent_seat_onboarding_docs.py tests/test_opsec_linter.py tests/test_operator_contract_wiring.py`
   - Result: 71 passed in 3.92s.
3. **Storage Topology Resolver Verification:**
   - Command: `.venv/bin/python -m pytest tests/test_storage_resolver.py`
   - Result: All tests passing hermetically.
4. **Agent Deploy Synchronization:**
   - Synchronized canonical `agents_extensions/` into deployment directories via `npm run agents:deploy`.

---

## 5. Residual List & Ownership

- **Issue #9425 Residuals:** **None**. All findings across the 375-file denominator are resolved.
- **Related Split Workstreams:**
  - **Issue #9447 / Private #710:** External publisher text scan normalization gap (boundary normalization in external scanner). Owned by the Infra Driver.
