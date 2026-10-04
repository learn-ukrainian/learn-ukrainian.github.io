"""Real fixture lifecycle and same-database queue contamination regressions."""

from __future__ import annotations

from pathlib import Path

import pytest
from _v4_linguistic_context_fixture import stored_preparation
from _v4_packaged_runtime_fixture import produce_author_record
from _v4_shared_runtime_fixtures import assert_authorized_request, role_connection
from learn_ukrainian_v4_runtime import semantic_inputs
from test_v4_operation_lifecycle import claim
from test_v4_protected_parent_mechanism import _run_real_pair

from scripts.fleet_comms.request_executor import RequestExecutor

pytest_plugins = ("pytester",)


def leave_foreign_request(pg, root, monkeypatch):
    """Leave a genuinely eligible, deterministically oldest queued request."""
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_PG_DSN", pg.info.dsn)
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    with RequestExecutor(root=root) as executor:
        request = executor.create_request(recipient="claude", body="foreign queue fixture")
        executor.authorize_author_execution(
            request_id=request.request_id, slot_id="v4p-standard-correct-001", expected_seat="claude-sonnet-5"
        )
    with role_connection(pg, "hramatka_v4_control_writer") as conn:
        semantic_inputs.freeze_semantic_input(
            conn, request_id=request.request_id, snapshot=stored_preparation(conn, request.request_id)
        )
    pg.execute("UPDATE requests SET created_at='2000-01-01T00:00:00Z' WHERE request_id=%s", (request.request_id,))
    eligible = pg.execute(
        """SELECT r.request_id FROM requests r JOIN v4_execution_dispatch_bindings b USING (request_id)
        WHERE r.request_id=%s AND r.state='queued' AND r.expires_at::timestamptz > clock_timestamp()
        AND b.semantic_input_json IS NOT NULL
        AND NOT EXISTS (SELECT FROM v4_operation_authorizations o WHERE o.request_id=r.request_id)""",
        (request.request_id,),
    ).fetchone()
    assert eligible == {"request_id": request.request_id}
    return request.request_id


def test_real_pg_cluster_lifecycle_isolates_queued_requests(pytester):
    """Two ordered tests must use the actual fixtures on one module's server."""
    fixture_dir = Path(__file__).resolve().parent
    repo = fixture_dir.parents[2]
    pytester.makeini("[pytest]\n")
    pytester.makeconftest(
        f"""
        import sys
        sys.path.insert(0, {str(repo)!r})
        sys.path.insert(0, {str(fixture_dir)!r})
        pytest_plugins = ("_v4_shared_runtime_fixtures",)
        """
    )
    pytester.makepyfile(
        test_queue_lifecycle="""
        import psycopg
        import pytest
        from _v4_shared_runtime_fixtures import assert_authorized_request, role_connection
        from test_v4_operation_lifecycle import claim
        from test_v4_pg_isolation import leave_foreign_request

        previous = {}

        def test_01_leave_foreign_request(pg_cluster, tmp_path, monkeypatch):
            previous["request"] = leave_foreign_request(pg_cluster, tmp_path, monkeypatch)
            previous["database"] = pg_cluster.info.dbname
            previous["host"] = pg_cluster.info.host
            previous["port"] = pg_cluster.info.port
            previous["connection"] = psycopg.connect(pg_cluster.info.dsn, autocommit=True)

        def test_02_authorize_and_claim_own_request(pg_cluster, prepared):
            assert (pg_cluster.info.host, pg_cluster.info.port) == (previous["host"], previous["port"])
            assert pg_cluster.info.dbname != previous["database"]
            assert pg_cluster.execute("SELECT 1 FROM pg_database WHERE datname=%s",
                                      (previous["database"],)).fetchone() is None
            assert pg_cluster.execute("SELECT 1 FROM requests WHERE request_id=%s",
                                      (previous["request"],)).fetchone() is None
            try:
                with pytest.raises(psycopg.OperationalError):
                    previous["connection"].execute("SELECT 1")
            finally:
                previous["connection"].close()
            assert pg_cluster.execute("SELECT rolsuper FROM pg_roles WHERE rolname=current_user").fetchone()["rolsuper"]
            with psycopg.connect(pg_cluster.info.dsn, autocommit=True) as fresh:
                assert fresh.info.dbname == pg_cluster.info.dbname
            with role_connection(pg_cluster, "hramatka_v4_control_writer") as conn:
                assert_authorized_request(conn, prepared["identifier"], prepared["request_id"])
                assert claim(conn, prepared)["request_id"] == prepared["request_id"]
        """
    )
    result = pytester.runpytest_subprocess("-n", "0", "-q", "test_queue_lifecycle.py", timeout=60)
    result.assert_outcomes(passed=2)


@pytest.mark.parametrize("helper", ["prepared", "real_pair", "author_record"])
def test_authorizing_helpers_refuse_foreign_queued_request(pg_cluster, tmp_path, monkeypatch, request, helper):
    foreign = leave_foreign_request(pg_cluster, tmp_path / "foreign", monkeypatch)
    with pytest.raises(AssertionError, match="authorization request mismatch: expected .+, got " + foreign) as error:
        if helper == "prepared":
            request.getfixturevalue("prepared")
        else:
            wheel = request.getfixturevalue("built_wheel")
            signing = request.getfixturevalue("signing_resources")
            own_root = tmp_path / "own"
            own_root.mkdir()
            if helper == "real_pair":
                _run_real_pair(pg_cluster, own_root, monkeypatch, wheel, signing, defect=False)
            else:
                produce_author_record(own_root, pg_cluster, monkeypatch, wheel)
    own = pg_cluster.execute("SELECT request_id, state FROM requests WHERE request_id<>%s", (foreign,)).fetchone()
    assert own is not None and own["state"] == "queued"
    assert own["request_id"] in str(error.value)
    assert pg_cluster.execute("SELECT request_id FROM v4_operation_authorizations").fetchall() == [
        {"request_id": foreign}
    ]
    assert pg_cluster.execute("SELECT count(*) AS n FROM v4_execution_attempts").fetchone()["n"] == 0


def test_claim_helper_refuses_valid_foreign_authorization(pg_cluster, prepared, tmp_path, monkeypatch):
    # claim selects the authorization digest, so queue pollution alone cannot
    # redirect it. Keep a valid authorization but expect a different request.
    expected = leave_foreign_request(pg_cluster, tmp_path / "expected", monkeypatch)
    foreign = prepared["request_id"]
    with role_connection(pg_cluster, "hramatka_v4_control_writer") as conn:
        with pytest.raises(AssertionError, match=f"claim request mismatch: expected {expected}, got {foreign}"):
            claim(conn, {**prepared, "request_id": expected})
    assert pg_cluster.execute("SELECT request_id FROM v4_execution_attempts").fetchall() == [{"request_id": foreign}]


def test_authorization_guard_refuses_missing_authorization(pg_cluster):
    with pytest.raises(AssertionError, match="no authorization for expected request missing-request"):
        assert_authorized_request(pg_cluster, None, "missing-request")
    with pytest.raises(AssertionError, match="authorization request mismatch: expected missing-request, got None"):
        assert_authorized_request(pg_cluster, "nonexistent-authorization", "missing-request")
