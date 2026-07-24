"""Contract tests for the Hramatka lesson-engine API boundary."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api import hramatka_router


def _write_vesum_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)"
        )
        conn.execute(
            "INSERT INTO forms VALUES (?, ?, ?, ?)",
            ("книги", "книга", "noun", "noun:inanim:f:np"),
        )


@pytest.fixture()
def hramatka(tmp_path, monkeypatch):
    db_path = tmp_path / "hramatka.sqlite3"
    support_dir = tmp_path / "support"
    baker_state = tmp_path / "baker-state.json"
    vesum_path = tmp_path / "vesum.db"
    _write_vesum_db(vesum_path)
    baker_state.write_text('{"state": "active"}', encoding="utf-8")
    monkeypatch.setattr(hramatka_router, "HRAMATKA_DB_PATH", db_path)
    monkeypatch.setattr(hramatka_router, "SUPPORT_DIR", support_dir)
    monkeypatch.setattr(hramatka_router, "BAKER_STATE_PATH", baker_state)
    monkeypatch.setattr(hramatka_router, "VESUM_DB_PATH", vesum_path)
    hramatka_router.initialize_hramatka_store()

    app = FastAPI()
    app.include_router(hramatka_router.router)
    return TestClient(app, raise_server_exceptions=False), support_dir, baker_state, vesum_path


def _ready_job(owner_id: str = "teacher-1") -> str:
    lesson_id = str(uuid4())
    hramatka_router.create_lesson_job(lesson_id, owner_id, hramatka_router.LessonJobState.QUEUED)
    hramatka_router.transition_lesson_job(lesson_id, hramatka_router.LessonJobState.BAKING)
    hramatka_router.transition_lesson_job(lesson_id, hramatka_router.LessonJobState.READY)
    return lesson_id


def _valid_support() -> dict:
    fixture = (
        Path("packages/activity-kit/src/fixtures/lu.lesson-support.v1.valid.fixture.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(fixture)


def test_support_endpoint_returns_only_ready_valid_sidecars(hramatka):
    client, support_dir, _, _ = hramatka
    lesson_id = _ready_job()
    support_dir.mkdir()
    (support_dir / f"{lesson_id}.json").write_text(
        json.dumps(_valid_support()), encoding="utf-8"
    )

    response = client.get(
        f"/api/hramatka/lessons/{lesson_id}/support",
        headers={"X-Hramatka-Owner": "teacher-1"},
    )

    assert response.status_code == 200
    assert response.json()["schema"] == "lu.lesson-support.v1"


def test_support_endpoint_hides_other_owners_and_never_returns_partial_lessons(hramatka):
    client, _, _, _ = hramatka
    lesson_id = str(uuid4())
    hramatka_router.create_lesson_job(lesson_id, "teacher-1", hramatka_router.LessonJobState.QUEUED)

    pending = client.get(
        f"/api/hramatka/lessons/{lesson_id}/support",
        headers={"X-Hramatka-Owner": "teacher-1"},
    )
    other_owner = client.get(
        f"/api/hramatka/lessons/{lesson_id}/support",
        headers={"X-Hramatka-Owner": "teacher-2"},
    )
    missing = client.get(
        f"/api/hramatka/lessons/{uuid4()}/support",
        headers={"X-Hramatka-Owner": "teacher-1"},
    )
    unauthenticated = client.get(f"/api/hramatka/lessons/{lesson_id}/support")

    assert pending.status_code == 409
    assert other_owner.status_code == 404
    assert missing.status_code == 404
    assert unauthenticated.status_code == 422


def test_support_endpoint_rejects_missing_or_invalid_ready_sidecars(hramatka):
    client, support_dir, _, _ = hramatka
    lesson_id = _ready_job()

    missing = client.get(
        f"/api/hramatka/lessons/{lesson_id}/support",
        headers={"X-Hramatka-Owner": "teacher-1"},
    )
    support_dir.mkdir()
    (support_dir / f"{lesson_id}.json").write_text('{"schema": "wrong"}', encoding="utf-8")
    malformed = client.get(
        f"/api/hramatka/lessons/{lesson_id}/support",
        headers={"X-Hramatka-Owner": "teacher-1"},
    )

    assert missing.status_code == 503
    assert malformed.status_code == 503


def test_verify_endpoint_batch_attests_vesum_forms_and_validates_payload(hramatka):
    client, _, _, _ = hramatka

    response = client.post(
        "/api/hramatka/linguistics/verify",
        json={"forms": ["книги", "вигадка"], "pos": "noun"},
    )
    oversized = client.post(
        "/api/hramatka/linguistics/verify",
        json={"forms": ["книги"] * 201},
    )
    blank = client.post("/api/hramatka/linguistics/verify", json={"forms": [" "]})

    assert response.status_code == 200
    assert response.json() == {
        "results": [
            {
                "form": "книги",
                "attested": True,
                "matches": [{"lemma": "книга", "pos": "noun", "tags": "noun:inanim:f:np"}],
            },
            {"form": "вигадка", "attested": False, "matches": []},
        ],
        "total": 2,
        "attested_count": 1,
    }
    assert oversized.status_code == 422
    assert blank.status_code == 422


def test_verify_endpoint_reports_unavailable_dictionary(hramatka, monkeypatch, tmp_path):
    client, _, _, _ = hramatka
    monkeypatch.setattr(hramatka_router, "VESUM_DB_PATH", tmp_path / "missing.db")

    response = client.post("/api/hramatka/linguistics/verify", json={"forms": ["книги"]})

    assert response.status_code == 503
    assert response.json()["detail"] == "VESUM dictionary unavailable"


def test_lesson_lifecycle_is_durable_idempotent_and_rejects_invalid_transitions(hramatka):
    lesson_id = str(uuid4())
    created = hramatka_router.create_lesson_job(lesson_id, "teacher-1")
    retried = hramatka_router.create_lesson_job(lesson_id, "teacher-1")

    assert created == retried
    assert hramatka_router.transition_lesson_job(
        lesson_id, hramatka_router.LessonJobState.QUEUED
    ).state is hramatka_router.LessonJobState.QUEUED
    assert hramatka_router.transition_lesson_job(
        lesson_id, hramatka_router.LessonJobState.BAKING
    ).state is hramatka_router.LessonJobState.BAKING
    assert hramatka_router.transition_lesson_job(
        lesson_id, hramatka_router.LessonJobState.FAILED
    ).state is hramatka_router.LessonJobState.FAILED
    assert hramatka_router.get_lesson_job(lesson_id).state is hramatka_router.LessonJobState.FAILED
    queued_failure_id = str(uuid4())
    hramatka_router.create_lesson_job(
        queued_failure_id, "teacher-1", hramatka_router.LessonJobState.QUEUED
    )
    assert hramatka_router.transition_lesson_job(
        queued_failure_id, hramatka_router.LessonJobState.FAILED
    ).state is hramatka_router.LessonJobState.FAILED
    with pytest.raises(hramatka_router.LessonTransitionError):
        hramatka_router.transition_lesson_job(lesson_id, hramatka_router.LessonJobState.BAKING)
    with pytest.raises(hramatka_router.LessonOwnershipError):
        hramatka_router.create_lesson_job(lesson_id, "teacher-2")


def test_readyz_requires_every_dependency_and_reports_each_check(hramatka, monkeypatch, tmp_path):
    client, _, baker_state, _ = hramatka

    healthy = client.get("/api/hramatka/readyz")
    baker_state.write_text('{"state": "paused"}', encoding="utf-8")
    unhealthy = client.get("/api/hramatka/readyz")
    monkeypatch.setattr(hramatka_router, "SCHEMA_PATHS", (tmp_path / "missing.schema.json",))
    schema_failure = client.get("/api/hramatka/readyz")

    assert healthy.status_code == 200
    assert healthy.json()["ready"] is True
    assert all(check["ok"] for check in healthy.json()["checks"].values())
    assert unhealthy.status_code == 503
    assert unhealthy.json()["checks"]["baker"]["ok"] is False
    assert schema_failure.status_code == 503
    assert schema_failure.json()["checks"]["schemas"]["ok"] is False
