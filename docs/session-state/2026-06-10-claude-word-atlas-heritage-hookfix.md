# Claude session handoff — 2026-06-10 (Word Atlas dual-mode + heritage engine + context-monitor fix)

> Router: `docs/session-state/current.md` → this is the latest detailed Claude handoff.
> Long, dense session. Read this top-to-bottom before acting.

## ⚡ TL;DR — where things stand
The Word Atlas got its **dual-mode design foundation + pages + clean synonyms + the shared heritage
engine** all merged. The **folk lane is now UNBLOCKED** (heritage engine on main). A misfiring
context-monitor hook was fixed. Two dispatches are mid-flight / freshly-landed and need review.

## ✅ MERGED to main this session
| PR | What |
|---|---|
| **#2900** | A1 activity dark-mode contrast fix (all activity types) + **header light/dark theme toggle** (sun/moon; the site had no theme control before) |
| **#2906** | Sense-correct Word Atlas synonyms (supersedes polluted #2895: `кава→∅` not `кава→Java`) |
| **#2907** | Heritage Attestation Engine **spec** (shared Atlas-render + VESUM-gate classifier) |
| **#2908** | **Dual-mode token authority** (`docs/best-practices/dual-mode-design-tokens.md` + `--lu-*` tokens in `custom.css`, light+dark) + Word Atlas POC both-theme; filter button fixed (`Фільтр` 11.91:1); section-identity pairs for 6 tracks |
| **#2912** | **Heritage classifier** `scripts/lexicon/heritage_classifier.py` (`classify_lemma` + `classify_surface_form`) — **folk's dependency, now landed** |
| **#2916** | Word Atlas **pages** on tokens — landing + detail + **3rd view** (`pages/lexicon/index/index.astro`) + Ukrainian UI + filter fix + activities→`--lu-state-*` tokens |
| **#2923** | **Fixed the context-monitor hook** — it estimated tokens from raw transcript bytes/7, inflated 2-3× by base64 screenshots, firing false "auto-compact EMERGENCY" every turn. Now strips base64 first. (May still be an open PR if CI not yet merged — check.) |

## 🟢 FOLK LANE UNBLOCKED
Posted to **#2882**: folk wires `classify_surface_form()` into `linear_pipeline.py::_vesum_gate` — allow
`authentic-archaism/dialect/historism/borrowing/standard` when `is_russianism=false`, keep blocking
russianisms. #2899 allowlist → thin override. Confirm the folk agent resumed kalendarna → 01 → dumy.
**Heritage tests skip on CI** (size-gated: the real `sources.db` is 1.68 GB, CI has only a stub; engine
verified locally 5/5). Follow-up **#2928** tracks adding a fixture for real CI coverage.

## 🔄 OPEN / IN-FLIGHT — next session MUST handle
1. **`landings-unify` dispatch (Codex, RUNNING at handoff)** → branch `codex/landings-unify`, PR pending.
   Migrates all track landings (A1/folk/…) onto the **A2/`LevelLanding` pattern** + adds a conformance
   test. **Root cause found:** A2's `index.mdx` renders via `LevelLanding` (contained hero card + module
   list); A1/folk were left on an OLD two-card layout though they import it. **A2 is the reference.**
   Monitor `/api/delegate/active`; review both-mode per-track screenshots; merge when green.
2. **PR #2925 (POC split) — DONE, needs review+trim before merge.** Split `poc-word-atlas-design.html`
   into `landing.html`/`detail.html`/`heritage-defense.html` (3rd view = decolonization layer) + `word-atlas.css`
   + README design→route map. **SCOPE CREEP to strip:** it also created new arch docs
   (`ui-template-matrix.md`, `ui-template-state-spec.md`) and **edited two `session-state/` handoff files**
   (out of scope — revert those). Review, trim, then merge.
3. **PR #2923 (context-monitor fix)** — merge when CI green (low-risk; live `.claude/hooks` already updated).

## 📌 USER DIRECTIVE for next session
**Split ALL POC files into one-design-per-HTML, not just the Atlas** (user, 2026-06-10). Apply #2925's
pattern (per-view HTML + `*.css` + README design→route map) to `poc-lesson-design.html`,
`poc-folk-lesson-design.html`, `poc-lit-lesson-design.html`, `poc-site-design.html`. NOTE: my earlier
`grep` showed those as single-view (0 view-markers) — reconcile (the user may want each page-type design
isolated regardless, or those files do contain multiple sections worth isolating). Treat the user's
directive as authoritative.

## 🗺 Word Atlas — remaining to "fully complete" (roadmap)
- **A:** render heritage **"Походження + статус" badges** in `[lemma].astro` from `classify_lemma()`
  (authentic/archaism/historism/dialect/русизм). Engine is on main; just needs the render wiring.
- **B (deterministic):** Etymology → **Горох + Wiktionary** (+ tear down the 36K-page OCR ЕСУМ surface);
  Idioms (frazeolohichnyi + relevance filter); register/temporal badges from SUM ремарки
  (`заст.`→archaism, `іст.`→historism, `діал.`→dialect, `розм.` etc. — verified populatable).
- **C (curated):** Літературні/Підручники/Wikipedia attestations — FTS + LLM-ranked 1-2 cited quotes/word.
  Depends on **#2901** (literary `source_url` fix).
- **D (partial-by-design):** Стилістичні нотатки (Антоненко where it covers) + Зовнішні матеріали
  (editorial). Antonyms omitted (no clean source). **Never fabricate.**
- **E (polish):** all POCs dual-mode; broaden beyond the 63 A1 lemmas; **deploy live**.

## 🧠 Key context / gotchas
- **Dual-mode token authority is the SSOT** (`docs/best-practices/dual-mode-design-tokens.md`): every
  color role has light+dark; components consume `--lu-*`, never hardcode; yellow-on-accent text is dark
  in BOTH modes (the filter-button rule); POCs must be dual-mode.
- **Context-monitor hook is now honest** (#2923). The "EMERGENCY auto-compact" messages earlier this
  session were FALSE (real context was ~38% while it screamed 116%). The Codex `thread_handoff.py`
  bootstrap flow is **NOT** Claude's mechanism — Claude handoff = this session-state doc.
- **Lexicon `/lexicon/` is its own design** (Word Atlas POC), NOT the `LevelLanding` track-landing pattern.
- **Deploy is manual:** `gh workflow run deploy-pages.yml --ref main`. Nothing this session is deployed live yet.
- **Worktree cruft:** several `.worktrees/dispatch/*` accumulated — run `scripts/orchestration/reap_worktrees.py --dry-run|--apply`.

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git merge --ff-only origin/main
curl -s http://localhost:8765/api/delegate/active        # landings-unify done?
gh pr list --state open --json number,title,headRefName  # #2925, #2923, landings PR
# Word Atlas live: rm -rf starlight/node_modules/.vite && ./services.sh restart astro ; open /lexicon/ /a1/ /a2/
```
