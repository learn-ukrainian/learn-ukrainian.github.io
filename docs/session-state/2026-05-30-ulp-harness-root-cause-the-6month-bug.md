---
date: 2026-05-30
session: "Root-cause session. Found WHY 6 months + $1200 produced zero shippable A1 modules: the V7 harness was configured to produce grammar-translation, never immersion. Gates enforce MECHANICS, never TEACHING. ULP pedagogy documented but not wired into the writer prompt; stress-marking never wired into V7; an active rule told the writer 'explanations stay in English'. Fix dispatched (ulp_fidelity harness change). Project at a transfer-to-Codex decision point."
status: ROOT-CAUSE-FOUND · ulp-harness-fix-IN-FLIGHT(codex) · 4-fixes-shipped-this-session · m20-still-not-shippable · DECISION-PENDING(continue-vs-transfer-to-codex)
main_sha: 41373bed32
main_green: yes
---

# 2026-05-30 — The 6-month root cause: the harness enforces mechanics, never teaching

## TL;DR for whoever owns this next (Claude, future-me, or Codex)
After 6 months and ~$1200, **no A1 module has ever shipped** (pipeline: `content_done=0`,
`audit_passing=0` all core tracks; **96 build attempts** for a1/my-morning alone, May 19→29).
The reason is NOT "LLMs can't teach" and NOT interface/state-loss (though that hurt too). It is a
**harness misconfiguration that makes the pipeline produce grammar-translation by construction**:

1. **`scripts/build/universal_rules/R-AUDIENCE-LANGUAGE-A1.md`** (injected into EVERY a1/a2 build)
   said verbatim: *"A1 explanation prose stays in English. Ukrainian appears only as TARGET."*
   That is the **anti-ULP rule.** It mandates English-lecture-about-Ukrainian. Duplicated at
   `scripts/build/phases/linear-write.md:308`.
2. **`scripts/config.py::compute_immersion_band`** emits, for early A1, the directive
   *"Every paragraph is English. THEORY & EXPLANATION: English prose."* — self-labeled a "Phase A
   placeholder"; the ULP doc warns it under-immerses.
3. **`scripts/pipeline/stress_annotator.py` was NEVER wired into the V7 path** (`linear_pipeline.py`
   / `v7_build.py`) — only into dead v5/v6. So V7 modules get **zero stress marks** → ULP Practice 3
   violated automatically. (`ukrainian_word_stress` v1.1.1 is installed and works.)
4. **Every gate checks mechanical correctness** (VESUM real-words, no-Russianisms, full tables,
   filled quizzes, decolonization markers) and **NOT ONE enforced teaching / immersion fidelity.**
   So 96 builds produced 96 mechanically-clean grammar-translations that passed gates and were never
   lessons.

**The pedagogy SSOT exists and was ignored**: `docs/best-practices/ulp-presentation-pattern.md`
(Anna Ohoiko's 7 practices, S1 baseline ≈50:50 UK:EN, Ukrainian-first, em-dash gloss, stress marks
on every multi-syllable word, dialogue UK-only, named teacher persona, UK-only comprehension Q&A).
CLAUDE.md says READ IT FIRST before any A1/A2 build. This session (and prior ones) didn't. The doc
was itself created 2026-05-25 after the user said *"this is not the first time we talk about this.
and you already don't remember."* — i.e. this is a **recurring** failure to apply ULP.

User's own words (authoritative): *"i as a foreigner prefer the ukranian approach"*; rejects
hand-authored modules (must scale to 1,700); rejects scope-cut (plans/wikis are intentional);
wants the **harness** to produce ULP-faithful lessons, guardrailed.

## What shipped to main THIS session (all green, main = 41373bed32)
- `a68cee0988` → `413c2904cc` wiki/m20: **полотенце removed from A1** — authentic Ukrainian
  (dim. of полотно; Грінченко 1907 / Голоскевич 1929 / СУМ-20; VESUM; check_russian_shadow=False)
  AND not A1 lexis. Flagging it was a heritage-mislabel (кобета/кобіта pattern). Kept завтрак (a real
  Russianism) as the contrast.
- `e1ed02ccb6` wiki/m20: **restored `<!-- bad -->завтрак<!-- /bad -->`** — repaired a self-caused
  `wiki_completeness_gate` regression (dropping полотенце took decolonization-pairs to 0 < a1 min 1).
  #M-7 miss: m20 wiki is mirrored in `tests/audit/test_wiki_completeness_gate.py`; test assertion
  updated 2→1 pairs.
- `ac069996df` (#2423) **qg: decolonization → WARNING on core A1–C2, TERMINAL only on seminars.**
  Per user direction: core ships on deterministic gates + pedagogy; the subjective LLM decolonization
  score no longer hard-blocks core. `thresholds.terminal_dims_for(profile)`; full verdict unchanged.
- `41373bed32` (#2425) **mdx renderer: dedup inline activities in Activities tab** (structural
  fingerprint, handles idless dups) **+ sanitize Resources `notes`** (strips "surfaced in module.md",
  "Plan reference;", "No Grade N blockquote", etc.). Verified on real 193432 render.

## IN FLIGHT — the decisive test
**Dispatch `ulp-harness-a1-immersion-2026-05-30`** (codex/gpt-5.5/xhigh, base 41373bed32, worktree
`.worktrees/dispatch/codex/ulp-harness-a1-immersion-2026-05-30`). Brief: `/tmp/brief-ulp-harness.md`.
It is editing the right files (confirmed mid-run): `R-AUDIENCE-LANGUAGE-A1.md`, `linear-write.md`,
`config.py`, `stress_annotator.py`, `linear_pipeline.py`, `v7_build.py`, `linear-review-dim.md`, and
NEW `scripts/audit/ulp_fidelity_gate.py`. No commit/PR yet as of this handoff (active=1).

The 4 harness changes:
1. Flip R-AUDIENCE-LANGUAGE-A1 → ULP S1 (UK-first, em-dash gloss, named persona, dialogue UK-only,
   English as receding scaffold, ~50:50).
2. Fix the immersion-band directive text (config.py) to describe ULP S1, not "every paragraph English".
3. Wire `stress_annotator` into V7 as a deterministic post-write phase (stress marks guaranteed by the
   machine, not the LLM; idempotent).
4. Add deterministic **`ulp_fidelity` gate**: stress present, em-dash glosses, UK-only dialogues,
   UK-first/non-lecture openers, UK:EN ratio in band → REVISE on violation. THIS is the guardrail that
   makes "gates check mechanics not teaching" impossible to repeat (incl. me forgetting ULP again).

## NEXT ACTIONS (verify on resume — do NOT trust this doc blindly)
1. `curl /api/delegate/active` — is `ulp-harness-a1-immersion-2026-05-30` done? `gh pr list`.
2. When PR opens: review diff (esp. R-AUDIENCE-LANGUAGE-A1 actually flipped; stress wired into
   `linear_pipeline`; `ulp_fidelity_gate.py` checks are real) + CI. Merge --squash if green.
   **Push-first**: the build worktree branches from origin/main.
3. **Fire ONE V7 build of a1/my-morning under the new harness** (`--writer codex-tools --use-generator
   --worktree`), Monitor the JSONL. The build's OUTPUT is the deliverable — render it (assemble_mdx)
   and judge against ULP (stress marks throughout, UK-first em-dash glosses, named persona, dialogue
   UK-only, no English-grammar-lecture). **Do NOT hand-author** — the user rejects hand-built modules.
4. If it teaches → the bug is fixed harness-wide; the gate keeps it true; resume the A1 line.
   If it's still grammar-translation → the diagnosis is right but the writer can't execute ULP under
   prompt-only direction; next lever is a cross-model editor pass or writer swap (NOT scope-cut, NOT
   hand-author).

## DECISION CONTEXT (read this — it's why the session ends here)
User is **deciding whether to transfer the project to Codex Desktop and cancel the Claude
subscription** (6 months, $1200, zero shipped A1 modules). Codex's pitch (sound): Desktop as owning
orchestrator, CLI as execution, Monitor API as state, PRs as durable record, subagents bounded —
correctly diagnoses the **state-loss** failure mode (this session served a STALE build6 preview as
"current" — exactly that failure). That operating model is already this project's documented
architecture; the gap was adherence, not the model. **The 6-month bug (mechanics-not-teaching) is
interface-agnostic and transfers to whoever owns it.**

Plan per user: based on the in-flight build result, either Claude continues, OR Claude writes a
handover doc per Codex's request; then work remaining issues until subscription lapses.

## Traps that keep biting (for ANY successor)
- **Stale artifacts**: the tracked `starlight/.../a1/my-morning.mdx` is OLD; build worktrees check it
  out; failed builds (before mdx phase) leave it stale → reviewers read a ghost. Render current output
  with `assemble_mdx(module_dir, out, plan_path)` (pure, no gate) before reviewing. Untracked preview
  MDX in `starlight/src/content/docs/a1/`: `my-morning-{CURRENT-193432,GOLD,v72,v72-build6}-preview.mdx`
  (review scaffolding; clean up on real promote). New preview files need a starlight dev-server restart
  (content-layer cache) or they 500 with UnknownContentCollectionError.
- **#M-7**: editing a wiki/plan that's mirrored in a hardcoded test fixture (e.g. m20 wiki ↔
  `test_wiki_completeness_gate.py`) REQUIRES local pytest before push. "Docs-only" excludes those.
- **Dispatch PRs branch from the base SHA at dispatch time** — if main moved (or was red), merge
  origin/main into the PR branch + re-run CI before merging.
