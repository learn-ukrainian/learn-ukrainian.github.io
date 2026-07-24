from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def test_vocab_drawer_component_exists_and_exports():
    vocab_path = PROJECT_ROOT / "packages/activity-kit/src/components/VocabularyDrawer.tsx"
    assert vocab_path.exists(), "VocabularyDrawer.tsx must exist in activity-kit"

    content = vocab_path.read_text(encoding="utf-8")
    assert "export const VocabularyDrawer" in content
    assert "vocabulary-drawer-overlay" in content
    assert "vocabulary-drawer-panel" in content

def test_theory_callout_component_exists_and_exports():
    theory_path = PROJECT_ROOT / "packages/activity-kit/src/components/TheoryCallout.tsx"
    assert theory_path.exists(), "TheoryCallout.tsx must exist in activity-kit"

    content = theory_path.read_text(encoding="utf-8")
    assert "export const TheoryCallout" in content
    assert "theory-callout" in content

def test_vocab_theory_index_exports():
    index_path = PROJECT_ROOT / "packages/activity-kit/src/index.ts"
    content = index_path.read_text(encoding="utf-8")
    assert "VocabularyDrawer" in content
    assert "TheoryCallout" in content
