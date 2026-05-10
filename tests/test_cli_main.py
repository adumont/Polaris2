"""Test CLI main entry point (via argparse simulation)."""

import subprocess
import sys
from contextlib import suppress

import pytest

from polaris2.cli.app import main


class TestMain:
    def test_main_with_seed(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["polaris2", "--seed", "42"])
        with suppress(SystemExit):
            main()

    def test_main_with_output(self, monkeypatch, tmp_path):
        out = tmp_path / "out.yaml"
        monkeypatch.setattr(sys, "argv", ["polaris2", "--seed", "42", "--output", str(out)])
        with suppress(SystemExit):
            main()
        assert out.exists()

    def test_main_with_format_dmm(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["polaris2", "--seed", "42", "--format", "dmm"])
        with suppress(SystemExit):
            main()

    def test_main_with_interactive_chooses_all(self, monkeypatch):
        inputs = iter(["all", "n", ""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        monkeypatch.setattr(sys, "argv", ["polaris2", "--seed", "42", "--interactive"])
        with suppress(SystemExit):
            main()

    def test_main_with_error_and_he(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["polaris2", "--seed", "42", "--error", "10.0", "--he", "20.0"])
        with suppress(SystemExit):
            main()

    def test_main_guard_via_subprocess(self):
        result = subprocess.run(
            [sys.executable, "-m", "polaris2.cli.app", "--seed", "1"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0
        assert "Real Position" in result.stdout
