# Plan: V4 Visibility Across All Monitoring Dashboards

## Context

API now returns `pipeline_version`, `needs_rebuild`, and `build_status` per module. But all 5 dashboards that render modules are v3-only — v4 modules show as blank/gray or use wrong phase labels. The user wants every module-displaying dashboard to clearly show whether a module is v4 or obsolete (v3/unbuilt).

## Shared Pattern

Every dashboard that renders modules will:
1. Check `mod.pipeline_version` (available in API responses)
2. **V4 modules**: render normally with bright colors
3. **Non-v4 modules**: render with `.obsolete` CSS class (opacity: 0.4) to visually signal "needs rebuild"
4. Show pipeline version in tooltips/detail panels

## Files Modified

### 1. `playgrounds/progress.html` — Phase chips

**Problem**: `chipClass()` / `chipLabel()` / `chipTitle()` only understand v3 phases (A, B, audit, D).

**Changes**:
- `chipClass(mod)`: if `pipeline_version === 'v4'`, check named phases (research → content → validate → review → mdx); else keep v3 logic
- `chipLabel(mod)`: v4 labels: `✓` (review/mdx done), `Va` (validate), `C` (content), `R` (research), `·`
- `chipTitle(mod)`: show v4 phase names for v4 modules
- Add `.obsolete` class to non-v4 chips (opacity dim)
- Add CSS: `.chip-v4-research`, `.chip-v4-content`, `.chip-v4-validate`, `.chip-v4-pass`
- Update legend: add v4 states + "Obsolete (v3)" grayed entry
- Topbar: "v3 pipeline state" → "Pipeline state" + v4 migration % (fetch `/api/state/pipeline-versions`)
- Stats bar: add "V4" stat card

### 2. `playgrounds/audit-dashboard.html` — Module grid cells + side panel

**Problem**: Module cells only show pass/fail/content-complete status. No pipeline version indicator. Side panel shows "Orchestration Phases" from v3 orchestration files.

**Changes**:
- Module cells: add `.obsolete` class for non-v4 modules (dim the cell)
- Add small "v4" badge overlay on v4 module cells (like existing `.review-badge`)
- Side panel: show `pipeline_version` in module info section
- Side panel: when v4, show v4 phases from `mod.v4_phases` instead of orchestration file listing
- API source: `/api/dashboard/track/{trackId}` already returns `pipeline_version` per module

### 3. `playgrounds/track-health.html` — Phase timeline in inspector

**Problem**: Phase labels hardcoded as `{A: 'Research', B: 'Content', C: 'Activities', audit: 'Audit', D: 'Review', E: 'Repair', F: 'Final'}`. V4 modules use different phase names.

**Changes**:
- Phase timeline: detect `pipeline_version` from module data, switch phase list:
  - v4: `{research: 'Research', discover: 'Discover', content: 'Content', activities: 'Activities', validate: 'Validate', review: 'Review', mdx: 'MDX'}`
  - v3: keep existing `{A, B, C, audit, D, E, F}`
- Module list items: add dim styling for non-v4 modules
- Health overview: add v4 migration % to the track health cards
- API source: `/api/state/module/{trackId}/{num}` already returns `pipeline_version` and v4 phases

### 4. `playgrounds/curriculum-dashboard.html` — Module table

**Problem**: Status dots show pass/fail but no pipeline version.

**Changes**:
- Add `pipeline_version` column or small "v4"/"v3" label next to module name
- Non-v4 rows: add `.obsolete` class (dim the row)
- Detail panel: show pipeline version in module info card

### 5. `playgrounds/quality.html` — Weak modules table

**Problem**: No pipeline version info on weak module rows.

**Changes**:
- Add `.tag-v3` badge (orange) for non-v4 modules in the tags column (alongside existing `.tag-audit`, `.tag-research`, `.tag-words`)
- This makes it easy to see which weak modules are also obsolete

### 6. `playgrounds/index.html` — Home page

**Changes**:
- Progress card description: "v3 pipeline state" → "Pipeline state across all tracks. V4 migration progress."
- Stats row: fetch `/api/state/pipeline-versions`, add stat card showing v4 count + pct_v4%
- Progress stat text: prepend v4 count

## Shared CSS (added to each file)

```css
.obsolete { opacity: 0.4; }
.v4-badge {
  position: absolute; top: -2px; right: -2px;
  background: var(--green); color: #000;
  font-size: 7px; padding: 1px 2px; border-radius: 2px;
  font-weight: 700;
}
```

## Verification

1. `localhost:8765/progress.html` → expand a1, v4 modules (my-world-objects, the-cyrillic-code-i) show bright chips, all others dimmed
2. `localhost:8765/audit-dashboard.html` → expand a1, v4 cells have green "v4" badge, v3 cells dimmed; click v4 module → side panel shows v4 phases
3. `localhost:8765/track-health.html` → click v4 module → phase timeline shows Research/Discover/Content/.../MDX; v3 module → shows A/B/C/audit/D/E/F
4. `localhost:8765/curriculum-dashboard.html` → v4 label visible, non-v4 rows dimmed
5. `localhost:8765/quality.html` → weak modules show "v3" tag when applicable
6. `localhost:8765/` → stats row shows v4 migration stat
