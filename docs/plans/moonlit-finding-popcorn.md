# Plan: Integrate Plan Review + Content Review + Friction into Dashboard

## Context

Three types of quality data exist on disk but are invisible to the dashboard:

1. **Plan reviews** — `audit/{slug}-plan-review.md` with PASS/NEEDS FIXES/FAIL verdicts. Exist for A1 (52P/12NF), A2 (69P/6NF/1F), B1 (56P/44NF), C1 (3P/103NF/18F). Dashboard shows these modules as "red" because it only checks audit gates, not plan review status.

2. **Content reviews** — `review/{slug}-review.md` with scores (X/10) and PASS/FAIL. Partially tracked: `has_review` boolean exists in `_scan_track()`, but scores and verdicts aren't exposed to the grid view. Only visible in quality.html Reviews tab (aggregate level).

3. **Orchestration friction** — `orchestration/*/phase-*-friction-*.md` files logging build issues, self-corrections, constraint violations. ~300+ files exist. Dashboard shows orchestration file list but doesn't parse friction data.

## Changes

### 1. Backend: `scripts/api/dashboard_router.py` — `_scan_track()`

**Add plan review detection** (after line 127, near existing review detection):

```python
# Plan review (from /plan-review skill)
plan_review_file = track_dir / "audit" / f"{slug}-plan-review.md"
has_plan_review = plan_review_file.exists()
plan_review_verdict = None
if has_plan_review:
    try:
        text = plan_review_file.read_text(errors="replace")
        verdict_match = re.search(r"\*\*Verdict:\*\*\s*(PASS|NEEDS FIXES|FAIL)", text)
        if verdict_match:
            plan_review_verdict = verdict_match.group(1)
    except Exception:
        pass
```

**Add content review score extraction** (extend existing review detection at line 124):

```python
review_score = None
review_verdict = None
if has_review:
    try:
        text = review_file.read_text(errors="replace")
        score_match = re.search(r"Overall Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", text, re.IGNORECASE)
        status_match = re.search(r"\bStatus:\s*(PASS|FAIL)\b", text, re.IGNORECASE)
        if score_match:
            review_score = float(score_match.group(1))
        if status_match:
            review_verdict = status_match.group(1).upper()
    except Exception:
        pass
```

**Add friction count** (from orchestration dir):

```python
friction_count = 0
if orch_dir.exists():
    friction_count = len(list(orch_dir.glob("*friction*")))
```

**Update `mod` dict** to include new fields:

```python
"has_plan_review": has_plan_review,
"plan_review_verdict": plan_review_verdict,
"review_score": review_score,
"review_verdict": review_verdict,
"friction_count": friction_count,
```

Update `files` dict: add `"plan_review": has_plan_review`

**Update stats aggregate** (~line 158):

```python
"plan_reviewed": sum(1 for m in modules if m.get("has_plan_review")),
"plan_pass": sum(1 for m in modules if m.get("plan_review_verdict") == "PASS"),
"plan_needs_fixes": sum(1 for m in modules if m.get("plan_review_verdict") == "NEEDS FIXES"),
"plan_fail": sum(1 for m in modules if m.get("plan_review_verdict") == "FAIL"),
```

### 2. Backend: `scripts/api/state_router.py` — `_compute_review_coverage()`

Extend the existing function (~line 571) to also scan plan review files alongside content reviews. Add to each track's output:

```python
"plan_reviewed": plan_reviewed_count,
"plan_pass": plan_pass_count,
"plan_needs_fixes": plan_nf_count,
"plan_fail": plan_fail_count,
```

### 3. Frontend: `playgrounds/audit-dashboard.html`

**Grid cells** (line 307-328 `renderModuleGrid`):
- Add plan review badge: bottom-left corner dot
  - Green = PASS, Orange = NEEDS FIXES, Red = FAIL
  - `<div class="plan-badge" title="Plan: PASS"></div>` (similar to review-badge/qa-badge pattern)
- Update tooltip to include plan review verdict

**Side panel** (line 343-464 `renderModulePanel`):
- Add "Plan Review" row after status badge, before word count
- Show verdict with color-coded badge: `<span class="status-badge pass">Plan: PASS</span>`
- If content review exists, show score: `Review: 9.2/10 PASS`
- If friction files exist, show count: `Build friction: 2 events`

**Legend** (line 197-207):
- Add plan review badge to legend

**CSS additions**:
```css
.module-cell .plan-badge {
  position: absolute; bottom: -3px; left: -3px;
  width: 8px; height: 8px; border-radius: 50%;
  border: 1px solid var(--bg2);
}
.plan-badge.plan-pass { background: var(--green); }
.plan-badge.plan-needs-fixes { background: #f0883e; }
.plan-badge.plan-fail { background: var(--red); }
```

### 4. Frontend: `playgrounds/quality.html`

**Reviews tab** (line 224-258 `loadReviews`):
- Add columns: "Plan Reviewed", "Plan Pass", "Plan NF", "Plan Fail"
- Color plan stats: green for pass, orange for needs-fixes, red for fail
- The existing "Reviewed" column stays (content reviews)

## Files to modify

1. `scripts/api/dashboard_router.py` — plan review + content review score + friction in `_scan_track()`
2. `scripts/api/state_router.py` — plan review stats in `_compute_review_coverage()`
3. `playgrounds/audit-dashboard.html` — plan badge on grid + details in side panel
4. `playgrounds/quality.html` — plan review columns in Reviews tab

## Verification

1. Check API returns new fields:
   ```bash
   curl -s http://localhost:8765/api/dashboard/track/a1 | python3 -c "
   import json,sys; d=json.load(sys.stdin)
   m=d['modules'][0]; print('plan_review:', m.get('has_plan_review'), m.get('plan_review_verdict'))
   print('review_score:', m.get('review_score'), m.get('review_verdict'))
   print('friction:', m.get('friction_count'))
   print('stats:', {k:v for k,v in d['stats'].items() if 'plan' in k})
   "
   ```
2. Check review coverage includes plan reviews:
   ```bash
   curl -s http://localhost:8765/api/state/review-coverage | python3 -m json.tool
   ```
3. Open audit-dashboard.html — verify plan review badges on grid cells
4. Open quality.html → Reviews tab — verify plan review columns appear
