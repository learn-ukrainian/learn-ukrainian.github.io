# Claude session handoff — 2026-06-11 (Word Atlas: design conformance + paradigm table + §8 gates; PR sweep; hygiene)

> Router: `docs/session-state/current.md` → `current.claude.md` → this is the latest detailed Claude handoff.
> Long autonomous session. Main orchestrator (standalone). Continues the Word Atlas line.

## ⏳ RESUME HERE — continue Word Atlas backlog (EPIC #2985), easiest-first
User direction: "continue with atlas." Next item is **#2985 item 3 — derivational-base etymology**
(filed as **#2971**). Plan: reduce the ~10 derived A1 lemmas to their etymological base, then look the
BASE up via the existing `_etymology()` precedence (Goroh → ЕСУМ → Wiktionary) in
`scripts/lexicon/enrich_manifest.py`, labeling results "за основою «X»".
- Bases present in ЕСУМ (≈7 will resolve): `чудово`→чудо, `пізно`→пізній, `сьома`→сім, `робота`→робити,
  `збиратися`→брати, `одягатися`→одяг, `повертатися`→вертати.
- Bases ЕСУМ lacks (≈3 stay blank — do NOT fabricate): `добре`→добрий, `нормально`→норма, `вмиватися`→мити.
- Reduction types needed (adverb→adj, reflexive→transitive→root, ordinal→cardinal, deverbal-noun→verb)
  are NOT covered by the existing `scripts/lexicon/derivational_morphology.py` (#2956 = only denominal/
  deverbal ADJ + secondary imperfectives) → needs new rules (pymorphy3 lemmatize + a reduction table).
- Dispatch to Codex; the new §8 gates (#2988) + paradigm tables (#2981) will validate the result.
After #3: reassess #7 (scale to A1+A2+B1 vocab) — the highest-leverage item; makes the decolonization
moat visible on real data. The 4 noisy corpus sections (#2985 item 4) need a relevance layer first.

## ✅ MERGED to main this session (7 PRs)
| PR | What |
|---|---|
| #2854 | folk `ukrlib /narod/` scraper — **salvaged** from a stale 128-behind PR (cherry-picked scraper, dropped obsolete Session-5 doc) |
| #2969 | **v7_build primary-checkout commit guard** (#2884 CLOSED) — refuse persist/build when git-toplevel == primary checkout; scoped `git add` (no more `-A`); +bonus `GIT_*` env sanitization |
| #2970 | Wiktionary etymology fallback (Goroh→ЕСУМ→Wiktionary) **+ quality gate** (rejects garbled/ramble rows; net +1 clean: `комп'ютер`) |
| #2980 | Word Atlas conformance fixes: omit empty sections (gate §8), POS `numeral`→числівник, provenance no longer leaks course-context, callout stub-only |
| #2981 | **Morphology paradigm table** — noun case×number + verb conjugation tables (PoC §4 #4); flat-grid fallback for unslottable POS |
| #2986 | **Hub search full corpus** (#2985 item 1) — was searching only 12 featured cards; now routes to А-Я index `?q=` |
| #2988 | **§8 deterministic conformance gates** (#2985 item 2) — validator + pytest enforces design quality floors on every PR (lemma_in_vesum, provenance, omit-empty, heritage-evidence, sovietization, cross-link, wiki-attribution) |

Issues: **filed #2971** (derivational etymology), **#2985** (Atlas remaining-work EPIC). **Closed #2884**.

## 🗺 Word Atlas state vs design (`docs/best-practices/word-atlas-design.md`)
Works end-to-end (hub `/lexicon/` + А-Я index `/lexicon/index/` + detail `/lexicon/{lemma}` — browser-verified,
no console errors). §4 contract conformant for: header, Значення, Етимологія (41/52 single-word),
**Морфологія paradigm table**, Походження/decolonization (synthetic-verified — all 63 A1 lemmas are
`standard`/`unknown`, so русизм/soviet badges don't fire on real data yet), course usage, provenance,
EN translation (header gloss). Conformance now **enforced in CI** (#2988).
**Still missing (EPIC #2985):** #3 derivational etymology · #4 corpus sections (idioms/literary/textbooks/
external — need relevance layer) · #5 synonyms (BLOCKED on #1657 WordNet audit — English leakage+antonyms) ·
#6 Стилістичні/Wikipedia (0/52 for basic A1 — defer to scale) · #7 scale to v2.

## 🧠 Key context / gotchas
- **#M-11 hit THREE times this session — always verify the ARTIFACT, not just green gates.** Wiktionary
  stripper emitted garbage behind passing tests (caught by reading the table); empty placeholder sections
  passed but violated the design (caught by rendering); WordNet synonyms are noisy (caught by probing).
- **CI lacks `data/vesum.db`** (967MB, gitignored). Any test/validator using it must degrade gracefully
  (see #2988 fix: `vesum=None` skips ONLY lemma_in_vesum; other gates still enforce). Bit us once.
- **`Secret Scanning (gitleaks)` flakes on ghcr.io 502** (TruffleHog image pull) — NOT a real leak;
  `gh run rerun <id> --failed` after the run settles. Only required check = `Test (pytest)`.
- **Other active lanes — DO NOT TOUCH:** A2 beta (`codex/2888-a2-*`, #2888), folk (`codex/folk-*`,
  `build/folk/*` forensic branches per #M-10), b1 pilot (`codex/b1-v72-*`). Their worktrees/dispatches are theirs.
- **`start-claude.sh` is locally modified** (npx→native-binary launcher) — pre-existing, NOT mine, leave it.
  Causes a harmless "Please commit or stash" warning on rebase; pushes still succeed.
- Codex opens PRs as **draft** sometimes → `gh pr ready N` before merge.
- Dev server runs from main checkout on :4321. To browser-verify a branch's render: overlay the
  branch's render files onto the main checkout (HMR), verify, then `git restore --source=HEAD` them.

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git merge --ff-only origin/main
curl -s --max-time 2 http://localhost:8765/api/orient | python3 -m json.tool | head
gh issue view 2985   # the Atlas backlog EPIC — next is item 3 (#2971 derivational etymology)
# dispatch #3 to codex (model on the conformance-gates / paradigm dispatch briefs in docs/dispatch-briefs/)
```
