# AGENTS.md - Rules for AI Coding Agents

> Shared source of truth for non-provider-specific repository rules.
> Codex prompts read this file only as runtime instructions; do not load `CLAUDE.md` or `GEMINI.md` for normal Codex startup.
> `CLAUDE.md` and `GEMINI.md` contain provider-specific context and may defer here for shared rules.

---

## Operator Contract (binding for ALL agents — read before acting)

The operator's working contract is `agents_extensions/shared/rules/operator-expectations.md`
(deploy copies: `.codex/rules/` · `.agent/rules/` · `.gemini/rules/`; served FIRST at
`GET http://localhost:8765/api/rules`). Its items are the tie-breakers when instructions
conflict. Digest — read the full file for the binding wording:
**1** Quality: no shortcuts, no threshold-lowering, no "for now" · **2** Best practices +
root-cause fixes · **3** Git/GitHub hygiene (**layout A**): primary non-bare on `main`
(human + services); agents only in `.worktrees/dispatch/<agent>/<task>/`; bare primary =
heal-as-bug; PRs + `X-Agent` · **4** Use the whole fleet; review gate = independent
**cross-family** reviewer (discussion ≠ review) · **5** Route by model × harness fit ·
**6** Limits: substitute lanes, NOTE substitutions · **7** Tool-backed claims only;
UA word/stress/morphology VESUM/`sources`-verified · **8** Clean code + current docs ·
**9** Max UA immersion EXCEPT A1 · **10** Drive within approved scope · **11** Repo hard
gates bind · **12** **Advisor/operator approval gate**: no architecture, layout, or
process decisions without present-tense **operator** or designated **advisor** approval
(current advisors: **Fable**, **Sol** — roster may change; check `/api/rules`).

### Fleet-comms mid-cutover (binding for standalone TUI/UI drivers; #5512)

Full text: `agents_extensions/shared/rules/fleet-comms-coordination.md` (also in
`GET /api/rules`). Digest: prefer `.venv/bin/python -m scripts.fleet_comms plane-status` +
`review-pr` / `publish-review-verdict` for topology and formal CF; while plane
`mode=off`, **file dual-write remains authoritative** — do not invent a competing
design or flip dual_write / stream authority / `formal_review_eligible` without
operator/advisor GO. Stream leases are already claimed by launchers.

---

## Project Research Registry — Orchestrator Duty (binding)

Before every delegated task, the accountable orchestrator must deliberately classify
its functional role, task family, track, and owned paths. For scoped work, pass every
known dimension through `--research-role`, `--research-task-family`,
`--research-track`, and repeatable `--research-owned-path`; never infer them from the
provider or agent name. A genuinely generic or unknown task omits all research flags
and remains pointer-free. A surfaced pointer is not proof of consumption: research
claimed as used requires an attributed record fetch while the task is active. Registry
delivery remains fail-open, but forgetting this classification is not an acceptable
generic-task classification. Full contract and examples:
`agents_extensions/shared/rules/workflow.md` § Project Research Registry.

---

## Work Intake — Stream Epics (binding for ALL orchestrators; #4708)

Every open GH issue belongs to **exactly one stream epic** — registry:
`scripts/config/issue_streams.yaml` (streams → epic numbers). Your work queue is YOUR
stream's epic, not the global issue list. Codex UI track drivers: your curriculum-track
work hangs off its stream epic (seminars-folk #2836, seminars-bio #4431, core-quality
#4274, …) — pick up from there, and link every issue you create to its stream epic at
creation (native sub-issue preferred; `#N` checklist line in the epic body accepted).
Unlinked issues are flagged as ORPHANS at every agent's cold start (session-setup 11b)
and at `GET /api/issues/streams`. When a PR fixes an issue, close it with evidence —
and if scope remains, split it into a new linked issue BEFORE the auto-close keyword
eats it. Full protocol: `agents_extensions/shared/rules/workflow.md` § Work intake
(served at `/api/rules`).

## Global Codex Operating Rules

- Start every task at the repository root and run `git status --short --branch` before editing. **This is a read-only preflight/orientation step only.** Do not use this as permission to implement from the primary checkout.
- **Any implementation edit, branch work, commit, or PR MUST happen from a worktree (`.worktrees/dispatch/<agent>/<task>/`)** unless the user explicitly authorizes an exception. This prose rule is a reminder/backstop; mechanical enforcement is tracked in #4444-#4450.
- Preserve user and unrelated changes; do not revert, delete, or clean up work outside the task.
- Use multi-agent delegation for non-trivial work that can run in parallel without shared-file contention.
- Keep worker scopes disjoint, and explicitly tell agents not to revert or overwrite others' changes.
- Use `apply_patch` for manual edits.
- Keep changes scoped to the requested files and behavior.
- Run relevant verification before finalizing, or state why verification was not run.
- Final reports must include changed files, verification performed, and final `git status --short --branch`.

---

## MANDATORY PRE-SUBMIT CHECKLIST

**Before creating a PR, verify EVERY item. If ANY check fails, fix it BEFORE submitting.**

- [ ] `.python-version` is unchanged (must be `3.12.8`)
- [ ] `.yamllint` is unchanged (zero modifications)
- [ ] `.markdownlint.json` is unchanged (zero modifications)
- [ ] No `status/*.json` files in the diff
- [ ] No `audit/*-review.md` files in the diff
- [ ] No `review/*-review.md` files in the diff
- [ ] No `data/telemetry/**` files in the diff
- [ ] No `sys.executable` anywhere in code (use `.venv/bin/python`)
- [ ] No `@pytest.mark.skip` with empty `pass` bodies
- [ ] No assertions weakened (e.g., `is True` → `isinstance(..., bool)`)
- [ ] Every changed file is directly related to the task
- [ ] Total files changed < 20 (if more, you likely included artifacts)
- [ ] Code runs without `NameError`, `KeyError`, or `ImportError`
- [ ] OPSEC check passed: zero raw IP addresses, SSH keys, or infrastructure secrets in diff (`.venv/bin/python scripts/audit/lint_opsec_leaks.py`)

**If you cannot check every box, your PR WILL be rejected.**

---

## Non-Negotiable Rules

These rules are ABSOLUTE. Violating ANY of them results in immediate PR rejection.
**100% of recent PRs violated these rules. Read carefully.**

### 1. NEVER Change `.python-version`

The file `.python-version` is set to `3.12.8`. This version is compiled via pyenv with `--enable-loadable-sqlite-extensions` for sqlite-vec support. Changing it to 3.12.12 or any other version breaks every developer's environment.

**Do not touch this file. Not even to "upgrade" it.**

### 2. NEVER Modify Linter Configs

`.markdownlint.json` and `.yamllint` contain intentional style rules.

**If your code fails linting:**
- **Fix the source files**, not the linter config
- Do NOT disable rules to make CI pass
- Do NOT set rules to `false` or `disable`
- Do NOT add `key-duplicates: disable` (duplicate YAML keys silently overwrite data)

**This is the #1 reason PRs get rejected.** Every single PR in the last batch gutted linter configs. "Fix source, not symptoms" is a core project principle.

### 3. NEVER Use `sys.executable`

```bash
# CORRECT — in shell commands
.venv/bin/python scripts/audit_module.py path/to/module.md

# CORRECT — in Python subprocess calls
subprocess.run(['.venv/bin/python', 'scripts/audit_module.py', path])

# WRONG — uses system Python, missing deps
python3 scripts/audit_module.py path/to/module.md
subprocess.run([sys.executable, 'scripts/audit_module.py', path])
```

`sys.executable` may point to the system Python or a different interpreter that lacks sqlite-vec and other venv dependencies. **Always use `.venv/bin/python` explicitly.**

### 4. NEVER Include Auto-Generated Files in Code PRs

These files are auto-generated and MUST NOT appear in PRs that change code/scripts:

- `curriculum/l2-uk-en/**/status/*.json` — audit cache files
- `curriculum/l2-uk-en/**/audit/*-review.md` — auto-generated reviews
- `curriculum/l2-uk-en/**/review/*-review.md` — review files
- `docs/*-STATUS.md` — level status reports
- `data/telemetry/**` — local runtime telemetry state

**Why this is critical:**
- Creates massive diffs (one PR had 296 artifact files out of 301 total)
- Overwrites hand-crafted reviews with generic machine output
- Introduces data regressions (e.g., `"plan": null` in status JSONs)
- Makes code review impossible (real changes buried in noise)

**Rule of thumb:** If your PR touches more than 20 files, you almost certainly included artifacts. Check your diff.

### 5. NEVER Weaken Tests

- Do NOT add `@pytest.mark.skip` with empty `pass` bodies
- Do NOT change `assert result['passed'] is True` to `assert isinstance(result['passed'], bool)`
- Do NOT stub imports with `try/except` that silently return empty results
- Do NOT comment out assertions
- Do NOT use double `@pytest.mark.skip` decorators (copy-paste error)

If tests fail, **fix the underlying code** or properly rewrite the tests. Dead tests are worse than no tests.

### 6. NEVER Fabricate Documentation

Do NOT invent:
- Error codes that don't exist in the codebase
- Phases/workflows that don't exist
- Screenshots or assets that don't exist
- API endpoints that don't exist
- Review documents at the repo root (e.g., `CODEBASE_QUALITY_REVIEW.md`)

**Read the actual source code first.** Reference real function names, real file paths, real workflows.

### 7. NEVER Delete Files Without Explicit Instructions

Do not remove scripts, utilities, or debug tools unless the task specifically asks for it. Files that exist in the repo exist for a reason. One failed session deleted 21 scripts — all were needed.

### 8. ALWAYS Test Your Code Before Submitting

Run the scripts you modified. Check for:
- `NameError` — variables referenced but not defined in scope
- `KeyError` — dictionary keys assumed but not present
- `ImportError` — modules imported but not installed
- Variable scoping bugs in multiprocessing/threading code
- `lru_cache` on functions that return mutable data (stale results)
- Temp files created with `delete=False` but never cleaned up

### 9. Scope Your PRs

One PR = one concern. Do NOT:
- Change linter configs in a "performance optimization" PR
- Change `.python-version` in a "test suite" PR
- Delete files in a "fix docs" PR
- Add unrelated CI changes in a "monitoring" PR
- Regenerate all audit/status files in a "code change" PR

If you find something unrelated that needs fixing, create a separate issue.

### 10. ALWAYS Use the Worktree Subtree Layout (layout A)

**Mental model (Fable 2026-07-21):** *Root is the human's and the services'; agents live under `.worktrees/`.*

| Who | Path | Notes |
| --- | --- | --- |
| **Human + services** | repo root (`~/projects/learn-ukrainian`) | Normal **non-bare** checkout, pinned to **`main`**. `git status` works. |
| **Agents** | `.worktrees/dispatch/<agent>/<task>/` | All implementation. Never commit on primary. |

Primary `core.bare=true` is a **bug** (heal with `git config core.bare false`; keep `extensions.worktreeConfig=true`). Do not invent alternate human homes (e.g. `.worktrees/main`) or layout helpers without **operator or advisor** approval.

When you create a worktree (orchestrator or self), use the **subtree layout**:

```
.worktrees/dispatch/<agent>/<task>/
```

Concrete examples:
- `.worktrees/dispatch/codex/1877-verify-quote/`
- `.worktrees/dispatch/gemini/1878-fixtures-update/`
- `.worktrees/dispatch/claude/1657-adr-010/`

The branch name aligns: `<agent>/<task>` (e.g. `codex/1877-verify-quote`).

**Why this matters:**
- Cleaner cleanup — `rm -rf .worktrees/dispatch/codex/` nukes all your leftovers at once instead of grepping names.
- Aligned branch + path makes `git worktree list` readable as the directory fills up.
- `scripts/delegate.py` emits a `⚠️ DEPRECATED flat worktree layout` warning on the old `.worktrees/<name>/` form.

**When the orchestrator dispatches you:** the runtime auto-derives the subtree path when invoked with bare `--worktree` (no path). Trust it.

**When you set up a worktree yourself (no orchestrator):** use the subtree layout manually:

```bash
git worktree add -b codex/<issue>-<topic> .worktrees/dispatch/codex/<issue>-<topic> origin/main
cd .worktrees/dispatch/codex/<issue>-<topic>
```

After the PR merges, clean up:

```bash
git worktree remove .worktrees/dispatch/<agent>/<task>
git branch -d <agent>/<task>
```

The flat `.worktrees/<name>/` layout still works for back-compat but is being phased out. Do not create new flat worktrees.

### 11. ALWAYS Add an `X-Agent` Trailer to Every Commit

Every commit you create MUST include an `X-Agent` trailer identifying which agent + task produced it. This is the ONLY way to distinguish Codex / Gemini / Claude-headless / orchestrator-inline work — the git `committer` field is the user's local config and is identical across all locally-dispatched agents.

**Format:**

```
X-Agent: <agent>/<task-id>
```

Where `<agent>` ∈ {`claude-inline`, `claude`, `codex`, `gemini`, `dependabot`} and `<task-id>` is your dispatch task identifier OR the literal `orchestrator` / `inline` for orchestrator-side commits.

**Examples:**

```
X-Agent: codex/1879-fix-ci-and-wikipedia
X-Agent: claude/1657-adr-010
X-Agent: gemini/1787-15-handoff-verifier
X-Agent: claude-inline/orchestrator
```

**How to add it:**

```bash
# Preferred: use --trailer on commit (auto-formats)
git commit -m "feat(foo): bar" --trailer "X-Agent: codex/1879-fix-ci-and-wikipedia"

# Or include it directly in the commit message body (separated by blank line):
git commit -m "$(cat <<EOF
feat(foo): bar

Implementation details here.

X-Agent: codex/1879-fix-ci-and-wikipedia
EOF
)"
```

**Enforcement:**

`scripts/audit/lint_agent_trailer.py` checks every commit in `origin/main..HEAD` for the trailer. Run it before pushing:

```bash
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Dependabot squash-merges are auto-skipped (recognized by subject `deps: ...` / `Bump ...` or `dependabot` in committer/author). Merge commits are skipped via `git log --no-merges`.

### 12. NEVER Use Container Paths

This project runs **locally with pyenv**, NOT in Docker. Do not use:
- `/app/curriculum/...` — use relative paths or real local paths
- `localhost:8765` — use relative URLs (`/api/...`)

### 13. Use Current Agent Tooling

Gemini CLI and Gemini Code Assist are not supported or restorable routes for
this project. For Gemini-family work, use AGY through the project bridge or
dispatch runtime.

Do not tell agents to run bare `ab ...` commands. On the user's machine `ab`
resolves to ApacheBench (`/usr/sbin/ab`), so bare `ab ask-*`, `ab post`, and
`ab discuss` instructions are brittle. Use explicit project entry points:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy - \
  --task-id review-123 \
  --to-model gemini-3.1-pro-high

scripts/delegate.py dispatch --agent agy --brief docs/dispatch-briefs/task.md --worktree
```

Direct `agy --model` calls use display labels from `agy models`, such as
`Gemini 3.1 Pro (High)` and `Gemini 3.5 Flash (High)`. The bridge/runtime may
map slugs such as `gemini-3.1-pro-high` to those labels.

### 14. Do Not Leave PRs In Limbo

Do not leave draft PRs or open PRs in limbo after checks are green. Every PR you
create must end the task in one of these states: merged, closed with a reason,
or explicitly handed off with the blocker, owner, and next action.

Before the final response, check PR state, checks, mergeability, and whether the
branch/worktree needs cleanup. If a PR remains open, the final response must say
exactly why and what action is required. Leaving PRs in review hell wastes CI,
agent, and human attention.

**Arm auto-merge at review-gate-pass (#4703, user directive 2026-07-07).** The repo
setting `allow_auto_merge` is enabled. The moment a PR's review gate passes
(cross-family review evidence, no requested changes), the responsible
orchestrator/reviewer runs `gh pr merge <N> --auto --squash --delete-branch` —
GitHub merges when CI settles, nobody babysits. Dispatched agents do NOT
self-enable auto-merge (the review gate comes first — unchanged). `--auto` waits
for green and never bypasses blocking checks.

**Out-of-lane pickup threshold (user directive 2026-07-07).** A PR belonging to
another lane/track is hands-off for every other orchestrator — no shepherding,
review-routing, or auto-merge arming — unless it has sat GREEN (CI passing +
review gate passed) idle for MORE THAN 1 HOUR. Only then does the orchestrator
sweep backstop pick it up. Fresh out-of-lane PRs belong to their lane.

---

## Economical Multi-Agent Delegation

When Codex multi-agent support is enabled, the user explicitly authorizes the main Codex agent to use lower-cost routine subagents for bounded work that can run in parallel without lowering quality. The main agent stays responsible for planning, integration, final review, PR creation, independent review routing, and merge decisions.

Prefer `explorer` subagents for read-only investigation and validation. Use `worker` subagents only for mechanical edits with a clearly owned file set and no ambiguity.

Routine subagent model routing:

- Use `gpt-5.4-mini` for general repo search, small summaries, docs/index checks, simple validation, and straightforward documentation edits.
- Use `gpt-5.3-codex-spark` for narrow code-heavy routine tasks where code fluency matters: mechanical Python/TypeScript edits, focused test-failure triage, small refactors with clear ownership, diff review, and targeted validation. This model has a separate usage/limit counter, so prefer it over the main model for bounded coding chores when it can run independently.

Use routine subagents for:

- finding where a feature, config, route, test, or workflow is defined
- summarizing a small file set before the main agent edits it
- checking whether docs, indexes, tests, or scripts reference a changed file
- running simple validation such as `bash -n`, YAML/JSON parsing, `git diff --check`, or targeted tests
- making mechanical edits in a clearly owned file set
- updating straightforward documentation or generated indexes when explicitly in scope
- verifying a narrow behavior while the main agent keeps implementing elsewhere

Do not use routine subagents for architecture decisions, security-sensitive judgment, ambiguous debugging, broad refactors, PR creation, independent review routing, merges, destructive actions, or work that blocks the main agent's next immediate step. Give each subagent a narrow task, a clear file ownership boundary when edits are allowed, and instructions not to revert unrelated changes. The main agent must review every routine-subagent diff before finalizing or presenting the work as complete.

Cost controls:

- Use local deterministic tools before model calls: `rg`, `git diff --check`, `bash -n`, `.venv/bin/ruff`, targeted tests, JSON/YAML parsers, and local API endpoints.
- Escalate routine model work in this order when quality allows: `gpt-5.4-mini` for general routine work, `gpt-5.3-codex-spark` for bounded code-heavy routine work, then the main model for judgment/integration.
- Do not spawn a subagent for work the main agent can finish faster than delegation overhead.
- Keep routine delegation to one to three subagents at a time unless the user explicitly asks for a larger sweep.
- Do not let subagents read secrets, source `.envrc`, call `gh`, request reviews, or merge PRs.
- Do not delegate independent review requirement. Internal GPT helper swarms Codex self-review do not satisfy external gate. Request one read-only review through an independent non-Codex route and treat unresolved findings as blockers. The reviewer must come from OUTSIDE the author's model family (cross-family; discussion/panel input does not satisfy this gate). Current lanes and per-task routing: `agents_extensions/shared/rules/model-assignment.md` (served at `/api/rules`) — the harness-vs-model table there explains which models each harness (hermes, opencode, native CLIs) can reach; never block on a single unavailable lane (Claude/Codex budget buckets at near_cap substitute per `scripts/config/agent_fallback_substitutions.yaml`; other lanes reroute via the harness table, noting the substitution). If AGY is used as that route, call it through the explicit bridge, example `printf '%s\n' "<review prompt>" | .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy - --task-id review-<id> --to-model gemini-3.1-pro-high --review`.

### Native Codex multi-agent V2 prompt contract

When the operator asks any repository agent to create, write, or improve a
Codex delegation/orchestration prompt, produce a native multi-agent V2 prompt
by default unless the operator names another harness or explicitly asks for a
single-agent prompt. This default applies to agent-work prompts, not unrelated
prompts such as lesson copy, image generation, or learner exercises.

Every V2 prompt must:

- appoint exactly one accountable root orchestrator that owns scope,
  sequencing, integration, validation, and the final disposition
- tell the root to call `list_agents` before spawning and again after all
  requested agents reach terminal states
- give each child a unique `task_name`, an explicit functional role, task
  family, track when applicable, owned paths, read/write authority, inputs,
  constraints, expected evidence, and return contract
- default to `fork_turns="none"` with a self-contained child brief; inherit
  conversation turns only when the child materially needs them
- parallelize only independent work, prohibit duplicate lanes and shared-file
  contention, and keep useful critical-path work with the root
- keep no more than three non-root agents active across the entire tree at
  once; nested descendants consume the same shared child capacity, so the root
  must reserve their required slots before starting a nested parent or delay
  conflicting siblings
- require the root to wait for every requested result, inspect worker output
  and diffs, reconcile disagreements, run integrated verification, and report
  canonical agent paths plus final statuses from a requested-agent ledger,
  including failures, cancellations, or missing descendants
- use nested parent → grandchild delegation only when a bounded sub-workstream
  needs its own coordinator; the parent must receive explicit spawn authority,
  wait for all descendants, and return their status to the root
- preserve the repository's worktree, research-classification, quota-routing,
  tool-backed-evidence, and cross-family review requirements

Native Codex children are same-family helpers. Their review or consensus never
satisfies the independent cross-family review gate. The canonical copy/paste
template and examples live in
[`docs/best-practices/agent-cooperation.md`](docs/best-practices/agent-cooperation.md#native-codex-multi-agent-v2).

Module-build PRs must persist token telemetry through
`POST /api/telemetry/module-builds` and include the same summary in the PR body
or final orchestration note. Every record must explicitly say whether a swarm
was used (`swarm_used: true/false`) and include a `swarm_note`; solo runs still
need a note such as "solo run; no swarm used". See
`docs/runbooks/module-build-token-telemetry.md`. The SQLite database under
`data/telemetry/` is local runtime state and must not be committed.


## Project Architecture

```
curriculum/l2-uk-en/
├── plans/{level}/{slug}.yaml     # SOURCE OF TRUTH (immutable)
├── {level}/meta/{slug}.yaml      # Build config (mutable)
├── {level}/{num}-{slug}.md       # Lesson content
├── {level}/activities/{slug}.yaml # Activities (V1 bare list or V2 inline/workbook)
├── {level}/vocabulary/{slug}.yaml # Vocabulary
├── {level}/status/{slug}.json    # AUTO-GENERATED — never include in PRs
└── {level}/audit/{slug}-review.md # AUTO-GENERATED — never include in PRs
```

**Key facts:**
- Activity YAML may be V1 bare list at root for simple modules, or V2 object with `inline:` and `workbook:` lists when Lesson-tab activities must be separated from Workbook/Activities-tab practice; never wrap the list in an `activities:` key
- Word targets in plans are MINIMUMS, not maximums
- Dependencies: `pyproject.toml` (NOT `requirements.txt` — it doesn't exist)
- Repo: `learn-ukrainian/learn-ukrainian.github.io`
- Python: pyenv 3.12.8 (NOT 3.10, NOT 3.12.12)
- All documentation goes in `docs/`, not repo root
- Only `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `README.md` belong at root

## Common Anti-Patterns (All Seen in Recent PRs)

| Anti-Pattern | Frequency | What to Do Instead |
| --- | --- | --- |
| Disable/gut `.yamllint` rules | 100% of PRs | Fix the source files that fail linting |
| Disable/gut `.markdownlint.json` rules | 80% of PRs | Fix the markdown files |
| Change `.python-version` to 3.12.12 | 60% of PRs | Don't. It must stay 3.12.8 |
| Include 50-300 regenerated artifacts | 60% of PRs | Only include files you actually changed |
| Use `sys.executable` in subprocess | 40% of PRs | Use `.venv/bin/python` |
| Skip tests with `@skip` + `pass` | 40% of PRs | Fix the code or rewrite the test |
| Ship code with `NameError` at runtime | 40% of PRs | Run your code before submitting |
| Scope creep (unrelated changes) | 80% of PRs | One PR = one concern |
| Use `/app/` container paths | 20% of PRs | Use real local paths or relative paths |
| Reference `requirements.txt` | seen | Use `pyproject.toml` |
| Delete existing scripts/files | seen | Don't delete without explicit instructions |
| Create root-level doc files | seen | Put documentation in `docs/` |

---

## Multi-Agent Deliberation Protocol (added 2026-05-02 — issue #1639)

You will sometimes be invoked via `.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss` for design / framing / pedagogy / architecture decisions. **This is NOT a quorum** — Claude/AGY/Codex have correlated training-data priors. What we DO get from deliberation: more angles, adversarial pressure, written record.

**When you participate in multi-agent discussion through `.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss`:**

1. **End with `[AGREE]`** if you genuinely agree with the prior round's converging position. This short-circuits the discussion.
2. **Surface options with explicit labels** — Option A / Option B / Option C. Don't bury alternatives in prose.
3. **State your rationale, not just your verdict.** "I prefer A because X" — not just "I prefer A."
4. **Push back on correlated-prior risks.** If the discussion is converging on a position that smells like training-data bias (Russian-imperial framings on Ukrainian topics, Western centrism on decolonization, etc.), explicitly flag it. You may be the only check.

**When the orchestrator (Claude) emits a `## DECISION REQUIRED — ...` block, that's a Decision Card.** It means user input is needed. Don't try to resolve it on your side; the orchestrator routes it to inline chat / `docs/decisions/pending/` / GH issue depending on user availability.

**High-risk-track override:** On sensitive tracks (FOLK, HIST, BIO, ISTORIO, LIT, OES, RUTH), an `[AGREE]` consensus is suspect due to shared training-data biases. The orchestrator will override consensus by either force-emitting a Decision Card or injecting domain-specific bias checklists to provoke adversarial review.

**Pending decisions (`docs/decisions/pending/*.md`) are BLOCKING only for the scope declared in their `Scope` field.** If you're starting work in a worktree and that directory has files, surface them in your initial response and check the field before assuming a decision blocks your work.

Full protocol: `docs/best-practices/agent-cooperation.md` "Multi-Agent Deliberation" section.
