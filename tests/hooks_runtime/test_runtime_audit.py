"""Runtime process-start audit for deployed hook entry points (#9807).

The child interpreter installs a PEP 578 audit hook before the entry executes.
A shell syntax check, a git or gh argv outside the reviewed templates, or a
hook-controlled configuration, pager, editor, askpass, or browser value fails
the run. Templates and launch explanations are fixtures, not exemptions.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from subprocess import CompletedProcess

import pytest

from scripts.common.git_context import GIT_REDIRECT_ENV_KEYS
from scripts.common.repo_root import project_interpreter
from scripts.publish.merge_guard import _checks_json_unsupported, _parse_status_rollup_rows
from tests.hooks_runtime.adapter import EntryReceipt, run_entry
from tests.hooks_runtime.conftest import REPORT
from tests.hooks_runtime.inventory import (
    CLASSIFICATION,
    COMMAND_PROCESSING,
    CoverageRow,
    command_processing_paths,
    denominator_text,
    excluded_surfaces,
    hook_root_files,
    unclassified,
)
from tests.hooks_runtime.policy import (
    REDIRECT_KEYS,
    ObservedStart,
    allowed_template,
    attempted_start,
    classify_start,
    identify_template,
    is_command_variable,
    is_redirect_key,
    load_explanations,
    load_template_records,
    load_templates,
    matches_template,
    template_ids,
)
from tests.hooks_runtime.probes.cases import DESCENDANT_ARGV
from tests.hooks_runtime.standin import canned_for, repo_root
from tests.test_guard_benign_corpus import _literal_corpus
from tests.test_hook_single_parser import REPO_ROOT

PROBE = Path(__file__).resolve().parent / "probes" / "cases.py"
_COMMAND_VARIABLES = (
    "BROWSER",
    "EDITOR",
    "GH_BROWSER",
    "GH_EDITOR",
    "GH_PAGER",
    "GIT_ASKPASS",
    "GIT_CONFIG_COUNT",
    "GIT_EDITOR",
    "GIT_EXTERNAL_DIFF",
    "GIT_PAGER",
    "GIT_SEQUENCE_EDITOR",
    "GIT_SSH",
    "GIT_SSH_COMMAND",
    "PAGER",
    "SSH_ASKPASS",
    "SSH_ASKPASS_REQUIRE",
    "VISUAL",
)


def _work(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    path.mkdir()
    return path


def _run(tmp_path: Path, case: str, **kwargs) -> EntryReceipt:
    extra = {"HOOK_RUNTIME_CASE": case}
    extra.update(kwargs.pop("extra_env", {}))
    name = kwargs.pop("name", case)
    return run_entry(
        PROBE,
        [case],
        cwd=_work(tmp_path, name),
        timeout=kwargs.pop("timeout", 20),
        extra_env=extra,
        allow_argv=kwargs.pop("allow_argv", None),
    )


def _text(receipt: EntryReceipt, cwd: Path | None = None) -> str:
    rendered = "\n".join(receipt.violations)
    if cwd is not None:
        rendered = rendered.replace(str(cwd), "<cwd>")
    return rendered


def _assert_blocked(receipt: EntryReceipt, *needles: str, cwd: Path | None = None) -> None:
    assert receipt.canary, receipt.driver_error or "missing canary"
    assert not receipt.timed_out
    assert not receipt.driver_error, receipt.driver_error
    assert not receipt.pair_errors, receipt.pair_errors
    rendered = _text(receipt, cwd)
    for needle in needles:
        assert needle in rendered, rendered
    assert not receipt.passed


def test_hook_roots_are_classified_once() -> None:
    on_disk = hook_root_files()
    assert unclassified() == ()
    assert set(on_disk) == set(CLASSIFICATION)
    assert len(on_disk) == len(CLASSIFICATION)
    driven = command_processing_paths()
    assert len(driven) == 8
    assert all(CLASSIFICATION[path] == COMMAND_PROCESSING for path in driven)


def test_templates_and_explanations_are_fixtures_not_exemptions(monkeypatch: pytest.MonkeyPatch) -> None:
    templates = load_templates()
    assert [name for name, _parts in templates] == [
        "git",
        "git",
        "git",
        "git",
        "git",
        "gh",
        "gh",
        "gh",
        "gh",
        "gh",
        "git",
        "gh",
        "gh",
        "git",
        "python",
    ]
    explanations = load_explanations()
    assert len(explanations) == 50
    assert all(item.get("explanation") for item in explanations)

    def boom() -> tuple[dict[str, str], ...]:
        raise AssertionError("launch explanations were consulted")

    monkeypatch.setattr("tests.hooks_runtime.policy.load_explanations", boom)
    start = ObservedStart(
        event="subprocess.Popen",
        pid=1,
        parent_pid=1,
        pair_index=0,
        executable="git",
        argv=("git", "-C", "<cwd>", "status"),
        explicit_env=None,
        inherited_dangerous={},
    )
    assert "unclassified-argv" in classify_start(start)
    assert not matches_template(("gh", "api", "user"))
    assert matches_template(("gh", "api", "repos/owner/repo/branches/main/protection"))
    assert not matches_template(("gh", "api", "--paginate"))
    assert not matches_template(("git", "-c", "core.pager=less", "rev-parse", "--git-dir"))
    assert not matches_template(("git", "-cname=value", "status"))
    assert not matches_template(("git", "--config-env", "foo=BAR", "status"))
    for name in _COMMAND_VARIABLES:
        assert is_command_variable(name), name
    assert not is_command_variable("NO_COLOR")
    assert not is_command_variable("CLICOLOR")


def test_second_level_helper_is_rejected(tmp_path: Path) -> None:
    receipt = _run(tmp_path, "second_level")
    _assert_blocked(receipt, "unclassified-argv", "config-injection:", "alias.x=!bash -n bad.sh")


def test_runner_passed_as_a_value_is_rejected(tmp_path: Path) -> None:
    receipt = _run(tmp_path, "value_runner")
    _assert_blocked(receipt, "syntax-check:bash -n")


def test_explicit_pager_is_rejected(tmp_path: Path) -> None:
    receipt = _run(tmp_path, "explicit_pager")
    _assert_blocked(receipt, "env-injection:GH_PAGER")


def test_inherited_pager_is_rejected(tmp_path: Path) -> None:
    receipt = _run(tmp_path, "inherited_pager", extra_env={"GH_FORCE_TTY": "1", "PAGER": "cat"})
    _assert_blocked(receipt, "env-injection:PAGER")
    assert "GH_FORCE_TTY" not in _text(receipt)


def test_launch_replacement_does_not_inherit_a_template(tmp_path: Path) -> None:
    keyword = _run(tmp_path, "launch_keyword")
    _assert_blocked(keyword, "launch-replacement")
    assert "unclassified-argv" not in _text(keyword)
    positional = _run(tmp_path, "launch_positional")
    _assert_blocked(positional, "launch-replacement", "unclassified-argv")


@pytest.mark.parametrize(
    ("case", "detail"),
    [
        ("asyncio_exec", "syntax-check:bash -n"),
        ("bytes_argv", "syntax-check:bash -xn"),
        ("os_system", "syntax-check:bash -n"),
        ("posix_spawn", "syntax-check:bash -n"),
        ("os_exec", "syntax-check:bash --noexec"),
    ],
)
def test_process_channels_reject_syntax_checks(tmp_path: Path, case: str, detail: str) -> None:
    _assert_blocked(_run(tmp_path, case), detail)


def test_overlapping_starts_are_both_recorded(tmp_path: Path) -> None:
    receipt = _run(tmp_path, "concurrent_starts", extra_env={"HOOK_RUNTIME_HOLD_HOOK": "1"})
    assert receipt.canary and not receipt.pair_errors, receipt.driver_error or receipt.pair_errors
    recorded = {event.argv for event in receipt.events}
    assert ("__concurrent_a__", "intercept") in recorded
    assert ("__concurrent_b__", "intercept") in recorded


def test_swallowed_exception_still_records_the_violation(tmp_path: Path) -> None:
    receipt = _run(tmp_path, "swallow")
    _assert_blocked(receipt, "syntax-check:bash -n")


def test_command_variables_and_config_forms_are_rejected(tmp_path: Path) -> None:
    env_receipt = _run(tmp_path, "command_env")
    rendered = _text(env_receipt)
    _assert_blocked(env_receipt, "env-injection:")
    for name in _COMMAND_VARIABLES:
        assert name in rendered, rendered
    assert "NO_COLOR" not in rendered
    assert "CLICOLOR" not in rendered
    shapes = _run(tmp_path, "config_shapes")
    _assert_blocked(shapes, "config-injection:-c", "config-injection:-cname=value", "config-injection:--config-env")
    assert "gh api --paginate" in _text(shapes)


def test_fork_child_exec_is_collected(tmp_path: Path) -> None:
    receipt = _run(tmp_path, "fork_child")
    _assert_blocked(receipt, "unknown-program:echo")
    collected = [
        event
        for event in receipt.events
        if event.event == "os.exec" and event.child_of_fork and event.argv[:1] == ("/bin/echo",)
    ]
    assert collected


def test_descendant_beyond_the_shell_is_unobserved(tmp_path: Path) -> None:
    work = _work(tmp_path, "descendant")
    receipt = run_entry(
        PROBE,
        ["descendant"],
        cwd=work,
        timeout=20,
        extra_env={"HOOK_RUNTIME_CASE": "descendant"},
        allow_argv=DESCENDANT_ARGV,
    )
    _assert_blocked(receipt, "shell-mediated:sh -c")
    assert (work / "descendant-marker").read_text(encoding="utf-8").strip() == "UNOBSERVED_CHILD"
    assert any(event.argv == DESCENDANT_ARGV for event in receipt.events)
    assert not any(event.argv and event.argv[0].endswith("echo") for event in receipt.events)


def test_missing_canary_missing_receipt_crash_and_timeout_fail(tmp_path: Path) -> None:
    quiet = _run(tmp_path, "noop", name="skip-canary", extra_env={"HOOK_RUNTIME_SKIP_CANARY": "1"})
    assert quiet.driver_error == "missing-canary"
    assert not quiet.passed
    omitted = _run(tmp_path, "noop", name="omit-summary", extra_env={"HOOK_RUNTIME_OMIT_SUMMARY": "1"})
    assert omitted.driver_error == "missing-receipt"
    assert omitted.canary
    assert not omitted.passed
    crashed = _run(tmp_path, "crash")
    assert crashed.pair_errors and "RuntimeError" in crashed.pair_errors[0]
    assert crashed.canary and not crashed.passed
    timed = _run(tmp_path, "sleeper", timeout=1)
    assert timed.timed_out and timed.driver_error == "timeout"
    assert not timed.passed


def _redact(text: str, cwd: Path) -> str:
    redacted = text.replace(str(cwd), "<cwd>")
    tmp = os.environ.get("TMPDIR", "").rstrip("/")
    if tmp:
        redacted = redacted.replace(tmp, "<tmpdir>")
    return redacted


def _shapes(receipt: EntryReceipt, cwd: Path) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter(_redact(item, cwd) for item in receipt.violations)
    return counter.most_common(12)


_VIEW_FIELDS = "isDraft,baseRefName,body,headRefOid,number,url"
_CHECK_FIELDS = "name,bucket,state"
_VIEW_REORDERED = "url,number,headRefOid,body,baseRefName,isDraft"


_FROZEN_TEMPLATE_IDS = (
    "git-rev-parse-git-common-dir",
    "git-rev-parse-git-dir",
    "git-rev-parse-common-dir-absolute",
    "git-rev-parse-toplevel-absolute",
    "git-symbolic-ref-head",
    "gh-api-branch-protection",
    "gh-pr-checks",
    "gh-pr-view",
    "gh-pr-view-repo",
    "gh-pr-checks-repo",
    "git-c-rev-parse-common-dir",
    "gh-pr-view-rollup",
    "gh-pr-view-repo-rollup",
    "git-c-rev-parse-toplevel",
    "python-check-core-bare",
)


def test_every_template_cites_the_hook_line_it_serves() -> None:
    records = load_template_records()
    assert template_ids() == _FROZEN_TEMPLATE_IDS
    assert len(records) == 15
    for record in records:
        assert record.serves
        for citation in record.serves:
            line = (REPO_ROOT / citation.file).read_text(encoding="utf-8").splitlines()[citation.line - 1]
            assert citation.text in line, citation


def test_pr_view_template_rejects_an_option_operand_and_an_extra_flag() -> None:
    assert matches_template(("gh", "pr", "view", "5", "--json", _VIEW_FIELDS))
    assert matches_template(("gh", "pr", "view", "...", "--json", _VIEW_FIELDS))
    assert matches_template(("gh", "pr", "view", "https://github.com/other/repo/pull/9", "--json", _VIEW_FIELDS))
    assert matches_template(("gh", "pr", "view", "feature/branch", "--json", _VIEW_FIELDS))
    assert matches_template(("gh", "pr", "view", "5", "--json", _VIEW_REORDERED))
    assert not matches_template(("gh", "pr", "view", "--admin", "--json", _VIEW_FIELDS))
    assert not matches_template(("gh", "pr", "view", "-5", "--json", _VIEW_FIELDS))
    assert not matches_template(("gh", "pr", "view", "5", "--json", _VIEW_FIELDS, "--paginate"))
    assert not matches_template(("gh", "pr", "view", "5", "--json", "isDraft"))
    assert not matches_template(("gh", "pr", "view", "https://example.com/other/repo/pull/9", "--json", _VIEW_FIELDS))


def test_pr_view_repo_template_rejects_an_option_operand_and_an_extra_flag() -> None:
    argv = ("gh", "pr", "view", "9", "--repo", "owner/repo", "--json", _VIEW_FIELDS)
    assert matches_template(argv)
    assert matches_template(("gh", "pr", "view", "689", "--repo", "cli/cli", "--json", _VIEW_FIELDS))
    assert not matches_template(("gh", "pr", "view", "--admin", "--repo", "owner/repo", "--json", _VIEW_FIELDS))
    assert not matches_template(("gh", "pr", "view", "9", "--repo", "-owner/repo", "--json", _VIEW_FIELDS))
    assert not matches_template(("gh", "pr", "view", "9", "--repo", "owner/repo", "--json", _VIEW_FIELDS, "--paginate"))
    assert not matches_template(("gh", "pr", "view", "9", "--repo", "host/owner/repo", "--json", _VIEW_FIELDS))


def test_pr_checks_repo_template_rejects_an_option_operand_and_an_extra_flag() -> None:
    argv = ("gh", "pr", "checks", "9", "--repo", "owner/repo", "--json", _CHECK_FIELDS)
    assert matches_template(argv)
    assert matches_template(("gh", "pr", "checks", "9", "--repo", "owner/repo", "--json", "state,name,bucket"))
    assert not matches_template(("gh", "pr", "checks", "--watch", "--repo", "owner/repo", "--json", _CHECK_FIELDS))
    assert not matches_template(("gh", "pr", "checks", "9", "--repo", "owner/-repo", "--json", _CHECK_FIELDS))
    assert not matches_template((*argv, "--watch"))
    assert not matches_template(("gh", "pr", "checks", "9", "--repo", "owner/repo", "--json", "name,bucket"))


def test_git_dash_c_rev_parse_template_rejects_an_option_operand_and_an_extra_flag(tmp_path: Path) -> None:
    flags = ("rev-parse", "--path-format=absolute", "--git-common-dir")
    assert matches_template(("git", "-C", str(tmp_path), *flags))
    missing = tmp_path / "curriculum"
    assert not missing.exists()
    assert matches_template(("git", "-C", str(missing), *flags))
    existing_file = tmp_path / "not-a-directory"
    existing_file.write_text("x", encoding="utf-8")
    assert not matches_template(("git", "-C", str(existing_file), *flags))
    assert not matches_template(("git", "-C", "relative-dir", *flags))
    assert not matches_template(("git", "-C", "--git-dir", *flags))
    assert not matches_template(("git", "-C", str(tmp_path), "--no-pager", *flags))
    assert not matches_template(("git", "-C", str(tmp_path), *flags, "--verify"))


def test_typed_slots_reject_shell_payloads_and_open_endpoints() -> None:
    assert matches_template(("gh", "api", "repos/owner/repo/branches/feature/name/protection"))
    assert not matches_template(("gh", "api", "repos/o/r/pulls/1/merge"))
    assert not matches_template(("gh", "api", "repos/o/r/branches/../protection"))
    assert not matches_template(("gh", "api", "repos/owner/repo/branches/main/protection?admin=1"))
    assert not matches_template(("gh", "pr", "checks", "x;bash -n y", "--json", _CHECK_FIELDS))
    assert matches_template(("gh", "pr", "checks", "feat/!bash", "--json", _CHECK_FIELDS))


def test_python_template_is_bound_to_the_healer_argv() -> None:
    root = REPO_ROOT
    argv = (
        str(project_interpreter(root)),
        str(root / "scripts" / "audit" / "check_core_bare.py"),
        "--repo",
        str(root),
        "--fix",
        "-q",
    )
    assert identify_template(argv) == "python-check-core-bare"
    assert not matches_template((*argv, "--extra"))
    assert not matches_template((argv[0], "-c", "print(1)"))
    assert not matches_template((argv[0], argv[1], "--repo", str(root), "--fix"))


def test_redirect_inventory_includes_git_common_dir() -> None:
    assert "GIT_COMMON_DIR" in GIT_REDIRECT_ENV_KEYS
    assert set(GIT_REDIRECT_ENV_KEYS) <= REDIRECT_KEYS
    for key in ("GIT_COMMON_DIR", "GIT_EXEC_PATH", "GH_CONFIG_DIR", "HOME", "PATH", "XDG_CONFIG_HOME"):
        assert is_redirect_key(key), key


def test_standin_fixtures_drive_the_checks_fallback_and_the_protection_read() -> None:
    unsupported = canned_for(
        "gh-pr-checks-repo",
        ("gh", "pr", "checks", "5", "--repo", "owner/repo", "--json", _CHECK_FIELDS),
    )
    proc = CompletedProcess([], unsupported.returncode, unsupported.stdout, unsupported.stderr)
    assert _checks_json_unsupported(proc)
    rollup = json.loads(canned_for("gh-pr-view-rollup", ()).stdout)
    failing, pending = _parse_status_rollup_rows(rollup["statusCheckRollup"])
    assert failing == [] and pending == []
    protection = json.loads(canned_for("gh-api-branch-protection", ()).stdout)
    assert protection["required_status_checks"]["contexts"] == ["ci"]


@pytest.mark.parametrize(
    ("case", "needles", "absent"),
    [
        ("fstring_shell", ("shell-mediated:sh -c", "syntax-check:bash -n"), ()),
        ("asyncio_shell", ("shell-mediated:sh -c", "syntax-check:bash -n"), ()),
        ("bash_c", ("shell-mediated:bash -c", "syntax-check:bash -n"), ()),
        ("shell_git_alias", ("shell-mediated:bash -c", "config-injection:"), ()),
        ("timeout_wrap", ("unknown-program:timeout", "syntax-check:bash -n"), ()),
        ("env_wrap", ("unknown-program:env",), ("unclassified-argv",)),
        ("nice_wrap", ("unknown-program:nice",), ()),
        ("os_system_git", ("shell-mediated:os.system",), ("unclassified-argv",)),
        ("argv0_override", ("executable-override", "unclassified-argv"), ()),
        ("executable_override", ("executable-override",), ("unclassified-argv",)),
        ("python_c", ("unknown-program:python",), ()),
        ("python_loader_redirect", ("env-injection:PYTHONPATH",), ()),
    ],
)
def test_round3_launches_are_rejected(
    tmp_path: Path,
    case: str,
    needles: tuple[str, ...],
    absent: tuple[str, ...],
) -> None:
    receipt = _run(tmp_path, case)
    _assert_blocked(receipt, *needles)
    rendered = _text(receipt)
    for item in absent:
        assert item not in rendered, rendered


def test_putenv_is_tracked_by_name_and_rejects_the_inherited_launch(tmp_path: Path) -> None:
    work = _work(tmp_path, "putenv")
    receipt = run_entry(
        PROBE,
        ["putenv_pager"],
        cwd=work,
        timeout=20,
        extra_env={"HOOK_RUNTIME_CASE": "putenv_pager"},
    )
    _assert_blocked(receipt, "env-injection:GH_PAGER")
    raw = (work / "audit.jsonl").read_text(encoding="utf-8")
    assert "sentinel-value" not in raw
    assert '"event":"os.putenv"' in raw
    assert '"key":"GH_PAGER"' in raw


def test_redirect_keys_changed_after_baseline_are_rejected(tmp_path: Path) -> None:
    work = _work(tmp_path, "redirect")
    keys = (
        "GH_CONFIG_DIR",
        "GIT_EXEC_PATH",
        "HOME",
        "PATH",
        "XDG_CONFIG_HOME",
        *GIT_REDIRECT_ENV_KEYS,
    )
    receipt = run_entry(
        PROBE,
        ["redirect_mutation"],
        cwd=work,
        timeout=20,
        extra_env={
            "HOOK_RUNTIME_CASE": "redirect_mutation",
            "HOOK_RUNTIME_REDIRECT_KEYS": ",".join(keys),
        },
    )
    _assert_blocked(receipt, "env-injection:")
    rendered = _text(receipt)
    for key in keys:
        assert key in rendered, rendered
    raw = (work / "audit.jsonl").read_text(encoding="utf-8")
    assert "redirected" not in raw
    assert not (work / "real-git-executed").exists()


def test_baseline_path_cannot_execute_a_fake_git(tmp_path: Path) -> None:
    work = _work(tmp_path, "path-tripwire")
    bindir = work / "fake-bin"
    bindir.mkdir()
    git = bindir / "git"
    git.write_text("#!/bin/sh\ntouch real-git-executed\n", encoding="utf-8")
    git.chmod(0o755)
    receipt = run_entry(
        PROBE,
        ["path_tripwire"],
        cwd=work,
        timeout=20,
        extra_env={"HOOK_RUNTIME_CASE": "path_tripwire", "PATH": str(bindir)},
    )
    assert receipt.canary and not receipt.driver_error, receipt.driver_error
    assert not receipt.violations, _text(receipt)
    assert not (work / "real-git-executed").exists()
    assert (work / "shim-result").read_text(encoding="utf-8") == f"canned\n0\n{repo_root()}/.git\n"


def test_canned_success_does_not_authorize_the_next_start(tmp_path: Path) -> None:
    work = _work(tmp_path, "shim-then-forbidden")
    receipt = run_entry(
        PROBE,
        ["shim_then_forbidden"],
        cwd=work,
        timeout=20,
        extra_env={"HOOK_RUNTIME_CASE": "shim_then_forbidden"},
    )
    _assert_blocked(receipt, "syntax-check:bash -n")
    assert (work / "shim-result").read_text(encoding="utf-8") == f"canned\n0\n{repo_root()}/.git\n"


def test_command_processing_corpus_reports_honest_coverage(tmp_path: Path) -> None:
    """Drive every command-processing entry and report which templates actually ran."""
    corpus = _literal_corpus()
    frozen = template_ids()
    rows: list[CoverageRow] = []
    details: list[str] = []

    def one(relative: str) -> tuple[str, EntryReceipt]:
        work = _work(tmp_path, Path(relative).name)
        receipt = run_entry(REPO_ROOT / relative, corpus, cwd=work, timeout=240)
        return relative, receipt

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(one, command_processing_paths()))
    reached_all: set[str] = set()
    for relative, receipt in results:
        starts = [event for event in receipt.events if attempted_start(event)]
        reached = tuple(sorted({ident for event in starts if (ident := allowed_template(event))}))
        reached_all.update(reached)
        unreached = tuple(item for item in frozen if item not in reached)
        name = Path(relative).name
        note = ""
        if receipt.driver_error or receipt.pair_errors:
            status = receipt.driver_error or "pair-error"
        elif receipt.violations:
            status = "violations"
        elif not starts:
            status = "zero-start"
        elif name == "heal-core-bare.py":
            status = "partial"
            note = "descendant withheld: scripts/audit/check_core_bare.py git reads and config writes"
        else:
            status = "pass"
        rows.append(
            CoverageRow(
                relative,
                len(corpus),
                receipt.pairs_completed,
                len(starts),
                len(receipt.violations),
                reached,
                unreached,
                status,
                note,
            )
        )
        if status not in {"pass", "partial", "zero-start"}:
            shown = [f"{count} {shape}" for shape, count in _shapes(receipt, Path(tmp_path) / name)]
            problems = "; ".join(receipt.pair_errors[:3])
            details.append(f"{name}: {receipt.driver_error} {problems}\n" + "\n".join(shown))
    missing = tuple(item for item in frozen if item not in reached_all)
    text = denominator_text(rows=rows)
    text += "\nglobal unreached: " + (", ".join(missing) if missing else "(none)")
    REPORT.write_text(text + "\n", encoding="utf-8")
    assert not details, text + "\n" + "\n".join(details)
    assert not missing, text
    zero = {row.entry.rsplit("/", 1)[-1] for row in rows if row.status == "zero-start"}
    assert zero == {
        "guard-public-github-text.py",
        "guard-reviewer-publish.py",
        "guard-secret-print.py",
    }
    heal = next(row for row in rows if row.entry.endswith("heal-core-bare.py"))
    assert heal.status == "partial"
    assert heal.attempted_starts > 0
    assert "python-check-core-bare" in heal.reached
    for row in rows:
        if row.status == "pass":
            assert row.attempted_starts > 0
            assert row.violations == 0
        if row.status == "zero-start":
            assert row.attempted_starts == 0
    assert excluded_surfaces()
