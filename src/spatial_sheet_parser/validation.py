"""Validation engine for enforcing product JSON contract integrity."""

import math
from typing import Any, Dict, List, Optional, Set
from spatial_sheet_parser.config import ParserConfig
from spatial_sheet_parser import schema, warnings as warn_taxonomy


VALID_WARNING_CODES = {
    warn_taxonomy.AMBIGUOUS_TABLE_TITLE,
    warn_taxonomy.MISSING_HEADER,
    warn_taxonomy.EMPTY_RECORDS,
    warn_taxonomy.DUPLICATE_HEADER,
    warn_taxonomy.LEVEL_SKIPPED,
    warn_taxonomy.ORPHAN_TABLE,
    warn_taxonomy.UNEXPECTED_BLANK_ROW,
    warn_taxonomy.POSSIBLE_FOOTER,
    warn_taxonomy.MERGED_CELL_DETECTED,
    warn_taxonomy.TRUNCATED_TABLE,
    warn_taxonomy.UNCLASSIFIED_DATA,
}


class OutputValidator:
    """Evaluates spatial spreadsheet parser output against JSON contract specifications."""

    def __init__(self, config: Optional[ParserConfig] = None) -> None:
        self.config = config or ParserConfig()

    def validate(self, output: Any) -> schema.ValidationResult:
        """Validates the parser output dictionary.

        Args:
            output: Dictionary returned by SpatialSheetParser.parse_grid() or deserialized JSON.

        Returns:
            schema.ValidationResult containing validation status, errors, and warnings.
        """
        result = schema.ValidationResult()

        if not isinstance(output, dict):
            result.add_error(
                code=schema.ERR_INVALID_METADATA_FIELD,
                path="$",
                message="Parser output root must be a dictionary object",
                context={"actual_type": type(output).__name__},
            )
            return result

        # 1. Validate top-level contract keys
        for required_key in ["metadata", "tables", "orphan_tables", "unclassified_rows"]:
            if required_key not in output:
                result.add_error(
                    code=schema.ERR_MISSING_METADATA if required_key == "metadata" else schema.ERR_MISSING_TABLE_FIELD,
                    path=f"$.{required_key}",
                    message=f"Missing top-level contract field: '{required_key}'",
                )

        if not result.is_valid and "metadata" not in output:
            return result

        # 2. Validate metadata
        meta = output.get("metadata", {})
        self._validate_metadata(meta, result)

        # 3. Validate tables and orphan tables
        tables = output.get("tables", [])
        orphan_tables = output.get("orphan_tables", [])

        if not isinstance(tables, list):
            result.add_error(
                code=schema.ERR_INVALID_TABLE_FIELD,
                path="$.tables",
                message="Field 'tables' must be a list of table objects",
            )
            tables = []

        if not isinstance(orphan_tables, list):
            result.add_error(
                code=schema.ERR_INVALID_TABLE_FIELD,
                path="$.orphan_tables",
                message="Field 'orphan_tables' must be a list of table objects",
            )
            orphan_tables = []

        all_table_objs: List[Tuple[str, int, Dict[str, Any]]] = []  # (path, list_idx, table_dict)

        for idx, t in enumerate(tables):
            path = f"$.tables[{idx}]"
            self._validate_single_table(t, path, is_orphan=False, result=result)
            if isinstance(t, dict):
                all_table_objs.append((path, idx, t))

        for idx, ot in enumerate(orphan_tables):
            path = f"$.orphan_tables[{idx}]"
            self._validate_single_table(ot, path, is_orphan=True, result=result)
            if isinstance(ot, dict):
                all_table_objs.append((path, idx, ot))

        # 4. Validate hierarchy consistency across all tables
        self._validate_hierarchy(all_table_objs, result)

        # 5. Validate unclassified rows
        unclassified = output.get("unclassified_rows", [])
        self._validate_unclassified_rows(unclassified, meta.get("data_start_row", 0), result)

        return result

    def _validate_metadata(self, meta: Any, result: schema.ValidationResult) -> None:
        if not isinstance(meta, dict):
            result.add_error(
                code=schema.ERR_INVALID_METADATA_FIELD,
                path="$.metadata",
                message="Metadata field must be a dictionary",
            )
            return

        # parser_version
        pv = meta.get("parser_version")
        if not isinstance(pv, str) or not pv.strip():
            result.add_error(
                code=schema.ERR_INVALID_METADATA_FIELD,
                path="$.metadata.parser_version",
                message="Field 'parser_version' must be a non-empty string",
                context={"value": pv},
            )

        # source_format
        sf = meta.get("source_format")
        if not isinstance(sf, str) or not sf.strip():
            result.add_error(
                code=schema.ERR_INVALID_METADATA_FIELD,
                path="$.metadata.source_format",
                message="Field 'source_format' must be a non-empty string",
                context={"value": sf},
            )

        # sheet_name
        sn = meta.get("sheet_name")
        if sn is not None and not isinstance(sn, str):
            result.add_error(
                code=schema.ERR_INVALID_METADATA_FIELD,
                path="$.metadata.sheet_name",
                message="Field 'sheet_name' must be string or None",
                context={"value": sn},
            )

        # toc_summary
        toc = meta.get("toc_summary")
        if not isinstance(toc, list):
            result.add_error(
                code=schema.ERR_INVALID_METADATA_FIELD,
                path="$.metadata.toc_summary",
                message="Field 'toc_summary' must be a list of TOC objects",
            )
        else:
            for idx, item in enumerate(toc):
                if not isinstance(item, dict) or "row" not in item or "content" not in item:
                    result.add_error(
                        code=schema.ERR_INVALID_METADATA_FIELD,
                        path=f"$.metadata.toc_summary[{idx}]",
                        message="TOC item must be a dictionary with 'row' and 'content' keys",
                    )

        # data_start_row
        dsr = meta.get("data_start_row")
        if not isinstance(dsr, int) or isinstance(dsr, bool) or dsr < 0:
            result.add_error(
                code=schema.ERR_INVALID_METADATA_FIELD,
                path="$.metadata.data_start_row",
                message="Field 'data_start_row' must be an integer >= 0",
                context={"value": dsr},
            )

        # warnings
        warns = meta.get("warnings")
        if not isinstance(warns, list):
            result.add_error(
                code=schema.ERR_INVALID_METADATA_FIELD,
                path="$.metadata.warnings",
                message="Field 'warnings' in metadata must be a list",
            )
        else:
            for idx, w in enumerate(warns):
                if not isinstance(w, str):
                    result.add_error(
                        code=schema.ERR_INVALID_METADATA_FIELD,
                        path=f"$.metadata.warnings[{idx}]",
                        message="Metadata warning item must be a string",
                    )

    def _validate_single_table(
        self,
        table: Any,
        path: str,
        is_orphan: bool,
        result: schema.ValidationResult,
    ) -> None:
        if not isinstance(table, dict):
            result.add_error(
                code=schema.ERR_INVALID_TABLE_FIELD,
                path=path,
                message="Table object must be a dictionary",
            )
            return

        required_fields = [
            "table_id", "title", "level", "parent_id", "title_cell",
            "anchor_column", "data_range", "header_row", "record_start_row",
            "record_end_row", "columns", "records", "children", "confidence", "warnings"
        ]

        for rf in required_fields:
            if rf not in table:
                result.add_error(
                    code=schema.ERR_MISSING_TABLE_FIELD,
                    path=f"{path}.{rf}",
                    message=f"Missing table required field: '{rf}'",
                )

        # 1. Check confidence bounds [0.0, 1.0]
        conf = table.get("confidence")
        if not isinstance(conf, (int, float)) or isinstance(conf, bool) or math.isnan(conf) or math.isinf(conf):
            result.add_error(
                code=schema.ERR_CONFIDENCE_OUT_OF_BOUNDS,
                path=f"{path}.confidence",
                message="Field 'confidence' must be a valid numeric value between 0.0 and 1.0",
                context={"value": conf},
            )
        elif not (0.0 <= conf <= 1.0):
            result.add_error(
                code=schema.ERR_CONFIDENCE_OUT_OF_BOUNDS,
                path=f"{path}.confidence",
                message=f"Field 'confidence' value {conf} is out of bounds [0.0, 1.0]",
                context={"value": conf},
            )

        # 2. Check title_cell and spatial coordinates
        tc = table.get("title_cell")
        lvl = table.get("level")
        dr = table.get("data_range")
        anchor = table.get("anchor_column")
        hr = table.get("header_row")
        rsr = table.get("record_start_row")
        rer = table.get("record_end_row")

        if isinstance(tc, dict) and "row" in tc and "col" in tc:
            t_row, t_col = tc["row"], tc["col"]
            if isinstance(lvl, int) and t_col != lvl:
                result.add_error(
                    code=schema.ERR_INVALID_COORDINATES,
                    path=f"{path}.level",
                    message=f"Table level ({lvl}) does not match title_cell col ({t_col})",
                    context={"level": lvl, "title_cell_col": t_col},
                )

            if isinstance(dr, dict) and "start_row" in dr:
                if t_row != dr["start_row"]:
                    result.add_error(
                        code=schema.ERR_INVALID_COORDINATES,
                        path=f"{path}.title_cell",
                        message=f"title_cell row ({t_row}) does not match data_range start_row ({dr['start_row']})",
                        context={"title_cell_row": t_row, "data_range_start_row": dr.get("start_row")},
                    )

        # 3. Check data_range bounds
        if isinstance(dr, dict):
            s_row = dr.get("start_row")
            s_col = dr.get("start_col")
            e_row = dr.get("end_row")
            e_col = dr.get("end_col")

            if any(not isinstance(v, int) or isinstance(v, bool) or v < 0 for v in [s_row, s_col, e_row, e_col] if v is not None):
                result.add_error(
                    code=schema.ERR_INVALID_COORDINATES,
                    path=f"{path}.data_range",
                    message="All data_range coordinates must be integers >= 0",
                    context={"data_range": dr},
                )
            else:
                if s_row is not None and e_row is not None and s_row > e_row:
                    result.add_error(
                        code=schema.ERR_INVALID_COORDINATES,
                        path=f"{path}.data_range",
                        message=f"data_range start_row ({s_row}) is greater than end_row ({e_row})",
                        context={"data_range": dr},
                    )
                if s_col is not None and e_col is not None and s_col > e_col:
                    result.add_error(
                        code=schema.ERR_INVALID_COORDINATES,
                        path=f"{path}.data_range",
                        message=f"data_range start_col ({s_col}) is greater than end_col ({e_col})",
                        context={"data_range": dr},
                    )
                if s_col is not None and e_col is not None and isinstance(anchor, int) and not (s_col <= anchor <= e_col):
                    result.add_error(
                        code=schema.ERR_INVALID_COORDINATES,
                        path=f"{path}.anchor_column",
                        message=f"anchor_column ({anchor}) is outside data_range column bounds [{s_col}, {e_col}]",
                        context={"anchor_column": anchor, "data_range": dr},
                    )

                if isinstance(hr, int) and s_row is not None and hr < s_row:
                    result.add_error(
                        code=schema.ERR_INVALID_COORDINATES,
                        path=f"{path}.header_row",
                        message=f"header_row ({hr}) is before data_range start_row ({s_row})",
                    )

                if isinstance(hr, int) and isinstance(rsr, int) and rsr < hr:
                    result.add_error(
                        code=schema.ERR_INVALID_COORDINATES,
                        path=f"{path}.record_start_row",
                        message=f"record_start_row ({rsr}) is before header_row ({hr})",
                    )

                records = table.get("records", [])
                if isinstance(records, list) and len(records) > 0:
                    if isinstance(rsr, int) and isinstance(rer, int) and rsr > rer:
                        result.add_error(
                            code=schema.ERR_INVALID_COORDINATES,
                            path=f"{path}.record_end_row",
                            message=f"record_end_row ({rer}) is before record_start_row ({rsr}) when records exist",
                        )
                    if isinstance(rer, int) and e_row is not None and rer > e_row:
                        result.add_error(
                            code=schema.ERR_INVALID_COORDINATES,
                            path=f"{path}.record_end_row",
                            message=f"record_end_row ({rer}) exceeds data_range end_row ({e_row})",
                        )

        # 4. Check stable unique column keys and record shape
        cols = table.get("columns")
        if not isinstance(cols, list):
            result.add_error(
                code=schema.ERR_INVALID_TABLE_FIELD,
                path=f"{path}.columns",
                message="Field 'columns' must be a list of column key strings",
            )
        else:
            seen_cols: Set[str] = set()
            for c_idx, col_key in enumerate(cols):
                if not isinstance(col_key, str):
                    result.add_error(
                        code=schema.ERR_INVALID_TABLE_FIELD,
                        path=f"{path}.columns[{c_idx}]",
                        message="Column key must be a string",
                    )
                elif col_key in seen_cols:
                    result.add_error(
                        code=schema.ERR_DUPLICATE_COLUMN_KEY,
                        path=f"{path}.columns[{c_idx}]",
                        message=f"Duplicate column key '{col_key}' found in table columns definition",
                        context={"column_key": col_key},
                    )
                else:
                    seen_cols.add(col_key)

            recs = table.get("records")
            if not isinstance(recs, list):
                result.add_error(
                    code=schema.ERR_INVALID_TABLE_FIELD,
                    path=f"{path}.records",
                    message="Field 'records' must be a list of record objects",
                )
            else:
                expected_keys = set(cols)
                for r_idx, rec in enumerate(recs):
                    if not isinstance(rec, dict):
                        result.add_error(
                            code=schema.ERR_INVALID_TABLE_FIELD,
                            path=f"{path}.records[{r_idx}]",
                            message="Record must be a dictionary",
                        )
                    else:
                        rec_keys = set(rec.keys())
                        if rec_keys != expected_keys:
                            diff_missing = list(expected_keys - rec_keys)
                            diff_extra = list(rec_keys - expected_keys)
                            result.add_error(
                                code=schema.ERR_RECORD_KEY_MISMATCH,
                                path=f"{path}.records[{r_idx}]",
                                message=f"Record shape mismatch against columns. Missing keys: {diff_missing}, Unexpected keys: {diff_extra}",
                                context={
                                    "record_index": r_idx,
                                    "missing_keys": diff_missing,
                                    "unexpected_keys": diff_extra,
                                },
                            )

        # 5. Check orphan rules
        if is_orphan:
            pid = table.get("parent_id")
            if pid is not None:
                result.add_error(
                    code=schema.ERR_ORPHAN_HAS_PARENT,
                    path=f"{path}.parent_id",
                    message=f"Orphan table cannot have a parent_id (found '{pid}')",
                    context={"parent_id": pid},
                )
            if isinstance(lvl, int) and lvl == 0:
                result.add_warning(
                    code="ORPHAN_LEVEL_ZERO",
                    path=f"{path}.level",
                    message="Orphan table has level 0; typically root tables at level 0 are not orphans",
                )

    def _validate_hierarchy(
        self,
        table_objs: List[Tuple[str, int, Dict[str, Any]]],
        result: schema.ValidationResult,
    ) -> None:
        table_map: Dict[str, Tuple[str, Dict[str, Any]]] = {}
        seen_ids: Set[str] = set()

        for path, _, t_dict in table_objs:
            tid = t_dict.get("table_id")
            if not isinstance(tid, str) or not tid.strip():
                continue
            if tid in seen_ids:
                result.add_error(
                    code=schema.ERR_DUPLICATE_TABLE_ID,
                    path=f"{path}.table_id",
                    message=f"Duplicate table_id '{tid}' detected",
                    context={"table_id": tid},
                )
            else:
                seen_ids.add(tid)
                table_map[tid] = (path, t_dict)

        # Check children & parent links
        for tid, (path, t_dict) in table_map.items():
            pid = t_dict.get("parent_id")
            children = t_dict.get("children", [])

            if pid is not None:
                if pid not in table_map:
                    result.add_error(
                        code=schema.ERR_HIERARCHY_MISSING_PARENT,
                        path=f"{path}.parent_id",
                        message=f"Table '{tid}' references non-existent parent_id '{pid}'",
                        context={"table_id": tid, "parent_id": pid},
                    )
                else:
                    _, parent_dict = table_map[pid]
                    p_children = parent_dict.get("children", [])
                    if tid not in p_children:
                        result.add_error(
                            code=schema.ERR_HIERARCHY_MISSING_CHILD,
                            path=f"{path}.parent_id",
                            message=f"Table '{tid}' specifies parent '{pid}', but parent does not list '{tid}' in children",
                            context={"child_id": tid, "parent_id": pid},
                        )

            if isinstance(children, list):
                for c_idx, child_id in enumerate(children):
                    if child_id not in table_map:
                        result.add_error(
                            code=schema.ERR_HIERARCHY_MISSING_CHILD,
                            path=f"{path}.children[{c_idx}]",
                            message=f"Table '{tid}' lists non-existent child_id '{child_id}'",
                            context={"parent_id": tid, "child_id": child_id},
                        )
                    else:
                        _, child_dict = table_map[child_id]
                        c_pid = child_dict.get("parent_id")
                        if c_pid != tid:
                            result.add_error(
                                code=schema.ERR_HIERARCHY_CHILD_PARENT_MISMATCH,
                                path=f"{path}.children[{c_idx}]",
                                message=f"Table '{tid}' lists child '{child_id}', but child specifies parent_id '{c_pid}'",
                                context={"parent_id": tid, "child_id": child_id, "actual_parent_id": c_pid},
                            )

        # Cycle detection
        for tid, (path, t_dict) in table_map.items():
            visited: Set[str] = set()
            curr = tid
            while curr is not None and curr in table_map:
                if curr in visited:
                    result.add_error(
                        code=schema.ERR_HIERARCHY_CYCLE_DETECTED,
                        path=f"{path}.parent_id",
                        message=f"Hierarchy cycle detected involving table '{curr}'",
                        context={"table_id": tid, "cycle_table": curr},
                    )
                    break
                visited.add(curr)
                _, curr_dict = table_map[curr]
                curr = curr_dict.get("parent_id")

    def _validate_unclassified_rows(
        self,
        unclassified: Any,
        data_start_row: int,
        result: schema.ValidationResult,
    ) -> None:
        if not isinstance(unclassified, list):
            result.add_error(
                code=schema.ERR_UNCLASSIFIED_ROW_MALFORMED,
                path="$.unclassified_rows",
                message="Field 'unclassified_rows' must be a list of row objects",
            )
            return

        for idx, u_row in enumerate(unclassified):
            path = f"$.unclassified_rows[{idx}]"
            if not isinstance(u_row, dict):
                result.add_error(
                    code=schema.ERR_UNCLASSIFIED_ROW_MALFORMED,
                    path=path,
                    message="Unclassified row item must be a dictionary",
                )
                continue

            r_idx = u_row.get("row")
            cells = u_row.get("cells")

            if not isinstance(r_idx, int) or isinstance(r_idx, bool) or r_idx < data_start_row:
                result.add_error(
                    code=schema.ERR_UNCLASSIFIED_ROW_MALFORMED,
                    path=f"{path}.row",
                    message=f"Unclassified row index ({r_idx}) must be integer >= data_start_row ({data_start_row})",
                )

            if not isinstance(cells, list) or len(cells) == 0:
                result.add_error(
                    code=schema.ERR_UNCLASSIFIED_ROW_MALFORMED,
                    path=f"{path}.cells",
                    message="Unclassified row must contain non-empty 'cells' list",
                )
            else:
                for c_idx, cell in enumerate(cells):
                    if not isinstance(cell, dict) or "col" not in cell or "value" not in cell:
                        result.add_error(
                            code=schema.ERR_UNCLASSIFIED_ROW_MALFORMED,
                            path=f"{path}.cells[{c_idx}]",
                            message="Unclassified cell must be a dictionary with 'col' and 'value'",
                        )


def validate_parse_output(
    output: Any,
    config: Optional[ParserConfig] = None,
) -> schema.ValidationResult:
    """Helper function to validate parser JSON contract output."""
    validator = OutputValidator(config=config)
    return validator.validate(output)
