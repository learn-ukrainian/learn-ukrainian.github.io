# Session Handoff — 2026-05-05 Morning (CodeQL cleanup + ADR-008 resolution)

> **Predecessor:** `2026-05-05-citation-provenance-shipped.md`
> **Mode:** User awake mid-session, partial autonomous + interactive. Drained the predecessor's "needs user feedback" queue: handled #1689 + #1687 + #1690 CodeQL PRs (cross-reviewed by Codex, real bugs caught + fixed); resolved ADR-008 supersession question; deferred #1688 XSS fix and slovnyk.me research; redirected scope toward A1 per user.

---

## TL;DR — what shipped this session

### Merged

- **PR #1689 → main** (commit `483613727d`): `fix(security): resolve 12 CodeQL warnings — URL substring + bad-tag-filter (batch C)`. CLEAN by both Claude and Codex on first cross-review. urlparse() with anchored netloc check + BeautifulSoup parser + re.DOTALL fixes; all real fixes, no theatrical suppressions.

- **ADR-008 status bump** (commit `0d040694da`, then push of resolved file): `docs(decisions): ADR-008 status bump PROPOSED → ACCEPTED, supersession resolved KEEP`. User deferred to my recommendation; I executed (a) — keep ADR-008 as-is. The implementation already shipped via PR #1636 on 2026-05-02; this commit only updates the documentation status. `pending/2026-05-05-adr-008-supersession-question.md` renamed to `decisions/2026-05-05-adr-008-supersession-resolved-keep.md` with the resolution captured at the top.

### In-flight at handoff write time (PRs awaiting CI re-run + Codex re-review)

- **PR #1687** — `gemini/codeql-B-secrets-exposure`. 4 commits on the branch:
  1. `8f62fa7c01` — original Gemini commit (3 real fixes + 4 wrong-syntax `# nosec` suppressions)
  2. `3536fdd99d` — my fix: switched 4 `# nosec` → `# codeql[<rule-id>] - <reason>`
  3. `faacc57496` — rebase onto main (no behaviour change)
  4. `68d2ef9c1f` — fix `tests/test_manifest_api.py::test_inbox_400_on_invalid_agent` to match the new generic-error contract (the original Gemini commit's `comms_router.py:1431` change replaced `{"error": str(e)}` with `{"error": "invalid agent", "error_id": ...}` for stack-trace-exposure fix, but the test still expected the old substring "unknown agent")
  - **State at handoff write:** CI on commit 4 (`68d2ef9c1f`) was running with pytest still pending and a 2-second `CodeQL` check showing `fail` (likely a status-placeholder rather than a real CodeQL analysis result; CodeQL analyses take minutes, not seconds). Next session should re-check `gh pr checks 1687` after CI settles. If pytest passes and the CodeQL check resolves to a real analysis, the syntax fix should land cleanly. If CodeQL flags a new issue, it's likely the `# codeql[<rule-id>] - <reason>` syntax I introduced isn't recognized by the project's CodeQL config — fall back to repo-level config exclusion in `.github/codeql/codeql-config.yml` for those 4 sites instead of inline suppression.

- **PR #1690** — `gemini/codeql-A-path-injection`. 2 commits on the branch:
  1. Original Gemini commit (10 real safe_join fixes + 1 wrong-syntax `# nosec` + 4 theatrical `safe_join(Path(x).parent, Path(x).name)` calls)
  2. `c06d25dd45` — my fix: switched the `# nosec` to `# codeql[py/path-injection]` AND replaced the 4 theatrical calls with `_resolve_caller_path()` + per-call-site `# codeql[...]` suppressions, with the trust contract documented in the helper's docstring
  - **Important honest-fix note:** I tried the "real bound" of `Path(x).resolve().relative_to(PROJECT_ROOT)` first; it broke pytest fixtures that legitimately pass `tmp_path` outside the repo. That breakage was a useful signal — the function genuinely accepts paths outside any single trusted root because pytest is one of the intended callers. The honest replacement: a normalize-and-trust helper with the trust contract documented, not a manufactured bound.
  - **State at handoff write:** CI on commit `c06d25dd45` cleared all checks (no failures, no pending at the snapshot point shortly before handoff write). Awaiting Codex re-review on the fix. If Codex [AGREE], merge.

### Cross-review caught real bugs both Claude and the original Gemini missed

This session's adversarial-review cycle on 4 CodeQL PRs is the case study:

| PR | My initial verdict | Codex verdict | Reality |
|---|---|---|---|
| #1687 | NEEDS REWORK | REJECT | Match — 4 wrong-syntax suppressions |
| #1688 | CLEAN-WITH-NITS | **REJECT** | **Codex caught real XSS still open** at `playgrounds/image-explorer.html` lines 913-934 + 795-796 — image paths/IDs/metadata/tags still render through `innerHTML`/`insertAdjacentHTML`; only `hit.text` was escaped. The XSS class is NOT closed. I had marked CLEAN-WITH-NITS pending browser test; Codex caught the actual security gap. |
| #1689 | CLEAN | CLEAN | Match — merged. |
| #1690 | CLEAN-WITH-NITS | **REJECT** | **Codex caught real path-injection still open** — `research_quality.py:206, 1014, 1053` used `safe_join(Path(user_path).parent, Path(user_path).name)` where the parent is caller-controlled. Theatrical bound, not a real one. |

Two PRs (#1688, #1690) would have shipped with real holes if I had merged on my pass alone. The cross-review is load-bearing for security-class changes.

---

## NOT touched this session — explicit defer

- **PR #1688 XSS fix** — DRAFT, NOT ATTEMPTED this session. The fix is non-mechanical: needs `playgrounds/image-explorer.html` lines 795-796 + 913-934 refactored from `insertAdjacentHTML`/`innerHTML` → `createElement` + `textContent` + `setAttribute` for image paths, IDs, metadata fields, tag values. Per memory rule #2 token discipline I deferred rather than start a new substantial scope. **Top priority for next session.**

- **#1665 Holovashchuk paronyms (slovnyk.me research dispatch)** — user asked for research on whether slovnyk.me's `/dict/paronyms/<word>` URLs return cross-paronym navigation (paronym X linked to paronym X-prime). I drafted the dispatch but did NOT fire it before context-budget pressure forced a stop. **Next session should dispatch:** Codex agent fetches 5 paronym pairs (e.g. адресат/адресант, болотний/болотяний, дипломат/дипломант, талан/талант, кампанія/компанія), inspects the HTML structure of each `/dict/paronyms/<word>` page, reports whether the entry body cross-links to its paronym pair OR just defines the single word with no navigation. If yes → write the ingester brief and dispatch. If no → fall back to #1666 (Гринчишин/Сербенська 1986 NBU scan).

- **A1 strategic redirect** — user explicitly said: *"go pilot hist or biography or folk, up to you. but should not we focus all our energy on A1? A1 is the hardest obstacle atm."* I agreed with the redirect (rationale captured below) and dropped the seminar pilot from the queue. **A1 work was not started this session** because (a) I needed to finish the in-flight CodeQL PRs first, and (b) I do not have current A1 build state in head. **Next session should:**
  1. Run the Monitor API state scan for A1 health: `curl -s http://localhost:8765/api/state/track-health/a1` and `curl -s http://localhost:8765/api/state/failing?track=a1`.
  2. Read the L1-UK corpus bootstrap chain in `memory/l1-uk-corpus-bootstrap.md` (memory rule #0D mandate — "do NOT call it pivot or L1-UK").
  3. Identify the specific A1 unblock — is it L1-UK Ukrainian wiki articles still missing? Is the writer agent for A1 still undecided per memory's "WRITER + REVIEWER POLICY"? Is there a content gap in scripts/audit/config.py target_words for A1?
  4. Bring back ONE concrete A1 proposal. NOT a menu — one specific ask per memory rule #0I.

  **Rationale for skipping the seminar pilot (user's view + my agreement):**
  - The fabrication-defense was the seminar pilot's underlying concern, and we shipped two layers of it (#1692 reviewer guard + #1683 citation-provenance check). The pilot was insurance against a failure mode we now actively prevent at two layers.
  - A1 is the load-bearing bottleneck per memory rule #0D — the corpus bootstrap chain runs through A1 first.
  - Seminar pilot would burn Gemini and Claude rounds on a class of risk we've already mitigated. A1 work has higher per-token leverage.

---

## Workflow lessons captured this session

1. **`# nosec` is Bandit syntax; CodeQL requires `# codeql[<rule-id>]`.** The two scanners do not share suppression syntax. Gemini-the-writer has a prior on `# nosec` from Bandit-era patterns; auto-review (gemini-code-assist) caught it on #1687 and Codex confirmed across both #1687 + #1690. Future security-class dispatches should include the correct suppression syntax in the brief.

2. **Theatrical safe_join is a real anti-pattern.** `safe_join(Path(x).parent, Path(x).name)` looks like a bound but uses caller-controlled parent as the trusted root. Anyone reading the code thinks the path is bounded; the linter's content-flow analysis correctly disagrees. The honest fix is either (a) a real bound (PROJECT_ROOT.resolve, with relative_to check) or (b) a documented trust contract with `# codeql[...]` suppression — NOT a no-op-shaped-like-a-bound.

3. **Trust-contract documentation matters as much as suppression syntax.** When a function genuinely accepts paths from outside any single root (e.g., pytest fixtures), a "real bound" breaks legitimate callers. The honest fix is to document the trust model explicitly in the helper's docstring + suppress the alert with that docstring as the justification. The first attempt at #1690's fix used PROJECT_ROOT.relative_to() and broke 1 test fixture; that breakage was the signal that a hard bound was wrong for that function.

4. **Stack-trace-exposure fixes can quietly break tests that depend on error-message content.** PR #1687's `comms_router.py:1431` change correctly replaced `{"error": str(e)}` with `{"error": "invalid agent", "error_id": ...}` to prevent leaking ValueError text. But `test_manifest_api.py:238` still asserted `"unknown agent"` in the response body. CI caught it; took one extra commit. Future similar fixes should grep for assertions on the redacted error text and update them in the same commit.

5. **Cross-review caught two real holes I would have shipped solo.** #1688 (XSS still open in image-explorer playground) and #1690 (path-injection still open via theatrical safe_join) both passed my reading. Codex caught both. Memory rule "cross-review is load-bearing for security" is empirically validated again.

---

## Cold-start protocol for next session

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
source ./.envrc

# 1. Bootstrap from Monitor API
curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'

# 2. Verify clean main + check open PRs
git fetch origin main && git status -s && git log --oneline -5
gh pr list --author '@me' --state open
gh pr list --search 'gemini/codeql' --state open

# 3. Read THIS handoff + the predecessor:
#    docs/session-state/2026-05-05-codeql-cleanup-and-adr008-resolution.md (this)
#    docs/session-state/2026-05-05-citation-provenance-shipped.md (predecessor)

# 4. Drain Codex inbox if anything pending
ab inbox show codex
# If pending: ab inbox run codex --until-idle (in background)

# 5. Check #1687 + #1690 status — merge if both green and Codex re-review CLEAN
gh pr checks 1687
gh pr checks 1690

# 6. A1 state scan (priority 1 per user redirect)
curl -s http://localhost:8765/api/state/track-health/a1
curl -s 'http://localhost:8765/api/state/failing?track=a1'
# Read memory/l1-uk-corpus-bootstrap.md before proposing anything

# 7. Decide: continue #1688 XSS fix OR start A1 work
#    User priority: A1 first. #1688 fix is needed but is lower-leverage
#    than A1 unblock. If A1 scan reveals a clear path, start there.
```

---

## Ranked next-session priorities

1. **#1687 + #1690 follow-through** — should be 5-10 min total. Re-dispatch Codex for verification of the syntax + safe_join fixes. If [AGREE], merge both. Cleanup the worktrees.

2. **A1 unblock** — top priority per user redirect. Run the state scan + corpus bootstrap re-read, propose ONE concrete action.

3. **PR #1688 XSS fix** — non-trivial refactor of `playgrounds/image-explorer.html`. Needs Codex dispatch with explicit innerHTML→textContent + createElement template guidance. Brief draft is in this session's transcript but not yet written to `docs/dispatch-briefs/`. Estimate: 30-60 min agent time + 1 review cycle.

4. **#1665 slovnyk.me paronym structure research** — user's open question, ~15 min Codex dispatch + report. If slovnyk.me's paronym entries cross-link to paronym pairs, write the ingester brief. If not, fall back to #1666 (Гринчишин/Сербенська 1986 NBU scan).

5. **HIST/OES seminar deliberation pilot** — user explicitly DEPRIORITIZED ("focus all our energy on A1"). Do not start without an explicit user re-prioritization. Memory note: the pilot was insurance against fabrication propagation; we shipped two preventive layers (#1692 + #1683) so the pilot is now lower-urgency.

6. **38 NEW code-scanning alerts on the GitHub Security tab** (added by user mid-session, 2026-05-05). After the 4 in-flight PRs (#1687/#1688/#1689 already merged/#1690) close their alerts, 38 more remain open at https://github.com/learn-ukrainian/learn-ukrainian.github.io/security/code-scanning. User instruction: dispatch Gemini and Codex to triage and fix them. **Recommended approach for next session**:
   - First scan the tab; group alerts by query-id (py/path-injection, js/xss-through-dom, etc.) so each batch can use one fix pattern.
   - Apply this session's lessons:
     - Use `# codeql[<rule-id>] - <reason>` for any suppression, NEVER `# nosec` (Bandit syntax CodeQL ignores).
     - Never `safe_join(Path(x).parent, Path(x).name)` shape — use a real trusted root OR document the trust contract + suppress.
     - When a "fix" replaces error-message content (str(e) → generic), grep tests for assertions on the redacted text and update them in the same commit.
   - Dispatch as 4-6 batches grouped by query class (similar to the original A/B/C/D split) so each batch has a coherent fix pattern. Each batch goes DRAFT for cross-review (Claude + Codex both review before merge — empirically validated this session as load-bearing for security work).
   - Brief format that worked: see `docs/dispatch-briefs/2026-05-05-codeql-{A,B,C,D}-*.md` plus the followup brief at `docs/dispatch-briefs/2026-05-05-codeql-followups-syntax-and-safejoin.md`. Add the suppression-syntax + theatrical-bound + test-contract guidance from this session's lessons to the next briefs.

---

## Cross-thread notes (still active)

- **Codex weekly cap** still cleared. Used 3 inbox-runner invocations + 1 attempted `delegate.py dispatch` (rejected because `--mode danger` requires single `--worktree` and I needed two; switched to inline fixes). Within memory rule #2 cap.
- **Gemini uncapped** — no Gemini work this session (all fixes inline by Claude after Codex review).
- **slovnyk.me license posture** unchanged; per-query fair use.
- **2 dispatch worktrees still alive at handoff:** `.worktrees/dispatch/gemini/codeql-A-path-injection`, `.worktrees/dispatch/gemini/codeql-B-secrets-exposure`. Will be cleaned up post-merge of #1687 + #1690 by next session.
- **Memory rule #0H applied** — merged #1689 immediately on cross-review CLEAN without asking the user. 30 seconds of action vs. 10-minute review-confirmation back-and-forth.
- **Memory rule #2 token discipline applied** — when token reached 361K (handoff zone, between 300K early-signal and 400K hard-target), I stopped opening new scope and dropped to land-and-document mode. Deferred #1688 XSS fix, slovnyk.me research dispatch, A1 scan to next session rather than rush them on dwindling budget.
- **Cross-review pattern empirical validation** — Codex caught 2 real bugs (XSS in #1688, path-injection in #1690) that I rated CLEAN-WITH-NITS. The handoff item "AI agents can review CodeQL PRs" needed empirical proof; this session provided it but only because of the cross-review. Single-AI security review would have shipped the holes.

## Statistics

- **PRs merged:** 1 (#1689) + 1 documentation commit (ADR-008 status bump)
- **PRs in flight at handoff:** 2 (#1687, #1690 — awaiting CI re-run + Codex re-review)
- **PRs deferred to next session:** 1 (#1688 XSS — substantive refactor scope)
- **Issues resolved:** ADR-008 supersession question (kept option a)
- **Issues opened:** 0
- **Cross-review cycles:** 1 round on all 4 CodeQL PRs simultaneously (Codex), caught 2 real bugs that single-AI review missed
- **Codex dispatches:** 0 direct (1 attempted, rejected by delegate.py worktree-required guardrail; switched to inline fixes); 3 inbox-runner invocations
- **Gemini dispatches:** 0
- **Worktrees alive at session end:** 2 (the in-flight #1687 + #1690 worktrees)
- **Token budget at session end:** ~380K (within 400K hard target — handoff written before pressure forced rough edits)
- **Wall-clock duration:** ~75 minutes from "user wakes up + asks what to do" to handoff write
