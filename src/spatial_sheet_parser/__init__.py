"""Spatial Sheet Parser package.

Deterministic spatial spreadsheet parser for Google Sheets/TSV/CSV
with structural hierarchy detection.
"""

from spatial_sheet_parser.version import __version__
from spatial_sheet_parser.config import ParserConfig
from spatial_sheet_parser.parser import SpatialSheetParser
from spatial_sheet_parser.grid import Cell, Grid
from spatial_sheet_parser import schema
from spatial_sheet_parser import warnings
from spatial_sheet_parser.validation import OutputValidator, validate_parse_output
from spatial_sheet_parser.presentation import export_json, render_preview

__all__ = [
    "ParserConfig",
    "SpatialSheetParser",
    "Cell",
    "Grid",
    "schema",
    "warnings",
    "OutputValidator",
    "validate_parse_output",
    "export_json",
    "render_preview",
    "__version__",
]

