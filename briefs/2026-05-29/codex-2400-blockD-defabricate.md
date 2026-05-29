# Codex brief — De-fabricate #2400 Block D §7 cross-track paths (mechanical application)

## Context
PR #2400 (branch `gemini/bio-r1a-blockD-survived-2026-05-28`) adds 6 bio dossiers whose
Section 7 ("Cross-track links") cite **fabricated** `plans/...` paths that don't exist. This is
the #2400-class systemic gemini fabrication (validator tracked in #2410). The mapping below is
ALREADY VERIFIED by the orchestrator (`test -e` against `curriculum/l2-uk-en/plans/`). Your job is
PURELY MECHANICAL: apply this mapping, fix metadata, verify, push. **Do NOT discover or invent any
new path. Do NOT cite any path you have not confirmed with `test -e curriculum/l2-uk-en/<path>`.**

## Setup
You are in a fresh worktree branched from `origin/gemini/bio-r1a-blockD-survived-2026-05-28` (via
`--base`). The 6 files are under `docs/research/bio/`. After edits, push your branch and open a PR
targeting `main` that says "supersedes #2400" in the body (we close #2400 in favor of yours).

## §7 corrections (apply EXACTLY; every replacement path is test-e-verified REAL)

**maksym-rylskyi.md** — under "Existing LIT modules": replace `plans/lit/rylskyi-neoclassicists.yaml`
→ `plans/lit/rylsky-neoclassicism.yaml`; replace `plans/lit/rylskyi-znak-tereziv.yaml`
→ `plans/lit/rylsky-liryka.yaml` and ALSO add `plans/lit/rylsky-translations.yaml` (matches the
translation-work note). Under "Existing HIST": replace BOTH
`plans/hist/stalinist-terror-intelligentsia.yaml` and `plans/hist/post-war-zhdanovschyna.yaml`
→ `plans/hist/mekhanizm-teroru.yaml` and `plans/hist/rozstriliane-vidrodzennia.yaml`.

**mykola-bazhan.md** — "Existing LIT" (change "(planned, discovery state)" → keep label but real
paths): replace `plans/lit/bazhan-avant-garde.yaml` → `plans/lit/bazhan-idols.yaml` and
`plans/lit/bazhan-quiet-step.yaml`; replace `plans/lit/stalinist-odes-capitulation.yaml`
→ `plans/lit/tychyna-soviet-period.yaml` (the Tychyna-1933-turn comparison). "Existing HIST":
replace `plans/hist/great-terror-1937.yaml` → `plans/hist/mekhanizm-teroru.yaml`.

**oleksandr-kovinka.md** — "Existing LIT": `plans/lit/ostap-vyshnia.yaml` has NO real equivalent →
relabel that bullet to "None currently; Ostap Vyshnia is a research-dossier cross-reference (see
`docs/research/bio/ostap-vyshnia.md`)." "Existing HIST": replace
`plans/hist/stalinist-terror-1930s.yaml` → `plans/hist/mekhanizm-teroru.yaml`;
`plans/hist/gulag-system-kolyma.yaml` has NO real equivalent → drop the path, keep the Kolyma/Dalstroy
prose but remove the fake `.yaml` reference (describe as historical context, not a module path).

**ostap-vyshnia.md** — "Existing LIT": `plans/lit/vyshnia-usmishka.yaml` has NO real equivalent →
relabel to "Potential (Phase 2+) candidate: a module defining the *усмішка* genre (not yet planned)."
"Existing HIST": replace `plans/hist/rozstriliane-vidrodzhennia.yaml`
→ `plans/hist/rozstriliane-vidrodzennia.yaml` (spelling); replace `plans/hist/upa-resistance.yaml`
→ `plans/hist/upa.yaml`.

**yurii-yanovskyi.md** — "Existing LIT": replace `plans/lit/neoromanticism-1920s.yaml`
→ `plans/lit/vaplite-literary-avant-garde.yaml`; replace `plans/lit/yanovskyi-master-korablya.yaml`
→ `plans/lit/yanovsky-master-of-the-ship.yaml` and add `plans/lit/yanovsky-four-sabres.yaml`
(*Вершники*/*Чотири шаблі*). "Existing HIST": replace `plans/hist/ukrainian-revolution-factions.yaml`
→ `plans/hist/syntez-revoliutsiia.yaml`. (Bio refs `plans/bio/oleksandr-dovzhenko.yaml` and
`plans/bio/mykola-khvylovyi.yaml` are REAL — leave them.)

**zinaida-tulub.md** — "Existing HIST": replace `plans/hist/sahaidachny-era.yaml`
→ `plans/hist/petro-sahaidachnyi.yaml`; replace `plans/hist/the-great-terror.yaml`
→ `plans/hist/mekhanizm-teroru.yaml`. (Bio ref `taras-shevchenko.yaml` → real
`plans/bio/taras-shevchenko.yaml` — make the path explicit; the "No dedicated module" LIT line is
honest, keep it.)

## Metadata fixes (all 6 files, header block lines 6-7)
- `**Issue:** #2318` AND `**Issue:** #2322` → `**Issue:** #2317` (Block D's canonical issue, per
  the PR's own commit `68cb28c10b ...(#2317)`).
- `**Researcher:** Gemini 1.5 Pro` / `Generalist Sub-Agent` / `Generalist Sub-Agent (Gemini 1.5 Pro)`
  / `Gemini Generalist Sub-Agent` → the ACTUAL model that ran this dispatch. Determine it
  deterministically: `grep -r bio-r1a-blockD batch_state/tasks/*.json` or
  `curl -s localhost:8765/api/orient | python -c "import sys,json; ..."` to read the recorded
  `model`. Use that exact string (do NOT guess `gemini-3.1-pro` if state says otherwise).

## Verification (#M-4 — quote raw)
1. `for p in $(grep -rhoE "plans/[a-z0-9-]+/[a-z0-9-]+\.yaml" docs/research/bio/*.md | sort -u); do
   test -e "curriculum/l2-uk-en/$p" && echo "REAL $p" || echo "FAKE $p"; done` → MUST print zero `FAKE`.
2. `grep -rn "#2318\|#2322\|Gemini 1.5\|Generalist Sub-Agent" docs/research/bio/*.md` → empty.

## Steps
1. Confirm you are on a branch based off `origin/gemini/bio-r1a-blockD-survived-2026-05-28`.
2. Apply §7 + metadata edits to the 6 files.
3. Run the two verification commands; paste raw output (zero FAKE, empty grep).
4. `git commit` conventional (`fix(bio): de-fabricate Block D §7 cross-track paths + metadata (#2400,#2317)`); Co-Authored-By line.
5. `git push -u origin <branch>`.
6. `gh pr create --base main` with body noting "supersedes #2400". **No auto-merge.**
Report PR URL (raw), the zero-FAKE proof, and the empty-grep proof.
