"""Override files must be loaded by IPA generation after the scripts refactor."""

import sys
from types import SimpleNamespace

import pytest

from scripts.generate_mdx import generate_ipa as ipa_module
from scripts.verification.stress import STRESS_OVERRIDES_PATH


def test_ipa_loader_uses_both_scripts_data_files(monkeypatch):
    assert STRESS_OVERRIDES_PATH.parent == ipa_module.DATA_DIR
    assert ipa_module._load_overrides("stress_overrides.yaml")["його"] == "його́"
    assert isinstance(ipa_module._load_overrides("ipa_overrides.yaml"), dict)

    monkeypatch.setattr(ipa_module, "_ipa_overrides", None)
    monkeypatch.setattr(ipa_module, "_stress_overrides", None)
    monkeypatch.setattr(ipa_module, "_get_stressifier", lambda: lambda word: "йо́го")
    received = []
    monkeypatch.setitem(sys.modules, "ipa_uk", SimpleNamespace(ipa=lambda stressed: received.append(stressed) or "joˈɦo"))
    assert ipa_module.generate_ipa("його") == "[jɔˈɦɔ]"
    assert received == ["його́"]


def test_missing_ipa_override_file_is_an_error(monkeypatch, tmp_path):
    monkeypatch.setattr(ipa_module, "DATA_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        ipa_module._load_overrides("stress_overrides.yaml")
