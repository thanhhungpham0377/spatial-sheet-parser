"""Detection engine for TOC, data markers, table candidates, headers, and boundaries."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from spatial_sheet_parser.config import ParserConfig
from spatial_sheet_parser.grid import Cell, Grid
from spatial_sheet_parser import warnings


SAFE_TITLE_PREFIXES = (
    "tổng hợp", "tổng quan", "tổng kết", "tổng chi phí",
    "bảng tổng", "báo cáo tổng", "tổng mức",
)

EXCLUSION_KEYWORDS = [
    "tổng cộng", "tổng số", "subtotal", "total", "ghi chú", "note",
    "người lập", "người duyệt", "ngày lập", "footer", "summary",
]

COLUMN_HEADER_EXCLUSIONS = {
    "stt", "số tt", "no", "no.", "stt.", "stt/no", "stt / no", "mã", "id"
}

# Keywords that identify a cell as a numeric sequence index (not a table title)
NUMERIC_INDEX_PATTERN = re.compile(
    r"^\s*(\d+(\.\d+)?|[ivxlcdmIVXLCDM]+\.?)\s*$"
)

# Max rows to look up above a header to find a linked single-cell title
TITLE_LOOKUP_ROWS_ABOVE = 4


@dataclass
class DetectedTable:
    """Internal structure representing a detected table candidate before hierarchy resolution."""

    table_id: str
    title: str
    level: int
    parent_id: Optional[str]
    title_cell: Dict[str, int]
    anchor_column: int
    data_range: Dict[str, int]
    header_row: int
    record_start_row: int
    record_end_row: int
    columns: List[str]
    records: List[Dict[str, Any]]
    column_details: List[Dict[str, Any]] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    confidence: float = 1.0
    warnings: List[str] = field(default_factory=list)
    classified_cells: Set[Tuple[int, int]] = field(default_factory=set)
    node_type: str = "table"


class RegionDetector:
    """Detects TOC regions and explicit markers in the grid matrix."""

    def __init__(self, config: ParserConfig) -> None:
        self.config = config

    def detect_preamble_and_markers(self, grid: Grid) -> Tuple[int, List[Dict[str, Any]], List[str]]:
        """Scans grid for explicit markers like [BEGIN DATA] and extracts TOC summary.

        Also auto-detects preamble outline blocks (e.g. B3:C22 multi-level TOC)
        when no explicit [BEGIN DATA] marker is present.

        Returns:
            (data_start_row, toc_summary, global_warnings)
        """
        data_start_row = 0
        toc_summary: List[Dict[str, Any]] = []
        global_warnings: List[str] = []

        begin_data_row: Optional[int] = None

        for r_idx in range(grid.num_rows):
            row_cells = grid.get_row_cells(r_idx)
            for cell in row_cells:
                if not cell.is_empty and isinstance(cell.value, str):
                    val_upper = cell.value.strip().upper()
                    if "[BEGIN DATA]" in val_upper:
                        begin_data_row = r_idx
                        break
            if begin_data_row is not None:
                break

        if begin_data_row is not None:
            data_start_row = begin_data_row + 1
            for r_idx in range(begin_data_row):
                row_cells = grid.get_row_cells(r_idx)
                non_empty = [c for c in row_cells if not c.is_empty]
                if non_empty:
                    content_str = " | ".join(c.display_value for c in non_empty)
                    toc_summary.append({
                        "row": r_idx,
                        "content": content_str,
                    })
        else:
            # Auto-detect preamble outline block: consecutive rows near top
            # where each row has only 1-2 cells in low columns (col 0..4),
            # and no multi-column data rows yet.
            preamble_end = self._detect_preamble_outline_end(grid)
            if preamble_end > 0:
                data_start_row = 0  # Data parsing still starts from row 0; preamble cells get classified by TOC
                for r_idx in range(preamble_end):
                    row_cells = grid.get_row_cells(r_idx)
                    non_empty = [c for c in row_cells if not c.is_empty]
                    if non_empty and len(non_empty) <= 2:
                        content_str = " | ".join(c.display_value for c in non_empty)
                        toc_summary.append({
                            "row": r_idx,
                            "content": content_str,
                        })

        if grid.has_merged_cells and self.config.merged_cell_policy == "top_left_only":
            global_warnings.append(warnings.MERGED_CELL_DETECTED)

        return data_start_row, toc_summary, global_warnings

    def _detect_preamble_outline_end(self, grid: Grid) -> int:
        """Detect end row of an auto-detected preamble/outline/TOC block at top of sheet.

        A preamble block is a contiguous set of rows near the top where every
        non-empty row has only 1-2 cells occupying low-index columns (0..4).
        As soon as we hit a row with 3+ non-empty cells, the preamble ends.

        Returns the exclusive end row (i.e., first row NOT in preamble), or 0 if
        no preamble detected.
        """
        # If the grid starts immediately with a table title + header row, there is no preamble
        if grid.num_rows >= 2:
            r0_cells = [c for c in grid.get_row_cells(0) if not c.is_empty]
            r1_cells = [c for c in grid.get_row_cells(1) if not c.is_empty]
            if len(r0_cells) == 1 and len(r1_cells) >= 2:
                # Row 0 is title, Row 1 is multi-column header -> immediate data table!
                return 0

        max_preamble_scan = min(50, grid.num_rows)
        preamble_end = 0
        preamble_non_empty_count = 0

        for r_idx in range(max_preamble_scan):
            row_cells = grid.get_row_cells(r_idx)
            non_empty = [c for c in row_cells if not c.is_empty]

            if not non_empty:
                # Blank row: allowed in preamble if already in a multi-row outline
                if preamble_non_empty_count > 0:
                    next_r = r_idx + 1
                    if next_r < grid.num_rows:
                        next_non_empty = [c for c in grid.get_row_cells(next_r) if not c.is_empty]
                        if len(next_non_empty) >= 3:
                            # Next row is a data header, end preamble here
                            break
                continue

            if len(non_empty) <= 2:
                all_low_col = all(c.col < 5 for c in non_empty)
                if all_low_col:
                    preamble_non_empty_count += 1
                    preamble_end = r_idx + 1
                    continue

            # Row has 3+ cells or high-col cells -> preamble ends here
            break

        # A true preamble outline / TOC block must have at least 8 items
        # (standalone notes or small tables with <= 7 rows are not TOC preambles)
        return preamble_end if preamble_non_empty_count >= 8 else 0


class TableCandidateDetector:
    """Detects table candidates, headers, record boundaries, and raw value retention."""

    def __init__(self, config: ParserConfig) -> None:
        self.config = config

    def is_exclusion_title(self, text: str) -> bool:
        norm = text.strip().lower()
        if norm in COLUMN_HEADER_EXCLUSIONS:
            return True
        if any(norm.startswith(p) or f" {p}" in norm or f": {p}" in norm for p in SAFE_TITLE_PREFIXES):
            return False
        if norm in ("tổng", "total", "tổng:", "total:"):
            return True
        for kw in EXCLUSION_KEYWORDS:
            if kw in norm:
                return True
        return False

    def _is_numeric_index(self, text: str) -> bool:
        """Returns True if text looks like a numeric sequence index (1, 2, 1.0, i, ii...)."""
        return bool(NUMERIC_INDEX_PATTERN.match(str(text).strip()))

    def clean_title(self, text: str) -> str:
        res = text.strip()
        for marker in self.config.explicit_markers:
            if marker in res:
                res = res.replace(marker, "").strip()
        return res

    def _has_header_at_row(self, grid: Grid, row_idx: int, anchor_col: int) -> bool:
        """Checks if row_idx contains non-empty header cells at or after anchor_col."""
        if not (0 <= row_idx < grid.num_rows):
            return False
        for c in range(anchor_col, grid.num_cols):
            cell = grid.get_cell(row_idx, c)
            if cell and not cell.is_empty:
                return True
        return False

    def _is_child_title_row(self, grid: Grid, row_idx: int, child_title_col: int) -> bool:
        """Determines if row_idx is a child table title row rather than a header row."""
        if not (0 <= row_idx < grid.num_rows):
            return False
        title_cell = grid.get_cell(row_idx, child_title_col)
        if not title_cell or title_cell.is_empty or self.is_exclusion_title(title_cell.display_value):
            return False

        for c in range(child_title_col + 1, grid.num_cols):
            chk = grid.get_cell(row_idx, c)
            if chk and not chk.is_empty:
                return False

        child_anchor = child_title_col + self.config.table_offset
        return self._has_header_at_row(grid, row_idx + 1, child_anchor)

    def _find_title_above_header(
        self, grid: Grid, header_row: int, anchor_col: int, candidate_col: int
    ) -> Tuple[Optional[str], Optional[Dict[str, int]]]:
        """Look up 1..TITLE_LOOKUP_ROWS_ABOVE rows above header_row for a single-cell title.

        A single-cell title is a row where:
        - Exactly one cell is non-empty
        - That cell is in a low column (col <= candidate_col + 1)
        - The cell is NOT an exclusion keyword and NOT a pure numeric index

        Returns (title_text, title_cell_dict) or (None, None).
        """
        for offset in range(1, TITLE_LOOKUP_ROWS_ABOVE + 1):
            lookup_row = header_row - offset
            if lookup_row < 0:
                break
            row_cells = grid.get_row_cells(lookup_row)
            non_empty = [c for c in row_cells if not c.is_empty]

            if len(non_empty) == 1:
                cell = non_empty[0]
                if cell.col <= min(candidate_col + 1, 4):
                    text = cell.display_value.strip()
                    if text and not self.is_exclusion_title(text) and not self._is_numeric_index(text):
                        return self.clean_title(text), {"row": lookup_row, "col": cell.col}
            elif len(non_empty) == 0:
                # blank row, keep looking up
                continue
            else:
                # Multiple cells in lookback row → not a simple title row
                break

        return None, None

    def detect_tables(self, grid: Grid, data_start_row: int) -> List[DetectedTable]:
        detected_tables: List[DetectedTable] = []
        tbl_counter = 1

        r = data_start_row
        # Track rows already classified as title rows by a table found below them
        pre_classified_title_rows: Set[int] = set()

        while r < grid.num_rows:
            if grid.is_empty_row(r):
                r += 1
                continue

            row_cells = grid.get_row_cells(r)
            if any("[BEGIN DATA]" in c.display_value.upper() for c in row_cells if not c.is_empty):
                r += 1
                continue

            # Skip rows that were already consumed as linked titles for a table below
            if r in pre_classified_title_rows:
                r += 1
                continue

            candidate_col: Optional[int] = None
            candidate_cell: Optional[Cell] = None

            for col_idx in self.config.title_columns:
                cell = grid.get_cell(r, col_idx)
                if cell and not cell.is_empty:
                    cell_text = cell.display_value
                    if self.is_exclusion_title(cell_text):
                        continue

                    if any(not grid.is_empty_cell(r, prev_c) for prev_c in range(col_idx)):
                        continue

                    other_data_cells = [
                        c for c in row_cells
                        if not c.is_empty
                        and c.col != col_idx
                        and not str(c.value).strip().lower().startswith(("http://", "https://", "www."))
                    ]
                    has_table_marker = "[TABLE]" in cell_text.upper()
                    if other_data_cells and not has_table_marker:
                        # A row with multiple non-empty data cells is a data/header row, NOT a single-cell title
                        continue

                    anchor_c = col_idx + self.config.table_offset
                    has_header = self._has_header_at_row(grid, r + 1, anchor_c)
                    has_child_title = self._is_child_title_row(grid, r + 1, col_idx + 1)
                    if not has_child_title and r + 2 < grid.num_rows and grid.is_empty_row(r + 1):
                        has_child_title = self._is_child_title_row(grid, r + 2, col_idx + 1)

                    if has_header or has_table_marker or has_child_title:
                        candidate_col = col_idx
                        candidate_cell = cell
                        break

            if candidate_col is None or candidate_cell is None:
                # --- NEW: Check if this row is a multi-column header row (no title row directly above) ---
                # Look for rows with 3+ non-empty cells where current row wasn't detected as title
                non_empty_current = [c for c in row_cells if not c.is_empty]
                if len(non_empty_current) >= 3:
                    # Find the minimum column occupied
                    min_col = min(c.col for c in non_empty_current)
                    # Check: is ALL content string-like (not numeric)? Suggests a header row
                    str_vals = [c for c in non_empty_current
                                if isinstance(c.value, str) and not self._is_numeric_index(c.value)]
                    if len(str_vals) >= 2 and min_col <= 4:
                        # Try to find a title in the rows above
                        title_above, title_cell_dict = self._find_title_above_header(
                            grid, r, min_col, min_col
                        )
                        if title_above and title_cell_dict:
                            # We found a linkable header row! Treat r as header_row
                            # and build a table from it.
                            anchor_col_new = min_col
                            header_row_idx = r
                            candidate_title_row = title_cell_dict["row"]

                            table_warnings: List[str] = []
                            classified_cells: Set[Tuple[int, int]] = set()

                            # Mark title cell as classified
                            classified_cells.add((title_cell_dict["row"], title_cell_dict["col"]))
                            pre_classified_title_rows.add(title_cell_dict["row"])

                            # Parse header columns
                            columns: List[str] = []
                            column_details: List[Dict[str, Any]] = []
                            col_end_idx = anchor_col_new
                            seen_headers: Dict[str, int] = {}

                            for c_idx in range(anchor_col_new, grid.num_cols):
                                h_cell = grid.get_cell(header_row_idx, c_idx)
                                if h_cell and not h_cell.is_empty:
                                    classified_cells.add((header_row_idx, c_idx))
                                    h_label = h_cell.display_value
                                    col_end_idx = c_idx
                                    if h_label in seen_headers:
                                        seen_headers[h_label] += 1
                                        unique_label = f"{h_label}_{seen_headers[h_label]}"
                                        if warnings.DUPLICATE_HEADER not in table_warnings:
                                            table_warnings.append(warnings.DUPLICATE_HEADER)
                                    else:
                                        seen_headers[h_label] = 1
                                        unique_label = h_label
                                    columns.append(unique_label)
                                    column_details.append({
                                        "key": unique_label,
                                        "label": h_label,
                                        "col_index": c_idx,
                                    })
                                else:
                                    if columns:
                                        subsequent = any(not grid.is_empty_cell(header_row_idx, c) for c in range(c_idx + 1, grid.num_cols))
                                        if not subsequent:
                                            break
                                        else:
                                            fallback_key = f"Col_{c_idx}"
                                            columns.append(fallback_key)
                                            column_details.append({"key": fallback_key, "label": "", "col_index": c_idx})
                                            col_end_idx = max(col_end_idx, c_idx)
                                    else:
                                        continue

                            if not columns:
                                r += 1
                                continue

                            table_id = f"tbl_{tbl_counter:03d}"
                            tbl_counter += 1

                            # Parse records starting from row after header
                            record_start_row = header_row_idx + 1
                            records: List[Dict[str, Any]] = []
                            curr_record_row = record_start_row
                            consecutive_blanks = 0
                            last_record_row = record_start_row - 1

                            while curr_record_row < grid.num_rows:
                                r_cells = grid.get_row_cells(curr_record_row)
                                if any("[BEGIN DATA]" in c.display_value.upper() or "[TABLE]" in c.display_value.upper() for c in r_cells if not c.is_empty):
                                    break

                                if grid.is_empty_row(curr_record_row):
                                    consecutive_blanks += 1
                                    if consecutive_blanks > self.config.max_blank_rows:
                                        break
                                    table_warnings.append(warnings.UNEXPECTED_BLANK_ROW)
                                    curr_record_row += 1
                                    continue

                                consecutive_blanks = 0

                                # Check for new title (breaks table boundary)
                                is_new_title = False
                                for t_col in self.config.title_columns:
                                    t_cell = grid.get_cell(curr_record_row, t_col)
                                    if t_cell and not t_cell.is_empty:
                                        t_text = t_cell.display_value
                                        if not self.is_exclusion_title(t_text) and not self._is_numeric_index(t_text):
                                            if any(not grid.is_empty_cell(curr_record_row, prev_c) for prev_c in range(t_col)):
                                                continue
                                            if t_col < anchor_col_new:
                                                is_new_title = True
                                                break
                                            else:
                                                if self._is_child_title_row(grid, curr_record_row, t_col) or "[TABLE]" in t_text.upper():
                                                    is_new_title = True
                                                    break

                                if is_new_title:
                                    break

                                rec_dict: Dict[str, Any] = {}
                                for idx, col_name in enumerate(columns):
                                    c_pos = anchor_col_new + idx
                                    cell_val = grid.get_value(curr_record_row, c_pos)
                                    rec_dict[col_name] = cell_val
                                    if not grid.is_empty_cell(curr_record_row, c_pos):
                                        classified_cells.add((curr_record_row, c_pos))
                                        col_end_idx = max(col_end_idx, c_pos)

                                records.append(rec_dict)
                                last_record_row = curr_record_row
                                curr_record_row += 1

                            record_end_row = max(record_start_row, last_record_row)

                            if not records and warnings.MISSING_HEADER not in table_warnings:
                                table_warnings.append(warnings.EMPTY_RECORDS)

                            dedup_warnings = list(dict.fromkeys(table_warnings))
                            confidence = 1.0
                            if warnings.AMBIGUOUS_TABLE_TITLE in dedup_warnings:
                                confidence -= 0.4
                            if warnings.MISSING_HEADER in dedup_warnings:
                                confidence -= 0.3
                            if warnings.EMPTY_RECORDS in dedup_warnings:
                                confidence -= 0.2
                            if warnings.UNEXPECTED_BLANK_ROW in dedup_warnings:
                                confidence -= 0.1
                            confidence = max(0.0, min(1.0, round(confidence, 2)))

                            data_range = {
                                "start_row": candidate_title_row,
                                "start_col": title_cell_dict["col"],
                                "end_row": record_end_row if record_end_row >= candidate_title_row else header_row_idx,
                                "end_col": col_end_idx,
                            }

                            table_obj = DetectedTable(
                                table_id=table_id,
                                title=title_above,
                                level=title_cell_dict["col"],
                                parent_id=None,
                                title_cell=title_cell_dict,
                                anchor_column=anchor_col_new,
                                data_range=data_range,
                                header_row=header_row_idx,
                                record_start_row=record_start_row,
                                record_end_row=record_end_row,
                                columns=columns,
                                column_details=column_details,
                                records=records,
                                confidence=confidence,
                                warnings=dedup_warnings,
                                classified_cells=classified_cells,
                            )
                            detected_tables.append(table_obj)

                            if record_end_row >= header_row_idx and records:
                                r = record_end_row + 1
                            else:
                                r = header_row_idx + 1
                            continue

                r += 1
                continue

            anchor_col = candidate_col + self.config.table_offset
            title_text = self.clean_title(candidate_cell.display_value)
            has_table_marker = "[TABLE]" in candidate_cell.display_value.upper()

            header_row_idx = r + 1
            has_header_cells = self._has_header_at_row(grid, header_row_idx, anchor_col)

            if has_header_cells and self._is_child_title_row(grid, header_row_idx, candidate_col + 1):
                has_header_cells = False

            # --- NEW: If no header immediately below, look for header row only through blank rows ---
            if not has_header_cells and not has_table_marker:
                # Try row r+2 as header ONLY if row r+1 is a blank or a continuation (not a child title)
                for offset in range(2, TITLE_LOOKUP_ROWS_ABOVE):
                    probe_header = r + offset
                    if probe_header >= grid.num_rows:
                        break
                    # Check the intermediate rows — if any contains a potential child title, STOP
                    intermediate_row = probe_header - 1
                    intermediate_cells = [c for c in grid.get_row_cells(intermediate_row) if not c.is_empty]
                    if len(intermediate_cells) == 1:
                        # Single cell row — could be child title; don't skip over it
                        break
                    if len(intermediate_cells) > 1:
                        # Multi-cell intermediate row already - stop scanning
                        break
                    # intermediate_row is blank → can probe ahead
                    probe_non_empty = [c for c in grid.get_row_cells(probe_header) if not c.is_empty]
                    if len(probe_non_empty) >= 2:
                        anchor_col_probe = anchor_col
                        has_header_probe = self._has_header_at_row(grid, probe_header, anchor_col_probe)
                        if has_header_probe:
                            header_row_idx = probe_header
                            has_header_cells = True
                            break
                    elif len(probe_non_empty) == 0:
                        continue
                    else:
                        break

            # --- NEW: If title text looks like numeric index, look up for a real title ---
            if self._is_numeric_index(title_text):
                title_above, title_cell_dict = self._find_title_above_header(
                    grid, r, anchor_col, candidate_col
                )
                if title_above:
                    title_text = title_above
                    pre_classified_title_rows.add(title_cell_dict["row"])
                else:
                    # Numeric title without linkable parent → mark with ambiguity warning
                    pass

            # --- NEW: Also try to find a better title above if current title is a section header ---
            # (title in col 0/1 but nothing linked from above - link it if we detect one)
            if not self._is_numeric_index(candidate_cell.display_value):
                # Already good title - but still check if we should link title row above to this detection
                pass

            table_id = f"tbl_{tbl_counter:03d}"
            tbl_counter += 1

            table_warnings: List[str] = []
            classified_cells: Set[Tuple[int, int]] = set()

            classified_cells.add((r, candidate_col))

            columns: List[str] = []
            column_details: List[Dict[str, Any]] = []
            col_end_idx = anchor_col

            if has_header_cells and header_row_idx < grid.num_rows:
                seen_headers: Dict[str, int] = {}
                raw_headers: List[str] = []

                for c_idx in range(anchor_col, grid.num_cols):
                    h_cell = grid.get_cell(header_row_idx, c_idx)
                    if h_cell and not h_cell.is_empty:
                        classified_cells.add((header_row_idx, c_idx))
                        h_label = h_cell.display_value
                        col_end_idx = c_idx

                        if h_label in seen_headers:
                            seen_headers[h_label] += 1
                            unique_label = f"{h_label}_{seen_headers[h_label]}"
                            if warnings.DUPLICATE_HEADER not in table_warnings:
                                table_warnings.append(warnings.DUPLICATE_HEADER)
                        else:
                            seen_headers[h_label] = 1
                            unique_label = h_label
                        raw_headers.append(unique_label)
                        column_details.append({
                            "key": unique_label,
                            "label": h_label,
                            "col_index": c_idx,
                        })
                    else:
                        if raw_headers:
                            subsequent = any(not grid.is_empty_cell(header_row_idx, c) for c in range(c_idx + 1, grid.num_cols))
                            if not subsequent:
                                break
                            else:
                                fallback_key = f"Col_{c_idx}"
                                raw_headers.append(fallback_key)
                                column_details.append({
                                    "key": fallback_key,
                                    "label": "",
                                    "col_index": c_idx,
                                })
                                col_end_idx = max(col_end_idx, c_idx)
                        else:
                            continue

                columns = raw_headers
            else:
                if not has_table_marker and candidate_col != 0:
                    table_warnings.append(warnings.MISSING_HEADER)

            if not columns:
                fallback_key = f"Col_{anchor_col}"
                columns = [fallback_key]
                column_details = [{
                    "key": fallback_key,
                    "label": "",
                    "col_index": anchor_col,
                }]

            record_start_row = header_row_idx + self.config.header_rows if has_header_cells else r + 1
            records: List[Dict[str, Any]] = []
            curr_record_row = record_start_row
            consecutive_blanks = 0
            last_record_row = record_start_row - 1

            while curr_record_row < grid.num_rows:
                r_cells = grid.get_row_cells(curr_record_row)
                if any("[BEGIN DATA]" in c.display_value.upper() or "[TABLE]" in c.display_value.upper() for c in r_cells if not c.is_empty):
                    break

                if grid.is_empty_row(curr_record_row):
                    consecutive_blanks += 1
                    if consecutive_blanks > self.config.max_blank_rows:
                        break
                    table_warnings.append(warnings.UNEXPECTED_BLANK_ROW)
                    curr_record_row += 1
                    continue

                consecutive_blanks = 0

                is_new_title = False
                for t_col in self.config.title_columns:
                    t_cell = grid.get_cell(curr_record_row, t_col)
                    if t_cell and not t_cell.is_empty:
                        t_text = t_cell.display_value
                        if not self.is_exclusion_title(t_text):
                            if any(not grid.is_empty_cell(curr_record_row, prev_c) for prev_c in range(t_col)):
                                continue
                            t_anchor = t_col + self.config.table_offset
                            t_has_marker = "[TABLE]" in t_text.upper()

                            if t_col <= candidate_col:
                                # Only treat as new title if it's NOT a numeric index AND
                                # the row doesn't look like a data record
                                if self._is_numeric_index(t_text):
                                    # Numeric value in anchor-or-lower column is likely a record's first value
                                    # (e.g. row number 1.0, 2.0 in a table indexed by column 0)
                                    # Do NOT break table unless a real header follows
                                    next_r = curr_record_row + 1
                                    if next_r < grid.num_rows:
                                        next_non_empty = [c for c in grid.get_row_cells(next_r) if not c.is_empty]
                                        next_all_str = all(
                                            isinstance(c.value, str) and not self._is_numeric_index(c.value)
                                            for c in next_non_empty
                                        ) if next_non_empty else False
                                        # If next row is all-string header-like → new table is forming
                                        if len(next_non_empty) >= 2 and next_all_str:
                                            is_new_title = True
                                            break
                                    # Otherwise, treat numeric as data
                                else:
                                    is_new_title = True
                                    break
                            else:
                                if self._is_child_title_row(grid, curr_record_row, t_col) or t_has_marker:
                                    is_new_title = True
                                    break

                if is_new_title:
                    break

                first_non_empty_val = ""
                for c_cell in r_cells:
                    if not c_cell.is_empty:
                        first_non_empty_val = c_cell.display_value
                        break

                if self.is_exclusion_title(first_non_empty_val):
                    table_warnings.append(warnings.POSSIBLE_FOOTER)
                    for c_idx in range(len(r_cells)):
                        if not r_cells[c_idx].is_empty:
                            classified_cells.add((curr_record_row, c_idx))
                    last_record_row = curr_record_row
                    curr_record_row += 1
                    break

                rec_dict: Dict[str, Any] = {}
                for idx, col_name in enumerate(columns):
                    c_pos = anchor_col + idx
                    cell_val = grid.get_value(curr_record_row, c_pos)
                    rec_dict[col_name] = cell_val
                    if not grid.is_empty_cell(curr_record_row, c_pos):
                        classified_cells.add((curr_record_row, c_pos))
                        col_end_idx = max(col_end_idx, c_pos)

                records.append(rec_dict)
                last_record_row = curr_record_row
                curr_record_row += 1

            record_end_row = max(record_start_row, last_record_row)

            if not records and warnings.MISSING_HEADER not in table_warnings and has_header_cells:
                table_warnings.append(warnings.EMPTY_RECORDS)

            dedup_warnings = list(dict.fromkeys(table_warnings))

            confidence = 1.0
            if warnings.AMBIGUOUS_TABLE_TITLE in dedup_warnings:
                confidence -= 0.4
            if warnings.MISSING_HEADER in dedup_warnings:
                confidence -= 0.3
            if warnings.EMPTY_RECORDS in dedup_warnings:
                confidence -= 0.2
            if warnings.UNEXPECTED_BLANK_ROW in dedup_warnings:
                confidence -= 0.1
            confidence = max(0.0, min(1.0, round(confidence, 2)))

            data_range = {
                "start_row": r,
                "start_col": candidate_col,
                "end_row": record_end_row if record_end_row >= r else r,
                "end_col": col_end_idx,
            }

            table_obj = DetectedTable(
                table_id=table_id,
                title=title_text,
                level=candidate_col,
                parent_id=None,
                title_cell={"row": r, "col": candidate_col},
                anchor_column=anchor_col,
                data_range=data_range,
                header_row=header_row_idx if has_header_cells else r,
                record_start_row=record_start_row,
                record_end_row=record_end_row,
                columns=columns,
                column_details=column_details,
                records=records,
                confidence=confidence,
                warnings=dedup_warnings,
                classified_cells=classified_cells,
            )

            detected_tables.append(table_obj)
            if record_end_row >= r and records:
                r = record_end_row + 1
            else:
                r = r + 1

        return detected_tables
