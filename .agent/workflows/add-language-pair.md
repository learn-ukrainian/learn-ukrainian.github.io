---
description: Add a new source-target language pair (e.g. l2-es-en)
---

This workflow sets up the directory structure and database for a new language pair.

1.  **Define Language Pair**
    Decide on the code, e.g., `l2-es-en` (Spanish for English speakers).
    Format: `l2-{target}-{source}`.

2.  **Create Directory Structure**
    Run the following command to create the necessary folders:
    ```bash
    mkdir -p curriculum/l2-TARGET-SOURCE/{a1,a2,b1,b2,c1,c2}
    mkdir -p docs/l2-TARGET-SOURCE
    ```
    *(Replace `l2-TARGET-SOURCE` with your actual pair, e.g., `l2-es-en`)*

3.  **Initialize Vocabulary Database**
    Initialize the SQLite database for this curriculum:
    ```bash
    npx ts-node scripts/vocab-init.ts l2-TARGET-SOURCE
    ```

4.  **Create Curriculum Plan (Optional but Recommended)**
    Create a plan in `docs/l2-TARGET-SOURCE/A1-CURRICULUM-PLAN.md` based on `docs/l2-uk-en/A1-CURRICULUM-PLAN.md`.

5.  **Create First Module**
    Create your first module file:
    ```bash
    touch curriculum/l2-TARGET-SOURCE/a1/module-01.md
    ```
    (Add content following `docs/l2-uk-en/MODULE-SKELETON.md`)

6.  **Generate Output**
    Test generation for the new language:
    ```bash
    npm run generate l2-TARGET-SOURCE a1 01
    ```
