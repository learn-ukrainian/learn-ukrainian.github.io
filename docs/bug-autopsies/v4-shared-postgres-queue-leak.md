# V4 tests dequeue another test's shared Postgres request

**Date:** 2026-10-03
**Issue:** #9595 (parent #6321)
**Category:** test-isolation / work-queue
**Affected tests:** V4 Postgres consumers in `tests/projects/open_model_data/`
and `tests/test_mcp_sources_v4_invocation_recording.py`

## Outcome

**Symptom:** unrelated changes failed the merge queue when an operation claim
or frozen prompt belonged to an earlier test's request. The reported failures
were `test_reviewer_cannot_substitute_target_evidence_or_author_origin[row]`
(run 37119510951, attempt 1) and
`test_frozen_target_is_actual_prompt_content_and_immutable`
(merge-group run 37146308141).

**Root cause:** the module-scoped `pg_cluster` fixture shared database rows
between tests. Production `OperationStore.authorize` dequeues the oldest
eligible queued request with frozen semantic input and no authorization. Its
caller supplies no request id. Test helpers froze their own request and assumed
the next authorization would select it. A preceding test's leftover eligible
request could be selected instead, leaving the current request queued for the
next test. `claim` itself selects an exact authorization digest.

**Why it was flaky:** test order and xdist assignment determined which leftover
requests a helper could encounter. Passing independently did not establish
isolation across the fixture's module lifetime.

## Fix

Keep one PostgreSQL server per module and apply the schema once to a template
database. Close its connection and disable template connections. Give every
test a fresh `CREATE DATABASE ... TEMPLATE ...` clone, then close its fixture
connection and drop the clone, terminating any remaining clone connections.
The yielded superuser connection and its DSN identify the test's database;
roles remain cluster-wide so role-login tests continue to work. No production
runtime or queue semantics change.

Template cloning follows [PostgreSQL's documented database creation
behavior](https://www.postgresql.org/docs/current/sql-createdatabase.html).
The template stays free of test requests, and its migrations are reused rather
than executed for each test.

## Guard and regression

**Prevention:** each authorizing helper resolves the issued authorization's
request id and asserts it matches the request just frozen, before claiming or
executing; `test_v4_pg_isolation.py` pins the per-test database isolation.

`prepared`, `_run_real_pair.run`, and `produce_author_record` resolve the
issued authorization's request id and assert that it matches the request just
frozen, before claiming or executing. Claiming helpers also check the returned
request id. Mismatch messages contain the expected and actual ids.

`test_v4_pg_isolation.py` runs a separate pytest session with the real shared
fixture module. Its first test leaves an eligible, deliberately older queued
request; its second authorizes and claims its own request on the same server.
It also checks distinct databases, removal of the previous clone, superuser
access, and reconnecting through the yielded DSN. Temporarily restoring the
original module-shared fixture makes the second test fail during `prepared`
with an authorization request mismatch.

Each authorizing helper has a same-database contamination test that checks the
guard fires before any execution attempt. The lifecycle `claim` helper's
negative test supplies a valid authorization for one request while expecting
another request id; merely adding a queued request cannot redirect an exact
digest claim. Missing authorizations have explicit diagnostic coverage.
