# Adversarial review — PR #1791 Decision Graph ADR (round 3)

**Reviewer:** Claude headless (Opus 4.7, xhigh, read-only)
**Date:** 2026-05-09
**Target file:** `docs/decisions/pending/2026-05-09-decision-graph-view.md` at `origin/gemini/decision-graph-adr` (159 lines)
**Prior reviews on PR #1791:**
- Gemini-code-assist drive-by (2026-05-07T23:05Z, 5 findings)
- Claude headless round 1 (2026-05-07T23:20Z, posted as PR comment, verdict REVISE — 5 IMPORTANT + 2 NIT findings)
- Claude headless round 2 (2026-05-08T07:46Z, posted as PR comment, verdict ALL FIXED — flip recommended)

This review re-examines the current head against the ACTUAL implementation in `scripts/ai_agent_bridge/_channels_cli.py` and the live `channel_messages` schema and data — angles the prior two reviews did not exercise. Two structural issues that the prior reviews missed are surfaced. Cosmetic cleanups confirmed by round 2 are accepted as-is and not re-litigated here.

---

## Section 1 — Verdict

**REVISE** (one structural correction is required before flipping PROPOSED → ACCEPTED; the other is a known-debt acknowledgement the ADR currently elides).

The ADR is well-shaped, the data backing the toggle-not-inversion conclusion holds up against the current DB, and the round-2 cosmetic fixes are correct. But the marker semantics in Q3 + Q4 silently disagree with the actual production broker, and the column key in Q1/Q2/Q4/Q5 (`agent_family`) does not exist in the live `channel_messages` schema today — making the "independent of Multi-UI ADR" claim in the frontmatter false.

Required revisions before ACCEPTED:

1. **Acknowledge the `[DISAGREE]` marker.** It is the canonical round-1 default and round-2 pushback marker per `_channels_cli.py:1254-1260, 1278-1283`, with 139 occurrences in the live DB vs 4 total for `[OPTION]+[OBJECT]+[DEFER]` combined. The ADR's four-marker set is incompatible with current channel data.
2. **Reconcile or call out the convergence-detection divergence.** The broker uses strict `endswith("[AGREE]")` (`_channels_cli.py:1436, 1456`); the ADR's Q3 says "anywhere in body, last-wins". These produce different convergence verdicts on `"I don't [AGREE] with that. [DISAGREE]"` — a shape the broker code explicitly cites as the false-positive case it guards against.
3. **Either retract `independent of` for the Multi-UI ADR, or pivot to `from_agent`.** `agent_family` is a Multi-UI-ADR-proposed column, not a current schema field. The Decision Graph cannot display real data using `agent_family` until Multi-UI lands. Frontmatter currently misrepresents the dependency.

The required-revision count is small and the diff would be ~10-30 lines. Non-blocking nits (`#1785` framing as Epic / `[AGREED]` regex matching a marker that has zero DB occurrences) are noted in §3 but waivable.

---

## Section 2 — Per-finding verification of the gemini-code-assist review

The bot review's body is a paragraph naming five items. I verify each against the **current** ADR text (post round-2 revision):

| # | Gemini's finding | Verdict | Evidence |
|---|---|---|---|
| G1 | "Broaden auto-engagement criteria to include human participants" | **Confirmed valid; partially addressed** | ADR Q1 line 51 still requires "≥2 distinct `agent_family` participants". Q2 line 66 separately says columns include "a `human` column for posts where `from_agent='human'`". So humans render in the matrix BUT do not count toward auto-engage threshold. If a `claude+codex+human` thread exists, auto-engage triggers. If a `claude+human` thread exists with markers, the participant-count threshold is failed (only 1 agent family, since `human` is not in the agent_family set per Multi-UI ADR line 109: `claude, codex, gemini, user`). I concur with G1: the auto-engage rule should use **distinct `from_agent` (or equivalent identity)** including `human/user`, not "agent_family minus user". The fix is one word: change `agent_family` → `participant identity` in Q1.1, or explicitly include `user`. |
| G2 | "Use unique agent identifiers for columns to prevent layout collisions between multiple instances of the same agent family" | **Confirmed valid; not addressed** | ADR Q2 line 66 hard-codes columns as `agent_family`. Multi-UI ADR line 139 (`{agent_family}:{ui_surface}:{instance_id_short}`) explicitly contemplates two `claude` participants posting in the same thread (e.g. `claude:cli` + `claude:desktop`). The current ADR's columns would collapse those into one column and last-write-wins the cell. The fix is to use the Multi-UI `participant_id` for columns and label by `agent_family:ui_surface`. This is a real defect and is not addressed in the round-2 revision. |
| G3 | "Convergence detection should respect the High-risk-track override per the style guide" | **Confirmed valid; not addressed** | `agent-cooperation.md:210-222` defines the High-risk-track override: when an `ab discuss` runs on HIST/BIO/ISTORIO/LIT/OES/RUTH and converges with `[AGREE]`, the orchestrator MUST emit a Decision Card anyway because correlated bias makes consensus unsafe. The ADR's Q4 convergence rule (line 99) says "thread is converged when every distinct agent_family … emits `[AGREE]` in the latest round" with no high-risk-track caveat, and the convergence indicator (line 103) "auto-suggests Decision Card creation" — but it should **force** a Decision Card on high-risk tracks, per Mechanism A. The fix is one paragraph in Q4: "Exception: for threads tagged with a high-risk track (HIST/BIO/ISTORIO/LIT/OES/RUTH), convergence triggers a forced Decision Card prompt rather than a soft auto-suggest." |
| G4 | "Refine the side drawer UX to maintain conversational context" | **Confirmed valid; partially addressed** | ADR Q5 line 114 still says drawer "displays the full-thread transcript filtered to that specific `agent_family` up to that round". Open-Question 2 (line 152) acknowledges the "single-message vs full-thread context" choice, deferring to the user. This is an OK punt but does not resolve G4. The semantic problem G4 names ("if I clicked Codex's `[OBJECT]`, I want to see what Gemini said in round 2 that Codex was objecting to") is still not addressed in the proposal text — the proposal explicitly filters out the antagonist. The fix is to default the drawer to **same-round all-agents** plus the clicked agent's prior posts, with a per-agent filter toggle. |
| G5 | "Clarify the logic regarding historical thread conditions" | **Resolved** in round 2 | Q4 (lines 99-101) is now a single-rule statement plus a clearly-demarcated `Edge case (partial participation)` paragraph. The earlier muddled "looser historical condition" wording is gone. I concur — G5 is fixed. |

**Net:** of Gemini's 5 findings, 1 is fully addressed (G5), 1 is partially addressed (G1 — humans render but don't auto-engage), and 3 are still open (G2 multi-instance columns, G3 high-risk-track override, G4 drawer cross-agent context). The round-2 revision did not target any of these.

---

## Section 3 — Independent findings

These are angles the prior two reviews did not exercise.

### IND-1 [BLOCKER] Marker set conflicts with actual broker code AND actual channel data

The ADR's Q3 lists `[AGREE], [OPTION], [OBJECT], [DEFER]` as the canonical four markers. The actual production broker uses a different set:

- `_channels_cli.py:1254` (round-1 directive): `[DISAGREE]` is the **default**, `[AGREE]` only for trivial pre-resolution.
- `_channels_cli.py:1278-1283` (round-2 directive): `[AGREE]` or `[DISAGREE]`, no third option.
- `_channels_cli.py:1417` (convergence comment): explicitly cites the false-positive case `"I don't [AGREE] with that. [DISAGREE]"`.
- `_channels_cli.py:1436, 1456`: convergence detection is `text.strip().endswith("[AGREE]")`.

Live `channel_messages` snapshot (queried 2026-05-09 inside this review):

| Marker | Occurrences in DB |
|---|---:|
| `[AGREE]` | 207 |
| `[DISAGREE]` | **139** |
| `[AGREED]` | 0 |
| `[OBJECT]` | 2 |
| `[OPTION]` | 1 |
| `[DEFER]` | 1 |

`[DISAGREE]` is the **second-most-prevalent marker in the system** and the ADR's marker set excludes it entirely. A Decision Graph parser implemented per Q3 would render zero chips for those 139 messages — the matrix would silently misrepresent the deliberation state for ~40% of marker-bearing replies. Conversely, `[OPTION]/[OBJECT]/[DEFER]` together account for 4 messages — the rationale for elevating them to first-class column headers is unsubstantiated.

**Fix:** add `[DISAGREE]` to the marker set as the explicit non-converging counterpart to `[AGREE]`. Either drop `[OPTION]/[OBJECT]/[DEFER]` to a "future markers" footnote or document where they originate (the only place I found `[OBJECT]` in canonical docs is `2026-05-06-multi-ui-channel-participation.md:297, 1049`, never `[OPTION]` or `[DEFER]`). The `[AGREED]` alternative in the regex (`AGREE(?:D)?`) currently matches a marker with zero historical use — minor, but ironic given the omission of the actual second marker.

This is the load-bearing finding of this review. The round-1/round-2 reviews verified the regex against the ADR's own table but did not probe whether the ADR's marker set matched the broker's marker set or the data.

### IND-2 [BLOCKER for "independent" framing] `agent_family` column does not yet exist; "independent of Multi-UI ADR" is wrong

ADR line 8 frontmatter: `Blocks/Blocked-by: …; independent of docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md.`

Live `channel_messages` schema (queried 2026-05-09 inside this review):

```
message_id, channel, thread_id, parent_id, correlation_id,
round_index, from_agent, from_model, kind, body, attachments,
context_rev_shared, context_rev_channel, monitor_state_snapshot, created_at
```

There is **no `agent_family` column**. The Decision Graph ADR uses `agent_family` as the load-bearing identity in:

- Q1.1 line 51 ("≥2 distinct `agent_family` participants")
- Q2 line 66 ("Columns: `agent_family`")
- Q4 line 99 ("every distinct `agent_family` … emits `[AGREE]`")
- Q5 line 114 ("filtered to that specific `agent_family`")
- Q6 (implicit via D4 integration)

`agent_family` is **proposed** by the Multi-UI ADR (`2026-05-06-multi-ui-channel-participation.md:104, 109, 150`) — line 150 says: *"The legacy `from_agent` column remains during migration. Old rows hydrate as `agent_family=from_agent`, `ui_surface=cli`, `client_id=legacy`, `instance_id=legacy`."* That migration has not run; the Multi-UI ADR is also still PROPOSED.

**Two fixes possible:**

(a) **Pivot to `from_agent` for the Decision Graph view.** This is the column that exists today, ships a real graph against real data, and remains compatible after the Multi-UI migration since old rows hydrate `agent_family=from_agent`. Truly independent.

(b) **Retract the "independent of" claim** and document the dependency explicitly: `Blocked-by: 2026-05-06-multi-ui-channel-participation.md (depends on agent_family schema migration)`.

Either fix unblocks ACCEPTED. (a) is preferable because it preserves the value Open-Question-shipping the Decision Graph standalone — which was the kubedojo-team handoff's whole point per `2026-05-07-kubedojo-paradigm-followups.md:24-28`.

### IND-3 [IMPORTANT — known-debt acknowledgement] Convergence semantics divergence between broker and view

Q3 line 88 says markers can appear "anywhere in body" and Q3 line 89 says "last-wins". Q4 line 99 says "every distinct agent_family … emits `[AGREE]` in the latest round". The actual broker's convergence check at `_channels_cli.py:1436` is:

```python
if all(text.strip().endswith("[AGREE]") for (text, _) in responses.values())
```

— **strict tail-anchored match**, with the explicit `_channels_cli.py:1417` comment that anywhere/last-wins would false-positive on `"I don't [AGREE] with that. [DISAGREE]"`.

If both parsers run side by side (broker decides convergence for `ab discuss` short-circuit; UI decides convergence for the "closing-out indicator" + auto-suggest Decision Card), they will disagree on edge cases. The ADR's Implementation Notes line 138 says "the underlying DB schema, the `ab discuss` Python broker logic" doesn't change — but Q3/Q4 do redefine convergence semantics for the UI, creating a divergence the ADR does not call out.

**Fix:** add a paragraph to Implementation Notes acknowledging the divergence: *"The broker's convergence detection uses strict `endswith('[AGREE]')` and is the source of truth for `ab discuss` short-circuit decisions. The Decision Graph view's convergence indicator uses the parser defined in Q3 and may differ on edge-case messages. When the two disagree, the broker's verdict is authoritative for protocol behavior; the view label is informational."*

### IND-4 [NIT] `#1785` is described as "Epic" but is closed

ADR line 8: "Integrates with D4 decision-lineage backlink scanner (#1785)". ADR line 126: "**D4** (decision-lineage backlink scanner, Epic #1785)". `gh issue view 1785` reports `state: CLOSED, stateReason: COMPLETED, closedAt: 2026-05-08T07:51:09Z`, and `scripts/audit/decision_lineage.py` exists in the worktree. The "Epic" framing is now historical. Non-blocking; replace with `(scanner shipped 2026-05-08, file: scripts/audit/decision_lineage.py)` or just `(#1785, completed)`.

### IND-5 [NIT] Channel-density numbers drift slightly under the current DB

The ADR's Context table (lines 18-22) reports the 2026-05-07 snapshot. Re-run on 2026-05-09:

| Channel | ADR (2026-05-07) | Now (2026-05-09) | Delta |
|---|---:|---:|---:|
| `architecture` | 32/39 = 82% | 36/40 = 90% | +8 pp |
| `pipeline` | 2/11 = 18% | 5/15 = 33% | +15 pp |
| `reviews` | 19/83 = 23% | 20/83 = 24% | +1 pp |

`pipeline` jumped 18% → 33% with only 4 new threads — high variance on small N. The "75-80% of channel traffic would be wrong paradigm" claim still holds qualitatively (averages 50% across non-architecture channels even now), but the Context section should be footnoted with the snapshot date that's already there (line 16) so future readers don't expect the table to track live data. Non-blocking.

### IND-6 [NIT] ADR template compliance

Most decisions in `docs/decisions/` use a 4-section structure (Status / Context / Decision / Consequences). The Multi-UI ADR (the precedent the brief referenced) uses Why/Scope/Q-by-Q/Implementation. This ADR uses a Q-by-Q structure with Implementation Notes and Cross-Agent Review. The pattern is consistent with the Multi-UI ADR but missing the **Consequences** section the older ones have. Non-blocking — the Q-by-Q rationale subsections cover trade-offs in-line. Worth confirming with the user that the precedent ADR's structure is the canonical going-forward template.

---

## Section 4 — Recommendation

**Push REVISE: dispatch Codex to apply the three structural revisions in §1 (IND-1 + IND-2 + IND-3), plus the three open Gemini-bot findings (G2 unique IDs, G3 high-risk override, G4 drawer cross-agent context).** Estimated diff: ~30-50 lines.

Concrete brief skeleton for the Codex dispatch:

1. ADR Q3: add `[DISAGREE]` to marker set; document `[AGREE]/[DISAGREE]` as canonical and `[OPTION]/[OBJECT]/[DEFER]` as forward-looking; cite `_channels_cli.py:1254-1283` as the source.
2. ADR Q4: add a one-paragraph "Exception: high-risk-track convergence forces Decision Card per `agent-cooperation.md:210-222`."
3. ADR Q5: change drawer default from "filtered to `agent_family`" to "same-round all-agents + clicked agent's prior posts, with filter toggle"; note in line 152 Open-Question 2 that this resolves the option.
4. ADR frontmatter line 8: either replace "independent of" with "blocked-by" the Multi-UI ADR, OR pivot Q1/Q2/Q4/Q5 column key from `agent_family` to `from_agent` (the column that actually exists today). Strongly recommend the pivot — the ADR's value is independent shipping.
5. ADR Implementation Notes (line 137-138): add paragraph calling out the broker-vs-view convergence semantics divergence and naming the broker as authoritative.
6. ADR Q2 line 66: define columns by `participant_id` (per Multi-UI ADR's tuple) so multi-instance same-family threads don't collapse — OR document the constraint that pre-Multi-UI threads collapse to one-column-per-`from_agent`.
7. ADR line 8 + 126: drop "Epic" prefix on #1785, note `decision_lineage.py` shipped.

Do **NOT** flip PROPOSED → ACCEPTED until at least IND-1 and IND-2 are resolved. IND-3 is acceptable as a known-debt acknowledgement paragraph; IND-4/5/6 are waivable.

If the user wants to ship a minimum-change ACCEPTED today and defer the structural fixes, the absolute-minimum set is: (a) IND-1 marker-set fix (the marker set as-written is just wrong against current data) + (b) IND-2 frontmatter retraction (the "independent" claim is factually false today). Those two are ~10 lines of edits.

---

## Section 5 — Evidence appendix

### E1. Marker counts in live DB (2026-05-09)

Ran inside the worktree against `messages.db`:

```python
import sys; sys.path.insert(0, 'scripts')
from ai_agent_bridge._config import DB_PATH
import sqlite3
db = sqlite3.connect(str(DB_PATH))
for marker in ['[AGREE]', '[AGREED]', '[OPTION]', '[OBJECT]', '[DEFER]', '[DISAGREE]']:
    n = db.execute('SELECT COUNT(*) FROM channel_messages WHERE upper(body) LIKE upper(?)', (f'%{marker}%',)).fetchone()[0]
    print(f'{marker}: {n}')
```

Output:
```
[AGREE]: 207
[AGREED]: 0
[OPTION]: 1
[OBJECT]: 2
[DEFER]: 1
[DISAGREE]: 139
```

DB path: `/Users/krisztiankoos/projects/learn-ukrainian/.mcp/servers/message-broker/messages.db`.

### E2. `channel_messages` schema (live, 2026-05-09)

```
message_id            TEXT
channel               TEXT
thread_id             TEXT
parent_id             TEXT
correlation_id        TEXT
round_index           INTEGER
from_agent            TEXT
from_model            TEXT
kind                  TEXT
body                  TEXT
attachments           TEXT
context_rev_shared    TEXT
context_rev_channel   TEXT
monitor_state_snapshot TEXT
created_at            TEXT
```

No `agent_family` column. No `ui_surface` column. No `participant_id` column.

### E3. Broker convergence detection — quoted from `scripts/ai_agent_bridge/_channels_cli.py`

Lines 1232-1240 (round-1 vs round-2+ comment):

> Round 2+ is where agents see each other's round-1 (and later) replies via the channel history, and `[AGREE]` / `[DISAGREE]` becomes meaningful as cross-agent assent or pushback. […] This was originally a single uniform directive; that produced false convergence in the собака-gender deliberation 2026-05-05 (3 agents disagreed substantively but all signed [AGREE] in round 1, short-circuiting before any agent saw the disagreements).

Lines 1253-1260 (round-1 directive):

> ```
> [DISAGREE]  — your default in round 1; you have a substantive position …
> [AGREE]     — only if your reading of the channel context (pinned rules) makes the question trivially resolved …
> Rare; default is [DISAGREE] in round 1.
> ```

Lines 1278-1283 (round-2 directive):

> ```
> [AGREE]     — you have read the other agents' prior replies …
> [DISAGREE]  — you still have open substantive objections …
> If every agent ends with [AGREE], the discussion short-circuits …
> ```

Lines 1413-1417 (convergence-check rationale):

> ```python
> # ── convergence check ─────────────────────────────────────
> #
> # response with the literal `[AGREE]` token at the tail.
> # "I don't [AGREE] with that. [DISAGREE]".
> ```

Line 1436 (the actual check):

> ```python
> text.strip().endswith("[AGREE]") for (text, _) in responses.values()
> ```

### E4. ADR Q3 marker set & regex (file under review)

Lines 78-89 of `docs/decisions/pending/2026-05-09-decision-graph-view.md`:

> *   **Target Markers:** `[AGREE]`, `[OPTION]`, `[OBJECT]`, `[DEFER]`.
> *   **Case Sensitivity:** Case-insensitive match …
> *   **Regex Matching:** `\[(AGREE(?:D)?|OPTION|OBJECT(?:[^\]]*)?|DEFER)(?:\b[^\]]*)?\]` (case-insensitive).
> *   **Position Requirement:** Anywhere in the body. While agents typically place markers at the end, human participants or modified prompts might place them at the top.
> *   **Multiple Markers:** … **last-wins** logic …

Note: regex does not include `DISAGREE`. Position rule and last-wins differ from the broker's strict `endswith("[AGREE]")` at line 1436.

### E5. ADR `agent_family` references

ADR lines using `agent_family` as a load-bearing schema column:

- Line 51: "≥2 distinct `agent_family` participants"
- Line 66: "Columns: `agent_family` (e.g., `claude`, `gemini`, `codex`, plus a `human` column for posts where `from_agent='human'`)" — note the cell-criterion mixes `agent_family` (proposed) and `from_agent='human'` (legacy)
- Line 99: "every distinct `agent_family` that has posted in the thread emits `[AGREE]` in the latest round"
- Line 114: "filtered to that specific `agent_family`"

Multi-UI ADR (`docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md`) line 150:

> The legacy `from_agent` column remains during migration. Old rows hydrate as `agent_family=from_agent`, `ui_surface=cli`, `client_id=legacy`, and `instance_id=legacy`.

→ confirms `agent_family` is post-migration only and `from_agent` is the current column.

### E6. ADR frontmatter "independent" claim (file under review)

Line 8:

> **Blocks/Blocked-by:** Blocks Decision Graph UI implementation; independent of docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md. Integrates with D4 decision-lineage backlink scanner (#1785).

Combined with E2 (no `agent_family` column today) and E5 (ADR keys columns by `agent_family`), the `independent of` claim is factually false: the Decision Graph cannot key columns by `agent_family` until Multi-UI migration runs.

### E7. `agent-cooperation.md` high-risk-track override

Lines 210-222:

> When all participating agents share the same underlying bias on a topic … an `[AGREE]` consensus is NOT a green light. It is exactly when the Decision Card mechanism is most needed and most likely to be bypassed. For high-risk tracks — **HIST, BIO, ISTORIO, LIT, OES, RUTH** … the orchestrator MUST apply at least one of the following failsafe mechanisms: – **Mechanism A (Force-emit Decision Card on `[AGREE]`):** … – **Mechanism B (Inject domain-specific bias checklist):** …
> **Pattern:** Consensus on high-risk tracks is a SIGNAL TO CHECK, not a signal to proceed.

ADR Q4 line 103 currently says "auto-suggest the creation of a Decision Card" which is softer than the "MUST apply" requirement above for high-risk tracks. Gemini-bot G3 was right to flag this.

### E8. `#1785` issue state

`gh issue view 1785 --json closedAt,state,stateReason`:

```
{"closedAt":"2026-05-08T07:51:09Z","state":"CLOSED","stateReason":"COMPLETED"}
```

`ls scripts/audit/decision_lineage.py` → file exists. Issue is closed and the scanner shipped, so the ADR's "Epic #1785" framing is stale.

### E9. Channel density / body sizes — current vs ADR snapshot

```python
import sys; sys.path.insert(0, 'scripts')
from ai_agent_bridge._config import DB_PATH
import sqlite3, re, statistics
db = sqlite3.connect(str(DB_PATH))
db.row_factory = sqlite3.Row
pat = re.compile(r'\[(AGREE|AGREED|OPTION|OBJECT|DEFER)\]', re.I)
for ch in ('architecture','pipeline','reviews'):
    threads = {}
    for r in db.execute("SELECT thread_id, body FROM channel_messages WHERE channel=?", (ch,)):
        threads.setdefault(r['thread_id'], []).append(r['body'] or '')
    total = len(threads)
    marker = sum(1 for tid, bodies in threads.items() if any(pat.search(b) for b in bodies))
    pct = (marker/total*100) if total else 0
    print(f'{ch}: {marker}/{total} = {pct:.0f}%')
    rows = db.execute("SELECT body FROM channel_messages WHERE channel=? AND parent_id IS NOT NULL", (ch,)).fetchall()
    sizes = [len(r['body'] or '') for r in rows]
    if sizes:
        print(f'  replies={len(sizes)} avg={int(sum(sizes)/len(sizes))} max={max(sizes)} median={int(statistics.median(sizes))}')
```

Output:
```
architecture: 36/40 = 90%
  replies=130 avg=2406 max=8349 median=2039
pipeline: 5/15 = 33%
  replies=27 avg=1410 max=5029 median=837
reviews: 20/83 = 24%
  replies=116 avg=1522 max=9654 median=1329
```

→ confirms the ADR's directional claims hold; pipeline density jumped from 18% to 33% post-snapshot but still well below `architecture`. Body-size avg/max for `architecture` matches ADR within rounding (the ADR's avg=2367, max=8349 is the snapshot; current avg=2406, max=8349 unchanged).

---

## Closing note for the orchestrator

This is round 3. Rounds 1 and 2 cleaned up cosmetic and wording issues correctly. Round 3 surfaces structural issues (marker set, schema dependency, broker/view divergence) that the prior reviews did not exercise because they audited the ADR text against itself rather than against the actual broker code and live DB. The deterministic-over-hallucination rule applies to ADR review too — the ADR's load-bearing schema and marker claims must be verified against the running system, not just internally consistent.

The fastest path to ACCEPTED is the two-line minimum from §4: pivot frontmatter to `Blocked-by: Multi-UI ADR` (or pivot column key to `from_agent`), and add `[DISAGREE]` to Q3's marker set. Everything else is documentation hygiene.

`[OBJECT]` (per the ADR's own marker set; per the broker's set this would be `[DISAGREE]`).
