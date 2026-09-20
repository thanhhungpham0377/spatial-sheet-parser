"""Smoke tests for Spatial Sheet Parser bootstrap skeleton."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from spatial_sheet_parser import __version__, ParserConfig, SpatialSheetParser
from spatial_sheet_parser.cli import main, create_parser


class TestSmoke(unittest.TestCase):

    def test_version(self):
        self.assertEqual(__version__, "0.1.0")

    def test_default_config(self):
        config = ParserConfig()
        self.assertEqual(config.title_columns, [0, 1, 2])
        self.assertEqual(config.table_offset, 1)
        self.assertEqual(config.max_blank_rows, 1)
        self.assertEqual(config.header_rows, 1)
        self.assertEqual(config.explicit_markers, ["[BEGIN DATA]", "[TABLE]"])
        self.assertEqual(config.merged_cell_policy, "top_left_only")
        self.assertEqual(config.strictness, "balanced")

    def test_parser_execution(self):
        parser = SpatialSheetParser()
        result = parser.parse_grid([["Title"], ["Header 1", "Header 2"]])
        self.assertIsInstance(result, dict)
        self.assertIn("metadata", result)
        self.assertIn("tables", result)

    def test_cli_help(self):
        cli_parser = create_parser()
        with self.assertRaises(SystemExit) as cm:
            cli_parser.parse_args(["--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_cli_parse_stub(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False) as f:
            f.write("Category A\t\t\n\tCol1\tCol2\n\tVal1\tVal2\n")
            temp_path = f.name
        try:
            exit_code = main(["parse", temp_path])
            self.assertEqual(exit_code, 0)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)



if __name__ == "__main__":
    unittest.main()
