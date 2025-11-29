# Curricula Opus - Language Content Factory

## 🌐 Mission
Curricula Opus is a pioneering project focused on generating structured, high-quality educational curricula for language acquisition and beyond. Our core mission is to empower learners with a "Theory-First" approach, providing deep contextual understanding alongside practical application.

Initially, we are building a comprehensive curriculum for **Ukrainian as a Second Language (L2) for English speakers**, with plans to expand to other language pairs and subjects like Arts and Sciences.

## ✨ Key Features
-   **Comprehensive L2 Ukrainian Curriculum**: A detailed A1 to C1 pathway designed for English-speaking learners.
-   **Theory-First Learning**: Emphasizes foundational understanding of grammar, culture, history, and literature.
-   **Dual Content Output**: 
    -   **Human-Readable Textbooks**: Detailed lesson content in Markdown (`.md`) and static HTML (`.html`) formats, ideal for deep study and reference.
    -   **Vibe-Compatible Activities**: Machine-readable JSON files tailored for interactive practice within the Vibe application.
-   **Scalable Architecture**: Designed to easily extend to new language pairs (e.g., Ukrainian L1, English L2 for Hungarians) and diverse subjects (e.g., Literature, History, STEM).
-   **Cultural Immersion**: Integrates cultural nuances, history, and authentic materials from early stages.

## 🚀 Getting Started

### Project Setup
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/krisztiankoos/curricula-opus.git
    cd curricula-opus
    ```
2.  **Install Dependencies**:
    ```bash
    npm install
    ```

### Viewing Content
-   **Curriculum Plans (High-Level)**: Explore the `docs/curriculum/` directory for the overall curriculum roadmap and theoretical approaches.
-   **Course Content (Textbooks)**: Navigate to `course-content/l2-uk-en/`. Each module has a `textbook.md` and `textbook.html` file. Open the `.html` files in your browser to view the lessons.

### Generating Content
The `scripts/` directory contains tools to generate various outputs.

-   **Scaffold Course Structure**: To create all module folders and placeholder Markdown files:
    ```bash
    npx ts-node scripts/scaffold-structure.ts
    ```
-   **Convert Markdown to HTML**: To generate HTML from a specific Markdown textbook:
    ```bash
    node scripts/convert-md-to-html.js course-content/l2-uk-en/book-01-survivor/module-01-cyrillic/textbook.md
    ```
    *(Replace the path with your target Markdown file)*
-   **Generate Vibe JSONs**: *(Currently under development)* This script will eventually take detailed Markdown definitions and output Vibe-compatible JSON files.
    ```bash
    # Example (will be expanded as modules are built)
    npx ts-node scripts/generate-curriculum.ts
    ```

## 📂 Project Structure

-   `**docs/**`: High-level curriculum plans, theoretical proposals, and internal documentation (e.g., `CURRICULUM_PLAN.md`).
-   `**scripts/**`: Automation and utility scripts for content generation and format conversion.
-   `**course-content/**`: The primary educational content (textbooks) in Markdown and HTML formats, organized by language pair, book, and module.
-   `**output/vibe-content/**`: Generated Vibe-compatible JSON files for interactive exercises.
-   `**.gemini/GEMINI.md**`: Internal agent memory and project context.
-   `**package.json, node_modules/**`: Standard Node.js project files.

## 🤝 Contribution
Contributions are welcome! Please refer to the `docs/` directory for methodological guidelines and the `scripts/` directory for development tools.

## 🗺️ Future Roadmap
-   **Ukrainian L1 Curriculum**: For native speakers, focusing on literature, history, and advanced linguistic analysis.
-   **English L2 for Ukrainians**.
-   **English L2 for Hungarians** (and other language pairs).
-   **Arts & Sciences Curricula**: Expanding the content factory to subjects beyond language.

---