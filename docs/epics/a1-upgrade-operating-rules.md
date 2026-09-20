# A1 / curriculum-upgrade operating rules

Binding scars from the 2026-09-14 hot session (PR #7999 live). Load this file
before any V7 `--upgrade` work, A1 content rollout, or Pages cutover.
Driver playbook: `$drive-epic` **§0d** (do not fork a second skill). Do not
rediscover these in chat. Issues #7994 and #7995 must match this file; if they
disagree, this file plus the operator GO below win until the issue body is
edited.

Epics: **#7994** machinery (`curriculum-upgrade`) · **#7995** A1 content
rollout (`a1-upgrade`). Inventory: [`a1-upgrade-inventory.md`](a1-upgrade-inventory.md).
Landing shape: [`a1-upgrade-landing-contract.md`](a1-upgrade-landing-contract.md).

## Operator GO already decided (do not reopen)

- Canonical learner URLs are **`/a1/`**. The old edition is archived as
  **`a1-v1`**. There is no live `a1-v2`. Parallel-preview language in older
  issue text is stale.
- Do **not** rebuild lessons by hand. Use
  `scripts/build/v7_build.py {level} {slug} --upgrade --worktree --writer …`.
- Preserve-and-expand the archived module. Do not regenerate from scratch.
  **Classify** keep / drop / rewrite: keep letter videos and working examples;
  drop hyphenation, named narrators, unread Ukrainian walls, slop. Copy Ohoiko's
  *method* (sound, then English that explains), never her persona or scripts.
  A1.1 (modules 1–4): the learner cannot read untaught letters — English carries
  teaching; Ukrainian is the example with audio/video. Create and upgrade use
  this same standard (C1/C2/FOLK/BIO change the immersion *band*, not the ethics).
- A1 is bilingual by design (about 40–55% Ukrainian on the page; English
  **after** Ukrainian). From **A2 on**, do not raise English.
- Module **9** (`what-is-it-like`) is the **close/summary shape**, not a
  content clone: bilingual bullets, dialogues as `>` / `DialogueBox`, last
  lesson heading `Підсумок модуля — Module summary`. Do not ship module 8's
  `Завершення модуля` completion table or raw ` ```text ` fences.
- No named narrator. Named people only inside dialogues. Quoted material only
  with attribution, listed in Ресурси.
- The operator is one person. Do not use they/them for the operator.

## What is already live (2026-09-14)

- Merge: PR #7999 → `18e6b86bae` on `main`.
- Published: `/a1/things-have-gender/{,1,2,3}/` and
  `/a1/what-is-it-like/{,1,2,3}/` (200). Archive: `/a1-v1/`.
- Next module in manifest order: **`sounds-letters-and-hello`**, then the rest
  of A1.1, then remaining A1.2 after 8–9, through `a1-finale`.

## Writers and review (do not substitute)

- **Writer:** Gemini 3.8 High via AGY (`--writer` `agy-tools` / `gemini-tools`).
  Sources and VESUM tool calls are mandatory (this corpus also feeds a
  Ukrainian LLM dataset).
- **Gemini self-adjust** after write is allowed. It is **not** the merge gate.
- **Independent CF of record:** Astra (`gpt-6-astra`) @ **medium**, native
  Codex, exact head. Writer family must not review itself.
- **Do not use Kimi** for this curriculum upgrade work (write, QG, or CF).
- Claude is available again as a future seat. Do not force it onto an
  already-resolved Astra review.
- If `gh pr review --approve` / `--request-changes` fails because the GitHub
  token is the PR opener, post the CF verdict as a **COMMENT** bound to the
  SHA, with `VERDICT: APPROVE` or `VERDICT: REQUEST_CHANGES` in the body.
  Discussion is not the gate.

## Stress marks

- Oracle: `scripts.verification.stress.verify_stress` (same as sources MCP
  `verify_stress`). VESUM has no stress field — do not guess.
- The annotator **repairs** already-stressed words. A single acute on an
  allowed vowel stays. Packed ULIF duals (`ро́збі́р`) collapse to one
  pedagogical mark. Overrides: `scripts/data/stress_overrides.yaml`
  (`завжди`, `також`, …). Lookup is casefolded so `Мене` → `Мене́`.
- Assembler: pair a ` ```text ` fence with a following support table only
  after blank lines or the captions `Support after the dialogue:` /
  `Support after the Ukrainian lines:`. Do not delete other prose.

## Merge and live Pages (two different steps)

- **CF review-fix before CI (operator 2026-09-18, fleet):** Astra (or other
  exact-head CF) on the **branch** → fix → re-CF until APPROVE **before**
  opening any PR (draft or ready — drafts still trigger CI here). Do not start
  CI Gate on heads still in the CF fix loop. Canonical:
  `agents_extensions/shared/rules/workflow.md` § Merge policy.
- Merge gate: exact-head CF APPROVE **and** CI Gate green on that SHA, then
  `gh pr merge --squash` (merge queue). Never `--auto`. Never
  `--delete-branch` until `gh pr view` shows `MERGED`. Then reap worktrees.
- **Push to `main` does not publish curriculum.** Auto-deploy
  (`deploy-pages.yml` eligibility) fail-closes on `curriculum/` and
  `site/src/content/` (`content_drift` / `unknown_path`). That is
  intentional: merge ≠ community rollout.
- **Continuous deploy (operator 2026-09-18):** after a content merge that
  should be live, the driver runs
  `gh workflow run deploy-pages.yml --ref main`, proves the learner URL(s)
  **200** (full module paths, not a single lesson), **notifies** the operator,
  and continues — do **not** wait for a per-cutover GO or create a deploy
  bottleneck. Operator checks async.
  Example prove: `https://learn-ukrainian.github.io/a1/<slug>/{,1,2,…}/`.
  Do not claim live from a skipped deploy job or from `/a1/` index 200 alone.

## Writer / reviewer split (do not swap hats)

- **Content (V7 writer):** one writer, one reviewer. Writer = Gemini 3.8 Flash
  High (`agy-tools`). Reviewer = Astra @ medium. They do not swap hats on the
  same module — the writer does not review its own module and the reviewer
  does not write. Parallelism model: writer on module N+1 while Astra reviews
  module N, not two content writers running at once.
- **Machinery:** Claude Sonnet implements this epic's scripts/docs/CI work;
  Fable advises only if needed. Independent CF of record for machinery
  changes is not Claude — Astra or Gemini.
- **No Chinese lanes** (Kimi, DeepSeek, GLM, Qwen) on this epic — write, QG,
  or CF.
- **A1 summaries may preview later grammar.** Example: `/a1/what-is-it-like/2/`
  `Підсумок уроку` names antonym pairs, **і / а / але**, calques, and dropping
  present-tense **є**. That is a teacher preview, not a defect. Reviewers
  (Astra/Gemini) must not REQUEST_CHANGES solely because the summary is "too
  advanced" for A1. Do not add a repeating "we will explain this later" line
  on every such mention.
- **Outcome, not engine-on-main:** the unit of done is a published
  `/a1/<slug>/` **full module** (landing + every lesson), not a lesson subset
  — content on branch → Astra CF review-fix → ready PR → green CI → merge →
  continuous `deploy-pages.yml` (see Merge and live Pages above). Landing the
  build engine on `main` is not completion. Once gates pass in a worktree,
  push the scripts-free branch and start Astra CF the same session — do not
  idle waiting for a prompt; open the PR only after CF APPROVE (no draft-before-CF
  either — drafts still trigger CI).
- **CF before any curriculum build (not upgrade-only):** exact-head CF must be
  clear on the prep the build depends on before `v7_build` / `--upgrade` /
  writer runs. CF feedback → fix → re-CF; do not rebuild while CF is still
  open. Built content gets its own CF before merge. Canonical wording:
  `agents_extensions/shared/rules/pipeline.md` § Pipeline policy authority.
- **Auto-finalize must not mix `scripts/` into curriculum PRs.** Content PRs
  from this epic stay scripts-free; `scripts/` changes are a separate PR.
  This is a constraint on the existing auto-finalize path in
  `scripts/delegate.py`, not a new control plane — do not build one to
  enforce it unless a future revision of this file says otherwise.
- **A1 module titles and lesson names are bilingual.** Landing cards (`title`
  + `titleEn`, `sub` + `subEn`) and the lesson list on each module landing
  (`lessons.yaml` titles + generated `index.mdx`) must show Ukrainian **and**
  English. Titles must match what the redesigned module actually teaches (no
  leftover Hello on module 1 after greetings moved). **English density in
  activities:** modules that teach letters before the learner can read (A1.1
  1–4) need English next to learner-facing **prompts, options, and
  explanations** (and activity **instructions**). That does **not** mean
  stuffing English into every interactive surface: `error-correction`
  **stems** stay natural Ukrainian sentences containing the error — English
  belongs in the **explanation** (solution), not in a meta «Не пиши… / Do not
  write…» stem and not as an em-dash gloss on the sentence to correct. Widget
  chrome (`Find and Fix`, step labels) must be Ukrainian for A1
  (`isUkrainian={true}`). From `who-am-i` onward, keep original A1 immersion
  (UA first, English support — not an English course). **Left nav** module
  labels must be bilingual like landing cards; CF may REQUEST_CHANGES for
  missing EN on sidebar labels (no longer deferred).

## Epic split (do not thrash sessions)

- Stay in the **hot session** while the machine is warm. Do not cut the
  driver to a new epic mid-rollout just because #7995 exists.
- #7995 is the A1 content **board**. #7994 stays open for machinery defects
  found during rollout. A blocking machinery defect is always fixed in its
  own **separate machinery PR** against #7994, never patched from the
  content PR — see "Auto-finalize must not mix `scripts/` into curriculum
  PRs" above. If the defect blocks the module in hand, the content PR waits
  on that machinery PR as a dependency rather than absorbing the fix.
- #7995 / older #7994 text that still says `a1-v2`, handmade Phase 0, or
  “leave `/a1/` untouched” is stale. Canonical `/a1/` is already the upgraded
  edition.

## Commands

```sh
.venv/bin/python scripts/build/v7_build.py a1 <slug> --upgrade --worktree --writer gemini-tools
gh workflow run deploy-pages.yml --ref main
```
