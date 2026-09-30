"""Deterministic v6.1 contracts; all compute uses stub models or fake processes."""
from __future__ import annotations

import copy
import json
import sqlite3
from types import SimpleNamespace

import pytest

from scripts.wiki.diagnostics import retrieval_bakeoff_9233 as b


class Tokenizer:
    def encode(self, text, **kwargs):
        return list(map(ord, text))

    def decode(self, ids, **kwargs):
        return "".join(map(chr, ids))

    def __call__(self, text, **kwargs):
        return {"input_ids": self.encode(text), "offset_mapping": [(i, i + 1) for i in range(len(text))]}


@pytest.fixture
def frozen(tmp_path, monkeypatch):
    monkeypatch.setattr(b, "EXTRA_SOURCES", ())
    source = tmp_path / "source.db"
    rows = [(i + 1, f"c{i:04}", "title", "x" * (i + 1), f"book-{i % 4}", "ukrmova", None) for i in range(600)]
    with sqlite3.connect(source) as conn:
        conn.execute("CREATE TABLE textbooks(id INTEGER,chunk_id TEXT,title TEXT,text TEXT,source_file TEXT,subject TEXT,parent_section_id INTEGER)")
        conn.executemany("INSERT INTO textbooks VALUES (?,?,?,?,?,?,?)", rows)
    work = tmp_path / "work"
    work.mkdir()
    evaluation = b.sample(source, work)
    configs = {}
    for repo in sorted(set(b.EMBEDDERS) | set(b.RERANKERS)):
        configs[repo] = {"revision": "a" * 40, "tokenizer": {"repository": repo, "revision": "a" * 40}, "max_tokens": 2048}
        if repo in b.EMBEDDERS:
            configs[repo]["prefixes"] = {"query": b.EMBEDDERS[repo]["query_prefix"], "passage": b.EMBEDDERS[repo]["passage_prefix"]}
        else:
            configs[repo]["scoring_template"] = b.RERANKERS[repo]
    run = b.run_manifest(source, work, configs)
    measurements = {**b._measurement_binding(work), "lexical_query_seconds": 0.1, "embedders": {repo: {"projected_seconds": 1000 + index * 1000, "query_seconds": 0.2, "batch_size": 16} for index, repo in enumerate(sorted(b.EMBEDDERS))}, "rerankers": {}}
    return SimpleNamespace(source=source, work=work, evaluation=evaluation, run=run, configs=configs, measurements=measurements)


def test_item5_manifest_freezes_all_allocations_and_seed(frozen):
    evaluation = frozen.evaluation
    assert b.Counter(q["family"] for q in evaluation["queries"]) == {"G1": 7, "G2": 24, "G3": 89}
    assert len(evaluation["queries"]) == len({q["query"] for q in evaluation["queries"]}) == 120
    assert len(evaluation["cost_query_ids"]) == 50
    assert len(evaluation["timing_query_ids"]) == 25
    assert set(evaluation["timing_query_ids"]) <= {q["id"] for q in evaluation["queries"] if q["family"] == "G3"}
    assert all(q["cluster"] and q["stratum"] for q in evaluation["queries"])
    assert evaluation["timing_recipe"] == {"hybrid": f"H:{b.E5}", "top": 20, "rrf_k": 60, "first_stage_depth": 100, "tie_break": "chunk_id ascending", "seed": 9233}
    assert b.sample(frozen.source, frozen.work) == evaluation
    assert b._evaluation(frozen.work) == evaluation


def test_item3_sample_is_500_source_by_length_stratified(frozen):
    rows = b._subset_rows(frozen.source)
    sample = frozen.evaluation["encode_sample"]
    assert len(sample) == len({r["chunk_id"] for r in sample}) == 500
    assert {(r["source_identity"], r["length_tercile"]) for r in sample} == {(f"book-{i}", t) for i in range(4) for t in range(3)}
    assert {r["length_tercile"] for r in sample} == {0, 1, 2}
    assert b._stratified_sample(rows) == b._stratified_sample(rows[::-1])
    assert b._hash(sample) == frozen.evaluation["encode_sample_sha256"]
    with pytest.raises(ValueError, match="500"):
        b._stratified_sample(rows[:499])
    too_many_cells = [{"chunk_id": str(i), "source_file": str(i), "text": "x"} for i in range(600)]
    with pytest.raises(ValueError, match="cells"):
        b._stratified_sample(too_many_cells)


@pytest.mark.parametrize("field", ["sha256", "queries", "cost_query_ids", "timing_recipe", "encode_sample_sha256"])
def test_item5_rehashed_and_raw_manifest_drift_is_refused(frozen, field):
    path = frozen.work / "evaluation-manifest.json"
    payload = json.loads(path.read_text())
    if field == "queries":
        payload[field][0]["query"] = "tampered"
    elif field == "cost_query_ids":
        payload[field] = payload[field][::-1]
    elif field == "timing_recipe":
        payload[field]["top"] = 50
    else:
        payload[field] = "0" * 64
    if field != "sha256":
        payload["sha256"] = b._hash({k: v for k, v in payload.items() if k != "sha256"})
    b._write_json(path, payload)
    with pytest.raises(ValueError, match="mismatch"):
        b._evaluation(frozen.work)


def test_item7_run_manifest_pins_models_and_refuses_drift(frozen, monkeypatch):
    assert b._validate_run(frozen.source, frozen.work) == frozen.run
    assert frozen.run["passage_policies"] == b.PASSAGE_POLICIES
    assert b._model_options(b.E5, frozen.work) == {"revision": "a" * 40}
    b._check_runtime(b.E5, {"max_tokens": 2048, "prefixes": frozen.configs[b.E5]["prefixes"]}, frozen.work)
    with pytest.raises(ValueError, match="Loaded"):
        b._check_runtime(b.E5, {"max_tokens": 512, "prefixes": {}}, frozen.work)
    monkeypatch.setattr(b, "TOP_RERANK", 50)
    with pytest.raises(ValueError, match="mismatch"):
        b._validate_run(frozen.source, frozen.work)


@pytest.mark.parametrize("change", ["revision", "tokenizer", "max_tokens", "prefixes", "models"])
def test_item7_incomplete_or_unresolved_configuration_fails(frozen, change):
    config = copy.deepcopy(frozen.configs)
    if change == "models":
        config.pop(b.E5)
    else:
        config[b.E5][change] = {"repository": "other", "revision": "a" * 40} if change == "tokenizer" else {} if change == "prefixes" else "main" if change == "revision" else 0
    with pytest.raises(ValueError):
        b.run_manifest(frozen.source, frozen.work, config)


def test_item7_corpus_changes_fail_before_model_loading(frozen, monkeypatch):
    with sqlite3.connect(frozen.source) as conn:
        conn.execute("UPDATE textbooks SET text='changed' WHERE id=1")
    monkeypatch.setattr(b, "_new_encoder", lambda *a: pytest.fail("must not load"))
    with pytest.raises(ValueError, match="corpus digest"):
        b.encode(frozen.source, frozen.work, b.E5, limit=None, batch_size=16)


def test_item3_admission_sorts_by_cost_and_stops_at_budget(frozen):
    ordered = sorted(frozen.measurements["embedders"])
    seconds = [1000, 5000, 15000, 20000, 31000, 32000]
    for repo, value in zip(ordered, seconds, strict=True):
        frozen.measurements["embedders"][repo]["projected_seconds"] = value
    decision = b.admit(frozen.work, frozen.measurements)
    assert decision["admitted_embedders"] == ordered[:5]
    assert decision["excluded_embedders"] == ordered[5:]
    assert decision["encode_total_projected_seconds"] == 72000
    assert b._admission(frozen.work) == decision
    payload = copy.deepcopy(decision)
    payload["admitted_embedders"].append(ordered[-1])
    b._write_json(frozen.work / "admission.json", payload)
    with pytest.raises(ValueError, match="decision mismatch"):
        b._admission(frozen.work)
    assert json.loads((frozen.work / "admission.json").read_text()) == payload


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), True, None])
def test_item3_invalid_measurement_and_stale_binding_rejected(frozen, value):
    frozen.measurements["embedders"][b.E5]["projected_seconds"] = value
    with pytest.raises(ValueError):
        b.admit(frozen.work, frozen.measurements)
    assert not (frozen.work / "admission.json").exists()


def _timing(frozen):
    result = {"evaluation_manifest_sha256": frozen.evaluation["sha256"], "run_manifest_sha256": frozen.run["sha256"], "arms": {f"H:{b.E5}": {qid: [f"c{i:04}" for i in range(20)] for qid in frozen.evaluation["timing_query_ids"]}}}
    pairs = b.freeze_timing_pairs(frozen.work, result)
    return result, pairs


def _attempt(frozen, p50, mean=None):
    _, pairs = _timing(frozen)
    return {"p50_seconds": p50, "p95_seconds": max(p50, mean or p50), "mean_seconds": mean or p50, "timing_pairs_sha256": pairs["sha256"]}


def test_item3_two_stage_timing_freeze_cannot_be_replaced(frozen):
    result, pairs = _timing(frozen)
    assert len(pairs["pairs"]) == 25 and sum(len(q["candidate_ids"]) for q in pairs["pairs"]) == 500
    result["arms"][f"H:{b.E5}"][frozen.evaluation["timing_query_ids"][0]][0] = "other"
    with pytest.raises(ValueError, match="mismatch"):
        b.freeze_timing_pairs(frozen.work, result)
    result["arms"] = {}
    with pytest.raises(ValueError, match="E5"):
        b.freeze_timing_pairs(frozen.work, result)


def test_item3_fp32_fail_int8_and_borderline_second_value(frozen):
    repo = next(iter(b.RERANKERS))
    frozen.measurements["rerankers"][repo] = {"fp32": [_attempt(frozen, 20)], "int8": [_attempt(frozen, 9.5), _attempt(frozen, 8)]}
    decision = b.admit(frozen.work, frozen.measurements)
    assert decision["rerankers"][repo]["variant"] == "int8"
    assert len(decision["rerankers"][repo]["measurements"]) == 2
    # A passing but borderline first value does not bypass the second result.
    frozen.measurements["rerankers"][repo] = {"fp32": [_attempt(frozen, 9.5), _attempt(frozen, 12)], "int8": [_attempt(frozen, 8)]}
    assert b.admit(frozen.work, frozen.measurements)["rerankers"][repo]["variant"] == "int8"


def test_item3_projection_mean_gate_and_borderline_rules(frozen):
    repo = next(iter(b.RERANKERS))
    frozen.measurements["rerankers"][repo] = {"fp32": [_attempt(frozen, 5, 50)], "int8": [_attempt(frozen, 11.1)]}
    assert b.admit(frozen.work, frozen.measurements)["rerankers"][repo]["variant"] is None
    # Full-pool projection near 8h independently triggers the second run.
    frozen.measurements["rerankers"][repo] = {"fp32": [_attempt(frozen, 5, 39)]}
    with pytest.raises(ValueError, match="remeasurement"):
        b.admit(frozen.work, frozen.measurements)
    frozen.measurements["rerankers"][repo] = {"fp32": [_attempt(frozen, 20)]}
    with pytest.raises(ValueError, match="int8"):
        b.admit(frozen.work, frozen.measurements)
    frozen.measurements["rerankers"][repo] = {"fp32": [_attempt(frozen, 9)]}
    with pytest.raises(ValueError, match="remeasurement"):
        b.admit(frozen.work, frozen.measurements)
    frozen.measurements["rerankers"][repo] = {"fp32": [_attempt(frozen, 8), _attempt(frozen, 8)]}
    with pytest.raises(ValueError, match="remeasurement"):
        b.admit(frozen.work, frozen.measurements)


def test_item4_passages_preserve_exercise_tail_and_report_by_source():
    text = "h" * 128 + "middle" * 100 + "t" * 384
    preview, truncated, retained = b._passage(text, Tokenizer(), budget=512, tail=True)
    assert preview == "h" * 128 + "t" * 384
    assert truncated and retained == 512
    rows = [{"text": text, "source_file": "book"}, {"text": "short", "source_file": "book"}]
    _, stats = b._passage_stats(rows, Tokenizer(), 512, tail=True)
    assert stats["book"]["truncation_rate"] == 0.5
    assert stats["book"]["retained_character_share"] == pytest.approx(517 / (len(text) + 5))
    assert b._passage(text, Tokenizer(), budget=900, tail=False)[0] == text[:900]
    assert b._passage("", Tokenizer(), budget=512, tail=True) == ("", False, 0)


def test_item2_permutation_and_real_adapter_top20_without_pool_addition():
    candidates = [{"chunk_id": f"c{i:02}", "text": "a" * 128 + "m" * 700 + "z" * 384, "source_file": "book"} for i in range(20)]
    class Ranker:
        tokenizer = Tokenizer()
        def predict(self, pairs, **kwargs):
            assert len(pairs) == 20
            assert all(len(document) == 512 and document.endswith("z" * 384) for _, document in pairs)
            assert all(query == "q" * 300 for query, _ in pairs)
            return list(range(20))
    ordered = b._rerank(Ranker(), {"kind": "cross_encoder", "max_tokens": 2048}, "q" * 300, candidates)
    assert ordered[0] == "c19" and ordered[-1] == "c00"
    b._assert_permutation([row["chunk_id"] for row in candidates], ordered)
    with pytest.raises(ValueError, match="permute"):
        b._assert_permutation([row["chunk_id"] for row in candidates], [*ordered[:-1], "new"])
    with pytest.raises(ValueError, match="permute"):
        b._assert_permutation(["a", "a"], ["a", "a"])
    with pytest.raises(ValueError, match="insufficient context"):
        b._rerank(Ranker(), {"kind": "cross_encoder", "max_tokens": 700}, "q" * 300, candidates)


def test_item1_binary_ndcg_and_mrr_respond_to_rank11_promotion():
    original = [f"c{i}" for i in range(20)]
    reordered = ["c10", *original[:10], *original[11:]]
    assert b._ranking_metrics(original, {"c10"}) == (0, 0)
    assert b._ranking_metrics(reordered, {"c10"}) == (1, 1)
    assert b._ranking_metrics(original, {"c1"}) == pytest.approx((1 / b.math.log2(3), .5))
    with pytest.raises(ValueError, match="Duplicate"):
        b._ranking_metrics(["a", "a"], {"a"})


def _decision_fixture():
    queries = [{"id": f"q{i}", "cluster": f"q{i}", "family": "G3"} for i in range(120)]
    def arm(recall, ndcg):
        return {q["id"]: {"recall_at_20_strict": recall, "ndcg_at_10_strict": ndcg} for q in queries}
    metrics = {"L": arm(.8, .4), "D:a": arm(1, .5), "H:a": arm(1, .7), "H:b": arm(.8, .9), "R:r|a": arm(1, .9)}
    costs = {a: {"query_p95_seconds": 1, "index_size_bytes": 10, "wall_seconds": 10} for a in metrics}
    return queries, metrics, costs


def test_item1_two_stage_decision_excludes_bad_coverage_and_uses_ndcg():
    queries, metrics, costs = _decision_fixture()
    costs["R:r|a"]["query_p95_seconds"] = 10
    result = b.decide(metrics, queries, costs, usable_queries=120, kappa_gate=True, iterations=20)
    assert result["outcome"] == "RECOMMENDED"
    assert result["recommended_configuration"] == "R:r|a"
    assert not result["coverage_comparisons"]["H:b"]["eligible_noninferior"]
    assert "H:b" not in result["ranking_comparisons"]
    assert result["ranking_comparisons"]["H:a"]["upper_95"] == pytest.approx(.2)


@pytest.mark.parametrize("reason,outcome", [("poor_reranker", "NO_RERANKER"), ("no_reranker", "NO_RERANKER"), ("bad_hybrids", "NO_ELIGIBLE_HYBRID"), ("sparse", "INCONCLUSIVE"), ("kappa", "INCONCLUSIVE"), ("missing_cost", "INCONCLUSIVE")])
def test_item1_all_terminal_outcomes_and_empty_candidate_set(reason, outcome):
    queries, metrics, costs = _decision_fixture()
    if reason == "poor_reranker":
        for entry in metrics["R:r|a"].values():
            entry["ndcg_at_10_strict"] = .5
    elif reason == "no_reranker":
        metrics.pop("R:r|a")
    elif reason == "bad_hybrids":
        for entry in metrics["H:a"].values():
            entry["recall_at_20_strict"] = .5
    elif reason == "missing_cost":
        costs["R:r|a"]["query_p95_seconds"] = None
    result = b.decide(metrics, queries, costs, usable_queries=59 if reason == "sparse" else 60, kappa_gate=reason != "kappa", iterations=20)
    assert result["outcome"] == outcome
    if outcome == "NO_RERANKER":
        assert result["recommended_configuration"] == "H:a"
    else:
        assert result["recommended_configuration"] is None


def test_item1_equal_cluster_weight_cost_ties_and_zero_queries():
    values = {"a": (1., 0.), "b": (1., 0.), "c": (0., 1.)}
    clusters = {"a": "pair", "b": "pair", "c": "single"}
    result = b.paired_cluster_bootstrap(values, clusters, iterations=100)
    assert result["estimate"] == 0
    assert b._cluster_mean({"a": 1, "b": 1, "c": 0}, clusters) == .5
    queries, metrics, costs = _decision_fixture()
    for entry in metrics["R:r|a"].values():
        entry["ndcg_at_10_strict"] = .7
    costs["R:r|a"].update(index_size_bytes=5)
    result = b.decide(metrics, queries, costs, usable_queries=120, kappa_gate=True, iterations=20)
    assert result["recommended_configuration"] == "R:r|a"
    costs["H:a"].update(index_size_bytes=5, wall_seconds=1)
    assert b.decide(metrics, queries, costs, usable_queries=120, kappa_gate=True, iterations=20)["recommended_configuration"] == "H:a"
    assert b.paired_cluster_bootstrap({}, {}, iterations=2)["estimate"] == 0
    with pytest.raises(ValueError):
        b.paired_cluster_bootstrap(values, clusters, iterations=0)


def test_item5_search_without_manifest_refuses_before_any_model(tmp_path, monkeypatch):
    monkeypatch.setattr(b, "_new_encoder", lambda *a: pytest.fail("No compute authorized"))
    with pytest.raises(FileNotFoundError, match="run-manifest"):
        b.search(tmp_path / "db", tmp_path, models=[b.E5], rerankers=[], query_limit=120, families=["G1", "G2", "G3"])


def test_item5_search_refuses_partial_or_excluded_queries(frozen, monkeypatch):
    b.admit(frozen.work, frozen.measurements)
    monkeypatch.setattr(b, "_new_encoder", lambda *a: pytest.fail("must not load"))
    with pytest.raises(ValueError, match="all and only"):
        b.search(frozen.source, frozen.work, models=[b.E5], rerankers=[], query_limit=119, families=["G1", "G2", "G3"])
    with pytest.raises(ValueError, match="all and only"):
        b.search(frozen.source, frozen.work, models=[b.E5], rerankers=[], query_limit=120, families=["G3"])


class Process:
    def __init__(self):
        self.terminated = False
        self.killed = False
    def terminate(self):
        self.terminated = True
    def kill(self):
        self.killed = True
    def join(self, **kwargs):
        pass
    def is_alive(self):
        return not self.terminated


class Pipe:
    def __init__(self, clock, message=None, finish_at=None):
        self.clock = clock
        self.message = message
        self.finish_at = finish_at
    def poll(self, seconds):
        self.clock[0] += 300
        return self.finish_at is not None and self.clock[0] >= self.finish_at
    def recv(self):
        return self.message


def test_item6_deadline_is_1point5_running_time_and_persists_on_resume():
    assert b._stop_reason(150, 100, None, 100000) is None
    assert b._stop_reason(151, 100, None, 1) == "DEADLINE"
    assert b._stop_reason(5, 100, 0, 1800) == "ADMISSION_REFUSED"
    clock = [0.]
    process = Process()
    state = {"running_seconds": 100}
    with pytest.raises(RuntimeError, match="DEADLINE"):
        b._supervise(process, Pipe(clock), state, 200, clock=lambda: clock[0], probe=lambda: True)
    assert state["running_seconds"] == 400
    assert state["status"] == "DEADLINE" and process.terminated


def test_item6_consecutive_refusals_stop_and_healthy_probe_resets():
    clock = [0.]
    process = Process()
    state = {}
    probes = []
    def refused():
        probes.append(clock[0])
        return False
    with pytest.raises(RuntimeError, match="ADMISSION_REFUSED"):
        b._supervise(process, Pipe(clock), state, 10000, clock=lambda: clock[0], probe=refused)
    assert probes == [300, 600, 900, 1200, 1500, 1800, 2100]
    assert process.terminated and state["running_seconds"] == 2100
    clock[0] = 0
    state = {}
    message = {"ok": True, "result": {"fixture": True}}
    status = iter([False, False, False, False, False, True, False, False, False, False])
    result = b._supervise(Process(), Pipe(clock, message, 3000), state, 10000, clock=lambda: clock[0], probe=lambda: next(status))
    assert result == message and state["status"] == "done"


def test_item6_quiet_window_end_stops_without_counting_calendar_gap():
    clock = [0.]
    state = {"running_seconds": 10}
    with pytest.raises(RuntimeError, match="QUIET_WINDOW_ENDED"):
        b._supervise(Process(), Pipe(clock), state, 10000, clock=lambda: clock[0], probe=lambda: True, window_end=500, wall_clock=lambda: 1000 + clock[0])
    assert state["running_seconds"] == 10
    assert state["status"] == "QUIET_WINDOW_ENDED"


def test_item6_launch_enforces_memory_threads_and_both_priorities(monkeypatch):
    calls = []
    monkeypatch.setattr(b.resource, "getrlimit", lambda *a: (b.resource.RLIM_INFINITY, b.resource.RLIM_INFINITY))
    monkeypatch.setattr(b.resource, "setrlimit", lambda *a: calls.append(("memory", a)))
    monkeypatch.setattr(b.os, "getpriority", lambda *a: 5)
    monkeypatch.setattr(b.os, "nice", lambda n: calls.append(("nice", n)))
    import sys
    monkeypatch.setitem(sys.modules, "psutil", SimpleNamespace(IOPRIO_CLASS_IDLE=3, Process=lambda: SimpleNamespace(ionice=lambda n: calls.append(("io", n)))))
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(set_num_threads=lambda n: calls.append(("threads", n)), set_num_interop_threads=lambda n: calls.append(("interop", n))))
    for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS", "ORT_NUM_THREADS", "TOKENIZERS_PARALLELISM"):
        monkeypatch.setenv(key, "fixture")
    report = b._enforce_host_limits()
    assert ("memory", (b.resource.RLIMIT_AS, (10 * 1024**3, 10 * 1024**3))) in calls
    assert ("nice", 14) in calls and ("io", 3) in calls
    assert ("threads", 6) in calls and ("interop", 6) in calls
    assert b.os.environ["OMP_NUM_THREADS"] == "6"
    assert b.os.environ["TOKENIZERS_PARALLELISM"] == "false"
    assert report == b.GUARDRAILS


def test_item6_host_lock_and_unavailable_admission_fail_closed(frozen, monkeypatch):
    with b._heavy_lock(), pytest.raises(ValueError, match="Another heavy"):
        with b._heavy_lock():
            pytest.fail("must refuse")
    monkeypatch.setattr(b, "_admission_probe", lambda: False)
    with pytest.raises(ValueError, match="unhealthy or unknown"):
        b._guarded_step(dict, (), {}, frozen.work, "fixture", 1)
    with pytest.raises(ValueError, match="positive"):
        b._guarded_step(dict, (), {}, frozen.work, "fixture", 0)


def test_item6_probe_unknown_is_not_healthy(monkeypatch):
    from scripts.orchestration import dispatch_admission
    monkeypatch.setattr(dispatch_admission, "evaluate", lambda *a: SimpleNamespace(admitted=True, probe=None))
    assert not b._admission_probe()
    monkeypatch.setattr(dispatch_admission, "evaluate", lambda *a: SimpleNamespace(admitted=True, probe=SimpleNamespace(proc_available=True, mem_available_bytes=100, load_per_cpu=.1)))
    assert b._admission_probe()


def test_item6_worker_enforces_limits_before_call_and_sends_typed_error(monkeypatch):
    events = []
    monkeypatch.setattr(b, "_enforce_host_limits", lambda: events.append("guard") or b.GUARDRAILS)
    connection = SimpleNamespace(send=lambda message: events.append(message), close=lambda: events.append("close"))
    b._heavy_worker(connection, lambda: events.append("compute") or {"result": 1}, (), {})
    assert events[:2] == ["guard", "compute"]
    assert events[2]["ok"] and events[2]["guardrails"] == b.GUARDRAILS
    def failure():
        raise ValueError("fixture")
    b._heavy_worker(connection, failure, (), {})
    assert events[-2] == {"ok": False, "error": "ValueError: fixture"}


def test_int8_quantization_wraps_each_adapter(monkeypatch):
    import sys
    calls = []
    torch = SimpleNamespace(ao=SimpleNamespace(quantization=SimpleNamespace(quantize_dynamic=lambda module, types, **kwargs: calls.append((module, types, kwargs)) or "quantized")), nn=SimpleNamespace(Linear="linear"), qint8="int8")
    monkeypatch.setitem(sys.modules, "torch", torch)
    assert b._quantize_reranker(("module", "tokenizer"), {"kind": "qwen"}) == ("quantized", "tokenizer")
    encoder = SimpleNamespace(model="module")
    assert b._quantize_reranker(encoder, {"kind": "cross_encoder"}).model == "quantized"
    assert b._quantize_reranker("module", {"kind": "jina"}) == "quantized"
    assert all(c[2] == {"dtype": "int8", "inplace": False} for c in calls)


def test_item3_measure_embedder_uses_exact_frozen_sample_and_projects(frozen, monkeypatch):
    calls = []
    clock = [0.]
    meta = {"kind": "sentence", "max_tokens": 2048, "prefixes": frozen.configs[b.E5]["prefixes"]}
    monkeypatch.setattr(b, "_new_encoder", lambda *a: (SimpleNamespace(tokenizer=Tokenizer()), meta))
    monkeypatch.setattr(b.time, "perf_counter", lambda: clock[0])
    def encode(model, metadata, texts, repo, batch):
        calls.extend(texts)
        clock[0] += len(texts) / 10
        return [[1] for _ in texts]
    monkeypatch.setattr(b, "_encode_batch", encode)
    def query(*args):
        clock[0] += .2
        return [1]
    monkeypatch.setattr(b, "_query_vector", query)
    result = b.measure(frozen.source, frozen.work, b.E5, batch_size=16)
    assert result["sample_rows"] == 500 and result["sample_seconds"] == pytest.approx(50)
    assert result["projected_seconds"] == pytest.approx(60)
    assert result["query_seconds"] == pytest.approx(.2)
    assert len(calls) == 516  # Separate 16-chunk warmup, then all 500 sample rows.
    again = b.measure(frozen.source, frozen.work, b.E5, batch_size=16)
    assert again["sample_seconds"] == result["sample_seconds"]
    assert len(calls) == 532  # Resume does only warmup, not the frozen sample again.


def test_item3_measure_reranker_uses_frozen_pairs_and_actual_latency(frozen, monkeypatch):
    _, pairs = _timing(frozen)
    b.admit(frozen.work, frozen.measurements)
    repo = next(iter(b.RERANKERS))
    clock = [0.]
    monkeypatch.setattr(b.time, "perf_counter", lambda: clock[0])
    model = SimpleNamespace(tokenizer=Tokenizer())
    monkeypatch.setattr(b, "_new_reranker", lambda *a: (model, {"kind": "cross_encoder", "max_tokens": 2048}))
    seen = []
    def rerank(model, meta, query, candidates):
        seen.append((query, [r["chunk_id"] for r in candidates]))
        clock[0] += 5
        return [r["chunk_id"] for r in candidates][::-1]
    monkeypatch.setattr(b, "_rerank", rerank)
    result = b.measure(frozen.source, frozen.work, repo)
    assert result["timing_pairs_sha256"] == pairs["sha256"]
    assert result["p50_seconds"] == result["p95_seconds"] == result["mean_seconds"] == 5
    assert len(seen) == 25 and sum(len(pair[1]) for pair in seen) == 500
    b.measure(frozen.source, frozen.work, repo)
    assert len(seen) == 25


def test_cli_sample_manifest_and_fake_admit_no_compute(frozen, capsys, monkeypatch):
    monkeypatch.setattr(b, "_new_encoder", lambda *a: pytest.fail("model compute forbidden"))
    measurements_path = frozen.work / "fake-measurements.json"
    b._write_json(measurements_path, frozen.measurements)
    common = ["--sources-db", str(frozen.source), "--work-dir", str(frozen.work)]
    assert b.main(["sample", *common]) == 0
    assert json.loads(capsys.readouterr().out)["encode_sample_sha256"] == frozen.evaluation["encode_sample_sha256"]
    config = frozen.work / "config.json"
    b._write_json(config, frozen.configs)
    assert b.main(["manifest", "--model-config", str(config), *common]) == 0
    capsys.readouterr()
    assert b.main(["admit", "--measurements", str(measurements_path), *common]) == 0
    result = json.loads(capsys.readouterr().out)
    assert len(result["admitted_embedders"]) == 6 and result["encode_total_projected_seconds"] == 21000
    assert b.main(["search", "--query-limit", "1", *common]) == 1
    assert "all and only" in capsys.readouterr().err


def test_item6_guarded_launcher_success_resume_and_exhausted_deadline(frozen, monkeypatch):
    events = []
    process = Process()
    monkeypatch.setenv("OPENBLAS_NUM_THREADS", "42")
    def start():
        assert all(b.os.environ[k] == "6" for k in b.THREAD_ENV)
        events.append("start")
    process.start = start
    process.join = lambda **kw: events.append("join")
    parent = SimpleNamespace(close=lambda: events.append("parent-close"))
    child = SimpleNamespace(close=lambda: events.append("child-close"))
    context = SimpleNamespace(Pipe=lambda **kw: (parent, child), Process=lambda **kw: process)
    monkeypatch.setattr(b.multiprocessing, "set_executable", lambda path: events.append("interpreter"))
    monkeypatch.setattr(b.multiprocessing, "get_context", lambda method: context)
    monkeypatch.setattr(b, "_admission_probe", lambda: True)
    def supervise(proc, pipe, state, projection, **kwargs):
        state.update(status="done", running_seconds=2)
        return {"ok": True, "result": {"fixture": True}, "guardrails": b.GUARDRAILS}
    monkeypatch.setattr(b, "_supervise", supervise)
    result = b._guarded_step(dict, (), {}, frozen.work, "fixture", 10)
    assert result == {"fixture": True, "host_guardrails": b.GUARDRAILS}
    assert events == ["interpreter", "start", "child-close", "join", "parent-close"]
    assert b.os.environ["OPENBLAS_NUM_THREADS"] == "42"
    assert b._guarded_step(dict, (), {}, frozen.work, "fixture", 10) == result
    assert events.count("start") == 1
    path = frozen.work / "steps" / (b.hashlib.sha256(b"fixture").hexdigest() + ".json")
    state = json.loads(path.read_text())
    state.update(status="DEADLINE", running_seconds=16)
    b._write_json(path, state)
    with pytest.raises(RuntimeError, match="exhausted"):
        b._guarded_step(dict, (), {}, frozen.work, "fixture", 10)
    assert events.count("start") == 1
    with pytest.raises(ValueError, match="configuration mismatch"):
        b._guarded_step(dict, (), {}, frozen.work, "fixture", 12)


def test_item6_failed_child_and_eof_are_typed(monkeypatch):
    clock = [0.]
    state = {}
    with pytest.raises(RuntimeError, match="fixture-error"):
        b._supervise(Process(), Pipe(clock, {"ok": False, "error": "fixture-error"}, 300), state, 10000, clock=lambda: clock[0], probe=lambda: True)
    assert state["status"] == "failed"
    state = {}
    pipe = Pipe(clock, finish_at=300)
    def eof():
        raise EOFError
    pipe.recv = eof
    with pytest.raises(RuntimeError, match="without a measurement"):
        b._supervise(Process(), pipe, state, 10000, clock=lambda: clock[0], probe=lambda: True)
    assert state["status"] == "failed"


def test_flag_model_is_loaded_at_pinned_revision_without_downloads(frozen, monkeypatch):
    import sys
    calls = []
    def download(repo, **kwargs):
        calls.append((repo, kwargs))
        return "stub-snapshot"
    def flag(snapshot, **kwargs):
        assert snapshot == "stub-snapshot" and kwargs["use_fp16"] is False
        return SimpleNamespace(tokenizer=SimpleNamespace(truncation_side="left"))
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(snapshot_download=download))
    monkeypatch.setitem(sys.modules, "FlagEmbedding", SimpleNamespace(BGEM3FlagModel=flag))
    model, meta = b._new_encoder("BAAI/bge-m3", frozen.work)
    assert meta["max_tokens"] == 8192 and model.tokenizer.truncation_side == "right"
    assert calls[0][1]["revision"] == "a" * 40


def test_retained_characters_use_original_offsets_not_decoded_length():
    class Normalizer(Tokenizer):
        def decode(self, ids, **kwargs):
            # Model tokenizer drops whitespace while decoding. Original
            # retention still accounts for the selected source spans.
            return super().decode(ids).replace(" ", "")
    _, _, retained = b._passage(" " * 700, Normalizer(), budget=512, tail=True)
    assert retained == 512


def test_item1_item2_item5_full_frozen_search_pool_and_score(frozen, monkeypatch):
    # Use the real frozen query allocation, with gold IDs mapped to this
    # independent synthetic corpus. No retrieval or model output informs it.
    original_queries, g3 = b._load_queries()
    gold_ids = sorted({q["gold_chunk_id"] for q in original_queries if q["family"] == "G1"})
    mapped = {cid: f"c{i:04}" for i, cid in enumerate(gold_ids)}
    queries = [{**q, "gold_chunk_id": mapped[q["gold_chunk_id"]]} if q["family"] == "G1" else q for q in original_queries]
    monkeypatch.setattr(b, "_load_queries", lambda: (queries, g3))
    # Fresh manifests preserve immutability; do not rewrite frozen files.
    work = frozen.work / "end-to-end"
    work.mkdir()
    evaluation = b.sample(frozen.source, work)
    run = b.run_manifest(frozen.source, work, frozen.configs)
    measurements = copy.deepcopy(frozen.measurements)
    measurements.update(b._measurement_binding(work))
    for repo, value in measurements["embedders"].items():
        value["projected_seconds"] = 1000 if repo == b.E5 else 100000
    decision = b.admit(work, measurements)
    assert decision["admitted_embedders"] == [b.E5]
    corpus_path = work / "corpus.sqlite3"
    rows = b._subset_rows(frozen.source)
    with sqlite3.connect(corpus_path) as conn:
        conn.execute("CREATE TABLE chunks(id INTEGER,chunk_id TEXT,title TEXT,text TEXT,source_file TEXT,subject TEXT,parent_section_id INTEGER)")
        conn.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?,?)", [tuple(row) for row in rows])
    index = work / "embeddings" / (b.E5.replace("/", "--") + ".sqlite3")
    index.parent.mkdir()
    with sqlite3.connect(index) as conn:
        conn.execute("CREATE TABLE vectors(chunk_id TEXT, text_sha256 TEXT, vector BLOB, dimensions INTEGER)")
        conn.executemany("INSERT INTO vectors VALUES (?, '', x'0000803f', 1)", [(r["chunk_id"],) for r in rows])
        conn.execute("CREATE TABLE index_metadata(key TEXT, value TEXT)")
        conn.execute("INSERT INTO index_metadata VALUES ('run_manifest_sha256',?)", (run["sha256"],))
    monkeypatch.setattr(b, "_copy_subset", lambda *a: corpus_path)
    def isolated(corpus, root, chosen, arm, embedder, ranker):
        assert chosen == evaluation["queries"] and len(chosen) == 120
        hits = [f"c{i:04}" for i in range(20)]
        return {"rankings": {q["id"]: hits for q in chosen}, "cost": {"query_p95_seconds": 2, "index_size_bytes": 100, "wall_seconds": 1000}}
    monkeypatch.setattr(b, "_isolated_arm", isolated)
    result = b.search(frozen.source, work, models=[b.E5], rerankers=[], query_limit=10000, families=["G1", "G2", "G3"])
    assert result["queries"] == evaluation["queries"]
    b.freeze_timing_pairs(work, result)
    assert b.pool(work)["queries"] == 120
    pool_rows = json.loads((work / "judging/pool.json").read_text())
    key = json.loads((work / "sealed/pool-key.json").read_text())
    items = {(r["query_id"], r["item_id"]): r["chunk_id"] for r in key}
    labels = []
    for query in pool_rows:
        for item in query["items"]:
            relevant = items[(query["query_id"], item["item_id"])] == "c0000"
            labels.append({"query_id": query["query_id"], "item_id": item["item_id"], "usable_quotation": relevant, "usable_exercise": False, "usable_example": False, "reason": "Independent synthetic relevance rule."})
    paths = [work / "a.jsonl", work / "b.jsonl"]
    for path in paths:
        path.write_text("\n".join(json.dumps(r) for r in labels))
    score = b.score(work, *paths, iterations=5)
    assert score["outcome"] == "NO_RERANKER" and score["recommended_configuration"] == f"H:{b.E5}"
    assert score["usable_queries"] == 120
    assert score["strata"][f"H:{b.E5}"]["pooled"]["ndcg_at_10_strict"] == 1
    assert score["strata"][f"H:{b.E5}"]["G1"]["n"] == 7
    assert score["strata"][f"H:{b.E5}"]["G2"]["n"] == 24
    assert score["strata"][f"H:{b.E5}"]["G3"]["n"] == 89
    assert any(name.startswith("G3-area:") for name in score["topic_coverage"])
    # A reranked arm cannot create new judged chunks, even with complete labels.
    result["arms"][f"R:r|{b.E5}"] = {q["id"]: ["c0599"] + [f"c{i:04}" for i in range(1, 20)] for q in evaluation["queries"]}
    b._write_json(work / "search-results.json", result)
    with pytest.raises(ValueError, match="permute"):
        b.score(work, *paths, iterations=5)


def test_item3_measurement_order_requires_failed_fp32_and_borderline(frozen):
    b.admit(frozen.work, frozen.measurements)
    repo = next(iter(b.RERANKERS))
    with pytest.raises(FileNotFoundError):
        b._measurement_preflight(frozen.work, repo, "int8", False)
    folder = frozen.work / "measurements"
    path = folder / (repo.replace("/", "--") + "-fp32-0.json")
    b._write_json(path, {**b._measurement_binding(frozen.work), **_attempt(frozen, 8)})
    with pytest.raises(ValueError, match="failing FP32"):
        b._measurement_preflight(frozen.work, repo, "int8", False)
    with pytest.raises(ValueError, match="only allowed"):
        b._measurement_preflight(frozen.work, repo, "fp32", True)
    b._write_json(path, {**b._measurement_binding(frozen.work), **_attempt(frozen, 9.5)})
    b._measurement_preflight(frozen.work, repo, "fp32", True)
    with pytest.raises(FileNotFoundError):
        b._measurement_preflight(frozen.work, repo, "int8", False)
    b._write_json(folder / (repo.replace("/", "--") + "-fp32-1.json"), {**b._measurement_binding(frozen.work), **_attempt(frozen, 12)})
    b._measurement_preflight(frozen.work, repo, "int8", False)
    with pytest.raises(ValueError, match="one frozen"):
        b._measurement_preflight(frozen.work, b.E5, "fp32", True)


def test_item4_embedder_uses_model_maximum_with_actual_prefix_overhead():
    model = SimpleNamespace(tokenizer=Tokenizer())
    rows = [{"text": "abcdefghij", "source_file": "book"}]
    stats = b._embedder_passage_stats(rows, model, {"max_tokens": 10, "prefixes": {"passage": "passage: "}}, b.E5)
    assert stats["book"]["truncation_rate"] == 1
    assert stats["book"]["retained_character_share"] == .1
    with pytest.raises(ValueError, match="no passage token budget"):
        b._embedder_passage_stats(rows, model, {"max_tokens": 9, "prefixes": {"passage": "passage: "}}, b.E5)
