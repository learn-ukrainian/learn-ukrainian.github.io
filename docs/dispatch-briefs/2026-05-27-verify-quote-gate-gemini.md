# 2026-05-27 — HARD verify_quote gate + prev/next link safety (Gemini)

> Dispatch target: `gemini --mode danger --worktree`, model `gemini-3.1-pro-preview`.
> Base: `origin/main` (currently `89295fac7d`, post PR #2365).
> Tracking: orchestrator-driven post-m20-ship hardening; sibling dispatch to `2026-05-27-v7-prompt-hardening-codex.md` (which handles the writer-prompt + reviewer-rubric side).

## Why this exists

m20 (`a1/my-morning`, PR #2364) shipped with two pipeline gaps:

**Gap 1 — unverified textbook blockquotes.** Line 57 of `curriculum/l2-uk-en/a1/my-morning/module.md` reads:

```
> Мій день
> — Сьогодні в мене багато справ, — мови-
> ло жабеня Кнак. — Запишу.
> «Поснідати. Одягнутися. Піти до Квака.
```

`Кнак` is a hallucinated proper noun — should be `Квак`, consistent with the rest of the quote ("до Квака", "з Кваком"). The blockquote is attributed `*— Захарійчук, Grade 1, p.24*` but no gate verified the quote against the source at write time. VESUM doesn't catch proper-noun typos. `mcp__sources__verify_quote` and `mcp__sources__verify_source_attribution` exist but are not gate-enforced — the writer can cite without verifying.

**Gap 2 — prev/next links point to existing-but-wrong modules.** The link generator falls back to whatever sibling module exists on disk when the LOGICAL prev/next per `curriculum.yaml` ordering doesn't exist yet. User direction: prefer `null` (no link) over a wrong link.

## What to build

### Part A — HARD `verify_quote` gate in `scripts/build/linear_pipeline.py`

Add a new gate that runs after the writer phase, before the LLM reviewer phase. For every `>` blockquote in `module.md`:

1. Detect attribution lines in the shape `*— Source, p.N*` or `*— Author, Source Title, Grade N, p.M*` immediately following the blockquote (zero or one blank line gap). Define a canonical regex; document it in a comment.
2. Extract the blockquote text and the (source, page) tuple.
3. Call the MCP tool that verifies the quote against the textbook corpus. The tool may be `mcp__sources__verify_quote` and/or `mcp__sources__verify_source_attribution` — read `scripts/mcp_servers/sources/` (or the equivalent location) to confirm the exact signature.
4. **HARD failures:**
   - Tool returns `match=False` / no result → FAIL with the offending blockquote text + attribution + nearest source candidate (if returned).
   - Tool returns a partial match (text differs by ≥3 chars from source, ignoring whitespace + OCR artifacts) → FAIL with the source's actual text in the diagnostic.
   - Blockquote has no `*— Source, p.N*` attribution → FAIL (require attribution) UNLESS a `<!-- NO_VERIFY: reason -->` comment immediately precedes the blockquote. Match the existing pipeline convention (read `_textbook_grounding_gate` or `_citations_resolve_gate` for the precedent).
5. The gate must be **HARD** (terminal failure, not soft warning). Follow the existing `_xxx_gate` pattern in `linear_pipeline.py` (~lines 6000-8800). Read 3-4 existing gates to absorb the shape (return dict with `passed`, `checked`, `violations`, `message`, etc.).

Wire the new gate into the gate registry where the other content gates are registered (look near `_activity_schema_gate` registration, ~line 6074). Give it a name like `textbook_quote_fidelity` (or `verify_quote_gate` — match existing naming style).

### Part B — prev/next link safety

Locate the prev/next module link generator. Candidates (run `git grep -l` to find the real one):
- `scripts/build/v7_build.py`
- `scripts/build/render_mdx.py` (if it exists)
- `scripts/build/linear_pipeline.py` (somewhere; the MDX assembly path)
- `starlight/src/components/` (if Astro-side)

Current behavior: when `curriculum.yaml` orders modules `m19 → m20 → m21`, and `m21` doesn't exist on disk, the link generator falls back to the nearest existing module (e.g., links to `m25` or whatever is next). That's wrong.

Desired behavior: prefer `null` (no prev/next link rendered) over a wrong link. The user said wrong links are worse than absent ones.

Implement at the source-of-truth layer (Python `scripts/build/` if possible; Astro only if Python-side has no link emit). Add tests covering:
- (a) Both prev and next exist on disk and match curriculum.yaml → both linked.
- (b) Prev exists, next doesn't → prev linked, next `null`.
- (c) Neither exists → both `null`.
- (d) Curriculum.yaml has no entry for current module → fail loudly (don't silent-skip).

## Anti-fabrication contract (#M-4)

| Claim | Required evidence in PR body |
|---|---|
| "verify_quote MCP tool exists and is callable from the pipeline" | The MCP tool definition raw (e.g., `cat scripts/mcp_servers/sources/.../verify_quote.py` head) OR the in-pipeline import + a one-liner unit test that mocks the MCP call |
| "Gate halts pipeline on mismatch" | A test that fires the gate against a known-bad quote and asserts on the failure shape (raw test output) |
| "Existing gates were used as a pattern, not replaced" | `git diff --stat` showing only ADDITIONS to existing gate function lists; no edits to existing gate bodies |
| "Tests pass" | `.venv/bin/pytest tests/test_linear_pipeline*.py tests/test_v7_build*.py tests/test_prev_next*.py -q --no-header` final line raw |
| "Lint clean" | `.venv/bin/ruff check scripts/build/ tests/` final line raw |
| "PR opened" | `gh pr view --json url` raw URL line |

## Numbered execution steps

1. **Worktree.** You start inside `.worktrees/dispatch/gemini/v7-verify-quote-gate-2026-05-27/`. Verify with `pwd` and `git branch --show-current`.

2. **Survey existing gates.** Read `scripts/build/linear_pipeline.py` around lines 6000-8800. Identify 3-4 existing `_xxx_gate` functions (`_activity_schema_gate`, `_textbook_grounding_gate`, `_citations_resolve_gate`, `_vesum_verified_gate`) — read their shapes. Note where gates are registered (the `record("name", _xxx_gate(...))` calls near line 6074).

3. **Confirm MCP tool signature.** Find the verify_quote tool definition. Try in order: `grep -rn "def verify_quote\|verify_quote =" scripts/mcp_servers/ scripts/audit/ scripts/build/`. Copy the signature into a comment in your new gate.

4. **Read m20 failure case.** `curriculum/l2-uk-en/a1/my-morning/module.md` lines 55-65 (the `Кнак` blockquote) and lines 95-107 (the second Захарійчук blockquote). These ground the gate against a real failure.

5. **Implement Part A — the `verify_quote` gate.** Match the existing `_xxx_gate` shape. Decide the no-attribution policy (FAIL hard vs allow with `<!-- NO_VERIFY: reason -->` opt-out) based on precedent from `_citations_resolve_gate`. Document the choice.

6. **Wire Part A into the gate registry.** Match existing registration style.

7. **Identify prev/next link generator** for Part B. Use `git grep -ln "prev\|next\|navigation\|sibling" scripts/build/ starlight/`. Pick the source-of-truth file.

8. **Implement Part B — null-over-wrong.** Add the 4 test cases. If link logic spans Python AND Astro, implement in Python; Astro consumes the JSON/YAML Python emits.

9. **Run tests.** `.venv/bin/pytest tests/test_linear_pipeline*.py tests/test_v7_build*.py tests/test_prev_next*.py -q --no-header`. Capture final line.

10. **Ruff.** `.venv/bin/ruff check scripts/build/ tests/`. Capture final line.

11. **Commit conventional:**
    ```
    feat(v7-gates): HARD verify_quote gate + prev/next link null-over-wrong

    Adds verify_quote gate to linear_pipeline.py: every `>` blockquote
    with `*— Source, p.N*` attribution is verified via the MCP sources
    layer; quote-text mismatch or missing-source FAIL hard at the gate
    stage, before reviewer phase. Catches the m20 `Кнак`/`Квак` typo
    class that VESUM cannot detect.

    Adds prev/next link safety: when curriculum.yaml's logical neighbor
    doesn't exist on disk, render `null` instead of falling back to the
    nearest existing module. Wrong links are worse than absent ones.

    Tests:
    - 4 cases on verify_quote (match / mismatch / partial / no-attribution)
    - 4 cases on prev/next (both exist / prev only / next only / neither)

    X-Agent: gemini/v7-verify-quote-gate-2026-05-27
    ```

12. **Push + PR.** `git push -u origin gemini/v7-verify-quote-gate-2026-05-27` then `gh pr create` with title `feat(v7-gates): HARD verify_quote gate + prev/next link null-over-wrong`.

13. **DO NOT auto-merge.**

## Scope guardrails

- **DO NOT** modify `scripts/build/phases/linear-write.md` or `linear-review-dim.md` — that's the parallel codex dispatch.
- **DO NOT** touch `curriculum/l2-uk-en/a1/my-morning/`.
- **DO NOT** change existing gate definitions — only ADD the new one.
- **DO NOT** loosen any existing gate to compensate for the new one.
- If prev/next link logic is Astro-only with no Python emit, implement in Astro with tests, but note the architectural drift in the PR body.

## On unexpected blockers

- If `verify_quote` MCP tool doesn't expose what we need (e.g., only exact-string match, no fuzzy ≥3-char tolerance), implement the fuzziness in the gate layer — the gate can normalize whitespace + OCR artifacts before comparing. Note this in the PR body.
- If the MCP tool requires async/await but `linear_pipeline.py` gates are sync, follow the existing pattern (`_textbook_grounding_gate` calls the MCP layer — copy its sync/async convention).
- If you find the prev/next logic is entirely client-side (Starlight Astro) with no Python emit, implement in Astro `astro.config.mjs` or component layer, but file a follow-up issue requesting Python-side ownership for testability.
