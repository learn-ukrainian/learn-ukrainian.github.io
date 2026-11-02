#!/usr/bin/env bash
# Launch the kube-dojo lane driver (#12553): a Claude Sonnet 5.5 session that runs the
# drive-epic skill on the kube-dojo stream, so the CTO stops hand-briefing kube-dojo pages.
# The kube-dojo work lives in kube-dojo/kube-dojo.github.io (sibling checkout, fleet repo
# `kube-dojo`); the lease, slot (claude-kube-dojo) and Fleet Comms stay on this repository.
# On this host, start it with the Claude account chosen through CLAUDE_CONFIG_DIR, in its own
# tmux session, for example:
#   tmux new-session -d -s kube-dojo -c /home/ops/learn-ukrainian \
#     -e CLAUDE_CONFIG_DIR=/home/ops/.claude scripts/start-kube-dojo-driver.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"
# The lane and the first-run instruction are fixed wrapper options: scope re-entry and
# successors replay only the caller's argv, and this wrapper adds them exactly once.
LC_WRAPPER_LAUNCHER_ARGS=(
  --epic kube-dojo
  "kube-dojo lane: drive kube-dojo/kube-dojo.github.io epic #2272 (complete evidence-backed KubeDojo content upgrade), its pages in learner order. Dispatch every kube-dojo worker with scripts/dispatch.py --repo kube-dojo. Routing (tracker C-4063/C-4064): Terra authors; the review of record is the cross-family reviewer the resolver picks; until an exercise environment exists, review covers prose factual claims only. Send every finding outside this lane to claude-cto through Fleet Comms."
)
LAUNCHER_MODEL="${LAUNCHER_MODEL:-claude-sonnet-5-5}" \
LAUNCHER_EFFORT="${LAUNCHER_EFFORT:-high}" \
launcher_main claude driver "$@"
