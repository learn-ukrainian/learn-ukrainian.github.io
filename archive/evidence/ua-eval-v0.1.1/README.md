# Historical UA evaluation verification source

These two `.py.txt` files preserve the exact verifier sources pinned by the immutable v0.1.1 manifest. They are evidence snapshots, not supported modules or commands. The active v0.1.1 verifier resolves exactly three historical logical paths: the inherited runner to `../ua-eval-v0.1.0/run_codex_baseline.py.txt`, and the two verifier paths to the matching files here. All other artifact paths remain unchanged.

The original manifest bytes and artifact hashes are unchanged. Modified or missing archived source fails verification, with no fallback to current source. Active verification checks historical dataset/baseline reproduction; it does not certify the changed active runner or its new model policy. New Codex executions use the guarded active runner and require GPT-6 Astra.
