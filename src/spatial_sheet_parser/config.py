"""Configuration data models for Spatial Sheet Parser."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ParserConfig:
    """Parser configuration settings matching product specification.

    Attributes:
        title_columns: List of column indices where table title cells can occur.
        table_offset: Column offset from title cell to table header anchor column.
        max_blank_rows: Maximum consecutive blank rows before table region terminates.
        header_rows: Expected number of header rows per table.
        explicit_markers: String markers triggering explicit region breaks or tables.
        merged_cell_policy: Strategy for handling merged cells ('top_left_only').
        strictness: Parser strictness level ('strict', 'balanced', 'lenient').
        sheet_name: Optional worksheet name to select for Excel workbooks.
    """

    title_columns: List[int] = field(default_factory=lambda: [0, 1, 2])
    table_offset: int = 1
    max_blank_rows: int = 1
    header_rows: int = 1
    explicit_markers: List[str] = field(
        default_factory=lambda: ["[BEGIN DATA]", "[TABLE]"]
    )
    merged_cell_policy: str = "top_left_only"
    strictness: str = "balanced"
    sheet_name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParserConfig":
        """Instantiates ParserConfig from dictionary, overriding default fields."""
        if not isinstance(data, dict):
            raise ValueError("Configuration data must be a dictionary.")
        known_fields = {
            "title_columns",
            "table_offset",
            "max_blank_rows",
            "header_rows",
            "explicit_markers",
            "merged_cell_policy",
            "strictness",
            "sheet_name",
        }
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)

