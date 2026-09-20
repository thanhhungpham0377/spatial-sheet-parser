"""Grid data structures and normalization logic for Spatial Sheet Parser."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Cell:
    """Represents a single cell in the grid matrix preserving source coordinates."""

    row: int
    col: int
    value: Any
    raw_value: Any
    merged: bool = False
    is_top_left: bool = True
    merged_range: Optional[Tuple[int, int, int, int]] = None

    @property
    def is_empty(self) -> bool:
        """Determines if the cell is empty or contains only whitespace."""
        if self.value is None:
            return True
        if isinstance(self.value, str):
            return self.value.strip() == ""
        return False

    @property
    def display_value(self) -> str:
        """Returns string representation of cell value."""
        if self.is_empty:
            return ""
        if isinstance(self.value, str):
            return self.value.strip()
        return str(self.value)


@dataclass
class Grid:
    """Normalized 2D matrix grid of Cells."""

    rows: List[List[Cell]] = field(default_factory=list)
    source_format: str = "raw"
    sheet_name: Optional[str] = None
    has_merged_cells: bool = False

    @property
    def num_rows(self) -> int:
        return len(self.rows)

    @property
    def num_cols(self) -> int:
        if not self.rows:
            return 0
        return max(len(r) for r in self.rows)

    def get_cell(self, row: int, col: int) -> Optional[Cell]:
        """Safely fetches cell by row and col index."""
        if 0 <= row < len(self.rows):
            r = self.rows[row]
            if 0 <= col < len(r):
                return r[col]
        return None

    def get_value(self, row: int, col: int) -> Any:
        """Fetches raw cell value or None if empty/out-of-bounds."""
        cell = self.get_cell(row, col)
        if cell is None or cell.is_empty:
            return None
        return cell.value

    def is_empty_cell(self, row: int, col: int) -> bool:
        cell = self.get_cell(row, col)
        return cell is None or cell.is_empty

    def is_empty_row(self, row: int) -> bool:
        """Returns True if all cells in the row are empty or out of bounds."""
        if not (0 <= row < len(self.rows)):
            return True
        return all(cell.is_empty for cell in self.rows[row])

    def get_row_cells(self, row: int) -> List[Cell]:
        if 0 <= row < len(self.rows):
            return self.rows[row]
        return []

    @classmethod
    def from_matrix(
        cls,
        matrix: List[List[Any]],
        source_format: str = "raw",
        sheet_name: Optional[str] = None,
        merged_cells: Optional[List[Dict[str, int]]] = None,
        merged_cell_policy: str = "top_left_only",
    ) -> "Grid":
        """Constructs a normalized Grid from a raw 2D matrix."""
        if not matrix:
            return cls(rows=[], source_format=source_format, sheet_name=sheet_name)

        max_cols = max((len(r) for r in matrix), default=0)
        grid_rows: List[List[Cell]] = []

        for r_idx, row in enumerate(matrix):
            cell_row: List[Cell] = []
            for c_idx in range(max_cols):
                val = row[c_idx] if c_idx < len(row) else None
                # Preserve raw value, strip whitespace for display/evaluation if string
                cell = Cell(
                    row=r_idx,
                    col=c_idx,
                    value=val,
                    raw_value=val,
                )
                cell_row.append(cell)
            grid_rows.append(cell_row)

        grid = cls(rows=grid_rows, source_format=source_format, sheet_name=sheet_name)

        if merged_cells:
            grid.apply_merged_cell_policy(merged_cells, policy=merged_cell_policy)

        return grid

    def apply_merged_cell_policy(
        self,
        merged_cells: List[Dict[str, int]],
        policy: str = "top_left_only",
    ) -> None:
        """Applies merged cell policy (e.g. top_left_only).

        Expects merged_cells list of dicts:
        {"start_row": r1, "start_col": c1, "end_row": r2, "end_col": c2}
        """
        if not merged_cells:
            return

        self.has_merged_cells = True
        for m in merged_cells:
            r1, c1 = m.get("start_row", 0), m.get("start_col", 0)
            r2, c2 = m.get("end_row", r1), m.get("end_col", c1)
            range_tuple = (r1, c1, r2, c2)

            for r in range(r1, r2 + 1):
                for c in range(c1, c2 + 1):
                    cell = self.get_cell(r, c)
                    if cell:
                        cell.merged = True
                        cell.merged_range = range_tuple
                        if r == r1 and c == c1:
                            cell.is_top_left = True
                        else:
                            cell.is_top_left = False
                            if policy == "top_left_only":
                                cell.value = None
