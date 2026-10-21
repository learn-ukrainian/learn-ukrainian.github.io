from __future__ import annotations

import json
import sqlite3
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.wiki.diagnostics import retrieval_bakeoff_9233 as bakeoff


def _vesum(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE forms_all (id INTEGER PRIMARY KEY, word_form TEXT, lemma TEXT, pos TEXT, tags TEXT DEFAULT '');
        CREATE TABLE form_markers (form_id INTEGER, marker TEXT);
        INSERT INTO forms_all(id,word_form,lemma,pos) VALUES
          (1,'як','як','adv'), (2,'апостроф','апостроф','noun'),
          (3,'пишемо','писати','verb'), (4,'з','з','prep'),
          (5,'із','із','prep'), (6,'зі','зі','prep'),
          (7,'і','і','conj'), (8,'й','й','conj');
        """
    )
    conn.commit()
    return conn


@pytest.fixture(autouse=True)
def fixture_sources_and_vesum(tmp_path: Path, monkeypatch):
    # Synthetic corpora test their own scope; production identity validation
    # is exercised separately with an explicitly nonempty list.
    monkeypatch.setattr(bakeoff, "EXTRA_SOURCES", ())
    path = tmp_path / "fixture-vesum.db"
    _vesum(path).close()
    monkeypatch.setattr(bakeoff, "_default_vesum_db", lambda: path)


def test_lemma_stop_words_and_topic_word_exception(tmp_path: Path) -> None:
    conn = _vesum(tmp_path / "vesum.db")
    assert bakeoff.filter_lemma_query("як пишемо апостроф", conn) == ["пишемо", "апостроф"]
    assert bakeoff.filter_lemma_query("з", conn) == ["з"]
    assert bakeoff.filter_lemma_query("з/із/зі", conn) == ["з", "із", "зі"]
    assert bakeoff.filter_lemma_query("і/й", conn) == ["і", "й"]
    # If filtering would leave fewer than two content terms, preserve the query.
    assert bakeoff.filter_lemma_query("як апостроф", conn) == ["як", "апостроф"]
    conn.close()


def test_pool_is_blind_and_sealed_key_maps_back(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    corpus = sqlite3.connect(work / "corpus.sqlite3")
    corpus.execute("CREATE TABLE chunks (id INTEGER,chunk_id TEXT,title TEXT,text TEXT,source_file TEXT,subject TEXT,parent_section_id INTEGER)")
    corpus.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?,?)", [(1, "c1", "t1", "текст перший", "ukrmova-a", "ukrmova", None), (2, "c2", "t2", "текст другий", "bukvar-b", "bukvar", None)])
    corpus.commit()
    corpus.close()
    (work / "search-results.json").write_text(json.dumps({
        "queries": [{"id": "G3-001", "family": "G3", "query": "приклад", "stratum": "G3-area-kind", "cluster": "G3-001"}],
        "arms": {"L": {"G3-001": ["c1"]}, "D:model": {"G3-001": ["c2"]}},
    }), encoding="utf-8")

    result = bakeoff.pool(work, query_limit=1)
    blind_text = (work / "judging/pool.json").read_text(encoding="utf-8")
    key = json.loads((work / "sealed/pool-key.json").read_text(encoding="utf-8"))
    assert "D:model" not in blind_text and '"L"' not in blind_text
    assert {item["chunk_id"] for item in key} == {"c1", "c2"}
    assert {item["arm"] for item in key if item["arm"]} == {"L", "D:model"}
    assert result["queries"] == 1
    assert '"chunk_id"' not in blind_text and '"source_identity"' not in blind_text
    for item in key:
        expected = bakeoff.hashlib.sha256(f"{item['query_id']}\0{item['chunk_id']}".encode()).hexdigest()[:20]
        assert item["item_id"] == expected
    labels = work / "judging/judge-a.jsonl"
    labels.write_text("already judged")
    with pytest.raises(ValueError, match="overwrite-pool"):
        bakeoff.pool(work)
    assert labels.read_text() == "already judged"
    bakeoff.pool(work, overwrite=True)
    assert labels.read_text() == ""


class StubTokenizer:
    def encode(self, text, **kwargs):
        return list(map(ord, text))

    def decode(self, ids, **kwargs):
        return "".join(map(chr, ids))


def _compute_fixture(monkeypatch, query=None):
    # These existing unit tests isolate pipeline mechanics. Real manifest,
    # budget and refusal gates are exercised without these mocks in v61 tests.
    monkeypatch.setattr(bakeoff, "_validate_run", lambda *a: {"sha256": "run"})
    monkeypatch.setattr(bakeoff, "_measurement_binding", lambda *a: {"run_manifest_sha256": "run"})
    monkeypatch.setattr(bakeoff, "_check_runtime", lambda *a: None)
    monkeypatch.setattr(bakeoff, "_admission", lambda *a: {"admitted_embedders": [bakeoff.E5], "rerankers": {"Qwen/Qwen3-Reranker-0.6B": {"variant": "fp32"}}, "measurements": {"lexical_query_seconds": 1}})
    if query is not None:
        monkeypatch.setattr(bakeoff, "_evaluation", lambda *a: {"queries": [query], "cost_query_ids": [query["id"]], "sha256": "eval"})


def test_encode_stub_is_resumable_and_uses_repository_prefix(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "sources.db"
    conn = sqlite3.connect(source)
    conn.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY,chunk_id TEXT,title TEXT,text TEXT,source_file TEXT,subject TEXT,parent_section_id INTEGER)")
    conn.executemany("INSERT INTO textbooks VALUES (?,?,?,?,?,?,?)", [
        (1, "e1", "title one", "first text", "book-one", "ukrmova", None),
        (2, "e2", "title two", "second text", "book-two", "bukvar", None),
        (3, "outside", "other", "excluded", "book-three", "history", None),
    ])
    conn.commit()
    conn.close()
    _compute_fixture(monkeypatch)
    calls: list[list[str]] = []

    class StubEncoder:
        tokenizer = StubTokenizer()

        def encode(self, texts, **kwargs):
            calls.append(list(texts))
            return [[1.0, float(index + 1)] for index, _ in enumerate(texts)]

    monkeypatch.setattr(bakeoff, "_new_encoder", lambda repo, work: (StubEncoder(), {"kind": "sentence", "max_tokens": 64}))
    work = tmp_path / "work"
    first = bakeoff.encode(source, work, "intfloat/multilingual-e5-small", limit=None, batch_size=2)
    second = bakeoff.encode(source, work, "intfloat/multilingual-e5-small", limit=None, batch_size=2)
    assert first["rows_encoded_this_run"] == 2
    assert second["rows_encoded_this_run"] == 0
    assert second["rows_resumed"] == 2
    assert calls == [["passage: first text", "passage: second text"]]


def test_rerank_adapters_rank_candidates_without_model_downloads() -> None:
    candidates = [{"chunk_id": "a", "text": "first"}, {"chunk_id": "b", "text": "second"}]

    class CrossEncoderStub:
        tokenizer = StubTokenizer()

        def predict(self, pairs, **kwargs):
            assert len(pairs) == 2
            return [0.9, 0.1]

    class JinaStub:
        _tokenizer = StubTokenizer()

        def rerank(self, query, documents):
            assert query == "query" and documents == ["first", "second"]
            return [{"index": 1}, {"index": 0}]

    assert bakeoff._rerank(CrossEncoderStub(), {"kind": "cross_encoder", "max_tokens": 512}, "query", candidates) == ["a", "b"]
    assert bakeoff._rerank(JinaStub(), {"kind": "jina", "max_tokens": 512}, "query", candidates) == ["b", "a"]


def test_strict_and_lenient_labels_drive_recall_scoring(tmp_path: Path, monkeypatch) -> None:
    work = tmp_path / "work"
    (work / "sealed").mkdir(parents=True)
    (work / "judging").mkdir()
    query = {"id": "G3-001", "family": "G3", "query": "приклад", "stratum": "G3-area-kind", "cluster": "G3-001"}
    items = [{"item_id": "i1", "chunk_id": "c1"}, {"item_id": "i2", "chunk_id": "c2"}]
    (work / "search-results.json").write_text(json.dumps({"queries": [query], "arms": {"A": {"G3-001": ["c1", "c2"]}, "B": {"G3-001": ["c1"]}}, "costs": {}}), encoding="utf-8")
    (work / "judging/pool.json").write_text(json.dumps([{"query_id": "G3-001", "query": "приклад", "items": items}]), encoding="utf-8")
    (work / "sealed/pool-key.json").write_text(json.dumps([
        {"query_id": "G3-001", "item_id": "i1", "chunk_id": "c1", "arm": "A"},
        {"query_id": "G3-001", "item_id": "i2", "chunk_id": "c2", "arm": "A"},
        {"query_id": "G3-001", "item_id": "i1", "chunk_id": "c1", "arm": "B"},
    ]), encoding="utf-8")
    labels_a = [
        {"query_id": "G3-001", "item_id": "i1", "usable_quotation": True, "usable_exercise": False, "usable_example": False, "reason": "One line."},
        {"query_id": "G3-001", "item_id": "i2", "usable_quotation": True, "usable_exercise": False, "usable_example": False, "reason": "One line."},
    ]
    labels_b = [
        {"query_id": "G3-001", "item_id": "i1", "usable_quotation": False, "usable_exercise": False, "usable_example": False, "reason": "One line."},
        {"query_id": "G3-001", "item_id": "i2", "usable_quotation": True, "usable_exercise": False, "usable_example": False, "reason": "One line."},
    ]
    a_path, b_path = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    a_path.write_text("\n".join(json.dumps(row) for row in labels_a) + "\n", encoding="utf-8")
    b_path.write_text("\n".join(json.dumps(row) for row in labels_b) + "\n", encoding="utf-8")
    monkeypatch.setattr(bakeoff, "ROOT", tmp_path)

    result = bakeoff.score(work, a_path, b_path, iterations=20)
    assert bakeoff.stricter_label(True, False) is False
    assert bakeoff.lenient_label(True, False) is True
    assert result["strata"]["A"]["G3-area-kind"]["recall_at_20_strict"] == 1.0
    assert result["strata"]["B"]["G3-area-kind"]["recall_at_20_strict"] == 0.0
    assert result["strata"]["B"]["G3-area-kind"]["recall_at_20_lenient"] == 0.5
    assert result["kappa_gate"] is False
    assert (work / "phase2-results.md").exists()
    assert not (tmp_path / "docs").exists()
    # A same-size label file from a different pool must fail by identity.
    labels_a[0]["item_id"] = "stale-id"
    a_path.write_text("\n".join(json.dumps(row) for row in labels_a))
    with pytest.raises(ValueError, match="label ids"):
        bakeoff.score(work, a_path, b_path, iterations=20)


def _sources(path: Path, rows: list[tuple]) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY,chunk_id TEXT,title TEXT,text TEXT,source_file TEXT,subject TEXT,parent_section_id INTEGER)")
        conn.executemany("INSERT INTO textbooks VALUES (?,?,?,?,?,?,?)", rows)


def test_unmocked_lemma_index_finds_surface_forms_and_shares_probe_expansion(tmp_path: Path) -> None:
    vesum_path = tmp_path / "vesum.db"
    with _vesum(vesum_path) as conn:
        conn.executemany("INSERT INTO forms_all(id,word_form,lemma,pos) VALUES (?,?,?,?)", [
            (10, "родового", "родовий", "adj"), (11, "відмінка", "відмінок", "noun"),
            (12, "бачу", "бачити", "verb"), (13, "чую", "чути", "verb"),
            (14, "родовий", "родовий", "adj"), (15, "відмінок", "відмінок", "noun"),
        ])
    source = tmp_path / "sources.db"
    _sources(source, [(1, "inflected", "", "родового відмінка", "book", "ukrmova", None),
                      (2, "verbs", "бачу чую", "", "book", "ukrmova", None),
                      (3, "base", "", "родовий відмінок", "book", "ukrmova", None)])
    index = bakeoff._copy_subset(source, tmp_path / "work", vesum_path=vesum_path)
    with bakeoff._ro_connect(index) as conn, bakeoff._ro_connect(vesum_path) as vesum:
        assert "inflected" in bakeoff._fts_search(conn, "родового відмінка", vesum, lemma=True, limit=20)
        assert bakeoff._fts_search(conn, "бачу чую", vesum, lemma=True, limit=20) == ["verbs"]
    probe_index, _ = bakeoff.phase1._create_lemma_index(source, vesum_path, tmp_path / "probe")
    with sqlite3.connect(probe_index) as probe, sqlite3.connect(index) as harness:
        assert probe.execute("SELECT chunk_id,title_terms,text_terms FROM lemma_fts ORDER BY rowid").fetchall() == harness.execute("SELECT chunk_id,title,text FROM chunks_fts ORDER BY rowid").fetchall()


def test_function_filter_preserves_topics_and_content_homonyms(tmp_path: Path) -> None:
    conn = _vesum(tmp_path / "vesum.db")
    conn.executemany("INSERT INTO forms_all(id,word_form,lemma,pos,tags) VALUES (?,?,?,?,?)", [
        (10, "у", "у", "prep", "prep"), (11, "в", "в", "prep", "prep"),
        (12, "біля", "біля", "prep", "prep"), (13, "до", "до", "prep", "prep"),
        (14, "навпроти", "навпроти", "prep", "prep"), (15, "навпроти", "навпроти", "adv", "adv"),
        (16, "поруч", "поруч", "prep", "prep"), (17, "поруч", "поруч", "adv", "adv"),
        (18, "раніше", "раніше", "prep", "prep"), (19, "раніше", "раніше", "adv", "adv:compc:predic"),
        (20, "де", "де", "adv", "adv:pron:int:rel"),
    ])
    _, g3 = bakeoff._load_queries()
    by_id = {q["id"]: q["query"] for q in g3}
    for qid, topics in [("G3-028", {"у", "в"}), ("G3-066", {"біля", "до", "навпроти"}), ("G3-067", {"і", "й"}), ("G3-138", {"у", "в"})]:
        assert topics <= set(bakeoff.filter_lemma_query(by_id[qid], conn))
    assert bakeoff.filter_lemma_query("де поруч раніше", conn) == ["поруч", "раніше"]
    assert bakeoff.filter_lemma_query("з пишемо апостроф", conn) == ["пишемо", "апостроф"]
    conn.close()


def test_cached_corpus_digest_and_missing_source_identity(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "sources.db"
    _sources(source, [(1, "c1", "", "text", "book", "ukrmova", None)])
    work = tmp_path / "work"
    target = bakeoff._copy_subset(source, work)
    assert bakeoff._copy_subset(source, work) == target
    with sqlite3.connect(target) as conn:
        conn.execute("UPDATE chunks SET text='tampered'")
    with pytest.raises(ValueError, match="digest"):
        bakeoff._copy_subset(source, work)
    monkeypatch.setattr(bakeoff, "EXTRA_SOURCES", ("pohribnyi-ukrainska-literaturna-vymova-1992",))
    with pytest.raises(ValueError, match="zero rows"):
        bakeoff._copy_subset(source, tmp_path / "empty")


@pytest.fixture
def fake_sentence_encoder(monkeypatch):
    import sys

    class Encoder:
        def __init__(self, repo, **kwargs):
            self.max_seq_length = 64
            self.tokenizer = StubTokenizer()
            self.tokenizer.num_special_tokens_to_add = lambda pair: 2
            self.prompts = {}
            self.calls = []
            self.encoded_texts = []

        def encode(self, texts, **kwargs):
            self.calls.append((texts, kwargs))
            # Mirror Sentence Transformers' named/explicit/default prompt
            # selection so these assertions pin the actual prefixed inputs.
            prompt = kwargs.get("prompt")
            if prompt is None:
                prompt = self.prompts.get(kwargs.get("prompt_name"), "unwanted default: ")
            self.encoded_texts.extend(prompt + text for text in texts)
            return [[1.0, 0.0] for _ in texts]

    monkeypatch.setattr(bakeoff, "_model_options", lambda *a: {"revision": "a" * 40})

    def install(prompts):
        model = Encoder(None)
        model.prompts = prompts
        monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=lambda *a, **kw: model))
        return model

    return install


SENTENCE_REPOS = [repo for repo, spec in bakeoff.EMBEDDERS.items() if spec["kind"] == "sentence"]


@pytest.mark.parametrize("repo", SENTENCE_REPOS)
@pytest.mark.parametrize("prompt", [None, "", " \t\n", "matching"])
def test_sentence_prompt_resolution_uses_frozen_prefixes_on_both_sides(
    tmp_path: Path, monkeypatch, fake_sentence_encoder, repo, prompt,
) -> None:
    spec = bakeoff.EMBEDDERS[repo]
    prompts = {} if prompt is None else {
        "query": spec["query_prefix"] if prompt == "matching" else prompt,
        "document": spec["passage_prefix"] if prompt == "matching" else prompt,
    }
    model = fake_sentence_encoder(prompts)
    loaded, meta = bakeoff._new_encoder(repo, tmp_path)
    assert loaded is model
    assert meta["prefixes"] == {"query": spec["query_prefix"], "passage": spec["passage_prefix"]}
    names = {
        "query": "query" if prompt == "matching" and spec["query_prefix"].strip() else None,
        "passage": "document" if prompt == "matching" and spec["passage_prefix"].strip() else None,
    }
    assert meta["prompt_names"] == names
    bakeoff._query_vector(model, meta, "sample query", repo)
    bakeoff._encode_batch(model, meta, ["sample passage"], repo, 1)
    assert model.encoded_texts == [spec["query_prefix"] + "sample query", spec["passage_prefix"] + "sample passage"]
    for side, (texts, kwargs), text in zip(("query", "passage"), model.calls, ("sample query", "sample passage"), strict=True):
        if names[side]:
            assert texts == [text] and kwargs["prompt_name"] == names[side]
            assert "prompt" not in kwargs
        else:
            assert texts == [meta["prefixes"][side] + text] and kwargs["prompt"] == ""
            assert "prompt_name" not in kwargs
    budgets = []
    monkeypatch.setattr(bakeoff, "_passage_stats", lambda rows, tokenizer, budget, **kw: ([], budgets.append(budget)))
    bakeoff._embedder_passage_stats([], model, meta, repo)
    assert budgets == [64 - len(spec["passage_prefix"]) - 2]


@pytest.mark.parametrize("repo", SENTENCE_REPOS)
@pytest.mark.parametrize("side", ["query", "document"])
def test_sentence_conflicting_nonempty_prompt_refuses_before_encoding(
    tmp_path: Path, fake_sentence_encoder, repo, side,
) -> None:
    model = fake_sentence_encoder({side: "conflicting prefix: "})
    with pytest.raises(ValueError, match=f"configuration mismatch.*{side} prompt"):
        bakeoff._new_encoder(repo, tmp_path)
    assert model.calls == []


@pytest.mark.parametrize("prompts", [{}, {"query": "", "document": ""}, {"query": " \t", "document": "\n"},
                                    {"query": "native query: ", "document": "native passage: "}])
def test_jina_native_selectors_and_actual_prompt_budget(
    tmp_path: Path, monkeypatch, fake_sentence_encoder, prompts,
) -> None:
    repo = "jinaai/jina-embeddings-v5-text-nano"
    model = fake_sentence_encoder(prompts)
    loaded, meta = bakeoff._new_encoder(repo, tmp_path)
    assert loaded is model
    assert meta["prefixes"] == {"query": "task=retrieval; prompt_name=query", "passage": "task=retrieval; prompt_name=document"}
    assert meta["prompt_names"] == {
        "query": "query" if prompts.get("query", "").strip() else None,
        "passage": "document" if prompts.get("document", "").strip() else None,
    }
    # Jina uses its native retrieval task and named prompts even when the
    # tokenizer prompt is empty; selector strings must never enter the text.
    model.prompts.setdefault("query", "")
    model.prompts.setdefault("document", "")
    bakeoff._query_vector(model, meta, "sample query", repo)
    bakeoff._encode_batch(model, meta, ["sample passage"], repo, 1)
    assert model.encoded_texts == [model.prompts["query"] + "sample query", model.prompts["document"] + "sample passage"]
    for (texts, kwargs), name, text in zip(model.calls, ("query", "document"), ("sample query", "sample passage"), strict=True):
        assert texts == [text]
        assert kwargs["task"] == "retrieval" and kwargs["prompt_name"] == name
    budgets = []
    monkeypatch.setattr(bakeoff, "_passage_stats", lambda rows, tokenizer, budget, **kw: ([], budgets.append(budget)))
    bakeoff._embedder_passage_stats([], model, meta, repo)
    assert budgets == [64 - len(model.prompts["document"]) - 2]


def test_flag_frozen_prefixes_on_both_sides_and_passage_budget(tmp_path: Path, monkeypatch) -> None:
    import sys

    calls = []
    model = SimpleNamespace(tokenizer=StubTokenizer())
    model.tokenizer.num_special_tokens_to_add = lambda pair: 2

    def encode(texts, **kwargs):
        calls.append((texts, kwargs))
        return {"dense_vecs": [[1.0, 0.0]]}

    model.encode = encode
    monkeypatch.setattr(bakeoff, "_model_options", lambda *a: {"revision": "a" * 40})
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(snapshot_download=lambda *a, **kw: "snapshot"))
    monkeypatch.setitem(sys.modules, "FlagEmbedding", SimpleNamespace(BGEM3FlagModel=lambda *a, **kw: model))
    repo = "BAAI/bge-m3"
    loaded, meta = bakeoff._new_encoder(repo, tmp_path)
    assert loaded is model
    assert meta["prefixes"] == {"query": "", "passage": ""}
    assert meta["prompt_names"] == {"query": None, "passage": None}
    bakeoff._query_vector(model, meta, "sample query", repo)
    bakeoff._encode_batch(model, meta, ["sample passage"], repo, 1)
    assert [texts for texts, _ in calls] == [["sample query"], ["sample passage"]]
    assert all(kwargs["max_length"] == 8192 for _, kwargs in calls)
    budgets = []
    monkeypatch.setattr(bakeoff, "_passage_stats", lambda rows, tokenizer, budget, **kw: ([], budgets.append(budget)))
    bakeoff._embedder_passage_stats([], model, meta, repo)
    assert budgets == [8192 - 2]


def test_qwen_yes_no_scoring_preserves_template_without_joint_truncation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(bakeoff, "_model_options", lambda *a: {"revision": "a" * 40})
    import sys
    from types import SimpleNamespace

    import numpy as np

    def softmax(values, dim):
        assert dim == 1
        weights = np.exp(values - values.max(axis=dim, keepdims=True))
        return weights / weights.sum(axis=dim, keepdims=True)

    torch = SimpleNamespace(tensor=np.asarray, no_grad=nullcontext, softmax=softmax)
    monkeypatch.setitem(sys.modules, "torch", torch)

    class Tokenizer:
        model_max_length = 100
        def encode(self, text, **kwargs):
            assert "max_length" not in kwargs and "truncation" not in kwargs
            if "<Query>:" in text:
                assert "<Query>: query" in text and "<Document>:" in text
                return [3, 4, 5]
            if text in {"document", "query"}:
                return [3]
            return [1, 2] if text.startswith("<|im_start|>") else [8, 9]

        def decode(self, ids, **kwargs):
            return "document"

        def pad(self, inputs, **kwargs):
            assert inputs["input_ids"] == [[1, 2, 3, 4, 5, 8, 9]]
            return {"input_ids": torch.tensor(inputs["input_ids"])}
        def convert_tokens_to_ids(self, text):
            return {"no": 0, "yes": 1}[text]
    class Model:
        config = SimpleNamespace(max_position_embeddings=128)
        def to(self, device):
            return self
        def float(self):
            return self

        def eval(self):
            return self
        def __call__(self, **inputs):
            return SimpleNamespace(logits=torch.tensor([[[0.0, 2.0]]]))
    tokenizer = Tokenizer()
    def new_tokenizer(*args, **kwargs):
        assert kwargs["truncation_side"] == "right"
        return tokenizer
    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=new_tokenizer), AutoModelForCausalLM=SimpleNamespace(from_pretrained=lambda *a, **kw: Model())))
    adapter, meta = bakeoff._new_reranker("Qwen/Qwen3-Reranker-0.6B", tmp_path)
    assert meta["max_tokens"] == 100
    assert bakeoff._qwen_scores(adapter, meta, "query", ["document"]) == pytest.approx([0.880797])
    assert bakeoff._rerank(adapter, meta, "query", [{"chunk_id": "c", "text": "document"}]) == ["c"]
    assert bakeoff._rerank(adapter, meta, "query", []) == []


def test_repeated_g1_queries_keep_every_known_citation(tmp_path: Path, monkeypatch) -> None:
    work = tmp_path / "work"
    work.mkdir()
    with sqlite3.connect(work / "corpus.sqlite3") as conn:
        conn.execute("CREATE TABLE chunks(id INTEGER,chunk_id TEXT,title TEXT,text TEXT,source_file TEXT,subject TEXT,parent_section_id INTEGER)")
        conn.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?,?)", [(1, "c1", "", "one", "book", "ukrmova", None), (2, "c2", "", "two", "book", "ukrmova", None)])
    queries = [{"id": "g1a", "family": "G1", "query": "same", "gold_chunk_id": "c1"}, {"id": "g1b", "family": "G1", "query": "same", "gold_chunk_id": "c2"}]
    monkeypatch.setattr(bakeoff, "_load_queries", lambda: (queries, []))
    (work / "search-results.json").write_text(json.dumps({"queries": queries, "arms": {"L": {}}}))
    result = bakeoff.pool(work)
    assert result["queries"] == 1 and result["items"] == 2
    key = json.loads((work / "sealed/pool-key.json").read_text())
    assert {row["chunk_id"] for row in key} == {"c1", "c2"}


def test_corpus_manifest_and_cli_paths(tmp_path: Path, monkeypatch, capsys) -> None:
    source = tmp_path / "sources.db"
    _sources(source, [(1, "c1", "", "text", "book", "ukrmova", None)])
    work = tmp_path / "work"
    assert bakeoff.main(["corpus", "--sources-db", str(source), "--work-dir", str(work)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["rows"] == 1 and result["identity_counts"] == {"ukrmova": 1}
    assert len(result["row_digest_sha256"]) == 64
    with pytest.raises(ValueError, match="outside"):
        bakeoff._work_dir(bakeoff.ROOT / "scratch")
    args = bakeoff.build_parser().parse_args(["pool", "--work-dir", str(work), "--overwrite-pool"])
    assert args.overwrite_pool
    with pytest.raises(SystemExit):
        bakeoff.build_parser().parse_args(["search", "--work-dir", str(work), "--batch-size", "2"])


@pytest.mark.parametrize("refused", [False, True])
def test_admission_probe_does_not_write_shadow_journal(tmp_path, monkeypatch, refused):
    from scripts.common import task_store_paths
    from scripts.orchestration import admission_shadow as shadow
    from scripts.orchestration import dispatch_admission as adm

    journal = tmp_path / "journal"
    monkeypatch.setenv(shadow.DIRECTORY_ENV, str(journal))
    monkeypatch.setattr(adm, "load_thresholds", lambda: adm.Thresholds(2, 3.5, 1.5))
    monkeypatch.setattr(adm, "probe_host", lambda: adm.HostProbe(12 * 1024**3, 100 if refused else 0, 8, True))
    monkeypatch.setattr(adm, "probe_disk", lambda: adm.DiskProbe(10, 90))
    tasks = tmp_path / "tasks"
    monkeypatch.setattr(task_store_paths, "tasks_dir", lambda: tasks)
    baseline = adm.evaluate("danger", tasks)
    paths = list(journal.glob("*.jsonl"))
    assert len(paths) == 1
    before = paths[0].read_bytes()
    assert bakeoff._admission_probe() is (not refused)
    assert paths[0].read_bytes() == before
    rows = [json.loads(line) for line in before.splitlines()]
    assert len(rows) == 1
    assert rows[0]["phase"] == "evaluate"
    assert rows[0]["current_admission_decision"] == ("refuse" if refused else "admit")
    assert shadow.compare_day(journal, paths[0].stem)["samples"] == 1
    assert baseline.admitted is (not refused)
