"""Secret redaction for config repr, child envs, and the no-print hook.

The live helper and the agent hook live in learn-ukrainian/learn-ukrainian.github.io.
These tests use synthetic values only.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from agent_runtime.env_sanitize import (
    unneeded_env_var_names,
    without_unneeded_secrets,
)

REPO = Path(__file__).resolve().parents[1]
HOOK = REPO / "agents_extensions/shared/hooks/guard-secret-print.py"
SYNTHETIC_KEY = "synthetic-cursor-key-0123456789"


def test_github_identity_token_is_omitted_from_repr() -> None:
    from agent_runtime.agent_github_identity import GitHubIdentity

    identity = GitHubIdentity(token=SYNTHETIC_KEY, source="test")
    rendered = repr(identity)
    assert SYNTHETIC_KEY not in rendered
    assert "token" not in rendered
    assert identity.token == SYNTHETIC_KEY


def test_unneeded_env_var_names_drop_cursor_key_except_for_cursor() -> None:
    env = {
        "CURSOR_API_KEY": SYNTHETIC_KEY,
        "OPENAI_API_KEY": "synthetic-openai-key-0123456789",
        "GH_TOKEN": "ghp_synthetic",
        "PATH": "/usr/bin",
    }
    assert unneeded_env_var_names(env, "claude") == ["CURSOR_API_KEY", "OPENAI_API_KEY"]
    assert unneeded_env_var_names(env, "cursor") == ["OPENAI_API_KEY"]
    assert unneeded_env_var_names(env, "codex") == ["CURSOR_API_KEY"]
    assert unneeded_env_var_names(env, "dispatcher") == []
    kept = without_unneeded_secrets(env, "cursor")
    assert kept["CURSOR_API_KEY"] == SYNTHETIC_KEY
    assert "OPENAI_API_KEY" not in kept
    assert kept["GH_TOKEN"] == "ghp_synthetic"


def test_launchers_and_dispatcher_call_the_sanitizer() -> None:
    launcher = (REPO / "scripts/lib/launcher_core.sh").read_text(encoding="utf-8")
    assert "launcher_drop_unneeded_secrets" in launcher
    assert "env_sanitize.py" in launcher
    assert '--provider "$LC_PROVIDER"' in launcher
    delegate = (REPO / "scripts/delegate.py").read_text(encoding="utf-8")
    assert "without_unneeded_secrets(worker_env, dispatch_agent)" in delegate
    dispatcher = (REPO / "scripts/batch/batch_dispatcher.py").read_text(encoding="utf-8")
    assert 'unneeded_env_var_names(os.environ, "dispatcher")' in dispatcher
    wrapper = (REPO / "run-dispatcher.sh").read_text(encoding="utf-8")
    assert "--provider dispatcher" in wrapper
    for name in ("kimi.sh", "glm.sh"):
        launcher_text = (REPO / "scripts" / "launchers" / name).read_text(encoding="utf-8")
        assert "launcher_drop_unneeded_secrets" in launcher_text


def test_no_print_hook_blocks_seeded_echo() -> None:
    proc = subprocess.run(
        [sys.executable, str(HOOK), "--self-test"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    assert SYNTHETIC_KEY not in proc.stdout
    assert SYNTHETIC_KEY not in proc.stderr


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
    env = {name: os.environ[name] for name in ("PATH", "TMPDIR", "LANG") if name in os.environ}
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


@pytest.mark.parametrize(
    "provider,key",
    [
        ("gemini", "GEMINI_API_KEY"),
        ("cursor", "CURSOR_API_KEY"),
        ("codex", "OPENAI_API_KEY"),
    ],
)
def test_api_key_only_dispatch_preserves_only_child_provider_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    key: str,
) -> None:
    from scripts import delegate
    from scripts.batch.batch_dispatcher import _drop_unneeded_dispatcher_secrets

    # Prevent credential resolution from ever consulting the real host.
    monkeypatch.setattr(delegate, "_inject_gh_token_for_agent", lambda *args: None)
    monkeypatch.setattr(delegate, "_scrub_unusable_gh_config_dir", lambda *args: None)
    parent = {
        "HOME": str(tmp_path),
        "PATH": os.defpath,
        "GEMINI_API_KEY": "synthetic-gemini-key-0123456789",
        "CURSOR_API_KEY": SYNTHETIC_KEY,
        "OPENAI_API_KEY": "synthetic-openai-key-0123456789",
        "UNRELATED_API_KEY": "synthetic-unrelated-key-0123456789",
    }
    with monkeypatch.context() as patch:
        patch.setattr(os, "environ", parent.copy())
        _drop_unneeded_dispatcher_secrets()
        assert "UNRELATED_API_KEY" not in os.environ
        child_env = delegate._build_worker_env(task_id="synthetic-key-dispatch", dispatch_agent=provider)
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import os,sys; sys.exit(0 if os.environ.get(sys.argv[1]) == sys.argv[2] else 1)",
            key,
            parent[key],
        ],
        env=child_env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert proc.returncode == 0
    assert proc.stdout == proc.stderr == ""
    assert {name for name in child_env if name.endswith("_API_KEY")} == {key}


def test_dispatcher_wrapper_retains_downstream_keys(tmp_path: Path) -> None:
    import shutil

    wrapper = tmp_path / "run-dispatcher.sh"
    shutil.copy2(REPO / "run-dispatcher.sh", wrapper)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    helper = tmp_path / ".venv/bin/python"
    helper.parent.mkdir(parents=True)
    # Execute the real sanitizer, then use a synthetic dispatcher entry point.
    helper.write_text(
        "#!/bin/sh\n"
        'case "$1" in\n'
        f"scripts/agent_runtime/env_sanitize.py) shift; exec {shlex.quote(sys.executable)} "
        f'{shlex.quote(str(REPO / "scripts/agent_runtime/env_sanitize.py"))} "$@" ;;\n'
        f'*) exec {shlex.quote(sys.executable)} "$@" ;;\nesac\n',
        encoding="utf-8",
    )
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
        env={
            "PATH": os.defpath,
            "GEMINI_API_KEY": "synthetic-gemini-key-0123456789",
            "CURSOR_API_KEY": SYNTHETIC_KEY,
            "UNRELATED_API_KEY": "synthetic-unrelated-key-0123456789",
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert proc.returncode == 0
    assert "Clean exit" in proc.stdout
    assert "synthetic-" not in proc.stdout + proc.stderr


def test_launcher_preserves_parent_api_key_and_fails_closed(tmp_path: Path) -> None:
    helper = tmp_path / "primary"
    python = helper / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} "$@"\n', encoding="utf-8")
    python.chmod(0o755)
    core = REPO / "scripts/lib/launcher_core.sh"
    clear = f"""
set -euo pipefail
export LC_PROVIDER=claude LC_MODE=interactive LC_DRY_RUN=0
export LC_ROOT={shlex.quote(str(REPO))}
export LC_DURABLE_HELPER_ROOT={shlex.quote(str(helper))}
export CURSOR_API_KEY={shlex.quote(SYNTHETIC_KEY)}
source {shlex.quote(str(core))}
launcher_drop_unneeded_secrets
if [ "${{CURSOR_API_KEY:-}}" != {shlex.quote(SYNTHETIC_KEY)} ]; then
  printf 'parent-changed\\n'
  exit 2
fi
printf 'parent-preserved\\n'
"""
    cleared = subprocess.run(
        ["bash", "-c", clear],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert cleared.returncode == 0, cleared.stderr
    assert cleared.stdout.strip() == "parent-preserved"
    assert SYNTHETIC_KEY not in cleared.stdout + cleared.stderr

    python.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    marker = tmp_path / "provider-started"
    refuse = f"""
set -euo pipefail
export LC_PROVIDER=claude LC_MODE=interactive LC_DRY_RUN=0
export LC_ROOT={shlex.quote(str(REPO))}
export LC_DURABLE_HELPER_ROOT={shlex.quote(str(helper))}
source {shlex.quote(str(core))}
launcher_exec_command touch {shlex.quote(str(marker))}
"""
    refused = subprocess.run(
        ["bash", "-c", refuse],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert refused.returncode != 0
    assert not marker.exists()
    assert "could not drop unneeded API keys" in refused.stderr


@pytest.mark.parametrize(
    "command",
    ["cat ~/.secrets/*", "env | grep KEY", "printenv *_KEY"],
)
def test_seeded_commands_are_blocked_by_the_hook(command: str) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("guard_secret_print_redaction", HOOK)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._scan_command(command, set())


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


@pytest.mark.parametrize(
    "provider,kept",
    [
        ("claude", {"ANTHROPIC_API_KEY", "CLAUDE_API_KEY"}),
        ("codex", {"CODEX_API_KEY", "OPENAI_API_KEY"}),
        ("kimi", {"KIMICC_AUTH_TOKEN", "MOONSHOT_API_KEY", "KIMI_API_KEY", "ANTHROPIC_AUTH_TOKEN"}),
        ("glm", set()),
        ("cursor", {"CURSOR_API_KEY"}),
    ],
)
def test_interactive_launcher_child_uses_dispatcher_credential_policy(
    tmp_path: Path, provider: str, kept: set[str]
) -> None:
    import json

    names = {
        "ANTHROPIC_API_KEY",
        "CLAUDE_API_KEY",
        "CODEX_API_KEY",
        "OPENAI_API_KEY",
        "CODEX_CC_AUTH_TOKEN",
        "KIMICC_AUTH_TOKEN",
        "MOONSHOT_API_KEY",
        "KIMI_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "CURSOR_API_KEY",
        "HF_TOKEN",
        "OTHER_AUTH_TOKEN",
        "OTHER_PASSWORD",
        "OTHER_PASSWD",
        "OTHER_SECRET",
        "other_token",
    }
    probe = tmp_path / "child.py"
    probe.write_text(
        "import os, json\n"
        + f"expected = {sorted(kept)!r}\n"
        + f"names = {sorted(names)!r}\n"
        + "assert sorted(name for name in names if name in os.environ) == expected\n"
        + "assert all(os.environ[name] == 'synthetic-launcher-credential-0123456789' for name in expected)\n"
        + "print(json.dumps({'credential_names': expected}))\n"
    )
    command = (
        f"source {shlex.quote(str(REPO / 'scripts/lib/launcher_core.sh'))}\n"
        f"LC_PROVIDER={shlex.quote(provider)} LC_MODE=interactive LC_ROOT={shlex.quote(str(REPO))}\n"
        f"LC_DURABLE_HELPER_ROOT={shlex.quote(str(Path(sys.executable).parents[2]))}\n"
        f"launcher_exec_command {shlex.quote(sys.executable)} {shlex.quote(str(probe))}\n"
    )
    env = {
        "PATH": os.defpath,
        "HOME": str(tmp_path),
        **dict.fromkeys(names, "synthetic-launcher-credential-0123456789"),
    }
    proc = subprocess.run(["bash", "-eu", "-c", command], env=env, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {"credential_names": sorted(kept)}
    assert "synthetic-launcher-credential" not in proc.stdout + proc.stderr


@pytest.mark.parametrize(
    "provider,keys",
    [
        ("gemini", {"GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY"}),
        ("claude", {"ANTHROPIC_API_KEY", "CLAUDE_API_KEY"}),
        ("codex", {"CODEX_API_KEY", "OPENAI_API_KEY"}),
        ("kimi", {"KIMICC_AUTH_TOKEN", "MOONSHOT_API_KEY", "KIMI_API_KEY", "ANTHROPIC_AUTH_TOKEN"}),
        ("cursor", {"CURSOR_API_KEY"}),
        ("acpx-cursor-shadow", {"CURSOR_API_KEY"}),
    ],
)
def test_existing_provider_allowlist_reaches_launcher_and_dispatcher(provider: str, keys: set[str]) -> None:
    all_keys = {
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_GENERATIVE_AI_API_KEY",
        "ANTHROPIC_API_KEY",
        "CLAUDE_API_KEY",
        "CODEX_API_KEY",
        "OPENAI_API_KEY",
        "KIMICC_AUTH_TOKEN",
        "MOONSHOT_API_KEY",
        "KIMI_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "CURSOR_API_KEY",
    }
    parent = dict.fromkeys(all_keys, SYNTHETIC_KEY)
    assert unneeded_env_var_names(parent, "dispatcher") == []
    downstream = without_unneeded_secrets(parent, provider)
    assert all(downstream[name] == SYNTHETIC_KEY for name in keys)
    dropped = set(unneeded_env_var_names(parent, provider))
    assert all_keys - dropped == set(downstream)
    assert all_keys - dropped == keys | (
        {"KIMICC_AUTH_TOKEN", "ANTHROPIC_AUTH_TOKEN"} if provider != "codex" else {"KIMICC_AUTH_TOKEN"}
    )


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


@pytest.mark.parametrize("harness", ["codex", "claude-code"])
def test_round2_codex_route_child_auth(tmp_path: Path, harness: str) -> None:
    child = tmp_path / "child.py"
    child.write_text(
        "import os\n"
        + f"assert ('ANTHROPIC_AUTH_TOKEN' in os.environ) == {harness == 'claude-code'!r}\n"
        + "assert os.environ['ANTHROPIC_BASE_URL'] == 'http://localhost:8317'\n"
        + "print('route-auth-ok')\n"
    )
    for name in ("codex", "claude"):
        binary = tmp_path / name
        binary.write_text(f"#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(child))}\n")
        binary.chmod(0o755)
    command = (
        f"source {shlex.quote(str(REPO / 'scripts/lib/launcher_core.sh'))}\n"
        f"source {shlex.quote(str(REPO / 'scripts/launchers/codex.sh'))}\n"
        f"LC_PROVIDER=codex LC_HARNESS={harness} LC_MODE=interactive LC_DRY_RUN=0\n"
        f"LC_ROOT={shlex.quote(str(REPO))} LC_SESSION_ROOT={shlex.quote(str(tmp_path))}\n"
        f"LC_DURABLE_HELPER_ROOT={shlex.quote(str(Path(sys.executable).parents[2]))}\n"
        "LC_MODEL=gpt-6.1-sol LC_EFFORT=high LC_FORWARD_ARGS=()\n"
        + (
            f'source {shlex.quote(str(REPO / "scripts/lib/codex_cc_route.sh"))}\ncodex_cc_configure_route "$LC_MODEL"\n'
            if harness == "claude-code"
            else ""
        )
        + "launcher_adapter_exec\n"
    )
    env = {
        "PATH": str(tmp_path) + os.pathsep + os.defpath,
        "HOME": str(tmp_path),
        "ANTHROPIC_AUTH_TOKEN": SYNTHETIC_KEY,
        "ANTHROPIC_BASE_URL": "http://localhost:8317",
        "CODEX_CC_BASE_URL": "http://localhost:8317",
        "CODEX_CC_AUTH_TOKEN": SYNTHETIC_KEY,
    }
    proc = subprocess.run(["bash", "-eu", "-c", command], env=env, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout == "route-auth-ok\n"


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
        env={name: os.environ[name] for name in ("PATH", "HOME", "TMPDIR") if name in os.environ},
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


@pytest.mark.parametrize(
    "provider,harness,provider_keys",
    [
        ("claude", "claude-code", {"ANTHROPIC_API_KEY", "CLAUDE_API_KEY"}),
        ("codex", "codex", {"CODEX_API_KEY", "OPENAI_API_KEY"}),
        ("codex", "claude-code", {"CODEX_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_AUTH_TOKEN"}),
        ("gemini", "agy", {"GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY"}),
        ("glm", "claude-code", {"ANTHROPIC_AUTH_TOKEN"}),
        ("grok", "grok", set()),
        ("cursor", "cursor", {"CURSOR_API_KEY"}),
    ],
)
def test_round3_real_launcher_dispatcher_child_parity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, provider: str, harness: str, provider_keys: set[str]
) -> None:
    import json
    from unittest.mock import patch

    import agent_runtime.agent_github_identity as identity
    from agent_runtime.env_sanitize import build_agent_env

    names = {
        "ANTHROPIC_API_KEY",
        "CLAUDE_API_KEY",
        "CODEX_API_KEY",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_GENERATIVE_AI_API_KEY",
        "CURSOR_API_KEY",
        "XAI_API_KEY",
        "ZAI_API_KEY",
        "OTHER_APIKEY",
        "ANTHROPIC_AUTH_TOKEN",
        "CODEX_CC_AUTH_TOKEN",
        "KIMICC_AUTH_TOKEN",
        "GLMCC_AUTH_TOKEN",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "HF_TOKEN",
        "NPM_TOKEN",
        "AWS_SECRET_ACCESS_KEY",
        "LU_AGENT_GITHUB_APP_PRIVATE_KEY",
        "OTHER_PASSWORD",
        "OTHER_SECRET",
        "GH_TOKEN",
        "GITHUB_TOKEN",
        "LU_AGENT_GITHUB_TOKEN",
    }
    parent = {
        "PATH": os.defpath,
        "HOME": str(tmp_path),
        "CLAUDE_CONFIG_DIR": str(tmp_path / ".claude"),
        **dict.fromkeys(names, SYNTHETIC_KEY),
    }
    parent["GH_TOKEN"] = "synthetic-parent-github-token-0123456789"
    parent["GITHUB_TOKEN"] = "synthetic-parent-github-token-9876543210"

    # Substitute only the external identity resolver. The real sanitizer and
    # launcher shell still decide which planted credentials reach the child.
    def resolver(**kwargs):
        return identity.GitHubIdentity(token=SYNTHETIC_KEY, source="test")

    monkeypatch.setattr(identity, "resolve_agent_github_identity", resolver)
    with patch.dict(os.environ, parent, clear=True):
        dispatcher = build_agent_env(provider=provider, harness=harness)
    expected = provider_keys | {"GH_TOKEN"}
    assert set(dispatcher) & names == expected

    bootstrap = tmp_path / "helper.py"
    bootstrap.write_text(
        "import runpy, sys\n"
        + f"sys.path[:0] = {[str(REPO), str(REPO / 'scripts')]!r}\n"
        + "import agent_runtime.agent_github_identity as identity\n"
        + f"identity.resolve_agent_github_identity = lambda **kwargs: identity.GitHubIdentity({SYNTHETIC_KEY!r}, 'test')\n"
        + "sys.argv = sys.argv[1:]\nrunpy.run_path(sys.argv[0], run_name='__main__')\n"
    )
    helper_root = tmp_path / "helper-root"
    interpreter = helper_root / ".venv/bin/python"
    interpreter.parent.mkdir(parents=True)
    interpreter.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(bootstrap))} "$@"\n')
    interpreter.chmod(0o755)
    child = tmp_path / "child.py"
    stored = tmp_path / ".claude" / "stored-login.json"
    stored.parent.mkdir()
    stored.write_text('{"authenticated": true}')
    child.write_text(
        "import json, os\nfrom pathlib import Path\n"
        + f"assert os.environ['HOME'] == {str(tmp_path)!r}\n"
        + "assert 'CLAUDE_CODE_OAUTH_TOKEN' not in os.environ\n"
        + "assert Path(os.environ['CLAUDE_CONFIG_DIR']) == Path(os.environ['HOME']) / '.claude'\n"
        + "assert json.loads((Path(os.environ['CLAUDE_CONFIG_DIR']) / 'stored-login.json').read_text())['authenticated']\n"
        + f"print(json.dumps({{name: os.environ[name] for name in {names!r} if name in os.environ}}))\n"
    )
    command = (
        f"source {shlex.quote(str(REPO / 'scripts/lib/launcher_core.sh'))}\n"
        f"LC_PROVIDER={provider} LC_HARNESS={harness} LC_MODE=interactive LC_DRIVER_LEASE_ENABLED=0\n"
        f"LC_ROOT={shlex.quote(str(REPO))} LC_DURABLE_HELPER_ROOT={shlex.quote(str(helper_root))}\n"
        f"launcher_exec_command {shlex.quote(sys.executable)} {shlex.quote(str(child))}\n"
    )
    proc = subprocess.run(["bash", "-eu", "-c", command], env=parent, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    launcher = json.loads(proc.stdout)
    assert launcher == {name: dispatcher[name] for name in names if name in dispatcher}
    assert set(launcher) == expected


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


@pytest.mark.parametrize("provider", ["claude", "codex", "gemini", "glm", "grok", "cursor"])
@pytest.mark.parametrize("source", ["GH_TOKEN", "GITHUB_TOKEN", "LU_AGENT_GITHUB_TOKEN"])
def test_round3_launcher_resolves_synthetic_github_identity(tmp_path: Path, provider: str, source: str) -> None:
    import json
    from unittest.mock import patch

    from agent_runtime.env_sanitize import build_agent_env

    parent = {"PATH": os.defpath, "HOME": str(tmp_path), source: SYNTHETIC_KEY}
    with patch.dict(os.environ, parent, clear=True):
        dispatcher = build_agent_env(provider=provider)
    child = tmp_path / "child.py"
    child.write_text(
        "import json, os\n"
        "print(json.dumps({name: os.environ[name] for name in ('GH_TOKEN', 'GITHUB_TOKEN', 'LU_AGENT_GITHUB_TOKEN') if name in os.environ}))\n"
    )
    command = (
        f"source {shlex.quote(str(REPO / 'scripts/lib/launcher_core.sh'))}\n"
        f"LC_PROVIDER={provider} LC_MODE=interactive LC_ROOT={shlex.quote(str(REPO))}\n"
        f"LC_DURABLE_HELPER_ROOT={shlex.quote(str(Path(sys.executable).parents[2]))}\n"
        f"launcher_exec_command {shlex.quote(sys.executable)} {shlex.quote(str(child))}\n"
    )
    proc = subprocess.run(["bash", "-eu", "-c", command], env=parent, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {"GH_TOKEN": dispatcher["GH_TOKEN"]} == {"GH_TOKEN": SYNTHETIC_KEY}


@pytest.mark.parametrize("counter", ["1", "synthetic-not-a-counter-0123456789"])
def test_round3_launcher_preserves_metadata_without_forwarding_worker_lease(tmp_path: Path, counter: str) -> None:
    import json
    from unittest.mock import patch

    from agent_runtime.env_sanitize import build_agent_env

    metadata = {
        "SESSION_STREAM_FENCING_TOKEN": counter,
        "LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS": "272000",
        "LEARN_UKRAINIAN_AUTO_COMPACT_CAPACITY_TOKENS": "272000",
        "LEARN_UKRAINIAN_COLD_START_BUDGET_TOKENS": "20000",
        "LEARN_UKRAINIAN_EXPECTED_MAIN_CONTEXT_WINDOW_TOKENS": "272000",
        "GIT_AUTHOR_NAME": "synthetic author",
        "GIT_AUTHOR_EMAIL": "synthetic@example.com",
    }
    parent = {"PATH": os.defpath, "HOME": str(tmp_path), **metadata}
    with patch.dict(os.environ, parent, clear=True):
        dispatcher = build_agent_env(provider="claude")
    assert "SESSION_STREAM_FENCING_TOKEN" not in dispatcher
    assert "LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS" not in dispatcher
    assert dispatcher["GIT_AUTHOR_NAME"] != metadata["GIT_AUTHOR_NAME"]
    child = tmp_path / "child.py"
    child.write_text(
        "import json, os\n"
        + f"print(json.dumps({{name: os.environ[name] for name in {set(metadata)!r} if name in os.environ}}))\n"
    )
    command = (
        f"source {shlex.quote(str(REPO / 'scripts/lib/launcher_core.sh'))}\n"
        f"LC_PROVIDER=claude LC_MODE=interactive LC_ROOT={shlex.quote(str(REPO))}\n"
        f"LC_DURABLE_HELPER_ROOT={shlex.quote(str(Path(sys.executable).parents[2]))}\n"
        f"launcher_exec_command {shlex.quote(sys.executable)} {shlex.quote(str(child))}\n"
    )
    proc = subprocess.run(["bash", "-eu", "-c", command], env=parent, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    expected = dict(metadata)
    if not counter.isdecimal():
        expected.pop("SESSION_STREAM_FENCING_TOKEN")
    assert json.loads(proc.stdout) == expected


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


def _round4_launcher_probe(
    tmp_path: Path,
    source: str,
    *,
    provider: str = "claude",
    harness: str = "claude-code",
    mode: str = "driver",
    environment: dict[str, str] | None = None,
    setup: str = "",
    bootstrap_code: str = "",
    forwarded: tuple[str, ...] = (),
    adapter: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run the real launcher and helper with only synthetic identity minting."""
    bootstrap = tmp_path / "bootstrap.py"
    bootstrap.write_text(
        "import runpy, sys\n"
        + f"sys.path[:0] = {[str(REPO), str(REPO / 'scripts')]!r}\n"
        + bootstrap_code
        + "sys.argv = sys.argv[1:]\nrunpy.run_path(sys.argv[0], run_name='__main__')\n"
    )
    helper_root = tmp_path / "helper-root"
    interpreter = helper_root / ".venv/bin/python"
    interpreter.parent.mkdir(parents=True)
    interpreter.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(bootstrap))} "$@"\n')
    interpreter.chmod(0o755)
    child = tmp_path / "child.py"
    child.write_text(source)
    command = (
        f"source {shlex.quote(str(REPO / 'scripts/lib/launcher_core.sh'))}\n"
        f"LC_PROVIDER={provider} LC_HARNESS={harness} LC_MODE={mode} LC_DRIVER_LEASE_ENABLED=0\n"
        f"LC_ROOT={shlex.quote(str(REPO))} LC_SESSION_ROOT={shlex.quote(str(REPO))}\n"
        f"LC_DURABLE_HELPER_ROOT={shlex.quote(str(helper_root))}\n" + setup
    )
    if adapter:
        # The real adapter builds argv, configures its real route and execs a
        # synthetic Claude binary. No model session or host config is used.
        binary = tmp_path / "bin/claude"
        binary.parent.mkdir()
        binary.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(child))} "$@"\n')
        binary.chmod(0o755)
        command += (
            f"source {shlex.quote(str(REPO / f'scripts/launchers/{provider}.sh'))}\n"
            "launcher_adapter_validate\nlauncher_adapter_preflight\nlauncher_adapter_exec\n"
        )
    else:
        command += "launcher_exec_command " + shlex.join((sys.executable, str(child), *forwarded)) + "\n"
    parent = {"PATH": os.defpath, "HOME": str(tmp_path), **(environment or {})}
    if adapter:
        parent["PATH"] = str(binary.parent) + os.pathsep + os.defpath
    return subprocess.run(["bash", "-eu", "-c", command], env=parent, capture_output=True, text=True, timeout=60)


@pytest.mark.parametrize("provider", ["glm", "kimi"])
def test_round4_real_claude_route_exports_reach_child(tmp_path: Path, provider: str) -> None:
    import json

    proc = _round4_launcher_probe(
        tmp_path,
        "import json, os\n"
        "assert os.environ['ANTHROPIC_AUTH_TOKEN'] == 'synthetic-route-auth-0123456789'\n"
        "assert os.environ['ANTHROPIC_BASE_URL'].startswith('https://')\n"
        "assert os.environ['CLAUDE_CODE_MAX_CONTEXT_TOKENS'].isascii()\n"
        "assert int(os.environ['CLAUDE_CODE_MAX_CONTEXT_TOKENS']) > 0\n"
        "assert 'OPENAI_API_KEY' not in os.environ\n"
        "assert 'ZAI_API_KEY' not in os.environ\n"
        "assert 'OTHER_PASSWORD' not in os.environ\n"
        "print(json.dumps(sorted(name for name in ('ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL', 'CLAUDE_CODE_MAX_CONTEXT_TOKENS') if name in os.environ)))\n",
        provider=provider,
        adapter=True,
        environment={
            "GLMCC_AUTH_TOKEN" if provider == "glm" else "KIMICC_AUTH_TOKEN": "synthetic-route-auth-0123456789",
            "OPENAI_API_KEY": SYNTHETIC_KEY,
            "OTHER_PASSWORD": SYNTHETIC_KEY,
            "GLMCC_ROUTE_PYTHON": sys.executable,
            "KIMICC_ROUTE_PYTHON": sys.executable,
        },
        setup=(
            f"LC_MODEL={'glm' if provider == 'glm' else 'k3'} LC_ENDPOINT=platform LC_ISOLATE_CONFIG=1 LC_DRY_RUN=0\n"
            "LC_RULES_CORE='' LC_EFFORT='' LC_FORWARD_ARGS=()\n"
        ),
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout.splitlines()[-1]) == [
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "CLAUDE_CODE_MAX_CONTEXT_TOKENS",
    ]


@pytest.mark.parametrize("key_source", ["inline", "file"])
@pytest.mark.parametrize("mode", ["driver", "interactive"])
def test_round4_driver_app_identity_and_worker_key_boundary(tmp_path: Path, key_source: str, mode: str) -> None:
    import json

    key_file = tmp_path / "app-key.txt"
    key_file.write_text("synthetic-app-signing-key")
    key_file.chmod(0o600)
    parent = {
        "LU_AGENT_GITHUB_APP_ID": "123",
        "LU_AGENT_GITHUB_APP_INSTALLATION_ID": "456",
        "LU_AGENT_GITHUB_APP_PRIVATE_KEY" if key_source == "inline" else "LU_AGENT_GITHUB_APP_PRIVATE_KEY_FILE": (
            "synthetic-app-signing-key" if key_source == "inline" else str(key_file)
        ),
        "OPENAI_API_KEY": SYNTHETIC_KEY,
        "OTHER_PASSWORD": SYNTHETIC_KEY,
        "OTHER_AUTH_TOKEN": SYNTHETIC_KEY,
        "HF_TOKEN": SYNTHETIC_KEY,
    }
    proc = _round4_launcher_probe(
        tmp_path,
        "import json, os, sys\n"
        + f"sys.path[:0] = {[str(REPO), str(REPO / 'scripts')]!r}\n"
        + "import agent_runtime.agent_github_identity as identity\n"
        "identity.mint_installation_token = lambda **kwargs: 'synthetic-minted-token'\n"
        "from agent_runtime.env_sanitize import build_agent_env\n"
        "assert all(name not in os.environ for name in ('OPENAI_API_KEY', 'OTHER_PASSWORD', 'OTHER_AUTH_TOKEN', 'HF_TOKEN'))\n"
        + (
            "assert identity.resolve_agent_github_identity().source == 'app'\n"
            "worker = build_agent_env(provider='claude')\n"
            if mode == "driver"
            else "worker = dict(os.environ)\n"
        )
        + "assert 'LU_AGENT_GITHUB_APP_PRIVATE_KEY' not in worker\n"
        "assert 'LU_AGENT_GITHUB_APP_PRIVATE_KEY_FILE' not in worker\n"
        "try:\n    identity.resolve_agent_github_identity(environment=worker)\n"
        "except identity.GitHubIdentityError as exc:\n    assert 'incomplete' in str(exc)\n"
        "else:\n    raise AssertionError('worker could mint an App token')\n"
        "print(json.dumps({'driver_can_resolve': " + str(mode == "driver") + ", 'worker_has_key': False}))\n",
        mode=mode,
        environment=parent,
        bootstrap_code=(
            "import agent_runtime.agent_github_identity as identity\n"
            "identity.mint_installation_token = lambda **kwargs: 'synthetic-minted-token'\n"
        ),
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {"driver_can_resolve": mode == "driver", "worker_has_key": False}


@pytest.mark.parametrize("forwarded", [("--", "literal"), ("first", "--", "--provider", "glm", "--harness=other")])
def test_round4_launcher_forwards_literal_argument_separator(tmp_path: Path, forwarded: tuple[str, ...]) -> None:
    import json

    proc = _round4_launcher_probe(tmp_path, "import json, sys\nprint(json.dumps(sys.argv[1:]))\n", forwarded=forwarded)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == list(forwarded)


def test_round4_exec_restores_signal_defaults(tmp_path: Path) -> None:
    import signal

    if not Path("/proc/self/status").is_file():
        pytest.skip("Linux signal mask proof requires procfs")
    proc = _round4_launcher_probe(tmp_path, "", setup="launcher_exec_command cat /proc/self/status\n")
    assert proc.returncode == 0, proc.stderr
    ignored = int(next(line.split()[1] for line in proc.stdout.splitlines() if line.startswith("SigIgn:")), 16)
    for number in (signal.SIGPIPE, signal.SIGXFSZ):
        assert not ignored & (1 << (number - 1))


def test_round4_check_helper_refuses_broken_identity_import(tmp_path: Path) -> None:
    marker = tmp_path / "provider-started"
    proc = _round4_launcher_probe(
        tmp_path,
        f"from pathlib import Path\nPath({str(marker)!r}).touch()\n",
        bootstrap_code=(
            "import importlib.abc\n"
            "class BrokenIdentity(importlib.abc.MetaPathFinder):\n"
            "    def find_spec(self, fullname, path, target=None):\n"
            "        if fullname.endswith('.agent_github_identity'):\n"
            "            raise ModuleNotFoundError('synthetic-sensitive-import-diagnostic')\n"
            "sys.meta_path.insert(0, BrokenIdentity())\n"
        ),
        setup=(
            "launcher_drop_unneeded_secrets || exit 1\n"
            # A lease claim may only happen after this preflight succeeds.
            f"touch {shlex.quote(str(marker))}\n"
        ),
    )
    assert proc.returncode == 1
    assert not marker.exists()
    assert "could not drop unneeded API keys" in proc.stderr
    assert "synthetic-sensitive-import-diagnostic" not in proc.stderr


def test_round4_exec_exception_describes_model_session_boundary() -> None:
    import yaml

    registry = yaml.safe_load((REPO / "tests/headless_claude_spawn_exceptions.yaml").read_text())
    entries = registry["exceptions"]
    entry = next(
        item
        for item in entries
        if item["module"] == "scripts/agent_runtime/env_sanitize.py" and item["program"] == "args.command[0]"
    )
    assert "operator-forwarded" in entry["reason"]
    assert "no worker-controlled value" in entry["reason"]
    assert "runs no model prompt" not in entry["reason"]


@pytest.mark.parametrize(
    "provider,harness,kept",
    [
        ("claude", "claude-code", {"ANTHROPIC_API_KEY", "CLAUDE_API_KEY"}),
        ("codex", "codex", {"CODEX_API_KEY", "OPENAI_API_KEY"}),
        ("codex", "claude-code", {"CODEX_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_AUTH_TOKEN"}),
        ("gemini", "agy", {"GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY"}),
        ("glm", "claude-code", {"ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_MAX_CONTEXT_TOKENS", "ANTHROPIC_BASE_URL"}),
        ("grok", "grok", set()),
        ("cursor", "cursor", {"CURSOR_API_KEY"}),
        ("kimi", "kimi-code", {"KIMICC_AUTH_TOKEN", "MOONSHOT_API_KEY", "KIMI_API_KEY", "ANTHROPIC_AUTH_TOKEN"}),
        (
            "kimi",
            "claude-code",
            {
                "KIMICC_AUTH_TOKEN",
                "MOONSHOT_API_KEY",
                "KIMI_API_KEY",
                "ANTHROPIC_AUTH_TOKEN",
                "CLAUDE_CODE_MAX_CONTEXT_TOKENS",
                "ANTHROPIC_BASE_URL",
            },
        ),
    ],
)
@pytest.mark.parametrize("mode", ["driver", "interactive"], ids=["driver", "worker"])
def test_round4_real_launcher_kept_dropped_table(
    tmp_path: Path, provider: str, harness: str, kept: set[str], mode: str, record_property
) -> None:
    import json

    app_keys = {
        "LU_AGENT_GITHUB_APP_ID",
        "LU_AGENT_GITHUB_APP_INSTALLATION_ID",
        "LU_AGENT_GITHUB_APP_PRIVATE_KEY",
        "LU_AGENT_GITHUB_APP_PRIVATE_KEY_FILE",
    }
    names = app_keys | {
        "ANTHROPIC_API_KEY",
        "CLAUDE_API_KEY",
        "CODEX_API_KEY",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_GENERATIVE_AI_API_KEY",
        "CURSOR_API_KEY",
        "KIMICC_AUTH_TOKEN",
        "MOONSHOT_API_KEY",
        "KIMI_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "CLAUDE_CODE_MAX_CONTEXT_TOKENS",
        "ANTHROPIC_BASE_URL",
        "XAI_API_KEY",
        "ZAI_API_KEY",
        "GLMCC_AUTH_TOKEN",
        "CODEX_CC_AUTH_TOKEN",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "HF_TOKEN",
        "NPM_TOKEN",
        "AWS_SECRET_ACCESS_KEY",
        "OTHER_PASSWORD",
        "OTHER_SECRET",
        "OTHER_AUTH_TOKEN",
        "OTHER_APIKEY",
        "GH_TOKEN",
        "GITHUB_TOKEN",
        "LU_AGENT_GITHUB_TOKEN",
    }
    parent = dict.fromkeys(names, SYNTHETIC_KEY)
    parent.update(
        {
            "LU_AGENT_GITHUB_APP_ID": "123",
            "LU_AGENT_GITHUB_APP_INSTALLATION_ID": "456",
            "CLAUDE_CODE_MAX_CONTEXT_TOKENS": "200000",
            "ANTHROPIC_BASE_URL": "https://route.invalid",
        }
    )
    # Use the same source environment for both policies. Only the identity's
    # external resolution is substituted, never either credential filter.
    proc = _round4_launcher_probe(
        tmp_path,
        "import json, os, sys\n"
        + f"sys.path[:0] = {[str(REPO), str(REPO / 'scripts')]!r}\n"
        + "import agent_runtime.agent_github_identity as identity\n"
        "identity.resolve_agent_github_identity = lambda **kwargs: identity.GitHubIdentity('synthetic-resolved-token', 'test')\n"
        "from agent_runtime.env_sanitize import build_agent_env\n"
        + f"names = {sorted(names)!r}\n"
        + (
            f"child = build_agent_env(provider={provider!r}, harness={harness!r})\n"
            if mode == "interactive"
            else "child = os.environ\n"
        )
        + "print(json.dumps({'kept': sorted(set(child) & set(names)), 'dropped': sorted(set(names) - set(child))}))\n",
        provider=provider,
        harness=harness,
        mode=mode,
        environment=parent,
        bootstrap_code=(
            "import agent_runtime.agent_github_identity as identity\n"
            "identity.resolve_agent_github_identity = lambda **kwargs: identity.GitHubIdentity('synthetic-resolved-token', 'test')\n"
        ),
    )
    assert proc.returncode == 0, proc.stderr
    observed = json.loads(proc.stdout)
    expected = kept | (set() if provider == "kimi" else {"GH_TOKEN"})
    if mode == "driver":
        expected |= app_keys
        expected |= {"GH_TOKEN", "GITHUB_TOKEN", "LU_AGENT_GITHUB_TOKEN"}
        # This is ordinary launcher context even for routes that do not use it.
        expected.add("ANTHROPIC_BASE_URL")
    else:
        expected |= {"LU_AGENT_GITHUB_APP_ID", "LU_AGENT_GITHUB_APP_INSTALLATION_ID"}
    assert set(observed["kept"]) == expected
    assert set(observed["dropped"]) == names - expected
    record_property(
        "credential_table", json.dumps({"provider": provider, "harness": harness, "mode": mode, **observed})
    )


@pytest.mark.parametrize("provider", ["claude", "codex", "gemini", "glm", "grok", "cursor", "kimi"])
@pytest.mark.parametrize("has_token", [True, False], ids=["parent-token", "no-parent-token"])
def test_round5_driver_github_passthrough(tmp_path: Path, provider: str, has_token: bool) -> None:
    parent = {
        "GITHUB_TOKEN": "synthetic-alternate-github-0123456789",
        "GH_ENTERPRISE_TOKEN": "synthetic-enterprise-github-0123456789",
        "GITHUB_ENTERPRISE_TOKEN": "synthetic-alternate-enterprise-0123456789",
        "LU_AGENT_GITHUB_TOKEN": "synthetic-application-token-0123456789",
        "LU_AGENT_GITHUB_APP_ID": "123",
        "LU_AGENT_GITHUB_APP_INSTALLATION_ID": "456",
        "LU_AGENT_GITHUB_APP_PRIVATE_KEY": "synthetic-signing-key-0123456789",
        "LU_AGENT_GITHUB_APP_PRIVATE_KEY_FILE": str(tmp_path / "synthetic-key-file"),
    }
    if has_token:
        parent["GH_TOKEN"] = "synthetic-parent-token-0123456789\nbytes-'\\"
    proc = _round4_launcher_probe(
        tmp_path,
        "import os\n"
        + f"expected = {parent!r}\n"
        + "assert all(os.environ[name].encode() == value.encode() for name, value in expected.items())\n"
        + f"assert ('GH_TOKEN' in os.environ) == {has_token!r}\n"
        + "assert 'LU_AGENT_GITHUB_IDENTITY_SOURCE' not in os.environ\nprint('identity-unchanged')\n",
        provider=provider,
        environment=parent,
        bootstrap_code=(
            "import agent_runtime.agent_github_identity as identity\n"
            "def forbidden(**kwargs):\n    raise AssertionError('driver attempted identity resolution or mint')\n"
            "identity.resolve_agent_github_identity = forbidden\nidentity.mint_installation_token = forbidden\n"
        ),
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == "identity-unchanged\n"


@pytest.mark.parametrize("name", ["PATH", "HOME", "PWD"])
@pytest.mark.parametrize("mode", ["driver", "interactive"])
def test_round5_launcher_preserves_process_paths(tmp_path: Path, name: str, mode: str) -> None:
    value = str(tmp_path / "task-ghp_syntheticpath")
    Path(value).mkdir()
    proc = _round4_launcher_probe(
        tmp_path,
        "import os\n" + f"assert os.environ[{name!r}] == {value!r}\nprint('path-unchanged')\n",
        # Shells maintain PWD themselves; use an actual directory for that case.
        setup=f"cd {shlex.quote(value)}\n" if name == "PWD" else f"export {name}={shlex.quote(value)}\n",
        mode=mode,
        bootstrap_code=(
            "import agent_runtime.agent_github_identity as identity\n"
            "identity.resolve_agent_github_identity = lambda **kwargs: None\n"
        ),
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == "path-unchanged\n"


@pytest.mark.parametrize("name", ["PATH", "HOME", "PWD"])
def test_round5_dispatcher_keeps_path_value_filter(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    from agent_runtime import agent_github_identity as identity
    from agent_runtime.env_sanitize import build_agent_env

    monkeypatch.setattr(identity, "resolve_agent_github_identity", lambda **kwargs: None)
    assert name not in build_agent_env(provider="claude", overrides={name: "synthetic/task-ghp_path"})


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
