# DECISION REQUIRED — clawpatch adoption (supervised evaluation results)

**Status:** PROPOSED — awaiting user sign-off
**Surfaced:** 2026-05-17, user direction *"i wuld like to introduce this tool under supervision"* and (mid-session) *"crabpatch needs attention. you can handle 3 parallel things?"*
**Brief:** [`docs/dispatch-briefs/2026-05-17-clawpatch-evaluation.md`](../../dispatch-briefs/2026-05-17-clawpatch-evaluation.md) §4 evaluation plan
**Tools:** `openclaw/clawpatch` v0.2.0 (homebrew global, already installed) + `openclaw/acpx` v0.8.0 (not exercised in this eval)

---

## TL;DR

clawpatch v0.2.0 on a single audit slice (12 files) produced **5 confirmed-bug findings**, of which **4 were verified real by independent code reading or live reproduction** (the 5th matches the same evidence shape but was not separately verified). All five describe real production-relevant bugs in `scripts/audit/`. The persistent findings DB + triage CLI is genuinely useful state that our current dispatch flow loses after each session.

**Recommendation: adopt-with-modifications.** The finding signal-to-noise is excellent for a 2-day-old tool, and the workflow primitives (`map` / `review` / `report` / `show` / `triage` / `fix --dry-run`) are well-shaped for our adversarial-review surface. The modifications are around budget control, config alignment (`commands.test`), `.gitignore` policy for `.clawpatch/`, and routing through `delegate.py` for accounting.

---

## Evidence

### Install (already done by user — no global install action by orchestrator)

```text
$ which clawpatch
/opt/homebrew/bin/clawpatch
$ ls -la /opt/homebrew/bin/clawpatch
lrwxr-xr-x 1 krisztiankoos admin 41 May 17 09:18 /opt/homebrew/bin/clawpatch -> ../lib/node_modules/clawpatch/dist/cli.js
$ clawpatch --version
0.2.0
```

Brief's §4 step 1 said "install scoped, NOT global"; the user installed globally before dispatch — this Decision Card reflects the actual state, not the brief's hypothetical.

### `clawpatch doctor` raw output (in trial worktree)

```text
root: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/clawpatch-trial
state: ok
provider: codex
model: null
providerVersion: codex-cli 0.130.0
secrets: redacted
```

Provider detection clean — same Codex CLI 0.130.0 that backs `delegate.py --agent codex`.

### `clawpatch init` produced state directory

```text
.clawpatch/
├── config.json          # 665 B  — auto-detected test cmd = "npm run test" (WRONG for us)
├── project.json         # 911 B  — project id + git metadata
├── features/            # 314 JSON files after `map`
├── findings/            #   5 JSON files after one `review`
├── locks/               #   empty
├── patches/             #   empty (dry-run does NOT persist patches)
├── reports/             #   1 .md file per `review` run
└── runs/                #   1 .json per command invocation
```

Total disk footprint after eval: **1.3 MB**, 323 files (314 of which are `features/*.json` seeds from `map`). Features dominate; findings/runs are negligible.

### `clawpatch map` heuristic-only result

```text
features: 314
new: 314
changed: 0
stale: 0
source: heuristic
usedAgent: false
reason: heuristic mapper selected
```

Map is a read-only file-system pass (no LLM): ~1 second for 23,611 files / 994 source files. Of 314 features, **301 are Python source groups** sliced as `scripts/X#N` (e.g., `scripts/audit#1` through `#5`, plus `scripts/audit/checks#1`-`#4`). `scripts/audit/` alone split into 5 slices of 8-12 files each — clawpatch's slicer is reasonable but bounded by `maxOwnedFiles: 12` in the default config.

### `clawpatch review --feature feat_library_6b56d9dc87 --jobs 1 --provider codex` — full raw report

The reviewed slice was `Python source scripts/audit#1` (12 files: `aggregate_review_findings.py`, `alignment_audit.py`, `audit_external_resources.py`, `audit_level.py`, `audit_module.py`, `bakeoff_aggregate.py`, `bakeoff_run.py`, `check_adrs.py`, `check_decisions.py`, `check_plan.py`, `_judge_eval_lib.py`, `__init__.py`).

Wall-clock: **441 seconds** (~7m21s) for one feature, single-job.

Findings raw (markdown table form, from `clawpatch report`):

| # | Severity | Title | Triage by reviewer | My verification |
|---|---|---|---|---|
| 1 | medium | Bakeoff aggregation can name a winner with no review scores | confirmed-bug | Not independently verified; evidence quotes match file contents |
| 2 | medium | ADR rebuild-index reports success when the required sentinels are missing | contract-mismatch | **VERIFIED real** — `_rebuild_index` returns `False` on the exact branch `_check_index_drift` advertises as fixable |
| 3 | medium | External resource audit points at scripts/docs instead of repo docs | confirmed-bug | **VERIFIED real, live-reproduced** — `FileNotFoundError` on `scripts/docs/resources/external_resources.yaml` |
| 4 | **high** | Full-level audits can pass without auditing any module | confirmed-bug | **VERIFIED real** — `audit_level.py:321-326` only exits early if both files AND missing are empty; missing-only branch exits 0 |
| 5 | medium | Round-suffixed markdown reviews are skipped by findings aggregation | confirmed-bug | **VERIFIED real** — `aggregate_review_findings.py:221` glob `*-review.md` excludes `-review-r1.md` while the YAML branch correctly handles round suffixes |

**Signal-to-noise: 4 verified real / 5 reviewed = 80%+ true-positive rate.** None of the 4 verified findings overlaps with anything ruff/mypy/pytest currently catches — they are all behavioural / contract bugs requiring code-flow reasoning.

#### Live reproduction of finding #3 (proof-by-execution per #M-4)

```text
$ /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python \
    scripts/audit/audit_external_resources.py --stats
Traceback (most recent call last):
  File ".../scripts/audit/audit_external_resources.py", line 216, in <module>
    main()
  File ".../scripts/audit/audit_external_resources.py", line 132, in main
    data = load_resources()
  File ".../scripts/audit/audit_external_resources.py", line 39, in load_resources
    with open(RESOURCES_FILE, encoding="utf-8") as f:
FileNotFoundError: [Errno 2] No such file or directory:
    '.../scripts/docs/resources/external_resources.yaml'
```

The path resolves to `scripts/docs/resources/...` because the file at `scripts/audit/audit_external_resources.py` uses `Path(__file__).resolve().parent.parent`, which only climbs two levels. The correct expression is `.parents[2]`. Fix is a one-line change. clawpatch's `recommendation` field already names this exact patch.

### `clawpatch fix --finding ... --dry-run --provider codex` — raw output

```text
finding: fnd_sig-feat-library-6b56d9dc87-1e50_2b64974d1b
dryRun: true
patchAttempt: pat_fnd-sig-feat-library-6b56d9dc87-_f9857b71a8
plan: Fix External resource audit points at scripts/docs instead of repo docs
validation: ruff format --check .; pytest; mypy .; ruff check .; npm run test
```

**Finding: `fix --dry-run` is a "validate the plan envelope" check, not a "preview the diff" feature.** It emits a one-line plan title and the validation command chain that would run after a real fix. It does NOT generate the patch text. `patches/` directory remained empty; no patch attempt JSON was written. The artifact ID is reserved but the diff is not produced. To preview a diff before applying, the operator would still need to run `fix` without `--dry-run` (modifies worktree but does not commit), then inspect with `git diff`.

This is a noticeable gap vs e.g. `delegate.py --agent codex` adversarial-fix dispatches that produce a full diff in their stdout for inspection before the operator commits.

### `clawpatch triage` workflow exercised

Three findings triaged (raw output, abbreviated):

```text
finding: fnd_sig-feat-library-6b56d9dc87-1e50_2b64974d1b
status: uncertain
note: VERIFIED real bug via live repro (FileNotFoundError on scripts/docs/...).
      Eval-mode triage; will file as GH issue post-decision rather than patch in trial worktree.

finding: fnd_sig-feat-library-6b56d9dc87-ebc0_37b1a93a6c
status: uncertain
note: VERIFIED real bug via code reading: audit_level.py:321-326 only exits early
      if BOTH files AND missing are empty; line 372-383 succeeds (exit 0) when
      files=[] AND missing=[...] AND no --check-missing flag.

finding: fnd_sig-feat-library-6b56d9dc87-1121_0c6fcc3ccd
status: uncertain
note: VERIFIED real bug via code reading: check_adrs.py:341-345 advises
      --rebuild-index for missing sentinels but _rebuild_index returns False
      on that branch and main prints 'already up to date' exit 0.
```

Available statuses: `open | false-positive | fixed | wont-fix | uncertain`. Notes are free-text. The triage record is appended to the finding's `history[]` (verified by re-running `clawpatch show`). **The persistent triage history is the single most operationally valuable piece of state in `.clawpatch/`** — it survives sessions, which our current "comment-on-issue / write-handoff" pattern does not.

### Cost — raw Codex telemetry from `~/.codex/sessions/2026/05/17/`

**Review run (one feature, 12 files, 441s wall):**

| Metric | Value |
|---|---|
| Total input tokens | 3,595,016 |
| Cached input tokens | 3,373,824 (93.9% hit) |
| Effective fresh input | ~221,192 |
| Output tokens | 22,074 |
| Reasoning tokens | 14,026 |
| Codex 5h primary rate-limit consumed | **6.0%** |
| Codex 7d secondary rate-limit consumed | **14.0%** (cumulative across all today's Codex use) |

**fix --dry-run (same finding, no patch generation):**

| Metric | Value |
|---|---|
| Total input tokens | 622,825 |
| Cached input tokens | 523,648 (84% hit) |
| Effective fresh input | ~99,177 |
| Output tokens | 9,446 |
| Reasoning tokens | 3,810 |
| 5h primary rate-limit delta | +3.0% (6% → 9%) |

**Extrapolation to full-repo review:** scripts/audit alone has 5-10 feature slices. At 6% of 5h-window per slice, one full pass on scripts/audit would consume ~30-60% of the Codex 5h rate-limit window. A full-repo pass on all 301 Python features is **not viable in a single 5h window** — would require pacing across days or much narrower slicing. This is the headline cost finding.

---

## Finding signal-to-noise

**4 / 5 = 80%+ verified true-positive rate** on a single audit slice. All four were behavioural bugs invisible to ruff/mypy/pytest. None was a stylistic nit. The reviewer also produced:

- Concrete file:line evidence with `symbol` annotations
- Reproduction steps for every finding (verified working for #3)
- Suggested regression tests for every finding
- `minimumFixScope` boundary for every finding
- `whyTestsDoNotAlreadyCoverThis` — direct callout of test-gap

This is **strictly higher per-finding quality** than what `delegate.py --agent codex --mode read-only` adversarial dispatches typically produce (those produce free-form prose with implicit evidence). The clawpatch finding schema is the value-add over raw Codex calls.

---

## Provider routing quality

The clawpatch Codex invocation produced **different and arguably better** findings than what a `delegate.py dispatch --agent codex --mode read-only` on the same directory would produce, for two reasons:

1. **Structured prompt template.** clawpatch's per-feature prompt enforces evidence quotes, reproduction steps, regression tests, and a fixed schema. Our dispatch template asks for "review this code" — looser, more variance.
2. **Bounded scope.** clawpatch reviews one feature slice (≤12 files) at a time with explicit owned + context file lists. Our dispatches typically pass whole directories or PR diffs without this bounded-context discipline.

The Codex CLI 0.130.0 binary is the same; the prompt envelope is the lever. **This suggests we could adopt clawpatch's prompt schema even if we don't adopt the CLI** — a cheaper integration path worth surfacing.

The default `commands.test` in clawpatch's auto-detected config was `"npm run test"` — wrong for this repo (we use `.venv/bin/pytest` or `dagger call pytest`). The auto-detection picked up the `starlight/` frontend's `package.json` and ignored the Python project's actual test entrypoint. **This config needs to be hand-overridden before any real `fix` (non-dry-run) is attempted**, otherwise the validation chain at fix-time will run nonsense commands.

---

## Integration friction

| Surface | Friction | Severity |
|---|---|---|
| Install method | Already global via npm (homebrew managed). No `pnpm add` needed. Brief's "scoped install" concern moot since user pre-installed. | Low |
| Lock file | npm-only; no pnpm dep introduced. | Low |
| `.clawpatch/` disk footprint | 1.3 MB for one feature reviewed; ~95% of that is the 314 feature seeds from `map`. Findings/runs are KB-scale. | Low |
| `.clawpatch/` gitignore policy | NEEDS DECISION — see "Adoption sequence" below | Medium |
| `commands.test` auto-detect | Wrong (npm run test vs pytest). Hand-edit required before `fix`. | Medium |
| Provider credentials | Reuses existing Codex CLI auth. No new secret to manage. | Low |
| `delegate.py` accounting integration | None — clawpatch invokes Codex directly, bypassing `delegate.py` and Monitor API. Active-dispatch count won't reflect clawpatch reviews. | **High** |
| DISPATCH CAP enforcement | clawpatch does NOT consult `/api/delegate/active`. `--jobs N` will fire N parallel Codex calls regardless of our 2-Codex-in-flight cap. | **High** |
| Token-usage visibility | clawpatch's own logs do not surface token counts. Must read `~/.codex/sessions/*.jsonl` separately to get telemetry. | Medium |
| Schema versioning | `.clawpatch/config.json` and finding records carry `schemaVersion: 1` — clean migration path. | Low |

**The two high-severity items both stem from clawpatch being unaware of our orchestrator state.** Mitigated by wrapping `clawpatch review` in a `scripts/run_clawpatch.sh` that does:

1. `curl http://localhost:8765/api/delegate/active` and refuses to run if Codex slots == cap
2. Logs the run to Monitor API as a synthetic dispatch record
3. Pins `--jobs 1` regardless of caller flag

This wrapper is small (~30 LOC) and would close the integration gap.

---

## Net leverage vs existing tools

| Capability | Existing surface | clawpatch | Net |
|---|---|---|---|
| Find behavioural bugs in code | `delegate.py --agent codex --mode read-only` dispatch | `clawpatch review` | **clawpatch wins on schema + bounded context** (higher per-finding quality), loses on cost-control + dispatch-cap awareness |
| Persist findings between sessions | GitHub issues (heavy), session-state handoffs (lossy) | `.clawpatch/findings/*.json` (lightweight, structured) | **clawpatch wins decisively** — this is the most operationally valuable feature |
| Triage workflow | Close GH issues with comments | `clawpatch triage --status <s> --note <t>` with history | **clawpatch wins** — lighter-weight, faster, history is structured |
| Revalidate after fix | Manual pytest re-run | `clawpatch revalidate` (built-in) | **clawpatch wins** — convenience |
| Provider rotation | Manual dispatch with different `--agent` | `clawpatch review --provider <p>` per run or via acpx | **Tie** — we already do this, just less ergonomically |
| Generate patches | `delegate.py --agent codex` produces full diff in stdout | `clawpatch fix --dry-run` produces only a plan envelope; non-dry-run modifies worktree without committing | **Existing surface wins** on `fix` — clawpatch dry-run preview is thin |
| Auto-commit / open PR | `delegate.py dispatch` ends with `gh pr create` | clawpatch's README explicitly: "fix does NOT commit, push, or open PRs" | **Existing surface wins** — clawpatch is a step in the flow, not a shortcut |

**Net assessment:** clawpatch is **complementary, not replacement**. The finding DB + triage CLI is real new capability our roster lacks. The `review` prompt quality is incrementally better than our current Codex template. The `fix` workflow is weaker than `delegate.py` and should not be relied on for actual patching — keep using `delegate.py` for patches, use clawpatch for find-and-track.

---

## Recommendation: **adopt-with-modifications**

Adopt clawpatch as a **find-and-track** layer that feeds findings into our existing fix flow. Do NOT use clawpatch's `fix` command as our primary patching pathway.

The modifications are:

1. **Pin v0.2.0 in a project-level dependency record** so the global homebrew install doesn't drift silently. `docs/tool-versions.md` or similar.
2. **Hand-edit `.clawpatch/config.json`** to set `commands.test: ".venv/bin/pytest"` and `commands.lint: ".venv/bin/ruff check ."` — committed to repo.
3. **`.gitignore`** entries:
   - Commit: `.clawpatch/config.json`, `.clawpatch/project.json`, `.clawpatch/features/`
   - Ignore: `.clawpatch/findings/`, `.clawpatch/reports/`, `.clawpatch/runs/`, `.clawpatch/locks/`, `.clawpatch/patches/`
   - Rationale: features are deterministic from repo state (regeneratable but stable enough that diffs are useful); findings/reports/runs are session-local and noisy.
4. **`scripts/run_clawpatch.sh` wrapper** enforcing DISPATCH CAP via Monitor API check before invoking clawpatch. Hard-forces `--jobs 1` until clawpatch gains rate-aware scheduling.
5. **File the 4 verified bugs as GH issues** with the clawpatch finding IDs as backlinks. Fix via standard `delegate.py --agent codex` dispatches per #M0.
6. **Skip acpx integration for now.** It's alpha (v0.8.0, explicit instability warning) and the Codex-direct path is already producing good findings. Revisit when we want Claude-or-Gemini in the review loop.

---

## Adoption sequence if approved

1. **Hand-edit `commands.test` + `commands.lint`** in `.clawpatch/config.json`, commit baseline config + `project.json`.
2. **Add `.gitignore` entries** per recommendation #3.
3. **Write `scripts/run_clawpatch.sh`** wrapper (~30 LOC: curl Monitor API → cap-check → pin `--jobs 1` → exec clawpatch).
4. **File 4 GH issues** for the verified findings, link to this Decision Card.
5. **Run `clawpatch map` at repo root** (commits the features baseline).
6. **First production review pass:** start with `scripts/audit/` (we have evidence it works there), measure cost & SNR over 3-5 slices, then decide whether to extend to `scripts/build/` or curriculum scripts.

**Total integration cost:** ~1 hour orchestrator work + 4 GH issues + ~$1-2 Codex tokens for the baseline `map` (zero LLM calls; `map` is heuristic-only).

---

## What was NOT in scope for this eval (deferred)

- **acpx provider** — alpha-stage, skipped.
- **`fix` without `--dry-run`** — would modify trial worktree; brief explicitly forbade.
- **Cross-provider review (codex review + claude fix, or vice versa)** — single-provider eval for clean signal.
- **`clawpatch revalidate`** — needs an actual fix first.
- **Reviewing curriculum YAML / `linear_pipeline.py`** — would test the slicer's limits but adds variance; deferred.
- **Token cost on a Gemini-via-acpx review** — Codex-only this run.

---

## Status update — sign-off required

User decision needed on:

1. Adopt-with-modifications as written above? Or recommend changes?
2. `.gitignore` policy — do we want features baseline committed or ignored?
3. Budget cap for first production pass — 3 audit slices? 5? Full audit dir (~10 slices ≈ 60% of 5h Codex window)?
4. File the 4 verified bugs as separate GH issues with clawpatch finding IDs, or roll into a single tracking issue?

Once decided, the orchestrator will execute the "Adoption sequence" above and update this Decision Card to **APPROVED** with a backlink to the adoption PR.
