# Advisory: Gemini epic-driver role and compaction recovery

## Failure modes and evidence

1. **The standing persona conflicts with the assigned lease.** `GEMINI.md:56-57` calls Gemini only a content builder and assigns infrastructure to Claude, while `GEMINI.md:66` already gives an orchestrator merge duty. `GEMINI.md:212-214` again assumes Claude is the orchestrator. An assigned Gemini driver can therefore regress toward worker behavior after losing recent context. This is a prompt conflict; the frequency and exact mechanism of observed regressions need a controlled post-compaction trial.
2. **The startup seed names the skill but not the role.** `launcher_bind_drive_epic` in `scripts/lib/launcher_core.sh:1026-1045` claims that the launcher owns the lease, points at `drive-epic`, and requests cross-family review. It does not explicitly tell Gemini that it is accountable for the whole stream or to reconstruct live queue state after compaction. The AGY launcher correctly passes the seed once with `-i` (`scripts/launchers/gemini.sh:9-29`); that startup injection alone does not prove the text remains salient after compaction.
3. **The supplied background brief is historical, not a live ledger.** `batch_state/briefs/gemini_orchestration_advisory.md` was available as read-only input in the primary checkout, but absent from this worktree. Its issue/PR statuses, fixed model roster, and “fixes applied” language were not reverified. Do not copy those statuses or pins into standing prompts. The existing `drive-epic` skill already supplies the stream-scoped issue cycle, live routing, exact-head cross-family review, merge order, canary, handoff, and cleanup procedure.
4. **A naïve global seed would affect other seats.** All public drivers use the same `LC_DRIVER_PROMPT` assignment. A Gemini-specific sentence belongs behind the provider/harness condition, while the shared prompt and its Work API and QA-observer wording stay intact. No worker dispatch should inherit a driver identity from the AGY runtime adapter.

## Proposed minimal patch

These are proposed source diffs, **not changes applied by this advisory**. Line numbers refer to this worktree's current head. Apply them in a follow-up implementation with the normal exact-head review and CI gates.

### `GEMINI.md` — replace lines 56-57 and 212-214

```diff
@@ GEMINI.md:56-57 @@
 ## Your Role
-You are **Gemini (Yellow Team)** — the content builder. You research, write content, and create activities. Claude (Blue Team) reviews work and maintains infrastructure. **An LLM must NEVER review its own work as an approval gate.** If Claude is unavailable, use another independent non-Codex review route from `AGENTS.md`; do not substitute self-review.
+You are **Gemini (Yellow Team)**. On curriculum authoring assignments, research, write content, and create activities. When a launcher assigns you an epic with a verified, live stream lease, you are that stream's **accountable driver**: inventory and disposition its issues, coordinate bounded workers, obtain independent cross-family exact-head review, verify required CI, merge or enqueue approved green PRs that belong to your stream, and complete issue and worktree/branch cleanup. The current assignment and verified lease determine which role applies; no provider is the permanent orchestrator. Never treat your own review as an approval gate. Follow `AGENTS.md` and `drive-epic` for routing and landing details.
+
+### Driver recovery after context compaction
+If you are an assigned epic driver, re-ground on cold start and after every compaction. Re-read `agents_extensions/shared/skills/drive-epic/SKILL.md` and the current handoff. Verify `SESSION_EPIC`, this session's launcher-owned stream lease, and the Gemini canary/hydration result; continue only when the current capsule permits execution. Check Fleet Comms with `plane-status`, stream-scoped open issues using `gh issue list` plus the issue-to-stream registry, owned open PRs with `gh pr list` and `gh pr checks <N>`, and running tasks with `scripts/delegate.py list --status running`. Query live fleet capacity before new dispatch. Reconcile each open stream issue to in-flight work, dispatch, a named hold, or verified completion; continue the `drive-epic` loop through merge and hygiene. Treat a missing or conflicting lease, stream membership, or hydration signal as unknown and stop consequential stream actions until resolved. Do not claim, renew, or release the launcher-owned lease yourself. The static content-builder description does not override an active, verified driver assignment; all repository hard gates still apply.
@@ GEMINI.md:212-214 @@
-**When the orchestrator (Claude) emits a `## DECISION REQUIRED — ...` block, that's a Decision Card** routed to inline chat / `docs/decisions/pending/` / GH issue. Don't try to resolve it on Gemini's side.
+**When the accountable orchestrator emits a `## DECISION REQUIRED — ...` block, that is a Decision Card** routed to inline chat / `docs/decisions/pending/` / GH issue. Do not resolve it solely as a discussion participant; an assigned driver records and routes it under the operator/advisor approval rule.
-**High-risk-track override:** On sensitive tracks (FOLK, HIST, BIO, ISTORIO, LIT, OES, RUTH), an `[AGREE]` consensus is suspect due to shared training-data biases. The orchestrator will override consensus by either force-emitting a Decision Card or injecting domain-specific bias checklists to provoke adversarial review.
+**High-risk-track override:** On sensitive tracks (FOLK, HIST, BIO, ISTORIO, LIT, OES, RUTH), an `[AGREE]` consensus is suspect due to shared training-data biases. The accountable orchestrator must seek adversarial, domain-specific evidence and route any unresolved decision through the Decision Card process.
```

**Rationale:** Role selection follows a verified assignment, without changing curriculum authoring. The recovery paragraph points to existing methods and live authorities instead of duplicating a mutable fleet roster. `gh issue list` is only an inventory input; `/api/issues/streams` membership remains authoritative and fail-closed for stream ownership. The canary/hydration gate comes from `scripts/session_canary/gemini_lane.py:66-84,197-207`; a prompt cannot substitute for it. The two deliberation lines no longer imply that Claude always owns orchestration.

### `scripts/lib/launcher_core.sh` — add after line 1041

```diff
@@ launcher_bind_drive_epic() @@
   LC_DRIVER_PROMPT="Load agents_extensions/shared/skills/drive-epic/SKILL.md before acting. The launcher already claimed the ${LC_EPIC} lease and ran its provider canary; do not claim, renew, or reopen the lease. ${fleet_clause} Consult the Work API projection (http://127.0.0.1:8765/api/work/v1/projection) for orientation and treat grok-bot QA-observer issues as a queue input — the skill covers both. Obtain independent cross-family review."
+  if [ "$LC_PROVIDER" = gemini ] && [ "$LC_HARNESS" = agy ]; then
+    LC_DRIVER_PROMPT+=" You are the accountable driver for the verified ${LC_EPIC} stream lease, including issue disposition, worker coordination, exact-head cross-family review, CI, merge, and cleanup. After context compaction, use GEMINI.md's driver-recovery checklist and drive-epic to recheck the launcher-owned lease, Gemini hydration permission, stream issue/PR queue, and live fleet state before continuing. Never infer authority or completion from a compacted summary."
+  fi
   launcher_inject_driver_agent
```

**Rationale:** The shared seed retains its current contract and its one-line Work API test. The new branch applies only to the validated Gemini/AGY driver route (`scripts/lib/launcher_core.sh:1065-1081,1123-1134` and `scripts/launchers/gemini.sh:3`). The seed repeats only the identity and recovery trigger; the standing file contains the procedure. `LC_HARNESS=agy` alone should not confer driver authority on an unrelated process. Ordinary `start-gemini.sh` does not call this binding function.

### `tests/test_start_gemini_launcher.py` — add after line 90

```diff
@@ after test_gemini_driver_passes_binding_via_agy_interactive_flag @@
+def test_gemini_driver_seed_names_accountability_and_compaction_recovery() -> None:
+    driver = run_launcher("start-gemini-driver.sh", "--epic", "devops")
+    assert driver.returncode == 0, driver.stderr
+    exec_line = _would_exec_line(driver.stdout)
+    _assert_drive_epic_uses_agy_interactive_flag(exec_line)
+    assert "accountable\\ driver" in exec_line
+    assert "After\\ context\\ compaction" in exec_line
+    assert "Gemini\\ hydration\\ permission" in exec_line
+
+    interactive = run_launcher("start-gemini.sh")
+    assert interactive.returncode == 0, interactive.stderr
+    assert "After\\ context\\ compaction" not in _would_exec_line(interactive.stdout)
```

**Rationale:** The existing dry-run helper exercises actual shell argument construction, so this checks that AGY receives the seed once through `-i` and ordinary interactive sessions remain unmodified. Escaped spaces follow `printf '%q'` in `scripts/launchers/gemini.sh:28`. Keep `tests/test_driver_work_api_onboarding.py` unchanged; its original shared prompt assertion guards the Work API pointer.

### Deliberate no-change files

- **`scripts/launchers/gemini.sh:9-29`: no diff.** It already passes `LC_DRIVER_PROMPT` through `agy -i` exactly once, filters the duplicate positional argument, and preserves interactive TUI mode. Reworking that path risks duplicate or non-interactive prompting without adding post-compaction durability.
- **`scripts/agent_runtime/adapters/agy.py:245-390`: no diff.** This is the headless `agy -p` worker/review adapter, with a prompt supplied per task. Giving every AGY invocation an epic-driver persona would contaminate workers and reviews. It is not the interactive driver's compaction hook.
- **`scripts/check_rules_deployment.sh` and `scripts/lib/deploy_extensions.sh`: no diff.** The former compares managed `.gemini` mirrors to `gemini_extensions`/shared sources, not root `GEMINI.md`; the latter deploys extensions at launch. `GEMINI.md` is a tracked root file, so there is no mirror to sync for this proposed edit. Do not hand-edit `.gemini/`.
- **`agents_extensions/shared/skills/drive-epic/SKILL.md`: no diff.** It already defines the epic issue cycle, canary, review/CI order, merge, and cleanup. A Gemini-only reminder belongs in Gemini's root context and launcher branch.

## Verification for the follow-up implementation

1. Inspect the exact diff for Gemini-only scope and confirm root `GEMINI.md` remains tracked: `git diff --check`, `git diff -- GEMINI.md scripts/lib/launcher_core.sh tests/test_start_gemini_launcher.py`, and `git ls-files GEMINI.md`.
2. Run shell syntax and focused tests from the implementation worktree with the shared interpreter: `bash -n scripts/lib/launcher_core.sh scripts/launchers/gemini.sh`; `/home/ops/learn-ukrainian/.venv/bin/python -m pytest -q tests/test_start_gemini_launcher.py tests/test_driver_work_api_onboarding.py tests/test_fleet_comms_launcher_awareness.py`. The same head must pass required CI after cross-family review.
3. In a dry-run of `start-gemini-driver.sh --epic <approved-selector>`, verify AGY argv has exactly one `-i` seed, includes the driver and compaction text, and still shows the lease/canary sequence. Verify `start-gemini.sh` has no driver seed. No production lease or paid provider call is needed for this check.
4. A separate **live, controlled** Gemini driver trial must validate actual post-compaction behavior. After a real compact, confirm it re-reads the handoff and skill, verifies the exact launcher-owned lease and canary `execution_allowed`, obtains a stream-scoped issue/PR inventory and current checks, and either advances one authorized item or emits a named hold. Missing authority must stop consequential actions. This is behavioral evidence, beyond unit-test proof.
5. `scripts/check_rules_deployment.sh --tracked-mirrors-only` should stay green. If later work changes canonical `agents_extensions` or `gemini_extensions`, deploy from those sources and run `npm run agents:deploy` followed by `scripts/check_rules_deployment.sh`; do not copy text into deployed mirrors manually.

## Risks and limits

- **Prompt salience is not a compaction hook.** The seed is delivered at session start; this patch cannot prove AGY replays it after compaction. The standing `GEMINI.md` paragraph and canary/hydration flow supply a recoverable anchor. If the live trial still drifts, investigate an AGY-supported post-compaction mechanism with a new scoped design and test; do not silently add a global adapter injection.
- **Authority must remain live.** A retained `SESSION_EPIC` string or the background brief alone cannot prove a lease. Missing Monitor/Fleet evidence is unknown, and stale or conflicting authority blocks dispatch and merge. The driver never manipulates the launcher-owned lease manually.
- **Merge ownership stays stream-scoped.** `gh issue list` and `gh pr list` may include other streams; reconcile each item through the issue-to-epic membership registry before review routing or merging. A green check is insufficient without exact-head independent cross-family approval; the branch head must match both gates.
- **Non-Gemini behavior stays unchanged by the proposed shell condition.** Curriculum-only Gemini sessions retain the content-builder role, and headless AGY workers retain their task prompts. Any actual behavioral change requires the tests and live trial above.

**Advisory disposition:** The smallest coherent implementation is the two Gemini persona locations, one provider-gated launcher append, and one focused launcher regression test. No adapter or deployment-script change is justified by the current evidence. This report makes no claim that epic #6321's current issues or PRs are complete.
