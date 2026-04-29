# Current — multi-agent index (2026-04-30)

> **Repo state: CLEAN.** As of session close 2026-04-30, no active agent
> threads, no in-flight builds, working tree empty, HEAD = origin/main
> at `143c955c40`. The "multi-agent concurrent writes" warning that
> previous current.md versions carried no longer applies — this is now
> a single-thread baseline. If a future session forks parallel work
> again, restore the warning.

## Latest handoff (read this first)

| Thread | Latest handoff | Status |
|---|---|---|
| **Dependabot triage + lockfile fixes + UK framing-A clarification** | **`docs/session-state/2026-04-30-dependabot-lockfile-fixes-and-uk-framing-clarification.md`** | **Closed clean — 11 dependabot PRs merged, lockfile coherence fixed, #1634 filed for resolver migration; ADR-008 still PROPOSED awaiting user signoff; #1631 + #1632 still pending dispatch** |

## Predecessor chain (most-recent first)

| Thread | Handoff |
|---|---|
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
2. Open `2026-04-30-dependabot-lockfile-fixes-and-uk-framing-clarification.md`
   for the latest state and open questions.
3. For Phase-4 thread context (round 4 bakeoff prereqs, ADR-008 status),
   also open the immediate predecessor `2026-04-29-phase-4-architectural-correction-and-adr-008.md`.
4. If picking up Phase-4 round-3.5 vs 4 decision history, the canonical
   prior is `2026-04-26-round-3.5-shipped.md`.
5. If you create a new handoff, **add a row to the "Latest handoff"
   table above and shift the previous "Latest" into "Predecessor
   chain"** — do NOT replace this whole file.

## Cross-thread notes (still active)

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

- **`~/.bash_secrets`** is where `GITHUB_TOKEN` lives. Not in any
  standard rc file. Source it manually before `gh` calls.

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
