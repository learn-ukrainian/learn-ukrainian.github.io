# Dispatch Brief — #2154 zizmor MEDIUM triage (DeepSeek-v4-pro)

**Date:** 2026-05-19
**Issue:** [#2154](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2154)
**Target agent:** **DeepSeek-v4-pro** (first project code dispatch — code-capability bakeoff vs Codex on a clean mechanical-with-design-judgment task)
**Mode:** `danger`
**Worktree:** mandatory
**Effort:** `xhigh` (per B1 writer bakeoff finding — DeepSeek-pro needs xhigh for non-trivial scope)

---

## Why you (DeepSeek-pro) on this task

You're being tested as a code-dispatch agent for the first time on this project. Project routing has historically sent code dispatches to Codex (mechanical-with-design-judgment) + Gemini (routine mechanical). Per user direction 2026-05-19, you're getting a project-internal code-capability evaluation because external benchmarks rate you highly and you proved out on V7 content writing this session. If this dispatch ships clean with the verifiable-claims preamble honored, you become a code-dispatch option in `agent_fallback_substitutions.yaml` ahead of the 2026-06-15 Claude sunset.

**No pressure**, but: the bar is "PR opens, all blocking checks green, verifiable-claims preamble honored with raw tool output (not `I checked X` hand-waves)." Codex just did exactly that on #2155 — your reference.

---

## Background

Zizmor adoption (`7a8c9e2af6`, 2026-05-19) shipped after 5 HIGH `unpinned-uses` fixes landed. Baseline scan: **21 MEDIUM findings**. None exploitable on their own; all are hardening opportunities. Left alone they create noise in the GitHub Security tab and erode signal.

| Category | Count | Disposition |
|---|---|---|
| `artipacked` (credential persistence via `actions/checkout`) | 17 | ~10-12 mechanical (`persist-credentials: false`), 5-7 need triage |
| `secrets-inherit` (unconditional `secrets: inherit` on reusable workflows) | 4 | All 4 need explicit `secrets:` blocks per called workflow |

Baseline forensics: `audit/2026-05-19-zizmor-baseline/findings.txt` and `findings.sarif`.

---

## Job

Land a SINGLE PR closing #2154 in this order:

### A. Triage the 17 artipacked findings

For each `actions/checkout` step flagged by zizmor:

1. **Trace downstream**: inspect the job for any step after the checkout that:
   - Pushes back to the repo (`git push`, `gh-pages` deploy)
   - Calls `gh` CLI against the same repo with the implicit `GITHUB_TOKEN`
   - Uses the persisted credential in any way (e.g., `ratchet`, auto-PR workflows)

2. **If no downstream credential use** → add `with: { persist-credentials: false }` to the checkout step.

3. **If downstream credential use** → leave the checkout as-is, add a YAML comment one line above the checkout block explaining WHY credentials are needed:
   ```yaml
   # zizmor:ignore artipacked — credentials needed for gh-pages push (line N)
   - uses: actions/checkout@v5  # already SHA-pinned upstream
   ```
   Adjust comment format to match zizmor's accepted ignore-marker syntax (check the zizmor docs link below). The marker must actually suppress the finding on re-scan.

Files affected (from baseline):
- `.github/workflows/ci.yml` (9 checkouts at lines 44, 71, 89, 173, 188, 252, 293, 416, 438)
- `.github/workflows/deploy-pages.yml` (line 30)
- `.github/workflows/validate-yaml.yml` (line 222)
- 6 remaining likely in `gemini-*.yml` workflow variants (invoke / plan-execute / review / triage)

Exact line numbers may have drifted since baseline; use `audit/2026-05-19-zizmor-baseline/findings.sarif` as the source of truth and grep current workflow files to relocate.

### B. Triage the 4 secrets-inherit findings

In `.github/workflows/gemini-dispatch.yml` at lines 107, 121, 135, 149, the calls to `./.github/workflows/gemini-{review,triage,invoke,plan-execute}.yml` use implicit `secrets: inherit`. Replace each with an explicit `secrets:` block:

1. Open each called workflow (`gemini-review.yml`, `gemini-triage.yml`, etc.).
2. Identify which `secrets.*` references it actually uses (`grep -E '\$\{\{\s*secrets\.' .github/workflows/gemini-<name>.yml`).
3. In `gemini-dispatch.yml`, replace `secrets: inherit` with the explicit list:
   ```yaml
   secrets:
     SOME_KEY: ${{ secrets.SOME_KEY }}
     OTHER_KEY: ${{ secrets.OTHER_KEY }}
   ```

This is fixing only what the called workflow actually reads, not blanket inheriting everything.

### C. Verify zizmor re-scan

Run zizmor locally against the modified workflows and capture before/after counts:

```bash
# From the worktree root:
ln -s /Users/krisztiankoos/projects/learn-ukrainian/.venv .venv 2>/dev/null || true
# Find the zizmor binary used in CI:
grep -h "zizmor" .github/workflows/*.yml | head -3  # to confirm version
# Re-run zizmor on the changed workflows:
zizmor .github/workflows/ 2>&1 | tee audit/2026-05-19-zizmor-post-fix.txt
```

Capture in PR body: MEDIUM count before (21) → after (<5 expected; some will remain as documented-credential-needed cases).

### D. PR closeout

- Branch: `fix/2154-zizmor-medium-triage`
- Commits: split if useful (artipacked batch, secrets-inherit batch, comments for documented exceptions)
- Conventional commit messages per repo style
- `X-Agent: deepseek-v4-pro` trailer per AGENTS.md
- PR title: `fix(ci): zizmor MEDIUM triage — artipacked + secrets-inherit — closes #2154`
- PR body MUST include "What this PR does" + "Verifiable claims" sections (template below)
- Do NOT auto-merge

---

## Verifiable claims preamble (per #M-4 — Deterministic Over Hallucination)

| Claim | Deterministic tool | Output format in PR body |
|---|---|---|
| Zizmor MEDIUM count dropped | `zizmor .github/workflows/ 2>&1 \| grep -E 'medium\|MEDIUM'` before+after | Raw finding-count line, before vs after |
| Per-finding disposition documented | The PR description includes a table: filename:line → fix-applied OR documented-as-needed (with reason) | The table itself |
| Yamllint clean | `yamllint .github/workflows/` | Raw `0 errors` or equivalent line |
| Workflow syntax valid | `gh workflow list` and `gh workflow view <one>` for any modified workflow | Raw `gh` output snippet |
| Pre-commit passed | `git commit` | `✅ pre-commit passed` literal line |
| X-Agent trailer valid | `.venv/bin/python scripts/audit/lint_agent_trailer.py` | `✅ All N non-skipped commit(s) carry an X-Agent trailer.` |
| Ruff (covers any tooling changes) | `.venv/bin/ruff check` | `All checks passed!` |
| Scoped review (no scope creep) | The PR description includes a "Scope checks" section confirming only `.github/workflows/*` + the audit re-scan output touched | Itemized list |

**"I checked X" without one of the above artifacts in the PR body is a hard fail.** The orchestrator will reject the PR and ask you to re-run with evidence.

---

## Halt / escalate triggers

| Trigger | Action |
|---|---|
| Zizmor binary not on PATH and not installable in <5 min | Use the zizmor GitHub Action invocation as the verification source. Don't get blocked. |
| Workflow downstream-credential analysis requires running the workflow to know | Default to the SAFE choice: keep credentials, add the documented-exception comment. Do NOT remove credentials speculatively. |
| Finding count drops by less than 10 of 21 | Halt, write status to orchestrator. The triage was too conservative or the auto-fixer didn't catch what it should. |
| Test (pytest) or Frontend (build + vitest) fail on the PR | These touch workflows; ensure the changes don't break CI semantics. If they do, halt + diagnose. |
| `review / review` workflow fails | EXPECTED — that workflow is broken-env per #2126. Skip; orchestrator will admin-merge if everything else is green. |
| Any blocker requiring user input | Write status to `docs/session-state/` — do NOT push a partial PR. |

---

## Out of scope (do NOT touch in this PR)

- The 79 zizmor suppressed/auto-fixable findings (low-severity, separate triage)
- Pinning workflow uses (already shipped in PR #2152)
- Changing zizmor's CI gating policy from advisory to blocking (separate decision)
- Any non-workflow code changes

---

## Refs

- Issue: [#2154](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2154)
- Adoption commit: `7a8c9e2af6`
- Predecessor SHA-pin work: PR #2152, commits `fd4b89f18d` / `e63df4593b`
- Zizmor docs: https://docs.zizmor.sh/audits/#artipacked + https://docs.zizmor.sh/audits/#secrets-inherit
- Baseline forensics: `audit/2026-05-19-zizmor-baseline/`
- Known broken CI check: #2126 (`review / review` — Gemini-auth env missing — advisory, expect to fail)
- Brief for the immediate-predecessor Codex dispatch (reference for verifiable-claims preamble style): `docs/dispatch-briefs/2026-05-19-2155-wiki-coverage-gate-codex.md`
