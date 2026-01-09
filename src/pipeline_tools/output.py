from __future__ import annotations

from typing import Iterable


def render_table(headers: list[str], rows: Iterable[list[str]]) -> list[str]:
    data = [headers, *rows]
    widths = [max(len(str(cell)) for cell in column) for column in zip(*data)]
    lines: list[str] = []
    for idx, row in enumerate(data):
        padded = [str(cell).ljust(widths[i]) for i, cell in enumerate(row)]
        lines.append("  ".join(padded))
        if idx == 0:
            lines.append("  ".join("-" * w for w in widths))
    return lines
