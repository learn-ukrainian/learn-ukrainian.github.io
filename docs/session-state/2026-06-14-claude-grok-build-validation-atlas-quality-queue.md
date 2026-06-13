# Claude session handoff — 2026-06-14 (grok-build lane VALIDATED · Atlas quality-queue merged · grok-swarm building §6)

> Router: `current.md` → `current.claude.md` → this. Dense session — read top-to-bottom.
> **Next session's first job: VERIFY the two in-flight grok-swarm outputs + land #3105/#2901 + run the deferred Atlas re-enrich.** See §In-flight and §Next.

## TL;DR
- **Atlas quality-grind queue: 5 PRs merged to main** (#3100 esum-desc-all-vols, #3101 UA-GEC tag_filter bug, #3104 §6 calque dataset, #3099 §12 Вікі + my license/cache fix, #3102 #2971 etymology + #3092 synonyms).
- **grok-build lane VALIDATED** (user: kubedojo peer says grok-build >> grok-4.3). Full bridge support shipped (#3105). The 4-agent purist swarm was tested + **independently corroborated (0 fabrication)** — heritage gate works (блискучий clean), MCP-grounded.
- **Routing decision (user 2026-06-14):** codex-swarm owns B1 QG/review (user driving that); **grok-swarm owns Word Atlas building**. grok-build single = tech-debt lane (#2901 live). $99/16-agent SuperGrok upgrade DEFERRED until 4-agent hits a ceiling.

## ✅ Shipped (merged to main this session)
| PR | What |
|---|---|
| #3100 | ЕСУМ MCP description → all 6 vols (was "vol 1 only"); fixed server.py + sources_db.py docstring + the `mcp-sources-and-dictionaries` rule source + test docstrings. Verified DB serves vol1-6 (36,177 rows). |
| #3101 | **UA-GEC `tag_filter` ambiguous-column bug** — `error_type` unqualified across f+m tables. Root-caused + qualified `m.error_type` + regression test. Unblocks 2397 F/Calque pairs. |
| #3104 | §6 calque-correction authority dataset `scripts/lexicon/calque_corrections.py` — 22 source-grounded active-participle calques (Glazova/Avramenko NUS + Antonenko) + 4 phrasal + 11 lexicalised-safe + heritage-gate spec. VESUM-verified. |
| #3099 | §12 Вікі-довідка (agy) + **my fix**: CC-BY-SA 3.0→4.0 (4 occurrences incl. kaikki sibling) + `@functools.cache` on query_wikipedia (was 1 HTTP/ lemma). deepseek-reviewed 6/7 PASS. |
| #3102 | #2971 derivational-base etymology + #3092 §7 synonyms via Karavansky/sense-filtered slovnyk (WordNet/ukrajinet dropped). **deepseek-pro reviewed PASS 5/5, no must-fix**; варити→фальсифікувати/бариги hazard test-asserted gone. |

## 🔄 In-flight (VERIFY/LAND these first)
1. **grok-swarm Atlas §6 calque extension** — background `bhmf66dbs` → `/tmp/grok-atlas-calque.log`. Mines NEW calques from Антоненко + UA-GEC F/Calque, heritage-gated, ends with a ```json``` array of dataset entries. **DON'T trust self-report — spot-check entries via mcp__sources__ (search_heritage + verify_word) then integrate verified ones into `calque_corrections.py` as a PR.**
2. **#3105 grok-build full bridge support** (codex, 16 files: `_grok_build.py` + adapter/registry/telemetry/_cli/_model/_env + 2 tests, telemetry "unknown model/effort" gap fixed). In deepseek review (`review-3105-grok-bridge`); CI green so far. **Land when review + pytest green.**
3. **#2901 grok-build literary source_url** — `delegate --agent grok-build`, running. Restores source_url through literary ingest (needs full DB rebuild to backfill — orchestrator-run). Review + merge when PR opens.
4. **folk dossiers** (#3103 striletski-povstanski + folk-dossier-rodynno-pobutovi) — codex track work, **awareness-only** unless the track asks.

## 🎯 Next (priority order)
1. **Verify + integrate the grok-swarm §6 calque output** (`/tmp/grok-atlas-calque.log`) → PR extending `calque_corrections.py`.
2. **Land #3105 + #2901** when green.
3. **Controlled Atlas re-enrich** (the visible payoff of #2971/#3092/#3096, all merged but NOT yet in the deployed manifest): run `enrich_manifest` on the main tree (WARM slovnyk cache, 3787 files) → **spot-check варити/хата/шлях/мрія synonyms + base-form etymology + §12 wiki** → commit `site/src/data/lexicon-manifest.json` ONLY if clean (per #M-11 verify-before-promote; m20 lesson). This is ONE background process (#M-9).
4. **#3098 §6 enrich wiring + template** — the calque DATA (#3104) + extension are landed/landing; now wire `_calque_warning()` into enrich_manifest + a §6 template card (now safe — the 3-way enrich_manifest.py conflict is resolved since #3099/#3102 merged).
5. deepseek #3102 nice-to-haves: negative test for group-head rejection; typo'd constant `_DERIVATIONAL_ETYMLOGY_BASES` (missing M).

## 🤖 grok-build lane — validated facts
- Native CLI at `~/.local/bin/grok`; **MCP `sources` already wired** (`grok mcp list` → `sources: http://127.0.0.1:8766/mcp`). Models: grok-build (default) + grok-composer-2.5-fast.
- Subagent mechanism: `grok -p '<captain>' --agents '<JSON>' --yolo -m grok-build --max-turns N`. Agents JSON schema `{name:{description,prompt,model}}` saved at `/tmp/grok-agents.json` (Джерело/Будова/Чистомовець, heritage-gated). Subagents inherit the `sources` MCP.
- **Caveat:** streamed subagent output interleaves char-by-char (garbled); only the FINAL Captain synthesis is clean. For harness use, capture final block / use `--output-format json`. Heavy: ~100+ tool calls/specialist per small batch — great for purist audits, not bulk speed.
- **Migration candidate:** V7 `grok-tools` writer uses Hermes `grok-4.3` (`linear_pipeline.py:89,137`) — should move to native grok-build (separate writer pilot, NOT the swarm). MEMORY #0 line updated (grok-build VALIDATED, prefer over grok-4.3).

## 📨 Parked for user
- **#3097** slovnyk.me local mirror — licensing/permission (Лепетун) — user-owned.
- **SuperGrok $99/16-agent** upgrade — decide only if 4-agent hits a ceiling on a real task.

## ⚠️ Lessons
- **git-verify the artifact, not the field name** — early this session I read `entry['etymology']` (top-level, always False) instead of `entry['enrichment']['etymology']` and nearly mis-reported the #3095 deploy as broken. The deploy was fine. Always confirm the actual schema before claiming.
- The grok swarm's "0 fabrications" self-report was TRUE on spot-check (інтерес Грінченко exact match; проблема ЕСУМ etym match) — but ALWAYS spot-check anyway (#M-4).
- Did a 3-line docstring fix (#3085→#3100) + the UA-GEC fix in branch-in-main / worktree; both fine, but tiny fixes should still prefer worktrees per the rule.

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git log -1 --oneline origin/main
cat /tmp/grok-atlas-calque.log          # grok swarm §6 output → verify + integrate
curl -s http://localhost:8765/api/delegate/active   # #2901 + reviews
gh pr list --state open                 # #3105, #2901(when opens), #3103
```
