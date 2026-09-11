### `DEPLOYMENT_REQUIRED`

Only after production QG passes, dispatch the canonical manual `Deploy to
GitHub Pages` workflow on `main` and wait for success. Its head must contain the
recorded publication merge. Use `verify-deployment --workflow-run-id <id> --url
<production-url> --out <external-runtime-receipt.json>`, then record that strict
`deployment` artifact. The verifier queries the exact Actions run, rejects push
events and runs created before the recorded QG pass, proves publication
ancestry, and fetches production; it writes a receipt only when production
exposes the build's unique immutable workflow-head marker and the module
response contains the exact target marker. A
successful workflow for another SHA, a generic HTTP 200, or a stale marker is
not deployment proof. Completion requires the deployment receipt; certification
alone is not terminal for goal `deploy`.
