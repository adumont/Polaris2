"""Test CLI main entry point (via argparse simulation)."""

import sys
from contextlib import suppress

from polaris2.cli.app import main


class TestMain:
    def test_main_with_seed(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["polaris2", "--seed", "42"])
        with suppress(SystemExit):
            main()
