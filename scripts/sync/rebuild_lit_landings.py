import re
from pathlib import Path

import yaml


def update_landing_pages():
    manifest_path = "curriculum/l2-uk-en/curriculum.yaml"
    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    tracks = manifest.get("levels", {})
    docs_base = Path("starlight/src/content/docs")

    titles = {
        "lit": "LIT - Українська література (Огляд)",
        "lit-essay": "LIT-ESSAY - Українська есеїстика",
        "lit-hist-fic": "LIT-HIST-FIC - Історична проза",
        "lit-fantastika": "LIT-FANTASTIKA - Українська фантастика",
        "lit-war": "LIT-WAR - Література війни",
        "lit-humor": "LIT-HUMOR - Український гумор",
        "lit-youth": "LIT-YOUTH - Юнацька література",
        "lit-doc": "LIT-DOC - Література факту та свідчення",
        "lit-drama": "LIT-DRAMA - Модерна та сучасна драма",
        "lit-crimea": "LIT-CRIMEA - Голоси Криму",
    }

    descriptions = {
        "lit": "Хронологічний огляд розвитку українського слова від Котляревського до наших днів.",
        "lit-essay": "Українська інтелектуальна традиція — від полемістів до сучасних філософів.",
        "lit-hist-fic": "Героїчне минуле крізь призму художнього слова.",
        "lit-fantastika": "Міфи, магія та майбутнє в українській літературі.",
        "lit-war": "Естетика спротиву: українська література в умовах війни.",
        "lit-humor": "Сміх як зброя та ліки української нації.",
        "lit-youth": "Література для нового покоління — від байок до Young Adult.",
        "lit-doc": "Література свідчення, мемуаристика та сила документального слова.",
        "lit-drama": "Від авангардних експериментів 1920-х до документального театру 2020-х.",
        "lit-crimea": "Корінні наративи та література окупованого півострова. Деколонізація кримської перспективи.",
    }

    sidebar_positions = {
        "lit": 10,
        "lit-essay": 11,
        "lit-hist-fic": 12,
        "lit-fantastika": 13,
        "lit-war": 14,
        "lit-humor": 15,
        "lit-youth": 16,
        "lit-doc": 17,
        "lit-drama": 18,
        "lit-crimea": 19,
    }

    for track_id, track_data in tracks.items():
        if not track_id.startswith("lit"):
            continue

        track_dir = docs_base / track_id
        track_dir.mkdir(parents=True, exist_ok=True)

        index_path = track_dir / "index.mdx"

        md_dir = Path("curriculum/l2-uk-en") / track_id
        audit_dir = md_dir / "audit"
        review_dir = md_dir / "review"

        modules = track_data.get("modules", [])

        title = titles.get(track_id, track_id.upper())
        desc = descriptions.get(track_id, "Опис в розробці.")
        pos = sidebar_positions.get(track_id, 100)

        header = "---\nsidebar_position: " + str(pos) + "\ntitle: " + title + "\n---\n\n# 📋 " + title + "\n\n## " + desc + "\n\n---\n\n## Модулі\n\n| # | Модуль | Статус |\n|---|--------|--------|\n"
        table = ""
        completed_count = 0
        qa_count = 0

        for i, slug in enumerate(modules, 1):
            bare = re.sub(r"^\d+-", "", slug)

            mdx_file = track_dir / f"{bare}.mdx"
            audit_file = audit_dir / f"{bare}-audit.md"
            review_file = review_dir / f"{bare}-review.md"
            final_review_file = review_dir / f"{bare}-final-review.md"

            display_name = bare.replace("-", " ").title()

            md_file = md_dir / f"{bare}.md"
            if md_file.exists():
                with open(md_file, encoding="utf-8") as mdf:
                    try:
                        line = mdf.readline()
                        if line.startswith("# "):
                            display_name = line[2:].strip()
                    except OSError:
                        pass

            status = "🚧"
            if mdx_file.exists():
                if review_file.exists() or final_review_file.exists():
                    status = "✅"
                    completed_count += 1
                elif audit_file.exists():
                    status = "QA"
                    qa_count += 1
                else:
                    status = "✅"
                    completed_count += 1

            link_text = display_name
            if status in ["✅", "QA"]:
                link_text = f"[{display_name}](./{bare})"

            table += f"| {i} | {link_text} | {status} |\n"

        total = len(modules)
        percent = int((completed_count / total) * 100) if total > 0 else 0

        footer = "\n---\n\n## Прогрес\n\n- **Готові модулі:** " + str(completed_count) + "\n- **Заплановані модулі:** " + str(total) + "\n- **Завершення:** " + str(percent) + "%\n"
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(header + table + footer)

if __name__ == "__main__":
    update_landing_pages()
