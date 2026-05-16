# Code Review Benchmark Matrix

Generated: 2026-05-16T18:03:07Z

## Summary

- Cells scored: 5
- Cells n/a: 0
- Cells with harness errors: 1
- Best F1: 61.5% (gpt-5.5 / hermes)

## Leaderboard

| family | model | harness | effort | mcp_state | F1 | P | R | HIGH R | strong-match-count | cat-miss | avg_dur |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai | gpt-5.5 | hermes | medium | with_mcp | 61.5% | 80.0% | 50.0% | 60.0% | 4 | 2 | 131.3s |
| google | gemini-3.1-pro-preview | native_cli | default | with_mcp | 28.6% | 33.3% | 25.0% | 20.0% | 2 | 4 | 290.1s |
| openai | gpt-5.4-mini | native_cli | medium | with_mcp | 16.7% | 25.0% | 12.5% | 0.0% | 1 | 5 | 323.5s |
| xai | grok-4.3 | hermes | medium | with_mcp | 16.7% | 25.0% | 12.5% | 0.0% | 1 | 5 | 100.3s |
| anthropic | claude-haiku-4-5-20251001 | native_cli | medium | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 2.1s |

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
