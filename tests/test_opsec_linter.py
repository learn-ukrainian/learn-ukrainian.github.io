import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.audit import lint_opsec_leaks as opsec_linter
from scripts.audit.lint_opsec_leaks import check_content


@pytest.fixture
def pushed_range(monkeypatch, tmp_path):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True, timeout=30).strip()

    git("init", "--initial-branch=main")
    git("config", "user.email", "ci@example.invalid")
    git("config", "user.name", "ci")
    path = tmp_path / "docs/push-scan.md"
    path.parent.mkdir()
    path.write_text("clean base\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "base")
    base = git("rev-parse", "HEAD")
    monkeypatch.setattr(opsec_linter, "REPO_ROOT", tmp_path)
    return git, path, base


@pytest.mark.parametrize("ending", ["reverted", "deleted"])
def test_push_range_refuses_sensitive_value_removed_before_head(pushed_range, monkeypatch, capsys, ending):
    git, path, base = pushed_range
    marker = "-----BEGIN " + "PRIVATE KEY-----"
    path.write_text(marker + "\n", encoding="utf-8")
    git("commit", "-am", "introduce synthetic sentinel")
    if ending == "deleted":
        path.unlink()
    else:
        path.write_text("clean base\n", encoding="utf-8")
    git("commit", "-am", "remove synthetic sentinel")
    monkeypatch.setenv("PRE_COMMIT_FROM_REF", base)
    monkeypatch.setenv("PRE_COMMIT_TO_REF", git("rev-parse", "HEAD"))

    assert opsec_linter.main([]) == 1
    output = capsys.readouterr()
    assert marker not in output.out + output.err
    assert "Private Key Header" in output.out


def test_clean_multi_commit_push_range_passes(pushed_range, monkeypatch):
    git, path, base = pushed_range
    for content in ("first clean version\n", "clean base\n"):
        path.write_text(content, encoding="utf-8")
        git("commit", "-am", "clean change")
    monkeypatch.setenv("PRE_COMMIT_FROM_REF", base)
    monkeypatch.setenv("PRE_COMMIT_TO_REF", git("rev-parse", "HEAD"))

    assert opsec_linter.main([]) == 0


def test_commit_range_fails_closed_when_selected_blob_is_unreadable(pushed_range, monkeypatch, capsys):
    git, path, base = pushed_range
    path.write_text("clean change\n", encoding="utf-8")
    git("commit", "-am", "change")
    monkeypatch.setattr(opsec_linter, "get_git_content", lambda path, rev: None)

    assert opsec_linter.main(["--commit-range", f"{base}..HEAD"]) == 1
    assert "unreadable selected blob" in capsys.readouterr().err


def test_commit_range_named_staged_reads_committed_blobs(pushed_range):
    git, path, base = pushed_range
    path.write_text("-----BEGIN " + "PRIVATE KEY-----\n", encoding="utf-8")
    git("commit", "-am", "introduce synthetic sentinel")
    git("branch", "staged-publication")
    path.write_text("clean base\n", encoding="utf-8")
    git("add", str(path.relative_to(path.parents[1])))

    assert opsec_linter.main(["--commit-range", f"{base}..staged-publication"]) == 1


@pytest.fixture
def publication(pushed_range, monkeypatch, tmp_path):
    git, _path, base = pushed_range
    git("commit", "--allow-empty", "-m", "clean publication")
    pr = {"number": 1, "title": "clean title", "body": None,
          "head": {"ref": "topic", "sha": git("rev-parse", "HEAD")}, "base": {"sha": base}}
    live = copy.deepcopy(pr)
    monkeypatch.setattr(opsec_linter, "current_publication_pr", lambda repo, number: live)
    event_file = tmp_path / "event.json"

    def run(payload, event="pull_request"):
        event_file.write_text(json.dumps(payload))
        monkeypatch.setenv("GITHUB_EVENT_NAME", event)
        return opsec_linter.main(["--event-file", str(event_file)])

    payload = {"repository": {"full_name": "example/project"}, "action": "edited", "pull_request": pr}
    return run, payload, live, git


@pytest.mark.parametrize("field", ["title", "body", "branch", "commit"])
@pytest.mark.parametrize("source", ["event", "live"])
def test_publication_scans_every_pr_field_without_erasing_event_evidence(publication, capsys, field, source):
    run, payload, live, git = publication
    assert run(payload) == 0
    marker = "10." + "23.45.67"
    pr = payload["pull_request"] if source == "event" else live
    if field == "branch":
        pr["head"]["ref"] = marker
    elif field == "commit":
        git("commit", "--allow-empty", "-m", "ordinary subject", "-m", marker)
        pr["head"]["sha"] = git("rev-parse", "HEAD")
    else:
        pr[field] = marker
    assert run(payload) == 1
    output = capsys.readouterr()
    assert marker not in output.out + output.err
    assert f"publication: {field} " in output.out


@pytest.mark.parametrize("field", ["title", "body", "head", "base"])
def test_incomplete_live_enrichment_fails_closed(publication, capsys, field):
    run, payload, live, _git = publication
    del live[field]
    assert run(payload) == 1
    assert capsys.readouterr().err == "OPSEC publication: required input unavailable or invalid\n"


@pytest.mark.parametrize("event,payload", [("unknown", {}), ("push", {}), ("pull_request", []),
                                         ("pull_request", {}), ("merge_group", {})])
def test_unrecognized_or_incomplete_publication_events_never_pass(publication, event, payload):
    run, *_ = publication
    assert run(payload, event) == 1


@pytest.mark.parametrize("invalid", [False, True])
def test_push_scans_complete_git_history_instead_of_truncated_payload(publication, capsys, invalid):
    run, payload, _live, git = publication
    marker = "-----BEGIN " + "PRIVATE KEY-----"
    git("commit", "--allow-empty", "-m", "first subject", "-m", marker)
    git("commit", "--allow-empty", "-m", "clean tip")
    push = {"ref": "refs/heads/topic", "before": payload["pull_request"]["base"]["sha"],
            "after": git("rev-parse", "HEAD"), "commits": [{"message": "clean tip"}]}
    if invalid:
        push["before"] = "f" * 40
    assert run(push, "push") == 1
    output = capsys.readouterr()
    assert marker not in output.out + output.err
    assert ("required input" in output.err) if invalid else ("publication: commit " in output.out)


def test_new_branch_scans_complete_delta_and_shallow_history_is_rejected(publication):
    run, payload, _live, git = publication
    git("update-ref", "refs/remotes/origin/main", payload["pull_request"]["base"]["sha"])
    push = {"ref": "refs/heads/topic", "before": "0" * 40, "after": git("rev-parse", "HEAD"),
            "repository": {"default_branch": "main"}}
    assert run(push, "push") == 0
    git_dir = Path(git("rev-parse", "--absolute-git-dir"))
    (git_dir / "shallow").write_text(push["after"] + "\n")
    assert run(push, "push") == 1


@pytest.mark.parametrize("kind", ["topic", "initial", "unresolved"])
def test_new_push_never_omits_earlier_commit_messages(publication, capsys, kind):
    run, payload, _live, git = publication
    marker = "10." + "23.45.67"
    git("update-ref", "refs/remotes/origin/main", payload["pull_request"]["base"]["sha"])
    git("commit", "--allow-empty", "-m", "subject", "-m", marker)
    git("commit", "--allow-empty", "-m", "clean tip")
    if kind == "unresolved":
        git("update-ref", "-d", "refs/remotes/origin/main")
    push = {"ref": "refs/heads/main" if kind == "initial" else "refs/heads/topic", "before": "0" * 40,
            "after": git("rev-parse", "HEAD"), "repository": {"default_branch": "main"}, "commits": []}
    assert run(push, "push") == 1
    output = capsys.readouterr()
    assert marker not in output.out + output.err
    assert ("required input" in output.err) if kind == "unresolved" else ("publication: commit " in output.out)


def test_direct_push_branch_is_scanned_even_when_commit_payload_is_empty(publication, capsys):
    run, payload, _live, git = publication
    marker = "10." + "23.45.67"
    push = {"ref": "refs/heads/" + marker, "before": payload["pull_request"]["base"]["sha"],
            "after": git("rev-parse", "HEAD"), "commits": []}
    assert run(push, "push") == 1
    output = capsys.readouterr()
    assert "publication: branch " in output.out
    assert marker not in output.out + output.err


@pytest.mark.parametrize("member,field", [(1, "title"), (1, "body"), (2, "branch"), (2, "commit"), (1, "clean")])
def test_queue_scans_each_members_current_fields_and_original_commit_bodies(publication, monkeypatch, capsys, member, field):
    run, payload, live, git = publication
    marker = "10." + "23.45.67"
    prs = {1: copy.deepcopy(live), 2: copy.deepcopy(live)}
    queue_base = queue_head = payload["pull_request"]["head"]["sha"]
    for number in (1, 2):
        git("commit", "--allow-empty", "-m", f"member (#{number})", "-m", marker if (number, field) == (member, "commit") else "clean body")
        prs[number]["number"] = number
        prs[number]["head"]["sha"] = git("rev-parse", "HEAD")
        queue_head = git("commit-tree", "HEAD^{tree}", "-p", queue_head, "-m", f"member (#{number})")
    if field == "branch":
        prs[member]["head"]["ref"] = marker
    elif field not in {"commit", "clean"}:
        prs[member][field] = marker
    monkeypatch.setattr(opsec_linter, "current_publication_pr", lambda repo, number: prs[number])
    group = {"base_sha": queue_base, "head_sha": queue_head,
             "head_ref": "refs/heads/gh-readonly-queue/main/pr-2-" + "a" * 40}
    assert run({"repository": payload["repository"], "action": "checks_requested", "merge_group": group}, "merge_group") == (0 if field == "clean" else 1)
    output = capsys.readouterr()
    assert marker not in output.out + output.err
    if field != "clean":
        assert f"publication: {field} " in output.out


def test_direct_script_publication_mode_needs_no_site_packages(tmp_path):
    script = Path(opsec_linter.__file__).resolve()
    event = tmp_path / "event.json"
    event.write_text("{}")
    result = subprocess.run([sys.executable, "-S", str(script), "--event-file", str(event)],
                            env={**os.environ, "GITHUB_EVENT_NAME": "unsupported"},
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 1
    assert result.stderr == "OPSEC publication: required input unavailable or invalid\n"
    # Exercise the live-metadata import closure too, without network or site packages.
    code = """
import runpy, sys
from types import SimpleNamespace
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).parents[2]))
from scripts.common import github_client
github_client.run = lambda *a, **kw: SimpleNamespace(returncode=0, stdout='{}')
module = runpy.run_path(sys.argv[1])
try:
    module['current_publication_pr']('example/project', 1)
except ValueError:
    raise SystemExit(0)
raise SystemExit(1)
"""
    result = subprocess.run([sys.executable, "-S", "-c", code, str(script)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0
    assert result.stderr == ""



def test_f002_pkcs8_unqualified_private_key_detected():
    begin = "-----BEGIN " + "PRIVATE KEY-----"
    content = f"Some header\n{begin}\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...\n-----END PRIVATE KEY-----"
    findings = check_content(content, "test.pem")
    assert len(findings) > 0
    assert any("Private Key Header" in desc for _, _, desc in findings)


def test_f003_public_ip_detected_and_version_strings_allowed():
    dummy_ip = f"{185}.{220}.{101}.{5}"
    content = f"Server IP is {dummy_ip}\nVersion string 1.2.3 is safe."
    findings = check_content(content, "config.py")
    assert len(findings) == 1
    assert findings[0][1] == dummy_ip
    assert "IPv4 address" in findings[0][2]


def test_passwordless_ssh_detected():
    phrase = "passwordless" + " " + "SSH"
    content = f"Do not use {phrase} in production environments."
    findings = check_content(content, "docs/infra.md")
    assert len(findings) == 1
    assert "Raw SSH auth method disclosure" in findings[0][2]


def test_linter_scans_itself_without_blanket_exemption():
    dummy_ip = f"{185}.{220}.{101}.{5}"
    content = f"dummy = '{dummy_ip}'"
    findings = check_content(content, "scripts/audit/lint_opsec_leaks.py")
    assert len(findings) == 1
    assert findings[0][1] == dummy_ip


def test_public_ip_flagged_even_with_low_octet_numbers_unless_heading():
    ip_like = f"{185}.{220}.{101}.{5}"
    content_prose = f"The primary node is located at {ip_like} in cluster."
    findings_prose = check_content(content_prose, "doc.py")
    assert len(findings_prose) == 1

    content_heading = "### 4.1.3.1 Section Heading"
    findings_heading = check_content(content_heading, "doc.py")
    assert len(findings_heading) == 0


def test_scrubbed_personal_identifier_is_blocked_in_public_content():
    findings = check_content(
        "export const source = 'Alona';\nconst sourceUk = 'АЛЬОНА';",
        "site/src/components/LexiconPractice.tsx",
    )

    assert findings == [
        (1, "alona", "Scrubbed personal identifier"),
        (2, "альона", "Scrubbed personal identifier"),
    ]


def test_scrubbed_personal_identifier_is_not_checked_in_private_code_or_as_substring():
    code_findings = check_content("owner = 'Alona'", "scripts/private_import.py")
    substring_findings = check_content("value = 'malonated'", "docs/safety.md")

    assert code_findings == []
    assert substring_findings == []


def test_scrubbed_personal_identifier_matches_ukrainian_declensions_and_latin_stem():
    forms = ("Альона", "Альони", "Альоні", "Альону", "Альоною", "Альоно", "Alona")

    findings = check_content("\n".join(forms), "site/src/pages/index.astro")

    assert findings == [
        (1, "альона", "Scrubbed personal identifier"),
        (2, "альона", "Scrubbed personal identifier"),
        (3, "альона", "Scrubbed personal identifier"),
        (4, "альона", "Scrubbed personal identifier"),
        (5, "альона", "Scrubbed personal identifier"),
        (6, "альона", "Scrubbed personal identifier"),
        (7, "alona", "Scrubbed personal identifier"),
    ]


def test_scrubbed_personal_identifier_stem_does_not_match_embedded_words():
    findings = check_content(
        "value = 'malonated'; noun = 'батальона'",
        "docs/safety.md",
    )

    assert findings == []


def test_scrubbed_personal_identifier_scans_site_source_and_public_assets():
    source_findings = check_content("const owner = 'Alona'", "site/src/lib/owner.ts")
    asset_findings = check_content("Альони", "site/public/lexicon/owner.json")

    assert source_findings == [(1, "alona", "Scrubbed personal identifier")]
    assert asset_findings == [(1, "альона", "Scrubbed personal identifier")]


def test_public_identifier_pr_mode_scans_only_changed_public_paths(monkeypatch):
    changed_public_path = "site/src/data/changed.json"
    unchanged_public_path = "docs/unchanged.md"
    scanned_paths: list[str] = []

    monkeypatch.setattr(
        opsec_linter,
        "get_files_to_check",
        lambda diff_range, **kwargs: ([changed_public_path, "scripts/private_import.py"], "git diff", "pr-head"),
    )

    def get_content(path: str, rev: str) -> str:
        scanned_paths.append(path)
        assert rev == "pr-head"
        return "clean content"

    monkeypatch.setattr(opsec_linter, "get_git_content", get_content)

    assert opsec_linter.main(["base...pr-head", "--public-identifiers"]) == 0
    assert scanned_paths == [changed_public_path]
    assert unchanged_public_path not in scanned_paths


def test_public_identifier_pr_mode_rejects_a_leak_in_a_changed_public_path(monkeypatch):
    changed_public_path = "docs/changed.md"
    marker = opsec_linter._SCRUBBED_PERSONAL_IDENTIFIER_TOKENS[0]

    monkeypatch.setattr(
        opsec_linter,
        "get_files_to_check",
        lambda diff_range, **kwargs: ([changed_public_path], "git diff", "pr-head"),
    )
    monkeypatch.setattr(opsec_linter, "get_git_content", lambda path, rev: marker)

    assert opsec_linter.main(["base...pr-head", "--public-identifiers"]) == 1


def test_public_identifier_pr_mode_scans_public_path_with_infrastructure_skip_substring(monkeypatch):
    changed_public_path = "docs/references/external/changed.md"
    marker = opsec_linter._SCRUBBED_PERSONAL_IDENTIFIER_TOKENS[0]
    scanned_paths: list[str] = []

    monkeypatch.setattr(opsec_linter, "run_git_nul_separated", lambda cmd: [changed_public_path])

    def get_content(path: str, rev: str) -> str:
        scanned_paths.append(path)
        assert rev == "pr-head"
        return marker

    monkeypatch.setattr(opsec_linter, "get_git_content", get_content)

    assert opsec_linter.main(["base...pr-head", "--public-identifiers"]) == 1
    assert scanned_paths == [changed_public_path]


def test_infrastructure_path_filter_keeps_its_skip_list():
    skipped_path = "docs/references/external/private.md"

    assert opsec_linter.filter_rel_paths([skipped_path]) == []
    assert opsec_linter.filter_rel_paths(
        [skipped_path], apply_infrastructure_skips=False
    ) == [skipped_path]


def test_public_identifier_full_tree_mode_scans_every_public_path(monkeypatch):
    public_paths = ["site/src/data/a.json", "docs/b.md"]
    scanned_paths: list[str] = []

    monkeypatch.setattr(opsec_linter, "get_public_personal_identifier_paths", lambda revision: public_paths)

    def get_content(path: str, rev: str) -> str:
        scanned_paths.append(path)
        assert rev == "HEAD"
        return "clean content"

    monkeypatch.setattr(opsec_linter, "get_git_content", get_content)

    assert opsec_linter.main(["--public-identifiers"]) == 0
    assert scanned_paths == public_paths


def test_symmetric_diff_uses_its_head_for_blob_reads(monkeypatch):
    monkeypatch.setattr(opsec_linter, "run_git_nul_separated", lambda cmd: ["site/src/data/a.json"])

    paths, mode, revision = opsec_linter.get_files_to_check("base-sha...head-sha")

    assert paths == ["site/src/data/a.json"]
    assert mode == "git diff (base-sha...head-sha)"
    assert revision == "head-sha"


def test_commit_range_mode_keeps_union_of_touched_public_paths(monkeypatch, tmp_path):
    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", *args], cwd=tmp_path, text=True, timeout=30
        ).strip()

    git("init", "--initial-branch=main")
    git("config", "user.email", "ci@example.com")
    git("config", "user.name", "ci")
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    git("add", "README.md")
    git("commit", "-m", "base")
    base = git("rev-parse", "HEAD")

    public_path = tmp_path / "site/src/data/changed.json"
    public_path.parent.mkdir(parents=True)
    public_path.write_text("Alona\n", encoding="utf-8")
    git("add", str(public_path.relative_to(tmp_path)))
    git("commit", "-m", "introduce public path")

    public_path.write_text("clean\n", encoding="utf-8")
    git("commit", "-am", "revert public identifier")
    head = git("rev-parse", "HEAD")

    monkeypatch.setattr(opsec_linter, "REPO_ROOT", tmp_path)
    # Read real historical blobs: retaining the path union alone is insufficient.
    assert opsec_linter.main(["--commit-range", f"{base}..{head}", "--public-identifiers"]) == 1


def test_private_tracker_citation_detected_in_public_docs():
    sample_text = (
        "Reference issue: private #622\n"
        "Or infra-private #710.\n"
        "Or private issue #800.\n"
        "And Private tracker #5.\n"
        "private_operational_board = #622\n"
        "private operational board #622\n"
        "private board: #622\n"
        "private board (#622)\n"
        "private board [#622](https://github.com)\n"
        "private [#622](https://github.com)\n"
        "private hramatka #451–#458\n"
        "private Hramatka board #349\n"
        "private repo issue #5\n"
        "private hramatka issue #451\n"
    )
    findings = check_content(
        sample_text,
        "docs/runbooks/agent-seat-onboarding.md",
    )
    assert len(findings) == 14
    for _line_idx, _matched, desc in findings:
        assert "Private tracker citation" in desc


def test_private_tracker_citation_false_positives_prevented():
    sample_text = (
        "Documenting private methods in PR #45.\n"
        "Please keep it private per #9425.\n"
        "private quality calibration under #5254\n"
        "public issue #123\n"
        "private function helper_call()\n"
    )
    findings = check_content(
        sample_text,
        "docs/runbooks/agent-seat-onboarding.md",
    )
    assert findings == []


def test_private_tracker_citation_not_flagged_in_private_code_or_tests():
    findings = check_content(
        "Reference issue: private #622\nOr infra-private #710.",
        "tests/test_something.py",
    )
    assert findings == []
