# Historical UA evaluation runner source

`run_codex_baseline.py.txt` preserves the exact source bytes pinned by the immutable v0.1.0 and inherited v0.1.1 release manifests. It is an evidence snapshot, not a supported Python module or launcher. Do not execute it or update its model labels: those labels describe the historical run.

The release verifier resolves only the historical logical artifact `scripts/projects/ua_eval_harness/run_codex_baseline.py` to this snapshot. Its original SHA-256 remains `06453da9cf0750aac5065650c510f4d03e1d7d2ef9ca21be1fefd719c1f1590b`. All other frozen artifact locations and all recorded manifests, hashes, and results remain unchanged. Missing or modified snapshot bytes fail verification; there is no fallback to the active runner.

New executions use `scripts/projects/ua_eval_harness/run_codex_baseline.py`, which independently requires GPT-6 Astra. Historical freeze verification does not certify that active implementation or any new model result.
