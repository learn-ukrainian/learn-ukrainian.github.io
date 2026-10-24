"""Exercise the four mandatory classifiers through their real entry points."""

import subprocess

import pytest

from batch import batch_dispatcher_helpers, batch_otaman, batch_utils
from scripts.etymology import bulk_ocr_gemini


@pytest.mark.parametrize("message", ["run 7f3a503c9e1b2d44", "run z503nonhexZ"])
def test_ocr_identifier_is_not_transient(message):
    assert bulk_ocr_gemini.classify_error(message, "") == "error"


@pytest.mark.parametrize("message", [
    "run c0ffee4019ab77de",
    "run 7f3a503c9e1b2d44",
    "digest e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
])
def test_batch_identifier_is_unknown(message):
    assert batch_utils.classify_error(1, message) == batch_utils.ErrorCategory.UNKNOWN


@pytest.mark.parametrize("module", [batch_otaman, batch_dispatcher_helpers])
@pytest.mark.parametrize("stderr,stdout,expected", [
    ("", "digest e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", False),
    ("run 7f3a429c9e1b2d44", "", False),
    ("4", "29", False),
    ("HTTP 429", "abc", True),
    ("abc", "HTTP429", True),
    ("x429" + " " * 1997, "", False),
    (" 429" + " " * 1997, "", True),
    ("HTTP429" + " " * 1997, "", True),
    ("", "x429" + " " * 1997, False),
    ("", " 429" + " " * 1997, True),
    ("HTTP 429" + " " * 2000, "", False),
    ("0.429", "", False),
    ("", "v1.429", False),
    ("QUOTA", "", True),
    ("", "RESOURCE_EXHAUSTED", True),
    ("rate", " limit", False),
])
def test_dispatch_status_preserves_stream_and_tail_boundaries(monkeypatch, module, stderr, stdout, expected):
    result = subprocess.CompletedProcess([], 1, stdout=stdout, stderr=stderr)
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: result)
    if module is batch_otaman:
        actual = module.dispatch_otaman("a1", 1, "fixture")
    else:
        actual = module.dispatch_track("a1", "build", [])
    assert actual["quota_hit"] is expected
    assert actual["stderr"] == stderr[-2000:]
    assert actual["stdout_tail"] == stdout[-2000:]


@pytest.mark.parametrize("module", [batch_otaman, batch_dispatcher_helpers])
@pytest.mark.parametrize("error", [subprocess.TimeoutExpired("fixture", 1), OSError("offline fixture")])
def test_dispatch_exception_is_not_quota(monkeypatch, module, error):
    def fail(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(module.subprocess, "run", fail)
    if module is batch_otaman:
        actual = module.dispatch_otaman("a1", 1, "fixture")
    else:
        actual = module.dispatch_track("a1", "build", [])
    assert actual["success"] is False
    assert actual["quota_hit"] is False
    assert actual["stdout_tail"] == ""
