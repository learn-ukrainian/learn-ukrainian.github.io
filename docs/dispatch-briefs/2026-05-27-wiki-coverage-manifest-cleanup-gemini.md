# 2026-05-27 — wiki_coverage manifest cleanup + writer-side coverage requirements (Gemini)

> Dispatch target: `gemini --mode danger --worktree`, model `gemini-3.1-pro-preview`.
> Base: `origin/main` (currently `6c49ee86ab`, post PR #2370).
> Tracking: HARD BLOCKER for Phase 2a m20 ship. Brain-pick turn 1+2 evidence + Pt 9 handoff + user audit on 2026-05-27.
> Sibling pattern: PR #2370 (textbook_grounding split). Mirror that shape for wiki_coverage.

## Why this exists

Phase 2a m20 refire (worktree `.worktrees/builds/a1-my-morning-20260527-163310/`) produced a clean writer output. Every `#R-` rule from PR #2366 satisfied. **But the wiki_coverage gate blocks ship for TWO reasons, both real**:

1. **Match target is wrong shape.** The gate's `required_claim` field contains literal `Крок N:` scaffolding labels + `[S\d+]` source-reference markers. The writer (correctly, per `#R-NO-SCAFFOLDING-LEAKS`) does not echo those labels. Gate's literal-substring matcher fails. Codex correction-loop refuses to violate the writer rule (returns `<fixes></fixes>`).
2. **Writer DID miss some required content.** Audit of the produced module.md against step-5's `required_claim` shows 1 of 7 required vocab items covered (only `сніданок`; missing `вода`, `зарядка`, `раненько`, `швиденько`, `завжди`, `ніколи`). The wiki gate's role — verifying lesson covers the planned content — is legitimate. Just fixing the matcher would silence the alarm but let lessons skip required vocab.

Two-layer fix needed. Pattern is the same as PR #2370 (textbook_grounding split): separate writer-side scaffolding from gate-side semantic check.

## What to build

### Part A — wiki_coverage gate matching

In `scripts/audit/wiki_coverage_gate.py` (verify the file location first; it may also live in `scripts/build/`):

1. **Read the current gate matching logic.** Find where `required_claim` text is compared to module text. Note the current substring/match pattern.

2. **Add normalization helpers**:
   - `_strip_step_prefix(text: str) -> str` — strips leading `Крок \d+:\s*`, `Step \d+:\s*`, `Урок \d+:\s*` (any of these patterns from the start of the claim text).
   - `_strip_source_markers(text: str) -> str` — strips inline source-reference markers `\[S\d+(,\s*S\d+)*\]` (single `[S7]` or `[S1, S3]` lists).
   - `_normalize_required_claim(text: str) -> str` — applies both strip helpers, collapses whitespace, returns the pedagogical content.

3. **Extract item-level requirements from the normalized claim**. New helper `_extract_required_items(claim_text: str) -> dict`:
   - Returns `{"vocabulary": [...], "examples": [...], "key_phrases": [...]}`.
   - Vocabulary extraction: find Ukrainian words inside parentheses, e.g., `(вода, зарядка, сніданок)` → `["вода", "зарядка", "сніданок"]`. Pattern: capture `[^()]+` inside `\(...\)`, split on `,`, trim. Filter to tokens containing Cyrillic.
   - Examples extraction: find Ukrainian sentences inside quotes — `«...»`, `"..."`, `'...'`. Pattern: capture text inside Ukrainian guillemets `«[^»]+»` and double-quote variants.
   - Key-phrases: the remaining substantive content from the normalized claim, split on sentences. For simpler `claimed_location_missing` obligation types (err-N), the `manifest_payload.correct` and `incorrect` fields already give the items directly — use those.

4. **Replace the literal-match logic with item-level coverage matching**:
   - For each required vocabulary item, check whether it appears in normalized module text (Cyrillic-only, case-folded substring containment, with `\b...\b` word-boundary fuzz).
   - For each required example, check substring containment (allow ≥3 char Levenshtein distance via existing RapidFuzz if needed — see `_textbook_quote_fidelity_gate` in `linear_pipeline.py` for the pattern, added in PR #2367).
   - Gate passes for an obligation when ALL its required items are found. Gate fails when ANY required item is missing — report which specific items are missing in the violation.

5. **Failure-mode mapping** (preserve, just change the matching):
   - `sequence_step` obligations (step-N) → use vocabulary + key-phrases extraction.
   - `l2_error` obligations (err-N) → use `manifest_payload.correct` + `incorrect` directly (already item-level). Check both expected_correction_value and expected_error_value appear in `activities.yaml` (parsed YAML, not raw text — handle the `error-correction` activity type structure).
   - Other obligation types: surface in PR body if you find more failure_reasons in the worktree-163310 wiki_coverage_correction_r1.json.

6. **Deprecate the old literal-match path with a comment**: `# DEPRECATED 2026-05-27: literal Крок N: substring match. Replaced by _extract_required_items + per-item coverage. Remove after one successful Phase 2a refire.` Don't delete; un-register.

### Part B — writer prompt: surface coverage requirements without scaffolding labels

In `scripts/build/phases/linear-write.md`:

1. **Find where wiki obligations are surfaced to the writer.** Look for the section that mentions `implementation_map`, `wiki_coverage`, or `obligation` near the top of the prompt (likely in the LESSON SOURCE / Implementation Map Contract / Wiki Obligations Manifest area around lines 158-180).

2. **Add a `wiki_coverage_required_items` block** that the build pipeline populates per-module. The shape:
   ```
   ## Wiki Coverage Required Items (per-obligation breakdown)

   For each plan reference / wiki obligation, the lesson MUST teach the
   following specific items. Integrate them into the natural lesson
   flow (a model sentence using the noun, a usage example for the
   adverb, a conjugation row, a phonetic transcription). Do NOT echo
   the `Крок N:` label or `[S\d+]` source markers — those are
   writer-side scaffolding (forbidden per `#R-NO-SCAFFOLDING-LEAKS`).

   {{wiki_coverage_required_items}}
   ```

3. **Wire the template variable**. Find where the writer prompt is rendered from plan + obligations (likely `linear_pipeline.py` `build_writer_prompt` or similar). Add the rendering for `{{wiki_coverage_required_items}}`:
   - For each obligation, normalize the `required_claim` (using the helpers from Part A).
   - Extract items (using `_extract_required_items` from Part A).
   - Format as a list per obligation:
     ```
     ### step-5 (sequence step)
     - Vocabulary to introduce: вода, зарядка, сніданок (nouns); раненько, швиденько, завжди, ніколи (frequency adverbs)
     - Pedagogical goal: extend the morning routine with concrete daily-life vocabulary and frequency markers
     - Required example shape: at least one model sentence per noun/adverb integrated into a routine description
     ```
   - For `l2_error` obligations, format as:
     ```
     ### err-3 (L2 error contrast)
     - Required contrast: incorrect `Вимова: [одягайет'с'а]` vs correct `Вимова: [одягайец':а]`
     - Pedagogical goal: assimilation [т']+[с'] → [ц':а] in reflexive verb endings
     - Required location: activities.yaml `error-correction` activity, entry with `sentence`, `error`, `correction` fields
     ```

### Part C — tests

1. **Unit tests for normalization helpers** in `tests/audit/test_wiki_coverage_normalize.py`:
   - `_strip_step_prefix("Крок 5: Розширення...")` → `"Розширення..."`
   - `_strip_step_prefix("Розширення...")` (no prefix) → unchanged
   - `_strip_source_markers("...автентичні конструкції [S3].")` → `"...автентичні конструкції ."`
   - `_strip_source_markers("...форм [S1, S3].")` → `"...форм ."`
   - `_normalize_required_claim("Крок 5: Розширення... [S1, S3].")` → `"Розширення... ."`

2. **Unit tests for `_extract_required_items`**:
   - Parses `"Розширення... (вода, зарядка, сніданок) ... (раненько, швиденько, завжди, ніколи)..."` → `vocabulary: ["вода", "зарядка", "сніданок", "раненько", "швиденько", "завжди", "ніколи"]`
   - Parses an example-quoted required_claim → extracts the quoted sentence.

3. **Integration test against worktree 163310**:
   - Load `.worktrees/builds/a1-my-morning-20260527-163310/wiki_manifest.json` AS FIXTURE (copy a sanitized version into `tests/fixtures/wiki_manifest_m20.json` if you can; the worktree itself may not be available in CI).
   - Load the clean module.md from the same worktree as fixture.
   - Assert: step-4 obligation passes (дивлюся conjugation is in the lesson).
   - Assert: step-5 obligation FAILS with specific missing items reported (вода, зарядка, раненько, швиденько, завжди, ніколи — at least 5 of these 6 missing).
   - This proves: gate now correctly identifies what's missing for the writer to add, not failing on label mismatch.

4. **Update existing wiki_coverage tests** in `tests/audit/test_wiki_coverage_gate.py` (or wherever they live). If existing tests assert on the literal-match behavior, update them to assert on the new per-item shape. Don't silently delete assertions.

## Anti-fabrication contract (#M-4)

| Claim | Required evidence in PR body |
|---|---|
| "Normalization helpers added and tested" | `pytest tests/audit/test_wiki_coverage_normalize.py -v --no-header` raw final summary |
| "Item extraction matches step-5 vocabulary" | The test result line showing the extraction test passes |
| "Gate now identifies missing items in worktree 163310 lesson" | The integration test output showing step-5 fails with named missing items (вода, зарядка, раненько...) |
| "Writer prompt block added with template wiring" | `grep -A 5 "wiki_coverage_required_items" scripts/build/phases/linear-write.md` raw |
| "Old literal-match path deprecated, not deleted" | `grep -B 1 -A 2 "DEPRECATED 2026-05-27" scripts/audit/wiki_coverage_gate.py` raw |
| "Tests pass" | `.venv/bin/pytest tests/audit/ tests/build/test_linear_pipeline.py -q --no-header` final line |
| "Lint clean" | `.venv/bin/ruff check scripts/audit/ scripts/build/ tests/audit/` final line |
| "PR opened" | `gh pr view --json url` raw URL line |

## Numbered execution steps

1. **Worktree**. You start in `.worktrees/dispatch/gemini/wiki-coverage-manifest-cleanup-2026-05-27/`. Verify with `git branch --show-current` and `pwd`. `git fetch origin main && git log --oneline -3` — confirm PR #2370 is in your base.

2. **Survey existing code**:
   - Read `scripts/audit/wiki_coverage_gate.py` (find the matching logic).
   - Read `scripts/build/phases/linear-write.md` lines 158-180 (Implementation Map Contract + Wiki Obligations Manifest).
   - Read `scripts/build/linear_pipeline.py` around the writer prompt rendering (search for `wiki_coverage` / `implementation_map` / `obligation` references).
   - Read `scripts/audit/wiki_coverage_gate.py` for the existing match function shape.

3. **Read the regression evidence**:
   - `cat .worktrees/builds/a1-my-morning-20260527-163310/wiki_manifest.json | jq '.obligations[] | select(.id=="step-5")'`
   - `cat .worktrees/builds/a1-my-morning-20260527-163310/wiki_coverage_correction_r1.json | head -50`
   - `cat .worktrees/builds/a1-my-morning-20260527-163310/curriculum/l2-uk-en/a1/my-morning/module.md`
   - These three files together show: what the manifest required, what the gate found missing, what the writer actually produced. Use them to design the item-extraction logic precisely.

4. **Implement Part A** — normalization helpers + item extraction + per-item match. Match existing function-shape conventions in the file.

5. **Implement Part B** — writer prompt block + template wiring. Keep the block tight; don't pad.

6. **Implement Part C** — tests. Use worktree-163310 wiki_manifest.json + module.md as fixtures (copy or reference; whatever fits CI policy).

7. **Run tests**: `.venv/bin/pytest tests/audit/ tests/build/test_linear_pipeline.py -q --no-header`. Capture final line.

8. **Run lint**: `.venv/bin/ruff check scripts/audit/ scripts/build/ tests/audit/`. Capture final line.

9. **Commit conventional**:
   ```
   feat(wiki_coverage): per-item gate matching + writer-side coverage block

   Resolves the writer-prompt vs wiki_coverage gate drift exposed by
   the Phase 2a m20 refire (worktree a1-my-morning-20260527-163310).
   The hardened pipeline produced a clean writer output (all 6 #R-
   rules satisfied) but wiki_coverage blocked ship because required_claim
   text contains literal Крок N: scaffolding labels and [S\d+] source
   markers; #R-NO-SCAFFOLDING-LEAKS correctly forbids those in module body.

   Two-layer fix:
   - Gate: normalize required_claim (strip Крок N:, [S\d+]), extract
     vocabulary + examples per-item, match each item in module text.
     Item-level coverage now drives the verdict, not literal substring.
   - Writer prompt: new wiki_coverage_required_items block surfaces
     normalized requirements (e.g. "step-5 requires vocab: вода, зарядка,
     сніданок, раненько, швиденько, завжди, ніколи") so writer integrates
     them without echoing scaffolding labels.

   Integration test against worktree 163310:
   - step-4 (дивлюся conjugation) PASSES — writer covered it
   - step-5 FAILS with specific missing items reported (writer skipped
     6 of 7 expansion-vocab items; gate now tells writer exactly what
     to add next refire instead of asking for a scaffolding label)

   Old literal-match path deprecated, not deleted. Remove after one
   successful Phase 2a refire.

   X-Agent: gemini/wiki-coverage-manifest-cleanup-2026-05-27
   ```

10. **Push + PR**: `git push -u origin gemini/wiki-coverage-manifest-cleanup-2026-05-27` then `gh pr create` with title `feat(wiki_coverage): per-item gate matching + writer-side coverage block`. Body must include raw test/lint outputs + the integration-test result showing step-4 PASS and step-5 FAIL with named missing items.

11. **DO NOT auto-merge**. Orchestrator review required.

## Scope guardrails

- **DO NOT** modify writer prompt rules other than adding the new `wiki_coverage_required_items` block. The 6 `#R-` rules from PR #2366 stay as-is.
- **DO NOT** modify `_textbook_quote_fidelity_gate`, `chunk_context_for_all_refs_gate`, or `published_quote_for_publishable_refs_gate` — those are settled.
- **DO NOT** touch `curriculum/l2-uk-en/a1/my-morning/` — m20 stays as-is until re-fire under this PR.
- **DO NOT** delete the old wiki_coverage match function — deprecate with comment, remove next cycle.
- **DO NOT** silence the err-1..err-6 failures by skipping them. Either include err-N in the new per-item path, OR keep the existing literal-match path active for `l2_error` obligation type as a transitional step (note in PR body which approach you chose).
- **DO NOT** bundle anything beyond the two-layer fix. If you find more failure modes in the regression evidence, file follow-up issues with `gh issue create`; don't expand scope.

## On unexpected blockers

- If `wiki_coverage_gate.py` doesn't exist at the expected path, search broadly: `grep -rln "wiki_coverage\|coverage_pct" scripts/`. The matching logic might be in `linear_pipeline.py` directly.
- If `required_claim` shapes vary across obligation types (sequence_step vs l2_error vs others not yet seen), implement per-type extractors. Default to internal-extraction if shape is unknown; don't crash.
- If the writer-prompt rendering pipeline is more complex than expected (e.g., the obligations are rendered as XML rows, not direct template), follow the existing rendering convention. Surface the architectural shape in the PR body.
- If integration tests against worktree 163310 can't run in CI because the worktree path isn't available, copy the wiki_manifest.json + module.md into `tests/fixtures/` so tests are hermetic.
