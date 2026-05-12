# Claude-headless dispatch brief — writer-prompt tune (budget + citation + immersion discipline)

> **Issue:** none yet — file 1 follow-up issue tracking the tune work + before/after gate evidence.
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/claude/writer-prompt-tune-2026-05-13/`
> **Base:** `origin/main` (currently `e7e892bb7a`)
> **Hard timeout:** 7200s
> **Silence timeout:** 1800s
> **Effort:** xhigh
> **Model:** claude-opus-4-7

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. CWD does NOT persist across blocks. Always prefix with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/writer-prompt-tune-2026-05-13 && ...` or use absolute path.

Inside the worktree, `.venv/` is gitignored. Use MAIN checkout's `.venv` via absolute path: `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

Tune the V7 writer prompt (`claude-tools` adapter is the current writer per ADR-2026-05-06 REVISED-AGAIN) so that on the next `a1/my-morning` build, the 3 prompt-tunable soft fails from yesterday's bakeoff resolve. The 2 pipeline-side gate bugs are being fixed in parallel by a separate Codex dispatch (`docs/dispatch-briefs/2026-05-13-pipeline-gate-trio.md`); together those + this brief should unblock A1 publication.

After this tune, on a re-run of `a1/my-morning` claude-tools writer, expect:
- `plan_sections.passed = true` (no section over its 270-330 budget; currently `Дієслова на -ся` is 336w, 6 over)
- `citations_resolve.passed = true` (every inline citation string exactly matches an entry in `resources.yaml`'s `references[]`)
- `immersion.pct` in 18-22% sweet spot (well under the 24% policy cap; currently 25.4%, 1.4 over)

---

## #M-4 preamble — verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "writer prompt now enforces budget discipline" | `git diff main -- claude_extensions/phases/linear-write*.md` shows new budget-discipline section | quote the diff |
| "writer prompt enforces citation-string parity" | same `git diff` shows added citation rules | quote the diff |
| "writer prompt targets 18-22% immersion sweet spot, not just ≤24% cap" | same `git diff` shows new immersion guidance | quote the diff |
| "Tests pass" | `.venv/bin/pytest tests/test_prompt_template*.py tests/test_writer*.py` if any exist | quote summary |
| "Lint clean" | `.venv/bin/ruff check claude_extensions/` if any python — likely no-op for md files | quote final line |
| "Re-run bakeoff (optional, costs ~1 LLM call) shows fix" | If you choose to dry-run, capture `python_qg.json` for the three gates before/after | quote before+after |

Inline "I checked X" claims without quoted raw output = hallucination per #M-4. Quote.

---

## The three prompt-tunable fails — exact evidence

### Fail A: plan_sections (1 section 6w over budget)

**Evidence from `audit/bakeoff-2026-05-13-midday/claude/python_qg.json` `plan_sections` gate:**
```json
{
  "passed": false,
  "missing_headings": [],
  "word_budgets": [
    {"section": "Діалоги", "count": 304, "min": 270, "max": 330, "passed": true},
    {"section": "Дієслова на -ся", "count": 336, "min": 270, "max": 330, "passed": false},
    {"section": "Мій ранок", "count": 330, "min": 270, "max": 330, "passed": true},
    {"section": "Підсумок", "count": 282, "min": 270, "max": 330, "passed": true}
  ]
}
```

Three of four sections are inside the band; one is 6 words over. The writer prompt currently states the budget but does not enforce mid-write self-correction. Two prompt patterns to consider:

- **Word-budget reminder block** at the top of each section's write directive: "Section budget: 270-330. After drafting, count words and trim if over OR add if under."
- **Compact rephrasing instruction** at draft-completion: "Before emitting, count each section. Any section exceeding `max` by >5w must be trimmed by removing one example or compressing one sentence."

Read the relevant phase prompts (likely `claude_extensions/phases/linear-write.md` or `linear-write-chunk.md` — verify via `find claude_extensions -name 'linear-write*'`). Apply minimal, surgical edits — do NOT rewrite the whole prompt.

### Fail B: citations_resolve (3 prose citations don't match references[])

**Evidence:**
```json
{
  "passed": false,
  "unknown": [
    "Захарійчук, 4 клас, с. 162-163",
    "Кравцова, 4 клас, с. 112-113",
    "Авраменко, 7 клас, с. 67"
  ]
}
```

These prose citation strings exist inline in the module but no exactly-matching entry in `resources.yaml`'s `references[]`. The writer needs a contract: **every inline citation string must have a byte-identical match in `resources.yaml` `references[]` `citation` field (or whatever the key is — verify by reading `resources.yaml` from the artifact)**.

Read `audit/bakeoff-2026-05-13-midday/claude/resources.yaml` to see the actual references[] shape. The fix in the prompt should be:

- A directive: "After drafting the module, list every prose citation string used. For each, verify it has an exact-match entry in `references[]`. If a citation lacks a `references[]` entry, ADD one (with full bibliographic detail) OR remove the citation."
- A formatting standard: pick one canonical citation string format (e.g. `Захарійчук, 4 клас, с. 162-163`) and require both inline and references[] to use that exact form.

### Fail C: immersion 25.4% > policy cap 24% (policy a1-m15-24)

**Evidence:**
```json
{
  "passed": false,
  "pct": 25.4,
  "min_pct": 15,
  "max_pct": 35,  // display bug being fixed separately; policy cap is 24
  "policy": "a1-m15-24",
  "long_ukrainian_sentences": [
    "> Дієслова із суфіксом -ся(-сь), які виражають зворотну дію, називаються зворотними: навчатися, закохатися",
    "Сучасний дієслівний суфікс -ся(-сь) — це давня коротка форма зворотного займенника себе в Зн",
    "Уживається -ся(-сь) після інфінітивного суфікса -ти(-ть) або закінчення в особових формах ді"
  ]
}
```

For policy `a1-m15-24`, the immersion cap is 24% and per the bakeoff brief the sweet spot is 18-22%. The writer is going long on Ukrainian-only sentences inside the EN-scaffolded sections (3 examples shown above are full Ukrainian sentences with no English gloss).

Prompt fix shape:

- Target band: explicitly state "Target: 18-22% Ukrainian-only content for A1. Hard cap: 24%. Going over the cap fails the build."
- Long-sentence guidance: "Long Ukrainian-only blockquotes (≥15 words) count strongly toward immersion. When you draft a Ukrainian-only blockquote, either (a) add an English gloss on the next line, or (b) shorten the blockquote to ≤10 words, or (c) cut the blockquote and paraphrase its content in English with a 1-2 word Ukrainian inline."
- Self-check: "Before emitting, estimate the immersion ratio. If over 22%, trim one Ukrainian-only sentence."

---

## Numbered steps (mandatory checklist)

1. **Worktree setup:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian && \
   git worktree add -b claude/writer-prompt-tune-2026-05-13 .worktrees/dispatch/claude/writer-prompt-tune-2026-05-13 origin/main
   ```
2. **Read context first** — before editing, read:
   - `claude_extensions/phases/linear-write.md` (and any sibling write prompts; verify list via `find claude_extensions -name 'linear-write*'`)
   - `audit/bakeoff-2026-05-13-midday/claude/writer_prompt.md` (the actual rendered prompt the writer received)
   - `audit/bakeoff-2026-05-13-midday/claude/resources.yaml` (to confirm references[] shape)
   - `audit/bakeoff-2026-05-13-midday/claude/module.md` (where the cited-but-missing references appear inline)
   - `docs/best-practices/module-content-quality.md`, `docs/best-practices/prompt-engineering.md`
3. **Make minimal edits** — target 30-100 LOC of prompt-text diff total. Do NOT rewrite the whole phase prompt. Each of the three fails should produce a small, scoped, named edit. Add a `<!-- BUDGET DISCIPLINE -->` / `<!-- CITATION DISCIPLINE -->` / `<!-- IMMERSION DISCIPLINE -->` comment block if useful for future archaeology.
4. **Linter / quick tests:**
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/ -k "prompt or writer" -x
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check claude_extensions/
   ```
   Quote both summary lines.
5. **Optional dry-validation** — DO NOT run a full V7 build (orchestrator policy: only user runs V7 builds). Instead, render the prompt template (whatever the `prompt-review` skill calls) and read the new prompt to confirm the budget/citation/immersion directives are actually present. Quote 3 lines (one per fail).
6. **Commit** — single commit, conventional message: `fix(writer-prompt): budget + citation + immersion discipline for V7 claude-tools writer`.
7. **Push:** `git push -u origin claude/writer-prompt-tune-2026-05-13`.
8. **Open PR** via `gh pr create`. Body must include:
   - The exact 3 prompt diff hunks (one per fail)
   - The prior-state evidence from `audit/bakeoff-2026-05-13-midday/claude/python_qg.json` (the JSON snippets above)
   - A statement: "validation requires user-run V7 rebuild on a1/my-morning to confirm fix — not run here per orchestrator-only build policy"
9. **DO NOT auto-merge.** Hand back for review.

---

## What blocks the merge

- Prompt edits accidentally remove existing discipline (e.g. activity-type coverage, decolonization, VESUM gate) — read AROUND the edit site.
- Tests failing.
- Ruff failing.
- Edits larger than 100 LOC suggesting a rewrite rather than a tune.

---

## Pre-submit checklist (per AGENTS.md:11-26)

- [ ] `.python-version` unchanged
- [ ] `.yamllint` and `.markdownlint.json` unchanged
- [ ] No `status/*.json` or `audit/*-review.md` files in diff
- [ ] Every changed file is a phase prompt or related schema/doc — no Python writer adapter changes
- [ ] Total files changed < 5

---

## Related

- ADR: `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` (REVISED-AGAIN; claude-tools is V7 writer for A1+A2)
- Predecessor handoff: `docs/session-state/2026-05-13-afternoon-bakeoff-and-twopass-brief.md`
- Discussion that named this as Track A of staged option C: channel `twopass-workflow-2026-05-13`
- Companion dispatch (Codex, pipeline gate trio): `docs/dispatch-briefs/2026-05-13-pipeline-gate-trio.md`
- Bakeoff artifacts: `audit/bakeoff-2026-05-13-midday/claude/`
