"""Unit tests for Schema Contract, Validation Engine, and Contract Integrity (SSP-003)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from spatial_sheet_parser import (
    ParserConfig,
    SpatialSheetParser,
    OutputValidator,
    validate_parse_output,
    schema,
    warnings,
)


class TestValidationSchema(unittest.TestCase):

    def setUp(self):
        self.config = ParserConfig()
        self.parser = SpatialSheetParser(self.config)
        self.validator = OutputValidator(self.config)

    # --- Positive Tests ---

    def test_valid_single_table_schema(self):
        grid = [
            ["Sales Overview", "", ""],
            ["", "Region", "Revenue"],
            ["", "North", "5000"],
            ["", "South", "6000"],
        ]
        res = self.parser.parse_grid(grid)
        val_res = validate_parse_output(res, self.config)

        self.assertTrue(val_res.is_valid)
        self.assertEqual(val_res.errors, [])
        self.assertEqual(res["metadata"]["validation"]["is_valid"], True)

        table = res["tables"][0]
        self.assertIn("column_details", table)
        self.assertEqual(len(table["column_details"]), 2)
        self.assertEqual(table["column_details"][0]["key"], "Region")
        self.assertEqual(table["column_details"][0]["label"], "Region")
        self.assertEqual(table["column_details"][1]["key"], "Revenue")
        self.assertEqual(table["column_details"][1]["label"], "Revenue")

    def test_valid_nested_hierarchy_schema(self):
        grid = [
            ["Company HQ", "", "", ""],
            ["", "Branch A", "", ""],
            ["", "", "Employee", "Role"],
            ["", "", "Alice", "Manager"],
            ["", "Branch B", "", ""],
            ["", "", "Employee", "Role"],
            ["", "", "Bob", "Developer"],
        ]
        res = self.parser.parse_grid(grid)
        val_res = validate_parse_output(res, self.config)

        self.assertTrue(val_res.is_valid)
        self.assertEqual(len(val_res.errors), 0)

        tables = res["tables"]
        parent = tables[0]
        child1 = tables[1]
        child2 = tables[2]

        self.assertIn(child1["table_id"], parent["children"])
        self.assertIn(child2["table_id"], parent["children"])
        self.assertEqual(child1["parent_id"], parent["table_id"])
        self.assertEqual(child2["parent_id"], parent["table_id"])

    def test_valid_orphan_table_schema(self):
        grid = [
            ["", "", "Orphan Table Level 2", ""],
            ["", "", "", "Metric"],
            ["", "", "", "100"],
        ]
        res = self.parser.parse_grid(grid)
        val_res = validate_parse_output(res, self.config)

        self.assertTrue(val_res.is_valid)
        self.assertEqual(len(res["orphan_tables"]), 1)
        orphan = res["orphan_tables"][0]
        self.assertIsNone(orphan["parent_id"])
        self.assertEqual(orphan["level"], 2)
        self.assertIn(warnings.ORPHAN_TABLE, orphan["warnings"])

    def test_valid_unclassified_rows_schema(self):
        grid = [
            ["[BEGIN DATA]"],
            ["Standalone text note outside tables"],
            ["Table Title", "", ""],
            ["", "Col1", "Col2"],
            ["", "Val1", "Val2"],
        ]
        res = self.parser.parse_grid(grid)
        val_res = validate_parse_output(res, self.config)

        self.assertTrue(val_res.is_valid)
        self.assertEqual(len(res["unclassified_rows"]), 1)
        u_row = res["unclassified_rows"][0]
        self.assertEqual(u_row["cells"][0]["value"], "Standalone text note outside tables")
        self.assertIn(warnings.UNCLASSIFIED_DATA, u_row["warnings"])

    # --- Negative / Schema Violation Tests ---

    def test_negative_missing_top_level_metadata(self):
        malformed = {
            "tables": [],
            "orphan_tables": [],
            "unclassified_rows": [],
        }
        val_res = self.validator.validate(malformed)
        self.assertFalse(val_res.is_valid)
        self.assertTrue(any(e.code == schema.ERR_MISSING_METADATA for e in val_res.errors))

    def test_negative_confidence_out_of_bounds(self):
        grid = [
            ["Test Table", ""],
            ["", "Col1"],
            ["", "Val1"],
        ]
        res = self.parser.parse_grid(grid)
        res["tables"][0]["confidence"] = 1.5  # Invalid out of bounds

        val_res = self.validator.validate(res)
        self.assertFalse(val_res.is_valid)
        self.assertTrue(any(e.code == schema.ERR_CONFIDENCE_OUT_OF_BOUNDS for e in val_res.errors))

    def test_negative_invalid_coordinates(self):
        grid = [
            ["Test Table", ""],
            ["", "Col1"],
            ["", "Val1"],
        ]
        res = self.parser.parse_grid(grid)
        # Corrupt data_range coordinates: start_row > end_row
        res["tables"][0]["data_range"]["start_row"] = 10
        res["tables"][0]["data_range"]["end_row"] = 2

        val_res = self.validator.validate(res)
        self.assertFalse(val_res.is_valid)
        self.assertTrue(any(e.code == schema.ERR_INVALID_COORDINATES for e in val_res.errors))

    def test_negative_record_key_mismatch(self):
        grid = [
            ["Test Table", "", ""],
            ["", "Col1", "Col2"],
            ["", "Val1", "Val2"],
        ]
        res = self.parser.parse_grid(grid)
        # Alter record to have mismatch key
        res["tables"][0]["records"][0] = {"Col1": "Val1", "WrongKey": "Val2"}

        val_res = self.validator.validate(res)
        self.assertFalse(val_res.is_valid)
        self.assertTrue(any(e.code == schema.ERR_RECORD_KEY_MISMATCH for e in val_res.errors))

    def test_negative_duplicate_column_key(self):
        grid = [
            ["Test Table", "", ""],
            ["", "Col1", "Col2"],
            ["", "Val1", "Val2"],
        ]
        res = self.parser.parse_grid(grid)
        # Duplicate string in columns definition
        res["tables"][0]["columns"] = ["Col1", "Col1"]

        val_res = self.validator.validate(res)
        self.assertFalse(val_res.is_valid)
        self.assertTrue(any(e.code == schema.ERR_DUPLICATE_COLUMN_KEY for e in val_res.errors))

    def test_negative_hierarchy_missing_parent(self):
        grid = [
            ["Parent Table", "", ""],
            ["", "Child Table", "", ""],
            ["", "", "H1", "H2"],
            ["", "", "V1", "V2"],
        ]
        res = self.parser.parse_grid(grid)
        # Point child to non-existent parent_id
        res["tables"][1]["parent_id"] = "non_existent_tbl_999"

        val_res = self.validator.validate(res)
        self.assertFalse(val_res.is_valid)
        self.assertTrue(any(e.code == schema.ERR_HIERARCHY_MISSING_PARENT for e in val_res.errors))

    def test_negative_hierarchy_child_parent_mismatch(self):
        grid = [
            ["Parent Table", "", ""],
            ["", "Child Table", "", ""],
            ["", "", "H1", "H2"],
            ["", "", "V1", "V2"],
        ]
        res = self.parser.parse_grid(grid)
        # Parent lists child, but child specifies different parent_id
        res["tables"][1]["parent_id"] = None

        val_res = self.validator.validate(res)
        self.assertFalse(val_res.is_valid)
        self.assertTrue(any(e.code == schema.ERR_HIERARCHY_CHILD_PARENT_MISMATCH for e in val_res.errors))

    def test_negative_hierarchy_cycle(self):
        grid = [
            ["Table A", "", ""],
            ["", "Table B", "", ""],
            ["", "", "H1", "H2"],
            ["", "", "V1", "V2"],
        ]
        res = self.parser.parse_grid(grid)
        # Create cycle: Table A's parent_id = Table B's table_id
        tbl_a_id = res["tables"][0]["table_id"]
        tbl_b_id = res["tables"][1]["table_id"]

        res["tables"][0]["parent_id"] = tbl_b_id
        res["tables"][1]["parent_id"] = tbl_a_id

        val_res = self.validator.validate(res)
        self.assertFalse(val_res.is_valid)
        self.assertTrue(any(e.code == schema.ERR_HIERARCHY_CYCLE_DETECTED for e in val_res.errors))

    def test_negative_orphan_has_parent(self):
        grid = [
            ["", "", "Orphan Table", ""],
            ["", "", "", "H1"],
            ["", "", "", "V1"],
        ]
        res = self.parser.parse_grid(grid)
        res["orphan_tables"][0]["parent_id"] = "tbl_001"

        val_res = self.validator.validate(res)
        self.assertFalse(val_res.is_valid)
        self.assertTrue(any(e.code == schema.ERR_ORPHAN_HAS_PARENT for e in val_res.errors))

    # --- Duplicate & Missing Header Handling ---

    def test_duplicate_header_validation_and_column_keys(self):
        grid = [
            ["Duplicate Header Table", "", ""],
            ["", "Status", "Status"],  # Duplicate display labels
            ["", "Active", "Pending"],
        ]
        res = self.parser.parse_grid(grid)
        val_res = validate_parse_output(res, self.config)

        self.assertTrue(val_res.is_valid)
        table = res["tables"][0]
        self.assertEqual(table["columns"], ["Status", "Status_2"])
        self.assertEqual(table["column_details"][0]["label"], "Status")
        self.assertEqual(table["column_details"][0]["key"], "Status")
        self.assertEqual(table["column_details"][1]["label"], "Status")
        self.assertEqual(table["column_details"][1]["key"], "Status_2")
        self.assertEqual(table["records"][0], {"Status": "Active", "Status_2": "Pending"})
        self.assertIn(warnings.DUPLICATE_HEADER, table["warnings"])

    def test_missing_header_validation_and_fallback_keys(self):
        grid = [
            ["", "Parent Headerless Table", ""],
            ["", "", "Child Table Title", ""],
            ["", "", "", "Header1"],
            ["", "", "", "Val1"],
        ]
        res = self.parser.parse_grid(grid)
        val_res = validate_parse_output(res, self.config)

        self.assertTrue(val_res.is_valid)
        orphan_table = res["orphan_tables"][0]
        self.assertIn("Col_2", orphan_table["columns"])
        self.assertIn(warnings.MISSING_HEADER, orphan_table["warnings"])

    # --- Determinism Test ---

    def test_deterministic_parser_output(self):
        grid = [
            ["[BEGIN DATA]"],
            ["Region North", "", "", ""],
            ["", "Store 101", "", ""],
            ["", "", "Status", "Status"],
            ["", "", "Active", "Closed"],
            ["", "Store 102", "", ""],
            ["", "", "Item", "Price"],
            ["", "", "Gadget", "100"],
            ["Unclassified footer note line"],
        ]

        res1 = self.parser.parse_grid(grid)
        res2 = self.parser.parse_grid(grid)

        self.assertEqual(res1, res2)
        self.assertTrue(validate_parse_output(res1).is_valid)
        self.assertTrue(validate_parse_output(res2).is_valid)


if __name__ == "__main__":
    unittest.main()
