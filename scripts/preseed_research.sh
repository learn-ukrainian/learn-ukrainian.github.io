#!/bin/bash
# Pre-seed Phase A research for tracks that still need it
# Skips modules with Phase A already complete
#
# Already done: a1, a2, b1, b2, c1, hist, c1-bio (856/1638)

set -e

LOGDIR="logs/research-preseed"
mkdir -p "$LOGDIR"
TIMESTAMP=$(date +%Y%m%d-%H%M)

echo "============================================="
echo "  Phase A Pre-Seed — $TIMESTAMP"
echo "============================================="
echo ""
echo "Gemini: istoriohrafiia (4), c2 (101), b2-pro (40), c1-pro (50)"
echo "Claude: lit* (387), oes (100), ruth (100)"
echo "Logs:   $LOGDIR/"
echo ""

# --- Gemini tracks ---

echo "[G1] istoriohrafiia (4 remaining)..."
.venv/bin/python scripts/build_module_v3.py istoriohrafiia --all --research-only \
  > "$LOGDIR/istoriohrafiia-$TIMESTAMP.log" 2>&1 &

sleep 10

echo "[G2] b2-pro (40)..."
.venv/bin/python scripts/build_module_v3.py b2-pro --all --research-only \
  > "$LOGDIR/b2-pro-$TIMESTAMP.log" 2>&1 &

sleep 10

echo "[G3] c1-pro (50)..."
.venv/bin/python scripts/build_module_v3.py c1-pro --all --research-only \
  > "$LOGDIR/c1-pro-$TIMESTAMP.log" 2>&1 &

sleep 10

echo "[G4] c2 (101 — last)..."
.venv/bin/python scripts/build_module_v3.py c2 --all --research-only \
  > "$LOGDIR/c2-$TIMESTAMP.log" 2>&1 &

# --- Claude tracks ---

sleep 30

echo "[C1] lit (217)..."
.venv/bin/python scripts/build_module_v3.py lit --all --research-only --use-claude A \
  > "$LOGDIR/lit-$TIMESTAMP.log" 2>&1 &

sleep 10

echo "[C2] lit-essay (55)..."
.venv/bin/python scripts/build_module_v3.py lit-essay --all --research-only --use-claude A \
  > "$LOGDIR/lit-essay-$TIMESTAMP.log" 2>&1 &

sleep 10

echo "[C3] lit-hist-fic (20)..."
.venv/bin/python scripts/build_module_v3.py lit-hist-fic --all --research-only --use-claude A \
  > "$LOGDIR/lit-hist-fic-$TIMESTAMP.log" 2>&1 &

sleep 10

echo "[C4] lit-fantastika (27)..."
.venv/bin/python scripts/build_module_v3.py lit-fantastika --all --research-only --use-claude A \
  > "$LOGDIR/lit-fantastika-$TIMESTAMP.log" 2>&1 &

sleep 10

echo "[C5] lit-war (24)..."
.venv/bin/python scripts/build_module_v3.py lit-war --all --research-only --use-claude A \
  > "$LOGDIR/lit-war-$TIMESTAMP.log" 2>&1 &

sleep 10

echo "[C6] lit-humor (14)..."
.venv/bin/python scripts/build_module_v3.py lit-humor --all --research-only --use-claude A \
  > "$LOGDIR/lit-humor-$TIMESTAMP.log" 2>&1 &

sleep 10

echo "[C7] lit-juvenile (30)..."
.venv/bin/python scripts/build_module_v3.py lit-juvenile --all --research-only --use-claude A \
  > "$LOGDIR/lit-juvenile-$TIMESTAMP.log" 2>&1 &

sleep 10

echo "[C8] oes (100)..."
.venv/bin/python scripts/build_module_v3.py oes --all --research-only --use-claude A \
  > "$LOGDIR/oes-$TIMESTAMP.log" 2>&1 &

sleep 10

echo "[C9] ruth (100)..."
.venv/bin/python scripts/build_module_v3.py ruth --all --research-only --use-claude A \
  > "$LOGDIR/ruth-$TIMESTAMP.log" 2>&1 &

echo ""
echo "13 tracks launched (4 Gemini + 9 Claude)."
echo "Monitor: tail -f $LOGDIR/*-$TIMESTAMP.log"
echo ""

wait

echo ""
echo "============================================="
echo "  ALL DONE — $(date)"
echo "============================================="
echo ""

for f in "$LOGDIR"/*-"$TIMESTAMP".log; do
  track=$(basename "$f" | sed "s/-$TIMESTAMP.log//")
  passed=$(grep -c "PASS\|Phase A: SKIP\|research complete" "$f" 2>/dev/null || echo "0")
  failed=$(grep -c "FAIL\|ERROR\|failed" "$f" 2>/dev/null || echo "0")
  echo "  $track: passed=$passed failed=$failed"
done
