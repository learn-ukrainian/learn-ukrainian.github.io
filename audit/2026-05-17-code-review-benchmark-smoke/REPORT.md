# Code Review Benchmark Matrix

Generated: 2026-05-16T17:21:11Z

## Summary

- Cells scored: 5
- Cells n/a: 0
- Cells with harness errors: 1
- Best F1: 30.8% (gpt-5.4-mini / native_cli)

## Leaderboard

| family | model | harness | effort | mcp_state | F1 | P | R | HIGH R | cat-miss | avg_dur |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai | gpt-5.4-mini | native_cli | medium | with_mcp | 30.8% | 40.0% | 25.0% | 20.0% | 4 | 250.4s |
| openai | gpt-5.5 | hermes | medium | with_mcp | 14.3% | 16.7% | 12.5% | 0.0% | 5 | 229.9s |
| anthropic | claude-haiku-4-5-20251001 | native_cli | medium | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 5 | 2.1s |
| google | gemini-3.1-pro-preview | native_cli | default | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 5 | 261.6s |
| xai | grok-4.3 | hermes | medium | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 5 | 159.9s |

## Harness Comparison

| model | effort | mcp_state | native_cli F1 | hermes F1 | delta |
| --- | --- | --- | --- | --- | --- |
| n/a | n/a | n/a | n/a | n/a | n/a |

## MCP Impact

| model | harness | effort | without F1 | with F1 | delta |
| --- | --- | --- | --- | --- | --- |
| n/a | n/a | n/a | n/a | n/a | n/a |

## Effort Scaling

| model | harness | mcp_state | F1 by effort |
| --- | --- | --- | --- |
| n/a | n/a | n/a | n/a |

## Failure Log

| family | model | harness | effort | mcp_state | reason |
| --- | --- | --- | --- | --- | --- |
| anthropic | claude-haiku-4-5-20251001 | native_cli | medium | with_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 1, "stdout": "Not logged in · Please run /login\n", "stderr": ""}, {"case_id": "pr-2031-activity-schema", "verdict": "review_error", "error": null, "returncode": 1, "stdout": "Not logged in · Please run /log |
