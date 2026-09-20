"""Integration tests for Spatial Sheet Parser CLI."""

import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from spatial_sheet_parser.cli import main, create_parser
from spatial_sheet_parser.version import __version__


class TestCLIIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _make_temp_file(self, filename: str, content: str) -> str:
        filepath = os.path.join(self.temp_dir.name, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def test_cli_help(self):
        parser = create_parser()
        with self.assertRaises(SystemExit) as cm:
            parser.parse_args(["--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_cli_tsv_file_json_stdout(self):
        tsv_data = "Category A\t\t\n\tItem Code\tPrice\n\tITEM01\t100\n"
        filepath = self._make_temp_file("test_sample.tsv", tsv_data)

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr

        try:
            sys.stdout, sys.stderr = stdout_buf, stderr_buf
            exit_code = main(["parse", filepath, "--format", "tsv"])
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

        self.assertEqual(exit_code, 0)
        out_text = stdout_buf.getvalue()
        self.assertIn('"metadata"', out_text)
        parsed = json.loads(out_text)
        self.assertEqual(parsed["metadata"]["source_format"], "tsv")
        self.assertTrue(len(parsed["tables"]) > 0)

    def test_cli_csv_file_preview(self):
        csv_data = "Category B,,\n,Product,Quantity\n,Widget A,10\n"
        filepath = self._make_temp_file("test_sample.csv", csv_data)

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr

        try:
            sys.stdout, sys.stderr = stdout_buf, stderr_buf
            exit_code = main(["parse", filepath, "--preview"])
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

        self.assertEqual(exit_code, 0)
        out_text = stdout_buf.getvalue()
        self.assertIn("Spatial Sheet Parser - Preview Summary", out_text)
        self.assertIn("Category B", out_text)
        self.assertIn("Source Format : csv", out_text)

    def test_cli_json_grid_out(self):
        json_data = json.dumps({
            "grid": [
                ["Section C", "", ""],
                ["", "Name", "Score"],
                ["", "Alice", "95"]
            ]
        })
        filepath = self._make_temp_file("test_sample.json", json_data)
        out_filepath = os.path.join(self.temp_dir.name, "out_result.json")

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr

        try:
            sys.stdout, sys.stderr = stdout_buf, stderr_buf
            exit_code = main(["parse", filepath, "--out", out_filepath])
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.exists(out_filepath))
        with open(out_filepath, "r", encoding="utf-8") as f:
            content = f.read()
        parsed = json.loads(content)
        self.assertEqual(parsed["metadata"]["source_format"], "json")
        self.assertEqual(parsed["tables"][0]["title"], "Section C")

    def test_cli_stdin_input(self):
        tsv_data = "Category Stdin\t\t\n\tCol1\tCol2\n\tVal1\tVal2\n"
        stdin_buf = io.StringIO(tsv_data)
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        old_stdin, old_stdout, old_stderr = sys.stdin, sys.stdout, sys.stderr

        try:
            sys.stdin = stdin_buf
            sys.stdout, sys.stderr = stdout_buf, stderr_buf
            exit_code = main(["parse", "-", "--format", "tsv", "--preview"])
        finally:
            sys.stdin, sys.stdout, sys.stderr = old_stdin, old_stdout, old_stderr

        self.assertEqual(exit_code, 0)
        out_text = stdout_buf.getvalue()
        self.assertIn("Category Stdin", out_text)
        self.assertIn("Preview Summary", out_text)

    def test_cli_custom_config(self):
        tsv_data = "Category Custom\t\t\n\tHeader A\tHeader B\n\tVal A\tVal B\n"
        filepath = self._make_temp_file("custom.tsv", tsv_data)

        config_data = json.dumps({"max_blank_rows": 2, "merged_cell_policy": "top_left_only"})
        config_path = self._make_temp_file("custom_config.json", config_data)

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr

        try:
            sys.stdout, sys.stderr = stdout_buf, stderr_buf
            exit_code = main(["parse", filepath, "--config", config_path])
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

        self.assertEqual(exit_code, 0)
        out_text = stdout_buf.getvalue()
        parsed = json.loads(out_text)
        self.assertEqual(parsed["tables"][0]["title"], "Category Custom")

    def test_cli_out_and_preview_combined(self):
        tsv_data = "Category Both\t\t\n\tH1\tH2\n\tV1\tV2\n"
        filepath = self._make_temp_file("both.tsv", tsv_data)
        out_filepath = os.path.join(self.temp_dir.name, "combined_out.json")

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr

        try:
            sys.stdout, sys.stderr = stdout_buf, stderr_buf
            exit_code = main(["parse", filepath, "--out", out_filepath, "--preview"])
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.exists(out_filepath))
        out_text = stdout_buf.getvalue()
        self.assertIn("Spatial Sheet Parser - Preview Summary", out_text)

    def test_cli_error_file_not_found(self):
        stderr_buf = io.StringIO()
        old_stderr = sys.stderr

        try:
            sys.stderr = stderr_buf
            exit_code = main(["parse", "non_existent_file.tsv"])
        finally:
            sys.stderr = old_stderr

        self.assertEqual(exit_code, 1)
        self.assertIn("Error: File not found", stderr_buf.getvalue())

    def test_cli_error_empty_input(self):
        filepath = self._make_temp_file("empty.tsv", "  \n  ")
        stderr_buf = io.StringIO()
        old_stderr = sys.stderr

        try:
            sys.stderr = stderr_buf
            exit_code = main(["parse", filepath])
        finally:
            sys.stderr = old_stderr

        self.assertEqual(exit_code, 1)
        self.assertIn("Error: Input content is empty", stderr_buf.getvalue())

    def test_cli_error_invalid_config(self):
        tsv_data = "Category Err\t\t\n\tH1\tH2\n\tV1\tV2\n"
        filepath = self._make_temp_file("valid.tsv", tsv_data)
        invalid_cfg_path = self._make_temp_file("bad_config.json", "{invalid json syntax")

        stderr_buf = io.StringIO()
        old_stderr = sys.stderr

        try:
            sys.stderr = stderr_buf
            exit_code = main(["parse", filepath, "--config", invalid_cfg_path])
        finally:
            sys.stderr = old_stderr

        self.assertEqual(exit_code, 1)
        self.assertIn("Error loading configuration file", stderr_buf.getvalue())

    def test_cli_excel_file_parsing(self):
        xlsx_fixture = os.path.join(os.path.dirname(__file__), "fixtures", "sample_workbook.xlsx")
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr

        try:
            sys.stdout, sys.stderr = stdout_buf, stderr_buf
            exit_code = main(["parse", xlsx_fixture, "--preview"])
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

        self.assertEqual(exit_code, 0)
        out_text = stdout_buf.getvalue()
        self.assertIn("Spatial Sheet Parser - Preview Summary", out_text)
        self.assertIn("Source Format : xlsx", out_text)
        self.assertIn("Sales Overview 2026", out_text)

    def test_cli_excel_file_sheet_selection(self):
        xlsx_fixture = os.path.join(os.path.dirname(__file__), "fixtures", "sample_workbook.xlsx")
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr

        try:
            sys.stdout, sys.stderr = stdout_buf, stderr_buf
            exit_code = main(["parse", xlsx_fixture, "--sheet", "Inventory", "--preview"])
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

        self.assertEqual(exit_code, 0)
        out_text = stdout_buf.getvalue()
        self.assertIn("Sheet: Inventory", out_text)
        self.assertIn("Warehouse Stock", out_text)

    def test_cli_xls_file_parsing(self):
        xls_fixture = os.path.join(os.path.dirname(__file__), "fixtures", "sample_workbook.xls")
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr

        try:
            sys.stdout, sys.stderr = stdout_buf, stderr_buf
            exit_code = main(["parse", xls_fixture, "--sheet", "Inventory", "--preview"])
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

        self.assertEqual(exit_code, 0)
        out_text = stdout_buf.getvalue()
        self.assertIn("Source Format : xls", out_text)
        self.assertIn("Sheet: Inventory", out_text)
        self.assertIn("Inventory List", out_text)

    def test_cli_ods_file_parsing(self):
        ods_fixture = os.path.join(os.path.dirname(__file__), "fixtures", "sample_workbook.ods")
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr

        try:
            sys.stdout, sys.stderr = stdout_buf, stderr_buf
            exit_code = main(["parse", ods_fixture, "--sheet", "Inventory", "--preview"])
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

        self.assertEqual(exit_code, 0)
        out_text = stdout_buf.getvalue()
        self.assertIn("Source Format : ods", out_text)
        self.assertIn("Sheet: Inventory", out_text)
        self.assertIn("Inventory List", out_text)


if __name__ == "__main__":
    unittest.main()
