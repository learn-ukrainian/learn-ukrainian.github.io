# Dispatch — refine PR #3195 (Atlas freshness gate #3150): scope hard gate to lexicon CODE only

You are refining an EXISTING, mostly-correct PR. The Makefile `atlas` target, the DB-free
code-hash approach, and the `check_manifest_freshness.py` script structure are all CORRECT — **keep
them.** This is a scoping tweak: the current design over-gates by including module *vocabulary* in the
freshness fingerprint + CI trigger, which red-X's every content PR (content authors have no
`vesum.db`/`sources.db` on CI and cannot regenerate the manifest). Fix that.

## #M-4 preamble — every claim must be tool-backed
Report each verifiable claim with the literal command + cwd + raw output line. Specifically:
- "tests pass" → `pytest` final summary line, verbatim.
- "ruff clean" → `ruff check` final line, verbatim.
- "freshness check passes" → `check_manifest_freshness.py` exit + last line, verbatim.
- "pushed" / "PR updated" → `git push` result + `gh pr view 3195 --json url` line, verbatim.
Do NOT write "I verified X" without the raw output.

## Branch / worktree
- This dispatch is launched with `--worktree --base codex/atlas-freshness-3150`, so your worktree is
  branched from the EXISTING PR #3195 branch. Build on it.
- When done, push so PR #3195 updates **in place**:
  `git push origin HEAD:codex/atlas-freshness-3150`
- Do NOT open a new PR. Do NOT merge. Do NOT commit `site/src/data/lexicon-manifest.json` or any `.db`.

## The fix (numbered)
1. `git status` to confirm your worktree base is the PR #3195 branch (you should see the Makefile
   `atlas` target, `scripts/lexicon/check_manifest_freshness.py`, the CI workflow edit, and a
   committed freshness sidecar).
2. **Fingerprint lexicon CODE only.** The gating fingerprint must hash the *content* of
   `scripts/lexicon/*.py` (the high-value drift to catch is "enrichment logic changed but the
   manifest wasn't regenerated"). **Remove module vocabulary lemmas** (`curriculum/l2-uk-en/*/*/vocabulary.yaml`)
   from the gating fingerprint entirely.
3. **Remove `curriculum/l2-uk-en/*/*/vocabulary.yaml` from the `atlas` CI trigger path filter** in the
   workflow. New-module vocab is expected churn folded in by the orchestrator's periodic `make atlas`,
   NOT a per-PR gate.
4. (Optional, low-risk only) keep a SEPARATE advisory `vocab_lemmas` count field in the sidecar for
   observability, but it must NOT participate in the hard-fail comparison.
5. **Recompute the committed sidecar** from the new code-only fingerprint and update any test fixture
   that pins the sidecar value. The freshness check must pass green on the current tree.
6. Tests: `.venv/bin/python -m pytest -k "freshness or fingerprint or manifest" -q` → green.
7. Lint: `.venv/bin/ruff check scripts/ tests/` → clean. Run `.venv/bin/python scripts/lexicon/check_manifest_freshness.py` → exits 0.
8. Commit (conventional): `fix(lexicon): scope atlas freshness hard-gate to lexicon code; drop vocab churn (#3150)`.
   End the commit body with the agent trailer if the repo lints it (`lint_agent_trailer.py`).
9. `git push origin HEAD:codex/atlas-freshness-3150` to update PR #3195. Paste the `gh pr view 3195 --json url` line.
10. Do NOT merge; leave for orchestrator review.

## Acceptance
- A pure content PR that only adds module vocab does NOT trigger the `atlas` CI job and does NOT change
  the gating fingerprint.
- A PR that edits `scripts/lexicon/*.py` WITHOUT regenerating the manifest DOES fail the freshness gate.
- `pytest -k "freshness or fingerprint or manifest"` green; `check_manifest_freshness.py` exits 0.
