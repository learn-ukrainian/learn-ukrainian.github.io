# Layered-Harness Audit — Push Advisory Rules Down to the Enforcement Layer

**Issue:** #1908
**Date:** 2026-05-17
**Branch:** `claude/harness-layered-audit-2026-05-17`
**Mode:** Read-only (no code changes in this PR; recommendations only)
**Auditor:** Claude (orchestrator-inline, this session)

---

## 0. TL;DR

Layer-3 (hard enforcement) is almost empty. We have **8 hooks** (one rewriter, seven informational/telemetry) and **zero `deny` permission rules** in `claude_extensions/settings.json` — only four `ask` rules. The advisory layer has accumulated **25+ `NEVER`/`MUST`/HARD-RULE** items across `MEMORY.md`, `claude_extensions/rules/*.md`, and `CLAUDE.md`. Every one of them is text the model has to remember to obey.

The asymmetry is the bug. Adding even a few cheap pre-bash `deny` hooks would convert recurring soft-rule violations (#M-7 pytest, #M-5 secrets, #M-0.5 admin-merge bypass) into mechanical blocks that the model literally cannot violate.

**Top 3 to ship in a follow-up PR (ordered by leverage/cost):**

1. **`block-dangerous-git-flags.sh`** — deny `git commit --no-verify`, `--no-gpg-sign`, and `git push --force* origin main`. ~25 LOC, zero false-positive risk, plugs three documented incidents.
2. **`pytest-before-push.sh`** — PreToolUse on `git push`: if staged diff touches `*.py` / `tests/**` / `claude_extensions/rules/**` AND `/tmp/learn-uk-pytest-ok.<branch>` is older than 5 min OR missing, deny. Plugs #M-7 (encoded 2026-05-12, violated 2026-05-13 — one week shelf life).
3. **`admin-merge-guard.sh`** — PreToolUse on `gh pr merge --admin`: probe `gh pr checks <N> --json` first; deny if any non-advisory check is `FAILURE`. Plugs #M-0.5 (PR #1813 incident).

These three are sufficient evidence that the layered-harness approach works at low cost. Five more candidates (`sys.executable` write-guard, V7-build `--worktree` enforcement, services.sh-restart wrapper, "no `delegate.py --agent claude` after 2026-06-15," `.claude/` write-deny) are documented below and recommended as a second sprint after the first three are validated.

**Not enforceable:** ~10 rules in MEMORY are genuinely judgment-dependent (M-4 deterministic-over-hallucination, M-6 drive-the-project, M-1 direct-order-obedience, M-2 HTML/MD flow, M-3 ask-about-colleague-tools, #0A push-back-on-unclear-instructions, #0I don't-stack-dilemmas, #0H merging-PRs-is-my-job, #1 quality-above-all, #M-6a /goal-status-lines). These stay in layer 2.

---

## 1. Current state inventory

### 1.1 Hooks (`claude_extensions/hooks/`)

| Hook | Event | What it does | Enforcement type |
|---|---|---|---|
| `session-setup.sh` | SessionStart | Reports env issues, drift, ADR/postmortem hygiene, handoff pointer | **Informational** |
| `enforce-venv.sh` | PreToolUse (Bash) | Rewrites bare `python3`/`python` → `.venv/bin/python` | **Rewrite** (silent) |
| `tool-timing.sh` | PostToolUse + Failure | Posts tool duration telemetry to Monitor API | **Telemetry** |
| `context-monitor.sh` | PostToolUse | Tiered warnings at 75/85/95% of autoCompactWindow | **Informational** |
| `post-compact.sh` | PostCompact | Re-injects in-progress modules, open issues, key reminders | **Informational** |
| `check-gemini-inbox.sh` | UserPromptSubmit | Queries broker DB for unread Gemini messages | **Informational** |
| `auto-audit.sh` | FileChanged (curriculum) | Runs `audit_module.py` on changed .md files | **Informational** |
| `auto-deploy-claude-extensions.sh` | FileChanged (claude_extensions) | Runs `npm run claude:deploy` | **Side-effect** (idempotent) |

**Observation:** Of 8 hooks, only `enforce-venv.sh` mutates a tool call. None deny. None block. Layer 3 is almost entirely watching, not enforcing.

### 1.2 Permission rules (`claude_extensions/settings.json`)

Counted via `jq` of the file (lines 1–625):

| Permission | Count | Notes |
|---|---|---|
| `allow` (bash) | 79 | Broad allow-list (npm, git \*, gh \*, sed, awk, curl, …) |
| `ask` | 4 | `git push *`, `gh * create *`, write to `.claude/**`, edit `.claude/settings.json` |
| `deny` | **0** | — |

`mcp` and `webfetch`/`websearch` are `allow *`. There is no deny rule anywhere in the canonical settings.

### 1.3 Advisory-text rule corpus (layer 2)

Source files containing `NEVER`/`MUST`/HARD RULE/CRITICAL markers:

| File | Approx rule count | Format |
|---|---|---|
| `~/.claude/projects/.../memory/MEMORY.md` | 20 (#M-9 … #2) | Numbered hard-rules |
| `claude_extensions/rules/critical-rules.md` | 7 | Numbered NEVER/ALWAYS |
| `claude_extensions/rules/non-negotiable-rules.md` | 11 sections | Critical-tagged |
| `claude_extensions/rules/delegate-must-use-worktree.md` | 1 (the rule) + 5 sub-rules | Critical-tagged |
| `claude_extensions/rules/model-assignment.md` | 1 table | Critical-tagged |
| `claude_extensions/rules/pipeline.md` | ~5 | Critical-tagged |
| `claude_extensions/rules/goal-driven-runs.md` | ~6 | Critical-tagged |
| `claude_extensions/rules/workflow.md` | ~15 | Critical-tagged |
| `claude_extensions/agents/curriculum-orchestrator.md` | 1 (no-ritual-restart line) | Inline |
| `CLAUDE.md` (project) | ~12 | Top-of-file admonitions |

**Total:** ~80 `NEVER`/`MUST` admonitions, ~0 are enforced at layer 3.

---

## 2. Rule-to-enforcement mapping

For each advisory rule that the issue or my own audit flagged as plausibly enforceable, I've classified it as:

- **(a)** Enforceable via hook + permission deny (ship-able)
- **(b)** Enforceable via tool-config (e.g. wrapping a script, requiring an env var)
- **(c)** Genuinely advisory (judgment-dependent; layer-3 enforcement would create unacceptable false positives)

### 2.1 Master table

| # | Rule (source) | Class | Hook design sketch | Feasibility | False-pos risk | Est LOC | Override |
|---|---|---|---|---|---|---|---|
| 1 | `git commit --no-verify` / `--no-gpg-sign` (CLAUDE-system, #M-0.5 sibling) | (a) | PreToolUse(Bash) regex; hard deny | **HIGH** | **LOW** | 25 | None — user-only territory |
| 2 | `git push -f origin main` / `--force-with-lease ... main` (CLAUDE-system) | (a) | PreToolUse(Bash) regex; hard deny | **HIGH** | **LOW** | 15 | None — never legitimate for an agent |
| 3 | #M-7 pytest-before-push | (a) | PreToolUse(Bash) on `git push`; check stamp `/tmp/learn-uk-pytest-ok.<branch>` mtime + staged diff filter | **HIGH** | **LOW** | 80 | `LEARN_UK_PYTEST_SKIP=1` for docs-only pushes |
| 4 | #M-0.5 admin-merge guard | (a) | PreToolUse(Bash) on `gh pr merge --admin`; run `gh pr checks <N> --json`; deny on any non-advisory FAILURE | **HIGH** | **LOW** | 60 | Explicit user override only (env var) |
| 5 | #M-5 don't print secrets — `env`/`printenv`/`set` w/o key-only filter | (a)/(b) | PreToolUse(Bash); regex-detect raw `env`/`printenv`/`set` with no `cut`/`awk`/`grep -v`; auto-rewrite to `env \| cut -d= -f1` OR deny | **MEDIUM** | **MEDIUM** (legit `env -i …`, sourcing scripts) | 100 | `LEARN_UK_SECRETS_OK=1` |
| 6 | #M-5 don't print secrets — `grep .env*` / `cat ~/.aws/credentials` | (a) | PreToolUse(Bash); regex-detect; auto-rewrite to `grep ... \| cut -d= -f1` | **HIGH** | **LOW** | 40 | `LEARN_UK_SECRETS_OK=1` |
| 7 | V7 build must use `--worktree` (pipeline.md, CLAUDE.md "BUILDS" line) | (a) | PreToolUse(Bash) on `v7_build.py` invocation; deny if `--worktree` missing | **HIGH** | **VERY LOW** | 30 | None — `--worktree` is always correct |
| 8 | No `sys.executable` in new Python | (a) | PreToolUse(Write/Edit) on `*.py`; scan `content`/`new_string` for `sys.executable` introduction; deny | **MEDIUM** | **LOW** | 60 | `# noqa: VENV` directive on the line |
| 9 | "Don't edit `.claude/` directly" (critical-rules #1) | (b) | Already `ask`; tighten to `deny` for non-`settings.local.json` paths | **HIGH** | **VERY LOW** | 0 (config only) | `ask` for `.claude/settings.local.json` (already exempt) |
| 10 | Services-restart-ritual ("Don't restart all services as a session-start ritual" — curriculum-orchestrator.md L86) | (a) | PreToolUse(Bash) on `./services.sh restart` w/o arg; require explicit service name OR `LEARN_UK_RESTART_ALL=1` | **HIGH** | **LOW** | 25 | `LEARN_UK_RESTART_ALL=1` |
| 11 | No `delegate.py --agent claude` after 2026-06-15 (#M0 calendar rule) | (a) | PreToolUse(Bash) on `delegate.py.*--agent claude`; date-check; deny after cutoff | **HIGH** | **LOW** | 30 | Explicit override env (rare) |
| 12 | Delegated work MUST use worktree (`delegate-must-use-worktree.md`) | (a)/(b) | PreToolUse(Bash) on `git checkout -b`/`git switch -c` when CWD is project root (not a `.worktrees/...` subtree); deny | **MEDIUM** | **MEDIUM** (legit emergency-branch in main checkout exists) | 50 | `LEARN_UK_MAIN_BRANCH=1` |
| 13 | `.python-version` / `.yamllint` / `.markdownlint.json` immutability | (b) | settings.json `deny` for edit/write on those paths | **HIGH** | **VERY LOW** | 0 (config only) | `LEARN_UK_CONFIG_EDIT=1` (env-gated allow rule) |
| 14 | X-Agent commit trailer required (`delegate-must-use-worktree.md` final section) | (a) | PreToolUse(Bash) on `git commit`; if message doesn't have `--trailer X-Agent:`, inject it or warn | **MEDIUM** | **MEDIUM** (user-initiated commits shouldn't get auto-trailer) | 50 | Off by default for orchestrator-inline (already named) |
| 15 | `/compact`, `--resume`, `--continue` (claude CLI flags on parent) | (c) | N/A — hooks run inside Claude Code; cannot intercept parent CLI flags | LOW | — | — | — |
| 16 | #M-9 local fanout one-at-a-time (OCR/ffmpeg/pytest workers) | (c)/(a) | PreToolUse(Bash) inspecting `pgrep` of running OCR/ffmpeg before allowing another launch — complex, fragile | LOW | HIGH | 150+ | Not recommended |
| 17 | #M-4 deterministic-over-hallucination | (c) | No mechanical signal for "model is about to hallucinate" | — | — | — | — |
| 18 | #M-6 drive-the-project / #0A push-back / #0I don't-stack-dilemmas | (c) | Conversational behavior; no tool-call signal | — | — | — | — |
| 19 | #M-1 direct-order-obedience / #M-3 ask-don't-assume-colleagues | (c) | Conversational | — | — | — | — |
| 20 | #M-2 HTML/MD by flow direction | (c) | Could lint-on-write but creative judgment about flow direction makes it noisy | — | — | — | — |
| 21 | #0B use Monitor tool (vs ScheduleWakeup polling) | (c)/(a) | Could detect ScheduleWakeup loops with same prompt — fragile heuristic | LOW | HIGH | — | — |
| 22 | #M-6a `/goal` status-line tokens | (c) | Output linting per turn — not a tool-call hook surface | LOW | — | — | — |

### 2.2 Counts

- **Class (a) enforceable, recommended:** items 1, 2, 3, 4, 6, 7, 8, 10, 11 — **9 hooks**
- **Class (a)/(b) borderline:** items 5, 9, 12, 13, 14 — **5 items** (most are cheap config tweaks or have meaningful false-positive risk worth piloting first)
- **Class (c) genuinely advisory:** items 15, 16, 17, 18, 19, 20, 21, 22 — **8+ items**

The advisory pile collapses from "~80 rules" to "~8–10 genuinely judgment-dependent rules" once we credit the enforceable ones to layer 3.

---

## 3. Per-candidate analysis (top 3)

### 3.1 Candidate #1 — `block-dangerous-git-flags.sh`

**Triggers:** `git commit --no-verify`, `git commit --no-gpg-sign`, `git push --force* … origin/main`, `git push --force* … main`.

**Mechanism:** PreToolUse(Bash) regex-detect, exit non-zero with structured `{"permissionDecision": "deny", "permissionDecisionReason": "..."}` JSON output.

**Why first:** zero false-positive risk (these flags are never legitimate for agent-initiated work — they exist for the human user to use in their own terminal, and the user is always free to do so outside Claude Code). Three documented incidents in 2026 — #M-0.5 (PR #1813), #M-0.5 sibling around `--no-verify` use, recurring `gh pr merge --admin` work-arounds.

**Bypass-rate concern (issue ask):** these are *new* hooks; bypass rate currently 100% because nothing blocks them. Post-deploy expectation: 0% (no override on these — they're truly forbidden for the agent).

**Implementation cost:** ~25 LOC bash + settings.json wiring + 2 pytest cases. Single hook covers all three patterns via shared regex matcher.

### 3.2 Candidate #2 — `pytest-before-push.sh`

**Trigger:** PreToolUse(Bash) matching `^git push\b`.

**Logic:**

1. `STAMP_FILE="/tmp/learn-uk-pytest-ok.$(git rev-parse --abbrev-ref HEAD)"`
2. If `STAMP_FILE` mtime ≥ 5 min ago OR missing → check `git diff --name-only @{u}..HEAD` (or `origin/main..HEAD` fallback)
3. If diff matches `\.py$|^tests/|^scripts/|^claude_extensions/rules/|\.dagger/` → deny with message `"Run pytest first: .venv/bin/python -m pytest && touch $STAMP_FILE"`
4. Otherwise (docs-only) → allow

**The 5-minute window** is the same heuristic from the issue table; matches typical pytest run time + agent context-switch.

**Bypass:** `LEARN_UK_PYTEST_SKIP=1 git push …` (must be explicit; logged).

**Why second:** #M-7 was encoded 2026-05-12 (failure: pushed `d1588dd0ae` without pytest, main went red 8 min) and **violated again 2026-05-13 morning of the same week** per the issue. Memory rule did not survive seven days. This is the canonical "soft rule died" case in the project.

**False positives:** docs-only pushes are filtered out by the diff scope. Risk is essentially zero outside genuinely large refactors where the agent is sure-the-tests-pass-without-running-them (those should run pytest anyway).

**Implementation cost:** ~80 LOC bash + settings.json wiring + 3 pytest cases (no-diff allowed, diff-but-stale-stamp denied, diff-but-fresh-stamp allowed).

### 3.3 Candidate #3 — `admin-merge-guard.sh`

**Trigger:** PreToolUse(Bash) matching `gh pr merge .*--admin\b`.

**Logic:**

1. Parse PR number out of the command (positional arg).
2. Fetch `gh pr checks $N --json` (1–2s, acceptable).
3. Identify any check in `{pytest, ruff, frontend, schema-drift, gitleaks, radon, prompt-lint, CodeQL}` with `conclusion=FAILURE`.
4. If any → deny with message listing the failing checks.
5. If only Gemini-Dispatch (advisory) is failing → allow with logged warning.

**Why third:** lower frequency than #1/#2 (admin merges are rare) but the cost of each violation is high — main goes red, often around a hot feature. The hook adds 1–2s to admin merges, which is justified by the asymmetric blast radius.

**False positives:** require an explicit "advisory check" allowlist (Gemini-Dispatch + any others handoffs flag). Risk: medium-low — if a new advisory check is added we have to update the list, but that's a 1-line PR.

**Implementation cost:** ~60 LOC bash + settings.json wiring + 2 pytest cases (pytest-fail denied; gemini-fail allowed).

---

## 4. Sequencing recommendation for follow-up PR

### Sprint 1 (the actual follow-up PR)

| Step | Work | Estimated dispatch cost |
|---|---|---|
| 1 | `block-dangerous-git-flags.sh` + settings wiring | 0.25 Codex dispatch |
| 2 | `pytest-before-push.sh` + settings wiring + stamp-file convention doc | 0.5 Codex dispatch |
| 3 | `admin-merge-guard.sh` + settings wiring | 0.5 Codex dispatch |
| 4 | `tests/test_hook_enforcement.py` covering all three | 0.25 Codex dispatch |
| 5 | `docs/harness/overrides.md` listing env vars + CLAUDE.md one-line pointer | inline orchestrator |

**Single PR, ~250 LOC bash + ~100 LOC pytest + 1 doc.** Codex dispatch, mechanical-with-design-judgment lane (correct routing per #M0). The dispatch brief should be small enough to fit in one Codex turn given clear hook specs.

### Sprint 2 (after Sprint 1 lands and is validated for ≥1 week)

Pilot the medium-complexity candidates (5, 7, 8, 10, 11). Each is ~30–100 LOC. Do them in batches of 2–3 hooks per PR to keep review surface small.

### Sprint 3 (config-only tightening)

Convert items 9 and 13 to settings-only `deny`/`ask` changes — no shell. Fastest of all (~5 LOC diff in `settings.json`), but only safe AFTER sprints 1 and 2 prove the "deny + override env" pattern doesn't cause workflow papercuts.

### Not in any sprint

Items 15–22 (advisory). The follow-up PR documents *why* they stay advisory so the catalog is closed — no future audit accidentally re-litigates them.

---

## 5. Risks & dissenting views

### 5.1 The "false-positive avalanche" risk

A `deny` hook that fires on a legitimate command is materially worse than a soft rule, because it forces the agent to choose between (a) finding the override env var (which it may not remember exists) or (b) silently giving up on the task. Soft rules can be ignored when needed; hard rules cannot. **Mitigation:** every recommended hook has an override path documented up-front (Section 2.1 column). The agent learns the override by reading `docs/harness/overrides.md` on cold start. We accept "agent has to read a doc to know the escape hatch" as the cost of moving rules to layer 3.

### 5.2 The "rules drift from hooks" risk

If `claude_extensions/rules/critical-rules.md` says "don't print secrets" and `block-secret-leaks.sh` enforces only the `env`/`printenv`/`set` patterns but not (say) `dscacheutil`, the rule and the hook diverge. **Mitigation:** every Sprint 1/2 hook ships with a one-line pointer in the rule file → `enforced by: .claude/hooks/<name>.sh`. The rule stays as documentation but explicitly cedes enforcement to the hook. Future rule updates are checked against the hook.

### 5.3 The "hook brittleness on macOS vs Linux" risk

Several existing hooks (`session-setup.sh` for example) already navigate BSD vs GNU `stat`/`find` differences. New hooks should follow the same patterns. Estimated overhead per hook: ~5 LOC for portable date/time handling.

### 5.4 The "this audit is itself rule advisory drift" risk

This audit produces a `REPORT.md` recommending hooks. If the recommended hooks are not shipped within (say) 30 days, the report joins the layer-2 pile it's trying to shrink. **Mitigation:** the follow-up PR should land within 2 weeks of merging this audit, before the report ages out of working memory. Sprint 1 alone is ≤1 Codex dispatch.

### 5.5 Dissent: "is layer-3 over-engineering?"

Codex / a skeptical reviewer might argue: the model's reading of rules is good enough, and these incidents are tail events. **Rebuttal:** #M-7 was violated 7 days after being encoded. The incident rate doesn't support "good enough." But: we should NOT push to layer 3 every rule that *could* go there — items 12 (worktree-for-branches) and 14 (X-Agent trailer) have meaningful false-positive risk and the existing soft-rule + lint-script enforcement (`scripts/audit/lint_agent_trailer.py`) is already working. Layer 3 belongs where the soft rule has DEMONSTRABLY failed AND the hook surface is clean.

### 5.6 Out-of-scope (per issue)

- Hooks that enforce content quality (#1 quality-above-all, #5 word targets) — already enforced by `scripts/audit/audit_module.py` + V7 gates.
- Hooks intercepting parent-process CLI flags (`/compact`, `--resume`, `--continue`).
- Refactoring existing informational hooks (`session-setup.sh`, `post-compact.sh`, …).
- Anything affecting commands the human user types in their own terminal — hooks fire only on Claude's tool calls.

---

## 6. Acceptance-criteria mapping (from issue #1908)

| Issue AC | Status this audit | Pointer |
|---|---|---|
| Audit pass enumerating every NEVER/MUST | **Done** (Section 2.1 + 1.3) | This file |
| Classify each as (a)/(b)/(c) | **Done** (Section 2.1 column) | This file |
| Output to `docs/harness/rule-classification.md` | **Deferred** to follow-up PR — audit dir convention places this file under `audit/2026-05-17-harness-layered-audit/` instead; follow-up PR can move/copy into `docs/harness/` | This file |
| Ship top 4-6 hooks | **Deferred** (this PR is `--mode read-only`) — recommended list in Sections 3 and 4 | — |
| Override pattern documented | **Designed** (Section 2.1 column, Section 3 per-hook); Sprint 1 ships `docs/harness/overrides.md` | — |
| Tests `tests/test_hook_enforcement.py` | **Deferred** — Sprint 1 includes tests per Section 4 | — |
| Deploy parity (`.claude/` + `.codex/` + `.gemini/`) | **Note:** PreToolUse(Bash) hooks are Claude-specific. Codex/Gemini have their own hook surfaces; same logic would need to be re-implemented per agent. Sprint 2 should evaluate `.codex/hooks/` and `.gemini/hooks/` parity for the four highest-leverage hooks. | — |
| Add "for every NEW rule, ask: can this be a hook?" to agent docs | **Recommended** in `docs/best-practices/harness-engineering.md` as a final section, drafted in Sprint 1 | — |

---

## 7. Appendix — observed permission/hook map

### 7.1 Permission rules summary

```
allow (bash): 79
ask           : 4   (.claude/** write, .claude/settings.json edit,
                    git push *, gh * create *)
deny          : 0
mcp           : allow mcp__ukrainian-validator__*
webfetch      : allow *
websearch     : allow *
```

### 7.2 Hook-event coverage

```
SessionStart        : session-setup.sh
PreToolUse(Bash)    : enforce-venv.sh    ← only mutating hook
PostToolUse         : tool-timing.sh, context-monitor.sh
PostToolUseFailure  : tool-timing.sh
UserPromptSubmit    : check-gemini-inbox.sh
PostCompact         : post-compact.sh
FileChanged         : auto-audit.sh, auto-deploy-claude-extensions.sh
StopFailure         : inline echo (no script)
```

No hooks on Write/Edit (so item 8 needs a new event matcher). No hooks on `git`-flavored Bash subsets specifically (current single PreToolUse(Bash) is `enforce-venv.sh` which only handles python rewrites — new hooks would be additional entries in the same array).

### 7.3 Existing `enforce-venv.sh` as template

The cleanest mutating-hook pattern in the codebase. Worth modeling new hooks on its `{"modifiedInput": {"command": …}}` JSON return shape. For deny-flavored hooks, the corresponding shape is `{"permissionDecision": "deny", "permissionDecisionReason": "..."}` per Claude Code docs.

---

**End of report.** Recommendations for the follow-up implementation PR are concentrated in Section 3 (top 3 hooks) and Section 4 (sequencing).
