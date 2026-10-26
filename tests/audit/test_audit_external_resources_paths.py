import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest


def get_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "audit" / "audit_external_resources.py"
    spec = importlib.util.spec_from_file_location("audit_external_resources", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_external_resources"] = module
    spec.loader.exec_module(module)
    return module

def test_resources_file_exists():
    module = get_module()
    assert module.RESOURCES_FILE.exists(), f"File does not exist: {module.RESOURCES_FILE}"

def test_resources_file_path_resolution():
    module = get_module()
    parts = module.RESOURCES_FILE.parts[-3:]
    assert "scripts" not in parts, f"Path resolved incorrectly into scripts/: {module.RESOURCES_FILE}"
    assert "docs" in module.RESOURCES_FILE.parts, f"Path should contain 'docs': {module.RESOURCES_FILE}"

def test_live_reproducer():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "audit" / "audit_external_resources.py"
    # We use subprocess with sys.executable to run exactly how the test is run
    result = subprocess.run([sys.executable, str(script_path), "--stats"], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, f"Script failed with output: {result.stderr}\n{result.stdout}"


@pytest.mark.parametrize("head_status", [200, 405])
def test_check_url_sends_public_contact_without_browser_impersonation(monkeypatch, head_status):
    module = get_module()
    url = "https://example.org/resource"
    head_response = Mock(status_code=head_status, history=[], url=url)
    get_response = Mock(status_code=200, history=[head_response], url=f"{url}/final")
    head = Mock(return_value=head_response)
    get = Mock(return_value=get_response)
    monkeypatch.setattr(module.requests, "head", head)
    monkeypatch.setattr(module.requests, "get", get)

    result = module.check_url(url)

    expected_headers = {
        "User-Agent": (
            "learn-ukrainian-audit/1.0 "
            "(+https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues)"
        ),
    }
    sent_user_agent = head.call_args.kwargs["headers"]["User-Agent"]
    assert "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues" in sent_user_agent
    assert "Mozilla" not in sent_user_agent
    head.assert_called_once_with(url, headers=expected_headers, timeout=15, allow_redirects=True)
    if head_status == 405:
        get.assert_called_once_with(
            url, headers=expected_headers, timeout=15, allow_redirects=True, stream=True,
        )
        get_response.close.assert_called_once_with()
    else:
        get.assert_not_called()
    head_response.close.assert_not_called()
    assert result == {
        "status": 200,
        "ok": True,
        "redirected": head_status == 405,
        "final_url": f"{url}/final" if head_status == 405 else None,
        "error": None,
    }
