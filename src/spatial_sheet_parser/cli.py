"""CLI entrypoint for Spatial Sheet Parser."""

import argparse
import json
import os
import sys
from typing import List, Optional

from spatial_sheet_parser.config import ParserConfig
from spatial_sheet_parser.parser import SpatialSheetParser
from spatial_sheet_parser.presentation import export_json, render_preview
from spatial_sheet_parser.version import __version__


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spatial-sheet-parser",
        description="Spatial Sheet Parser - Deterministic 2D grid matrix parser",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    parse_cmd = subparsers.add_parser("parse", help="Parse a spreadsheet matrix file")
    parse_cmd.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to input file (TSV/CSV/JSON/XLSX/XLS/ODS) or '-' for stdin",
    )
    parse_cmd.add_argument(
        "--format",
        "-f",
        choices=["tsv", "csv", "json", "xlsx", "excel", "xls", "ods"],
        help="Input source format (default: auto-detect)",
    )
    parse_cmd.add_argument(
        "--sheet",
        "--sheet-name",
        dest="sheet_name",
        help="Worksheet name to parse from workbook",
    )
    parse_cmd.add_argument(
        "--config",
        "-c",
        help="Path to JSON configuration file",
    )
    parse_cmd.add_argument(
        "--out",
        "-o",
        help="Path to output JSON result file",
    )
    parse_cmd.add_argument(
        "--preview",
        action="store_true",
        help="Output human-readable table summary to stdout",
    )
    return parser


def main(args: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = create_parser()

    if args is None:
        raw_args = sys.argv[1:]
    else:
        raw_args = list(args)

    if raw_args and raw_args[0] not in ("parse", "-h", "--help", "-v", "--version"):
        raw_args.insert(0, "parse")

    parsed_args = parser.parse_args(raw_args)

    if not parsed_args.command:
        parser.print_help()
        return 0

    if parsed_args.command == "parse":
        file_target = parsed_args.file

        # Determine format and binary vs text mode
        fmt = parsed_args.format
        source_file_path = file_target if file_target and file_target != "-" else None
        ext = os.path.splitext(source_file_path)[1].lower() if source_file_path else ""

        if not fmt:
            if ext in (".tsv",):
                fmt = "tsv"
            elif ext in (".csv",):
                fmt = "csv"
            elif ext in (".json",):
                fmt = "json"
            elif ext in (".xlsx", ".excel"):
                fmt = "xlsx"
            elif ext in (".xls",):
                fmt = "xls"
            elif ext in (".ods",):
                fmt = "ods"
            else:
                fmt = "raw"

        is_binary = (fmt in ("xlsx", "excel", "xls", "ods") or ext in (".xlsx", ".xls", ".ods"))

        # Read input content
        if file_target is None or file_target == "-":
            if sys.stdin.isatty() and file_target is None:
                sys.stderr.write("Error: Input file path or stdin content is required.\n")
                return 1
            if is_binary:
                content = sys.stdin.buffer.read()
            else:
                content = sys.stdin.read()
        else:
            if not os.path.exists(file_target):
                sys.stderr.write(f"Error: File not found: {file_target}\n")
                return 1
            try:
                if is_binary:
                    with open(file_target, "rb") as f:
                        content = f.read()
                else:
                    with open(file_target, "r", encoding="utf-8-sig") as f:
                        content = f.read()
            except Exception as e:
                sys.stderr.write(f"Error reading file '{file_target}': {e}\n")
                return 1

        if not content or (isinstance(content, str) and not content.strip()):
            sys.stderr.write("Error: Input content is empty.\n")
            return 1

        # Load configuration
        config = ParserConfig()
        if parsed_args.config:
            if not os.path.exists(parsed_args.config):
                sys.stderr.write(f"Error: Configuration file not found: {parsed_args.config}\n")
                return 1
            try:
                with open(parsed_args.config, "r", encoding="utf-8") as f:
                    cfg_dict = json.load(f)
                config = ParserConfig.from_dict(cfg_dict)
            except Exception as e:
                sys.stderr.write(f"Error loading configuration file '{parsed_args.config}': {e}\n")
                return 1

        # Execute parser engine
        try:
            sp_parser = SpatialSheetParser(config=config)
            result = sp_parser.parse_grid(
                content,
                source_format=fmt,
                sheet_name=parsed_args.sheet_name,
            )
        except Exception as e:
            sys.stderr.write(f"Error parsing input grid: {e}\n")
            return 1

        # Check validation
        validation_info = result.get("metadata", {}).get("validation", {})
        is_valid = validation_info.get("is_valid", True)
        if not is_valid:
            err_cnt = validation_info.get("error_count", 0)
            sys.stderr.write(f"Error: Parsed output failed contract validation: {err_cnt} error(s).\n")

        # Formatting / Output
        formatted_json = export_json(result)

        if parsed_args.out:
            try:
                out_dir = os.path.dirname(parsed_args.out)
                if out_dir and not os.path.exists(out_dir):
                    os.makedirs(out_dir, exist_ok=True)
                with open(parsed_args.out, "w", encoding="utf-8") as f:
                    f.write(formatted_json + "\n")
            except Exception as e:
                sys.stderr.write(f"Error writing output file '{parsed_args.out}': {e}\n")
                return 1

        if parsed_args.preview:
            preview_str = render_preview(result)
            sys.stdout.write(preview_str + "\n")
        elif not parsed_args.out:
            sys.stdout.write(formatted_json + "\n")

        return 0 if is_valid else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
