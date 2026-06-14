# Claude session handoff — 2026-06-14 (§6 calque integrated · stale MCP server root-caused · Atlas re-enrich in flight)

> Router: `current.md` → `current.claude.md` → this. Read top-to-bottom.
> **Next session's first job (if re-enrich unresolved): check PID/`/tmp/atlas-reenrich.log`, run `/tmp/atlas-spotcheck.py`, commit manifest IF CLEAN.** See §In-flight.

## TL;DR
- **#3110 MERGED** — §6 grok-swarm calque integration (`PHRASAL_CALQUES` +6, new `SENSE_RESTRICTED_CALQUES` bucket +5 polysemes, regression test) **+ a Content-Gate scope fix** (the dossier word-count gate falsely flagged `docs/research/atlas/` notes). All CI green.
- **Stale sources MCP server root-caused + fixed** — `tag_filter` still threw the `ambiguous column name` error #3101 had fixed; the running server (PID 8432) predated the merge. Restarted (PID 46274) → fix verified live. Recurring "fix merged but server not restarted" failure mode.
- **Controlled Atlas re-enrich IN FLIGHT** (queue #3 — handoff payoff). Confirmed the gap deterministically: deployed manifest has **synonyms 21 (old hardcoded allowlist) / wiki 0** despite #3092/#3099 merged.

## ✅ Merged this session
| PR/action | What |
|---|---|
| **#3110** | §6 calque integration. `PHRASAL_CALQUES` +6 (UA-GEC/Antonenko-grounded: точка зору→погляд, по відношенню до→щодо, ні в якому разі→аж ніяк, в дійсності→насправді, з моєї точки зору→на мою думку, прийшло в голову→спало на думку). New `SENSE_RESTRICTED_CALQUES` (5 polysemes: вірний/дійсний/відношення/рахувати/виглядати — each authentic in one sense, calque only in another; carries `calque_sense`/`authentic_sense`, soft-note contract, never blanket-flag). **Rigor catch:** swarm marked дійсно + відносно ✅ always-flag, but live verify showed both AUTHENTIC (Грінченко/СУМ-20; UA-GEC offers відносно AS a correction) → DROPPED. `tests/test_calque_corrections.py` (7) pins the drops. |
| **#3110 (+commit)** | `fix(audit)`: `check_dossier_wordcount._is_research_dossier()` matched any `docs/research/*/*.md`; exempted `_NON_DOSSIER_RESEARCH_SUBDIRS={atlas,lexicon}` + test. |
| **stale-server fix** | Restarted `sources` MCP (8432→46274); `search_ua_gec_errors(tag_filter=["F/Calque"])` now returns rows (was erroring). No PR — operational. |

## ✅ Atlas re-enrich — DONE + on main (`4fabcecfc5`); deploy is MANUAL
- Ran `enrich_manifest.py` on main (warm caches). **Coverage: synonyms 21→794 · wiki_reference 0→183 · etymology 1165→1250** (enriched 1933/2190). Spot-check (`/tmp/atlas-spotcheck.py`, now committed as `scripts/lexicon/verify_manifest.py` in #3122) hazard scans CLEAN; synonym sources 100% Караванський + СУМ синонімів (zero WordNet).
- **⚠️ DEPLOY IS MANUAL — "auto-deploys" in prior handoffs is WRONG.** `.github/workflows/deploy-pages.yml` has the `push: [main]` trigger COMMENTED OUT (intentionally, commit on 2026-06-13); only `workflow_dispatch` remains. Last deploy was 18:12 UTC 2026-06-13 (sha 19c89e6aa). Committing the manifest does NOT publish it. To release: `gh workflow run deploy-pages.yml` (builds `npm run build:full`, ~3min). User (2026-06-14) was holding the deploy back deliberately; cleared me to release — releasing after a local `build:full` check.
- **#3116 filed then CORRECTED to an enhancement:** I flagged шлях→кам'яниця / річка→звір as wrong, but the raw Караванський synsets mark them `д.`/`г.` = **dialectal** (кам'яниця = dialectal paved-road; звір = dialectal mountain-stream) — VALID, faithfully reproduced. A stoplist would've dropped valid heritage data (блискучий error). Real (low-prio) refinement: chips strip register qualifiers (д./розм./заст.) → preserve them as chip labels. Retitled #3116.

## ✅ DEPLOYED LIVE (manual `deploy-pages.yml`, run 27483805505) + ⚠️ RED-main hotfix
- User cleared the held-back deploy (2026-06-14). Local `npm run build:full` clean (40250 pages, exit 0) → triggered deploy → **verified live**: гарний shows `славний`, шлях shows `магістраль` (both new-only). The big re-enrich payoff is now on production.
- **⚠️ The re-enrich turned `test_atlas_conformance.py` RED on main** (required pytest → blocked ALL merges). Root cause: **#2971** appends ` (etymology of base form X)` to the etymology `source`; `_check_kaikki_attribution` required an EXACT match to `KAIKKI_SOURCE`, so the suffix (e.g. `kaikki/Wiktionary (CC BY-SA 3.0) (etymology of base form вигляд)`) tripped it. #2971's fixture-only tests never hit the real re-enriched manifest. Attribution prefix intact → live site fine. **Fix = #3124** (strip the suffix before the attribution check; 21/21 conformance pass). MERGE #3124 FIRST to unblock everything. Autopsy-worthy: a feature gated only by fixtures + a strict gate = latent break that detonates on the next real artifact regen.

## 🔄 In-flight — §6 calque wiring dispatch (#3098)
- Codex dispatch `s6-calque-wiring-3098` fired (worktree `.worktrees/dispatch/codex/s6-calque-wiring-3098`, branch `codex/s6-calque-wiring-3098`, base `4fabcecfc5`). Brief: `/tmp/s6-calque-wiring-brief.md`. Bg poller `byj20ofe2` notifies on completion.
- **On completion:** review the PR (generator `_curated_calque` + renderer sense-restricted SOFT card + tests). Verify the sense-restricted contract (rule 3: soft sense-scoped note, never blanket/auto-replace). Merge if green. Then a re-enrich populates `curated_calque` (1 card: виглядати). DO NOT touch `enrich_manifest.py` until this lands (conflict).

## 🎯 Next (priority order)
1. **Resolve the re-enrich** (spot-check → commit-if-clean). #M-11.
2. **§6 enrich wiring (#3098)** — brief READY at `/tmp/s6-calque-wiring-brief.md` (Codex dispatch). **De-risked: ~1 card today** — only `виглядати` of 37 dataset keys is in the A1 manifest (calque dataset targets B1+ vocab). Still worth shipping (dataset's only consumer + future-proof) but LOW urgency. `виглядати` validated additive: today classification=standard/is_russianism=False, card adds sense-note without false-flagging. Sequence after a higher-payoff manifest item.
3. **#3102 nice-to-haves** — fold into the §6 wiring dispatch (same file): typo'd const `_DERIVATIONAL_ETYMLOGY_BASES` (missing M); negative test for group-head rejection.
4. **#3106 sources.db rebuild backfill** — orchestrator-run, like the re-enrich, to backfill existing literary rows' `source_url`.

## ⚠️ Lessons / notes
- **Verify the running process, not just `ps|grep`** — my first `ps|grep python` missed the live enrich; `pgrep -fl enrich_manifest` found PID 94346. Nearly mis-diagnosed a healthy run as dead (#M-11 class).
- **TZ trap:** manifest mtime "Jun 13 23:26" is LOCAL CEST; session/PR times are UTC. Don't compare across TZ without normalizing.
- **De-risk a dispatch's payoff before firing it** — checking dataset∩manifest overlap (1/37) downgraded the §6 wiring from "headline" to "1-card, low-urgency." Cheap check, saved overselling.

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git log -1 --oneline origin/main      # expect #3110 (99d83cf489) + maybe manifest commit
pgrep -fl enrich_manifest                                    # re-enrich still running?
cat /tmp/atlas-reenrich.log                                  # final summary when done
.venv/bin/python3 /tmp/atlas-spotcheck.py                    # #M-11 gate; commit manifest IF CLEAN
cat /tmp/s6-calque-wiring-brief.md                           # §6 wiring dispatch brief (ready, low-urgency)
```
