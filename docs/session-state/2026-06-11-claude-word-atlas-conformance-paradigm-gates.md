# Claude session handoff — 2026-06-11 (Word Atlas: conformance + paradigm + §8 gates; DEPLOY FIX; UA-dict source research)

> Router: `docs/session-state/current.md` → `current.claude.md` → this is the latest detailed Claude handoff.
> Long autonomous session. Main orchestrator (standalone). Word Atlas line.

## 🚨 CRITICAL LESSON — GitHub Pages auto-deploy is DISABLED
`.github/workflows/deploy-pages.yml` is `workflow_dispatch`-only ("Auto-deploy disabled — push to main
no longer triggers deploy"). **Merging to main does NOT update the live site.** This burned us: all
Atlas work (#2980/#2981/#2986/#2988) merged 06-11 but the live site was frozen at the 06-10 20:28 deploy,
so the user correctly saw "the Word Atlas is not following the design" — my fixes weren't deployed. I had
only verified localhost, never the live site. **ALWAYS, after merging user-facing (starlight/) changes:
`gh workflow run deploy-pages.yml --ref main`, watch it, and verify the LIVE site (learn-ukrainian.github.io),
not just localhost.** Deploy triggered this session (run 27368018028 from `4fd56b705`).

## ⏳ RESUME HERE (in order)
1. **Verify the deploy landed** (run 27368018028) and the LIVE Atlas now shows the paradigm table +
   conformance fixes + full-corpus search. `gh run list --workflow=deploy-pages.yml --limit 2`.
2. **Synthesize the UA-dictionary source research** (IN FLIGHT — 3 agents). User directive: source
   AUTHENTIC Ukrainian dictionaries (synonyms/antonyms/idioms), **NO Russian content, NO English-auto-
   translated** (current `ukrajinet` WordNet is auto-translated → antonyms/wrong-sense, unusable). Asks:
   `ua-dict-research-{codex,agy,hermes}` (bridge). Brief: `docs/dispatch-briefs/2026-06-11-ua-lexicon-source-research.md`.
   Collect their answers (`ab inbox`/task logs), dedup, produce a ranked sourcing table on #2985, name the
   best path to a clean UA synonym dataset. Seed names to verify: Караванський; Бурячок «Словник синонімів
   української мови» 2т (Інститут укр. мови НАН); Полюга антоніми; СФУМ idioms.
3. Then continue backlog (EPIC #2985), per the research-reprioritized order below.

## ✅ MERGED this session (7 PRs) + issues
#2854 (folk scraper salvage) · #2969 (v7_build primary-checkout guard → **#2884 closed**) · #2970 (Wiktionary
etymology + quality gate) · #2980 (Atlas conformance: omit-empty, POS, provenance) · #2981 (**paradigm table**) ·
#2986 (**hub search full corpus**) · #2988 (**§8 conformance gates** enforced in CI). Filed #2971 (derivational
etymology), **#2985 (Atlas backlog EPIC)**. Git/GitHub hygiene done.

## 🔬 Research: blocked-parts feasibility (full detail = #2985 comment 2026-06-11)
- **#5 Synonyms**: GENUINELY blocked — WordNet noisy even strict-filtered (antonyms/wrong-sense/synset
  pollution); no alt table in sources.db → needs #1657 cleanup OR a real UA synonym source (the research above).
- **#4 Corpus sections** (idioms/literary/textbooks): need a relevance/selection layer (idioms keyed by
  phrase → exact-lemma = 0; FTS noisy).
- **#6 Стилістичні/Wikipedia**: sparse even at scale (Антоненко 0/52 A1, 0/80 A2+B1 — 342 specific headwords).
- **#7 Scale to v2 (≈4,512 PULS A1-B1 lemmas)**: HIGH value + feasible. At scale: morphology ~complete,
  **meaning (СУМ-11) 87%**, etymology 26%→~50-60%. **Moat activates: ~5.6% sovietization-flagged → ~200+
  red-warning pages** (vs 0 now). Risk: ~4.5K-page static build perf (spike S2).
- **Reprioritized:** #3 derivational etymology → **#7 scale (promote)** → #6 Антоненко cheap add →
  #4 relevance layer → #5 synonyms (after source research) → Wikipedia.

## 🧠 Gotchas
- **#M-11** (verify ARTIFACT not gates) bit 3× + the DEPLOY miss above = 4× this session. Always check the LIVE thing.
- **CI lacks `data/vesum.db`** — tests using it degrade gracefully (`vesum=None` skips lemma_in_vesum; #2988).
- **gitleaks 502 flake** = ghcr.io image pull, not a real leak → `gh run rerun <id> --failed`.
- **main checkout is locally diverged + has folk untracked files + `start-claude.sh` local mod (not mine).**
  Pushing docs from the main checkout FAILS (folk untracked files block rebase). **Push via a clean worktree
  off origin/main** (used this all session). Do NOT `reset --hard` the main checkout (would lose folk's work).
- **DO NOT TOUCH** `codex/2888-a2-*` (A2), `codex/folk-*` + `build/folk/*` (folk), `codex/b1-v72-*` (b1).
- Codex PRs sometimes open as **draft** → `gh pr ready N` before merge.
- To browser-verify a branch's render on the running dev server: overlay the branch's render files onto the
  main checkout (HMR), verify, `git restore --source=HEAD` after.

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q
gh run list --workflow=deploy-pages.yml --limit 2   # did the deploy land? live Atlas current?
gh issue view 2985                                  # Atlas backlog EPIC + research findings
# collect UA-dict research answers: ab inbox / task logs for ua-dict-research-*
```
