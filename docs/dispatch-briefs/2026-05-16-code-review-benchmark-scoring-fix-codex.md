# Dispatch — code-review benchmark: semantic matching + raw response persistence

**Agent:** codex
**Model:** gpt-5.5
**Effort:** medium
**Mode:** danger (worktree)
**Base:** origin/main

## Why

PR #2041 landed the harness + 3-case corpus + smoke validation. Empirical run of the smoke surfaced TWO diagnosability gaps:

### Gap 1 — strict tuple matching gives 0% F1 to semantically correct findings

Current scorer requires `(id, severity, category, location-file)` exact match. Models emit valid findings with different ids/severities than gold:

| Gold (pr-2025) | Model emission | Why scorer rejects |
|---|---|---|
| `arg-max` HIGH security | `prompt-leaked-in-process-argv` MED security | Different id; severity diff |
| `host-flag` LOW security | `unauthenticated-non-loopback-bind` HIGH security | Different id; severity HIGH vs LOW |
| `healthz-fork` MED dos-surface | (semantic overlap with `unbounded-request-size`) | Different id; different specific concern |
| `error-envelope` HIGH spec-compliance | (model missed it) | True miss |

The model gets credit only when it happens to use the SAME slug as gold — which is luck. Smoke result "best F1: 30.8% (gpt-5.4-mini)" is a measurement artifact, not a routing signal.

### Gap 2 — raw response not persisted

Per-cell JSON only stores `raw_response_chars` (length). Diagnosing why a model returned `[]` or non-matching findings requires loading the Hermes session JSON at `~/.hermes/sessions/session_*.json` and grep-matching by prompt fingerprint. That's a real diagnosability hole.

## Goal

Two surgical changes:
1. Replace the strict tuple matcher with a **semantic-equivalence matcher** that uses `category + file-location` as primary keys, severity-tolerance of ±1 step, and a fallback `description` text-similarity check.
2. Persist `raw_response` (truncated to 8 KB per finding) in per-cell JSON for direct diagnosis without leaving the audit dir.

Also: extract gold corpus refresh as a follow-up — not in scope here, but file as next-step issue.

## Concrete plan

### Step 1 — git worktree

```bash
git worktree add -b codex/code-review-bench-scoring-2026-05-16 \
  .worktrees/dispatch/codex/code-review-bench-scoring-2026-05-16 origin/main
cd .worktrees/dispatch/codex/code-review-bench-scoring-2026-05-16
```

### Step 2 — implement semantic matcher in `scripts/audit/code_review_benchmark.py`

Find the existing finding-matching function (likely named `match_findings` or similar — `grep -n 'matched_gold_ids\|def match\|def score' scripts/audit/code_review_benchmark.py`).

Replace strict tuple match with:

```python
def find_semantic_match(model_finding, gold_findings, matched_already):
    """
    Find the best gold finding that matches a model finding semantically.
    Returns the gold_id if matched, else None.
    
    Match criteria (in priority order):
    1. category + file-location match → strong match (severity tolerated ±1 step)
    2. category match + description text overlap > 0.4 (token-set Jaccard) → weak match
    3. else no match
    """
    SEVERITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    
    model_category = model_finding.get("category", "").lower()
    model_loc_file = (model_finding.get("location", "") or "").split(":")[0]
    model_sev = SEVERITY_ORDER.get(model_finding.get("severity", "").upper(), 1)
    model_desc_tokens = set(_tokenize(model_finding.get("description", "")))
    
    best = None
    best_score = 0.0
    for gold in gold_findings:
        if gold["id"] in matched_already:
            continue
        gold_category = gold.get("category", "").lower()
        gold_loc_file = (gold.get("location", "") or "").split(":")[0]
        gold_sev = SEVERITY_ORDER.get(gold.get("severity", "").upper(), 1)
        
        # Strong match: same category, same file, severity within ±1
        if (model_category == gold_category 
            and model_loc_file == gold_loc_file 
            and abs(model_sev - gold_sev) <= 1):
            return gold["id"]  # Strong match wins immediately
        
        # Weak match: same category + description text overlap
        if model_category == gold_category:
            gold_desc_tokens = set(_tokenize(gold.get("description", "")))
            jaccard = (len(model_desc_tokens & gold_desc_tokens) 
                       / max(len(model_desc_tokens | gold_desc_tokens), 1))
            if jaccard > 0.4 and jaccard > best_score:
                best = gold["id"]
                best_score = jaccard
    
    return best

def _tokenize(s):
    """Split on whitespace + punctuation, lowercase, drop short tokens + common stopwords."""
    import re
    STOP = {"the","a","an","is","are","of","to","in","on","for","and","or","by",
            "with","this","that","be","as","at","it","from","has","have","not"}
    toks = re.findall(r"\w{3,}", (s or "").lower())
    return [t for t in toks if t not in STOP]
```

Apply this in the scoring loop:

```python
matched = set()
for mf in model_findings:
    gold_id = find_semantic_match(mf, gold_findings, matched)
    if gold_id:
        matched.add(gold_id)
```

### Step 3 — persist raw responses in per-cell JSON

Find where the per-cell JSON is written (search for `model_findings_count` or `raw_response_chars`). Add a `raw_response` field per judgment, truncated to 8000 chars:

```python
RAW_RESPONSE_TRUNCATE = 8000
...
judgment["raw_response"] = raw_response[:RAW_RESPONSE_TRUNCATE] if raw_response else ""
judgment["raw_response_truncated"] = len(raw_response or "") > RAW_RESPONSE_TRUNCATE
```

Keep `raw_response_chars` (the full length pre-truncation) for backward compat.

### Step 4 — also persist parsed `model_findings` list in per-cell JSON

Currently the per-cell JSON has `matched_gold_ids` and `missed_gold_ids` but the parsed `model_findings` (the structured list the model emitted) is lost after scoring. Add it:

```python
judgment["model_findings"] = parsed_model_findings  # the list of dicts post-JSON-parse
```

### Step 5 — update REPORT.md to show match-strength breakdown

Add a column to the leaderboard: `strong-match-count` (count of strong matches per cell) so we can distinguish "model emitted SAME findings as gold" from "model emitted SEMANTICALLY similar but novel-id findings."

### Step 6 — tests

Update `tests/audit/test_code_review_benchmark.py`:

1. `test_semantic_match_strong()` — exact category + file + severity match returns gold_id.
2. `test_semantic_match_severity_tolerance()` — same category + file, severity diff of 1 still matches.
3. `test_semantic_match_severity_too_far()` — same category + file, severity diff of 2 → returns None (no match).
4. `test_semantic_match_description_jaccard()` — same category, different file, but description Jaccard > 0.4 → matches.
5. `test_semantic_match_consumes_gold()` — once a gold finding is matched, subsequent model findings can't double-count it.
6. `test_raw_response_persistence()` — per-cell JSON contains `raw_response` and `model_findings` fields after scoring.

### Step 7 — verify deterministically (#M-4 preamble)

| Claim | Tool + raw output |
|---|---|
| Tests pass | `.venv/bin/pytest tests/audit/test_code_review_benchmark.py -v` final line |
| Lint clean | `.venv/bin/ruff check scripts/audit/code_review_benchmark.py tests/audit/test_code_review_benchmark.py` |
| New scoring exists | `grep -n 'find_semantic_match\|raw_response\|model_findings' scripts/audit/code_review_benchmark.py \| head -20` |

DO NOT re-run the smoke yourself. Orchestrator will do that post-merge as the empirical validation.

### Step 8 — commit, push, PR

```bash
git add scripts/audit/code_review_benchmark.py tests/audit/test_code_review_benchmark.py
.venv/bin/ruff check scripts/audit/code_review_benchmark.py tests/audit/test_code_review_benchmark.py
.venv/bin/pytest tests/audit/test_code_review_benchmark.py -v
git commit -m "fix(audit): semantic finding-matching + raw response persistence in code-review benchmark"
git push -u origin codex/code-review-bench-scoring-2026-05-16
gh pr create --title "fix(audit): semantic finding-matching + raw response persistence" --body "..."  # with raw outputs from step 7
```

**DO NOT auto-merge.**

## Out of scope

- Refreshing the 3-case gold corpus with more comprehensive findings (separate issue)
- Adding LLM-judge as a fallback semantic matcher (could be a future iteration; Jaccard is enough for now)
- Re-running the smoke or the full matrix (orchestrator post-merge)
- Computing semantic similarity via embeddings (too heavyweight; Jaccard suffices for the scale we have)

## Reference

- `scripts/audit/code_review_benchmark.py` — the harness
- `audit/2026-05-17-code-review-benchmark-smoke/REPORT.md` — current biased results
- `~/.hermes/sessions/session_20260516_*.json` — actual model responses (for cross-reference if needed)
