from __future__ import annotations

import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class SmokeTests(unittest.TestCase):
    def test_text_files_do_not_contain_common_mojibake(self) -> None:
        mojibake_markers = [
            "\u00c3",  # UTF-8 text decoded as Latin-1/Windows-1252
            "\u00c2",  # stray non-breaking-space/control mojibake prefix
            "\u00e2\u20ac",  # smart quote/dash mojibake prefix
            "\u00e2\u20ac\u0153",  # opening curly quote mojibake
            "\u00e2\u20ac\ufffd",  # closing curly quote with replacement char
            "\u00e2\u20ac\u2122",  # apostrophe mojibake
            "\u00e2\u20ac\u201c",  # en dash mojibake
            "\u00e2\u20ac\u201d",  # em dash mojibake
            "\u00e2\u201d",  # box drawing mojibake prefix
            "\u00f0\u0178",  # emoji mojibake prefix
            "\ufffd",  # replacement character
        ]
        text_suffixes = {
            ".css",
            ".html",
            ".js",
            ".jsx",
            ".json",
            ".md",
            ".ps1",
            ".py",
            ".sh",
            ".txt",
            ".yaml",
            ".yml",
        }
        ignored_parts = {
            ".git",
            ".venv",
            "__pycache__",
            "node_modules",
            "dist",
            "cache",
            "results",
        }

        offenders: list[str] = []
        for path in REPO_ROOT.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in text_suffixes:
                continue
            if any(part in ignored_parts for part in path.parts):
                continue

            text = path.read_text(encoding="utf-8", errors="replace")
            for marker in mojibake_markers:
                if marker in text:
                    rel = path.relative_to(REPO_ROOT)
                    offenders.append(f"{rel}: contains {marker!r}")
                    break

        self.assertEqual([], offenders)

    def test_env_example_has_required_keys(self) -> None:
        env_text = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
        required_keys = [
            "GEMINI_API_KEY",
            "GEMINI_API_KEYS",
            "FINNHUB_API_KEY",
            "NEWSAPI_KEY",
            "NEWSDATA_API_KEY",
            "ADMIN_USERNAME",
            "ADMIN_PASSWORD",
            "ADMIN_SECRET",
        ]
        for key in required_keys:
            with self.subTest(key=key):
                self.assertIn(f"{key}=", env_text)

    def test_frontend_package_scripts_and_proxy_are_present(self) -> None:
        package_data = json.loads((REPO_ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
        scripts = package_data.get("scripts", {})

        self.assertIn("dev", scripts)
        self.assertIn("build", scripts)
        self.assertIn("lint", scripts)
        self.assertIn("preview", scripts)
        self.assertIn("--host 0.0.0.0", scripts["dev"])
        self.assertIn("--host 0.0.0.0", scripts["preview"])

        vite_config = (REPO_ROOT / "frontend" / "vite.config.js").read_text(encoding="utf-8")
        self.assertIn("'/api'", vite_config)
        self.assertIn("http://localhost:5000", vite_config)

    def test_build_helper_help_runs(self) -> None:
        if os.name == "nt":
            powershell = shutil.which("powershell") or shutil.which("pwsh")
            self.assertIsNotNone(powershell, "PowerShell is required for the Windows smoke test")
            command = [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(REPO_ROOT / "build.ps1"),
                "help",
            ]
        else:
            bash = shutil.which("bash")
            self.assertIsNotNone(bash, "bash is required for the Unix smoke test")
            command = [bash, str(REPO_ROOT / "build.sh"), "help"]

        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("frontend-build", result.stdout)
        self.assertIn("backend", result.stdout)


if __name__ == "__main__":
    unittest.main()
