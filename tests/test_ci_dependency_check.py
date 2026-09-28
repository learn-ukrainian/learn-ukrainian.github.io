"""Guard the CI install's cache fallback and fail-closed dependency check."""

from pathlib import Path
from subprocess import CompletedProcess

import yaml

from scripts.audit import check_ci_dependencies
from scripts.audit.check_ci_dependencies import unexpected_diagnostics

_CI = Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml"


def test_ci_install_blocks_use_the_same_cache_and_integrity_sequence() -> None:
    workflow = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    jobs = workflow["jobs"]
    scripts = [
        next(step["run"] for step in jobs[job]["steps"] if step.get("name") == name)
        for job, name in (
            ("fast-checks", "Install preflight Python deps"),
            ("pytest", "Install Python deps"),
            ("needs-artifact-audit", "Install Python deps"),
        )
    ]
    commands = [
        [line.strip() for line in script.splitlines() if line.strip() and not line.strip().startswith("#")]
        for script in scripts
    ]
    assert commands[0] == commands[1] == commands[2]
    script = scripts[0]
    assert script.index("uv pip install --offline") < script.index(
        "uv pip install --python"
    ) < script.index("scripts/audit/check_ci_dependencies.py")
    assert script.index("scripts/audit/check_ci_dependencies.py") < script.index(
        "build_assets.py"
    )


def test_ci_retry_settings_cover_uv_and_pip() -> None:
    workflow = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    assert workflow["env"] | {
        "UV_HTTP_RETRIES": "6",
        "UV_HTTP_TIMEOUT": "60",
        "PIP_RETRIES": "6",
        "PIP_TIMEOUT": "60",
    } == workflow["env"]


def test_only_exact_existing_conflict_is_allowed() -> None:
    known = (
        "marker-pdf 1.10.2 has requirement Pillow<11.0.0,>=10.1.0, "
        "but you have pillow 12.3.0."
    )
    skew = (
        "pydantic 2.13.5 has requirement pydantic-core==2.46.5, "
        "but you have pydantic-core 2.46.4."
    )
    assert unexpected_diagnostics(known) == []
    assert unexpected_diagnostics(known + "\n" + skew) == [skew]
    changed_known_pair = known.replace("pillow 12.3.0", "pillow 12.4.0")
    assert unexpected_diagnostics(changed_known_pair) == [changed_known_pair]
    assert unexpected_diagnostics("unrecognized pip diagnostic") == [
        "unrecognized pip diagnostic"
    ]


def test_dependency_check_fails_on_pydantic_skew(monkeypatch, capsys) -> None:
    skew = (
        "pydantic 2.13.5 has requirement pydantic-core==2.46.5, "
        "but you have pydantic-core 2.46.4."
    )
    monkeypatch.setattr(
        check_ci_dependencies.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcess(args, 1, skew, ""),
    )
    assert check_ci_dependencies.main() == 1
    assert skew in capsys.readouterr().err


def test_dependency_check_fails_on_empty_pip_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        check_ci_dependencies.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcess(args, 1, "", ""),
    )
    assert check_ci_dependencies.main() == 1
