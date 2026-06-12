# Claude session handoff — 2026-06-12 (Atlas finalize + kaikki IPA/etym + GoatCounter fix + reviewer-seat policy)

> Router: `current.md` → `current.claude.md` → this. Long standalone orchestrator session.
> Everything below is **merged + deployed + live-verified** unless marked otherwise.

## ✅ Shipped this session (5 PRs, all merged + on live)
1. **#3037 — Atlas full-vocab + decolonization conformance.** Salvaged + fixed a **dead codex dispatch**
   (`atlas-finalize-all`, stalled in a wait-loop, never committed). Manifest 138→**2,156 lemmas** (§1 lemma
   hygiene: dropped 13 non-lemma entries), §2 Грінченко UA→RU removal, §3 entry-scoped soviet caveat, §4
   heritage classifier **strict Grinchenko/ESUM** (user decision). **Live-verified** (автобус = "Сучасна норма",
   no false badge, 0 Russian).
2. **#3038 — kaikki fillability assessment.** Script + report. kaikki (English Wiktionary via wiktextract,
   CC BY-SA 3.0) = **88% net-add IPA**, ~39% etymology, ~11% examples. English-mediated → does NOT solve the
   authentic-UA-synonym gap (#2985 #5 still blocked).
3. **#3039 — reviewer-seat economics policy.** Claude review seat = **in-session inline**, never
   `claude -p`/`--agent claude`/Agent-subagent (50–150× reload cost); defer to next session if heavy.
   Encoded in `rules/model-assignment.md`, `agents/curriculum-orchestrator.md`, `skills/batch-review`, + auto-memory #M0.
4. **#3040 — GoatCounter fix + Plausible removal.** GoatCounter was **inert in production** (env-gated on
   `PUBLIC_GOATCOUNTER_CODE`, never set in the Pages deploy → null script). Fixed via the KubeDojo pattern:
   **hardcoded** site code (`learn-ukrainian.goatcounter.com`), **self-hosted** loader (`public/count.js`),
   **injected from `astro.config.mjs`** (injectScript → every page). Removed third-party Plausible (user: GoatCounter
   only). **Live-verified**: snippet in the page JS bundle, `/count.js` 200, Plausible gone.
5. **#3041 — kaikki IPA + etymology wiring.** `build_kaikki_lookup.py` preprocesses the 252 MB extract → 7 MB
   `data/lexicon/kaikki_uk_lookup.json`; `enrich_manifest.py` adds `pronunciation.ipa` (**1604/2190 entries**) +
   etymology gap-fill (final fallback, existing Goroh/ESUM NOT overwritten); §8 gate + CC BY-SA attribution.
   **Live-verified**: IPA `[ɐu̯ˈtɔbʊs]` + attribution render on `/lexicon/автобус`.

## 🔁 RECURRING LESSON — codex stalls at the FINALIZE step (3× today)
`atlas-finalize-all`, `atlas-heritage-fix`, `kaikki-ipa-etym-wiring` ALL completed the real work (gates green)
then **hung in a `write_stdin` empty-poll loop at the pre-submit/commit step** and never committed/pushed/PR'd.
The delegate tracker kept showing `running` (zombie); the **non-zero `--silence-timeout` (2700s) caught all
three** (prior `atlas-finalize-all` had `silence-timeout=0` and ran unbounded ~75 min).
**Playbook (finalize-the-zombie):** when a codex dispatch reads `running` but its pid is dead / session is at
pre-submit: (1) verify the worktree work is there + uncommitted; (2) re-run the gates yourself (#M-11, don't
trust the session claim); (3) **check `git diff` for OUT-OF-SCOPE files** — codex over-reaches on pre-submit
checklist items (today it did a `sys.executable→.venv/bin/python` cleanup on 5 unrelated test files; I stripped
them); (4) commit (X-Agent: codex) + push + PR yourself. Detail: `docs/bug-autopsies/codex-dispatch-stall.md`.
**Always set a non-zero `--silence-timeout` on long codex dispatches.**

## ⚠️ Watch-outs
- **GitHub Pages auto-deploy is DISABLED.** After any `starlight/` merge: `gh workflow run deploy-pages.yml --ref main`,
  watch, verify the **LIVE** site. GoatCounter is runtime-injected (in the JS bundle, NOT raw HTML) — grep the
  `/_astro/page.*.js` bundle, not the page HTML.
- **Heritage badges = 0 at A1–A2** under strict Grinchenko/ESUM — this is **correct-but-empty** (basic vocab has
  no Grinchenko/ESUM heritage markers). Classifier proven functional (опришок→historism, глагол→archaism); it
  populates at B1+/seminar levels. Not a bug.
- `data/lexicon/kaikki_uk_lookup.json` (7 MB) is committed; rebuild: `.venv/bin/python scripts/lexicon/build_kaikki_lookup.py`
  (needs `~/.cache/learn-ukrainian-kaikki/kaikki-uk.jsonl`, the 252 MB extract).

## ⏭️ Open follow-ups (none blocking)
- EPIC #2985 remaining: #6 Антоненко (cheap add) → #4 relevance layer → #5 synonyms (needs a real UA synonym
  source — kaikki does NOT solve it) → Wikipedia.
- Optional hygiene PR: the `sys.executable→.venv/bin/python` cleanup codex did on 5 test files (stripped from #3041).
- Optional: browser-confirm a GoatCounter pageview beacon actually fires (all pieces verified present).
