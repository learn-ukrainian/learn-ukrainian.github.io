# Handoff: Infrastructure Feature Template

Use this template when creating issues for new tools, scripts, or infrastructure work.

## Usage

```bash
gh issue create \
  --title "feat(scope): Brief description of tool/feature" \
  --body-file /tmp/issue-body.md \
  --label "enhancement" \
  --label "infrastructure" \
  --label "agent:claude"
```

---

## Template

```markdown
## Overview

**What**: [Tool/script name and purpose]
**Why**: [Problem it solves / value it provides]
**Assigned to**: [Claude / Gemini]

## Requirements

### Functional Requirements
1. [What the tool must do - be specific]
2. [Input format / expected arguments]
3. [Output format / side effects]

### Non-Functional Requirements
- Performance: [Any speed/memory constraints]
- Compatibility: [Python version, dependencies]
- Error handling: [How to handle edge cases]

## Tasks

- [ ] Design: Define CLI interface and module structure
- [ ] Implement: Core functionality
- [ ] Implement: Error handling and edge cases
- [ ] Test: Manual testing with sample data
- [ ] Test: Add automated tests (if applicable)
- [ ] Document: Update relevant docs (SCRIPTS.md, README)
- [ ] Integrate: Add npm scripts to package.json

## CLI Interface Design

```bash
# Primary usage
.venv/bin/python scripts/{tool_name}.py [args]

# Examples
.venv/bin/python scripts/{tool_name}.py --help
.venv/bin/python scripts/{tool_name}.py input.yaml --output result.json
.venv/bin/python scripts/{tool_name}.py --all --format markdown
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `input` | positional | Yes | Input file path |
| `--output` | option | No | Output file (default: stdout) |
| `--format` | choice | No | Output format: json, markdown |
| `--verbose` | flag | No | Enable verbose logging |

## Definition of Done

- [ ] Tool runs without errors on happy path
- [ ] Help text is clear and complete (`--help`)
- [ ] Edge cases handled gracefully (missing files, bad input)
- [ ] Added to `package.json` scripts (if applicable)
- [ ] Documentation updated in `docs/SCRIPTS.md`
- [ ] Works in CI environment (no interactive prompts)

## Related Files

| File | Purpose |
|------|---------|
| `scripts/{tool_name}.py` | Main script (to create) |
| `scripts/{module}/` | Supporting module (if needed) |
| `docs/SCRIPTS.md` | Documentation to update |
| `package.json` | npm scripts to add |

## Context

### Background
[What problem does this solve? What manual process does it replace?]

### Design Decisions
- [Decision 1: rationale]
- [Decision 2: rationale]

### Similar Existing Tools
- `scripts/example.py` - [How this relates]

### Dependencies
- [Any new packages needed?]
- [Any existing code to reuse?]

### Breaking Changes

| Change | Impact | Migration |
|--------|--------|-----------|
| [Flag renamed] | [Who/what is affected] | [How to migrate] |
| [Output format changed] | [Scripts that parse output] | [Update X to handle Y] |

> If no breaking changes, state: "None - fully backward compatible"

## Test Plan

### Manual Testing
```bash
# Test 1: Basic functionality
.venv/bin/python scripts/{tool_name}.py test_input.yaml

# Test 2: Edge case - missing file
.venv/bin/python scripts/{tool_name}.py nonexistent.yaml

# Test 3: All options
.venv/bin/python scripts/{tool_name}.py input.yaml --output out.json --verbose
```

### Expected Results
- Test 1: [Expected output]
- Test 2: [Expected error message]
- Test 3: [Expected behavior]
```

---

## npm Script Convention

```json
{
  "scripts": {
    "toolname": ".venv/bin/python scripts/tool_name.py",
    "toolname:verbose": ".venv/bin/python scripts/tool_name.py --verbose"
  }
}
```
