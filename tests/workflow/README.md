# Workflow Testing

Testing the 9-phase module workflow (RFC-001) with Claude and Gemini.

**Issue:** #461

---

## Directory Structure

```
tests/workflow/
├── README.md           # This file
├── specs/              # YAML test specifications (machine-readable)
├── scenarios/          # Markdown test scenarios (human-readable)
└── results/            # Test outputs
    ├── claude/         # Claude test results
    └── gemini/         # Gemini test results
```

---

## Running Tests

### With Claude

1. Open Claude Code in the project directory
2. Read the scenario: `tests/workflow/scenarios/{test-name}.md`
3. Execute each phase command sequentially
4. Record results in the scenario checklist
5. Save outputs to `results/claude/{test-name}/`

### With Gemini

1. Open Gemini (or gemini-cli) with project context
2. Provide the scenario markdown as context
3. Execute each phase command sequentially
4. Record results in the scenario checklist
5. Save outputs to `results/gemini/{test-name}/`

---

## Test Cases

| Test ID | Track | Module | Focus |
|---------|-------|--------|-------|
| b2-hist-m41-full-pipeline | B2-HIST | 41 | Full 9-phase validation |

---

## Comparison Analysis

After running tests with both LLMs, compare:

1. **Template Compliance** - Did both follow the AI template structure?
2. **Phase Locking** - Did either modify locked files?
3. **Output Quality** - Audit script pass rates
4. **Naturalness** - MCP validator scores
5. **Consistency** - Similar quality for same inputs?

---

## Adding New Tests

1. Create YAML spec in `specs/` with input and evaluation criteria
2. Create markdown scenario in `scenarios/` with step-by-step instructions
3. Update this README with the new test case
4. Create result directories when running tests
