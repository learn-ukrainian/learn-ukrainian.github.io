# /module-status

View status of a single module from the audit cache.

## Usage

```bash
/module-status {level} {module_num}
```

## What This Does

Reads the status cache JSON file and displays a formatted status report for a single module. Fast (<1 second) because it reads from cache, not running full audit.

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Resolve Module Path

**For core levels (a1, a2, b1, b2, c1, c2):**
```bash
slug=$(ls curriculum/l2-uk-en/${level}/${num}-*.md 2>/dev/null | head -1 | xargs basename -s .md)
```

**For tracks (b2-hist, c1-bio, c1-hist, lit):**
```bash
slug=$(yq ".levels.\"${level}\".modules[$((num-1))]" curriculum/l2-uk-en/curriculum.yaml)
```

### Step 2: Read Status Cache

```bash
status_file=curriculum/l2-uk-en/${level}/status/${slug}.json
```

If cache file doesn't exist:
```
Status cache not found for ${level}/${slug}

Run audit to generate cache:
  .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/${level}/${slug}.md
```

### Step 3: Parse and Display

Read the JSON cache and format output:

```
Module: {slug}
Level: {level}
Status: {PASS/FAIL} ({blocking_count} blocking issues)

Gates:
  {icon} Meta: {status} - {message}
  {icon} Lesson: {status} - {message}
  {icon} Activities: {status} - {message}
  {icon} Vocabulary: {status} - {message}
  {icon} Naturalness: {score}/10

{If FAIL, list blocking issues:}
Blocking:
  - {issue 1}
  - {issue 2}

Last audit: {last_audit timestamp}
Plan version: {plan_version}
```

### Icons

- `✅` = pass
- `❌` = fail
- `⚠️` = warning
- `ℹ️` = info/skipped

## Example Output

```
Module: 01-how-to-talk-about-grammar
Level: B1
Status: PASS (0 blocking issues)

Gates:
  ✅ Meta: PASS - Valid Structure
  ✅ Lesson: PASS - 2032/1200 (raw: 2520)
  ✅ Activities: PASS - 16/12
  ✅ Vocabulary: PASS - 149/20
  ✅ Naturalness: 9/10 (High)

Last audit: 2026-01-26T15:47:03Z
Plan version: 1.0
```

## Related Commands

| Command | Purpose |
|---------|---------|
| `/level-status` | View status of entire level |
| `/module-fix` | Fix module until all gates pass |
