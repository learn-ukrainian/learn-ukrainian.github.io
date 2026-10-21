"""Structural conversion tests; synthetic strings make no language claims."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.rag import convert_phase2 as converter


def test_complete_definitions_duplicates_ordinals_text_and_counts(tmp_path, capsys):
    definitions = [f"item {i}" for i in range(13)] + ['quote " and \\ and \n']
    entries = [
        {"word": "sample", "pos": "noun", "defs": definitions},
        {"word": "", "defs": ["excluded"]},
        {"word": "empty", "defs": []},
        {"word": "sample", "pos": "noun", "defs": ["duplicate"]},
        {"word": "sample", "pos": "verb", "defs": ["other POS"]},
    ]
    source, output = tmp_path / "words.json", tmp_path / "chunks.jsonl"
    source.write_text(json.dumps(entries), encoding="utf-8")
    assert converter.convert_dmklinger(source, output) == 3
    first = output.read_bytes()
    rows = [json.loads(line) for line in first.splitlines()]
    assert rows == [
        {"id": "dmk-000000", "word": "sample", "pos": "noun", "translations": definitions,
         "text": "sample (noun): item 0; item 1; item 2; item 3; item 4", "source": "dmklinger UK→EN"},
        {"id": "dmk-000003", "word": "sample", "pos": "noun", "translations": ["duplicate"],
         "text": "sample (noun): duplicate", "source": "dmklinger UK→EN"},
        {"id": "dmk-000004", "word": "sample", "pos": "verb", "translations": ["other POS"],
         "text": "sample (verb): other POS", "source": "dmklinger UK→EN"},
    ]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "Converting dmklinger UK→EN...\n  ✅ 3 entries → chunks.jsonl\n"
    assert converter.convert_dmklinger(source, output) == 3
    assert output.read_bytes() == first


def test_default_paths_and_empty_count(tmp_path, monkeypatch, capsys):
    folder = tmp_path / "data/dmklinger-uk-en"
    folder.mkdir(parents=True)
    (folder / "words.json").write_text("[]")
    monkeypatch.setattr(converter, "PROJECT_ROOT", tmp_path)
    assert converter.convert_dmklinger() == 0
    assert (folder / "chunks.jsonl").read_bytes() == b""
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "Converting dmklinger UK→EN...\n  ✅ 0 entries → chunks.jsonl\n"


def test_direct_cli_explicit_paths_and_help(tmp_path):
    source, output = tmp_path / "words.json", tmp_path / "chunks.jsonl"
    source.write_text('[{"word":"sample","pos":"noun","defs":["one"]}]')
    command = [sys.executable, str(Path(converter.__file__))]
    result = subprocess.run([*command, "--dmklinger", "--input", str(source), "--output", str(output)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == "Converting dmklinger UK→EN...\n  ✅ 1 entries → chunks.jsonl\n"
    assert json.loads(output.read_text())["translations"] == ["one"]
    for arguments in (["--help"], []):
        result = subprocess.run(command + arguments, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0
        assert "Outputs:" in result.stdout and "Exit codes:" in result.stdout
    result = subprocess.run([*command, "--input", str(source)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 2
    assert "require --dmklinger" in result.stderr


def test_main_dispatches_selected_converter_only(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(converter, "convert_dmklinger", lambda *args: calls.append(args))
    for flag in ("--dmklinger", "--all"):
        for function in ("convert_ukrajinet", "convert_ubertext_freq", "extract_sum11_registers"):
            monkeypatch.setattr(converter, function, lambda: None)
        monkeypatch.setattr(sys, "argv", ["converter", flag, "--input", "raw.json", "--output", "out.jsonl"])
        converter.main()
    assert calls == [(Path("raw.json"), Path("out.jsonl"))] * 2


@pytest.mark.parametrize("payload", ["not JSON", "{}"])
def test_invalid_source_never_reports_success(tmp_path, payload):
    source = tmp_path / "words.json"
    source.write_text(payload)
    if payload == "not JSON":
        with pytest.raises(json.JSONDecodeError):
            converter.convert_dmklinger(source, tmp_path / "out")
    else:
        # An empty mapping produces zero rows, preserving the existing parser behavior.
        assert converter.convert_dmklinger(source, tmp_path / "out") == 0
