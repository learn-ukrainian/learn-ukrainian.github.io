from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def test_lesson_viewer_component_exists_and_exports():
    component_path = PROJECT_ROOT / "packages/activity-kit/src/components/LessonViewer.tsx"
    assert component_path.exists(), "LessonViewer.tsx must exist in activity-kit package"

    content = component_path.read_text(encoding="utf-8")
    assert "export const LessonViewer" in content
    assert "export function sanitizeLessonForStudent" in content
    assert "sanitizeLessonForStudent" in content
    assert "student-mode-container" in content

def test_lesson_viewer_index_export():
    index_path = PROJECT_ROOT / "packages/activity-kit/src/index.ts"
    content = index_path.read_text(encoding="utf-8")
    assert "LessonViewer" in content
    assert "sanitizeLessonForStudent" in content

def test_zero_answer_leakage_sanitizer_contract():
    component_path = PROJECT_ROOT / "packages/activity-kit/src/components/LessonViewer.tsx"
    content = component_path.read_text(encoding="utf-8")

    # Ensure sanitizer explicitly strips answer_key, note, and nested activity model answers
    assert "answer_key: null" in content
    assert "note: null" in content
    assert "model_answer: undefined" in content
    assert "guidance: undefined" in content
    assert "rubric: undefined" in content
