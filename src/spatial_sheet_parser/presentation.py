"""Presentation and formatting functions for terminal previews and JSON export."""

import json
from typing import Any, Dict, List, Optional


def export_json(result: Dict[str, Any], indent: int = 2) -> str:
    """Serializes parser result dictionary to formatted JSON string.

    Args:
        result: Result dictionary from SpatialSheetParser.parse_grid().
        indent: Indentation spaces (default: 2).

    Returns:
        JSON formatted string preserving raw cell values and structure.
    """
    return json.dumps(result, indent=indent, ensure_ascii=False)


def render_markdown_tables(result: Dict[str, Any]) -> str:
    """Renders all parsed tables as structured Markdown with embedded metadata headers.

    The output is designed to be human-readable AND machine-parsable (reversible).
    Each table block looks like:

        ### [TABLE: tbl_001] "Title Here"
        <!-- id=tbl_001 level=0 parent=null range=R28C1:R38C9 -->
        | Col1 | Col2 | Col3 |
        |------|------|------|
        | val1 | val2 | val3 |

    Args:
        result: Result dictionary from SpatialSheetParser.parse_grid().

    Returns:
        Reversible Markdown string with all tables represented.
    """
    lines: List[str] = []
    meta = result.get("metadata", {})
    tables = result.get("tables", [])
    orphan_tables = result.get("orphan_tables", [])
    toc = meta.get("toc_summary", [])

    author = meta.get("author", "Phạm Thanh Hùng")
    copyright_str = meta.get("copyright", "Copyright © 2026 Phạm Thanh Hùng. All Rights Reserved.")

    lines.append(f"# Spatial Sheet Parser — Structured Output")
    lines.append(f"<!-- author=\"{author}\" copyright=\"{copyright_str}\" format={meta.get('source_format','?')} "
                 f"sheet={meta.get('sheet_name') or 'default'} version={meta.get('parser_version','?')} -->")
    lines.append("")

    if toc:
        lines.append("## Table of Contents / Mục lục")
        lines.append("")
        for item in toc:
            lines.append(f"- (Row {item['row'] + 1}) {item['content']}")
        lines.append("")

    def _md_table(t: Dict[str, Any], depth: int) -> None:
        prefix = "#" * (depth + 3)
        tid = t.get("table_id", "")
        title = t.get("title") or "<No Title>"
        level = t.get("level", 0)
        parent = t.get("parent_id") or "null"
        dr = t.get("data_range", {})
        s_row, s_col = dr.get("start_row", 0) + 1, dr.get("start_col", 0) + 1
        e_row, e_col = dr.get("end_row", 0) + 1, dr.get("end_col", 0) + 1
        range_str = f"R{s_row}C{s_col}:R{e_row}C{e_col}"

        is_section = t.get("node_type") == "section" or (len(t.get("records", [])) == 0 and len(t.get("children", [])) > 0)
        children = t.get("children", [])

        if is_section:
            lines.append(f"{prefix} 📁 [SECTION: {tid}] \"{title}\"")
            lines.append(f"<!-- id={tid} type=section level={level} parent={parent} children={len(children)} range={range_str} -->")
            lines.append(f"*📁 Chuyên mục gồm {len(children)} bảng dữ liệu bên dưới:*")
            lines.append("")
            return

        lines.append(f"{prefix} [TABLE: {tid}] \"{title}\"")
        lines.append(f"<!-- id={tid} level={level} parent={parent} range={range_str} -->")
        lines.append("")

        cols = t.get("columns", [])
        records = t.get("records", [])

        if cols:
            # Build markdown table
            header_row = "| " + " | ".join(str(c) for c in cols) + " |"
            sep_row = "| " + " | ".join("---" for _ in cols) + " |"
            lines.append(header_row)
            lines.append(sep_row)
            for rec in records:
                cells = []
                for col in cols:
                    val = rec.get(col, "")
                    if val is None:
                        val = ""
                    # Escape pipe characters in values
                    cells.append(str(val).replace("|", "\\|").replace("\n", " "))
                lines.append("| " + " | ".join(cells) + " |")
            if not records:
                lines.append("| " + " | ".join("—" for _ in cols) + " |")
        else:
            lines.append("_(no columns detected)_")

        lines.append("")

    def _walk(t_dict: Dict[str, Any], table_map: Dict[str, Any], depth: int) -> None:
        _md_table(t_dict, depth)
        for child_id in t_dict.get("children", []):
            if child_id in table_map:
                _walk(table_map[child_id], table_map, depth + 1)

    all_tables = tables + orphan_tables
    if all_tables:
        lines.append("## Detected Tables")
        lines.append("")

        table_map = {t["table_id"]: t for t in tables if "table_id" in t}
        roots = [t for t in tables if t.get("parent_id") is None or t.get("parent_id") not in table_map]
        for r_dict in roots:
            _walk(r_dict, table_map, 0)

        if orphan_tables:
            lines.append("---")
            lines.append("## Orphan Tables (No Parent)")
            lines.append("")
            for ot in orphan_tables:
                _md_table(ot, 0)
    else:
        lines.append("_(No tables detected)_")
        lines.append("")

    unclassified = result.get("unclassified_rows", [])
    if unclassified:
        lines.append("---")
        lines.append("## Unclassified Rows")
        lines.append("")
        lines.append("| Row | Col | Value |")
        lines.append("| --- | --- | ----- |")
        for u in unclassified:
            row_num = u.get("row", 0) + 1
            for cell in u.get("cells", []):
                col_num = cell.get("col", 0) + 1
                val = str(cell.get("value", "")).replace("|", "\\|")
                lines.append(f"| {row_num} | {col_num} | {val} |")
        lines.append("")

    return "\n".join(lines)


def render_preview(result: Dict[str, Any]) -> str:
    """Renders human-readable summary preview of spatial parser result.

    Args:
        result: Result dictionary from SpatialSheetParser.parse_grid().

    Returns:
        Formatted summary string summarizing metadata, tables, hierarchy,
        records, warnings, and unclassified rows.
    """
    lines: List[str] = []
    divider = "=" * 80

    meta = result.get("metadata", {})
    tables = result.get("tables", [])
    orphan_tables = result.get("orphan_tables", [])
    unclassified_rows = result.get("unclassified_rows", [])
    validation = meta.get("validation", {})

    version = meta.get("parser_version", "unknown")
    fmt = meta.get("source_format", "unknown")
    sheet = meta.get("sheet_name") or "None"
    dsr = meta.get("data_start_row", 0)
    global_warnings = meta.get("warnings", [])

    is_valid = validation.get("is_valid", True)
    err_cnt = validation.get("error_count", 0)
    warn_cnt = validation.get("warning_count", 0)
    status_str = "VALID" if is_valid else f"INVALID ({err_cnt} error(s))"

    lines.append(divider)
    lines.append("Spatial Sheet Parser - Preview Summary")
    lines.append(divider)
    lines.append(f"Source Format : {fmt} | Sheet: {sheet} | Data Start Row: {dsr} | Parser: v{version}")
    lines.append(f"Validation    : {status_str} ({warn_cnt} warning(s))")

    toc_summary = meta.get("toc_summary", [])
    if toc_summary:
        lines.append("")
        lines.append("--- Table of Contents (TOC) ---")
        for item in toc_summary:
            r = item.get("row")
            c = item.get("content")
            lines.append(f"  Row {r + 1:3d}: {c}")

    lines.append("")
    lines.append("--- Table Hierarchy & Regions ---")

    def _render_table_node(table: Dict[str, Any], depth: int = 0) -> None:
        indent_str = "  " * depth
        prefix = "└── " if depth > 0 else ""
        tid = table.get("table_id", "")
        title = table.get("title") or "<No Title>"
        level = table.get("level", 0)
        dr = table.get("data_range", {})
        s_row, s_col = dr.get("start_row", 0) + 1, dr.get("start_col", 0) + 1
        e_row, e_col = dr.get("end_row", 0) + 1, dr.get("end_col", 0) + 1
        range_str = f"R{s_row}C{s_col}:R{e_row}C{e_col}"

        hr = table.get("header_row", 0) + 1
        recs = table.get("records", [])
        num_recs = len(recs)
        rsr = table.get("record_start_row", 0) + 1
        rer = table.get("record_end_row", 0) + 1
        rec_range_str = f"Rows {rsr}-{rer}" if num_recs > 0 else "No records"
        conf = table.get("confidence", 1.0)
        cols = table.get("columns", [])
        t_warns = table.get("warnings", [])
        pid = table.get("parent_id")

        is_section = table.get("node_type") == "section" or (num_recs == 0 and len(table.get("children", [])) > 0)
        type_badge = " 📁 [SECTION]" if is_section else ""

        lines.append(f"{indent_str}{prefix}[{tid}]{type_badge} \"{title}\" (Level {level})")
        lines.append(f"{indent_str}    Parent   : {pid if pid else 'None (Root)'}")
        if is_section:
            child_cnt = len(table.get("children", []))
            lines.append(f"{indent_str}    Type     : Category / Section Header ({child_cnt} sub-tables)")
            lines.append(f"{indent_str}    Range    : {range_str}")
        else:
            lines.append(f"{indent_str}    Range    : {range_str} | Anchor: Col {table.get('anchor_column')} | Header: Row {hr}")
            lines.append(f"{indent_str}    Records  : {num_recs} record(s) ({rec_range_str}) | Confidence: {conf:.2f}")
            cols_preview = ", ".join(cols[:5]) + ("..." if len(cols) > 5 else "")
            lines.append(f"{indent_str}    Columns  : [{cols_preview}]")
        if t_warns:
            lines.append(f"{indent_str}    Warnings : {t_warns}")

    if not tables:
        lines.append("  (No hierarchical tables detected)")
    else:
        table_map = {t["table_id"]: t for t in tables if "table_id" in t}
        roots = [t for t in tables if t.get("parent_id") is None or t.get("parent_id") not in table_map]

        def _walk_tree(t_dict: Dict[str, Any], depth: int) -> None:
            _render_table_node(t_dict, depth)
            for child_id in t_dict.get("children", []):
                if child_id in table_map:
                    _walk_tree(table_map[child_id], depth + 1)

        for r_dict in roots:
            _walk_tree(r_dict, depth=0)

    if orphan_tables:
        lines.append("")
        lines.append("--- Orphan Tables ---")
        for ot in orphan_tables:
            _render_table_node(ot, depth=0)

    lines.append("")
    lines.append("--- Summary Statistics ---")
    tot_tables = len(tables) + len(orphan_tables)
    lines.append(f"Total Tables     : {tot_tables} (Hierarchical: {len(tables)}, Orphans: {len(orphan_tables)})")
    lines.append(f"Unclassified Rows: {len(unclassified_rows)}")
    if unclassified_rows:
        u_row_indices = [u.get("row", 0) + 1 for u in unclassified_rows if "row" in u]
        if len(u_row_indices) <= 10:
            lines.append(f"  Unclassified row indices: {u_row_indices}")
        else:
            lines.append(f"  Unclassified row indices: {u_row_indices[:10]}... (+{len(u_row_indices) - 10} more)")

    if global_warnings:
        lines.append(f"Global Warnings  : {global_warnings}")

    lines.append(divider)
    return "\n".join(lines)
