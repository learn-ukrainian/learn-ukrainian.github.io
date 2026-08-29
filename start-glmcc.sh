#!/usr/bin/env bash
# Compatibility wrapper: Claude Code UI routed to Z.AI GLM (GLM Coding Plan).
#
# Canonical Coding Plan entry (#7416):
#   ./start-glmcc.sh
#
# `./start-glm.sh` is now OpenCode `zai-coding-plan/glm-5.3-flash` (headless).
# This wrapper keeps the Claude Code / glmcc route. Isolation, credential
# selection (explicit env or ~/.secret/zai.key), and route guards remain in
# scripts/lib/glmcc_route.sh + launcher_core.sh.
#
# Official reference: https://docs.z.ai/scenario-example/develop-tools/claude

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/lib/launcher_core.sh"
launcher_main glm interactive "$@"
