# Session Handoff — 2026-05-04 (MCP verification-layer architecture kickoff + batch ingestion dispatched)

> **Predecessor:** `2026-05-02-1644-cleanup-and-poc-unblocked.md`
> **Successor scope:** Land in-flight PRs (#1670, #1672), follow up on Gemini's #1663 dispatch, pick up #1669 VESUM arch tag exposure, then continue Tier-1 ingestion work after codex returns at 11am tomorrow.
> **Mode:** Continued user-online session. Codex (delegate.py path) hit weekly cap mid-session; codex-desktop web UI on a separate counter completed one task. Gemini and Claude active throughout.

---

## TL;DR — what shipped this arc

Started as a kubedojo-style model-routing port; pivoted hard after the user shared a Сибір-gender question that Gemini answered with three fabricated source citations (Грінченко example, Антоненко-Давидович claim, fused Shevchenko quote). That case study exposed a deeper architectural issue than data-coverage gaps: **our MCP has the wrong abstractions for verification work** — naming mismatches, no quote-verification primitive, no source-attribution tool, no Sovietization metadata, no provenance returns.

Three threads emerged:

1. **EPIC #1657 filed** — MCP verification-layer improvements, 3-phase plan (P1 quick wins, P2 new primitives, P3 architectural). 11 sibling issues filed against it (#1658–#1669).
2. **Tier-1 ingestion kicked off** — three executions in parallel: Claude inline (#1659 СУМ-11 Sovietization flag → PR #1670), Codex web UI (#1662 ЕСУМ vol 1 PoC → PR #1672), Gemini dispatch (#1663 Antonenko full ingest → still running).
3. **Codex's ЕСУМ PR caught CI failure** (data-dependent tests + missing `search_esum` in the expected-tools test). Fixed both, pushed to his branch, ready for re-review.

Memory rule **#0I** added: *"DON'T STACK MICRO-DILEMMAS, DECIDE FOR THE USER"* — saved after the user explicitly pushed back on me asking 5 sign-off questions in a single response. Stronger than #0A: a numbered "sign off on these 5" list IS a menu even when buried at the bottom of a structured response.

---

## Issues filed (#1657–#1669, 13 total)

| # | Title | Status |
|---|---|---|
| **#1657** | EPIC: MCP verification-layer improvements (3-phase plan) | open, parent of all below |
| #1658 | [P1] Rename `search_etymology` → `search_grinchenko_1907` | open, not started |
| #1659 | [P1] Add `sovietization_risk` flag to СУМ-11 | **PR #1670 open** |
| #1660 | [P1] Tool descriptions: flag completeness gaps explicitly | open, not started |
| #1661 | [V7 prompts] Add Tier-1 verification discipline to writer + reviewer prompts | open, not started |
| #1662 | [P1] Ingest ЕСУМ all 6 volumes from archive.org | **PR #1672 open** (vol 1 PoC) |
| #1663 | [P1] Ingest Antonenko-Davydovych «Як ми говоримо» — full 169-page text | **Gemini dispatch FAILED** (segmenter broken; production DB polluted, rolled back — see incident below) |
| #1664 | [P1] Ingest Karavansky «Російсько-український словник складної лексики» (r2u) | open, not started |
| #1665 | [P1] Ingest Holovashchuk «Словник-довідник з українського літературного слововживання» (2004) | open, not started |
| #1666 | [P1] Ingest Гринчишин/Сербенська «Словник паронімів української мови» (1986 NBU scan) | open, **license read needed first** |
| #1667 | [P1] Ingest СУМ-20 (ULIF, 2010-ongoing) — modern definitional baseline | open, **license review needed** |
| #1668 | [P1] PyMorphy3 wrapper for Russian-shadow form detection | open, not started |
| #1669 | [P1] Surface VESUM `arch` tag — modern-vs-historical form discrimination | open, **next pickup** |

---

## PRs in flight at handoff

### PR #1670 — feat(mcp): СУМ-11 Sovietization flag layer (closes #1659)

- Branch: `claude-1659-sum11-soviet-flag` → main
- 4 commits, well-scoped (migration / scan / consumer-side / tests)
- Local validation: 5 tests pass, ruff clean, scan finds 7,152/127,069 (5.63%) flagged on production DB
- Awaiting cross-family Gemini review (codex-out blocks codex review)
- **Action for next session:** dispatch Gemini review on this PR; if clean, merge

### PR #1672 — feat(mcp): ingest ЕСУМ Volume 1 (А–Г) — etymology PoC (closes #1662 step 1)

- Branch: `codex-1662-esum-vol1-poc` → main
- 5 commits: 4 by Codex (raw text, parse, loader, MCP wiring) + 1 by Claude (test fixture + tool list update)
- Scope: vol 1 only as PoC; vols 2-6 follow-up after this lands
- 1,923 ЕСУМ headwords loaded from vol 1 (А–Г). **Open question:** is this segmentation complete or undercatching? Codex follow-up prompt was generated to do a recall audit on 5 sampled pages.
- **Action for next session:** check if Codex ran the recall audit; if recall ≥90%, merge

---

## Gemini dispatch — FAILED + production DB polluted (rolled back)

**Timeline:**
- 14:54 UTC — Gemini dispatched on `gemini-1663-antonenko-full-ingest`
- 16:55 UTC — Gemini process exited with `status: failed` (delegate state was not auto-polled, so it showed "running" until manually checked at session end)
- 17:45 UTC — `data/sources.db` last written (Gemini's load script bypassed worktree isolation and wrote into the **production** DB instead of the worktree's gitignored 0-byte placeholder)
- 20:23 UTC — handoff investigation; pollution discovered + cleanup performed

**What Gemini polluted into production `data/sources.db`:**

A new `antonenko_full` table containing **1,268 garbage rows**. The segmenter mistook paragraph-starts for discussion-item headwords, so row 1 was the foreword title `ПЕРЕДНЄ СЛОВО`, row 2 was a Shevchenko poetry line `Ну, що б, здавалося, слова…`, and so on — almost none of the rows are actual Antonenko discussion items.

**Cleanup performed in this session (already done):**

1. Backed up production DB: `/tmp/sources.db.pre-gemini-1663-rollback-20260504-202324` (1.5 GB, full snapshot before drop)
2. Verified existing `style_guide` table (279-entry partial subset) is still intact and untouched
3. Dropped the bad table:
   ```bash
   sqlite3 data/sources.db "DROP TABLE IF EXISTS antonenko_full;
       DROP INDEX IF EXISTS idx_antonenko_full_headword;"
   ```
4. Confirmed `style_guide` row count still 279
5. Gemini process was already gone (exited at 16:55); no kill needed

**Branch state:**

- Remote branch `gemini/1663-antonenko-full-ingest` exists at `94571ffede` ("feat(mcp): update search tool and rules for 325-entry Antonenko DB"). Has 4 commits including ingestion code. **Do NOT merge — segmentation logic is broken.**
- Local worktree `.worktrees/gemini-1663-antonenko-full-ingest` is at a different SHA `8d8db833f9` (only the raw PDF commit — earlier in the chain). Worktree is preserved for inspection / salvage in next session.

**Salvage value:**

The ingestion script in Gemini's branch may still have useful scaffolding (PDF→text extraction, table schema, MCP wiring) — only the segmentation regex is wrong. A follow-up session could either: (a) cherry-pick the framework + write a corrected segmenter, or (b) start over from the brief with stricter guard rails in the segmentation step.

**Lesson for the dispatch-brief discipline:**

The brief said *"data/raw/antonenko/yak-my-hovorymo.pdf"* as the worktree-local source path (✓ correct), but did not explicitly forbid absolute paths into the main checkout's `data/sources.db`. Gemini's load script appears to have used `Path(__file__).resolve().parent.parent / "data" / "sources.db"` or similar, which resolves to **main checkout's DB** (since worktrees share the parent .git but have their own working tree — the gitignored DB is the main checkout's by reference). For future ingestion briefs: explicitly warn that gitignored DB files in worktrees are SEPARATE 0-byte placeholders, and ingestion must target the worktree-local DB path or the migration must be deferred to PR-merge time. Filing this as a follow-up to the dispatch-brief discipline rule.

**Action for next session:**

1. Inspect Gemini's branch via `git diff origin/main..gemini/1663-antonenko-full-ingest` to assess salvage value
2. Decide: cherry-pick framework + rewrite segmenter, OR re-dispatch with corrected brief
3. The original brief at `/tmp/gemini-1663-antonenko-brief.md` is still on disk; update it before any re-dispatch

---

## Codex web UI follow-up prompt (queued)

A follow-up prompt for Codex (web UI works on a separate counter than the dispatch path that hit the cap) was generated to verify segmentation quality on PR #1672. Prompt asks for:
1. Sample 5 random pages from vol 1
2. Cross-check headword recall (target ≥ 90%)
3. Spot-check entry body precision
4. Document in `audit/esum_vol1_segmentation_recall.md`
5. Bonus: ≤5min ЕСУМ vol 7 status check

Full prompt is in the chat transcript; not separately saved to disk. **The user has it; will paste into codex-desktop when ready.**

---

## Active in flight, DO NOT TOUCH

- Worktree `.worktrees/claude-1659-sum11-soviet-flag/` — branch pushed, PR open, can be cleaned up after PR merges
- Worktree `.worktrees/claude-fix-codex-1662/` — branch `claude-fix-codex-1662` pushed onto Codex's PR branch, can be cleaned up after PR merges
- Worktree `.worktrees/gemini-1663-antonenko-full-ingest/` — Gemini's process exited (failed). Worktree preserved for next-session inspection / salvage; **do NOT merge the branch as-is** — segmenter is broken (see incident notes above)

## Main checkout dirty state at handoff (NOT MINE)

Main checkout has uncommitted changes from two distinct sources, **neither of them Gemini**:

**(a) Pre-existing user WIP (orchestration / runtime work from earlier sessions):**
- `AGENTS.md` (+36 -1)
- `start-codex.sh` (+27 -1)
- `scripts/api/comms_router.py` (+37 -11) and other API routers
- `scripts/api/admin_router.py`, `scripts/api/agent_router.py`, `scripts/api/main.py`, `scripts/api/state_helpers.py`, `scripts/api/wiki_router.py`
- New untracked dirs `.agents/` (skills) and `.codex/` (agent config) — pre-session, used by codex-desktop integration

**(b) Codex web UI is concurrently fixing a CodeQL / code-scan run with 127 outstanding issues** (user-confirmed at session end). Small diffs landed in main checkout this session, mtimes 18:56–18:59:
- `scripts/path_safety.py` (+18 -12) — `os.path.commonpath`-based security-scanner compatibility refactor
- `scripts/api/build_events_router.py` (+1 -1)
- `scripts/api/module_dashboard.py` (+1 -1)
- `scripts/api/state_build.py` (+3 -3)
- `scripts/api/state_compute.py` (+1 -1)
- `scripts/api/state_coverage.py` (+2 -2)
- `scripts/api/state_issues.py` (+1 -1)
- `scripts/api/state_router.py` (+4 -4)
- `scripts/api/blue_router.py`, `scripts/api/consultation_router.py`
- `scripts/audit/audit_external_resources.py` (+3 -1)
- `scripts/content/video_discovery_helpers.py` (+4 -2)

These were verified non-Gemini by grepping all diffs for `antonenko|1663|esum|gemini-1663` markers — zero hits. Gemini's broken ingestion stayed inside its worktree at the FILE level; only `data/sources.db` (gitignored, shared via worktree filesystem mechanics) was the cross-boundary leak, and that table has been rolled back.

**Action for next session: do NOT touch these dirty files.** They are split between user WIP and Codex's in-flight code-scan PR work. The session-end handoff commits ONLY the new handoff file + current.md update (clean diff scoped to those two files).

---

## Codex weekly-cap timing

User confirmed 2026-05-04 evening: codex (CLI dispatch path) is out of weekly until **11am 2026-05-05 (CET)**. Codex web UI (codex-desktop) appears to be on a separate counter — completed PR #1672 work tonight after the dispatch path was capped.

**Implication:** through 11am tomorrow, batch ingestion work routes through:
- Claude inline (current orchestrator) — but watch Anthropic weekly cap
- Gemini dispatch — subscription, unmetered
- Codex web UI (user-pasted briefs) — separate counter, unconfirmed remaining capacity

After 11am: full three-agent bandwidth restored.

---

## Cold-start protocol for next session

```bash
# 1. Verify clean state on main
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git status -s              # AGENTS.md + scripts/api/*.py expected dirty (pre-existing)
git log --oneline -3       # confirm 083d35d2c5 still tip OR newer (handoff commit if landed)

# 2. Read this handoff. Predecessor chain in current.md.

# 3. Source auth before any gh call
source ./.envrc            # GH_TOKEN, not stale ~/.bash_secrets

# 4. Check open PRs
gh pr list --state open --base main

# 5. Check Gemini dispatch status
.venv/bin/python scripts/delegate.py status gemini-1663-antonenko-full-ingest

# 6. If Codex is back (after 11am): check codex weekly via
#    `.venv/bin/python scripts/ai_agent_bridge/__main__.py codex-usage`
```

---

## Next-session priorities (ranked)

1. **Land #1670 (СУМ-11 sovietization flag PR)** — dispatch Gemini cross-family review; if clean, merge.
2. **Land #1672 (ЕСУМ vol 1 PoC PR)** — check Codex's segmentation recall audit; if ≥90%, merge. CI tests already fixed by Claude's pushed commit.
3. **Check #1663 (Antonenko full ingest)** — Gemini was running for ~70 min at handoff; likely finished by morning. Review output PR if opened.
4. **Pick up #1669 (VESUM arch tag)** — quick win, ~1-2h, internal data exposure only, unblocks the modern-vs-historical guard for V7 prompts later.
5. **#1658 (rename search_grinchenko_1907)** + **#1660 (completeness flags)** — both small Phase-1 cleanups, can run in parallel.
6. **#1661 (V7 prompt diffs)** — ready to draft against current MCP; will simplify dramatically after Phase 2 primitives land.
7. **After codex returns at 11am**: dispatch #1664 (Karavansky), #1665 (Holovashchuk), #1668 (PyMorphy3) via delegate.py.

---

## Cross-thread notes (still active)

- **Memory rule #0I added** to `~/.claude/projects/.../memory/MEMORY.md` — "DON'T STACK MICRO-DILEMMAS, DECIDE FOR THE USER". Required pattern for compound decisions: state-of-play → 2-3-row options table → **MY RECOMMENDATION** → "going to execute unless you stop me". WRONG pattern (today's failure mode): asking 5 sign-off questions disguised as a numbered list.
- **СУМ-11 Sovietization confirmed empirically** — 7,152 of 127,069 entries (5.63%) flag against the curated Soviet keyword stem list. Top high-risk: `прапор`, `революційний`, `партійний`, `школа`, `центр`, `шлях` — even neutral terms have Soviet citations woven in. Anti-scope: do NOT delete or rewrite Sovietized entries; they remain visible, the flag exists for reviewer override at decision time.
- **Гринчишин/Сербенська 1986 NBU scan license** says "use is for навчальною та науковою некомерційною метою" with no further full-text reproduction. Project policy is non-commercial → educational use aligned, but bulk ingestion vs. live WebFetch caching path needs interpretation. **Read NBU terms before any bulk fetch (#1666 phase A).**
- **СУМ-20 license** not stated on ULIF portal pages. Same: read terms before bulk ingestion (#1667 phase A).
- **Wikisource Pravopys 1929/1933 URLs are dead** (404). Codex confirmed. izbornyk.org.ua has historical references but no full digital editions. Sourcing not yet identified — keeps issue #1657 Phase 1 / Pravopys-historical work blocked.
- **ЕСУМ vol 7 confirmed not publicly available** per Codex's research — vol 7 is the planned multilingual index, unpublished due to funding shortfall (Day/ZN.ua interview citation). Drop from scope; vols 1-6 are the lexical body.
- **Ukrajinet 122K-vs-3K discrepancy resolved by Codex** — public GitHub README now shows 122,441 synsets, matching our local DB. The 2023 paper described initial 3,360-synset version; current version grew via auto-translation from Open English WordNet. **Quality concern documented:** synsets are MT-derived not natively curated. Audit pending under #1657.
- **A1/20 build (POC step 3) is parked** — checkpoint A is user-eval anyway, so writer-phase running on existing prompts is fine. The prompt-discipline diff (#1661) is queued; will simplify dramatically once #1657 Phase 2 primitives land. No blocker on running A1/20 tonight if user wants.
- **Bridge channel `architecture` thread `2792e731f4464b02a090b5cbc3936147`** — Gemini consultation on MCP expansion. Useful context if revisiting prioritization. 6 ranked recommendations, including the "PyMorphy3 wrapper not Russian-text-ingest" pattern (#1668), the "СУМ-11 is Sovietized" warning (#1659), and the Wikisource Pravopys lead that turned out to be dead.
- **Brief discipline reinforced today**: Codex's ЕСУМ brief used sample words (мати, сибір) that were NOT in vol 1 (А-Г). For vols 2-6 briefs, use words actually in the target alphabet range. Codex correctly handled the out-of-scope cases by documenting them as expected-empty-results — no fabrication.
- **CI bypass on chore handoff pushes** — handoff commits go directly to main via the user's branch-protection bypass (per current.md prior note). This file commits the same way.
