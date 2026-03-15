"""Tests for semantic Russicism detection in plans."""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from pipeline.semantic_russianisms import scan_and_fix_plan, scan_plan_for_russianisms


class TestScanPlan:
    """scan_plan_for_russianisms finds semantic false friends."""

    def test_detects_luk_as_onion(self, tmp_path):
        plan = {
            "vocabulary_hints": {
                "recommended": [
                    "лук (onion/bow) — decodable; everyday food",
                ]
            }
        }
        plan_path = tmp_path / "test.yaml"
        plan_path.write_text(yaml.dump(plan, allow_unicode=True))

        findings = scan_plan_for_russianisms(plan_path)
        assert len(findings) == 1
        assert findings[0]["word"] == "лук"
        assert findings[0]["meaning_found"] == "onion"
        assert findings[0]["replacement"] == "цибуля"

    def test_ignores_luk_as_bow(self, tmp_path):
        plan = {
            "vocabulary_hints": {
                "recommended": [
                    "лук (bow) — decodable",
                ]
            }
        }
        plan_path = tmp_path / "test.yaml"
        plan_path.write_text(yaml.dump(plan, allow_unicode=True))

        findings = scan_plan_for_russianisms(plan_path)
        assert len(findings) == 0

    def test_detects_gorod_as_city(self, tmp_path):
        plan = {
            "vocabulary_hints": {
                "required": [
                    "город (city) — high frequency",
                ]
            }
        }
        plan_path = tmp_path / "test.yaml"
        plan_path.write_text(yaml.dump(plan, allow_unicode=True))

        findings = scan_plan_for_russianisms(plan_path)
        assert len(findings) == 1
        assert findings[0]["word"] == "город"
        assert findings[0]["replacement"] == "місто"

    def test_no_findings_for_clean_plan(self, tmp_path):
        plan = {
            "vocabulary_hints": {
                "required": [
                    "мама (mom) — decodable",
                    "кіт (cat) — decodable",
                ]
            }
        }
        plan_path = tmp_path / "test.yaml"
        plan_path.write_text(yaml.dump(plan, allow_unicode=True))

        findings = scan_plan_for_russianisms(plan_path)
        assert len(findings) == 0

    def test_missing_file(self, tmp_path):
        findings = scan_plan_for_russianisms(tmp_path / "nonexistent.yaml")
        assert findings == []


class TestFixPlan:
    """fix_plan_russianisms auto-corrects semantic false friends."""

    def test_fixes_luk_to_tsybulya(self, tmp_path):
        plan = {
            "vocabulary_hints": {
                "recommended": [
                    "лук (onion) — everyday food",
                    "кіт (cat) — decodable",
                ]
            }
        }
        plan_path = tmp_path / "test.yaml"
        plan_path.write_text(yaml.dump(plan, allow_unicode=True))

        findings, fixes = scan_and_fix_plan(plan_path)
        assert len(findings) == 1
        assert fixes == 1

        updated = plan_path.read_text()
        assert "цибуля" in updated
        assert "лук (onion)" not in updated

    def test_no_fix_for_flag_only(self, tmp_path):
        plan = {
            "vocabulary_hints": {
                "required": [
                    "дурний (stupid) — adjective",
                ]
            }
        }
        plan_path = tmp_path / "test.yaml"
        plan_path.write_text(yaml.dump(plan, allow_unicode=True))

        findings, fixes = scan_and_fix_plan(plan_path)
        assert len(findings) == 1
        assert fixes == 0  # flag-only, no auto-fix
