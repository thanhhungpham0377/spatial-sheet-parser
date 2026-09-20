"""Packaging smoke test verifying built Windows portable single-file EXE."""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXE_PATH = os.path.join(PROJECT_ROOT, "dist", "spatial-sheet-parser.exe")


class TestPackagingSmoke(unittest.TestCase):
    """Smoke tests for the packaged Windows executable artifact."""

    def test_exe_exists_and_size(self):
        """Verify the generated executable exists and is non-empty."""
        self.assertTrue(os.path.isfile(EXE_PATH), f"Executable not found at {EXE_PATH}")
        size = os.path.getsize(EXE_PATH)
        self.assertGreater(size, 1024 * 1024, "Executable size is smaller than expected (minimum 1MB)")

    def test_exe_cli_help(self):
        """Verify executing the EXE with --help returns 0 exit code."""
        if not os.path.isfile(EXE_PATH):
            self.skipTest("Executable artifact not found.")

        res = subprocess.run([EXE_PATH, "--help"], capture_output=True, text=True, timeout=10)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Spatial Sheet Parser", res.stdout)

    def test_exe_web_server_smoke(self):
        """Verify starting the EXE in double-click web mode serves UI and parsing API."""
        if not os.path.isfile(EXE_PATH):
            self.skipTest("Executable artifact not found.")

        proc_web = subprocess.Popen(
            [EXE_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            base_url = None
            for _ in range(25):
                time.sleep(0.2)
                for p in range(8080, 8090):
                    try:
                        req = urllib.request.urlopen(f"http://127.0.0.1:{p}/", timeout=0.5)
                        if req.status == 200:
                            base_url = f"http://127.0.0.1:{p}"
                            req.close()
                            break
                    except Exception:
                        continue
                if base_url:
                    break

            self.assertIsNotNone(base_url, "Packaged web server failed to respond on localhost within timeout.")

            # Verify GET / index page HTML
            with urllib.request.urlopen(f"{base_url}/") as resp:
                self.assertEqual(resp.status, 200)
                html = resp.read().decode("utf-8")
                self.assertIn("Spatial Sheet Parser", html)

            # Verify POST /api/parse API endpoint with Excel base64
            import base64
            xlsx_fixture = os.path.join(PROJECT_ROOT, "tests", "fixtures", "sample_workbook.xlsx")
            with open(xlsx_fixture, "rb") as f:
                b64_content = base64.b64encode(f.read()).decode("utf-8")

            payload = {
                "content": b64_content,
                "format": "xlsx",
                "encoding": "base64",
                "sheet_name": "Sales Overview",
            }
            req = urllib.request.Request(
                url=f"{base_url}/api/parse",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200)
                res_json = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(res_json.get("success"))
                self.assertEqual(res_json["result"]["metadata"]["source_format"], "xlsx")
                self.assertEqual(res_json["result"]["metadata"]["sheet_name"], "Sales Overview")

        finally:
            proc_web.stdout.close()
            proc_web.stderr.close()
            proc_web.terminate()
            try:
                proc_web.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc_web.kill()

    def test_exe_cli_excel_parsing(self):
        """Verify direct CLI execution of packaged EXE with an .xlsx file."""
        if not os.path.isfile(EXE_PATH):
            self.skipTest("Executable artifact not found.")

        xlsx_fixture = os.path.join(PROJECT_ROOT, "tests", "fixtures", "sample_workbook.xlsx")
        res = subprocess.run([EXE_PATH, "parse", xlsx_fixture, "--sheet", "Inventory", "--preview"], capture_output=True, text=True, timeout=15)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Source Format : xlsx", res.stdout)
        self.assertIn("Sheet: Inventory", res.stdout)
        self.assertIn("Warehouse Stock", res.stdout)

    def test_exe_cli_xls_parsing(self):
        """Verify direct CLI execution of packaged EXE with an .xls file."""
        if not os.path.isfile(EXE_PATH):
            self.skipTest("Executable artifact not found.")

        xls_fixture = os.path.join(PROJECT_ROOT, "tests", "fixtures", "sample_workbook.xls")
        res = subprocess.run([EXE_PATH, "parse", xls_fixture, "--sheet", "Inventory", "--preview"], capture_output=True, text=True, timeout=15)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Source Format : xls", res.stdout)
        self.assertIn("Sheet: Inventory", res.stdout)
        self.assertIn("Inventory List", res.stdout)

    def test_exe_cli_ods_parsing(self):
        """Verify direct CLI execution of packaged EXE with an .ods file."""
        if not os.path.isfile(EXE_PATH):
            self.skipTest("Executable artifact not found.")

        ods_fixture = os.path.join(PROJECT_ROOT, "tests", "fixtures", "sample_workbook.ods")
        res = subprocess.run([EXE_PATH, "parse", ods_fixture, "--sheet", "Inventory", "--preview"], capture_output=True, text=True, timeout=15)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Source Format : ods", res.stdout)
        self.assertIn("Sheet: Inventory", res.stdout)
        self.assertIn("Inventory List", res.stdout)


if __name__ == "__main__":
    unittest.main()
