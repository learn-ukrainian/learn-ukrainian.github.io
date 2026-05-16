# Code Review Benchmark Matrix

Generated: 2026-05-16T18:41:09Z

## Summary

- Cells scored: 8
- Cells n/a: 12
- Cells with harness errors: 3
- Best F1: 57.1% (gpt-5.5 / hermes)

## Leaderboard

| family | model | harness | effort | mcp_state | F1 | P | R | HIGH R | strong-match-count | cat-miss | avg_dur |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai | gpt-5.5 | hermes | high | with_mcp | 57.1% | 66.7% | 50.0% | 60.0% | 4 | 2 | 235.2s |
| openai | gpt-5.5 | native_cli | high | without_mcp | 46.2% | 60.0% | 37.5% | 40.0% | 3 | 3 | 135.1s |
| openai | gpt-5.5 | native_cli | high | with_mcp | 30.8% | 40.0% | 25.0% | 20.0% | 2 | 4 | 265.3s |
| xai | grok-4.3 | hermes | xhigh | with_mcp | 16.7% | 25.0% | 12.5% | 0.0% | 1 | 5 | 106.8s |
| xai | grok-4.3 | hermes | high | with_mcp | 15.4% | 20.0% | 12.5% | 0.0% | 1 | 5 | 102.5s |
| openai | gpt-5.5 | hermes | high | without_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 0.5s |
| xai | grok-4.3 | hermes | high | without_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 0.5s |
| xai | grok-4.3 | hermes | xhigh | without_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 0.5s |

## Harness Comparison

| model | effort | mcp_state | native_cli F1 | hermes F1 | delta |
| --- | --- | --- | --- | --- | --- |
| gpt-5.5 | high | with_mcp | 30.8% | 57.1% | +26.4pp |
| gpt-5.5 | high | without_mcp | 46.2% | 0.0% | -46.2pp |

## MCP Impact

| model | harness | effort | without F1 | with F1 | delta |
| --- | --- | --- | --- | --- | --- |
| gpt-5.5 | hermes | high | 0.0% | 57.1% | +57.1pp |
| gpt-5.5 | native_cli | high | 46.2% | 30.8% | -15.4pp |
| grok-4.3 | hermes | high | 0.0% | 15.4% | +15.4pp |
| grok-4.3 | hermes | xhigh | 0.0% | 16.7% | +16.7pp |

## Effort Scaling

| model | harness | mcp_state | F1 by effort |
| --- | --- | --- | --- |
| grok-4.3 | hermes | with_mcp | high=15.4%, xhigh=16.7% |
| grok-4.3 | hermes | without_mcp | high=0.0%, xhigh=0.0% |

## Failure Log

| family | model | harness | effort | mcp_state | reason |
| --- | --- | --- | --- | --- | --- |
| google | gemini-3.1-pro-preview | native_cli | high | with_mcp | gemini-3.1-pro-preview does not accept effort=high via native_cli; configured palette: default |
| google | gemini-3.1-pro-preview | native_cli | high | without_mcp | gemini-3.1-pro-preview does not accept effort=high via native_cli; configured palette: default |
| google | gemini-3.1-pro-preview | native_cli | xhigh | with_mcp | gemini-3.1-pro-preview does not accept effort=xhigh via native_cli; configured palette: default |
| google | gemini-3.1-pro-preview | native_cli | xhigh | without_mcp | gemini-3.1-pro-preview does not accept effort=xhigh via native_cli; configured palette: default |
| openai | gpt-5.5 | hermes | high | without_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_acti |
| openai | gpt-5.5 | hermes | xhigh | with_mcp | gpt-5.5 does not accept effort=xhigh via hermes; configured palette: low, medium, high |
| openai | gpt-5.5 | hermes | xhigh | without_mcp | gpt-5.5 does not accept effort=xhigh via hermes; configured palette: low, medium, high |
| openai | gpt-5.5 | native_cli | xhigh | with_mcp | gpt-5.5 does not accept effort=xhigh via native_cli; configured palette: low, medium, high |
| openai | gpt-5.5 | native_cli | xhigh | without_mcp | gpt-5.5 does not accept effort=xhigh via native_cli; configured palette: low, medium, high |
| xai | grok-4.3 | hermes | high | without_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_acti |
| xai | grok-4.3 | hermes | xhigh | without_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_acti |
| xai | grok-4.3 | native_cli | high | with_mcp | xai does not have a native_cli route |
| xai | grok-4.3 | native_cli | high | without_mcp | xai does not have a native_cli route |
| xai | grok-4.3 | native_cli | xhigh | with_mcp | xai does not have a native_cli route |
| xai | grok-4.3 | native_cli | xhigh | without_mcp | xai does not have a native_cli route |
