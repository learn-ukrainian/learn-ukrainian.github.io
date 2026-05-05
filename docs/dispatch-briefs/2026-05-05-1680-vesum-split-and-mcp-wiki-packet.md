# Codex dispatch — #1680 Split VESUM out of `scripts/rag/query.py` + wire MCP into wiki packet

## Context

Spawned from #1631 (closed via PR #1635). Three residuals not covered:

1. **Split VESUM out of `scripts/rag/query.py`.** Currently hybrid — Qdrant client (`search_text`, `search_literary`, etc.) PLUS VESUM SQLite (`verify_words`, `verify_lemma`). Can't be wholesale deleted because `linear_pipeline._vesum_gate` (~line 2075) and `tests/test_rag.py` consumers still import VESUM functions from it. After split, `query.py` should be deletable.

2. **Wire MCP dictionary verification into wiki knowledge packet.** Current `build_knowledge_packet` only documents which MCP tools to use as instruction text — does NOT append actual `verify_lemma` / `search_style_guide` / `search_definitions` output for the plan's required vocab. Brief for #1631 specified this; PR #1635 didn't include it.

3. **Update `docs/phase-4-exemplar-report.md`.** Still mentions Qdrant in failure-mode section (~line 82). Replace with new wiki+MCP flow description.

## Worktree (mandatory)

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
.venv/bin/python scripts/delegate.py dispatch ...  # invoked by parent — do not re-invoke
```

Worktree will be created at `.worktrees/dispatch/codex/1680-vesum-split-mcp-packet/` automatically by delegate.py when this brief is dispatched with `--worktree` (bare). Inside the worktree:

1. Verify branch base: `git log --oneline HEAD..origin/main` empty.

## Numbered steps

### Part 1 — VESUM extraction

1. **Inventory.** `git grep -n 'from scripts.rag.query\|from scripts.rag import query\|rag.query.verify\|rag.query.lemma\|verify_words\|verify_lemma' scripts/ tests/ orchestration/ docs/`. Capture every consumer.

2. **Decide target module.** Two options:
   - `scripts/rag/vesum_query.py` (sibling, low-churn import path)
   - `scripts/verification/vesum.py` (semantic home with other verification logic)

   Pick (b) if `scripts/verification/` exists and houses related code; otherwise (a). Document the choice in commit body.

3. **Move VESUM functions** to the chosen target module. Keep API surface IDENTICAL (function names, signatures, return shapes). Tests `tests/test_rag.py` should continue to pass with only an import-line change.

4. **Update import sites.** Every consumer found in step 1 → update to new module. Run `git grep -n 'from scripts.rag.query'` afterward to verify zero remaining VESUM references in `query.py`.

5. **Inspect Qdrant path.** Is `scripts/rag/query.py`'s Qdrant logic genuinely dead? `git grep -n 'search_text\|search_literary\|qdrant_client'` across active code. If dead → delete `query.py` entirely. If still consumed → leave Qdrant logic in `query.py` and just remove the VESUM functions; document the residual in the commit body.

6. **Run pytest.** `.venv/bin/python -m pytest tests/test_rag.py tests/test_verification* -x -q`. All must pass.

7. **Run full pytest.** `.venv/bin/python -m pytest tests/ -x -q -k "not slow"` (skip slow tests).

### Part 2 — MCP into wiki packet

8. **Locate `build_knowledge_packet`** — likely in `scripts/wiki/` or `scripts/build/phases/`. `git grep -n 'def build_knowledge_packet\|build_knowledge_packet(' scripts/`.

9. **Read the function.** Understand current shape: what it accepts (plan + wiki articles?), what it returns (compressed packet text), and where `compress_wiki_packet` is invoked.

10. **Add a `Dictionary context` section** AFTER `compress_wiki_packet`. For each `required_vocab` lemma in the plan (or `vocabulary_hints`):
    - Call `verify_lemma(lemma)` — capture form + part-of-speech
    - Call `search_definitions(lemma, limit=1)` — capture top SUM-11 definition
    - Call `search_style_guide(lemma, limit=1)` — capture style note if any

    Format as a compact YAML or markdown block:
    ```
    ## Dictionary context
    - **<lemma>** [<POS>]
      - Definition: <SUM-11 short>
      - Style note: <if present>
    ```

11. **Batch the MCP calls.** Use `mcp__sources__verify_words` (plural) for efficiency where possible. Keep total round-trip ≤ 2× the plan's lemma count.

12. **Token budget.** Cap the appended dictionary context at ~1500 tokens (≈ 6000 chars). Truncate definitions to first 200 chars. If lemma count exceeds budget, prefer SHORT entries over fewer lemmas.

13. **Test.** Add a test in `tests/test_wiki_packet_dictionary_context.py` (or similar) that:
    - Loads a fixture plan with 5 known lemmas
    - Calls `build_knowledge_packet`
    - Asserts the `Dictionary context` section appears with all 5 lemmas
    - Asserts truncation applies to overly-long definitions

14. **Run new test.** `.venv/bin/python -m pytest tests/test_wiki_packet_dictionary_context.py -x -v`

### Part 3 — Doc update

15. **Open `docs/phase-4-exemplar-report.md`.** Find the Qdrant mention (~line 82). Replace with a description of the wiki+MCP flow:
    > "Failure mode: writer cites a vocabulary item that fails MCP verification at review-time. The wiki+MCP knowledge packet is supposed to surface this gap during writing — see `Dictionary context` section in `build_knowledge_packet`."

### Part 4 — Wrap

16. **Run ruff.** `.venv/bin/ruff check scripts/ tests/`

17. **Commit.**
    ```
    refactor(rag): split VESUM out of query.py + wire MCP into wiki packet (#1680)
    ```
    Body lists:
    - Files moved/renamed (VESUM extraction)
    - Import sites updated (count)
    - `query.py` status (deleted / Qdrant residual kept)
    - `build_knowledge_packet` enhancement summary
    - New test path
    - `docs/phase-4-exemplar-report.md` line(s) updated

18. **Push:** `git push -u origin codex/1680-vesum-split-mcp-packet`

19. **Open PR:**
    ```bash
    gh pr create --title "refactor(rag): split VESUM out of query.py + wire MCP into wiki packet (#1680)" --body "$(cat <<'EOF'
    ## Summary

    Three residuals from #1631:

    1. VESUM functions moved out of `scripts/rag/query.py` to `<target module>` so the Qdrant-only `query.py` becomes a clean candidate for deletion.
    2. `build_knowledge_packet` now appends a `Dictionary context` section with `verify_lemma` + `search_definitions` + `search_style_guide` output for plan vocab.
    3. `docs/phase-4-exemplar-report.md` Qdrant reference replaced with wiki+MCP flow description.

    ## Verification

    - Existing `tests/test_rag.py` passes against new VESUM module
    - New `tests/test_wiki_packet_dictionary_context.py` passes
    - Full pytest passes (modulo `-k "not slow"`)
    - ruff clean
    - `git grep` confirms VESUM is fully relocated

    ## Notes

    <document VESUM target module choice + query.py deletion status>

    Closes #1680.
    EOF
    )"
    ```

20. **Do NOT enable auto-merge.**

## Acceptance criteria

- VESUM functions moved out of `scripts/rag/query.py` to a clean home; consumers updated
- `query.py` either deleted (preferred) or documented as Qdrant residual
- `build_knowledge_packet` appends a `Dictionary context` section with real MCP tool output
- Token budget enforced (~1500 tokens dictionary context cap)
- New tests added; existing tests unbroken
- `docs/phase-4-exemplar-report.md` updated
- ruff clean

## Discipline

- Keep VESUM API surface identical (no renames, no signature changes)
- `git grep` BEFORE deleting `query.py` (memory rule "rename/refactor checklist")
- Reference #1680 in commit
- No `--no-verify`
- Worktree cleanup post-merge by next session
