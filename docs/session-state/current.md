# Current — multi-agent index (2026-05-11)

> **Repo state (evening 2026-05-11):** **#1657 Phase 2 complete on main** — all 4 verifiers shipped (`verify_quote`, `verify_source_attribution`, `check_modern_form`, `check_russian_shadow`). **ADR-010 PROPOSED merged (#1881)** covering Phase 3 designs (verify_external Tier-2 ladder, Pydantic verdict envelope, asymmetric per-dim review tools). **5 PRs merged this session** (#1879, #1880, #1881, #1867, #1869). **3 direct commits to main**: subtree worktree-layout standardization, writer/reviewer prompt rewrite for #1807 single-primitives, and **X-Agent commit trailer guardrail** (lint + warn-only pre-push hook). **Drift caught the hard way:** EPIC #1787 was already 100% shipped on 2026-05-08 (PRs #1788/#1789/#1792/#1793) but EPIC body never updated — re-dispatched 4 redundant tasks before Claude-headless self-refused; killed 3 others; closed #1787 retroactively. Encoded as X-Agent trailer + orchestrator-definition refinement (TODO: `lint_epic_drift.py`). Earlier same trap on #1657 Phase 1 caught pre-dispatch via live `grep` on `server.py`. Working tree clean, 0 PRs of mine open, 0 active dispatches, 0 stale worktrees, main at `f1c7a1701c`. **Codex weekly quota at 7%**, resets 01:07 May 12. **P0 next session:** prompt-validation bakeoff on a1/my-morning via `/goal` (Codex interactive). If pass → #1577 vertical-slice A1 batch unblocked. If fail → iterate prompt further on #1807.

> **Repo state (2026-05-11):** Single-PR session focused on epic #1865 item #1 (two-tier handoffs). **PR #1876 merged** (`9860cdb92a`), **sub-issue #1875 closed**. Brief format is now mandatory for new sessions — every future cold-start ramps at ~4KB instead of ~22KB on the handoff tier (−81%, −18KB total). This is the first handoff written under the spec it ships. Side traffic: 9 dependabot PRs (#1866-#1874) arrived mid-session, untouched, queued. Working tree clean, 0 PRs of mine open, 0 active dispatches. **P0 next session (user-stated 2026-05-11):** **#1657** (MCP verification-layer Phase 1) → **#1577** (V7 curriculum reboot vertical slice). **Background dispatches:** **#1787** (4 small orchestration-guardrail PRs, parallel Codex). **Tracked but not actioned:** **#1782** (persistent-listener architecture — kept active per user, premise partially superseded by Codex Desktop Automations).

> **Repo state (evening 2026-05-10 → 2026-05-11):** **3 more PRs merged this evening** (#1861, #1863, #1864) on top of afternoon's 9, **1 PR rejected + closed** (#1862, Gemini's centralize-config disaster — 10 critical findings including curriculum vandalism). Total today: **12 merged, 1 closed-REJECT, 0 admin-bypasses.** CodeQL backlog: **18 → 0 alerts** (all dismissed FP). Main green for first time since `f4bab7125f`. 2 epics filed: **#1863 cleanup plan** + **#1865 context-budget optimization** (triggered by `/usage` warning at session end — 82% at >150K context). Working tree clean, 0 open PRs, 0 active dispatches. **P0 next session: implement context-budget epic #1865 item #1 (two-tier handoffs)** before anything else — direct quota-burn reduction starting from the very next session.

> **Repo state (afternoon 2026-05-10):** **9 PRs merged** today (#1849, #1850, #1852-#1858), 0 admin-bypasses. **CI overhaul done:** PR-A (#1854) killed trigger duplication on `ci.yml`+`validate-yaml.yml`+`rules-deployment-check.yml`; PR-B (#1855) dropped torch `--force-reinstall` + adopted `setup-python` `cache:'pip'` (pytest 5:00→4:33 cold-cache, expected to drop further as cache warms). PR-C (router job for `gemini-dispatch.yml` skip cascade) deferred. **3-agent quorum review pattern validated** (Codex + Gemini + Claude judge with #M-4 verification) — saved at `reviews/2026-05-10/{codex,gemini,quorum-verdict}.md`. **Morning queue cleared:** #1794 (#1857), #1799 (#1856), #1801 (#1850), #1805 (#1858 with 4 sub-tasks) all shipped. **v5/v6 deprecation done right after first attempt failed:** Gemini caught Codex's #1851 destroying forensic docstrings; closed and replaced with #1853 (PRESERVE-original-prepend-OBSOLETE banner). **Empirical CI finding:** only `Test (pytest)` is branch-protection-required on main; all other checks cosmetic. Working tree clean, 0 open PRs, 0 active dispatches. **P0 next:** open noop PR to verify PR-A duplication fix stuck on subsequent PRs; user runs `/graphify docs/` for docs-only graph; user dismisses CodeQL `actions` lane via repo settings + #1762 12 alerts via UI; pytest matrix split reconsider after 2-3 PRs of warm-cache data.

## Latest handoff (read this first)

> **Two-tier format (epic #1865 item #1, shipped 2026-05-11):** new rows ship a **brief.md** (cold-start entry point, ~4KB) AND an **.html** (rich human-read). Agents read the brief; humans read the .html. Older rows predate the split and have only an .html — those agents need to read the full HTML, expensive but unavoidable until backfilled.

| Thread | Handoff | Status |
|---|---|---|
| **Evening 2026-05-11 — Phase 2 MCP shipped + orchestrator hygiene caught** | **Brief (read first):** `docs/session-state/2026-05-11-evening-phase2-mcp-and-orchestrator-hygiene-brief.md`<br>**Detail (human-read):** `docs/session-state/2026-05-11-evening-phase2-mcp-and-orchestrator-hygiene.html` *(HTML, eleventh under #M-2)* | **5 PRs merged + 3 direct commits + 1 EPIC closed + 4 redundant dispatches caught. Phase 2 of #1657 100% done on main: `verify_quote` (#1880), `verify_source_attribution` (#1879 — required 6-conflict rebase after #1880 landed on same files), `check_modern_form` + `check_russian_shadow` already there. ADR-010 PROPOSED merged (#1881) — Phase 3 design with `verify_external` Tier-2 ladder, Pydantic verdict envelope, asymmetric `review_dim_*` (only naturalness + decolonization get server-side bundles). Writer + reviewer prompts rewritten (`28417cc3cb`) to call new primitives as single calls vs compose-pattern — addresses #1807 tool-theatre; awaiting bakeoff. **Drift caught:** #1787 was already shipped 2026-05-08 (PRs #1788/#1789/#1792/#1793) but EPIC body never updated; re-dispatched 4 redundant tasks before Claude-headless self-refused → encoded as **X-Agent commit trailer** guardrail (`scripts/audit/lint_agent_trailer.py` + warn-only pre-push hook + AGENTS.md/GEMINI.md/rule deploy). Plus subtree worktree-layout standardization (`1515fc5a8a`). 2 dependabot greens merged (#1867 markdown2, #1869 joserfc). Stash dropped (was stale post-`playgrounds→dashboards` rename). Codex weekly 7% remaining, resets 01:07 May 12. **P0 next:** prompt-validation bakeoff on a1/my-morning via `/goal`. PASS → #1577 vertical slice; FAIL → iterate #1807. Tracked: #1782 (per user), #1870/#1874 react atomic merge, 5 dependabot reds/yellows, ADR-010 user accept/revise.** |
| **2026-05-11 — Two-tier handoffs shipped (epic #1865 item #1)** | **Brief (read first):** `docs/session-state/2026-05-11-two-tier-handoffs-shipped-brief.md`<br>**Detail (human-read):** `docs/session-state/2026-05-11-two-tier-handoffs-shipped.html` *(HTML, tenth under #M-2)* | **PR #1876 merged (`9860cdb92a`). Sub-issue #1875 closed. Brief format mandatory for new sessions — `claude_extensions/rules/workflow.md` § "Two-tier handoffs" + 15-field YAML schema + body shape + pair-authoring rule. First handoff written under its own spec (self-referential PoC). −18KB per cold-start on the handoff tier (22KB→4.3KB, −81%). Single-PR session by design — compound benefit justifies narrow focus. Side traffic: 9 dependabot PRs (#1866-#1874) arrived untouched, queued. **P0 next session (user-stated):** **#1657** (MCP verification-layer Phase 1) → **#1577** (V7 vertical slice). **Background:** **#1787** (4 small guardrail PRs, parallel Codex). **Tracked:** **#1782** (kept active per user).** |
| **Evening 2026-05-10 — CodeQL clearance + cleanup plan + context-budget epic** | **Brief (read first):** `docs/session-state/2026-05-10-evening-codeql-cleanup-and-context-budget-brief.md`<br>**Detail (human-read):** `docs/session-state/2026-05-10-evening-codeql-cleanup-and-context-budget.html` *(HTML, ninth under #M-2)* | **3 PRs merged (#1861, #1863, #1864) + 1 REJECTED (#1862, Gemini cross-file refactor disaster — 10 findings, curriculum vandalism, hallucinated pedagogy). CodeQL 18→0 alerts dismissed. Main green for first time since `f4bab7125f` (~8h gap). Codex `codex-dashboards-rename` dispatched + landed cleanly (6 files, +36/-35, perfect rename). 2 epics filed: #1863 cleanup plan (5-phase, 10 categories) + #1865 context-budget optimization (6 items, order 1→3→5→2→4→6, triggered by `/usage` "82% at >150K context"). All worktrees + stale branches cleaned. P0 next: epic #1865 item #1 (two-tier handoffs — brief.md + .html) to compound-benefit future sessions.** |
| Afternoon 2026-05-10 — CI overhaul + queue clearance + 3-agent quorum review | `docs/session-state/2026-05-10-afternoon-ci-overhaul-and-queue-clearance.html` *(HTML, eighth under #M-2)* | **9 PRs merged + 0 admin-bypasses + 8 dispatches fired. CI: PR-A (#1854) trigger duplication kill, PR-B (#1855) pytest perf, PR-C deferred. Morning queue cleared: #1794→#1857 (with 1 inline 3-LoC revert for Gemini scope creep on lint_anti_menu.py), #1799→#1856, #1805→#1858 (4 sub-tasks; PR opened manually after Codex pushed branch but skipped `gh pr create`). v5/v6 deprecation: closed bad #1851 (destroyed forensic content per Gemini review), replaced with #1853 prepend-OBSOLETE-banner-PRESERVE-original. 3-agent quorum review pattern validated: Codex+Gemini independent reviews ~80% overlap; Claude judge breaks ties via #M-4 verification. Token economics inverted from morning: Claude inline ~3% weekly was the constrained resource (not Codex); survived 9 PRs on near-pure orchestration. P0 next: verify PR-A duplication fix on noop PR; `/graphify docs/`; CodeQL `actions` UI disable + #1762 12 alerts UI dismissal; pytest matrix decide on warm-cache data.** |
| Morning 2026-05-10 — orientation rewrite + graphify install + secret-leak postmortem | `docs/session-state/2026-05-10-morning-orientation-rewrite-and-graphify-install.html` *(HTML, seventh under #M-2)* | 3 commits clean. PR #1843 merged (Codex Desktop UI sweep). curriculum-maintainer.md rewritten 24.9→15.4KB after Codex+Gemini cross-review (thread `b6bac43c`); 6 revisions applied. MEMORY synced 6:4→3:3:3 split + v6→v7 in both locations. graphify installed for claude+gemini CLIs (Codex variant at `~/.agents/skills/graphify` removed by user via Gemini CLI — older SKILL was masking newer one due to .agents > .gemini scan order); BeforeTool hook in gemini_extensions/settings.json for survival across deploy stomp; OAuth posture (key commented out by user). 1 secret-leak incident: GEMINI_API_KEY printed verbatim during diagnostic; new MEMORY #M-5 + autopsy shipped; user rotating. Codex Desktop worktree removed post-merge. **All 4 P0 inherited dispatches (#1794, #1799, #1801, #1805) cleared this afternoon.** |
| Evening 2026-05-09 — Codex Desktop comms validated + tech-debt push (+ late-evening closeout) | `docs/session-state/2026-05-09-evening-codex-desktop-comms-validated-and-tech-debt-push.html` *(HTML, sixth under #M-2)* | 8 PRs merged + 5 issues closed + 0 admin-bypasses. Codex Desktop comms test executed end-to-end: hooks empirically don't inject `additionalContext` into Desktop model context; Codex Desktop Automations is the right primitive (per Late-evening closeout: ADR addendum `8bf0d42f0c`). MEMORY reconciled (#1825 closed → 143 lines, deployed) with new #M0 row 8 + #M-1 amendment. 8 dispatches fired (#1838→#1840, #1819→#1842, #1822→#1841, #1806→#1844, #1809 stale-closed, #1828→#1845, #1779→#1846, #1778→#1847) — all merged via watcher `bp1mya3x7`. Plus inline fixes: #1848 orient session_hints includes HTML handoffs, `6d81e694b1` api auto-reload. P0 next was: user dismisses CodeQL alert on #1843 + #1762 via UI; brief + dispatch #1794, #1799, #1801, #1805; restart Monitor API once. **#1843 NOW MERGED this morning; Monitor API restarted by user; #1794/#1799/#1801/#1805 + #1762 UI dismissal still queued.** |
| Afternoon 2026-05-09 — Decision Graph ADR shipped + Codex Desktop comms MVP | `docs/session-state/2026-05-09-afternoon-codex-desktop-comms-mvp.html` *(HTML, fifth under #M-2)* | 12 commits clean. 3 PRs merged: #1835 (`1c475c9874` + N1 fix `b7a9748c9b`) Decision Graph ADR round-3 revisions (supersedes #1791); #1836 (`5029c8adbc`) Codex Desktop's autonomous UI follow-up; #1837 (`fdf2a47aa0`) Codex Desktop comms MVP — `codex-desktop`/`claude-desktop` as first-class flat-string identities in `VALID_AGENTS` + registry (`cli_available=False`) + argparse choices + `ab channel tail --follow` + cli_available guards on `inbox run`/`discuss --with`/`sync --all`. Plus `1ff563585f` #M-3 extension (work-state lesson), `6a4b78fc55` round-4 ADR audit cherry-pick, `73d5316a04` ADR HTML companion, `242100ee36` Codex Desktop comms research report. 1 inline ≤5-LOC fix (test_channels_discuss_resume.py monkey-patch for new cli_available gate). #1832 closed not-planned (misclassification self-corrected; refs/recovered/* anchors preserved). #1834 filed (MEMORY trim-pass). P0 next was: test the Codex Desktop comms MVP end-to-end — DONE this session (see evening handoff). |
| Lunch 2026-05-09 — orchestration cascade + 5 PRs merged + 0 admin-bypasses | `docs/session-state/2026-05-09-lunch-orchestration-cascade-and-clean-merge.html` *(HTML, fourth under #M-2)* | 9 commits clean. 5 PRs merged: #1827 (`af17ece46a`) idempotency, #1830 (`a92d78cc70`) `.codex/` sync, #1831 (`def7788cd5`) **perf-flake keystone**, #1829 (`132e5dad99`) `ab discuss` read-only, #1824 (`13a97c0ca7`) Codex Desktop UI revamp. 2 audit cherry-picks (`a36da4e0cb` #1791 review, `c552d8514c` #1824 review). 2 inline ≤5-LOC fixes resolved CI cascade after #1831 unblocked everything (test-wording on #1829, allowlist on #1824). 4 issues filed (#1825 MEMORY drift, #1828 CSS debt, #1832 phantom edits, #1826 perf flake closed by #1831). All 5 dispatch worktrees pruned. Open: only PR #1791 (REVISE per Claude round-3 review). |
| Morning 2026-05-09 — /artifacts route + #M-4 rule + Codex Desktop dispatched | `docs/session-state/2026-05-09-morning-artifacts-route-and-deterministic-rule.html` *(HTML, third under #M-2)* | 5 commits clean (`c17450a6c1` /artifacts router + 9 migrations, `dc0238c953` 8 more migrations, `653ffe39e9` #M-4 rule, `1ea4d241c4` Codex Desktop brief, `25484e5dec` /artifacts prefix fix). 4 issues filed (#1820/#1821/#1822/#1823). Multi-agent discussion `33d8893f` converged: HTML as companion to MD, NOT replacement (Codex's hard rule). Round-2 violated read-only — encoded as #1821. Codex Desktop dispatched for UI revamp (precedent: kubedojo). #M-4 paid for itself in its first hour by catching a stale prefix claim in the handoff itself. |
| Late-night 2026-05-09 — gemini-tools cwd fix + 3-PR clean overnight | `docs/session-state/2026-05-09-late-night-gemini-tools-cwd-fix.html` *(HTML, second under #M-2)* | 3 PRs merged (#1816 HTML backfill, #1817 gemini-tools audit, #1818 gemini-tools cwd fix). 2 issues activity (#1811 closed, #1815 filed for upstream deploy-script gap). 0 admin-bypass violations — `#M-0.5` held. Audit found root cause: gemini-tools writers ran with cwd=module_dir (no `.gemini/settings.json`), so `--allowed-mcp-server-names sources` filtered an empty MCP catalog. Fix is 1-line ternary in v7_build.py. Bakeoff verification queued for user. |
| Overnight 2026-05-08→05-09 — codex-tools fix + HTML migration kickoff | `docs/session-state/2026-05-09-overnight-codex-tools-and-html-migration.html` *(HTML, first under the new policy)* | PR #1813 merged (admin-bypassed pytest:fail — perf flake). 2 issues filed (#1811 deploy invariants, #1812 fix tracking). 4 MEMORY rules added (#M-3, #M-2, #M-1, #M-0.5). HTML migration policy adopted; this handoff is Phase 1 proof-of-concept. Bakeoff verification queued (still unverified after this shift). |
| Overnight orchestration shift (Codex/Gemini/Claude-headless) | `docs/session-state/2026-05-09-night-shift-orchestration.md` | 1 merged (#1788). 7 open PRs (#1789, #1791, #1792, #1793, #1795, #1796, #1797). 5 issues filed (#1785, #1786, #1787, #1790, #1794). 3 multi-agent reviews shipped via Claude headless. #1790 = A1-blocker escalation. #1791 (Decision Graph ADR) and #1792 await rebase before merge. #1789 + #1791 in flight as REVISE per Claude review. |
| Replacement evaluation done + autonomous mode flip + A1 blocker reframe | `docs/session-state/2026-05-08-replacement-evaluation-and-autonomous-mode.md` | 3 PRs merged (#1781 HARD STOP RULE, #1783 tier-2 warm-cache, #1784 codex MCP). Replacement eval: both Codex+Gemini say KEEP. 7 guardrails identified, 1 shipped, 6 queued. Bakeoff signal on Codex INVALID until re-run post-#1784. **2026-05-08 night-shift verified #1784 was insufficient — see #1790.** |
| Bakeoff blockers cleared + first attempt failed + prompt fix in flight | `docs/session-state/2026-05-07-bakeoff-blockers-cleared-and-first-attempt.md` | 10 PRs merged 2026-05-07 (#1763 #1766 #1767 #1757 #1769 #1772 #1775 #1776 #1777 #1780 + #1760). 6 follow-up issues filed. Bakeoff attempt #1 failed at 1801s — Claude went meta, Gemini stalled, silence-timeout fired. PR #1781 fix landed via this session. |

## Predecessor chain (most-recent first)

| Thread | Handoff |
|---|---|
| Tech-debt arc + dispatch infrastructure cascades + PAT auth blocker (yesterday morning) | `2026-05-06-evening-tech-debt-arc-and-auth-cascades.md` |
| Path-A orchestration plan (early 2026-05-07 morning) | `2026-05-06-tonight-path-a-orchestration.md` |
| Channels rollout + ADR cycles + writer-lock ACCEPTED + orchestrator-discipline reset (afternoon) | `2026-05-06-channels-rollout-adr-cycles-and-orchestrator-discipline.md` |
| Discussion converged + Gemini fix shipped + channels-UX deferred (this morning's pre-session) | `2026-05-06-morning-discussion-converged-and-channels-ux.md` |
| Writer-selection bakeoff: Codex wins; Decision Card pending | `2026-05-06-bakeoff-result-codex-wins-decision-pending.md` |
| Four fixes merged + bakeoff re-running (mid-state) | `2026-05-06-four-fixes-merged-bakeoff-rerunning.md` |
| Multi-dispatch arc + slovnyk.me unblock | `2026-05-04-evening-multi-dispatch.md` |
| Tools-before-A1/20 ordering locked + git cleanup completed | `2026-05-04-tools-before-a1-20.md` |
| MCP verification-layer architecture kickoff + Antonenko ingest incident | `2026-05-04-mcp-verification-architecture-kickoff.md` |
| #1639/#1644 closed + POC fully unblocked | `2026-05-02-1644-cleanup-and-poc-unblocked.md` |
| Multi-Agent Deliberation Protocol shipped + onboarded + validated | `2026-05-02-deliberation-protocol-shipped.md` |
| POC plan locked + #1631/#1632/#1637 prereqs merged | `2026-05-02-poc-plan-locked-and-prereqs-merged.md` |
| Dependabot triage + lockfile fixes + UK framing-A clarification | `2026-04-30-dependabot-lockfile-fixes-and-uk-framing-clarification.md` |
| Phase 4 architectural correction + ADR-008 PROPOSED | `2026-04-29-phase-4-architectural-correction-and-adr-008.md` |
| Wiki cleanup + lit-* completion + hygiene flush | `2026-04-28-wiki-cleanup-and-hygiene-flush.md` |
| EPIC #1577 reboot — Round 3.5 shipped, decision pending on user re-run | `2026-04-26-session-close.md` |
| Round 3.5 prompt-tighten shipped (#1603) — full detail | `2026-04-26-round-3.5-shipped.md` |
| Round 3 QG bugfixes shipped (#1599) | `2026-04-26-qg-bugfix-shipped.md` |
| Phase 4 round 3 dispatched (strict-JSON exemplar) | `2026-04-26-evening-handoff.md` |
| Autonomous orchestration during user-away window | `2026-04-26-autonomous-orchestration.md` |
| Overnight wiki rebuild + Phase 4 dispatch | `2026-04-26-overnight-claude.md` |
| EPIC #1577 reboot — Phase 0–3 done, Phase 4 staged | `2026-04-26-overnight-1586-phase4.md` |
| EPIC #1550 a1/1 verification (Unit 6 A/B) | `2026-04-25-orchestration-final-with-data.md` |
| Wiki retrieval overhaul (#1553) | `2026-04-25-wiki-retrieval-overhaul-1553.md` |
| Cold encode complete → next is #1569 | `2026-04-25-cold-encode-complete.md` |

## Cold-start protocol

1. Read this index.
2. Open the **Brief** link in the top row of the "Latest handoff" table — that's the cold-start entry point (~4KB, machine-readable). Open the **Detail** `.html` only if the brief flags something you need narrative for. If the top row has no brief (predates the split), fall back to the .html.
3. **Check `docs/decisions/pending/`** for any Decision Cards awaiting user input. Pending decisions are BLOCKING — surface them to the user before starting any new work that could invalidate them. Convention: see [`docs/decisions/pending/README.md`](../decisions/pending/README.md) and the "Multi-Agent Deliberation" section of [`docs/best-practices/agent-cooperation.md`](../best-practices/agent-cooperation.md).
4. If picking up a thread that spans multiple sessions, open the relevant predecessor(s) from the "Predecessor chain" table for context.
5. If you create a new handoff, **ship the pair** (`*-brief.md` + `*.html`) per the two-tier format spec in `claude_extensions/rules/workflow.md` § "Two-tier handoffs". Add one row to the "Latest handoff" table above linking both, and shift the previous "Latest" into "Predecessor chain" — do NOT replace this whole file.

## Cross-thread notes (still active)

- **Kubedojo Decision Graph paradigm + persistent listener architecture
  follow-ups** — Tracking doc:
  `docs/session-state/2026-05-07-kubedojo-paradigm-followups.md`.
  - Actions A-D from the morning kubedojo conversation (D4 lineage scanner,
    3 infra bugs, Decision Graph ADR, kubedojo team reply) remain QUEUED
    behind bakeoff completion + writer-selection signoff.
  - **NEW evening additions:** Persistent agent listener architecture
    (issue **#1782**, `decision-pending` label). Tier-2 warm-cache fix
    DISPATCHED via Codex (`tier-2-warm-cache`, ~50-100 LOC PR, fixes
    `ab discuss` cold-cache asymmetry: switches entrypoint `delegate`→`bridge`
    + per-(agent, discussion) session_id gated by registry resume_policy).
    Tier-3 daemon listeners DEFERRED until pending Multi-UI ADR ACCEPTED.

- **Phase 4 round 3.5 verification = round-4 bakeoff trigger** —
  shipped via #1621. Gemini-tools writer fails writer-discipline gates
  (word_count short, meta-narration bypass via paragraph-level
  rephrasing, JSX prop-stuffing for immersion gaming). Round-4 bakeoff
  is filed as **#1622** but blocked on TWO prereqs: **#1631** (wiki
  migration) and **#1632** (ADR-008 implementation). See
  `2026-04-29-phase-4-architectural-correction-and-adr-008.md`.

- **ADR-008 PROPOSED on main** (`f4df43af06`, PR #1633). Defines
  per-gate bounded correction paths under four hard architectural
  constraints (patch-bounded, full revalidation, pipeline-assisted
  dictionary, one attempt per gate). Cross-agent reviewed by Gemini +
  Codex; both REVISE on v1, v2 incorporates their findings. **Awaits
  user signoff to flip PROPOSED → ACCEPTED.** Implementation tracked
  at #1632. Refines but does NOT supersede ADR-007.

- **V7 retrieval-layer drift identified** — `linear_pipeline.py` was
  inadvertently calling V6-era Qdrant path (`scripts/rag/query.py`)
  instead of V6's wiki path (`_build_wiki_packet` +
  `compress_wiki_packet`). PR #1628 hardened the deprecated path; PR
  #1630 reverted it. The real fix is **#1631 wiki migration**: port V6
  wiki reader into linear_pipeline + use MCP sources for dictionary
  verification. No Qdrant in the V7 architecture.

- **Three-agent code dispatch pattern validated** (Codex/Claude/Gemini)
  per user directive 2026-04-28. Empirical signal recorded in the
  2026-04-29 handoff: Codex fastest one-shot for mechanical fixes;
  Claude depth + iteration on architectural; Gemini functional but
  hits rate limits + missing summary on cutoff (orchestrator must
  reconstruct). Full quality/cost profile in handoff.

- **Wiki rebuild fully landed.** All 8 lit-* tracks complete on main
  (435 articles), all other namespaces (academic, figures, folk,
  grammar, historiography, linguistics, mastery, pedagogy, periods)
  refreshed post-#1592 citation-shift. `wiki/.state/progress.db` has
  1492 articles, all post-shift, disk:DB sync clean.

- **Wiki search-index rebuild pending.** When the wiki rebuild
  finished (it has — see 2026-04-28 handoff), the search index needs
  refresh against the new artifacts. Also: `wiki/index.md` was last
  regenerated mid-rebuild and should be re-built via
  `.venv/bin/python scripts/wiki/compile.py --update-index`.

- **Cold-encode 88,192 units / 4 corpora committed 2026-04-25 evening**
  (wiki agent). All `up_to_date: true`. GDrive backup refreshed. The
  retrieval layer is consistent with PR #1555's paragraph-aware
  chunker.

- **Pyenv-rehash 60s lock — FIXED 2026-04-28.** Stale sentinel removed,
  preventive SessionStart hook now auto-cleans any sentinel >1 min old.
  See `claude_extensions/hooks/session-setup.sh` lines 6–32.

- **`GH_TOKEN` lives in the project root `.envrc`** (loaded by direnv when
  you `cd` into the project). NOT in `~/.bash_secrets` — that wrong note
  was in this file for a while and bit several agent sessions including
  2026-05-07 (corrected by user after Codex's #1783 dispatch hit a 401).
  The user maintains separate GH tokens per project; the `.envrc` token
  is the project-scoped one. For `gh` calls inside dispatched subprocesses
  that don't run direnv, ensure the dispatch wrapper sources `.envrc`
  explicitly before invoking `gh`. Issue noted in #1782 sub-task list.

- **`experiments/phase-4/round-3.5/`** preserves the failed Gemini
  round-3.5 outputs as evidence (per Codex REVISE finding 5 on PR
  #1621). Useful for round-4 bakeoff comparison once #1622 fires.

- **Main is at `143c955c40`** as of 2026-04-30 session close.
  Sequence of recent main commits worth knowing:
  - `143c955c40` chore(deps): fix lockfile internal inconsistencies (no PR — direct push)
  - `da0ed4c660` deps: vitest 4.1.5 (#1618)
  - `94b08cd12b` deps: astro 6.1.9 (#1617)
  - `719dc035cc` ci: actions/cache 5.0.5 (#1616)
  - `bc2b0cd5ce` deps: @vitest/coverage-v8 4.1.5 (#1615)
  - `a58bd57ef4` deps: cryptography 47.0.0 (#1614)
  - `9477b8e01b` deps: @astrojs/starlight 0.38.4 (#1613)
  - `ec31dd758c` deps: google-auth 2.49.2 (#1612)
  - `1a58305722` deps: @astrojs/react 5.0.4 (#1611)
  - `a1483b2ddc` deps: anthropic 0.97.0 (#1610)
  - `ccb615df19` deps: pathspec 1.1.1 (#1609)
  - `4367dcdb28` deps: ipdb >=0.13.13 (#1608)
  - `f4df43af06` docs(adr): ADR-008 PROPOSED (#1633)
  - `ad54161ec0` revert: Qdrant fail-fast on deprecated path (#1630)
  - `b5d894d009` feat(qg): per-type extra-field validation (#1627)
  - `e0f8db8fb1` fix(qg): VESUM gate skips errorWord (#1626)
  - `253f3c00c4` feat(phase-4): A1/20 round-3.5 verification (#1621)

- **#1634 (NEW, open):** lockfile resolver migration — `requirements-lock.txt`
  is `pip freeze` output, no cross-package validation; today's commit
  `143c955c40` is a bandaid. Proper fix: migrate to pip-tools / uv / poetry.
  Recommended: pip-tools.

- **Framing A vs B clarification** added to `memory/l1-uk-corpus-bootstrap.md`
  (Claude-local, not in repo). When discussing UK track / wiki rebuild:
  Framing A says wikis ARE the UK content-creation track (yabluko-equivalent
  decolonized pedagogical artifacts). Framing B says "wiki is just retrieval
  plumbing, no UK track needed." Same architecture, different value bar —
  Framing B silently demotes citation audits + register reviews. Adopt
  Framing A explicitly. Cross-agent broadcast (bridge `architecture` thread
  `be8c4617`) NOT done — would need explicit user request to fire.

- **#1604 (open):** `PhraseTable` (and other vocabulary-tab activities)
  get `activity_type: null` in `lesson-schema.yaml`. Schema-generator
  fix needed. Not Phase-4-blocking.

- **`lit-doc` / `lit-crimea` scrub fan-out:** wiki/ tooling fully
  cleaned, but references remain in `scripts/api/`, `scripts/scoring/`,
  `scripts/generate_mdx/`, `scripts/build/v6_build.py`,
  `scripts/research/`, `scripts/tools/`, `scripts/sync/`. Filing as a
  separate issue is the recommended path. Not Phase-4-blocking.

- **Round-3 failed Gemini exemplar artifacts** preserved in repo
  `stash@{0}` and `stash@{1}` (duplicates). `git stash show -p
  stash@{0}` to inspect — useful for round 3.5 prompt-tightening
  evidence.

- **Adversarial review discipline** (added 2026-04-26 late): all 3
  agents (bot + Gemini + Codex) must review code PRs before merge.
  Drive-by bot is not a substitute. Reviews are cheap and parallel;
  silent merge then bug-then-fix is expensive.

- **CI bypass on chore-wiki pushes:** GitHub flags `Required status
  check "Test (pytest)" is expected` on direct main pushes. User
  account has bypass permission for `refs/heads/main`; pushes go
  through, audit log captures the bypass. Pytest still runs in CI
  background — check Actions tab if curious.
