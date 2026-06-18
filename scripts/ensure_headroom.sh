#!/usr/bin/env bash
# Shared launch guard for Headroom.
#
# This file is intended to be sourced by start-*.sh launchers. It may unset dead
# proxy environment variables in the calling shell so agents do not start with a
# broken local endpoint.

_learn_ukrainian_ensure_headroom() {
    local proxy_url="${HEADROOM_PROXY_URL:-}"
    local base_url

    if [ -z "${ANTHROPIC_BASE_URL:-}${OPENAI_BASE_URL:-}${COPILOT_PROVIDER_BASE_URL:-}" ] \
        && [ -f "$HOME/.profile" ]; then
        # Pick up Headroom routing env from shells that did not source login
        # profiles before launching the agent.
        # shellcheck disable=SC1090
        source "$HOME/.profile" || true
    fi

    if [ -z "$proxy_url" ]; then
        for base_url in "${ANTHROPIC_BASE_URL:-}" "${OPENAI_BASE_URL:-}" "${COPILOT_PROVIDER_BASE_URL:-}"; do
            case "$base_url" in
                http://127.0.0.1:8787*|http://localhost:8787*)
                    proxy_url="${base_url%/}"
                    break
                    ;;
            esac
        done
    fi

    proxy_url="${proxy_url:-http://127.0.0.1:8787}"
    proxy_url="${proxy_url%/}"
    proxy_url="${proxy_url%/v1}"

    if curl -fsS --max-time 2 "$proxy_url/health" >/dev/null 2>&1; then
        return 0
    fi

    echo "headroom proxy down -- attempting restart..."
    if command -v headroom >/dev/null 2>&1; then
        headroom install start --profile default >/dev/null 2>&1 || true
    elif [ -x "$HOME/.local/bin/headroom" ]; then
        "$HOME/.local/bin/headroom" install start --profile default >/dev/null 2>&1 || true
    fi

    if ! curl -fsS --max-time 2 "$proxy_url/health" >/dev/null 2>&1; then
        local plist="$HOME/Library/LaunchAgents/com.headroom.default.plist"
        if command -v launchctl >/dev/null 2>&1 && [ -f "$plist" ]; then
            launchctl bootstrap "gui/$(id -u)" "$plist" >/dev/null 2>&1 || true
        fi
    fi

    sleep 2

    if curl -fsS --max-time 2 "$proxy_url/health" >/dev/null 2>&1; then
        return 0
    fi

    echo "headroom unavailable -- clearing dead local proxy env"
    case "${ANTHROPIC_BASE_URL:-}" in
        http://127.0.0.1:8787*|http://localhost:8787*) unset ANTHROPIC_BASE_URL ;;
    esac
    case "${OPENAI_BASE_URL:-}" in
        http://127.0.0.1:8787*|http://localhost:8787*) unset OPENAI_BASE_URL ;;
    esac
    case "${COPILOT_PROVIDER_BASE_URL:-}" in
        http://127.0.0.1:8787*|http://localhost:8787*) unset COPILOT_PROVIDER_BASE_URL ;;
    esac
}

_learn_ukrainian_ensure_headroom
unset -f _learn_ukrainian_ensure_headroom
