# Codex brief — Kill the scaffolding-leak class (m20 / #2389, #2380)

## Why (root cause, already traced — do NOT re-litigate)
m20 (a1/my-morning) reached `module_done` end-to-end under `--use-generator` but scored
`llm_qg 3.5 REJECT` on naturalness/tone. The reviewer was FAIR (same leak scored 7.0 on a
prior build — run-to-run variance). The ONLY defect: the writer pasted **planning scaffolding
verbatim** into published prose. Leaked lines (from build #3 `module.md`):

```
A reflexive verb adds **-ся**... Крок 1: спершу regular **читати**: ... (наприклад, читати) [S8].
Крок 2: use **прокидатися, одягатися, умиватися**; add **-ся** або **-сь**... with **я/ти** practice [S3, S6].
Крок 4: teach **дивитися** ...; note поява вставного «л» — дивлюся [S7].
```

These `Крок N:` step labels + `[SN]` source markers + EN↔UK code-switch are **scaffolding from
the wiki manifest**, never meant for learner prose. Two confirmed defects in the pipeline:

1. **Primary leak vector — `render_for_writer_prompt`** in
   `scripts/build/phases/implementation_map.py:426` renders `treatment_template` (which carries the
   RAW `required_claim`, e.g. `"Крок 1: Ознайомлення... [S8]... [S6, S8]"`) and `location_hint`
   **without sanitizing**. It is the ONLY writer-prompt render path that skips the existing strip
   helpers. Proof: `writer_prompt.md` has 21× `Крок`, 56× `[SN]`; the dominant source is the impl-map
   contract. (The obligation-checklist path `_render_structured_wiki_coverage_required_items` already
   sanitizes via `normalized_claim` — leave it alone.)

2. **No deterministic safety net.** The only thing that catches this leak class is the noisy LLM
   naturalness reviewer (3.5↔7.0 on the SAME leak). The advisory prompt rule
   `scripts/build/universal_rules/R-NO-SCAFFOLDING-LEAKS.md` exists but the writer ignored it.

The existing, reusable strip helpers live in `scripts/audit/wiki_coverage_gate.py`:
- `_strip_step_prefix` (line 1151) — strips LEADING `Крок|Step|Урок N:` (`^`-anchored).
- `_strip_source_markers` (line 1158) — strips `[S\d]`/`[С\d]` markers ANYWHERE.
- `_normalize_required_claim` (line 1163) — both + whitespace collapse.

## Scope — TWO fixes + tests. Do NOT add the exemplar, do NOT change prompt size limits.

### Fix 1 — Sanitize the impl-map writer-prompt render (the root cause)
In `scripts/build/phases/implementation_map.py`:
- Add a render-time sanitizer that, for the WRITER PROMPT only, strips scaffolding from every string
  rendered by `render_for_writer_prompt`: `treatment_template` string values (recursively for nested
  dict/list values) AND `location_hint`.
- It MUST strip step labels **anywhere in the string, not just leading** (the source claims start with
  `Крок N:` but be robust) AND strip `[SN]`/`[СN]` source markers, then collapse double spaces.
- **Do NOT modify `_strip_step_prefix`'s `^` anchoring** — the wiki_coverage gate uses
  `_normalize_required_claim` for claim-MATCHING and changing its anchoring risks gate drift. Add a
  NEW un-anchored step-label regex for the render path (you may reuse `_strip_source_markers` as-is).
  Put the new shared sanitizer where both modules can import it without a circular import — a small
  public helper in `scripts/audit/wiki_coverage_gate.py` (e.g. `strip_writer_scaffolding(text)`) is
  fine; `implementation_map.py` already sits below it in the import graph.
- **GUARD (critical): do NOT mutate the implementation_map / seeded sidecar data itself.** Per PR #2404
  the `wiki_coverage` gate reads the SEEDED sidecar for its claim fallback. Sanitize only the rendered
  STRING returned to the writer prompt; the JSON payload keeps markers intact for the gate.

### Fix 2 — Deterministic post-emit gate: `scaffolding_leak`
Add `_scaffolding_leak_gate(text: str) -> dict` in `scripts/build/linear_pipeline.py`, modeled on
`_formatting_standards_gate` (line 8245). Wire it into the deterministic gate report next to
`record("formatting_standards", ...)` (line 6482) via `record("scaffolding_leak", _scaffolding_leak_gate(module_text))`,
and ensure it is included in the `gates["passed"] = all(...)` aggregation (line ~6540).
- **FAIL (passed=False)** when the published `module.md` prose contains, OUTSIDE comments and code:
  - step labels: `(?:Крок|Step|Урок)\s+\d+\s*:`
  - source markers: `\[[SС]\d+(?:\s*,\s*[SС]\d+)*\]`
- **Exclusions (avoid false positives):** strip `<!-- ... -->` HTML/MDX comments (the legit
  `<!-- VERIFY: source="...step-1..." -->` lines must NOT trip it) and fenced code blocks (``` ```)
  before scanning. The error-correction deliberate-bad-form fields are in `activities.yaml`, not
  `module.md`, so they are out of scope here.
- Report the offending `{line, text}` list so failures are actionable.
- **HARD gate, no auto-correction.** Do NOT add it to `WRITER_CORRECTION_GATES` — a leak interwoven
  into prose is not a clean find/replace; fail the build and force a clean rewrite.

### Tests (required — `tests/`)
- `render_for_writer_prompt` on a payload whose `treatment_template.required_claim` =
  `"Крок 1: Ознайомлення... [S8] ... [S6, S8]"` → rendered output contains NEITHER `Крок 1:` NOR `[S8]`
  but DOES retain the substance (e.g. `Ознайомлення`). Also assert `location_hint` is sanitized.
- Assert the seeded/payload dict is UNCHANGED after rendering (guard against in-place mutation).
- `_scaffolding_leak_gate`: FAIL on prose with `Крок 2:` / `[S3, S6]`; PASS when those tokens appear
  ONLY inside `<!-- ... -->` or a fenced code block; PASS on clean A1 prose.

## Verification (#M-4 — every claim tool-backed; quote raw output)
Run from repo root, paste RAW final lines:
- `.venv/bin/python -m pytest tests/<new_test_files> -q` → final `N passed` line.
- `.venv/bin/ruff check scripts/build/phases/implementation_map.py scripts/build/linear_pipeline.py scripts/audit/wiki_coverage_gate.py <new tests>` → `All checks passed!`.
- The render regression test IS the clean-render proof (assert no `Крок N:` / `[SN]` in the rendered
  string). Build the synthetic payload inline in the test from the leaked `required_claim` above —
  do NOT depend on any `.worktrees/builds/...` path; that build worktree is NOT present in your fresh
  dispatch checkout.

## Numbered execution steps (MANDATORY — dispatch enforces worktree)
1. `git worktree add` is handled by `--worktree` (you run inside it). Confirm `git rev-parse --show-toplevel` is the worktree.
2. Implement Fix 1 + Fix 2 + shared sanitizer.
3. Add the regression tests.
4. `.venv/bin/python -m pytest` the new tests + `tests/test_writer_prompt_*` + any impl-map/wiki-coverage tests touched.
5. `.venv/bin/ruff check` the changed files.
6. `git commit` conventional, e.g. `fix(pipeline): sanitize impl-map writer-prompt render + scaffolding_leak gate (#2389,#2380)`. Co-Authored-By line per repo convention.
7. `git push -u origin <branch>`.
8. `gh pr create` with body summarizing root cause + the two fixes + test evidence. **Do NOT auto-merge.**

Report back with: PR URL (raw `gh pr view --json url`), the pytest final line, the ruff final line,
and the `grep -c` = 0 proof.
