# Dispatch brief: H2 — full-text Antonenko + UA-GEC calque annotations

**Agent:** Claude headless (claude-opus-4-7)
**Mode:** `--mode danger` (worktree-isolated)
**Base branch:** `main`
**Task ID:** `h2-antonenko-fulltext-uagec-2026-05-17`

## Why this work — what H1 missed and what H2 fixes

H1 (PR #2046) collapsed F1 across all models because the cite-or-forbid
rule lacked evidence anchors for the calibration set's russianisms.
Diagnosis: retrieval only queried `style_guide` (342 structured entries
~50% of Antonenko book). Two evidence sources were not wired in:

1. **Full-text Antonenko** — the OTHER 50% of the book (169 page-chunks
   of prose with embedded rules, examples, discussions) is in the
   `textbooks` table under source `antonenko-davydovych-yak-my-hovorymo`.
   `mcp__sources__search_text` would surface it.

2. **UA-GEC annotated corpus** — `data/ua-gec/data/gec-only/{train,test}/annotated/`
   contains **4,162 .ann files** with `{error=>correct:::error_type=Tag}`
   inline annotations. Tag counts (verified by grep):
   - `F/Calque`: **2,397** annotations (russian-pattern calques)
   - `F/Style`: **3,725** (register/style improvements, many russianism-adjacent)
   - `F/Collocation`: **459** (unnatural pairings)
   - `G/Case`/`G/Gender`: ~6K (russian-pattern grammar)
   - Total useful for russianism detection: ~7K annotation pairs

   Authoritative source — Grammarly Ukraine team, professional
   annotators, MIT-licensed, gold standard for Ukrainian error
   correction.

## Hypothesis H2

Adding both evidence sources will:
- Restore F1 to ≥ baseline (≥0.83 for opus-xhigh+mcp) — H1's cite-or-forbid rule remains, but now flags have real evidence to cite.
- Preserve H1's case_acc=true for the greeting case (FP elimination).
- For dirty cases where UA-GEC has matching calque annotations, the model now sees: "this exact phrase pattern was annotated as F/Calque in N learner essays, correction was X" — strongest possible evidence anchor.

## Deterministic claims (#M-4)

| Claim | Required evidence |
|---|---|
| "retrieve_evidence reaches all 4 sources" | Print the rendered prompt for `cal_dirty_email_calques` — must show non-empty Antonenko full-text section AND non-empty UA-GEC section |
| "6 H2 cells ran successfully" | `find audit/2026-05-17-judge-calibration-h2 -name '*.json' \| wc -l` returns 6 |
| "0 cells errored" | grep `"errors": []` matches 6 |
| "Comparison written" | `audit/2026-05-17-judge-calibration-h2/COMPARISON.md` contains a 3-column table (baseline / H1 / H2) for each of 6 cells |
| "Tests pass + ruff clean" | raw pytest summary + ruff final line |
| "PR opened, not merged" | raw `gh pr view --json url,state` line, OPEN |

## Numbered execution steps

### 1. Worktree
Dispatch system creates `.worktrees/dispatch/claude/h2-antonenko-fulltext-uagec-2026-05-17/` from main.

### 2. Data symlinks (sparse worktree — three sources now)

```
[ -L data/sources.db ] || { rm -f data/sources.db; ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/sources.db data/sources.db; }
[ -L data/vesum.db ]   || { rm -f data/vesum.db;   ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/vesum.db   data/vesum.db; }
[ -L data/ua-gec ]     || { rm -f data/ua-gec;     ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/ua-gec     data/ua-gec; }
```

Verify:
```
ls -la data/sources.db data/vesum.db data/ua-gec
sqlite3 data/sources.db "SELECT COUNT(*) FROM textbooks WHERE source LIKE 'antonenko-davydovych%'"  # expect: 169
find data/ua-gec/data -name "*.ann" | wc -l  # expect: 4162
```

### 3. Fetch calibration cases

```
git rev-parse origin/pr-2006 >/dev/null 2>&1 || git fetch origin 'refs/pull/2006/head:refs/remotes/origin/pr-2006'
```

### 4. Extend `_judge_eval_lib.py`

`scripts/audit/_judge_eval_lib.py` already has `retrieve_evidence()`
from H1 (returns Antonenko-structured, heritage, russian-shadow,
vesum-unknown). ADD two helpers and wire them in:

#### 4a. Add `_antonenko_fulltext_search(text, k=4)` helper

Query `textbooks` table for chunks where `source` matches
`antonenko-davydovych-yak-my-hovorymo` AND the chunk body contains any
2-4 word substring of `text`. Use FTS5 if `textbooks_fts` exists,
otherwise plain LIKE with bounded scan. Return list of `{chunk_id,
page, snippet}` dicts, snippet ≤200 chars per hit, max k hits.

```python
def _antonenko_fulltext_search(text: str, k: int = 4) -> list[dict]:
    """Search the full-text Antonenko book corpus (169 page chunks) for
    phrases overlapping with the input text. Complements the 342 keyed
    headwords in style_guide."""
    # implementation: tokenize text → 2-4-gram phrases → FTS5 MATCH or LIKE
    # against textbooks WHERE source LIKE 'antonenko-davydovych%'
    # return [{"page": ..., "snippet": ...}, ...]
```

#### 4b. Add `_ua_gec_calque_search(text, k=4)` helper

Pre-load a small in-memory index (only on first call) of all
`{error=>correct:::error_type=Tag}` triples from
`data/ua-gec/data/{gec-fluency,gec-only}/{train,test}/annotated/*.ann`
where `Tag IN ('F/Calque', 'F/Style', 'F/Collocation', 'G/Case', 'G/Gender')`.

For each `text` input: tokenize, find triples whose `error` field
shares ≥2-word overlap with input. Return top-k as
`{"error": "...", "correct": "...", "tag": "F/Calque", "source": "ua-gec"}`.

Implementation budget: ≤120 LOC including index load + search. Use a
module-level lazy-loaded dict keyed by error tokens.

#### 4c. Wire both into `retrieve_evidence`

```python
def retrieve_evidence(text: str) -> dict[str, Any]:
    return {
        "antonenko": retrieve_antonenko(text),                      # 342 structured
        "antonenko_fulltext": _antonenko_fulltext_search(text),     # 169 page-chunks  NEW
        "heritage_attested": _heritage_check(text),
        "russian_shadow_signal": _russian_shadow_check(text),
        "vesum_unknown_tokens": _vesum_unknown(text),
        "ua_gec_calques": _ua_gec_calque_search(text),              # 7K annotations    NEW
    }
```

#### 4d. Update `build_judge_prompt` to render new sections

Two new sections in the prompt (preserve all H1 sections too):

```
### Antonenko-Davydovych full-book prose hits (in addition to structured headwords above)
<list of snippets with page refs; if empty: "(no prose hits)">

### UA-GEC corpus — similar errors flagged by professional annotators
<list of error→correct pairs with tag; if empty: "(no UA-GEC matches)">
```

The "cite-or-forbid" rule expands: a flag may now cite an Antonenko
prose snippet OR a UA-GEC annotation as evidence. Update the
`evidence_type` enum accordingly:

```
evidence_type ∈ {antonenko_headword, antonenko_prose, ua_gec_calque,
                 vesum_unknown, russian_shadow}
```

### 5. Eyeball check — render the prompt for the dirty case that broke H1

```
# venv symlinked into worktree by delegate.py
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts/audit')
from _judge_eval_lib import build_judge_prompt, retrieve_evidence, pull_calibration_cases
cases = pull_calibration_cases()
dirty = next(c for c in cases if c['prompt_id'] == 'cal_dirty_email_calques')
ev = retrieve_evidence(dirty['output_text'])
print('=== retrieve_evidence summary ===')
print({k: (len(v) if hasattr(v, '__len__') else bool(v)) for k, v in ev.items()})
print()
print('=== rendered prompt ===')
print(build_judge_prompt(dirty['output_text'], ev))
"
```

**Gate:** if `antonenko_fulltext` and `ua_gec_calques` both return 0
hits on `cal_dirty_email_calques`, the retrieval is too narrow — fix
the n-gram window OR the overlap threshold before running the
6-cell matrix. Iterate on the helpers until at least one of the two
returns ≥1 hit on at least 3 of the 8 dirty cases. Document the
threshold choice in a code comment.

### 6. Tests + lint

```
# venv symlinked into worktree by delegate.py
.venv/bin/python -m pytest tests/audit/ -q
.venv/bin/ruff check scripts/audit/_judge_eval_lib.py scripts/audit/judge_calibration_matrix.py
```

Add ONE new test in `tests/audit/test_judge_eval_lib_h2.py`:
- Given `text = "Прошу повістку дня"` (known F/Calque in UA-GEC), `_ua_gec_calque_search(text)` returns ≥1 hit.
- Given `text = "Доброго дня"`, `_ua_gec_calque_search(text)` returns 0 hits (it's the canonical greeting).

### 7. Run the 6 H2 cells

**New out-dir:** `audit/2026-05-17-judge-calibration-h2/`

Same 6 cells as H1 (per-config filter; harness will skip unsupported combos):

```
# venv symlinked into worktree by delegate.py
.venv/bin/python scripts/audit/judge_calibration_matrix.py \
  --out-dir audit/2026-05-17-judge-calibration-h2 \
  --families anthropic,openai,google,xai \
  --models claude-opus-4-7,claude-haiku-4-5-20251001,gpt-5.5,gemini-3.1-pro-preview,grok-4.3 \
  --harnesses native_cli,hermes \
  --efforts xhigh,high,medium,default \
  --mcp-states with_mcp,without_mcp \
  --max-parallel 2
```

The 6 cells we expect (skipping unsupported combos):
1. anthropic/claude-opus-4-7/native_cli/xhigh-with_mcp
2. anthropic/claude-opus-4-7/native_cli/high-without_mcp
3. anthropic/claude-haiku-4-5-20251001/native_cli/high-without_mcp
4. openai/gpt-5.5/native_cli/medium-with_mcp
5. google/gemini-3.1-pro-preview/native_cli/default-with_mcp
6. xai/grok-4.3/hermes/xhigh-with_mcp

If the harness produces more than 6 cells with the broad filters above,
narrow with explicit `--models` × `--efforts` per dispatch. Target is 6.

### 8. Build the 3-way comparison

Write `audit/2026-05-17-judge-calibration-h2/COMPARISON.md`:

```markdown
# H2 vs H1 vs Baseline (3-way A/B/C)

## Headline
<2-3 sentences: did H2 restore F1 vs baseline? did greeting FP stay fixed?>

## Per-cell deltas

| Cell | Baseline F1 | H1 F1 | H2 F1 | ΔH2-Base | Baseline acc | H1 acc | H2 acc | greeting (B/H1/H2) |

## Evidence anchor usage
For each of the 6 cells, count how many of the H2 verdicts cited each evidence type
(antonenko_headword | antonenko_prose | ua_gec_calque | vesum_unknown | russian_shadow).
This tells us which retrieval source carried each model's flags.

## Surprises / negative results / model failures

## Recommendation for next iteration
```

Read prior cells from `audit/2026-05-17-judge-calibration-matrix/` (baseline) and `audit/2026-05-17-judge-calibration-h1/` (H1) and current from `audit/2026-05-17-judge-calibration-h2/`. Use `jq` for all reads, quote raw output in the report.

### 9. Commit

```
git add scripts/audit/_judge_eval_lib.py scripts/audit/judge_calibration_matrix.py tests/audit/test_judge_eval_lib_h2.py audit/2026-05-17-judge-calibration-h2/
git commit -m "$(cat <<'EOF'
feat(audit): H2 — Antonenko full-text + UA-GEC calque retrieval

H1 (PR #2046) collapsed F1 because retrieval only hit Antonenko
structured (342 headwords, ~50% of book). H2 adds two evidence
sources that were on disk but unwired:

1. Antonenko full-book prose (169 page-chunks via textbooks table)
2. UA-GEC F/Calque + F/Style + F/Collocation + G/Case/Gender
   annotations (~7K human-annotated error pairs from Grammarly UA's
   gold-standard MIT-licensed corpus)

cite-or-forbid rule from H1 preserved. evidence_type enum extended.

A/B/C results in audit/2026-05-17-judge-calibration-h2/COMPARISON.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### 10. Push + PR (no auto-merge)

Title: `feat(audit): H2 judge prompt — Antonenko full-text + UA-GEC annotations (6-cell A/B/C)`

Body must include:
- 1-paragraph summary of A/B/C result
- Link to COMPARISON.md
- Test plan checklist (pytest pass / ruff clean / manual REPORT.html review / COMPARISON.md read)

**Do NOT auto-merge.**

## Hard rules

- Do NOT modify baseline (`audit/2026-05-17-judge-calibration-matrix/`) or H1 (`audit/2026-05-17-judge-calibration-h1/`) cells — they are the A and B halves of the comparison.
- Do NOT touch `eval/russianism/calibration-cases.jsonl` — A/B/C requires SAME inputs.
- If retrieval iteration in step 5 takes more than 30 min, STOP and commit what works — partial-evidence H2 is still informative.
- Hard timeout 90 min wall-time. If you're at 75 min with cells incomplete, commit what landed + document the gap in COMPARISON.md.
- NO auto-merge.
- NO new effort tiers, NO new models, NO scope creep — exactly the 6 cells listed.

## What you do NOT do

- Do NOT ingest UA-GEC into sources.db (that's a separate engineering decision — for H2 we read .ann files directly with a lazy in-memory index).
- Do NOT use Karavansky (separate decision needed about source data location — out of scope).
- Do NOT change the H1 helpers (heritage, russian-shadow, vesum-unknown, antonenko-structured) — only ADD the two new helpers and wire them in alongside.
- Do NOT change calibration_matrix.py beyond what step 4c-d requires.
