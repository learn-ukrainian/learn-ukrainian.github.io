# Fresh-build writer harness recovery

**Writer harness recovery (#9525).** `writer_harness_exhausted` stops a lesson after three
dispatch/execution/harvesting defects following an attempted writer dispatch, across input changes.
Content validation and caller errors before dispatch spend no harness budget; typed `rate_limited`
and `timeout` outcomes (including subprocess timeouts) also spend none, because capacity trouble
must not become a permanent lesson stop. They still fail the current build; retry explicitly after
capacity recovers. To reset the cap, first stop all builds and writer tasks for that lesson, preserve
its task records and sidecar as local diagnostic evidence, and fix the underlying defect. Then remove
only `lesson-N.writer-harness.yaml` and its `.lock` digest from that lesson's evidence state directory
and retry once. Keep the regeneration ledger and `.mutex` files; removing a mutex can defeat locking.
