# Windows Standalone Executable Packaging Guide

## Overview
Spatial Sheet Parser is packaged as a standalone, zero-dependency Windows executable (`spatial-sheet-parser.exe`) using PyInstaller.

## Artifact Details
* **Location:** `dist/spatial-sheet-parser.exe`
* **Size:** ~11.31 MB
* **Format:** Windows 64-bit single-file executable (`--onefile`, windowed mode)
* **Dependencies:** Self-contained Python runtime and bundled spreadsheet format dependencies (`openpyxl`, `xlrd`, `odfpy`, `et_xmlfile`, `defusedxml`). No local Python installation required.

## Quick Run Instructions

### 1. Double-Click Launch (GUI Web Mode)
Double-click `dist/spatial-sheet-parser.exe` in Windows Explorer:
- Starts local HTTP server on `127.0.0.1` using an available port (starting from `8080`).
- Automatically opens the default web browser to `http://127.0.0.1:8080/`.
- Serves drag-and-drop web UI supporting `.xlsx`, `.xls`, `.ods`, `.tsv`, `.csv`, and `.json` file uploads.
- Serves `/api/parse` JSON endpoint.

### 2. Command Line Execution (CLI Mode)
Run directly from PowerShell or CMD with arguments:

```powershell
# Display CLI help
.\dist\spatial-sheet-parser.exe --help

# Parse Excel (.xlsx) file with default sheet and terminal preview
.\dist\spatial-sheet-parser.exe parse tests\fixtures\sample_workbook.xlsx --preview

# Parse specific worksheet from Excel (.xlsx) workbook
.\dist\spatial-sheet-parser.exe parse tests\fixtures\sample_workbook.xlsx --sheet Inventory --preview

# Parse legacy Excel (.xls) or OpenDocument (.ods) file
.\dist\spatial-sheet-parser.exe parse tests\fixtures\sample_workbook.xls --preview
.\dist\spatial-sheet-parser.exe parse tests\fixtures\sample_workbook.ods --preview

# Parse TSV file with terminal preview
.\dist\spatial-sheet-parser.exe parse tests\fixtures\sample_financial_report.tsv --preview

# Export JSON contract result
.\dist\spatial-sheet-parser.exe parse tests\fixtures\sample_inventory.csv --out result.json
```

## Rebuilding the Executable

To rebuild the executable artifact from source:

```powershell
# 1. Activate virtual environment and install PyInstaller
python -m venv .venv
.\.venv\Scripts\activate
pip install pyinstaller

# 2. Run automated build script
python packaging/build_exe.py
```

Or run PyInstaller directly with the spec file:
```powershell
pyinstaller --clean --noconfirm --distpath dist packaging/spatial_sheet_parser.spec
```

## Antivirus & Windows SmartScreen Notice
Because `spatial-sheet-parser.exe` is an unsigned binary compiled via PyInstaller, Windows SmartScreen or antivirus software (e.g. Windows Defender) may present a warning on first execution:
- **Bypass for local use:** Click **"More info"** on the SmartScreen dialog and select **"Run anyway"**.
- **Production Distribution:** Sign the executable using `signtool.exe` with an Authenticode Code Signing Certificate.

## Packaging Verification & Testing
Run the full test suite and packaging smoke test:
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```
