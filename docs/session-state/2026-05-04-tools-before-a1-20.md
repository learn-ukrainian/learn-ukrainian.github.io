# Session Handoff — 2026-05-04 evening (tools-before-A1/20 ordering locked)

> **Predecessor:** `2026-05-04-mcp-verification-architecture-kickoff.md`
> **Successor scope:** Build tooling in tiers A→D, THEN run A1/20. Do not run A1/20 until Tier D ships.
> **Mode:** User-online session — git cleanup completed (3 PRs merged, dirty main committed in 2 coherent commits, all worktrees + stashes + stale branches purged).

---

## TL;DR — what shipped this arc

Cleanup-only session after the prior MCP architecture kickoff:

1. **PR #1670** (СУМ-11 Sovietization flag) merged.
2. **PR #1672** (ЕСУМ vol 1 PoC) merged. Conflict with #1670 resolved on rebase.
3. **PR #1671** (Antonenko broken segmenter) closed without merge — issue #1663 stays open for re-dispatch with corrected segmenter.
4. **Dirty main checkout** — committed as two coherent commits:
   - `9fe99a00a7` Propagate `safe_join` across all API routers (security-scanner hardening). Caught real bugs: orphaned `except` clause causing syntax error in `blue_router.py`, 6 routers calling `safe_join` without import causing `/api/state/summary` 500s.
   - `aee57c8271` Codex multi-agent infrastructure (AGENTS.md routing, GEMINI.md worktree policy, `start-codex.sh --enable multi_agent`, `.codex/` runtime, `.agents/` skill prompts).
5. **All 4 worktrees removed**, **5 stale local branches deleted**, **11 stashes cleared** (recoverable from reflog ~30 days), **10+ stale remote branches pruned**.

State at handoff: `main` clean, no PRs open, no worktrees, no stashes.

---

## CRITICAL — Tools-before-A1/20 execution order

User stated 2026-05-04 evening: "should we not build the tools first?" Locking that ordering as the gating sequence. **Do NOT run A1/20 until Tier D ships.** Running it earlier wastes a build cycle on a known-broken retrieval path.

### Tier A — Critical infrastructure (blocks A1/20 architecturally)

| # | What | Notes |
|---|---|---|
| #1631 | Wiki migration into `linear_pipeline.py` | Current code calls V6-era Qdrant via `scripts/rag/query.py` — this is the V7 retrieval-layer drift bug. Replace with V6 wiki reader (`_build_wiki_packet` + `compress_wiki_packet`) + MCP sources for dictionary verification. **No Qdrant in V7 architecture.** |
| #1632 | ADR-008 implementation | Per-gate bounded correction paths. Patch-bounded, full revalidation, pipeline-assisted dictionary, one attempt per gate. **Blocked on user signoff to flip ADR-008 PROPOSED → ACCEPTED.** |

### Tier B — Verification tools + prompt scaffolding V7 will use

| # | What | Effort |
|---|---|---|
| #1669 | Surface VESUM `arch` tag — modern-vs-historical discrimination | Internal data exposure only, ~1-2h |
| #1658 | Rename `search_grinchenko_1907` → `search_grinchenko_1907` | Naming bug fix — Грінченко is NOT etymology, mislabeling fed bad assumptions into prompts |
| #1660 | Flag completeness gaps in tool descriptions | Small docs change |
| #1668 | PyMorphy3 wrapper for Russian-shadow form detection | No Russian text ingested — wrapper-only design |
| **#1673** | **Chain-of-thought scaffolding in writer + reviewer prompts** | **User-flagged 2026-05-04 — CoT was supposed to be there and isn't. Writer must reason explicitly through word budget / plan-vocab / register / teaching sequence before drafting. Reviewer must list 2-3 specific evidence quotes per dim before scoring. Pilot on 3 modules before bulk.** |

### Tier C — Content-source + license unblocks

| # | What | Notes |
|---|---|---|
| (new) | Add `license_tier` column to `external_articles` + backfill per domain + wire wiki compiler to read with license-aware behavior | ULP subtitles, opentext.ku.edu/dobraforma, ULIF dictionary all sit unused in `external_articles` (403 entries). License tiers: public-domain / CC-cite / fair-use-study / paid-no-copy. Wiki writer prompt must emit citations for cite-required tier; never paraphrase study-only tier. |
| #1666 | Гринчишин/Сербенська paronyms (1986 NBU scan) | License says "use is for навчальною та науковою некомерційною метою" — non-commercial educational use OK, but bulk reproduction unclear. **License memo needed before any bulk fetch.** |
| #1667 | СУМ-20 (ULIF, 2010-ongoing) — modern definitional baseline | License terms not stated on ULIF portal. **License memo needed.** Without СУМ-20, all definitions trace to Sovietized 1970s СУМ-11. |
| #1662 | ЕСУМ vols 2-6 | Vol 1 (А-Г) shipped in PR #1672. Vols 2-6 cover the other ~90% of headwords. |

### Tier D — Prompts that use everything above

| # | What | Notes |
|---|---|---|
| #1661 | V7 prompt diff: Tier-1 verification discipline in writer + reviewer | Wires writer/reviewer to actually USE the MCP verification stack. Per prior handoff: "ready to draft against current MCP; will simplify dramatically after Phase 2 primitives land." Wait until Tiers A+B+C are mostly closed — otherwise we rewrite the prompt twice. |

### Tier E — Run A1/20

A1/20 POC step 3 currently parked at checkpoint A (user-eval). After Tier D ships, this is the meaningful run. Until Tier D, any A1/20 output is invalid because the retrieval/verification stack is broken.

**Writer choice for A1/20 (user 2026-05-04):** options are **gemini OR opus OR gpt-5.5**. Decision still open per `docs/decisions/2026-04-26-reboot-agent-responsibilities.md §3`. Default in `v6_build.py` is currently `claude-tools` (Opus) but that's V6-legacy inertia, not a reboot decision. Decide before Tier E fires.

---

## Pedagogical framing (LOCKED — do not propose alternatives)

User confirmed multiple times this session:

1. **Strategy: L1 corpus bootstrap (memory rule #0D), not direct L2 textbook ingestion.** UK-for-English-speakers textbooks exist (Anna Ohoiko / ULP, the 500-verbs book, the new A1 book) but the user has chosen not to use them as content sources because they are IP-protected AND because building from L1 native corpus is the explicit decolonization play.
2. **IP tiers user articulated:**
   - Public domain (Shevchenko, Franko, expired copyright) — use freely, no citation needed.
   - **Free with attribution** (ULP video subtitles, blogs that allow educational use with citation) — usable, MUST cite.
   - **Fair use / transformative** — short quotes for analysis OK, full reproduction not.
   - **All rights reserved** (Anna O. premium PDFs, her A1 book, her 500-verbs book) — **study only, never copy phrasing**. Notes from study live OUTSIDE the repo (`~/.claude/projects/.../memory/` or gitignored `private-notes/`).
3. **Current project posture: non-commercial, permanent, open-source educational resource.** Decision recorded 2026-04-19. CC BY-NC dependencies acceptable.
4. **Plan order (per #0D):** L1 corpus → UK wiki articles → UK A1/A2 modules → those modules become enriched source material → English-facing A1/A2 immersion modules. Step 1 partially done (1,492 wiki articles). Step 2 parked at A1/20 POC checkpoint A.

---

## Current state of `external_articles` (non-zero IP surface)

- **403 ukrainianlessons.com entries** (ULP) sit in `external_articles`. Subtitles likely; some may be transcripts.
- **opentext.ku.edu/dobraforma** entries — Kansas University open-licensed Ukrainian textbook.
- **lcorp.ulif.org.ua/dictua** entries — ULIF dictionary (public).
- **No `license_tier` column today.** All three tiers are mixed in one undifferentiated table.
- **No production consumer reads `external_articles`** today. The ingester (`scripts/wiki/build_sources_db.py`) is the only writer; nothing reads. Confirmed via grep across `scripts/build/`, `scripts/pipeline/`, `scripts/wiki/compile.py`, claude_extensions, orchestration.
- **MCP exposes `search_external`** — any agent could call it and pull unlicensed content. No production consumer does, but the surface is open.
- **The right fix (Tier C above):** add `license_tier` column, backfill per domain, wire wiki compiler to read with license-aware behavior, embed citation requirements into wiki writer prompt. **Not** un-exposing `search_external` (would waste the ingest work).

---

## Open issues snapshot (post-cleanup)

| # | Title | Tier |
|---|---|---|
| #1657 | EPIC: MCP verification-layer improvements (parent of B/C) | parent |
| #1658 | Rename search_grinchenko_1907 → search_grinchenko_1907 | B |
| #1660 | Tool descriptions: completeness gaps | B |
| #1661 | V7 prompt diffs for Tier-1 verification | D |
| #1663 | Antonenko full ingest — re-dispatch needed (segmenter broken on prior run, polluted DB rolled back) | C |
| #1664 | Karavansky ingest | C |
| #1665 | Holovashchuk ingest | C |
| #1666 | Гринчишин/Сербенська (paronyms) | C — license read first |
| #1667 | СУМ-20 (ULIF) | C — license read first |
| #1668 | PyMorphy3 Russian-shadow wrapper | B |
| #1669 | VESUM arch tag exposure | B |
| #1622 | Round-4 bakeoff | gated on Tier A |
| #1631 | Wiki migration into linear_pipeline | A |
| #1632 | ADR-008 implementation | A — gated on user signoff |
| #1604 | PhraseTable activity_type bug | not A1/20-blocking |
| #1634 | Lockfile resolver migration (pip-tools/uv/poetry) | not A1/20-blocking |

---

## Cold-start protocol for next session

```bash
# 1. Verify clean state on main
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git status -s              # expected empty
git log --oneline -5

# 2. Read this handoff. The Tier A→E ordering is LOCKED — do not propose
#    A1/20 runs until Tier D ships.

# 3. Source auth before any gh call
source ./.envrc

# 4. Decide entry point per tier:
#    - Tier A start: #1631 wiki migration (no dependencies, safe to start)
#    - Tier A blocker: ADR-008 user signoff for #1632 — surface to user
#    - Tier B parallel: #1669, #1658, #1660 inline; #1668 dispatch when codex returns
#    - Tier C: license memos for #1666/#1667 — draft and surface
#    - Tier D: #1661 — wait until A+B+C mostly closed
```

---

## Next-session priorities (ranked, user-locked)

1. **Surface ADR-008 PROPOSED → ACCEPTED** to user — 5-min decision, unblocks #1632.
2. **Start #1631 wiki migration into `linear_pipeline.py`** — no dependencies, can begin inline immediately.
3. **Tier B inline batch:** #1669 VESUM arch tag → #1658 rename Грінченко tool → #1660 completeness flags. ~3h total.
4. **License memos for #1666/#1667** — draft as 1-page summaries, user signs off in 10 min, unblocks Tier C ingestion.
5. **After codex returns 11am 2026-05-05:** dispatch #1664 Karavansky, #1665 Holovashchuk, #1668 PyMorphy3 in parallel.
6. **Last:** #1661 V7 prompt diff once Tiers A-C closed.
7. **Run A1/20** only after Tier D ships.

---

## Cross-thread notes (still active)

- **Memory rules respected this session:** #0A (push back, don't menu), #0I (don't stack micro-dilemmas), #0H (claude merges PRs, not user). User explicitly pushed back on me when I proposed un-exposing `search_external` — corrected to "wire it up with IP guards instead." Lesson: my reflex when seeing a risk is to remove the surface; user's expectation is to use what we ingested. Bias toward use-with-discipline, not removal.
- **MCP `search_external` is open today** — IP risk is theoretical (no production consumer) but surface is real. Tier C `license_tier` work closes this properly without throwing away the ingest.
- **A1/20 is parked, NOT abandoned.** Checkpoint A user-eval is the validation gate for the entire L1-corpus-bootstrap strategy. If A1/20 fails after Tier D ships, the failure mode tells us what about the strategy is broken (vs failing today which would just tell us the retrieval path is broken).
- **Anna O.'s materials are off-limits as content but ON-limits as study reference.** Notes go to `~/.claude/projects/.../memory/` or gitignored `private-notes/` — never the repo.
- **Pre-existing items still active from prior handoff:** Phase 4 round 3.5 verification done (#1621 shipped), but round-4 bakeoff (#1622) blocked on Tier A. ADR-008 PROPOSED on `f4df43af06`. Wiki rebuild fully landed (1,492 articles). Cold encode done. Pyenv-rehash 60s lock fixed.
- **Codex (delegate.py) returns 11am 2026-05-05 CET.** Codex web UI on separate counter — separate availability.

---

## Bug autopsies recorded this session

**Orphaned `except` clause in `blue_router.py:199`** (caused syntax error). The path_safety refactor accidentally deleted the `try:` and `with open(status_file) as f: data = json.load(f)` body but kept the trailing `except Exception:`. The dirty checkout had been carrying this syntax error untested. Fixed by restoring the try-body. Caught because `git status` showed it as part of the dirty state and I ran ast.parse before committing.

**6 API routers calling `safe_join` without import** (caused `/api/state/summary` to return 500: `NameError: name 'safe_join' is not defined`). The path_safety refactor was applied as a search-and-replace on call sites without verifying the import. Caught by running pytest on `test_api_endpoints.py` before commit. Fixed by adding `from ..path_safety import safe_join` to each.

Both bugs sat in dirty main for at least a day before I committed. Lesson: never let dirty checkouts persist across sessions — they accumulate untested edits.
