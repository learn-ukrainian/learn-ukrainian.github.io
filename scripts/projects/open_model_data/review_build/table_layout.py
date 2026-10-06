"""Declarative, source-only table axes and cell associations.

The grammar is component-reviewed data. This module reconstructs physical
rowspan/colspan coordinates from HTML and authenticates the held row projection;
no candidate-provided header or form association is trusted.
"""

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from .errors import require


@dataclass(frozen=True)
class Cell:
    row: int
    column: int
    text: str
    rowspan: int
    colspan: int
    data: bool

    @property
    def pointer(self):
        return f"/rows/{self.row}/{self.column}"


@dataclass(frozen=True)
class Association:
    cell: Cell
    sections: tuple[Cell, ...]
    row: Cell | None
    columns: tuple[Cell, ...]
    tags: tuple[str, ...]
    unmapped: tuple[str, ...]

    @property
    def headers(self):
        return self.sections + ((self.row,) if self.row else ()) + self.columns


def label(text):
    return re.sub(r"\s+", " ", text).strip().casefold()


def layout(payload: dict, policy: dict) -> list[Association]:
    """Return every data cell with its independently reconstructed axes."""
    soup = BeautifulSoup(payload["raw_html"], "html.parser")
    tables = soup.find_all("table")
    require(len(tables) == 1, "table_authentication")
    occupied, physical = {}, []
    width = 0
    for tr in tables[0].find_all("tr", recursive=False):
        elements = tr.find_all(["td", "th"], recursive=False)
        texts = [re.sub(r"\s+", " ", td.get_text(" ", strip=True)).strip() for td in elements]
        if not texts or not any(texts):
            # Empty source rows cannot change the grid silently.
            require(not elements, "table_authentication")
            continue
        row = len(physical)
        cells, col = [], 0
        for index, (td, text) in enumerate(zip(elements, texts, strict=True)):
            while (row, col) in occupied:
                col += 1
            rs, cs = int(td.get("rowspan") or 1), int(td.get("colspan") or 1)
            require(rs >= 1 and cs >= 1, "table_authentication")
            cell = Cell(row, index, text, rs, cs, bool(set(td.get("class", [])) & set(policy["data_classes"])))
            cells.append((col, cell))
            for dy in range(rs):
                for dx in range(cs):
                    require((row + dy, col + dx) not in occupied, "table_authentication")
                    occupied[row + dy, col + dx] = cell
            col += cs
            width = max(width, col)
        physical.append(cells)
    require([[cell.text for _, cell in row] for row in physical] == payload["rows"], "table_authentication")
    mappings = policy["labels"]
    columns, stacking, parent, subsection = {}, False, None, None
    result = []
    for origins in physical:
        nonblank = [cell for _, cell in origins if cell.text]
        if not nonblank:
            continue
        recognized = [mappings.get(label(cell.text), {}) for cell in nonblank]
        clean = not any(policy["stress_marker"] in cell.text or cell.text.endswith("*") for cell in nonblank)
        is_columns = (
            clean
            and not any(cell.data for cell in nonblank)
            and any(m.get("role") in policy["column_roles"] for m in recognized)
            and not any(m.get("role") in policy["row_exclusive_roles"] for m in recognized)
        )
        if is_columns:
            if not stacking:
                columns = {}
            stacking = True
            for col, cell in origins:
                if not cell.text or label(cell.text) in policy["axis_labels"]:
                    continue
                for dx in range(cell.colspan):
                    columns.setdefault(col + dx, []).append(cell)
            continue
        stacking = False
        distinct = list(dict.fromkeys(cell.text for cell in nonblank))
        section = None
        if clean and len(distinct) == 1:
            first = nonblank[0]
            role = mappings.get(label(first.text), {}).get("role")
            spans_all = len(origins) == 1 and first.colspan >= width
            if role in policy["section_roles"] or (spans_all and role is None):
                section = first
        if section:
            if mappings.get(label(section.text), {}).get("role") == policy["subsection_role"]:
                subsection = section
            else:
                parent, subsection = section, None
            continue
        first = origins[0][1]
        role = mappings.get(label(first.text), {}).get("role")
        row_header = None
        if (
            first.text
            and policy["stress_marker"] not in first.text
            and (role in policy["row_roles"] or len(origins) > 1)
        ):
            row_header = first
        for col, cell in origins[1:] if row_header else origins:
            if not cell.text:
                continue
            active_columns = tuple(columns.get(col, []))
            sections = tuple(c for c in (parent, subsection) if c)
            tags, unknown = [], []
            column_tags = [t for c in active_columns for t in mappings.get(label(c.text), {}).get("tags", [])]
            for c in (*sections, *((row_header,) if row_header else ()), *active_columns):
                mapping = mappings.get(label(c.text))
                if mapping is None:
                    unknown.append(c.text)
                elif not (
                    c is row_header and mapping["role"] == policy["gender_role"] and policy["plural_tag"] in column_tags
                ):
                    tags.extend(mapping["tags"])
            # Source grammar canonicalizes number immediately before person.
            if set(tags) & set(policy["number_tags"]) and set(tags) & set(policy["person_tags"]):
                number_person = [t for t in tags if t in policy["number_tags"]] + [
                    t for t in tags if t in policy["person_tags"]
                ]
                output, placed = [], False
                for tag in tags:
                    if tag in policy["number_tags"] or tag in policy["person_tags"]:
                        if not placed:
                            output.extend(number_person)
                            placed = True
                    else:
                        output.append(tag)
                tags = output
            result.append(Association(cell, sections, row_header, active_columns, tuple(tags), tuple(unknown)))
    return result
