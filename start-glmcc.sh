#!/usr/bin/env bash
# Compatibility wrapper: Claude Code UI routed to Z.AI GLM (GLM Coding Plan).
#
# Canonical entry after the launcher cutover (#5958):
#   ./start-glm.sh
#
# This wrapper restores the historical `./start-glmcc.sh` name. It does not
# invent a second route — it forwards to the shared glm adapter. Isolation,
# credential selection (explicit env or ~/.secret/zai.key), and route guards
# remain in scripts/lib/glmcc_route.sh + launcher_core.sh.
#
# Official reference: https://docs.z.ai/scenario-example/develop-tools/claude

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT/start-glm.sh" "$@"
