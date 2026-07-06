# lm_eval emitter for qg_bakeoff

`scripts/audit/qg_bakeoff.py --emit-lm-eval <dir>` writes `eval-results/<model>/results_<created_at>.json`.
The timestamp is copied from artifact `created_at`; missing legacy timestamps become `results_unknown.json`.
Each JSON has `config_general.model_name` set to the qg_bakeoff model pin.
`qg_factuality_model_judgment.score` maps to the scorecard model judgment aggregate.
`qg_factuality_u_honesty.score` maps to the U-fabrication honesty rate.
`qg_factuality_m_alignment.score` maps to the M-fabrication alignment rate.
`qg_factuality_harness_lift.score` maps to tooled minus bare model judgment on paired cells only.
Multi-run exports use the same run-aware means printed in the scorecard.
Low-N flags, run counts, arm identity, transport, and entrypoint live under each task's `qg_meta`.
Legacy/missing fields set `qg_meta.partial=true` with `partial_reasons` instead of blocking export.
A leaderboard maintainer can copy each model directory under their `eval-results/` tree.
Their loader should read `results.<task>.<metric>` floats and ignore `qg_meta` for ranking.
Keep qg_bakeoff as a factuality track, and regenerate after rescoring or new matrix runs.
