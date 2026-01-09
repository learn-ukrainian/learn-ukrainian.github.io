---
name: Curriculum Maintainer
description: Maintains Ukrainian curriculum with strict quality standards
model: sonnet
hooks:
  PreToolUse:
    - matcher:
        tool: Write
        args:
          pattern: "curriculum/l2-uk-en/*/[0-9]*-*.md"
      command: |
        echo "📝 Writing to curriculum file: ${TOOL_INPUT_file_path}"
        echo "   Will validate after save..."

    - matcher:
        tool: Write
        args:
          pattern: "curriculum/l2-uk-en/*/activities/*.yaml"
      command: |
        echo "🎯 Writing activity file: ${TOOL_INPUT_file_path}"
        echo "   Will validate YAML structure after save..."

    - matcher:
        tool: Write
        args:
          pattern: "curriculum/l2-uk-en/*/vocabulary/*.yaml"
      command: |
        echo "📚 Writing vocabulary file: ${TOOL_INPUT_file_path}"
        echo "   Will validate vocabulary structure after save..."

  PostToolUse:
    - matcher:
        tool: Write
        args:
          pattern: "curriculum/l2-uk-en/*/[0-9]*-*.md"
      command: |
        # Extract level and module from path
        FILE="${TOOL_INPUT_file_path}"
        LEVEL=$(echo "$FILE" | grep -oP 'l2-uk-en/\K[a-z0-9]+')
        MODULE=$(basename "$FILE" | grep -oP '^[0-9]+')

        echo ""
        echo "🔍 Running audit for ${LEVEL^^} Module ${MODULE}..."
        .venv/bin/python scripts/audit_module.py "$FILE"

        if [ $? -eq 0 ]; then
          echo "✅ Audit passed!"
        else
          echo "⚠️  Audit found issues - please review output above"
          exit 1
        fi

    - matcher:
        tool: Write
        args:
          pattern: "curriculum/l2-uk-en/*/activities/*.yaml"
      command: |
        FILE="${TOOL_INPUT_file_path}"

        echo ""
        echo "🧪 Validating YAML syntax..."
        if ! npm run validate:yaml "$FILE" > /dev/null 2>&1; then
          echo "❌ YAML validation failed - check syntax"
          exit 1
        fi
        echo "✅ YAML valid"

    - matcher:
        tool: Write
        args:
          pattern: "curriculum/l2-uk-en/*/vocabulary/*.yaml"
      command: |
        FILE="${TOOL_INPUT_file_path}"
        LEVEL=$(echo "$FILE" | grep -oP 'l2-uk-en/\K[a-z0-9]+')

        echo ""
        echo "🧪 Validating vocabulary YAML..."
        if ! npm run validate:yaml "$FILE" > /dev/null 2>&1; then
          echo "❌ YAML validation failed - check syntax"
          exit 1
        fi

        echo "📊 Running global vocabulary audit for ${LEVEL^^}..."
        .venv/bin/python scripts/global_vocab_audit.py --level "$LEVEL"

        if [ $? -eq 0 ]; then
          echo "✅ Vocabulary audit passed!"
        else
          echo "⚠️  Vocabulary issues found - please review"
          exit 1
        fi

    - matcher:
        tool: Bash
        args:
          pattern: "git commit *"
      command: |
        echo ""
        echo "📊 Updating curriculum status..."

        for level in a1 a2 b1 b2 c1 c2; do
          if [ -f "scripts/check_${level}_status.py" ]; then
            echo "   Checking ${level^^}..."
            .venv/bin/python "scripts/check_${level}_status.py" > /dev/null 2>&1 || true
          fi
        done

        echo "✅ Status tracking updated"

  Stop:
    - command: |
        echo ""
        echo "👋 Curriculum Maintainer session ended"
        echo "📈 Summary of changes will be preserved in git history"
---

# Curriculum Maintainer Agent

This agent provides automated quality assurance for Ukrainian curriculum development.

## Features

### Automatic Validation
- **Module edits**: Runs `audit_module.py` after every curriculum file save
- **Activity edits**: Validates YAML syntax after activity file saves
- **Vocabulary edits**: Validates YAML + runs global vocabulary audit
- **Git commits**: Updates curriculum status tracking

### Quality Gates
All validations must pass before you can proceed. If audit fails:
1. Review the error output
2. Fix the issues
3. Save again (re-triggers validation)

### Performance
- Uses Sonnet model for cost efficiency
- Hooks run asynchronously (won't block your workflow)
- Fast feedback on quality issues

## Usage

This agent is automatically active when working in the curriculum directory.
No manual activation needed.

## Bypassing Validation

If you need to save work-in-progress without validation:
```bash
# Temporarily disable hooks
export CLAUDE_SKIP_HOOKS=1

# Make your edits
# ...

# Re-enable hooks
unset CLAUDE_SKIP_HOOKS
```

**Note:** Only use this for experimental work. All commits should pass validation.
