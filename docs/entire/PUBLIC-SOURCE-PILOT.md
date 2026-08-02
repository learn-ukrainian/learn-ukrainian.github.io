# Public source Entire pilot

This receipt onboards `learn-ukrainian/learn-ukrainian.github.io` as the source
repository for a bounded Entire 0.8.42 canary.

Checkpoint bodies are stored only in the private
`learn-ukrainian/entire-checkpoints-private` repository. The public product
origin must retain zero `entire/*` refs and zero session bodies. Entire remains
optional and non-authoritative; GitHub, Fleet Comms, Monitor, rollover, leases,
and formal review remain authoritative.

The committed `.entire/settings.json` is the body-free project binding Entire.io
uses to locate the separate checkpoint repository. Agent enablement and PII or
custom redaction rules remain local to each explicitly enabled worktree.

The public issue receipt in #6165 records the checkpoint identifier, source
commit, private destination ref, leakage verdict, retry result, and authenticated
Entire activity result without reproducing a prompt, response, transcript, or
generated summary.
