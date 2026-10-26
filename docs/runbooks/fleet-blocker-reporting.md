# Report Fleet blockers

Send ordinary owned blocker reports through the existing `epics` Fleet authority.
Use `cto` for explicit operator escalation. Fleet Comms remains the durable
message authority; its delivery and inbox procedures are unchanged.

An ordinary report can name the blocker, current state, owner, and next action.
State unknown coverage or uncertain attribution truthfully. A report does not
prove resolution or task delivery; support those claims with tool evidence.

Blocker reports do not require a complete ledger, delta comparison, exact body
format, receipt file, generation, custody inventory, or baseline publication.
Existing private reports and receipts remain historical evidence. Do not erase
or rewrite them.

The existing inbox checkpoint still reports aged `needs_finalize` tasks through
Fleet Comms. `LU_NEEDS_FINALIZE_MAX_AGE_MINUTES` defaults to 30 positive finite
minutes, measured from `finished_at`. Unknown age or configuration requires
attention. Alert deduplication and private diagnostic handling are unchanged.
