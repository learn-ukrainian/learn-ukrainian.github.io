# Claude session handoff — 2026-06-15 (parallel fan-out · Atlas §6/§7 live · deps root-caused · 3 dispatches in flight)

> **ROLE:** main orchestrator = infra / tooling / tech-debt / general features / integration / merge.
> Track issues (bio/folk/lit-seminar) are track-orchestrator-owned — left alone this session.

## TL;DR
User pushed hard on parallelism ("we have lots of agents... why one at a time?"). Switched from
single-dispatch to a sustained fan-out across idle lanes, with a key discipline: **parallelize across
subsystems, serialize within shared-file clusters** (the Atlas issues all write
`site/src/data/lexicon-manifest.json` → made every Atlas dispatch **code-only / never commit the manifest**;
orchestrator regenerates it once after merge). That unlocked safe Atlas parallelism.

## Shipped (merged to main this session)
- **#3164** (`5aa34ea2aa`) — telemetry PR1 (#3153): central JSONL emitter + correlation IDs + dispatch event
  + **honest cost layer** (`pricing.py` + `model_pricing.yaml`; refuses to fabricate prices for split-rate
  API models, marks subscription lanes). PR2/PR3 (per-adapter token extraction + directional tokens) recorded
  on #3153. TODO(#3153 PR2) markers at the 9 `runner.py` `tokens=None` sites.
- **#3166** (lit-slug, #2526) — 8 outlier lit slugs aligned to the 224/232 filename convention. Verified the
  convention deterministically (96.5% slug==filename, English-descriptive) before approving the rename direction.
- **#3168** (`6e68c7d7e4`, Atlas §7, #3116) — drop wrong-sense synonyms (шлях✗кам'яниця, річка✗звір),
  **per-lemma + Грінченко-cited** `_WRONG_SENSE_SYNONYMS`, register qualifiers preserved.
- **#3170** (`63b157f2e0`, Atlas §6, #3098) — active-participle calque layer, Antonenko/textbook-cited.
  **Verified the citations are REAL via sources MCP** (antonenko p145 is the canonical "active participles
  aren't Ukrainian" passage; glazova-11 confirms працюючий→працівник etc.) — not fabricated.
- **`3752cc3df2`** — regenerated + committed `lexicon-manifest.json`. §7 LIVE+visible (шлях/річка cleaned);
  verify_manifest CLEAN, 0 violations. **§6 honest status: built+correct but DORMANT** — only `виглядати`
  (sense-restricted, correct) got a §6 note; **0 `-учий` participles in current Atlas vocab** (expected per
  #3098). §6 becomes visible only as Atlas vocab grows (#2882) or if the note also surfaces on replacement-word
  pages (possible enhancement — consider filing).

## Resolved / recorded
- **#2261 CLOSED** — torchvision moot: Dependabot bump #2226 is closed, lock at 0.26.0, named tests green.
- **#2732 documented** (NOT fixed — partial patch refused per #0.1). Root cause: lock is a `pip freeze`
  artifact (#1634) with cascading latent conflicts. Confirmed fixes: `lxml==5.4.0` (inscriptis<6),
  `pillow==10.4.0` (marker-pdf/surya <11). **Real blocker = `marker-pdf 1.10.2` HARD-pins `anthropic<0.47`
  vs project's 0.97** → architectural. Proper fix: isolate marker-pdf (ingestion-only) to requirements-dev /
  extra + adopt resolver-generated locking (pip-compile/uv). Needs a decision — did NOT auto-fire.
- **#3167 CLOSED** — agy deps dispatch STALLED (narrated "I will wait..." then timed out) + did a dangerous
  unrequested pillow 12→10 downgrade. Caught at review, not merged. (#M-8 verify-self-reports paid off.)

## LANDED — review status (2nd wave all done; 3 PRs open)
| PR | issue | status | next action |
|---|---|---|---|
| **#3177** | #2901 | ✅ **MERGED** + migration RUN on live `data/sources.db`: column added, **11,037 rows backfilled**, 126,659 NULL (those waves' JSONL absent locally — no fabrication). | **Follow-ups:** (a) most NULL rows need the missing wave JSONL to backfill (or accept NULL for archival waves); (b) `search_literary` MCP tool should SELECT+surface `source_url` so modules can actually consume it (data layer done, tool layer not). (c) MCP sources server (8766) may need restart to see the new column if anything queries it. |
| **#3179** | #2882 | ⏳ **DEFER deep review** (context heavy). +556/-5; `enrich_manifest.py` + `[lemma].astro` page + test. No manifest-data committed ✓. BLOCKED=pytest pending. | Inline-review lexicon enrich correctness + verify any new dict data via MCP. **code-only — regen manifest after merge.** |
| **#3178** | #1905 | 🔴 **NEEDS FIX — do NOT merge.** Touched PRODUCTION code (`codex.py`, `linear_pipeline.py`) not just `tests/replay/`, AND **pytest FAILS**. Scope crept beyond "regression suite." | Review: did it FIX the 4 bugs (good) or break something (bad)? Fix the failing pytest. Possibly split test-suite from any production change. |

### #2901 correction (verified, important)
The issue text is STALE: `build_sources_db.py` (the real sqlite `literary_texts` writer) **already has `source_url`**
(CREATE TABLE + INSERT) on main. The actual problem = the **live `data/sources.db` is stale** (built before the
column existed → column absent). #3177's migration (ALTER + backfill from JSONL) is the correct targeted fix
(avoids a full 1.6 GB rebuild). #3177's `ingest.py`/`ingest_literary.py` edits target the **Qdrant** collection
(harmless bonus, not the sqlite concern). I initially mis-flagged a builder gap; verification corrected it.

### Original brief notes (kept for review context)
- `atlas-populate-2882` (#2882): brief told it to RE-MEASURE first (issue's "syn 5/52" is STALE — now 794+).
- `replay-suite-1905` (#1905): was meant to be LLM-free `tests/replay/` — verify it runs with NO db/network;
  scrutinize the production-code changes it made.
- `literary-srcurl-2901` (#2901): see correction above.

Monitor `bvwp5jsuh` ended (all 3 terminal).

### Review-on-land protocol (worked well this session)
1. `gh pr view <N> --json mergeable,statusCheckRollup,isDraft` — finalize PRs come as **draft**; `gh pr ready`.
2. Verify guards: no `lexicon-manifest.json` / no `.db` committed; CI no failures.
3. **Read the diff inline** (Claude review seat — never subagent). For lexicon/calque, **verify source claims
   via `mcp__sources__*`** (don't trust self-reports — see #3170 + #3167).
4. `gh pr merge <N> --squash --delete-branch --subject "<proper conventional title>"` (finalize PRs have a
   generic `chore(dispatch)` title — override it).
5. **After ANY Atlas/lexicon PR merges:** regenerate the manifest locally —
   `.venv/bin/python -m scripts.lexicon.enrich_manifest` → `verify_manifest` → commit
   `site/src/data/lexicon-manifest.json`. (Needs local `data/vesum.db` 967 MB; CI can't.)

## Queue / next wave (fire as lanes free)
- **#3150** (Atlas auto-freshness `make atlas` + DB-free CI freshness gate) — HOLD until #2882 lands (shared
  lexicon pipeline). Confirmed needed: no `make atlas` target exists; I regenerated the manifest by hand.
- **#2732 proper fix** — isolate marker-pdf + resolver-lock. Needs a decision (blast radius). Don't auto-fire.
- **#1908** layered-harness audit, **#3079** seminar self-converge (EPIC, needs design), **#3162** primary-text
  routing (folk-adjacent — coordinate with folk orchestrator).
- Consider filing: §6 calque note should also surface on the *replacement* word's Atlas page (else dormant).

## Key learnings
- **Parallelism discipline:** across-subsystem parallel, within-shared-file serial. Atlas dispatches =
  code-only/no-manifest-commit so they don't conflict on the generated manifest.
- **agy is unreliable for fiddly multi-step resolution** (deps) — it stalls narrating "I will wait...". Fine
  for bounded deterministic work; route hard-resolution to codex.
- **Verify dispatch self-reports** (#M-8) — both #3167 (agy garbage) and #3170 (grok citations) needed
  independent verification; one failed, one passed. Always check.
- **Render/visibility honesty (#M-11):** §6 code merged green but is near-invisible live (lemma-set gap). Don't
  celebrate ship without checking the artifact actually shows the change.
