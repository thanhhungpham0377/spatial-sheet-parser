# Spatial Sheet Parser

Deterministic spatial spreadsheet parser for Google Sheets / TSV / CSV matrices with structural hierarchy detection, explicit data region boundaries, loss-free data traceability, and schema contract validation.

---

## 1. Requirements & Setup

* **Python:** 3.10+ (Tested on Python 3.10, 3.11, 3.12, 3.14)
* **Dependencies:** `openpyxl>=3.1.0` (.xlsx), `xlrd>=2.0.1` (.xls), `odfpy>=1.4.1` (.ods). All dependencies are bundled automatically in the packaged standalone EXE.

### Installation from clean checkout

```bash
# Option A: Install in editable mode
pip install -e .

# Option B: Create virtual environment and install dev dependencies
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -e .[dev]
```

---

## 2. Verification Command

Run the full test suite using Python standard library `unittest`:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

If `pytest` is installed in your environment:

```bash
pytest -v
```

---

## 3. Usage & Examples

### Local Web Surface (Browser Interface)

Run the local web application server from Windows PowerShell:

```powershell
python -m spatial_sheet_parser.web
```

Then open your browser at:
`http://127.0.0.1:8080/`

You can drag & drop `.xlsx`, `.tsv`, `.csv`, or `.json` files directly into the web surface, or paste matrix text. Non-ASCII Vietnamese filenames (such as `Bảng tính không có tiêu đề.xlsx`) are fully supported via Uint8Array Base64 binary chunking.

### Staged Progress Pipeline (6 Steps)

The web UI processes spreadsheet workbooks through a 6-step progress pipeline:
1. **Reading file:** Reads local file into memory via `FileReader.readAsArrayBuffer` (binary) or text reader without UTF-8 corruption.
2. **Preparing upload:** Constructs JSON payload, verifies format parameters, and attaches a client request correlation ID (`X-Request-ID`).
3. **Uploading:** Transmits payload to `/api/parse` with timeout (30s) and cancellation abort support (`AbortController`).
4. **Parsing workbook:** Server ingests grid matrix via `openpyxl`/adapters and runs spatial hierarchy detection.
5. **Building result:** Renders human-readable summary preview, tabular structural cards, and JSON output tree.
6. **Completed:** Displays full metrics and unlocks copy/download actions. In case of failure, the error panel pinpoints the exact step that failed.

### Server Health Check Endpoint

Check server liveness and version:
```bash
curl http://127.0.0.1:8080/api/health
# Response: {"status": "ok", "version": "0.1.0", "app": "Spatial Sheet Parser", "timestamp": "...", "request_id": "..."}
```

Optional command arguments:
```powershell
# Launch on a custom port and automatically open default browser
python -m spatial_sheet_parser.web --port 8080 --open
```

### CLI Surface Examples

```bash
# 1. Display CLI help and options
python -m spatial_sheet_parser.cli --help

# 2. Parse an Excel (.xlsx) file (default active sheet) with terminal preview
python -m spatial_sheet_parser.cli parse tests/fixtures/sample_workbook.xlsx --preview

# 3. Parse a specific worksheet from an Excel (.xlsx) workbook
python -m spatial_sheet_parser.cli parse tests/fixtures/sample_workbook.xlsx --sheet Inventory --preview

# 4. Parse a TSV file and output human-readable terminal preview
python -m spatial_sheet_parser.cli parse tests/fixtures/sample_financial_report.tsv --preview

# 5. Parse a CSV file and export JSON contract result to file
python -m spatial_sheet_parser.cli parse tests/fixtures/sample_inventory.csv --out result.json

# 6. Parse JSON grid input from stdin (-) using pipe
cat tests/fixtures/sample_nested_grid.json | python -m spatial_sheet_parser.cli parse - --format json

# 7. Use custom JSON configuration and combine output with terminal preview
python -m spatial_sheet_parser.cli parse tests/fixtures/sample_financial_report.tsv --config custom_config.json --out result.json --preview
```

### Python API Usage Example

```python
from spatial_sheet_parser import SpatialSheetParser, ParserConfig, validate_parse_output

# 1. Initialize custom or default parser configuration (optional sheet_name)
config = ParserConfig(
    title_columns=[0, 1, 2],
    table_offset=1,
    max_blank_rows=1,
    explicit_markers=["[BEGIN DATA]", "[TABLE]"],
    merged_cell_policy="top_left_only",
    sheet_name="Inventory"  # Optional sheet selection default
)

# 2. Create parser instance
parser = SpatialSheetParser(config=config)

# 3. Ingest Excel workbook file path or binary bytes
result = parser.parse_grid("tests/fixtures/sample_workbook.xlsx", source_format="xlsx", sheet_name="Inventory")

# 4. Inspect result tree and contract validation status
print(f"Source Format: {result['metadata']['source_format']}")
print(f"Sheet Name: {result['metadata']['sheet_name']}")
print(f"Is Valid: {result['metadata']['validation']['is_valid']}")
print(f"Tables Detected: {len(result['tables'])}")

# 5. Re-validate result contract directly
val_result = validate_parse_output(result, config)
assert val_result.is_valid
```

---

## 4. Parser Configuration Specification

| Parameter | Type | Default | Description |
|---|---|---|---|
| `title_columns` | `List[int]` | `[0, 1, 2]` | Column indices evaluated as table title candidates |
| `table_offset` | `int` | `1` | Column offset relative to title column for header anchor (`title_col + table_offset`) |
| `max_blank_rows` | `int` | `1` | Maximum allowable consecutive blank rows before ending table record range |
| `header_rows` | `int` | `1` | Expected header rows count per table candidate |
| `explicit_markers` | `List[str]` | `["[BEGIN DATA]", "[TABLE]"]` | Explicit spatial delimiter tags |
| `merged_cell_policy` | `str` | `"top_left_only"` | Policy for merged cell resolution (`top_left_only`) |
| `strictness` | `str` | `"balanced"` | Structural strictness level (`strict`, `balanced`, `permissive`) |
| `sheet_name` | `Optional[str]` | `None` | Optional worksheet name to select from Excel workbooks |

---

## 5. Standard Output JSON Contract Summary

```json
{
  "metadata": {
    "parser_version": "0.1.0",
    "source_format": "tsv",
    "sheet_name": "SalesSheet",
    "toc_summary": [
      {"row": 0, "content": "Company Financial Report 2026"}
    ],
    "data_start_row": 3,
    "warnings": ["MERGED_CELL_DETECTED"],
    "validation": {
      "is_valid": true,
      "error_count": 0,
      "warning_count": 0,
      "errors": [],
      "warnings": []
    }
  },
  "tables": [
    {
      "table_id": "tbl_001",
      "title": "Corporate Group Alpha",
      "level": 0,
      "parent_id": null,
      "title_cell": {"row": 3, "col": 0},
      "anchor_column": 1,
      "data_range": {"start_row": 3, "start_col": 0, "end_row": 10, "end_col": 4},
      "header_row": 4,
      "record_start_row": 5,
      "record_end_row": 10,
      "columns": ["Item Name", "Revenue"],
      "column_details": [
        {"key": "Item Name", "label": "Item Name", "col_index": 1},
        {"key": "Revenue", "label": "Revenue", "col_index": 2}
      ],
      "records": [
        {"Item Name": "Product A1", "Revenue": "10000"}
      ],
      "children": ["tbl_002"],
      "confidence": 1.0,
      "warnings": []
    }
  ],
  "orphan_tables": [],
  "unclassified_rows": []
}
```

---

## 6. Warning Taxonomy Reference

* `AMBIGUOUS_TABLE_TITLE`: Table title candidate lacks sufficient spatial supporting evidence.
* `MISSING_HEADER`: Table candidate detected without a valid header row.
* `EMPTY_RECORDS`: Header row found but no records present in data range.
* `DUPLICATE_HEADER`: Multiple columns share identical display headers (resolved with stable suffix keys like `Header_2`).
* `LEVEL_SKIPPED`: Indentation jumped more than one level without intermediate parent.
* `ORPHAN_TABLE`: Table has no valid parent in hierarchy (level > 0 without ancestor).
* `UNEXPECTED_BLANK_ROW`: Blank row encountered within record region.
* `POSSIBLE_FOOTER`: Single-cell summary or total row detected after records.
* `MERGED_CELL_DETECTED`: Merged cells encountered in grid.
* `TRUNCATED_TABLE`: Table boundary truncated by explicit marker or EOF.
* `UNCLASSIFIED_DATA`: Non-empty cell/row not included in any table structure.

---

## 7. Format Support Matrix & Google Sheets Ingestion Guide

### Spreadsheet Format Gateway

| Format Extension | Format ID | Underlying Engine | Binary / Text | Multi-Sheet Support | Merged Cell Support | Google Sheets Export Compatible |
|---|---|---|---|---|---|---|
| `.xlsx` | `xlsx` / `excel` | `openpyxl>=3.1.0` | Binary | Yes (`--sheet <name>`) | Yes (top-left policy) | Yes (`File -> Download -> Microsoft Excel`) |
| `.xls` | `xls` | `xlrd>=2.0.1` | Binary | Yes (`--sheet <name>`) | Yes (BIFF8 formatting) | N/A (Legacy format) |
| `.ods` | `ods` | `odfpy>=1.4.1` | Binary | Yes (`--sheet <name>`) | Yes (spanned cells) | Yes (`File -> Download -> OpenDocument`) |
| `.tsv` | `tsv` | Built-in text adapter | Text / UTF-8 BOM | Single Sheet | N/A | Yes (`File -> Download -> Tab-separated values`) |
| `.csv` | `csv` | Built-in CSV reader | Text / UTF-8 BOM | Single Sheet | N/A | Yes (`File -> Download -> Comma-separated values`) |
| `.json` | `json` | Built-in JSON grid reader | Text / Structure | Yes (`sheet_name` attr) | Yes (`merged_cells` array) | N/A |

### Google Sheets Download & Ingestion Instructions

To process spreadsheets created or stored in **Google Sheets**:

1. **Download Export File from Google Sheets UI**:
   - Open your spreadsheet in Google Sheets.
   - Click **File** → **Download**.
   - Select your preferred export format:
     - **Microsoft Excel (.xlsx)** *(Recommended for multi-sheet workbooks with merged cells)*
     - **OpenDocument (.ods)**
     - **Tab-separated values (.tsv)** *(Active sheet only)*
     - **Comma-separated values (.csv)** *(Active sheet only)*

2. **Pass Downloaded File to Spatial Sheet Parser**:
   - **Local Web Interface**: Open `http://127.0.0.1:8080/`, drag & drop the downloaded file, and optionally specify the target worksheet name.
   - **CLI Execution**:
     ```powershell
     python -m spatial_sheet_parser.cli parse path/to/downloaded_sheet.xlsx --sheet "Sales 2026" --preview
     ```
   - **Python API**:
     ```python
     from spatial_sheet_parser import SpatialSheetParser

     parser = SpatialSheetParser()
     result = parser.parse_grid("path/to/downloaded_sheet.ods", sheet_name="Sales 2026")
     ```

> [!NOTE]
> Direct Google Sheets OAuth API network access and live URL scraping are deliberately excluded from this offline parser engine to guarantee fast, offline execution without credential requirements.

---

## 8. Limitations & MVP Scope Boundary

* **Single Sheet Scope per Invocation:** Analyzes one matrix grid/worksheet per invocation. For multi-sheet workbooks (`.xlsx`, `.xls`, `.ods`), pass `--sheet <name>` or `sheet_name="<name>"` to select a specific worksheet (defaults to active/first sheet).
* **Format Support:** Supports `.xlsx` (openpyxl), `.xls` (xlrd), `.ods` (odfpy), `.csv`, `.tsv`, and `.json`.
* **Single Header Row:** Supports 1 header row per table (`header_rows=1`). Multi-line stacked headers are flattened.
* **Vertical Record Orientation:** Designed for standard vertical record tables (row-based records). Horizontal matrix tables require configuration adapters.
* **Offline Processing Only:** Input grid matrices must be ingested as downloaded files (`.xlsx`, `.ods`, `.xls`, `.csv`, `.tsv`), raw JSON grids, or pasted text. Direct Google Sheets OAuth network API integration is out of scope for this task.

---

## 9. Architecture & Detailed Quality Documentation

* Architectural specification & module boundaries: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
* Testing strategy & quality assurance guide: [docs/TESTING_AND_QUALITY.md](docs/TESTING_AND_QUALITY.md)
* Windows portable executable packaging guide: [docs/PACKAGING.md](docs/PACKAGING.md)

---

## 10. Windows Portable Standalone EXE

The application is packaged as a portable single-file Windows executable:

* **Artifact Location:** `dist/spatial-sheet-parser.exe` (~11.31 MB)
* **Workbook Format Support:** Includes full `.xlsx`, `.xls`, and `.ods` workbook parsing via bundled `openpyxl`, `xlrd`, and `odfpy`.
* **Double-Click Behavior:** Starts local HTTP server on `127.0.0.1` (available port starting at 8080), opens default browser automatically, and serves web UI without requiring a console window.
* **CLI Execution:** Supports direct CLI usage from terminal (e.g. `.\dist\spatial-sheet-parser.exe parse tests\fixtures\sample_workbook.ods --sheet Inventory --preview`).

### Rebuild Executable
```powershell
python packaging/build_exe.py
```

### Troubleshooting & Process Conflicts

1. **Old Process / Port 8080 Conflict:**
   If a previously running server process is active on port 8080, query `GET http://127.0.0.1:8080/api/health` to check running version. If port 8080 is occupied by an older process, start the server on another port:
   ```powershell
   python -m spatial_sheet_parser.web --port 8085 --open
   ```
2. **Vietnamese / Non-ASCII Filenames:**
   Excel files with Vietnamese filenames (e.g. `Bảng tính không có tiêu đề.xlsx`) are read directly as binary `ArrayBuffer` and sent as Base64. Ensure JavaScript is enabled in your browser and do not manually edit the `[Binary Workbook Loaded: ...]` text placeholder in the text area.

---

## 11. Project Layout

```text
.
├── README.md                 # Setup, verification, CLI & API usage, contract summary
├── pyproject.toml            # Package metadata & build configuration
├── dist/
│   └── spatial-sheet-parser.exe # Portable single-file Windows executable
├── docs/
│   ├── ARCHITECTURE.md       # Architecture specification & contracts
│   ├── PACKAGING.md          # Windows portable EXE packaging guide
│   └── TESTING_AND_QUALITY.md# Test suite architecture & quality metrics
├── ai_docs/
│   ├── PRODUCT_SPEC.md       # Product requirements document
│   └── TODO.md               # Task queue manifest
├── packaging/
│   ├── build_exe.py          # Automated PyInstaller build script
│   ├── launcher.py           # Single-file double-click launcher entrypoint
│   └── spatial_sheet_parser.spec # PyInstaller specification
├── src/
│   └── spatial_sheet_parser/
│       ├── __init__.py       # Package exports & version
│       ├── adapters.py       # Input adapters (TSV, CSV, JSON, raw)
│       ├── cli.py            # CLI entrypoint & argument parser
│       ├── config.py         # ParserConfig dataclass model
│       ├── detection.py      # Region, marker, title & boundary detector
│       ├── grid.py           # Matrix Grid & Cell data structures
│       ├── hierarchy.py      # Parent-child table hierarchy builder
│       ├── parser.py         # Core SpatialSheetParser engine
│       ├── presentation.py   # Preview summary & JSON export formatters
│       ├── schema.py         # Output JSON contract schema definitions
│       ├── static/           # Web app static assets (index.html, style.css, app.js)
│       ├── validation.py     # Schema validation & integrity engine
│       ├── version.py        # Version string
│       ├── warnings.py       # Taxonomy warning constants
│       └── web.py            # Dependency-free HTTP server & web app module
└── tests/
    ├── fixtures/             # Realistic TSV, CSV, and JSON test fixtures
    ├── test_cli.py           # CLI integration tests
    ├── test_grid_adapters.py # Grid & input adapters unit tests
    ├── test_packaging.py     # Standalone EXE smoke test suite
    ├── test_parser_core.py   # Deterministic core engine unit tests
    ├── test_performance.py   # Large in-memory grid performance smoke test
    ├── test_regression.py    # Regression & fixture test suite
    ├── test_smoke.py         # Basic package smoke tests
    ├── test_validation_schema.py # Contract validation unit tests
    └── test_web.py           # Local web server & API integration tests
```
