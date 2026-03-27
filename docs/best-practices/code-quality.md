# Code Quality Best Practices

> **Scope:** Python scripts in `scripts/`, infrastructure tooling, and pipeline code.

---

## Python Environment

**Always use `.venv/bin/python`.**

```bash
# ✅ Correct
.venv/bin/python scripts/build/v6_build.py a1 1
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/sounds-letters-and-hello.md

# ❌ Wrong
python3 scripts/build/v6_build.py a1 1   # missing deps
python scripts/build/v6_build.py a1 1    # wrong version
```

**Why:** The venv uses pyenv Python 3.12.8 compiled with `--enable-loadable-sqlite-extensions` for sqlite-vec. Homebrew Python will silently fail on vector search.

If recreating the venv:
```bash
rm -rf .venv && ~/.pyenv/versions/3.12.8/bin/python -m venv .venv
```

---

## Script Hierarchy

| Script | Use for | Status |
|--------|---------|--------|
| `scripts/build/v6_build.py` | All new builds | **Current (V6)** |
| `scripts/build/dispatch.py` | LLM subprocess dispatch | **Current** |
| `scripts/build/enrich.py` | Deterministic enrichment | **Current** |
| `build_module_v5.py` | Legacy v5 pipeline | **RETIRED** — do not use |
| `pipeline_v5.py` | Legacy v5 phases | **RETIRED** — do not use |
| `build_module.py` | Legacy v4 pipeline | **RETIRED** — do not use |

Always use V6 (`scripts/build/v6_build.py`). Legacy scripts remain for reference only.

---

## Modern CLI Tools

Use fast replacements, not legacy POSIX tools:

| Task | Use | Not |
|------|-----|-----|
| Search content | `rg` (ripgrep) | `grep` |
| Find files | `fd` | `find` |
| Read files | `bat` | `cat` |
| Edit in-place | `sd` | `sed` |
| Parse YAML | `yq` | custom scripts |
| Parse JSON | `jq` | custom scripts |

---

## Error Handling Principles

### Graceful degradation, not crash
A bad plan file for one module should not abort the entire batch:

```python
# ✅ Correct
try:
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}
except yaml.YAMLError as e:
    log(f"  WARNING — plan YAML parse error for {slug}, skipping: {e}")
    return  # skip this module, continue batch

# ❌ Wrong
plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))  # crashes entire batch
```

### Fix source, not symptoms
When a bug appears: find the root cause and fix the process/tool, not the output.
- Bad: manually fix 9 meta files
- Good: add meta health check so pipeline auto-heals, then fix the prompt that caused bad metas

### Don't retry identical failures
If an API call or test fails, don't wait and retry the same action. Consider alternative approaches or ask the user.

---

## State File Conventions

### v5 state file
`state-v5.json` in each module's orchestration directory tracks phase progress.

### Phase names (v5)
v5 phases: `research`, `discover`, `sandbox`, `content`, `activities`, `validate`, `review`, `mdx`.

### State schema
```json
{
  "track": "bio",
  "slug": "danylo-apostol",
  "mode": "v5",
  "phases": {
    "research": {"status": "complete", "ts": "2026-02-19T00:00:00Z"},
    "content": {"status": "complete", "ts": "2026-02-19T00:10:00Z"}
  }
}
```

Always include: `status`, `ts`. Add `mode`, `note`, `task_id` as needed for observability.

---

## Delimiter Extraction

Use `_extract_delimiter()` from `pipeline_lib.py` for all structured output parsing:

```python
def _extract_delimiter(text: str, start_tag: str, end_tag: str) -> str | None:
    if start_tag not in text or end_tag not in text:
        return None
    s = text.index(start_tag) + len(start_tag)
    e = text.index(end_tag)
    return text[s:e].strip()
```

Never use regex for delimiter extraction — exact string matching is more reliable.

---

## YAML Safety

### Always use `yaml.safe_load()`
Never `yaml.load()` — security risk with arbitrary objects.

### Wrap all YAML loads in try/except
```python
try:
    data = yaml.safe_load(path.read_text("utf-8")) or {}
except yaml.YAMLError as e:
    log(f"WARNING — YAML parse error: {e}")
    return {}
```

### Quoting in plan/meta YAML
Strings containing colons followed by content must be single-quoted:
```yaml
# ❌ Breaks YAML parser
- Культурна спадщина: "Дід Панас" як бренд добра

# ✅ Safe
- 'Культурна спадщина: "Дід Панас" як бренд добра'
```

---

## Logging Conventions

Use the `log()` function from `build_module_v2.py` — it writes to both stdout and the module's log file.

```python
log("  Phase A: Research saved → slavic-tribes-research.md")
log("  Phase A: Meta outline updated [meta-only] → slavic-tribes.yaml (8 sections)")
log("  Phase A: WARNING — no RESEARCH delimiters in output")
log("  Phase A: FAILED — Gemini dispatch error")
```

Format: `"  Phase {X}: {verb} — {detail}"`. Two-space indent. Status at end.

Status words: `SKIP`, `ADOPT`, `WARNING`, `FAILED`, `DRY-RUN`, `PASS`, `FAIL`.

---

## Path Handling

Always use `pathlib.Path`, never string concatenation:

```python
# ✅
meta_path = CURRICULUM_DIR / ctx.track / "meta" / f"{ctx.slug}.yaml"

# ❌
meta_path = f"{CURRICULUM_DIR}/{ctx.track}/meta/{ctx.slug}.yaml"
```

Use `path.exists()`, `path.read_text("utf-8")`, `path.write_text(content, "utf-8")`.
Always specify encoding explicitly.

---

## Checking Work Before Marking Done

Never mark a phase complete without verifying output:

```python
# ✅ Check output exists and is non-trivial before marking complete
wrote_file = path.exists() and path.stat().st_size > 10
if not wrote_file:
    _mark_phase_v3(ctx, state, phase, "failed")
    return False
_mark_phase_v3(ctx, state, phase, "complete")
```

---

## Security

- No command injection: never pass user strings directly to `subprocess.run()` with `shell=True`
- No SQL injection: use parameterized queries for vocabulary database
- No hardcoded credentials or API keys
- Sensitive paths: never log full file contents, only file names and sizes
