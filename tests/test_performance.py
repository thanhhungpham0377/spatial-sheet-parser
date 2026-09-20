"""Performance smoke check on moderately sized in-memory spreadsheet grids (SSP-005)."""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from spatial_sheet_parser import ParserConfig, SpatialSheetParser, validate_parse_output


class TestPerformance(unittest.TestCase):
    """Smoke test for performance and scalability on large/moderate in-memory grids."""

    def test_moderate_grid_performance_smoke_check(self):
        """Generates a 2,000 row x 10 column grid with 50 sub-tables and parses it."""
        config = ParserConfig()
        parser = SpatialSheetParser(config)

        matrix = []
        num_sections = 50
        rows_per_section = 40  # Total 2,000 rows

        for s in range(num_sections):
            # Section root title (Level 0)
            matrix.append([f"Region Section {s+1}", "", "", "", "", "", "", "", "", ""])
            # Sub-table title (Level 1)
            matrix.append(["", f"District Sub {s+1}", "", "", "", "", "", "", "", ""])
            # Header row
            matrix.append(["", "", "Metric_A", "Metric_B", "Metric_C", "Status", "", "", "", ""])
            # Record rows (34 records per section)
            for r in range(rows_per_section - 6):
                matrix.append(["", "", f"Val_{s}_{r}_A", f"Val_{s}_{r}_B", f"{r * 10}", "Active", "", "", "", ""])
            # 2 Blank rows to exceed max_blank_rows (1) and end table boundary
            matrix.append(["", "", "", "", "", "", "", "", "", ""])
            matrix.append(["", "", "", "", "", "", "", "", "", ""])
            # Unclassified row outside table boundary
            matrix.append(["", "", "", "", "", "", "Standalone Note Outside Table", "", "", ""])

        total_rows = len(matrix)
        self.assertEqual(total_rows, 2000)

        t_start = time.perf_counter()
        result = parser.parse_grid(matrix)
        t_elapsed = time.perf_counter() - t_start

        # Verification
        self.assertTrue(t_elapsed < 5.0, f"Parsing 2,000 rows took {t_elapsed:.2f}s, exceeding 5.0s limit")
        validation_res = validate_parse_output(result, config)
        self.assertTrue(validation_res.is_valid, f"Validation errors: {validation_res.errors}")

        # Total tables = 50 Level 0 + 50 Level 1 = 100 tables
        tot_tables = len(result["tables"]) + len(result["orphan_tables"])
        self.assertEqual(tot_tables, 100)
        self.assertEqual(len(result["unclassified_rows"]), 50)


if __name__ == "__main__":
    unittest.main()
