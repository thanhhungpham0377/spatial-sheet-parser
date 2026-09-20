"""Core SpatialSheetParser class connecting pipeline stages."""

from typing import Any, Dict, List, Optional, Set, Tuple, Union
from spatial_sheet_parser.version import __version__, __author__, __copyright__
from spatial_sheet_parser.adapters import normalize_input
from spatial_sheet_parser.config import ParserConfig
from spatial_sheet_parser.detection import RegionDetector, TableCandidateDetector, DetectedTable
from spatial_sheet_parser.grid import Grid
from spatial_sheet_parser import hierarchy
from spatial_sheet_parser import warnings


from spatial_sheet_parser.validation import validate_parse_output


class SpatialSheetParser:
    """Core entry point for spatial spreadsheet parsing."""

    def __init__(self, config: Optional[ParserConfig] = None) -> None:
        self.config = config or ParserConfig()

    def parse_grid(
        self,
        grid: Union[List[List[Any]], str, bytes, Dict[str, Any]],
        source_format: str = "raw",
        sheet_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Parses a 2D matrix grid into structured JSON result tree.

        Args:
            grid: 2D array of cell values, TSV/CSV text, JSON grid structure, or raw Excel bytes.
            source_format: Format identifier ('raw', 'tsv', 'csv', 'json', 'xlsx').
            sheet_name: Optional sheet name metadata.

        Returns:
            Dict matching standard JSON contract output.
        """
        effective_sheet_name = sheet_name or self.config.sheet_name
        # 1. Normalize input grid
        norm_grid = normalize_input(
            grid_input=grid,
            source_format=source_format,
            sheet_name=effective_sheet_name,
            merged_cell_policy=self.config.merged_cell_policy,
        )

        # 2. Region & Marker Detection
        region_detector = RegionDetector(self.config)
        data_start_row, toc_summary, global_warnings = region_detector.detect_preamble_and_markers(norm_grid)

        # 3. Table Candidates & Boundary Detection
        table_detector = TableCandidateDetector(self.config)
        detected_tables = table_detector.detect_tables(norm_grid, data_start_row=data_start_row)

        # 4. Hierarchy Resolution
        all_tables, orphan_tables = hierarchy.build_table_hierarchy(detected_tables)

        orphan_ids = {ot.table_id for ot in orphan_tables}
        non_orphan_tables = [t for t in all_tables if t.table_id not in orphan_ids]

        # Separate root/hierarchical tables vs orphan tables for output serialization
        table_dicts: List[Dict[str, Any]] = []
        orphan_dicts: List[Dict[str, Any]] = []

        all_classified_cells: Set[Tuple[int, int]] = set()

        for t in non_orphan_tables:
            all_classified_cells.update(t.classified_cells)
            t_dict = self._serialize_table(t)
            table_dicts.append(t_dict)

        for ot in orphan_tables:
            all_classified_cells.update(ot.classified_cells)
            ot_dict = self._serialize_table(ot)
            if ot_dict not in orphan_dicts:
                orphan_dicts.append(ot_dict)

        # Mark preamble/TOC summary cells as classified so they are not treated as unclassified
        for toc_item in toc_summary:
            t_row = toc_item.get("row")
            if t_row is not None:
                for c_cell in norm_grid.get_row_cells(t_row):
                    if not c_cell.is_empty:
                        all_classified_cells.add((t_row, c_cell.col))

        # 5. Extract Unclassified Rows (Zero Silent Data Loss)
        unclassified_rows = self._extract_unclassified_rows(
            grid=norm_grid,
            data_start_row=data_start_row,
            classified_cells=all_classified_cells,
        )

        # Metadata format identification
        actual_format = norm_grid.source_format if norm_grid.source_format != "raw" else source_format

        # Standard Output JSON Contract
        result = {
            "metadata": {
                "parser_version": __version__,
                "author": __author__,
                "copyright": __copyright__,
                "source_format": actual_format,
                "sheet_name": norm_grid.sheet_name,
                "toc_summary": toc_summary,
                "data_start_row": data_start_row,
                "warnings": list(dict.fromkeys(global_warnings)),
            },
            "tables": table_dicts,
            "orphan_tables": orphan_dicts,
            "unclassified_rows": unclassified_rows,
        }

        # 6. Schema & Contract Validation Integration
        validation_res = validate_parse_output(result, config=self.config)
        result["metadata"]["validation"] = validation_res.to_dict()

        for vw in validation_res.warnings:
            if vw.code not in result["metadata"]["warnings"]:
                result["metadata"]["warnings"].append(vw.code)

        result["metadata"]["warnings"] = list(dict.fromkeys(result["metadata"]["warnings"]))

        return result

    def _serialize_table(self, table: DetectedTable) -> Dict[str, Any]:
        return {
            "table_id": table.table_id,
            "title": table.title,
            "level": table.level,
            "parent_id": table.parent_id,
            "title_cell": table.title_cell,
            "anchor_column": table.anchor_column,
            "data_range": table.data_range,
            "header_row": table.header_row,
            "record_start_row": table.record_start_row,
            "record_end_row": table.record_end_row,
            "columns": table.columns,
            "column_details": table.column_details,
            "records": table.records,
            "children": list(dict.fromkeys(table.children)),
            "confidence": table.confidence,
            "warnings": list(dict.fromkeys(table.warnings)),
            "node_type": getattr(table, "node_type", "table"),
        }

    def _extract_unclassified_rows(
        self,
        grid: Grid,
        data_start_row: int,
        classified_cells: Set[Tuple[int, int]],
    ) -> List[Dict[str, Any]]:
        unclassified: List[Dict[str, Any]] = []

        for r in range(grid.num_rows):
            # Rows before data_start_row are part of preamble/TOC
            if r < data_start_row:
                continue

            row_cells = grid.get_row_cells(r)
            # check for explicit marker in row
            if any("[BEGIN DATA]" in c.display_value.upper() for c in row_cells if not c.is_empty):
                continue

            unclassified_in_row = []
            for c in row_cells:
                if not c.is_empty and (r, c.col) not in classified_cells:
                    unclassified_in_row.append({
                        "col": c.col,
                        "value": c.raw_value,
                    })

            if unclassified_in_row:
                unclassified.append({
                    "row": r,
                    "cells": unclassified_in_row,
                    "warnings": [warnings.UNCLASSIFIED_DATA],
                })

        return unclassified
