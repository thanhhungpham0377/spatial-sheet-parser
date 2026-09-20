# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

spec_dir = os.path.abspath(SPECPATH)
project_root = os.path.abspath(os.path.join(spec_dir, ".."))
src_dir = os.path.join(project_root, "src")
static_dir = os.path.join(src_dir, "spatial_sheet_parser", "static")

datas = [
    (static_dir, os.path.join("spatial_sheet_parser", "static")),
]

hiddenimports = [
    "spatial_sheet_parser",
    "spatial_sheet_parser.adapters",
    "spatial_sheet_parser.cli",
    "spatial_sheet_parser.config",
    "spatial_sheet_parser.detection",
    "spatial_sheet_parser.grid",
    "spatial_sheet_parser.hierarchy",
    "spatial_sheet_parser.parser",
    "spatial_sheet_parser.presentation",
    "spatial_sheet_parser.schema",
    "spatial_sheet_parser.validation",
    "spatial_sheet_parser.version",
    "spatial_sheet_parser.warnings",
    "spatial_sheet_parser.web",
    "openpyxl",
    "et_xmlfile",
    "xlrd",
    "odf",
    "odf.opendocument",
    "odf.table",
    "odf.text",
    "odf.element",
    "defusedxml",
]

a = Analysis(
    ['launcher.py'],
    pathex=[src_dir, spec_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='spatial-sheet-parser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=os.path.join(spec_dir, 'version_info.txt'),
)
