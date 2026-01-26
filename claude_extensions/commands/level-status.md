# /level-status

View status of an entire level from cache files.

## Usage

```bash
/level-status {level}
```

## What This Does

Aggregates all status cache JSON files for a level and displays a summary report. Fast (<5 seconds) because it reads from cache files.

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Generate Fresh Status

Run the status generation script which reads from JSON cache:

```bash
.venv/bin/python scripts/generate_level_status.py ${level}
```

This:
1. Reads all `{level}/status/*.json` cache files
2. Falls back to running audit for modules without cache
3. Generates `docs/{LEVEL}-STATUS.md`

### Step 2: Display Summary

Read and display the generated status file:

```bash
head -50 docs/${LEVEL^^}-STATUS.md
```

### Step 3: Show Key Metrics

Parse and display:

```
Level: {LEVEL} ({total_modules} modules)
Overall: {pass_percentage}% complete

Status breakdown:
  ✅ Passing: {pass_count}/{total} modules
  ❌ Failing: {fail_count}/{total} modules
  📝 Stubs: {stub_count}/{total} modules

{If any failures, list blocking modules:}
Blocking issues ({count} modules):
  - {module}: {issue}
  - {module}: {issue}
  ...

Status file: docs/{LEVEL}-STATUS.md
```

## Example Output

```
Level: B1 (92 modules)
Overall: 96% complete

Status breakdown:
  ✅ Passing: 89/92 modules
  ❌ Failing: 3/92 modules
  📝 Stubs: 0/92 modules

Blocking issues (3 modules):
  - 09-aspect-future: structure
  - 16-motion-verbs-full-system: structure
  - 23-motion-patterns-other-verbs: structure

Status file: docs/B1-STATUS.md
```

## Speed Note

Status generation is fast when caches exist:
- **With cache:** ~0.1s per module (just reads JSON)
- **Without cache:** ~6s per module (runs full audit)

To populate cache for all modules:
```bash
# Audit all modules (slow but builds cache)
for f in curriculum/l2-uk-en/${level}/*.md; do
  .venv/bin/python scripts/audit_module.py "$f"
done
```

## Related Commands

| Command | Purpose |
|---------|---------|
| `/module-status` | View status of single module |
| `/module-fix` | Fix module until all gates pass |
| `npm run status:{level}` | Same as this command |
