# Claude session handoff — 2026-06-15 (Atlas completion push + #1908 enforcement hooks)

> **ROLE:** main orchestrator (infra/tooling/integration/merge). Atlas completion is the
> active user priority. User was (rightly) frustrated this session — wants RESULTS on Atlas,
> blunt reporting (NEED / HAVE / BLOCKING lists), and the fleet used (dispatch + verify, not
> hand-coding). Deliver, don't theorize.

## State (main @ baba4608bc, tree clean, core.bare=false)
- **Live enforcement hooks (#1908):** `guard-admin-merge.py` (#M-0.5) ✓ + `guard-push-pytest.py`
  (#M-7) + `stamp-pytest.sh` ✓ — registered in `agents_extensions/shared/settings.json`,
  deployed to `.claude/`. **`guard-secret-print.py` (#M-5) is DEACTIVATED** (0 registrations) —
  shipped with a false-positive (flagged `cat guard-secret-print.py` / `| tail -3` + the word
  "secret"). FIX is **PR #3240** (codex, done, awaiting my verify+merge).
- **0 active dispatches.**

## ⏭️ RESUME HERE — in-flight, precise next steps
1. **PR #3240** — `[codex] tighten #M-5 secret-guard file-matching`. **Verify before merge**
   (smoke-test the DEPLOYED hook, the lesson below): create review worktree → confirm it ALLOWS
   `cat agents_extensions/shared/hooks/guard-secret-print.py`, `… | tail -3`, `head -20 x.py`,
   commit-body-mentioning-"secret-print"; AND still BLOCKS real credential-file reads, dotenv reads,
   bare env-dumps, and secret-var echoes. Only then: merge → re-register `guard-secret-print.py`
   in `settings.json` PreToolUse[Bash] (timeout 5) → `bash scripts/deploy_prompts.sh` → live-smoke.
2. **kaikki translation fill** — branch `claude/atlas-kaikki-translation-2882` (WIP committed).
   Helpers `extract_glosses`/`_is_translation_gloss` are in `build_kaikki_lookup.py` but NOT wired.
   FINISH: (a) call `extract_glosses` in `build_lookup` loop, store `row["glosses"]`, add to the
   keep-condition + final lookup dict; (b) rebuild `data/lexicon/kaikki_uk_lookup.json` (runs off
   `~/.cache/learn-ukrainian-kaikki/kaikki-uk.jsonl`, 252MB, present); (c) add a kaikki-gloss
   fallback in `enrich_manifest._translation` AFTER dmklinger (and cache `_load_kaikki_lookup` —
   it currently re-reads the 7MB file every call); (d) **verify output on real gap words**
   (бандероль→wrapper clean; meta-glosses excluded); (e) `make atlas` regen + verify_manifest + PR.
   → fills **315/548 (57%)** of the translation gap, clean, from Wiktionary (CC-BY-SA, no license issue).
3. **Dedup-to-lemma** (USER-APPROVED, not started) — ~233 of the 548 "gap" words are inflected
   forms (`брата`=gen-of-брат) / misspellings (`агенство`) that shouldn't be standalone Atlas pages.
   In `build_data_manifest.py`: for each candidate, VESUM→lemma; if word≠lemma and not independently
   a headword, **alias it to the lemma's page** (don't create a separate entry); drop misspellings
   (kaikki "misspelling of X" / absent-from-VESUM). Deterministic. **Biggest lever** — shrinks the gap.

## Atlas completion — the verified plan (docs/atlas-data-coverage-strategy.md is the SSOT)
2,667 entries / 150 modules. Per-field, where data comes from + can it hit 100%:
| Field | Now (core) | Source | 100%? |
|---|---|---|---|
| English translation | 75% | **Wiktionary/kaikki glosses (local, unused — item 2)** | ~100% for real words |
| Ukrainian definition (meaning) | 81% | local СУМ-11 + slovnyk.me СУМ-20 (attributed — see license note) | ~100% |
| Stress + IPA | 88% | VESUM stress + kaikki IPA | ~100% single words |
| Grammar forms | 83% | VESUM | ~100% single words |
| Etymology | 66% | ЕСУМ + kaikki | **NO — many words have no recorded etymology; ~80% max** |
| CEFR level | 57% | see CEFR research below | **NO without estimate — only PULS 5.9K has official levels** |

**License correction (I was wrong):** I over-treated slovnyk.me's #1667 "no-bulk-cache" note as a
hard wall. It is a cautious anti-scraping posture, NOT a copyright bar. For this non-commercial,
attributed, educational project, СУМ-20 with attribution is the **user's call and a fine one** — use it.
kaikki (the main fill) is CC-BY-SA — fully open. **No real license blocker stands.**

**What slovnyk.me CANNOT give** (verified): English translation (its bilingual is EN→UK, wrong way),
etymology, CEFR, IPA. Everything else (meaning, synonyms, idioms, stress, spelling, Russianism
warnings, regional/archaic) it DOES give. So only translation+IPA+etymology need Wiktionary; only
CEFR needs a separate source.

## CEFR — research done (the one genuine data gap)
- **State Standard 2024 «Українська мова як іноземна. Рівні А1–С2»** (Нац. комісія зі стандартів
  держ. мови, рішення №279, 29.08.2024, mova.gov.ua) — **IS the CEFR framework (A1–C2)**, but likely
  has **level descriptors, not a per-word list** (a corpus paper says it lacks vocabulary specs).
  **TODO: fetch the actual standard .docx** (WebFetch timed out — retry / use claude-in-chrome):
  `https://mova.gov.ua/storage/app/sites/19/uploaded-files/34202434-1standartderzhavnoimoviproektukrainskamovayakinozemnarivnizagalnogovolodinnyaa1-s2.docx`
  — check if it contains a lexical minimum per level.
- **Per-word CEFR data sources:** (1) **Synchak et al., "Corpus-Based Vocabulary Profiling for
  Ukrainian", eLex 2025** (`https://elex.link/elex2025/wp-content/uploads/eLex2025-29-Synchak_etal.pdf`)
  — data-driven A1–C2 profile, THE most promising; **fetch it, check for a downloadable dataset.**
  (2) Published lexical minimums (Turkevych & Borodin «1000 і 1 слово» A1 + per-level series).
  (3) LoadWords (loadwords.com/uk/a1) interactive lists. Our current PULS 5.9K is likely one of these.
- **Decision pending (user):** estimate CEFR from corpus frequency (GRAC) + label "estimated" for the
  long tail, OR leave blank past the official list. Do NOT fabricate exact levels.

## Other open infra
- **#2842 core.bare flip** recurred this session (worktree/dispatch git-op pollutes shared .git/config;
  broke all git mid-session; fixed with `git config core.bare false`). Canary `scripts/audit/check_core_bare.py
  --fix` EXISTS but is NOT wired into a hook → **proper fix = wire it into a PreToolUse(Bash)/session hook
  to auto-heal.** Next #1908-family hook. Recheck `core.bare=false` after worktree churn.
- **#2882** (Atlas populate) is the umbrella issue; **#2732** marker-pdf isolation (needs decision).

## Shipped to main this session
Dependabot 9/9; #3195 (freshness rescope), #3206 (#3197 antonym filter), #3210 (§8 gate root-fix),
#3213 (antonym cleanup LIVE + vocab refresh), #3218 (#3211 §8 heritage fallback), #3224+#3226
(#M-0.5 admin-guard live), #3232 (#M-7 pytest-push live), #3233 (#M-5 — merged then deactivated).
**CLOSED (verified garbage, not merged):** #3229 (reverse-Балла translation), #3231 (ЕСУМ suffix-strip etymology).

## HARD LESSON (cost real time this session — internalize)
**VERIFY THE OUTPUT ON REAL DATA before merging/deploying — passing unit tests ≠ correct.** This caught
THREE broken deliverables this session: 2 garbage Atlas fills (вода→bail, річка→"thing") and 1
false-positive secret-hook — none caught by the dispatched agents' own green tests. For Atlas fills:
print the actual rows. For hooks: smoke-test the DEPLOYED artifact, not just unit tests. The cheap
heuristic fills (inversion, suffix-strip) DO NOT WORK — use direct per-lemma sources (kaikki/slovnyk).

Prior handoff (superseded): `current.claude.md` was last the dependabot/Atlas-correctness one.
