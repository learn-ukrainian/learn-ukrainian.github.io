# Code Review Benchmark Matrix

Generated: 2026-05-16T20:13:06Z

## Summary

- Cells scored: 44
- Cells n/a: 12
- Cells with harness errors: 19
- Best F1: 61.5% (gpt-5.5 / native_cli)

## Leaderboard

| family | model | harness | effort | mcp_state | F1 | P | R | HIGH R | strong-match-count | cat-miss | avg_dur |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai | gpt-5.5 | native_cli | medium | with_mcp | 61.5% | 80.0% | 50.0% | 40.0% | 4 | 3 | 209.6s |
| openai | gpt-5.5 | hermes | medium | with_mcp | 46.2% | 60.0% | 37.5% | 40.0% | 3 | 3 | 231.5s |
| openai | gpt-5.5 | native_cli | low | without_mcp | 46.2% | 60.0% | 37.5% | 40.0% | 3 | 3 | 72.8s |
| openai | gpt-5.5 | native_cli | medium | without_mcp | 46.2% | 60.0% | 37.5% | 40.0% | 3 | 3 | 122.6s |
| openai | gpt-5.5 | native_cli | high | without_mcp | 42.9% | 50.0% | 37.5% | 40.0% | 3 | 3 | 301.1s |
| anthropic | claude-sonnet-4-6 | native_cli | xhigh | with_mcp | 41.7% | 31.2% | 62.5% | 60.0% | 5 | 2 | 503.9s |
| openai | gpt-5.5 | hermes | low | with_mcp | 40.0% | 42.9% | 37.5% | 40.0% | 3 | 3 | 153.2s |
| openai | gpt-5.5 | native_cli | low | with_mcp | 36.4% | 66.7% | 25.0% | 20.0% | 2 | 4 | 61.0s |
| anthropic | claude-sonnet-4-6 | native_cli | low | without_mcp | 34.8% | 26.7% | 50.0% | 40.0% | 4 | 3 | 142.9s |
| openai | gpt-5.5 | hermes | high | with_mcp | 30.8% | 40.0% | 25.0% | 20.0% | 2 | 4 | 142.8s |
| anthropic | claude-opus-4-7 | native_cli | low | with_mcp | 28.6% | 23.1% | 37.5% | 40.0% | 3 | 3 | 87.8s |
| anthropic | claude-opus-4-7 | native_cli | medium | without_mcp | 28.6% | 23.1% | 37.5% | 20.0% | 3 | 4 | 107.6s |
| anthropic | claude-opus-4-7 | native_cli | low | without_mcp | 27.3% | 21.4% | 37.5% | 20.0% | 3 | 4 | 90.1s |
| openai | gpt-5.5 | native_cli | high | with_mcp | 26.7% | 28.6% | 25.0% | 20.0% | 2 | 4 | 204.4s |
| anthropic | claude-opus-4-7 | native_cli | high | without_mcp | 26.1% | 20.0% | 37.5% | 20.0% | 3 | 4 | 137.6s |
| anthropic | claude-sonnet-4-6 | native_cli | low | with_mcp | 24.0% | 17.6% | 37.5% | 20.0% | 3 | 4 | 134.7s |
| anthropic | claude-sonnet-4-6 | native_cli | medium | without_mcp | 24.0% | 17.6% | 37.5% | 20.0% | 3 | 4 | 274.0s |
| anthropic | claude-sonnet-4-6 | native_cli | high | with_mcp | 21.4% | 15.0% | 37.5% | 20.0% | 3 | 4 | 419.7s |
| anthropic | claude-sonnet-4-6 | native_cli | xhigh | without_mcp | 16.0% | 11.8% | 25.0% | 20.0% | 2 | 4 | 340.7s |
| anthropic | claude-sonnet-4-6 | native_cli | high | without_mcp | 14.8% | 10.5% | 25.0% | 20.0% | 2 | 4 | 558.1s |
| anthropic | claude-opus-4-7 | native_cli | medium | with_mcp | 8.3% | 6.2% | 12.5% | 0.0% | 1 | 5 | 111.5s |
| anthropic | claude-sonnet-4-6 | native_cli | medium | with_mcp | 7.4% | 5.3% | 12.5% | 20.0% | 1 | 4 | 339.0s |
| anthropic | claude-opus-4-7 | hermes | high | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 6.2s |
| anthropic | claude-opus-4-7 | hermes | high | without_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 0.5s |
| anthropic | claude-opus-4-7 | hermes | low | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 7.7s |
| anthropic | claude-opus-4-7 | hermes | low | without_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 0.5s |
| anthropic | claude-opus-4-7 | hermes | medium | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 10.5s |
| anthropic | claude-opus-4-7 | hermes | medium | without_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 0.5s |
| anthropic | claude-opus-4-7 | hermes | xhigh | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 6.4s |
| anthropic | claude-opus-4-7 | hermes | xhigh | without_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 0.5s |
| anthropic | claude-opus-4-7 | native_cli | high | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 150.6s |
| anthropic | claude-opus-4-7 | native_cli | xhigh | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 193.1s |
| anthropic | claude-opus-4-7 | native_cli | xhigh | without_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 187.8s |
| anthropic | claude-sonnet-4-6 | hermes | high | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 6.3s |
| anthropic | claude-sonnet-4-6 | hermes | high | without_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 0.6s |
| anthropic | claude-sonnet-4-6 | hermes | low | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 6.6s |
| anthropic | claude-sonnet-4-6 | hermes | low | without_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 0.6s |
| anthropic | claude-sonnet-4-6 | hermes | medium | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 6.2s |
| anthropic | claude-sonnet-4-6 | hermes | medium | without_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 0.6s |
| anthropic | claude-sonnet-4-6 | hermes | xhigh | with_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 7.3s |
| anthropic | claude-sonnet-4-6 | hermes | xhigh | without_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 0.6s |
| openai | gpt-5.5 | hermes | high | without_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 0.5s |
| openai | gpt-5.5 | hermes | low | without_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 0.6s |
| openai | gpt-5.5 | hermes | medium | without_mcp | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 5 | 0.5s |

## Harness Comparison

| model | effort | mcp_state | native_cli F1 | hermes F1 | delta |
| --- | --- | --- | --- | --- | --- |
| claude-opus-4-7 | high | with_mcp | 0.0% | 0.0% | +0.0pp |
| claude-opus-4-7 | high | without_mcp | 26.1% | 0.0% | -26.1pp |
| claude-opus-4-7 | low | with_mcp | 28.6% | 0.0% | -28.6pp |
| claude-opus-4-7 | low | without_mcp | 27.3% | 0.0% | -27.3pp |
| claude-opus-4-7 | medium | with_mcp | 8.3% | 0.0% | -8.3pp |
| claude-opus-4-7 | medium | without_mcp | 28.6% | 0.0% | -28.6pp |
| claude-opus-4-7 | xhigh | with_mcp | 0.0% | 0.0% | +0.0pp |
| claude-opus-4-7 | xhigh | without_mcp | 0.0% | 0.0% | +0.0pp |
| claude-sonnet-4-6 | high | with_mcp | 21.4% | 0.0% | -21.4pp |
| claude-sonnet-4-6 | high | without_mcp | 14.8% | 0.0% | -14.8pp |
| claude-sonnet-4-6 | low | with_mcp | 24.0% | 0.0% | -24.0pp |
| claude-sonnet-4-6 | low | without_mcp | 34.8% | 0.0% | -34.8pp |
| claude-sonnet-4-6 | medium | with_mcp | 7.4% | 0.0% | -7.4pp |
| claude-sonnet-4-6 | medium | without_mcp | 24.0% | 0.0% | -24.0pp |
| claude-sonnet-4-6 | xhigh | with_mcp | 41.7% | 0.0% | -41.7pp |
| claude-sonnet-4-6 | xhigh | without_mcp | 16.0% | 0.0% | -16.0pp |
| gpt-5.5 | high | with_mcp | 26.7% | 30.8% | +4.1pp |
| gpt-5.5 | high | without_mcp | 42.9% | 0.0% | -42.9pp |
| gpt-5.5 | low | with_mcp | 36.4% | 40.0% | +3.6pp |
| gpt-5.5 | low | without_mcp | 46.2% | 0.0% | -46.2pp |
| gpt-5.5 | medium | with_mcp | 61.5% | 46.2% | -15.4pp |
| gpt-5.5 | medium | without_mcp | 46.2% | 0.0% | -46.2pp |

## MCP Impact

| model | harness | effort | without F1 | with F1 | delta |
| --- | --- | --- | --- | --- | --- |
| claude-opus-4-7 | hermes | high | 0.0% | 0.0% | +0.0pp |
| claude-opus-4-7 | hermes | low | 0.0% | 0.0% | +0.0pp |
| claude-opus-4-7 | hermes | medium | 0.0% | 0.0% | +0.0pp |
| claude-opus-4-7 | hermes | xhigh | 0.0% | 0.0% | +0.0pp |
| claude-opus-4-7 | native_cli | high | 26.1% | 0.0% | -26.1pp |
| claude-opus-4-7 | native_cli | low | 27.3% | 28.6% | +1.3pp |
| claude-opus-4-7 | native_cli | medium | 28.6% | 8.3% | -20.2pp |
| claude-opus-4-7 | native_cli | xhigh | 0.0% | 0.0% | +0.0pp |
| claude-sonnet-4-6 | hermes | high | 0.0% | 0.0% | +0.0pp |
| claude-sonnet-4-6 | hermes | low | 0.0% | 0.0% | +0.0pp |
| claude-sonnet-4-6 | hermes | medium | 0.0% | 0.0% | +0.0pp |
| claude-sonnet-4-6 | hermes | xhigh | 0.0% | 0.0% | +0.0pp |
| claude-sonnet-4-6 | native_cli | high | 14.8% | 21.4% | +6.6pp |
| claude-sonnet-4-6 | native_cli | low | 34.8% | 24.0% | -10.8pp |
| claude-sonnet-4-6 | native_cli | medium | 24.0% | 7.4% | -16.6pp |
| claude-sonnet-4-6 | native_cli | xhigh | 16.0% | 41.7% | +25.7pp |
| gpt-5.5 | hermes | high | 0.0% | 30.8% | +30.8pp |
| gpt-5.5 | hermes | low | 0.0% | 40.0% | +40.0pp |
| gpt-5.5 | hermes | medium | 0.0% | 46.2% | +46.2pp |
| gpt-5.5 | native_cli | high | 42.9% | 26.7% | -16.2pp |
| gpt-5.5 | native_cli | low | 46.2% | 36.4% | -9.8pp |
| gpt-5.5 | native_cli | medium | 46.2% | 61.5% | +15.4pp |

## Effort Scaling

| model | harness | mcp_state | F1 by effort |
| --- | --- | --- | --- |
| claude-opus-4-7 | hermes | with_mcp | high=0.0%, low=0.0%, medium=0.0%, xhigh=0.0% |
| claude-opus-4-7 | hermes | without_mcp | high=0.0%, low=0.0%, medium=0.0%, xhigh=0.0% |
| claude-opus-4-7 | native_cli | with_mcp | high=0.0%, low=28.6%, medium=8.3%, xhigh=0.0% |
| claude-opus-4-7 | native_cli | without_mcp | high=26.1%, low=27.3%, medium=28.6%, xhigh=0.0% |
| claude-sonnet-4-6 | hermes | with_mcp | high=0.0%, low=0.0%, medium=0.0%, xhigh=0.0% |
| claude-sonnet-4-6 | hermes | without_mcp | high=0.0%, low=0.0%, medium=0.0%, xhigh=0.0% |
| claude-sonnet-4-6 | native_cli | with_mcp | high=21.4%, low=24.0%, medium=7.4%, xhigh=41.7% |
| claude-sonnet-4-6 | native_cli | without_mcp | high=14.8%, low=34.8%, medium=24.0%, xhigh=16.0% |
| gpt-5.5 | hermes | with_mcp | high=30.8%, low=40.0%, medium=46.2% |
| gpt-5.5 | hermes | without_mcp | high=0.0%, low=0.0%, medium=0.0% |
| gpt-5.5 | native_cli | with_mcp | high=26.7%, low=36.4%, medium=61.5% |
| gpt-5.5 | native_cli | without_mcp | high=42.9%, low=46.2%, medium=46.2% |

## Failure Log

| family | model | harness | effort | mcp_state | reason |
| --- | --- | --- | --- | --- | --- |
| anthropic | claude-opus-4-7 | hermes | high | with_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2031-activity-schema", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2038-m20-three-fixes", "verd |
| anthropic | claude-opus-4-7 | hermes | high | without_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_acti |
| anthropic | claude-opus-4-7 | hermes | low | with_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2031-activity-schema", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2038-m20-three-fixes", "verd |
| anthropic | claude-opus-4-7 | hermes | low | without_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_acti |
| anthropic | claude-opus-4-7 | hermes | medium | with_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2031-activity-schema", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2038-m20-three-fixes", "verd |
| anthropic | claude-opus-4-7 | hermes | medium | without_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_acti |
| anthropic | claude-opus-4-7 | hermes | xhigh | with_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2031-activity-schema", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2038-m20-three-fixes", "verd |
| anthropic | claude-opus-4-7 | hermes | xhigh | without_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_acti |
| anthropic | claude-sonnet-4-6 | hermes | high | with_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2031-activity-schema", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2038-m20-three-fixes", "verd |
| anthropic | claude-sonnet-4-6 | hermes | high | without_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_acti |
| anthropic | claude-sonnet-4-6 | hermes | low | with_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2031-activity-schema", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2038-m20-three-fixes", "verd |
| anthropic | claude-sonnet-4-6 | hermes | low | without_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_acti |
| anthropic | claude-sonnet-4-6 | hermes | medium | with_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2031-activity-schema", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2038-m20-three-fixes", "verd |
| anthropic | claude-sonnet-4-6 | hermes | medium | without_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_acti |
| anthropic | claude-sonnet-4-6 | hermes | xhigh | with_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2031-activity-schema", "verdict": "review_error", "error": null, "returncode": 0, "stdout": null, "stderr": ""}, {"case_id": "pr-2038-m20-three-fixes", "verd |
| anthropic | claude-sonnet-4-6 | hermes | xhigh | without_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_acti |
| google | gemini-3.1-pro-preview | native_cli | high | with_mcp | gemini-3.1-pro-preview does not accept effort=high via native_cli; configured palette: default |
| google | gemini-3.1-pro-preview | native_cli | high | without_mcp | gemini-3.1-pro-preview does not accept effort=high via native_cli; configured palette: default |
| google | gemini-3.1-pro-preview | native_cli | low | with_mcp | gemini-3.1-pro-preview does not accept effort=low via native_cli; configured palette: default |
| google | gemini-3.1-pro-preview | native_cli | low | without_mcp | gemini-3.1-pro-preview does not accept effort=low via native_cli; configured palette: default |
| google | gemini-3.1-pro-preview | native_cli | medium | with_mcp | gemini-3.1-pro-preview does not accept effort=medium via native_cli; configured palette: default |
| google | gemini-3.1-pro-preview | native_cli | medium | without_mcp | gemini-3.1-pro-preview does not accept effort=medium via native_cli; configured palette: default |
| google | gemini-3.1-pro-preview | native_cli | xhigh | with_mcp | gemini-3.1-pro-preview does not accept effort=xhigh via native_cli; configured palette: default |
| google | gemini-3.1-pro-preview | native_cli | xhigh | without_mcp | gemini-3.1-pro-preview does not accept effort=xhigh via native_cli; configured palette: default |
| openai | gpt-5.5 | hermes | high | without_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_acti |
| openai | gpt-5.5 | hermes | low | without_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_acti |
| openai | gpt-5.5 | hermes | medium | without_mcp | [{"case_id": "pr-2025-openai-proxy", "verdict": "review_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_acti |
| openai | gpt-5.5 | hermes | xhigh | with_mcp | gpt-5.5 does not accept effort=xhigh via hermes; configured palette: low, medium, high |
| openai | gpt-5.5 | hermes | xhigh | without_mcp | gpt-5.5 does not accept effort=xhigh via hermes; configured palette: low, medium, high |
| openai | gpt-5.5 | native_cli | xhigh | with_mcp | gpt-5.5 does not accept effort=xhigh via native_cli; configured palette: low, medium, high |
| openai | gpt-5.5 | native_cli | xhigh | without_mcp | gpt-5.5 does not accept effort=xhigh via native_cli; configured palette: low, medium, high |
