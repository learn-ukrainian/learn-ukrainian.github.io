# Adversarial review — PR #1835 Decision Graph ADR (round 4)

**Reviewer:** Claude headless (Opus 4.7, xhigh, read-only)
**Date:** 2026-05-09
**Target PR:** #1835 — `docs(adr): Decision Graph view ADR — round-3 revisions (PROPOSED, supersedes #1791)`
**PR head SHA:** `1116e3054cb433d488ae4eba8a3ef1a433a21aa0`
**PR base merge-base:** `b94150a86f` (origin/main snapshot at 2026-05-08 evening)
**Target file:** `docs/decisions/pending/2026-05-09-decision-graph-view.md` at PR head (164 lines)
**Round-3 review verified against:** `audit/claude-review-1791-decision-graph-adr-2026-05-09/REVIEW.md` on `origin/main`
**Scope:** Verify the 6 round-3 revisions were correctly applied + hunt for new issues introduced by the surgical edits. Not a re-litigation of round-3 findings.

---

## §1 — Verdict

**APPROVE-WITH-NITS**

All 6 round-3 revisions are correctly applied at PR head. Two waivable round-3 nits (IND-4 stale `Epic` framing, IND-5 snapshot-date footnote) are also resolved as a side-effect of the marker-set rewrite. IND-3 was upgraded from a known-debt acknowledgement to a stronger fix where the view now adopts the broker rule rather than acknowledging divergence — improvement on what was asked.

**One non-blocking nit:** the ADR cites `scripts/ai_agent_bridge/_channels_cli.py:1413` (lines 79 + PR body), which is correct at the PR's merge-base `b94150a86f` but will resolve to a comment, not the convergence check, after the PR merges into current `origin/main` (the upstream broker file shifted by ~49 lines between PR base and current main — see §3.N1). Two fixes possible; both small.

**Recommendation:** Merge #1835 → user flips PROPOSED → ACCEPTED. The line-number drift can be addressed in a tiny follow-up or accepted as normal documentation decay.

---

## §2 — Per-revision verification

All quotes are from `docs/decisions/pending/2026-05-09-decision-graph-view.md` at PR head SHA `1116e3054c`.

### Revision 1 / IND-1 marker set — APPLIED CORRECTLY

> Line 79: `* **Canonical Markers:** `[AGREE]` and `[DISAGREE]`. The broker prompt requires agents to end round replies with one of these markers …`
> Line 80: `* **Future/ADR-specific Markers:** `[OPTION]`, `[OBJECT]`, and `[DEFER]` may be displayed when present, but they are not canonical broker markers today. Current live DB evidence shows … rare compared with `[DISAGREE]`; `[OBJECT]` is documented in the Multi-UI ADR as a user pushback marker.`
> Line 82: regex `\[(AGREE|DISAGREE|OPTION|OBJECT(?:[^\]]*)?|DEFER)(?:\b[^\]]*)?\]` — `DISAGREE` added; `AGREE(?:D)?` removed.
> Line 86: `| `[DISAGREE]` | `DISAGREE` | `[DISAGREE]` |` row added to mapping table.

Concur. The four-marker set the round-3 review flagged as unsupported (`[OPTION]`/`[OBJECT]`/`[DEFER]` total = 4 DB occurrences vs `[DISAGREE]` = 139) is now correctly demoted to "future/ADR-specific display"; `[DISAGREE]` is elevated to canonical alongside `[AGREE]`. Regex no longer matches `[AGREED]` (zero DB occurrences). Quick regex trace: input `[AGREED]` → `\[` matches `[`, alternation tries `AGREE` (matches), then `(?:\b[^\]]*)?` requires word-boundary which fails after `E→D` (both word chars), group goes empty, then expects `\]` but gets `D` → no match. Correct.

### Revision 2 / IND-1 secondary convergence wording — APPLIED CORRECTLY

> Line 89: `* **Position Requirement:** Display extraction may find markers anywhere in the body, but convergence uses the broker-compatible rule: the latest round message must end with literal `[AGREE]` after `.strip()`.`
> Line 90: `* **Multiple Markers:** … Protocol convergence still follows strict tail-anchored `[AGREE]`, so a message such as `I don't [AGREE] with that. [DISAGREE]` is not converged.`
> Line 100 (Q4): `A thread is converged when every distinct current-schema participant (`from_agent`) that has posted in the thread has a latest round-N message whose stripped body ends with literal `[AGREE]`. Earlier-round content does not factor in.`
> Line 109 (Q4 Rationale): `The Decision Graph's closing-out indicator must treat the broker's strict `endswith("[AGREE]")` rule as authoritative for protocol convergence.`

Concur. The "anywhere in body / last-wins" wording is replaced with strict tail-anchored `[AGREE]` after `.strip()`, matching `_channels_cli.py:1413` (`text.strip().endswith("[AGREE]")` at PR head SHA — verified directly in §5.E3). The exact false-positive pattern the broker explicitly guards against (`I don't [AGREE] with that. [DISAGREE]`) is now correctly identified as non-converged on line 90.

### Revision 3 / IND-2 current schema dependency — APPLIED CORRECTLY

> Line 8 (frontmatter): `Blocks Decision Graph UI implementation; ships today against the current `from_agent` schema and remains forward-compatible with docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md participant identity fields.`
> Line 51 (Q1.1): `**≥2 distinct `from_agent` participants** in the current schema (e.g., `claude` and `codex`; user/human posts count as participants when they use the same channel-message path).`
> Line 66 (Q2): `current implementation keys columns by `from_agent` because `channel_messages` currently has `from_agent` but no `agent_family`/`participant_id` columns.`
> Line 100 (Q4): `every distinct current-schema participant (`from_agent`) …`
> Line 142 (Implementation Notes): `Before Multi-UI lands, Decision Graph reads `from_agent` as the participant key. Once Multi-UI adds first-class identity, the view can re-key columns by `participant_id` …`
> Line 164 (Supersedes/Refines): `**Complements:** docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md (Multi-UI sets up future identity primitives; this ADR defines the visualization and uses current `from_agent` until those primitives land).`

Concur. The frontmatter "independent of" claim that was factually wrong (Multi-UI's `agent_family` column does not exist on the live `channel_messages` schema, verified again at §5.E2) is replaced with a "ships today against `from_agent`, forward-compatible" framing. All 4 of the load-bearing column-key references that round-3 flagged (Q1, Q2, Q4, Q5) now use `from_agent`. The "Complements" relationship in the supersedes/refines section is consistent with the new frontmatter — no contradictory framing left behind.

Bonus: Q1.1 line 51 also addresses Gemini-bot finding G1 (humans should count toward auto-engage). Round-3 listed G1 as "partially addressed" — it is now fully addressed by the parenthetical "user/human posts count as participants when they use the same channel-message path". Not in the explicit 6-revision scope but cleanly covered.

### Revision 4 / G2 multi-instance forward-compat — APPLIED CORRECTLY

> Line 66 (Q2): `… After the Multi-UI ADR lands, columns should re-key to the exact participant identity, preferably `participant_id` or the tuple `(agent_family, ui_surface, instance_id_short)`, with labels such as `claude:cli` and `claude:desktop`.`
> Line 142 (Implementation Notes): `Once Multi-UI adds first-class identity, the view can re-key columns by `participant_id` or `(agent_family, ui_surface, instance_id_short)` without changing the current DB schema first.`

Concur. The `claude:cli` + `claude:desktop` multi-instance collision case Gemini-bot G2 raised is explicitly named, with the same `participant_id` / `(agent_family, ui_surface, instance_id_short)` tuple the Multi-UI ADR proposes. Today's collapse-by-`from_agent` constraint is documented and the migration path is forward-compat.

### Revision 5 / G3 high-risk override — APPLIED CORRECTLY

> Line 106 (Q4): `Exception: for threads tagged with a high-risk track (HIST, BIO, ISTORIO, LIT, OES, or RUTH), convergence triggers a forced Decision Card prompt rather than a soft auto-suggest, per `docs/best-practices/agent-cooperation.md:210-222` Mechanism A.`

Concur. The exact track list (HIST/BIO/ISTORIO/LIT/OES/RUTH) matches `agent-cooperation.md:214` verbatim. The "soft auto-suggest" → "forced Decision Card prompt" semantic upgrade aligns with `agent-cooperation.md:216` Mechanism A ("the orchestrator emits a Decision Card anyway"). Line-range citation `:210-222` is correct at PR head SHA AND at current `origin/main` (verified — that doc has no upstream drift between PR base and main; see §5.E5).

### Revision 6 / G4 drawer same-round all-agents — APPLIED CORRECTLY

> Line 117 (Q5 Content): `Defaults to the same-round transcript across all agents plus the clicked participant's prior posts in earlier rounds, highlighting the specific single-message cell clicked. A per-agent filter toggle lets readers narrow the drawer when they want a single participant's history.`
> Line 122 (Q5 Rationale): `Showing same-round all-agent context preserves the antagonist/proponent relationship for objections, while the clicked participant's prior posts show how that participant arrived at its conclusion over multiple rounds.`
> Line 157 (Open Questions): `**Thread Filtering in Drawer:** Resolved by Q5: default to same-round all-agents plus clicked participant prior posts, with a per-agent filter toggle.`

Concur. The exact failure case G4 named ("if I clicked Codex's `[OBJECT]`, I want to see what Gemini said in round 2 that Codex was objecting to") is now the default behavior — the antagonist is no longer filtered out. The per-agent filter toggle is preserved as an opt-in for single-participant drilldown. Open-Question 2 is explicitly marked Resolved with a back-pointer to Q5, so the reader is not left wondering whether the punt still stands.

---

## §3 — New issues introduced by the surgical edits

I hunted for: (a) cross-reference contradictions, (b) terminology drift between sections, (c) marker-set inconsistencies between Q1.2 / Q3 / Q4 / Decision summary, (d) any stale `agent_family` reference left behind by the pivot, (e) line-number off-by-N risk after edits.

### N1 [NIT, non-blocking] Broker line citation will drift after merge to current main

ADR line 79 cites `scripts/ai_agent_bridge/_channels_cli.py:1413` and the PR body's grep evidence cites lines 1413 + 1435. Both are correct at the PR's merge-base `b94150a86f` (verified — `git show 1116e3054c:scripts/ai_agent_bridge/_channels_cli.py | awk 'NR==1413 || NR==1435'` returns the convergence check). However, between the PR base and current `origin/main`, `_channels_cli.py` had ~49 lines inserted near the top (new `_build_discuss_round_body` helper + `_discussion_worktree_snapshot` signature change adding a `--stat` capture). The convergence check now sits at lines **1462 and 1484** on current main.

When this PR merges (or rebases) into current main, the ADR's `_channels_cli.py:1413` reference will point to a comment (`# auto_snapshot=False here — the root message captured the …`), not the convergence check. The semantic claim ("strict `[AGREE]` tail matching in `_channels_cli.py`") remains true; only the line number is off-by-49.

**Two fixes, neither blocking:**
- (a) Drop the line number from line 79: cite `scripts/ai_agent_bridge/_channels_cli.py` without `:1413`. Stable across upstream code drift.
- (b) Rebase the ADR PR onto current `origin/main` and bump the citation to `:1462`. Tracks today but will drift again on the next refactor.

I'd recommend (a) since ADRs are long-lived and source files churn. The PR body's grep evidence (which is build artifact, not the ADR text) is fine to leave as-is.

### N2 — Checked-and-clean: no orphan `agent_family` references

Round-3's IND-2 fix risked leaving stale `agent_family` references behind. I grepped the post-edit ADR for every `agent_family` mention:

> Lines 66, 142: only inside the forward-compat clause "preferably `participant_id` or the tuple `(agent_family, ui_surface, instance_id_short)`". Both correctly framed as future, post-Multi-UI identity.

No stale "Columns: `agent_family`" or "filtered to that specific `agent_family`" references remain. Pivot is clean.

### N3 — Checked-and-clean: marker-set consistency across sections

Three places mention the marker set after the IND-1 fix. All consistent:

- Decision summary line 43: `[AGREE]` and `[DISAGREE]` canonical, `[OPTION]/[OBJECT]/[DEFER]` future/ADR-specific.
- Q1.2 line 52 (auto-engage marker-density threshold): `[AGREE], [DISAGREE], or future display markers [OPTION], [OBJECT], [DEFER]`.
- Q3 lines 79–80: same canonical/future split.

Q4 (line 102) explicitly says `[DISAGREE]` is the canonical non-converging marker and `[DEFER]` is a future display marker without protocol meaning today. Internally consistent.

### N4 — Checked-and-clean: convergence rule consistency

Three places state the convergence rule. All match the broker-strict tail rule:

- Q3 line 89: "convergence uses the broker-compatible rule: the latest round message must end with literal `[AGREE]` after `.strip()`".
- Q4 line 100: "latest round-N message whose stripped body ends with literal `[AGREE]`".
- Implementation Notes line 143: "broker's strict `text.strip().endswith("[AGREE]")` check is authoritative".

No section disagrees with another. Bonus: this is stricter than IND-3 asked for (a known-debt acknowledgement paragraph). The view now USES the broker rule rather than running a parallel parser, which structurally eliminates the divergence IND-3 worried about.

### N5 — Checked-and-clean: round-3 waivable nits resolved

- IND-4 ("Epic" prefix on #1785, scanner shipped): line 8 says `Integrates with D4 decision-lineage backlink scanner (#1785).` — no "Epic" prefix. Line 129 says `**D4** (decision-lineage backlink scanner, #1785)` — also no "Epic" prefix. Resolved.
- IND-5 (snapshot-date footnote on density numbers): line 16 says `Codex provided verifiable data from our channel_messages snapshot (2026-05-07)` — already footnoted with snapshot date. Resolved (was actually already addressed in round-2 — confirmed).

### N6 — Newly-added "Decision" section (lines 36-43) is consistent with the rest

The PR adds a new top-level `## Decision` summary section that wasn't in round-3's review target. It crisply summarizes the 4 paradigm choices: toggle-not-inversion, outline-first matrix, side drawer, explicit marker semantics. Line 43's marker-semantics summary matches Q3 and Q4 exactly. Useful upgrade; no contradiction surfaced.

---

## §4 — Recommendation

**Merge #1835 → user flips PROPOSED → ACCEPTED.** All 6 round-3 revisions are correctly applied; the surgical edits introduced no new contradictions; bonus fixes covered IND-3 (upgraded from acknowledgement to in-spec adoption), IND-4 (Epic prefix dropped), and G1 (humans count toward auto-engage). The single nit (N1, broker line citation drift after rebase to current main) is non-blocking and can be patched in a follow-up commit either by dropping the line number or bumping it to the post-rebase value.

If the orchestrator wants strict zero-nit before flipping ACCEPTED: ask Codex to push one more 1-line edit removing `:1413` from line 79 and from line 143. Otherwise merge as-is.

---

## §5 — Evidence appendix

### E1. PR head SHA confirmation

```
$ git log --oneline 1116e3054cb433d488ae4eba8a3ef1a433a21aa0~5..1116e3054cb433d488ae4eba8a3ef1a433a21aa0
1116e3054c docs(adr): apply round-3 REVISE findings (#1791)
442bf5e024 docs(adr): revise decision-graph-view ADR per Claude review …
28bf0b4d57 docs(adr): draft decision-graph-view ADR (PROPOSED, kubedojo Action C)
b94150a86f chore: 2026-05-08 evening hygiene …
1ebdc93769 docs(session-state): 2026-05-08 handoff …
```

PR head: `1116e3054c`. Merge-base with current `origin/main`: `b94150a86f`. PR diff stat: `docs/decisions/pending/2026-05-09-decision-graph-view.md | 45 ++++++++++++----------` (25 insertions, 20 deletions).

### E2. Live DB marker counts (re-run 2026-05-09)

```
$ sqlite3 'file:/Users/krisztiankoos/projects/learn-ukrainian/.mcp/servers/message-broker/messages.db?mode=ro&immutable=1' "SELECT '[AGREE]', COUNT(*) FROM channel_messages WHERE body LIKE '%[AGREE]%' UNION ALL SELECT '[AGREED]', COUNT(*) … UNION ALL SELECT '[DISAGREE]', COUNT(*) …"
[AGREE]|207
[AGREED]|0
[OPTION]|1
[OBJECT]|2
[DEFER]|1
[DISAGREE]|139
```

Identical to round-3 numbers. The marker-set rationale in the ADR (`[DISAGREE]` 139 vs `[OPTION]/[OBJECT]/[DEFER]` total 4) holds.

### E3. `channel_messages` schema (live, 2026-05-09)

```
$ sqlite3 'file:…/messages.db?mode=ro&immutable=1' ".schema channel_messages"
CREATE TABLE channel_messages (
    message_id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    thread_id TEXT NOT NULL,
    parent_id TEXT,
    correlation_id TEXT,
    round_index INTEGER DEFAULT 0,
    from_agent TEXT NOT NULL,             -- claude/gemini/codex/user
    from_model TEXT,
    kind TEXT DEFAULT 'post',
    body TEXT NOT NULL,
    attachments TEXT,
    context_rev_shared TEXT,
    context_rev_channel TEXT,
    monitor_state_snapshot TEXT,
    created_at TEXT NOT NULL,
    …
);
```

No `agent_family`, `ui_surface`, or `participant_id` column. The pivot to `from_agent` (R3) is the only column that exists today. The forward-compat tuple cited in R4 is consistent with the Multi-UI ADR's proposed schema.

### E4. Broker convergence check at PR head SHA

```
$ git show 1116e3054cb433d488ae4eba8a3ef1a433a21aa0:scripts/ai_agent_bridge/_channels_cli.py | grep -nE "endswith.*\[AGREE\]"
1413:            text.strip().endswith("[AGREE]") for (text, _) in responses.values()
1435:                if not t.strip().endswith("[AGREE]")
```

Lines 1413 and 1435 cited in the ADR (line 79) and PR body are correct **at the PR's merge-base**.

### E5. Same broker file at current `origin/main`

```
$ grep -nE "endswith.*\[AGREE\]" scripts/ai_agent_bridge/_channels_cli.py
1462:            text.strip().endswith("[AGREE]") for (text, _) in responses.values()
1484:                if not t.strip().endswith("[AGREE]")
```

Drift of +49 lines. Diff cause:

```
$ git diff b94150a86f..origin/main -- scripts/ai_agent_bridge/_channels_cli.py | head -5
diff --git a/scripts/ai_agent_bridge/_channels_cli.py b/scripts/ai_agent_bridge/_channels_cli.py
…
+def _build_discuss_round_body(root_body: str, directive: str) -> str:
+    """Render the high-priority body for a discuss round prompt.
…
-def _discussion_worktree_snapshot() -> tuple[str, str, str]:
+def _discussion_worktree_snapshot() -> tuple[str, str, str, str]:
```

Upstream added a helper + extended a tuple signature. After this PR rebases or merges into current main, the ADR's `_channels_cli.py:1413` will resolve to a comment (`# auto_snapshot=False here — the root message captured the …`), not the convergence check. Source of N1.

### E6. `agent-cooperation.md:210-222` at PR head SHA

```
$ git show 1116e3054cb433d488ae4eba8a3ef1a433a21aa0:docs/best-practices/agent-cooperation.md | awk 'NR>=210 && NR<=222'
### High-risk-track override (false-consensus failsafe)

When all participating agents share the same underlying bias on a topic …
For high-risk tracks — **HIST, BIO, ISTORIO, LIT, OES, RUTH** … — the orchestrator MUST apply at least one of the following failsafe mechanisms:

- **Mechanism A (Force-emit Decision Card on `[AGREE]`):** If `ab discuss` runs on a topic touching any high-risk track and converges with `[AGREE]`, the orchestrator emits a Decision Card anyway. …
```

Lines 214 (track list) and 216 (Mechanism A) fall in the cited `:210-222` range. The cite is correct on the PR base AND on current `origin/main` (the upstream diff to that file inserts content at line ~453, well below 222 — no drift). R5 citation is durable.

### E7. ADR fields verified, line by line

Final cross-walk of every line cited in the PR body's "Revisions applied" checklist against the file at PR head SHA:

| PR-body claim | Actual file line(s) | Match |
|---|---|---|
| R1 / lines 79-86 | 79 (Canonical Markers), 80 (Future markers), 82 (regex), 86 (DISAGREE row) | ✓ |
| R2 / lines 89-100 | 89 (Position Requirement), 90 (Multiple Markers), 100 (Q4 convergence rule) | ✓ |
| R3 / lines 8, 51, 66, 100, 142 | 8 (frontmatter), 51 (Q1.1), 66 (Q2 columns), 100 (Q4 from_agent), 142 (Implementation Notes) | ✓ |
| R4 / line 66 | 66 (participant_id + tuple + claude:cli/claude:desktop) | ✓ |
| R5 / line 106 | 106 (HIST/BIO/ISTORIO/LIT/OES/RUTH + Mechanism A) | ✓ |
| R6 / lines 117, 122, 157 | 117 (Content), 122 (Rationale), 157 (Open-Q 2 resolved) | ✓ |

All 14 line-anchored claims in the PR body resolve correctly against the file at PR head SHA.

---

## Closing note for the orchestrator

This is round 4 of an ADR that converged on its content at round 3. The round-3 review surfaced 6 structural issues; round 4 confirms all 6 are correctly applied and that the surgical edits introduced no new contradictions. Two waivable round-3 nits (IND-4, IND-5) were also resolved as a side-effect of the rewrite. The only remaining loose thread is N1 (broker line-number drift after merge to current main), which is documentation decay rather than a substantive issue.

**Recommend merge → flip PROPOSED → ACCEPTED.** If a zero-nit ACCEPTED is preferred, push a tiny follow-up dropping `:1413` from ADR line 79 and from the implementation note on line 143.

`[AGREE]`
