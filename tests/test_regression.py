"""Regression test suite for Spatial Sheet Parser (SSP-005).

Tests realistic fixtures, edge cases, contracts, determinism, and CLI integration.
"""

import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from spatial_sheet_parser import (
    ParserConfig,
    SpatialSheetParser,
    validate_parse_output,
    warnings,
)
from spatial_sheet_parser.cli import main, create_parser


class TestSpatialSheetParserRegression(unittest.TestCase):
    """Comprehensive regression test suite covering all MVP spatial parsing requirements."""

    def setUp(self):
        self.config = ParserConfig()
        self.parser = SpatialSheetParser(self.config)
        self.fixtures_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))

    def _read_fixture(self, filename: str) -> str:
        filepath = os.path.join(self.fixtures_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    # --- 1. TOC & Explicit Data Marker Tests ---

    def test_toc_and_explicit_begin_data_marker(self):
        tsv_content = self._read_fixture("sample_financial_report.tsv")
        res = self.parser.parse_grid(tsv_content, source_format="tsv")

        meta = res["metadata"]
        self.assertEqual(meta["source_format"], "tsv")
        self.assertTrue(meta["data_start_row"] > 0)
        self.assertEqual(len(meta["toc_summary"]), 3)
        self.assertIn("Company Annual Financial Report", meta["toc_summary"][0]["content"])

        # Tables should begin after [BEGIN DATA]
        self.assertTrue(len(res["tables"]) >= 3)
        root_table = res["tables"][0]
        self.assertEqual(root_table["title"], "Corporate Group Alpha")

    # --- 2. Hierarchy & Orphan Level Jump Tests ---

    def test_nested_hierarchy_and_level_skipping(self):
        tsv_content = self._read_fixture("sample_financial_report.tsv")
        res = self.parser.parse_grid(tsv_content, source_format="tsv")

        tables = res["tables"]
        root = tables[0]  # Corporate Group Alpha (level 0)
        child_div_north = tables[1]  # Division North (level 1)
        child_div_south = tables[2]  # Division South (level 1)

        self.assertEqual(root["level"], 0)
        self.assertIn(child_div_north["table_id"], root["children"])
        self.assertIn(child_div_south["table_id"], root["children"])

        self.assertEqual(child_div_north["parent_id"], root["table_id"])
        self.assertEqual(child_div_south["parent_id"], root["table_id"])

        # Check records for Division North
        records_n = child_div_north["records"]
        self.assertEqual(len(records_n), 2)
        self.assertEqual(records_n[0]["Item Name"], "Product A1")
        self.assertEqual(records_n[0]["Q1 Revenue"], "10000")

    def test_orphan_table_detection_from_csv_fixture(self):
        csv_content = self._read_fixture("sample_inventory.csv")
        res = self.parser.parse_grid(csv_content, source_format="csv")

        self.assertTrue(len(res["orphan_tables"]) >= 1)
        orphan = res["orphan_tables"][0]
        self.assertEqual(orphan["title"], "Orphan Sub-Table Level 2")
        self.assertEqual(orphan["level"], 2)
        self.assertIsNone(orphan["parent_id"])
        self.assertIn(warnings.ORPHAN_TABLE, orphan["warnings"])

    # --- 3. Duplicate and Missing Headers ---

    def test_duplicate_headers_handling(self):
        tsv_content = self._read_fixture("sample_financial_report.tsv")
        res = self.parser.parse_grid(tsv_content, source_format="tsv")

        div_north = res["tables"][1]
        self.assertIn(warnings.DUPLICATE_HEADER, div_north["warnings"])
        self.assertIn("Status", div_north["columns"])
        self.assertIn("Status_2", div_north["columns"])
        self.assertEqual(div_north["records"][0]["Status"], "Active")
        self.assertEqual(div_north["records"][0]["Status_2"], "Verified")

    def test_missing_header_fallback(self):
        grid = [
            ["", "Parent Headerless Table", ""],
            ["", "", "Child Table Title", ""],
            ["", "", "", "Header1"],
            ["", "", "", "Val1"],
        ]
        res = self.parser.parse_grid(grid)
        self.assertTrue(len(res["orphan_tables"]) >= 1)
        orphan = res["orphan_tables"][0]
        self.assertIn(warnings.MISSING_HEADER, orphan["warnings"])

    # --- 4. Merged-Cell Policy Tests ---

    def test_merged_cell_top_left_only_policy_from_json_fixture(self):
        json_content = self._read_fixture("sample_nested_grid.json")
        res = self.parser.parse_grid(json_content, source_format="json")

        meta = res["metadata"]
        self.assertEqual(meta["sheet_name"], "RegionalSalesSheet")
        self.assertIn(warnings.MERGED_CELL_DETECTED, meta["warnings"])

        # Check table extraction
        self.assertTrue(len(res["tables"]) >= 3)
        root = res["tables"][0]
        self.assertEqual(root["title"], "Region East")
        self.assertEqual(len(root["children"]), 2)

    # --- 5. Unclassified Rows & Footer Policy ---

    def test_unclassified_rows_and_footer_detection(self):
        tsv_content = self._read_fixture("sample_financial_report.tsv")
        res = self.parser.parse_grid(tsv_content, source_format="tsv")

        unclassified = res["unclassified_rows"]
        self.assertTrue(len(unclassified) > 0)
        unclassified_texts = [
            cell["value"] for u_row in unclassified for cell in u_row["cells"]
        ]
        self.assertIn("Standalone Footer Note: Pending final audit approval", unclassified_texts)

    # --- 6. CLI Export, Preview, & Stdin Verification ---

    def test_cli_full_pipeline_tsv_file_export(self):
        tsv_path = os.path.join(self.fixtures_dir, "sample_financial_report.tsv")
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "output.json")
            stdout_buf = io.StringIO()
            stderr_buf = io.StringIO()

            old_stdout, old_stderr = sys.stdout, sys.stderr
            try:
                sys.stdout, sys.stderr = stdout_buf, stderr_buf
                code = main(["parse", tsv_path, "--out", out_file, "--preview"])
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr

            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(out_file))

            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertTrue(data["metadata"]["validation"]["is_valid"])
            self.assertIn("Corporate Group Alpha", stdout_buf.getvalue())

    def test_cli_stdin_json_grid_pipeline(self):
        json_content = self._read_fixture("sample_nested_grid.json")
        stdin_buf = io.StringIO(json_content)
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        old_stdin, old_stdout, old_stderr = sys.stdin, sys.stdout, sys.stderr
        try:
            sys.stdin = stdin_buf
            sys.stdout, sys.stderr = stdout_buf, stderr_buf
            code = main(["parse", "-", "--format", "json"])
        finally:
            sys.stdin, sys.stdout, sys.stderr = old_stdin, old_stdout, old_stderr

        self.assertEqual(code, 0)
        out_json = stdout_buf.getvalue()
        res = json.loads(out_json)
        self.assertEqual(res["metadata"]["source_format"], "json")
        self.assertEqual(res["metadata"]["sheet_name"], "RegionalSalesSheet")

    # --- 7. Malformed Input Resilience ---

    def test_malformed_input_graceful_handling(self):
        # Empty input string
        with self.assertRaises(ValueError):
            self.parser.parse_grid(12345)  # Invalid non-grid type

        # Matrix with all whitespace
        grid_whitespace = [["   ", "  "], ["  ", "\t"]]
        res = self.parser.parse_grid(grid_whitespace)
        self.assertEqual(len(res["tables"]), 0)
        self.assertEqual(len(res["unclassified_rows"]), 0)

        # Single cell matrix
        grid_single = [["Single Title Only"]]
        res_single = self.parser.parse_grid(grid_single)
        self.assertTrue(len(res_single["unclassified_rows"]) > 0 or len(res_single["tables"]) == 0)

    # --- 8. Determinism & Schema Contract Verification ---

    def test_deterministic_output_contract_integrity(self):
        tsv_content = self._read_fixture("sample_financial_report.tsv")
        
        baseline_res = self.parser.parse_grid(tsv_content, source_format="tsv")
        baseline_val = validate_parse_output(baseline_res, self.config)
        self.assertTrue(baseline_val.is_valid)

        for _ in range(10):
            iteration_res = self.parser.parse_grid(tsv_content, source_format="tsv")
            self.assertEqual(baseline_res, iteration_res)


if __name__ == "__main__":
    unittest.main()
