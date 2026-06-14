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

## 🔄 In-flight — Atlas re-enrich (RESOLVE FIRST)
- Process: `.venv/bin/python -u scripts/lexicon/enrich_manifest.py` (launched bg; was PID 94346). Silent (final summary only); writes `site/src/data/lexicon-manifest.json` ONCE at end. Warm caches (`data/lexicon/slovnyk_cache` 3789, `data/wiki_cache.db`).
- **Baseline (pre-enrich):** entries 2190 · synonyms 21 · wiki_reference 0 · etymology 1165 · pronunciation 1604 (top-level). Expect synonyms ≫21 + wiki >0 after.
- **On completion:** run `.venv/bin/python3 /tmp/atlas-spotcheck.py` → it prints coverage deltas + samples present lemmas (шлях/робота/гарний/дім…; NB **варити/хата/мрія are NOT in the A1 manifest** — only шлях is) + deterministic hazard scans (WordNet-junk фальсифікувати/бариги, HTML-entity, gloss-chunk). **Commit `site/src/data/lexicon-manifest.json` ONLY if it prints `VERDICT: CLEAN`** (#M-11; auto-deploys). If not clean → `git checkout site/src/data/lexicon-manifest.json` and investigate.

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
