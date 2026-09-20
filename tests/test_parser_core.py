"""Comprehensive unit tests for Spatial Sheet Parser deterministic core engine."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from spatial_sheet_parser import ParserConfig, SpatialSheetParser, warnings


class TestSpatialSheetParserCore(unittest.TestCase):

    def setUp(self):
        self.config = ParserConfig()
        self.parser = SpatialSheetParser(self.config)

    def test_happy_path_single_table(self):
        grid = [
            ["Sales Table", "", ""],
            ["", "Product", "Revenue"],
            ["", "Widget A", "1000"],
            ["", "Widget B", "2000"],
        ]
        result = self.parser.parse_grid(grid)

        self.assertEqual(result["metadata"]["data_start_row"], 0)
        self.assertEqual(len(result["tables"]), 1)
        
        table = result["tables"][0]
        self.assertEqual(table["table_id"], "tbl_001")
        self.assertEqual(table["title"], "Sales Table")
        self.assertEqual(table["level"], 0)
        self.assertIsNone(table["parent_id"])
        self.assertEqual(table["title_cell"], {"row": 0, "col": 0})
        self.assertEqual(table["anchor_column"], 1)
        self.assertEqual(table["columns"], ["Product", "Revenue"])
        self.assertEqual(len(table["records"]), 2)
        self.assertEqual(table["records"][0], {"Product": "Widget A", "Revenue": "1000"})
        self.assertEqual(table["records"][1], {"Product": "Widget B", "Revenue": "2000"})
        self.assertEqual(table["data_range"], {"start_row": 0, "start_col": 0, "end_row": 3, "end_col": 2})

    def test_nested_hierarchy(self):
        grid = [
            ["Region North", "", "", ""],
            ["", "Store 101", "", ""],
            ["", "", "Item", "Qty"],
            ["", "", "Apples", "50"],
            ["", "Store 102", "", ""],
            ["", "", "Item", "Qty"],
            ["", "", "Oranges", "30"],
        ]
        result = self.parser.parse_grid(grid)
        tables = result["tables"]

        self.assertEqual(len(tables), 3)

        parent = tables[0]
        child1 = tables[1]
        child2 = tables[2]

        self.assertEqual(parent["title"], "Region North")
        self.assertEqual(parent["level"], 0)
        self.assertIsNone(parent["parent_id"])
        self.assertIn(child1["table_id"], parent["children"])
        self.assertIn(child2["table_id"], parent["children"])

        self.assertEqual(child1["title"], "Store 101")
        self.assertEqual(child1["level"], 1)
        self.assertEqual(child1["parent_id"], parent["table_id"])
        self.assertEqual(child1["records"][0], {"Item": "Apples", "Qty": "50"})

        self.assertEqual(child2["title"], "Store 102")
        self.assertEqual(child2["level"], 1)
        self.assertEqual(child2["parent_id"], parent["table_id"])

    def test_data_markers_and_toc_preamble(self):
        grid = [
            ["Report Title: Q3 Financial Summary"],
            ["Generated on: 2026-09-20"],
            ["[BEGIN DATA]"],
            ["[TABLE] Q3 Sales", "", ""],
            ["", "Quarter", "Amount"],
            ["", "Q3-2026", "$500k"],
        ]
        result = self.parser.parse_grid(grid)

        self.assertEqual(result["metadata"]["data_start_row"], 3)
        self.assertEqual(len(result["metadata"]["toc_summary"]), 2)
        self.assertIn("Report Title", result["metadata"]["toc_summary"][0]["content"])

        self.assertEqual(len(result["tables"]), 1)
        table = result["tables"][0]
        self.assertEqual(table["title"], "Q3 Sales")
        self.assertEqual(table["records"][0], {"Quarter": "Q3-2026", "Amount": "$500k"})

    def test_blank_row_boundary(self):
        grid = [
            ["Data Table", "", ""],
            ["", "Col1", "Col2"],
            ["", "Val1", "Val2"],
            ["", "", ""],  # 1 blank row
            ["", "Val3", "Val4"],
            ["", "", ""],  # blank 1
            ["", "", ""],  # blank 2 (exceeds max_blank_rows = 1)
            ["", "Val5", "Val6"],
        ]
        parser = SpatialSheetParser(ParserConfig(max_blank_rows=1))
        result = parser.parse_grid(grid)

        tables = result["tables"]
        self.assertEqual(len(tables), 1)
        table = tables[0]
        # Table should include Val1 and Val3, stop at 2nd consecutive blank
        self.assertEqual(len(table["records"]), 2)
        self.assertEqual(table["records"][0]["Col1"], "Val1")
        self.assertEqual(table["records"][1]["Col1"], "Val3")
        self.assertIn(warnings.UNEXPECTED_BLANK_ROW, table["warnings"])

        # Val5 should be captured as unclassified row (zero silent data loss)
        self.assertTrue(len(result["unclassified_rows"]) > 0)
        unclassified_vals = [c["value"] for row in result["unclassified_rows"] for c in row["cells"]]
        self.assertIn("Val5", unclassified_vals)

    def test_duplicate_and_missing_headers(self):
        grid = [
            ["Dup Header Table", "", ""],
            ["", "Status", "Status"],  # Duplicate header
            ["", "Active", "Pending"],
        ]
        result = self.parser.parse_grid(grid)
        table = result["tables"][0]
        self.assertIn("Status", table["columns"])
        self.assertIn("Status_2", table["columns"])
        self.assertIn(warnings.DUPLICATE_HEADER, table["warnings"])

    def test_level_jump_and_orphan_table(self):
        grid = [
            ["", "", "Deep Level 2 Table", ""],  # Level 2 table without Level 0 or Level 1 parent
            ["", "", "", "Header1"],
            ["", "", "", "Val1"],
        ]
        result = self.parser.parse_grid(grid)
        
        # Should be classified as orphan table
        self.assertEqual(len(result["orphan_tables"]), 1)
        orphan = result["orphan_tables"][0]
        self.assertEqual(orphan["level"], 2)
        self.assertIn(warnings.ORPHAN_TABLE, orphan["warnings"])

    def test_empty_and_malformed_input(self):
        # Empty grid
        res_empty = self.parser.parse_grid([])
        self.assertEqual(len(res_empty["tables"]), 0)
        self.assertEqual(len(res_empty["unclassified_rows"]), 0)

        # Matrix with unclassified standalone note
        grid_note = [
            ["Overview Note: Unstructured text line"],
            ["", "", ""],
            ["Table Title", "", ""],
            ["", "Metric", "Value"],
            ["", "CPU", "80%"],
        ]
        res_note = self.parser.parse_grid(grid_note)
        self.assertEqual(len(res_note["tables"]), 1)
        self.assertEqual(len(res_note["unclassified_rows"]), 1)
        self.assertEqual(res_note["unclassified_rows"][0]["cells"][0]["value"], "Overview Note: Unstructured text line")


if __name__ == "__main__":
    unittest.main()
