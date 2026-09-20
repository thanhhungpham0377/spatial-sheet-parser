"""Windows Portable Single-File Launcher Entrypoint for Spatial Sheet Parser."""

import os
import sys
import socket
from typing import List, Optional

# Ensure package root is in sys.path when executed directly or frozen
if getattr(sys, "frozen", False):
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
else:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from spatial_sheet_parser.cli import main as cli_main
from spatial_sheet_parser.web import run_server


def find_available_port(preferred_port: int = 8080, max_attempts: int = 100) -> int:
    """Find an available TCP port starting from preferred_port."""
    for port in range(preferred_port, preferred_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main(args: Optional[List[str]] = None) -> int:
    """Launcher entry point."""
    log_file = os.path.join(os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd(), "launcher_debug.log")
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"Launcher started. Frozen={getattr(sys, 'frozen', False)}, argv={sys.argv}\n")

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

        cli_args = args if args is not None else sys.argv[1:]

        # If CLI arguments are provided (e.g. `parse`, `--help`, `-v`), pass to CLI
        if cli_args:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"Running cli_main with args={cli_args}\n")
            return cli_main(cli_args)

        # Double-click behavior: find available port, launch web UI server & open default browser
        port = find_available_port(8080)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"Found port {port}, calling run_server...\n")
        run_server(host="127.0.0.1", port=port, open_browser=True)
        return 0
    except Exception:
        import traceback
        tb = traceback.format_exc()
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"EXCEPTION: {tb}\n")
        except Exception:
            pass
        if sys.stderr is not None:
            sys.stderr.write(tb)
        return 1


if __name__ == "__main__":
    sys.exit(main())
