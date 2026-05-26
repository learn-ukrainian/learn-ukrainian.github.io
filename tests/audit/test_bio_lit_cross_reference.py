import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(repo_root))

from scripts.audit.bio_lit_cross_reference import extract_bio_slug, load_exclusions, main


def test_slug_derivation():
    bios = {"oles-honchar", "oleksandr-oles"}

    yaml_data_tychyna = {'title': 'Павло Тичина: «Сонячні кларнети»'}
    slug1 = extract_bio_slug('tychyna-clarinets', yaml_data_tychyna, bios)
    assert slug1 == 'pavlo-tychyna'

    slug2 = extract_bio_slug('oles-the-nightingale', {'title': 'Олександр Олесь'}, bios)
    assert slug2 == 'oleksandr-oles'

    slug3 = extract_bio_slug('oles-honchar-praporonosy', {}, bios)
    assert slug3 == 'oles-honchar'

    yaml_data_vin = {'title': 'Микола Вінграновський: Поезія'}
    slug4 = extract_bio_slug('vinhranovskyi-poetry', yaml_data_vin, bios)
    assert slug4 == 'mykola-vinhranovskyi'


def test_exclusion_integration(tmp_path):
    exclusion_file = tmp_path / "exclusions.md"
    exclusion_file.write_text("""
| LIT plan(s) | Excluded author | Reason | Reviewer |
|---|---|---|---|
| plans/lit/example1.yaml, plans/lit/example2.yaml | "Pushkin Alexander" | Russian author | claude |
| plans/lit/thematic.yaml | "Thematic" | Not an author | gemini |
""")

    exclusions = load_exclusions(exclusion_file)
    assert "plans/lit/example1.yaml" in exclusions
    assert "plans/lit/example2.yaml" in exclusions
    assert "plans/lit/thematic.yaml" in exclusions


def test_empty_state(tmp_path, monkeypatch):
    """
    Test 4: Empty-state test: with all bios theoretically created, script returns clean.
    """
    # Create fake repo structure
    bio_dir = tmp_path / 'curriculum' / 'l2-uk-en' / 'plans' / 'bio'
    bio_dir.mkdir(parents=True)
    (bio_dir / 'pavlo-tychyna.yaml').write_text("slug: pavlo-tychyna")

    lit_dir = tmp_path / 'curriculum' / 'l2-uk-en' / 'plans' / 'lit'
    lit_dir.mkdir(parents=True)
    (lit_dir / 'tychyna-clarinets.yaml').write_text("title: 'Павло Тичина'")

    audit_dir = tmp_path / 'docs' / 'audits'
    audit_dir.mkdir(parents=True)

    def mock_resolve(*args, **kwargs):
        class MockPath:
            @property
            def parent(self):
                class Parent1:
                    @property
                    def parent(self):
                        class Parent2:
                            @property
                            def parent(self):
                                return tmp_path
                        return Parent2()
                return Parent1()
        return MockPath()

    monkeypatch.setattr("scripts.audit.bio_lit_cross_reference.Path.resolve", mock_resolve)

    try:
        main()
    except SystemExit as e:
        assert e.code == 0


def test_sanity_gap_detection(tmp_path, monkeypatch):
    """
    Test 1: Sanity test: script SHOULD report Тичина as a gap since bio doesn't exist.
    """
    bio_dir = tmp_path / 'curriculum' / 'l2-uk-en' / 'plans' / 'bio'
    bio_dir.mkdir(parents=True)
    # Intentionally missing pavlo-tychyna.yaml

    lit_dir = tmp_path / 'curriculum' / 'l2-uk-en' / 'plans' / 'lit'
    lit_dir.mkdir(parents=True)
    (lit_dir / 'tychyna-clarinets.yaml').write_text("title: 'Павло Тичина'")

    audit_dir = tmp_path / 'docs' / 'audits'
    audit_dir.mkdir(parents=True)

    def mock_resolve(*args, **kwargs):
        class MockPath:
            @property
            def parent(self):
                class Parent1:
                    @property
                    def parent(self):
                        class Parent2:
                            @property
                            def parent(self):
                                return tmp_path
                        return Parent2()
                return Parent1()
        return MockPath()

    monkeypatch.setattr("scripts.audit.bio_lit_cross_reference.Path.resolve", mock_resolve)

    try:
        main()
    except SystemExit as e:
        assert e.code == 1
