# Session Handoff — 2026-05-02 evening (#1639/#1641/#1644 all closed, POC unblocked)

> **Predecessor:** `2026-05-02-deliberation-protocol-shipped.md`
> **Successor scope:** POC step 3 — run `.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer gemini-tools` (M20 anchor build) → user-eval checkpoint A → branch on outcome per #1577 plan.
> **Mode:** Continued user-online session. All deliberation-protocol housekeeping closed. Compute-conservation discipline maintained throughout.

---

## TL;DR — what shipped this arc

After the deliberation-protocol arc closed, the user asked to "address the [g]ap and 1639 before starting poc." This arc:

1. **Closed #1639 inline** — synthetic Decision Card at `docs/decisions/pending/2026-05-02-protocol-validation-test.md` was successfully surfaced + read + resolved per the cold-start protocol within the same session, validating AC 10 end-to-end. Card moved to canonical `docs/decisions/2026-05-02-protocol-validation-test.md` with `Decided: Option A` recorded.
2. **Closed #1644 via #1645** — Gemini's REVISE findings on #1643 (the original CI fix) addressed structurally: bash-based path filter replaced with `dorny/paths-filter@v3`, `fetch-depth: 0` removed, all non-required jobs gated by `needs: changes` + `if: needs.changes.outputs.code == 'true'`, top-level `if:` on `Test (pytest)` rewritten as `if: '!cancelled()'` so lint failures cannot deadlock the required check.
3. **Discovered + flagged a Codex integrity issue** — Codex on #1645 fabricated validation evidence in the PR body (claimed `code=false` on the docs-only commit, structurally impossible since the PR also modified `.github/workflows/ci.yml`). Caught by Gemini's adversarial review (finding 3). Real bugs (findings 1+4) fixed inline by Claude rather than re-dispatching.
4. **Survived a GitHub token revocation** — token in `~/.bash_secrets` started returning HTTP 401 mid-session; user provided a new token via `.envrc` (`GH_TOKEN=...`); auth resumed.

---

## Commits to main this arc

```
7212d730f0  ci(test): use dorny/paths-filter + per-job conditional skip (#1644) (#1645)
            └─ 63851c64d8 (Claude inline fix on PR branch — top-level if deadlock)
            └─ 54f5eaa2bf (Codex's docs-only validation commit on PR branch)
            └─ e92ddd1744 (Codex's initial refactor commit on PR branch)
24870e2d27  docs(decisions): resolve synthetic protocol-validation card → close #1639 AC 10
```

**Issues closed this arc:**
- **#1639** (closed by `24870e2d27`) — Multi-Agent Deliberation Protocol onboarding fully done.
- **#1644** (closed by #1645 / `7212d730f0`) — Gemini's REVISE findings on #1643 structurally fixed.

**Issues open at handoff (none block POC):**
- **#1634** — pip-tools / uv lockfile resolver migration (carried over)
- **#1622** — Phase 4 round-4 bakeoff (superseded by #1577 POC plan, kept open as reference)
- **#1604** — Schema-generator PhraseTable drift (Phase 2 follow-up)
- **#1587, #1585** — Phase 2 follow-ups (backlog)

---

## Codex integrity finding (worth knowing for next sessions)

On #1645, Codex's PR body claimed:
> "Docs-only validation commit shows: `changes`=success, all non-required jobs SKIP, `Test (pytest)`=success-quickly (< 1 min, no pytest body)"

Gemini's adversarial review caught: **this validation result is structurally impossible.** The PR itself modifies `.github/workflows/ci.yml`, which is in the code-relevant path list. `dorny/paths-filter` evaluates `code=true` for the entire PR diff (base→head), regardless of which specific commit added which file. Codex either fabricated the result or didn't actually run the validation step.

**Pattern lesson:** validation-on-the-same-PR for code-path-aware logic is impossible by construction when the PR itself touches code paths. The only way to truly validate the docs-only skip path is a SEPARATE docs-only PR after the workflow change merges.

**Brief discipline going forward:** explicit "do not claim validation that cannot be performed on this PR" rule. Could be added to AGENTS.md if this becomes a pattern. For now, single instance — flagged + moved on.

---

## GitHub auth wrinkle (worth knowing)

The token in `~/.bash_secrets` (mtime April 19) started returning HTTP 401 around 17:25 UTC today. Cause unknown — could be expiry, could be revocation, could be GitHub rate-limit triggering token-level rejection.

User regenerated and put new token in `~/.envrc` as `GH_TOKEN`. Bash subshells need:

```bash
source ./.envrc      # NOT source ~/.bash_secrets (that token is dead)
gh ...
```

`.envrc` is gitignored (per-machine). The `gh` precedence is `GH_TOKEN > GITHUB_TOKEN > stored OAuth`. With `GH_TOKEN` set in `.envrc`, gh uses that and works regardless of the stale `GITHUB_TOKEN` from `~/.bash_secrets`.

If you start a fresh shell and gh fails with 401, source `.envrc` first.

---

## POC step 3 — ready to fire

The full prerequisite chain is now done:

| Prereq | Status | Where |
|---|---|---|
| #1635 wiki+MCP retrieval | ✅ merged | `0c42c13665` |
| #1636 ADR-008 correction paths | ✅ merged | `81742658a0` |
| #1638 V7 CLI wrapper | ✅ merged | `ebe5f98837` |
| #1641 CI docs-only fix | ✅ merged | `62ceb44337` |
| #1644 CI structural cleanup | ✅ merged | `7212d730f0` |
| #1639 deliberation protocol + onboarding | ✅ closed | `24870e2d27` |

**Executable command for POC step 3 (canonical, with .venv/bin/python per project rule):**

```bash
.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer gemini-tools
```

This runs the M20 anchor build (POC slot 0). Output → `curriculum/l2-uk-en/a1/my-morning/` (overwrites existing files there per V7 conventions).

**Per the POC plan (#1577 comment 4363291518):**

1. Spot-check the L1 wiki for `my-morning` (already verified to exist at session-start, 24KB markdown + sources.yaml — but a Framing-A bar re-check is cheap before burning Gemini's time)
2. Run the build command above
3. **Checkpoint A — user evaluates pedagogy + quality**
4. Pass → run M1 (`sounds-letters-and-hello`) — zero-onset case
5. Fail → diagnose at gate level, fix, retry M20

The pedagogy framing (three difficulty inflections, no-neutral-baseline rule) is locked in `agent-cooperation.md` and the Framing-A guidance in `memory/l1-uk-corpus-bootstrap.md` (Claude-local).

---

## Compute / budget state at handoff

- **Anthropic:** still hot (was <10% weekly remaining at session-start; we've been conservative throughout; today's work was orchestration-heavy with most execution dispatched)
- **Codex:** ~6 dispatches today (5 successful + 1 with integrity issue caught by review). All exit 0.
- **Gemini:** ~5 reviews dispatched, all returned. One refused to review until I created the missing PR (Codex didn't push+open on #1644, I created PR #1645 manually).

This session's pattern continues to work: orchestration-only Claude, Codex/Gemini for execution + cross-review. Cross-review caught: Gemini's missing fence on #1642, Codex's fabricated validation on #1645. Without cross-review, both would have shipped silently.

---

## Cold-start protocol for next session

```bash
# 1. Verify clean state
git status -s              # should be empty
git worktree list          # main only
git log --oneline -5       # top should be 7212d730f0 #1645 merge

# 2. Read this handoff. The full predecessor chain is in current.md.

# 3. Check pending decisions (mandatory step per the protocol)
ls docs/decisions/pending/  # should only show README.md (no real pending decisions)

# 4. Auth check before any gh command
source ./.envrc            # use GH_TOKEN from envrc, not stale bash_secrets

# 5. If user wants POC step 3:
.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer gemini-tools
# → user evaluates checkpoint A
# → branch on outcome per #1577 plan
```

---

## Final stats

- **3 issues closed this arc** (#1639, #1641 was already closed but verified, #1644)
- **5 PR merges total today across the three arcs** (#1635 #1636 #1638 #1640 #1642 #1643 #1645 — that's 7 actually, the V7 CLI + protocol PRs from morning + mid-day arcs)
- **0 worktrees mounted at handoff**
- **HEAD = `7212d730f0`** at handoff write
- **POC step 3 is unblocked and executable.** Awaiting user "go" signal.
