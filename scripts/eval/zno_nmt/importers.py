"""Import a complete NLPForUA/ZNO paper without silently dropping questions."""

from __future__ import annotations

from .core import ExamError, prepare_exam


def import_zno(papers: list, test_id: str, metadata: dict) -> dict:
    if not isinstance(papers, list):
        raise ExamError("NLPForUA input must be an array of papers")
    matches = [paper for paper in papers if isinstance(paper, dict) and paper.get("test_id") == test_id]
    if len(matches) != 1:
        raise ExamError("source test ID must select exactly one complete paper")
    paper = matches[0]
    tasks = paper.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != paper.get("num_tasks") or not tasks:
        raise ExamError("source paper count mismatch")
    items = []
    seen = set()
    for task in tasks:
        if not isinstance(task, dict):
            raise ExamError("invalid source task")
        source_id = task.get("task_id")
        if type(source_id) is not int or source_id in seen or source_id < 0:
            raise ExamError("invalid or duplicate source task ID")
        seen.add(source_id)
        if task.get("with_photo") is not False:
            raise ExamError("image-dependent task requires a separately verified multimodal adapter")
        answers = task.get("answers")
        columns = task.get("answer_vheader")
        row_ids = task.get("answer_hheader")
        correct = task.get("correct_answer")
        if not all(isinstance(value, list) for value in (answers, columns, row_ids, correct)):
            raise ExamError("invalid source answer table")
        if len(set(columns)) != len(columns) or len(set(row_ids)) != len(row_ids):
            raise ExamError("duplicate source answer table headers")
        if set(columns) & set(row_ids):
            raise ExamError("ambiguous source answer table headers")
        entries = {}
        for answer in answers:
            if not isinstance(answer, dict) or set(answer) != {"answer", "text"}:
                raise ExamError("invalid source option")
            marker = answer["answer"]
            if not isinstance(marker, str) or marker in entries:
                raise ExamError("invalid or duplicate source option")
            entries[marker] = answer["text"]
        if not set(columns) <= entries.keys() or not entries.keys() <= set(columns) | set(row_ids):
            raise ExamError("source options do not match table headers")
        if len(correct) != (len(row_ids) if row_ids else 1):
            raise ExamError("source key does not match table shape")
        items.append({
            "id": str(source_id + 1),  # upstream is zero-based; paper numbering is one-based
            "kind": "matching" if row_ids else "single",
            "question": task.get("question"),
            "options": [{"id": marker, "text": entries[marker]} for marker in columns],
            "rows": [{"id": marker, "text": entries.get(marker, "")} for marker in row_ids],
            "correct": dict(zip(row_ids, correct, strict=True)) if row_ids else correct[0],
        })
    if set(metadata) != {"title", "subject", "year", "provenance", "scoring"}:
        raise ExamError("metadata must contain title, subject, year, provenance and scoring")
    exam = {"schema": "zno-nmt.exam.v1", **metadata, "items": items}
    prepare_exam(exam)
    return exam
