import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts/audit"))

import lint_opsec_leaks as opsec_linter
from lint_opsec_leaks import check_content


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
