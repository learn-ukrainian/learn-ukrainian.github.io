import importlib.util
import subprocess
import sys
from pathlib import Path


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
    result = subprocess.run([sys.executable, str(script_path), "--stats"], capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed with output: {result.stderr}\n{result.stdout}"
