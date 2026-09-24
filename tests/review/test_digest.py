"""Tests for module digest generator (#8430 WP 15 Part R2a).

Verifies:
- Digest schema conformity against schemas/module-digest-v1.schema.json;
- Every field computed accurately from engine state files (occurrences, names, grammar, dialogue);
- Dialogue address forms classification (second-person s/p and vocatives);
- Question provenance handling;
- Sort ordering of occurrences, names, and address forms;
- Determinism and byte-stability across multiple runs;
- Correct mode (0o644) and lock sidecar integrity;
- Up-to 1 boundary case (empty sources and lessons);
- --check mode detection of byte drift;
- Failure closed on missing or unlocked inputs;
- CLI invocation and help output.
"""

from __future__ import annotations

import builtins
import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.curriculum.evidence import lock
from scripts.review.digest import (
    DIGEST_SCHEMA,
    GENERATOR_VERSION,
    DigestError,
    build_digest,
    check_digest,
    classify_address_form,
    codes,
    digest_output_path,
    validate_digest,
    write_digest,
)

pytestmark = pytest.mark.reads_content

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_BIN = sys.executable

PLAN_SCHEMA_PATH = REPO_ROOT / "schemas/module-plan-v2.schema.json"
RECEIPTS_SCHEMA_PATH = REPO_ROOT / "schemas/resolution-receipts-v1.schema.json"
OBSERVED_SCHEMA_PATH = REPO_ROOT / "schemas/learner-observed-v1.schema.json"
DIGEST_SCHEMA_PATH = REPO_ROOT / "schemas/module-digest-v1.schema.json"


@contextlib.contextmanager
def record_file_reads(monkeypatch: pytest.MonkeyPatch) -> Generator[list[str], None, None]:
    """Record every file open/read operation made during the context."""
    opened: list[str] = []

    real_builtin_open = builtins.open
    real_io_open = io.open
    real_os_open = os.open
    real_read_bytes = Path.read_bytes
    real_read_text = Path.read_text

    def _record_path(file: Any) -> None:
        if isinstance(file, (str, Path)):
            opened.append(str(file))
        elif isinstance(file, bytes):
            opened.append(file.decode(errors="replace"))
        elif isinstance(file, int):
            opened.append(f"<fd:{file}>")

    def mock_builtin_open(file: Any, *args: Any, **kwargs: Any) -> Any:
        _record_path(file)
        return real_builtin_open(file, *args, **kwargs)

    def mock_io_open(file: Any, *args: Any, **kwargs: Any) -> Any:
        _record_path(file)
        return real_io_open(file, *args, **kwargs)

    def mock_os_open(path: Any, *args: Any, **kwargs: Any) -> int:
        _record_path(path)
        return real_os_open(path, *args, **kwargs)

    def mock_read_bytes(self: Path) -> bytes:
        _record_path(self)
        return real_read_bytes(self)

    def mock_read_text(self: Path, *args: Any, **kwargs: Any) -> str:
        _record_path(self)
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", mock_builtin_open)
    monkeypatch.setattr(io, "open", mock_io_open)
    monkeypatch.setattr(os, "open", mock_os_open)
    monkeypatch.setattr(Path, "read_bytes", mock_read_bytes)
    monkeypatch.setattr(Path, "read_text", mock_read_text)

    yield opened


def _load_linguistic_seeds() -> tuple[str, str, str, str, str, str, str]:
    """Dynamically load Ukrainian tokens from existing repository files without typing them.

    Returns:
        ty_str: 2nd-person singular pronoun
        vy_str: 2nd-person plural pronoun
        voc_str: word with vocative reading
        voc_tag: VESUM tag with vocative (v_kly)
        q_str: token for question selection
        name_str: token for proper noun / name
        l2_str: token for lesson 2 occurrence
    """
    base_req = yaml.safe_load(
        (REPO_ROOT / "curriculum/l2-uk-en/evidence/a1/_base.request.yaml").read_text(encoding="utf-8")
    )
    ty_str = next(w["lemma"] for w in base_req["words"] if "2nd pers sing" in w.get("note", ""))
    vy_str = next(w["lemma"] for w in base_req["words"] if "2nd pers plur" in w.get("note", ""))

    synii_data = json.loads((REPO_ROOT / "tests/fixtures/vesum_synii_analyses.json").read_text(encoding="utf-8"))
    voc_str = synii_data["word"]
    voc_tag = next(m["tags"] for m in synii_data["matches"] if "v_kly" in m["tags"])

    five_lemmas = yaml.safe_load((REPO_ROOT / "tests/fixtures/a1_five_lemmas_request.yaml").read_text(encoding="utf-8"))
    name_str = five_lemmas["words"][0]["lemma"]
    q_str = five_lemmas["words"][2]["lemma"]
    l2_str = five_lemmas["words"][3]["lemma"]

    return ty_str, vy_str, voc_str, voc_tag, q_str, name_str, l2_str


def _setup_two_lesson_fixture(root: Path, level: str = "a1", slug: str = "mod-fixture") -> dict[str, Path]:
    """Build a complete two-lesson fixture tree adhering strictly to plan v2, receipts, and observed schemas."""
    ty_str, vy_str, voc_str, voc_tag, q_str, name_str, l2_str = _load_linguistic_seeds()

    plans_dir = root / f"curriculum/l2-uk-en/lesson-plans/{level}"
    state_dir = root / f"curriculum/l2-uk-en/evidence/{level}/_state/{slug}"
    mdx_dir = root / f"site/src/content/docs/{level}/{slug}"
    schemas_dir = root / "schemas"

    plans_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    mdx_dir.mkdir(parents=True, exist_ok=True)
    schemas_dir.mkdir(parents=True, exist_ok=True)

    for s_name in (
        "module-plan-v2.schema.json",
        "resolution-receipts-v1.schema.json",
        "learner-observed-v1.schema.json",
        "module-digest-v1.schema.json",
    ):
        (schemas_dir / s_name).write_bytes((REPO_ROOT / "schemas" / s_name).read_bytes())

    # 1. Module plan v2
    plan_doc: dict[str, Any] = {
        "plan_schema": 2,
        "module": slug,
        "level": level,
        "sequence": 1,
        "slug": slug,
        "version": "1",
        "title": "Fixture Module Title",
        "arc_ref": {"level": level, "position": 1},
        "evidence_ref": {"path": f"curriculum/l2-uk-en/evidence/{level}/{slug}.yaml", "sha256": "0" * 64},
        "lessons": [
            {
                "n": 1,
                "slug": "l01",
                "title": "Lesson 1",
                "kind": "teach",
                "job": "Demonstrate pronouns and vocatives in conversation",
                "rationale": "Initial communicative encounter",
                "word_target": 10,
                "inventory": {
                    "vocabulary": {
                        "core": [
                            {"lemma": "pron-2s", "evidence": "W-1", "forms": ["noun:anim:s:v_naz:pron:pers:2"]},
                            {"lemma": "pron-2p", "evidence": "W-2", "forms": ["noun:anim:p:v_naz:pron:pers:2"]},
                        ],
                        "incidental": [
                            {"lemma": "synii-adj", "evidence": "W-3"},
                        ],
                        "recycled": ["W-4"],
                    }
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "teach": "Teach greetings and address forms",
                        "introduces": {
                            "letters": [],
                            "grammar": ["G-a1-001"],
                            "vocabulary": ["W-1", "W-2"],
                        },
                        "uses": {"grammar": [], "vocabulary": []},
                        "evidence": ["T-001"],
                        "practice": ["a1"],
                    },
                    {
                        "id": "s2",
                        "kind": "teach",
                        "teach": "Expand dialogue vocabulary",
                        "introduces": {
                            "letters": [],
                            "grammar": ["G-a1-002"],
                            "vocabulary": [],
                        },
                        "uses": {"grammar": [], "vocabulary": ["W-3", "W-4"]},
                        "evidence": ["T-002"],
                        "practice": ["a2"],
                    },
                ],
                "activities": [
                    {"id": "a1", "type": "quiz", "placement": "inline", "focus": "grammar"},
                    {"id": "a2", "type": "quiz", "placement": "inline", "focus": "grammar"},
                ],
                "dialogue": {
                    "step": "s1",
                    "situation": "Meeting at a city landmark",
                    "setting": "City center cafe table",
                    "speakers": [
                        {"name": "SpeakerOne", "role": "host", "gender": "m", "evidence": "W-5"},
                        {"name": "SpeakerTwo", "role": "guest", "gender": "f", "evidence": "W-5"},
                    ],
                    "places": [
                        {"name": "Kyiv", "evidence": "W-100"},
                    ],
                    "register": "informal",
                    "target_grammar": "Second person pronouns and vocative address",
                    "evidence": ["T-001"],
                },
            },
            {
                "n": 2,
                "slug": "l02",
                "title": "Lesson 2",
                "kind": "teach",
                "job": "Describe basic domestic objects",
                "rationale": "Vocabulary expansion",
                "word_target": 10,
                "inventory": {
                    "vocabulary": {
                        "core": [
                            {"lemma": "object-table", "evidence": "W-6", "forms": ["noun:inanim:m:v_naz"]},
                        ],
                        "incidental": [],
                        "recycled": [],
                    }
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "teach": "Name furniture items",
                        "introduces": {
                            "letters": [],
                            "grammar": ["G-a1-003"],
                            "vocabulary": ["W-6"],
                        },
                        "uses": {"grammar": [], "vocabulary": []},
                        "evidence": ["T-003"],
                        "practice": ["a3"],
                    }
                ],
                "activities": [
                    {"id": "a3", "type": "quiz", "placement": "inline", "focus": "vocabulary"},
                ],
            },
        ],
    }

    # Validate plan v2 against real schema
    plan_schema = json.loads(PLAN_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator(plan_schema).validate(plan_doc)
    plan_path = plans_dir / f"{slug}.yaml"
    plan_path.write_bytes(yaml.safe_dump(plan_doc, allow_unicode=True, sort_keys=False).encode("utf-8"))

    # 2. MDX files
    mdx_1 = mdx_dir / "1.mdx"
    mdx_2 = mdx_dir / "2.mdx"
    mdx_1.write_bytes(b"# Lesson 1 Content\n")
    mdx_2.write_bytes(b"# Lesson 2 Content\n")

    # 3. Lesson 1 files
    # Provenance
    prov_1 = {
        "provenance_schema": 1,
        "lesson": {"level": level, "slug": slug, "n": 1},
        "spans": [
            {
                "tab": "urok",
                "step": "s1",
                "activity": None,
                "item": None,
                "block": "dialogue_0",
                "source": "writer_prose",
                "ref": None,
                "text": ty_str,
            },
            {
                "tab": "urok",
                "step": "s1",
                "activity": None,
                "item": None,
                "block": "dialogue_1",
                "source": "writer_prose",
                "ref": None,
                "text": vy_str,
            },
            {
                "tab": "urok",
                "step": "s1",
                "activity": None,
                "item": None,
                "block": "dialogue_2",
                "source": "writer_prose",
                "ref": None,
                "text": voc_str,
            },
            {
                "tab": "urok",
                "step": "s1",
                "activity": None,
                "item": None,
                "block": "dialogue_3",
                "source": "record",
                "ref": "W-4",
                "text": q_str,
            },
            {
                "tab": "urok",
                "step": "s1",
                "activity": None,
                "item": None,
                "block": "lead_in",
                "source": "writer_prose",
                "ref": None,
                "text": name_str,
            },
        ],
    }
    prov_1_path = state_dir / "lesson-1.provenance.yaml"
    lock.atomic_write(prov_1_path, yaml.safe_dump(prov_1, allow_unicode=True, sort_keys=False).encode("utf-8"))

    # Resolutions
    receipts_1 = {
        "resolutions_schema": 1,
        "lesson": {"level": level, "slug": slug, "n": 1},
        "inputs": {
            "expanded_sha256": "0" * 64,
            "allowlist_sha256": "0" * 64,
            "words_lock": "0" * 64,
            "vesum": "0" * 64,
            "trie_digest": "0" * 64,
        },
        "tokens": [
            {
                "unit": {"tab": "urok", "step": "s1", "activity": None, "item": None, "block": "dialogue_0"},
                "offset": 0,
                "token": ty_str,
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-1"],
                "selected": {"record": "W-1", "forms": ["noun:anim:s:v_naz:pron:pers:2"], "stressed": ty_str},
                "provenance": "deterministic",
            },
            {
                "unit": {"tab": "urok", "step": "s1", "activity": None, "item": None, "block": "dialogue_1"},
                "offset": 0,
                "token": vy_str,
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-2"],
                "selected": {"record": "W-2", "forms": ["noun:anim:p:v_naz:pron:pers:2"], "stressed": vy_str},
                "provenance": "deterministic",
            },
            {
                "unit": {"tab": "urok", "step": "s1", "activity": None, "item": None, "block": "dialogue_2"},
                "offset": 0,
                "token": voc_str,
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-3"],
                "selected": {"record": "W-3", "forms": [voc_tag], "stressed": voc_str},
                "provenance": "deterministic",
            },
            {
                "unit": {"tab": "urok", "step": "s1", "activity": None, "item": None, "block": "dialogue_3"},
                "offset": 0,
                "token": q_str,
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-4"],
                "selected": {"record": "W-4", "forms": ["noun:inanim:f:v_naz"], "stressed": q_str},
                "provenance": "question:reviewer:Q-101",
            },
            {
                "unit": {"tab": "urok", "step": "s1", "activity": None, "item": None, "block": "lead_in"},
                "offset": 0,
                "token": name_str,
                "surface": "proper_noun",
                "class": "resolved",
                "candidates": ["W-5"],
                "selected": {"record": "W-5", "forms": ["noun:anim:f:v_naz:prop:fname"], "stressed": name_str},
                "provenance": "deterministic",
            },
        ],
    }
    receipts_schema = json.loads(RECEIPTS_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator(receipts_schema).validate(receipts_1)
    res_1_path = state_dir / "lesson-1.resolutions.yaml"
    lock.write(res_1_path, lock.yaml_bytes(receipts_1))

    # Observed
    obs_1 = {
        "observed_schema": 1,
        "lesson": {"level": level, "slug": slug, "n": 1},
        "records": [
            {
                "id": "W-1",
                "role": "taught",
                "forms": [
                    {
                        "tags": "noun:anim:s:v_naz:pron:pers:2",
                        "count_by_tab": {"urok": 1, "slovnyk": 0, "vpravy": 0, "resursy": 0},
                    }
                ],
            },
            {
                "id": "W-2",
                "role": "drilled",
                "forms": [
                    {
                        "tags": "noun:anim:p:v_naz:pron:pers:2",
                        "count_by_tab": {"urok": 1, "slovnyk": 0, "vpravy": 0, "resursy": 0},
                    }
                ],
            },
            {
                "id": "W-3",
                "role": "incidental",
                "forms": [{"tags": voc_tag, "count_by_tab": {"urok": 1, "slovnyk": 0, "vpravy": 0, "resursy": 0}}],
            },
            {
                "id": "W-4",
                "role": "recycled",
                "forms": [
                    {
                        "tags": "noun:inanim:f:v_naz",
                        "count_by_tab": {"urok": 1, "slovnyk": 0, "vpravy": 0, "resursy": 0},
                    }
                ],
            },
            {
                "id": "W-5",
                "role": "name",
                "forms": [
                    {
                        "tags": "noun:anim:f:v_naz:prop:fname",
                        "count_by_tab": {"urok": 1, "slovnyk": 0, "vpravy": 0, "resursy": 0},
                    }
                ],
            },
        ],
        "untaught_forms": {
            "count": 1,
            "share": 0.2,
            "forms": [{"record": "W-3", "tags": voc_tag, "category": "v_kly"}],
        },
    }
    obs_schema = json.loads(OBSERVED_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator(obs_schema).validate(obs_1)
    obs_1_path = state_dir / "lesson-1.observed.yaml"
    lock.write(obs_1_path, lock.yaml_bytes(obs_1))

    # 4. Lesson 2 files
    prov_2 = {
        "provenance_schema": 1,
        "lesson": {"level": level, "slug": slug, "n": 2},
        "spans": [
            {
                "tab": "urok",
                "step": "s1",
                "activity": None,
                "item": None,
                "block": 0,
                "source": "record",
                "ref": "W-6",
                "text": l2_str,
            },
        ],
    }
    prov_2_path = state_dir / "lesson-2.provenance.yaml"
    lock.atomic_write(prov_2_path, yaml.safe_dump(prov_2, allow_unicode=True, sort_keys=False).encode("utf-8"))

    receipts_2 = {
        "resolutions_schema": 1,
        "lesson": {"level": level, "slug": slug, "n": 2},
        "inputs": {
            "expanded_sha256": "0" * 64,
            "allowlist_sha256": "0" * 64,
            "words_lock": "0" * 64,
            "vesum": "0" * 64,
            "trie_digest": "0" * 64,
        },
        "tokens": [
            {
                "unit": {"tab": "urok", "step": "s1", "activity": None, "item": None, "block": 0},
                "offset": 0,
                "token": l2_str,
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-6"],
                "selected": {"record": "W-6", "forms": ["noun:inanim:m:v_naz"], "stressed": l2_str},
                "provenance": "deterministic",
            }
        ],
    }
    Draft202012Validator(receipts_schema).validate(receipts_2)
    res_2_path = state_dir / "lesson-2.resolutions.yaml"
    lock.write(res_2_path, lock.yaml_bytes(receipts_2))

    obs_2 = {
        "observed_schema": 1,
        "lesson": {"level": level, "slug": slug, "n": 2},
        "records": [
            {
                "id": "W-6",
                "role": "taught",
                "forms": [
                    {
                        "tags": "noun:inanim:m:v_naz",
                        "count_by_tab": {"urok": 1, "slovnyk": 0, "vpravy": 0, "resursy": 0},
                    }
                ],
            },
        ],
        "untaught_forms": {
            "count": 0,
            "share": 0.0,
            "forms": [],
        },
    }
    Draft202012Validator(obs_schema).validate(obs_2)
    obs_2_path = state_dir / "lesson-2.observed.yaml"
    lock.write(obs_2_path, lock.yaml_bytes(obs_2))

    return {
        "plan": plan_path,
        "mdx_1": mdx_1,
        "mdx_2": mdx_2,
        "prov_1": prov_1_path,
        "res_1": res_1_path,
        "obs_1": obs_1_path,
        "prov_2": prov_2_path,
        "res_2": res_2_path,
        "obs_2": obs_2_path,
    }


def test_classify_address_form() -> None:
    """Classify address forms with second-person precedence over vocative."""
    # Second person singular
    assert classify_address_form(["noun:anim:s:v_naz:pron:pers:2"]) == ("second_person", "s")
    # Second person plural
    assert classify_address_form(["noun:anim:p:v_naz:pron:pers:2"]) == ("second_person", "p")
    # Precedence: second person wins even if v_kly tag is present
    mixed = ["noun:anim:s:v_naz:pron:pers:2", "noun:anim:s:v_kly:compb"]
    assert classify_address_form(mixed) == ("second_person", "s")
    # Vocative alone
    assert classify_address_form(["noun:anim:m:v_kly"]) == ("vocative", None)
    # Non-address form returns None
    assert classify_address_form(["noun:inanim:m:v_naz", "verb:perf:past:m"]) is None


def test_build_digest_upto_3_every_field(tmp_path: Path) -> None:
    """Build digest up to 3 and verify all fields against expectations and module-digest-v1 schema."""
    paths = _setup_two_lesson_fixture(tmp_path)
    doc = build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)

    # Validate against schemas/module-digest-v1.schema.json
    validate_digest(doc)

    assert doc["digest_schema"] == DIGEST_SCHEMA
    assert doc["generator_version"] == GENERATOR_VERSION
    assert doc["level"] == "a1"
    assert doc["slug"] == "mod-fixture"
    assert doc["up_to"] == 3
    assert doc["plan_sha256"] == hashlib.sha256(paths["plan"].read_bytes()).hexdigest()

    # Sources
    sources = doc["sources"]
    assert len(sources) == 2
    assert sources[0]["lesson"] == 1
    assert sources[0]["mdx_sha256"] == hashlib.sha256(paths["mdx_1"].read_bytes()).hexdigest()
    assert sources[0]["observed_sha256"] == hashlib.sha256(paths["obs_1"].read_bytes()).hexdigest()
    assert sources[0]["resolutions_sha256"] == hashlib.sha256(paths["res_1"].read_bytes()).hexdigest()
    assert sources[0]["provenance_sha256"] == hashlib.sha256(paths["prov_1"].read_bytes()).hexdigest()

    assert sources[1]["lesson"] == 2
    assert sources[1]["mdx_sha256"] == hashlib.sha256(paths["mdx_2"].read_bytes()).hexdigest()

    # Lessons
    lessons = doc["lessons"]
    assert len(lessons) == 2

    # Lesson 1
    l1 = lessons[0]
    assert l1["lesson"] == 1
    assert len(l1["occurrences"]) == 4  # W-1, W-2, W-3, W-4 (W-5 is a name)
    assert len(l1["names"]) == 1  # W-5

    # Check occurrences fields
    occ_by_rec = {o["record"]: o for o in l1["occurrences"]}
    assert set(occ_by_rec.keys()) == {"W-1", "W-2", "W-3", "W-4"}

    w1 = occ_by_rec["W-1"]
    assert w1["pos"] == "noun"
    assert w1["forms"] == ["noun:anim:s:v_naz:pron:pers:2"]
    assert w1["role"] == "taught"
    assert w1["chosen_by"] == "resolver"
    assert w1["question_ref"] is None
    assert w1["locator"]["block"] == "dialogue_0"
    assert w1["span_source"] == "writer_prose"
    assert w1["span_ref"] is None

    w4 = occ_by_rec["W-4"]
    assert w4["role"] == "recycled"
    assert w4["chosen_by"] == "question"
    assert w4["question_ref"] == "question:reviewer:Q-101"
    assert w4["span_source"] == "record"
    assert w4["span_ref"] == "W-4"

    # Check names fields
    name_entry = l1["names"][0]
    assert name_entry["record"] == "W-5"
    assert name_entry["pos"] == "noun"
    assert "role" not in name_entry
    assert name_entry["chosen_by"] == "resolver"

    # Check grammar
    assert l1["grammar"]["taught"] == ["G-a1-001", "G-a1-002"]
    assert len(l1["grammar"]["encountered_unexplained"]) == 1
    assert l1["grammar"]["encountered_unexplained"][0] == {
        "record": "W-3",
        "tags": occ_by_rec["W-3"]["forms"][0],
        "category": "v_kly",
    }

    # Check dialogue
    diag = l1["dialogue"]
    assert diag is not None
    assert diag["step"] == "s1"
    assert diag["setting"] == "City center cafe table"
    assert diag["register"] == "informal"
    assert diag["places"] == ["Kyiv"]
    assert diag["speakers"] == [
        {"name": "SpeakerOne", "role": "host", "gender": "m"},
        {"name": "SpeakerTwo", "role": "guest", "gender": "f"},
    ]

    # Check address forms
    address_forms = diag["address_forms"]
    assert len(address_forms) == 3
    af_by_rec = {af["record"]: af for af in address_forms}
    assert af_by_rec["W-1"]["kind"] == "second_person"
    assert af_by_rec["W-1"]["number"] == "s"
    assert af_by_rec["W-2"]["kind"] == "second_person"
    assert af_by_rec["W-2"]["number"] == "p"
    assert af_by_rec["W-3"]["kind"] == "vocative"
    assert af_by_rec["W-3"]["number"] is None

    # Lesson 2
    l2 = lessons[1]
    assert l2["lesson"] == 2
    assert len(l2["occurrences"]) == 1
    assert l2["occurrences"][0]["record"] == "W-6"
    assert l2["names"] == []
    assert l2["grammar"]["taught"] == ["G-a1-003"]
    assert l2["grammar"]["encountered_unexplained"] == []
    assert l2["dialogue"] is None


def test_build_digest_upto_1_empty(tmp_path: Path) -> None:
    """--up-to 1 yields empty sources and lessons arrays."""
    paths = _setup_two_lesson_fixture(tmp_path)
    doc = build_digest("a1", "mod-fixture", 1, repo_root=tmp_path)
    validate_digest(doc)

    assert doc["up_to"] == 1
    assert doc["sources"] == []
    assert doc["lessons"] == []
    assert doc["plan_sha256"] == hashlib.sha256(paths["plan"].read_bytes()).hexdigest()


def test_write_digest_byte_stability_and_lock(tmp_path: Path) -> None:
    """Writing digest twice yields identical bytes, 0o644 mode, and matching lock."""
    _setup_two_lesson_fixture(tmp_path)
    doc1 = build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    path1, sha1 = write_digest(doc1, repo_root=tmp_path)

    bytes1 = path1.read_bytes()
    mode1 = os.stat(path1).st_mode & 0o777
    assert mode1 == 0o644

    lock_file = Path(f"{path1}.lock")
    assert lock_file.is_file()
    assert lock_file.read_bytes() == f"{sha1}\n".encode("ascii")

    # Second run
    doc2 = build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    path2, sha2 = write_digest(doc2, repo_root=tmp_path)
    bytes2 = path2.read_bytes()

    assert bytes1 == bytes2
    assert sha1 == sha2


def test_check_digest_success_and_byte_drift(tmp_path: Path) -> None:
    """--check verifies byte stability and fails closed on drift or lock mismatch."""
    _setup_two_lesson_fixture(tmp_path)
    doc = build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    path, sha = write_digest(doc, repo_root=tmp_path)

    # Valid check passes
    check_path, check_sha = check_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert check_path == path
    assert check_sha == sha

    # Mutate disk file -> byte drift
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(DigestError) as exc_info:
        check_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    # Since bytes changed, lock check fails first
    assert exc_info.value.code in (codes.LOCK_MISMATCH, codes.BYTE_DRIFT)


def test_missing_lock_sidecar_fails(tmp_path: Path) -> None:
    """Missing lock sidecar on observed or resolutions fails with lock_mismatch."""
    paths = _setup_two_lesson_fixture(tmp_path)
    # Remove lock for lesson 1 observed
    obs_lock = Path(f"{paths['obs_1']}.lock")
    obs_lock.unlink()

    with pytest.raises(DigestError) as exc_info:
        build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert exc_info.value.code == codes.LOCK_MISMATCH
    assert str(paths["obs_1"]) in exc_info.value.message


def test_missing_provenance_fails(tmp_path: Path) -> None:
    """Missing provenance file fails with provenance_missing."""
    paths = _setup_two_lesson_fixture(tmp_path)
    paths["prov_1"].unlink()

    with pytest.raises(DigestError) as exc_info:
        build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert exc_info.value.code == codes.PROVENANCE_MISSING


def test_missing_plan_fails(tmp_path: Path) -> None:
    """Missing plan file fails with plan_missing."""
    paths = _setup_two_lesson_fixture(tmp_path)
    paths["plan"].unlink()

    with pytest.raises(DigestError) as exc_info:
        build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert exc_info.value.code == codes.PLAN_MISSING


def test_missing_mdx_fails(tmp_path: Path) -> None:
    """Missing MDX file fails with mdx_missing."""
    paths = _setup_two_lesson_fixture(tmp_path)
    paths["mdx_1"].unlink()

    with pytest.raises(DigestError) as exc_info:
        build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert exc_info.value.code == codes.MDX_MISSING


def test_unit_not_in_provenance_fails(tmp_path: Path) -> None:
    """Token unit missing from provenance spans fails with unit_not_in_provenance."""
    paths = _setup_two_lesson_fixture(tmp_path)
    # Overwrite provenance without dialogue_0 unit
    prov_doc = yaml.safe_load(paths["prov_1"].read_text(encoding="utf-8"))
    prov_doc["spans"] = [s for s in prov_doc["spans"] if s["block"] != "dialogue_0"]
    lock.atomic_write(paths["prov_1"], yaml.safe_dump(prov_doc, allow_unicode=True, sort_keys=False).encode("utf-8"))

    with pytest.raises(DigestError) as exc_info:
        build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert exc_info.value.code == codes.UNIT_NOT_IN_PROVENANCE


def test_record_not_in_observed_fails(tmp_path: Path) -> None:
    """Token record missing from observed index fails with record_not_in_observed."""
    paths = _setup_two_lesson_fixture(tmp_path)
    # Remove W-1 from observed records
    obs_doc = yaml.safe_load(paths["obs_1"].read_text(encoding="utf-8"))
    obs_doc["records"] = [r for r in obs_doc["records"] if r["id"] != "W-1"]
    lock.write(paths["obs_1"], lock.yaml_bytes(obs_doc))

    with pytest.raises(DigestError) as exc_info:
        build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert exc_info.value.code == codes.RECORD_NOT_IN_OBSERVED


def test_cli_subprocess_invocation(tmp_path: Path) -> None:
    """Test CLI commands via subprocess with timeout."""
    _setup_two_lesson_fixture(tmp_path)

    # 1. Run digest generation --up-to 3
    cmd_write = [
        PYTHON_BIN,
        "-m",
        "scripts.review.digest",
        "a1",
        "mod-fixture",
        "--up-to",
        "3",
        "--repo-root",
        str(tmp_path),
    ]
    proc = subprocess.run(cmd_write, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0
    assert "ok: wrote" in proc.stdout

    digest_file = digest_output_path("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert digest_file.is_file()
    assert Path(f"{digest_file}.lock").is_file()

    # 2. Run --check
    cmd_check = [
        PYTHON_BIN,
        "-m",
        "scripts.review.digest",
        "a1",
        "mod-fixture",
        "--up-to",
        "3",
        "--check",
        "--repo-root",
        str(tmp_path),
    ]
    proc_check = subprocess.run(cmd_check, capture_output=True, text=True, timeout=30)
    assert proc_check.returncode == 0
    assert "verified byte-stable" in proc_check.stdout

    # 3. Run --up-to 1
    cmd_upto_1 = [
        PYTHON_BIN,
        "-m",
        "scripts.review.digest",
        "a1",
        "mod-fixture",
        "--up-to",
        "1",
        "--repo-root",
        str(tmp_path),
    ]
    proc_upto_1 = subprocess.run(cmd_upto_1, capture_output=True, text=True, timeout=30)
    assert proc_upto_1.returncode == 0
    assert "ok: wrote" in proc_upto_1.stdout

    # 4. Lock mismatch causes exit code 1
    Path(f"{digest_file}.lock").unlink()
    proc_fail = subprocess.run(cmd_check, capture_output=True, text=True, timeout=30)
    assert proc_fail.returncode == 1
    assert "failure:" in proc_fail.stderr or "digest_file_missing" in proc_fail.stderr


@pytest.mark.parametrize(
    "bad_slug",
    [
        "../../plans/lit-humor",
        "plans/lit-humor",
        "/etc/passwd",
    ],
)
def test_path_traversal_slug_fails_and_reads_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bad_slug: str
) -> None:
    """R-11: Traversal slugs, slashes, and absolute paths fail with path_forbidden and read nothing."""
    _setup_two_lesson_fixture(tmp_path)
    forbidden_file = tmp_path / "curriculum/l2-uk-en/plans/lit-humor.yaml"
    forbidden_file.parent.mkdir(parents=True, exist_ok=True)
    forbidden_file.write_text("plan_schema: 1\n", encoding="utf-8")

    with record_file_reads(monkeypatch) as opened_files:
        with pytest.raises(DigestError) as exc_info:
            build_digest("a1", bad_slug, 1, repo_root=tmp_path)

    assert exc_info.value.code == codes.PATH_FORBIDDEN
    assert opened_files == []


def test_symlink_pointing_outside_root_fails_and_reads_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """R-11: A symlinked input pointing outside its root fails with path_forbidden and reads nothing."""
    _setup_two_lesson_fixture(tmp_path)
    outside_dir = tmp_path / "outside_dir"
    outside_dir.mkdir(parents=True, exist_ok=True)
    secret_file = outside_dir / "secret.yaml"
    secret_file.write_text("secret_content: 1\n", encoding="utf-8")

    symlink_plan = tmp_path / "curriculum/l2-uk-en/lesson-plans/a1/mod-symlink.yaml"
    symlink_plan.symlink_to(secret_file)

    with record_file_reads(monkeypatch) as opened_files:
        with pytest.raises(DigestError) as exc_info:
            build_digest("a1", "mod-symlink", 1, repo_root=tmp_path)

    assert exc_info.value.code == codes.PATH_FORBIDDEN
    assert opened_files == []


def test_symlink_pointing_to_forbidden_dir_fails_and_reads_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R-11: A symlinked input pointing under curriculum/l2-uk-en/plans/ fails with path_forbidden and reads nothing."""
    _setup_two_lesson_fixture(tmp_path)
    forbidden_dir = tmp_path / "curriculum/l2-uk-en/plans"
    forbidden_dir.mkdir(parents=True, exist_ok=True)
    forbidden_plan = forbidden_dir / "lit-humor.yaml"
    forbidden_plan.write_text("plan_schema: 1\n", encoding="utf-8")

    symlink_plan = tmp_path / "curriculum/l2-uk-en/lesson-plans/a1/mod-symlink-forbidden.yaml"
    symlink_plan.symlink_to(forbidden_plan)

    with record_file_reads(monkeypatch) as opened_files:
        with pytest.raises(DigestError) as exc_info:
            build_digest("a1", "mod-symlink-forbidden", 1, repo_root=tmp_path)

    assert exc_info.value.code == codes.PATH_FORBIDDEN
    assert opened_files == []


def test_invalid_level_fails(tmp_path: Path) -> None:
    """Invalid level not in CLI allowed choices fails with path_forbidden."""
    _setup_two_lesson_fixture(tmp_path)
    with pytest.raises(DigestError) as exc_info:
        build_digest("a3", "mod-fixture", 1, repo_root=tmp_path)
    assert exc_info.value.code == codes.PATH_FORBIDDEN


def test_dialogue_missing_register_fails(tmp_path: Path) -> None:
    """A dialogue missing required 'register' breaks schema and fails with plan_invalid."""
    paths = _setup_two_lesson_fixture(tmp_path)
    plan_doc = yaml.safe_load(paths["plan"].read_text(encoding="utf-8"))
    del plan_doc["lessons"][0]["dialogue"]["register"]
    paths["plan"].write_bytes(yaml.safe_dump(plan_doc, allow_unicode=True, sort_keys=False).encode("utf-8"))

    with pytest.raises(DigestError) as exc_info:
        build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert exc_info.value.code == codes.PLAN_INVALID
    assert str(paths["plan"]) in exc_info.value.message


def test_malformed_dialogue_fails(tmp_path: Path) -> None:
    """A malformed dialogue breaks schema and fails with plan_invalid (not silently null)."""
    paths = _setup_two_lesson_fixture(tmp_path)
    plan_doc = yaml.safe_load(paths["plan"].read_text(encoding="utf-8"))
    plan_doc["lessons"][0]["dialogue"] = "not a valid dialogue mapping"
    paths["plan"].write_bytes(yaml.safe_dump(plan_doc, allow_unicode=True, sort_keys=False).encode("utf-8"))

    with pytest.raises(DigestError) as exc_info:
        build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert exc_info.value.code == codes.PLAN_INVALID
    assert str(paths["plan"]) in exc_info.value.message


def test_plan_lesson_with_no_steps_fails(tmp_path: Path) -> None:
    """A plan lesson with no 'steps' breaks schema and fails with plan_invalid."""
    paths = _setup_two_lesson_fixture(tmp_path)
    plan_doc = yaml.safe_load(paths["plan"].read_text(encoding="utf-8"))
    del plan_doc["lessons"][0]["steps"]
    paths["plan"].write_bytes(yaml.safe_dump(plan_doc, allow_unicode=True, sort_keys=False).encode("utf-8"))

    with pytest.raises(DigestError) as exc_info:
        build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert exc_info.value.code == codes.PLAN_INVALID
    assert str(paths["plan"]) in exc_info.value.message


def test_observed_index_with_no_untaught_forms_fails(tmp_path: Path) -> None:
    """An observed index with no 'untaught_forms' breaks schema and fails with observed_invalid."""
    paths = _setup_two_lesson_fixture(tmp_path)
    obs_doc = yaml.safe_load(paths["obs_1"].read_text(encoding="utf-8"))
    del obs_doc["untaught_forms"]
    lock.write(paths["obs_1"], lock.yaml_bytes(obs_doc))

    with pytest.raises(DigestError) as exc_info:
        build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert exc_info.value.code == codes.OBSERVED_INVALID
    assert str(paths["obs_1"]) in exc_info.value.message


def test_resolutions_missing_tokens_fails(tmp_path: Path) -> None:
    """Resolutions missing 'tokens' breaks schema and fails with resolutions_invalid."""
    paths = _setup_two_lesson_fixture(tmp_path)
    res_doc = yaml.safe_load(paths["res_1"].read_text(encoding="utf-8"))
    del res_doc["tokens"]
    lock.write(paths["res_1"], lock.yaml_bytes(res_doc))

    with pytest.raises(DigestError) as exc_info:
        build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert exc_info.value.code == codes.RESOLUTIONS_INVALID
    assert str(paths["res_1"]) in exc_info.value.message


def test_optional_places_defaults_to_empty_list(tmp_path: Path) -> None:
    """A dialogue omitting optional 'places' defaults to [] in digest."""
    paths = _setup_two_lesson_fixture(tmp_path)
    plan_doc = yaml.safe_load(paths["plan"].read_text(encoding="utf-8"))
    del plan_doc["lessons"][0]["dialogue"]["places"]
    paths["plan"].write_bytes(yaml.safe_dump(plan_doc, allow_unicode=True, sort_keys=False).encode("utf-8"))

    doc = build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert doc["lessons"][0]["dialogue"]["places"] == []


def test_symlinked_lock_sidecar_refused_before_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A .lock sidecar that is a symlink is refused before any read of that sidecar."""
    paths = _setup_two_lesson_fixture(tmp_path)

    obs_lock = Path(f"{paths['obs_1']}.lock")
    target_lock = obs_lock.parent / "target.lock"
    target_lock.write_text(obs_lock.read_text(encoding="utf-8"), encoding="utf-8")
    obs_lock.unlink()
    obs_lock.symlink_to(target_lock)

    with record_file_reads(monkeypatch) as opened_files:
        with pytest.raises(DigestError) as exc_info:
            build_digest("a1", "mod-fixture", 2, repo_root=tmp_path)

    assert exc_info.value.code == codes.PATH_FORBIDDEN
    assert not any("obs_1" in p and "lock" in p for p in opened_files)
    assert not any("target.lock" in p for p in opened_files)
    expected_allowed = {
        str(paths["plan"]),
        str(paths["mdx_1"]),
        str(tmp_path / "schemas/module-plan-v2.schema.json"),
    }
    assert set(opened_files).issubset(expected_allowed)


def test_dialogue_missing_step_fails(tmp_path: Path) -> None:
    """A dialogue missing required 'step' fails with plan_invalid."""
    paths = _setup_two_lesson_fixture(tmp_path)
    plan_doc = yaml.safe_load(paths["plan"].read_text(encoding="utf-8"))
    del plan_doc["lessons"][0]["dialogue"]["step"]
    paths["plan"].write_bytes(yaml.safe_dump(plan_doc, allow_unicode=True, sort_keys=False).encode("utf-8"))

    with pytest.raises(DigestError) as exc_info:
        build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert exc_info.value.code == codes.PLAN_INVALID
    assert str(paths["plan"]) in exc_info.value.message
    assert "step" in exc_info.value.message


def test_dialogue_null_step_fails(tmp_path: Path) -> None:
    """A dialogue with step: null fails with plan_invalid instead of defaulting to null."""
    paths = _setup_two_lesson_fixture(tmp_path)
    plan_doc = yaml.safe_load(paths["plan"].read_text(encoding="utf-8"))
    plan_doc["lessons"][0]["dialogue"]["step"] = None
    paths["plan"].write_bytes(yaml.safe_dump(plan_doc, allow_unicode=True, sort_keys=False).encode("utf-8"))

    with pytest.raises(DigestError) as exc_info:
        build_digest("a1", "mod-fixture", 3, repo_root=tmp_path)
    assert exc_info.value.code == codes.PLAN_INVALID
    assert str(paths["plan"]) in exc_info.value.message
    assert "step" in exc_info.value.message


def test_in_root_data_symlink_with_escaping_lock_refused_before_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An in-root data symlink to another in-root file whose .lock escapes is refused before any read."""
    paths = _setup_two_lesson_fixture(tmp_path)

    # In-root target file in the state directory
    state_dir = tmp_path / "curriculum/l2-uk-en/evidence/a1/_state/mod-fixture"
    target_data = state_dir / "target.observed.yaml"
    target_data.write_text(paths["obs_1"].read_text(encoding="utf-8"), encoding="utf-8")

    # Target file's .lock escapes outside repo root
    outside_dir = tmp_path / "outside_secret"
    outside_dir.mkdir(parents=True, exist_ok=True)
    escaping_secret = outside_dir / "secret_lock.txt"
    escaping_secret.write_text("escaping_lock_data\n", encoding="utf-8")
    (state_dir / "target.observed.yaml.lock").symlink_to(escaping_secret)

    # Replace lesson-1.observed.yaml with an in-root symlink to target_data
    paths["obs_1"].unlink()
    paths["obs_1"].symlink_to(target_data)

    with record_file_reads(monkeypatch) as opened_files:
        with pytest.raises(DigestError) as exc_info:
            build_digest("a1", "mod-fixture", 2, repo_root=tmp_path)

    assert exc_info.value.code == codes.PATH_FORBIDDEN
    assert not any("target.observed" in p or "secret_lock" in p or "lesson-1.observed" in p for p in opened_files)
    expected_allowed = {
        str(paths["plan"]),
        str(paths["mdx_1"]),
        str(tmp_path / "schemas/module-plan-v2.schema.json"),
    }
    assert set(opened_files).issubset(expected_allowed)


@pytest.mark.parametrize("dir_kind", ["plan", "state", "mdx"])
def test_symlinked_parent_directory_refused_before_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dir_kind: str
) -> None:
    """A symlinked parent directory is refused before any read of that input."""
    paths = _setup_two_lesson_fixture(tmp_path)

    if dir_kind == "plan":
        plans_parent = tmp_path / "curriculum/l2-uk-en/lesson-plans"
        real_plans_dir = plans_parent / "a1_real"
        (plans_parent / "a1").rename(real_plans_dir)
        (plans_parent / "a1").symlink_to(real_plans_dir)
        real_target_dir = real_plans_dir
        expected_allowed: set[str] = set()
    elif dir_kind == "state":
        state_parent = tmp_path / "curriculum/l2-uk-en/evidence/a1/_state"
        real_state_dir = state_parent / "mod-fixture_real"
        (state_parent / "mod-fixture").rename(real_state_dir)
        (state_parent / "mod-fixture").symlink_to(real_state_dir)
        real_target_dir = real_state_dir
        expected_allowed = {
            str(paths["plan"]),
            str(paths["mdx_1"]),
            str(tmp_path / "schemas/module-plan-v2.schema.json"),
        }
    elif dir_kind == "mdx":
        mdx_parent = tmp_path / "site/src/content/docs/a1"
        real_mdx_dir = mdx_parent / "mod-fixture_real"
        (mdx_parent / "mod-fixture").rename(real_mdx_dir)
        (mdx_parent / "mod-fixture").symlink_to(real_mdx_dir)
        real_target_dir = real_mdx_dir
        expected_allowed = {
            str(paths["plan"]),
            str(tmp_path / "schemas/module-plan-v2.schema.json"),
        }

    with record_file_reads(monkeypatch) as opened_files:
        with pytest.raises(DigestError) as exc_info:
            build_digest("a1", "mod-fixture", 2, repo_root=tmp_path)

    assert exc_info.value.code == codes.PATH_FORBIDDEN
    assert not any(str(real_target_dir) in p for p in opened_files)
    assert set(opened_files).issubset(expected_allowed)

    if dir_kind == "state":
        with record_file_reads(monkeypatch) as opened_check:
            with pytest.raises(DigestError) as exc_info_chk:
                check_digest("a1", "mod-fixture", 2, repo_root=tmp_path)
        assert exc_info_chk.value.code == codes.PATH_FORBIDDEN
        assert opened_check == []


def test_symlinked_schema_refused_before_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A symlinked schema is refused before any read."""
    _setup_two_lesson_fixture(tmp_path)

    schemas_dir = tmp_path / "schemas"
    real_schema = schemas_dir / "target.schema.json"
    real_schema.write_text("{}", encoding="utf-8")

    symlink_schema = schemas_dir / "module-digest-v1.schema.json"
    symlink_schema.unlink(missing_ok=True)
    symlink_schema.symlink_to(real_schema)

    doc = {
        "digest_schema": DIGEST_SCHEMA,
        "generator_version": GENERATOR_VERSION,
        "level": "a1",
        "slug": "mod-fixture",
        "up_to": 1,
        "plan_sha256": "0" * 64,
        "sources": [],
        "lessons": [],
    }

    with record_file_reads(monkeypatch) as opened_files:
        with pytest.raises(DigestError) as exc_info:
            validate_digest(doc, repo_root=tmp_path)

    assert exc_info.value.code == codes.PATH_FORBIDDEN
    assert opened_files == []


def test_symlinked_output_directory_refused_before_write(
    tmp_path: Path,
) -> None:
    """A symlinked output directory is refused before any write."""
    import shutil

    _setup_two_lesson_fixture(tmp_path)
    doc = build_digest("a1", "mod-fixture", 2, repo_root=tmp_path)

    real_out = tmp_path / "curriculum/l2-uk-en/evidence/a1/_state/mod-fixture-real"
    real_out.mkdir(parents=True, exist_ok=True)

    state_dir = tmp_path / "curriculum/l2-uk-en/evidence/a1/_state/mod-fixture"
    shutil.rmtree(state_dir)
    state_dir.symlink_to(real_out)

    with pytest.raises(DigestError) as exc_info:
        write_digest(doc, repo_root=tmp_path)

    assert exc_info.value.code == codes.PATH_FORBIDDEN
    assert list(real_out.iterdir()) == []

    with pytest.raises(DigestError) as exc_info2:
        digest_output_path("a1", "mod-fixture", 2, repo_root=tmp_path)

    assert exc_info2.value.code == codes.PATH_FORBIDDEN


def test_check_digest_refuses_symlink_before_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """check_digest refuses a symlinked digest file before any read."""
    _setup_two_lesson_fixture(tmp_path)
    doc = build_digest("a1", "mod-fixture", 2, repo_root=tmp_path)
    path, _ = write_digest(doc, repo_root=tmp_path)

    state_dir = path.parent
    target_data = state_dir / "target.digest.yaml"
    target_data.write_bytes(path.read_bytes())

    path.unlink()
    path.symlink_to(target_data)

    with record_file_reads(monkeypatch) as opened_files:
        with pytest.raises(DigestError) as exc_info:
            check_digest("a1", "mod-fixture", 2, repo_root=tmp_path)

    assert exc_info.value.code == codes.PATH_FORBIDDEN
    assert opened_files == []


def test_symlinked_repo_root_resolved_once_and_refuses_symlink_below_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A symlinked --repo-root is resolved once at entry and still refuses a symlink below it."""
    real_root = tmp_path / "real_repo"
    real_root.mkdir(parents=True, exist_ok=True)
    paths = _setup_two_lesson_fixture(real_root)

    symlink_root = tmp_path / "symlink_repo"
    symlink_root.symlink_to(real_root)

    # 1. Resolves once at entry and succeeds when no symlinks below it
    doc = build_digest("a1", "mod-fixture", 2, repo_root=symlink_root)
    assert doc["level"] == "a1"
    assert doc["up_to"] == 2

    # 2. CLI also succeeds with symlinked --repo-root
    cmd_write = [
        PYTHON_BIN,
        "-m",
        "scripts.review.digest",
        "a1",
        "mod-fixture",
        "--up-to",
        "2",
        "--repo-root",
        str(symlink_root),
    ]
    proc = subprocess.run(cmd_write, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0
    assert "ok: wrote" in proc.stdout

    # 3. Refuses a symlink below the resolved root before reading it
    state_dir = real_root / "curriculum/l2-uk-en/evidence/a1/_state/mod-fixture"
    target_data = state_dir / "target.observed.yaml"
    target_data.write_text(paths["obs_1"].read_text(encoding="utf-8"), encoding="utf-8")
    paths["obs_1"].unlink()
    paths["obs_1"].symlink_to(target_data)

    with record_file_reads(monkeypatch) as opened_files:
        with pytest.raises(DigestError) as exc_info:
            build_digest("a1", "mod-fixture", 2, repo_root=symlink_root)

    assert exc_info.value.code == codes.PATH_FORBIDDEN
    assert not any("target.observed" in p or "lesson-1.observed" in p for p in opened_files)

    proc_fail = subprocess.run(cmd_write, capture_output=True, text=True, timeout=30)
    assert proc_fail.returncode == 1
    assert "path_forbidden" in proc_fail.stderr


def test_missing_schema_in_supplied_root_fails_without_fallback(
    tmp_path: Path,
) -> None:
    """Schemas come from supplied root only; missing schema fails with DIGEST_SCHEMA_INVALID without fallback."""
    import shutil

    _setup_two_lesson_fixture(tmp_path)
    shutil.rmtree(tmp_path / "schemas")

    with pytest.raises(DigestError) as exc_info:
        build_digest("a1", "mod-fixture", 2, repo_root=tmp_path)

    assert exc_info.value.code == codes.DIGEST_SCHEMA_INVALID
    assert "schema file not found" in exc_info.value.message

    doc = {
        "digest_schema": DIGEST_SCHEMA,
        "generator_version": GENERATOR_VERSION,
        "level": "a1",
        "slug": "mod-fixture",
        "up_to": 1,
        "plan_sha256": "0" * 64,
        "sources": [],
        "lessons": [],
    }
    with pytest.raises(DigestError) as exc_info2:
        validate_digest(doc, repo_root=tmp_path)

    assert exc_info2.value.code == codes.DIGEST_SCHEMA_INVALID
    assert "schema file not found" in exc_info2.value.message


def test_cached_validator_requires_schema_file_on_every_call(tmp_path: Path) -> None:
    """A cached validator requires schema file to exist on every call; deleting it fails with DIGEST_SCHEMA_INVALID."""
    _setup_two_lesson_fixture(tmp_path)

    doc = {
        "digest_schema": DIGEST_SCHEMA,
        "generator_version": GENERATOR_VERSION,
        "level": "a1",
        "slug": "mod-fixture",
        "up_to": 1,
        "plan_sha256": "0" * 64,
        "sources": [],
        "lessons": [],
    }

    # Validate once succeeds and populates cache
    validate_digest(doc, repo_root=tmp_path)

    # Delete the schema file
    schema_path = tmp_path / "schemas/module-digest-v1.schema.json"
    schema_path.unlink()

    # Call again in the same process must fail with DIGEST_SCHEMA_INVALID
    with pytest.raises(DigestError) as exc_info:
        validate_digest(doc, repo_root=tmp_path)
    assert exc_info.value.code == codes.DIGEST_SCHEMA_INVALID
    assert "schema file not found" in exc_info.value.message


def test_cached_validator_reloads_on_schema_byte_change(tmp_path: Path) -> None:
    """Changing schema bytes between calls invalidates old cache and uses the new schema."""
    _setup_two_lesson_fixture(tmp_path)

    doc = {
        "digest_schema": DIGEST_SCHEMA,
        "generator_version": GENERATOR_VERSION,
        "level": "a1",
        "slug": "mod-fixture",
        "up_to": 1,
        "plan_sha256": "0" * 64,
        "sources": [],
        "lessons": [],
    }

    # Validate once succeeds
    validate_digest(doc, repo_root=tmp_path)

    # Modify schema bytes to require a new mandatory property
    schema_path = tmp_path / "schemas/module-digest-v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["required"].append("review_round_5_marker")
    schema["properties"]["review_round_5_marker"] = {"type": "string"}
    schema_path.write_text(json.dumps(schema), encoding="utf-8")

    # Calling again in the same process must use new schema and fail because doc lacks the field
    with pytest.raises(DigestError) as exc_info:
        validate_digest(doc, repo_root=tmp_path)
    assert exc_info.value.code == codes.DIGEST_SCHEMA_INVALID
    assert "review_round_5_marker" in exc_info.value.message

    # Providing the new property succeeds under the new schema
    doc["review_round_5_marker"] = "r5_verified"
    validate_digest(doc, repo_root=tmp_path)


def test_build_digest_fails_when_plan_schema_deleted_after_cache(tmp_path: Path) -> None:
    """build_digest caches plan validator, but deleting plan schema causes subsequent call to fail."""
    _setup_two_lesson_fixture(tmp_path)

    # First call succeeds
    doc = build_digest("a1", "mod-fixture", 2, repo_root=tmp_path)
    assert doc["level"] == "a1"

    # Delete the plan schema
    plan_schema_path = tmp_path / "schemas/module-plan-v2.schema.json"
    plan_schema_path.unlink()

    # Second call in same process must fail
    with pytest.raises(DigestError) as exc_info:
        build_digest("a1", "mod-fixture", 2, repo_root=tmp_path)
    assert exc_info.value.code == codes.DIGEST_SCHEMA_INVALID
    assert "schema file not found" in exc_info.value.message

    # Recreate plan schema with changed bytes requiring an extra property
    real_schema = json.loads((REPO_ROOT / "schemas/module-plan-v2.schema.json").read_text(encoding="utf-8"))
    real_schema["required"].append("custom_module_field")
    real_schema["properties"]["custom_module_field"] = {"type": "string"}
    plan_schema_path.write_text(json.dumps(real_schema), encoding="utf-8")

    # Subsequent call in same process must reload schema and fail with plan_invalid
    with pytest.raises(DigestError) as exc_info2:
        build_digest("a1", "mod-fixture", 2, repo_root=tmp_path)
    assert exc_info2.value.code == codes.PLAN_INVALID
    assert "custom_module_field" in exc_info2.value.message


def test_digest_token_in_multi_span_attributed_to_record(tmp_path: Path) -> None:
    # Finding 4: multi-span block attributes token to correct span and record
    paths = _setup_two_lesson_fixture(tmp_path)

    # Update lesson 1 provenance to have a multi-span prompt block
    prov_path = paths["prov_1"]
    prov_data = yaml.safe_load(prov_path.read_text(encoding="utf-8"))
    prov_data["spans"].append(
        {
            "tab": "vpravy",
            "step": "s1",
            "activity": "a1",
            "item": 0,
            "block": "prompt",
            "span": 0,
            "start": 0,
            "end": 18,
            "source": "writer_prose",
            "ref": None,
            "text": "Виправте помилку: ",
            "record_kind": None,
            "record_side": None,
            "option_origin": None,
            "is_key": None,
        }
    )
    prov_data["spans"].append(
        {
            "tab": "vpravy",
            "step": "s1",
            "activity": "a1",
            "item": 0,
            "block": "prompt",
            "span": 1,
            "start": 18,
            "end": 23,
            "source": "record",
            "ref": "E-001",
            "text": "слове",
            "record_kind": "error",
            "record_side": "incorrect",
            "option_origin": None,
            "is_key": None,
        }
    )
    prov_bytes = yaml.safe_dump(prov_data, allow_unicode=True, sort_keys=False).encode("utf-8")
    lock.write(prov_path, prov_bytes)

    # Add a resolution token pointing to that unit and offset 18
    rec_path = paths["res_1"]
    rec_data = yaml.safe_load(rec_path.read_text(encoding="utf-8"))
    rec_data["tokens"].append(
        {
            "unit": {"tab": "vpravy", "step": "s1", "activity": "a1", "item": 0, "block": "prompt"},
            "offset": 18,
            "token": "слове",
            "surface": "sentence_token",
            "class": "resolved",
            "candidates": ["W-1"],
            "selected": {"record": "W-1", "forms": ["noun:inanim:n:v_kly"], "stressed": "сло́ве"},
            "provenance": "deterministic",
        }
    )
    rec_bytes = yaml.safe_dump(rec_data, allow_unicode=True, sort_keys=False).encode("utf-8")
    lock.write(rec_path, rec_bytes)

    doc = build_digest("a1", "mod-fixture", 2, repo_root=tmp_path)
    validate_digest(doc)

    occ = next(
        (
            o
            for o in doc["lessons"][0]["occurrences"]
            if o["locator"]["tab"] == "vpravy" and o["locator"]["block"] == "prompt"
        ),
        None,
    )
    assert occ is not None
    assert occ["span_source"] == "record"
    assert occ["span_ref"] == "E-001"
    assert occ["locator"].get("span") == 1
