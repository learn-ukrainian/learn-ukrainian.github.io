#!/usr/bin/env bash
# Launch the kube-dojo lane driver (#12553): a Claude Sonnet 5.5 session that runs the
# drive-epic skill on the kube-dojo stream, so the CTO stops hand-briefing kube-dojo pages.
# The kube-dojo work lives in kube-dojo/kube-dojo.github.io (sibling checkout, fleet repo
# `kube-dojo`); the lease, slot (claude-kube-dojo) and Fleet Comms stay on this repository.
# From the repository root, with CLAUDE_CONFIG_DIR set to the chosen Claude account,
# start it in its own tmux session, for example:
#   tmux new-session -d -s kube-dojo -c "$PWD" \
#     -e CLAUDE_CONFIG_DIR="$CLAUDE_CONFIG_DIR" scripts/start-kube-dojo-driver.sh
# Roots (scripts/common/repo_root.py): ROOT below is the runtime root, the machinery
# checkout this wrapper and launcher_core.sh ship in, so it is read from this file's
# location. Everything the driver then targets comes from the machinery configuration
# (LEARN_UKRAINIAN_PRIMARY_REPO_ROOT and the rest): `--repo kube-dojo` resolves the
# kube-dojo checkout beside the configured primary, and task records, locks and the
# lease stay on that primary's state root.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# The dispatcher beside this wrapper, named from the wrapper's own location so the
# instruction holds in either checkout layout.
KUBE_DISPATCHER="$(basename "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)")/dispatch.py"
source "$ROOT/scripts/lib/launcher_core.sh"
# The lane and the first-run instruction are fixed wrapper options: scope re-entry and
# successors replay only the caller's argv, and this wrapper adds them exactly once.
# LC_WRAPPER_FIXED_EPIC makes the launcher refuse any caller lane before side effects.
LC_WRAPPER_FIXED_EPIC=kube-dojo
LC_WRAPPER_LAUNCHER_ARGS=(
  --epic "$LC_WRAPPER_FIXED_EPIC"
  "kube-dojo lane: drive kube-dojo/kube-dojo.github.io epic #2272 (complete evidence-backed KubeDojo content upgrade), its pages in learner order. Dispatch every kube-dojo worker with ${KUBE_DISPATCHER} --repo kube-dojo. Routing (tracker C-4063/C-4064): Terra authors; the review of record is the cross-family reviewer the resolver picks; until an exercise environment exists, review covers prose factual claims only. Send every finding outside this lane to claude-cto through Fleet Comms."
)
LAUNCHER_MODEL="${LAUNCHER_MODEL:-claude-sonnet-5-5}" \
LAUNCHER_EFFORT="${LAUNCHER_EFFORT:-high}" \
launcher_main claude driver "$@"
