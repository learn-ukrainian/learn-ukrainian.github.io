#!/bin/bash
# Learn Ukrainian - Claude Code Wrapper
# Ensures skills are deployed and starts Claude

set -e

# Ensure ~/.local/bin is in PATH (where claude installs by default)
export PATH="$HOME/.local/bin:$PATH"
hash -r 2>/dev/null || true  # Clear command cache

# Get script directory (project root)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Claude in Learn Ukrainian project..."
echo "Project: $PROJECT_DIR"

# Preflight check: Verify required tools
echo "Preflight check..."
MISSING_TOOLS=""
for tool in git gh node npm; do
    if ! command -v $tool &> /dev/null; then
        MISSING_TOOLS="$MISSING_TOOLS $tool"
    fi
done

if [ -n "$MISSING_TOOLS" ]; then
    echo "Warning: Optional tools not found:$MISSING_TOOLS"
    echo "   (These are recommended but not required to start)"
fi

# Locate the Claude Code NATIVE install (preferred). The npx route is broken as of
# 2026-06-12: the npx-cached binary exits 194 ("native binary not installed").
CLAUDE_BIN="$HOME/.local/bin/claude"
if [ ! -x "$CLAUDE_BIN" ]; then
    echo "Error: Claude Code native install not found at $CLAUDE_BIN"
    echo "   Install/repair it, e.g.:  curl -fsSL https://claude.ai/install.sh | bash"
    exit 1
fi
echo "Claude native install: $("$CLAUDE_BIN" --version 2>/dev/null) ($CLAUDE_BIN)"

# Change to project directory
cd "$PROJECT_DIR"

# Show current branch
if git rev-parse --git-dir > /dev/null 2>&1; then
    CURRENT_BRANCH=$(git branch --show-current)
    echo "Current branch: $CURRENT_BRANCH"

    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        echo "Uncommitted changes detected"
    fi
fi

# Deploy agent extensions (always run to ensure up-to-date). Fail-honest: a
# failing deploy prints a loud banner + the real output instead of the old
# silent `|| true` that claimed "Skills deployed" over a stale .claude/.
# shellcheck source=scripts/lib/deploy_extensions.sh
source "$PROJECT_DIR/scripts/lib/deploy_extensions.sh"
deploy_agent_extensions "$PROJECT_DIR" agents:deploy \
    || echo "Continuing launch despite deploy failure (see banner above)."

# Show project status
echo ""
echo "LEARN UKRAINIAN - Ukrainian Language Learning"

# Show completion status from CLAUDE.md
if [ -f "CLAUDE.md" ]; then
    echo "   Completion Status:"
    # Extract completion status (lines between "### Completion Status" and next "###")
    sed -n '/^### Completion Status/,/^###/p' CLAUDE.md 2>/dev/null | \
        grep -E "^- \*\*[ABC][12]" | \
        sed 's/^- /       /' | \
        head -4
fi

# Count modules per level
echo ""
echo "   Module counts:"
for level in a1 a2 b1 b2 c1 c2; do
    if [ -d "curriculum/l2-uk-en/$level" ]; then
        COUNT=$(ls -1 curriculum/l2-uk-en/$level/*.md 2>/dev/null | wc -l | xargs)
        LEVEL_UPPER=$(echo "$level" | tr 'a-z' 'A-Z')
        echo "       $LEVEL_UPPER: $COUNT modules"
    fi
done

# List available skills dynamically
echo ""
if [ -d ".claude/skills" ]; then
    SKILL_COUNT=$(ls -1d .claude/skills/*/ 2>/dev/null | wc -l | xargs)
    echo "   Skills ($SKILL_COUNT available):"
    ls -1 .claude/skills/ 2>/dev/null | head -5 | sed 's/^/       /'
    if [ "$SKILL_COUNT" -gt 5 ]; then
        echo "       ... and $((SKILL_COUNT - 5)) more"
    fi
fi

# List available commands dynamically
echo ""
if [ -d ".claude/commands" ]; then
    CMD_COUNT=$(ls -1 .claude/commands/*.md 2>/dev/null | wc -l | xargs)
    echo "   Commands ($CMD_COUNT available):"
    ls -1 .claude/commands/*.md 2>/dev/null | \
        sed 's|.claude/commands/||' | \
        sed 's|.md$||' | \
        sed 's/^/       \//' | \
        head -4
    if [ "$CMD_COUNT" -gt 4 ]; then
        echo "       ... and $((CMD_COUNT - 4)) more"
    fi
fi

echo ""
echo "   Quick reference: npm run generate, npm run vocab:enrich, npm run pipeline"

echo ""

# Autocompact at the full 1M context window (kubedojo parity; raised from 750K 2026-06-08).
# Soft handoff discipline is separate and EARLIER — see MEMORY #2 (~750K, gated by a
# context-integrity self-check). Late handoff fails silently, so we hand off well before
# autocompact rewrites context. Subagents handle isolated work in their own windows.
export CLAUDE_CODE_AUTO_COMPACT_WINDOW=1000000
export LEARN_UKRAINIAN_TELEMETRY_FOOTER="${LEARN_UKRAINIAN_TELEMETRY_FOOTER:-1}"

# Launch the NATIVE install directly. (Previously launched via
# `npx @anthropic-ai/claude-code@latest`, but that route broke 2026-06-12 — the
# npx-cached binary exits 194. The native install at ~/.local/bin/claude auto-updates
# via `claude update`, so npx is no longer needed to stay current.)
# Derive the cold-start handoff identity from the selected `--agent`, so ONE
# launcher serves every lane: the SessionStart hook keys the thread handoff off
# SESSION_HANDOFF_AGENT, and each lane reads/writes its OWN
# .agent/<id>-thread-handoff.md slot (no per-lane wrapper scripts). Folk /
# curriculum default to the `claude` slot; `--agent infra-orchestrator` →
# `claude-infra`. An explicit SESSION_HANDOFF_AGENT in the environment wins.
# Mapping + argv parsing live in scripts/lib/handoff_identity.sh (unit-tested).
if [ -z "${SESSION_HANDOFF_AGENT:-}" ] && [ -f "$PROJECT_DIR/scripts/lib/handoff_identity.sh" ]; then
    # shellcheck source=scripts/lib/handoff_identity.sh
    source "$PROJECT_DIR/scripts/lib/handoff_identity.sh"
    _selected_agent="$(handoff_agent_from_argv "$@")"
    _handoff_slot="$(handoff_identity_for_agent "$_selected_agent")"
    if [ -n "$_handoff_slot" ]; then
        export SESSION_HANDOFF_AGENT="$_handoff_slot"
        echo "Handoff identity: $SESSION_HANDOFF_AGENT (from --agent $_selected_agent)"
    fi
    unset _selected_agent _handoff_slot
fi

echo "Launching Claude Code (native install)..."
exec "$CLAUDE_BIN" --chrome --permission-mode bypassPermissions "$@"
