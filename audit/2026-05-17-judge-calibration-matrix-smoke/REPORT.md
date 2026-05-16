# Russianism Judge Calibration Matrix

Generated: 2026-05-16T12:30:49Z

## Summary

- Cells scored: 5
- Cells n/a: 0
- Cells with harness errors: 1

## Leaderboard

| family | model | harness | effort | mcp_state | F1 | P | R | case_acc | avg_dur | n/a-count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic | claude-haiku-4-5-20251001 | native_cli | medium | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0.7s | 0 |
| google | gemini-3.1-pro-preview | native_cli | default | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 25.1s | 0 |
| openai | gpt-5.4-mini | native_cli | medium | with_mcp | 0.0% | 0.0% | 0.0% | 100.0% | 14.2s | 0 |
| openai | gpt-5.5 | hermes | medium | with_mcp | 0.0% | 0.0% | 0.0% | 100.0% | 11.6s | 0 |
| xai | grok-4.3 | hermes | medium | with_mcp | 0.0% | 0.0% | 0.0% | 100.0% | 16.1s | 0 |

## Harness Comparison

| model | effort | mcp_state | native_cli F1 | hermes F1 | delta |
| --- | --- | --- | --- | --- | --- |
| n/a | n/a | n/a | n/a | n/a | n/a |

## MCP Impact

| model | harness | effort | without case_acc | with case_acc | delta |
| --- | --- | --- | --- | --- | --- |
| n/a | n/a | n/a | n/a | n/a | n/a |

## Effort Scaling

| model | harness | mcp_state | F1 by effort |
| --- | --- | --- | --- |
| n/a | n/a | n/a | n/a |

## Failure Log

| family | model | harness | effort | mcp_state | reason |
| --- | --- | --- | --- | --- | --- |
| anthropic | claude-haiku-4-5-20251001 | native_cli | medium | with_mcp | [{"case_id": "cal_clean_greeting", "verdict": "judge_error", "error": null, "returncode": 1, "stdout": "Not logged in · Please run /login\n", "stderr": ""}] |
