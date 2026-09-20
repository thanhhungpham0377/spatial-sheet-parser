"""Local web application server for Spatial Sheet Parser."""

import argparse
import http.server
import json
import os
import sys
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

# Ensure package root is in sys.path when executed directly
_PACKAGE_PARENT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PACKAGE_PARENT not in sys.path:
    sys.path.insert(0, _PACKAGE_PARENT)

from spatial_sheet_parser.config import ParserConfig
from spatial_sheet_parser.parser import SpatialSheetParser
from spatial_sheet_parser.presentation import render_preview, render_markdown_tables
from spatial_sheet_parser.version import __version__, __author__, __copyright__

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    STATIC_DIR = os.path.join(sys._MEIPASS, "spatial_sheet_parser", "static")
else:
    STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

MAX_REQUEST_SIZE = 50 * 1024 * 1024  # 50 MB payload safety limit

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".txt": "text/plain; charset=utf-8",
}


if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _try_fetch_google_sheet(url_or_json: str) -> Tuple[Optional[bytes], Optional[str]]:
    import re
    import urllib.request

    clean = url_or_json.strip()
    if clean.startswith("{") and "docs.google.com" in clean:
        try:
            data = json.loads(clean)
            clean = data.get("url", clean)
        except Exception:
            pass

    match = re.search(r"https?://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)", clean)
    if not match:
        return None, None

    sheet_id = match.group(1)
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        req = urllib.request.Request(
            export_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SpatialSheetParser/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read()
            if raw.startswith(b"PK\x03\x04") or "spreadsheet" in content_type:
                return raw, "xlsx"
    except Exception:
        pass
    return None, sheet_id


class SpatialSheetHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    """HTTP request handler serving local web UI and JSON parsing API."""

    server_version = f"SpatialSheetParserWeb/{__version__}"

    def log_message(self, format: str, *args: Any) -> None:
        """Controlled logging to suppress noise during automated unit tests."""
        if getattr(self.server, "quiet", False) or sys.stderr is None:
            return
        try:
            super().log_message(format, *args)
        except UnicodeEncodeError:
            try:
                msg = format % args
                sys.stderr.buffer.write(
                    f"{self.address_string()} - - [{self.log_date_time_string()}] {msg}\n".encode("utf-8", errors="replace")
                )
            except Exception:
                pass


    def do_GET(self) -> None:
        """Handle GET requests for index page and static assets."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path in ("/", "/index.html"):
            index_path = os.path.join(STATIC_DIR, "index.html")
            self._serve_file(index_path, "text/html; charset=utf-8")
            return

        if path in ("/api/health", "/api/version"):
            import datetime
            now = datetime.datetime.now(datetime.timezone.utc)
            timestamp = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            req_id = self.headers.get("X-Request-ID") or f"req-{int(now.timestamp() * 1000)}"
            self._send_json(
                {
                    "status": "ok",
                    "version": __version__,
                    "app": "Spatial Sheet Parser",
                    "author": __author__,
                    "copyright": __copyright__,
                    "max_upload_size_mb": 50,
                    "timestamp": timestamp,
                    "request_id": req_id,
                },
                status=200,
                request_id=req_id,
            )
            return

        if path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            safe_target = os.path.normpath(os.path.join(STATIC_DIR, rel_path))

            # Security check: prevent directory traversal outside STATIC_DIR
            try:
                common = os.path.commonpath([STATIC_DIR, safe_target])
            except ValueError:
                common = ""

            if common == STATIC_DIR and os.path.isfile(safe_target):
                ext = os.path.splitext(safe_target)[1].lower()
                mime = MIME_TYPES.get(ext, "application/octet-stream")
                self._serve_file(safe_target, mime)
                return

            self._send_error_json("Static asset not found.", status=404)
            return

        self._send_error_json("Endpoint not found.", status=404)

    def do_POST(self) -> None:
        """Handle POST requests for spreadsheet parsing API."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path in ("/api/parse", "/parse"):
            content_length_header = self.headers.get("Content-Length")
            req_id = self.headers.get("X-Request-ID")
            if not content_length_header:
                self._send_error_json("Missing Content-Length header.", status=400, request_id=req_id)
                return

            try:
                content_length = int(content_length_header)
            except ValueError:
                self._send_error_json("Invalid Content-Length header.", status=400, request_id=req_id)
                return

            # Safety check: enforce maximum allowable request size
            if content_length > MAX_REQUEST_SIZE:
                limit_mb = MAX_REQUEST_SIZE // (1024 * 1024)
                self._send_error_json(
                    f"Payload exceeds maximum allowed limit of {limit_mb}MB.",
                    status=413,
                    request_id=req_id,
                )
                return

            if content_length <= 0:
                self._send_error_json("Request payload body cannot be empty.", status=400, request_id=req_id)
                return

            import base64

            filename = None
            try:
                raw_body = self.rfile.read(content_length)
                if raw_body.startswith(b"PK\x03\x04") or raw_body.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
                    grid_content = raw_body
                    fmt_input = "auto"
                    sheet_name = None
                    config = ParserConfig()
                else:
                    try:
                        payload = json.loads(raw_body.decode("utf-8"))
                    except json.JSONDecodeError as e:
                        self._send_error_json(f"Invalid JSON payload body: {e}", status=400, request_id=req_id)
                        return
                    except Exception as e:
                        self._send_error_json(f"Failed to read request body: {e}", status=400, request_id=req_id)
                        return

                    if not isinstance(payload, dict):
                        self._send_error_json("JSON payload must be an object.", status=400, request_id=req_id)
                        return

                    if not req_id and payload.get("request_id"):
                        req_id = str(payload.get("request_id"))

                    filename = payload.get("filename")
                    if filename is not None and not isinstance(filename, str):
                        filename = str(filename)

                    content = payload.get("content", "")
                    if not content or (isinstance(content, str) and not content.strip()):
                        self._send_error_json(
                            "Input spreadsheet content is empty.",
                            status=400,
                            request_id=req_id,
                            details={
                                "filename": filename or "N/A",
                                "format": str(payload.get("format", "auto")),
                                "sheet_name": str(payload.get("sheet_name") or "Default"),
                                "exception_type": "ValueError",
                                "exception_message": "Input spreadsheet content is empty.",
                            },
                        )
                        return

                    fmt_input = str(payload.get("format", "auto")).lower()
                    sheet_name = payload.get("sheet_name")
                    if sheet_name is not None and not isinstance(sheet_name, str):
                        sheet_name = str(sheet_name)

                    encoding = payload.get("encoding", "")
                    if isinstance(content, str) and ("docs.google.com/spreadsheets" in content or content.strip().startswith('{"url":')):
                        raw_sheet, sheet_id = _try_fetch_google_sheet(content)
                        if raw_sheet:
                            grid_content = raw_sheet
                            fmt_input = "xlsx"
                        else:
                            self._send_error_json(
                                "Không thể tải trực tiếp bảng tính Google Sheets này do giới hạn quyền riêng tư. "
                                "Cách mở nhanh: Trong Google Sheets, chọn menu Tệp (File) > Tải xuống (Download) > Microsoft Excel (.xlsx), "
                                "sau đó chọn file .xlsx vừa tải vào ứng dụng, hoặc copy các ô rồi dán trực tiếp vào đây.",
                                status=400,
                                request_id=req_id,
                            )
                            return
                    elif encoding == "base64" or fmt_input in ("xlsx", "excel", "xls", "ods", "xlsm", "xltx", "xltm") or (isinstance(content, str) and content.startswith("data:")):
                        if isinstance(content, str):
                            clean_str = content.split(",", 1)[-1] if content.startswith("data:") else content
                            try:
                                grid_content = base64.b64decode(clean_str)
                            except Exception as e:
                                self._send_error_json(
                                    f"Invalid base64 payload: {e}",
                                    status=400,
                                    request_id=req_id,
                                    details={
                                        "filename": filename or "N/A",
                                        "format": fmt_input,
                                        "sheet_name": sheet_name or "Default",
                                        "exception_type": type(e).__name__,
                                        "exception_message": f"Invalid base64 payload: {e}",
                                    },
                                )
                                return
                        else:
                            grid_content = content
                    else:
                        grid_content = content

                    config_dict = payload.get("config")
                    config = ParserConfig()
                    if isinstance(config_dict, dict):
                        try:
                            config = ParserConfig.from_dict(config_dict)
                        except Exception as e:
                            self._send_error_json(
                                f"Invalid configuration parameters: {e}",
                                status=400,
                                request_id=req_id,
                                details={
                                    "filename": filename or "N/A",
                                    "format": fmt_input,
                                    "sheet_name": sheet_name or "Default",
                                    "exception_type": type(e).__name__,
                                    "exception_message": f"Invalid configuration parameters: {e}",
                                },
                            )
                            return
            except Exception as e:
                self._send_error_json(f"Failed to read request body: {e}", status=400, request_id=req_id)
                return

            # Format resolution
            source_format = "raw" if fmt_input in ("auto", "raw") else fmt_input

            try:
                from spatial_sheet_parser.adapters import normalize_input
                norm_grid = normalize_input(
                    grid_input=grid_content,
                    source_format=source_format,
                    sheet_name=sheet_name,
                    merged_cell_policy=config.merged_cell_policy,
                )
                actual_format = norm_grid.source_format if norm_grid.source_format else source_format
                parser = SpatialSheetParser(config=config)
                result = parser.parse_grid(
                    grid=norm_grid,
                    source_format=actual_format,
                    sheet_name=sheet_name,
                )
                result["metadata"]["grid_dimensions"] = {
                    "rows": norm_grid.num_rows,
                    "cols": norm_grid.num_cols,
                }
                preview = render_preview(result)
                markdown_text = render_markdown_tables(result)

                response_data = {
                    "success": True,
                    "request_id": req_id or f"req-{int(urllib.parse.time.time() * 1000) if hasattr(urllib.parse, 'time') else 0}",
                    "result": result,
                    "preview": preview,
                    "markdown": markdown_text,
                    "metadata_summary": {
                        "filename": filename or "N/A",
                        "source_format": result["metadata"].get("source_format"),
                        "sheet_name": result["metadata"].get("sheet_name"),
                        "num_rows": norm_grid.num_rows,
                        "num_cols": norm_grid.num_cols,
                        "total_tables": len(result.get("tables", [])) + len(result.get("orphan_tables", [])),
                        "unclassified_rows": len(result.get("unclassified_rows", [])),
                        "warnings_count": len(result["metadata"].get("warnings", [])),
                    },
                }
                if not response_data["request_id"].startswith("req-"):
                    import time
                    response_data["request_id"] = f"req-{int(time.time() * 1000)}"
                self._send_json(response_data, status=200, request_id=response_data["request_id"])
            except Exception as e:
                err_details = {
                    "filename": filename or "N/A",
                    "format": source_format,
                    "sheet_name": sheet_name or "Default / Active Sheet",
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                }
                self._send_error_json(
                    f"Error parsing spreadsheet matrix: {e}",
                    status=400,
                    request_id=req_id,
                    details=err_details,
                )
            return

        if path in ("/api/sheets", "/sheets"):
            content_length_header = self.headers.get("Content-Length")
            req_id = self.headers.get("X-Request-ID")
            if not content_length_header:
                self._send_error_json("Missing Content-Length header.", status=400, request_id=req_id)
                return

            try:
                content_length = int(content_length_header)
            except ValueError:
                self._send_error_json("Invalid Content-Length header.", status=400, request_id=req_id)
                return

            if content_length > MAX_REQUEST_SIZE:
                limit_mb = MAX_REQUEST_SIZE // (1024 * 1024)
                self._send_error_json(
                    f"Payload exceeds maximum allowed limit of {limit_mb}MB.",
                    status=413,
                    request_id=req_id,
                )
                return

            if content_length <= 0:
                self._send_error_json("Request payload body cannot be empty.", status=400, request_id=req_id)
                return

            import base64

            try:
                raw_body = self.rfile.read(content_length)
                if raw_body.startswith(b"PK\x03\x04") or raw_body.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
                    grid_content = raw_body
                    fmt_input = "auto"
                else:
                    try:
                        payload = json.loads(raw_body.decode("utf-8"))
                    except json.JSONDecodeError as e:
                        self._send_error_json(f"Invalid JSON payload body: {e}", status=400, request_id=req_id)
                        return
                    except Exception as e:
                        self._send_error_json(f"Failed to read request body: {e}", status=400, request_id=req_id)
                        return

                    if not isinstance(payload, dict):
                        self._send_error_json("JSON payload must be an object.", status=400, request_id=req_id)
                        return

                    if not req_id and payload.get("request_id"):
                        req_id = str(payload.get("request_id"))

                    content = payload.get("content", "")
                    fmt_input = str(payload.get("format", "auto")).lower()
                    encoding = payload.get("encoding", "")
                    if isinstance(content, str) and ("docs.google.com/spreadsheets" in content or content.strip().startswith('{"url":')):
                        raw_sheet, _ = _try_fetch_google_sheet(content)
                        if raw_sheet:
                            grid_content = raw_sheet
                            fmt_input = "xlsx"
                        else:
                            grid_content = b""
                    elif encoding == "base64" or fmt_input in ("xlsx", "excel", "xls", "ods", "xlsm", "xltx", "xltm") or (isinstance(content, str) and content.startswith("data:")):
                        if isinstance(content, str):
                            clean_str = content.split(",", 1)[-1] if content.startswith("data:") else content
                            try:
                                grid_content = base64.b64decode(clean_str)
                            except Exception as e:
                                self._send_error_json(
                                    f"Invalid base64 payload: {e}",
                                    status=400,
                                    request_id=req_id,
                                )
                                return
                        else:
                            grid_content = content
                    else:
                        grid_content = content

                from spatial_sheet_parser.adapters import inspect_workbook_sheets
                sheet_names = inspect_workbook_sheets(grid_content, source_format=fmt_input)
                self._send_json(
                    {
                        "success": True,
                        "sheets": sheet_names,
                        "active_sheet": sheet_names[0] if sheet_names else None,
                    },
                    status=200,
                    request_id=req_id,
                )
            except Exception as e:
                self._send_error_json(f"Error inspecting workbook sheets: {e}", status=400, request_id=req_id)
            return

        self._send_error_json("Endpoint not found.", status=404)


    def _serve_file(self, file_path: str, mime_type: str) -> None:
        try:
            with open(file_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("X-XSS-Protection", "1; mode=block")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self._send_error_json(f"Failed to read asset file: {e}", status=500)

    def _send_json(self, data: Dict[str, Any], status: int = 200, request_id: Optional[str] = None) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-XSS-Protection", "1; mode=block")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Connection", "close")
        if request_id:
            self.send_header("X-Request-ID", request_id)
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(
        self,
        message: str,
        status: int = 400,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        import datetime
        import time

        now = datetime.datetime.now(datetime.timezone.utc)
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        req_id = request_id or self.headers.get("X-Request-ID") or f"req-{int(time.time() * 1000)}"
        error_payload: Dict[str, Any] = {
            "success": False,
            "error": message,
            "status_code": status,
            "timestamp": timestamp,
            "request_id": req_id,
        }
        if details is not None:
            error_payload["details"] = details
        self._send_json(error_payload, status=status, request_id=req_id)


def create_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    quiet: bool = False,
) -> http.server.ThreadingHTTPServer:
    """Creates a ThreadingHTTPServer bound to host and port."""
    server = http.server.ThreadingHTTPServer((host, port), SpatialSheetHTTPRequestHandler)
    server.quiet = quiet  # type: ignore[attr-defined]
    server.daemon_threads = True
    return server



def run_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    open_browser: bool = False,
) -> None:
    """Runs local web server loop."""
    server = create_server(host=host, port=port, quiet=False)
    actual_port = server.socket.getsockname()[1]
    url = f"http://{host}:{actual_port}/"

    if sys.stdout is not None:
        print(f"Spatial Sheet Parser Web UI running at {url}")
        print("Press Ctrl+C to stop the web server.")

    if open_browser:
        import webbrowser
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if sys.stdout is not None:
            print("\nShutting down web server gracefully...")
    finally:
        server.server_close()


def main(args: Optional[List[str]] = None) -> int:
    """CLI entry point for web application server module."""
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    env_port_str = os.environ.get("PORT")
    default_port = int(env_port_str) if env_port_str and env_port_str.isdigit() else 8080
    env_host = os.environ.get("HOST", "0.0.0.0" if env_port_str else "127.0.0.1")
    is_cloud_env = bool(env_port_str or os.environ.get("RENDER"))

    parser = argparse.ArgumentParser(
        prog="spatial-sheet-parser-web",
        description="Spatial Sheet Parser — Local & Cloud Web Application Interface",
    )
    parser.add_argument(
        "--host",
        default=env_host,
        help=f"Host address to bind (default: {env_host})",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=default_port,
        help=f"Port number to listen on (default: {default_port})",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        default=False if is_cloud_env else None,
        help="Open default browser automatically on launch",
    )

    parsed_args = parser.parse_args(args if args is not None else sys.argv[1:])
    run_server(
        host=parsed_args.host,
        port=parsed_args.port,
        open_browser=parsed_args.open if parsed_args.open is not None else (False if is_cloud_env else False),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
