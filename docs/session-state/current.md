# Current — multi-agent index (2026-05-07)

> **Repo state: 10 PRs merged today, all bakeoff blockers cleared; first bakeoff attempt failed on prompt-discipline bug; PR #1781 (HARD STOP RULE fix) awaiting CI.** Trace-capture infrastructure (#1761/#1767), verbatim-quoting gate (#1725/#1757), trace-capture contamination fixes (#1768/#1775), aggregator theatre-aware winner gate (#1773/#1776), structured CoT prompt scaffolding (#1661+#1673/#1772), plan-review-time corpus check (#1765/#1769), silence-timeout default (#1758/#1763), Claude headless OAuth (#1754/#1760), crawler upgrade (#1764/#1766), A1 resource backfill (#1774/#1780) ALL on main. Bakeoff `audit/bakeoff-2026-05-07/` failed: Claude wrote 474-byte meta-summary instead of 4 artifact fences (preserved as evidence). PR #1781 fixes that. **Critical path: merge #1781 → re-fire bakeoff with `--silence-timeout 3600` → REPORT.md → writer-selection proposal → user signoff → A1 builds.**

## Latest handoff (read this first)

| Thread | Latest handoff | Status |
|---|---|---|
| **Bakeoff blockers cleared + first attempt failed + prompt fix in flight** | **`docs/session-state/2026-05-07-bakeoff-blockers-cleared-and-first-attempt.md`** | **10 PRs merged today (#1763 #1766 #1767 #1757 #1769 #1772 #1775 #1776 #1777 #1780 + #1760 from morning). 6 follow-up issues filed (#1762 #1770 #1771-closed-via-#1777 #1773-closed-via-#1776 #1778 #1779). Bakeoff attempt #1 failed at 1801s — Claude went meta, Gemini stalled, silence-timeout fired. Pre-crafted writer-selection template at `/tmp/writer-selection-proposal-template.md`. Open: PR #1781 (HARD STOP RULE). Next: merge → bakeoff retry with `--silence-timeout 3600`.** |

## Predecessor chain (most-recent first)

| Thread | Handoff |
|---|---|
| Tech-debt arc + dispatch infrastructure cascades + PAT auth blocker | `2026-05-06-evening-tech-debt-arc-and-auth-cascades.md` |
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
2. Open the file in the **"Latest handoff"** table above (top row) for current state, in-flight threads, and open questions.
3. **Check `docs/decisions/pending/`** for any Decision Cards awaiting user input. Pending decisions are BLOCKING — surface them to the user before starting any new work that could invalidate them. Convention: see [`docs/decisions/pending/README.md`](../decisions/pending/README.md) and the "Multi-Agent Deliberation" section of [`docs/best-practices/agent-cooperation.md`](../best-practices/agent-cooperation.md).
4. If picking up a thread that spans multiple sessions, open the relevant predecessor(s) from the "Predecessor chain" table for context.
5. If you create a new handoff, **add a row to the "Latest handoff" table above and shift the previous "Latest" into "Predecessor chain"** — do NOT replace this whole file.

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
