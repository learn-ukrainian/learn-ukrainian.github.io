# Claude session handoff — 2026-06-13 (agy gemini-retirement · Atlas cache+pair fixes · Atlas/content quality-grind queue for fleet fan-out)

> Router: `current.md` → `current.claude.md` → this. Long, dense session.
> **Next session's job (user directive): PRIORITIZE the quality-grind issues below, SOLVE them, and
> FAN OUT to as many fleet agents as possible — they're idle.** See the fan-out plan (§Fleet).

## TL;DR
- **gemini-cli retirement landed** (#3060 agy↔MCP + §7-fabrication re-verify PASS + #3061 wiki routing→agy). agy is now cleared for §7/factual content.
- **Atlas data-pipeline fixed**: #3091 (transient slovnyk cache-miss heal, schema-v2) + #3095 (pair-lemma base-form for morphology/etymology/synonyms).
- **Honest correction**: non-pair Atlas pages were ALREADY rich in the deployed manifest; #3091 was *robustness* (no visible change). The real visible gap was the **65 sparse aspect pairs** (брати/взяти…), which #3095 fixes — **deploy pending the in-flight re-enrich**.
- **Quality-grind issue queue created** (the next-session payload) + **fleet fan-out plan** below.

## ✅ Shipped (merged to main)
| PR/commit | What |
|---|---|
| #3082 (`da969703dc`) | #3060 — honest agy MCP resolution in tool_config (un-no-op, reads agy global config) |
| #3089 (`6c8f321151`) | #3061 — retire gemini-cli routing → agy (wiki DEFAULT_PRIMARY/FALLBACKS + `--writer`) |
| #3091 (`d3e24bdb3a`) | slovnyk cached-miss heal — transient≠genuine, schema-v2 migration |
| #3095 (`0e94a136d4`) | pair-lemma base-form in manifest builder (`_base_lemma`) |
| `7c028f6ebc` | CLAUDE.md top directive: always aim for + research best-practice |
| `bec3912443`,`1c1af5af23` | gitignore `.codex/` + `docs/outreach/` (untracked deploy/local) |

**§7-fabrication re-verify (the gemini→agy unblock gate): PASS** — deterministic, 4 words, agy grounds
in ЕСУМ/WordNet + abstains "NO SOURCE", 0 fabrications. MEMORY guard lifted (3 lines edited).

## 🗺️ Atlas state (truth)
- Template `site/src/pages/lexicon/[lemma].astro` implements design §1–§11 (§6 calque folds into §5). **§12 Вікі-довідка NOT built** (#3096).
- Non-pair words: rich (synonyms/etymology/morphology) — already deployed.
- Pairs (67; 65 were sparse): #3095 fixes via base-form. **Re-enrich `btg57685z` running → on completion: `git add site/src/data/lexicon-manifest.json && commit && push` (auto-deploys), then screenshot варити sparse→rich.**
- Atlas only covers **course vocabulary** (2190 lemmas) by design (e.g. `працюючий` isn't in it).

## 🎯 QUALITY-GRIND ISSUE QUEUE (prioritize + solve next session)
Mission filter: **better Atlas + better lessons.**
1. **#3098** — §6 decolonization moat: participle/calque correction layer (Antonenko/Pravopys/UA-GEC). **HIGHEST mission value.**
2. **#3092** — §7 synonym coverage: lean on Karavansky/sense-filtered slovnyk, drop WordNet junk.
3. **#2971** — Atlas etymology coverage (derived lemmas + **~704/1816 single words lack etymology** — audit WHY; see new comment).
4. **#3096** — §12 Вікі-довідка (Wikipedia/Wiktionary outbound, omit-empty).
5. **#2882** — fully populate Atlas per POC (data-source fillability).
6. **#3097** — mirror slovnyk.me locally (anti-hammering + reproducible + dataset-safe two-bucket).
7. **#3085** — search_esum tool description stale (quick docstring).
8. **#2997** — vesum_verified false-flags authentic archaic forms.
9. **#3087** — route noisy wiki reviewer dims off Gemini-family (deepseek/claude).
10. **#2156** — UA calque+grammar eval harness → start the LEAN **reviewer-calibration kernel** (fleet leaderboard on UA-GEC); helps translation+seminars+routing, little for Atlas.

## 🤖 Fleet fan-out plan (user: "use as many agents as possible")
Dispatch cap discipline: 2 codex + 2 agy + 2 claude in flight; check `/api/delegate/active`. All via `--worktree --mode danger`, no auto-merge, #M-4 evidence.
- **codex** → #3097 (mirror, robots-compliant scraper) · #2971 (etymology-miss audit/debug) · #2997 (vesum archaic).
- **agy** (now §7-cleared, unmetered) → #3085 (esum docstring) · #3096 (§12 wiki wiring) · #3098 drafting (grounded, MCP) — pair with a strong reviewer.
- **deepseek** (review lane) → review every content/pipeline PR (off-seat, use it).
- **claude (next orchestrator, inline)** → linguistic curation/verify for #3098 + #3092 (the `mcp__sources__*` judgment calls) + adversarial PR review seat + merge.
- **cursor** → a parallel content/fix lane.
Run several in parallel; the fleet has been idle.

## 📨 Open / awaiting-user
- **Лепетун (ukr-mova.in.ua)** collaboration material prepared (local gitignored file, **user-owned next step**). robots.txt permissive for content + sitemap. Read slovnyk/Лепетун `/policy` once before any pull. Use ULP-pattern (private gitignored reference, verify, re-express, never verbatim; link + attribute). Citation ≠ permission.
- Calibration kernel (#2156 lean) — fire as a parallel dispatch whenever a routing decision (#3087) needs evidence.

## ⚠️ Lessons this session
- **Don't claim a visible change without git-verifying the deployed artifact.** I said "the page changed" — but the committed manifest was already rich for non-pairs; my heal was robustness, not a visible change. The real fix was pairs (#3095).
- The "pair-string" bug recurs (slovnyk #2985, then morphology/etymology #3095) — any new per-lemma lookup must use `_base_lemma`/`_slovnyk_lookup_word`, never the raw `"X / Y"` display lemma.
- Enricher writes the manifest ONCE at the end → run as ONE background process (#M-9); deploy = commit that one file.

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git log -1 --oneline origin/main
# 1) land in-flight pair deploy if not done: re-enrich finished? commit+push site/src/data/lexicon-manifest.json
# 2) fan out the quality queue (see §Fleet) — prioritize #3098, #3092, #2971
curl -s http://localhost:8765/api/delegate/active   # cap check before dispatching
```
