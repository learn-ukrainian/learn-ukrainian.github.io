#!/usr/bin/env bash
# Shell-level tests for scripts/deploy_prompts.sh orphan guard.
#
# Run:  bash tests/test_deploy_prompts_orphan_guard.sh
#
# Exit 0 on pass, 1 on fail. Each test is self-contained — creates
# its own temp source/dest tree, sources the script helpers, and
# asserts behavior.

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$PROJECT_ROOT/scripts/deploy_prompts.sh"

if [[ ! -f "$SCRIPT" ]]; then
    echo "FAIL: $SCRIPT not found"
    exit 1
fi

# Extract the helper functions from the deploy script into a temp
# sourcable file so we can test them in isolation without running
# the full deploy.
EXTRACT=$(mktemp)
trap 'rm -f "$EXTRACT"' EXIT
sed -n '/^build_excludes()/,/^}$/p' "$SCRIPT" >> "$EXTRACT"
echo "" >> "$EXTRACT"
sed -n '/^check_orphans()/,/^}$/p' "$SCRIPT" >> "$EXTRACT"

# shellcheck disable=SC1090
source "$EXTRACT"

PASS=0
FAIL=0

_assert_eq() {
    local name="$1" expected="$2" actual="$3"
    if [[ "$expected" == "$actual" ]]; then
        echo "  ✓ $name"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $name"
        echo "    expected: $expected"
        echo "    actual:   $actual"
        FAIL=$((FAIL + 1))
    fi
}

_assert_rc() {
    local name="$1" expected_rc="$2" actual_rc="$3"
    if [[ "$expected_rc" == "$actual_rc" ]]; then
        echo "  ✓ $name"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $name (expected rc=$expected_rc, got rc=$actual_rc)"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== build_excludes ==="
_assert_eq "empty orphans → no excludes" "" "$(build_excludes '')"
_assert_eq "single orphan" " --exclude=docs/" "$(build_excludes 'docs/')"
_assert_eq "two orphans" " --exclude=docs/ --exclude=foo/" "$(build_excludes 'docs/ foo/')"
_assert_eq "file orphan" " --exclude=notes.md" "$(build_excludes 'notes.md')"

echo ""
echo "=== check_orphans ==="
TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT

# Scenario 1: source and dst identical → no orphan, returns 0
mkdir -p "$TEST_DIR/src1"/a "$TEST_DIR/dst1"/a
echo "x" > "$TEST_DIR/src1/a/file.txt"
echo "x" > "$TEST_DIR/dst1/a/file.txt"
check_orphans "$TEST_DIR/src1" "$TEST_DIR/dst1" "" "identical" >/dev/null 2>&1
_assert_rc "identical trees → rc 0" "0" "$?"

# Scenario 2: dst has an orphan path NOT declared → returns 1
mkdir -p "$TEST_DIR/src2"/a "$TEST_DIR/dst2"/a "$TEST_DIR/dst2"/orphan
echo "x" > "$TEST_DIR/src2/a/file.txt"
echo "x" > "$TEST_DIR/dst2/a/file.txt"
echo "ghost" > "$TEST_DIR/dst2/orphan/note.md"
check_orphans "$TEST_DIR/src2" "$TEST_DIR/dst2" "" "undeclared" >/dev/null 2>&1
_assert_rc "undeclared orphan → rc 1" "1" "$?"

# Scenario 3: dst has an orphan path AND it is declared → returns 0
check_orphans "$TEST_DIR/src2" "$TEST_DIR/dst2" "orphan/" "declared" >/dev/null 2>&1
_assert_rc "declared orphan → rc 0" "0" "$?"

# Scenario 4: dst doesn't exist → returns 0 (not an error)
check_orphans "$TEST_DIR/src2" "$TEST_DIR/missing_dst" "" "missing dst" >/dev/null 2>&1
_assert_rc "missing dst → rc 0 (not an error)" "0" "$?"

# Scenario 5: orphan directory with multiple files inside (real-world case)
mkdir -p "$TEST_DIR/src5" "$TEST_DIR/dst5/docs"
echo "a" > "$TEST_DIR/dst5/docs/LINGUISTICS.md"
echo "b" > "$TEST_DIR/dst5/docs/TOOLS.md"
echo "c" > "$TEST_DIR/dst5/docs/WORKFLOW.md"
# Without declaration → fails
check_orphans "$TEST_DIR/src5" "$TEST_DIR/dst5" "" "docs/ multi-file undeclared" >/dev/null 2>&1
_assert_rc "docs/ multi-file undeclared → rc 1" "1" "$?"
# With docs/ declared → passes
check_orphans "$TEST_DIR/src5" "$TEST_DIR/dst5" "docs/" "docs/ multi-file declared" >/dev/null 2>&1
_assert_rc "docs/ multi-file declared → rc 0" "0" "$?"

echo ""
echo "=== results ==="
echo "Passed: $PASS"
echo "Failed: $FAIL"
if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
