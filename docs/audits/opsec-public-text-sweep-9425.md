# Audit Report: OPSEC Public Text Sweep (#9425)

- **Date:** 2026-10-01
- **Task / Issue:** [#9425](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/9425) (`[infra][opsec] Sweep agent-facing docs and rules for operational detail in public text`)
- **Parent Stream Epic:** #5703 (`[epic] DevOps Stream`)
- **Driver:** Gemini (`gemini/opsec-9425-sweep`)
- **Reviewer of Record:** Pending exact-head CF review (Claude Opus 5.5)
- **Status:** In Progress / Verification (Pre-Merge Review)

---

## 1. Executive Summary & Denominator Definition (AC-01)

This audit implements the operational security hardening required under issue #9425: systematically sweeping all public agent-facing documentation, rules, and runbooks to remove concrete operational details, infrastructure specifics, hosting topologies, and internal forge postures while strictly preserving the functional authority, requirements, and safety guarantees of every rule.

### Scanned Denominator
The complete denominator consists of **375 tracked Markdown and YAML files** across three canonical roots:
- `agents_extensions/shared/`: 254 files (233 Markdown, 21 YAML)
- `docs/runbooks/`: 64 files (64 Markdown, 0 YAML)
- `docs/best-practices/`: 57 files (57 Markdown, 0 YAML)
Total denominator: **375 files** (354 Markdown, 21 YAML).

---

## 2. Categorization of Findings

Findings identified across the denominator were grouped into four distinct operational security categories:

### Category A: Merge Automation & Retired Pipeline Labels
- **Description:** Mentions of internal pipeline labels (`automerge-ok`), workflow files (`auto-arm-merge.yml`), or automated merge permissions that disclose automation tooling topology or could lead agents to attempt self-labeling or unauthorized bypass.
- **Action Taken:** Replaced pipeline-specific label strings with neutral contract-level invariants requiring independent cross-family exact-head review and green CI checks prior to merge. Corrected local pre-tool merge guard documentation in `gitflow.md` and `guard-pr-merge.py` to reflect exact tool behavior without asserting review verification in tooling.

### Category B: Repository Protection & Forge Posture Disclosures
- **Description:** Concrete descriptions of GitHub plan limitations (e.g. private repo 403 API responses on branch protection), signed commit status ("off today"), organizational public/private status, or forge ruleset implementation gaps.
- **Action Taken:** Rephrased from organizational/forge vulnerability descriptions into neutral, universal technical standards and invariant merge guard requirements.

### Category C: Storage Topology, Host Paths & Service Counts
- **Description:** Explicit internal SMB share names (`UkrainianData`), cloud drive folder paths, absolute local host paths (`/home/ops/...`), backup repository remotes (`rclone:lu-gdrive:...`), loopback listener process counts, and systemd service dropin counts.
- **Action Taken:** Generalized to neutral architecture terms ("primary bulk storage mirror", "cloud storage fallback", relative repo paths, generic backup remote placeholders, and standard service/timer dropin guards) while retaining strict local filesystem requirements for SQLite.

### Category D: Private Tracker Citations
- **Description:** Explicit cross-references to private security issue tracker numbers in public files.
- **Action Taken:** Replaced private issue citations with corresponding public issue numbers or neutral authorization scopes. Extended `scripts/audit/lint_opsec_leaks.py` with automated detection for Category D private tracker patterns in public agent docs and rules.

---

## 3. Inventory of Neutralized Files & Changes (AC-02)

| File Path | Category | Neutralized Operational Detail | Invariant / Meaning Preserved |
| :--- | :--- | :--- | :--- |
| `agents_extensions/shared/agents/curriculum-track-orchestrator.md` | Cat A | Retired `automerge-ok` pipeline label and auto-arm references. | Preserved strict lane model requirement: driver lands own PRs only after independent cross-family review + blocking CI. Restored `#7450` citation. |
| `agents_extensions/shared/rules/critical-rules.md` | Cat A, Cat B | Neutralized `automerge-ok` pipeline wording (§8.5), ruleset non-existence disclosure (§8.1), and forge protection/org status disclosure (§8.6). Restored concrete cancellation instruction (item 2). | Preserved non-negotiable invariant that auto-merge and `--auto` cannot substitute for review/CI gates; preserved supply-chain controls and serialization requirements without forge posture disclosures. |
| `agents_extensions/shared/rules/storage-topology.md` | Cat C | Removed explicit Windows NTFS share name `UkrainianData`, Google Drive path, `/Volumes/UkrainianData` mount path, and platform-specific cache/maintenance wording. | Retained all storage topology invariants: active DBs must remain strictly local; bulk roots require marker validation; network paths for SQLite remain strictly refused. |
| `agents_extensions/shared/rules/workflow.md` | Cat A | Retired `auto-arm-merge.yml` and `automerge-ok` references. | Retained invariant that dispatched agents never self-enable auto-merge or bypass blocking CI checks. |
| `agents_extensions/shared/skills/drive-ukrainian-dataset-epic/SKILL.md` | Cat D | Neutralized private operational board citation to paired private tracking surface. | Retained requirement that stopped V4 dataset production remains stopped. |
| `agents_extensions/shared/skills/drive-ukrainian-dataset-epic/references/legacy-v4-contract.md` | Cat D | Neutralized private operational board and tracker citations in identity block and launch prompt. | Retained prohibition on restarting legacy V4 row generation. |
| `docs/best-practices/gitflow.md` | Cat B, Cat A | Neutralized GitHub UI settings list, signed commit status ("off today"), private repo 403 API response disclosures, and corrected pre-tool merge guard checks. | Preserved all 8 required branch invariants for `main` and accurately documented local pre-tool merge guards (draft, check states, running checks, branch protection inspection). |
| `docs/runbooks/agent-seat-onboarding.md` | Cat D | Replaced internal tracker citation with public authorization under `#6943`. | Retained full agent seat onboarding authorization scope. |
| `docs/runbooks/atlas-job-protocol.md` | Cat C | Neutralized explicit hosting provider references. | Retained atlas job execution protocol and failure isolation. |
| `docs/runbooks/clear-stale-git-lock.md` | Cat C | Removed absolute local host path `/home/ops/learn-ukrainian/.venv/bin/python`. | Retained exact command invocation using standard `.venv/bin/python`. |
| `docs/runbooks/data-backup.md` | Cat C | Neutralized cloud provider desktop sync mount name, lu-gdrive remote, OAuth renewal details, and scheduled job label. | Retained backup initialization and execution procedures using generic remote placeholder and documented LU_BACKUP_ENV_FILE path. |
| `docs/runbooks/grok-bot-qa-observer.md` | Cat D | Neutralized internal tracking issue citation from line 79 to paired private tracking issues. | Retained operational QA review evidence notes without exposing private tracker names or issue numbers. |
| `docs/runbooks/storage-topology.md` | Cat C | Neutralized NTFS share name (`Get-SmbShare -Name UkrainianData` -> `Get-SmbShare`), Drive path, listener counts, systemd dropin numbers, and Mac/Finder cache reclaim phrasing. | Retained full storage topology layout, migration window steps, and exit status 78 guard behavior. |
| `docs/runbooks/teacher-curated-seed-rebuild.md` | Cat C | Neutralized concrete cloud drive recovery and curriculum paths (`/absolute/path/to/My Drive/Projects/...`). | Retained teacher-curated seed rebuild workflow using generic path placeholders. |
| `agents_extensions/shared/hooks/guard-pr-merge.py` | Cat B | Neutralized historical private repo 403 API response disclosures in docstring and _FOOTER. | Retained fail-closed merge guard enforcement logic and exact command checking. |
| `scripts/audit/lint_opsec_leaks.py` | Tooling | Added Category D private tracker pattern detection with targeted qualifiers, colons, parens, and markdown links for public documentation and agent rule paths. | Automates enforcement so private tracker citations in public text are blocked in local pre-commit and pre-push hooks while preventing false positives. |
| `tests/test_opsec_linter.py` | Tooling | Added unit tests verifying Category D private tracker citation detection in public agent docs/rules and false positive prevention. | Verified via pytest (20/20 passing). |
| `tests/test_agent_seat_onboarding_docs.py` | Hygiene | Updated test assertion to match neutralized public citation `#6943`. | Fully passing (41/41 tests pass). |

---

## 4. Evaluation of Conventional Local Paths & Host Plist Identifiers

During the denominator sweep, references to standard off-repo local secret paths (`~/.secrets/`) and macOS LaunchAgent plist labels (`com.learn-ukrainian.*`) were evaluated across the denominator:

1. **Standard Local Secret Directory (`~/.secrets/`):**
   - **Evaluated Files:** `rules/model-assignment.md:299`, `skills/typesafe-ai/SKILL.md:32,36,56`, `best-practices/typesafe-jev.md:22,25`, `runbooks/atlas-job-protocol.md:96`, `runbooks/launchd-inventory.md:44`, `runbooks/recovery.md:172`.
   - **Evaluation & Rationale:** `~/.secrets/` is the project-wide convention for local off-repo credential storage on developer and service hosts. Its mention informs operators and agents where machine-local credentials reside without embedding secret keys or environment variables in tracked git files. These paths disclose no credentials, API keys, hostnames, or network topology, and are retained as standard acceptable local conventions.

2. **Standard Host Plist Identifiers (`com.learn-ukrainian.*`):**
   - **Evaluated Files:** `launchd-inventory.md`, `local-api-server.md`, `archived-thread-cleanup.md`, `worktree-cleanup.md`, `recovery.md`.
   - **Evaluation & Rationale:** `com.learn-ukrainian.<service>` is the reverse-DNS bundle namespace standard for macOS LaunchAgent plists (`~/Library/LaunchAgents/`). It represents standard local service names (e.g. `monitor-api`, `worktree-cleanup`, `codex-archived-thread-cleanup`), disclosing no internal IP addresses, credentials, or private attack surfaces.

3. **Standard Local Loopback Service Endpoints (`localhost:8765`, `127.0.0.1:8765`):**
   - **Evaluated Files:** Appears across 25 denominator files (e.g. `docs/best-practices/universal-rules-registry.md`, `docs/best-practices/local-api-server.md`, `agents_extensions/shared/rules/mcp-server-registry.yaml`, etc.).
   - **Evaluation & Rationale:** Port 8765 is the well-known local loopback daemon endpoint for the local MCP tool and Monitor API server running strictly on the host loopback interface (`127.0.0.1`). It is not routable externally, exposes no public IP addresses or wide-area network topology, and is required for local agent tool discovery and IPC. Retained as standard local loopback convention.

---

## 5. Recorded Residuals & Ownership

Per the issue residual policy, items outside the documentation sweep or belonging to other drivers are formally recorded:

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

3. **Backup Shell Script Remote Name (`lu-gdrive`):**
   - **Path:** `scripts/backup-data.sh:194`
   - **Category:** Category C (Backup Remote Names)
   - **Description:** `scripts/backup-data.sh` contains default remote name fallback `lu-gdrive`. Shell scripts are outside the documentation denominator scope of #9425.
   - **Owner:** Infra Driver.

4. **Systemd Service Environment File Path:**
   - **Path:** `packaging/systemd/learn-ukrainian-backup.service:7` and `packaging/systemd/README.md:141`
   - **Category:** Category C (Service Environment Paths)
   - **Description:** Packaging unit definitions and packaging README outside the documentation denominator scope specify `%h/.secrets/learn-ukrainian-backup.env`.
   - **Owner:** Infra Driver.

5. **Windows Storage Documentation Share Name:**
   - **Path:** `scripts/storage/windows/README.md`
   - **Category:** Category C (Storage Share Names)
   - **Description:** Storage scripts documentation outside the documentation denominator references share name `UkrainianData`.
   - **Owner:** Infra Driver.

6. **Branch Switch Hook Private Repository Path Reference:**
   - **Path:** `agents_extensions/shared/hooks/guard-branch-switch-in-main.py:112`
   - **Category:** Category B / D (Hook Repo References)
   - **Description:** Python hook contains an exception handling path naming the private repository.
   - **Owner:** Infra Driver.

7. **Open-Model Data Delivery Plan Private Tracker Citations:**
   - **Path:** `docs/projects/open-model-data/cyrillic-slavic-dataset-delivery-plan.md:17,181`
   - **Category:** Category D (Private Tracker Citations)
   - **Description:** Delivery plan document outside denominator roots contains cross-references to internal operational board tracker issues at lines 17 and 181.
   - **Owner:** Open-Model-Data Driver.

8. **V4 Runtime Python Package & Open-Model-Data Test Fixture Citations:**
   - **Path:** `packages/v4-runtime/src/learn_ukrainian_v4_runtime/` (14 Python modules: `v4_a10_pilot_review_gate.py`, `v4_a11_silver_release_gate.py`, `v4_a12_gold_overlay_gate.py`, `v4_a13_cleanup_recovery.py`, `v4_a3_builder_packet.py`, `v4_a4_deterministic_extraction.py`, `v4_a5_evidence_enrichment.py`, `v4_a6_blind_arena.py`, `v4_a7_original_row_factory.py`, `v4_a8_admission_assembly.py`, `v4_a9_evaluation_package.py`, `v4_per_slot_private_factory.py`, `v4_public_slot_commitment_assignment.py`, `v4_source_byte_ingestion_admission.py`; and 13 provenance JSON blobs) plus 11 test modules under `tests/projects/open_model_data/`
   - **Category:** Category D (Private Tracker Citations)
   - **Description:** Python package runtime modules, provenance JSON blobs, and test fixture definitions outside denominator roots carry `"private_operational_board": 622`.
   - **Owner:** Open-Model-Data Driver.

9. **Historical Design Document Private Tracker Citations:**
   - **Path:** `docs/design/2026-09-06-cloud-agent-pytest-advisory.md:27` and `docs/design/control-plane-storage-seam.md:1,88`
   - **Category:** Category D (Private Tracker Citations)
   - **Description:** Historical architectural design documents outside denominator roots cite internal issue tracker numbers at line 27 and lines 1 and 88.
   - **Owner:** Infra Driver.

10. **Workflows, Scripts, Planning Documents & Test Fixtures Outside Denominator Roots:**
    - **Path / Repeatable Search:** `git grep -nI -iE 'private.*#[0-9]'` (outside the swept denominator roots `agents_extensions/shared/`, `docs/runbooks/`, `docs/best-practices/`, and `docs/audits/`):
      - `docs/plans/2026-09-02-ci-sweet-spot.md:5`: historical CI plan cites private issue tracker with URL
      - `.github/workflows/security-audit.yml:8`, `scripts/ci/audit_dependencies.py:6`, `scripts/config/pip-audit-ignore.yaml:2`: dependency audit workflow and scripts cite private security audit tracking issue
      - `scripts/audit/curriculum_manifest_canary.py:19`: curriculum manifest canary script cites private canary tracking issue
      - `scripts/control_plane/storage.py:3`, `scripts/fleet_comms/artifacts.py:10`: control plane storage and fleet comms scripts cite private storage seam issue
      - `scripts/fleet_comms/cli.py:227`, `scripts/fleet_comms/fleet_overview.py:1`: fleet comms tools cite private seat issue
      - `scripts/orchestration/reconcile_sweep.py:237`: reconciliation sweep script cites private issue
      - `tests/test_hramatka_scope_gate.py:188`: test fixture assertion string cites private board number
    - **Category:** Category D (Private Tracker Citations)
    - **Description:** Operational Python scripts, CI GitHub workflows, planning documents, and test fixture strings outside the documentation sweep denominator contain internal tracker references.
    - **Owner:** Infra Driver.

---

## 6. Verification Evidence

1. **OPSEC Leak Linter:**
   - Command: `.venv/bin/python scripts/audit/lint_opsec_leaks.py origin/main...HEAD`
   - Result: 0 leaks detected across all touched files.
2. **Onboarding & Operator Contract Verification:**
   - Command: `.venv/bin/python -m pytest tests/test_agent_seat_onboarding_docs.py tests/test_opsec_linter.py tests/test_operator_contract_wiring.py tests/test_storage_resolver.py`
   - Result: 91 passed in 5.86s.
3. **PR Merge Guard Verification:**
   - Command: `.venv/bin/python -m pytest tests/test_guard_pr_merge.py`
   - Result: 286 passed in 11.30s.
4. **Agent Deploy Preflight:**
   - Command: `npm run agents:deploy -- --dry-run`
   - Result: Preflight clean. Actual synchronization will be executed post-merge as required by the terminal goal.

---

## 7. Complete Denominator Disposition Table (375 Files)

The following table records the verification disposition of every tracked file in the denominator:

| # | File Path | Root | Disposition | Category / Notes |
| :---: | :--- | :--- | :---: | :--- |

| 1 | `agents_extensions/shared/NON-NEGOTIABLE-RULES.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 2 | `agents_extensions/shared/_archive/commands/module-act.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 3 | `agents_extensions/shared/_archive/commands/module-integrate.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 4 | `agents_extensions/shared/_archive/commands/module-stage-1.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 5 | `agents_extensions/shared/_archive/commands/module-stage-2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 6 | `agents_extensions/shared/_archive/commands/module-stage-3.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 7 | `agents_extensions/shared/_archive/commands/module-stage-4.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 8 | `agents_extensions/shared/_archive/commands/module-vocab.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 9 | `agents_extensions/shared/_archive/commands/review-content.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 10 | `agents_extensions/shared/agents/curriculum-orchestrator.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 11 | `agents_extensions/shared/agents/curriculum-track-orchestrator.md` | `agents_extensions/shared` | **NEUTRALIZED** | Cat A: Neutralized automerge-ok and auto-arm pipeline wording; preserved #7450 citation |
| 12 | `agents_extensions/shared/agents/curriculum-writer.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 13 | `agents_extensions/shared/agents/infra-orchestrator.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 14 | `agents_extensions/shared/commands/state.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 15 | `agents_extensions/shared/consultation-queue/README.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 16 | `agents_extensions/shared/consultation-queue/applied/20260313T185704317117-being-and-becoming.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 17 | `agents_extensions/shared/consultation-queue/rejected/20260313T184951744734-being-and-becoming.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 18 | `agents_extensions/shared/contracts/rollover-registry.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 19 | `agents_extensions/shared/contracts/task-identity.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 20 | `agents_extensions/shared/contracts/task-lifecycle-closeout.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 21 | `agents_extensions/shared/curriculum-lifecycle/config/certification-profiles.v1.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 22 | `agents_extensions/shared/curriculum-lifecycle/config/coordinator.v1.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 23 | `agents_extensions/shared/curriculum-lifecycle/config/legacy-prompt-migration.v1.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 24 | `agents_extensions/shared/curriculum-lifecycle/config/pilot-matrix.v1.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 25 | `agents_extensions/shared/curriculum-lifecycle/config/readiness-profiles.v1.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 26 | `agents_extensions/shared/docs/session-streams-design.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 27 | `agents_extensions/shared/memory/MEMORY.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 28 | `agents_extensions/shared/phases/calibration/a1.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 29 | `agents_extensions/shared/phases/calibration/a2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 30 | `agents_extensions/shared/phases/calibration/b1-bridge.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 31 | `agents_extensions/shared/phases/calibration/b1-immersed.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 32 | `agents_extensions/shared/phases/calibration/b2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 33 | `agents_extensions/shared/phases/calibration/bio.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 34 | `agents_extensions/shared/phases/calibration/c1.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 35 | `agents_extensions/shared/phases/calibration/hist.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 36 | `agents_extensions/shared/phases/calibration/istorio.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 37 | `agents_extensions/shared/phases/calibration/lit.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 38 | `agents_extensions/shared/phases/calibration/oes.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 39 | `agents_extensions/shared/phases/calibration/ruth.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 40 | `agents_extensions/shared/phases/claude/direct-review.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 41 | `agents_extensions/shared/phases/gemini/README.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 42 | `agents_extensions/shared/phases/gemini/_retired/content-v6.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 43 | `agents_extensions/shared/phases/gemini/_retired/phase-0-5-enrich-plan.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 44 | `agents_extensions/shared/phases/gemini/_retired/phase-0-research-core.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 45 | `agents_extensions/shared/phases/gemini/_retired/phase-1-meta.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 46 | `agents_extensions/shared/phases/gemini/_retired/phase-2-content-section.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 47 | `agents_extensions/shared/phases/gemini/_retired/phase-2-summary.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 48 | `agents_extensions/shared/phases/gemini/_retired/phase-6-review.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 49 | `agents_extensions/shared/phases/gemini/_retired/phase-7-final-review.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 50 | `agents_extensions/shared/phases/gemini/_retired/phase-D-review-fix.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 51 | `agents_extensions/shared/phases/gemini/_shared-activity-rules.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 52 | `agents_extensions/shared/phases/gemini/_shared-content-rules-beginner.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 53 | `agents_extensions/shared/phases/gemini/_shared-content-rules-core.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 54 | `agents_extensions/shared/phases/gemini/_shared-content-rules.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 55 | `agents_extensions/shared/phases/gemini/_shared-preflight.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 56 | `agents_extensions/shared/phases/gemini/_shared-quality-dimensions-seminar.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 57 | `agents_extensions/shared/phases/gemini/_shared-quality-dimensions.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 58 | `agents_extensions/shared/phases/gemini/_shared-self-audit.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 59 | `agents_extensions/shared/phases/gemini/activities.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 60 | `agents_extensions/shared/phases/gemini/activity-build.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 61 | `agents_extensions/shared/phases/gemini/activity-schema-examples.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 62 | `agents_extensions/shared/phases/gemini/beginner-activities.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 63 | `agents_extensions/shared/phases/gemini/beginner-checkpoint-activities.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 64 | `agents_extensions/shared/phases/gemini/beginner-checkpoint.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 65 | `agents_extensions/shared/phases/gemini/beginner-full-rag.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 66 | `agents_extensions/shared/phases/gemini/beginner-research.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 67 | `agents_extensions/shared/phases/gemini/consultation.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 68 | `agents_extensions/shared/phases/gemini/content.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 69 | `agents_extensions/shared/phases/gemini/core-activities.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 70 | `agents_extensions/shared/phases/gemini/core-checkpoint-activities.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 71 | `agents_extensions/shared/phases/gemini/core-checkpoint.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 72 | `agents_extensions/shared/phases/gemini/core-content.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 73 | `agents_extensions/shared/phases/gemini/direct-enrich.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 74 | `agents_extensions/shared/phases/gemini/fix-activities.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 75 | `agents_extensions/shared/phases/gemini/fix-content.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 76 | `agents_extensions/shared/phases/gemini/fix.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 77 | `agents_extensions/shared/phases/gemini/gemini-review-fix.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 78 | `agents_extensions/shared/phases/gemini/gemini-review-pass1.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 79 | `agents_extensions/shared/phases/gemini/gemini-review-pass2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 80 | `agents_extensions/shared/phases/gemini/help-response.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 81 | `agents_extensions/shared/phases/gemini/phase-0-research-seminar.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 82 | `agents_extensions/shared/phases/gemini/phase-2-content.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 83 | `agents_extensions/shared/phases/gemini/phase-3-activities.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 84 | `agents_extensions/shared/phases/gemini/phase-5-review.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 85 | `agents_extensions/shared/phases/gemini/phase-A-core.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 86 | `agents_extensions/shared/phases/gemini/phase-A-meta-only.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 87 | `agents_extensions/shared/phases/gemini/phase-A-pro.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 88 | `agents_extensions/shared/phases/gemini/phase-A-seminar.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 89 | `agents_extensions/shared/phases/gemini/phase-D1-evidence-review.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 90 | `agents_extensions/shared/phases/gemini/phase-D1-output-format.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 91 | `agents_extensions/shared/phases/gemini/phase-D1-structured-review.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 92 | `agents_extensions/shared/phases/gemini/phase-D2-repair.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 93 | `agents_extensions/shared/phases/gemini/phase-fix-activities.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 94 | `agents_extensions/shared/phases/gemini/phase-fix-content.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 95 | `agents_extensions/shared/phases/gemini/phase-fix.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 96 | `agents_extensions/shared/phases/gemini/phase-gemini-review-fix.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 97 | `agents_extensions/shared/phases/gemini/phase-gemini-review-pass1.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 98 | `agents_extensions/shared/phases/gemini/phase-gemini-review-pass2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 99 | `agents_extensions/shared/phases/gemini/plan-enrichment.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 100 | `agents_extensions/shared/phases/gemini/research-core.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 101 | `agents_extensions/shared/phases/gemini/research-meta-only.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 102 | `agents_extensions/shared/phases/gemini/research-pro.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 103 | `agents_extensions/shared/phases/gemini/research-seminar-v0.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 104 | `agents_extensions/shared/phases/gemini/research-seminar.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 105 | `agents_extensions/shared/phases/gemini/resource-request.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 106 | `agents_extensions/shared/phases/gemini/review-evidence.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 107 | `agents_extensions/shared/phases/gemini/review-legacy.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 108 | `agents_extensions/shared/phases/gemini/review-output-format.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 109 | `agents_extensions/shared/phases/gemini/review-repair.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 110 | `agents_extensions/shared/phases/gemini/review-structured.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 111 | `agents_extensions/shared/phases/gemini/v6-review.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 112 | `agents_extensions/shared/phases/gemini/v6-write.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 113 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-common.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 114 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-core-a1.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 115 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-core-a2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 116 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-core-b1.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 117 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-core-b2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 118 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-core-c1.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 119 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-core-c2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 120 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-core.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 121 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-seminar-bio-v1-2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 122 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-seminar-bio.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 123 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-seminar-folk-v1-2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 124 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-seminar-folk.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 125 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-seminar-hist-v1-2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 126 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-seminar-istorio-v1-2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 127 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-seminar-lit-v1-2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 128 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-seminar-oes-v1-2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 129 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-seminar-ruth-v1-2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 130 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-seminar-v1-2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 131 | `agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-seminar.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 132 | `agents_extensions/shared/prompt-contracts/manifests/curriculum-lifecycle.module.v1.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 133 | `agents_extensions/shared/prompt-contracts/manifests/curriculum-lifecycle.module.v2.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 134 | `agents_extensions/shared/prompt-contracts/manifests/curriculum-lifecycle.module.v3.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 135 | `agents_extensions/shared/prompt-contracts/profiles/curriculum-lifecycle.v1.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 136 | `agents_extensions/shared/prompt-contracts/registry.v1.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 137 | `agents_extensions/shared/prompts/dynamic-area-epic-fleet-governor.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 138 | `agents_extensions/shared/prompts/hermes-nightly-audit.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 139 | `agents_extensions/shared/protocols/a1-naturalness-scan.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 140 | `agents_extensions/shared/quick-ref/ACTIVITY-SCHEMAS.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 141 | `agents_extensions/shared/quick-ref/FOLK.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 142 | `agents_extensions/shared/quick-ref/LIT.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 143 | `agents_extensions/shared/quick-ref/a1.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 144 | `agents_extensions/shared/quick-ref/a2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 145 | `agents_extensions/shared/quick-ref/b1.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 146 | `agents_extensions/shared/quick-ref/b2-hist.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 147 | `agents_extensions/shared/quick-ref/b2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 148 | `agents_extensions/shared/quick-ref/c1-bio.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 149 | `agents_extensions/shared/quick-ref/c1-hist.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 150 | `agents_extensions/shared/quick-ref/c1.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 151 | `agents_extensions/shared/quick-ref/c2.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 152 | `agents_extensions/shared/quick-ref/error-correction-extended.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 153 | `agents_extensions/shared/quick-ref/literary-rag.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 154 | `agents_extensions/shared/quick-ref/monitor-api.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 155 | `agents_extensions/shared/quick-ref/oes.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 156 | `agents_extensions/shared/quick-ref/philosophy.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 157 | `agents_extensions/shared/quick-ref/ruth.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 158 | `agents_extensions/shared/rules/_load-via-api.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 159 | `agents_extensions/shared/rules/activity-yaml.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 160 | `agents_extensions/shared/rules/cli-help-standard.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 161 | `agents_extensions/shared/rules/core-curriculum.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 162 | `agents_extensions/shared/rules/core-manifest.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 163 | `agents_extensions/shared/rules/core.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 164 | `agents_extensions/shared/rules/critical-rules.md` | `agents_extensions/shared` | **NEUTRALIZED** | Cat A, Cat B: Neutralized ruleset existence disclosure, automerge-ok pipeline labels, and forge posture; restored concrete cancellation instruction |
| 165 | `agents_extensions/shared/rules/delegate-must-use-worktree.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 166 | `agents_extensions/shared/rules/fleet-comms-coordination.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 167 | `agents_extensions/shared/rules/fleet-driver-routing.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 168 | `agents_extensions/shared/rules/mcp-sources-and-dictionaries.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 169 | `agents_extensions/shared/rules/model-assignment.md` | `agents_extensions/shared` | **EVALUATED CONVENTION** | Line 299 references ~/.secrets/openrouter-management.key as standard off-repo local credential path convention |
| 170 | `agents_extensions/shared/rules/non-negotiable-rules.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 171 | `agents_extensions/shared/rules/operator-expectations.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 172 | `agents_extensions/shared/rules/pipeline.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 173 | `agents_extensions/shared/rules/storage-topology.md` | `agents_extensions/shared` | **NEUTRALIZED** | Cat C: Neutralized share names, Drive path, mount path, local cache and mirror maintenance |
| 174 | `agents_extensions/shared/rules/task-scoped-reading.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 175 | `agents_extensions/shared/rules/ukrainian-linguistics.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 176 | `agents_extensions/shared/rules/workflow.md` | `agents_extensions/shared` | **NEUTRALIZED** | Cat A: Neutralized auto-arm-merge.yml and automerge-ok pipeline references |
| 177 | `agents_extensions/shared/skills/apply-plan-fixes/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 178 | `agents_extensions/shared/skills/apply-plan-fixes/apply-plan-fixes-prompt.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 179 | `agents_extensions/shared/skills/batch-review/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 180 | `agents_extensions/shared/skills/build-monitoring/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 181 | `agents_extensions/shared/skills/caveman/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 182 | `agents_extensions/shared/skills/content-review/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 183 | `agents_extensions/shared/skills/content-review/content-review-prompt.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 184 | `agents_extensions/shared/skills/context-budget-audit/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 185 | `agents_extensions/shared/skills/curriculum-lifecycle/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 186 | `agents_extensions/shared/skills/curriculum-lifecycle/agents/openai.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 187 | `agents_extensions/shared/skills/curriculum-preparation/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 188 | `agents_extensions/shared/skills/curriculum-preparation/agents/openai.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 189 | `agents_extensions/shared/skills/drive-epic/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 190 | `agents_extensions/shared/skills/drive-epic/references/epic-specific.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 191 | `agents_extensions/shared/skills/drive-epic/references/handoff.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 192 | `agents_extensions/shared/skills/drive-epic/references/model-deltas.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 193 | `agents_extensions/shared/skills/drive-epic/references/orient.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 194 | `agents_extensions/shared/skills/drive-epic/references/queue-and-capacity.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 195 | `agents_extensions/shared/skills/drive-epic/references/review-merge-cleanup.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 196 | `agents_extensions/shared/skills/drive-epic/references/routing-and-dispatch.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 197 | `agents_extensions/shared/skills/drive-ukrainian-dataset-epic/SKILL.md` | `agents_extensions/shared` | **NEUTRALIZED** | Cat D: Neutralized private operational board citation to paired private tracking surface |
| 198 | `agents_extensions/shared/skills/drive-ukrainian-dataset-epic/references/legacy-v4-contract.md` | `agents_extensions/shared` | **NEUTRALIZED** | Cat D: Neutralized private operational board and tracker citations in identity block and launch prompt |
| 199 | `agents_extensions/shared/skills/entire-context/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 200 | `agents_extensions/shared/skills/entire-context/references/private-native.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 201 | `agents_extensions/shared/skills/local-code-review/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 202 | `agents_extensions/shared/skills/local-code-review/local-code-review-checklist.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 203 | `agents_extensions/shared/skills/plan-review/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 204 | `agents_extensions/shared/skills/plan-review/plan-review-prompt.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 205 | `agents_extensions/shared/skills/plan-review/review-tiers/tier-1-beginner.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 206 | `agents_extensions/shared/skills/plan-review/review-tiers/tier-2-core.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 207 | `agents_extensions/shared/skills/plan-review/review-tiers/tier-3-seminar.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 208 | `agents_extensions/shared/skills/plan-review/review-tiers/tier-4-advanced.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 209 | `agents_extensions/shared/skills/plan-review-seminar/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 210 | `agents_extensions/shared/skills/plan-review-seminar/plan-review-seminar-prompt.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 211 | `agents_extensions/shared/skills/post-build-review/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 212 | `agents_extensions/shared/skills/post-build-review/config/track-policy.v1.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 213 | `agents_extensions/shared/skills/post-build-review/contracts/combined-disposition-policy.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 214 | `agents_extensions/shared/skills/post-build-review/contracts/deterministic-audit-contract.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 215 | `agents_extensions/shared/skills/post-build-review/contracts/evidence-derived-size-policy-contract.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 216 | `agents_extensions/shared/skills/post-build-review/prompts/common-semantic-review-prompt.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 217 | `agents_extensions/shared/skills/post-build-review/prompts/core-semantic-review-prompt.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 218 | `agents_extensions/shared/skills/post-build-review/prompts/seminar-semantic-review-prompt.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 219 | `agents_extensions/shared/skills/prompt-review/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 220 | `agents_extensions/shared/skills/prompt-review/prompt-review-prompt.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 221 | `agents_extensions/shared/skills/prompt-template-review/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 222 | `agents_extensions/shared/skills/prompt-template-review/template-review-checklist.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 223 | `agents_extensions/shared/skills/seminar-content-review/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 224 | `agents_extensions/shared/skills/seminar-content-review/seminar-content-review-prompt.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 225 | `agents_extensions/shared/skills/task-family-manager/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 226 | `agents_extensions/shared/skills/task-family-manager/agents/openai.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 227 | `agents_extensions/shared/skills/task-family-manager/references/archive-cleanup.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 228 | `agents_extensions/shared/skills/task-family-manager/references/manifest.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 229 | `agents_extensions/shared/skills/task-family-manager/references/rename.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 230 | `agents_extensions/shared/skills/task-family-manager/references/restore-receipts.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 231 | `agents_extensions/shared/skills/thread-rollover/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 232 | `agents_extensions/shared/skills/thread-rollover/agents/openai.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 233 | `agents_extensions/shared/skills/thread-rollover/references/archive.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 234 | `agents_extensions/shared/skills/thread-rollover/references/health.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 235 | `agents_extensions/shared/skills/thread-rollover/references/prepare.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 236 | `agents_extensions/shared/skills/thread-rollover/references/resume.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 237 | `agents_extensions/shared/skills/track-completion/SKILL.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 238 | `agents_extensions/shared/skills/track-completion/agents/openai.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 239 | `agents_extensions/shared/skills/track-completion/config/track-completion.v1.yaml` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 240 | `agents_extensions/shared/skills/track-completion/references/awaiting-production-qg-arming.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 241 | `agents_extensions/shared/skills/track-completion/references/blocked-budget-exhausted.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 242 | `agents_extensions/shared/skills/track-completion/references/build-required.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 243 | `agents_extensions/shared/skills/track-completion/references/deployment-required.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 244 | `agents_extensions/shared/skills/track-completion/references/independent-review-required.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 245 | `agents_extensions/shared/skills/track-completion/references/integration-required.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 246 | `agents_extensions/shared/skills/track-completion/references/partial-recovery-required.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 247 | `agents_extensions/shared/skills/track-completion/references/plan-review-required.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 248 | `agents_extensions/shared/skills/track-completion/references/post-build-review-required.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 249 | `agents_extensions/shared/skills/track-completion/references/production-qg-required.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 250 | `agents_extensions/shared/skills/track-completion/references/publish-required.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 251 | `agents_extensions/shared/skills/track-completion/references/repair-required.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 252 | `agents_extensions/shared/skills/track-completion/references/reviewer-instability.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 253 | `agents_extensions/shared/skills/typesafe-ai/SKILL.md` | `agents_extensions/shared` | **EVALUATED CONVENTION** | Lines 32, 36, 56 reference ~/.secrets/typesafe-ai.key as standard off-repo local credential path convention |
| 254 | `agents_extensions/shared/skills/typesafe-ai/UPSTREAM.md` | `agents_extensions/shared` | **CLEAN** | Verified clean across Categories A–D |
| 255 | `docs/runbooks/acp-capability-refusals.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 256 | `docs/runbooks/agent-github-identity.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 257 | `docs/runbooks/agent-seat-onboarding.md` | `docs` | **NEUTRALIZED** | Cat D: Neutralized internal tracker citation to public authorization under #6943 |
| 258 | `docs/runbooks/agy-formal-cf-isolation.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 259 | `docs/runbooks/archived-thread-cleanup.md` | `docs` | **EVALUATED CONVENTION** | Documents standard macOS LaunchAgent plist com.learn-ukrainian.codex-archived-thread-cleanup |
| 260 | `docs/runbooks/atlas-20k-runner-durability.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 261 | `docs/runbooks/atlas-full-reenrich-campaign.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 262 | `docs/runbooks/atlas-job-protocol.md` | `docs` | **NEUTRALIZED** | Cat C: Neutralized hosting provider references |
| 263 | `docs/runbooks/background-session-tasks.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 264 | `docs/runbooks/ci-gate.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 265 | `docs/runbooks/clear-stale-git-lock.md` | `docs` | **NEUTRALIZED** | Cat C: Removed absolute local host path with username |
| 266 | `docs/runbooks/codex-hooks.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 267 | `docs/runbooks/codex-rollout-state.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 268 | `docs/runbooks/cursor-driver.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 269 | `docs/runbooks/data-backup.md` | `docs` | **NEUTRALIZED** | Cat C: Neutralized cloud provider desktop sync mount name, lu-gdrive remote, OAuth renewal details, and scheduled job label |
| 270 | `docs/runbooks/driver-cold-start-board.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 271 | `docs/runbooks/entire-context-handoff-dualwrite.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 272 | `docs/runbooks/epic-orchestrator-roster.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 273 | `docs/runbooks/epic-stream-handoff.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 274 | `docs/runbooks/fleet-comms-open-gaps.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 275 | `docs/runbooks/formal-review-attempt-isolation.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 276 | `docs/runbooks/gemini-orchestrator.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 277 | `docs/runbooks/grok-bot-qa-observer.md` | `docs` | **NEUTRALIZED** | Cat D: Neutralized internal tracking issue citation from line 79 to paired private tracking issues |
| 278 | `docs/runbooks/grok-formal-cf-isolation.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 279 | `docs/runbooks/grok-hook-profile.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 280 | `docs/runbooks/grok-session-canary.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 281 | `docs/runbooks/home-session-inventory.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 282 | `docs/runbooks/hramatka-driver-queue.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 283 | `docs/runbooks/judge-calibration-matrix-runbook.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 284 | `docs/runbooks/kimi-formal-cf-isolation.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 285 | `docs/runbooks/kimi-orchestrator.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 286 | `docs/runbooks/launchd-inventory.md` | `docs` | **EVALUATED CONVENTION** | Line 44 references ~/.secrets/ and documents standard macOS LaunchAgent plists (com.learn-ukrainian.*) |
| 287 | `docs/runbooks/module-build-token-telemetry.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 288 | `docs/runbooks/module-quality-gates.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 289 | `docs/runbooks/post-build-review.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 290 | `docs/runbooks/project-state-reporter.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 291 | `docs/runbooks/pronunciation-audio.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 292 | `docs/runbooks/recovery.md` | `docs` | **EVALUATED CONVENTION** | Line 172 references ~/.secrets/ and com.learn-ukrainian.backup as standard host-managed LaunchAgent label |
| 293 | `docs/runbooks/secret-scanning.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 294 | `docs/runbooks/session-streams-monitor-api.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 295 | `docs/runbooks/session-supervisor.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 296 | `docs/runbooks/sibling-git.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 297 | `docs/runbooks/stem-textbook-incremental-ingest.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 298 | `docs/runbooks/storage-topology.md` | `docs` | **NEUTRALIZED** | Cat C: Neutralized NTFS share name Get-SmbShare -Name UkrainianData, Drive path, listener counts, systemd dropins, cache and mirror maintenance |
| 299 | `docs/runbooks/teacher-curated-seed-rebuild.md` | `docs` | **NEUTRALIZED** | Cat C: Neutralized concrete Drive recovery and curriculum paths |
| 300 | `docs/runbooks/ukrainian-data-foundry-clean-ukrainian-recipe.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 301 | `docs/runbooks/ukrainian-data-foundry-consumer-quickstart.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 302 | `docs/runbooks/ukrainian-data-foundry-corpus-admission.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 303 | `docs/runbooks/ukrainian-data-foundry-correction-factory.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 304 | `docs/runbooks/ukrainian-data-foundry-language-contact-detector.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 305 | `docs/runbooks/ukrainian-data-foundry-model-views.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 306 | `docs/runbooks/ukrainian-data-foundry-reference-build.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 307 | `docs/runbooks/ukrainian-data-foundry-treatment.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 308 | `docs/runbooks/wiki-rebuild.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 309 | `docs/runbooks/word-atlas-entry-model-census.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 310 | `docs/runbooks/word-atlas-entry-model.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 311 | `docs/runbooks/word-atlas-ohoiko-ulp-source-scope.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 312 | `docs/runbooks/word-atlas-private-teacher-source-scope.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 313 | `docs/runbooks/word-atlas-source-census-planning.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 314 | `docs/runbooks/word-atlas-source-entry-count.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 315 | `docs/runbooks/word-atlas-source-inventory-review-candidates.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 316 | `docs/runbooks/word-atlas-static-api.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 317 | `docs/runbooks/word-atlas-textbook-source-scope.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 318 | `docs/runbooks/worktree-cleanup.md` | `docs` | **EVALUATED CONVENTION** | Documents standard macOS LaunchAgent plist com.learn-ukrainian.worktree-cleanup |
| 319 | `docs/best-practices/activity-pedagogy.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 320 | `docs/best-practices/adr-management.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 321 | `docs/best-practices/agent-activity-matrix.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 322 | `docs/best-practices/agent-bridge.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 323 | `docs/best-practices/agent-cooperation.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 324 | `docs/best-practices/api-ui-improvements-proposal.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 325 | `docs/best-practices/atlas-source-presentation.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 326 | `docs/best-practices/audit-standards.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 327 | `docs/best-practices/b2-c2-plan-architecture.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 328 | `docs/best-practices/bio-image-rights.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 329 | `docs/best-practices/bio-naming-canonical.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 330 | `docs/best-practices/bio-research-source-tiers.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 331 | `docs/best-practices/ci-health.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 332 | `docs/best-practices/code-quality.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 333 | `docs/best-practices/codex-thread-handoff.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 334 | `docs/best-practices/context-engineering.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 335 | `docs/best-practices/decision-journal.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 336 | `docs/best-practices/derivational-morphology-gate.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 337 | `docs/best-practices/deterministic-over-hallucination.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 338 | `docs/best-practices/dialogue-situations.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 339 | `docs/best-practices/dual-mode-design-tokens.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 340 | `docs/best-practices/fleet-role-scorecard.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 341 | `docs/best-practices/fleet-shared-doctrine.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 342 | `docs/best-practices/force-flag-audit-2026-04-22.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 343 | `docs/best-practices/git-hygiene.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 344 | `docs/best-practices/gitflow.md` | `docs` | **NEUTRALIZED** | Cat B, Cat A: Neutralized GitHub UI ruleset assertions, signed commit status, private repo 403 API disclosures; corrected pre-tool merge guard checks |
| 345 | `docs/best-practices/guardrail-lifecycle.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 346 | `docs/best-practices/harness-engineering.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 347 | `docs/best-practices/heritage-attestation-engine.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 348 | `docs/best-practices/hermes-usage.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 349 | `docs/best-practices/hook-audit.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 350 | `docs/best-practices/issue-tracking.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 351 | `docs/best-practices/lesson-schema.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 352 | `docs/best-practices/local-api-server.md` | `docs` | **EVALUATED CONVENTION** | Documents standard macOS LaunchAgent plist com.learn-ukrainian.monitor-api |
| 353 | `docs/best-practices/local-ci-replay.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 354 | `docs/best-practices/module-content-quality.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 355 | `docs/best-practices/openai-compat-proxy.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 356 | `docs/best-practices/pipeline/v7-build-preservation.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 357 | `docs/best-practices/pipeline/writer-bakeoff-methodology.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 358 | `docs/best-practices/plan-references.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 359 | `docs/best-practices/plan-version-drift.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 360 | `docs/best-practices/politically-charged-bios.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 361 | `docs/best-practices/postmortem-management.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 362 | `docs/best-practices/pr-issue-references.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 363 | `docs/best-practices/prompt-engineering.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 364 | `docs/best-practices/seminar-reading-links.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 365 | `docs/best-practices/strict-reviewer-persona.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 366 | `docs/best-practices/task-quality.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 367 | `docs/best-practices/track-architecture.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 368 | `docs/best-practices/typesafe-jev.md` | `docs` | **EVALUATED CONVENTION** | Lines 22, 25 reference ~/.secrets/typesafe-ai.key as standard off-repo local credential path convention |
| 369 | `docs/best-practices/ulp-presentation-pattern.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 370 | `docs/best-practices/universal-rules-registry.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 371 | `docs/best-practices/v7-design-and-corpus.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 372 | `docs/best-practices/vocabulary-activity-standards.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 373 | `docs/best-practices/wiki-plan-review-and-lock.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 374 | `docs/best-practices/word-atlas-design.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
| 375 | `docs/best-practices/writer-prompt-appendix.md` | `docs` | **CLEAN** | Verified clean across Categories A–D |
