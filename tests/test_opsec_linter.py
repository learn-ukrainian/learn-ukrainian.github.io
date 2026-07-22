import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts/audit"))

from lint_opsec_leaks import check_content


def test_f002_pkcs8_unqualified_private_key_detected():
    begin = "-----BEGIN " + "PRIVATE KEY-----"
    content = f"Some header\n{begin}\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...\n-----END PRIVATE KEY-----"
    findings = check_content(content, "test.pem")
    assert len(findings) > 0
    assert any("Private Key Header" in desc for _, _, desc in findings)


def test_f003_public_ip_detected_and_version_strings_allowed():
    dummy_ip = "185.220.101.5"
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
    dummy_ip = "185.220.101.5"
    content = f"dummy = '{dummy_ip}'"
    findings = check_content(content, "scripts/audit/lint_opsec_leaks.py")
    assert len(findings) == 1
    assert findings[0][1] == dummy_ip


def test_public_ip_flagged_even_with_low_octet_numbers_unless_heading():
    ip_like = "185.220.101.5"
    content_prose = f"The primary node is located at {ip_like} in cluster."
    findings_prose = check_content(content_prose, "doc.py")
    assert len(findings_prose) == 1

    content_heading = "### 4.1.3.1 Section Heading"
    findings_heading = check_content(content_heading, "doc.py")
    assert len(findings_heading) == 0
