# Epic-specific rules (drive-epic §0c, §0d)

Read before the first action on the named epic. Other epics skip this file.

## §0c. Hramatka epic — dual-repo queue (epic #4542 only)

If `SESSION_EPIC` is Hramatka (public #4542), the priority/ownership queue is
private BOARD `learn-ukrainian-infra-private#349`, not the public epic body. Cold-start
read order: **private #349 → private open PRs → public PRs linked from #4542 only.**
Public #4542 is charter + bare pointer — never generate or mirror a public checklist
from the private board (leak + dual-write). GitHub issue/PR state in either repo
remains the factual SSOT for open/closed; #349 is the priority queue, not a duplicate
status feed. If #349 and any other queue view disagree, **#349 wins** — correct the other
view the same session. Full contract: `docs/runbooks/hramatka-driver-queue.md`.

Before a new dispatch, scope, or PR, run `scripts.fleet.hramatka_scope_gate`
as specified in that runbook; only `ALLOW` permits the new action.

Before declaring a Hramatka handoff verified-clean, run
`.venv/bin/python -m scripts.fleet.hramatka_hygiene_check` — only exit 0 is a pass;
exit 2 (`unknown`, GitHub unreachable) is never a clean handoff either.

**Host actions on the Hramatka host** follow operator-expectations item 10 and the
§7-rollout table in `review-merge-cleanup.md`:

- **Routine maintenance is driver work, done then reported**, including sudo where the
  host requires it: pull merged `main`; restart an updated or broken service (system or
  user unit) after checking no active dispatch depends on it; install or enable a reviewed
  systemd unit or timer that lives in the repo; clean agent-generated caches, logs, and
  worktrees; install OS packages a reviewed repo change needs.
- **A production release rollover** on the live-serving host (running
  `hramatka/ops/deploy.sh` or anything that swaps live `/opt/hramatka/current`, including
  rebuilding or swapping the read-only release checkout — private #360 class) is a
  **production cutover** and needs a present-tense operator GO for that rollover; a GO
  recorded on an earlier or closed issue does not count. The private deploy runbook
  (including the sudo steps inside it) applies only after that GO; without it the rollover
  stays **ESCALATE**.
- **Host access and security configuration stays operator-only (ESCALATE, not solo)** —
  sshd configuration (e.g. `PermitRootLogin`), sudoers, user accounts, SSH keys and other
  credentials, and firewall changes that could cut off operator access — because of
  lock-out risk and because accounts/credentials are an operator stop condition.

## §0d. Core fresh lesson-based build (epic #7994, sub-epic #8397)

A1–B2 core modules are built fresh from new lesson plans by the fresh-build engine;
`--upgrade` is abandoned (`docs/epics/fresh-build-requirements.md` §1). Same
`$drive-epic` loop — **not** a second driver skill, and **not** `$track-completion`.

Read first: [`docs/epics/fresh-build-build-program.md`](../../../../../docs/epics/fresh-build-build-program.md)
(§1–§3, §5, §6), then the requirements, plan schema, writer contract and review
contracts as the phase needs. Seats live in `model-assignment.md` (Ukrainian
content authoring row) — do not freeze a roster here.

**Done** is the learner URL on the level's track (`/<level>/<slug>/`, e.g. `/a1/<slug>/`), with Pages only
on present-tense operator GO (§7-rollout), and the LU QA sweep triaged (build
program §5 step 10). Engine-on-`main` and gates green in a worktree are **not**
done.

Binding for this lane:

1. **Nothing typed**: every Ukrainian string is a tool copy or the writer's
   resolved text; a defect is fixed at its layer (plan, pack, word store, prompt,
   gate or code), never by hand-editing a lesson or a generated file (R-12, R-35).
2. A module has as many lessons as its content needs (R-02). The arc's
   `est_lessons` is an estimate, never a target; nobody pads or squeezes a module.
3. The plan fixes each lesson's activities (count, type, placement); the writer
   cannot add or change them. Activity volume, correctness and workbook variety
   are acceptance criteria (teacher feedback, operator 2026-09-27).
4. The **driver does not decide Ukrainian**; the sources override any model
   (R-35). Language work and its reviews go only to sanctioned language lanes,
   cross-family to the author; Gemini seats review Ukrainian only, never code.
   If an AGY run ends `agy_background_task_canceled` (#8771), retry once, then
   reroute.
5. Review at scale is automated (review tooling WP 14–16, LU QA sweep); the
   operator reviews the pilot module and spot-checks after it (2026-09-27).
6. Content PRs are **scripts-free**. While CF/CI runs on unit N, prepare N+1.
   After gates pass in a worktree, **open the PR the same session**.
