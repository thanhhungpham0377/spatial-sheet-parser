# Spatial Sheet Parser — Testing & Quality Assurance

This document details the test strategy, suite structure, quality metrics, and performance verification for the Spatial Sheet Parser.

---

## 1. Test Suite Architecture

The test suite is built using Python's standard library `unittest` framework to ensure zero external test runner dependencies.

```text
tests/
├── fixtures/
│   ├── sample_financial_report.tsv    # Realistic TSV with TOC, [BEGIN DATA], nested tables, footers
│   ├── sample_inventory.csv           # Realistic CSV with level jumps, orphan tables, preamble
│   └── sample_nested_grid.json        # Realistic JSON grid with merged cells & hierarchy
├── test_smoke.py                      # Basic package import and CLI entrypoint sanity tests
├── test_grid_adapters.py              # Adapters (TSV, CSV, JSON) & Grid normalization unit tests
├── test_parser_core.py                # Core detection, boundaries, hierarchy, and warning rules
├── test_validation_schema.py          # Output JSON contract schema validation & error checks
├── test_cli.py                        # Integration tests for CLI arguments, stdin, preview, export
├── test_regression.py                 # Real-world fixture regression suite & determinism checks
└── test_performance.py                # Moderately sized in-memory grid performance smoke test
```

---

## 2. Key Quality Principles

1. **Zero Silent Data Loss:**
   Every cell and row in the matrix is either classified into a table structure or preserved in `unclassified_rows` with the `UNCLASSIFIED_DATA` warning code.
2. **Deterministic Output:**
   Given the exact same grid input and `ParserConfig`, repeated parser executions produce identical JSON result trees. verified by determinism regression tests (`test_deterministic_output_contract_integrity`).
3. **Contract Integrity:**
   All parser outputs are validated against the standard JSON schema using `validate_parse_output()`. Outputs containing schema violations fail validation with explicit error diagnostics.
4. **Resilience to Malformed Input:**
   Empty grids, whitespace-only rows, single-cell titles, irregular column lengths, and duplicate header labels do not crash the engine; appropriate warning codes (`DUPLICATE_HEADER`, `MISSING_HEADER`, `UNEXPECTED_BLANK_ROW`) and fallback keys (`Col_X`, `Header_2`) are assigned.

---

## 3. Real-World Fixture Test Coverage

| Fixture File | Source Format | Features Tested |
|---|---|---|
| `sample_financial_report.tsv` | TSV | TOC preambles, `[BEGIN DATA]`, 3-level hierarchy, duplicate headers, footers, unclassified notes |
| `sample_inventory.csv` | CSV | Level 0 -> Level 2 indentation jump, `ORPHAN_TABLE` classification, missing headers |
| `sample_nested_grid.json` | JSON Grid | Merged cell ranges, `top_left_only` policy, `MERGED_CELL_DETECTED` warnings |

---

## 4. Performance Smoke Benchmark

* **Grid Dimensions:** 2,000 rows × 10 columns (50 sections containing 100 hierarchical sub-tables and 50 unclassified rows).
* **Execution Time:** ~0.45 seconds on standard CPU hardware.
* **Threshold Limit:** Verified to execute within < 5.0 seconds without fragile hardcoded timing assertions.
* **Scalability:** Linear $O(N)$ row-scanning time complexity.

---

## 5. Running the Test Suite

Run the full test suite with standard library `unittest`:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

If `pytest` is installed in your development environment:

```bash
pytest -v
```
