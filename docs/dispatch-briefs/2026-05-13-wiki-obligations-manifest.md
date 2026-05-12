# Codex dispatch brief — Wiki Obligations Manifest + prompt restructure + reviewer pass + parser gate

> **Decision:** User signoff 2026-05-13 on "ship all" (Codex's Option E synthesis from the `wiki-enforcement-2026-05-13` channel). Substance converged across Codex + Gemini + Claude-headless rounds; the architecture is yours from round 1 + round 2.
> **Discussion thread:** `ab channel tail wiki-enforcement-2026-05-13 --thread 03b423305969482f84e46d574388297a` (your full round-1 + round-2 posts) and `--thread 65fb2ccb4fd44dcc91ec2024a1c2976e` (Gemini + Claude reads + areas of agreement)
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/wiki-obligations-manifest-2026-05-13/`
> **Base:** `origin/main` (currently `62e5f7ccdf` post-Phase-B-merge)
> **Hard timeout:** 7200s
> **Silence timeout:** 1800s
> **Effort:** high

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. CWD does NOT persist across blocks. Prefix every command with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/wiki-obligations-manifest-2026-05-13 && ...` or absolute path.

Inside the worktree, `.venv/` is gitignored. Use MAIN checkout's `.venv` via absolute path: `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

Ship the architecture you proposed in the channel: **Wiki Obligations Manifest** as the enforced object, replacing the failed "tag-audit on writer's free declaration" approach. Four coordinated pieces:

1. **Deterministic manifest extractor** — parses wiki pages into structured `sequence_steps[]`, `l2_errors[]`, `phonetic_rules[]`, `decolonization_bans[]` arrays with stable IDs and source line metadata.
2. **Writer prompt restructure** — manifest goes near TOP of the writer prompt (before plan/contract), reframed as "synthesize this wiki content into the 4-tab format" (Gemini's phrasing). `<wiki_coverage>` replaced with `<implementation_map>` — no DEFERRED hatch. Knowledge Packet stays later as source context. The current 1254-line tail-burial pattern dies.
3. **Dedicated wiki-coverage reviewer pass** (`scripts/build/phases/linear-review-wiki-coverage.md`) — receives manifest + generated artifacts, verifies each obligation_id has artifact evidence in the claimed location. Runs as a hard sub-gate before aggregate QG. **NOT a 6th `QG_DIMS` dimension** (you caught the structural constraint: `scripts/common/thresholds.py:49-55` + `scripts/build/linear_pipeline.py:2610-2619`).
4. **Deterministic coverage gate** (`scripts/audit/wiki_coverage_gate.py`) — compares manifest obligation IDs to artifact evidence locations. HARD fail only on objective absence (missing obligation IDs, missing correct form, missing wrong/right contrast for `treatment=contrast_pair` errors, missing learner-facing phonetic rule). Semantic-quality scoring stays with the reviewer pass. Numbers (coverage threshold, treatment-type requirements) live in `scripts/config.py` SSOT.

**Empirical baseline to beat:** `curriculum/l2-uk-en/a1/my-morning/module.md` (current state, on main) addresses 0 of 6 wiki-named L2 errors, 1 of 5 sequence steps, 0 phonetic rules. Anti-degradation test: rebuild `a1/my-morning` with the new pipeline and verify L2-error coverage moves from 0/6 to a meaningful number (≥4/6 if the design works as proposed). If the rebuild doesn't move the needle, surface immediately rather than silently shipping.

---

## #M-4 preamble — verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "Manifest extractor exists and produces structured output for a1/my-morning" | `.venv/bin/python -c "from scripts.build.phases.wiki_manifest import extract_manifest; import json; print(json.dumps(extract_manifest('wiki/pedagogy/a1/my-morning.md'), indent=2, ensure_ascii=False)[:2000])"` | quote stdout — must show ≥6 l2_errors and ≥5 sequence_steps |
| "Parser handles wiki heading variants" | run extractor on at least 10 distinct A1 wiki pages; quote the per-page (l2_errors, sequence_steps, phonetic_rules) counts | table or per-page summary in PR body |
| "Prompt restructure landed" | `grep -n 'LESSON SOURCE\|Wiki Obligations Manifest\|## Knowledge Packet' scripts/build/phases/linear-write.md` shows manifest section before `## Module Context` line | quote grep output |
| "DEFERRED hatch is gone" | `grep -i 'DEFERRED' scripts/build/phases/linear-write.md` returns nothing | quote grep (empty) |
| "Reviewer pass exists with manifest in context" | `grep -n 'manifest\|wiki.coverage\|obligation' scripts/build/phases/linear-review-wiki-coverage.md` shows manifest is consumed | quote grep |
| "Deterministic gate exists" | `grep -n 'def check_wiki_coverage\|def validate_obligations' scripts/audit/wiki_coverage_gate.py` | quote grep |
| "Gate wired into pipeline" | `grep -n 'wiki_coverage\|wiki_manifest' scripts/build/linear_pipeline.py scripts/build/v7_build.py` | quote grep |
| "QG_DIMS unchanged (still 5 dims)" | `grep -A 10 'QG_DIMS' scripts/common/thresholds.py` shows same 5 dimensions | quote grep |
| "Tests pass" | `.venv/bin/pytest tests/test_wiki_manifest.py tests/test_wiki_coverage_gate.py tests/test_linear_pipeline*.py -x` | quote final summary line raw |
| "Lint clean" | `.venv/bin/ruff check scripts/build/phases/wiki_manifest.py scripts/audit/wiki_coverage_gate.py scripts/build/phases/linear-write.md scripts/build/linear_pipeline.py` (md files skipped by ruff; just .py) | quote final line raw |
| "Rebuild test on a1/my-morning improves coverage" | rebuild instructions in §"Phase 2 rebuild test" below | quote before/after coverage report |

Inline "I checked X" claims without quoted raw output = hallucination per #M-4. Quote.

---

## Files to create

### 1. `scripts/build/phases/wiki_manifest.py` (new)

Parser for wiki pages → structured obligations.

**Schema** (Python TypedDict or dataclass):

```python
@dataclass
class L2Error:
    id: str  # e.g. "err-1"
    incorrect: str
    correct: str
    why: str
    treatment: Literal["contrast_pair", "prose_explanation"]
    source_lines: str  # e.g. "37-44"

@dataclass
class SequenceStep:
    id: str  # e.g. "step-1"
    heading: str  # full heading text
    step_num: int
    required_claim: str  # the canonical pedagogical claim
    source_lines: str

@dataclass
class PhoneticRule:
    id: str  # e.g. "phon-1"
    written: str  # e.g. "-шся"
    spoken: str  # e.g. "[с':а]"
    treatment: Literal["explicit_explanation"]
    source_lines: str

@dataclass
class DecolonizationBan:
    id: str  # e.g. "ban-1"
    rule: str
    source_lines: str

@dataclass
class WikiManifest:
    slug: str
    wiki_path: str
    sequence_steps: list[SequenceStep]
    l2_errors: list[L2Error]
    phonetic_rules: list[PhoneticRule]
    decolonization_bans: list[DecolonizationBan]
```

**Parsing sources to handle** (sample 10+ A1 wiki pages to discover heading variants):
- `## Послідовність викладання` OR `## Послідовність введення` — numbered "Крок N:" entries
- `## Типові помилки L2` OR `## Типові помилки L2 (англомовні учні)` — markdown table with `| ❌ Помилково | ✅ Правильно | Чому |` 3-column shape (sometimes 4-column with explanation column)
- Phonetic rules — extracted from tables/sequence steps mentioning `вимова` + IPA-style `[ ]` notation
- `## Деколонізаційні застереження` when present

**Heading detection** must be robust to whitespace + parenthetical variants. Recommend regex like `r'^## Послідовність (викладання|введення)\b'` for the sequence header.

**Empty obligations are valid** — a wiki page may have no phonetic rules, or no decolonization bans. Empty lists are not errors.

### 2. `scripts/build/phases/linear-review-wiki-coverage.md` (new)

Reviewer prompt for the dedicated wiki-coverage pass. Input: manifest JSON + generated artifacts. Output: per-obligation verdict + final pass/fail.

**Shape:**
- Read each obligation ID + required treatment + claimed artifact location
- Verify the cited artifact location actually contains evidence consistent with the treatment type
  - `contrast_pair`: both incorrect and correct forms appear in the activity body
  - `prose_explanation`: the rule is discussed in module.md prose with the wiki claim's substance
  - `explicit_explanation` (phonetic): learner-facing pronunciation guidance present, not vague "smooth speech" wave-away
- Emit verdict per obligation: PASS / PARTIAL / FAIL with evidence excerpt
- Final aggregate: all PASS → green; any FAIL → red; PARTIAL → soft signal (configurable threshold for hard-fail)

**Pattern after `linear-review-dim.md`** but DO NOT extend `QG_DIMS`. This is a parallel pipeline step, not a per-dim addition.

### 3. `scripts/audit/wiki_coverage_gate.py` (new)

Deterministic gate. Inputs: manifest + writer's implementation_map (from `<plan_reasoning>` blocks) + activities.yaml + module.md.

**Hard-fail conditions:**
- Implementation map missing for any obligation_id in the manifest
- For `treatment=contrast_pair` L2 errors: incorrect form OR correct form not present in the cited activity
- For `treatment=prose_explanation` L2 errors OR phonetic rules: claimed module.md location doesn't contain the substance markers (correct form + key terms from the wiki claim)
- For sequence_steps: step's heading or canonical claim substance not present in module.md prose

**Advisory output:** per-obligation coverage status, exposed as telemetry.

**SSOT for thresholds** (in `scripts/config.py`):
- `WIKI_COVERAGE_MIN_PCT` (advisory)
- `WIKI_COVERAGE_HARD_FAIL` (bool, default True — gate flips to advisory in development if needed)

### 4. Tests

- `tests/test_wiki_manifest.py` — extractor unit tests against `wiki/pedagogy/a1/my-morning.md` and 2-3 other A1 wiki pages. Assert L2 errors extracted include the 6 known mistakes from my-morning. Assert sequence steps include 5 from my-morning. Assert heading-variant robustness.
- `tests/test_wiki_coverage_gate.py` — gate unit tests with synthetic manifests + synthetic implementation_map + synthetic artifacts that pass/fail each hard-fail condition.
- `tests/test_linear_pipeline.py` (extend existing) — integration test that the pipeline calls the manifest extractor + gate + reviewer in the right order, and `QG_DIMS` remains 5 dimensions.

---

## Files to edit

### `scripts/build/phases/linear-write.md`

- **Move the Knowledge Packet block.** Currently rendered at the END (lines 263-265 in the template: `## Knowledge Packet\n\n{KNOWLEDGE_PACKET}`). Move it (and add the manifest section) to appear near the TOP, BEFORE `## Module Context` (currently line 176).
- **Add a new section ABOVE the Knowledge Packet block in its new position:**
  ```
  ## LESSON SOURCE — synthesize this wiki content into the 4-tab format

  The wiki content below is the LESSON SOURCE you must translate into the
  four artifacts. It is not background reference. Every obligation listed in
  the Wiki Obligations Manifest must be implemented in the artifacts you
  produce. Failure to address a wiki-named L2 error, sequence step, or
  phonetic rule is the project's most common writer failure and is the
  single largest reason A1 modules under-teach.

  ## Wiki Obligations Manifest

  {WIKI_MANIFEST}
  ```
- **Add a new template variable `{WIKI_MANIFEST}`** that renders the compact JSON manifest (separate from the full wiki text).
- **Replace `<wiki_coverage>` references / placeholders if present** — the current template uses `<teaching_sequence>` (line 19); KEEP `<teaching_sequence>` as-is (it's useful trace metadata) BUT add a new sub-node `<implementation_map>` that requires:
  ```
  <implementation_map>
  For each obligation_id in the Wiki Obligations Manifest, list:
    - obligation_id: <id>
    - artifact: <module.md | activities.yaml | vocabulary.yaml | resources.yaml>
    - location: <section name or activity id>
    - treatment: <how the obligation is addressed — e.g. "contrast_pair in activity act-3"
                  or "prose explanation in section §Дієслова на -ся paragraph 2">
  No DEFERRED. Every obligation must be implemented in THIS module, not a later one.
  </implementation_map>
  ```
- **The OLD `## Knowledge Packet` section at the tail stays** (full wiki context) but renamed to `## Full Wiki Context (source of truth for citations)` to disambiguate from the new top-position manifest section.

### `scripts/build/linear_pipeline.py`

- **Add manifest generation** to the knowledge-packet build path. The existing `build_knowledge_packet()` function at line 535 returns rendered markdown; either extend it to ALSO produce a manifest JSON, or add a parallel function `build_wiki_manifest()` that the v7 writer phase calls separately.
- **Wire `{WIKI_MANIFEST}` template variable** into `writer_context()` (line 1803) so the renderer fills the new template slot.
- **Update `review_context()`** (around line 2224) to pass the manifest to the new wiki-coverage reviewer pass (it currently doesn't have wiki content in scope — you flagged this).
- **Wire the deterministic gate** as a hard sub-gate that runs BEFORE aggregate QG. Pipeline calls `wiki_coverage_gate.check(...)` after artifacts are produced; if FAIL, the module hard-fails before review.

### `scripts/build/v7_build.py`

- **Add manifest generation step** in the writer phase (around line 291 where `build_knowledge_packet` is called). The manifest is generated once per module and passed to both writer (as template input) and reviewer (as evaluation input).

### `scripts/config.py`

- **Add new section** `# WIKI COVERAGE` near the immersion policies (which already use the SSOT pattern).
- **Threshold values** (placeholders; calibrate empirically in a follow-up Phase B-style replay):
  - `WIKI_COVERAGE_HARD_FAIL = True`
  - `WIKI_COVERAGE_MIN_PCT_BY_LEVEL = {"a1": 0.80, "a2": 0.80, ...}`
  - Optional: per-obligation-type stricter requirements (e.g. all `contrast_pair` L2 errors MUST be covered, no threshold)

---

## Phase 2 rebuild test (anti-degradation)

After all code lands and tests pass, **before opening the PR**, run one V7 build on `a1/my-morning` with the new pipeline and compare:

```bash
# Baseline (current main, before this branch) — already on disk
curriculum/l2-uk-en/a1/my-morning/module.md  # 153 lines, 0/6 L2 errors addressed

# New build (this branch's pipeline)
# NOTE: do NOT run v7_build.py yourself — surface to user for execution
# Instead: write a script `scripts/audit/measure_wiki_coverage.py` that takes
# a wiki page + a module.md (existing on disk) and reports coverage statistics
# Then run it on the CURRENT my-morning module to confirm the parser sees
# the same 0/6 coverage you'd expect, validating the parser before any rebuild
```

If the parser-side measurement on the existing my-morning correctly identifies 0/6 L2 errors covered, you've validated the parser is calibrated against the baseline. The actual rebuild on a1/my-morning is a USER-RUN step per CLAUDE.md ("BUILDS — NEVER RUN, ONLY SUGGEST"). Suggest the user run it after PR merge; report measurement of existing baseline only.

**Include in PR body:** before-state coverage report (0/6 L2 errors, 1/5 sequence steps for my-morning) using your new measurement script. This proves the parser works end-to-end on real content.

---

## Numbered steps (mandatory checklist)

1. **Worktree setup:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian && \
   git worktree add -b codex/wiki-obligations-manifest-2026-05-13 .worktrees/dispatch/codex/wiki-obligations-manifest-2026-05-13 origin/main
   ```

2. **Read first, change second.** Read these files end-to-end before editing:
   - `scripts/build/phases/linear-write.md` (template; understand the variable substitution pattern)
   - `scripts/build/linear_pipeline.py:535-580` (build_knowledge_packet); `:1803-1850` (writer_context); `:2224-2240` (review_context); `:2610-2630` (QG_DIMS coverage check)
   - `scripts/build/v7_build.py:280-320` (writer phase invocation)
   - `scripts/build/phases/linear-review-dim.md` (existing reviewer prompt shape)
   - `scripts/common/thresholds.py:49-56` (QG_DIMS — confirm you understand the invariant)
   - 5+ wiki pages in `wiki/pedagogy/a1/` to discover heading variants
   - `wiki/pedagogy/a1/my-morning.md` end-to-end (the empirical baseline)
   - `curriculum/l2-uk-en/a1/my-morning/module.md` (the broken output you're enforcing against)

3. **Implement in order** to keep the diff coherent:
   a. `scripts/build/phases/wiki_manifest.py` + tests (parser is the foundation)
   b. `scripts/audit/wiki_coverage_gate.py` + tests
   c. `scripts/build/phases/linear-review-wiki-coverage.md` (reviewer prompt)
   d. `scripts/build/phases/linear-write.md` edits (template restructure)
   e. `scripts/build/linear_pipeline.py` wiring
   f. `scripts/build/v7_build.py` wiring
   g. `scripts/config.py` SSOT entries
   h. Integration test in `tests/test_linear_pipeline.py`

4. **Test suite:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/wiki-obligations-manifest-2026-05-13 && \
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/test_wiki_manifest.py tests/test_wiki_coverage_gate.py tests/test_linear_pipeline*.py -x
   ```
   Quote final summary line raw.

5. **Lint:**
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check \
     scripts/build/phases/wiki_manifest.py \
     scripts/audit/wiki_coverage_gate.py \
     scripts/build/linear_pipeline.py \
     scripts/build/v7_build.py \
     scripts/config.py \
     tests/test_wiki_manifest.py \
     tests/test_wiki_coverage_gate.py
   ```
   Quote final line raw.

6. **Baseline measurement on existing my-morning.** Run your measurement script on `curriculum/l2-uk-en/a1/my-morning/module.md` against `wiki/pedagogy/a1/my-morning.md`. Capture the before-state in `audit/wiki-coverage-baseline-2026-05-13/REPORT.md` (or .html per #M-2 since it's ai→human). Should show ~0/6 L2 errors, 1/5 sequence steps, 0 phonetic rules covered. If your parser shows materially different numbers, dig in — either the parser is wrong or my framing's empirical baseline was wrong; surface the discrepancy in the PR body either way.

7. **Commit** with conventional message: `feat(wiki-obligations): manifest extractor + prompt restructure + reviewer pass + coverage gate`. Body should reference this brief, the channel thread IDs, and the baseline measurement.

8. **Push:** `git push -u origin codex/wiki-obligations-manifest-2026-05-13`.

9. **Open PR** via `gh pr create`. Body must include:
   - Link to channel thread (your own design proposal in round 1 + 2)
   - Baseline measurement before/after (parser on existing my-morning)
   - Confirmation that QG_DIMS is still 5 dimensions (quote grep)
   - Per-file rationale (this brief's §"Files to create/edit" sections work as the outline)
   - Suggested user-run validation: `python scripts/build/v7_build.py a1 my-morning` then re-run coverage measurement on output

10. **DO NOT auto-merge.** Hand back for orchestrator review.

---

## What blocks the merge

- Tests failing.
- Ruff failing.
- `QG_DIMS` modified (would break the structural invariant).
- Parser fails to extract the 6 known L2 errors from `wiki/pedagogy/a1/my-morning.md`.
- DEFERRED hatch reintroduced anywhere.
- Writer prompt's Knowledge Packet position unchanged (must move from line 1254 to top).
- Threshold values hard-coded outside `scripts/config.py` (SSOT violation).
- Baseline measurement report missing or claims improvement before any rebuild has happened (the PR ships infrastructure, not new content).

---

## Pre-submit checklist (per AGENTS.md:11-26)

- [ ] `.python-version` unchanged
- [ ] `.yamllint` and `.markdownlint.json` unchanged
- [ ] No `status/*.json` or `audit/*-review.md` files in diff (the baseline measurement report goes under `audit/wiki-coverage-baseline-2026-05-13/`, that path is expected)
- [ ] No `sys.executable` — use `.venv/bin/python`
- [ ] No `@pytest.mark.skip` with empty `pass` bodies
- [ ] No assertion-weakening
- [ ] Every changed file directly related to wiki obligations / prompt restructure / coverage enforcement
- [ ] Total files changed < 20
- [ ] No `NameError` / `KeyError` / `ImportError` on import

---

## Anti-pattern catalog

- ❌ Reintroducing a `DEFERRED` clause anywhere. The point of this design is the writer cannot defer.
- ❌ Adding a 6th `QG_DIMS` dimension (you flagged this is structurally invasive).
- ❌ Tag-audit as the primary gating mechanism. Tags are trace metadata; the deterministic gate compares OUTPUT STRUCTURE to MANIFEST STRUCTURE.
- ❌ Frontmatter-as-source-of-truth for obligations. The wiki body is the source; parse from the body. Manual frontmatter annotation is the parser-fallback only.
- ❌ Running the V7 build yourself (`v7_build.py a1 my-morning`). That's a USER-RUN step. Your job is to ship the parser + gate + reviewer + prompt restructure; the user verifies via rebuild.
- ❌ Calibrating threshold values empirically in this PR. Phase B-style replay calibration is follow-up work; ship placeholder thresholds in `config.py` with calibration noted as TODO.
- ❌ Reformatting unrelated regions of touched files.

---

## Related

- Decision discussion: `ab channel tail wiki-enforcement-2026-05-13 --thread 03b423305969482f84e46d574388297a` (your round 1 + 2) and `--thread 65fb2ccb4fd44dcc91ec2024a1c2976e` (Gemini + Claude)
- Card 1 (just merged, related infrastructure): `docs/decisions/2026-05-13-immersion-gate-tab-aware-structural.md` (structural gates landed via Phase A + B)
- Card 2-REVISED (PROPOSED, downstream): `docs/decisions/pending/2026-05-13-writer-split-by-tab.md` — the manifest you're shipping becomes the shared cross-tab contract if Card 2 lands
- Wiki structure reference: `wiki/pedagogy/a1/my-morning.md` (canonical example of all 4 obligation types present)
- Empirical baseline (broken output): `curriculum/l2-uk-en/a1/my-morning/module.md`
- Lesson Contract authority: `docs/lesson-contract.md` (4-tab structure that obligations get distributed across)
