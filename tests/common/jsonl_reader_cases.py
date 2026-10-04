"""Fixtures for actual JSONL reader boundaries, without provider/corpus runs.

Parser-boundary cases execute the real function up to json.loads, decode with
Python's real parser, and assert the exact string before stopping via a private
BaseException. This keeps schema/ML/provider setup out of a line-boundary test;
transport and artifact dependencies are fixture-only and never contacted.
"""

from __future__ import annotations

import importlib
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

VALUE = "before\u0085middle\u2028more\u2029after"


class _ParsedRecord(BaseException):
    pass


def reader_case(module_name, function, site, ending, tmp_path, monkeypatch):
    module = importlib.import_module(module_name)
    path = tmp_path / "fixture.jsonl"
    record = {"probe": VALUE, "prediction": VALUE}
    raw_record = json.dumps(record, ensure_ascii=False)
    text = raw_record + ending
    path.write_bytes(text.encode("utf-8"))
    fn = getattr(module, function)
    args, kwargs = [path], {}
    leaf = module_name.rsplit(".", 1)[-1]

    if function == "_jsonl_record_count":
        assert fn(text + "\n" + raw_record) == 2
        return
    if function == "_update_index_header":
        path.write_bytes((json.dumps({"header": 0}) + "\n" + text).encode())
        fn(path, {"header": 1})
        assert [json.loads(line) for line in path.read_text().split("\n") if line] == [{"header": 1}, record]
        assert path.read_text().count("\n") == 2
        return
    if function == "_cached_jsonl_records":
        assert fn(text) == [record]
        return
    if function == "_replay_forms":
        path.write_text(json.dumps({"form": VALUE}, ensure_ascii=False) + ending)
        assert fn(path) == [VALUE]
        return
    if function == "_read_predictions":
        assert fn(path) == [VALUE]
        return

    def patch(name, value):
        monkeypatch.setattr(module, name, value)

    if function in {"_release_bundle", "public_bundle"}:
        patch("PUBLIC_FILES", ["fixture"])
        patch("_managed_release", lambda _: False)
        patch("_release_bytes", lambda *a: text.encode())
        if function == "public_bundle":
            patch(
                "read_json",
                lambda _: {
                    "outputs": {
                        "public_fixture": {
                            "records": 1,
                            "bytes": len(text.encode()),
                            "sha256": module.sha256_bytes(text.encode()),
                        }
                    }
                },
            )
    elif function == "_jsonl_bytes":
        args = [text.encode()]
    elif function == "_load_existing_suite":
        patch("EXISTING_SUITE_FILE", path)
        args = []
    elif function in {"mine_lemko_from_seeds", "mine_oes_from_seeds", "mine_middle_ua_from_seeds"}:
        patch(
            {
                "mine_lemko_from_seeds": "LEMKO_SEED_FILE",
                "mine_oes_from_seeds": "OES_SEED_FILE",
                "mine_middle_ua_from_seeds": "MID_UA_SEED_FILE",
            }[function],
            path,
        )
        args = [1] if function == "mine_middle_ua_from_seeds" else []
    elif function == "_phase1_rows":
        monkeypatch.setattr(module.phase1, "verify_existing", lambda **kw: None)
        args.append(tmp_path / "receipt.json")
    elif function == "_native_grok_turn_status":
        (tmp_path / "events.jsonl").write_text(text)
        patch("grok_session_dir", lambda *a: tmp_path)
        args, kwargs = [], {"session_id": "fixture", "cwd": tmp_path}
    elif function in {
        "read_opencode_turn_status",
        "_parse_opencode_stream",
        "_parse_stdout_events",
        "_parse_jsonl",
    }:
        args = [text]
    elif function == "_read_transcript_events":
        patch("_transcript_file", lambda _: path)
        args = ["fixture"]
    elif function == "send":
        patch("find_session_file", lambda _: None)
        monkeypatch.setattr(
            module.subprocess, "run", lambda *a, **kw: SimpleNamespace(stdout=text, stderr="", returncode=0)
        )
        args = ["fixture", "fixture"]
    elif function == "compute_build_stats":
        dest = tmp_path / "a1" / "build-stats.jsonl"
        dest.parent.mkdir()
        dest.write_text(text)
        args, kwargs = ["a1"], {"curriculum_root": tmp_path}
    elif function == "pull_calibration_cases":
        dest = tmp_path / "eval" / "fixture.jsonl"
        dest.parent.mkdir()
        dest.write_text(text)
        args, kwargs = [], {"project_root": tmp_path, "blob": "eval/fixture.jsonl"}
    elif leaf == "bakeoff_aggregate":
        args.append([])
    elif function == "_jsonl_has_event":
        args.append("fixture")
    elif function == "call_opencode":
        monkeypatch.setattr(
            module.subprocess, "run", lambda *a, **kw: SimpleNamespace(stdout=text, stderr="", returncode=0)
        )
        args = ["fixture", "fixture"]
    elif function == "_read_jsonl_inventory":
        kwargs = {"inventory_path": "fixture"}
    elif function == "evaluation_texts":
        args = [[path]]
    elif function in {"_parse_sse_or_json", "decode_response"}:
        args = [("data: " + text + "\n").encode()]
    elif function == "_parse_stream_json":
        args = [text, {}, set(), 0]
    elif function == "cmd_authority_import":
        authority = importlib.import_module("scripts.fleet_comms.authority")
        service = MagicMock()
        monkeypatch.setattr(authority, "AuthorityService", service)
        args = [SimpleNamespace(root=str(tmp_path), legacy_db=None, records_jsonl=str(path), source="fixture")]
    elif function == "append_space_collapse_audit":
        args = [[], path]
    elif function == "_load_usage_by_task_id":
        path.rename(tmp_path / "usage_fixture.jsonl")
        args = [tmp_path]
    elif function == "json":
        fn = module.Run.json
        args = [module.Run(0, "diagnostic\n" + text, "")]
    elif function == "parse_writer_output_strict_json":
        args = ["```json file=activities.yaml\n" + text + "\n```\n"]
    elif function in {"build_sft_dialect_dataset", "build_sft_dataset"}:
        path.rename(tmp_path / "sft_shard_fixture.jsonl")
        # Empty language inputs ensure only fixture replay is reached. No
        # linguistic generation or live dictionaries participate in this test.
        db = tmp_path / "empty.db"
        db.touch()
        patch("V02_SFT_SHARDS_DIR", tmp_path)
        if function == "build_sft_dialect_dataset":
            args, kwargs = (
                [[]],
                {"vesum_db": db, "sft_dialect_quota": 0, "replay_quota": 1, "replay_shards_dir": tmp_path},
            )
        else:
            args, kwargs = [[], [], []], {"vesum_db": db, "target_sft_quota": 0, "replay_quota": 1}
    elif function == "run_pretraining_audit":
        sft, dpo = tmp_path / "sft", tmp_path / "dpo"
        sft.mkdir()
        dpo.mkdir()
        # The non-target stage uses an empty shard to reach the DPO reader.
        (sft / "fixture.jsonl").write_text(text if site == 953 else "")
        (dpo / "fixture.jsonl").write_text(text if site == 1010 else "")
        db = tmp_path / "empty.db"
        db.touch()
        patch("resolve_data_path", lambda p: p)
        patch(
            "load_protection_suite",
            lambda _: [{"stratum": "historical_text", "expected_action": "PRESERVE", "target_term": "fixture"}],
        )
        args, kwargs = (
            [],
            {
                "protection_path": path,
                "sft_dir": sft,
                "dpo_dir": dpo,
                "sources_db_path": db,
                "vesum_db_path": db,
                "min_cases": 1,
            },
        )

    original = json.loads

    def loads(value, *a, **kw):
        parsed = original(value, *a, **kw)
        if isinstance(parsed, dict) and parsed.get("probe") == VALUE:
            assert parsed["prediction"] == VALUE
            raise _ParsedRecord
        return parsed

    monkeypatch.setattr(json, "loads", loads)
    with pytest.raises(_ParsedRecord):
        fn(*args, **kwargs)
