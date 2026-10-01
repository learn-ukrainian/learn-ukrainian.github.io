"""Override files must be loaded by IPA generation after the scripts refactor."""

import sys
from types import SimpleNamespace

import pytest

from scripts.generate_mdx import generate_ipa as ipa_module
from scripts.verification.stress import STRESS_OVERRIDES_PATH, pending_stress_reason


def test_ipa_loader_uses_both_scripts_data_files(monkeypatch):
    assert STRESS_OVERRIDES_PATH.parent == ipa_module.DATA_DIR
    assert ipa_module._load_overrides("stress_overrides.yaml")["любов"] == "любо́в"
    assert "його" not in ipa_module._load_overrides("stress_overrides.yaml")
    assert pending_stress_reason("його")
    assert isinstance(ipa_module._load_overrides("ipa_overrides.yaml"), dict)

    monkeypatch.setattr(ipa_module, "_ipa_overrides", None)
    received = []
    monkeypatch.setitem(
        sys.modules, "ipa_uk", SimpleNamespace(ipa=lambda stressed: received.append(stressed) or "joˈɦo")
    )
    assert ipa_module.generate_ipa("любов") == "[jɔˈɦɔ]"
    assert received == ["любо́в"]


@pytest.mark.parametrize("form", ["його", "Його", "йому", "Йому", "нього", "переді", "піді"])
def test_pending_form_never_reaches_ipa_or_stressifier(form, monkeypatch):
    monkeypatch.setattr(ipa_module, "_ipa_overrides", {form: "[invalid]"})
    monkeypatch.setitem(sys.modules, "ipa_uk", SimpleNamespace(ipa=lambda _: pytest.fail("pending reached ipa_uk")))
    assert pending_stress_reason(form)
    assert ipa_module.generate_ipa(form) is None


def test_missing_ipa_override_file_is_an_error(monkeypatch, tmp_path):
    monkeypatch.setattr(ipa_module, "DATA_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        ipa_module._load_overrides("stress_overrides.yaml")
