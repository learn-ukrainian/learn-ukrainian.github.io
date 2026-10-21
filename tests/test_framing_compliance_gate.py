from __future__ import annotations

from pathlib import Path

from scripts.audit import framing_compliance_gate as gate


def _write_fixture(tmp_path: Path, module_text: str, plan_text: str = "content_outline: []\n") -> tuple[Path, Path]:
    module_path = tmp_path / "module.md"
    plan_path = tmp_path / "plan.yaml"
    module_path.write_text(module_text, encoding="utf-8")
    plan_path.write_text(plan_text, encoding="utf-8")
    return module_path, plan_path


def _verify_fixture(tmp_path: Path, module_text: str, plan_text: str = "content_outline: []\n") -> dict:
    module_path, plan_path = _write_fixture(tmp_path, module_text, plan_text)
    return gate.verify("folk", "fixture", module_path=module_path, plan_path=plan_path, repo_root=tmp_path)


def test_contaminated_fixture_hard_fails_core_veneer_and_magic_on_carols(tmp_path: Path) -> None:
    report = _verify_fixture(
        tmp_path,
        """## Рамка жанру

Учительська теза: колядки мають дохристиянське ядро, а християнська оболонка лише приховує старий зміст.
У такому читанні продукувальна магія колядок забезпечує врожай і добробут дому.
""",
    )

    assert report["passed"] is False
    assert {item["rule_id"] for item in report["violations"]} == {"C1", "C2"}


def test_clean_fixture_passes(tmp_path: Path) -> None:
    report = _verify_fixture(
        tmp_path,
        """## Різдвяна пісенна традиція

Колядки і щедрівки вивчаємо як різдвяні та новорічні пісні побажання в християнській культурі.
Учительська проза тримається тексту: формули славлення, побажання добра, образ дому й громади.
""",
        """content_outline:
  - section: Різдвяна пісенна традиція
    points:
      - Колядки як усна основа письмової літератури
""",
    )

    assert report["passed"] is True
    assert report["violations"] == []
    assert report["warnings"] == []


def test_debunking_fixture_names_bad_frame_without_warning(tmp_path: Path) -> None:
    report = _verify_fixture(
        tmp_path,
        """## Критична рамка

Радянська теза про «прикладну магію» в колядках є хибною: тут ми не повторюємо її як пояснення жанру.
""",
    )

    assert report["passed"] is True
    assert report["violations"] == []
    assert report["warnings"] == []
    assert {item["rule_id"] for item in report["infos"]} == {"W1"}


def test_primary_reading_quote_is_not_scanned_as_teacher_prose(tmp_path: Path) -> None:
    report = _verify_fixture(
        tmp_path,
        """## Читання

:::primary-reading
У цитованому фрагменті може бути прикладна магія.
І навіть продукувальна магія колядки не має рахуватися прозаїчною рамкою.
:::

Після цитати вчитель говорить тільки про текст, образи і різдвяний контекст.
""",
    )

    assert report["passed"] is True
    assert report["violations"] == []
    assert report["warnings"] == []


def test_creation_myth_carol_title_warns(tmp_path: Path) -> None:
    report = _verify_fixture(
        tmp_path,
        """## Колядки: міф про створення світу

Учительська проза має отримати W2, бо це заголовок рамки, а не дебанкінг поганої схеми.
""",
    )

    assert report["passed"] is True
    assert {item["rule_id"] for item in report["warnings"]} == {"W2"}
