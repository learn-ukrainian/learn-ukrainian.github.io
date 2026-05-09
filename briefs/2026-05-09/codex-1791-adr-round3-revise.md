# Codex CLI — PR #1791 Decision Graph ADR — apply Claude's round-3 REVISE findings

## TL;DR

PR #1791 (`docs(adr): Decision Graph view ADR (PROPOSED)`) on branch `gemini/decision-graph-adr` already addressed Gemini-code-assist's round-1 findings (Gemini's commit `442bf5e024`, "Issues 1-5, [OBJECT] resolved"). **Today's Claude round-3 adversarial review surfaced 2 NEW BLOCKER findings + 3 still-open items prior reviewers missed.** Apply them.

Full review at: **`audit/claude-review-1791-decision-graph-adr-2026-05-09/REVIEW.md`** (now on main, 347 lines, every claim tool-backed).

Estimated diff: **30–50 LOC** in `docs/decisions/pending/2026-05-09-decision-graph-view.md` (the ADR file).

---

## Mandatory orientation (#M-4 — deterministic over hallucination)

Before any edits:

1. **`docs/best-practices/deterministic-over-hallucination.md`** — every claim in the revised ADR + your PR body MUST be tool-backed (file/line citations, quoted SQL output, quoted CLI output).
2. **`audit/claude-review-1791-decision-graph-adr-2026-05-09/REVIEW.md`** — Claude's round-3 review. Read end-to-end. The findings are spec'd with exact file/line + remediation language.
3. **The ADR being revised:** `docs/decisions/pending/2026-05-09-decision-graph-view.md` at `origin/gemini/decision-graph-adr` head (`442bf5e024`). Read every line.
4. **The bridge code the ADR claims about:** `scripts/ai_agent_bridge/_channels_cli.py:1254-1260, 1278-1283, 1417, 1436, 1456` — these are the lines Claude cited as the source-of-truth for marker semantics + convergence detection.
5. **The live `channel_messages` schema and data:** verify by querying. Claude already did this; reproduce the queries to confirm:
   ```sql
   -- Marker prevalence
   SELECT body LIKE '%[AGREE]%', COUNT(*) FROM channel_messages
   WHERE body LIKE '%[AGREE]%' OR body LIKE '%[DISAGREE]%' OR body LIKE '%[OPTION]%' OR body LIKE '%[OBJECT]%' OR body LIKE '%[DEFER]%';
   ```
   The DB lives at the path bridged from `MESSAGE_DB`.
6. **Multi-UI ADR for context on `agent_family`:** `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md`.
7. **Project ADR style:** `ls docs/architecture/adr/` — read one for tone/template alignment.

## Verifiable claims this work will produce + the tool

| Claim | Tool | Evidence format |
|---|---|---|
| "Live DB has 139 `[DISAGREE]` occurrences" | `sqlite3 <broker.db> "SELECT COUNT(*) FROM channel_messages WHERE body LIKE '%[DISAGREE]%'"` | Quoted SQL output in PR body |
| "Broker uses `endswith('[AGREE]')` strict matching" | `grep -nE "endswith.*\[AGREE\]|\.endswith\\(.\\[AGREE\\]" scripts/ai_agent_bridge/_channels_cli.py` | Quoted source line |
| "ADR now acknowledges `[DISAGREE]` as the canonical pushback marker" | `grep -nE "\[DISAGREE\]" docs/decisions/pending/2026-05-09-decision-graph-view.md` | Quoted post-edit line |
| "ADR uses `from_agent` (or unique participant_id), not `agent_family`, for column keys" | `grep -nE "agent_family|from_agent|participant_id" docs/decisions/pending/2026-05-09-decision-graph-view.md` | Quoted post-edit lines |
| "Pre-commit clean" | `.venv/bin/pre-commit run --files docs/decisions/pending/2026-05-09-decision-graph-view.md` | Quoted output |

If any tool query disagrees with what the ADR claims, fix the ADR — don't rationalize the divergence.

---

## The 5 revisions (apply ALL)

From Claude's round-3 review §1 ("Required revisions before ACCEPTED") and §3 (Independent findings):

### Revision 1 — IND-1 BLOCKER: marker set conflicts with broker + live data

The ADR's Q3 lists `[AGREE], [OPTION], [OBJECT], [DEFER]` as canonical four markers. The broker uses `[AGREE]` + `[DISAGREE]`. Live DB: 139 `[DISAGREE]` vs 4 total for `[OPTION]+[OBJECT]+[DEFER]`.

**Edit:** Q3 marker set. Add `[DISAGREE]` as the explicit non-converging counterpart to `[AGREE]`. Either drop `[OPTION]/[OBJECT]/[DEFER]` to a "future markers" footnote OR document where each originated (only `[OBJECT]` has documented use, in the Multi-UI ADR; `[OPTION]` and `[DEFER]` have zero canonical use).

**Also fix the regex.** Current ADR regex `AGREE(?:D)?` matches `[AGREED]` which has zero DB occurrences. Drop the `(?:D)?` — match `[AGREE]` strictly.

### Revision 2 — IND-1 secondary: convergence-detection wording

Q3 says "anywhere in body, last-wins." Broker uses `text.strip().endswith("[AGREE]")` (`_channels_cli.py:1436, 1456`). These differ on the case `"I don't [AGREE] with that. [DISAGREE]"` — the broker's exact case it guards against.

**Edit:** Q3 + Q4. Clarify: "Convergence triggers when the LAST line of the latest round-N message from each distinct agent ends with `[AGREE]` after `.strip()`." Cite the broker line `_channels_cli.py:1436` so the ADR pins to the implementation.

### Revision 3 — IND-2 BLOCKER: `agent_family` schema dependency

Frontmatter line 8 says "independent of `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md`." Q1/Q2/Q4/Q5 use `agent_family` as the column key. **`agent_family` does not exist as a column in current `channel_messages`** — it's a Multi-UI-ADR-proposed addition (line 109).

**Edit:** EITHER:
- (a) Pivot to `from_agent` (which IS a current schema column) and add a note: "Once Multi-UI ADR lands, columns can be re-keyed by `participant_id`."
- (b) Retract the "independent of" claim in the frontmatter and add `Blocked-by: docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md` (which Multi-UI lands `agent_family`/`participant_id`).

Option (a) is preferable — it lets the Decision Graph ship today.

### Revision 4 — G2: unique agent identifiers for columns

Multi-UI ADR contemplates `claude:cli` + `claude:desktop` posting in the same thread. ADR's Q2 hard-codes columns as `agent_family` — collapses both into one column, last-write-wins.

**Edit:** Q2. Use `participant_id` (Multi-UI) OR an interim `(agent_family, ui_surface, instance_id_short)` triple as the column key. Label by `agent_family:ui_surface`. Forward-compat with Multi-UI ADR.

### Revision 5 — G3: high-risk-track override on convergence

`agent-cooperation.md:210-222` mandates that on HIST/BIO/ISTORIO/LIT/OES/RUTH tracks, `[AGREE]` consensus FORCES a Decision Card prompt (because correlated bias makes consensus unsafe on those tracks). The ADR's Q4 says convergence "auto-suggests Decision Card creation" — should be FORCE on high-risk tracks.

**Edit:** Q4. Add a paragraph: "Exception: for threads tagged with a high-risk track (HIST/BIO/ISTORIO/LIT/OES/RUTH per `agent-cooperation.md:210-222` Mechanism A), convergence triggers a forced Decision Card prompt rather than a soft auto-suggest."

### Revision 6 — G4: drawer cross-agent context

Q5 says drawer "displays the full-thread transcript filtered to that specific `agent_family`." Open-Question 2 (line 152) defers the single-message vs full-thread choice. Per Gemini's finding: when a user clicks Codex's `[OBJECT]`, they want to see what Gemini said in the prior round that Codex was objecting to — but the proposal explicitly filters out the antagonist.

**Edit:** Q5. Default the drawer to **same-round all-agents** plus the clicked agent's prior posts in earlier rounds, with a per-agent filter toggle. Resolve Open-Question 2.

---

## Worktree instructions (mandatory — `delegate-must-use-worktree.md`)

You will be invoked via `delegate.py dispatch --agent codex --mode danger --worktree --base gemini/decision-graph-adr`. The worktree branches from `origin/gemini/decision-graph-adr` at the current ADR head (`442bf5e024`). The auto-derived branch is `codex/1791-adr-round3-revise`.

**Do NOT push to `gemini/decision-graph-adr` directly.** That's Gemini's branch. Instead push your commits to your own branch (`codex/1791-adr-round3-revise`) and **open a new PR titled `docs(adr): Decision Graph view ADR — round-3 revisions (PROPOSED, supersedes #1791)`**. Reference #1791 in the body. The orchestrator will close #1791 with a comment pointing at the new PR.

---

## Workflow (numbered)

1. **Worktree setup** — confirmed by the dispatcher. Verify `pwd` is the worktree, branch is `codex/1791-adr-round3-revise`, base is `origin/gemini/decision-graph-adr`.
2. **Read** the round-3 review end-to-end: `audit/claude-review-1791-decision-graph-adr-2026-05-09/REVIEW.md`.
3. **Read** the current ADR at `docs/decisions/pending/2026-05-09-decision-graph-view.md`.
4. **Verify the live data** referenced in §3 of the review (run the SQL queries). Quote the output in your PR body.
5. **Apply the 6 revisions** above. Keep edits surgical — don't rewrite untouched sections.
6. **Lint** — `.venv/bin/pre-commit run --files docs/decisions/pending/2026-05-09-decision-graph-view.md`.
7. **Commit** — conventional message:
   ```
   docs(adr): apply round-3 REVISE findings (#1791)

   - IND-1: marker set acknowledges [DISAGREE] (139 DB occurrences) as
     canonical pushback marker; demote [OPTION]/[OBJECT]/[DEFER] to
     "future markers" footnote (4 total DB occurrences).
   - IND-1 secondary: convergence wording aligned with broker's strict
     endswith('[AGREE]') matching (_channels_cli.py:1436); regex no
     longer matches [AGREED] (zero DB occurrences).
   - IND-2: pivoted column key from agent_family to from_agent so the
     view ships today; forward-compat note for Multi-UI ADR's
     participant_id.
   - G2: column-key triple forward-compat with Multi-UI's claude:cli +
     claude:desktop case.
   - G3: high-risk-track override forces Decision Card prompt on
     HIST/BIO/ISTORIO/LIT/OES/RUTH per agent-cooperation.md Mechanism A.
   - G4: drawer defaults to same-round all-agents plus clicked agent's
     prior posts; per-agent filter toggle. Open-Question 2 resolved.

   Supersedes #1791. Closes round-3 review at
   audit/claude-review-1791-decision-graph-adr-2026-05-09/REVIEW.md.

   Co-Authored-By: Codex (gpt-5.5) <noreply@anthropic.com>
   ```
8. **Push** — `git push -u origin codex/1791-adr-round3-revise`.
9. **PR** — `gh pr create --title "docs(adr): Decision Graph view ADR — round-3 revisions (PROPOSED, supersedes #1791)" --body ...` with #M-4 evidence per claim, list each of the 6 revisions ticked with file/line + before/after snippet.
10. **NO auto-merge.** Stop. Orchestrator will close #1791 + dispatch Claude round-4 review.

---

## Done criteria

- All 6 revisions applied to the ADR with surgical edits.
- Live SQL output proves marker prevalence claim in the PR body.
- Pre-commit clean.
- New PR opened, **NOT merged**.
- Branch `codex/1791-adr-round3-revise` pushed.

## Escalation

If a revision conflicts with another open ADR in `docs/decisions/pending/` that you discover during reading (e.g., Multi-UI), STOP, post a comment on PR #1791 with the conflict + proposed reconciliation, exit cleanly.

If the SQL query disagrees with the review's claimed numbers, STOP, post the actual numbers, ask for direction. Do NOT silently use different data than the review.
