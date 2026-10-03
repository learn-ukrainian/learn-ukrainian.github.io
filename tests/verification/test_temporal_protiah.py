"""Development-only hybrid grammar and real fail-safe paths; no held-out data."""

from __future__ import annotations

import builtins
import hashlib
import importlib
import subprocess
import sys

import pytest

from scripts.curriculum.resolver.tokenize import tokenize
from scripts.verification import stanza_models as models
from scripts.verification import temporal_protiah as hybrid

TEXT = "На протязі року архів отримував листи."
MORPH = {"року": [{"lemma": "рік", "pos": "noun", "tags": "noun:m:v_rod"}]}


def proposed_tree(text):
    """Propose an NP without supplying any morphological case evidence."""
    tokens = tokenize(text)
    root = len(tokens)
    return [
        dict(
            id=i + 1,
            text=t.text,
            start=t.start,
            end=t.end,
            head=0 if i + 1 == root else (2 if i == 2 else 3 if i == 3 and root > 5 else root),
            deprel="root" if i + 1 == root else "nmod" if i == 2 else "obl",
            upos="NOUN",
            feats="Case=Gen",
        )
        for i, t in enumerate(tokens)
    ]


class FakeParser:
    def __init__(self, tree=None, reason=None):
        self.tree = tree
        self.reason = reason
        self.calls = 0

    def parse(self, text, budget):
        self.calls += 1
        return self.tree if self.tree is not None else proposed_tree(text), self.reason


def classify(text=TEXT, morphology=None, parser=None, **kwargs):
    return hybrid.classify(
        text,
        tokenize(text),
        0,
        MORPH if morphology is None else morphology,
        parser=parser or FakeParser(),
        firm_enabled=True,
        **kwargs,
    )


def test_positive_genitive_proof_and_default_gate():
    result = classify()
    assert result["reading"] == "temporal" and result["status"] == "documented_calque"
    assert result["evidence"]["positive_genitive_government"]
    assert not hybrid.FIRM_ENABLED
    result = hybrid.classify(TEXT, tokenize(TEXT), 0, MORPH, parser=FakeParser())
    assert result["status"] == "suspicion" and result["reading"] == "temporal"


@pytest.mark.parametrize("alternative", ["v_naz", "v_zna", "nv"])
def test_parser_cannot_erase_vesum_alternative(alternative):
    morphology = {"року": MORPH["року"] + [{"lemma": "рік", "pos": "noun", "tags": "noun:" + alternative}]}
    assert classify(morphology=morphology)["status"] == "suspicion"


def test_parse_only_elimination_and_missing_morphology_abstain():
    assert classify(morphology={})["status"] == "suspicion"
    tree = proposed_tree(TEXT)
    tree[2]["head"] = len(tree)
    assert classify(parser=FakeParser(tree))["evidence"]["reason"] == "parser_grammar_disagreement"


@pytest.mark.parametrize("defect", ["cycle", "offset", "root", "ids", "empty", "head"])
def test_malformed_tree(defect):
    tree = proposed_tree(TEXT)
    if defect == "cycle":
        tree[0]["head"] = 1
    if defect == "offset":
        tree[0]["end"] = 999
    if defect == "root":
        tree[0]["head"] = 0
    if defect == "ids":
        tree[0]["id"] = 99
    if defect == "empty":
        tree = []
    if defect == "head":
        tree[0]["head"] = 999
    parser = FakeParser(tree)
    parser.tree = tree
    if not tree:
        parser.parse = lambda text, budget: ([], None)
    result = classify(parser=parser)
    assert result["status"] == "suspicion"
    assert result["evidence"]["parser_unavailable"]


def test_single_sentence_cache_and_offset_rebasing():
    text = "Архів працює. " + TEXT
    parser = FakeParser()
    budget = hybrid.CallBudget()
    start = next(i for i, t in enumerate(tokenize(text)) if t.lookup == "На")
    for _ in range(2):
        result = hybrid.classify(text, tokenize(text), start, MORPH, parser=parser, budget=budget, firm_enabled=True)
        assert result["reading"] == "temporal"
    assert parser.calls == 1


def test_lock_busy_budget_and_large_sentence():
    parser = hybrid.Parser()
    parser.lock.acquire()
    try:
        assert classify(parser=parser)["evidence"]["reason"] == "lock_busy"
    finally:
        parser.lock.release()
    assert classify(parser=parser, budget=hybrid.CallBudget(0))["evidence"]["reason"] == "budget_exhausted"
    assert (
        classify(TEXT.rstrip(".") + " архів" * 41, parser=parser)["evidence"]["reason"]
        == "sentence_token_budget_exhausted"
    )
    assert parser.process is None


@pytest.mark.parametrize("defect", ["absent", "size", "hash", "resources"])
def test_real_missing_and_hash_mismatch(tmp_path, monkeypatch, defect):
    payload = b"model"
    entry = dict(install_path="uk/pos/test.pt", size=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    monkeypatch.setattr(models, "manifest", lambda: {"files": [entry]})
    monkeypatch.setattr(models, "model_root", lambda: tmp_path)
    path = tmp_path / entry["install_path"]
    path.parent.mkdir(parents=True)
    if defect != "absent":
        path.write_bytes(b"shorter" if defect == "size" else b"wrong" if defect == "hash" else payload)
    with pytest.raises(FileNotFoundError):
        models.pipeline_kwargs()


def test_stanza_not_installed(monkeypatch):
    monkeypatch.setattr(models, "pipeline_kwargs", lambda: {})
    original = builtins.__import__

    def missing(name, *args, **kwargs):
        if name == "stanza":
            raise ModuleNotFoundError("stanza")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing)
    with pytest.raises(ModuleNotFoundError):
        hybrid._load_pipeline()

    # Exercise the actual child error protocol, not an injected success parser.
    class Connection:
        def __init__(self):
            self.sent = []

        def send(self, message):
            self.sent.append(message)

        def close(self):
            pass

    connection = Connection()
    hybrid._parser_child(connection)
    assert connection.sent == [(False, "ModuleNotFoundError")]


@pytest.mark.parametrize("phase", ["cold", "inference", "missing"])
def test_real_supervisor_deadlines_and_error_fallback(monkeypatch, phase):
    class Connection:
        calls = 0

        def poll(self, timeout):
            self.calls += 1
            return phase != "cold" and self.calls == 1

        def recv(self):
            return (phase != "missing", None)

        def close(self):
            pass

        def send(self, text):
            pass

    class Process:
        stopped = False

        def start(self):
            pass

        def terminate(self):
            self.stopped = True

        def join(self, timeout):
            pass

        def is_alive(self):
            return False

    connection, process = Connection(), Process()

    class Context:
        def Pipe(self):
            return connection, Connection()

        def Process(self, **kwargs):
            return process

    monkeypatch.setattr(hybrid.multiprocessing, "get_context", lambda kind: Context())
    parser = hybrid.Parser()
    result = classify(parser=parser)
    assert result["status"] == "suspicion" and result["evidence"]["parser_unavailable"]
    assert process.stopped and parser.failed
    assert parser.parse(TEXT, hybrid.CallBudget()) == (None, "parser_unavailable")


def test_candidate_free_checker_and_server_do_not_import_optional_models(tmp_path):
    code = """
import builtins, importlib.util, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'stanza', 'torch'}: raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
import importlib, os
from pathlib import Path
checker = importlib.import_module('scripts.verification.check_text')
db = Path(os.environ['LU_MCP_SOURCES_LOG_DIR']) / 'vesum.db'
db.touch()
checker._vesum_path_resolved = lambda: db
checker.verify_words = lambda words, **kwargs: {word: [] for word in words}
checker._vesum_version = lambda: 'test'
checker.source_info = lambda: {}
result = checker.check_text(text='Архів отримував листи.', checks=['russian_shadow'])
assert result.get('status') != 'error' and result['summary']['tokens'] == 3

spec = importlib.util.spec_from_file_location('sources_server', '.mcp/servers/sources/server.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert 'stanza' not in sys.modules and 'torch' not in sys.modules
print('lazy-import proof passed')
"""
    # Real fresh interpreter; no imported-module cache can mask eager imports.
    import os

    env = dict(os.environ, LU_MCP_SOURCES_LOG_DIR=str(tmp_path))
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "lazy-import proof passed" in result.stdout


@pytest.mark.slow
def test_real_model_determinism_and_loaded_warm_benchmark(requires_vesum_db, requires_sources_db):
    from scripts.verification.vesum import verify_words

    pipeline = hybrid._load_pipeline()

    class RealParser:
        def parse(self, text, budget):
            return hybrid.document_tree(pipeline(text)), None

    parser = RealParser()
    morphology = verify_words([t.lookup.lower() for t in tokenize(TEXT)], db_path=requires_vesum_db)
    results = [hybrid.classify(TEXT, tokenize(TEXT), 0, morphology, parser=parser, firm_enabled=True) for _ in range(5)]
    assert not any(r["evidence"].get("parser_unavailable") for r in results)
    assert all(result == results[0] for result in results)
    assert results[0]["reading"] == "temporal"
    # Check the unchanged benchmark in the same process with real weights loaded.
    spec = importlib.util.spec_from_file_location("benchmark_test", "tests/test_check_text.py")
    test_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_module)
    test_module.test_speed_warm_call_under_2s(requires_vesum_db, requires_sources_db)


def test_document_tree_rejects_multiple_sentences_and_mwt():
    from types import SimpleNamespace as NS

    assert hybrid.document_tree(NS(sentences=[])) == []
    assert hybrid.document_tree(NS(sentences=[NS(tokens=[NS(words=[1, 2])])])) == []
    word = NS(id=1, text="На", head=0, deprel="root", upos="ADP", feats=None)
    doc = NS(sentences=[NS(tokens=[NS(words=[word], start_char=0, end_char=2)])])
    assert hybrid.document_tree(doc)[0]["text"] == "На"


@pytest.mark.parametrize("reading,expected", [("noun:f:v_zna", "draught"), ("noun:f:v_rod:nv", "undecided")])
def test_positive_counterevidence_and_indeclinable(reading, expected):
    text = "На протязі годину архіваріус стояв."
    morphology = {"годину": [{"lemma": "година", "pos": "noun", "tags": reading}]}
    tree = proposed_tree(text)
    tree[2]["deprel"] = "obl"
    tree[2]["head"] = len(tree)
    result = classify(text, morphology, FakeParser(tree))
    assert result["reading"] == expected
    assert result["status"] == ("none" if expected == "draught" else "suspicion")


def test_adjective_agreement_can_resolve_case_but_not_number_disagreement():
    text = "На протязі цієї години архів отримував листи."
    morphology = {
        "цієї": [{"lemma": "цей", "pos": "adj", "tags": "adj:f:v_rod"}],
        "години": [
            {"lemma": "година", "pos": "noun", "tags": "noun:f:v_rod"},
            {"lemma": "година", "pos": "noun", "tags": "noun:p:v_naz"},
        ],
    }
    tree = proposed_tree(text)
    tree[2]["head"], tree[2]["deprel"] = 4, "det"
    tree[3]["head"], tree[3]["deprel"] = 2, "nmod"
    assert classify(text, morphology, FakeParser(tree))["reading"] == "temporal"
    morphology["цієї"][0]["tags"] = "adj:p:v_rod"
    assert classify(text, morphology, FakeParser(tree))["evidence"]["reason"] == "agreement_disagreement"


@pytest.mark.parametrize("tail", ["дві", "з десяток", "так зо дві", ", мабуть, дві", "півтори"])
def test_independent_quantities_never_eliminated_by_parse(tail):
    text = "На протязі години " + tail + " архіваріус стояв."
    morphology = {
        "години": [{"lemma": "година", "pos": "noun", "tags": "noun:f:v_rod"}],
        "дві": [{"lemma": "два", "pos": "numr", "tags": "numr:v_naz"}],
        "десяток": [{"lemma": "десяток", "pos": "noun", "tags": "noun:m:v_zna"}],
        "півтори": [{"lemma": "півтора", "pos": "numr", "tags": "numr:nv"}],
    }
    assert classify(text, morphology)["evidence"]["reason"] == "quantity_or_aside_alternative"


def test_provision_verifies_before_installing(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from scripts.verification import provision_stanza_uk as installer

    payload = b"verified bytes"
    source = tmp_path / "download"
    source.write_bytes(payload)
    root = tmp_path / "models"
    entry = dict(
        path="models/test.pt", install_path="uk/test.pt", size=len(payload), sha256=hashlib.sha256(payload).hexdigest()
    )
    inventory = dict(repository="stanfordnlp/stanza-uk", revision="a" * 40, files=[entry])
    monkeypatch.setattr(installer, "manifest", lambda: inventory)
    monkeypatch.setattr(installer, "model_root", lambda: root)
    calls = []

    def download(**kwargs):
        calls.append(kwargs)
        return str(source)

    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(hf_hub_download=download))
    assert installer.provision()["verified"]
    assert calls[0]["revision"] == "a" * 40
    assert (root / entry["install_path"]).read_bytes() == payload
    assert installer.provision(verify_only=True)["verified"]
    (root / entry["install_path"]).write_bytes(b"wrong bytes")
    source.write_bytes(b"wrong bytes")
    with pytest.raises(ValueError, match="download_hash_mismatch"):
        installer.provision()
    with pytest.raises(ValueError):
        installer.provision(verify_only=True)


def test_runtime_paths_and_manifest_inventory():
    inventory = models.manifest()
    assert inventory["stanza_version"] == "1.13.0"
    assert len(inventory["revision"]) == 40
    assert {entry["install_path"].split("/")[1] for entry in inventory["files"]} == {
        "tokenize",
        "mwt",
        "pos",
        "lemma",
        "depparse",
        "pretrain",
        "forward_charlm",
        "backward_charlm",
    }
    assert all(len(entry["sha256"]) == 64 and entry["size"] > 0 for entry in inventory["files"])


def test_per_occurrence_status_does_not_merge_equal_surfaces(monkeypatch, tmp_path):
    checker = importlib.import_module("scripts.verification.check_text")
    patterns = importlib.import_module("scripts.verification.antonenko_patterns")
    db = tmp_path / "vesum.db"
    db.touch()
    monkeypatch.setattr(checker, "_vesum_path_resolved", lambda: db)
    monkeypatch.setattr(checker, "verify_words", lambda words, **kw: {w: MORPH.get(w.lower(), []) for w in words})
    monkeypatch.setattr(checker, "source_info", lambda: {})
    monkeypatch.setattr(checker, "_morph_uk", type("Morph", (), {"parse": staticmethod(lambda word: [])})())
    monkeypatch.setattr(checker, "check_russian_patterns_batch", lambda words, **kw: {})

    def classified(text, tokens, start, morphology, **kwargs):
        firm = "архів" in text
        return dict(
            status="documented_calque" if firm else "suspicion",
            end=start + 3,
            reading="temporal" if firm else "undecided",
            evidence=dict(reason="test"),
        )

    monkeypatch.setattr(patterns, "classify", classified)
    result = checker.check_text(
        items=[{"id": "a", "text": TEXT}, {"id": "b", "text": TEXT.replace("архів", "музей")}],
        checks=["russian_shadow"],
    )
    assert len(result["problems"]) == len(result["suspicions"]) == 1
    assert result["problems"][0]["locations"] == [["a", 0, 15]]
    assert result["suspicions"][0]["locations"] == [["b", 0, 15]]


def test_provision_cli_help_and_error(monkeypatch, capsys):
    from scripts.verification import provision_stanza_uk as installer

    monkeypatch.setattr(sys, "argv", ["provision_stanza_uk", "--help"])
    with pytest.raises(SystemExit) as raised:
        installer.main()
    assert raised.value.code == 0
    assert "Outputs:" in capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", ["provision_stanza_uk", "--verify-only"])

    def failure(**kwargs):
        raise ValueError("private diagnostic must not be printed")

    monkeypatch.setattr(installer, "provision", failure)
    assert installer.main() == 1
    output = capsys.readouterr().out
    assert "ValueError" in output and "private diagnostic" not in output


@pytest.mark.slow
def test_pinned_resources_support_shared_context_parser(tmp_path):
    import os

    env = dict(os.environ, STANZA_RESOURCES_DIR=str(models.model_root()))
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
from scripts.pipeline.stress_annotator import _load_context_parser
parser = _load_context_parser()
assert parser is not None
assert parser('На протязі року.').sentences[0].words
print('shared offline context parser passed')
""",
        ],
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
