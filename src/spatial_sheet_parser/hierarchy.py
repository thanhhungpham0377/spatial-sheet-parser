"""Hierarchy engine for parent-child relationship resolution and orphan detection."""

from typing import List, Tuple
from spatial_sheet_parser.detection import DetectedTable
from spatial_sheet_parser import warnings


def build_table_hierarchy(tables: List[DetectedTable]) -> Tuple[List[DetectedTable], List[DetectedTable]]:
    """Resolves parent-child relationships and identifies orphan tables.

    Returns:
        (root_tables_and_children, orphan_tables)
    """
    if not tables:
        return [], []

    # Sort tables by spatial row position
    sorted_tables = sorted(tables, key=lambda t: (t.title_cell["row"], t.title_cell["col"]))

    # Active ancestor stack maintaining (table, level)
    active_stack: List[DetectedTable] = []

    root_tables: List[DetectedTable] = []
    orphan_tables: List[DetectedTable] = []

    for table in sorted_tables:
        table_lvl = table.level

        # Pop tables from stack that have level >= current table level
        while active_stack and active_stack[-1].level >= table_lvl:
            active_stack.pop()

        if active_stack:
            parent = active_stack[-1]
            table.parent_id = parent.table_id
            parent.children.append(table.table_id)

            # Check for level skipping (e.g. parent level 0, current level 2)
            if table_lvl > parent.level + 1:
                if warnings.LEVEL_SKIPPED not in table.warnings:
                    table.warnings.append(warnings.LEVEL_SKIPPED)
                    table.confidence = max(0.0, round(table.confidence - 0.15, 2))
        else:
            table.parent_id = None
            is_orphan = False
            if table_lvl == 0:
                is_orphan = False
            elif table_lvl == 1:
                # Level 1 is a valid Top-Level Root Table when there is no Level 0 ancestor,
                # unless explicitly headerless without section role
                if "headerless" in table.title.lower():
                    is_orphan = True
                elif warnings.MISSING_HEADER in table.warnings and not table.children:
                    is_orphan = True
                else:
                    is_orphan = False
            else:
                # Deep level (>= 2) without ancestor is a true orphan table
                is_orphan = True

            if is_orphan:
                if warnings.ORPHAN_TABLE not in table.warnings:
                    table.warnings.append(warnings.ORPHAN_TABLE)
                    table.confidence = max(0.0, round(table.confidence - 0.25, 2))
                orphan_tables.append(table)

        active_stack.append(table)

    # Post-process: identify Section / Category Header nodes (0 data records, has child tables)
    for table in sorted_tables:
        if len(table.records) == 0 and len(table.children) >= 1 and "headerless" not in table.title.lower():
            table.node_type = "section"
            # Section headers are structural containers, not malformed data tables
            table.columns = []
            table.column_details = []
            table.warnings = [w for w in table.warnings if w not in (warnings.MISSING_HEADER, warnings.EMPTY_RECORDS, warnings.ORPHAN_TABLE)]
            table.confidence = 1.0
            if table in orphan_tables:
                orphan_tables.remove(table)
        else:
            table.node_type = "table"

    return sorted_tables, orphan_tables
