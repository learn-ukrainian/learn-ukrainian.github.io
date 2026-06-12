# Claude session handoff — 2026-06-13 (Atlas §11 Translation shipped + live · 4 security alerts · v2 decouple killed on cost)

> Router: `current.md` → `current.claude.md` → this. Long standalone orchestrator session.
> Everything below is merged + deployed + live-verified unless marked otherwise.

## ✅ Shipped this session
1. **Word Atlas §11 «Переклад» (Translation) — #3052, merged + deployed + LIVE.** Filled one of the two
   entirely-missing page-contract sections. dmklinger UK→EN, **67% coverage (1467/2190)**. Load-bearing
   fix: dmklinger stores *stressed* headwords (`робо́та`) while lemmas are unstressed → a stress-stripped
   index took it from 7% to 67%. §8 provenance gate extended (`translation` ∈ `SOURCE_REQUIRED_SECTIONS`).
   Live-verified: `learn-ukrainian.github.io/lexicon/робота/` renders «Переклад» = "work (labour,
   employment, occupation, job)". Deploy run 27440086542.
2. **4 Dependabot security alerts resolved.** zeroconf #129/#130 (CVE-2026-48045) → fixed via #3046
   (`0.149.7→0.149.12` lock + requirements.txt floor); torch #125/#126 (CVE-2025-3000, low) → dismissed
   `not_used` (no patched torch exists — vuln range `<=2.12.0`, `first_patched: None` — and `torch.jit.script`
   is never called). Dependabot #2987 closed as superseded.
3. **Deploy-drift root fix — #3044 + autopsy.** 6 stray `a2-*` scratch files in the `.agent/` deploy-target
   root were tripping the orphan-guard, silently aborting EVERY `agents:deploy` → `.claude/.codex/.agent`
   were stale (the #3039 policy + 197 files never deployed). Cleared + resynced. New autopsy:
   `deploy-orphan-guard-silent-abort.md`. Also fixed the postmortem-hygiene SessionStart flag.
4. **PR triage:** folk dossier #3032 merged; junk #3028 closed (only a machine `node_modules` symlink);
   dependabot pypdf #3048 merged. b1 PRs (#3031/#3035/#3049) left to codex per user.
5. **#2985 updated** with a measured conformance table + a correction: §6 Антоненко is NOT a cheap add
   (`style_guide` is topic-keyed, not lemma-keyed → 0/2190 lemma hits); reclassified under the relevance
   layer (#4). Hub-search "item 1" confirmed already fixed.

## 🗑️ v2 decouple — built, de-risked, then KILLED on cost (user call 2026-06-13)
Explored decoupling the Atlas lemma source from built curriculum (PULS CEFR B1, +1877 lemmas → 4061 total;
`build_data_manifest.py` change worked, thin build + conformance green). Spike proved the moat fires at
scale via **sovietization** (701/3565 = 19.7% of B1+ words carry a Soviet-framed СУМ-11 def), NOT the rare
русизм classifier (1.6%). BUT the full enrich is a ~2-hour, ~13K live-slovnyk-fetch batch. **User killed it:**
codex is building B1, and the Atlas's ORIGINAL sourcing already harvests every built module's
`vocabulary.yaml` — so B1 vocab lands in the Atlas *for free* as modules ship, *with* real course-links
(which the PULS decouple couldn't provide). Worktree/branch/regen all torn down. Decouple code is in this
session's transcript if ever revived (e.g. if B1 stalls). **Lesson: don't pay for "vocab before the lesson
exists" when the lessons are being built anyway.**

## 🧭 Roles confirmed
- **codex owns B1 builds.** Do not fire B1 V7 builds; awareness-review their PRs only, merge when asked.
- Claude (me) = orchestrator + reviewer + the Atlas/lexicon tooling lane.

## ⏭️ Next for me (priority order)
1. **Vocab→Atlas link (the next clean Atlas piece).** Design §7/§13: lesson Tab 2 VocabCard gains a
   "more →" link to `/lexicon/{lemma}`. Render-time (derive slug from lemma + manifest lookup — do NOT
   edit `vocabulary.yaml`), **integrity-gated** (only link lemmas that have an Atlas page; stress-strip/
   lemma-key match). Completes the bidirectional funnel (we built Atlas→lesson `course_usage`; this is the
   return). Gets better as codex's B1 builds grow the Atlas. Touches the VocabCard component + MDX generator.
2. **#2985 Atlas backlog (no v2):** §6 + §12 are now scale-gated and fill *naturally* as B1 ships; §7
   synonyms still blocked on a clean UA source (#1657); §4 relevance layer would unblock §6/§9 quality.
3. **Standing orchestrator hygiene:** PR sweeps, security-alert watch, deploy verification after any
   `starlight/` merge (Pages auto-deploy is DISABLED — `gh workflow run deploy-pages.yml --ref main`).

## ⚠️ Watch-outs
- **GitHub Pages auto-deploy is DISABLED** — deploy manually after any `starlight/` merge, verify the LIVE
  site (not localhost). GoatCounter is runtime-injected into the JS bundle.
- Atlas enrich (`enrich_manifest.py`) does **live throttled slovnyk.me fetches** on cache miss — a full
  rebuild over uncached lemmas is hours. Cache lives at `data/lexicon/slovnyk_cache`.
- main checkout carries folk-lane untracked `wiki/` files + occasional `.codex/` deploy-sync drift — push
  docs via a clean worktree off origin/main (this handoff did).
