#!/usr/bin/env python3
"""
FloTHERM HTML 报告对比工具

比较两个 FloTHERM 求解报告（-r report.html），提取表格数据并计算差异。

用法:
    python tools/html_report_compare.py report1.html report2.html
    python tools/html_report_compare.py report1.html report2.html --table "Cuboid*"
    python tools/html_report_compare.py report1.html report2.html --tolerance 0.5
    python tools/html_report_compare.py report1.html report2.html --csv diff.csv
    python tools/html_report_compare.py report1.html --list-tables
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import json
import math
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional, Sequence


# ============================================================================
# Data structures
# ============================================================================


@dataclass
class ParsedTable:
    title: str
    section: str
    headers: list[str]
    rows: list[list[str]]


@dataclass
class ParsedReport:
    path: Path
    project_name: str
    created: str
    tables: list[ParsedTable]

    def __post_init__(self) -> None:
        self.tables_by_title: dict[str, ParsedTable] = {t.title: t for t in self.tables}


@dataclass
class CellDiff:
    column: str
    raw_a: str
    raw_b: str
    value_a: Optional[float]
    value_b: Optional[float]
    abs_diff: Optional[float]
    pct_diff: Optional[float]
    status: str  # "match", "diff", "missing", "non_numeric"


@dataclass
class RowDiff:
    key: str
    cells: list[CellDiff]
    status: str  # "match", "diff", "only_a", "only_b"


@dataclass
class TableDiff:
    title: str
    rows: list[RowDiff]
    pass_count: int
    fail_count: int
    skip_count: int


@dataclass
class CompareResult:
    report_a: ParsedReport
    report_b: ParsedReport
    tolerance: float
    table_diffs: list[TableDiff]

    @property
    def overall_pass(self) -> bool:
        return all(td.fail_count == 0 for td in self.table_diffs)


# ============================================================================
# HTML Parser
# ============================================================================


class FlothermReportParser(HTMLParser):
    """Parse FloTHERM HTML report into structured tables."""

    def __init__(self) -> None:
        super().__init__()
        self.tables: list[ParsedTable] = []
        self.project_name: str = ""
        self.created: str = ""

        # State
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._in_font = False
        self._font_size = ""
        self._font_text = ""

        self._current_cell_text = ""
        self._current_row: list[str] = []
        self._current_table_rows: list[list[str]] = []
        self._current_section = ""
        self._current_table_title = ""

        self._capture_p = False
        self._p_key = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        tag_lower = tag.lower()
        attr_dict = dict(attrs)

        if tag_lower == "font":
            self._in_font = True
            self._font_size = attr_dict.get("size", "")
            self._font_text = ""
        elif tag_lower == "table":
            self._in_table = True
            self._current_table_rows = []
        elif tag_lower == "tr" and self._in_table:
            self._in_row = True
            self._current_row = []
        elif tag_lower == "td" and self._in_row:
            self._in_cell = True
            self._current_cell_text = ""
        elif tag_lower == "p":
            self._capture_p = True
            self._p_key = ""
        elif tag_lower == "b" and self._capture_p:
            pass  # bold tag inside <p>, keep capturing

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()

        if tag_lower == "font" and self._in_font:
            self._in_font = False
            text = _normalize(self._font_text)
            if self._font_size == "+2":
                self._current_section = text
            elif self._font_size == "+1":
                self._current_table_title = text

        elif tag_lower == "td" and self._in_cell:
            self._in_cell = False
            self._current_row.append(_normalize(self._current_cell_text))

        elif tag_lower == "tr" and self._in_row:
            self._in_row = False
            if self._current_row:
                self._current_table_rows.append(self._current_row)

        elif tag_lower == "table" and self._in_table:
            self._in_table = False
            rows = self._current_table_rows
            if len(rows) >= 2:
                headers = rows[0]
                data = rows[1:]
                title = self._current_table_title or headers[0] if headers else "Unknown"
                self.tables.append(ParsedTable(
                    title=title,
                    section=self._current_section,
                    headers=headers,
                    rows=data,
                ))

        elif tag_lower == "p" and self._capture_p:
            self._capture_p = False
            text = _normalize(self._p_key)
            if text.startswith("Project Name"):
                self.project_name = text[len("Project Name"):].strip()
            elif text.startswith("Created:"):
                self.created = text[len("Created:"):].strip()

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._current_cell_text += data
        elif self._in_font:
            self._font_text += data
        elif self._capture_p:
            self._p_key += data

    def handle_entityref(self, name: str) -> None:
        if self._in_cell and name == "nbsp":
            pass  # skip &nbsp;


def _normalize(text: str) -> str:
    """Collapse whitespace and strip."""
    return " ".join(text.split())


def parse_report(path: Path) -> ParsedReport:
    """Parse a FloTHERM HTML report file."""
    parser = FlothermReportParser()
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        parser.feed(fh.read())
    return ParsedReport(
        path=path,
        project_name=parser.project_name,
        created=parser.created,
        tables=parser.tables,
    )


# ============================================================================
# Value utilities
# ============================================================================

_SENTINELS = {"", "-", "n/a", "na", "none", "&nbsp;"}


def _try_float(text: str) -> Optional[float]:
    """Try to parse a cell as float."""
    t = text.strip().lower()
    if t in _SENTINELS:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _pct_diff(a: float, b: float) -> Optional[float]:
    """Calculate percentage difference."""
    denom = max(abs(a), abs(b))
    if denom < 1e-30:
        return 0.0 if abs(a - b) < 1e-30 else None
    return abs(a - b) / denom * 100.0


# ============================================================================
# Comparison logic
# ============================================================================


def _find_key_columns(table: ParsedTable) -> list[int]:
    """Identify columns to use as row key for matching."""
    if not table.rows:
        return [0]
    # Check if column 0 has duplicates
    col0_vals = [row[0].strip() for row in table.rows if row]
    unique = len(set(col0_vals))
    if unique < len(col0_vals):
        # Duplicates exist, add column 1 as composite key
        key_cols = [0]
        if len(table.headers) > 1:
            key_cols.append(1)
        return key_cols
    return [0]


def _row_key(row: list[str], key_cols: list[int]) -> str:
    """Build a key string from row cells."""
    parts = [row[i].strip() if i < len(row) else "" for i in key_cols]
    return " / ".join(parts)


def _match_rows(
    rows_a: list[list[str]],
    rows_b: list[list[str]],
    key_cols_a: list[int],
    key_cols_b: list[int],
) -> list[tuple[Optional[list[str]], Optional[list[str]]]]:
    """Match rows between two tables by key columns."""
    map_a = {_row_key(r, key_cols_a): r for r in rows_a if r}
    map_b = {_row_key(r, key_cols_b): r for r in rows_b if r}

    result: list[tuple[Optional[list[str]], Optional[list[str]]]] = []
    seen: set[str] = set()

    for key, row in map_a.items():
        seen.add(key)
        result.append((row, map_b.get(key)))

    for key, row in map_b.items():
        if key not in seen:
            result.append((None, row))

    return result


def _compare_cells(raw_a: str, raw_b: str, tolerance: float) -> CellDiff:
    """Compare two cell values."""
    va = _try_float(raw_a)
    vb = _try_float(raw_b)

    if va is not None and vb is not None:
        ad = abs(va - vb)
        pd = _pct_diff(va, vb)
        is_match = pd is not None and pd <= tolerance
        return CellDiff(
            column="", raw_a=raw_a, raw_b=raw_b,
            value_a=va, value_b=vb,
            abs_diff=ad, pct_diff=pd,
            status="match" if is_match else "diff",
        )
    elif va is None and vb is None:
        is_match = raw_a.strip() == raw_b.strip()
        return CellDiff(
            column="", raw_a=raw_a, raw_b=raw_b,
            value_a=None, value_b=None,
            abs_diff=None, pct_diff=None,
            status="match" if is_match else "non_numeric",
        )
    else:
        return CellDiff(
            column="", raw_a=raw_a, raw_b=raw_b,
            value_a=va, value_b=vb,
            abs_diff=None, pct_diff=None,
            status="missing",
        )


def compare_table(
    table_a: ParsedTable,
    table_b: ParsedTable,
    tolerance: float,
) -> TableDiff:
    """Compare two tables and return structured diff."""
    key_cols_a = _find_key_columns(table_a)
    key_cols_b = _find_key_columns(table_b)

    # Use headers from table_a as reference, extend if table_b has more columns
    n_cols = max(len(table_a.headers), len(table_b.headers))

    pairs = _match_rows(table_a.rows, table_b.rows, key_cols_a, key_cols_b)

    row_diffs: list[RowDiff] = []
    total_pass = 0
    total_fail = 0
    total_skip = 0

    for row_a, row_b in pairs:
        if row_a is not None and row_b is not None:
            key = _row_key(row_a, key_cols_a)
            key_col_set = set(key_cols_a)
            cells: list[CellDiff] = []
            has_diff = False

            for i in range(n_cols):
                if i in key_col_set:
                    continue  # skip key columns
                ra = row_a[i].strip() if i < len(row_a) else ""
                rb = row_b[i].strip() if i < len(row_b) else ""
                cd = _compare_cells(ra, rb, tolerance)
                cd.column = table_a.headers[i] if i < len(table_a.headers) else f"Col{i}"
                cells.append(cd)
                if cd.status == "diff":
                    has_diff = True
                    total_fail += 1
                elif cd.status == "match":
                    total_pass += 1
                else:
                    total_skip += 1

            row_diffs.append(RowDiff(
                key=key, cells=cells,
                status="diff" if has_diff else "match",
            ))
        elif row_a is not None:
            key = _row_key(row_a, key_cols_a)
            row_diffs.append(RowDiff(key=key, cells=[], status="only_a"))
            total_skip += n_cols - len(key_cols_a)
        else:
            assert row_b is not None
            key = _row_key(row_b, key_cols_b)
            row_diffs.append(RowDiff(key=key, cells=[], status="only_b"))
            total_skip += n_cols - len(key_cols_b)

    return TableDiff(
        title=table_a.title,
        rows=row_diffs,
        pass_count=total_pass,
        fail_count=total_fail,
        skip_count=total_skip,
    )


def compare_reports(
    report_a: ParsedReport,
    report_b: ParsedReport,
    tolerance: float = 1.0,
    table_filter: Optional[str] = None,
) -> CompareResult:
    """Compare two full reports."""
    diffs: list[TableDiff] = []

    for table_a in report_a.tables:
        # Apply filter
        if table_filter and not fnmatch.fnmatch(table_a.title, table_filter):
            continue

        table_b = report_b.tables_by_title.get(table_a.title)
        if table_b is None:
            # Table only in A
            diffs.append(TableDiff(
                title=table_a.title,
                rows=[RowDiff(key=_row_key(r, _find_key_columns(table_a)), cells=[], status="only_a")
                      for r in table_a.rows if r],
                pass_count=0, fail_count=0,
                skip_count=sum(len(r) for r in table_a.rows),
            ))
            continue

        diffs.append(compare_table(table_a, table_b, tolerance))

    return CompareResult(
        report_a=report_a,
        report_b=report_b,
        tolerance=tolerance,
        table_diffs=diffs,
    )


# ============================================================================
# Output formatting
# ============================================================================


def _fmt_num(v: Optional[float], width: int = 10) -> str:
    if v is None:
        return " " * width
    if abs(v) < 1e-3 or abs(v) >= 1e6:
        return f"{v:.4e}".rjust(width)
    return f"{v:.6g}".rjust(width)


def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "    -  "
    return f"{v:6.2f}%"


def _status_tag(s: str) -> str:
    if s == "match":
        return "[OK]"
    elif s == "diff":
        return "[WARN]"
    return "[-]"


def format_console(result: CompareResult, verbose: bool = False, only_diffs: bool = True) -> str:
    """Format comparison as console text."""
    lines: list[str] = []
    ra, rb = result.report_a, result.report_b

    lines.append(f"基准报告: {ra.path.name}  (Project: {ra.project_name})")
    lines.append(f"对比报告: {rb.path.name}  (Project: {rb.project_name})")
    lines.append(f"容差阈值: {result.tolerance:.2f}%")
    lines.append("")

    if not result.table_diffs:
        lines.append("[INFO] 没有找到可对比的表格")
        return "\n".join(lines)

    for td in result.table_diffs:
        # Table header
        status_icon = "PASS" if td.fail_count == 0 else "FAIL"
        lines.append(f"{'=' * 60}")
        lines.append(f"  {td.title}")
        lines.append(f"  {td.pass_count} match, {td.fail_count} differ, {td.skip_count} skipped [{status_icon}]")
        lines.append(f"{'=' * 60}")

        for rd in td.rows:
            if only_diffs and rd.status == "match" and not verbose:
                continue

            if rd.status in ("only_a", "only_b"):
                label = "仅基准" if rd.status == "only_a" else "仅对比"
                lines.append(f"  {rd.key}  [{label}]")
                continue

            for cd in rd.cells:
                if only_diffs and cd.status == "match" and not verbose:
                    continue
                tag = _status_tag(cd.status)
                if cd.value_a is not None and cd.value_b is not None:
                    lines.append(
                        f"  {rd.key:<30s} | {cd.column:<35s} | "
                        f"{_fmt_num(cd.value_a)} | {_fmt_num(cd.value_b)} | "
                        f"{_fmt_num(cd.abs_diff)} | {_fmt_pct(cd.pct_diff)} | {tag}"
                    )
                else:
                    lines.append(
                        f"  {rd.key:<30s} | {cd.column:<35s} | "
                        f"{cd.raw_a:>10s} | {cd.raw_b:>10s} | {'':>10s} | {'':>7s} | {tag}"
                    )

        lines.append("")

    # Summary
    total_pass = sum(td.pass_count for td in result.table_diffs)
    total_fail = sum(td.fail_count for td in result.table_diffs)
    total_skip = sum(td.skip_count for td in result.table_diffs)
    overall = "PASS" if result.overall_pass else "FAIL"

    lines.append(f"{'=' * 60}")
    lines.append(f"汇总: {total_pass} match, {total_fail} differ, {total_skip} skipped  [{overall}]")
    lines.append(f"{'=' * 60}")

    return "\n".join(lines)


def format_csv(result: CompareResult) -> str:
    """Format comparison as CSV."""
    import io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Table", "Row_Key", "Column", "Value_A", "Value_B", "Abs_Diff", "Pct_Diff", "Status"])

    for td in result.table_diffs:
        for rd in td.rows:
            if rd.status in ("only_a", "only_b"):
                writer.writerow([td.title, rd.key, "", "", "", "", "", rd.status])
                continue
            for cd in rd.cells:
                writer.writerow([
                    td.title, rd.key, cd.column,
                    cd.value_a if cd.value_a is not None else cd.raw_a,
                    cd.value_b if cd.value_b is not None else cd.raw_b,
                    cd.abs_diff if cd.abs_diff is not None else "",
                    f"{cd.pct_diff:.4f}" if cd.pct_diff is not None else "",
                    cd.status,
                ])

    return buf.getvalue()


def format_json(result: CompareResult) -> str:
    """Format comparison as JSON."""
    data = {
        "report_a": {"path": str(result.report_a.path), "project": result.report_a.project_name},
        "report_b": {"path": str(result.report_b.path), "project": result.report_b.project_name},
        "tolerance_pct": result.tolerance,
        "overall_pass": result.overall_pass,
        "tables": [],
    }
    for td in result.table_diffs:
        table_data: dict = {
            "title": td.title,
            "pass": td.pass_count,
            "fail": td.fail_count,
            "skip": td.skip_count,
            "rows": [],
        }
        for rd in td.rows:
            row_data: dict = {"key": rd.key, "status": rd.status, "cells": []}
            for cd in rd.cells:
                cell_data: dict = {"column": cd.column, "status": cd.status}
                if cd.value_a is not None:
                    cell_data["value_a"] = cd.value_a
                else:
                    cell_data["raw_a"] = cd.raw_a
                if cd.value_b is not None:
                    cell_data["value_b"] = cd.value_b
                else:
                    cell_data["raw_b"] = cd.raw_b
                if cd.abs_diff is not None:
                    cell_data["abs_diff"] = cd.abs_diff
                if cd.pct_diff is not None:
                    cell_data["pct_diff"] = round(cd.pct_diff, 4)
                row_data["cells"].append(cell_data)
            table_data["rows"].append(row_data)
        data["tables"].append(table_data)

    return json.dumps(data, indent=2, ensure_ascii=False)


def format_html(result: CompareResult, summary_only: bool = False) -> str:
    """Format comparison result as a styled HTML report."""
    ra, rb = result.report_a, result.report_b
    from datetime import datetime

    total_pass = sum(td.pass_count for td in result.table_diffs)
    total_fail = sum(td.fail_count for td in result.table_diffs)
    overall = result.overall_pass

    # Build key tables set for summary mode
    key_table_titles = set(_KEY_TABLES.keys()) if summary_only else None

    parts: list[str] = []
    parts.append('<!DOCTYPE html>')
    parts.append('<html lang="zh"><head><meta charset="utf-8">')
    parts.append(f'<title>FloTHERM Report Comparison: {ra.path.name} vs {rb.path.name}</title>')
    parts.append('''<style>
body { font-family: -apple-system, "Segoe UI", Arial, sans-serif; margin: 20px; background: #f5f6fa; color: #2c3e50; font-size: 14px; }
h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
.meta { background: #fff; padding: 15px 20px; border-radius: 8px; margin: 15px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.summary-box { padding: 20px; border-radius: 8px; margin: 15px 0; text-align: center; font-size: 20px; font-weight: bold; }
.pass-box { background: #d5f5e3; color: #1e8449; }
.fail-box { background: #fadbd8; color: #c0392b; }
.stats { display: flex; gap: 30px; justify-content: center; margin: 15px 0; }
.stat { background: #fff; padding: 12px 24px; border-radius: 6px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.stat-num { font-size: 28px; font-weight: bold; }
.stat-label { font-size: 12px; color: #7f8c8d; }
.stat-pass .stat-num { color: #27ae60; }
.stat-fail .stat-num { color: #e74c3c; }
.stat-skip .stat-num { color: #95a5a6; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 20px 0; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 6px; overflow: hidden; }
th { background: #34495e; color: white; padding: 8px 12px; text-align: left; font-size: 13px; }
td { padding: 6px 12px; border-bottom: 1px solid #ecf0f1; font-size: 13px; }
tr:last-child td { border-bottom: none; }
tr:hover { background: #f8f9fa; }
.section-header { background: #2c3e50; color: white; padding: 10px 16px; border-radius: 6px 6px 0 0; margin-top: 20px; display: flex; justify-content: space-between; align-items: center; }
.section-header.pass { background: #27ae60; }
.section-header.fail { background: #e74c3c; }
.tag { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }
.tag-ok { background: #d5f5e3; color: #1e8449; }
.tag-warn { background: #fadbd8; color: #c0392b; }
.tag-skip { background: #eaecee; color: #7f8c8d; }
.num { font-family: "SF Mono", "Consolas", monospace; }
.diff-val { color: #e74c3c; font-weight: 600; }
</style></head><body>''')

    # Title
    parts.append(f'<h1>FloTHERM Report Comparison</h1>')
    parts.append(f'<p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>')

    # Meta info
    parts.append(f'<div class="meta">')
    parts.append(f'<b>Report A:</b> {ra.path.name} (Project: {ra.project_name}, Created: {ra.created})<br>')
    parts.append(f'<b>Report B:</b> {rb.path.name} (Project: {rb.project_name}, Created: {rb.created})<br>')
    parts.append(f'<b>Tolerance:</b> {result.tolerance:.2f}%')
    parts.append(f'</div>')

    # Overall result
    if overall:
        parts.append(f'<div class="summary-box pass-box">PASS - All values match within tolerance</div>')
    else:
        parts.append(f'<div class="summary-box fail-box">FAIL - {total_fail} differences found</div>')

    # Stats
    total_skip = sum(td.skip_count for td in result.table_diffs)
    parts.append(f'<div class="stats">')
    parts.append(f'<div class="stat stat-pass"><div class="stat-num">{total_pass}</div><div class="stat-label">Match</div></div>')
    parts.append(f'<div class="stat stat-fail"><div class="stat-num">{total_fail}</div><div class="stat-label">Differ</div></div>')
    parts.append(f'<div class="stat stat-skip"><div class="stat-num">{total_skip}</div><div class="stat-label">Skipped</div></div>')
    parts.append(f'</div>')

    # Tables
    for td in result.table_diffs:
        # Skip non-key tables in summary mode
        if summary_only and td.title not in _KEY_TABLES:
            continue

        is_pass = td.fail_count == 0
        header_class = "pass" if is_pass else "fail"
        parts.append(f'<div class="section-header {header_class}">')
        parts.append(f'<span>{td.title}</span>')
        parts.append(f'<span>{td.pass_count} match, {td.fail_count} differ, {td.skip_count} skipped</span>')
        parts.append(f'</div>')

        parts.append(f'<table>')
        parts.append(f'<tr><th>Name</th><th>Column</th><th>Report A</th><th>Report B</th><th>Abs Diff</th><th>% Diff</th><th>Status</th></tr>')

        for rd in td.rows:
            if rd.status in ("only_a", "only_b"):
                label = "Only in A" if rd.status == "only_a" else "Only in B"
                parts.append(f'<tr><td colspan="7">{rd.key} <span class="tag tag-skip">{label}</span></td></tr>')
                continue

            for cd in rd.cells:
                # In summary mode, only show key columns and diff rows
                if summary_only:
                    if not _is_key_column(td.title, cd.column):
                        continue
                    if cd.status != "diff":
                        continue

                tag_class = {"match": "tag-ok", "diff": "tag-warn"}.get(cd.status, "tag-skip")
                tag_text = {"match": "OK", "diff": "WARN", "non_numeric": "-", "missing": "MISS"}.get(cd.status, "-")

                val_a = f'{cd.value_a:.6g}' if cd.value_a is not None else cd.raw_a or '-'
                val_b = f'{cd.value_b:.6g}' if cd.value_b is not None else cd.raw_b or '-'
                abs_str = f'{cd.abs_diff:.4g}' if cd.abs_diff is not None else '-'
                pct_str = f'{cd.pct_diff:.2f}%' if cd.pct_diff is not None else '-'

                diff_class = ' class="diff-val"' if cd.status == "diff" else ''

                parts.append(
                    f'<tr>'
                    f'<td>{rd.key}</td>'
                    f'<td>{cd.column}</td>'
                    f'<td class="num">{val_a}</td>'
                    f'<td class="num">{val_b}</td>'
                    f'<td class="num"{diff_class}>{abs_str}</td>'
                    f'<td class="num"{diff_class}>{pct_str}</td>'
                    f'<td><span class="tag {tag_class}">{tag_text}</span></td>'
                    f'</tr>'
                )

        parts.append(f'</table>')

    parts.append('</body></html>')
    return "\n".join(parts)


def list_tables(report: ParsedReport) -> str:
    """List all tables in a report."""
    lines: list[str] = []
    lines.append(f"文件: {report.path}")
    lines.append(f"项目: {report.project_name}")
    lines.append(f"创建时间: {report.created}")
    lines.append(f"共 {len(report.tables)} 个表格:")
    lines.append("")
    for i, t in enumerate(report.tables, 1):
        lines.append(f"  {i:>3d}. [{t.section}] {t.title}  ({len(t.rows)} 行 x {len(t.headers)} 列)")
    return "\n".join(lines)


# ============================================================================
# Summary mode: key solving results
# ============================================================================

# Key result tables and which columns to show
# Column patterns matched by substring; only matched columns are shown
_KEY_TABLES: dict[str, list[str]] = {
    "Cuboid Name": [
        "Minimum (degC)", "Maximum (degC)", "Mean (degC)",
    ],
    "Solid Conductors Summary": [
        "Max. S-F Surface Temperature (degC)",
        "Max. S-S Surface Temperature (degC)",
        "Cond Heat Net (W)",
        "Total Heat Net (W)",
    ],
    "Temperature Monitor Summary": [
        "Temperature (degC)",
    ],
    "Overall/Cutouts": [
        "Temperature In (degC)", "Temperature Out (degC)",
        "Heat Flow Net (W)",
        "Maximum Solid Temperature(degC)", "Mean Solid Temperature(degC)",
    ],
    "Fixed Flows": [
        "Mean Temperature (degC)", "Max Temperature (degC)",
        "Heat Flow (W)",
    ],
}

# Column name substrings for matching
_KEY_COL_PATTERNS: dict[str, list[str]] = {}
for _tbl, _cols in _KEY_TABLES.items():
    _KEY_COL_PATTERNS[_tbl] = [c.split("(")[0].strip().rstrip() for c in _cols]


def _is_key_column(table_title: str, col_name: str) -> bool:
    """Check if a column is a key result column for the given table."""
    if table_title not in _KEY_COL_PATTERNS:
        return False
    for pat in _KEY_COL_PATTERNS[table_title]:
        if pat in col_name:
            return True
    return False


def format_summary(result: CompareResult) -> str:
    """Format a focused summary of key solving result differences."""
    lines: list[str] = []
    ra, rb = result.report_a, result.report_b

    lines.append(f"{'=' * 70}")
    lines.append(f"  FloTHERM 求解结果对比摘要")
    lines.append(f"  基准: {ra.path.name} ({ra.project_name})")
    lines.append(f"  对比: {rb.path.name} ({rb.project_name})")
    lines.append(f"  容差: {result.tolerance:.2f}%")
    lines.append(f"{'=' * 70}")

    total_key_pass = 0
    total_key_fail = 0
    found_any = False

    for td in result.table_diffs:
        # Only process key tables
        if td.title not in _KEY_TABLES:
            continue
        found_any = True

        # Filter rows and cells to key columns only
        table_pass = 0
        table_fail = 0
        diff_lines: list[str] = []

        for rd in td.rows:
            if rd.status in ("only_a", "only_b"):
                label = "仅基准" if rd.status == "only_a" else "仅对比"
                diff_lines.append(f"    {rd.key:<35s}  [{label}]")
                continue

            filtered_cells: list[CellDiff] = []
            for cd in rd.cells:
                if _is_key_column(td.title, cd.column):
                    filtered_cells.append(cd)
                    if cd.status == "diff":
                        table_fail += 1
                    elif cd.status == "match":
                        table_pass += 1

            if not filtered_cells:
                continue

            has_diff = any(c.status == "diff" for c in filtered_cells)

            # Only show rows with differences in summary mode
            if has_diff:
                for cd in filtered_cells:
                    if cd.status != "diff":
                        continue
                    tag = _status_tag(cd.status)
                    if cd.value_a is not None and cd.value_b is not None:
                        diff_lines.append(
                            f"    {rd.key:<35s} | {cd.column:<40s} | "
                            f"{_fmt_num(cd.value_a)} | {_fmt_num(cd.value_b)} | "
                            f"{_fmt_num(cd.abs_diff)} | {_fmt_pct(cd.pct_diff)} | {tag}"
                        )
                    else:
                        diff_lines.append(
                            f"    {rd.key:<35s} | {cd.column:<40s} | "
                            f"{cd.raw_a:>10s} | {cd.raw_b:>10s} | {'':>10s} | {'':>7s} | {tag}"
                        )

        total_key_pass += table_pass
        total_key_fail += table_fail

        status = "PASS" if table_fail == 0 else "FAIL"
        lines.append(f"\n  {td.title}  [{status}]  "
                     f"{table_pass} match, {table_fail} differ")
        lines.extend(diff_lines)

    if not found_any:
        lines.append("\n  [INFO] 未找到关键求解结果表格")
        return "\n".join(lines)

    overall = "PASS" if total_key_fail == 0 else "FAIL"
    lines.append(f"\n{'=' * 70}")
    lines.append(f"  关键结果汇总: {total_key_pass} match, {total_key_fail} differ  [{overall}]")
    lines.append(f"{'=' * 70}")

    return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="FloTHERM HTML 报告对比工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python tools/html_report_compare.py report1.html report2.html
    python tools/html_report_compare.py report1.html report2.html --summary
    python tools/html_report_compare.py report1.html report2.html --table "Solid*"
    python tools/html_report_compare.py report1.html report2.html --tolerance 0.5 --csv diff.csv
    python tools/html_report_compare.py report1.html report2.html --html diff.html
    python tools/html_report_compare.py report1.html --list-tables
        """,
    )
    parser.add_argument("report_a", type=Path, help="基准报告 HTML 文件")
    parser.add_argument("report_b", type=Path, nargs="?", help="对比报告 HTML 文件")
    parser.add_argument("--list-tables", action="store_true", help="列出报告中所有表格")
    parser.add_argument("--summary", action="store_true", help="只显示关键求解结果（温度、热流）")
    parser.add_argument("--table", help="只比较匹配的表格名（支持通配符，如 'Solid*'）")
    parser.add_argument("--tolerance", type=float, default=1.0, help="容差阈值 (%%), 默认 1.0")
    parser.add_argument("--csv", type=Path, help="导出 CSV 文件")
    parser.add_argument("--json", type=Path, help="导出 JSON 文件")
    parser.add_argument("--html", type=Path, help="导出 HTML 可视化对比报告")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示所有数值（包括匹配的）")
    parser.add_argument("--only-diffs", action="store_true", default=True, help="只显示有差异的行（默认开启）")
    parser.add_argument("--all", action="store_true", help="显示所有行（等价于取消 --only-diffs）")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.report_a.exists():
        print(f"[ERROR] 文件不存在: {args.report_a}", file=sys.stderr)
        return 1

    report_a = parse_report(args.report_a)

    if args.list_tables:
        print(list_tables(report_a))
        return 0

    if args.report_b is None:
        print("[ERROR] 对比模式需要提供第二个报告文件", file=sys.stderr)
        return 1

    if not args.report_b.exists():
        print(f"[ERROR] 文件不存在: {args.report_b}", file=sys.stderr)
        return 1

    report_b = parse_report(args.report_b)

    result = compare_reports(
        report_a, report_b,
        tolerance=args.tolerance,
        table_filter=args.table,
    )

    if args.summary:
        print(format_summary(result))
    else:
        only_diffs = not args.all
        output = format_console(result, verbose=args.verbose, only_diffs=only_diffs)
        print(output)

    if args.csv:
        with args.csv.open("w", encoding="utf-8", newline="") as f:
            f.write(format_csv(result))
        print(f"\n[OK] CSV 已导出: {args.csv}")

    if args.json:
        with args.json.open("w", encoding="utf-8") as f:
            f.write(format_json(result))
        print(f"[OK] JSON 已导出: {args.json}")

    if args.html:
        summary_only = args.summary
        with args.html.open("w", encoding="utf-8") as f:
            f.write(format_html(result, summary_only=summary_only))
        print(f"[OK] HTML 已导出: {args.html}")

    return 0 if result.overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
