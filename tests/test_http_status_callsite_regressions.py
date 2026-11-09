"""Offline behavioral checks for the remaining named status classifiers."""

import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ai_llm import fallback
from build import dispatch as build_dispatch
from pipeline import dispatch as pipeline_dispatch
from rag import benchmark_embeddings
from scripts.ai_agent_bridge import _gemini, _model
from tools import analyze_textbook_pages, convert_plans_v4


@pytest.mark.parametrize("classifier", [
    pipeline_dispatch._is_rate_limited,
    fallback.is_gemini_rate_limited,
    _gemini._is_gemini_429_error,
    build_dispatch._is_rate_limited,  # Legacy helper, tested directly, no live caller claimed.
])
@pytest.mark.parametrize("message,expected", [
    ("run 7f3a429c9e1b2d44", False),
    ("digest e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", False),
    ("z429nonhexZ", False), ("v1.429", False), ("0.429", False),
    ("_429", False), ("4290", False), ("HTTP429", True),
    ("status: 429", True), ("429 Too Many Requests", True),
    ("HTTP503", False), ("", False),
])
def test_rate_classifiers_select_only_real_429(classifier, message, expected):
    assert classifier(message) is expected


@pytest.mark.parametrize("classifier,message", [
    (pipeline_dispatch._is_rate_limited, "Error authenticating"),
    (pipeline_dispatch._is_rate_limited, "FatalAuthenti"),
    (pipeline_dispatch._is_rate_limited, "RESOURCE_EXHAUSTED"),
    (pipeline_dispatch._is_rate_limited, "RATE LIMIT"),
    (pipeline_dispatch._is_rate_limited, "quota exceeded"),
    (fallback.is_gemini_rate_limited, "RESOURCE_EXHAUSTED"),
    (fallback.is_gemini_rate_limited, "QUOTA"),
    (fallback.is_gemini_rate_limited, "rate_limited"),
    (fallback.is_gemini_rate_limited, "rate limit exceeded"),
    (fallback.is_gemini_rate_limited, "free tier limits"),
    (fallback.is_gemini_rate_limited, "no capacity available"),
    (fallback.is_gemini_rate_limited, "model is overloaded"),
    (fallback.is_gemini_rate_limited, "UNAVAILABLE"),
    (_gemini._is_gemini_429_error, "TOO MANY REQUESTS"),
    (_gemini._is_gemini_429_error, "RATE LIMIT"),
    (_gemini._is_gemini_429_error, "rate_limit"),
    (_gemini._is_gemini_429_error, "capacity unavailable"),
    (_gemini._is_gemini_429_error, "no capacity available"),
    (build_dispatch._is_rate_limited, "RESOURCE_EXHAUSTED"),
    (build_dispatch._is_rate_limited, "rate_limit"),
    (build_dispatch._is_rate_limited, "capacity"),
    (build_dispatch._is_rate_limited, "Too Many Requests"),
])
def test_original_rate_keywords(classifier, message):
    assert classifier(message) is True


def test_fallback_none_is_not_rate_limited():
    assert fallback.is_gemini_rate_limited(None) is False


@pytest.mark.parametrize("message,attempt,expected", [
    ("run 7f3a429c9e1b2d44", 0, "continue"),
    ("HTTP429", 0, "retry"), ("HTTP429", 2, "stop"),
    ("quota", 0, "retry"), ("exhausted your capacity", 0, "retry"),
    ("Exhausted your capacity", 0, "continue"),
    ("Model not found HTTP429", 0, "stop"),
])
def test_bridge_error_actions(monkeypatch, message, attempt, expected):
    sleep = Mock()
    monkeypatch.setattr(_gemini.time, "sleep", sleep)
    assert _gemini._handle_gemini_error(message, "fixture-model", attempt, 3, 2) == expected
    assert sleep.call_args_list == ([((2 * 2**attempt,),)] if expected == "retry" else [])


@pytest.mark.parametrize("message,expected", [
    ("run 7f3a429c9e1b2d44", "check failed"),
    ("z429nonhexZ", "check failed"), ("HTTP429", "quota is exhausted"),
    ("QUOTA", "quota is exhausted"), ("EXHAUSTED", "quota is exhausted"),
    ("not found HTTP429", "not available on this account"),
    ("NOT AVAILABLE", "not available on this account"),
    ("invalid model", "not available on this account"),
])
def test_model_check_failure_message(capsys, message, expected):
    result = subprocess.CompletedProcess([], 1, stdout="", stderr=message)
    _model._handle_model_check_failure(result, "fixture-model", None)
    assert expected in capsys.readouterr().out


@pytest.mark.parametrize("message,expected", [
    ("c0ffee4019ab77de", False), ("z401nonhexZ", False),
    ("0.401", False), ("HTTP401", True), ("401 Unauthorized", True),
    ("HTTP403", False),
])
def test_embedding_auth_exception_text(message, expected):
    assert benchmark_embeddings.is_hf_unauthorized(RuntimeError(message)) is expected


def test_embedding_numeric_status_still_wins():
    exc = RuntimeError("opaque failure")
    exc.response = SimpleNamespace(status_code=401)
    assert benchmark_embeddings.is_hf_unauthorized(exc) is True


@pytest.mark.parametrize("message,retries", [
    ("run 7f3a429c9e1b2d44", 0), ("z429nonhexZ", 0),
    ("v1.429", 0), ("HTTP429", 3), ("RESOURCE_EXHAUSTED", 3),
    ("resource_exhausted", 0), ("Thinking_config", 0),
])
def test_page_analysis_does_not_retry_identifiers(monkeypatch, tmp_path, message, retries):
    module = analyze_textbook_pages
    run = Mock(return_value=subprocess.CompletedProcess([], 1, stdout="", stderr=message))
    sleep = Mock()
    monkeypatch.setattr(module, "render_page", lambda *args: True)
    monkeypatch.setattr(module.subprocess, "run", run)
    monkeypatch.setattr(module.time, "sleep", sleep)
    record = {"page_id": "fixture", "pdf_path": tmp_path / "fixture.pdf", "page_num": 0}
    assert module.analyze_page_via_cli(record, tmp_path) is None
    assert sleep.call_count == retries
    assert run.call_count == max(1, retries)


@pytest.fixture()
def plan_cli(monkeypatch):
    from scripts.review import model_catalog

    # Isolate the existing admission boundary; no model is admitted or called.
    monkeypatch.setattr(model_catalog, "require_execution_model", Mock())
    sleep = Mock()
    monkeypatch.setattr(convert_plans_v4.time, "sleep", sleep)
    return convert_plans_v4, sleep


@pytest.mark.parametrize("message,wait", [
    ("run 7f3a429c9e1b2d44", None), ("z429nonhexZ", None),
    ("0.429", None), ("HTTP429", 60), ("QUOTA", 60), ("RATE", 60),
])
def test_plan_conversion_preserves_output_on_unrelated_failure(monkeypatch, plan_cli, message, wait):
    module, sleep = plan_cli
    response = "fixture output " * 20
    proc = SimpleNamespace(returncode=1, communicate=Mock(return_value=(response, message)))
    popen = Mock(return_value=proc)
    monkeypatch.setattr(module.subprocess, "Popen", popen)
    result = module.call_gemini("fixture", max_retries=1)
    assert result == (None if wait else response.strip())
    assert sleep.call_args_list == ([((wait,),)] if wait else [])
    popen.assert_called_once()


@pytest.mark.parametrize("scenario,expected_calls,expected_sleeps", [
    ("success", 1, 0), ("read_error", 2, 1), ("invalid_json", 3, 2),
    ("timeout", 3, 3), ("exception", 1, 0), ("render_failure", 0, 0),
])
def test_page_analysis_offline_control_flow(monkeypatch, tmp_path, scenario, expected_calls, expected_sleeps):
    module = analyze_textbook_pages
    record = {"page_id": "fixture", "pdf_path": tmp_path / "fixture.pdf", "page_num": 0, "page": 1}

    def render(_pdf, _page, target):
        if scenario == "render_failure":
            return False
        target.write_bytes(b"offline fixture")
        return True

    okay = subprocess.CompletedProcess([], 0, stdout='{"page_type":"text","elements":[]}', stderr="")
    result = Mock(return_value=okay)
    if scenario == "read_error":
        result.side_effect = [subprocess.CompletedProcess([], 0, stdout="Error executing tool read_file", stderr=""), okay]
    elif scenario == "invalid_json":
        result.return_value = subprocess.CompletedProcess([], 0, stdout="invalid output", stderr="")
    elif scenario == "timeout":
        result.side_effect = subprocess.TimeoutExpired("offline fixture", 120)
    elif scenario == "exception":
        result.side_effect = OSError("offline fixture failure")
    sleep = Mock()
    monkeypatch.setattr(module, "render_page", render)
    monkeypatch.setattr(module.subprocess, "run", result)
    monkeypatch.setattr(module.time, "sleep", sleep)
    actual = module.analyze_page_via_cli(record, tmp_path)
    if scenario in ("success", "read_error"):
        assert actual["page_id"] == "fixture"
        assert actual["page_type"] == "text"
        assert actual["elements"] == []
    else:
        assert actual is None
    assert result.call_count == expected_calls
    assert sleep.call_count == expected_sleeps
    assert not (tmp_path / "fixture.png").exists()


@pytest.mark.parametrize("scenario", ["short", "empty_failure", "timeout", "missing", "exception"])
@pytest.mark.parametrize("attempts", [1, 2])
def test_plan_conversion_offline_retry_control(monkeypatch, plan_cli, scenario, attempts):
    module, sleep = plan_cli
    response = "fixture output " * 20
    initial = SimpleNamespace(returncode=0, communicate=Mock(return_value=("short", "")), kill=Mock())
    if scenario == "empty_failure":
        initial.returncode = 1
        initial.communicate.return_value = ("", "ordinary failure")
    elif scenario == "timeout":
        initial.communicate.side_effect = [subprocess.TimeoutExpired("fixture", 300), ("", "")]
    okay = SimpleNamespace(returncode=0, communicate=Mock(return_value=(response, "")))
    popen = Mock(side_effect=[initial, okay])
    if scenario == "missing":
        popen.side_effect = FileNotFoundError("offline fixture")
    elif scenario == "exception":
        popen.side_effect = [RuntimeError("offline fixture"), okay]
    monkeypatch.setattr(module.subprocess, "Popen", popen)
    actual = module.call_gemini("fixture", max_retries=attempts)
    recovered = attempts == 2 and scenario != "missing"
    assert actual == (response.strip() if recovered else None)
    assert popen.call_count == (2 if recovered else 1)
    assert sleep.call_count == (1 if recovered else 0)
    if scenario == "timeout":
        initial.kill.assert_called_once()


@pytest.mark.parametrize("message,expected", [
    ("run 7f3a429c9e1b2d44", False), ("HTTP429", True),
])
def test_inbox_capacity_adapter_uses_corrected_classifier(message, expected):
    from scripts.ai_agent_bridge._inbox import _is_gemini_capacity_error

    assert _is_gemini_capacity_error(message) is expected


@pytest.mark.parametrize("message,expected_fallback_checks", [
    ("run 7f3a429c9e1b2d44", 0), ("HTTP429", 2),
])
def test_pipeline_caller_enters_fallback_only_for_status(monkeypatch, message, expected_fallback_checks):
    dispatch = Mock(return_value=(False, message))
    routes = Mock(return_value=("fixture-transport", "fixture-model"))
    monkeypatch.setattr(pipeline_dispatch, "dispatch_gemini_raw", dispatch)
    monkeypatch.setattr(pipeline_dispatch, "_effective_agy_route", routes)
    assert pipeline_dispatch.dispatch_gemini("offline fixture", "fixture-task") == (False, message)
    dispatch.assert_called_once()
    # The configured default route has no distinct fallback, but only a real
    # status should inspect its two configured fallback candidates.
    assert routes.call_count == (expected_fallback_checks + 1 if expected_fallback_checks else 0)
