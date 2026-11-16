"""Secret redaction for config repr, child envs, and the no-print hook.

The live helper and the agent hook live in learn-ukrainian/learn-ukrainian.github.io.
These tests use synthetic values only.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from tests.launcher_sandbox import launcher_environment

REPO = Path(__file__).resolve().parents[1]
SYNTHETIC_KEY = "synthetic-cursor-key-0123456789"


@pytest.fixture(params=[False, True], ids=["single", "xdist"])
def xdist_enabled(request: pytest.FixtureRequest) -> bool:
    return request.param


def _run_secret_probe(
    tmp_path: Path,
    source: str,
    *,
    xdist_enabled: bool,
    token: str = SYNTHETIC_KEY,
    extra_args: tuple[str, ...] = (),
    credentials: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Load the real suite plugin against an isolated, synthetic child suite."""
    sample = tmp_path / "test_sample.py"
    sample.write_text(source, encoding="utf-8")
    env = launcher_environment()
    env.update(
        {
            "HOME": str(tmp_path),
            "PYTHONPATH": os.pathsep.join((str(REPO), str(REPO / "scripts"))),
            "CURSOR_API_KEY": token,
            "OPENAI_API_KEY": "synthetic-openai-key-0123456789",
            "SYNTHETIC_SERVICE_PASSWORD": "synthetic-service-password-0123456789",
            "SYNTHETIC_SERVICE_APIKEY": "synthetic-service-apikey-0123456789",
        }
    )
    if not credentials:
        env = {name: value for name, value in env.items() if name in {"HOME", "PATH", "TMPDIR", "LANG", "PYTHONPATH"}}
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(sample),
            "-p",
            "tests.conftest",
            "-p",
            "no:cacheprovider",
            *(["-n", "2"] if xdist_enabled else ["-p", "no:xdist"]),
            "-c",
            "/dev/null",
            "--rootdir",
            str(tmp_path),
            "-o",
            "addopts=",
            "-q",
            "--tb=long",
            "--junitxml",
            str(tmp_path / "report.xml"),
            *extra_args,
        ],
        cwd=REPO,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )


def test_conftest_scrubs_api_keys_and_fails_when_output_contains_one(tmp_path: Path, xdist_enabled: bool) -> None:
    secret_file = tmp_path / "sample.txt"
    other_key = "synthetic-openai-key-0123456789"
    secret_file.write_text(SYNTHETIC_KEY + "\n" + other_key, encoding="utf-8")
    proc = _run_secret_probe(
        tmp_path,
        "import os\nfrom pathlib import Path\n"
        "def test_api_key_is_absent():\n"
        "    assert 'CURSOR_API_KEY' not in os.environ\n"
        "    assert 'OPENAI_API_KEY' not in os.environ\n"
        "def test_prints_the_parent_key():\n"
        f"    print(Path({str(secret_file)!r}).read_text())\n",
        xdist_enabled=xdist_enabled,
    )
    assert proc.returncode == 1, proc.stderr + proc.stdout
    combined = proc.stdout + proc.stderr + (tmp_path / "report.xml").read_text()
    assert "1 passed" in combined
    assert SYNTHETIC_KEY not in combined
    assert other_key not in combined
    assert "scrubbed env var" in combined
    assert "CURSOR_API_KEY" in combined
    assert "OPENAI_API_KEY" in combined


@pytest.mark.parametrize("phase", ["assertion", "setup", "teardown", "collection", "skip"])
def test_conftest_redacts_unsuccessful_reports(tmp_path: Path, phase: str, xdist_enabled: bool) -> None:
    secret_file = tmp_path / "sample.txt"
    secret_file.write_text(SYNTHETIC_KEY, encoding="utf-8")
    prefix = (
        "import pytest\nfrom pathlib import Path\n"
        + f"def value():\n    return Path({str(secret_file)!r}).read_text()\n"
    )
    if phase == "collection":
        source = prefix + "print(value())\nraise RuntimeError(value())\n"
    elif phase == "assertion":
        source = prefix + "def test_sample():\n    print(value())\n    assert value() == 'expected-safe-value'\n"
    elif phase == "skip":
        source = prefix + "def test_sample():\n    print(value())\n    pytest.skip(value())\n"
    else:
        body = (
            "    print(value())\n    raise RuntimeError(value())\n"
            if phase == "setup"
            else "    yield\n    print(value())\n    raise RuntimeError(value())\n"
        )
        source = prefix + "@pytest.fixture(autouse=True)\ndef fixture():\n" + body + "def test_sample():\n    pass\n"
    proc = _run_secret_probe(tmp_path, source, xdist_enabled=xdist_enabled)
    expected = 0 if phase == "skip" else 2 if phase == "collection" and not xdist_enabled else 1
    assert proc.returncode == expected, proc.stderr + proc.stdout
    combined = proc.stdout + proc.stderr + (tmp_path / "report.xml").read_text()
    assert SYNTHETIC_KEY not in combined
    assert "[REDACTED]" in combined
    if phase != "skip":
        assert "AssertionError" in combined if phase == "assertion" else "RuntimeError" in combined


def test_collection_cannot_read_inherited_key(tmp_path: Path, xdist_enabled: bool) -> None:
    proc = _run_secret_probe(
        tmp_path,
        "import os\nassert 'CURSOR_API_KEY' not in os.environ\ndef test_sample():\n    pass\n",
        xdist_enabled=xdist_enabled,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    combined = proc.stdout + proc.stderr + (tmp_path / "report.xml").read_text()
    assert SYNTHETIC_KEY not in combined
    assert "1 passed" in proc.stdout


@pytest.mark.parametrize("secret_in_name", [False, True], ids=["value", "name"])
def test_conftest_redacts_junit_properties(tmp_path: Path, secret_in_name: bool, xdist_enabled: bool) -> None:
    secret_file = tmp_path / "sample.txt"
    secret_file.write_text(SYNTHETIC_KEY, encoding="utf-8")
    proc = _run_secret_probe(
        tmp_path,
        "from pathlib import Path\n"
        "def test_sample(record_property):\n"
        f"    secret = Path({str(secret_file)!r}).read_text()\n"
        "    record_property('safe-count', 7)\n"
        + (
            "    record_property(secret, 'safe-value')\n"
            if secret_in_name
            else "    record_property('credential', secret)\n"
        ),
        xdist_enabled=xdist_enabled,
    )
    assert proc.returncode == 1, proc.stderr + proc.stdout
    xml = (tmp_path / "report.xml").read_text()
    combined = proc.stdout + proc.stderr + xml
    assert SYNTHETIC_KEY not in combined
    assert "[REDACTED]" in xml
    assert '<property name="safe-count" value="7"' in xml
    assert "scrubbed env var CURSOR_API_KEY" in combined
    assert "1 failed" in proc.stdout
    assert "1 error" not in proc.stdout


def test_collection_cannot_read_inherited_password_or_apikey(tmp_path: Path, xdist_enabled: bool) -> None:
    proc = _run_secret_probe(
        tmp_path,
        "import os\n"
        "assert 'SYNTHETIC_SERVICE_PASSWORD' not in os.environ\n"
        "assert 'SYNTHETIC_SERVICE_APIKEY' not in os.environ\n"
        "def test_sample():\n    pass\n",
        xdist_enabled=xdist_enabled,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    combined = proc.stdout + proc.stderr + (tmp_path / "report.xml").read_text()
    assert SYNTHETIC_KEY not in combined
    assert "1 passed" in proc.stdout


def test_dispatcher_wrapper_is_executable() -> None:
    import stat

    assert (REPO / "run-dispatcher.sh").stat().st_mode & stat.S_IXUSR


def test_dispatcher_wrapper_retains_downstream_keys(tmp_path: Path) -> None:
    import shutil

    wrapper = tmp_path / "run-dispatcher.sh"
    shutil.copy2(REPO / "run-dispatcher.sh", wrapper)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    helper = tmp_path / ".venv/bin/python"
    helper.parent.mkdir(parents=True)
    # Execute the installed release's sanitizer, then use a synthetic dispatcher entry point.
    helper.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} "$@"\n', encoding="utf-8")
    helper.chmod(0o755)
    (scripts / "batch_dispatcher.py").write_text(
        "import os\n"
        "assert os.environ.get('GEMINI_API_KEY') == 'synthetic-gemini-key-0123456789'\n"
        "assert os.environ.get('CURSOR_API_KEY') == 'synthetic-cursor-key-0123456789'\n"
        "assert 'UNRELATED_API_KEY' not in os.environ\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [str(wrapper)],
        env=launcher_environment({
            "PATH": os.defpath,
            "GEMINI_API_KEY": "synthetic-gemini-key-0123456789",
            "CURSOR_API_KEY": SYNTHETIC_KEY,
            "UNRELATED_API_KEY": "synthetic-unrelated-key-0123456789",
        }),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert proc.returncode == 0
    assert "Clean exit" in proc.stdout
    assert "synthetic-" not in proc.stdout + proc.stderr


@pytest.mark.parametrize("release", ["installed", "missing"])
def test_launcher_secret_drop_fails_closed_without_the_release_sanitizer(tmp_path: Path, release: str) -> None:
    """Defect class: the launcher starts a provider with every inherited key when its sanitizer cannot run.

    With the installed lu-machinery release the child loses unneeded keys and keeps the product root and
    shared-state anchor its hooks need; with the release module unavailable (an interpreter whose
    site-packages are off), the launch refuses and the provider never runs.
    """
    from lu_machinery.common.repo_root import main_checkout_root

    interpreter = sys.executable
    if release == "missing":
        fake = tmp_path / "python"
        fake.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} -S "$@"\n', encoding="utf-8")
        fake.chmod(0o755)
        interpreter = str(fake)
    proc = subprocess.run(
        [
            "bash",
            "-uc",
            """
source scripts/lib/launcher_core.sh
source scripts/lib/project_interpreter.sh
LC_ROOT="$PWD"
LC_PROVIDER=claude
LC_HARNESS=""
LC_MODE=interactive
launcher_project_python() { printf '%s\\n' "$TEST_PYTHON"; }
launcher_drop_unneeded_secrets || exit 7
exec "${LC_CHILD_ENV_COMMAND[@]}" "$TEST_REAL_PYTHON" -c 'import json, os; print("provider-ran", json.dumps(dict(os.environ)))'
""",
        ],
        cwd=REPO,
        env=launcher_environment({
            "TEST_PYTHON": interpreter,
            "TEST_REAL_PYTHON": sys.executable,
            "UNRELATED_API_KEY": "synthetic-unrelated-key-0123456789",
            "LAUNCHER_SYNTHETIC_CONTROL": "1",
        }),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if release == "installed":
        assert proc.returncode == 0, proc.stderr
        assert "provider-ran" in proc.stdout
        child = json.loads(proc.stdout.split("provider-ran", 1)[1])
        assert "HOME" in child
        assert "UNRELATED_API_KEY" not in child
        assert "LAUNCHER_SYNTHETIC_CONTROL" not in child
        assert child["LU_PRODUCT_ROOT"] == str(REPO)
        assert child["LEARN_UKRAINIAN_PRIMARY_REPO_ROOT"] == str(main_checkout_root(REPO))
    else:
        assert proc.returncode == 7
        assert "provider-ran" not in proc.stdout
        assert "could not drop unneeded API keys" in proc.stderr
        assert "refusing to launch" in proc.stderr


@pytest.mark.parametrize("phase", ["collection", "call", "teardown"])
def test_conftest_redacts_warning_summary(tmp_path: Path, xdist_enabled: bool, phase: str) -> None:
    secret_file = tmp_path / "sample.txt"
    secret_file.write_text(SYNTHETIC_KEY, encoding="utf-8")
    prefix = (
        "import warnings, pytest\nfrom pathlib import Path\n"
        f"def warn():\n    warnings.warn('w:' + Path({str(secret_file)!r}).read_text(), UserWarning)\n"
    )
    if phase == "collection":
        source = prefix + "warn()\ndef test_sample():\n    pass\n"
    elif phase == "teardown":
        source = (
            prefix
            + "@pytest.fixture(autouse=True)\ndef fixture():\n    yield\n    warn()\ndef test_sample():\n    pass\n"
        )
    else:
        source = prefix + "def test_sample():\n    warn()\n"
    proc = _run_secret_probe(tmp_path, source, xdist_enabled=xdist_enabled)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    xml = (tmp_path / "report.xml").read_text()
    assert SYNTHETIC_KEY not in proc.stdout + proc.stderr + xml
    assert "UserWarning: w:[REDACTED]" in proc.stdout


@pytest.mark.parametrize("channel", ["stderr", "log"])
def test_conftest_fails_other_captured_disclosures(tmp_path: Path, xdist_enabled: bool, channel: str) -> None:
    secret_file = tmp_path / "sample.txt"
    secret_file.write_text(SYNTHETIC_KEY, encoding="utf-8")
    source = (
        "import sys, logging\nfrom pathlib import Path\ndef test_sample():\n"
        f"    secret = Path({str(secret_file)!r}).read_text()\n"
        + ("    print(secret, file=sys.stderr)\n" if channel == "stderr" else "    logging.warning(secret)\n")
    )
    proc = _run_secret_probe(tmp_path, source, xdist_enabled=xdist_enabled)
    assert proc.returncode == 1, proc.stderr + proc.stdout
    xml = (tmp_path / "report.xml").read_text()
    assert SYNTHETIC_KEY not in proc.stdout + proc.stderr + xml
    assert "scrubbed env var CURSOR_API_KEY" in proc.stdout


@pytest.mark.parametrize("secret_in_message", [False, True], ids=["source-line", "message-and-line"])
def test_conftest_redacts_warning_source_line(
    tmp_path: Path,
    xdist_enabled: bool,
    secret_in_message: bool,
) -> None:
    message = "w:" + SYNTHETIC_KEY if secret_in_message else "safe-warning"
    source = f"import warnings\ndef test_sample():\n    warnings.warn({message!r}, UserWarning)  # {SYNTHETIC_KEY}\n"
    proc = _run_secret_probe(tmp_path, source, xdist_enabled=xdist_enabled)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    xml = (tmp_path / "report.xml").read_text()
    assert SYNTHETIC_KEY not in proc.stdout + proc.stderr + xml
    assert "[REDACTED]" in proc.stdout


@pytest.mark.parametrize("summary", ["-rA", "-rx"])
def test_xfail_reason_is_redacted(tmp_path: Path, xdist_enabled: bool, summary: str) -> None:
    secret_file = tmp_path / "sample.txt"
    secret_file.write_text(SYNTHETIC_KEY)
    proc = _run_secret_probe(
        tmp_path,
        "import pytest\nfrom pathlib import Path\n"
        f"def test_sample():\n    pytest.xfail(Path({str(secret_file)!r}).read_text())\n",
        xdist_enabled=xdist_enabled,
        extra_args=(summary,),
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    combined = proc.stdout + proc.stderr + (tmp_path / "report.xml").read_text()
    assert SYNTHETIC_KEY not in combined
    assert "[REDACTED]" in combined
    assert "1 xfailed" in proc.stdout


def test_all_serialized_report_strings_are_redacted() -> None:
    from tests.conftest import _sanitize_secret_report

    report = pytest.TestReport(
        nodeid=SYNTHETIC_KEY,
        location=(SYNTHETIC_KEY, 1, SYNTHETIC_KEY),
        keywords={SYNTHETIC_KEY: 1},
        outcome="skipped",
        longrepr=("safe.py", 1, "safe"),
        when="call",
        wasxfail=SYNTHETIC_KEY,
        extra={"nested": [SYNTHETIC_KEY, (SYNTHETIC_KEY, 7)]},
    )
    sanitized = _sanitize_secret_report(report, {"CURSOR_API_KEY": SYNTHETIC_KEY})
    assert sanitized is report
    assert report.nodeid == "[REDACTED]"
    assert report.location == ("[REDACTED]", 1, "[REDACTED]")
    assert report.keywords == {"[REDACTED]": 1}
    assert report.wasxfail == "[REDACTED]"
    assert report.extra == {"nested": ["[REDACTED]", ("[REDACTED]", 7)]}


def test_collection_redaction_preserves_collected_items() -> None:
    from tests.conftest import _sanitize_secret_report

    items = [object()]
    report = pytest.CollectReport(
        nodeid="safe", outcome="passed", longrepr=None, result=items, extra={"secret": SYNTHETIC_KEY}
    )
    assert _sanitize_secret_report(report, {"CURSOR_API_KEY": SYNTHETIC_KEY}) is report
    assert report.extra == {"secret": "[REDACTED]"}
    assert report.result is items


@pytest.mark.parametrize(
    "token",
    [
        "SyntheticPrefix0123456789" + "m" * 300 + "SyntheticSuffix9876543210",
        "SyntheticPrefix0123456789" + "\\n" * 150 + "SyntheticSuffix9876543210",
    ],
)
def test_truncated_assertion_repr_is_redacted(tmp_path: Path, xdist_enabled: bool, token: str) -> None:
    secret_file = tmp_path / "sample.txt"
    secret_file.write_text(token)
    proc = _run_secret_probe(
        tmp_path,
        f"from pathlib import Path\ndef test_sample():\n    assert Path({str(secret_file)!r}).read_text() == 'safe'\n",
        xdist_enabled=xdist_enabled,
        token=token,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    combined = proc.stdout + proc.stderr + (tmp_path / "report.xml").read_text()
    assert token[:12] not in combined
    assert token[-13:] not in combined
    assert "[REDACTED]" in combined
    assert "AssertionError" in combined


@pytest.mark.parametrize("mode", [("-s",), ("--capture=no",), ("-o", "log_cli=true")])
@pytest.mark.parametrize("credentials", [True, False], ids=["credentials", "no-credentials"])
def test_direct_print_modes_warn_once_without_values(tmp_path: Path, mode: tuple[str, ...], credentials: bool) -> None:
    proc = _run_secret_probe(
        tmp_path,
        "def test_one():\n    pass\ndef test_two():\n    pass\n",
        xdist_enabled=False,
        extra_args=mode,
        credentials=credentials,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    combined = proc.stdout + proc.stderr
    assert combined.count("credential redaction cannot protect direct terminal output") == int(credentials)
    assert SYNTHETIC_KEY not in combined


@pytest.mark.parametrize("maxsize", [20, 30, 60, 120])
def test_repr_redaction_preserves_unrelated_ellipsis(maxsize: int) -> None:
    from _pytest._io.saferepr import saferepr

    from tests.conftest import _redact_secret_data

    value = "SyntheticPrefix0123456789" + "m" * 300 + "SyntheticSuffix9876543210"
    short = saferepr(value, maxsize=maxsize)
    assert _redact_secret_data(short, [value]) == "'[REDACTED]'"
    assert _redact_secret_data("'SyntheticPre...other-suffix'", [value]) == "'[REDACTED]'"
    neighbor = "'DifferentPre...other-suffix'"
    assert _redact_secret_data(neighbor, [value]) == neighbor
    assert _redact_secret_data({"safe": [7, None, (True, "a...b")]}, [value]) == {"safe": [7, None, (True, "a...b")]}


@pytest.mark.parametrize(
    "value",
    [
        "Secret'Head012345" + "m" * 300 + "Tail9876543210",
        'Secret"Head012345' + "m" * 300 + "Tail9876543210",
        "Secret\\Head012345" + "m" * 300 + "Tail9876543210",
        "Secret\nHead012345" + "m" * 300 + "Tail9876543210",
        "Secret...Head012345" + "m" * 300 + "Tail...9876543210",
    ],
    ids=["single-quote", "double-quote", "backslash", "newline", "ellipsis"],
)
def test_repr_redaction_handles_escaped_credentials(value: str) -> None:
    from _pytest._io.saferepr import saferepr

    from tests.conftest import _redact_secret_data

    shortened = saferepr(value, maxsize=30)
    assert "[REDACTED]" in _redact_secret_data(shortened, [value])
    wrapped = "outer-message: '" + shortened + "'"
    assert "Tail9876543210" not in _redact_secret_data(wrapped, [value])
    assert _redact_secret_data(repr(value), [value]) in {"'[REDACTED]'", '"[REDACTED]"'}


def test_serialization_hooks_redact_plugin_fields_in_both_directions(monkeypatch: pytest.MonkeyPatch) -> None:
    from _pytest import reports
    from _pytest.config import PytestPluginManager

    from tests import conftest

    monkeypatch.setattr(conftest, "_IMPORT_STRIPPED_SECRETS", {"CURSOR_API_KEY": SYNTHETIC_KEY})
    manager = PytestPluginManager()
    manager.register(reports)
    manager.register(conftest)

    class ExtraFields:
        @pytest.hookimpl(tryfirst=True)
        def pytest_report_to_serializable(self, report):
            data = reports.pytest_report_to_serializable(report)
            data["plugin_extra"] = {"nested": [SYNTHETIC_KEY]}
            return data

    manager.register(ExtraFields())
    report = pytest.TestReport(
        nodeid="safe", location=("safe.py", 1, "safe"), keywords={}, outcome="passed", longrepr=None, when="call"
    )
    outgoing = manager.hook.pytest_report_to_serializable(config=None, report=report)
    assert outgoing["plugin_extra"] == {"nested": ["[REDACTED]"]}
    incoming = reports.pytest_report_to_serializable(report)
    incoming["plugin_extra"] = {"nested": [SYNTHETIC_KEY]}
    restored = manager.hook.pytest_report_from_serializable(config=None, data=incoming)
    assert restored.plugin_extra == {"nested": ["[REDACTED]"]}


def test_xdist_redacts_parameter_ids_without_breaking_worker_routing(tmp_path: Path) -> None:
    secret_file = tmp_path / "sample.txt"
    secret_file.write_text(SYNTHETIC_KEY)
    proc = _run_secret_probe(
        tmp_path,
        "import pytest\nfrom pathlib import Path\n"
        f"@pytest.mark.parametrize('value', [Path({str(secret_file)!r}).read_text()])\n"
        "def test_sample(value):\n    assert value == 'safe'\n",
        xdist_enabled=True,
        extra_args=("-v",),
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    combined = proc.stdout + proc.stderr + (tmp_path / "report.xml").read_text()
    assert SYNTHETIC_KEY not in combined
    assert "[REDACTED]" in combined
    assert "AssertionError" in combined
    assert "INTERNALERROR" not in combined


@pytest.mark.parametrize("container", ["list", "tuple", "dict", "set", "nested"])
def test_round2_container_truncation(tmp_path: Path, xdist_enabled: bool, container: str) -> None:
    token = "SyntheticKeyPrefix012345" + "m" * 300 + "SyntheticSuffix9876543210"
    secret_file = tmp_path / "sample.txt"
    secret_file.write_text(token)
    shapes = {
        "list": ("[v, 'x']", "[v, 'y']"),
        "tuple": ("(v, 'x')", "(v, 'y')"),
        "dict": ("{'secret': v, 'safe': 'x'}", "{'secret': v, 'safe': 'y'}"),
        "set": ("{v, 'x'}", "{v, 'y'}"),
        "nested": ("[{'secret': (v,), 'safe': 'x'}]", "[{'secret': (v,), 'safe': 'y'}]"),
    }
    left, right = shapes[container]
    proc = _run_secret_probe(
        tmp_path,
        "from pathlib import Path\nfrom _pytest._io.saferepr import saferepr\ndef test_sample():\n"
        f"    v = Path({str(secret_file)!r}).read_text()\n"
        f"    print(saferepr({left}, maxsize=80))\n    assert {left} == {right}\n",
        xdist_enabled=xdist_enabled,
        token=token,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    terminal = proc.stdout + proc.stderr
    xml = (tmp_path / "report.xml").read_text()
    for output in (terminal, xml):
        assert token[:12] not in output
        assert token[-13:] not in output
        assert "AssertionError" in output
    assert "[REDACTED]" in terminal


@pytest.mark.parametrize("kind", ["bytes", "path", "object"])
def test_round2_property_types(tmp_path: Path, xdist_enabled: bool, kind: str) -> None:
    secret_file = tmp_path / "sample.txt"
    secret_file.write_text(SYNTHETIC_KEY)
    expressions = {"bytes": "v.encode()", "path": "Path('safe') / v", "object": "SecretObject(v)"}
    proc = _run_secret_probe(
        tmp_path,
        "from pathlib import Path\n"
        "class SecretObject:\n"
        "    def __init__(self, value):\n        self.value = value\n"
        "    def __str__(self):\n        return self.value\n"
        "def test_sample(record_property):\n"
        f"    v = Path({str(secret_file)!r}).read_text()\n"
        f"    record_property('credential', {expressions[kind]})\n"
        "    record_property('safe-count', 7)\n",
        xdist_enabled=xdist_enabled,
    )
    xml = (tmp_path / "report.xml").read_text()
    combined = proc.stdout + proc.stderr + xml
    assert SYNTHETIC_KEY not in combined
    assert proc.returncode == 1, combined
    assert "[REDACTED]" in xml
    assert '<property name="safe-count" value="7"' in xml
    assert "INTERNALERROR" not in combined


@pytest.mark.parametrize("mode", [("--capture=tee-sys",), ("--log-cli-level=INFO",)])
def test_round2_direct_output_warning(tmp_path: Path, mode: tuple[str, ...]) -> None:
    proc = _run_secret_probe(
        tmp_path,
        "import logging\ndef test_sample():\n    print('safe')\n    logging.info('safe')\n",
        xdist_enabled=False,
        extra_args=mode,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (proc.stdout + proc.stderr).count("credential redaction cannot protect direct terminal output") == 1


def test_round2_redactor_single_line_bound() -> None:
    import time

    source = (
        "from tests.conftest import _redact_secret_data\n"
        "line = \"'\" + '.' * 200_000\n"
        "assert _redact_secret_data(line, ['synthetic-performance-credential-0123456789']) == line\n"
        "print('bounded-redaction-ok')\n"
    )
    start = time.monotonic()
    proc = subprocess.run(
        [sys.executable, "-c", source],
        cwd=REPO,
        env=launcher_environment(),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout == "bounded-redaction-ok\n"
    assert time.monotonic() - start < 15


@pytest.mark.parametrize(
    "xdist_enabled,hook", [(False, "report"), (True, "report"), (True, "serialize"), (True, "deserialize")]
)
def test_round2_redaction_exception_fails_closed(tmp_path: Path, xdist_enabled: bool, hook: str) -> None:
    secret_file = tmp_path / "sample.txt"
    secret_file.write_text(SYNTHETIC_KEY)
    # Inject a failure after collection, so the actual reporting hooks see the
    # report, and the pytest child proves INTERNALERROR never renders locals.
    (tmp_path / "conftest.py").write_text(
        "import pytest\nfrom tests import conftest as shared\n"
        "@pytest.hookimpl(wrapper=True)\n"
        "def pytest_runtest_call(item):\n"
        "    result = yield\n"
        "    def broken(data, values):\n        raise RuntimeError('synthetic-redactor-failure')\n"
        + (
            "    shared._redact_secret_data = broken\n"
            if hook == "report"
            else "    shared._sanitize_secret_report = lambda report, secrets: report\n"
            + ("    shared._redact_secret_data = broken\n" if hook == "serialize" else "")
        )
        + "    return result\n"
        + (
            "def pytest_configure(config):\n"
            "    if not hasattr(config, 'workerinput'):\n"
            "        def broken(data, values):\n            raise RuntimeError('synthetic-redactor-failure')\n"
            "        shared._redact_secret_data = broken\n"
            "        shared._sanitize_secret_report = lambda report, secrets: report\n"
            if hook == "deserialize"
            else ""
        )
    )
    proc = _run_secret_probe(
        tmp_path,
        f"from pathlib import Path\ndef test_sample():\n    print(Path({str(secret_file)!r}).read_text())\n",
        xdist_enabled=xdist_enabled,
    )
    combined = proc.stdout + proc.stderr + (tmp_path / "report.xml").read_text()
    assert SYNTHETIC_KEY not in combined
    assert "INTERNALERROR" not in combined
    assert proc.returncode == 1, combined
    assert "[REDACTED] report unavailable: credential redaction failed" in combined


@pytest.mark.parametrize("length", [40, 108, 325])
@pytest.mark.parametrize("shape", ["bearer", "url", "list", "dict", "url-list", "url-dict"])
@pytest.mark.parametrize("mode", [(), ("-v",), ("-l",), ("-n", "2")], ids=["default", "verbose", "locals", "xdist"])
def test_round3_embedded_shortened_secret(tmp_path: Path, length: int, shape: str, mode: tuple[str, ...]) -> None:
    import xml.etree.ElementTree as ET

    # Alternating letter case keeps four-character leak checks distinct from
    # unrelated numeric process IDs printed by the nested test guards.
    token = ("aQbRcSdTeUfVgWhXiYjZkPlOmNnMoLpKqJrIsHtGuFvEwDxCyBzA" * 7)[:length]
    secret_file = tmp_path / "sample.txt"
    secret_file.write_text(token)
    expression = {
        "bearer": "'Bearer ' + v + ' tail'",
        "url": "'https://h/?token=' + v + '&a=1'",
        "list": "['Bearer ' + v + ' tail']",
        "dict": "{'header': 'Bearer ' + v + ' tail'}",
        "url-list": "['https://h/?token=' + v + '&a=1']",
        "url-dict": "{'url': 'https://h/?token=' + v + '&a=1'}",
    }[shape]
    proc = _run_secret_probe(
        tmp_path,
        "from pathlib import Path\nfrom _pytest._io.saferepr import saferepr\n"
        "def test_sample():\n"
        f"    v = Path({str(secret_file)!r}).read_text()\n"
        f"    value = {expression}\n"
        "    print(saferepr(value, maxsize=40))\n"
        "    assert value == 'x'\n",
        xdist_enabled=bool(mode == ("-n", "2")),
        token=token,
        extra_args=() if mode == ("-n", "2") else mode,
    )
    xml = (tmp_path / "report.xml").read_text()
    failure = ET.fromstring(xml).find(".//failure")
    assert failure is not None
    for output in (proc.stdout + proc.stderr, xml, failure.get("message", "")):
        # Every four-character secret fragment must be absent, including the
        # visible head and tail of reprlib clipping inside headers and URLs.
        assert not any(token[i : i + 4] in output for i in range(len(token) - 3))
    assert proc.returncode == 1, proc.stderr
    assert "[REDACTED]" in proc.stdout


@pytest.mark.parametrize("credentials", [False, True])
def test_round3_wrapper_property_does_not_persist_without_credentials(tmp_path: Path, credentials: bool) -> None:
    (tmp_path / "conftest.py").write_text(
        "import pytest\n"
        "@pytest.hookimpl(wrapper=True)\n"
        "def pytest_runtest_makereport(item, call):\n"
        "    report = yield\n"
        "    if report.when == 'call':\n"
        "        report.user_properties.append(('wrapper-only', 'safe'))\n"
        "    return report\n"
    )
    proc = _run_secret_probe(tmp_path, "def test_sample():\n    pass\n", xdist_enabled=False, credentials=credentials)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    xml = (tmp_path / "report.xml").read_text()
    assert 'name="wrapper-only"' not in xml


@pytest.mark.parametrize("overlap", [1, 4, 7])
def test_round3_short_ordinary_overlap_is_preserved(overlap: int) -> None:
    from tests.conftest import _redact_shortened_secret_reprs

    token = "ABCDEFGH" + "0123456789" * 4 + "ZYXWVUTS"
    text = repr("ordinary " + token[:overlap] + "..." + token[-overlap:] + " text")
    assert _redact_shortened_secret_reprs(text, [token]) == text


@pytest.mark.parametrize("edge", ["head", "tail", "open-head"])
def test_round3_embedded_overlap_at_minimum(edge: str) -> None:
    from tests.conftest import _redact_shortened_secret_reprs

    token = "ABCDEFGH" + "0123456789" * 4 + "ZYXWVUTS"
    text = {
        "head": "'Bearer ABCDEFGH...ordinary'",
        "tail": "'ordinary...ZYXWVUTS&a=1'",
        "open-head": "'Bearer ABCDEFGH...\n",
    }[edge]
    assert "[REDACTED]" in _redact_shortened_secret_reprs(text, [token])


@pytest.mark.parametrize("length", [40, 108, 325])
@pytest.mark.parametrize("shape", ["leading", "list", "dict", "trailing", "interior"])
@pytest.mark.parametrize("mode", [(), ("-v",), ("-l",), ("-n", "2")], ids=["default", "verbose", "locals", "xdist"])
def test_round4_leading_secret_with_trailer(tmp_path: Path, length: int, shape: str, mode: tuple[str, ...]) -> None:
    import xml.etree.ElementTree as ET

    token = ("aQbRcSdTeUfVgWhXiYjZkPlOmNnMoLpKqJrIsHtGuFvEwDxCyBzA" * 7)[:length]
    secret_file = tmp_path / "sample.txt"
    secret_file.write_text(token)
    expression = {
        "leading": "v + ':x-oauth-basic-trailer'",
        "list": "[v + ':x-oauth-basic-trailer']",
        "dict": "{'credential': v + ':x-oauth-basic-trailer'}",
        "trailing": "'prefix:' + v",
        "interior": "'prefix:' + v + ':trailer'",
    }[shape]
    proc = _run_secret_probe(
        tmp_path,
        "from pathlib import Path\nfrom _pytest._io.saferepr import saferepr\n"
        "def test_sample():\n"
        f"    v = Path({str(secret_file)!r}).read_text()\n"
        f"    value = {expression}\n"
        "    print(saferepr(value, maxsize=40))\n"
        "    assert value == 'expected-safe-value'\n",
        xdist_enabled=mode == ("-n", "2"),
        token=token,
        extra_args=() if mode == ("-n", "2") else mode,
    )
    assert proc.returncode == 1
    xml = (tmp_path / "report.xml").read_text()
    failure = ET.fromstring(xml).find(".//failure")
    assert failure is not None
    outputs = (proc.stdout + proc.stderr, xml, failure.get("message", ""), failure.text or "")
    for output in outputs:
        assert "[REDACTED]" in output
        assert not any(token[index : index + 8] in output for index in range(len(token) - 7))


@pytest.mark.parametrize("length", [40, 108, 325])
@pytest.mark.parametrize("shape", ["plain", "url"])
@pytest.mark.parametrize("xdist_enabled", [False, True], ids=["single", "xdist"])
def test_round5_assertion_suffix_fragments(tmp_path: Path, length: int, shape: str, xdist_enabled: bool) -> None:
    token = ("aQbRcSdTeUfVgWhXiYjZkPlOmNnMoLpKqJrIsHtGuFvEwDxCyBzA" * 7)[:length]
    secret_file = tmp_path / "sample.txt"
    secret_file.write_text(token)
    expression = "v" if shape == "plain" else "'https://host.invalid/?token=' + v"
    proc = _run_secret_probe(
        tmp_path,
        "from pathlib import Path\ndef test_sample():\n"
        + f"    v = Path({str(secret_file)!r}).read_text()\n    value = {expression}\n"
        + "    assert value + 'actual' == value + 'expected'\n",
        token=token,
        xdist_enabled=xdist_enabled,
    )
    assert proc.returncode == 1
    for output in (proc.stdout + proc.stderr, (tmp_path / "report.xml").read_text()):
        assert "[REDACTED]" in output
        assert not any(token[index : index + 8] in output for index in range(len(token) - 7))


@pytest.mark.parametrize("form", ["raw", "repr"])
def test_round5_quote_independent_fragments(form: str) -> None:
    from tests.conftest import _redact_secret_data

    token = "HeadAbCd0123\\\nMiddleEfGh4567TailIjKl8901"
    body = token if form == "raw" else repr(token)[1:-1]
    # Every eight-character window, including interior and escaped fragments,
    # must be covered without quotes, ellipsis, or an assignment key.
    for start in range(len(body) - 7):
        assert _redact_secret_data("before " + body[start : start + 8] + " after", [token]) == "before [REDACTED] after"
    assert _redact_secret_data("before " + body[3:25] + " after", [token]) == "before [REDACTED] after"


def test_round5_fragment_threshold_preserves_ordinary_text() -> None:
    from tests.conftest import _redact_secret_data

    token = "ABCDEFGH0123456789ZYXWVUTS"
    ordinary = "ordinary ABCDEFG / YXWVUTS; a...b; pytest assertion explanation and https://host.invalid/path"
    assert _redact_secret_data(ordinary, [token]) == ordinary
    assert _redact_secret_data("prefixABCDEFGHsuffix", [token]) == "prefix[REDACTED]suffix"
    assert _redact_secret_data("ABCDEFGH0123456789ZYXWVUTS", [token]) == "[REDACTED]"
    for length in range(1, 8):
        for start in range(len(token) - length + 1):
            text = "before " + token[start : start + length] + " after"
            assert _redact_secret_data(text, [token]) == text


def test_round5_fragment_spans_merge_without_losing_safe_neighbors() -> None:
    from tests.conftest import _redact_secret_data

    secrets = ["HeadAbCd0123456789", "TailEfGh9876543210"]
    text = "safe: HeadAbCd012345TailEfGh / 9876543210 safe"
    assert _redact_secret_data(text, secrets) == "safe: [REDACTED] / [REDACTED] safe"


@pytest.mark.parametrize("size", range(5, 20))
def test_round5_retains_tiny_repr_coverage(size: int) -> None:
    from _pytest._io.saferepr import saferepr

    from tests.conftest import _redact_secret_data

    token = "HeadAbCd0123456789MiddleEfGh9876543210TailIjKl"
    assert _redact_secret_data(saferepr(token, maxsize=size), [token]) == "'[REDACTED]'"
    assert _redact_secret_data("'other...ordinary'", [token]) == "'other...ordinary'"


@pytest.mark.parametrize(
    "prefix", ["github_pat_", "sk-proj-", "sk-svcacct-", "sk-ant-api03-", "sk-ant-oat01-", "sk-ant-admin01-"]
)
@pytest.mark.parametrize("form", ["raw", "repr"])
def test_round6_public_prefix_windows_preserve_body_coverage(prefix: str, form: str) -> None:
    from tests.conftest import _redact_secret_data

    token = prefix + "aQbRcSdTeUfVgWhX\\\nTailIjKl8901"
    body = token if form == "raw" else repr(token)[1:-1]
    for start in range(len(body) - 7):
        text = "before " + body[start : start + 8] + " after"
        expected = text if start + 8 <= len(prefix) else "before [REDACTED] after"
        assert _redact_secret_data(text, [token]) == expected
    fake = "before " + prefix + "000000 after"
    assert _redact_secret_data(fake, [token]) == fake
    assert _redact_secret_data(token, [token]) == "[REDACTED]"


@pytest.mark.parametrize("prefix", ["github_pat_", "sk-ant-api03-"])
@pytest.mark.parametrize("channel", ["print", "log"])
@pytest.mark.parametrize("disclosure", ["public-prefix", "crossing", "body"])
def test_round6_public_prefix_output_and_body_leaks(
    tmp_path: Path, xdist_enabled: bool, prefix: str, channel: str, disclosure: str
) -> None:
    token = prefix + "aQbRcSdTeUfVgWhXiYjZkPlOmNnMoLpKqJr"
    secret_file = tmp_path / "sample.txt"
    secret_file.write_text(token)
    expression = {
        "public-prefix": f"{prefix!r} + '000000'",
        "crossing": f"value[{len(prefix) - 7}:{len(prefix) + 1}]",
        "body": f"value[{len(prefix) + 5}:{len(prefix) + 13}]",
    }[disclosure]
    emit = "print(output)" if channel == "print" else "logging.warning('%s', output)"
    proc = _run_secret_probe(
        tmp_path,
        "import logging\nfrom pathlib import Path\ndef test_sample():\n"
        + f"    value = Path({str(secret_file)!r}).read_text()\n"
        + f"    output = {expression}\n    {emit}\n",
        token=token,
        xdist_enabled=xdist_enabled,
        extra_args=("-rP", "-o", "junit_logging=all"),
    )
    assert proc.returncode == (0 if disclosure == "public-prefix" else 1)
    for output in (proc.stdout + proc.stderr, (tmp_path / "report.xml").read_text()):
        if disclosure == "public-prefix":
            assert prefix + "000000" in output
            assert "captured output contained the value of scrubbed env var" not in output
        else:
            fragment = (
                token[len(prefix) - 7 : len(prefix) + 1]
                if disclosure == "crossing"
                else token[len(prefix) + 5 : len(prefix) + 13]
            )
            assert fragment not in output
            assert "[REDACTED]" in output
            assert "captured output contained the value of scrubbed env var CURSOR_API_KEY" in output
