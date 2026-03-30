# B2-C2 Plan Architecture — Beyond Dialogues

At B2, C1, and C2 levels, the curriculum shifts from simple situational dialogues to complex linguistic competencies: analytical reading, professional writing, argumentative speaking, and nuanced listening.

## Core Philosophy

Long dialogues at B2+ often feel artificial. While `dialogue_situations` should remain available for role-play scenarios (e.g., job interviews, negotiations), they are no longer the primary vehicle for grammar grounding. Instead, plans must use **Reading Situations**, **Listening Situations**, **Writing Tasks**, and **Discussion Topics**.

## New Plan Fields

### 1. Reading Situations (`reading_situations`)
Grounds grammar in authentic or semi-authentic written Ukrainian.

| Field | Description |
|-------|-------------|
| `source_type` | Type of text: `наукова стаття`, `художній уривок`, `офіційний лист`, `блог`, `новина`. |
| `topic` | Specific subject matter (e.g., "The impact of AI on the labor market"). |
| `key_elements` | Specific terms, stylistic devices (metaphors, epithets), or facts to be included in the text. |
| `motivation` | Why this text? (e.g., "Demonstrate passive voice in scientific style"). |

### 2. Listening Situations (`listening_situations`)
Focuses on capturing arguments, tone, and specific details from audio/video.

| Field | Description |
|-------|-------------|
| `media_type` | `відео`, `аудіо`, `інтерв'ю`, `подкаст`, `лекція`. |
| `setting` | Context of the recording (e.g., "A televised debate between two historians"). |
| `focus_points` | Specific details or arguments the learner must capture. |
| `motivation` | Pedagogical goal (e.g., "Identifying speaker bias", "Listening for numbers in financial reports"). |

### 3. Writing Tasks (`writing_tasks`)
Structured production tasks following Ukrainian educational standards (ЗНО/НМТ).

| Field | Description |
|-------|-------------|
| `task_type` | `есе`, `офіційний лист`, `відгук`, `репортаж`, `власне висловлення`. |
| `prompt` | The specific question or assignment for the learner. |
| `requirements` | Specific constraints: word count, required grammar, structure. |
| `motivation` | Goal (e.g., "Mastering the 'Thesis-Argument-Example' structure"). |

### 4. Discussion Topics (`discussion_topics`)
Prompts for oral production, debate, and defending a point of view.

| Field | Description |
|-------|-------------|
| `context` | A scenario or controversial statement for discussion. |
| `questions` | Specific prompts to trigger debate or analysis. |
| `motivation` | Pedagogical goal (e.g., "Using rhetorical questions", "Expressing concession with 'хоча'"). |

---

## Gemini's Input: Textbook Alignment (Заболотний, Авраменко)

To ensure academic rigor and decolonized pedagogy, B2+ modules should mirror the rigor of Ukrainian Grades 9-11:

1.  **Stylistics (Стилістика)**: Every module should highlight which *style* (artistic, scientific, official, publicistic) is being modeled.
2.  **Culture of Speech (Культура мовлення)**: Explicitly target paronyms (тактичний/тактовний) and common Russianisms.
3.  **Complex Syntax**: Use `reading_situations` to demonstrate multi-clause sentences with various conjunctions.
4.  **Model Answers**: ALL writing tasks at B2+ MUST have a model answer in the content.

## Template Example (B2 Grammar Module)

```yaml
level: B2
slug: passive-voice
# ...
reading_situations:
  - source_type: "наукова стаття"
    topic: "Охорона навколишнього середовища в Україні"
    key_elements: ["забруднення", "екосистема", "державна програма"]
    motivation: "Showcase passive constructions (було розроблено, здійснюється) in formal register."

writing_tasks:
  - task_type: "офіційний лист"
    prompt: "Write a letter to the Ministry of Ecology regarding a local environmental issue."
    requirements: ["мінімум 150 слів", "використати 3 пасивні конструкції"]
    motivation: "Apply formal register and passive voice in a professional context."
```
