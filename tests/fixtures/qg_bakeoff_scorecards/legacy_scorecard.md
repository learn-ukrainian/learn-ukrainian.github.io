# QG Bakeoff Scorecard

Generated: 2026-07-06T00:00:00Z

Fractions are exact. `low-N` marks denominators below 10.


## Runs

| model | transport | entrypoint | passage | arm | status | failure_class | parse_lenient | model judgment | live admissible | missing | U honesty | M alignment | true unsupported | invalid | inadmissible | tools | wall_s |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: |
| openrouter/test/m [opencode/qg_bakeoff_opencode] | opencode | qg_bakeoff_opencode | vesnianky | bare | ran | n/a | False | -80 | -80 | 0 | 0/0 low-N | 1/1 low-N | 0/1 low-N | 0 | 0 | 1 | 1.0 |
| openrouter/test/m [opencode/qg_bakeoff_opencode] | opencode | qg_bakeoff_opencode | vesnianky | tooled | ran | n/a | False | 30 | 30 | 0 | 0/0 low-N | 1/1 low-N | 0/1 low-N | 0 | 0 | 1 | 1.0 |

## Totals With Anchor

| model | arm | passages | model judgment | live admissible | U honesty | M alignment headline | true unsupported | missing | invalid | inadmissible | tools | wall_s |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| openrouter/test/m [opencode/qg_bakeoff_opencode] | bare | 1 | -80 | -80 | 0/0 low-N | 1/1 low-N | 0/1 low-N | 0 | 0 | 0 | 1 | 1.0 |
| openrouter/test/m [opencode/qg_bakeoff_opencode] | tooled | 1 | 30 | 30 | 0/0 low-N | 1/1 low-N | 0/1 low-N | 0 | 0 | 0 | 1 | 1.0 |

## Harness Lift With Anchor

Lift = tooled model judgment − bare model judgment (positive = the harness helps),
over PAIRED passages only (both arms on disk for that model+passage).
M alignment is the discriminating fraction; low-N marks denominators below 10.

| model | paired passages | tooled model judgment | bare model judgment | harness_lift | tooled M alignment | bare M alignment |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| openrouter/test/m [opencode/qg_bakeoff_opencode] | 1 | 30 | -80 | 110 | 1/1 low-N | 1/1 low-N |

## Totals Without Anchor

| model | arm | passages | model judgment | live admissible | U honesty | M alignment headline | true unsupported | missing | invalid | inadmissible | tools | wall_s |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |

## Harness Lift Without Anchor

Lift = tooled model judgment − bare model judgment (positive = the harness helps),
over PAIRED passages only (both arms on disk for that model+passage).
M alignment is the discriminating fraction; low-N marks denominators below 10.

| model | paired passages | tooled model judgment | bare model judgment | harness_lift | tooled M alignment | bare M alignment |
| --- | ---: | ---: | ---: | ---: | --- | --- |
