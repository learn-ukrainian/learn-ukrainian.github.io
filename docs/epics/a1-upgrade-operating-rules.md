# A1 / curriculum-upgrade operating rules

Binding scars from the 2026-09-14 hot session (PR #7999 live). Load this file
before any V7 `--upgrade` work, A1 content rollout, or Pages cutover. Do not
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

- Merge gate: exact-head CF APPROVE **and** CI Gate green on that SHA, then
  `gh pr merge --squash` (merge queue). Never `--auto`. Never
  `--delete-branch` until `gh pr view` shows `MERGED`. Then reap worktrees.
- **Push to `main` does not publish curriculum.** Auto-deploy
  (`deploy-pages.yml` eligibility) fail-closes on `curriculum/` and
  `site/src/content/` (`content_drift` / `unknown_path`). That is
  intentional: merge ≠ community rollout.
- When the operator wants it live:
  `gh workflow run deploy-pages.yml --ref main`
  Then prove the learner URL is **200** (e.g.
  `https://learn-ukrainian.github.io/a1/<slug>/1/`). Do not claim live from
  a skipped deploy job or from `/a1/` index 200 alone.

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
- **Outcome, not engine-on-main:** the unit of done is a published
  `/a1/<slug>/` — content PR, CF, green CI, merge, and manual
  `deploy-pages.yml` cutover (see Merge and live Pages above). Landing the
  build engine on `main` is not completion. Once gates pass in a worktree,
  open the scripts-free content PR the same session — do not idle waiting
  for a prompt.
- **Auto-finalize must not mix `scripts/` into curriculum PRs.** Content PRs
  from this epic stay scripts-free; `scripts/` changes are a separate PR.
  This is a constraint on the existing auto-finalize path in
  `scripts/delegate.py`, not a new control plane — do not build one to
  enforce it unless a future revision of this file says otherwise.

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
