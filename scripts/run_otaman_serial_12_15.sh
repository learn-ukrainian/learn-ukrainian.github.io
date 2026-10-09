#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OTAMAN_SKILL_MD="$REPO_ROOT/.gemini/skills/otaman/SKILL.md"
LOG_ROOT="${TMPDIR:-${LU_TASK_SCRATCH_DIR:?Set TMPDIR or LU_TASK_SCRATCH_DIR to an existing task scratch directory}}"

echo "Starting serial otaman execution for A1 modules 12-15"

for i in {12..15}; do
  echo "--- Processing Module $i ---"
  log_file="$LOG_ROOT/otaman-a1-$i-serial.log"
  .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini "Activate skill otaman. Read and execute the instructions at $OTAMAN_SKILL_MD to process a1 $i" --task-id otaman-a1-$i --allow-write --model gemini-3.8-flash-high > "$log_file" 2>&1

  if [ $? -eq 0 ]; then
    echo "Module $i completed successfully."
  else
    echo "Module $i failed. Check log: $log_file"
    # Decide whether to continue or stop. For now, continue to next.
  fi

  # Optional: add a small delay to let API limits recover slightly
  sleep 10
done

echo "Serial execution completed."
