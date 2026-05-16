# Russianism Judge Calibration Matrix

Generated: 2026-05-16T13:20:43Z

## Summary

- Cells scored: 30
- Cells n/a: 0
- Cells with harness errors: 13

## Leaderboard

| family | model | harness | effort | mcp_state | F1 | P | R | case_acc | avg_dur | n/a-count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| google | gemini-3.1-pro-preview | native_cli | default | with_mcp | 80.0% | 85.7% | 75.0% | 91.7% | 342.6s | 0 |
| xai | grok-4.3 | hermes | xhigh | with_mcp | 78.6% | 91.7% | 68.8% | 100.0% | 220.5s | 0 |
| google | gemini-3.1-pro-preview | native_cli | default | without_mcp | 77.4% | 80.0% | 75.0% | 91.7% | 299.2s | 0 |
| openai | gpt-5.5 | hermes | medium | with_mcp | 76.9% | 100.0% | 62.5% | 91.7% | 491.7s | 0 |
| xai | grok-4.3 | hermes | high | with_mcp | 76.9% | 100.0% | 62.5% | 83.3% | 435.9s | 0 |
| xai | grok-4.3 | hermes | low | with_mcp | 73.3% | 78.6% | 68.8% | 75.0% | 416.4s | 0 |
| openai | gpt-5.5 | native_cli | medium | with_mcp | 72.0% | 100.0% | 56.2% | 100.0% | 243.2s | 0 |
| openai | gpt-5.4-mini | native_cli | medium | with_mcp | 66.7% | 100.0% | 50.0% | 75.0% | 308.5s | 0 |
| openai | gpt-5.5 | native_cli | high | without_mcp | 66.7% | 100.0% | 50.0% | 83.3% | 277.7s | 0 |
| openai | gpt-5.5 | native_cli | medium | without_mcp | 66.7% | 100.0% | 50.0% | 100.0% | 260.6s | 0 |
| xai | grok-4.3 | hermes | medium | with_mcp | 66.7% | 81.8% | 56.2% | 75.0% | 435.0s | 0 |
| xai | grok-4.3 | hermes | minimal | with_mcp | 64.0% | 88.9% | 50.0% | 66.7% | 401.9s | 0 |
| openai | gpt-5.5 | native_cli | high | with_mcp | 58.3% | 87.5% | 43.8% | 83.3% | 282.1s | 0 |
| openai | gpt-5.4-mini | native_cli | high | with_mcp | 54.5% | 100.0% | 37.5% | 75.0% | 379.2s | 0 |
| openai | gpt-5.4-mini | native_cli | medium | without_mcp | 54.5% | 100.0% | 37.5% | 75.0% | 352.9s | 0 |
| openai | gpt-5.5 | hermes | high | with_mcp | 52.2% | 85.7% | 37.5% | 91.7% | 472.9s | 0 |
| openai | gpt-5.4-mini | native_cli | high | without_mcp | 31.6% | 100.0% | 18.8% | 66.7% | 467.5s | 0 |
| google | gemini-3.0-flash-preview | native_cli | default | with_mcp | 0.0% | 0.0% | 0.0% | 58.3% | 181.9s | 0 |
| google | gemini-3.0-flash-preview | native_cli | default | without_mcp | 0.0% | 0.0% | 0.0% | 58.3% | 181.6s | 0 |
| openai | gpt-5.4-mini | hermes | high | with_mcp | 0.0% | 0.0% | 0.0% | 58.3% | 19.6s | 0 |
| openai | gpt-5.4-mini | hermes | high | without_mcp | 0.0% | 0.0% | 0.0% | 58.3% | 4.5s | 0 |
| openai | gpt-5.4-mini | hermes | medium | with_mcp | 0.0% | 0.0% | 0.0% | 58.3% | 19.2s | 0 |
| openai | gpt-5.4-mini | hermes | medium | without_mcp | 0.0% | 0.0% | 0.0% | 58.3% | 4.3s | 0 |
| openai | gpt-5.5 | hermes | high | without_mcp | 0.0% | 0.0% | 0.0% | 58.3% | 468.9s | 0 |
| openai | gpt-5.5 | hermes | medium | without_mcp | 0.0% | 0.0% | 0.0% | 58.3% | 474.7s | 0 |
| xai | grok-4.3 | hermes | high | without_mcp | 0.0% | 0.0% | 0.0% | 58.3% | 436.0s | 0 |
| xai | grok-4.3 | hermes | low | without_mcp | 0.0% | 0.0% | 0.0% | 58.3% | 417.1s | 0 |
| xai | grok-4.3 | hermes | medium | without_mcp | 0.0% | 0.0% | 0.0% | 58.3% | 420.8s | 0 |
| xai | grok-4.3 | hermes | minimal | without_mcp | 0.0% | 0.0% | 0.0% | 58.3% | 416.7s | 0 |
| xai | grok-4.3 | hermes | xhigh | without_mcp | 0.0% | 0.0% | 0.0% | 58.3% | 220.6s | 0 |

## Harness Comparison

| model | effort | mcp_state | native_cli F1 | hermes F1 | delta |
| --- | --- | --- | --- | --- | --- |
| gpt-5.4-mini | high | with_mcp | 54.5% | 0.0% | -54.5pp |
| gpt-5.4-mini | high | without_mcp | 31.6% | 0.0% | -31.6pp |
| gpt-5.4-mini | medium | with_mcp | 66.7% | 0.0% | -66.7pp |
| gpt-5.4-mini | medium | without_mcp | 54.5% | 0.0% | -54.5pp |
| gpt-5.5 | high | with_mcp | 58.3% | 52.2% | -6.2pp |
| gpt-5.5 | high | without_mcp | 66.7% | 0.0% | -66.7pp |
| gpt-5.5 | medium | with_mcp | 72.0% | 76.9% | +4.9pp |
| gpt-5.5 | medium | without_mcp | 66.7% | 0.0% | -66.7pp |

## MCP Impact

| model | harness | effort | without case_acc | with case_acc | delta |
| --- | --- | --- | --- | --- | --- |
| gemini-3.0-flash-preview | native_cli | default | 58.3% | 58.3% | +0.0pp |
| gemini-3.1-pro-preview | native_cli | default | 91.7% | 91.7% | +0.0pp |
| gpt-5.4-mini | hermes | high | 58.3% | 58.3% | +0.0pp |
| gpt-5.4-mini | hermes | medium | 58.3% | 58.3% | +0.0pp |
| gpt-5.4-mini | native_cli | high | 66.7% | 75.0% | +8.3pp |
| gpt-5.4-mini | native_cli | medium | 75.0% | 75.0% | +0.0pp |
| gpt-5.5 | hermes | high | 58.3% | 91.7% | +33.3pp |
| gpt-5.5 | hermes | medium | 58.3% | 91.7% | +33.3pp |
| gpt-5.5 | native_cli | high | 83.3% | 83.3% | +0.0pp |
| gpt-5.5 | native_cli | medium | 100.0% | 100.0% | +0.0pp |
| grok-4.3 | hermes | high | 58.3% | 83.3% | +25.0pp |
| grok-4.3 | hermes | low | 58.3% | 75.0% | +16.7pp |
| grok-4.3 | hermes | medium | 58.3% | 75.0% | +16.7pp |
| grok-4.3 | hermes | minimal | 58.3% | 66.7% | +8.3pp |
| grok-4.3 | hermes | xhigh | 58.3% | 100.0% | +41.7pp |

## Effort Scaling

| model | harness | mcp_state | F1 by effort |
| --- | --- | --- | --- |
| gpt-5.4-mini | hermes | with_mcp | high=0.0%, medium=0.0% |
| gpt-5.4-mini | hermes | without_mcp | high=0.0%, medium=0.0% |
| gpt-5.4-mini | native_cli | with_mcp | high=54.5%, medium=66.7% |
| gpt-5.4-mini | native_cli | without_mcp | high=31.6%, medium=54.5% |
| gpt-5.5 | hermes | with_mcp | high=52.2%, medium=76.9% |
| gpt-5.5 | hermes | without_mcp | high=0.0%, medium=0.0% |
| gpt-5.5 | native_cli | with_mcp | high=58.3%, medium=72.0% |
| gpt-5.5 | native_cli | without_mcp | high=66.7%, medium=66.7% |
| grok-4.3 | hermes | with_mcp | high=76.9%, low=73.3%, medium=66.7%, minimal=64.0%, xhigh=78.6% |
| grok-4.3 | hermes | without_mcp | high=0.0%, low=0.0%, medium=0.0%, minimal=0.0%, xhigh=0.0% |

## Failure Log

| family | model | harness | effort | mcp_state | reason |
| --- | --- | --- | --- | --- | --- |
| google | gemini-3.0-flash-preview | native_cli | default | with_mcp | [{"case_id": "cal_clean_greeting", "verdict": "judge_error", "error": null, "returncode": 1, "stdout": null, "stderr": "Ripgrep is not available. Falling back to GrepTool.\nError when talking to Gemini API Full report available at: /var/folders/pd/wvj52r1j3bd4z9y3dfc2k4180000gn/T/gemini-client-error |
| google | gemini-3.0-flash-preview | native_cli | default | without_mcp | [{"case_id": "cal_clean_greeting", "verdict": "judge_error", "error": null, "returncode": 1, "stdout": null, "stderr": "Ripgrep is not available. Falling back to GrepTool.\nError when talking to Gemini API Full report available at: /var/folders/pd/wvj52r1j3bd4z9y3dfc2k4180000gn/T/gemini-client-error |
| openai | gpt-5.4-mini | hermes | high | with_mcp | [{"case_id": "cal_clean_greeting", "verdict": "judge_error", "error": null, "returncode": 1, "stdout": null, "stderr": "Traceback (most recent call last):\n  File \"/Users/krisztiankoos/.hermes/hermes-agent/venv/bin/hermes\", line 10, in <module>\n    sys.exit(main())\n             ^^^^^^\n  File \" |
| openai | gpt-5.4-mini | hermes | high | without_mcp | [{"case_id": "cal_clean_greeting", "verdict": "judge_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_action: |
| openai | gpt-5.4-mini | hermes | medium | with_mcp | [{"case_id": "cal_clean_greeting", "verdict": "judge_error", "error": null, "returncode": 1, "stdout": null, "stderr": "Traceback (most recent call last):\n  File \"/Users/krisztiankoos/.hermes/hermes-agent/venv/bin/hermes\", line 10, in <module>\n    sys.exit(main())\n             ^^^^^^\n  File \" |
| openai | gpt-5.4-mini | hermes | medium | without_mcp | [{"case_id": "cal_clean_greeting", "verdict": "judge_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_action: |
| openai | gpt-5.5 | hermes | high | without_mcp | [{"case_id": "cal_clean_greeting", "verdict": "judge_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_action: |
| openai | gpt-5.5 | hermes | medium | without_mcp | [{"case_id": "cal_clean_greeting", "verdict": "judge_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_action: |
| xai | grok-4.3 | hermes | high | without_mcp | [{"case_id": "cal_clean_greeting", "verdict": "judge_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_action: |
| xai | grok-4.3 | hermes | low | without_mcp | [{"case_id": "cal_clean_greeting", "verdict": "judge_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_action: |
| xai | grok-4.3 | hermes | medium | without_mcp | [{"case_id": "cal_clean_greeting", "verdict": "judge_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_action: |
| xai | grok-4.3 | hermes | minimal | without_mcp | [{"case_id": "cal_clean_greeting", "verdict": "judge_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_action: |
| xai | grok-4.3 | hermes | xhigh | without_mcp | [{"case_id": "cal_clean_greeting", "verdict": "judge_error", "error": null, "returncode": 2, "stdout": null, "stderr": "usage: hermes mcp [-h] [--accept-hooks]\n                  {serve,add,remove,rm,list,ls,test,configure,config,login}\n                  ...\nhermes mcp: error: argument mcp_action: |
