"""Unit tests for Grid data structure, normalization, format gateway, and input adapters."""

import io
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from spatial_sheet_parser import Cell, Grid
from spatial_sheet_parser.adapters import (
    CSVAdapter,
    ExcelAdapter,
    JSONGridAdapter,
    ODSAdapter,
    TSVAdapter,
    XLSAdapter,
    normalize_input,
)


class TestGridAndAdapters(unittest.TestCase):

    def setUp(self):
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        self.xlsx_path = os.path.join(self.fixtures_dir, "sample_workbook.xlsx")
        self.xls_path = os.path.join(self.fixtures_dir, "sample_workbook.xls")
        self.ods_path = os.path.join(self.fixtures_dir, "sample_workbook.ods")
        self.tsv_path = os.path.join(self.fixtures_dir, "sample_financial_report.tsv")
        self.csv_path = os.path.join(self.fixtures_dir, "sample_inventory.csv")

    def test_grid_normalization_and_padding(self):
        matrix = [
            ["A", "B"],
            ["C"],
            ["D", "E", "F"],
        ]
        grid = Grid.from_matrix(matrix)
        self.assertEqual(grid.num_rows, 3)
        self.assertEqual(grid.num_cols, 3)
        self.assertEqual(grid.get_value(0, 0), "A")
        self.assertEqual(grid.get_value(1, 0), "C")
        self.assertIsNone(grid.get_value(1, 1))  # padded cell
        self.assertEqual(grid.get_value(2, 2), "F")

    def test_merged_cell_top_left_only_policy(self):
        matrix = [
            ["Region North", "Val 1", "Val 2"],
            ["Region North", "Val 3", "Val 4"],
        ]
        merged_cells = [
            {"start_row": 0, "start_col": 0, "end_row": 1, "end_col": 0}
        ]
        grid = Grid.from_matrix(matrix, merged_cells=merged_cells, merged_cell_policy="top_left_only")

        top_left = grid.get_cell(0, 0)
        self.assertIsNotNone(top_left)
        self.assertEqual(top_left.value, "Region North")
        self.assertTrue(top_left.is_top_left)

        merged_cell = grid.get_cell(1, 0)
        self.assertIsNotNone(merged_cell)
        self.assertIsNone(merged_cell.value)  # zeroed by top_left_only policy
        self.assertFalse(merged_cell.is_top_left)
        self.assertTrue(merged_cell.merged)

    def test_tsv_adapter(self):
        tsv_data = "Category A\t\t\n\tItem\tPrice\n\tWidget\t100\n"
        grid = TSVAdapter.parse(tsv_data)
        self.assertEqual(grid.source_format, "tsv")
        self.assertEqual(grid.get_value(0, 0), "Category A")
        self.assertEqual(grid.get_value(1, 1), "Item")
        self.assertEqual(grid.get_value(2, 2), "100")

    def test_tsv_adapter_multiline_cells(self):
        # Google sheets format for multiline cells: quoted string with newline inside
        tsv_data = 'Category A\t\t\n\t"Item\nDescription"\tPrice\n\t"Widget\nModel X"\t100\n'
        grid = TSVAdapter.parse(tsv_data)
        self.assertEqual(grid.source_format, "tsv")
        self.assertEqual(grid.get_value(0, 0), "Category A")
        self.assertEqual(grid.get_value(1, 1), "Item\nDescription")
        self.assertEqual(grid.get_value(2, 1), "Widget\nModel X")
        self.assertEqual(grid.num_rows, 3)

    def test_csv_adapter(self):
        csv_data = "Category B,,\n,Product,Quantity\n,Gadget,50\n"
        grid = CSVAdapter.parse(csv_data)
        self.assertEqual(grid.source_format, "csv")
        self.assertEqual(grid.get_value(0, 0), "Category B")
        self.assertEqual(grid.get_value(1, 1), "Product")

    def test_json_adapter_with_merged_cells(self):
        json_data = {
            "sheet_name": "SalesSheet",
            "grid": [
                ["Title", None],
                ["Header1", "Header2"],
            ],
            "merged_cells": [
                {"start_row": 0, "start_col": 0, "end_row": 0, "end_col": 1}
            ]
        }
        grid = JSONGridAdapter.parse(json_data)
        self.assertEqual(grid.source_format, "json")
        self.assertEqual(grid.sheet_name, "SalesSheet")
        self.assertEqual(grid.get_value(0, 0), "Title")
        self.assertIsNone(grid.get_value(0, 1))

    def test_xlsx_adapter(self):
        with open(self.xlsx_path, "rb") as f:
            content = f.read()
        grid_active = ExcelAdapter.parse(content)
        self.assertEqual(grid_active.source_format, "xlsx")
        self.assertIsNotNone(grid_active.sheet_name)

        grid_sheet = ExcelAdapter.parse(content, sheet_name="Inventory")
        self.assertEqual(grid_sheet.sheet_name, "Inventory")
        self.assertEqual(grid_sheet.get_value(0, 0), "Warehouse Stock")

    def test_xls_adapter(self):
        with open(self.xls_path, "rb") as f:
            content = f.read()
        grid_active = XLSAdapter.parse(content)
        self.assertEqual(grid_active.source_format, "xls")
        self.assertEqual(grid_active.sheet_name, "SalesSummary")

        grid_sheet = XLSAdapter.parse(content, sheet_name="Inventory")
        self.assertEqual(grid_sheet.sheet_name, "Inventory")
        self.assertEqual(grid_sheet.get_value(0, 0), "Inventory List")

        # Test merged cell policy top_left_only
        grid_merged = XLSAdapter.parse(content, sheet_name="SalesSummary")
        self.assertEqual(grid_merged.get_value(4, 0), "Merged Notes")
        self.assertIsNone(grid_merged.get_value(5, 0))

    def test_ods_adapter(self):
        with open(self.ods_path, "rb") as f:
            content = f.read()
        grid_active = ODSAdapter.parse(content)
        self.assertEqual(grid_active.source_format, "ods")
        self.assertEqual(grid_active.sheet_name, "SalesSummary")

        grid_sheet = ODSAdapter.parse(content, sheet_name="Inventory")
        self.assertEqual(grid_sheet.sheet_name, "Inventory")
        self.assertEqual(grid_sheet.get_value(0, 0), "Inventory List")

        # Test merged cell policy top_left_only
        grid_merged = ODSAdapter.parse(content, sheet_name="SalesSummary")
        self.assertEqual(grid_merged.get_value(0, 0), "Sales Report 2026")
        self.assertIsNone(grid_merged.get_value(0, 1))

    def test_missing_sheet_exposes_available_sheet_names(self):
        with open(self.xlsx_path, "rb") as f:
            xlsx_content = f.read()
        with self.assertRaises(ValueError) as cm_xlsx:
            ExcelAdapter.parse(xlsx_content, sheet_name="NonExistentSheet")
        self.assertIn("Available sheets:", str(cm_xlsx.exception))

        with open(self.xls_path, "rb") as f:
            xls_content = f.read()
        with self.assertRaises(ValueError) as cm_xls:
            XLSAdapter.parse(xls_content, sheet_name="NonExistentSheet")
        self.assertIn("Available sheets:", str(cm_xls.exception))
        self.assertIn("SalesSummary", str(cm_xls.exception))

        with open(self.ods_path, "rb") as f:
            ods_content = f.read()
        with self.assertRaises(ValueError) as cm_ods:
            ODSAdapter.parse(ods_content, sheet_name="NonExistentSheet")
        self.assertIn("Available sheets:", str(cm_ods.exception))
        self.assertIn("SalesSummary", str(cm_ods.exception))

    def test_normalize_input_auto_detect_binary_and_extensions(self):
        grid_from_list = normalize_input([["A", "B"]])
        self.assertIsInstance(grid_from_list, Grid)

        grid_from_tsv = normalize_input("Col1\tCol2\nVal1\tVal2", source_format="tsv")
        self.assertEqual(grid_from_tsv.source_format, "tsv")

        # File paths
        grid_xlsx = normalize_input(self.xlsx_path)
        self.assertEqual(grid_xlsx.source_format, "xlsx")

        grid_xls = normalize_input(self.xls_path)
        self.assertEqual(grid_xls.source_format, "xls")

        grid_ods = normalize_input(self.ods_path)
        self.assertEqual(grid_ods.source_format, "ods")

        # Magic bytes auto detection
        with open(self.xlsx_path, "rb") as f:
            xlsx_bytes = f.read()
        grid_xlsx_bytes = normalize_input(xlsx_bytes)
        self.assertEqual(grid_xlsx_bytes.source_format, "xlsx")

        with open(self.ods_path, "rb") as f:
            ods_bytes = f.read()
        grid_ods_bytes = normalize_input(ods_bytes)
        self.assertEqual(grid_ods_bytes.source_format, "ods")

        with open(self.xls_path, "rb") as f:
            xls_bytes = f.read()
        grid_xls_bytes = normalize_input(xls_bytes)
        self.assertEqual(grid_xls_bytes.source_format, "xls")

    def test_utf8_bom_handling(self):
        tsv_bom_bytes = b"\xef\xbb\xbfCategory BOM\t\t\n\tCol1\tCol2\n\tVal1\tVal2\n"
        grid = normalize_input(tsv_bom_bytes, source_format="tsv")
        self.assertEqual(grid.get_value(0, 0), "Category BOM")

    def test_malformed_binary_files_raise_value_error(self):
        bad_bytes = b"PK\x03\x04CORRUPTED_ZIP_HEADER_DATA_12345"
        with self.assertRaises(ValueError):
            normalize_input(bad_bytes, source_format="xlsx")

        bad_ole_bytes = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1CORRUPTED_OLE_HEADER"
        with self.assertRaises(ValueError):
            normalize_input(bad_ole_bytes, source_format="xls")


if __name__ == "__main__":
    unittest.main()
